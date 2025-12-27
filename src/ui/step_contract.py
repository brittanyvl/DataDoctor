"""
Step 2: Contract Builder - Define schema, tests, and remediation.

This module implements the unified contract configuration step that combines
contract creation/loading with test and remediation configuration.
"""

import streamlit as st
import pandas as pd

from src.constants import (
    COLUMN_TEST_TYPES,
    DATA_TYPES,
    FAILURE_ACTIONS,
    REMEDIATION_TYPES,
    CASE_OPTIONS,
)
from src.contract.builder import (
    build_contract_from_dataframe,
    add_column_test,
    add_column_remediation,
    add_dataset_test,
    get_column_config,
)
from src.contract.parser import (
    parse_yaml_file,
    extract_contract_metadata,
)
from src.contract.validator import validate_contract, format_validation_errors
from src.contract.schema import (
    FailureHandling,
    Normalization,
)
from src.presets.patterns import get_all_preset_names as get_pattern_presets
from src.presets.enums import get_all_enum_preset_names as get_enum_presets
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
    collapsible_section,
    get_help_text,
)


def render_step_contract():
    """Render the contract configuration step."""
    step_header(
        2,
        "Contract Builder",
        "Define your data schema, validation tests, and remediation rules.",
    )

    # Check if we have a dataframe
    df = st.session_state.get("dataframe")
    if df is None:
        error_box("No dataset loaded. Please upload a file first.")
        if st.button("Go to Upload"):
            set_current_step(1)
            st.rerun()
        return

    # Contract initialization
    contract = st.session_state.get("contract")

    if contract is None:
        _render_contract_source_selection(df)
        return

    # Contract is loaded - show configuration tabs
    st.subheader("Contract Configuration")

    source = st.session_state.get("contract_source", "built")
    metadata = extract_contract_metadata(contract)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Contract ID: {metadata['contract_id'][:8]}...")
    with col2:
        st.caption(f"Columns: {metadata['column_count']}")
    with col3:
        st.caption(f"Source: {source}")

    # Configuration tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Column Schema",
        "Column Tests",
        "Column Remediation",
        "Dataset Tests",
        "FK Checks",
    ])

    with tab1:
        _render_column_schema(contract, df)

    with tab2:
        _render_column_tests(contract, df)

    with tab3:
        _render_column_remediation(contract, df)

    with tab4:
        _render_dataset_tests(contract, df)

    with tab5:
        _render_fk_checks(contract, df)

    # Option to reset contract
    st.divider()
    with st.expander("Contract Options", expanded=False):
        if st.button("Reset Contract", type="secondary"):
            st.session_state["contract"] = None
            st.session_state["contract_hash"] = None
            st.session_state["contract_source"] = None
            st.rerun()

        # Upload different contract
        st.markdown("**Or upload a different contract:**")
        uploaded_contract = st.file_uploader(
            "Choose a YAML contract file",
            type=["yaml", "yml"],
            key="replace_contract_uploader",
        )
        if uploaded_contract:
            _handle_contract_upload(uploaded_contract, df)

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


def _render_contract_source_selection(df):
    """Render contract source selection (create or upload)."""
    st.subheader("Initialize Contract")

    contract_option = st.radio(
        "How would you like to start?",
        options=[
            "Create new contract from my data",
            "Upload existing YAML contract",
        ],
        help="Choose whether to create a new contract based on your data or upload a previously saved contract.",
    )

    if contract_option == "Create new contract from my data":
        st.markdown(
            "A new contract will be created with columns matching your dataset. "
            "You can then configure data types, tests, and remediation rules."
        )

        if st.button("Create Contract", type="primary"):
            filename = st.session_state.get("uploaded_file_name", "data.csv")
            sheet_name = st.session_state.get("sheet_name")

            with st.spinner("Creating contract..."):
                contract = build_contract_from_dataframe(df, filename, sheet_name)

                st.session_state["contract"] = contract
                st.session_state["contract_hash"] = compute_contract_hash(
                    {"id": contract.contract_id}
                )
                st.session_state["contract_source"] = "built"

            success_box("Contract created! Configure your validation rules below.")
            st.rerun()

    else:
        st.markdown(
            "Upload a previously saved YAML contract. "
            "The contract will be validated against your current dataset."
        )

        uploaded_contract = st.file_uploader(
            "Choose a YAML contract file",
            type=["yaml", "yml"],
            help="Upload a .yaml or .yml contract file",
        )

        if uploaded_contract:
            _handle_contract_upload(uploaded_contract, df)


