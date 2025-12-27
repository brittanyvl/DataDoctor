"""
Application constants and configuration values.

This module defines all hard-coded limits, version information, and
configuration constants used throughout the Data Doctor application.
"""

# Application metadata
APP_NAME = "Data Doctor"
APP_VERSION = "0.1.0"
CONTRACT_VERSION = "1.0"

# File size and content limits (Section 5 of acceptance criteria)
MAX_UPLOAD_SIZE_MB = 75
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
MAX_ROW_COUNT = 250_000
MAX_COLUMN_COUNT = 100

# Rate limiting
MAX_UPLOADS_PER_MINUTE = 5

# Supported file extensions
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".xlsb"}

# MIME types for file validation
MIME_TYPES = {
    ".csv": ["text/csv", "text/plain", "application/csv"],
    ".xlsx": [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ],
    ".xls": ["application/vnd.ms-excel"],
    ".xlsb": ["application/vnd.ms-excel.sheet.binary.macroEnabled.12"],
}

# CSV encoding fallback order (Section 23.7)
CSV_ENCODING_DEFAULT = "utf-8"
CSV_ENCODING_FALLBACKS = ["utf-8-sig", "latin-1"]
CSV_ENCODING_OPTIONS = ["utf-8", "utf-8-sig", "latin-1"]

# Supported data types (Section 21.1.1)
DATA_TYPES = ["string", "boolean", "integer", "float", "date", "timestamp"]

# Failure handling actions (Section 21.1.1)
FAILURE_ACTIONS = [
    "strict_fail",
    "set_null",
    "label_failure",
    "quarantine_row",
    "drop_row",
]

# Regex pattern tiers (Section 21.1.1)
REGEX_TIERS = ["preset", "builder", "advanced"]

# Test severity levels
SEVERITY_LEVELS = ["error", "warning"]

# Boolean recognition tokens (Section 23.6)
BOOLEAN_TRUE_TOKENS = {"true", "yes", "1", "t", "y", "on"}
BOOLEAN_FALSE_TOKENS = {"false", "no", "0", "f", "n", "off"}

# Default null tokens
DEFAULT_NULL_TOKENS = ["", "NA", "N/A", "null", "None", "NULL", "none"]

# Outlier detection defaults (Section 23.5)
OUTLIER_IQR_MULTIPLIER_DEFAULT = 1.5
OUTLIER_ZSCORE_THRESHOLD_DEFAULT = 3.0

# Error label column names (Section 23.4)
ERROR_COLUMN_NAME = "__data_doctor_errors__"
ERROR_COUNT_COLUMN_NAME = "__data_doctor_error_count__"
STATUS_COLUMN_NAME = "__data_doctor_status__"

# Status values
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"

# Formula injection prevention - characters that trigger escaping in exports
FORMULA_INJECTION_CHARS = ("=", "+", "-", "@")

# Column-level test types (Section 21.3.3)
COLUMN_TEST_TYPES = [
    "not_null",
    "type_conformance",
    "range",
    "length",
    "enum",
    "uniqueness",
    "monotonic",
    "cardinality_warning",
    "pattern",
    "date_rule",
    "date_window",
]

# Dataset-level test types (Section 21.4)
DATASET_TEST_TYPES = [
    "duplicate_rows",
    "primary_key_completeness",
    "primary_key_uniqueness",
    "composite_key_uniqueness",
    "cross_field_rule",
    "outliers_iqr",
    "outliers_zscore",
]

# Remediation types (Section 21.3.4)
REMEDIATION_TYPES = [
    "trim_whitespace",
    "standardize_nulls",
    "normalize_case",
    "remove_non_printable",
    "deduplicate_rows",
    "numeric_cleanup",
    "boolean_normalization",
    "date_coerce",
    "categorical_standardize",
    "split_column",
    "custom_calculation",
]

# Case normalization options
CASE_OPTIONS = ["none", "lower", "upper", "title"]

# Cross-field comparison operators (Section 23.3)
COMPARISON_OPERATORS = ["<", "<=", ">", ">=", "==", "!="]

# UI step definitions (4-step workflow)
UI_STEPS = [
    {"number": 1, "name": "Upload", "description": "Upload dataset and configure columns"},
    {"number": 2, "name": "Contract", "description": "Define schema, tests, and remediation"},
    {"number": 3, "name": "Results", "description": "Review validation results"},
    {"number": 4, "name": "Export", "description": "Export artifacts"},
]
