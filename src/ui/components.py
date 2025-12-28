"""
Reusable UI components for the Streamlit application.

This module provides styled components, info tooltips, and other
reusable UI elements used throughout the Data Doctor interface.
"""

from typing import Any, Callable, Optional

import streamlit as st

from src.ui.tooltips import get_tooltip
from src.ui.theme import (
    BRAND_GREEN,
    BRAND_RED,
    BRAND_AMBER,
    BRAND_SLATE,
    get_status_badge_html,
)


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
        f'color: {BRAND_SLATE}; font-size: 0.9em;">&#9432; {title}</span>',
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


def scroll_to_top_after_render() -> None:
    """
    Scroll the page to the top AFTER all content has rendered.

    This should be called at the END of the main app render, not the beginning.
    It only triggers after a step navigation (not on every rerun).
    """
    import streamlit.components.v1 as components

    # Use components.html at the END of the page to scroll after render
    components.html(
        """
        <script>
            function scrollToTop() {
                const parent = window.parent;
                const doc = parent.document;

                // Scroll all possible containers
                const containers = [
                    doc.querySelector('[data-testid="stMain"]'),
                    doc.querySelector('section.main'),
                    doc.querySelector('[data-testid="stAppViewContainer"]'),
                    doc.querySelector('[data-testid="stVerticalBlock"]'),
                ];

                containers.forEach(container => {
                    if (container) {
                        container.scrollTop = 0;
                    }
                });

                // Also scroll the parent window
                parent.scrollTo(0, 0);
            }

            // Execute after Streamlit has finished rendering
            // Using requestAnimationFrame ensures we run after the current paint
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    scrollToTop();
                });
            });
        </script>
        """,
        height=0,
        width=0,
    )


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
            # Add left arrow before back label
            if st.button(f"← {back_label}", use_container_width=True):
                back_clicked = True
                if on_back:
                    on_back()

    with col3:
        if show_next:
            # Add right arrow after next label
            if st.button(
                f"{next_label} →",
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
    Display a colored status badge using brand colors.

    Args:
        status: Status text (e.g., "PASS", "FAIL", "WARNING")
    """
    badge_html = get_status_badge_html(status.lower(), status)
    st.markdown(badge_html, unsafe_allow_html=True)


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


def demo_tip(message: str) -> None:
    """
    Display a demo tip info box if in demo mode.

    This component shows helpful tips during the demo walkthrough
    to guide users through the application features.

    Args:
        message: The tip message to display
    """
    if st.session_state.get("is_demo_mode"):
        st.markdown(
            f'<div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; '
            f'padding: 12px 16px; margin: 8px 0; border-radius: 4px;">'
            f'<span style="color: #92400E; font-weight: 600;">Demo Tip:</span> '
            f'<span style="color: #78350F;">{message}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# Demo column explanations - explains why each test is configured for the demo
DEMO_COLUMN_EXPLANATIONS = {
    "order_id": "Each order needs a unique ID. The **Uniqueness** test catches duplicate order IDs that could cause data integrity issues.",
    "customer_name": "Customer name is marked as **Required** to ensure every order is associated with a customer. Missing names would make the data incomplete.",
    "email": "The **Email Pattern** test validates that email addresses follow the standard format (user@domain.com). Invalid emails can't receive order confirmations.",
    "phone": "The **US Phone** pattern validates phone numbers match common US formats like (555) 123-4567 or 555-123-4567. This catches typos and incomplete numbers.",
    "quantity": "The **Range (1-1000)** test ensures order quantities are reasonable. Zero, negative, or extremely large quantities likely indicate data entry errors.",
    "unit_price": "The **Range (0-10000)** test validates prices are positive and within expected bounds. Negative prices or extreme values suggest errors.",
    "discount_pct": "Discount percentages should be between 0-100. The **Remove Punctuation** treatment strips the '%' symbol, and the **Range** test validates the numeric value.",
    "order_date": "The **Expected Date Format (YYYY-MM-DD)** rule ensures dates are in a consistent format. Mixed formats like '01/15/2024' or 'Jan 15, 2024' cause sorting and filtering issues.",
    "ship_date": "Same as order_date, the **Expected Date Format** rule enforces consistency. The **Cross-Field Validation** (at page bottom) also checks that ship_date is on or after order_date.",
    "is_priority": "This boolean column accepts Y/N values. Inconsistent formats like 'true', 'yes', or '1' may need standardization.",
    "status": "The **Approved Values** test ensures status values match your business workflow. Note: 'canceled' (American spelling) will fail because only 'cancelled' (British) is in the approved list.",
    "state_code": "The **US State Preset** validates against all 50 US state codes. Invalid codes like 'XX' or 'UK' are caught automatically.",
}


def demo_column_explanation(column_name: str) -> None:
    """
    Display a blue explanation box for a column in demo mode.

    Shows why certain tests are pre-configured for each column in the demo,
    helping users understand the purpose of each validation rule.

    Args:
        column_name: The name of the column to explain
    """
    if not st.session_state.get("is_demo_mode"):
        return

    explanation = DEMO_COLUMN_EXPLANATIONS.get(column_name)
    if explanation:
        st.markdown(
            f'<div style="background-color: #EBF8FF; border-left: 4px solid #3182CE; '
            f'padding: 12px 16px; margin: 8px 0 16px 0; border-radius: 4px;">'
            f'<span style="color: #2C5282; font-weight: 600;">Why this test?</span> '
            f'<span style="color: #2A4365;">{explanation}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
