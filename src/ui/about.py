"""
About page.

This module implements the About page showcasing the project
and its creator as a portfolio piece.
"""

import streamlit as st

from src.constants import APP_NAME, APP_VERSION


def render_about_page():
    """Render the About page."""
    st.title("About Data Doctor")

    # Hero section
    st.markdown("""
    **Data Doctor** is a portfolio project demonstrating software engineering,
    analytics, product thinking, and stakeholder communication. It showcases how
    real business data quality problems can be solved through a guided, transparent
    workflow that transforms tedious, error-prone data cleaning into an intuitive
    experience.
    """)

    st.markdown(
        '<p style="font-size: 1.1rem; color: #2F855A; font-weight: 600;">'
        'Created by Brittany Justice</p>',
        unsafe_allow_html=True,
    )

    # Connect section (moved to top)
    st.markdown("#### Connect With Me")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            '<a href="https://www.linkedin.com/in/brittanycampos/" target="_blank" '
            'style="color: #2F855A;">LinkedIn</a>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            '<a href="https://github.com/brittanyvl" target="_blank" '
            'style="color: #2F855A;">GitHub</a>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            '<a href="https://datadoctor.streamlit.app/" target="_blank" '
            'style="color: #2F855A;">This Project</a>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # The Problem section
    st.markdown("## The Problem This Solves")

    st.markdown("""
    If you've ever inherited a spreadsheet you didn't create, you know the drill.
    Mismatched columns, random formatting, values that make you tilt your head—and
    somehow it's now your problem to fix before it goes back out into the world.
    You do what I call "spreadsheet triage": check columns, scan for weird formatting,
    verify the totals add up, fix the little things that "probably don't matter" but
    definitely do. It's not hard work—it's just draining. And it has a way of
    devouring your afternoon.

    **Data Doctor is for people whose jobs depend on spreadsheets and who are tired
    of being the human automation layer.** You define what "good data" looks like.
    Data Doctor checks every file against your standards—same rules, applied
    consistently, every time. It cleans what it can, predictably and repeatably,
    so you're not doing one-off manual fixes forever. Instead of saying "this looks
    fine," you can say "this was validated and cleaned"—and you've got the proof.
    """)

    st.markdown("""
    **Business pain points addressed:**

    - **Inconsistent formatting** - Spreadsheets with mixed date formats, inconsistent
      capitalization, and rogue punctuation that break downstream processes

    - **Manual data cleaning** - Tedious, error-prone work that consumes hours of
      analyst time and introduces human error

    - **Technical barriers** - Non-technical users needing data validation without
      writing code or learning complex tools

    - **Lack of visibility** - No clear understanding of what's wrong with data
      and exactly how to fix it
    """)

    st.markdown("---")

    # Skills Demonstrated section
    st.markdown("## Skills Demonstrated")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### Product Skills

        - Identified a real business problem from hands-on experience
        - Designed intuitive 5-step wizard workflow
        - Translated technical data concepts into user-friendly language
        - Created clear feedback loops and guided experiences (Demo Mode)
        - Prioritized user privacy and data safety
        """)

        st.markdown("""
        ### Data Skills

        - Deep understanding of tabular data structures and common issues
        - Comprehensive validation: type checking, patterns, ranges, enums, cross-field rules
        - Built data remediation/cleansing pipeline with configurable transformers
        - Knowledge of real-world data quality problems (nulls, duplicates, format inconsistencies)
        """)

    with col2:
        st.markdown("""
        ### Engineering Skills

        - Built complete application from scratch using Python/Streamlit
        - Full software lifecycle: ideation, requirements, design, build, test, deploy
        - Clean, modular architecture with separation of concerns
        - Proper error handling, edge case management, and user feedback
        - YAML-based contract system for flexible, reusable validation rules
        """)

        st.markdown("""
        ### Communication Skills

        - User-friendly terminology ("Data Check-In", "Order Diagnostics", "Treatments")
        - Contextual help and demo tips for guidance
        - Clear reporting that explains issues in plain language
        - Designed for non-technical users while maintaining power for technical users
        """)

    st.markdown("---")

    # Technical Implementation section
    st.markdown("## Technical Implementation")

    st.markdown("""
    | Component | Technology |
    |-----------|------------|
    | **Backend** | Python 3.11+ |
    | **Frontend** | Streamlit |
    | **Data Processing** | Pandas |
    | **Validation Engine** | Custom YAML-based contract system |
    | **Reporting** | HTML/CSS with Jinja2 templating |
    | **Hosting** | Streamlit Community Cloud |
    """)

    st.markdown("""
    **Key architectural decisions:**

    - **Privacy-first design** - In-memory processing only, no data persistence
    - **Modular transformer system** - Easily extensible remediation actions
    - **Contract-driven validation** - Reusable, shareable data quality rules
    - **Comprehensive reporting** - Detailed HTML reports with actionable insights
    """)

    st.markdown("---")

    # Other Projects section
    st.markdown("## Other Projects")

    # MedSupplyPro
    st.markdown("### MedSupplyPro")
    st.markdown("*Android Inventory Management App*")
    st.markdown("""
    **Problem:** Independent healthcare providers need simple inventory tracking
    without complex enterprise software.

    **Solution:** Offline-first Android app for medical supply cataloging, tracking,
    and reporting.

    **Skills:** Mobile Application Development, Relational Databases, Data Modeling,
    API Development, privacy-first architecture, local data persistence,
    healthcare domain expertise
    """)
    st.markdown(
        '[Demo Site](https://brittanyvl.github.io/MedSupplyProDemo/) | '
        '[GitHub](https://github.com/brittanyvl/MedSupplyProDemo)'
    )

    st.markdown("")

    # SterileCalc
    st.markdown("### SterileCalc")
    st.markdown("*Healthcare Procurement Calculator Toolkit*")
    st.markdown("""
    **Problem:** Healthcare procurement professionals lack accessible tools for
    sterile drug calculations.

    **Solution:** Web-based calculator suite for injection volumes, doses per unit,
    cost per dose, and Beyond Use Date calculations.

    **Skills:** Web development (HTML, CSS, JavaScript), Drug Procurement,
    healthcare compliance, user-centered design, pharmaceutical domain knowledge
    """)
    st.markdown(
        '[Live Site](https://brittanyvl.github.io/SterileCalc/index.html) | '
        '[GitHub](https://github.com/brittanyvl/SterileCalc)'
    )

    st.markdown("")

    # Safer Sourcing
    st.markdown("### Safer Sourcing - California Sterile Compounding License Dashboard")
    st.markdown("""
    **Problem:** Regulatory pharmacy licensing data is difficult to explore and understand.

    **Solution:** Interactive Streamlit dashboard for exploring California Board of
    Pharmacy sterile compounder licenses.

    **Skills:** Data analysis, interactive visualization, Python/Streamlit,
    regulatory data handling, Web Scraping, Business Research,
    Compound Pharmacy Domain Knowledge, Compound Pharmacy Compliance
    """)
    st.markdown(
        '[Live Dashboard](https://sterilecali.streamlit.app) | '
        '[GitHub](https://github.com/brittanyvl/California-Pharmacy-License-Dashboard)'
    )

    st.markdown("---")

    # Footer
    st.caption(f"{APP_NAME} v{APP_VERSION}")
    st.caption("Built with Python, Streamlit, and Pandas")
