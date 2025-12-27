"""
Tooltip content derived from the glossary.

This module provides plain-English explanations for technical terms
used in the Data Doctor UI. All definitions are based on glossary.md.
"""

# Tooltip definitions mapping term keys to (title, explanation, example) tuples
# The example field is optional and may be None

TOOLTIPS = {
    "cardinality": (
        "Cardinality",
        "The number of distinct (unique) values in a column. Low cardinality "
        "columns are often categories (e.g., status, state). Very high "
        "cardinality may indicate IDs, free text, or messy data.",
        'A column with values ["TX", "CA", "TX", "NY"] has a cardinality of 3.',
    ),
    "coerce": (
        "Coerce",
        "To convert values into the expected type or format when possible. "
        "Coercion allows the system to fix common issues instead of failing "
        "immediately.",
        '"1,200" can be coerced to 1200; "01/07/2025" can be coerced to 2025-01-07.',
    ),
    "composite_key": (
        "Composite Key",
        "A key made up of multiple columns together that uniquely identify a row. "
        "Sometimes no single column is unique, but a combination is.",
        "order_id + line_number together form a composite key.",
    ),
    "date_format": (
        "Date Format",
        "The specific way a date is written. Dates like 01/07/25 can be ambiguous. "
        "Data Doctor requires you to explicitly state the expected format.",
        "YYYY-MM-DD means 2025-01-07; MM/DD/YYYY means 01/07/2025.",
    ),
    "excel_serial_date": (
        "Excel Serial Date",
        "A numeric value Excel uses internally to represent dates. Dates may "
        "appear as numbers instead of readable dates.",
        "45321 represents 2024-01-01 in Excel's date system.",
    ),
    "enum": (
        "Enumerated Values",
        "A fixed list of allowed values for a column. Ensures consistency and "
        "prevents unexpected or misspelled values.",
        'Allowed values: ["TX", "CA", "NY"]',
    ),
    "failure_handling": (
        "Failure Handling",
        "What Data Doctor should do when a rule or test fails. Options include: "
        "Strict fail (stop processing), Set null (replace with empty), "
        "Label failure (mark the row), Quarantine row (separate output), "
        "or Drop row (remove entirely).",
        None,
    ),
    "foreign_key": (
        "Foreign Key (FK)",
        "A value in one dataset that must exist in another dataset. Ensures "
        "references are valid.",
        "orders.customer_id must exist in customers.customer_id",
    ),
    "monotonic": (
        "Monotonic",
        "Values always increase (or stay the same) as you move down the column. "
        "Useful for timestamps, sequence numbers, or IDs that should never go backwards.",
        "[1, 2, 3, 4, 4, 5] is monotonic; [1, 3, 2] is not monotonic.",
    ),
    "null": (
        "Null",
        "A missing or empty value. Nulls can break calculations, joins, and "
        "reporting if not handled intentionally.",
        'Common null tokens: "", "NA", "N/A", "null", "None"',
    ),
    "outlier": (
        "Outlier",
        "A value that is unusually large or small compared to the rest of the data. "
        "Outliers may indicate errors, data entry issues, or rare but valid cases. "
        "Common detection methods include IQR and Z-score.",
        None,
    ),
    "pattern_validation": (
        "Pattern Validation",
        "Checking that values follow a specific structure. Ensures consistency "
        "for IDs, ZIP codes, emails, and other formatted data.",
        "ZIP code must be exactly 5 digits; UUID must match a specific format.",
    ),
    "primary_key": (
        "Primary Key",
        "A column (or columns) that uniquely identifies each row. Primary keys "
        "prevent duplicate records and enable reliable joins.",
        "order_id is typically a primary key.",
    ),
    "quarantine": (
        "Quarantine",
        "Removing problematic rows from the main dataset and placing them in a "
        "separate output. Allows you to keep clean data while still reviewing "
        "what failed.",
        None,
    ),
    "referential_integrity": (
        "Referential Integrity",
        "Ensuring relationships between datasets remain valid. Prevents orphaned "
        "records.",
        "An order should not reference a customer that does not exist.",
    ),
    "strict_fail": (
        "Strict Fail",
        "Stop processing immediately when a rule fails. Useful when data must "
        "be perfect before use.",
        None,
    ),
    "timestamp": (
        "Timestamp",
        "A date and time, optionally including timezone information.",
        "2025-01-07 14:32:10 or 2025-01-07T14:32:10Z",
    ),
    "type_conformance": (
        "Type Conformance",
        "Checking whether values match the declared data type. Prevents mixing "
        "numbers, text, and dates in the same column.",
        'A numeric column containing "abc" fails type conformance.',
    ),
    "uniqueness": (
        "Uniqueness",
        "Ensuring values in a column do not repeat. Often required for IDs and keys.",
        "[1, 2, 3] is unique; [1, 2, 2] is not unique.",
    ),
    "uuid": (
        "UUID",
        "Universally Unique Identifier. A standardized format for IDs that "
        "should never repeat across systems.",
        "550e8400-e29b-41d4-a716-446655440000",
    ),
    "yaml_contract": (
        "YAML Contract",
        "A human-readable configuration file that defines schema, rules, tests, "
        "and remediation behavior. Allows you to re-run the same validation "
        "logic consistently without storing data.",
        None,
    ),
    "z_score": (
        "Z-Score",
        "A statistical measure of how far a value is from the average, expressed "
        "in terms of standard deviations. Used to flag potential outliers.",
        "A Z-score of 3 means the value is 3 standard deviations from the mean.",
    ),
    "iqr": (
        "IQR (Interquartile Range)",
        "A measure of statistical dispersion: the difference between the 75th "
        "and 25th percentiles. Values beyond 1.5x IQR from the quartiles are "
        "often considered outliers.",
        None,
    ),
    "normalization": (
        "Normalization",
        "Preprocessing applied to values before testing. Common normalizations "
        "include trimming whitespace, converting case, and standardizing null tokens.",
        '"  TX  " normalized becomes "TX"',
    ),
    "remediation": (
        "Remediation",
        "The process of automatically fixing data issues according to defined rules. "
        "Changes are always applied to a copy, never the original.",
        None,
    ),
    "data_type": (
        "Data Type",
        "The kind of value a column contains: string (text), boolean (true/false), "
        "integer (whole number), float (decimal number), date, or timestamp.",
        None,
    ),
}


def get_tooltip(key: str) -> tuple[str, str, str | None]:
    """
    Get tooltip content for a term.

    Args:
        key: The tooltip key (e.g., "cardinality", "uuid")

    Returns:
        Tuple of (title, explanation, example) where example may be None
    """
    return TOOLTIPS.get(key, (key.replace("_", " ").title(), "No description available.", None))


def get_tooltip_text(key: str) -> str:
    """
    Get a simple text tooltip suitable for Streamlit help parameter.

    Args:
        key: The tooltip key

    Returns:
        Combined explanation and example text
    """
    title, explanation, example = get_tooltip(key)
    if example:
        return f"{explanation} Example: {example}"
    return explanation


def get_all_tooltip_keys() -> list[str]:
    """
    Get all available tooltip keys.

    Returns:
        List of tooltip keys
    """
    return list(TOOLTIPS.keys())
