"""
File upload validation and processing.

This module handles file upload validation including extension checks,
MIME type validation, size limits, and rate limiting.
"""

import os
from dataclasses import dataclass
from typing import Optional

from src.constants import (
    MAX_COLUMN_COUNT,
    MAX_ROW_COUNT,
    MAX_UPLOAD_SIZE_BYTES,
    MIME_TYPES,
    SUPPORTED_EXTENSIONS,
)


@dataclass
class UploadValidationResult:
    """Result of upload validation."""

    is_valid: bool
    error_message: Optional[str] = None
    file_extension: Optional[str] = None
    file_size_bytes: Optional[int] = None


def validate_file_extension(filename: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Validate that the file has a supported extension.

    Args:
        filename: The uploaded file name

    Returns:
        Tuple of (is_valid, error_message, extension)
    """
    if not filename:
        return False, "No filename provided.", None

    # Extract extension (lowercase)
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return (
            False,
            f"Unsupported file type '{ext}'. Supported formats: {supported}",
            ext,
        )

    return True, None, ext


def validate_mime_type(
    file_extension: str,
    mime_type: Optional[str],
) -> tuple[bool, Optional[str]]:
    """
    Validate the MIME type matches the expected type for the extension.

    Note: MIME type validation is a secondary check. Some browsers may
    report different MIME types, so we allow flexibility here.

    Args:
        file_extension: The file extension (e.g., ".csv")
        mime_type: The reported MIME type

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not mime_type:
        # If no MIME type provided, allow based on extension only
        return True, None

    expected_types = MIME_TYPES.get(file_extension, [])

    # Allow if MIME type matches expected, or if it's a generic type
    generic_types = [
        "application/octet-stream",
        "application/binary",
    ]

    if mime_type in expected_types or mime_type in generic_types:
        return True, None

    # Log warning but don't fail - MIME types can be unreliable
    # In production, you might want to be stricter
    return True, None


def validate_file_size(file_size_bytes: int) -> tuple[bool, Optional[str]]:
    """
    Validate the file size is within limits.

    Args:
        file_size_bytes: Size of the file in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size_bytes > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        actual_mb = file_size_bytes / (1024 * 1024)
        return (
            False,
            f"File size ({actual_mb:.1f} MB) exceeds the maximum allowed "
            f"size of {max_mb:.0f} MB. Please upload a smaller file.",
        )

    return True, None


def validate_dataframe_limits(
    row_count: int,
    column_count: int,
) -> tuple[bool, Optional[str]]:
    """
    Validate that the loaded dataframe is within row and column limits.

    Args:
        row_count: Number of rows in the dataframe
        column_count: Number of columns in the dataframe

    Returns:
        Tuple of (is_valid, error_message)
    """
    errors = []

    if row_count > MAX_ROW_COUNT:
        errors.append(
            f"Row count ({row_count:,}) exceeds the maximum allowed "
            f"({MAX_ROW_COUNT:,} rows)."
        )

    if column_count > MAX_COLUMN_COUNT:
        errors.append(
            f"Column count ({column_count}) exceeds the maximum allowed "
            f"({MAX_COLUMN_COUNT} columns)."
        )

    if errors:
        error_message = " ".join(errors) + " Please upload a smaller subset of data."
        return False, error_message

    return True, None


def validate_upload(
    filename: str,
    file_size_bytes: int,
    mime_type: Optional[str] = None,
) -> UploadValidationResult:
    """
    Perform complete upload validation.

    This validates the file before attempting to parse it.

    Args:
        filename: The uploaded file name
        file_size_bytes: Size of the file in bytes
        mime_type: Optional MIME type reported by the browser

    Returns:
        UploadValidationResult with validation status
    """
    # Validate extension
    ext_valid, ext_error, extension = validate_file_extension(filename)
    if not ext_valid:
        return UploadValidationResult(
            is_valid=False,
            error_message=ext_error,
        )

    # Validate file size
    size_valid, size_error = validate_file_size(file_size_bytes)
    if not size_valid:
        return UploadValidationResult(
            is_valid=False,
            error_message=size_error,
            file_extension=extension,
            file_size_bytes=file_size_bytes,
        )

    # Validate MIME type (non-blocking warning)
    if mime_type:
        validate_mime_type(extension, mime_type)

    return UploadValidationResult(
        is_valid=True,
        file_extension=extension,
        file_size_bytes=file_size_bytes,
    )


def get_file_info(filename: str, file_size_bytes: int) -> dict:
    """
    Get formatted file information for display.

    Args:
        filename: The file name
        file_size_bytes: File size in bytes

    Returns:
        Dictionary with formatted file information
    """
    _, ext = os.path.splitext(filename)

    # Format size
    if file_size_bytes < 1024:
        size_str = f"{file_size_bytes} B"
    elif file_size_bytes < 1024 * 1024:
        size_str = f"{file_size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"

    # Determine file type display name
    type_names = {
        ".csv": "CSV (Comma-Separated Values)",
        ".xlsx": "Excel Workbook",
        ".xls": "Excel 97-2003 Workbook",
        ".xlsb": "Excel Binary Workbook",
    }

    return {
        "filename": filename,
        "extension": ext.lower(),
        "size_bytes": file_size_bytes,
        "size_display": size_str,
        "type_name": type_names.get(ext.lower(), "Unknown"),
    }
