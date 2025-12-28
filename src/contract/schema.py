"""
YAML contract schema definitions.

This module defines dataclasses representing the structure of a
Data Doctor contract as specified in Section 21 of the acceptance criteria.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import uuid


@dataclass
class AppInfo:
    """Application metadata in the contract."""

    name: str = "Data Doctor"
    version: str = "0.1.0"


@dataclass
class Limits:
    """Resource limits recorded in the contract."""

    max_upload_mb: int = 75
    max_rows: int = 250000
    max_columns: int = 100


@dataclass
class RowLimitBehavior:
    """Row limit behavior configuration."""

    reject_if_over_limit: bool = True


@dataclass
class QuickActions:
    """Quick column name transformation actions."""

    to_lowercase: bool = False
    to_uppercase: bool = False
    to_titlecase: bool = False
    trim_whitespace: bool = False
    remove_punctuation: bool = False
    replace_spaces_with_underscores: bool = False


@dataclass
class ImportSettings:
    """Import settings for file processing.

    These settings are applied when loading a file and can be saved/restored
    from a contract to ensure consistent processing across runs.
    """

    skip_rows: int = 0
    skip_footer_rows: int = 0
    column_renames: dict[str, str] = field(default_factory=dict)
    columns_to_ignore: list[str] = field(default_factory=list)
    quick_actions: QuickActions = field(default_factory=QuickActions)


@dataclass
class DatasetConfig:
    """Dataset configuration in the contract."""

    row_limit_behavior: RowLimitBehavior = field(default_factory=RowLimitBehavior)
    contract_basis_filename: Optional[str] = None
    sheet_name: Optional[str] = None
    header_row: int = 1
    delimiter: Optional[str] = None
    encoding: Optional[str] = None
    import_settings: ImportSettings = field(default_factory=ImportSettings)


@dataclass
class Normalization:
    """Column normalization settings."""

    trim_whitespace: bool = True
    null_tokens: list[str] = field(default_factory=lambda: ["", "NA", "N/A", "null", "None"])
    case: str = "none"  # none, lower, upper, title
    remove_non_printable: bool = True


@dataclass
class FailureHandling:
    """Failure handling configuration."""

    action: str = "strict_fail"  # strict_fail, set_null, label_failure, quarantine_row, drop_row
    label_column_name: Optional[str] = None
    quarantine_export_name: Optional[str] = None


@dataclass
class TestConfig:
    """Configuration for a single test."""

    type: str
    severity: str = "error"  # error or warning
    params: dict[str, Any] = field(default_factory=dict)
    on_fail: Optional[FailureHandling] = None


@dataclass
class RemediationConfig:
    """Configuration for a remediation action."""

    type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ColumnConfig:
    """Configuration for a single column."""

    name: str
    data_type: str = "string"
    required: bool = False
    rename_to: Optional[str] = None
    normalization: Optional[Normalization] = None
    tests: list[TestConfig] = field(default_factory=list)
    remediation: list[RemediationConfig] = field(default_factory=list)
    failure_handling: FailureHandling = field(default_factory=FailureHandling)


@dataclass
class DatasetTest:
    """Configuration for a dataset-level test."""

    type: str
    severity: str = "error"
    params: dict[str, Any] = field(default_factory=dict)
    on_fail: Optional[FailureHandling] = None


@dataclass
class NullPolicy:
    """Null handling policy for FK checks."""

    allow_nulls: bool = False


@dataclass
class ForeignKeyCheck:
    """Configuration for a foreign key membership check."""

    name: str
    dataset_column: str
    fk_file: str
    fk_column: str
    fk_sheet: Optional[str] = None
    normalization_inherit_from_dataset_column: bool = True
    null_policy: NullPolicy = field(default_factory=NullPolicy)
    on_fail: FailureHandling = field(default_factory=FailureHandling)


@dataclass
class ExportConfig:
    """Export configuration."""

    report_html: bool = True
    cleaned_dataset: bool = False
    contract_yaml: bool = True
    remediation_summary: bool = False
    output_format: str = "csv"


@dataclass
class Contract:
    """Complete Data Doctor contract."""

    contract_version: str = "1.0"
    contract_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at_utc: str = field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    app: AppInfo = field(default_factory=AppInfo)
    limits: Optional[Limits] = field(default_factory=Limits)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    columns: list[ColumnConfig] = field(default_factory=list)
    dataset_tests: list[DatasetTest] = field(default_factory=list)
    foreign_key_checks: list[ForeignKeyCheck] = field(default_factory=list)
    exports: ExportConfig = field(default_factory=ExportConfig)


def create_default_column_config(
    name: str,
    data_type: str = "string",
    required: bool = False,
) -> ColumnConfig:
    """
    Create a default column configuration.

    Args:
        name: Column name
        data_type: Data type
        required: Whether the column is required

    Returns:
        ColumnConfig with defaults
    """
    return ColumnConfig(
        name=name,
        data_type=data_type,
        required=required,
        normalization=Normalization(),
        failure_handling=FailureHandling(),
    )


def create_empty_contract() -> Contract:
    """
    Create an empty contract with default values.

    Returns:
        Contract with defaults
    """
    return Contract()


def contract_to_dict(contract: Contract) -> dict:
    """
    Convert a Contract dataclass to a dictionary for YAML serialization.

    Args:
        contract: The Contract to convert

    Returns:
        Dictionary representation
    """

    def dataclass_to_dict(obj: Any) -> Any:
        """Recursively convert dataclasses to dicts."""
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if value is not None:
                    result[field_name] = dataclass_to_dict(value)
            return result
        elif isinstance(obj, list):
            return [dataclass_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: dataclass_to_dict(v) for k, v in obj.items()}
        else:
            return obj

    return dataclass_to_dict(contract)


def dict_to_normalization(data: Optional[dict]) -> Optional[Normalization]:
    """Convert a dictionary to a Normalization object."""
    if data is None:
        return None
    return Normalization(
        trim_whitespace=data.get("trim_whitespace", True),
        null_tokens=data.get("null_tokens", ["", "NA", "N/A", "null", "None"]),
        case=data.get("case", "none"),
        remove_non_printable=data.get("remove_non_printable", True),
    )


def dict_to_failure_handling(data: Optional[dict]) -> FailureHandling:
    """Convert a dictionary to a FailureHandling object."""
    if data is None:
        return FailureHandling()
    return FailureHandling(
        action=data.get("action", "strict_fail"),
        label_column_name=data.get("label_column_name"),
        quarantine_export_name=data.get("quarantine_export_name"),
    )


def dict_to_test_config(data: dict) -> TestConfig:
    """Convert a dictionary to a TestConfig object."""
    return TestConfig(
        type=data.get("type", ""),
        severity=data.get("severity", "error"),
        params=data.get("params", {}),
        on_fail=dict_to_failure_handling(data.get("on_fail")),
    )


def dict_to_remediation_config(data: dict) -> RemediationConfig:
    """Convert a dictionary to a RemediationConfig object."""
    return RemediationConfig(
        type=data.get("type", ""),
        params=data.get("params", {}),
    )


def dict_to_column_config(data: dict) -> ColumnConfig:
    """Convert a dictionary to a ColumnConfig object."""
    return ColumnConfig(
        name=data.get("name", ""),
        data_type=data.get("data_type", "string"),
        required=data.get("required", False),
        rename_to=data.get("rename_to"),
        normalization=dict_to_normalization(data.get("normalization")),
        tests=[dict_to_test_config(t) for t in data.get("tests", [])],
        remediation=[dict_to_remediation_config(r) for r in data.get("remediation", [])],
        failure_handling=dict_to_failure_handling(data.get("failure_handling")),
    )


def dict_to_contract(data: dict) -> Contract:
    """
    Convert a dictionary (from YAML) to a Contract object.

    Args:
        data: Dictionary from YAML parsing

    Returns:
        Contract object
    """
    # Parse app info
    app_data = data.get("app", {})
    app = AppInfo(
        name=app_data.get("name", "Data Doctor"),
        version=app_data.get("version", "0.1.0"),
    )

    # Parse limits
    limits_data = data.get("limits")
    limits = None
    if limits_data:
        limits = Limits(
            max_upload_mb=limits_data.get("max_upload_mb", 75),
            max_rows=limits_data.get("max_rows", 250000),
            max_columns=limits_data.get("max_columns", 100),
        )

    # Parse dataset config
    dataset_data = data.get("dataset", {})
    row_limit_data = dataset_data.get("row_limit_behavior", {})

    # Parse import settings
    import_data = dataset_data.get("import_settings", {})
    quick_actions_data = import_data.get("quick_actions", {})
    import_settings = ImportSettings(
        skip_rows=import_data.get("skip_rows", 0),
        skip_footer_rows=import_data.get("skip_footer_rows", 0),
        column_renames=import_data.get("column_renames", {}),
        columns_to_ignore=import_data.get("columns_to_ignore", []),
        quick_actions=QuickActions(
            to_lowercase=quick_actions_data.get("to_lowercase", False),
            to_uppercase=quick_actions_data.get("to_uppercase", False),
            to_titlecase=quick_actions_data.get("to_titlecase", False),
            trim_whitespace=quick_actions_data.get("trim_whitespace", False),
            remove_punctuation=quick_actions_data.get("remove_punctuation", False),
            replace_spaces_with_underscores=quick_actions_data.get(
                "replace_spaces_with_underscores", False
            ),
        ),
    )

    dataset = DatasetConfig(
        row_limit_behavior=RowLimitBehavior(
            reject_if_over_limit=row_limit_data.get("reject_if_over_limit", True)
        ),
        contract_basis_filename=dataset_data.get("contract_basis_filename"),
        sheet_name=dataset_data.get("sheet_name"),
        header_row=dataset_data.get("header_row", 1),
        delimiter=dataset_data.get("delimiter"),
        encoding=dataset_data.get("encoding"),
        import_settings=import_settings,
    )

    # Parse columns
    columns = [dict_to_column_config(c) for c in data.get("columns", [])]

    # Parse dataset tests
    dataset_tests = []
    for dt in data.get("dataset_tests", []):
        dataset_tests.append(
            DatasetTest(
                type=dt.get("type", ""),
                severity=dt.get("severity", "error"),
                params=dt.get("params", {}),
                on_fail=dict_to_failure_handling(dt.get("on_fail")),
            )
        )

    # Parse foreign key checks
    fk_checks = []
    for fk in data.get("foreign_key_checks", []):
        null_policy_data = fk.get("null_policy", {})
        fk_checks.append(
            ForeignKeyCheck(
                name=fk.get("name", ""),
                dataset_column=fk.get("dataset_column", ""),
                fk_file=fk.get("fk_file", ""),
                fk_column=fk.get("fk_column", ""),
                fk_sheet=fk.get("fk_sheet"),
                normalization_inherit_from_dataset_column=fk.get(
                    "normalization_inherit_from_dataset_column", True
                ),
                null_policy=NullPolicy(
                    allow_nulls=null_policy_data.get("allow_nulls", False)
                ),
                on_fail=dict_to_failure_handling(fk.get("on_fail")),
            )
        )

    # Parse exports
    exports_data = data.get("exports", {})
    exports = ExportConfig(
        report_html=exports_data.get("report_html", True),
        cleaned_dataset=exports_data.get("cleaned_dataset", False),
        contract_yaml=exports_data.get("contract_yaml", True),
        remediation_summary=exports_data.get("remediation_summary", False),
        output_format=exports_data.get("output_format", "csv"),
    )

    return Contract(
        contract_version=data.get("contract_version", "1.0"),
        contract_id=data.get("contract_id", str(uuid.uuid4())),
        created_at_utc=data.get("created_at_utc", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
        app=app,
        limits=limits,
        dataset=dataset,
        columns=columns,
        dataset_tests=dataset_tests,
        foreign_key_checks=fk_checks,
        exports=exports,
    )
