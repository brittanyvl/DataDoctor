"""
Main validation orchestrator.

This module coordinates the execution of all validation tests
based on a contract configuration.
"""

from typing import Any, Optional

import pandas as pd

from src.constants import (
    ERROR_COLUMN_NAME,
    ERROR_COUNT_COLUMN_NAME,
    STATUS_COLUMN_NAME,
    STATUS_FAIL,
    STATUS_PASS,
)
from src.contract.schema import (
    ColumnConfig,
    Contract,
    Normalization,
)
from src.validation.column_tests import run_column_test
from src.validation.dataset_tests import run_dataset_test
from src.validation.foreign_key import (
    create_normalization_function,
    validate_foreign_key,
)
from src.validation.results import (
    CellValidationResult,
    ColumnTestResult,
    ColumnValidationResult,
    DatasetTestResult,
    ForeignKeyCheckResult,
    ValidationResult,
    ValidationSummary,
    calculate_summary,
)


def run_validation(
    df: pd.DataFrame,
    contract: Contract,
    fk_dataframe: Optional[pd.DataFrame] = None,
) -> ValidationResult:
    """
    Run complete validation based on a contract.

    Args:
        df: The DataFrame to validate
        contract: The validation contract
        fk_dataframe: Optional foreign key reference DataFrame

    Returns:
        ValidationResult with all test results
    """
    column_results: dict[str, ColumnValidationResult] = {}
    dataset_test_results: list[DatasetTestResult] = []
    fk_check_results: list[ForeignKeyCheckResult] = []
    cell_errors: list[CellValidationResult] = []
    blocking_errors: list[str] = []

    # Pre-process the dataframe (apply normalizations)
    processed_df = _apply_normalizations(df, contract)

    # Run column-level tests
    for col_config in contract.columns:
        col_name = col_config.name

        if col_name not in processed_df.columns:
            # Column missing from dataset
            blocking_errors.append(f"Column '{col_name}' not found in dataset")
            continue

        series = processed_df[col_name]
        col_result, col_cell_errors = _validate_column(
            series,
            col_config,
        )

        column_results[col_name] = col_result
        cell_errors.extend(col_cell_errors)

        # Check for blocking errors
        for test_result in col_result.test_results:
            if not test_result.passed and test_result.severity == "error":
                if col_config.failure_handling.action == "strict_fail":
                    blocking_errors.append(
                        f"Column '{col_name}' test '{test_result.test_type}' "
                        "has strict_fail policy"
                    )

    # Run dataset-level tests
    for dt_test in contract.dataset_tests:
        dt_result = run_dataset_test(
            dt_test.type,
            processed_df,
            dt_test.severity,
            dt_test.params,
        )
        dataset_test_results.append(dt_result)

        # Check for blocking errors
        if not dt_result.passed and dt_test.severity == "error":
            on_fail = dt_test.on_fail
            if on_fail and on_fail.action == "strict_fail":
                blocking_errors.append(
                    f"Dataset test '{dt_test.type}' has strict_fail policy"
                )

    # Run foreign key checks
    for fk_check in contract.foreign_key_checks:
        if fk_dataframe is None:
            fk_check_results.append(
                ForeignKeyCheckResult(
                    name=fk_check.name,
                    dataset_column=fk_check.dataset_column,
                    fk_column=fk_check.fk_column,
                    passed=False,
                    total_values=0,
                    missing_count=0,
                    missing_values=[],
                    missing_row_indices=[],
                )
            )
            blocking_errors.append(
                f"FK check '{fk_check.name}' failed: no FK file provided"
            )
            continue

        if fk_check.dataset_column not in processed_df.columns:
            blocking_errors.append(
                f"FK check '{fk_check.name}': column '{fk_check.dataset_column}' "
                "not found in dataset"
            )
            continue

        if fk_check.fk_column not in fk_dataframe.columns:
            blocking_errors.append(
                f"FK check '{fk_check.name}': column '{fk_check.fk_column}' "
                "not found in FK file"
            )
            continue

        # Get normalization from dataset column config
        col_config = _get_column_config(contract, fk_check.dataset_column)
        norm_func = None
        if col_config and col_config.normalization:
            norm_func = create_normalization_function(
                trim_whitespace=col_config.normalization.trim_whitespace,
                case=col_config.normalization.case,
                null_tokens=col_config.normalization.null_tokens,
            )

        fk_result = validate_foreign_key(
            processed_df[fk_check.dataset_column],
            fk_dataframe[fk_check.fk_column],
            fk_check.name,
            fk_check.dataset_column,
            fk_check.fk_column,
            allow_nulls=fk_check.null_policy.allow_nulls,
            normalization_func=norm_func,
        )
        fk_check_results.append(fk_result)

        # Check for blocking errors
        if not fk_result.passed:
            if fk_check.on_fail.action == "strict_fail":
                blocking_errors.append(
                    f"FK check '{fk_check.name}' has strict_fail policy"
                )

    # Calculate summary
    summary = calculate_summary(
        column_results,
        dataset_test_results,
        fk_check_results,
        cell_errors,
        len(df),
        len(df.columns),
    )

    # Determine overall validity
    is_valid = len(blocking_errors) == 0 and summary.total_errors == 0

    return ValidationResult(
        is_valid=is_valid,
        summary=summary,
        column_results=column_results,
        dataset_test_results=dataset_test_results,
        fk_check_results=fk_check_results,
        cell_errors=cell_errors,
        blocking_errors=blocking_errors,
    )


