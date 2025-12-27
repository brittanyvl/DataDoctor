"""
Privacy policy page.

This module implements the privacy policy and session control page.
"""

import streamlit as st

from src.constants import APP_NAME, APP_VERSION
from src.session import reset_session_state


def render_privacy_page():
    """Render the privacy policy page."""
    st.title("Privacy & Data Safety")

    st.markdown(f"""
    ## {APP_NAME} Privacy Policy

    **Last updated:** December 2025

    ### Our Commitment

    {APP_NAME} is designed with privacy as a core principle. We believe your data
    belongs to you, and we have built this application to ensure it stays that way.

    ---

    ### Data Handling

    **No Data Storage**

    - Your uploaded files are processed entirely in memory
    - No data is written to disk on our servers
    - No data is stored in any database
    - Your data exists only for the duration of your session

    **No Data Sharing**

    - Your data is never shared with third parties
    - Your data is never used for training AI models
    - Your data is never sold or monetized

    **Session-Based Processing**

    - All data is cleared when you close your browser tab
    - All data is cleared when your session times out
    - You can manually clear your data at any time using the button below

    ---

    ### Technical Details

    **How We Process Your Data**

    1. You upload a file through your web browser
    2. The file is transferred to our Streamlit server
    3. The file is loaded into memory (RAM) for processing
    4. Validation and remediation are performed in memory
    5. Results are returned to your browser
    6. When you leave or clear your session, all data is removed from memory

    **What We Don't Do**

    - We do not log the contents of your files
    - We do not store file metadata beyond your session
    - We do not use cookies to track your data
    - We do not run analytics on your file contents

    **Infrastructure**

    This application runs on Streamlit Community Cloud, which provides:
    - Secure HTTPS connections
    - No persistent storage of user data
    - Session isolation between users

    ---

    ### Your Rights

    You have the right to:

    - Know how your data is processed (this page)
    - Clear your data at any time (button below)
    - Close your session at any time
    - Use the application without creating an account

    ---

    ### Contact

    For privacy-related questions or concerns, please open an issue on our
    [GitHub repository](https://github.com).

    ---

    ### Session Control
    """)

    # Clear session button
    st.warning(
        "Clicking the button below will immediately clear all data from your "
        "current session, including any uploaded files, contracts, and results."
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "Clear Session Now",
            type="primary",
            use_container_width=True,
        ):
            reset_session_state()
            st.success("Session cleared successfully. All data has been removed.")
            st.balloons()

    st.markdown("---")

    # Application info
    st.caption(f"{APP_NAME} v{APP_VERSION}")
    st.caption("Built with Streamlit and Pandas")


def render_privacy_sidebar():
    """Render a condensed privacy notice in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Privacy")
    st.sidebar.markdown("""
    Your data is:
    - Processed in memory only
    - Never stored on disk
    - Never shared with anyone
    - Cleared when you leave
    """)

    if st.sidebar.button("Clear Session", use_container_width=True):
        reset_session_state()
        st.rerun()

    st.sidebar.markdown("[Full Privacy Policy](#)")
