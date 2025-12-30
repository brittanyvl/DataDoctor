"""
Step 5: Export artifacts.

This module implements the export step of the Data Doctor workflow.
"""

import io
import zipfile

import pandas as pd
import streamlit as st

from src.contract.parser import serialize_contract_to_bytes, serialize_contract_to_yaml
from src.file_handling.export import export_dataframe
from src.reporting.html_report import generate_html_report_bytes
from src.session import set_current_step
from src.ui.components import (
    step_header,
    error_box,
    success_box,
    info_box,
    navigation_buttons,
    demo_tip,
)
from src.validation.engine import add_error_columns


def render_step_export():
    """Render the export step."""
    step_header(
        5,
        "Download Data & Diagnostic Reports",
        "Download your cleaned data, reports, and rules.",
    )

    # Show demo tip if in demo mode
    demo_tip(
        "Download the complete package to see all outputs including the HTML report. "
        "In demo mode, you can start over anytime with 'Clear Session' in the sidebar."
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
            set_current_step(4)
            st.rerun()
        return

    # Get base filename
    original_filename = st.session_state.get("uploaded_file_name", "data")
    base_name = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename

    # Export format selection
    st.subheader("Export Settings")

    col1, col2 = st.columns(2)

    with col1:
        output_format = st.radio(
            "Output format",
            options=["CSV", "Excel (.xlsx)"],
            horizontal=True,
        )

    format_ext = "csv" if output_format == "CSV" else "xlsx"

    # XLSX multi-sheet option
    xlsx_multi_sheet = False
    if format_ext == "xlsx":
        with col2:
            xlsx_multi_sheet = st.checkbox(
                "Combine data into one Excel file with multiple sheets",
                value=True,
                help="If checked and multiple data files are included, they will be on separate sheets in one .xlsx file. Otherwise, they will be separate files.",
            )

    # Download Complete Package (primary action - first)
    _render_zip_download(
        df, contract, validation_result, original_filename, base_name, format_ext, xlsx_multi_sheet
    )

    # Individual Downloads (optional)
    with st.expander("Individual Downloads", expanded=False):
        _render_data_export(df, contract, validation_result, base_name, format_ext)
        st.markdown("---")
        _render_report_export(validation_result, original_filename, contract, base_name)

    # Navigation
    st.divider()
    back_clicked, _ = navigation_buttons(
        back_label="Back to Findings",
        show_next=False,
    )

    if back_clicked:
        set_current_step(4)
        st.rerun()

    # Restart option - prominent call to action
    st.divider()
    # Dark green styling for the button
    st.markdown(
        """<style>
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #2F855A !important;
            border-color: #2F855A !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #276749 !important;
            border-color: #276749 !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    if st.button("🔄 Start New Analysis", use_container_width=True, type="primary"):
        # Clear most session state but keep rate limiting
        from src.session import reset_session_state
        reset_session_state()
        st.rerun()


def _render_contract_export(contract, base_name):
    """Render the contract export section prominently."""
    st.subheader("Contract Export")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Download YAML contract
        contract_bytes = serialize_contract_to_bytes(contract)

        st.download_button(
            label="Download Contract (YAML)",
            data=contract_bytes,
            file_name=f"{base_name}_contract.yaml",
            mime="text/yaml",
            use_container_width=True,
        )

    with col2:
        st.markdown(
            "Save this contract to re-run the same validation on future datasets. "
            "Upload it in Step 2 to restore your configuration."
        )

    # Preview YAML in expander
    with st.expander("Preview Contract YAML", expanded=False):
        yaml_content = serialize_contract_to_yaml(contract)
        st.code(yaml_content, language="yaml")


def _has_label_failure_action(contract) -> bool:
    """Check if any field in the contract uses the label_failure action."""
    # Check column failure handling
    for col in contract.columns:
        if col.failure_handling and col.failure_handling.action == "label_failure":
            return True
        # Check column-level tests
        for test in col.tests:
            if test.on_fail and test.on_fail.action == "label_failure":
                return True

    # Check dataset-level tests
    for test in contract.dataset_tests:
        if test.on_fail and test.on_fail.action == "label_failure":
            return True

    # Check foreign key checks
    for fk in contract.foreign_key_checks:
        if fk.on_fail and fk.on_fail.action == "label_failure":
            return True

    return False


def _render_zip_download(df, contract, validation_result, original_filename, base_name, format_ext, xlsx_multi_sheet):
    """Render the main zip download button."""
    st.subheader("Download Complete Package")

    # Prepare all assets
    labeled_df = add_error_columns(df, validation_result)
    remediated_df = st.session_state.get("remediated_dataframe")
    remediation_diff = st.session_state.get("remediation_diff")

    # Build list of what's included
    included_items = []

    # Add cleaned dataset if available (primary output)
    if remediated_df is not None:
        included_items.append("Final cleaned dataset")

    # Add HTML report
    if remediation_diff and remediation_diff.cells_changed > 0:
        included_items.append("Personalized HTML report with data quality results and cleansing summary")
    else:
        included_items.append("Personalized HTML report with data quality results")

    # Add YAML contract
    included_items.append("YAML data contract to reuse settings from this session")

    # Add labeled data only if user selected label_failure action
    if _has_label_failure_action(contract):
        included_items.append("Labeled original dataset (with error columns)")

    info_box("**Included in download:**\n- " + "\n- ".join(included_items))

    # Generate zip
    include_labeled = _has_label_failure_action(contract)
    zip_bytes = _create_export_zip(
        labeled_df=labeled_df,
        remediated_df=remediated_df,
        validation_result=validation_result,
        remediation_diff=remediation_diff,
        contract=contract,
        original_filename=original_filename,
        base_name=base_name,
        format_ext=format_ext,
        xlsx_multi_sheet=xlsx_multi_sheet,
        include_labeled=include_labeled,
    )

    st.download_button(
        label="📦 Download Complete Package (.zip)",
        data=zip_bytes,
        file_name=f"{base_name}_datadoctor_export.zip",
        mime="application/zip",
        use_container_width=True,
        type="primary",
    )


def _create_export_zip(
    labeled_df,
    remediated_df,
    validation_result,
    remediation_diff,
    contract,
    original_filename,
    base_name,
    format_ext,
    xlsx_multi_sheet,
    include_labeled=False,
):
    """Create a zip file containing all export artifacts."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Handle data exports
        if format_ext == "xlsx" and xlsx_multi_sheet and remediated_df is not None and include_labeled:
            # Combine into single xlsx with multiple sheets (only if both are included)
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
                remediated_df.to_excel(writer, sheet_name="Cleaned Data", index=False)
                labeled_df.to_excel(writer, sheet_name="Labeled Data", index=False)
            xlsx_buffer.seek(0)
            zf.writestr(f"{base_name}_data.xlsx", xlsx_buffer.read())
        else:
            # Separate files - always include cleaned data if available
            if remediated_df is not None:
                cleaned_bytes, ext, _ = export_dataframe(remediated_df, output_format=format_ext, escape_formulas=True)
                zf.writestr(f"{base_name}_cleaned{ext}", cleaned_bytes)

            # Only include labeled data if label_failure action is used
            if include_labeled:
                labeled_bytes, ext, _ = export_dataframe(labeled_df, output_format=format_ext, escape_formulas=True)
                zf.writestr(f"{base_name}_labeled{ext}", labeled_bytes)

        # HTML Report (includes data cleansing summary if available)
        report_bytes = generate_html_report_bytes(
            validation_result,
            original_filename,
            contract.contract_id,
            remediation_diff,
        )
        zf.writestr(f"{base_name}_report.html", report_bytes)

        # Contract YAML
        contract_bytes = serialize_contract_to_bytes(contract)
        zf.writestr(f"{base_name}_contract.yaml", contract_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def _render_data_export(df, contract, validation_result, base_name, format_ext):
    """Render individual data export buttons."""
    st.markdown("**Data Files**")

    col1, col2 = st.columns(2)

    with col1:
        # Add error columns to original data
        labeled_df = add_error_columns(df, validation_result)

        # Export
        data_bytes, ext, mime = export_dataframe(
            labeled_df,
            output_format=format_ext,
            escape_formulas=True,
        )

        st.download_button(
            label=f"Labeled Data ({format_ext.upper()})",
            data=data_bytes,
            file_name=f"{base_name}_labeled{ext}",
            mime=mime,
            use_container_width=True,
        )

    with col2:
        remediated_df = st.session_state.get("remediated_dataframe")

        if remediated_df is not None:
            # Export remediated data
            data_bytes, ext, mime = export_dataframe(
                remediated_df,
                output_format=format_ext,
                escape_formulas=True,
            )

            st.download_button(
                label=f"Cleaned Data ({format_ext.upper()})",
                data=data_bytes,
                file_name=f"{base_name}_cleaned{ext}",
                mime=mime,
                use_container_width=True,
            )
        else:
            st.caption("No cleaned data available.")


def _render_report_export(validation_result, original_filename, contract, base_name):
    """Render individual report export buttons."""
    st.markdown("**Reports**")

    # Get remediation diff if available
    remediation_diff = st.session_state.get("remediation_diff")

    # Generate HTML report (includes data cleansing summary if available)
    report_bytes = generate_html_report_bytes(
        validation_result,
        original_filename,
        contract.contract_id,
        remediation_diff,
    )

    report_label = "Data Quality Report (HTML)"
    if remediation_diff and remediation_diff.cells_changed > 0:
        report_label = "Data Quality Report with Cleansing Summary (HTML)"

    st.download_button(
        label=report_label,
        data=report_bytes,
        file_name=f"{base_name}_report.html",
        mime="text/html",
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("**Contract**")

    # Contract YAML download
    contract_bytes = serialize_contract_to_bytes(contract)

    st.download_button(
        label="Validation Rules Contract (YAML)",
        data=contract_bytes,
        file_name=f"{base_name}_contract.yaml",
        mime="text/yaml",
        use_container_width=True,
    )
