"""
Step 2: Contract Builder - Configure validation rules for each column.

This module implements the contract configuration step where users define
validation tests and remediation rules for each column in their dataset.
"""

import streamlit as st
import pandas as pd

from src.constants import (
    DATA_TYPES,
    FAILURE_ACTION_LABELS,
    FAILURE_LABEL_TO_ACTION,
)
from src.contract.builder import (
    build_contract_from_dataframe,
    build_import_settings_from_session,
    get_column_config,
)
from src.contract.validator import validate_contract, format_validation_errors
from src.contract.schema import (
    FailureHandling,
    Normalization,
    TestConfig,
    RemediationConfig,
)
from src.presets.patterns import (
    get_all_pattern_display_names,
    get_pattern_key_from_display,
    pattern_requires_input,
    PATTERNS_REQUIRING_INPUT,
)
from src.presets.enums import (
    get_all_enum_preset_display_names,
    get_enum_key_from_display,
)
from src.presets.date_formats import get_common_format_names
from src.session import (
    compute_contract_hash,
    set_current_step,
)
from src.ui.components import (
    step_header,
    error_box,
    success_box,
    info_box,
    warning_box,
    navigation_buttons,
)

# Characters removed by "Remove special characters" remediation
SPECIAL_CHARS_REMOVED = "Control characters (ASCII 0-31), null bytes, backspace, form feed, vertical tab, and other non-printable characters"


def render_step_contract():
    """Render the contract configuration step."""
    step_header(
        2,
        "Configure Validation Rules",
        "Define validation tests and remediation rules for each column.",
    )

    # Check if we have a dataframe
    df = st.session_state.get("dataframe")
    if df is None:
        error_box("No dataset loaded. Please upload a file first.")
        if st.button("Go to Upload"):
            set_current_step(1)
            st.rerun()
        return

    # Get ignored columns from step 1
    ignored_columns = st.session_state.get("ignored_columns", [])

    # Get columns to configure (excluding ignored)
    columns_to_configure = [col for col in df.columns if col not in ignored_columns]

    if not columns_to_configure:
        warning_box("All columns are marked as ignored. Please go back and select columns to validate.")
        if st.button("Go to Upload"):
            set_current_step(1)
            st.rerun()
        return

    # Initialize or get contract
    contract = _ensure_contract_exists(df, ignored_columns)

    # Summary
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Columns to Validate", len(columns_to_configure))
    with col2:
        st.metric("Ignored", len(ignored_columns))

    # Configuration tabs
    tab1, tab2, tab3 = st.tabs([
        "Column Rules",
        "Dataset Tests",
        "FK Checks",
    ])

    with tab1:
        _render_column_rules(contract, df, columns_to_configure)

    with tab2:
        _render_dataset_tests(contract, df, columns_to_configure)

    with tab3:
        _render_fk_checks(contract, df, columns_to_configure)

    # Navigation
    st.divider()
    back_clicked, next_clicked = navigation_buttons(
        back_label="Back to Upload",
        next_label="Run Validation",
    )

    if back_clicked:
        set_current_step(1)
        st.rerun()

    if next_clicked:
        # Validate contract before proceeding
        validation_result = validate_contract(contract)
        if not validation_result.is_valid:
            error_box(format_validation_errors(validation_result))
            return

        set_current_step(3)
        st.rerun()


def _ensure_contract_exists(df, ignored_columns):
    """Ensure a contract exists, creating one if needed."""
    contract = st.session_state.get("contract")

    # Check if we have an uploaded contract from step 1
    uploaded_contract = st.session_state.get("uploaded_contract")
    if uploaded_contract and contract is None:
        contract = uploaded_contract
        st.session_state["contract"] = contract
        st.session_state["contract_source"] = "uploaded"
        st.session_state["contract_hash"] = compute_contract_hash({"id": contract.contract_id})

    # Create new contract if none exists
    if contract is None:
        filename = st.session_state.get("uploaded_file_name", "data.csv")
        sheet_name = st.session_state.get("sheet_name")

        # Build import settings from session
        import_settings = build_import_settings_from_session(dict(st.session_state))

        contract = build_contract_from_dataframe(
            df,
            filename,
            sheet_name,
            import_settings=import_settings,
            ignored_columns=ignored_columns,
        )

        st.session_state["contract"] = contract
        st.session_state["contract_hash"] = compute_contract_hash({"id": contract.contract_id})
        st.session_state["contract_source"] = "built"

    return contract


