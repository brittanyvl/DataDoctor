"""
Step 1: Upload dataset and configure columns.

This module implements the file upload step of the Data Doctor workflow,
including column name configuration, FK file handling, and contract upload.
"""

import streamlit as st
import pandas as pd
import yaml

from src.constants import (
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
    # Step header with upload limits in description
    step_header(
        1,
        "Upload Dataset",
        f"Upload your data file (max {MAX_UPLOAD_SIZE_MB}MB, {MAX_ROW_COUNT:,} rows, {MAX_COLUMN_COUNT} columns). "
        f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
    )

    # Check rate limit
    is_allowed, wait_seconds = check_rate_limit()
    if not is_allowed:
        warning_box(
            f"Rate limit reached. Please wait {wait_seconds} seconds before uploading again."
        )
        return

    # File upload section
    _render_file_upload_section()

    # Show current file info and column config if already uploaded
    df = st.session_state.get("dataframe")
    if df is not None:
        _show_current_file()

        st.divider()

        # Column configuration section (includes import options)
        _render_column_configuration()

        # Navigation
        st.divider()
        _, next_clicked = navigation_buttons(
            show_back=False,
            next_label="Continue to Contract",
            next_disabled=False,
        )

        if next_clicked:
            # Apply any pending column renames before moving on
            _apply_column_renames()
            set_current_step(2)
            st.rerun()


def _render_file_upload_section():
    """Render the file upload section with support for multi-sheet Excel and FK files."""
    st.subheader("Data Files")

    # Check if we're in sheet selection mode
    pending_file = st.session_state.get("pending_file_content")
    if pending_file is not None:
        _render_sheet_selection()
        return

    # Primary data file uploader
    st.markdown("**Primary Data File**")
    primary_file = st.file_uploader(
        "Choose your main data file",
        type=[ext.lstrip('.') for ext in SUPPORTED_EXTENSIONS],
        help="Upload a CSV or Excel file containing your data",
        key="primary_file_uploader",
    )

    # Optional uploads section (FK file and Contract)
    with st.expander("Optional: Load Contract or FK Reference File", expanded=False):
        st.markdown("**Load Existing Contract**")
        st.caption(
            "If you have a contract from a previous run, upload it here to "
            "automatically apply column settings, skip rows, and ignore columns."
        )
        contract_file = st.file_uploader(
            "Choose contract YAML file",
            type=["yaml", "yml"],
            help="Upload a Data Doctor contract to restore import settings",
            key="contract_file_uploader",
        )

        if contract_file is not None:
            _handle_contract_upload(contract_file)

        st.markdown("---")

        st.markdown("**Foreign Key Reference File**")
        st.caption(
            "Upload a file containing valid values for foreign key validation. "
            "You can also select a sheet from multi-sheet Excel files."
        )
        fk_file = st.file_uploader(
            "Choose FK reference file",
            type=[ext.lstrip('.') for ext in SUPPORTED_EXTENSIONS],
            help="Optional: Upload a file containing valid FK values",
            key="fk_file_uploader",
        )

        # Handle FK file upload (only if primary is loaded)
        if fk_file is not None and st.session_state.get("dataframe") is not None:
            _handle_fk_file(fk_file)
        elif fk_file is not None:
            info_box("Upload a primary data file first, then the FK reference will be processed.")

    # Handle primary file upload
    if primary_file is not None:
        _handle_primary_file(primary_file)


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

    st.info(f"**{filename}** contains {len(sheets)} sheets. Please select which sheets to use.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Primary Data Sheet**")
        primary_sheet = st.selectbox(
            "Select sheet containing your main data",
            options=sheets,
            key="primary_sheet_select",
        )

    with col2:
        st.markdown("**FK Reference Sheet (Optional)**")
        fk_options = ["(None)"] + sheets
        fk_sheet = st.selectbox(
            "Select sheet containing FK reference values",
            options=fk_options,
            key="fk_sheet_select",
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Selected Sheets", type="primary", use_container_width=True):
            file_content = st.session_state["pending_file_content"]
            file_ext = st.session_state["pending_file_ext"]
            file_hash = st.session_state["pending_file_hash"]

            # Load primary data
            _load_primary_data(file_content, filename, file_ext, primary_sheet, file_hash)

            # Load FK sheet if selected
            if fk_sheet != "(None)":
                _load_fk_data(file_content, file_ext, fk_sheet, is_sheet=True)

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

        success_box(f"Loaded {filename}" + (f" (sheet: {sheet_name})" if sheet_name else ""))

        # Check if there are pending contract import settings to apply
        if st.session_state.get("pending_import_settings"):
            _apply_contract_import_settings()

    finally:
        set_processing(False)


def _handle_fk_file(fk_file):
    """Handle FK file upload."""
    file_content = fk_file.read()
    fk_file.seek(0)

    validation_result = validate_upload(
        fk_file.name,
        len(file_content),
        fk_file.type,
    )

    if not validation_result.is_valid:
        error_box(f"FK file error: {validation_result.error_message}")
        return

    file_ext = validation_result.file_extension

    # For Excel, use first sheet
    sheet_name = None
    if file_ext in {".xlsx", ".xls", ".xlsb"}:
        sheet_result = get_excel_sheet_names(file_content, file_ext)
        if sheet_result.success and sheet_result.sheet_names:
            sheet_name = sheet_result.sheet_names[0]

    _load_fk_data(file_content, file_ext, sheet_name, is_sheet=False, filename=fk_file.name)


def _load_fk_data(file_content, file_ext, sheet_name, is_sheet=False, filename=None):
    """Load FK reference data."""
    read_result = read_file(
        file_content,
        filename or "fk_data",
        file_ext,
        sheet_name=sheet_name,
    )

    if read_result.success:
        st.session_state["fk_dataframe"] = read_result.dataframe
        st.session_state["fk_source"] = f"sheet: {sheet_name}" if is_sheet else filename
        success_box(f"FK reference loaded: {sheet_name if is_sheet else filename}")


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
        "ignored_columns", "fk_dataframe", "fk_source", "uploaded_contract",
        "loaded_contract_hash", "pending_import_settings", "contract",
        "contract_source", "validation_results", "remediated_df",
        "remediation_approved", "column_config_version", "applied_quick_actions",
        "apply_changes_message", "pending_file_content", "pending_file_name",
        "pending_file_ext", "pending_file_hash", "available_sheets",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Reset current step to 1
    st.session_state["current_step"] = 1


def _show_current_file():
    """Show information about the currently loaded file."""
    df = st.session_state.get("dataframe")
    filename = st.session_state.get("uploaded_file_name", "Unknown")
    sheet_name = st.session_state.get("sheet_name")

    # Header row with title and Clear Session button
    header_col1, header_col2 = st.columns([3, 1])

    with header_col1:
        st.subheader("Loaded Data")

    with header_col2:
        if st.button("Clear Session", type="secondary", help="Clear all data and start over"):
            _clear_session()
            st.rerun()

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

    # Show FK status if loaded
    fk_df = st.session_state.get("fk_dataframe")
    if fk_df is not None:
        fk_source = st.session_state.get("fk_source", "Unknown")
        st.caption(f"FK Reference: {fk_source} ({len(fk_df):,} rows)")

    # Data preview
    data_preview(df, max_rows=10, title="Data Preview")


def _render_column_configuration():
    """Render column name configuration section with import options."""
    st.subheader("Column Configuration")

    df = st.session_state.get("dataframe")
    if df is None:
        return

    # Get current settings
    column_renames = st.session_state.get("column_renames", {col: col for col in df.columns})

    # Import and transformation options as checkboxes
    st.markdown("**Quick Options**")

    col1, col2, col3 = st.columns(3)

    with col1:
        to_lowercase = st.checkbox("Convert to lowercase", key="opt_lowercase")
        to_uppercase = st.checkbox("Convert to UPPERCASE", key="opt_uppercase")
    with col2:
        to_titlecase = st.checkbox("Convert to Title Case", key="opt_titlecase")
        trim_whitespace = st.checkbox("Trim whitespace", key="opt_trim")
    with col3:
        remove_punctuation = st.checkbox("Remove punctuation", key="opt_remove_punct")
        replace_spaces = st.checkbox("Replace spaces with _", key="opt_replace_spaces")

    # Skip rows options
    st.markdown("**Row Options**")
    col1, col2 = st.columns(2)

    with col1:
        skip_rows = st.number_input(
            "Skip first N rows (header from row N+1)",
            min_value=0,
            max_value=100,
            value=st.session_state.get("skip_rows", 0),
            help="Skip rows at the beginning. Column headers will be read from the first non-skipped row.",
            key="skip_rows_input",
        )
        st.session_state["skip_rows"] = skip_rows

    with col2:
        skip_footer = st.number_input(
            "Skip last N rows",
            min_value=0,
            max_value=100,
            value=st.session_state.get("skip_footer_rows", 0),
            help="Skip rows at the end of the file.",
            key="skip_footer_input",
        )
        st.session_state["skip_footer_rows"] = skip_footer

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

        # Increment version to force widget refresh
        st.session_state["column_config_version"] = st.session_state.get("column_config_version", 0) + 1

        # Clear checkbox states after applying
        for key in ["opt_lowercase", "opt_uppercase", "opt_titlecase", "opt_trim",
                    "opt_remove_punct", "opt_replace_spaces"]:
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

    st.markdown("---")

    # Individual column names
    st.markdown("**Column Names**")
    st.caption(
        "Edit column names below. Check 'Ignore' to exclude columns from validation rules. "
        "Ignored columns will be hidden in previews and unavailable for rule configuration. "
        "You can choose to drop them entirely when exporting."
    )

    # Get version for widget keys (forces refresh when Apply Changes is clicked)
    version = st.session_state.get("column_config_version", 0)

    # Get current ignored columns set
    columns_to_ignore = st.session_state.get("columns_to_ignore", set())

    # Header row
    header_col1, header_col2, header_col3 = st.columns([0.5, 3, 0.5])
    with header_col1:
        st.caption("#")
    with header_col2:
        st.caption("Column Name")
    with header_col3:
        st.caption("Ignore")

    # Display columns with ignore checkbox
    for i, orig_col in enumerate(df.columns):
        current_name = column_renames.get(orig_col, orig_col)

        col1, col2, col3 = st.columns([0.5, 3, 0.5])

        with col1:
            st.markdown(f"**{i+1}**")

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
            is_ignored = st.checkbox(
                "Ignore",
                value=orig_col in columns_to_ignore,
                key=f"ignore_col_{i}_v{version}",
                label_visibility="collapsed",
            )

            # Update ignored columns set
            if is_ignored:
                columns_to_ignore.add(orig_col)
            elif orig_col in columns_to_ignore:
                columns_to_ignore.discard(orig_col)

            st.session_state["columns_to_ignore"] = columns_to_ignore

    # Show summary of ignored columns
    if columns_to_ignore:
        ignored_names = [column_renames.get(col, col) for col in columns_to_ignore if col in df.columns]
        if ignored_names:
            st.caption(f"Ignored columns (hidden from rules): {', '.join(ignored_names)}")


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
