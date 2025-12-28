"""
Column-level test implementations.

This module implements all column-level validation tests as specified
in Section 12.1 of the acceptance criteria.
"""

from typing import Any, Callable, Optional

import pandas as pd

from src.constants import (
    BOOLEAN_FALSE_TOKENS,
    BOOLEAN_TRUE_TOKENS,
)
from src.presets.date_formats import (
    parse_date_with_format,
    try_parse_date_robust,
)
from src.presets.enums import get_enum_preset, validate_with_custom_enum
from src.presets.patterns import (
    build_pattern_from_builder,
    get_preset_pattern,
    validate_with_custom_pattern,
    validate_with_preset,
)
from src.validation.results import ColumnTestResult


def test_not_null(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that values are not null.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Additional parameters (unused)

    Returns:
        ColumnTestResult
    """
    null_mask = series.isna()
    failed_indices = series.index[null_mask].tolist()
    failed_count = len(failed_indices)

    return ColumnTestResult(
        column_name=column_name,
        test_type="not_null",
        severity=severity,
        passed=failed_count == 0,
        total_values=len(series),
        failed_count=failed_count,
        failed_indices=failed_indices[:100],  # Limit to first 100
        failed_values=[None] * min(failed_count, 100),
        error_details=[f"Row {i}: value is null" for i in failed_indices[:10]],
    )


def test_type_conformance(
    series: pd.Series,
    column_name: str,
    data_type: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that values conform to the declared data type.

    Args:
        series: The column data
        column_name: Column name
        data_type: Expected data type
        severity: Test severity
        params: Additional parameters

    Returns:
        ColumnTestResult
    """
    failed_indices = []
    failed_values = []
    error_details = []

    for idx, value in series.items():
        if pd.isna(value):
            continue  # Skip nulls (handled by not_null test)

        is_valid = _check_type_conformance(value, data_type)
        if not is_valid:
            failed_indices.append(idx)
            failed_values.append(value)
            if len(error_details) < 10:
                error_details.append(
                    f"Row {idx}: '{value}' is not a valid {data_type}"
                )

    return ColumnTestResult(
        column_name=column_name,
        test_type="type_conformance",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def _check_type_conformance(value: Any, data_type: str) -> bool:
    """Check if a value conforms to a data type."""
    str_value = str(value).strip()

    if data_type == "string":
        return True  # Any value is a valid string

    elif data_type == "integer":
        try:
            # Remove commas
            cleaned = str_value.replace(",", "")
            int(cleaned)
            return True
        except ValueError:
            return False

    elif data_type == "float":
        try:
            # Remove commas and currency symbols
            cleaned = str_value.replace(",", "").replace("$", "")
            float(cleaned)
            return True
        except ValueError:
            return False

    elif data_type == "boolean":
        lower_val = str_value.lower()
        return lower_val in BOOLEAN_TRUE_TOKENS or lower_val in BOOLEAN_FALSE_TOKENS

    elif data_type == "date":
        # Try common date formats
        try:
            pd.to_datetime(str_value)
            return True
        except Exception:
            return False

    elif data_type == "timestamp":
        try:
            pd.to_datetime(str_value)
            return True
        except Exception:
            return False

    return True


def test_range(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that numeric values are within a specified range.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with 'min' and/or 'max' values

    Returns:
        ColumnTestResult
    """
    params = params or {}
    min_val = params.get("min")
    max_val = params.get("max")

    failed_indices = []
    failed_values = []
    error_details = []

    for idx, value in series.items():
        if pd.isna(value):
            continue

        try:
            # Strip common numeric punctuation for validation (%, $, commas)
            # This allows validation of "15%" as 15, "$100" as 100, etc.
            clean_value = str(value).replace(",", "").replace("$", "").replace("%", "")
            num_value = float(clean_value)

            if min_val is not None and num_value < min_val:
                failed_indices.append(idx)
                failed_values.append(value)
                if len(error_details) < 10:
                    error_details.append(
                        f"Row {idx}: {value} is below minimum {min_val}"
                    )
            elif max_val is not None and num_value > max_val:
                failed_indices.append(idx)
                failed_values.append(value)
                if len(error_details) < 10:
                    error_details.append(
                        f"Row {idx}: {value} is above maximum {max_val}"
                    )
        except ValueError:
            # Not a valid number - skip (handled by type_conformance)
            pass

    return ColumnTestResult(
        column_name=column_name,
        test_type="range",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def test_length(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that string values are within a specified length range.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with 'min' and/or 'max' length values

    Returns:
        ColumnTestResult
    """
    params = params or {}
    min_len = params.get("min")
    max_len = params.get("max")

    failed_indices = []
    failed_values = []
    error_details = []

    for idx, value in series.items():
        if pd.isna(value):
            continue

        str_len = len(str(value))

        if min_len is not None and str_len < min_len:
            failed_indices.append(idx)
            failed_values.append(value)
            if len(error_details) < 10:
                error_details.append(
                    f"Row {idx}: length {str_len} is below minimum {min_len}"
                )
        elif max_len is not None and str_len > max_len:
            failed_indices.append(idx)
            failed_values.append(value)
            if len(error_details) < 10:
                error_details.append(
                    f"Row {idx}: length {str_len} is above maximum {max_len}"
                )

    return ColumnTestResult(
        column_name=column_name,
        test_type="length",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def test_enum(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that values are within an allowed set.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with 'allowed_values' list or 'preset' name,
                and optional 'case_insensitive' boolean

    Returns:
        ColumnTestResult
    """
    params = params or {}
    allowed_values = params.get("allowed_values", [])
    preset = params.get("preset")
    case_insensitive = params.get("case_insensitive", True)

    # Get preset values if specified
    if preset:
        preset_values = get_enum_preset(preset)
        if preset_values:
            allowed_values = list(preset_values)

    failed_indices = []
    failed_values = []
    error_details = []

    for idx, value in series.items():
        if pd.isna(value):
            continue

        is_valid = validate_with_custom_enum(
            str(value),
            allowed_values,
            case_insensitive,
        )

        if not is_valid:
            failed_indices.append(idx)
            failed_values.append(value)
            if len(error_details) < 10:
                error_details.append(
                    f"Row {idx}: '{value}' is not in allowed values"
                )

    return ColumnTestResult(
        column_name=column_name,
        test_type="enum",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def test_uniqueness(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that values are unique.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with optional 'allow_nulls' boolean

    Returns:
        ColumnTestResult
    """
    params = params or {}
    allow_nulls = params.get("allow_nulls", True)

    # Handle nulls
    if allow_nulls:
        check_series = series.dropna()
    else:
        check_series = series

    # Find duplicates
    duplicated = check_series.duplicated(keep=False)
    failed_indices = check_series.index[duplicated].tolist()
    failed_values = check_series[duplicated].tolist()

    # Get unique duplicate values for error details
    unique_duplicates = list(set(failed_values))[:10]
    error_details = [
        f"Value '{v}' appears multiple times" for v in unique_duplicates
    ]

    return ColumnTestResult(
        column_name=column_name,
        test_type="uniqueness",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def test_monotonic(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that values are monotonically increasing (or staying the same).

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with optional 'direction' ("increasing" or "decreasing")

    Returns:
        ColumnTestResult
    """
    params = params or {}
    direction = params.get("direction", "increasing")

    failed_indices = []
    failed_values = []
    error_details = []

    # Drop nulls for comparison
    non_null = series.dropna()

    if len(non_null) < 2:
        # Not enough values to check monotonicity
        return ColumnTestResult(
            column_name=column_name,
            test_type="monotonic",
            severity=severity,
            passed=True,
            total_values=len(series),
            failed_count=0,
            warning_message="Not enough non-null values to check monotonicity",
        )

    prev_value = None
    for idx, value in non_null.items():
        if prev_value is not None:
            try:
                # Try numeric comparison first
                curr_num = float(str(value).replace(",", ""))
                prev_num = float(str(prev_value).replace(",", ""))

                if direction == "increasing":
                    if curr_num < prev_num:
                        failed_indices.append(idx)
                        failed_values.append(value)
                        if len(error_details) < 10:
                            error_details.append(
                                f"Row {idx}: {value} is less than previous {prev_value}"
                            )
                else:  # decreasing
                    if curr_num > prev_num:
                        failed_indices.append(idx)
                        failed_values.append(value)
                        if len(error_details) < 10:
                            error_details.append(
                                f"Row {idx}: {value} is greater than previous {prev_value}"
                            )
            except ValueError:
                # Fall back to string comparison
                if direction == "increasing":
                    if str(value) < str(prev_value):
                        failed_indices.append(idx)
                        failed_values.append(value)
                else:
                    if str(value) > str(prev_value):
                        failed_indices.append(idx)
                        failed_values.append(value)

        prev_value = value

    return ColumnTestResult(
        column_name=column_name,
        test_type="monotonic",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def test_cardinality_warning(
    series: pd.Series,
    column_name: str,
    severity: str = "warning",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Generate a warning if cardinality is unusually high or low.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity (usually warning)
        params: Dict with 'min' and/or 'max' cardinality thresholds

    Returns:
        ColumnTestResult
    """
    params = params or {}
    min_cardinality = params.get("min", 1)
    max_cardinality = params.get("max")

    # Calculate cardinality (unique non-null values)
    cardinality = series.nunique(dropna=True)
    total_count = len(series.dropna())

    warning_message = None
    passed = True

    if cardinality < min_cardinality:
        passed = False
        warning_message = (
            f"Low cardinality: {cardinality} unique values "
            f"(minimum expected: {min_cardinality})"
        )
    elif max_cardinality is not None and cardinality > max_cardinality:
        passed = False
        warning_message = (
            f"High cardinality: {cardinality} unique values "
            f"(maximum expected: {max_cardinality})"
        )
    elif cardinality == total_count and total_count > 10:
        # All values are unique - might indicate ID or free text
        warning_message = (
            f"All {cardinality} values are unique - "
            "this may be an ID column or free text"
        )

    return ColumnTestResult(
        column_name=column_name,
        test_type="cardinality_warning",
        severity="warning",  # Always warning
        passed=passed,
        total_values=len(series),
        failed_count=0 if passed else 1,
        warning_message=warning_message,
    )


def test_pattern(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that values match a pattern (preset, builder, or advanced regex).

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with 'tier' ("preset", "builder", "advanced") and tier-specific params

    Returns:
        ColumnTestResult
    """
    params = params or {}
    tier = params.get("tier", "preset")

    # Build the pattern based on tier
    if tier == "preset":
        preset_name = params.get("preset_name")
        pattern = get_preset_pattern(preset_name) if preset_name else None
    elif tier == "builder":
        builder_params = params.get("builder", {})
        pattern = build_pattern_from_builder(
            allowed_characters=builder_params.get("allowed_characters"),
            length_exact=builder_params.get("length", {}).get("exact"),
            length_min=builder_params.get("length", {}).get("min"),
            length_max=builder_params.get("length", {}).get("max"),
            starts_with=builder_params.get("starts_with"),
            ends_with=builder_params.get("ends_with"),
        )
    else:  # advanced
        pattern = params.get("pattern")

    if not pattern:
        return ColumnTestResult(
            column_name=column_name,
            test_type="pattern",
            severity=severity,
            passed=False,
            total_values=len(series),
            failed_count=0,
            warning_message="No pattern specified",
        )

    failed_indices = []
    failed_values = []
    error_details = []

    for idx, value in series.items():
        if pd.isna(value):
            continue

        is_valid = validate_with_custom_pattern(str(value), pattern)

        if not is_valid:
            failed_indices.append(idx)
            failed_values.append(value)
            if len(error_details) < 10:
                error_details.append(
                    f"Row {idx}: '{value}' does not match pattern"
                )

    return ColumnTestResult(
        column_name=column_name,
        test_type="pattern",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def test_date_rule(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that date values conform to the expected format.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with 'target_format', 'mode', 'accepted_input_formats',
                'excel_serial_enabled', 'allow_multi_input_formats'

    Returns:
        ColumnTestResult
    """
    params = params or {}
    target_format = params.get("target_format", "YYYY-MM-DD")
    mode = params.get("mode", "simple")
    accepted_formats = params.get("accepted_input_formats", [target_format])
    excel_serial = params.get("excel_serial_enabled", False)

    if mode == "simple":
        accepted_formats = [target_format]

    failed_indices = []
    failed_values = []
    error_details = []

    for idx, value in series.items():
        if pd.isna(value):
            continue

        parsed, matched = try_parse_date_robust(
            str(value),
            accepted_formats,
            excel_serial,
        )

        if parsed is None:
            failed_indices.append(idx)
            failed_values.append(value)
            if len(error_details) < 10:
                error_details.append(
                    f"Row {idx}: '{value}' is not a valid date"
                )

    return ColumnTestResult(
        column_name=column_name,
        test_type="date_rule",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


def test_date_window(
    series: pd.Series,
    column_name: str,
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Test that date values fall within a specified window.

    Args:
        series: The column data
        column_name: Column name
        severity: Test severity
        params: Dict with 'min_date' and/or 'max_date' (as strings)

    Returns:
        ColumnTestResult
    """
    params = params or {}
    min_date_str = params.get("min_date")
    max_date_str = params.get("max_date")

    # Parse boundary dates
    min_date = pd.to_datetime(min_date_str) if min_date_str else None
    max_date = pd.to_datetime(max_date_str) if max_date_str else None

    failed_indices = []
    failed_values = []
    error_details = []

    for idx, value in series.items():
        if pd.isna(value):
            continue

        try:
            date_value = pd.to_datetime(value)

            if min_date is not None and date_value < min_date:
                failed_indices.append(idx)
                failed_values.append(value)
                if len(error_details) < 10:
                    error_details.append(
                        f"Row {idx}: {value} is before minimum date {min_date_str}"
                    )
            elif max_date is not None and date_value > max_date:
                failed_indices.append(idx)
                failed_values.append(value)
                if len(error_details) < 10:
                    error_details.append(
                        f"Row {idx}: {value} is after maximum date {max_date_str}"
                    )
        except Exception:
            # Invalid date - skip (handled by date_rule test)
            pass

    return ColumnTestResult(
        column_name=column_name,
        test_type="date_window",
        severity=severity,
        passed=len(failed_indices) == 0,
        total_values=len(series),
        failed_count=len(failed_indices),
        failed_indices=failed_indices[:100],
        failed_values=failed_values[:100],
        error_details=error_details,
    )


# Test function registry
COLUMN_TEST_FUNCTIONS: dict[str, Callable] = {
    "not_null": test_not_null,
    "type_conformance": test_type_conformance,
    "range": test_range,
    "length": test_length,
    "enum": test_enum,
    "uniqueness": test_uniqueness,
    "monotonic": test_monotonic,
    "cardinality_warning": test_cardinality_warning,
    "pattern": test_pattern,
    "date_rule": test_date_rule,
    "date_window": test_date_window,
}


def run_column_test(
    test_type: str,
    series: pd.Series,
    column_name: str,
    data_type: str = "string",
    severity: str = "error",
    params: Optional[dict] = None,
) -> ColumnTestResult:
    """
    Run a column test by type.

    Args:
        test_type: The type of test to run
        series: The column data
        column_name: Column name
        data_type: Column data type
        severity: Test severity
        params: Test parameters

    Returns:
        ColumnTestResult
    """
    test_func = COLUMN_TEST_FUNCTIONS.get(test_type)

    if test_func is None:
        return ColumnTestResult(
            column_name=column_name,
            test_type=test_type,
            severity=severity,
            passed=False,
            total_values=len(series),
            failed_count=0,
            warning_message=f"Unknown test type: {test_type}",
        )

    # Special handling for type_conformance which needs data_type
    if test_type == "type_conformance":
        return test_func(series, column_name, data_type, severity, params)

    return test_func(series, column_name, severity, params)
