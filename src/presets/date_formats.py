"""
Date format token mapping.

This module maps human-readable date format tokens to Python strftime
codes as specified in Section 23.2 of the acceptance criteria.
"""

import re
from datetime import datetime
from typing import Optional

import pandas as pd


# Human-readable token to strftime mapping
TOKEN_TO_STRFTIME = {
    # Year
    "YYYY": "%Y",  # 4-digit year (2025)
    "YY": "%y",    # 2-digit year (25)

    # Month
    "MM": "%m",    # 2-digit month (01-12)
    "M": "%-m",    # Month without leading zero (1-12) - may not work on Windows
    "MMM": "%b",   # Abbreviated month name (Jan)
    "MMMM": "%B",  # Full month name (January)

    # Day
    "DD": "%d",    # 2-digit day (01-31)
    "D": "%-d",    # Day without leading zero (1-31) - may not work on Windows

    # Hour
    "HH": "%H",    # 24-hour format (00-23)
    "hh": "%I",    # 12-hour format (01-12)
    "H": "%-H",    # 24-hour without leading zero
    "h": "%-I",    # 12-hour without leading zero

    # Minute
    "mm": "%M",    # Minutes (00-59)
    "m": "%-M",    # Minutes without leading zero

    # Second
    "ss": "%S",    # Seconds (00-59)
    "s": "%-S",    # Seconds without leading zero

    # AM/PM
    "A": "%p",     # AM/PM
    "a": "%p",     # am/pm (lowercase handled separately)

    # Timezone
    "Z": "%z",     # Timezone offset (+0000)
    "ZZ": "%z",    # Timezone offset with colon (+00:00)

    # Day of week
    "ddd": "%a",   # Abbreviated weekday (Mon)
    "dddd": "%A",  # Full weekday (Monday)
}


# Common date format patterns (human-readable to strftime)
COMMON_DATE_FORMATS = {
    "YYYY-MM-DD": "%Y-%m-%d",
    "YYYY/MM/DD": "%Y/%m/%d",
    "YYYYMMDD": "%Y%m%d",
    "MM/DD/YYYY": "%m/%d/%Y",
    "DD/MM/YYYY": "%d/%m/%Y",
    "MM-DD-YYYY": "%m-%d-%Y",
    "DD-MM-YYYY": "%d-%m-%Y",
    "DD-MMM-YYYY": "%d-%b-%Y",
    "MMM DD, YYYY": "%b %d, %Y",
    "MMMM DD, YYYY": "%B %d, %Y",
    "YYYY-MM-DD HH:mm:ss": "%Y-%m-%d %H:%M:%S",
    "YYYY-MM-DDTHH:mm:ssZ": "%Y-%m-%dT%H:%M:%SZ",
    "MM/DD/YY": "%m/%d/%y",
    "DD/MM/YY": "%d/%m/%y",
    "MMDDYY": "%m%d%y",
    "DDMMYY": "%d%m%y",
}


def human_format_to_strftime(human_format: str) -> str:
    """
    Convert a human-readable date format to Python strftime format.

    Args:
        human_format: Format string like "YYYY-MM-DD"

    Returns:
        strftime format string like "%Y-%m-%d"
    """
    # First check if it's a known common format
    if human_format in COMMON_DATE_FORMATS:
        return COMMON_DATE_FORMATS[human_format]

    # Otherwise, do token replacement
    # Sort tokens by length (longest first) to avoid partial replacements
    result = human_format
    sorted_tokens = sorted(TOKEN_TO_STRFTIME.keys(), key=len, reverse=True)

    for token in sorted_tokens:
        result = result.replace(token, TOKEN_TO_STRFTIME[token])

    return result


def strftime_to_human_format(strftime_format: str) -> str:
    """
    Convert a strftime format to human-readable format.

    Args:
        strftime_format: Format string like "%Y-%m-%d"

    Returns:
        Human-readable format string like "YYYY-MM-DD"
    """
    # Reverse mapping
    strftime_to_token = {v: k for k, v in TOKEN_TO_STRFTIME.items()}

    result = strftime_format
    # Sort by length to handle longer patterns first
    sorted_strftime = sorted(strftime_to_token.keys(), key=len, reverse=True)

    for strftime_code in sorted_strftime:
        result = result.replace(strftime_code, strftime_to_token[strftime_code])

    return result


