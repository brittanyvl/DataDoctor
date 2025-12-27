"""
File readers for CSV and Excel formats.

This module provides functions to read tabular data from various file
formats with proper encoding handling and Excel sheet selection.
"""

import io
from dataclasses import dataclass
from typing import Any, BinaryIO, Optional

import pandas as pd

from src.constants import (
    CSV_ENCODING_DEFAULT,
    CSV_ENCODING_FALLBACKS,
)


@dataclass
class ReadResult:
    """Result of reading a file."""

    success: bool
    dataframe: Optional[pd.DataFrame] = None
    error_message: Optional[str] = None
    sheet_names: Optional[list[str]] = None
    encoding_used: Optional[str] = None


def read_csv(
    file_content: bytes,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
    skip_rows: int = 0,
    skip_footer_rows: int = 0,
) -> ReadResult:
    """
    Read a CSV file with encoding fallback.

    Args:
        file_content: Raw file bytes
        encoding: Specific encoding to use (or None for auto-fallback)
        delimiter: Column delimiter (or None for auto-detection)
        skip_rows: Number of rows to skip at the beginning (header row is after skipped rows)
        skip_footer_rows: Number of rows to skip at the end

    Returns:
        ReadResult with the parsed DataFrame or error
    """
    # Build list of encodings to try
    if encoding:
        encodings_to_try = [encoding]
    else:
        encodings_to_try = [CSV_ENCODING_DEFAULT] + CSV_ENCODING_FALLBACKS

    last_error = None

    for enc in encodings_to_try:
        try:
            # Create file-like object from bytes
            file_buffer = io.BytesIO(file_content)

            # Read CSV with pandas
            read_kwargs: dict[str, Any] = {
                "encoding": enc,
                "on_bad_lines": "warn",
                "dtype": str,  # Read all columns as strings initially
            }

            if delimiter:
                read_kwargs["sep"] = delimiter

            if skip_rows > 0:
                read_kwargs["skiprows"] = skip_rows

            if skip_footer_rows > 0:
                read_kwargs["skipfooter"] = skip_footer_rows
                read_kwargs["engine"] = "python"  # skipfooter requires python engine

            df = pd.read_csv(file_buffer, **read_kwargs)

            return ReadResult(
                success=True,
                dataframe=df,
                encoding_used=enc,
            )

        except UnicodeDecodeError as e:
            last_error = f"Encoding error with {enc}: {str(e)}"
            continue
        except pd.errors.ParserError as e:
            last_error = f"CSV parsing error: {str(e)}"
            break
        except Exception as e:
            last_error = f"Error reading CSV: {str(e)}"
            break

    return ReadResult(
        success=False,
        error_message=last_error or "Failed to read CSV file.",
    )


def get_excel_sheet_names(file_content: bytes, file_extension: str) -> ReadResult:
    """
    Get list of sheet names from an Excel file.

    Args:
        file_content: Raw file bytes
        file_extension: File extension (e.g., ".xlsx")

    Returns:
        ReadResult with sheet_names populated
    """
    try:
        file_buffer = io.BytesIO(file_content)

        # Select appropriate engine based on extension
        if file_extension == ".xlsb":
            engine = "pyxlsb"
        elif file_extension == ".xls":
            engine = "xlrd"
        else:
            engine = "openpyxl"

        # Use ExcelFile to get sheet names without reading data
        with pd.ExcelFile(file_buffer, engine=engine) as excel_file:
            sheet_names = excel_file.sheet_names

        return ReadResult(
            success=True,
            sheet_names=sheet_names,
        )

    except Exception as e:
        return ReadResult(
            success=False,
            error_message=f"Error reading Excel file: {str(e)}",
        )


