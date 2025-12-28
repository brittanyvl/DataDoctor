"""
Remediation transformer implementations.

This module implements all remediation actions as specified
in Section 21.3.4 of the acceptance criteria.
"""

import re
from typing import Any, Callable, Optional

import pandas as pd

from src.constants import (
    BOOLEAN_FALSE_TOKENS,
    BOOLEAN_TRUE_TOKENS,
    DEFAULT_NULL_TOKENS,
)
from src.presets.date_formats import coerce_date_to_format


def transform_trim_whitespace(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Trim leading and trailing whitespace from string values.

    Args:
        series: The column data
        params: Additional parameters (unused)

    Returns:
        Transformed series
    """
    return series.apply(
        lambda x: str(x).strip() if pd.notna(x) else x
    )


def transform_standardize_nulls(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Standardize various null representations to actual nulls.

    Args:
        series: The column data
        params: Dict with optional 'null_tokens' list

    Returns:
        Transformed series
    """
    params = params or {}
    null_tokens = set(params.get("null_tokens", DEFAULT_NULL_TOKENS))

    def standardize(value: Any) -> Any:
        if pd.isna(value):
            return None
        str_value = str(value).strip()
        if str_value in null_tokens:
            return None
        return value

    return series.apply(standardize)


def transform_normalize_case(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Normalize string case.

    Args:
        series: The column data
        params: Dict with 'case' ("lower", "upper", "title")

    Returns:
        Transformed series
    """
    params = params or {}
    case = params.get("case", "lower")

    def normalize(value: Any) -> Any:
        if pd.isna(value):
            return value
        str_value = str(value)
        if case == "lower":
            return str_value.lower()
        elif case == "upper":
            return str_value.upper()
        elif case == "title":
            return str_value.title()
        return str_value

    return series.apply(normalize)


def transform_remove_non_printable(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Remove non-printable characters from string values.

    Args:
        series: The column data
        params: Additional parameters (unused)

    Returns:
        Transformed series
    """
    def remove_non_printable(value: Any) -> Any:
        if pd.isna(value):
            return value
        str_value = str(value)
        return "".join(c for c in str_value if c.isprintable() or c in "\t\n\r")

    return series.apply(remove_non_printable)


def transform_numeric_cleanup(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Clean up numeric values (remove formatting, handle negatives).

    Args:
        series: The column data
        params: Dict with options:
            - remove_commas: bool
            - remove_currency_symbols: bool
            - parentheses_as_negative: bool
            - on_parse_error: "set_null" or "keep"

    Returns:
        Transformed series
    """
    params = params or {}
    remove_commas = params.get("remove_commas", True)
    remove_currency = params.get("remove_currency_symbols", True)
    parentheses_negative = params.get("parentheses_as_negative", True)
    on_error = params.get("on_parse_error", "keep")

    def cleanup(value: Any) -> Any:
        if pd.isna(value):
            return value

        str_value = str(value).strip()

        # Handle parentheses as negative
        if parentheses_negative and str_value.startswith("(") and str_value.endswith(")"):
            str_value = "-" + str_value[1:-1]

        # Remove currency symbols
        if remove_currency:
            str_value = re.sub(r"[$\u00A3\u20AC\u00A5]", "", str_value)

        # Remove commas
        if remove_commas:
            str_value = str_value.replace(",", "")

        # Try to parse as number
        try:
            # Try integer first
            if "." not in str_value:
                return int(str_value)
            return float(str_value)
        except ValueError:
            if on_error == "set_null":
                return None
            return value

    return series.apply(cleanup)


def transform_boolean_normalization(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Normalize boolean representations to True/False.

    Args:
        series: The column data
        params: Dict with optional custom mappings

    Returns:
        Transformed series
    """
    params = params or {}
    true_tokens = set(params.get("true_tokens", BOOLEAN_TRUE_TOKENS))
    false_tokens = set(params.get("false_tokens", BOOLEAN_FALSE_TOKENS))

    def normalize(value: Any) -> Any:
        if pd.isna(value):
            return value

        str_value = str(value).strip().lower()

        if str_value in true_tokens:
            return True
        elif str_value in false_tokens:
            return False
        else:
            return value  # Keep original if not recognized

    return series.apply(normalize)


def transform_date_coerce(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Coerce date values to a target format.

    Args:
        series: The column data
        params: Dict with:
            - target_format: target date format
            - accepted_input_formats: list of input formats to try
            - excel_serial_enabled: bool
            - on_parse_error: "set_null" or "keep" (default: "keep")

    Returns:
        Transformed series
    """
    params = params or {}
    target_format = params.get("target_format", "YYYY-MM-DD")
    # Default to common formats if not specified
    default_formats = [
        "YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "YYYY/MM/DD",
        "MM-DD-YYYY", "DD-MM-YYYY", "YYYYMMDD",
        "MM/DD/YY", "DD/MM/YY", "MMM DD, YYYY", "MMMM DD, YYYY",
        "DD-MMM-YYYY",
    ]
    accepted_formats = params.get("accepted_input_formats", default_formats)
    excel_serial = params.get("excel_serial_enabled", False)
    on_error = params.get("on_parse_error", "keep")

    def coerce(value: Any) -> Any:
        if pd.isna(value):
            return value

        result, error = coerce_date_to_format(
            str(value),
            target_format,
            accepted_formats,
            excel_serial,
        )

        if result is not None:
            return result
        elif on_error == "set_null":
            return None  # Invalid date becomes null
        else:
            return value  # Keep original

    return series.apply(coerce)


def transform_categorical_standardize(
    series: pd.Series,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Standardize categorical values using a mapping.

    Args:
        series: The column data
        params: Dict with:
            - mapping: dict mapping input values to standardized values
            - case_insensitive: bool

    Returns:
        Transformed series
    """
    params = params or {}
    mapping = params.get("mapping", {})
    case_insensitive = params.get("case_insensitive", True)

    # Build normalized mapping
    if case_insensitive:
        normalized_mapping = {
            str(k).lower().strip(): v for k, v in mapping.items()
        }
    else:
        normalized_mapping = {
            str(k).strip(): v for k, v in mapping.items()
        }

    def standardize(value: Any) -> Any:
        if pd.isna(value):
            return value

        str_value = str(value).strip()
        lookup_value = str_value.lower() if case_insensitive else str_value

        if lookup_value in normalized_mapping:
            return normalized_mapping[lookup_value]

        return value

    return series.apply(standardize)


def transform_split_column(
    df: pd.DataFrame,
    column_name: str,
    params: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Split a column into multiple columns.

    Args:
        df: The DataFrame
        column_name: Column to split
        params: Dict with:
            - delimiter: string delimiter
            - new_column_names: list of names for new columns
            - max_splits: maximum number of splits

    Returns:
        DataFrame with new columns added
    """
    params = params or {}
    delimiter = params.get("delimiter", ",")
    new_names = params.get("new_column_names", [])
    max_splits = params.get("max_splits", -1)

    if column_name not in df.columns:
        return df

    result_df = df.copy()

    # Split the column
    split_data = result_df[column_name].str.split(delimiter, expand=True, n=max_splits if max_splits > 0 else None)

    # Assign column names
    for i, col in enumerate(split_data.columns):
        if i < len(new_names):
            new_col_name = new_names[i]
        else:
            new_col_name = f"{column_name}_part_{i + 1}"

        result_df[new_col_name] = split_data[col]

    return result_df


def transform_custom_calculation(
    df: pd.DataFrame,
    column_name: str,
    params: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Create a calculated column.

    Note: This is limited to simple operations for security.
    No eval() or exec() is used.

    Args:
        df: The DataFrame
        column_name: Name for the new column
        params: Dict with:
            - operation: "concat", "add", "subtract", "multiply", "divide"
            - operand_columns: list of column names
            - operand_values: list of literal values
            - separator: for concat operations

    Returns:
        DataFrame with new column
    """
    params = params or {}
    operation = params.get("operation", "concat")
    operand_columns = params.get("operand_columns", [])
    separator = params.get("separator", " ")

    result_df = df.copy()

    if not operand_columns:
        return result_df

    # Verify columns exist
    missing = [c for c in operand_columns if c not in df.columns]
    if missing:
        return result_df

    if operation == "concat":
        # String concatenation
        result_df[column_name] = df[operand_columns[0]].astype(str)
        for col in operand_columns[1:]:
            result_df[column_name] = (
                result_df[column_name] + separator + df[col].astype(str)
            )

    elif operation in ["add", "subtract", "multiply", "divide"]:
        # Numeric operations
        try:
            numeric_cols = [pd.to_numeric(df[c], errors="coerce") for c in operand_columns]

            if operation == "add":
                result = numeric_cols[0]
                for col in numeric_cols[1:]:
                    result = result + col
            elif operation == "subtract":
                result = numeric_cols[0]
                for col in numeric_cols[1:]:
                    result = result - col
            elif operation == "multiply":
                result = numeric_cols[0]
                for col in numeric_cols[1:]:
                    result = result * col
            elif operation == "divide":
                result = numeric_cols[0]
                for col in numeric_cols[1:]:
                    result = result / col.replace(0, float("nan"))

            result_df[column_name] = result
        except Exception:
            pass

    return result_df


# Transformer registry for column-level transforms
COLUMN_TRANSFORMERS: dict[str, Callable] = {
    "trim_whitespace": transform_trim_whitespace,
    "standardize_nulls": transform_standardize_nulls,
    "normalize_case": transform_normalize_case,
    "remove_non_printable": transform_remove_non_printable,
    "numeric_cleanup": transform_numeric_cleanup,
    "boolean_normalization": transform_boolean_normalization,
    "date_coerce": transform_date_coerce,
    "categorical_standardize": transform_categorical_standardize,
}

# Transformer registry for dataframe-level transforms
DATAFRAME_TRANSFORMERS: dict[str, Callable] = {
    "split_column": transform_split_column,
    "custom_calculation": transform_custom_calculation,
}


def apply_column_remediation(
    series: pd.Series,
    remediation_type: str,
    params: Optional[dict] = None,
) -> pd.Series:
    """
    Apply a remediation transformation to a column.

    Args:
        series: The column data
        remediation_type: Type of remediation
        params: Remediation parameters

    Returns:
        Transformed series
    """
    transformer = COLUMN_TRANSFORMERS.get(remediation_type)

    if transformer is None:
        return series

    return transformer(series, params)


def apply_dataframe_remediation(
    df: pd.DataFrame,
    column_name: str,
    remediation_type: str,
    params: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Apply a remediation transformation that affects the DataFrame.

    Args:
        df: The DataFrame
        column_name: Target column name
        remediation_type: Type of remediation
        params: Remediation parameters

    Returns:
        Transformed DataFrame
    """
    transformer = DATAFRAME_TRANSFORMERS.get(remediation_type)

    if transformer is None:
        return df

    return transformer(df, column_name, params)


def deduplicate_rows(
    df: pd.DataFrame,
    params: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Remove duplicate rows from a DataFrame.

    Args:
        df: The DataFrame
        params: Dict with optional:
            - subset: columns to consider for duplicates
            - keep: "first", "last", or False

    Returns:
        DataFrame with duplicates removed
    """
    params = params or {}
    subset = params.get("subset")
    keep = params.get("keep", "first")

    return df.drop_duplicates(subset=subset, keep=keep)
