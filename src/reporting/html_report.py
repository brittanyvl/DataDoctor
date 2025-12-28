"""
HTML report generator.

This module generates human-readable HTML data quality reports
as specified in Section 16 of the acceptance criteria.
"""

import os
from datetime import datetime
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.constants import APP_NAME, APP_VERSION
from src.remediation.diff import RemediationDiff
from src.validation.results import ValidationResult


def generate_html_report(
    validation_result: ValidationResult,
    filename: str,
    contract_id: str,
    remediation_diff: Optional[RemediationDiff] = None,
) -> str:
    """
    Generate an HTML data quality report.

    Args:
        validation_result: The validation results
        filename: Original dataset filename
        contract_id: Contract ID
        remediation_diff: Optional remediation diff if remediation was applied

    Returns:
        HTML report as string
    """
    # Get template directory
    template_dir = os.path.join(os.path.dirname(__file__), "templates")

    # Create Jinja environment
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Add custom filters
    env.filters["format_number"] = lambda x: f"{x:,}" if isinstance(x, (int, float)) else x

    # Load template
    template = env.get_template("report.html")

    # Prepare summary data
    summary = validation_result.summary
    summary_data = {
        "total_rows": summary.total_rows,
        "total_columns": summary.total_columns,
        "tests_run": summary.total_tests_run,
        "tests_passed": summary.total_tests_passed,
        "tests_failed": summary.total_tests_failed,
        "warnings": summary.total_warnings,
        "errors": summary.total_errors,
        "rows_with_errors": summary.rows_with_errors,
        "clean_rows": summary.clean_rows,
        "error_rate_percent": summary.error_rate_percent,
        "is_valid": validation_result.is_valid,
    }

    # Prepare ALL failed examples (no limit)
    failed_examples = []
    for cell_error in validation_result.cell_errors:
        failed_examples.append({
            "row_index": cell_error.row_index,
            "column_name": cell_error.column_name,
            "test_type": cell_error.test_type,
            "original_value": _format_value(cell_error.original_value),
            "error_message": cell_error.error_message or "",
        })

    # Prepare data cleansing summary if available
    cleansing_summary = None
    if remediation_diff:
        # Build per-column statistics and changes
        # Logic:
        #   - Under 1000 rows: show ALL changes
        #   - 1000+ rows: cap at 100 changes per column
        column_stats = []
        sample_changes_by_column = {}
        total_rows = remediation_diff.total_rows

        # Determine limit per column based on dataset size
        if total_rows < 1000:
            per_column_limit = None  # No limit - show all
        else:
            per_column_limit = 100  # Cap at 100 per column

        for col_name, col_diff in remediation_diff.column_diffs.items():
            # Get treatments applied to this column
            treatments = col_diff.treatments_applied if col_diff.treatments_applied else []
            treatments_str = ", ".join(treatments) if treatments else "N/A"

            # Filter out null-to-null changes
            real_changes = []
            for change in col_diff.sample_changes:
                if _is_null(change.original_value) and _is_null(change.new_value):
                    continue
                real_changes.append({
                    "row_index": change.row_index,
                    "column_name": change.column_name,
                    "original_value": _format_value(change.original_value),
                    "new_value": _format_value(change.new_value),
                    "treatments": treatments_str,
                })

            # Only include columns with actual changes
            if col_diff.changed_count > 0:
                column_stats.append({
                    "column_name": col_name,
                    "cells_changed": col_diff.changed_count,
                    "treatments": treatments_str,
                })

                # Apply limit based on dataset size
                if real_changes:
                    if per_column_limit is None:
                        # Under 1000 rows: show all changes
                        sample_changes_by_column[col_name] = real_changes
                    else:
                        # 1000+ rows: cap at 100 per column
                        sample_changes_by_column[col_name] = real_changes[:per_column_limit]

        cleansing_summary = {
            "rows_changed": remediation_diff.rows_changed,
            "cells_changed": remediation_diff.cells_changed,
            "column_stats": column_stats,
            "sample_changes_by_column": sample_changes_by_column,
            "has_cached_data_issue": len(sample_changes_by_column) == 0 and remediation_diff.cells_changed > 0,
        }

    # Render template
    html_content = template.render(
        filename=filename,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        contract_id=contract_id,
        app_name=APP_NAME,
        app_version=APP_VERSION,
        summary=summary_data,
        blocking_errors=validation_result.blocking_errors,
        column_results=validation_result.column_results,
        dataset_test_results=validation_result.dataset_test_results,
        fk_check_results=validation_result.fk_check_results,
        failed_examples=failed_examples,
        cleansing_summary=cleansing_summary,
    )

    return html_content


def generate_html_report_bytes(
    validation_result: ValidationResult,
    filename: str,
    contract_id: str,
    remediation_diff: Optional[RemediationDiff] = None,
) -> bytes:
    """
    Generate an HTML report as bytes for download.

    Args:
        validation_result: The validation results
        filename: Original dataset filename
        contract_id: Contract ID
        remediation_diff: Optional remediation diff

    Returns:
        HTML report as bytes
    """
    html_content = generate_html_report(
        validation_result,
        filename,
        contract_id,
        remediation_diff,
    )
    return html_content.encode("utf-8")


