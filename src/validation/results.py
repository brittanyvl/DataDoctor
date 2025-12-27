"""
Validation result structures.

This module defines dataclasses for representing validation results
at various levels (cell, column, dataset, overall).
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CellValidationResult:
    """Result of validating a single cell."""

    row_index: int
    column_name: str
    original_value: Any
    is_valid: bool
    test_type: str
    error_message: Optional[str] = None
    severity: str = "error"


@dataclass
class ColumnTestResult:
    """Result of running a test on a column."""

    column_name: str
    test_type: str
    severity: str
    passed: bool
    total_values: int
    failed_count: int
    failed_indices: list[int] = field(default_factory=list)
    failed_values: list[Any] = field(default_factory=list)
    error_details: list[str] = field(default_factory=list)
    warning_message: Optional[str] = None


@dataclass
class ColumnValidationResult:
    """Aggregate result for a column."""

    column_name: str
    data_type: str
    is_valid: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_count: int
    test_results: list[ColumnTestResult] = field(default_factory=list)
    overall_status: str = "PASS"  # PASS, FAIL, or WARNING


@dataclass
class DatasetTestResult:
    """Result of running a dataset-level test."""

    test_type: str
    severity: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    affected_rows: list[int] = field(default_factory=list)


@dataclass
class ForeignKeyCheckResult:
    """Result of a foreign key membership check."""

    name: str
    dataset_column: str
    fk_column: str
    passed: bool
    total_values: int
    missing_count: int
    missing_values: list[Any] = field(default_factory=list)
    missing_row_indices: list[int] = field(default_factory=list)


@dataclass
class ValidationSummary:
    """Summary statistics for validation."""

    total_rows: int
    total_columns: int
    total_tests_run: int
    total_tests_passed: int
    total_tests_failed: int
    total_warnings: int
    total_errors: int
    rows_with_errors: int
    clean_rows: int
    error_rate_percent: float
    has_blocking_errors: bool


@dataclass
class ValidationResult:
    """Complete validation result for a dataset."""

    is_valid: bool
    summary: ValidationSummary
    column_results: dict[str, ColumnValidationResult] = field(default_factory=dict)
    dataset_test_results: list[DatasetTestResult] = field(default_factory=list)
    fk_check_results: list[ForeignKeyCheckResult] = field(default_factory=list)
    cell_errors: list[CellValidationResult] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)


def create_empty_summary(row_count: int, column_count: int) -> ValidationSummary:
    """Create an empty validation summary."""
    return ValidationSummary(
        total_rows=row_count,
        total_columns=column_count,
        total_tests_run=0,
        total_tests_passed=0,
        total_tests_failed=0,
        total_warnings=0,
        total_errors=0,
        rows_with_errors=0,
        clean_rows=row_count,
        error_rate_percent=0.0,
        has_blocking_errors=False,
    )


def calculate_summary(
    column_results: dict[str, ColumnValidationResult],
    dataset_test_results: list[DatasetTestResult],
    fk_check_results: list[ForeignKeyCheckResult],
    cell_errors: list[CellValidationResult],
    row_count: int,
    column_count: int,
) -> ValidationSummary:
    """
    Calculate validation summary from component results.

    Args:
        column_results: Results for each column
        dataset_test_results: Dataset-level test results
        fk_check_results: Foreign key check results
        cell_errors: List of cell-level errors
        row_count: Total row count
        column_count: Total column count

    Returns:
        ValidationSummary with calculated statistics
    """
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    warnings = 0
    errors = 0

    # Count column test results
    for col_result in column_results.values():
        total_tests += col_result.total_tests
        passed_tests += col_result.passed_tests
        failed_tests += col_result.failed_tests
        warnings += col_result.warning_count

    # Count dataset test results
    for dt_result in dataset_test_results:
        total_tests += 1
        if dt_result.passed:
            passed_tests += 1
        else:
            failed_tests += 1
            if dt_result.severity == "warning":
                warnings += 1
            else:
                errors += 1

    # Count FK check results
    for fk_result in fk_check_results:
        total_tests += 1
        if fk_result.passed:
            passed_tests += 1
        else:
            failed_tests += 1
            errors += 1

    # Calculate rows with errors
    error_row_indices = set()
    for cell_error in cell_errors:
        if cell_error.severity == "error":
            error_row_indices.add(cell_error.row_index)
            errors += 1
        else:
            warnings += 1

    rows_with_errors = len(error_row_indices)
    clean_rows = row_count - rows_with_errors

    # Calculate error rate
    error_rate = (rows_with_errors / row_count * 100) if row_count > 0 else 0.0

    # Check for blocking errors (strict_fail)
    has_blocking = errors > 0

    return ValidationSummary(
        total_rows=row_count,
        total_columns=column_count,
        total_tests_run=total_tests,
        total_tests_passed=passed_tests,
        total_tests_failed=failed_tests,
        total_warnings=warnings,
        total_errors=errors,
        rows_with_errors=rows_with_errors,
        clean_rows=clean_rows,
        error_rate_percent=round(error_rate, 2),
        has_blocking_errors=has_blocking,
    )


def get_failed_rows(validation_result: ValidationResult) -> set[int]:
    """
    Get set of row indices that have any errors.

    Args:
        validation_result: The validation result

    Returns:
        Set of row indices with errors
    """
    failed_rows = set()

    for cell_error in validation_result.cell_errors:
        if cell_error.severity == "error":
            failed_rows.add(cell_error.row_index)

    return failed_rows


def get_column_error_summary(
    validation_result: ValidationResult,
) -> dict[str, dict[str, int]]:
    """
    Get summary of errors by column and test type.

    Args:
        validation_result: The validation result

    Returns:
        Dict mapping column name to dict of test_type: count
    """
    summary: dict[str, dict[str, int]] = {}

    for cell_error in validation_result.cell_errors:
        col_name = cell_error.column_name
        test_type = cell_error.test_type

        if col_name not in summary:
            summary[col_name] = {}

        if test_type not in summary[col_name]:
            summary[col_name][test_type] = 0

        summary[col_name][test_type] += 1

    return summary


def format_validation_summary(summary: ValidationSummary) -> str:
    """
    Format validation summary for display.

    Args:
        summary: The validation summary

    Returns:
        Formatted summary string
    """
    lines = [
        "Validation Summary",
        "=" * 40,
        f"Total Rows: {summary.total_rows:,}",
        f"Total Columns: {summary.total_columns}",
        f"Tests Run: {summary.total_tests_run}",
        f"Tests Passed: {summary.total_tests_passed}",
        f"Tests Failed: {summary.total_tests_failed}",
        f"Warnings: {summary.total_warnings}",
        f"Errors: {summary.total_errors}",
        f"Rows with Errors: {summary.rows_with_errors:,}",
        f"Clean Rows: {summary.clean_rows:,}",
        f"Error Rate: {summary.error_rate_percent:.2f}%",
    ]

    if summary.has_blocking_errors:
        lines.append("Status: BLOCKED (has strict failures)")
    else:
        lines.append("Status: OK")

    return "\n".join(lines)
