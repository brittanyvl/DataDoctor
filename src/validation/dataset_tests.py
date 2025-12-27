"""
Dataset-level test implementations.

This module implements all dataset-level validation tests as specified
in Section 12.2 of the acceptance criteria.
"""

from typing import Any, Callable, Optional

import pandas as pd
import numpy as np

from src.constants import (
    COMPARISON_OPERATORS,
    OUTLIER_IQR_MULTIPLIER_DEFAULT,
    OUTLIER_ZSCORE_THRESHOLD_DEFAULT,
)
from src.validation.results import DatasetTestResult


def test_duplicate_rows(
    df: pd.DataFrame,
    severity: str = "warning",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Test for duplicate rows in the dataset.

    Args:
        df: The DataFrame to test
        severity: Test severity
        params: Optional dict with 'subset' (list of columns to check)

    Returns:
        DatasetTestResult
    """
    params = params or {}
    subset = params.get("subset")  # None means all columns

    # Find duplicates
    duplicated = df.duplicated(subset=subset, keep=False)
    duplicate_indices = df.index[duplicated].tolist()
    duplicate_count = len(duplicate_indices)

    if duplicate_count > 0:
        # Count unique duplicate groups
        if subset:
            grouped = df[duplicated].groupby(subset).size()
        else:
            grouped = df[duplicated].groupby(list(df.columns)).size()
        unique_duplicate_groups = len(grouped)

        message = (
            f"Found {duplicate_count} rows in {unique_duplicate_groups} "
            "duplicate groups"
        )
    else:
        message = "No duplicate rows found"

    return DatasetTestResult(
        test_type="duplicate_rows",
        severity=severity,
        passed=duplicate_count == 0,
        message=message,
        details={
            "duplicate_count": duplicate_count,
            "subset": subset,
        },
        affected_rows=duplicate_indices[:1000],  # Limit
    )


def test_primary_key_completeness(
    df: pd.DataFrame,
    severity: str = "error",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Test that primary key columns have no null values.

    Args:
        df: The DataFrame to test
        severity: Test severity
        params: Dict with 'key_columns' list

    Returns:
        DatasetTestResult
    """
    params = params or {}
    key_columns = params.get("key_columns", [])

    if not key_columns:
        return DatasetTestResult(
            test_type="primary_key_completeness",
            severity=severity,
            passed=False,
            message="No key columns specified",
            details={},
        )

    # Check for nulls in key columns
    null_counts = {}
    affected_rows = []

    for col in key_columns:
        if col in df.columns:
            null_mask = df[col].isna()
            null_count = null_mask.sum()
            null_counts[col] = int(null_count)
            if null_count > 0:
                affected_rows.extend(df.index[null_mask].tolist())

    total_nulls = sum(null_counts.values())
    affected_rows = list(set(affected_rows))  # Remove duplicates

    if total_nulls > 0:
        message = f"Primary key has {total_nulls} null values across key columns"
    else:
        message = "Primary key is complete (no null values)"

    return DatasetTestResult(
        test_type="primary_key_completeness",
        severity=severity,
        passed=total_nulls == 0,
        message=message,
        details={
            "key_columns": key_columns,
            "null_counts": null_counts,
        },
        affected_rows=affected_rows[:1000],
    )


def test_primary_key_uniqueness(
    df: pd.DataFrame,
    severity: str = "error",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Test that primary key values are unique.

    Args:
        df: The DataFrame to test
        severity: Test severity
        params: Dict with 'key_columns' list

    Returns:
        DatasetTestResult
    """
    params = params or {}
    key_columns = params.get("key_columns", [])

    if not key_columns:
        return DatasetTestResult(
            test_type="primary_key_uniqueness",
            severity=severity,
            passed=False,
            message="No key columns specified",
            details={},
        )

    # Check if all key columns exist
    missing_cols = [c for c in key_columns if c not in df.columns]
    if missing_cols:
        return DatasetTestResult(
            test_type="primary_key_uniqueness",
            severity=severity,
            passed=False,
            message=f"Key columns not found: {missing_cols}",
            details={"missing_columns": missing_cols},
        )

    # Find duplicates on key columns
    duplicated = df.duplicated(subset=key_columns, keep=False)
    duplicate_indices = df.index[duplicated].tolist()
    duplicate_count = len(duplicate_indices)

    if duplicate_count > 0:
        # Get sample of duplicate key values
        duplicate_keys = df.loc[duplicated, key_columns].drop_duplicates().head(10)
        sample_keys = duplicate_keys.to_dict("records")

        message = f"Primary key has {duplicate_count} duplicate rows"
    else:
        sample_keys = []
        message = "Primary key is unique"

    return DatasetTestResult(
        test_type="primary_key_uniqueness",
        severity=severity,
        passed=duplicate_count == 0,
        message=message,
        details={
            "key_columns": key_columns,
            "duplicate_count": duplicate_count,
            "sample_duplicate_keys": sample_keys,
        },
        affected_rows=duplicate_indices[:1000],
    )


def test_composite_key_uniqueness(
    df: pd.DataFrame,
    severity: str = "error",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Test that composite key values are unique.

    This is essentially the same as primary_key_uniqueness but
    with a different semantic meaning (explicitly multiple columns).

    Args:
        df: The DataFrame to test
        severity: Test severity
        params: Dict with 'key_columns' list

    Returns:
        DatasetTestResult
    """
    # Reuse primary key uniqueness logic
    result = test_primary_key_uniqueness(df, severity, params)
    # Update the test type
    return DatasetTestResult(
        test_type="composite_key_uniqueness",
        severity=result.severity,
        passed=result.passed,
        message=result.message.replace("Primary key", "Composite key"),
        details=result.details,
        affected_rows=result.affected_rows,
    )


def test_cross_field_rule(
    df: pd.DataFrame,
    severity: str = "error",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Test a cross-field logical rule.

    Args:
        df: The DataFrame to test
        severity: Test severity
        params: Dict with 'rule_name', 'if' (conditions), 'assert' (expression)

    Returns:
        DatasetTestResult
    """
    params = params or {}
    rule_name = params.get("rule_name", "unnamed_rule")
    if_clause = params.get("if", {})
    assert_clause = params.get("assert", {})

    expression = assert_clause.get("expression", "")

    if not expression:
        return DatasetTestResult(
            test_type="cross_field_rule",
            severity=severity,
            passed=False,
            message=f"Rule '{rule_name}': No expression specified",
            details={"rule_name": rule_name},
        )

    # Build mask for rows that meet the 'if' condition
    all_not_null = if_clause.get("all_not_null", [])

    if all_not_null:
        # Only evaluate rows where all specified columns are not null
        condition_mask = pd.Series(True, index=df.index)
        for col in all_not_null:
            if col in df.columns:
                condition_mask = condition_mask & df[col].notna()
        rows_to_check = df[condition_mask]
    else:
        rows_to_check = df

    if len(rows_to_check) == 0:
        return DatasetTestResult(
            test_type="cross_field_rule",
            severity=severity,
            passed=True,
            message=f"Rule '{rule_name}': No rows to check (all filtered by conditions)",
            details={"rule_name": rule_name, "rows_checked": 0},
        )

    # Parse and evaluate the expression
    failed_indices = []

    try:
        result_mask = _evaluate_cross_field_expression(rows_to_check, expression)
        failed_mask = ~result_mask
        failed_indices = rows_to_check.index[failed_mask].tolist()
    except Exception as e:
        return DatasetTestResult(
            test_type="cross_field_rule",
            severity=severity,
            passed=False,
            message=f"Rule '{rule_name}': Error evaluating expression: {str(e)}",
            details={"rule_name": rule_name, "expression": expression},
        )

    failed_count = len(failed_indices)

    if failed_count > 0:
        message = f"Rule '{rule_name}': {failed_count} rows failed the assertion"
    else:
        message = f"Rule '{rule_name}': All {len(rows_to_check)} rows passed"

    return DatasetTestResult(
        test_type="cross_field_rule",
        severity=severity,
        passed=failed_count == 0,
        message=message,
        details={
            "rule_name": rule_name,
            "expression": expression,
            "rows_checked": len(rows_to_check),
            "rows_failed": failed_count,
        },
        affected_rows=failed_indices[:1000],
    )


def _evaluate_cross_field_expression(df: pd.DataFrame, expression: str) -> pd.Series:
    """
    Evaluate a simple cross-field comparison expression.

    Supports: <, <=, >, >=, ==, !=
    Operands: column names or literals

    Args:
        df: DataFrame to evaluate against
        expression: Expression like "start_date <= end_date"

    Returns:
        Boolean Series with evaluation results
    """
    # Parse the expression
    for op in ["<=", ">=", "==", "!=", "<", ">"]:
        if op in expression:
            parts = expression.split(op, 1)
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()

                # Get left operand
                if left in df.columns:
                    left_series = df[left]
                else:
                    # Try to parse as literal
                    left_series = pd.Series(_parse_literal(left), index=df.index)

                # Get right operand
                if right in df.columns:
                    right_series = df[right]
                else:
                    right_series = pd.Series(_parse_literal(right), index=df.index)

                # Apply operator
                if op == "<":
                    return left_series < right_series
                elif op == "<=":
                    return left_series <= right_series
                elif op == ">":
                    return left_series > right_series
                elif op == ">=":
                    return left_series >= right_series
                elif op == "==":
                    return left_series == right_series
                elif op == "!=":
                    return left_series != right_series

    raise ValueError(f"Could not parse expression: {expression}")


def _parse_literal(value: str) -> Any:
    """Parse a string literal to its appropriate type."""
    # Try numeric
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Try boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Try to parse as date
    try:
        return pd.to_datetime(value)
    except Exception:
        pass

    # Return as string (remove quotes if present)
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    return value


def test_outliers_iqr(
    df: pd.DataFrame,
    severity: str = "warning",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Detect outliers using the IQR method.

    Args:
        df: The DataFrame to test
        severity: Test severity (usually warning)
        params: Dict with 'column' and optional 'multiplier'

    Returns:
        DatasetTestResult
    """
    params = params or {}
    column = params.get("column")
    multiplier = params.get("multiplier", OUTLIER_IQR_MULTIPLIER_DEFAULT)

    if not column or column not in df.columns:
        return DatasetTestResult(
            test_type="outliers_iqr",
            severity=severity,
            passed=True,
            message="No valid column specified for outlier detection",
            details={},
        )

    # Get numeric values
    try:
        values = pd.to_numeric(df[column], errors="coerce")
    except Exception:
        return DatasetTestResult(
            test_type="outliers_iqr",
            severity=severity,
            passed=True,
            message=f"Column '{column}' is not numeric",
            details={"column": column},
        )

    # Calculate IQR
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)

    # Find outliers
    outlier_mask = (values < lower_bound) | (values > upper_bound)
    outlier_indices = df.index[outlier_mask].tolist()
    outlier_count = len(outlier_indices)

    if outlier_count > 0:
        message = (
            f"Found {outlier_count} potential outliers in '{column}' "
            f"(outside {lower_bound:.2f} to {upper_bound:.2f})"
        )
    else:
        message = f"No outliers detected in '{column}' using IQR method"

    return DatasetTestResult(
        test_type="outliers_iqr",
        severity="warning",  # Always warning
        passed=True,  # Outliers are informational, don't fail
        message=message,
        details={
            "column": column,
            "multiplier": multiplier,
            "q1": float(q1) if not pd.isna(q1) else None,
            "q3": float(q3) if not pd.isna(q3) else None,
            "iqr": float(iqr) if not pd.isna(iqr) else None,
            "lower_bound": float(lower_bound) if not pd.isna(lower_bound) else None,
            "upper_bound": float(upper_bound) if not pd.isna(upper_bound) else None,
            "outlier_count": outlier_count,
        },
        affected_rows=outlier_indices[:1000],
    )


def test_outliers_zscore(
    df: pd.DataFrame,
    severity: str = "warning",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Detect outliers using the Z-score method.

    Args:
        df: The DataFrame to test
        severity: Test severity (usually warning)
        params: Dict with 'column' and optional 'threshold'

    Returns:
        DatasetTestResult
    """
    params = params or {}
    column = params.get("column")
    threshold = params.get("threshold", OUTLIER_ZSCORE_THRESHOLD_DEFAULT)

    if not column or column not in df.columns:
        return DatasetTestResult(
            test_type="outliers_zscore",
            severity=severity,
            passed=True,
            message="No valid column specified for outlier detection",
            details={},
        )

    # Get numeric values
    try:
        values = pd.to_numeric(df[column], errors="coerce")
    except Exception:
        return DatasetTestResult(
            test_type="outliers_zscore",
            severity=severity,
            passed=True,
            message=f"Column '{column}' is not numeric",
            details={"column": column},
        )

    # Calculate Z-scores
    mean_val = values.mean()
    std_val = values.std()

    if std_val == 0 or pd.isna(std_val):
        return DatasetTestResult(
            test_type="outliers_zscore",
            severity=severity,
            passed=True,
            message=f"Column '{column}' has zero variance",
            details={"column": column},
        )

    z_scores = np.abs((values - mean_val) / std_val)

    # Find outliers
    outlier_mask = z_scores > threshold
    outlier_indices = df.index[outlier_mask].tolist()
    outlier_count = len(outlier_indices)

    if outlier_count > 0:
        message = (
            f"Found {outlier_count} potential outliers in '{column}' "
            f"(Z-score > {threshold})"
        )
    else:
        message = f"No outliers detected in '{column}' using Z-score method"

    return DatasetTestResult(
        test_type="outliers_zscore",
        severity="warning",  # Always warning
        passed=True,  # Outliers are informational, don't fail
        message=message,
        details={
            "column": column,
            "threshold": threshold,
            "mean": float(mean_val) if not pd.isna(mean_val) else None,
            "std": float(std_val) if not pd.isna(std_val) else None,
            "outlier_count": outlier_count,
        },
        affected_rows=outlier_indices[:1000],
    )


# Test function registry
DATASET_TEST_FUNCTIONS: dict[str, Callable] = {
    "duplicate_rows": test_duplicate_rows,
    "primary_key_completeness": test_primary_key_completeness,
    "primary_key_uniqueness": test_primary_key_uniqueness,
    "composite_key_uniqueness": test_composite_key_uniqueness,
    "cross_field_rule": test_cross_field_rule,
    "outliers_iqr": test_outliers_iqr,
    "outliers_zscore": test_outliers_zscore,
}


def run_dataset_test(
    test_type: str,
    df: pd.DataFrame,
    severity: str = "error",
    params: Optional[dict] = None,
) -> DatasetTestResult:
    """
    Run a dataset test by type.

    Args:
        test_type: The type of test to run
        df: The DataFrame to test
        severity: Test severity
        params: Test parameters

    Returns:
        DatasetTestResult
    """
    test_func = DATASET_TEST_FUNCTIONS.get(test_type)

    if test_func is None:
        return DatasetTestResult(
            test_type=test_type,
            severity=severity,
            passed=False,
            message=f"Unknown test type: {test_type}",
            details={},
        )

    return test_func(df, severity, params)
