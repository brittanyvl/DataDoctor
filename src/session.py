"""
Session state management for the Streamlit application.

This module handles initialization and management of all session state
variables used throughout the Data Doctor application. All data exists
only for the duration of a user session (stateless design).
"""

import hashlib
import time
from typing import Any, Optional

import streamlit as st

from src.constants import MAX_UPLOADS_PER_MINUTE


def initialize_session_state() -> None:
    """
    Initialize all session state variables with default values.

    This function should be called at the start of every page render
    to ensure all required session state keys exist.
    """
    defaults = {
        # Current UI step (1-6)
        "current_step": 1,

        # Upload mode selection
        "upload_mode": None,  # "fresh", "contract", or "demo"

        # Demo mode flag
        "is_demo_mode": False,

        # File upload state
        "uploaded_file": None,
        "uploaded_file_name": None,
        "file_hash": None,

        # Parsed dataset
        "dataframe": None,
        "sheet_name": None,
        "available_sheets": [],

        # Contract state
        "contract": None,
        "contract_hash": None,
        "contract_source": None,  # "uploaded" or "built"

        # Validation state
        "validation_results": None,
        "validation_complete": False,

        # Remediation state
        "remediation_approved": False,
        "remediated_dataframe": None,
        "remediation_diff": None,

        # Rate limiting
        "upload_timestamps": [],

        # Processing flags
        "is_processing": False,

        # Error state
        "last_error": None,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def reset_session_state() -> None:
    """
    Clear all session state and reset to defaults.

    This is called when the user clicks "Clear session now" or
    when starting a completely new analysis.
    """
    keys_to_clear = list(st.session_state.keys())
    for key in keys_to_clear:
        del st.session_state[key]
    initialize_session_state()


def reset_from_step(step: int) -> None:
    """
    Reset session state from a specific step onwards.

    When a user goes back to an earlier step or re-uploads a file,
    downstream state should be cleared.

    Args:
        step: The step number to reset from (inclusive)
    """
    if step <= 1:
        # Reset everything except rate limiting
        upload_timestamps = st.session_state.get("upload_timestamps", [])
        reset_session_state()
        st.session_state["upload_timestamps"] = upload_timestamps
    elif step <= 2:
        # Keep file, reset contract and beyond
        st.session_state["contract"] = None
        st.session_state["contract_hash"] = None
        st.session_state["contract_source"] = None
        st.session_state["validation_results"] = None
        st.session_state["validation_complete"] = False
        st.session_state["remediation_approved"] = False
        st.session_state["remediated_dataframe"] = None
        st.session_state["remediation_diff"] = None
    elif step <= 3:
        # Keep file and contract, reset validation and beyond
        st.session_state["validation_results"] = None
        st.session_state["validation_complete"] = False
        st.session_state["remediation_approved"] = False
        st.session_state["remediated_dataframe"] = None
        st.session_state["remediation_diff"] = None
    elif step <= 4:
        # Keep validation, reset remediation
        st.session_state["remediation_approved"] = False
        st.session_state["remediated_dataframe"] = None
        st.session_state["remediation_diff"] = None


def set_current_step(step: int) -> None:
    """
    Set the current UI step and mark that a navigation occurred.

    Args:
        step: Step number (1-6)
    """
    new_step = max(1, min(6, step))
    old_step = st.session_state.get("current_step", 1)

    # Mark that we're navigating to a different step
    if new_step != old_step:
        st.session_state["_step_changed"] = True

    st.session_state["current_step"] = new_step


def consume_step_change() -> bool:
    """
    Check if a step change occurred and clear the flag.

    Returns:
        True if the step changed since last check
    """
    changed = st.session_state.pop("_step_changed", False)
    return changed


def get_current_step() -> int:
    """
    Get the current UI step.

    Returns:
        Current step number (1-6)
    """
    return st.session_state.get("current_step", 1)


def compute_file_hash(file_content: bytes) -> str:
    """
    Compute SHA256 hash of file content for caching purposes.

    Args:
        file_content: Raw file bytes

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(file_content).hexdigest()


def compute_contract_hash(contract: dict) -> str:
    """
    Compute hash of contract dictionary for caching purposes.

    Args:
        contract: Contract dictionary

    Returns:
        Hexadecimal hash string
    """
    import json
    contract_str = json.dumps(contract, sort_keys=True, default=str)
    return hashlib.sha256(contract_str.encode()).hexdigest()


def check_rate_limit() -> tuple[bool, Optional[int]]:
    """
    Check if the user has exceeded the upload rate limit.

    Returns:
        Tuple of (is_allowed, seconds_until_allowed)
        If is_allowed is True, seconds_until_allowed is None
    """
    current_time = time.time()
    one_minute_ago = current_time - 60

    # Filter to only timestamps within the last minute
    recent_uploads = [
        ts for ts in st.session_state.get("upload_timestamps", [])
        if ts > one_minute_ago
    ]
    st.session_state["upload_timestamps"] = recent_uploads

    if len(recent_uploads) >= MAX_UPLOADS_PER_MINUTE:
        oldest_in_window = min(recent_uploads)
        seconds_until_allowed = int(oldest_in_window + 60 - current_time) + 1
        return False, seconds_until_allowed

    return True, None


def record_upload() -> None:
    """Record a new upload timestamp for rate limiting."""
    if "upload_timestamps" not in st.session_state:
        st.session_state["upload_timestamps"] = []
    st.session_state["upload_timestamps"].append(time.time())


def set_processing(is_processing: bool) -> None:
    """
    Set the processing flag.

    Args:
        is_processing: Whether processing is active
    """
    st.session_state["is_processing"] = is_processing


def is_processing() -> bool:
    """
    Check if processing is active.

    Returns:
        True if processing is in progress
    """
    return st.session_state.get("is_processing", False)


def set_error(error_message: Optional[str]) -> None:
    """
    Set or clear the last error message.

    Args:
        error_message: Error message or None to clear
    """
    st.session_state["last_error"] = error_message


def get_error() -> Optional[str]:
    """
    Get the last error message.

    Returns:
        Error message or None
    """
    return st.session_state.get("last_error")


def clear_error() -> None:
    """Clear the last error message."""
    st.session_state["last_error"] = None


def get_session_value(key: str, default: Any = None) -> Any:
    """
    Safely get a session state value.

    Args:
        key: Session state key
        default: Default value if key doesn't exist

    Returns:
        Session state value or default
    """
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any) -> None:
    """
    Set a session state value.

    Args:
        key: Session state key
        value: Value to set
    """
    st.session_state[key] = value
