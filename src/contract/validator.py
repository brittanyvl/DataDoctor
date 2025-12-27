"""
Contract self-validation.

This module validates YAML contracts according to Section 24 of the
acceptance criteria before allowing dataset validation to proceed.
"""

from dataclasses import dataclass
from typing import Optional

from src.constants import (
    COLUMN_TEST_TYPES,
    DATA_TYPES,
    DATASET_TEST_TYPES,
    FAILURE_ACTIONS,
    REMEDIATION_TYPES,
)
from src.contract.schema import Contract


@dataclass
class ValidationError:
    """A single validation error."""

    field: str
    message: str
    guidance: str


@dataclass
class ContractValidationResult:
    """Result of contract validation."""

    is_valid: bool
    errors: list[ValidationError]


def validate_contract(contract: Contract) -> ContractValidationResult:
    """
    Validate a contract according to the rules in Section 24.

    Args:
        contract: The Contract to validate

    Returns:
        ContractValidationResult with validation status and any errors
    """
    errors = []

    # Validate top-level required fields
    errors.extend(_validate_top_level(contract))

    # Validate columns
    errors.extend(_validate_columns(contract))

    # Validate dataset tests
    errors.extend(_validate_dataset_tests(contract))

    # Validate foreign key checks
    errors.extend(_validate_foreign_key_checks(contract))

    return ContractValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )


def _validate_top_level(contract: Contract) -> list[ValidationError]:
    """Validate top-level required fields."""
    errors = []

    # contract_version is required
    if not contract.contract_version:
        errors.append(
            ValidationError(
                field="contract_version",
                message="Contract version is required.",
                guidance="Add 'contract_version: \"1.0\"' to the contract.",
            )
        )

    # contract_id is required
    if not contract.contract_id:
        errors.append(
            ValidationError(
                field="contract_id",
                message="Contract ID is required.",
                guidance="Add a unique 'contract_id' field (can be a UUID).",
            )
        )

    # created_at_utc is required
    if not contract.created_at_utc:
        errors.append(
            ValidationError(
                field="created_at_utc",
                message="Creation timestamp is required.",
                guidance="Add 'created_at_utc' in ISO 8601 format.",
            )
        )

    # app is required
    if not contract.app or not contract.app.name:
        errors.append(
            ValidationError(
                field="app",
                message="Application metadata is required.",
                guidance="Add 'app' section with 'name' and 'version'.",
            )
        )

    # dataset is required
    if not contract.dataset:
        errors.append(
            ValidationError(
                field="dataset",
                message="Dataset configuration is required.",
                guidance="Add 'dataset' section with 'row_limit_behavior'.",
            )
        )

    # columns is required (and must not be empty)
    if not contract.columns:
        errors.append(
            ValidationError(
                field="columns",
                message="At least one column must be defined.",
                guidance="Add 'columns' list with column configurations.",
            )
        )

    return errors


def _validate_columns(contract: Contract) -> list[ValidationError]:
    """Validate column configurations."""
    errors = []
    column_names = set()

    for i, col in enumerate(contract.columns):
        col_prefix = f"columns[{i}]"

        # name is required
        if not col.name:
            errors.append(
                ValidationError(
                    field=f"{col_prefix}.name",
                    message=f"Column {i} is missing a name.",
                    guidance="Each column must have a 'name' field.",
                )
            )
        else:
            # Check for duplicate column names
            if col.name in column_names:
                errors.append(
                    ValidationError(
                        field=f"{col_prefix}.name",
                        message=f"Duplicate column name: '{col.name}'.",
                        guidance="Each column name must be unique.",
                    )
                )
            column_names.add(col.name)

        # data_type must be valid
        if col.data_type not in DATA_TYPES:
            errors.append(
                ValidationError(
                    field=f"{col_prefix}.data_type",
                    message=f"Invalid data type: '{col.data_type}'.",
                    guidance=f"Valid data types: {', '.join(DATA_TYPES)}",
                )
            )

        # Validate failure_handling
        errors.extend(
            _validate_failure_handling(
                col.failure_handling,
                f"{col_prefix}.failure_handling",
            )
        )

        # Validate tests
        for j, test in enumerate(col.tests):
            test_prefix = f"{col_prefix}.tests[{j}]"
            errors.extend(_validate_test(test, test_prefix, is_column_test=True))

            # Special validation for date_rule
            if test.type == "date_rule":
                errors.extend(_validate_date_rule(test, test_prefix))

        # Validate remediation
        for j, rem in enumerate(col.remediation):
            rem_prefix = f"{col_prefix}.remediation[{j}]"
            if rem.type not in REMEDIATION_TYPES:
                errors.append(
                    ValidationError(
                        field=f"{rem_prefix}.type",
                        message=f"Invalid remediation type: '{rem.type}'.",
                        guidance=f"Valid types: {', '.join(REMEDIATION_TYPES)}",
                    )
                )

    return errors