def _render_column_rules(contract, df, columns_to_configure):
    """Render column-by-column rule configuration with per-column sections."""
    st.markdown("Configure each column below.")

    # Each column displayed directly on page (no expanders)
    for i, col_name in enumerate(columns_to_configure):
        col_config = get_column_config(contract, col_name)
        if col_config is None:
            continue

        # Add divider between columns (not before first)
        if i > 0:
            st.divider()

        # Column header
        tests_count = len(col_config.tests)
        required_badge = " *(Required)*" if col_config.required else ""
        rules_badge = f" — {tests_count} rule(s)" if tests_count > 0 else ""
        st.markdown(f"## {col_name}{required_badge}{rules_badge}")

        _render_single_column_config(contract, df, col_name, col_config)


def _render_column_preview_table(df, col_name):
    """Render a small table showing 3 sample values for this column."""
    col_data = df[col_name].dropna()
    samples = col_data.head(3).tolist()

    # Pad with empty strings if less than 3 values
    while len(samples) < 3:
        samples.append("")

    # Create a small dataframe for display
    preview_df = pd.DataFrame({
        col_name: [str(s)[:50] for s in samples]  # Truncate long values
    })
    st.dataframe(preview_df, use_container_width=True, hide_index=True)


def _render_single_column_config(contract, df, col_name, col_config):
    """Render configuration for a single column."""
    # Preview table at top of section
    st.markdown("##### Sample Data")
    _render_column_preview_table(df, col_name)

    # Statistics row
    col_data = df[col_name]
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.caption(f"Non-null: {col_data.notna().sum():,}")
    with stat_cols[1]:
        st.caption(f"Null: {col_data.isna().sum():,}")
    with stat_cols[2]:
        st.caption(f"Unique: {col_data.nunique():,}")
    with stat_cols[3]:
        st.caption(f"Inferred: {str(col_data.dtype)[:10]}")

    st.divider()

    # Column Settings - adjusted column widths (1:2:3 ratio)
    st.markdown("##### Column Settings")
    settings_cols = st.columns([1, 2, 3])

    with settings_cols[0]:
        required = st.checkbox(
            "Required",
            value=col_config.required,
            key=f"req_{col_name}",
            help="Values in this column cannot be empty/null",
        )

    with settings_cols[1]:
        current_type_idx = DATA_TYPES.index(col_config.data_type) if col_config.data_type in DATA_TYPES else 0
        data_type = st.selectbox(
            "Data Type",
            options=DATA_TYPES,
            index=current_type_idx,
            key=f"dtype_{col_name}",
            label_visibility="collapsed",
        )

    with settings_cols[2]:
        failure_labels = list(FAILURE_ACTION_LABELS.values())
        current_action = col_config.failure_handling.action
        current_label = FAILURE_ACTION_LABELS.get(current_action, failure_labels[2])
        current_idx = failure_labels.index(current_label) if current_label in failure_labels else 2

        failure_label = st.selectbox(
            "On Failure",
            options=failure_labels,
            index=current_idx,
            key=f"fail_{col_name}",
            label_visibility="collapsed",
        )
        failure_action = FAILURE_LABEL_TO_ACTION.get(failure_label, "label_failure")

    # Apply settings if changed
    if required != col_config.required or data_type != col_config.data_type or failure_action != col_config.failure_handling.action:
        col_config.required = required
        col_config.data_type = data_type
        col_config.failure_handling = FailureHandling(
            action=failure_action,
            label_column_name="__data_doctor_errors__" if failure_action == "label_failure" else None,
        )

    st.divider()

    # Validation Rules - no expander, just section
    st.markdown("##### Validation Rules")
    _render_validation_rules(contract, col_config, col_name, data_type)

    st.divider()

    # Formatting/Remediation - no expander
    st.markdown("##### Formatting (Remediation)")
    _render_remediation_options(contract, col_config, col_name, data_type)


