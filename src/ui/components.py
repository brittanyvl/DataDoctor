"""
Reusable UI components for the Streamlit application.

This module provides styled components, info tooltips, and other
reusable UI elements used throughout the Data Doctor interface.
"""

from typing import Any, Callable, Optional

import streamlit as st

from src.ui.tooltips import get_tooltip


def info_tooltip(key: str) -> None:
    """
    Display an info icon with a tooltip for a technical term.

    This component renders a small info icon that, when hovered,
    shows a plain-English explanation of the term.

    Args:
        key: The tooltip key from the glossary
    """
    title, explanation, example = get_tooltip(key)

    tooltip_content = explanation
    if example:
        tooltip_content += f"\n\n**Example:** {example}"

    st.markdown(
        f'<span title="{tooltip_content}" style="cursor: help; '
        f'color: #666; font-size: 0.9em;">&#9432; {title}</span>',
        unsafe_allow_html=True,
    )


def labeled_with_tooltip(label: str, tooltip_key: str) -> str:
    """
    Create a label with an inline help tooltip for Streamlit widgets.

    Args:
        label: The visible label text
        tooltip_key: The tooltip key for help text

    Returns:
        The label (tooltip is accessed via help parameter)
    """
    return label


def get_help_text(tooltip_key: str) -> str:
    """
    Get help text for a Streamlit widget's help parameter.

    Args:
        tooltip_key: The tooltip key

    Returns:
        Help text string
    """
    title, explanation, example = get_tooltip(tooltip_key)
    if example:
        return f"{explanation} Example: {example}"
    return explanation


def step_header(step_number: int, title: str, description: str) -> None:
    """
    Display a consistent step header.

    Args:
        step_number: The step number (1-6)
        title: The step title
        description: Brief description of the step
    """
    st.markdown(f"### Step {step_number}: {title}")
    st.markdown(f"*{description}*")
    st.divider()


def error_box(message: str) -> None:
    """
    Display a styled error message box.

    Args:
        message: The error message to display
    """
    st.error(message)


def warning_box(message: str) -> None:
    """
    Display a styled warning message box.

    Args:
        message: The warning message to display
    """
    st.warning(message)


def success_box(message: str) -> None:
    """
    Display a styled success message box.

    Args:
        message: The success message to display
    """
    st.success(message)


def info_box(message: str) -> None:
    """
    Display a styled info message box.

    Args:
        message: The info message to display
    """
    st.info(message)


def metric_card(label: str, value: Any, delta: Optional[str] = None) -> None:
    """
    Display a metric card with optional delta.

    Args:
        label: The metric label
        value: The metric value
        delta: Optional delta text (e.g., "+5" or "-3")
    """
    st.metric(label=label, value=value, delta=delta)


def section_container(title: str) -> Any:
    """
    Create a collapsible section container.

    Args:
        title: The section title

    Returns:
        Streamlit expander context manager
    """
    return st.expander(title, expanded=True)


def collapsible_section(title: str, expanded: bool = False) -> Any:
    """
    Create a collapsible section that starts collapsed by default.

    Args:
        title: The section title
        expanded: Whether to start expanded

    Returns:
        Streamlit expander context manager
    """
    return st.expander(title, expanded=expanded)


def navigation_buttons(
    show_back: bool = True,
    show_next: bool = True,
    back_label: str = "Back",
    next_label: str = "Next",
    on_back: Optional[Callable] = None,
    on_next: Optional[Callable] = None,
    next_disabled: bool = False,
) -> tuple[bool, bool]:
    """
    Display navigation buttons for step-based flow.

    Args:
        show_back: Whether to show the back button
        show_next: Whether to show the next button
        back_label: Label for back button
        next_label: Label for next button
        on_back: Callback when back is clicked
        on_next: Callback when next is clicked
        next_disabled: Whether the next button is disabled

    Returns:
        Tuple of (back_clicked, next_clicked)
    """
    back_clicked = False
    next_clicked = False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if show_back:
            if st.button(back_label, use_container_width=True):
                back_clicked = True
                if on_back:
                    on_back()

    with col3:
        if show_next:
            if st.button(
                next_label,
                use_container_width=True,
                disabled=next_disabled,
                type="primary",
            ):
                next_clicked = True
                if on_next:
                    on_next()

    return back_clicked, next_clicked


def progress_indicator(current_step: int, total_steps: int = 6) -> None:
    """
    Display a progress indicator showing current position in workflow.

    Args:
        current_step: Current step number (1-based)
        total_steps: Total number of steps
    """
    progress = current_step / total_steps
    st.progress(progress, text=f"Step {current_step} of {total_steps}")


def file_size_display(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def data_preview(
    dataframe: Any,
    max_rows: int = 10,
    title: str = "Data Preview",
) -> None:
    """
    Display a preview of a dataframe.

    Args:
        dataframe: Pandas DataFrame to preview
        max_rows: Maximum rows to show
        title: Title for the preview section
    """
    with st.expander(title, expanded=True):
        st.dataframe(dataframe.head(max_rows), use_container_width=True)
        if len(dataframe) > max_rows:
            st.caption(f"Showing {max_rows} of {len(dataframe)} rows")


def confirm_action(
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
) -> Optional[bool]:
    """
    Display a confirmation dialog.

    Args:
        message: The confirmation message
        confirm_label: Label for confirm button
        cancel_label: Label for cancel button

    Returns:
        True if confirmed, False if cancelled, None if no action yet
    """
    st.warning(message)
    col1, col2 = st.columns(2)

    with col1:
        if st.button(cancel_label, use_container_width=True):
            return False

    with col2:
        if st.button(confirm_label, use_container_width=True, type="primary"):
            return True

    return None


def status_badge(status: str) -> None:
    """
    Display a colored status badge.

    Args:
        status: Status text (e.g., "PASS", "FAIL", "WARNING")
    """
    if status.upper() == "PASS":
        st.markdown(
            '<span style="background-color: #28a745; color: white; '
            'padding: 2px 8px; border-radius: 4px; font-size: 0.85em;">'
            f"{status}</span>",
            unsafe_allow_html=True,
        )
    elif status.upper() == "FAIL":
        st.markdown(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 2px 8px; border-radius: 4px; font-size: 0.85em;">'
            f"{status}</span>",
            unsafe_allow_html=True,
        )
    elif status.upper() == "WARNING":
        st.markdown(
            '<span style="background-color: #ffc107; color: black; '
            'padding: 2px 8px; border-radius: 4px; font-size: 0.85em;">'
            f"{status}</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 2px 8px; border-radius: 4px; font-size: 0.85em;">'
            f"{status}</span>",
            unsafe_allow_html=True,
        )


def two_column_layout() -> tuple[Any, Any]:
    """
    Create a two-column layout.

    Returns:
        Tuple of (left_column, right_column)
    """
    return st.columns(2)


def three_column_layout() -> tuple[Any, Any, Any]:
    """
    Create a three-column layout.

    Returns:
        Tuple of (left_column, middle_column, right_column)
    """
    return st.columns(3)


def sidebar_section(title: str) -> None:
    """
    Create a titled section in the sidebar.

    Args:
        title: Section title
    """
    st.sidebar.markdown(f"### {title}")


def download_button_styled(
    label: str,
    data: Any,
    file_name: str,
    mime_type: str,
    help_text: Optional[str] = None,
) -> bool:
    """
    Create a styled download button.

    Args:
        label: Button label
        data: Data to download
        file_name: Name for the downloaded file
        mime_type: MIME type of the file
        help_text: Optional help text

    Returns:
        True if button was clicked
    """
    return st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime=mime_type,
        help=help_text,
        use_container_width=True,
    )