def _validate_failure_handling(
    fh: Optional[object],
    field_prefix: str,
) -> list[ValidationError]:
    """Validate failure handling configuration."""
    errors = []

    if fh is None:
        return errors

    # Access attributes if it's a dataclass
    action = getattr(fh, "action", None)
    label_column_name = getattr(fh, "label_column_name", None)
    quarantine_export_name = getattr(fh, "quarantine_export_name", None)

    # action must be valid
    if action and action not in FAILURE_ACTIONS:
        errors.append(
            ValidationError(
                field=f"{field_prefix}.action",
                message=f"Invalid failure action: '{action}'.",
                guidance=f"Valid actions: {', '.join(FAILURE_ACTIONS)}",
            )
        )

    # label_failure requires label_column_name
    if action == "label_failure" and not label_column_name:
        errors.append(
            ValidationError(
                field=f"{field_prefix}.label_column_name",
                message="label_column_name is required when action is 'label_failure'.",
                guidance="Add 'label_column_name' to specify the error label column.",
            )
        )

    # quarantine_row requires quarantine_export_name
    if action == "quarantine_row" and not quarantine_export_name:
        errors.append(
            ValidationError(
                field=f"{field_prefix}.quarantine_export_name",
                message="quarantine_export_name is required when action is 'quarantine_row'.",
                guidance="Add 'quarantine_export_name' to specify the quarantine output name.",
            )
        )

    return errors


def _validate_test(
    test: object,
    field_prefix: str,
    is_column_test: bool,
) -> list[ValidationError]:
    """Validate a test configuration."""
    errors = []

    test_type = getattr(test, "type", None)
    severity = getattr(test, "severity", None)
    on_fail = getattr(test, "on_fail", None)

    # type is required
    if not test_type:
        errors.append(
            ValidationError(
                field=f"{field_prefix}.type",
                message="Test type is required.",
                guidance="Add 'type' field to the test.",
            )
        )
    else:
        valid_types = COLUMN_TEST_TYPES if is_column_test else DATASET_TEST_TYPES
        if test_type not in valid_types:
            errors.append(
                ValidationError(
                    field=f"{field_prefix}.type",
                    message=f"Invalid test type: '{test_type}'.",
                    guidance=f"Valid types: {', '.join(valid_types)}",
                )
            )

    # severity must be valid
    if severity and severity not in ["error", "warning"]:
        errors.append(
            ValidationError(
                field=f"{field_prefix}.severity",
                message=f"Invalid severity: '{severity}'.",
                guidance="Severity must be 'error' or 'warning'.",
            )
        )

    # Validate on_fail if present
    if on_fail:
        errors.extend(_validate_failure_handling(on_fail, f"{field_prefix}.on_fail"))

    return errors


def _validate_date_rule(test: object, field_prefix: str) -> list[ValidationError]:
    """Validate date_rule test specific requirements."""
    errors = []

    params = getattr(test, "params", {}) or {}

    # target_format is required
    if not params.get("target_format"):
        errors.append(
            ValidationError(
                field=f"{field_prefix}.params.target_format",
                message="Date rule requires exactly one target_format.",
                guidance="Add 'target_format' to params (e.g., 'YYYY-MM-DD').",
            )
        )

    # If mode is "robust", accepted_input_formats is required
    mode = params.get("mode", "simple")
    if mode == "robust":
        accepted_formats = params.get("accepted_input_formats")
        if not accepted_formats or not isinstance(accepted_formats, list):
            errors.append(
                ValidationError(
                    field=f"{field_prefix}.params.accepted_input_formats",
                    message="Robust mode requires accepted_input_formats list.",
                    guidance="Add 'accepted_input_formats' as a non-empty list.",
                )
            )
        elif len(accepted_formats) == 0:
            errors.append(
                ValidationError(
                    field=f"{field_prefix}.params.accepted_input_formats",
                    message="accepted_input_formats cannot be empty in robust mode.",
                    guidance="Add at least one format to accepted_input_formats.",
                )
            )

    return errors