def _render_validation_rules(contract, col_config, col_name, data_type):
    """Render validation rule checkboxes based on data type."""
    # Track which tests are already enabled
    existing_tests = {t.type: t for t in col_config.tests}

    # Common rules for all types
    rule_cols = st.columns(2)

    with rule_cols[0]:
        # Uniqueness
        has_unique = "uniqueness" in existing_tests
        unique_check = st.checkbox(
            "Must be unique",
            value=has_unique,
            key=f"unique_{col_name}",
            help="Each value in this column must be different",
        )
        _toggle_test(col_config, "uniqueness", unique_check, existing_tests)

    with rule_cols[1]:
        # Approved Values (enum)
        has_enum = "enum" in existing_tests
        enum_check = st.checkbox(
            "Approved values only",
            value=has_enum,
            key=f"enum_{col_name}",
            help="Values must match a predefined list",
        )

    # If approved values is checked, show single dropdown
    if enum_check:
        _render_approved_values_dropdown(col_config, col_name, existing_tests)
    elif has_enum and not enum_check:
        # Remove enum test
        col_config.tests = [t for t in col_config.tests if t.type != "enum"]

    # Data type specific rules
    if data_type in ["integer", "float"]:
        _render_numeric_rules(col_config, col_name, existing_tests)
    elif data_type == "string":
        _render_string_rules(col_config, col_name, existing_tests)
    elif data_type == "date":
        _render_date_rules(col_config, col_name, existing_tests)
    elif data_type == "timestamp":
        _render_timestamp_rules(col_config, col_name, existing_tests)
    elif data_type == "boolean":
        _render_boolean_rules(col_config, col_name, existing_tests)


def _toggle_test(col_config, test_type, enabled, existing_tests):
    """Toggle a simple test on or off."""
    has_test = test_type in existing_tests

    if enabled and not has_test:
        # Add the test
        col_config.tests.append(TestConfig(type=test_type, severity="error"))
    elif not enabled and has_test:
        # Remove the test
        col_config.tests = [t for t in col_config.tests if t.type != test_type]


def _render_approved_values_dropdown(col_config, col_name, existing_tests):
    """Render approved values (enum) as single dropdown with Custom + presets."""
    # Build options: Custom list first, then all presets
    preset_options = get_all_enum_preset_display_names()
    all_options = ["Custom list (enter values below)"] + preset_options

    # Get current selection if exists
    existing = next((t for t in col_config.tests if t.type == "enum"), None)
    current_idx = 0
    if existing and existing.params.get("preset"):
        # Find matching preset
        preset_key = existing.params.get("preset")
        for i, opt in enumerate(preset_options):
            if get_enum_key_from_display(opt) == preset_key:
                current_idx = i + 1  # +1 because Custom is first
                break

    selected = st.selectbox(
        "Select approved values source",
        options=all_options,
        index=current_idx,
        key=f"enum_source_{col_name}",
    )

    params = {}

    if selected == "Custom list (enter values below)":
        values_str = st.text_area(
            "Enter allowed values (one per line)",
            key=f"enum_vals_{col_name}",
            height=100,
        )
        if values_str:
            params["allowed_values"] = [v.strip() for v in values_str.split("\n") if v.strip()]
    else:
        # It's a preset
        params["preset"] = get_enum_key_from_display(selected)

    params["case_insensitive"] = st.checkbox(
        "Ignore case when matching",
        value=True,
        key=f"enum_case_{col_name}",
    )

    # Update or add test
    if existing:
        existing.params = params
    else:
        col_config.tests.append(TestConfig(type="enum", severity="error", params=params))