def _handle_contract_upload(uploaded_contract, df):
    """Handle upload of a YAML contract file."""
    file_content = uploaded_contract.read()

    # Parse the contract
    contract, error = parse_yaml_file(file_content)

    if error:
        error_box(f"Failed to parse contract: {error}")
        return

    # Validate contract structure
    validation_result = validate_contract(contract)
    if not validation_result.is_valid:
        error_box(format_validation_errors(validation_result))
        return

    # Check column compatibility
    contract_columns = {col.name for col in contract.columns}
    data_columns = set(df.columns)

    missing_in_data = contract_columns - data_columns
    missing_in_contract = data_columns - contract_columns

    if missing_in_data:
        warning_box(
            f"Contract references columns not in data: {', '.join(missing_in_data)}"
        )

    if missing_in_contract:
        info_box(
            f"Data has columns not in contract (will use defaults): {', '.join(missing_in_contract)}"
        )

    # Store contract
    st.session_state["contract"] = contract
    st.session_state["contract_hash"] = compute_contract_hash(
        {"id": contract.contract_id}
    )
    st.session_state["contract_source"] = "uploaded"

    success_box("Contract loaded successfully!")
    st.rerun()


def _render_column_schema(contract, df):
    """Render column schema configuration."""
    st.markdown("Configure data types and requirements for each column.")

    # Column selector
    column_names = list(df.columns)
    selected_column = st.selectbox(
        "Select column to configure",
        options=column_names,
        key="schema_column_select",
    )

    if not selected_column:
        return

    col_config = get_column_config(contract, selected_column)

    if col_config is None:
        info_box(f"Column '{selected_column}' not in contract. Add it below.")
        return

    with st.form(key=f"col_schema_{selected_column}"):
        st.markdown(f"**Configure: {selected_column}**")

        col1, col2 = st.columns(2)

        with col1:
            # Data type
            current_type_idx = DATA_TYPES.index(col_config.data_type) if col_config.data_type in DATA_TYPES else 0
            data_type = st.selectbox(
                "Data Type",
                options=DATA_TYPES,
                index=current_type_idx,
                help=get_help_text("data_type"),
            )

            # Required
            required = st.checkbox(
                "Required (not null)",
                value=col_config.required,
            )

            # Rename
            rename_to = st.text_input(
                "Rename to (optional)",
                value=col_config.rename_to or "",
                help="New name for the column after processing",
            )

        with col2:
            # Failure handling
            current_action_idx = FAILURE_ACTIONS.index(col_config.failure_handling.action) if col_config.failure_handling.action in FAILURE_ACTIONS else 2
            failure_action = st.selectbox(
                "Default Failure Action",
                options=FAILURE_ACTIONS,
                index=current_action_idx,
                help=get_help_text("failure_handling"),
            )

            # Label column name (if label_failure)
            label_col_name = "__data_doctor_errors__"
            if failure_action == "label_failure":
                label_col_name = st.text_input(
                    "Error Label Column",
                    value=col_config.failure_handling.label_column_name or "__data_doctor_errors__",
                )

            # Quarantine name (if quarantine_row)
            quarantine_name = ""
            if failure_action == "quarantine_row":
                quarantine_name = st.text_input(
                    "Quarantine Export Name",
                    value=col_config.failure_handling.quarantine_export_name or f"quarantine_{selected_column}",
                )

        # Normalization options
        st.markdown("**Normalization Options**")
        norm = col_config.normalization or Normalization()

        norm_col1, norm_col2 = st.columns(2)

        with norm_col1:
            trim_whitespace = st.checkbox(
                "Trim whitespace",
                value=norm.trim_whitespace,
            )
            remove_non_printable = st.checkbox(
                "Remove non-printable characters",
                value=norm.remove_non_printable,
            )

        with norm_col2:
            case_idx = CASE_OPTIONS.index(norm.case) if norm.case in CASE_OPTIONS else 0
            case_norm = st.selectbox(
                "Case normalization",
                options=CASE_OPTIONS,
                index=case_idx,
            )

        if st.form_submit_button("Save Column Configuration"):
            # Update column config
            col_config.data_type = data_type
            col_config.required = required
            col_config.rename_to = rename_to if rename_to else None
            col_config.failure_handling = FailureHandling(
                action=failure_action,
                label_column_name=label_col_name if failure_action == "label_failure" else None,
                quarantine_export_name=quarantine_name if failure_action == "quarantine_row" else None,
            )
            col_config.normalization = Normalization(
                trim_whitespace=trim_whitespace,
                remove_non_printable=remove_non_printable,
                case=case_norm,
                null_tokens=norm.null_tokens,
            )

            success_box(f"Configuration saved for '{selected_column}'")
            st.rerun()