def _validate_dataset_tests(contract: Contract) -> list[ValidationError]:
    """Validate dataset-level tests."""
    errors = []
    column_names = {col.name for col in contract.columns}

    for i, test in enumerate(contract.dataset_tests):
        test_prefix = f"dataset_tests[{i}]"
        errors.extend(_validate_test(test, test_prefix, is_column_test=False))

        # Validate column references in params
        params = getattr(test, "params", {}) or {}

        # Check key_columns references
        key_columns = params.get("key_columns", [])
        for col_name in key_columns:
            if col_name not in column_names:
                errors.append(
                    ValidationError(
                        field=f"{test_prefix}.params.key_columns",
                        message=f"Referenced column '{col_name}' not found in columns.",
                        guidance="Ensure all referenced columns are defined in 'columns'.",
                    )
                )

        # Check cross_field_rule references
        if test.type == "cross_field_rule":
            if_clause = params.get("if", {})
            all_not_null = if_clause.get("all_not_null", [])
            for col_name in all_not_null:
                if col_name not in column_names:
                    errors.append(
                        ValidationError(
                            field=f"{test_prefix}.params.if.all_not_null",
                            message=f"Referenced column '{col_name}' not found.",
                            guidance="Ensure all referenced columns are defined.",
                        )
                    )

    return errors


def _validate_foreign_key_checks(contract: Contract) -> list[ValidationError]:
    """Validate foreign key check configurations."""
    errors = []
    column_names = {col.name for col in contract.columns}

    for i, fk in enumerate(contract.foreign_key_checks):
        fk_prefix = f"foreign_key_checks[{i}]"

        # name is required
        if not fk.name:
            errors.append(
                ValidationError(
                    field=f"{fk_prefix}.name",
                    message="Foreign key check name is required.",
                    guidance="Add a descriptive 'name' for the FK check.",
                )
            )

        # dataset_column must exist in columns
        if fk.dataset_column and fk.dataset_column not in column_names:
            errors.append(
                ValidationError(
                    field=f"{fk_prefix}.dataset_column",
                    message=f"Dataset column '{fk.dataset_column}' not found.",
                    guidance="Ensure the referenced column is defined in 'columns'.",
                )
            )

        # fk_file is required
        if not fk.fk_file:
            errors.append(
                ValidationError(
                    field=f"{fk_prefix}.fk_file",
                    message="FK file reference is required.",
                    guidance="Add 'fk_file' with the FK list filename.",
                )
            )

        # fk_column is required
        if not fk.fk_column:
            errors.append(
                ValidationError(
                    field=f"{fk_prefix}.fk_column",
                    message="FK column is required.",
                    guidance="Add 'fk_column' with the FK column name.",
                )
            )

        # normalization_inherit_from_dataset_column must be true in v1
        if not fk.normalization_inherit_from_dataset_column:
            errors.append(
                ValidationError(
                    field=f"{fk_prefix}.normalization_inherit_from_dataset_column",
                    message="Must be true in v1.",
                    guidance="Set 'normalization_inherit_from_dataset_column: true'.",
                )
            )

        # Validate on_fail
        errors.extend(_validate_failure_handling(fk.on_fail, f"{fk_prefix}.on_fail"))

    return errors


def format_validation_errors(result: ContractValidationResult) -> str:
    """
    Format validation errors for display.

    Args:
        result: The validation result

    Returns:
        Formatted error message string
    """
    if result.is_valid:
        return "Contract is valid."

    lines = ["Contract validation failed:"]
    for error in result.errors:
        lines.append(f"\n- {error.field}: {error.message}")
        lines.append(f"  Guidance: {error.guidance}")

    return "\n".join(lines)
