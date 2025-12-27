"""
Safe file export with formula injection prevention.

This module provides functions to export DataFrames to CSV and Excel
formats with proper escaping to prevent formula injection attacks.
"""

import io
from typing import Any, Optional

import pandas as pd

from src.constants import FORMULA_INJECTION_CHARS


def escape_formula_injection(value: Any) -> Any:
    """
    Escape values that could be interpreted as formulas in spreadsheet applications.

    Values starting with =, +, -, or @ are prefixed with a single quote
    to prevent formula execution.

    Args:
        value: The value to escape

    Returns:
        Escaped value (string values only; others returned unchanged)
    """
    if not isinstance(value, str):
        return value

    if value and value[0] in FORMULA_INJECTION_CHARS:
        return "'" + value

    return value


def escape_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a copy of a DataFrame with formula injection prevention.

    Args:
        df: The DataFrame to escape

    Returns:
        New DataFrame with escaped string values
    """
    # Create a copy to avoid modifying the original
    escaped_df = df.copy()

    # Apply escaping to all string columns
    for col in escaped_df.columns:
        if escaped_df[col].dtype == object:  # String columns
            escaped_df[col] = escaped_df[col].apply(escape_formula_injection)

    return escaped_df


def export_to_csv(
    df: pd.DataFrame,
    escape_formulas: bool = True,
    encoding: str = "utf-8",
    index: bool = False,
) -> bytes:
    """
    Export a DataFrame to CSV format.

    Args:
        df: The DataFrame to export
        escape_formulas: Whether to escape formula injection characters
        encoding: Output encoding
        index: Whether to include the index column

    Returns:
        CSV content as bytes
    """
    # Apply formula escaping if requested
    if escape_formulas:
        df_to_export = escape_dataframe(df)
    else:
        df_to_export = df

    # Create buffer and write CSV
    buffer = io.StringIO()
    df_to_export.to_csv(buffer, index=index, encoding=encoding)

    return buffer.getvalue().encode(encoding)


def export_to_excel(
    df: pd.DataFrame,
    escape_formulas: bool = True,
    sheet_name: str = "Sheet1",
    index: bool = False,
) -> bytes:
    """
    Export a DataFrame to Excel format (.xlsx).

    Args:
        df: The DataFrame to export
        escape_formulas: Whether to escape formula injection characters
        sheet_name: Name for the worksheet
        index: Whether to include the index column

    Returns:
        Excel file content as bytes
    """
    # Apply formula escaping if requested
    if escape_formulas:
        df_to_export = escape_dataframe(df)
    else:
        df_to_export = df

    # Create buffer and write Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_to_export.to_excel(writer, sheet_name=sheet_name, index=index)

    return buffer.getvalue()


def export_dataframe(
    df: pd.DataFrame,
    output_format: str = "csv",
    escape_formulas: bool = True,
    sheet_name: str = "Sheet1",
    encoding: str = "utf-8",
    index: bool = False,
) -> tuple[bytes, str, str]:
    """
    Export a DataFrame to the specified format.

    Args:
        df: The DataFrame to export
        output_format: "csv" or "xlsx"
        escape_formulas: Whether to escape formula injection characters
        sheet_name: Sheet name for Excel output
        encoding: Encoding for CSV output
        index: Whether to include index column

    Returns:
        Tuple of (file_bytes, filename_extension, mime_type)
    """
    if output_format.lower() == "xlsx":
        content = export_to_excel(
            df,
            escape_formulas=escape_formulas,
            sheet_name=sheet_name,
            index=index,
        )
        return (
            content,
            ".xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        content = export_to_csv(
            df,
            escape_formulas=escape_formulas,
            encoding=encoding,
            index=index,
        )
        return content, ".csv", "text/csv"


def export_multiple_sheets(
    dataframes: dict[str, pd.DataFrame],
    escape_formulas: bool = True,
    index: bool = False,
) -> bytes:
    """
    Export multiple DataFrames to a single Excel file with multiple sheets.

    Args:
        dataframes: Dictionary mapping sheet names to DataFrames
        escape_formulas: Whether to escape formula injection characters
        index: Whether to include index columns

    Returns:
        Excel file content as bytes
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in dataframes.items():
            # Apply formula escaping if requested
            if escape_formulas:
                df_to_export = escape_dataframe(df)
            else:
                df_to_export = df

            # Truncate sheet name to Excel's 31 character limit
            safe_sheet_name = sheet_name[:31]

            df_to_export.to_excel(writer, sheet_name=safe_sheet_name, index=index)

    return buffer.getvalue()


def get_export_filename(
    base_name: str,
    suffix: str,
    extension: str,
) -> str:
    """
    Generate a filename for export.

    Args:
        base_name: Original file name (without extension)
        suffix: Suffix to add (e.g., "_cleaned", "_report")
        extension: File extension (e.g., ".csv", ".xlsx")

    Returns:
        Generated filename
    """
    # Remove any existing extension from base_name
    if "." in base_name:
        base_name = base_name.rsplit(".", 1)[0]

    return f"{base_name}{suffix}{extension}"


def prepare_quarantine_export(
    df: pd.DataFrame,
    quarantine_rows: pd.DataFrame,
    quarantine_name: str,
) -> dict[str, pd.DataFrame]:
    """
    Prepare data for export with quarantined rows separated.

    Args:
        df: The main DataFrame (with quarantined rows removed)
        quarantine_rows: DataFrame containing quarantined rows
        quarantine_name: Name for the quarantine sheet/file

    Returns:
        Dictionary with "clean" and quarantine sheet names mapped to DataFrames
    """
    result = {"clean_data": df}

    if len(quarantine_rows) > 0:
        result[quarantine_name] = quarantine_rows

    return result