def _render_column_tests(contract, df):
    """Render column tests configuration."""
    st.markdown("Add validation tests to specific columns.")

    # Column selector
    column_names = list(df.columns)
    selected_column = st.selectbox(
        "Select column",
        options=column_names,
        key="test_column_select",
    )

    if not selected_column:
        return

    col_config = get_column_config(contract, selected_column)

    # Show existing tests
    if col_config and col_config.tests:
        st.markdown(f"**Current tests for {selected_column}:**")
        for i, test in enumerate(col_config.tests):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {test.type} ({test.severity})")
            with col2:
                if st.button("Remove", key=f"remove_test_{selected_column}_{i}"):
                    col_config.tests.pop(i)
                    st.rerun()

    # Add new test
    with st.expander("Add New Test", expanded=True):
        test_type = st.selectbox(
            "Test Type",
            options=COLUMN_TEST_TYPES,
            help="Select the type of validation test",
        )

        severity = st.radio(
            "Severity",
            options=["error", "warning"],
            horizontal=True,
        )

        # Test-specific parameters
        params = {}

        if test_type == "range":
            range_col1, range_col2 = st.columns(2)
            with range_col1:
                min_val = st.number_input("Minimum value", value=0.0)
                params["min"] = min_val
            with range_col2:
                max_val = st.number_input("Maximum value", value=100.0)
                params["max"] = max_val

        elif test_type == "length":
            len_col1, len_col2 = st.columns(2)
            with len_col1:
                min_len = st.number_input("Minimum length", min_value=0, value=0)
                if min_len > 0:
                    params["min"] = min_len
            with len_col2:
                max_len = st.number_input("Maximum length", min_value=0, value=0)
                if max_len > 0:
                    params["max"] = max_len

        elif test_type == "enum":
            enum_option = st.radio(
                "Enum source",
                options=["Custom values", "Preset"],
                horizontal=True,
            )

            if enum_option == "Custom values":
                values_str = st.text_area(
                    "Allowed values (one per line)",
                    help="Enter allowed values, one per line",
                )
                if values_str:
                    params["allowed_values"] = [v.strip() for v in values_str.split("\n") if v.strip()]
            else:
                preset = st.selectbox("Preset", options=get_enum_presets())
                params["preset"] = preset

            params["case_insensitive"] = st.checkbox("Case insensitive", value=True)

        elif test_type == "pattern":
            tier = st.radio(
                "Pattern type",
                options=["preset", "advanced"],
                horizontal=True,
            )
            params["tier"] = tier

            if tier == "preset":
                preset_name = st.selectbox("Pattern preset", options=get_pattern_presets())
                params["preset_name"] = preset_name
            else:
                pattern = st.text_input("Regex pattern", help="Enter a regular expression")
                params["pattern"] = pattern

        elif test_type == "date_rule":
            params["target_format"] = st.selectbox(
                "Target format",
                options=get_common_format_names(),
            )
            mode = st.radio("Mode", options=["simple", "robust"], horizontal=True)
            params["mode"] = mode

            if mode == "robust":
                formats_str = st.text_area(
                    "Accepted input formats (one per line)",
                    value=params["target_format"],
                )
                params["accepted_input_formats"] = [f.strip() for f in formats_str.split("\n") if f.strip()]
                params["excel_serial_enabled"] = st.checkbox("Accept Excel serial dates", value=False)

        elif test_type == "uniqueness":
            params["allow_nulls"] = st.checkbox("Allow nulls", value=True)

        elif test_type == "monotonic":
            params["direction"] = st.selectbox("Direction", options=["ascending", "descending"])
            params["strict"] = st.checkbox("Strict (no equal values)", value=False)

        elif test_type == "cardinality_warning":
            params["warn_if_above"] = st.number_input("Warn if cardinality above", min_value=1, value=100)

        if st.button("Add Test", type="primary"):
            contract = add_column_test(
                contract,
                selected_column,
                test_type,
                severity,
                params,
            )
            st.session_state["contract"] = contract
            success_box(f"Added {test_type} test to {selected_column}")
            st.rerun()


