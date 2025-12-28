"""
Remediation orchestrator.

This module coordinates the execution of all remediation actions
based on a contract configuration.
"""

from typing import Any, Optional

import pandas as pd

from src.contract.schema import Contract
from src.remediation.diff import RemediationDiff, compute_diff
from src.remediation.transformers import (
    apply_column_remediation,
    apply_dataframe_remediation,
    deduplicate_rows,
    COLUMN_TRANSFORMERS,
    DATAFRAME_TRANSFORMERS,
)
from src.validation.results import ValidationResult


def run_remediation(
    df: pd.DataFrame,
    contract: Contract,
    validation_result: Optional[ValidationResult] = None,
) -> tuple[pd.DataFrame, RemediationDiff]:
    """
    Run all remediation actions defined in the contract.

    Args:
        df: The DataFrame to remediate
        contract: The contract with remediation configurations
        validation_result: Optional validation result for targeted remediation

    Returns:
        Tuple of (remediated DataFrame, RemediationDiff)
    """
    # Create a copy to avoid modifying the original
    result_df = df.copy()

    # Track which treatments are applied to each column
    column_treatments: dict[str, list[str]] = {}

    # Apply column-level remediations
    for col_config in contract.columns:
        col_name = col_config.name

        if col_name not in result_df.columns:
            continue

        for rem in col_config.remediation:
            rem_type = rem.type
            rem_params = rem.params

            # Track the treatment for this column
            if col_name not in column_treatments:
                column_treatments[col_name] = []
            column_treatments[col_name].append(_format_treatment_name(rem_type))

            # Check if this is a column or dataframe transformer
            if rem_type in COLUMN_TRANSFORMERS:
                result_df[col_name] = apply_column_remediation(
                    result_df[col_name],
                    rem_type,
                    rem_params,
                )
            elif rem_type in DATAFRAME_TRANSFORMERS:
                result_df = apply_dataframe_remediation(
                    result_df,
                    col_name,
                    rem_type,
                    rem_params,
                )

    # Apply dataset-level remediations (e.g., deduplication)
    # Check if any column has deduplicate_rows remediation
    for col_config in contract.columns:
        for rem in col_config.remediation:
            if rem.type == "deduplicate_rows":
                result_df = deduplicate_rows(result_df, rem.params)
                break

    # Compute the diff with generous sample limit
    # Under 1000 rows: capture all changes
    # Over 1000 rows: capture up to 1000 per column (report will cap at 100)
    total_rows = len(df)
    max_samples = total_rows if total_rows < 1000 else 1000
    diff = compute_diff(
        df,
        result_df,
        max_samples_per_column=max_samples,
        column_treatments=column_treatments,
    )

    return result_df, diff


