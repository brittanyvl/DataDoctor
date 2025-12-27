"""
Step 3: Validation Results.

This module implements the validation results step of the Data Doctor workflow,
including dataset summary and remediation options.
"""

import streamlit as st
import pandas as pd

from src.contract.validator import validate_contract, format_validation_errors
from src.remediation.diff import format_diff_summary, get_sample_changes_table
from src.remediation.engine import run_remediation, preview_remediation
from src.reporting.summary import generate_dataset_summary
from src.session import set_current_step, set_processing
from src.ui.components import (
    step_header,
    error_box,
    success_box,
    warning_box,
    info_box,
    navigation_buttons,
    status_badge,
    collapsible_section,
)
from src.validation.engine import (
    run_validation,
    add_error_columns,
    get_validation_summary_dict,
)


def render_step_results():
    """Render the validation results step."""
    step_header(
        3,
        "Validation Results",
        "Review data quality summary, validation results, and apply remediation.",
    )

    # Check prerequisites
    df = st.session_state.get("dataframe")
    contract = st.session_state.get("contract")

    if df is None or contract is None:
        error_box("Missing data or contract. Please complete previous steps.")
        return

    # Run validation if not already done
    validation_result = st.session_state.get("validation_results")

    if validation_result is None:
        _run_validation(df, contract)
        return

    # Display data summary first
    _display_data_summary(df)

    st.divider()

    # Display validation results
    _display_validation_summary(validation_result)
    _display_column_results(validation_result)
    _display_failed_examples(validation_result)

    # Remediation section
    st.divider()
    _render_remediation_section(df, contract, validation_result)

    # Navigation
    st.divider()
    back_clicked, next_clicked = navigation_buttons(
        back_label="Back to Contract",
        next_label="Continue to Export",
    )

    if back_clicked:
        # Clear validation results when going back
        st.session_state["validation_results"] = None
        set_current_step(2)
        st.rerun()

    if next_clicked:
        set_current_step(4)
        st.rerun()


def _run_validation(df, contract):
    """Run validation and store results."""
    # Validate contract first
    contract_validation = validate_contract(contract)
    if not contract_validation.is_valid:
        error_box(format_validation_errors(contract_validation))
        return

    set_processing(True)

    try:
        with st.spinner("Running validation..."):
            # Get FK dataframe if available
            fk_df = st.session_state.get("fk_dataframe")

            # Run validation
            validation_result = run_validation(df, contract, fk_df)

            # Store results
            st.session_state["validation_results"] = validation_result
            st.session_state["validation_complete"] = True

        st.rerun()

    finally:
        set_processing(False)


def _display_data_summary(df):
    """Display dataset summary statistics."""
    st.subheader("Dataset Summary")

    # Generate summary
    summary = generate_dataset_summary(df)

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Rows", f"{summary['row_count']:,}")

    with col2:
        st.metric("Total Columns", summary['column_count'])

    with col3:
        st.metric("Memory Usage", f"{summary['memory_mb']:.1f} MB")

    with col4:
        completeness = summary.get('overall_completeness', 0)
        st.metric("Data Completeness", f"{completeness:.1f}%")

    # Column type breakdown
    with st.expander("Column Details", expanded=False):
        col_data = []
        for col_name, col_info in summary.get('columns', {}).items():
            col_data.append({
                "Column": col_name,
                "Type": col_info.get('dtype', 'unknown'),
                "Non-Null": f"{col_info.get('non_null_count', 0):,}",
                "Null": f"{col_info.get('null_count', 0):,}",
                "Unique": f"{col_info.get('unique_count', 0):,}",
                "Completeness": f"{col_info.get('completeness', 0):.1f}%",
            })

        if col_data:
            st.dataframe(pd.DataFrame(col_data), use_container_width=True, hide_index=True)


def _display_validation_summary(validation_result):
    """Display validation summary metrics."""
    st.subheader("Validation Results")

    summary = validation_result.summary

    # Status banner
    if validation_result.is_valid:
        success_box("Validation passed - no blocking errors found.")
    else:
        if validation_result.blocking_errors:
            error_box(
                f"Validation failed with {len(validation_result.blocking_errors)} blocking errors."
            )
        else:
            warning_box(
                f"Validation completed with {summary.total_errors} errors."
            )

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Tests Run", summary.total_tests_run)

    with col2:
        st.metric(
            "Tests Passed",
            summary.total_tests_passed,
            delta=f"{summary.total_tests_passed}/{summary.total_tests_run}",
        )

    with col3:
        st.metric(
            "Rows with Errors",
            f"{summary.rows_with_errors:,}",
            delta=f"{summary.error_rate_percent}%",
            delta_color="inverse",
        )

    with col4:
        st.metric(
            "Clean Rows",
            f"{summary.clean_rows:,}",
        )

    # Blocking errors
    if validation_result.blocking_errors:
        with st.expander("Blocking Errors", expanded=True):
            for error in validation_result.blocking_errors:
                st.error(error)


