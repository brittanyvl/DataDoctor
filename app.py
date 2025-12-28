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

from src.constants import APP_NAME, APP_VERSION, APP_TAGLINE, UI_STEPS
from src.session import initialize_session_state, get_current_step, set_current_step, consume_step_change
from src.ui.components import progress_indicator, scroll_to_top_after_render
from src.ui.theme import get_custom_css
from src.ui.privacy import render_privacy_page
from src.ui.step_upload import render_step_upload
from src.ui.step_contract import render_step_contract
from src.ui.step_cleaning import render_step_cleaning
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

    # Inject custom CSS for branding (fonts, colors)
    st.markdown(get_custom_css(), unsafe_allow_html=True)

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

    # Render page header with branding (green title, coal tagline)
    # Using inline styles to guarantee they override Streamlit defaults
    st.markdown(
        f'<h1 style="color: #2F855A; font-size: 2.25rem; font-weight: 700; '
        f'margin: 0 0 0.25rem 0; padding: 0; line-height: 1.1;">Data Doctor</h1>'
        f'<p style="color: #2D3748; font-size: 1rem; font-style: italic; '
        f'margin: 0 0 1rem 0; padding: 0;">{APP_TAGLINE}</p>',
        unsafe_allow_html=True,
    )

    # Render progress indicator
    progress_indicator(current_step, total_steps=5)

    # Render current step (5-step workflow)
    if current_step == 1:
        render_step_upload()
    elif current_step == 2:
        render_step_contract()
    elif current_step == 3:
        render_step_cleaning()
    elif current_step == 4:
        render_step_results()
    elif current_step == 5:
        render_step_export()
    else:
        st.error(f"Unknown step: {current_step}")
        set_current_step(1)
        st.rerun()

    # Scroll to top AFTER all content has rendered, but only when step changed
    # This is placed at the END so it executes after Streamlit finishes rendering
    if consume_step_change():
        scroll_to_top_after_render()


def _render_sidebar():
    """Render the application sidebar."""
    # Number emojis for steps
    STEP_NUMBERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    with st.sidebar:
        # Branding header (green title, coal tagline) - compact with inline styles
        # Using div wrapper to ensure styles apply
        st.markdown(
            f'<div style="margin-bottom: 0.75rem;">'
            f'<span style="color: #2F855A; font-size: 1.25rem; font-weight: 700; '
            f'display: block; line-height: 1.2;">{APP_NAME}</span>'
            f'<span style="color: #2D3748; font-size: 0.8rem; font-style: italic; '
            f'display: block; margin-top: 0.15rem;">{APP_TAGLINE}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Clear Session button
        if st.button("🗑️ Clear Session", use_container_width=True, help="Clear all data and start fresh"):
            from src.session import reset_session_state
            reset_session_state()
            st.balloons()
            st.rerun()

        # Compact divider with less top margin
        st.markdown('<hr style="margin: 0.25rem 0 0.5rem 0;">', unsafe_allow_html=True)

        # Step navigation with number emojis
        st.markdown("### Workflow")

        current_step = get_current_step()

        for step in UI_STEPS:
            step_num = step["number"]
            step_name = step["name"]
            step_emoji = STEP_NUMBERS[step_num - 1] if step_num <= len(STEP_NUMBERS) else str(step_num)

            # Determine if step is accessible
            is_current = step_num == current_step
            is_completed = step_num < current_step

            if is_current:
                # Current step - highlighted with green accent
                st.markdown(
                    f'<div style="background-color: #C6F6D5; padding: 8px 12px; '
                    f'border-radius: 6px; border-left: 4px solid #2F855A; margin: 4px 0;">'
                    f'<span style="font-weight: 600; color: #22543D;">'
                    f'{step_emoji} {step_name}</span></div>',
                    unsafe_allow_html=True,
                )
            elif is_completed:
                # Completed step - clickable with checkmark
                if st.button(
                    f"✓ {step_emoji} {step_name}",
                    key=f"nav_step_{step_num}",
                    use_container_width=True,
                ):
                    set_current_step(step_num)
                    st.rerun()
            else:
                # Future step - muted
                st.markdown(
                    f'<div style="padding: 8px 12px; color: #A0AEC0; margin: 4px 0;">'
                    f'{step_emoji} {step_name}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Quick status
        _render_status_summary()

        st.markdown("---")

        # Feature requests link
        st.markdown(
            '<a href="https://github.com/brittanyvl/DataDoctor/issues" target="_blank" '
            'style="color: #2F855A;">Request a Feature</a>',
            unsafe_allow_html=True,
        )

        # Privacy section at the bottom
        st.markdown("---")
        st.caption(
            "Your data is processed in memory only and never stored."
        )

        # Privacy policy button
        if st.session_state.get("show_privacy_page"):
            if st.button("← Back to App", use_container_width=True, type="primary"):
                st.session_state["show_privacy_page"] = False
                st.rerun()
        else:
            if st.button("Privacy Policy", use_container_width=True):
                st.session_state["show_privacy_page"] = True
                st.rerun()


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

    # Diagnostics status (rules/contract)
    contract = st.session_state.get("contract")
    if contract:
        source = st.session_state.get("contract_source", "unknown")
        st.markdown(f"**Diagnostics:** {source}")
    else:
        st.markdown("*No Diagnostics Ordered*")

    # Treatment status (validation/cleaning results)
    validation = st.session_state.get("validation_results")
    if validation:
        if validation.is_valid:
            st.markdown("**Findings:** All checks passed")
        else:
            errors = validation.summary.total_errors
            st.markdown(f"**Findings:** {errors} issues found")
    else:
        st.markdown("*No Treatments Ordered*")

    # Data cleansing status
    if st.session_state.get("remediation_approved"):
        st.markdown("**Cleansing:** Applied")


if __name__ == "__main__":
    main()