def _render_numeric_rules(col_config, col_name, existing_tests):
    """Render rules specific to numeric types."""
    st.markdown("**Numeric Options:**")

    num_cols = st.columns(2)

    with num_cols[0]:
        # Range check
        has_range = "range" in existing_tests
        range_check = st.checkbox(
            "Set min/max range",
            value=has_range,
            key=f"range_{col_name}",
        )

    with num_cols[1]:
        # Monotonic (sequential)
        has_mono = "monotonic" in existing_tests
        mono_check = st.checkbox(
            "Must be sequential",
            value=has_mono,
            key=f"mono_{col_name}",
            help="Values must always increase or decrease (e.g., ID numbers, dates)",
        )

    if range_check:
        range_cols = st.columns(2)
        with range_cols[0]:
            min_val = st.number_input(
                "Minimum value",
                value=existing_tests.get("range", TestConfig(type="range", params={})).params.get("min", 0.0),
                key=f"range_min_{col_name}",
            )
        with range_cols[1]:
            max_val = st.number_input(
                "Maximum value",
                value=existing_tests.get("range", TestConfig(type="range", params={})).params.get("max", 100.0),
                key=f"range_max_{col_name}",
            )

        # Update or add test
        existing = next((t for t in col_config.tests if t.type == "range"), None)
        if existing:
            existing.params = {"min": min_val, "max": max_val}
        else:
            col_config.tests.append(TestConfig(type="range", severity="error", params={"min": min_val, "max": max_val}))
    elif has_range and not range_check:
        col_config.tests = [t for t in col_config.tests if t.type != "range"]

    if mono_check:
        mono_cols = st.columns(2)
        with mono_cols[0]:
            mono_dir = st.selectbox(
                "Direction",
                options=["ascending", "descending"],
                index=0 if existing_tests.get("monotonic", TestConfig(type="monotonic", params={})).params.get("direction", "ascending") == "ascending" else 1,
                key=f"mono_dir_{col_name}",
            )
        with mono_cols[1]:
            mono_strict = st.checkbox(
                "No duplicates allowed",
                value=existing_tests.get("monotonic", TestConfig(type="monotonic", params={})).params.get("strict", False),
                key=f"mono_strict_{col_name}",
            )

        # Update or add test
        existing = next((t for t in col_config.tests if t.type == "monotonic"), None)
        if existing:
            existing.params = {"direction": mono_dir, "strict": mono_strict}
        else:
            col_config.tests.append(TestConfig(type="monotonic", severity="error", params={"direction": mono_dir, "strict": mono_strict}))
    elif has_mono and not mono_check:
        col_config.tests = [t for t in col_config.tests if t.type != "monotonic"]


def _render_string_rules(col_config, col_name, existing_tests):
    """Render rules specific to string types."""
    st.markdown("**Text Options:**")

    str_cols = st.columns(2)

    with str_cols[0]:
        # Length check
        has_length = "length" in existing_tests
        length_check = st.checkbox(
            "Set length limits",
            value=has_length,
            key=f"length_{col_name}",
        )

    with str_cols[1]:
        # Pattern check
        has_pattern = "pattern" in existing_tests
        pattern_check = st.checkbox(
            "Must match pattern",
            value=has_pattern,
            key=f"pattern_{col_name}",
            help="Validate against common formats like email, phone, etc.",
        )

    if length_check:
        len_cols = st.columns(2)
        with len_cols[0]:
            min_len = st.number_input(
                "Min characters",
                min_value=0,
                value=existing_tests.get("length", TestConfig(type="length", params={})).params.get("min", 0),
                key=f"len_min_{col_name}",
            )
        with len_cols[1]:
            max_len = st.number_input(
                "Max characters",
                min_value=0,
                value=existing_tests.get("length", TestConfig(type="length", params={})).params.get("max", 255),
                key=f"len_max_{col_name}",
            )

        params = {}
        if min_len > 0:
            params["min"] = min_len
        if max_len > 0:
            params["max"] = max_len

        # Update or add test
        existing = next((t for t in col_config.tests if t.type == "length"), None)
        if existing:
            existing.params = params
        else:
            col_config.tests.append(TestConfig(type="length", severity="error", params=params))
    elif has_length and not length_check:
        col_config.tests = [t for t in col_config.tests if t.type != "length"]

    if pattern_check:
        _render_pattern_dropdown(col_config, col_name, existing_tests)
    elif has_pattern and not pattern_check:
        col_config.tests = [t for t in col_config.tests if t.type != "pattern"]