def _display_column_results(validation_result):
    """Display per-column validation results."""
    st.subheader("Column Results")

    # Build results table
    rows = []
    for col_name, col_result in validation_result.column_results.items():
        rows.append({
            "Column": col_name,
            "Type": col_result.data_type,
            "Tests": col_result.total_tests,
            "Passed": col_result.passed_tests,
            "Failed": col_result.failed_tests,
            "Status": col_result.overall_status,
        })

    if rows:
        results_df = pd.DataFrame(rows)
        st.dataframe(results_df, use_container_width=True, hide_index=True)

    # Dataset tests
    if validation_result.dataset_test_results:
        with st.expander("Dataset-Level Test Results", expanded=False):
            for test_result in validation_result.dataset_test_results:
                status = "PASS" if test_result.passed else "FAIL"
                st.markdown(
                    f"**{test_result.test_type}** ({test_result.severity}): "
                    f"{status} - {test_result.message}"
                )

    # FK check results
    if validation_result.fk_check_results:
        with st.expander("Foreign Key Check Results", expanded=False):
            for fk_result in validation_result.fk_check_results:
                status = "PASS" if fk_result.passed else "FAIL"
                st.markdown(
                    f"**{fk_result.name}**: {status} - "
                    f"{fk_result.missing_count} missing values"
                )


def _display_failed_examples(validation_result):
    """Display examples of failed validations."""
    if not validation_result.cell_errors:
        return

    st.subheader("Sample Failures")

    with st.expander(
        f"View {len(validation_result.cell_errors)} cell errors",
        expanded=False,
    ):
        # Build table of errors
        error_rows = []
        for cell_error in validation_result.cell_errors[:100]:
            error_rows.append({
                "Row": cell_error.row_index,
                "Column": cell_error.column_name,
                "Test": cell_error.test_type,
                "Value": str(cell_error.original_value)[:50],
                "Severity": cell_error.severity,
            })

        if error_rows:
            errors_df = pd.DataFrame(error_rows)
            st.dataframe(errors_df, use_container_width=True, hide_index=True)

            if len(validation_result.cell_errors) > 100:
                st.caption(
                    f"Showing first 100 of {len(validation_result.cell_errors)} errors"
                )


def _render_remediation_section(df, contract, validation_result):
    """Render the remediation section."""
    st.subheader("Remediation")

    # Check if contract has any remediation configured
    has_remediation = any(
        col.remediation for col in contract.columns
    )

    if not has_remediation:
        info_box(
            "No remediation actions configured. "
            "Add remediation rules in the Contract step to enable data cleaning."
        )
        return

    # Preview remediation
    if st.button("Preview Remediation"):
        with st.spinner("Generating preview..."):
            preview = preview_remediation(df, contract)

        st.markdown(f"""
        **Estimated Impact:**
        - Sample size: {preview['sample_size']} rows
        - Changes in sample: {preview['sample_changes']} cells
        - Estimated total changes: {preview['estimated_total_changes']:,} cells
        - Columns affected: {', '.join(preview['columns_affected']) or 'None'}
        """)

    # Run remediation
    remediated_df = st.session_state.get("remediated_dataframe")

    if remediated_df is None:
        st.markdown("---")
        st.markdown("**Apply Remediation**")

        warning_box(
            "Remediation will create a cleaned copy of your data. "
            "The original data is never modified."
        )

        if st.button("Apply Remediation", type="primary"):
            with st.spinner("Applying remediation..."):
                remediated_df, diff = run_remediation(df, contract)

                st.session_state["remediated_dataframe"] = remediated_df
                st.session_state["remediation_diff"] = diff
                st.session_state["remediation_approved"] = True

            success_box("Remediation applied successfully!")
            st.rerun()
    else:
        success_box("Remediation has been applied.")

        diff = st.session_state.get("remediation_diff")
        if diff:
            st.markdown(f"""
            **Remediation Results:**
            - Rows changed: {diff.rows_changed:,}
            - Cells changed: {diff.cells_changed:,}
            - Columns affected: {', '.join(diff.columns_affected)}
            """)

            # Show sample changes
            with st.expander("View Sample Changes", expanded=False):
                sample_df = get_sample_changes_table(diff, max_rows=20)
                if not sample_df.empty:
                    st.dataframe(sample_df, use_container_width=True, hide_index=True)

        # Option to clear remediation
        if st.button("Clear Remediation"):
            st.session_state["remediated_dataframe"] = None
            st.session_state["remediation_diff"] = None
            st.session_state["remediation_approved"] = False
            st.rerun()
