"""
Step 3: Data Cleaning - Configure data cleaning/remediation options.

This module implements the data cleaning step where users configure
formatting and remediation rules to be applied during processing.
"""

import streamlit as st
import pandas as pd

from src.constants import (
    DATA_TYPES,
    DATA_TYPE_LABELS,
    SPECIAL_CHARS_REMOVED,
    PUNCTUATION_MARKS_REMOVED,
)
from src.contract.builder import get_column_config
from src.contract.schema import RemediationConfig
from src.presets.date_formats import get_common_format_names
from src.session import set_current_step
from src.ui.components import (
    step_header,
    error_box,
    warning_box,
    info_box,
    navigation_buttons,
)


def render_step_cleaning():
    """Render the data cleaning configuration step."""
    # Custom header without divider
    st.markdown("### Step 3: Order Data Treatments")
    st.info(
        "After testing you can optionally treat data hygiene issues. If you selected "
        "**Label Failure: Mark and Continue** as your failure action, we will provide "
        "the labeled original dataset along with the cleaned dataset for download in your final reports."
    )

    # Check prerequisites
    df = st.session_state.get("dataframe")
    contract = st.session_state.get("contract")

    if df is None:
        error_box("No dataset loaded. Please upload a file first.")
        if st.button("Go to Upload"):
            set_current_step(1)
            st.rerun()
        return

    if contract is None:
        error_box("No rules defined. Please create validation rules first.")
        if st.button("Go to Rules"):
            set_current_step(2)
            st.rerun()
        return

    # Get columns to configure (excluding ignored)
    ignored_columns = st.session_state.get("ignored_columns", [])
    columns_to_configure = [col for col in df.columns if col not in ignored_columns]

    if not columns_to_configure:
        warning_box("All columns are marked as ignored. Please go back and select columns to validate.")
        if st.button("Go to Upload"):
            set_current_step(1)
            st.rerun()
        return

    # Global cleaning options
    st.markdown("## Global Cleaning Options")
    st.markdown("Apply these options to all columns at once.")

    # Checkbox options in two rows
    st.markdown("**Apply to All Columns:**")

    # Row 1: Trim whitespace, Remove special chars, Standardize nulls
    row1_cols = st.columns(3)
    with row1_cols[0]:
        apply_trim = st.checkbox("Trim whitespace", key="global_trim", help="Remove leading/trailing spaces from all columns")
    with row1_cols[1]:
        apply_special = st.checkbox("Remove special chars", key="global_special", help="Remove control characters and non-printable characters")
    with row1_cols[2]:
        apply_nulls = st.checkbox("Standardize nulls", key="global_nulls", help="Convert NA, N/A, None, etc. to actual null")

    # Row 2: Remove punctuation (text), Remove punctuation (numbers), Drop ignored columns
    row2_cols = st.columns(3)
    with row2_cols[0]:
        apply_punct = st.checkbox("Remove punctuation (text)", key="global_punct", help="Remove all punctuation marks from text columns only. Does not apply to numeric columns (integer/float) to preserve decimal points.")
    with row2_cols[1]:
        apply_numeric_clean = st.checkbox("Remove punctuation (numbers)", key="global_numeric", help="Remove currency symbols ($, EUR), thousand separators (,), and other non-numeric characters from all numeric columns")
    with row2_cols[2]:
        drop_ignored = st.checkbox("Drop ignored columns", key="global_drop_ignored", help="Remove columns marked as 'ignored' from the final output")

    # Dropdown options in a row
    drop_cols = st.columns(2)

    with drop_cols[0]:
        case_options = ["No change", "lowercase", "UPPERCASE", "Title Case"]
        global_case = st.selectbox(
            "Case conversion",
            options=case_options,
            index=0,
            key="global_case",
            help="Convert text to a specific case in all columns",
        )

    with drop_cols[1]:
        # Get date columns only
        date_columns = [col for col in columns_to_configure
                       if get_column_config(contract, col) and get_column_config(contract, col).data_type == "date"]

        if date_columns:
            date_format_options = ["No change", "YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "YYYY/MM/DD"]
            global_date_format = st.selectbox(
                f"Standardize date format ({len(date_columns)} date columns)",
                options=date_format_options,
                index=0,
                key="global_date_format",
                help="Convert all date columns to a consistent format",
            )
        else:
            global_date_format = "No change"
            st.selectbox(
                "Standardize date format (no date columns)",
                options=["No date columns"],
                disabled=True,
                key="global_date_format_disabled",
            )

    # Apply and Clear buttons
    btn_cols = st.columns([1, 1, 2])

    with btn_cols[0]:
        apply_global = st.button("Apply Global Options", type="primary", use_container_width=True)

    with btn_cols[1]:
        clear_all = st.button("Clear All Cleaning", use_container_width=True, help="Remove all cleaning options from all columns")

    if apply_global:
        changes_made = []

        if apply_trim:
            _apply_cleaning_to_all(contract, columns_to_configure, "trim_whitespace")
            changes_made.append("trim whitespace")

        if apply_special:
            _apply_cleaning_to_all(contract, columns_to_configure, "remove_non_printable")
            changes_made.append("remove special chars")

        if apply_punct:
            # Apply punctuation removal only to non-numeric columns
            non_numeric_cols = [col for col in columns_to_configure
                               if get_column_config(contract, col) and get_column_config(contract, col).data_type not in ["integer", "float"]]
            _apply_cleaning_to_all(contract, non_numeric_cols, "remove_punctuation")
            changes_made.append("remove punctuation (non-numeric)")

        if apply_nulls:
            _apply_cleaning_to_all(contract, columns_to_configure, "standardize_nulls")
            changes_made.append("standardize nulls")

        if apply_numeric_clean:
            # Apply numeric cleanup only to numeric columns
            numeric_cols = [col for col in columns_to_configure
                          if get_column_config(contract, col) and get_column_config(contract, col).data_type in ["integer", "float"]]
            _apply_cleaning_to_all(contract, numeric_cols, "numeric_cleanup")
            changes_made.append(f"clean numeric ({len(numeric_cols)} columns)")

        if drop_ignored:
            # Store the setting to drop ignored columns in session state
            st.session_state["drop_ignored_columns"] = True
            changes_made.append(f"drop ignored ({len(ignored_columns)} columns)")

        if global_case != "No change":
            case_map = {"lowercase": "lower", "UPPERCASE": "upper", "Title Case": "title"}
            _apply_case_to_all(contract, columns_to_configure, case_map[global_case])
            changes_made.append(f"case: {global_case}")

        if global_date_format != "No change" and date_columns:
            _apply_date_format_to_all(contract, date_columns, global_date_format)
            changes_made.append(f"date format: {global_date_format}")

        if changes_made:
            st.session_state["global_clean_message"] = f"Applied: {', '.join(changes_made)}"
        st.rerun()

    if clear_all:
        _clear_all_cleaning(contract, columns_to_configure)
        st.rerun()

    # Show message from previous action
    if "global_clean_message" in st.session_state:
        st.success(st.session_state["global_clean_message"])
        del st.session_state["global_clean_message"]

    # Skip button - go directly to validation (styled dark green)
    skip_cols = st.columns([2, 1])
    with skip_cols[1]:
        if st.button("Run Diagnostics & Treatments →", use_container_width=True, key="skip_to_diag", type="primary"):
            set_current_step(4)
            st.rerun()

    # Inject CSS to make the skip button dark green (override primary color)
    st.markdown(
        """<style>
        [data-testid="stButton"] button[kind="primary"] {
            background-color: #2F855A !important;
            border-color: #2F855A !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    st.divider()

    # Per-column cleaning configuration
    st.markdown("## Per-Column Cleaning")
    st.markdown("Configure cleaning options for each column below. Click to expand.")

    for i, col_name in enumerate(columns_to_configure):
        col_config = get_column_config(contract, col_name)
        if col_config is None:
            continue

        # Column header with cleaning count badge
        cleaning_count = len(col_config.remediation)
        badge = f" ({cleaning_count} option{'s' if cleaning_count != 1 else ''})" if cleaning_count > 0 else ""

        # Show data type
        data_type = col_config.data_type
        type_label = DATA_TYPE_LABELS.get(data_type, data_type)

        # Use expander for each column
        with st.expander(f"**{col_name}** - {type_label}{badge}", expanded=False):
            # Show column preview
            _render_column_preview(df, col_name)

            # Render cleaning options for this column
            _render_column_cleaning(contract, col_config, col_name, data_type)

    # Navigation
    st.divider()
    back_clicked, next_clicked = navigation_buttons(
        back_label="Back to Diagnostics",
        next_label="Run Diagnostics & Treatments",
    )

    if back_clicked:
        set_current_step(2)
        st.rerun()

    if next_clicked:
        set_current_step(4)
        st.rerun()


def _render_column_preview(df, col_name):
    """Render a small preview of the column data."""
    col_data = df[col_name].dropna()
    samples = col_data.head(3).tolist()

    # Pad with empty strings if less than 3 values
    while len(samples) < 3:
        samples.append("")

    preview_df = pd.DataFrame({
        col_name: [str(s)[:50] for s in samples]
    })
    st.dataframe(preview_df, use_container_width=True, hide_index=True)


def _render_column_cleaning(contract, col_config, col_name, data_type):
    """Render cleaning options for a single column."""
    existing_rems = {r.type: r for r in col_config.remediation}

    # Common text cleaning options
    st.markdown("##### Text Cleaning")
    text_cols = st.columns(3)

    with text_cols[0]:
        # Trim whitespace
        has_trim = "trim_whitespace" in existing_rems
        trim_check = st.checkbox(
            "Trim whitespace",
            value=has_trim,
            key=f"clean_trim_{col_name}",
            help="Remove leading and trailing spaces from values",
        )
        _toggle_remediation(col_config, "trim_whitespace", trim_check, existing_rems)

    with text_cols[1]:
        # Remove non-printable (special characters)
        has_nonprint = "remove_non_printable" in existing_rems
        nonprint_check = st.checkbox(
            "Remove special characters",
            value=has_nonprint,
            key=f"clean_special_{col_name}",
            help=f"Removes: {SPECIAL_CHARS_REMOVED}",
        )
        _toggle_remediation(col_config, "remove_non_printable", nonprint_check, existing_rems)

    with text_cols[2]:
        # Remove punctuation
        has_punct = "remove_punctuation" in existing_rems
        punct_check = st.checkbox(
            "Remove punctuation",
            value=has_punct,
            key=f"clean_punct_{col_name}",
            help=f"Removes: {PUNCTUATION_MARKS_REMOVED}. WARNING: This will also remove decimal points! For numeric columns, use 'Clean numeric formatting' instead to strip only currency symbols and commas.",
        )
        _toggle_remediation(col_config, "remove_punctuation", punct_check, existing_rems)

    # Text case normalization
    st.markdown("##### Text Case")
    case_options = ["As Entered (no change)", "lowercase", "UPPERCASE", "Title Case"]
    case_map = {"As Entered (no change)": None, "lowercase": "lower", "UPPERCASE": "upper", "Title Case": "title"}
    case_reverse = {v: k for k, v in case_map.items()}

    # Get current case setting
    has_case = "normalize_case" in existing_rems
    current_case = None
    if has_case:
        current_case = existing_rems["normalize_case"].params.get("case")
    current_display = case_reverse.get(current_case, "As Entered (no change)")
    current_idx = case_options.index(current_display) if current_display in case_options else 0

    case_selection = st.selectbox(
        "Convert text to",
        options=case_options,
        index=current_idx,
        key=f"clean_case_{col_name}",
        label_visibility="collapsed",
    )

    selected_case = case_map[case_selection]
    if selected_case:
        existing = next((r for r in col_config.remediation if r.type == "normalize_case"), None)
        if existing:
            existing.params = {"case": selected_case}
        else:
            col_config.remediation.append(RemediationConfig(type="normalize_case", params={"case": selected_case}))
    else:
        col_config.remediation = [r for r in col_config.remediation if r.type != "normalize_case"]

    # Data type-specific cleaning options
    if data_type == "date":
        _render_date_cleaning(col_config, col_name, existing_rems)
    elif data_type in ["integer", "float"]:
        _render_numeric_cleaning(col_config, col_name, existing_rems)
    elif data_type == "boolean":
        _render_boolean_cleaning(col_config, col_name, existing_rems)
    elif data_type == "text":
        _render_text_cleaning(col_config, col_name, existing_rems)


def _render_date_cleaning(col_config, col_name, existing_rems):
    """Render date-specific cleaning options."""
    st.markdown("##### Date Standardization")

    has_date_coerce = "date_coerce" in existing_rems
    date_coerce_check = st.checkbox(
        "Standardize date format",
        value=has_date_coerce,
        key=f"clean_date_{col_name}",
        help="Convert all dates to a consistent format. Invalid dates will be set to null.",
    )

    if date_coerce_check:
        format_options = get_common_format_names()
        current_format = existing_rems.get("date_coerce", RemediationConfig(type="date_coerce", params={})).params.get("target_format", format_options[0] if format_options else "YYYY-MM-DD")
        format_idx = format_options.index(current_format) if current_format in format_options else 0

        target_format = st.selectbox(
            "Target date format",
            options=format_options,
            index=format_idx,
            key=f"clean_date_fmt_{col_name}",
        )

        # Show example
        st.caption(f"Example: {_get_date_example(target_format)}")

        # Common input formats to try when parsing
        common_input_formats = [
            "YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "YYYY/MM/DD",
            "MM-DD-YYYY", "DD-MM-YYYY", "YYYYMMDD",
            "MM/DD/YY", "DD/MM/YY", "MMM DD, YYYY", "MMMM DD, YYYY",
            "DD-MMM-YYYY",
        ]

        params = {
            "target_format": target_format,
            "accepted_input_formats": common_input_formats,
            "on_parse_error": "set_null",  # Invalid dates become null
        }
        existing = next((r for r in col_config.remediation if r.type == "date_coerce"), None)
        if existing:
            existing.params = params
        else:
            col_config.remediation.append(RemediationConfig(type="date_coerce", params=params))
    elif has_date_coerce and not date_coerce_check:
        col_config.remediation = [r for r in col_config.remediation if r.type != "date_coerce"]


def _get_date_example(format_name):
    """Get an example date string for a format name."""
    examples = {
        "YYYY-MM-DD": "2000-01-15",
        "MM/DD/YYYY": "01/15/2000",
        "DD/MM/YYYY": "15/01/2000",
        "YYYY/MM/DD": "2000/01/15",
        "Month DD, YYYY": "January 15, 2000",
        "DD Month YYYY": "15 January 2000",
    }
    return examples.get(format_name, "2000-01-15")


def _render_numeric_cleaning(col_config, col_name, existing_rems):
    """Render numeric-specific cleaning options."""
    st.markdown("##### Numeric Formatting")

    has_numeric = "numeric_cleanup" in existing_rems
    numeric_check = st.checkbox(
        "Clean numeric formatting",
        value=has_numeric,
        key=f"clean_numeric_{col_name}",
        help="Remove currency symbols ($, EUR), thousand separators (,), and other non-numeric characters",
    )
    _toggle_remediation(col_config, "numeric_cleanup", numeric_check, existing_rems)


def _render_boolean_cleaning(col_config, col_name, existing_rems):
    """Render boolean-specific cleaning options."""
    st.markdown("##### Boolean Standardization")

    has_bool_norm = "boolean_normalization" in existing_rems
    bool_check = st.checkbox(
        "Standardize to true/false",
        value=has_bool_norm,
        key=f"clean_bool_{col_name}",
        help="Convert various boolean representations (yes/no, 1/0, Y/N) to true/false",
    )
    _toggle_remediation(col_config, "boolean_normalization", bool_check, existing_rems)


def _render_text_cleaning(col_config, col_name, existing_rems):
    """Render text-specific cleaning options."""
    st.markdown("##### Additional Text Options")

    has_null_std = "standardize_nulls" in existing_rems
    null_check = st.checkbox(
        "Standardize null values",
        value=has_null_std,
        key=f"clean_null_{col_name}",
        help="Convert common null representations (NA, N/A, None, etc.) to actual null",
    )
    _toggle_remediation(col_config, "standardize_nulls", null_check, existing_rems)


def _toggle_remediation(col_config, rem_type, enabled, existing_rems):
    """Toggle a simple remediation on or off."""
    has_rem = rem_type in existing_rems

    if enabled and not has_rem:
        col_config.remediation.append(RemediationConfig(type=rem_type, params={}))
    elif not enabled and has_rem:
        col_config.remediation = [r for r in col_config.remediation if r.type != rem_type]


def _apply_cleaning_to_all(contract, columns_to_configure, rem_type):
    """Apply a cleaning option to all columns."""
    for col_name in columns_to_configure:
        col_config = get_column_config(contract, col_name)
        if col_config is None:
            continue

        existing_rems = {r.type: r for r in col_config.remediation}
        if rem_type not in existing_rems:
            col_config.remediation.append(RemediationConfig(type=rem_type, params={}))


def _clear_all_cleaning(contract, columns_to_configure):
    """Clear all cleaning options from all columns."""
    for col_name in columns_to_configure:
        col_config = get_column_config(contract, col_name)
        if col_config is None:
            continue
        col_config.remediation = []


def _apply_case_to_all(contract, columns_to_configure, case_value):
    """Apply case normalization to all columns."""
    for col_name in columns_to_configure:
        col_config = get_column_config(contract, col_name)
        if col_config is None:
            continue

        # Remove existing normalize_case if any
        col_config.remediation = [r for r in col_config.remediation if r.type != "normalize_case"]

        # Add new normalize_case
        col_config.remediation.append(RemediationConfig(type="normalize_case", params={"case": case_value}))


def _apply_date_format_to_all(contract, date_columns, target_format):
    """Apply date format standardization to all date columns."""
    # Common input formats to try when parsing
    common_input_formats = [
        "YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "YYYY/MM/DD",
        "MM-DD-YYYY", "DD-MM-YYYY", "YYYYMMDD",
        "MM/DD/YY", "DD/MM/YY", "MMM DD, YYYY", "MMMM DD, YYYY",
        "DD-MMM-YYYY",
    ]

    for col_name in date_columns:
        col_config = get_column_config(contract, col_name)
        if col_config is None:
            continue

        # Remove existing date_coerce if any
        col_config.remediation = [r for r in col_config.remediation if r.type != "date_coerce"]

        # Add new date_coerce with comprehensive input formats
        col_config.remediation.append(RemediationConfig(
            type="date_coerce",
            params={
                "target_format": target_format,
                "accepted_input_formats": common_input_formats,
                "on_parse_error": "set_null",  # Invalid dates become null
            }
        ))