def _render_pattern_dropdown(col_config, col_name, existing_tests):
    """Render pattern selection as single dropdown with Custom at end."""
    # Get all pattern display names
    pattern_options = get_all_pattern_display_names()

    # Get current selection if exists
    existing = next((t for t in col_config.tests if t.type == "pattern"), None)
    current_idx = 0
    if existing:
        preset_name = existing.params.get("preset_name")
        if preset_name:
            # Find matching display name
            for i, opt in enumerate(pattern_options):
                if get_pattern_key_from_display(opt) == preset_name:
                    current_idx = i
                    break

    selected = st.selectbox(
        "Select pattern format",
        options=pattern_options,
        index=current_idx,
        key=f"pattern_format_{col_name}",
    )

    pattern_key = get_pattern_key_from_display(selected)
    params = {}

    # Check if this pattern needs additional input
    if pattern_key == "starts_with":
        prefix = st.text_input("Must start with:", key=f"pat_prefix_{col_name}")
        params = {"tier": "builder", "starts_with": prefix}
    elif pattern_key == "ends_with":
        suffix = st.text_input("Must end with:", key=f"pat_suffix_{col_name}")
        params = {"tier": "builder", "ends_with": suffix}
    elif pattern_key == "contains":
        text = st.text_input("Must contain:", key=f"pat_contains_{col_name}")
        params = {"tier": "builder", "contains": text}
    elif pattern_key == "custom":
        pattern = st.text_input(
            "Enter custom pattern",
            key=f"pat_custom_{col_name}",
            help="Use standard pattern syntax (e.g., [A-Z]{2}[0-9]{4} for 2 letters + 4 digits)",
        )
        params = {"tier": "advanced", "pattern": pattern}
    else:
        # Standard preset
        params = {"tier": "preset", "preset_name": pattern_key}

    # Update or add test
    if existing:
        existing.params = params
    else:
        col_config.tests.append(TestConfig(type="pattern", severity="error", params=params))


def _render_date_rules(col_config, col_name, existing_tests):
    """Render rules specific to date types."""
    st.markdown("**Date Options:**")

    has_date_rule = "date_rule" in existing_tests
    date_format_check = st.checkbox(
        "Specify expected format",
        value=has_date_rule,
        key=f"date_fmt_{col_name}",
    )

    if date_format_check:
        format_options = get_common_format_names()
        current_format = existing_tests.get("date_rule", TestConfig(type="date_rule", params={})).params.get("target_format", format_options[0] if format_options else "YYYY-MM-DD")
        format_idx = format_options.index(current_format) if current_format in format_options else 0

        selected_format = st.selectbox(
            "Date format",
            options=format_options,
            index=format_idx,
            key=f"date_format_{col_name}",
            help="Example: January 1st 2000 would be 01/01/2000 in MM/DD/YYYY format",
        )

        # Show example
        st.caption(f"Example: {_get_date_example(selected_format)}")

        params = {"target_format": selected_format, "mode": "robust"}

        # Update or add test
        existing = next((t for t in col_config.tests if t.type == "date_rule"), None)
        if existing:
            existing.params = params
        else:
            col_config.tests.append(TestConfig(type="date_rule", severity="error", params=params))
    elif has_date_rule and not date_format_check:
        col_config.tests = [t for t in col_config.tests if t.type != "date_rule"]

    # Date window check
    has_window = "date_window" in existing_tests
    window_check = st.checkbox(
        "Set valid date range",
        value=has_window,
        key=f"date_window_{col_name}",
    )

    if window_check:
        win_cols = st.columns(2)
        with win_cols[0]:
            not_before = st.date_input(
                "Not before",
                key=f"date_before_{col_name}",
            )
        with win_cols[1]:
            not_after = st.date_input(
                "Not after",
                key=f"date_after_{col_name}",
            )

        params = {
            "not_before": not_before.strftime("%Y-%m-%d") if not_before else None,
            "not_after": not_after.strftime("%Y-%m-%d") if not_after else None,
        }

        # Update or add test
        existing = next((t for t in col_config.tests if t.type == "date_window"), None)
        if existing:
            existing.params = params
        else:
            col_config.tests.append(TestConfig(type="date_window", severity="error", params=params))
    elif has_window and not window_check:
        col_config.tests = [t for t in col_config.tests if t.type != "date_window"]


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


