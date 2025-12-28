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

        /* AGGRESSIVELY reduce main content top padding */
        .main .block-container,
        .stMainBlockContainer,
        [data-testid="stMainBlockContainer"] {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 100% !important;
        }}

        /* Reduce Streamlit header height but keep toolbar visible */
        .stApp > header,
        [data-testid="stHeader"],
        header[data-testid="stHeader"] {{
            height: auto !important;
            min-height: 0 !important;
            background: transparent !important;
        }}

        /* Keep toolbar visible */
        [data-testid="stDecoration"] {{
            display: none !important;
        }}

        /* Remove top margin/padding from ALL main area containers */
        .stApp,
        [data-testid="stAppViewContainer"],
        .stAppViewContainer {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}

        .main,
        section.main,
        [data-testid="stMain"] {{
            padding-top: 0 !important;
            margin-top: 0 !important;
        }}

        /* Ensure first element has no top margin */
        .main .block-container > div:first-child,
        .stMainBlockContainer > div:first-child {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}

        /* Target the vertical block which often has margin */
        .stVerticalBlock {{
            gap: 0.5rem !important;
        }}

        .stVerticalBlock > div:first-child {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}

        /* Reduce sidebar padding - start content immediately */
        [data-testid="stSidebar"] {{
            padding-top: 0 !important;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 0.5rem !important;
        }}

        [data-testid="stSidebarContent"] {{
            padding-top: 0.25rem !important;
        }}

        [data-testid="stSidebarUserContent"] {{
            padding-top: 0.25rem !important;
        }}

        [data-testid="stSidebarHeader"] {{
            padding-bottom: 0 !important;
            display: none !important;
        }}

        /* Main header styling - Data Doctor in GREEN with !important */
        .dd-header {{
            color: {BRAND_GREEN} !important;
            font-size: 1.75rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
        }}

        /* Tagline styling - in slate/coal */
        .dd-tagline {{
            color: {BRAND_SLATE} !important;
            font-size: 0.95rem !important;
            font-style: italic !important;
            margin: 0.25rem 0 0.75rem 0 !important;
            padding: 0 !important;
        }}

        /* Sidebar header styling - BOLD GREEN */
        .dd-sidebar-header {{
            color: {BRAND_GREEN} !important;
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
        }}

        .dd-sidebar-tagline {{
            color: {BRAND_SLATE} !important;
            font-size: 0.8rem !important;
            font-style: italic !important;
            margin: 0.15rem 0 0 0 !important;
            padding: 0 !important;
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

        /* Reduce spacing after dividers */
        hr {{
            margin: 0.5rem 0;
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
