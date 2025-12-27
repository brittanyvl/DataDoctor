"""
Step 4: Export artifacts.

This module implements the export step of the Data Doctor workflow.
"""

import streamlit as st

from src.contract.parser import serialize_contract_to_bytes, serialize_contract_to_yaml
from src.file_handling.export import export_dataframe
from src.reporting.html_report import (
    generate_html_report_bytes,
    generate_remediation_summary_bytes,
)
from src.session import set_current_step
from src.ui.components import (
    step_header,
    error_box,
    success_box,
    info_box,
    navigation_buttons,
)
from src.validation.engine import add_error_columns


def render_step_export():
    """Render the export step."""
    step_header(
        4,
        "Export",
        "Download your cleaned data, reports, and contract.",
    )

    # Check prerequisites
    df = st.session_state.get("dataframe")
    contract = st.session_state.get("contract")
    validation_result = st.session_state.get("validation_results")

    if df is None or contract is None:
        error_box("Missing data or contract. Please complete previous steps.")
        return

    if validation_result is None:
        error_box("No validation results. Please run validation first.")
        if st.button("Go to Results"):
            set_current_step(3)
            st.rerun()
        return

    # Get base filename
    original_filename = st.session_state.get("uploaded_file_name", "data")
    base_name = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename

    # Export format selection
    st.subheader("Export Settings")

    output_format = st.radio(
        "Output format",
        options=["CSV", "Excel (.xlsx)"],
        horizontal=True,
    )

    format_ext = "csv" if output_format == "CSV" else "xlsx"

    st.divider()

    # Export sections
    _render_data_export(df, contract, validation_result, base_name, format_ext)
    _render_report_export(validation_result, original_filename, contract, base_name)

    # Advanced settings (includes YAML contract)
    st.divider()
    _render_advanced_settings(contract, base_name)

    # Navigation
    st.divider()
    back_clicked, _ = navigation_buttons(
        back_label="Back to Results",
        show_next=False,
    )

    if back_clicked:
        set_current_step(3)
        st.rerun()

    # Restart option
    st.divider()
    if st.button("Start New Analysis"):
        # Clear most session state but keep rate limiting
        from src.session import reset_session_state
        reset_session_state()
        st.rerun()


def _render_data_export(df, contract, validation_result, base_name, format_ext):
    """Render data export section."""
    st.subheader("Data Export")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Original Data with Error Labels**")

        # Add error columns to original data
        labeled_df = add_error_columns(df, validation_result)

        # Export
        data_bytes, ext, mime = export_dataframe(
            labeled_df,
            output_format=format_ext,
            escape_formulas=True,
        )

        st.download_button(
            label=f"Download Labeled Data ({format_ext.upper()})",
            data=data_bytes,
            file_name=f"{base_name}_labeled{ext}",
            mime=mime,
            use_container_width=True,
        )

        st.caption(
            "Original data with error labels added. "
            "Includes __data_doctor_errors__ and __data_doctor_status__ columns."
        )

    with col2:
        st.markdown("**Cleaned Data**")

        remediated_df = st.session_state.get("remediated_dataframe")

        if remediated_df is not None:
            # Export remediated data
            data_bytes, ext, mime = export_dataframe(
                remediated_df,
                output_format=format_ext,
                escape_formulas=True,
            )

            st.download_button(
                label=f"Download Cleaned Data ({format_ext.upper()})",
                data=data_bytes,
                file_name=f"{base_name}_cleaned{ext}",
                mime=mime,
                use_container_width=True,
            )

            st.caption(
                "Data with remediation applied. "
                f"{len(remediated_df):,} rows."
            )
        else:
            info_box(
                "No cleaned data available. "
                "Apply remediation in the Results step to generate cleaned data."
            )


def _render_report_export(validation_result, original_filename, contract, base_name):
    """Render report export section."""
    st.subheader("Reports")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Data Quality Report (HTML)**")

        # Get remediation diff if available
        remediation_diff = st.session_state.get("remediation_diff")

        # Generate HTML report
        report_bytes = generate_html_report_bytes(
            validation_result,
            original_filename,
            contract.contract_id,
            remediation_diff,
        )

        st.download_button(
            label="Download HTML Report",
            data=report_bytes,
            file_name=f"{base_name}_report.html",
            mime="text/html",
            use_container_width=True,
        )

        st.caption(
            "Human-readable report with validation summary, "
            "test results, and sample failures."
        )

    with col2:
        st.markdown("**Remediation Summary (HTML)**")

        remediation_diff = st.session_state.get("remediation_diff")

        if remediation_diff:
            summary_bytes = generate_remediation_summary_bytes(
                remediation_diff,
                original_filename,
            )

            st.download_button(
                label="Download Remediation Summary",
                data=summary_bytes,
                file_name=f"{base_name}_remediation_summary.html",
                mime="text/html",
                use_container_width=True,
            )

            st.caption(
                "Summary of all changes made during remediation."
            )
        else:
            info_box("No remediation applied. Apply remediation to generate summary.")


def _render_advanced_settings(contract, base_name):
    """Render advanced settings including YAML contract export."""
    with st.expander("Advanced Settings", expanded=False):
        st.subheader("Contract Export")

        st.markdown(
            "Download the YAML contract to re-run the same validation on future datasets. "
            "Upload this file in the Contract step to restore your configuration."
        )

        # Download YAML contract
        contract_bytes = serialize_contract_to_bytes(contract)

        st.download_button(
            label="Download Contract (YAML)",
            data=contract_bytes,
            file_name=f"{base_name}_contract.yaml",
            mime="text/yaml",
            use_container_width=True,
        )

        # Preview YAML
        st.markdown("---")
        st.markdown("**Contract Preview**")
        yaml_content = serialize_contract_to_yaml(contract)
        st.code(yaml_content, language="yaml")
