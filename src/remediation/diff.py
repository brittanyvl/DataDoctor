"""
Before/after diff generation for remediation preview.

This module provides functions to generate and display diffs
showing the impact of remediation actions.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass
class CellChange:
    """Represents a change to a single cell."""

    row_index: int
    column_name: str
    original_value: Any
    new_value: Any


@dataclass
class ColumnDiff:
    """Diff summary for a single column."""

    column_name: str
    total_values: int
    changed_count: int
    change_rate_percent: float
    sample_changes: list[CellChange]


@dataclass
class RemediationDiff:
    """Complete diff for a remediation operation."""

    total_rows: int
    total_columns: int
    rows_changed: int
    cells_changed: int
    columns_affected: list[str]
    column_diffs: dict[str, ColumnDiff]
    row_change_summary: dict[int, int]  # row_index -> change_count


def compute_diff(
    original_df: pd.DataFrame,
    remediated_df: pd.DataFrame,
    max_samples_per_column: int = 10,
) -> RemediationDiff:
    """
    Compute the diff between original and remediated DataFrames.

    Args:
        original_df: The original DataFrame
        remediated_df: The remediated DataFrame
        max_samples_per_column: Max sample changes to include per column

    Returns:
        RemediationDiff with change details
    """
    column_diffs: dict[str, ColumnDiff] = {}
    row_changes: dict[int, int] = {}
    total_cells_changed = 0
    columns_affected = []

    # Compare each column
    for col in original_df.columns:
        if col not in remediated_df.columns:
            continue

        orig_col = original_df[col]
        new_col = remediated_df[col]

        # Find changes
        # Handle comparison with nulls
        changed_mask = (
            (orig_col != new_col) |
            (orig_col.isna() & new_col.notna()) |
            (orig_col.notna() & new_col.isna())
        )

        changed_indices = orig_col.index[changed_mask].tolist()
        changed_count = len(changed_indices)

        if changed_count > 0:
            columns_affected.append(col)
            total_cells_changed += changed_count

            # Track row changes
            for idx in changed_indices:
                row_changes[idx] = row_changes.get(idx, 0) + 1

            # Collect sample changes
            sample_changes = []
            for idx in changed_indices[:max_samples_per_column]:
                sample_changes.append(
                    CellChange(
                        row_index=idx,
                        column_name=col,
                        original_value=orig_col.loc[idx],
                        new_value=new_col.loc[idx],
                    )
                )

            change_rate = (changed_count / len(orig_col) * 100) if len(orig_col) > 0 else 0

            column_diffs[col] = ColumnDiff(
                column_name=col,
                total_values=len(orig_col),
                changed_count=changed_count,
                change_rate_percent=round(change_rate, 2),
                sample_changes=sample_changes,
            )

    rows_changed = len(row_changes)

    return RemediationDiff(
        total_rows=len(original_df),
        total_columns=len(original_df.columns),
        rows_changed=rows_changed,
        cells_changed=total_cells_changed,
        columns_affected=columns_affected,
        column_diffs=column_diffs,
        row_change_summary=row_changes,
    )


def format_diff_summary(diff: RemediationDiff) -> str:
    """
    Format a diff summary for display.

    Args:
        diff: The remediation diff

    Returns:
        Formatted summary string
    """
    lines = [
        "Remediation Summary",
        "=" * 40,
        f"Total Rows: {diff.total_rows:,}",
        f"Rows Changed: {diff.rows_changed:,}",
        f"Cells Changed: {diff.cells_changed:,}",
        f"Columns Affected: {len(diff.columns_affected)}",
    ]

    if diff.columns_affected:
        lines.append("")
        lines.append("Changes by Column:")
        for col_name in diff.columns_affected:
            col_diff = diff.column_diffs[col_name]
            lines.append(
                f"  - {col_name}: {col_diff.changed_count:,} changes "
                f"({col_diff.change_rate_percent:.1f}%)"
            )

    return "\n".join(lines)


def get_sample_changes_table(
    diff: RemediationDiff,
    max_rows: int = 20,
) -> pd.DataFrame:
    """
    Get a table of sample changes for display.

    Args:
        diff: The remediation diff
        max_rows: Maximum rows to include

    Returns:
        DataFrame with columns [Row, Column, Original, New]
    """
    rows = []

    for col_name, col_diff in diff.column_diffs.items():
        for change in col_diff.sample_changes:
            if len(rows) >= max_rows:
                break

            rows.append({
                "Row": change.row_index,
                "Column": change.column_name,
                "Original": _format_value(change.original_value),
                "New": _format_value(change.new_value),
            })

        if len(rows) >= max_rows:
            break

    return pd.DataFrame(rows)


def _format_value(value: Any) -> str:
    """Format a value for display in diff."""
    if pd.isna(value):
        return "(null)"
    if value is None:
        return "(null)"
    if value == "":
        return "(empty)"
    return str(value)


def get_change_statistics(diff: RemediationDiff) -> dict:
    """
    Get statistics about the changes.

    Args:
        diff: The remediation diff

    Returns:
        Dictionary with statistics
    """
    change_rate_rows = (
        diff.rows_changed / diff.total_rows * 100
        if diff.total_rows > 0 else 0
    )

    total_cells = diff.total_rows * diff.total_columns
    change_rate_cells = (
        diff.cells_changed / total_cells * 100
        if total_cells > 0 else 0
    )

    return {
        "rows_changed": diff.rows_changed,
        "rows_unchanged": diff.total_rows - diff.rows_changed,
        "row_change_rate_percent": round(change_rate_rows, 2),
        "cells_changed": diff.cells_changed,
        "cell_change_rate_percent": round(change_rate_cells, 2),
        "columns_affected": len(diff.columns_affected),
        "columns_unaffected": diff.total_columns - len(diff.columns_affected),
    }


def get_rows_with_changes(
    original_df: pd.DataFrame,
    remediated_df: pd.DataFrame,
    diff: RemediationDiff,
    max_rows: int = 100,
) -> pd.DataFrame:
    """
    Get a DataFrame showing rows that have changes.

    Args:
        original_df: Original DataFrame
        remediated_df: Remediated DataFrame
        diff: The remediation diff
        max_rows: Maximum rows to return

    Returns:
        DataFrame with changed rows, showing before/after columns
    """
    changed_row_indices = list(diff.row_change_summary.keys())[:max_rows]

    if not changed_row_indices:
        return pd.DataFrame()

    # Build comparison DataFrame
    rows = []
    for idx in changed_row_indices:
        row_data = {"_row_index": idx}

        for col in diff.columns_affected:
            if col in original_df.columns and col in remediated_df.columns:
                orig_val = original_df.loc[idx, col]
                new_val = remediated_df.loc[idx, col]

                # Check if this specific cell changed
                changed = (
                    orig_val != new_val or
                    (pd.isna(orig_val) and pd.notna(new_val)) or
                    (pd.notna(orig_val) and pd.isna(new_val))
                )

                if changed:
                    row_data[f"{col} (before)"] = _format_value(orig_val)
                    row_data[f"{col} (after)"] = _format_value(new_val)

        rows.append(row_data)

    return pd.DataFrame(rows)
