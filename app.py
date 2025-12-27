"""
Data Doctor - Data Quality and Remediation Tool

Main Streamlit application entry point.

This application allows users to:
- Upload tabular datasets (CSV, Excel)
- Define or upload YAML-based data contracts
- Validate data against schema and quality rules
- Optionally remediate data issues
- Export cleaned data and quality reports
"""

import streamlit as st

from src.constants import APP_NAME, APP_VERSION, UI_STEPS
from src.session import initialize_session_state, get_current_step, set_current_step
from src.ui.components import progress_indicator
from src.ui.privacy import render_privacy_page
from src.ui.step_upload import render_step_upload
from src.ui.step_contract import render_step_contract
from src.ui.step_results import render_step_results
from src.ui.step_export import render_step_export


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="DD",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    _render_sidebar()

    # Get current step
    current_step = get_current_step()

    # Check for privacy page
    if st.session_state.get("show_privacy_page", False):
        render_privacy_page()
        return

    # Render progress indicator
    progress_indicator(current_step, total_steps=4)

    # Render current step (4-step workflow)
    if current_step == 1:
        render_step_upload()
    elif current_step == 2:
        render_step_contract()
    elif current_step == 3:
        render_step_results()
    elif current_step == 4:
        render_step_export()
    else:
        st.error(f"Unknown step: {current_step}")
        set_current_step(1)
        st.rerun()


def _render_sidebar():
    """Render the application sidebar."""
    with st.sidebar:
        st.title(APP_NAME)
        st.caption(f"Version {APP_VERSION}")

        st.markdown("---")

        # Step navigation
        st.markdown("### Workflow")

        current_step = get_current_step()

        for step in UI_STEPS:
            step_num = step["number"]
            step_name = step["name"]

            # Determine if step is accessible
            is_current = step_num == current_step
            is_completed = step_num < current_step

            # Style the step indicator
            if is_current:
                prefix = ">> "
                style = "**"
            elif is_completed:
                prefix = "[x] "
                style = ""
            else:
                prefix = "[ ] "
                style = ""

            # Make completed steps clickable
            if is_completed:
                if st.button(
                    f"{prefix}{step_name}",
                    key=f"nav_step_{step_num}",
                    use_container_width=True,
                ):
                    set_current_step(step_num)
                    st.rerun()
            else:
                st.markdown(f"{style}{prefix}{step_name}{style}")

        st.markdown("---")

        # Quick status
        _render_status_summary()

        st.markdown("---")

        # Privacy and help links
        if st.button("Privacy Policy", use_container_width=True):
            st.session_state["show_privacy_page"] = True
            st.rerun()

        if st.session_state.get("show_privacy_page"):
            if st.button("Back to App", use_container_width=True, type="primary"):
                st.session_state["show_privacy_page"] = False
                st.rerun()

        st.markdown("---")

        # Feature requests link
        st.markdown(
            "[Request a Feature](https://github.com/anthropics/claude-code/issues)"
        )

        # Compact privacy notice
        st.markdown("---")
        st.caption(
            "Your data is processed in memory only and never stored. "
            "See Privacy Policy for details."
        )


def _render_status_summary():
    """Render a quick status summary in the sidebar."""
    st.markdown("### Status")

    # File status
    df = st.session_state.get("dataframe")
    if df is not None:
        filename = st.session_state.get("uploaded_file_name", "Unknown")
        # Truncate long filenames
        display_name = filename[:20] + "..." if len(filename) > 20 else filename
        st.markdown(f"**File:** {display_name}")
        st.markdown(f"**Rows:** {len(df):,}")
        st.markdown(f"**Columns:** {len(df.columns)}")
    else:
        st.markdown("*No file loaded*")

    # Contract status
    contract = st.session_state.get("contract")
    if contract:
        source = st.session_state.get("contract_source", "unknown")
        st.markdown(f"**Contract:** {source}")
    else:
        st.markdown("*No contract*")

    # Validation status
    validation = st.session_state.get("validation_results")
    if validation:
        if validation.is_valid:
            st.markdown("**Validation:** Passed")
        else:
            errors = validation.summary.total_errors
            st.markdown(f"**Validation:** {errors} errors")
    else:
        st.markdown("*Not validated*")

    # Remediation status
    if st.session_state.get("remediation_approved"):
        st.markdown("**Remediation:** Applied")


if __name__ == "__main__":
    main()
