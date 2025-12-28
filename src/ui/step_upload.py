"""
Step 1: Upload dataset and configure columns.

This module implements the file upload step of the Data Doctor workflow,
including column name configuration and contract upload options.
"""

import streamlit as st
import pandas as pd
import yaml

from src.constants import (
    FAILURE_ACTION_LABELS,
    FAILURE_LABEL_TO_ACTION,
    MAX_COLUMN_COUNT,
    MAX_ROW_COUNT,
    MAX_UPLOAD_SIZE_MB,
    SUPPORTED_EXTENSIONS,
)
from src.file_handling.readers import (
    get_excel_sheet_names,
    read_file,
    validate_dataframe,
)
from src.file_handling.upload import (
    validate_upload,
    validate_dataframe_limits,
)
from src.session import (
    check_rate_limit,
    compute_file_hash,
    record_upload,
    reset_from_step,
    set_current_step,
    clear_error,
    set_processing,
)
from src.ui.components import (
    step_header,
    error_box,
    warning_box,
    success_box,
    info_box,
    data_preview,
    navigation_buttons,
)
from src.contract.schema import dict_to_contract


def render_step_upload():
    """Render the file upload step."""
    # Compact step header without extra description
    st.markdown("### Step 1: Upload Dataset")
    st.caption(
        f"Max {MAX_UPLOAD_SIZE_MB}MB, {MAX_ROW_COUNT:,} rows, {MAX_COLUMN_COUNT} columns. "
        f"Formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )

    # Check rate limit
    is_allowed, wait_seconds = check_rate_limit()
    if not is_allowed:
        warning_box(
            f"Rate limit reached. Please wait {wait_seconds} seconds before uploading again."
        )
        return

    # Check upload mode - if using contract flow, stay in that view
    upload_mode = st.session_state.get("upload_mode")
    if upload_mode == "contract":
        # Stay in contract upload flow until auto-navigation happens
        _render_contract_upload()
        return

    # Check if we have a file loaded already
    df = st.session_state.get("dataframe")

    if df is None:
        # Show the two-path selection
        _render_start_options()
    else:
        # File is loaded - show configuration
        _show_current_file()
        _render_column_configuration()

        # Navigation
        st.divider()
        _, next_clicked = navigation_buttons(
            show_back=False,
            next_label="Order Diagnostics",
            next_disabled=False,
        )

        if next_clicked:
            # Apply any pending column renames before moving on
            _apply_column_renames()
            set_current_step(2)
            st.rerun()


def _render_start_options():
    """Render the two starting options: Start Fresh or Use Existing Contract."""
    # Check what mode we're in
    upload_mode = st.session_state.get("upload_mode", None)

    if upload_mode is None:
        # Show the two options
        st.markdown("**How would you like to start?**")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                '<div style="background-color: #EDF2F7; padding: 20px; border-radius: 8px; '
                'border: 2px solid #E2E8F0; text-align: center; height: 100%;">'
                '<p style="font-weight: 600; color: #2D3748; margin-bottom: 8px;">Start Fresh</p>'
                '<p style="color: #718096; font-size: 0.9rem;">Create new diagnostic and treatment rules from scratch</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("📄 Start Fresh", use_container_width=True, type="primary"):
                st.session_state["upload_mode"] = "fresh"
                st.rerun()

        with col2:
            st.markdown(
                '<div style="background-color: #EDF2F7; padding: 20px; border-radius: 8px; '
                'border: 2px solid #E2E8F0; text-align: center; height: 100%;">'
                '<p style="font-weight: 600; color: #2D3748; margin-bottom: 8px;">Use Existing Contract</p>'
                '<p style="color: #718096; font-size: 0.9rem;">Load a saved contract to diagnose and treat data from saved settings</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("📋 Use Existing Contract", use_container_width=True):
                st.session_state["upload_mode"] = "contract"
                st.rerun()

    elif upload_mode == "fresh":
        _render_fresh_upload()

    elif upload_mode == "contract":
        _render_contract_upload()


def _render_fresh_upload():
    """Render the fresh upload flow - just file upload."""
    # Back button
    if st.button("← Back to options"):
        st.session_state["upload_mode"] = None
        st.rerun()

    st.markdown("**Upload your data file**")

    # Check if we're in sheet selection mode
    pending_file = st.session_state.get("pending_file_content")
    if pending_file is not None:
        _render_sheet_selection()
        return

    uploader_version = st.session_state.get("uploader_version", 0)

    primary_file = st.file_uploader(
        "Choose your data file",
        type=[ext.lstrip('.') for ext in SUPPORTED_EXTENSIONS],
        help="Upload a CSV or Excel file containing your data",
        key=f"primary_file_uploader_v{uploader_version}",
    )

    if primary_file is not None:
        _handle_primary_file(primary_file)


def _render_contract_upload():
    """Render the contract-first upload flow - wait for BOTH files before processing."""
    # Back button
    if st.button("← Back to options"):
        st.session_state["upload_mode"] = None
        # Clear any pending files
        for key in ["pending_contract_file", "pending_data_file", "pending_data_filename",
                    "uploaded_contract", "contract_auto_applied"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    uploader_version = st.session_state.get("uploader_version", 0)

    st.markdown("Upload both files to run diagnostics with your saved settings.")

    # Show both uploaders side by side
    upload_cols = st.columns(2)

    with upload_cols[0]:
        st.markdown("**Contract File (YAML)**")
        contract_file = st.file_uploader(
            "Choose contract YAML file",
            type=["yaml", "yml"],
            help="Upload a Data Doctor contract from a previous run",
            key=f"contract_file_uploader_v{uploader_version}",
        )

    with upload_cols[1]:
        st.markdown("**Data File**")
        data_file = st.file_uploader(
            "Choose your data file",
            type=[ext.lstrip('.') for ext in SUPPORTED_EXTENSIONS],
            help="Upload a CSV or Excel file to diagnose and treat",
            key=f"contract_data_uploader_v{uploader_version}",
        )

    # Only process when BOTH files are present
    if contract_file is not None and data_file is not None:
        # Process both files and navigate to Step 4
        _process_contract_and_data(contract_file, data_file)


def _process_contract_and_data(contract_file, data_file):
    """Process both contract and data file together, then navigate to Step 4."""
    with st.spinner("Loading contract and data, applying settings..."):
        # 1. Parse the contract
        try:
            content = contract_file.read()
            contract_file.seek(0)
            contract_data = yaml.safe_load(content.decode("utf-8"))
            contract = dict_to_contract(contract_data)
        except yaml.YAMLError as e:
            error_box(f"Invalid YAML format: {str(e)}")
            return
        except Exception as e:
            error_box(f"Error loading contract: {str(e)}")
            return

        # 2. Read and validate the data file
        data_content = data_file.read()
        data_file.seek(0)
        file_hash = compute_file_hash(data_content)

        # Validate upload
        validation_result = validate_upload(
            data_file.name,
            len(data_content),
            data_file.type,
        )

        if not validation_result.is_valid:
            error_box(validation_result.error_message)
            return

        file_ext = validation_result.file_extension

        # Handle Excel sheet selection if needed
        if file_ext in {".xlsx", ".xls", ".xlsb"}:
            sheet_result = get_excel_sheet_names(data_content, file_ext)
            if not sheet_result.success:
                error_box(sheet_result.error_message)
                return

            if len(sheet_result.sheet_names) > 1:
                # For now, use the first sheet. Could add sheet selection later.
                sheet_name = sheet_result.sheet_names[0]
                info_box(f"Using first sheet: {sheet_name}")
            else:
                sheet_name = sheet_result.sheet_names[0]
        else:
            sheet_name = None

        # Get import settings from contract
        import_settings = contract.dataset.import_settings
        skip_rows = import_settings.skip_rows
        skip_footer_rows = import_settings.skip_footer_rows

        # Read the file
        read_result = read_file(
            data_content,
            data_file.name,
            file_ext,
            sheet_name=sheet_name,
            skip_rows=skip_rows,
            skip_footer_rows=skip_footer_rows,
        )

        if not read_result.success:
            error_box(read_result.error_message)
            return

        df = read_result.dataframe

        # Validate dataframe
        is_valid, error_msg = validate_dataframe(df)
        if not is_valid:
            error_box(error_msg)
            return

        is_valid, error_msg = validate_dataframe_limits(len(df), len(df.columns))
        if not is_valid:
            error_box(error_msg)
            return

        # 3. Apply contract import settings (column renames, etc.)
        # Apply quick actions to column names
        qa = import_settings.quick_actions
        if any([qa.to_lowercase, qa.to_uppercase, qa.to_titlecase,
                qa.trim_whitespace, qa.remove_punctuation, qa.replace_spaces_with_underscores]):
            import re
            import string
            new_columns = []
            for col in df.columns:
                new_name = str(col)
                if qa.trim_whitespace:
                    new_name = re.sub(r'^\s+|\s+$', '', new_name)
                if qa.remove_punctuation:
                    new_name = "".join(c for c in new_name if c not in string.punctuation)
                if qa.replace_spaces_with_underscores:
                    new_name = re.sub(r'\s+', '_', new_name)
                if qa.to_lowercase:
                    new_name = new_name.lower()
                elif qa.to_uppercase:
                    new_name = new_name.upper()
                elif qa.to_titlecase:
                    new_name = new_name.title()
                new_columns.append(new_name)
            df.columns = new_columns

        # Apply column renames from contract
        if import_settings.column_renames:
            df = df.rename(columns=import_settings.column_renames)

        # 4. Store everything in session state
        st.session_state["uploaded_file_name"] = data_file.name
        st.session_state["file_hash"] = file_hash
        st.session_state["file_content"] = data_content
        st.session_state["file_ext"] = file_ext
        st.session_state["dataframe"] = df
        st.session_state["sheet_name"] = sheet_name
        st.session_state["applied_skip_rows"] = skip_rows
        st.session_state["applied_skip_footer_rows"] = skip_footer_rows
        st.session_state["column_renames"] = {col: col for col in df.columns}
        st.session_state["columns_to_ignore"] = set(import_settings.columns_to_ignore or [])
        st.session_state["ignored_columns"] = list(import_settings.columns_to_ignore or [])

        # Store the contract
        st.session_state["uploaded_contract"] = contract
        st.session_state["contract"] = contract
        st.session_state["contract_source"] = "uploaded"
        st.session_state["contract_auto_applied"] = True

        # 5. Navigate directly to Step 4
        set_current_step(4)
        st.rerun()


def _render_contract_summary(contract):
    """Render a human-readable summary of the contract."""
    # Overview metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Columns", len(contract.columns))

    with col2:
        total_tests = sum(len(c.tests) for c in contract.columns) + len(contract.dataset_tests)
        st.metric("Diagnostic Rules", total_tests)

    with col3:
        total_remediation = sum(len(c.remediation) for c in contract.columns)
        st.metric("Treatment Rules", total_remediation)

    # Column details
    st.markdown("**Column Diagnostics:**")

    for col_config in contract.columns:
        # Build column summary line
        col_info = f"• **{col_config.name}** ({col_config.data_type})"

        details = []
        if col_config.required:
            details.append("required")

        # List tests
        test_names = [t.type.replace("_", " ") for t in col_config.tests]
        if test_names:
            details.append(f"tests: {', '.join(test_names)}")

        # List remediation
        rem_names = [r.type.replace("_", " ") for r in col_config.remediation]
        if rem_names:
            details.append(f"treatments: {', '.join(rem_names)}")

        if details:
            col_info += f" — {'; '.join(details)}"

        st.markdown(col_info)

    # Dataset-level tests
    if contract.dataset_tests:
        st.markdown("**Dataset-Level Diagnostics:**")
        for test in contract.dataset_tests:
            st.markdown(f"• {test.type.replace('_', ' ')} ({test.severity})")

    # Foreign key checks
    if contract.foreign_key_checks:
        st.markdown("**Foreign Key Checks:**")
        for fk in contract.foreign_key_checks:
            st.markdown(f"• {fk.name}: {fk.dataset_column} → {fk.fk_column}")


def _handle_primary_file(uploaded_file):
    """Handle primary file upload."""
    file_content = uploaded_file.read()
    uploaded_file.seek(0)

    new_hash = compute_file_hash(file_content)
    current_hash = st.session_state.get("file_hash")

    if new_hash == current_hash:
        return  # Same file, no need to re-process

    # Reset downstream state
    reset_from_step(1)
    clear_error()

    # Validate upload
    validation_result = validate_upload(
        uploaded_file.name,
        len(file_content),
        uploaded_file.type,
    )

    if not validation_result.is_valid:
        error_box(validation_result.error_message)
        return

    record_upload()
    file_ext = validation_result.file_extension

    # Check for multi-sheet Excel
    if file_ext in {".xlsx", ".xls", ".xlsb"}:
        sheet_result = get_excel_sheet_names(file_content, file_ext)
        if not sheet_result.success:
            error_box(sheet_result.error_message)
            return

        if len(sheet_result.sheet_names) > 1:
            # Store file for sheet selection
            st.session_state["pending_file_content"] = file_content
            st.session_state["pending_file_name"] = uploaded_file.name
            st.session_state["pending_file_ext"] = file_ext
            st.session_state["pending_file_hash"] = new_hash
            st.session_state["available_sheets"] = sheet_result.sheet_names
            st.rerun()
        else:
            # Single sheet, load directly
            _load_primary_data(file_content, uploaded_file.name, file_ext,
                             sheet_result.sheet_names[0], new_hash)
    else:
        # CSV file, load directly
        _load_primary_data(file_content, uploaded_file.name, file_ext, None, new_hash)


def _render_sheet_selection():
    """Render sheet selection for multi-sheet Excel files."""
    sheets = st.session_state.get("available_sheets", [])
    filename = st.session_state.get("pending_file_name", "")

    st.info(f"**{filename}** contains {len(sheets)} sheets. Please select which sheet to use.")

    primary_sheet = st.selectbox(
        "Select sheet containing your data",
        options=sheets,
        key="primary_sheet_select",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Sheet", type="primary", use_container_width=True):
            file_content = st.session_state["pending_file_content"]
            file_ext = st.session_state["pending_file_ext"]
            file_hash = st.session_state["pending_file_hash"]

            # Load primary data
            _load_primary_data(file_content, filename, file_ext, primary_sheet, file_hash)

            # Clear pending state
            _clear_pending_file_state()
            st.rerun()

    with col2:
        if st.button("Cancel", use_container_width=True):
            _clear_pending_file_state()
            st.rerun()


def _clear_pending_file_state():
    """Clear pending file state after sheet selection."""
    for key in ["pending_file_content", "pending_file_name", "pending_file_ext",
                "pending_file_hash", "available_sheets"]:
        if key in st.session_state:
            del st.session_state[key]


def _load_primary_data(file_content, filename, file_ext, sheet_name, file_hash):
    """Load primary data file into session state."""
    set_processing(True)

    try:
        skip_rows = st.session_state.get("skip_rows", 0)
        skip_footer_rows = st.session_state.get("skip_footer_rows", 0)

        read_result = read_file(
            file_content,
            filename,
            file_ext,
            sheet_name=sheet_name,
            skip_rows=skip_rows,
            skip_footer_rows=skip_footer_rows,
        )

        if not read_result.success:
            error_box(read_result.error_message)
            return

        df = read_result.dataframe

        # Validate
        is_valid, error_msg = validate_dataframe(df)
        if not is_valid:
            error_box(error_msg)
            return

        is_valid, error_msg = validate_dataframe_limits(len(df), len(df.columns))
        if not is_valid:
            error_box(error_msg)
            return

        # Store in session state
        st.session_state["uploaded_file_name"] = filename
        st.session_state["file_hash"] = file_hash
        st.session_state["file_content"] = file_content  # Keep for reload
        st.session_state["file_ext"] = file_ext
        st.session_state["dataframe"] = df
        st.session_state["sheet_name"] = sheet_name
        st.session_state["applied_skip_rows"] = skip_rows
        st.session_state["applied_skip_footer_rows"] = skip_footer_rows
        st.session_state["column_renames"] = {col: col for col in df.columns}
        st.session_state["columns_to_ignore"] = set()  # Reset ignored columns

        # Check if there are pending contract import settings to apply
        if st.session_state.get("pending_import_settings"):
            _apply_contract_import_settings()

        # Rerun to show the preview and configuration
        st.rerun()

    finally:
        set_processing(False)


def _handle_contract_upload(contract_file):
    """Handle contract YAML file upload and apply import settings."""
    try:
        content = contract_file.read()
        contract_file.seek(0)

        # Check if we already processed this contract
        import hashlib
        contract_hash = hashlib.sha256(content).hexdigest()
        if st.session_state.get("loaded_contract_hash") == contract_hash:
            return  # Already processed

        # Parse YAML
        contract_data = yaml.safe_load(content.decode("utf-8"))

        # Convert to Contract object for validation
        contract = dict_to_contract(contract_data)

        # Store the contract for later use (Step 2 will use it)
        st.session_state["uploaded_contract"] = contract
        st.session_state["loaded_contract_hash"] = contract_hash

        # Extract import settings
        import_settings = contract.dataset.import_settings

        # Store settings to apply when file is loaded
        st.session_state["pending_import_settings"] = {
            "skip_rows": import_settings.skip_rows,
            "skip_footer_rows": import_settings.skip_footer_rows,
            "column_renames": import_settings.column_renames,
            "columns_to_ignore": import_settings.columns_to_ignore,
            "quick_actions": {
                "to_lowercase": import_settings.quick_actions.to_lowercase,
                "to_uppercase": import_settings.quick_actions.to_uppercase,
                "to_titlecase": import_settings.quick_actions.to_titlecase,
                "trim_whitespace": import_settings.quick_actions.trim_whitespace,
                "remove_punctuation": import_settings.quick_actions.remove_punctuation,
                "replace_spaces": import_settings.quick_actions.replace_spaces_with_underscores,
            },
        }

        success_box(
            f"Contract loaded! Import settings will be applied when you upload a data file. "
            f"(Skip rows: {import_settings.skip_rows}, "
            f"Columns to ignore: {len(import_settings.columns_to_ignore)})"
        )

        # If a file is already loaded, apply settings now
        if st.session_state.get("dataframe") is not None:
            _apply_contract_import_settings()

    except yaml.YAMLError as e:
        error_box(f"Invalid YAML format: {str(e)}")
    except Exception as e:
        error_box(f"Error loading contract: {str(e)}")


def _apply_contract_import_settings():
    """Apply pending import settings from a loaded contract."""
    settings = st.session_state.get("pending_import_settings")
    if not settings:
        return

    df = st.session_state.get("dataframe")
    if df is None:
        return

    changes_made = []

    # Apply skip rows if different
    current_skip = st.session_state.get("applied_skip_rows", 0)
    current_footer = st.session_state.get("applied_skip_footer_rows", 0)

    if settings["skip_rows"] != current_skip or settings["skip_footer_rows"] != current_footer:
        st.session_state["skip_rows"] = settings["skip_rows"]
        st.session_state["skip_footer_rows"] = settings["skip_footer_rows"]
        reload_success = _reload_with_new_skip_settings()
        if reload_success:
            changes_made.append(f"Applied skip rows ({settings['skip_rows']} first, {settings['skip_footer_rows']} last)")
            # Re-fetch df after reload
            df = st.session_state.get("dataframe")

    # Apply quick actions
    qa = settings["quick_actions"]
    if any(qa.values()):
        _apply_quick_options(
            qa["to_lowercase"], qa["to_uppercase"], qa["to_titlecase"],
            qa["trim_whitespace"], qa["remove_punctuation"], qa["replace_spaces"]
        )
        changes_made.append("Applied column name transformations")

    # Apply column renames from contract
    if settings["column_renames"]:
        column_renames = st.session_state.get("column_renames", {})
        for orig_name, new_name in settings["column_renames"].items():
            if orig_name in column_renames:
                column_renames[orig_name] = new_name
        st.session_state["column_renames"] = column_renames
        changes_made.append(f"Applied {len(settings['column_renames'])} column renames")

    # Apply columns to ignore
    if settings["columns_to_ignore"]:
        # Match by column name (after any renames applied)
        columns_to_ignore = set()
        column_renames = st.session_state.get("column_renames", {})
        df = st.session_state.get("dataframe")

        for ignore_name in settings["columns_to_ignore"]:
            # Find matching column in current df
            for orig_col in df.columns:
                renamed = column_renames.get(orig_col, orig_col)
                if renamed == ignore_name or orig_col == ignore_name:
                    columns_to_ignore.add(orig_col)
                    break

        st.session_state["columns_to_ignore"] = columns_to_ignore
        if columns_to_ignore:
            changes_made.append(f"Marked {len(columns_to_ignore)} columns to ignore")

    # Clear pending settings
    del st.session_state["pending_import_settings"]

    # Force widget refresh
    st.session_state["column_config_version"] = st.session_state.get("column_config_version", 0) + 1

    if changes_made:
        st.session_state["apply_changes_message"] = "Contract settings applied: " + "; ".join(changes_made)
        st.rerun()


def _clear_session():
    """Clear all session state and reset to initial state."""
    # List of keys to clear
    keys_to_clear = [
        "dataframe", "uploaded_file_name", "file_hash", "file_content",
        "file_ext", "sheet_name", "applied_skip_rows", "applied_skip_footer_rows",
        "skip_rows", "skip_footer_rows", "column_renames", "columns_to_ignore",
        "ignored_columns", "uploaded_contract", "upload_mode",
        "loaded_contract_hash", "pending_import_settings", "contract",
        "contract_source", "validation_results", "remediated_df",
        "remediation_approved", "column_config_version", "applied_quick_actions",
        "apply_changes_message", "pending_file_content", "pending_file_name",
        "pending_file_ext", "pending_file_hash", "available_sheets",
        "contract_auto_applied",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Increment uploader version to force file uploaders to reset
    # This creates new widget instances with fresh state
    st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1

    # Reset current step to 1
    st.session_state["current_step"] = 1


def _show_current_file():
    """Show information about the currently loaded file."""
    df = st.session_state.get("dataframe")
    filename = st.session_state.get("uploaded_file_name", "Unknown")
    sheet_name = st.session_state.get("sheet_name")

    st.subheader("Loaded Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Rows", f"{len(df):,}")

    with col2:
        st.metric("Columns", len(df.columns))

    with col3:
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        st.metric("Memory", f"{memory_mb:.1f} MB")

    if sheet_name:
        st.caption(f"Sheet: {sheet_name}")

    # Data preview
    data_preview(df, max_rows=10, title="Data Preview")


def _render_column_configuration():
    """Render column name configuration section with import options."""
    df = st.session_state.get("dataframe")
    if df is None:
        return

    # Get current settings
    column_renames = st.session_state.get("column_renames", {col: col for col in df.columns})

    # ===== ROW OPTIONS SECTION (first) =====
    st.markdown("### Row Options")

    col1, col2 = st.columns(2)

    with col1:
        skip_rows = st.number_input(
            "Skip first # rows",
            min_value=0,
            max_value=100,
            value=st.session_state.get("skip_rows", 0),
            help="Skip rows at the beginning. Column headers will be read from the first non-skipped row.",
            key="skip_rows_input",
        )
        st.session_state["skip_rows"] = skip_rows

    with col2:
        skip_footer = st.number_input(
            "Skip last # rows",
            min_value=0,
            max_value=100,
            value=st.session_state.get("skip_footer_rows", 0),
            help="Skip rows at the end of the file.",
            key="skip_footer_input",
        )
        st.session_state["skip_footer_rows"] = skip_footer

    # Checkboxes in two columns
    check_col1, check_col2 = st.columns(2)

    with check_col1:
        skip_total_rows = st.checkbox(
            "Drop rows containing totals",
            key="opt_skip_totals",
            help="Remove rows where any cell contains 'total' or 'grand total' (case insensitive)"
        )

    with check_col2:
        check_duplicates = st.checkbox(
            "Check for duplicate rows",
            value=st.session_state.get("check_duplicates", False),
            key="opt_check_duplicates",
            help="Flag rows that are exact duplicates of other rows"
        )
        st.session_state["check_duplicates"] = check_duplicates

    # Show failure action dropdown if duplicate check is enabled
    if check_duplicates:
        failure_labels = list(FAILURE_ACTION_LABELS.values())
        current_action = st.session_state.get("duplicate_failure_action", "label_failure")
        current_label = FAILURE_ACTION_LABELS.get(current_action, failure_labels[2])
        current_idx = failure_labels.index(current_label) if current_label in failure_labels else 2

        dup_failure_label = st.selectbox(
            "On duplicate found",
            options=failure_labels,
            index=current_idx,
            key="dup_failure_select",
            help="What to do when duplicate rows are detected"
        )
        st.session_state["duplicate_failure_action"] = FAILURE_LABEL_TO_ACTION.get(dup_failure_label, "label_failure")

    st.divider()

    # ===== COLUMN OPTIONS SECTION =====
    st.markdown("### Select & Name Columns")

    # Case conversion on its own line
    case_options = ["No case change", "lowercase", "UPPERCASE", "Title Case"]
    case_selection = st.selectbox(
        "Set text case for column names",
        options=case_options,
        index=0,
        key="opt_case",
        help="Convert column names to a specific case",
    )
    to_lowercase = case_selection == "lowercase"
    to_uppercase = case_selection == "UPPERCASE"
    to_titlecase = case_selection == "Title Case"

    # 3 checkboxes in one row
    col1, col2, col3 = st.columns(3)

    with col1:
        trim_whitespace = st.checkbox("Trim whitespace", key="opt_trim")

    with col2:
        remove_punctuation = st.checkbox("Remove punctuation", key="opt_remove_punct")

    with col3:
        replace_spaces = st.checkbox("Replace spaces with _", key="opt_replace_spaces")

    # Apply Changes button
    if st.button("Apply Changes", type="primary"):
        changes_made = []

        # Check if skip rows changed - need to reload FIRST to get new headers
        applied_skip = st.session_state.get("applied_skip_rows", 0)
        applied_footer = st.session_state.get("applied_skip_footer_rows", 0)

        if skip_rows != applied_skip or skip_footer != applied_footer:
            reload_success = _reload_with_new_skip_settings()
            if reload_success:
                changes_made.append(f"Reloaded file (skip first {skip_rows}, skip last {skip_footer})")
            else:
                error_box("Failed to reload file with new skip settings.")
                return

        # Apply quick options AFTER reload (so they apply to new column names)
        quick_options_applied = _apply_quick_options(
            to_lowercase, to_uppercase, to_titlecase, trim_whitespace,
            remove_punctuation, replace_spaces
        )
        if quick_options_applied:
            changes_made.append("Applied column name transformations")

        # Apply skip total rows if selected
        if skip_total_rows:
            rows_removed = _apply_skip_total_rows()
            if rows_removed > 0:
                changes_made.append(f"Removed {rows_removed} rows containing 'total'")

        # Increment version to force widget refresh
        st.session_state["column_config_version"] = st.session_state.get("column_config_version", 0) + 1

        # Clear option states after applying
        for key in ["opt_case", "opt_trim", "opt_remove_punct", "opt_replace_spaces", "opt_skip_totals"]:
            if key in st.session_state:
                del st.session_state[key]

        # Show feedback
        if changes_made:
            st.session_state["apply_changes_message"] = "; ".join(changes_made)
        else:
            st.session_state["apply_changes_message"] = "No changes to apply."

        st.rerun()

    # Show message from previous Apply Changes action
    if "apply_changes_message" in st.session_state:
        success_box(st.session_state["apply_changes_message"])
        del st.session_state["apply_changes_message"]

    # ===== FINALIZE COLUMN NAMES SECTION (no divider before) =====
    st.markdown("### Finalize Column Names")
    st.markdown(
        "Edit column names below. Check 'Ignore' to exclude columns from validation rules. "
        "Ignored columns will be hidden in previews and unavailable for rule configuration. "
        "You can choose to drop them entirely when exporting."
    )

    # Get version for widget keys (forces refresh when Apply Changes is clicked)
    version = st.session_state.get("column_config_version", 0)

    # Get current ignored columns set
    columns_to_ignore = st.session_state.get("columns_to_ignore", set())

    # Header row with bold Ignore Column header - wider ignore column
    header_col1, header_col2, header_col3 = st.columns([0.2, 2.5, 1.3])
    with header_col1:
        st.markdown("**#**")
    with header_col2:
        st.markdown("**Column Name**")
    with header_col3:
        st.markdown("**Ignore Column**")

    # Display columns with ignore checkbox
    for i, orig_col in enumerate(df.columns):
        current_name = column_renames.get(orig_col, orig_col)

        col1, col2, col3 = st.columns([0.2, 2.5, 1.3])

        with col1:
            st.markdown(f"{i+1}")

        with col2:
            new_name = st.text_input(
                f"Column {i+1}",
                value=current_name,
                key=f"col_name_{i}_v{version}",
                label_visibility="collapsed",
            )

            if new_name != current_name:
                column_renames[orig_col] = new_name
                st.session_state["column_renames"] = column_renames

        with col3:
            is_ignored = orig_col in columns_to_ignore
            # Use checkbox with visible label that shows status
            checkbox_label = "Ignored" if is_ignored else "Ignore"
            new_ignored = st.checkbox(
                checkbox_label,
                value=is_ignored,
                key=f"ignore_col_{i}_v{version}",
            )

            # Update ignored columns set
            if new_ignored:
                columns_to_ignore.add(orig_col)
            elif orig_col in columns_to_ignore:
                columns_to_ignore.discard(orig_col)

            st.session_state["columns_to_ignore"] = columns_to_ignore

    # Show summary of ignored columns
    if columns_to_ignore:
        ignored_names = [column_renames.get(col, col) for col in columns_to_ignore if col in df.columns]
        if ignored_names:
            st.caption(f"Ignored columns (hidden from rules): {', '.join(ignored_names)}")


def _apply_skip_total_rows() -> int:
    """
    Remove rows where any cell contains 'total' (case insensitive).

    Returns:
        Number of rows removed.
    """
    df = st.session_state.get("dataframe")
    if df is None:
        return 0

    original_count = len(df)

    # Create a mask for rows that contain 'total' in any cell
    # Convert all cells to string and check for 'total' (case insensitive)
    def row_contains_total(row):
        for val in row:
            if pd.notna(val):
                val_str = str(val).lower()
                if 'total' in val_str:
                    return True
        return False

    mask = df.apply(row_contains_total, axis=1)

    # Keep rows that do NOT contain 'total'
    df_filtered = df[~mask].reset_index(drop=True)

    rows_removed = original_count - len(df_filtered)

    if rows_removed > 0:
        st.session_state["dataframe"] = df_filtered
        # Update column renames to match new dataframe
        st.session_state["column_renames"] = {col: col for col in df_filtered.columns}

    return rows_removed


def _apply_quick_options(
    to_lowercase: bool,
    to_uppercase: bool,
    to_titlecase: bool,
    trim_whitespace: bool,
    remove_punctuation: bool = False,
    replace_spaces: bool = False,
) -> bool:
    """
    Apply quick transformation options to column names.

    Returns:
        True if any transformations were applied, False otherwise.
    """
    import re
    import string

    # Check if any option is selected
    if not any([to_lowercase, to_uppercase, to_titlecase, trim_whitespace,
                remove_punctuation, replace_spaces]):
        return False

    df = st.session_state.get("dataframe")
    if df is None:
        return False

    column_renames = st.session_state.get("column_renames", {col: col for col in df.columns})

    for orig_col in df.columns:
        current_name = column_renames.get(orig_col, orig_col)

        # Apply transformations in a sensible order
        if trim_whitespace:
            # Use regex to strip all Unicode whitespace from start/end
            current_name = re.sub(r'^\s+|\s+$', '', current_name)

        if remove_punctuation:
            # Remove punctuation but keep spaces and alphanumeric
            current_name = "".join(
                c for c in current_name if c not in string.punctuation
            )

        if replace_spaces:
            # Replace ALL types of whitespace with underscores:
            # - Regular spaces, tabs, newlines, carriage returns
            # - Non-breaking spaces (\u00A0)
            # - Other Unicode whitespace characters
            # Using \s which matches all Unicode whitespace
            current_name = re.sub(r'\s+', '_', current_name)

        # Only one case option can apply
        if to_lowercase:
            current_name = current_name.lower()
        elif to_uppercase:
            current_name = current_name.upper()
        elif to_titlecase:
            current_name = current_name.title()

        column_renames[orig_col] = current_name

    st.session_state["column_renames"] = column_renames

    # Store which quick actions were applied (for saving in contract)
    st.session_state["applied_quick_actions"] = {
        "to_lowercase": to_lowercase,
        "to_uppercase": to_uppercase,
        "to_titlecase": to_titlecase,
        "trim_whitespace": trim_whitespace,
        "remove_punctuation": remove_punctuation,
        "replace_spaces": replace_spaces,
    }

    return True


def _reload_with_new_skip_settings() -> bool:
    """
    Reload the file with new skip row settings.

    Returns:
        True if reload succeeded, False otherwise.
    """
    file_content = st.session_state.get("file_content")
    filename = st.session_state.get("uploaded_file_name")
    file_ext = st.session_state.get("file_ext")
    sheet_name = st.session_state.get("sheet_name")

    if file_content is None:
        error_box("Cannot reload: original file content not available. Please re-upload the file.")
        return False

    skip_rows = st.session_state.get("skip_rows", 0)
    skip_footer = st.session_state.get("skip_footer_rows", 0)

    read_result = read_file(
        file_content,
        filename,
        file_ext,
        sheet_name=sheet_name,
        skip_rows=skip_rows,
        skip_footer_rows=skip_footer,
    )

    if not read_result.success:
        error_box(f"Reload failed: {read_result.error_message}")
        return False

    df = read_result.dataframe

    # Validate
    is_valid, error_msg = validate_dataframe(df)
    if not is_valid:
        error_box(error_msg)
        return False

    # Update session state with new dataframe and fresh column names
    st.session_state["dataframe"] = df
    st.session_state["applied_skip_rows"] = skip_rows
    st.session_state["applied_skip_footer_rows"] = skip_footer
    st.session_state["column_renames"] = {col: col for col in df.columns}
    st.session_state["columns_to_ignore"] = set()  # Reset ignored columns on reload

    return True


def _apply_column_renames():
    """Apply pending column renames to the dataframe and store ignored columns info."""
    df = st.session_state.get("dataframe")
    column_renames = st.session_state.get("column_renames", {})
    columns_to_ignore = st.session_state.get("columns_to_ignore", set())

    if df is None:
        return

    # Store ignored column names (after rename) for use in later steps
    # These columns will be excluded from previews and rule configuration
    ignored_column_names = []
    for orig_col in columns_to_ignore:
        if orig_col in df.columns:
            renamed = column_renames.get(orig_col, orig_col)
            ignored_column_names.append(renamed)

    st.session_state["ignored_columns"] = ignored_column_names

    # Apply renames
    renames_needed = {k: v for k, v in column_renames.items() if k != v and k in df.columns}

    if renames_needed:
        df = df.rename(columns=renames_needed)

    # Update session state
    st.session_state["dataframe"] = df
    st.session_state["column_renames"] = {col: col for col in df.columns}
    # Note: columns_to_ignore is preserved for reference