def _render_timestamp_rules(col_config, col_name, existing_tests):
    """Render rules specific to timestamp types."""
    st.markdown("**Timestamp Options:**")
    st.caption("Timestamps include both date and time components.")

    # Similar to date but for timestamps
    has_window = "date_window" in existing_tests
    window_check = st.checkbox(
        "Set valid timestamp range",
        value=has_window,
        key=f"ts_window_{col_name}",
    )

    if window_check:
        win_cols = st.columns(2)
        with win_cols[0]:
            not_before = st.date_input(
                "Not before",
                key=f"ts_before_{col_name}",
            )
        with win_cols[1]:
            not_after = st.date_input(
                "Not after",
                key=f"ts_after_{col_name}",
            )

        params = {
            "not_before": not_before.strftime("%Y-%m-%d") if not_before else None,
            "not_after": not_after.strftime("%Y-%m-%d") if not_after else None,
        }

        # Update or add test
        existing = next((t for t in col_config.tests if t.type == "date_window"), None)
        if existing:
            existing.params = params
        else:
            col_config.tests.append(TestConfig(type="date_window", severity="error", params=params))
    elif has_window and not window_check:
        col_config.tests = [t for t in col_config.tests if t.type != "date_window"]


def _render_boolean_rules(col_config, col_name, existing_tests):
    """Render rules specific to boolean types."""
    st.markdown("**Boolean Options:**")

    st.caption("Select which values should be recognized as true/false:")

    bool_format = st.selectbox(
        "Boolean format",
        options=[
            "true/false (text)",
            "1/0 (numeric)",
            "yes/no",
            "Y/N",
            "Any standard format",
        ],
        key=f"bool_fmt_{col_name}",
        help="Choose how boolean values are represented in your data",
    )

    # Store this in normalization or as a note (doesn't create a separate test)
    st.caption(f"Selected format: {bool_format}")