def read_excel(
    file_content: bytes,
    file_extension: str,
    sheet_name: Optional[str] = None,
    skip_rows: int = 0,
    skip_footer_rows: int = 0,
) -> ReadResult:
    """
    Read an Excel file.

    Args:
        file_content: Raw file bytes
        file_extension: File extension (e.g., ".xlsx")
        sheet_name: Name of sheet to read (or None for first sheet)
        skip_rows: Number of rows to skip at the beginning (header row is after skipped rows)
        skip_footer_rows: Number of rows to skip at the end

    Returns:
        ReadResult with the parsed DataFrame or error
    """
    try:
        file_buffer = io.BytesIO(file_content)

        # Select appropriate engine based on extension
        if file_extension == ".xlsb":
            engine = "pyxlsb"
        elif file_extension == ".xls":
            engine = "xlrd"
        else:
            engine = "openpyxl"

        # First get sheet names
        with pd.ExcelFile(file_buffer, engine=engine) as excel_file:
            sheet_names = excel_file.sheet_names

            # Determine which sheet to read
            if sheet_name:
                if sheet_name not in sheet_names:
                    return ReadResult(
                        success=False,
                        error_message=f"Sheet '{sheet_name}' not found. "
                        f"Available sheets: {', '.join(sheet_names)}",
                        sheet_names=sheet_names,
                    )
                target_sheet = sheet_name
            else:
                # Default to first sheet
                target_sheet = sheet_names[0]

            # Build read kwargs
            read_kwargs: dict[str, Any] = {
                "sheet_name": target_sheet,
                "dtype": str,  # Read all columns as strings initially
            }

            if skip_rows > 0:
                read_kwargs["skiprows"] = skip_rows

            if skip_footer_rows > 0:
                read_kwargs["skipfooter"] = skip_footer_rows

            # Read the sheet with data_only=True equivalent
            # (openpyxl reads values, not formulas, by default with pandas)
            df = pd.read_excel(excel_file, **read_kwargs)

        return ReadResult(
            success=True,
            dataframe=df,
            sheet_names=sheet_names,
        )

    except Exception as e:
        return ReadResult(
            success=False,
            error_message=f"Error reading Excel file: {str(e)}",
        )


def read_file(
    file_content: bytes,
    filename: str,
    file_extension: str,
    sheet_name: Optional[str] = None,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
    skip_rows: int = 0,
    skip_footer_rows: int = 0,
) -> ReadResult:
    """
    Read a file based on its extension.

    This is the main entry point for file reading, which dispatches
    to the appropriate reader based on file type.

    Args:
        file_content: Raw file bytes
        filename: Original filename
        file_extension: File extension (e.g., ".csv", ".xlsx")
        sheet_name: Sheet name for Excel files
        encoding: Encoding for CSV files
        delimiter: Delimiter for CSV files
        skip_rows: Number of rows to skip at the beginning
        skip_footer_rows: Number of rows to skip at the end

    Returns:
        ReadResult with the parsed DataFrame or error
    """
    if file_extension == ".csv":
        return read_csv(
            file_content,
            encoding=encoding,
            delimiter=delimiter,
            skip_rows=skip_rows,
            skip_footer_rows=skip_footer_rows,
        )
    elif file_extension in {".xlsx", ".xls", ".xlsb"}:
        return read_excel(
            file_content,
            file_extension,
            sheet_name=sheet_name,
            skip_rows=skip_rows,
            skip_footer_rows=skip_footer_rows,
        )
    else:
        return ReadResult(
            success=False,
            error_message=f"Unsupported file extension: {file_extension}",
        )


def detect_delimiter(file_content: bytes, encoding: str = "utf-8") -> str:
    """
    Attempt to detect the delimiter in a CSV file.

    Args:
        file_content: Raw file bytes
        encoding: Encoding to use

    Returns:
        Detected delimiter (defaults to comma)
    """
    try:
        # Read first few lines
        text = file_content.decode(encoding)
        lines = text.split("\n")[:5]

        # Count occurrences of common delimiters
        delimiters = [",", ";", "\t", "|"]
        counts = {d: 0 for d in delimiters}

        for line in lines:
            for d in delimiters:
                counts[d] += line.count(d)

        # Return the most common delimiter
        max_count = max(counts.values())
        if max_count > 0:
            for d, c in counts.items():
                if c == max_count:
                    return d

        return ","

    except Exception:
        return ","


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, Optional[str]]:
    """
    Validate a loaded dataframe for basic issues.

    Args:
        df: The loaded DataFrame

    Returns:
        Tuple of (is_valid, error_message)
    """
    if df is None:
        return False, "DataFrame is None."

    if df.empty:
        return False, "The file contains no data rows."

    if len(df.columns) == 0:
        return False, "The file contains no columns."

    # Check for duplicate column names
    if len(df.columns) != len(set(df.columns)):
        duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
        unique_duplicates = list(set(duplicates))
        return (
            False,
            f"Duplicate column names found: {', '.join(unique_duplicates)}. "
            "Please ensure all column names are unique.",
        )

    return True, None


def get_dataframe_summary(df: pd.DataFrame) -> dict:
    """
    Get summary statistics for a dataframe.

    Args:
        df: The DataFrame to summarize

    Returns:
        Dictionary with summary statistics
    """
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "memory_usage_bytes": df.memory_usage(deep=True).sum(),
        "null_counts": df.isnull().sum().to_dict(),
        "total_null_count": int(df.isnull().sum().sum()),
    }