def _render_column_remediation(contract, df):
    """Render column remediation configuration."""
    st.markdown("Add remediation actions to clean data in specific columns.")

    # Column selector
    column_names = list(df.columns)
    selected_column = st.selectbox(
        "Select column",
        options=column_names,
        key="remediation_column_select",
    )

    if not selected_column:
        return

    col_config = get_column_config(contract, selected_column)

    # Show existing remediation actions
    if col_config and col_config.remediation:
        st.markdown(f"**Current remediation for {selected_column}:**")
        for i, rem in enumerate(col_config.remediation):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {rem.type}")
            with col2:
                if st.button("Remove", key=f"remove_rem_{selected_column}_{i}"):
                    col_config.remediation.pop(i)
                    st.rerun()

    # Add new remediation
    with st.expander("Add Remediation Action", expanded=True):
        rem_type = st.selectbox(
            "Remediation Type",
            options=REMEDIATION_TYPES,
            help="Select the type of remediation action",
        )

        params = {}

        if rem_type == "normalize_case":
            params["case"] = st.selectbox("Target case", options=["lower", "upper", "title"])

        elif rem_type == "date_coerce":
            params["target_format"] = st.selectbox(
                "Target format",
                options=get_common_format_names(),
            )
            params["accepted_input_formats"] = st.text_area(
                "Accepted input formats (one per line)",
                help="Enter accepted date formats, one per line",
            ).split("\n")
            params["accepted_input_formats"] = [f.strip() for f in params["accepted_input_formats"] if f.strip()]

        elif rem_type == "categorical_standardize":
            mappings_str = st.text_area(
                "Mappings (format: old_value -> new_value, one per line)",
                help="Example: yes -> Yes\\nno -> No",
            )
            mappings = {}
            for line in mappings_str.split("\n"):
                if "->" in line:
                    old, new = line.split("->", 1)
                    mappings[old.strip()] = new.strip()
            params["mappings"] = mappings

        elif rem_type == "split_column":
            params["delimiter"] = st.text_input("Delimiter", value=",")
            params["output_columns"] = st.text_input(
                "Output column names (comma-separated)",
                help="Names for the new columns created from split",
            ).split(",")
            params["output_columns"] = [c.strip() for c in params["output_columns"] if c.strip()]

        elif rem_type == "custom_calculation":
            params["expression"] = st.text_input(
                "Expression",
                help="Python expression using column names, e.g., price * quantity",
            )
            params["output_column"] = st.text_input(
                "Output column name",
                help="Name for the result column",
            )

        if st.button("Add Remediation", type="primary"):
            contract = add_column_remediation(
                contract,
                selected_column,
                rem_type,
                params,
            )
            st.session_state["contract"] = contract
            success_box(f"Added {rem_type} remediation to {selected_column}")
            st.rerun()