def generate_pdf_report(
    validation_result: ValidationResult,
    filename: str,
    contract_id: str,
    remediation_diff: Optional[RemediationDiff] = None,
) -> bytes:
    """
    Generate a PDF data quality report.

    Args:
        validation_result: The validation results
        filename: Original dataset filename
        contract_id: Contract ID
        remediation_diff: Optional remediation diff

    Returns:
        PDF report as bytes
    """
    from io import BytesIO

    try:
        from xhtml2pdf import pisa
    except ImportError:
        raise ImportError("xhtml2pdf is required for PDF generation. Install with: pip install xhtml2pdf")

    # Generate HTML first
    html_content = generate_html_report(
        validation_result,
        filename,
        contract_id,
        remediation_diff,
    )

    # Convert HTML to PDF
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

    if pisa_status.err:
        raise RuntimeError(f"Error generating PDF: {pisa_status.err}")

    pdf_buffer.seek(0)
    return pdf_buffer.read()


def _format_value(value: Any) -> str:
    """Format a value for display in the report."""
    import pandas as pd

    if value is None:
        return "(null)"
    if pd.isna(value):
        return "(null)"
    if value == "":
        return "(empty)"
    return str(value)


def _is_null(value: Any) -> bool:
    """Check if a value is null/None/NaN."""
    import pandas as pd

    if value is None:
        return True
    if pd.isna(value):
        return True
    return False


def generate_standalone_remediation_summary(
    remediation_diff: RemediationDiff,
    filename: str,
) -> str:
    """
    Generate a standalone remediation summary HTML.

    Args:
        remediation_diff: The remediation diff
        filename: Original filename

    Returns:
        HTML string
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Data Cleansing Summary - {filename}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #2D3748; }}
        h1 {{ color: #2D3748; }}
        h1 + p.tagline {{ color: #2F855A; font-style: italic; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #EDF2F7; color: #2D3748; }}
        .summary {{ background-color: #C6F6D5; padding: 15px; border-radius: 6px; margin: 20px 0; border: 1px solid #9AE6B4; }}
        code {{ font-family: 'JetBrains Mono', monospace; }}
    </style>
</head>
<body>
    <h1>Data Cleansing Summary</h1>
    <p class="tagline">Diagnose and treat your spreadsheet ailments.</p>
    <p><strong>File:</strong> {filename}</p>
    <p><strong>Generated:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>

    <div class="summary">
        <p><strong>Total Rows:</strong> {remediation_diff.total_rows:,}</p>
        <p><strong>Rows Changed:</strong> {remediation_diff.rows_changed:,}</p>
        <p><strong>Cells Changed:</strong> {remediation_diff.cells_changed:,}</p>
        <p><strong>Columns Affected:</strong> {len(remediation_diff.columns_affected)}</p>
    </div>

    <h2>Changes by Column</h2>
    <table>
        <thead>
            <tr>
                <th>Column</th>
                <th>Changes</th>
                <th>Change Rate</th>
            </tr>
        </thead>
        <tbody>
"""

    for col_name, col_diff in remediation_diff.column_diffs.items():
        html += f"""            <tr>
                <td>{col_name}</td>
                <td>{col_diff.changed_count:,}</td>
                <td>{col_diff.change_rate_percent:.1f}%</td>
            </tr>
"""

    html += """        </tbody>
    </table>

    <h2>Sample Changes</h2>
    <table>
        <thead>
            <tr>
                <th>Row</th>
                <th>Column</th>
                <th>Original</th>
                <th>New</th>
            </tr>
        </thead>
        <tbody>
"""

    sample_count = 0
    for col_name, col_diff in remediation_diff.column_diffs.items():
        for change in col_diff.sample_changes[:10]:
            if sample_count >= 30:
                break
            orig = _format_value(change.original_value)
            new = _format_value(change.new_value)
            html += f"""            <tr>
                <td>{change.row_index}</td>
                <td>{change.column_name}</td>
                <td>{orig}</td>
                <td>{new}</td>
            </tr>
"""
            sample_count += 1
        if sample_count >= 30:
            break

    html += """        </tbody>
    </table>

    <footer style="margin-top: 30px; color: #666; font-size: 12px; text-align: center;">
        <p>Generated by Data Doctor — Diagnose and treat your spreadsheet ailments.</p>
    </footer>
</body>
</html>
"""

    return html


def generate_remediation_summary_bytes(
    remediation_diff: RemediationDiff,
    filename: str,
) -> bytes:
    """
    Generate remediation summary as bytes for download.

    Args:
        remediation_diff: The remediation diff
        filename: Original filename

    Returns:
        HTML as bytes
    """
    html = generate_standalone_remediation_summary(remediation_diff, filename)
    return html.encode("utf-8")