def _render_remediation_options(contract, col_config, col_name, data_type):
    """Render remediation/formatting options."""
    # Track existing remediation
    existing_rems = {r.type: r for r in col_config.remediation}

    rem_cols = st.columns(2)

    with rem_cols[0]:
        # Trim whitespace
        has_trim = "trim_whitespace" in existing_rems
        trim_check = st.checkbox(
            "Trim whitespace",
            value=has_trim,
            key=f"rem_trim_{col_name}",
            help="Remove leading/trailing spaces",
        )
        _toggle_remediation(col_config, "trim_whitespace", trim_check, existing_rems)

    with rem_cols[1]:
        # Remove non-printable with detailed tooltip
        has_nonprint = "remove_non_printable" in existing_rems
        nonprint_check = st.checkbox(
            "Remove special characters",
            value=has_nonprint,
            key=f"rem_nonprint_{col_name}",
            help=f"Removes: {SPECIAL_CHARS_REMOVED}",
        )
        _toggle_remediation(col_config, "remove_non_printable", nonprint_check, existing_rems)

    # Normalize case as dropdown (not checkbox + dropdown)
    st.markdown("**Text Case:**")
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
        key=f"rem_case_{col_name}",
        label_visibility="collapsed",
    )

    selected_case = case_map[case_selection]
    if selected_case:
        # Add or update normalize_case remediation
        existing = next((r for r in col_config.remediation if r.type == "normalize_case"), None)
        if existing:
            existing.params = {"case": selected_case}
        else:
            col_config.remediation.append(RemediationConfig(type="normalize_case", params={"case": selected_case}))
    else:
        # Remove normalize_case if "As Entered" selected
        col_config.remediation = [r for r in col_config.remediation if r.type != "normalize_case"]

    # Data type specific remediation
    if data_type == "date":
        has_date_coerce = "date_coerce" in existing_rems
        date_coerce_check = st.checkbox(
            "Standardize date format",
            value=has_date_coerce,
            key=f"rem_date_{col_name}",
        )

        if date_coerce_check:
            target_format = st.selectbox(
                "Target format",
                options=get_common_format_names(),
                key=f"rem_date_fmt_{col_name}",
            )
            params = {"target_format": target_format}

            existing = next((r for r in col_config.remediation if r.type == "date_coerce"), None)
            if existing:
                existing.params = params
            else:
                col_config.remediation.append(RemediationConfig(type="date_coerce", params=params))
        elif has_date_coerce and not date_coerce_check:
            col_config.remediation = [r for r in col_config.remediation if r.type != "date_coerce"]

    elif data_type in ["integer", "float"]:
        has_numeric = "numeric_cleanup" in existing_rems
        numeric_check = st.checkbox(
            "Clean numeric formatting",
            value=has_numeric,
            key=f"rem_numeric_{col_name}",
            help="Remove currency symbols, commas, etc.",
        )
        _toggle_remediation(col_config, "numeric_cleanup", numeric_check, existing_rems)

    elif data_type == "boolean":
        has_bool_norm = "boolean_normalization" in existing_rems
        bool_check = st.checkbox(
            "Standardize to true/false",
            value=has_bool_norm,
            key=f"rem_bool_{col_name}",
        )
        _toggle_remediation(col_config, "boolean_normalization", bool_check, existing_rems)


def _toggle_remediation(col_config, rem_type, enabled, existing_rems):
    """Toggle a simple remediation on or off."""
    has_rem = rem_type in existing_rems

    if enabled and not has_rem:
        col_config.remediation.append(RemediationConfig(type=rem_type, params={}))
    elif not enabled and has_rem:
        col_config.remediation = [r for r in col_config.remediation if r.type != rem_type]