def _render_dataset_tests(contract, df):
    """Render dataset-level tests configuration."""
    st.markdown("Add tests that validate the entire dataset.")

    # Show existing tests
    if contract.dataset_tests:
        st.markdown("**Current dataset tests:**")
        for i, test in enumerate(contract.dataset_tests):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {test.type} ({test.severity})")
            with col2:
                if st.button("Remove", key=f"remove_dataset_test_{i}"):
                    contract.dataset_tests.pop(i)
                    st.rerun()

    # Add new test
    with st.expander("Add Dataset Test", expanded=True):
        test_type = st.selectbox(
            "Test Type",
            options=[
                "duplicate_rows",
                "primary_key_completeness",
                "primary_key_uniqueness",
                "composite_key_uniqueness",
                "cross_field_rule",
                "outliers_iqr",
                "outliers_zscore",
            ],
        )

        severity = st.radio(
            "Severity",
            options=["error", "warning"],
            horizontal=True,
            key="dataset_test_severity",
        )

        params = {}

        if test_type in ["primary_key_completeness", "primary_key_uniqueness", "composite_key_uniqueness"]:
            key_cols = st.multiselect(
                "Key columns",
                options=list(df.columns),
            )
            params["key_columns"] = key_cols

        elif test_type == "cross_field_rule":
            rule_name = st.text_input("Rule name", value="my_rule")
            params["rule_name"] = rule_name

            condition_cols = st.multiselect(
                "Columns that must not be null (optional)",
                options=list(df.columns),
            )
            if condition_cols:
                params["if"] = {"all_not_null": condition_cols}

            expression = st.text_input(
                "Expression",
                help="e.g., start_date <= end_date",
            )
            params["assert"] = {"expression": expression}

        elif test_type in ["outliers_iqr", "outliers_zscore"]:
            target_col = st.selectbox(
                "Target column",
                options=list(df.columns),
            )
            params["column"] = target_col

            if test_type == "outliers_iqr":
                params["multiplier"] = st.number_input("IQR multiplier", value=1.5, step=0.1)
            else:
                params["threshold"] = st.number_input("Z-score threshold", value=3.0, step=0.1)

        if st.button("Add Dataset Test", type="primary"):
            contract = add_dataset_test(
                contract,
                test_type,
                severity,
                params,
            )
            st.session_state["contract"] = contract
            success_box(f"Added {test_type} dataset test")
            st.rerun()


def _render_fk_checks(contract, df):
    """Render foreign key checks configuration."""
    st.markdown("Configure foreign key validation against reference data.")

    # Check if FK data is loaded
    fk_df = st.session_state.get("fk_dataframe")

    if fk_df is None:
        info_box(
            "No FK reference data loaded. Upload a FK file in Step 1 to enable FK validation."
        )
        return

    fk_source = st.session_state.get("fk_sheet_name") or st.session_state.get("fk_file_name", "Unknown")
    st.markdown(f"**FK Reference Source:** {fk_source} ({len(fk_df):,} rows)")

    # Show existing checks
    if contract.foreign_key_checks:
        st.markdown("**Current FK checks:**")
        for i, fk in enumerate(contract.foreign_key_checks):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {fk.name}: {fk.dataset_column} -> {fk.fk_column}")
            with col2:
                if st.button("Remove", key=f"remove_fk_{i}"):
                    contract.foreign_key_checks.pop(i)
                    st.rerun()

    # Add new FK check
    with st.expander("Add FK Check", expanded=True):
        fk_name = st.text_input("Check name", value="fk_check")

        col1, col2 = st.columns(2)

        with col1:
            dataset_column = st.selectbox(
                "Dataset column",
                options=list(df.columns),
                help="Column in your data to validate",
            )

        with col2:
            fk_column = st.selectbox(
                "FK reference column",
                options=list(fk_df.columns),
                help="Column in FK reference containing valid values",
            )

        allow_nulls = st.checkbox("Allow null values", value=True)

        if st.button("Add FK Check", type="primary"):
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
