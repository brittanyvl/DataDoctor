"""
Step 4: Validation Results.

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
    demo_tip,
)
from src.validation.engine import (
    run_validation,
    add_error_columns,
    get_validation_summary_dict,
)


def render_step_results():
    """Render the validation results step."""
    step_header(
        4,
        "Diagnostic Findings",
        "Review data quality summary and diagnostic findings.",
    )

    # Show demo tip if in demo mode
    demo_tip(
        "Found issues! Expand 'Sample Failures' below to see specific errors. "
        "The Data Cleansing Applied section shows what was automatically fixed."
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

    # Auto-apply remediation if configured in Data Cleaning step
    _auto_apply_remediation(df, contract)

    # Navigation
    st.divider()
    back_clicked, next_clicked = navigation_buttons(
        back_label="Back to Data Cleaning",
        next_label="Access Full Downloads",
    )

    if back_clicked:
        # Clear validation and remediation results when going back
        st.session_state["validation_results"] = None
        st.session_state["remediated_dataframe"] = None
        st.session_state["remediation_diff"] = None
        st.session_state["remediation_approved"] = None
        set_current_step(3)
        st.rerun()

    if next_clicked:
        set_current_step(5)
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
        with st.spinner("Running diagnostics..."):
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
    st.subheader("Diagnostic Findings")

    summary = validation_result.summary

    # Status banner
    if validation_result.is_valid:
        success_box("All checks passed - no blocking issues found.")
    else:
        if validation_result.blocking_errors:
            error_box(
                f"We found {len(validation_result.blocking_errors)} blocking issues that need attention."
            )
        else:
            warning_box(
                f"Diagnostics completed - {summary.total_errors} issues found."
            )

    # Metrics - simple counts without misleading delta arrows
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Tests Run", summary.total_tests_run)

    with col2:
        pass_rate = f"{summary.total_tests_passed}/{summary.total_tests_run}"
        st.metric("Tests Passed", pass_rate)

    with col3:
        error_display = f"{summary.rows_with_errors:,} ({summary.error_rate_percent}%)"
        st.metric("Rows with Errors", error_display)

    with col4:
        st.metric("Clean Rows", f"{summary.clean_rows:,}")

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


def _auto_apply_remediation(df, contract):
    """Automatically apply remediation based on Data Cleaning step configuration."""
    # Check if contract has any remediation configured
    has_remediation = any(
        col.remediation for col in contract.columns
    )

    if not has_remediation:
        return  # No cleaning configured

    # Check if already applied
    if st.session_state.get("remediated_dataframe") is not None:
        return  # Already applied

    # Auto-apply remediation
    with st.spinner("Applying data cleaning..."):
        remediated_df, diff = run_remediation(df, contract)

        st.session_state["remediated_dataframe"] = remediated_df
        st.session_state["remediation_diff"] = diff
        st.session_state["remediation_approved"] = True

    # Show summary of cleaning applied
    if diff and diff.cells_changed > 0:
        st.divider()
        st.subheader("Data Cleansing Applied")
        success_box(
            f"Cleaned {diff.cells_changed:,} cells across {diff.rows_changed:,} rows. "
            f"Columns affected: {', '.join(diff.columns_affected) or 'None'}"
        )

        # Show sample changes (filter out null-to-null)
        with st.expander("View Sample Changes", expanded=False):
            sample_df = get_sample_changes_table(diff, max_rows=20)
            if not sample_df.empty:
                # Filter out rows where Original and New are both (null)
                sample_df = sample_df[
                    ~((sample_df["Original"] == "(null)") & (sample_df["New"] == "(null)"))
                ]
                if not sample_df.empty:
                    st.dataframe(sample_df, use_container_width=True, hide_index=True)
                else:
                    st.caption("No changes to display.")
