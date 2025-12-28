"""
Data Doctor Brand Theme.

Centralized branding constants for colors, typography, and styling.
Based on brandingrequirements.md specifications.
"""

# =============================================================================
# BRAND COLORS
# =============================================================================

# Primary Colors
BRAND_GREEN = "#2F855A"      # Primary - success, healthy, passed checks
BRAND_SLATE = "#2D3748"      # Primary - text, headings, structure

# Secondary & Support Colors
BRAND_GRAY_BG = "#EDF2F7"    # Secondary - backgrounds, cards, dividers
BRAND_AMBER = "#D69E2E"      # Warnings - needs attention
BRAND_RED = "#C53030"        # Errors - issues requiring action

# Neutral Colors
BRAND_WHITE = "#FFFFFF"      # Main backgrounds
BRAND_LIGHT_GRAY = "#F7FAFC" # Alternate table rows, subtle separation

# =============================================================================
# TYPOGRAPHY
# =============================================================================

FONT_PRIMARY = "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_MONO = "JetBrains Mono, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

# =============================================================================
# BRANDING
# =============================================================================

APP_TAGLINE = "Spreadsheet diagnostics you can trust."

# =============================================================================
# CSS INJECTION
# =============================================================================


def get_custom_css() -> str:
    """
    Get custom CSS for font and styling injection.

    Returns:
        CSS string to inject via st.markdown
    """
    return f"""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* Apply Inter to main UI */
        html, body, [class*="css"] {{
            font-family: {FONT_PRIMARY};
        }}

        /* Apply monospace font to code blocks */
        code, pre, .stCode {{
            font-family: {FONT_MONO};
        }}

        /* Sidebar title styling */
        [data-testid="stSidebarHeader"] {{
            padding-bottom: 0;
        }}

        /* Main header styling */
        .main-header {{
            color: {BRAND_SLATE};
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}

        /* Tagline styling */
        .tagline {{
            color: {BRAND_GREEN};
            font-size: 0.9rem;
            font-style: italic;
            margin-bottom: 1rem;
        }}

        /* Status badge base */
        .status-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .status-pass {{
            background-color: {BRAND_GREEN};
            color: white;
        }}

        .status-fail {{
            background-color: {BRAND_RED};
            color: white;
        }}

        .status-warning {{
            background-color: {BRAND_AMBER};
            color: white;
        }}

        /* Metric styling */
        [data-testid="stMetricValue"] {{
            color: {BRAND_SLATE};
        }}
    </style>
    """


def get_status_badge_html(status: str, text: str = None) -> str:
    """
    Get HTML for a styled status badge.

    Args:
        status: One of "pass", "fail", "warning"
        text: Optional custom text (defaults to status)

    Returns:
        HTML string for the badge
    """
    display_text = text or status.upper()
    status_lower = status.lower()

    if status_lower == "pass":
        bg_color = BRAND_GREEN
    elif status_lower == "fail":
        bg_color = BRAND_RED
    elif status_lower == "warning":
        bg_color = BRAND_AMBER
    else:
        bg_color = BRAND_SLATE

    return (
        f'<span style="background-color: {bg_color}; color: white; '
        f'padding: 2px 10px; border-radius: 4px; font-size: 0.85em; '
        f'font-weight: 600;">{display_text}</span>'
    )