def parse_date_with_format(
    value: str,
    human_format: str,
) -> tuple[Optional[datetime], Optional[str]]:
    """
    Parse a date string using a human-readable format.

    Args:
        value: The date string to parse
        human_format: The expected format (e.g., "YYYY-MM-DD")

    Returns:
        Tuple of (parsed_datetime, error_message)
    """
    strftime_format = human_format_to_strftime(human_format)

    try:
        parsed = datetime.strptime(value.strip(), strftime_format)
        return parsed, None
    except ValueError as e:
        return None, f"Does not match format {human_format}: {str(e)}"


def format_date(
    dt: datetime,
    human_format: str,
) -> str:
    """
    Format a datetime object using a human-readable format.

    Args:
        dt: The datetime to format
        human_format: The target format (e.g., "YYYY-MM-DD")

    Returns:
        Formatted date string
    """
    strftime_format = human_format_to_strftime(human_format)
    return dt.strftime(strftime_format)


def parse_excel_serial_date(
    value: float,
    date_system: str = "1900",
) -> Optional[datetime]:
    """
    Parse an Excel serial date number.

    Args:
        value: The serial date number
        date_system: "1900" (Windows) or "1904" (Mac)

    Returns:
        Parsed datetime or None
    """
    try:
        if date_system == "1904":
            # Mac Excel uses 1904-01-01 as day 0
            base = pd.Timestamp("1904-01-01")
        else:
            # Windows Excel uses 1899-12-30 as day 0 (due to Lotus 123 bug)
            base = pd.Timestamp("1899-12-30")

        result = base + pd.Timedelta(days=value)
        return result.to_pydatetime()
    except Exception:
        return None


def try_parse_date_robust(
    value: str,
    accepted_formats: list[str],
    excel_serial_enabled: bool = False,
) -> tuple[Optional[datetime], Optional[str]]:
    """
    Try to parse a date using multiple accepted formats.

    Args:
        value: The date string to parse
        accepted_formats: List of human-readable formats to try
        excel_serial_enabled: Whether to try Excel serial date parsing

    Returns:
        Tuple of (parsed_datetime, matched_format) or (None, None) if no match
    """
    value = str(value).strip()

    # Try Excel serial date first if enabled
    if excel_serial_enabled:
        try:
            serial_value = float(value)
            # Excel serial dates are typically in range 1-2958465 (1900-9999)
            if 1 <= serial_value <= 2958465:
                parsed = parse_excel_serial_date(serial_value)
                if parsed:
                    return parsed, "EXCEL_SERIAL"
        except ValueError:
            pass

    # Try each format in order
    for fmt in accepted_formats:
        parsed, error = parse_date_with_format(value, fmt)
        if parsed:
            return parsed, fmt

    return None, None


def get_common_format_names() -> list[str]:
    """
    Get list of common format names for UI display.

    Returns:
        List of human-readable format strings
    """
    return list(COMMON_DATE_FORMATS.keys())


def get_format_examples() -> list[dict]:
    """
    Get examples for each common format.

    Returns:
        List of dicts with format and example
    """
    now = datetime(2025, 1, 7, 14, 32, 10)
    result = []

    for human_format, strftime_format in COMMON_DATE_FORMATS.items():
        try:
            example = now.strftime(strftime_format)
            result.append({
                "format": human_format,
                "example": example,
            })
        except Exception:
            result.append({
                "format": human_format,
                "example": "(example unavailable)",
            })

    return result


def validate_date_format_string(human_format: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a date format string is valid.

    Args:
        human_format: The format string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    strftime_format = human_format_to_strftime(human_format)

    # Try to format a test date
    test_date = datetime(2025, 1, 7, 14, 32, 10)
    try:
        test_date.strftime(strftime_format)
        return True, None
    except Exception as e:
        return False, f"Invalid format: {str(e)}"


def coerce_date_to_format(
    value: str,
    target_format: str,
    accepted_input_formats: list[str],
    excel_serial_enabled: bool = False,
) -> tuple[Optional[str], Optional[str]]:
    """
    Attempt to coerce a date value to the target format.

    Args:
        value: The date string to coerce
        target_format: The target format (human-readable)
        accepted_input_formats: List of formats to try for parsing
        excel_serial_enabled: Whether to try Excel serial dates

    Returns:
        Tuple of (coerced_value, error_message)
        If successful, error_message is None
    """
    # Try to parse with any accepted format
    parsed, matched_format = try_parse_date_robust(
        value,
        accepted_input_formats,
        excel_serial_enabled,
    )

    if parsed:
        # Format to target
        result = format_date(parsed, target_format)
        return result, None
    else:
        return None, f"Could not parse '{value}' with any accepted format"