def _apply_normalizations(
    df: pd.DataFrame,
    contract: Contract,
) -> pd.DataFrame:
    """
    Apply column normalizations as preprocessing.

    Args:
        df: The original DataFrame
        contract: The contract with normalization configs

    Returns:
        DataFrame with normalizations applied
    """
    result_df = df.copy()

    for col_config in contract.columns:
        col_name = col_config.name

        if col_name not in result_df.columns:
            continue

        norm = col_config.normalization
        if norm is None:
            continue

        series = result_df[col_name]

        # Apply normalizations
        if norm.trim_whitespace:
            series = series.apply(
                lambda x: str(x).strip() if pd.notna(x) and isinstance(x, str) else x
            )

        if norm.remove_non_printable:
            series = series.apply(
                lambda x: _remove_non_printable(x) if pd.notna(x) else x
            )

        if norm.null_tokens:
            null_tokens_set = set(norm.null_tokens)
            series = series.apply(
                lambda x: None if str(x) in null_tokens_set else x
            )

        if norm.case and norm.case != "none":
            if norm.case == "lower":
                series = series.apply(
                    lambda x: str(x).lower() if pd.notna(x) else x
                )
            elif norm.case == "upper":
                series = series.apply(
                    lambda x: str(x).upper() if pd.notna(x) else x
                )
            elif norm.case == "title":
                series = series.apply(
                    lambda x: str(x).title() if pd.notna(x) else x
                )

        result_df[col_name] = series

    return result_df


def _remove_non_printable(value: Any) -> Any:
    """Remove non-printable characters from a value."""
    if not isinstance(value, str):
        return value

    # Keep printable ASCII and common whitespace
    return "".join(
        c for c in value
        if c.isprintable() or c in "\t\n\r"
    )


def _validate_column(
    series: pd.Series,
    col_config: ColumnConfig,
) -> tuple[ColumnValidationResult, list[CellValidationResult]]:
    """
    Validate a single column.

    Args:
        series: The column data
        col_config: Column configuration

    Returns:
        Tuple of (ColumnValidationResult, list of CellValidationResults)
    """
    test_results: list[ColumnTestResult] = []
    cell_errors: list[CellValidationResult] = []

    col_name = col_config.name
    data_type = col_config.data_type

    # Run each configured test
    for test in col_config.tests:
        result = run_column_test(
            test.type,
            series,
            col_name,
            data_type,
            test.severity,
            test.params,
        )
        test_results.append(result)

        # Generate cell-level errors for failed tests
        if not result.passed:
            for i, idx in enumerate(result.failed_indices):
                value = result.failed_values[i] if i < len(result.failed_values) else None
                detail = result.error_details[i] if i < len(result.error_details) else ""

                cell_errors.append(
                    CellValidationResult(
                        row_index=idx,
                        column_name=col_name,
                        original_value=value,
                        is_valid=False,
                        test_type=test.type,
                        error_message=detail,
                        severity=test.severity,
                    )
                )

    # Calculate column-level stats
    passed_tests = sum(1 for r in test_results if r.passed)
    failed_tests = sum(1 for r in test_results if not r.passed)
    warning_count = sum(
        1 for r in test_results
        if not r.passed and r.severity == "warning"
    )
    error_count = sum(
        1 for r in test_results
        if not r.passed and r.severity == "error"
    )

    # Determine overall status
    if error_count > 0:
        overall_status = "FAIL"
    elif warning_count > 0:
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    col_result = ColumnValidationResult(
        column_name=col_name,
        data_type=data_type,
        is_valid=error_count == 0,
        total_tests=len(test_results),
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        warning_count=warning_count,
        test_results=test_results,
        overall_status=overall_status,
    )

    return col_result, cell_errors