def apply_failure_handling(
    df: pd.DataFrame,
    contract: Contract,
    validation_result: ValidationResult,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    """
    Apply failure handling policies to the DataFrame.

    Args:
        df: The DataFrame
        contract: The contract
        validation_result: Validation results

    Returns:
        Tuple of (clean_df, quarantine_df, named_quarantines)
    """
    result_df = df.copy()
    quarantine_rows: list[int] = []
    drop_rows: list[int] = []
    named_quarantines: dict[str, list[int]] = {}

    # Group errors by row
    row_errors: dict[int, list[tuple[str, str, str]]] = {}  # row -> [(col, test, action)]

    for cell_error in validation_result.cell_errors:
        idx = cell_error.row_index
        col_name = cell_error.column_name

        # Get failure handling for this column/test
        col_config = _get_column_config(contract, col_name)
        if col_config is None:
            continue

        # Get the action
        action = col_config.failure_handling.action

        # Check if test has override
        for test in col_config.tests:
            if test.type == cell_error.test_type and test.on_fail:
                action = test.on_fail.action
                break

        if idx not in row_errors:
            row_errors[idx] = []

        row_errors[idx].append((col_name, cell_error.test_type, action))

    # Process each row
    for idx, errors in row_errors.items():
        for col_name, test_type, action in errors:
            if action == "set_null":
                result_df.at[idx, col_name] = None

            elif action == "drop_row":
                drop_rows.append(idx)

            elif action == "quarantine_row":
                quarantine_rows.append(idx)

                # Check for named quarantine
                col_config = _get_column_config(contract, col_name)
                if col_config and col_config.failure_handling.quarantine_export_name:
                    q_name = col_config.failure_handling.quarantine_export_name
                    if q_name not in named_quarantines:
                        named_quarantines[q_name] = []
                    named_quarantines[q_name].append(idx)

    # Build quarantine DataFrame
    unique_quarantine = list(set(quarantine_rows))
    quarantine_df = df.loc[df.index.isin(unique_quarantine)].copy()

    # Build named quarantine DataFrames
    named_quarantine_dfs = {}
    for q_name, indices in named_quarantines.items():
        unique_indices = list(set(indices))
        named_quarantine_dfs[q_name] = df.loc[df.index.isin(unique_indices)].copy()

    # Remove dropped and quarantined rows from result
    rows_to_remove = list(set(drop_rows + quarantine_rows))
    result_df = result_df.loc[~result_df.index.isin(rows_to_remove)]

    return result_df, quarantine_df, named_quarantine_dfs


def _get_column_config(contract: Contract, column_name: str):
    """Get column configuration by name."""
    for col in contract.columns:
        if col.name == column_name:
            return col
    return None


def preview_remediation(
    df: pd.DataFrame,
    contract: Contract,
    max_preview_rows: int = 100,
) -> dict[str, Any]:
    """
    Generate a preview of remediation without actually applying it.

    Args:
        df: The DataFrame
        contract: The contract
        max_preview_rows: Maximum rows to include in preview

    Returns:
        Dictionary with preview information
    """
    # Run remediation on a sample
    sample_df = df.head(max_preview_rows).copy()
    remediated_sample, diff = run_remediation(sample_df, contract)

    # Estimate full impact
    estimated_changes = int(
        diff.cells_changed * (len(df) / len(sample_df))
        if len(sample_df) > 0 else 0
    )

    return {
        "sample_size": len(sample_df),
        "sample_changes": diff.cells_changed,
        "sample_rows_changed": diff.rows_changed,
        "estimated_total_changes": estimated_changes,
        "columns_affected": diff.columns_affected,
        "sample_diff": diff,
    }


def get_remediation_summary(
    contract: Contract,
) -> dict[str, list[dict]]:
    """
    Get a summary of configured remediation actions.

    Args:
        contract: The contract

    Returns:
        Dictionary mapping column names to list of remediation configs
    """
    summary = {}

    for col_config in contract.columns:
        if col_config.remediation:
            summary[col_config.name] = [
                {
                    "type": rem.type,
                    "params": rem.params,
                }
                for rem in col_config.remediation
            ]

    return summary


def validate_remediation_config(
    contract: Contract,
) -> list[str]:
    """
    Validate that remediation configurations are valid.

    Args:
        contract: The contract to validate

    Returns:
        List of warning/error messages
    """
    messages = []
    all_rem_types = set(COLUMN_TRANSFORMERS.keys()) | set(DATAFRAME_TRANSFORMERS.keys())
    all_rem_types.add("deduplicate_rows")

    for col_config in contract.columns:
        for rem in col_config.remediation:
            if rem.type not in all_rem_types:
                messages.append(
                    f"Column '{col_config.name}': unknown remediation type '{rem.type}'"
                )

            # Validate specific remediation params
            if rem.type == "date_coerce":
                if not rem.params.get("target_format"):
                    messages.append(
                        f"Column '{col_config.name}': date_coerce requires target_format"
                    )

            if rem.type == "categorical_standardize":
                if not rem.params.get("mapping"):
                    messages.append(
                        f"Column '{col_config.name}': categorical_standardize requires mapping"
                    )

    return messages


def _format_treatment_name(treatment_type: str) -> str:
    """
    Convert a treatment type to a human-readable name.

    Args:
        treatment_type: The snake_case treatment type (e.g., "trim_whitespace")

    Returns:
        Human-readable name (e.g., "Trim Whitespace")
    """
    # Map of treatment types to friendly names
    treatment_names = {
        "trim_whitespace": "Trim Whitespace",
        "remove_punctuation": "Remove Punctuation",
        "to_lowercase": "Convert to Lowercase",
        "to_uppercase": "Convert to Uppercase",
        "to_titlecase": "Convert to Title Case",
        "remove_non_printable": "Remove Non-Printable Characters",
        "standardize_nulls": "Standardize Null Values",
        "date_coerce": "Standardize Date Format",
        "numeric_coerce": "Convert to Number",
        "boolean_coerce": "Standardize Boolean",
        "categorical_standardize": "Standardize Category Values",
        "fill_null": "Fill Null Values",
        "clamp_range": "Clamp to Range",
        "deduplicate_rows": "Remove Duplicate Rows",
    }

    return treatment_names.get(treatment_type, treatment_type.replace("_", " ").title())
