"""
Dataset summary statistics.

This module provides functions to generate summary statistics
for datasets as specified in Section 9 of the acceptance criteria.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass
class ColumnSummary:
    """Summary statistics for a single column."""

    name: str
    pandas_dtype: str
    inferred_type: str
    total_values: int
    null_count: int
    null_percent: float
    unique_count: int
    cardinality_percent: float
    min_value: Optional[Any]
    max_value: Optional[Any]
    sample_values: list[Any]
    warnings: list[str]


@dataclass
class DatasetSummary:
    """Summary statistics for a dataset."""

    row_count: int
    column_count: int
    total_cells: int
    total_null_count: int
    null_percent: float
    duplicate_row_count: int
    memory_usage_bytes: int
    memory_usage_display: str
    column_summaries: list[ColumnSummary]


def compute_dataset_summary(df: pd.DataFrame) -> DatasetSummary:
    """
    Compute summary statistics for a dataset.

    Args:
        df: The DataFrame to summarize

    Returns:
        DatasetSummary with statistics
    """
    row_count = len(df)
    column_count = len(df.columns)
    total_cells = row_count * column_count

    # Total null count
    total_null_count = int(df.isnull().sum().sum())
    null_percent = (total_null_count / total_cells * 100) if total_cells > 0 else 0

    # Duplicate rows
    duplicate_row_count = int(df.duplicated().sum())

    # Memory usage
    memory_bytes = int(df.memory_usage(deep=True).sum())
    memory_display = _format_bytes(memory_bytes)

    # Column summaries
    column_summaries = []
    for col in df.columns:
        col_summary = _compute_column_summary(df[col], str(col))
        column_summaries.append(col_summary)

    return DatasetSummary(
        row_count=row_count,
        column_count=column_count,
        total_cells=total_cells,
        total_null_count=total_null_count,
        null_percent=round(null_percent, 2),
        duplicate_row_count=duplicate_row_count,
        memory_usage_bytes=memory_bytes,
        memory_usage_display=memory_display,
        column_summaries=column_summaries,
    )


def _compute_column_summary(series: pd.Series, name: str) -> ColumnSummary:
    """
    Compute summary statistics for a single column.

    Args:
        series: The column data
        name: Column name

    Returns:
        ColumnSummary
    """
    total_values = len(series)
    null_count = int(series.isnull().sum())
    null_percent = (null_count / total_values * 100) if total_values > 0 else 0

    # Unique values (excluding nulls)
    unique_count = int(series.nunique(dropna=True))
    non_null_count = total_values - null_count
    cardinality_percent = (
        (unique_count / non_null_count * 100) if non_null_count > 0 else 0
    )

    # Infer type
    inferred_type = _infer_column_type(series)

    # Min/max (for sortable types)
    min_value = None
    max_value = None
    try:
        non_null = series.dropna()
        if len(non_null) > 0:
            min_value = non_null.min()
            max_value = non_null.max()
    except Exception:
        pass

    # Sample values
    sample_values = list(series.dropna().head(5).unique())

    # Generate warnings
    warnings = _generate_column_warnings(
        name, null_percent, unique_count, non_null_count, cardinality_percent
    )

    return ColumnSummary(
        name=name,
        pandas_dtype=str(series.dtype),
        inferred_type=inferred_type,
        total_values=total_values,
        null_count=null_count,
        null_percent=round(null_percent, 2),
        unique_count=unique_count,
        cardinality_percent=round(cardinality_percent, 2),
        min_value=min_value,
        max_value=max_value,
        sample_values=sample_values,
        warnings=warnings,
    )


def _infer_column_type(series: pd.Series) -> str:
    """Infer the semantic type of a column."""
    dtype_str = str(series.dtype)

    if "int" in dtype_str:
        return "integer"
    elif "float" in dtype_str:
        return "float"
    elif "bool" in dtype_str:
        return "boolean"
    elif "datetime" in dtype_str:
        return "datetime"

    # For object dtype, sample values
    if series.dtype == object:
        non_null = series.dropna()
        if len(non_null) == 0:
            return "unknown"

        sample = non_null.head(100)

        # Check for boolean-like
        bool_tokens = {"true", "false", "yes", "no", "1", "0", "t", "f", "y", "n"}
        if all(str(v).lower().strip() in bool_tokens for v in sample):
            return "boolean"

        # Check for numeric
        try:
            pd.to_numeric(sample)
            return "numeric"
        except Exception:
            pass

        # Check for dates
        try:
            pd.to_datetime(sample, errors="raise")
            return "date/datetime"
        except Exception:
            pass

    return "string"


def _generate_column_warnings(
    name: str,
    null_percent: float,
    unique_count: int,
    non_null_count: int,
    cardinality_percent: float,
) -> list[str]:
    """Generate warnings for a column based on its statistics."""
    warnings = []

    # High null percentage
    if null_percent > 50:
        warnings.append(f"High null rate ({null_percent:.1f}%)")
    elif null_percent > 20:
        warnings.append(f"Moderate null rate ({null_percent:.1f}%)")

    # Cardinality warnings
    if non_null_count > 10:
        if cardinality_percent > 95 and unique_count > 100:
            warnings.append(
                "Very high cardinality - may be ID or free text"
            )
        elif cardinality_percent < 1 and unique_count < 5:
            warnings.append(
                "Very low cardinality - consider as categorical"
            )

    # Single value
    if unique_count == 1 and non_null_count > 0:
        warnings.append("Contains only one unique value")

    return warnings


def _format_bytes(bytes_count: int) -> str:
    """Format bytes count to human-readable string."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.1f} GB"


