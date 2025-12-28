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

    # Hosting provider notice
    st.info(
        "This application is hosted on **Streamlit Community Cloud**, which is owned by "
        "**Snowflake Inc.** For information about how Snowflake handles data, please review their "
        "[Privacy Policy](https://www.snowflake.com/en/legal/privacy/privacy-policy/)."
    )

    st.markdown(f"""
    ## {APP_NAME} Privacy Policy

    **Last updated:** December 2025

    ### Our Commitment

    {APP_NAME} is designed with privacy as a core principle. We believe your data
    belongs to you, and we have built this application to ensure it stays that way.

    ---

    ### Hosting Platform

    This application is hosted on **Streamlit Community Cloud**, a service owned and
    operated by **Snowflake Inc.** Your use of this application is subject to:

    - [Snowflake Privacy Notice](https://www.snowflake.com/en/legal/privacy/privacy-policy/)
    - [Streamlit Privacy Policy](https://streamlit.io/privacy-policy)
    - [Streamlit Community Cloud Terms of Use](https://streamlit.io/deployment-terms-of-use)

    The Snowflake Privacy Notice governs how the hosting platform collects, stores,
    uses, and discloses information. We encourage you to review these policies.

    ---

    ### Intended Use

    This application is provided for **personal and non-commercial purposes** such as
    evaluation, educational, or household use, in accordance with Streamlit Community
    Cloud terms of service.

    **Important:** This application is **not intended** for processing:
    - Financial information (bank accounts, credit cards, financial records)
    - Health information (medical records, health data)
    - Biometric information
    - Other sensitive personal information subject to heightened legal or regulatory
      data protection requirements

    If you need to process such data, please use an appropriate enterprise solution.

    ---

    ### How We Handle Your Data

    **No Persistent Storage**

    - Your uploaded files are processed entirely in memory (RAM)
    - No data is written to disk on the hosting servers
    - No data is stored in any database by this application
    - Your data exists only for the duration of your session

    **No Data Sharing by This Application**

    - Your file contents are not shared with third parties by this application
    - Your data is not used for training AI models
    - Your data is not sold or monetized

    **Session-Based Processing**

    - All data is cleared when you close your browser tab
    - All data is cleared when your session times out
    - You can manually clear your data at any time using the button below

    ---

    ### Technical Details

    **Data Processing Flow**

    1. You upload a file through your web browser (HTTPS encrypted)
    2. The file is transferred to the Streamlit Community Cloud server
    3. The file is loaded into memory (RAM) for processing
    4. Validation and remediation are performed in memory
    5. Results are returned to your browser
    6. When you leave or clear your session, all data is removed from memory

    **What This Application Does Not Do**

    - We do not log the contents of your files
    - We do not store file metadata beyond your session
    - We do not run analytics on your file contents

    **Platform Analytics**

    Streamlit Community Cloud may collect usage statistics about application
    performance and usage patterns. This is governed by the Snowflake Privacy Notice.
    This application does not implement additional analytics or tracking.

    **Infrastructure Security**

    Streamlit Community Cloud provides:
    - Secure HTTPS connections
    - Session isolation between users
    - Authentication and access controls

    ---

    ### Your Rights

    You have the right to:

    - Know how your data is processed (this page)
    - Clear your data at any time (button below)
    - Close your session and end processing at any time
    - Use the application without creating an account

    For rights related to data collected by the hosting platform (Snowflake/Streamlit),
    please refer to the [Snowflake Privacy Notice](https://www.snowflake.com/en/legal/privacy/privacy-policy/).

    ---

    ### Contact

    **For questions about this application:**
    - Open an issue on our GitHub repository
    - Message the developer on [LinkedIn](https://www.linkedin.com/in/brittanycampos/)

    **For questions about the hosting platform:**
    Contact Streamlit/Snowflake at streamlitcommunity@snowflake.com

    **To report a security issue:**
    Contact security@snowflake.com

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