def _render_dataset_tests(contract, df, columns_to_configure):
    """Render dataset-level tests configuration."""
    st.markdown("Add tests that validate the entire dataset.")

    # Show existing
    if contract.dataset_tests:
        st.markdown("**Current dataset tests:**")
        for i, test in enumerate(contract.dataset_tests):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- **{test.type}** ({test.severity})")
            with col2:
                if st.button("Remove", key=f"rm_ds_test_{i}"):
                    contract.dataset_tests.pop(i)
                    st.rerun()
        st.divider()

    # Checkbox-based dataset tests
    st.markdown("**Add dataset tests:**")

    # Duplicate row check
    dup_check = st.checkbox(
        "Check for duplicate rows",
        key="ds_dup_check",
        help="Flag rows that are exact duplicates of other rows",
    )

    if dup_check:
        if not any(t.type == "duplicate_rows" for t in contract.dataset_tests):
            from src.contract.schema import DatasetTest
            contract.dataset_tests.append(DatasetTest(type="duplicate_rows", severity="error"))
    else:
        contract.dataset_tests = [t for t in contract.dataset_tests if t.type != "duplicate_rows"]

    # Primary key check
    pk_check = st.checkbox(
        "Primary key uniqueness",
        key="ds_pk_check",
        help="Ensure selected column(s) uniquely identify each row",
    )

    if pk_check:
        pk_columns = st.multiselect(
            "Select key column(s)",
            options=columns_to_configure,
            key="ds_pk_cols",
        )

        if pk_columns:
            test_type = "composite_key_uniqueness" if len(pk_columns) > 1 else "primary_key_uniqueness"

            existing = next((t for t in contract.dataset_tests if t.type in ["primary_key_uniqueness", "composite_key_uniqueness"]), None)
            if existing:
                existing.type = test_type
                existing.params = {"key_columns": pk_columns}
            else:
                from src.contract.schema import DatasetTest
                contract.dataset_tests.append(DatasetTest(
                    type=test_type,
                    severity="error",
                    params={"key_columns": pk_columns}
                ))
    else:
        contract.dataset_tests = [t for t in contract.dataset_tests if t.type not in ["primary_key_uniqueness", "composite_key_uniqueness"]]

    # Cross-field rule
    xf_check = st.checkbox(
        "Cross-field validation",
        key="ds_xf_check",
        help="Validate relationships between columns (e.g., start_date <= end_date)",
    )

    if xf_check:
        st.text_input(
            "Rule name",
            value="my_rule",
            key="ds_xf_name",
        )
        expression = st.text_input(
            "Expression",
            key="ds_xf_expr",
            help="Example: start_date <= end_date",
        )

        if expression:
            existing = next((t for t in contract.dataset_tests if t.type == "cross_field_rule"), None)
            if existing:
                existing.params = {"rule_name": st.session_state.get("ds_xf_name", "my_rule"), "assert": {"expression": expression}}
            else:
                from src.contract.schema import DatasetTest
                contract.dataset_tests.append(DatasetTest(
                    type="cross_field_rule",
                    severity="error",
                    params={"rule_name": st.session_state.get("ds_xf_name", "my_rule"), "assert": {"expression": expression}}
                ))
    else:
        contract.dataset_tests = [t for t in contract.dataset_tests if t.type != "cross_field_rule"]


def _render_fk_checks(contract, df, columns_to_configure):
    """Render foreign key checks configuration."""
    st.markdown("Configure foreign key validation against reference data.")

    fk_df = st.session_state.get("fk_dataframe")

    if fk_df is None:
        info_box(
            "No FK reference data loaded. Upload a FK file in Step 1 to enable FK validation."
        )
        return

    fk_source = st.session_state.get("fk_source", "Unknown")
    st.markdown(f"**FK Reference:** {fk_source} ({len(fk_df):,} rows)")

    # Show existing
    if contract.foreign_key_checks:
        st.markdown("**Current FK checks:**")
        for i, fk in enumerate(contract.foreign_key_checks):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- **{fk.name}**: {fk.dataset_column} -> {fk.fk_column}")
            with col2:
                if st.button("Remove", key=f"rm_fk_{i}"):
                    contract.foreign_key_checks.pop(i)
                    st.rerun()
        st.divider()

    # Add new
    st.markdown("**Add FK check:**")

    fk_name = st.text_input("Check name", value="fk_check", key="fk_name")

    col1, col2 = st.columns(2)
    with col1:
        dataset_column = st.selectbox(
            "Dataset column",
            options=columns_to_configure,
            key="fk_ds_col",
        )
    with col2:
        fk_column = st.selectbox(
            "FK reference column",
            options=list(fk_df.columns),
            key="fk_ref_col",
        )

    allow_nulls = st.checkbox("Allow null values", value=True, key="fk_nulls")

    if st.button("Add FK Check", type="primary", key="add_fk"):
        from src.contract.builder import add_foreign_key_check
        contract = add_foreign_key_check(
            contract,
            name=fk_name,
            dataset_column=dataset_column,
            fk_file=fk_source,
            fk_column=fk_column,
            allow_nulls=allow_nulls,
        )
        st.session_state["contract"] = contract
        success_box(f"Added FK check: {fk_name}")
        st.rerun()