def _get_column_config(
    contract: Contract,
    column_name: str,
) -> Optional[ColumnConfig]:
    """Get column configuration by name."""
    for col in contract.columns:
        if col.name == column_name:
            return col
    return None


def add_error_columns(
    df: pd.DataFrame,
    validation_result: ValidationResult,
) -> pd.DataFrame:
    """
    Add error label columns to a DataFrame based on validation results.

    Args:
        df: The original DataFrame
        validation_result: Validation results

    Returns:
        DataFrame with error columns added
    """
    result_df = df.copy()

    # Initialize error columns
    result_df[ERROR_COLUMN_NAME] = ""
    result_df[ERROR_COUNT_COLUMN_NAME] = 0
    result_df[STATUS_COLUMN_NAME] = STATUS_PASS

    # Group cell errors by row
    row_errors: dict[int, list[str]] = {}

    for cell_error in validation_result.cell_errors:
        idx = cell_error.row_index
        if idx not in row_errors:
            row_errors[idx] = []

        # Format error: test_type:detail
        error_str = cell_error.test_type
        if cell_error.error_message:
            # Extract short detail
            error_str += f":{cell_error.column_name}"

        row_errors[idx].append(error_str)

    # Apply to DataFrame
    for idx, errors in row_errors.items():
        if idx in result_df.index:
            result_df.at[idx, ERROR_COLUMN_NAME] = "|".join(errors)
            result_df.at[idx, ERROR_COUNT_COLUMN_NAME] = len(errors)
            result_df.at[idx, STATUS_COLUMN_NAME] = STATUS_FAIL

    return result_df


def get_rows_by_status(
    df: pd.DataFrame,
    validation_result: ValidationResult,
    status: str = "fail",
) -> pd.DataFrame:
    """
    Get rows filtered by validation status.

    Args:
        df: The original DataFrame
        validation_result: Validation results
        status: "pass", "fail", or "warning"

    Returns:
        Filtered DataFrame
    """
    # Get indices with errors
    error_indices = set()
    warning_indices = set()

    for cell_error in validation_result.cell_errors:
        if cell_error.severity == "error":
            error_indices.add(cell_error.row_index)
        else:
            warning_indices.add(cell_error.row_index)

    if status == "fail":
        return df.loc[df.index.isin(error_indices)]
    elif status == "warning":
        return df.loc[df.index.isin(warning_indices - error_indices)]
    else:  # pass
        all_failed = error_indices | warning_indices
        return df.loc[~df.index.isin(all_failed)]


def get_validation_summary_dict(
    validation_result: ValidationResult,
) -> dict[str, Any]:
    """
    Convert validation result to a dictionary for reporting.

    Args:
        validation_result: The validation result

    Returns:
        Dictionary with summary data
    """
    summary = validation_result.summary

    return {
        "is_valid": validation_result.is_valid,
        "total_rows": summary.total_rows,
        "total_columns": summary.total_columns,
        "tests_run": summary.total_tests_run,
        "tests_passed": summary.total_tests_passed,
        "tests_failed": summary.total_tests_failed,
        "warnings": summary.total_warnings,
        "errors": summary.total_errors,
        "rows_with_errors": summary.rows_with_errors,
        "clean_rows": summary.clean_rows,
        "error_rate_percent": summary.error_rate_percent,
        "has_blocking_errors": summary.has_blocking_errors,
        "blocking_errors": validation_result.blocking_errors,
        "column_statuses": {
            col_name: col_result.overall_status
            for col_name, col_result in validation_result.column_results.items()
        },
    }