def get_column_health_indicators(
    summary: DatasetSummary,
) -> dict[str, str]:
    """
    Get health indicators for each column.

    Args:
        summary: The dataset summary

    Returns:
        Dict mapping column name to health status (good/warning/critical)
    """
    indicators = {}

    for col in summary.column_summaries:
        if col.null_percent > 50 or len(col.warnings) >= 2:
            indicators[col.name] = "critical"
        elif col.null_percent > 20 or len(col.warnings) >= 1:
            indicators[col.name] = "warning"
        else:
            indicators[col.name] = "good"

    return indicators


def summary_to_dict(summary: DatasetSummary) -> dict:
    """
    Convert a DatasetSummary to a dictionary for JSON/report use.

    Args:
        summary: The dataset summary

    Returns:
        Dictionary representation
    """
    return {
        "row_count": summary.row_count,
        "column_count": summary.column_count,
        "total_cells": summary.total_cells,
        "total_null_count": summary.total_null_count,
        "null_percent": summary.null_percent,
        "duplicate_row_count": summary.duplicate_row_count,
        "memory_usage": summary.memory_usage_display,
        "columns": [
            {
                "name": col.name,
                "dtype": col.pandas_dtype,
                "inferred_type": col.inferred_type,
                "null_count": col.null_count,
                "null_percent": col.null_percent,
                "unique_count": col.unique_count,
                "cardinality_percent": col.cardinality_percent,
                "warnings": col.warnings,
            }
            for col in summary.column_summaries
        ],
    }


def generate_dataset_summary(df: pd.DataFrame) -> dict:
    """
    Generate a dataset summary dictionary for UI display.

    Args:
        df: The DataFrame to summarize

    Returns:
        Dictionary with summary statistics
    """
    row_count = len(df)
    column_count = len(df.columns)
    total_cells = row_count * column_count

    # Memory usage
    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = memory_bytes / (1024 * 1024)

    # Total null count and completeness
    total_null = int(df.isnull().sum().sum())
    overall_completeness = ((total_cells - total_null) / total_cells * 100) if total_cells > 0 else 100

    # Per-column info
    columns = {}
    for col in df.columns:
        series = df[col]
        non_null = int(series.notna().sum())
        null_count = int(series.isnull().sum())
        unique_count = int(series.nunique(dropna=True))
        completeness = (non_null / row_count * 100) if row_count > 0 else 100

        columns[col] = {
            "dtype": str(series.dtype),
            "non_null_count": non_null,
            "null_count": null_count,
            "unique_count": unique_count,
            "completeness": completeness,
        }

    return {
        "row_count": row_count,
        "column_count": column_count,
        "memory_mb": memory_mb,
        "overall_completeness": overall_completeness,
        "columns": columns,
    }
