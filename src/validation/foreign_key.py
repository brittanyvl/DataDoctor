"""
Foreign key membership validation.

This module implements foreign key membership checks as specified
in Section 13 of the acceptance criteria.
"""

from typing import Any, Optional

import pandas as pd

from src.validation.results import ForeignKeyCheckResult


def validate_foreign_key(
    dataset_series: pd.Series,
    fk_series: pd.Series,
    name: str,
    dataset_column: str,
    fk_column: str,
    allow_nulls: bool = False,
    normalization_func: Optional[callable] = None,
) -> ForeignKeyCheckResult:
    """
    Validate that dataset values exist in the foreign key reference set.

    Args:
        dataset_series: The column from the main dataset
        fk_series: The reference column from the FK file
        name: Name of the FK check
        dataset_column: Name of dataset column
        fk_column: Name of FK column
        allow_nulls: Whether to allow null values in dataset column
        normalization_func: Optional function to normalize values before comparison

    Returns:
        ForeignKeyCheckResult
    """
    # Apply normalization if provided
    if normalization_func:
        dataset_values = dataset_series.apply(
            lambda x: normalization_func(x) if pd.notna(x) else x
        )
        fk_values = fk_series.apply(
            lambda x: normalization_func(x) if pd.notna(x) else x
        )
    else:
        dataset_values = dataset_series
        fk_values = fk_series

    # Build the FK reference set (unique non-null values)
    fk_set = set(fk_values.dropna().unique())

    # Check each dataset value
    missing_values = []
    missing_row_indices = []

    for idx, value in dataset_values.items():
        # Handle nulls
        if pd.isna(value):
            if not allow_nulls:
                missing_row_indices.append(idx)
                missing_values.append(None)
            continue

        # Check membership
        if value not in fk_set:
            missing_row_indices.append(idx)
            missing_values.append(value)

    missing_count = len(missing_row_indices)
    total_values = len(dataset_series)

    return ForeignKeyCheckResult(
        name=name,
        dataset_column=dataset_column,
        fk_column=fk_column,
        passed=missing_count == 0,
        total_values=total_values,
        missing_count=missing_count,
        missing_values=list(set(missing_values))[:100],  # Unique, limited
        missing_row_indices=missing_row_indices[:1000],  # Limited
    )


def create_normalization_function(
    trim_whitespace: bool = True,
    case: str = "none",
    null_tokens: Optional[list[str]] = None,
) -> callable:
    """
    Create a normalization function based on column configuration.

    Args:
        trim_whitespace: Whether to trim whitespace
        case: Case normalization ("none", "lower", "upper", "title")
        null_tokens: List of strings to treat as null

    Returns:
        Normalization function
    """
    null_tokens_set = set(null_tokens or [])

    def normalize(value: Any) -> Any:
        if pd.isna(value):
            return value

        str_value = str(value)

        # Trim whitespace
        if trim_whitespace:
            str_value = str_value.strip()

        # Check if it's a null token
        if str_value in null_tokens_set:
            return None

        # Apply case normalization
        if case == "lower":
            str_value = str_value.lower()
        elif case == "upper":
            str_value = str_value.upper()
        elif case == "title":
            str_value = str_value.title()

        return str_value

    return normalize


def format_fk_check_result(result: ForeignKeyCheckResult) -> str:
    """
    Format a foreign key check result for display.

    Args:
        result: The FK check result

    Returns:
        Formatted string
    """
    lines = [
        f"Foreign Key Check: {result.name}",
        f"  Dataset Column: {result.dataset_column}",
        f"  FK Column: {result.fk_column}",
        f"  Total Values: {result.total_values:,}",
        f"  Missing Count: {result.missing_count:,}",
        f"  Status: {'PASS' if result.passed else 'FAIL'}",
    ]

    if result.missing_values:
        sample_values = result.missing_values[:5]
        lines.append(f"  Sample Missing Values: {sample_values}")

    return "\n".join(lines)


def get_fk_failure_details(
    result: ForeignKeyCheckResult,
    df: pd.DataFrame,
    max_examples: int = 10,
) -> list[dict]:
    """
    Get detailed examples of FK failures for display.

    Args:
        result: The FK check result
        df: The original DataFrame
        max_examples: Maximum number of examples to return

    Returns:
        List of dicts with row details
    """
    examples = []

    for idx in result.missing_row_indices[:max_examples]:
        if idx in df.index:
            row = df.loc[idx]
            examples.append({
                "row_index": idx,
                "value": row.get(result.dataset_column),
                "row_data": row.to_dict(),
            })

    return examples
