"""
Contract builder from UI state.

This module provides functions to build a Contract from user selections
in the Streamlit UI.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

import pandas as pd

from src.constants import (
    APP_NAME,
    APP_VERSION,
    CONTRACT_VERSION,
    DEFAULT_NULL_TOKENS,
    MAX_COLUMN_COUNT,
    MAX_ROW_COUNT,
    MAX_UPLOAD_SIZE_MB,
)
from src.contract.schema import (
    AppInfo,
    ColumnConfig,
    Contract,
    DatasetConfig,
    DatasetTest,
    ExportConfig,
    FailureHandling,
    ForeignKeyCheck,
    ImportSettings,
    Limits,
    Normalization,
    NullPolicy,
    QuickActions,
    RemediationConfig,
    RowLimitBehavior,
    TestConfig,
)


def build_contract_from_dataframe(
    df: pd.DataFrame,
    filename: Optional[str] = None,
    sheet_name: Optional[str] = None,
    import_settings: Optional[ImportSettings] = None,
    ignored_columns: Optional[list[str]] = None,
) -> Contract:
    """
    Build a basic contract from a DataFrame with default column configs.

    Args:
        df: The DataFrame to build contract for
        filename: Optional source filename
        sheet_name: Optional Excel sheet name
        import_settings: Optional import settings (skip rows, quick actions, etc.)
        ignored_columns: Optional list of column names to exclude from the contract

    Returns:
        Contract with columns matching the DataFrame
    """
    ignored_set = set(ignored_columns or [])

    columns = []
    for col_name in df.columns:
        # Skip ignored columns - they won't be in the contract
        if str(col_name) in ignored_set:
            continue

        # Infer data type from pandas dtype and column name
        inferred_type = infer_data_type(df[col_name], str(col_name))

        columns.append(
            ColumnConfig(
                name=str(col_name),
                data_type=inferred_type,
                required=False,
                normalization=Normalization(
                    trim_whitespace=True,
                    null_tokens=DEFAULT_NULL_TOKENS.copy(),
                    case="none",
                    remove_non_printable=True,
                ),
                failure_handling=FailureHandling(
                    action="label_failure",
                    label_column_name="__data_doctor_errors__",
                ),
            )
        )

    return Contract(
        contract_version=CONTRACT_VERSION,
        contract_id=str(uuid.uuid4()),
        created_at_utc=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        app=AppInfo(name=APP_NAME, version=APP_VERSION),
        limits=Limits(
            max_upload_mb=MAX_UPLOAD_SIZE_MB,
            max_rows=MAX_ROW_COUNT,
            max_columns=MAX_COLUMN_COUNT,
        ),
        dataset=DatasetConfig(
            row_limit_behavior=RowLimitBehavior(reject_if_over_limit=True),
            contract_basis_filename=filename,
            sheet_name=sheet_name,
            import_settings=import_settings or ImportSettings(),
        ),
        columns=columns,
        exports=ExportConfig(),
    )


def build_import_settings_from_session(session_state: dict) -> ImportSettings:
    """
    Build ImportSettings from Streamlit session state.

    Args:
        session_state: The Streamlit session state dictionary

    Returns:
        ImportSettings with current configuration
    """
    # Get column renames - only include actual renames (where key != value)
    column_renames_raw = session_state.get("column_renames", {})
    column_renames = {k: v for k, v in column_renames_raw.items() if k != v}

    # Get ignored columns (as renamed names)
    ignored_columns = session_state.get("ignored_columns", [])

    # Get applied transformations (we store which were applied in session)
    applied_actions = session_state.get("applied_quick_actions", {})

    return ImportSettings(
        skip_rows=session_state.get("applied_skip_rows", 0),
        skip_footer_rows=session_state.get("applied_skip_footer_rows", 0),
        column_renames=column_renames,
        columns_to_ignore=ignored_columns,
        quick_actions=QuickActions(
            to_lowercase=applied_actions.get("to_lowercase", False),
            to_uppercase=applied_actions.get("to_uppercase", False),
            to_titlecase=applied_actions.get("to_titlecase", False),
            trim_whitespace=applied_actions.get("trim_whitespace", False),
            remove_punctuation=applied_actions.get("remove_punctuation", False),
            replace_spaces_with_underscores=applied_actions.get("replace_spaces", False),
        ),
    )


def infer_data_type(series: pd.Series, column_name: str = "") -> str:
    """
    Infer the data type for a pandas Series.

    Args:
        series: The pandas Series to analyze
        column_name: Optional column name to help infer type

    Returns:
        Inferred data type string (text, boolean, integer, float, date, timestamp)
    """
    # Check if column name contains "date" (case insensitive)
    # This is a strong hint that the column should be treated as a date
    col_name_lower = column_name.lower()
    if "date" in col_name_lower:
        return "date"

    # Get non-null values
    non_null = series.dropna()

    if len(non_null) == 0:
        return "text"

    # Check the pandas dtype first
    dtype_str = str(series.dtype)

    if "int" in dtype_str:
        return "integer"
    elif "float" in dtype_str:
        return "float"
    elif "bool" in dtype_str:
        return "boolean"
    elif "datetime" in dtype_str:
        return "timestamp"

    # For object dtype, try to infer from values
    if series.dtype == object:
        # Sample up to 20 values for type inference (per user request)
        sample = non_null.head(20)

        # Try to detect booleans first (use 20 rows)
        if _looks_like_boolean(sample):
            return "boolean"

        # Try to detect integers
        if _looks_like_integer(sample):
            return "integer"

        # Try to detect floats
        if _looks_like_float(sample):
            return "float"

        # Try to detect dates
        if _looks_like_date(sample):
            return "date"

    return "text"


def _looks_like_boolean(series: pd.Series) -> bool:
    """Check if series looks like boolean values."""
    bool_tokens = {
        "true", "false", "yes", "no", "1", "0",
        "t", "f", "y", "n", "on", "off",
    }
    try:
        values = series.astype(str).str.lower().str.strip()
        unique_values = set(values.unique())
        return unique_values.issubset(bool_tokens)
    except Exception:
        return False


def _looks_like_integer(series: pd.Series) -> bool:
    """Check if series looks like integer values."""
    try:
        # Remove commas and try to convert
        cleaned = series.astype(str).str.replace(",", "", regex=False)
        cleaned = cleaned.str.strip()
        # Check if all values are digits (possibly with leading minus)
        pattern = r"^-?\d+$"
        return cleaned.str.match(pattern).all()
    except Exception:
        return False


def _looks_like_float(series: pd.Series) -> bool:
    """Check if series looks like float values."""
    try:
        # Remove commas and try to convert
        cleaned = series.astype(str).str.replace(",", "", regex=False)
        cleaned = cleaned.str.replace("$", "", regex=False)
        cleaned = cleaned.str.strip()
        pd.to_numeric(cleaned)
        return True
    except Exception:
        return False


def _looks_like_date(series: pd.Series) -> bool:
    """Check if series looks like date values."""
    try:
        # Try to parse as dates
        pd.to_datetime(series, errors="raise")
        return True
    except Exception:
        return False


def update_column_config(
    contract: Contract,
    column_name: str,
    updates: dict[str, Any],
) -> Contract:
    """
    Update a column configuration in a contract.

    Args:
        contract: The contract to update
        column_name: Name of the column to update
        updates: Dictionary of updates to apply

    Returns:
        Updated contract
    """
    for col in contract.columns:
        if col.name == column_name:
            for key, value in updates.items():
                if hasattr(col, key):
                    setattr(col, key, value)
            break

    return contract


def add_column_test(
    contract: Contract,
    column_name: str,
    test_type: str,
    severity: str = "error",
    params: Optional[dict] = None,
    on_fail: Optional[dict] = None,
) -> Contract:
    """
    Add a test to a column configuration.

    Args:
        contract: The contract to update
        column_name: Name of the column
        test_type: Type of test to add
        severity: Test severity (error or warning)
        params: Test parameters
        on_fail: Override failure handling

    Returns:
        Updated contract
    """
    for col in contract.columns:
        if col.name == column_name:
            test = TestConfig(
                type=test_type,
                severity=severity,
                params=params or {},
            )
            if on_fail:
                test.on_fail = FailureHandling(
                    action=on_fail.get("action", "label_failure"),
                    label_column_name=on_fail.get("label_column_name"),
                    quarantine_export_name=on_fail.get("quarantine_export_name"),
                )
            col.tests.append(test)
            break

    return contract


def add_column_remediation(
    contract: Contract,
    column_name: str,
    remediation_type: str,
    params: Optional[dict] = None,
) -> Contract:
    """
    Add a remediation action to a column configuration.

    Args:
        contract: The contract to update
        column_name: Name of the column
        remediation_type: Type of remediation
        params: Remediation parameters

    Returns:
        Updated contract
    """
    for col in contract.columns:
        if col.name == column_name:
            col.remediation.append(
                RemediationConfig(
                    type=remediation_type,
                    params=params or {},
                )
            )
            break

    return contract


def add_dataset_test(
    contract: Contract,
    test_type: str,
    severity: str = "error",
    params: Optional[dict] = None,
    on_fail: Optional[dict] = None,
) -> Contract:
    """
    Add a dataset-level test.

    Args:
        contract: The contract to update
        test_type: Type of test
        severity: Test severity
        params: Test parameters
        on_fail: Failure handling override

    Returns:
        Updated contract
    """
    test = DatasetTest(
        type=test_type,
        severity=severity,
        params=params or {},
    )
    if on_fail:
        test.on_fail = FailureHandling(
            action=on_fail.get("action", "label_failure"),
            label_column_name=on_fail.get("label_column_name"),
            quarantine_export_name=on_fail.get("quarantine_export_name"),
        )
    contract.dataset_tests.append(test)

    return contract


def add_foreign_key_check(
    contract: Contract,
    name: str,
    dataset_column: str,
    fk_file: str,
    fk_column: str,
    fk_sheet: Optional[str] = None,
    allow_nulls: bool = False,
    on_fail_action: str = "label_failure",
) -> Contract:
    """
    Add a foreign key check.

    Args:
        contract: The contract to update
        name: Name for the FK check
        dataset_column: Column in dataset to check
        fk_file: FK list filename
        fk_column: Column in FK list
        fk_sheet: Sheet name if FK file is Excel
        allow_nulls: Whether to allow null values
        on_fail_action: Action on failure

    Returns:
        Updated contract
    """
    fk_check = ForeignKeyCheck(
        name=name,
        dataset_column=dataset_column,
        fk_file=fk_file,
        fk_column=fk_column,
        fk_sheet=fk_sheet,
        normalization_inherit_from_dataset_column=True,
        null_policy=NullPolicy(allow_nulls=allow_nulls),
        on_fail=FailureHandling(action=on_fail_action),
    )
    contract.foreign_key_checks.append(fk_check)

    return contract


def update_export_config(
    contract: Contract,
    report_html: Optional[bool] = None,
    cleaned_dataset: Optional[bool] = None,
    contract_yaml: Optional[bool] = None,
    remediation_summary: Optional[bool] = None,
    output_format: Optional[str] = None,
) -> Contract:
    """
    Update export configuration.

    Args:
        contract: The contract to update
        report_html: Whether to export HTML report
        cleaned_dataset: Whether to export cleaned dataset
        contract_yaml: Whether to export contract YAML
        remediation_summary: Whether to export remediation summary
        output_format: Output format (csv or xlsx)

    Returns:
        Updated contract
    """
    if report_html is not None:
        contract.exports.report_html = report_html
    if cleaned_dataset is not None:
        contract.exports.cleaned_dataset = cleaned_dataset
    if contract_yaml is not None:
        contract.exports.contract_yaml = contract_yaml
    if remediation_summary is not None:
        contract.exports.remediation_summary = remediation_summary
    if output_format is not None:
        contract.exports.output_format = output_format

    return contract


def get_column_config(contract: Contract, column_name: str) -> Optional[ColumnConfig]:
    """
    Get the configuration for a specific column.

    Args:
        contract: The contract
        column_name: Name of the column

    Returns:
        ColumnConfig or None if not found
    """
    for col in contract.columns:
        if col.name == column_name:
            return col
    return None
