# Data Doctor  
## Acceptance Criteria & Technical Requirements (v1)

---

## 1. Purpose

Data Doctor is a **stateless, rules-based data quality and remediation application** built with **Streamlit** and **Pandas**.

The application allows users to:
- upload a tabular dataset,
- define or upload a YAML-based data contract,
- validate the dataset against explicit schema and quality rules,
- optionally remediate data issues,
- export a **cleaned dataset**, a **human-readable HTML data quality report**, and an updated **YAML contract**.

The system must be:
- deterministic (no AI / no LLM inference inside the app),
- explainable to non-technical users,
- safe to run on Streamlit Community Cloud,
- and fully ephemeral (no data persistence).

This document defines **what must be built** and **how it must behave**.

---

## 2. Technology Constraints (Hard Requirements)

### 2.1 Frontend
- Framework: **Streamlit**
- UI must be:
  - accessible to Excel power users,
  - organized into clear steps,
  - progressively disclose advanced options.

### 2.2 Backend / Data Processing
- Primary library: **Pandas**
- Excel reading via Pandas-supported engines (e.g. openpyxl, pyxlsb)
- All data processing occurs **in-memory only**

### 2.3 Deployment Environment
- Streamlit Community Cloud (Linux)
- No external databases
- No background workers
- No secrets or API keys required

---

## 3. Core Design Principles

1. **Stateless**
   - No data, contracts, or reports are stored server-side.
   - All artifacts exist only for the duration of a user session.

2. **Rules-Based Only**
   - No AI, LLMs, or probabilistic inference.
   - All validations and transformations are explicit and user-declared.

3. **User-Controlled Contracts**
   - The YAML contract is the source of truth.
   - Users can upload, inspect, override, and re-download contracts.

4. **Explainability**
   - Every test, rule, and remediation must be explainable in plain English.
   - Any non-obvious term must have an info tooltip in the UI.

---

## 4. Inputs

### 4.1 Required Input
- **Dataset file**:
  - Formats: `.csv`, `.xlsx`, `.xls`, `.xlsb`
  - One sheet selected per run (sheet selector required if multiple sheets exist)

### 4.2 Optional Inputs
- **YAML contract file**
- **Foreign Key (FK) list file**:
  - Same supported formats
  - One sheet only
  - One FK column selected

---

## 5. File Size, Row, and Column Limits

### 5.1 Hard Limits (Reject File if Exceeded)
- File size: **75 MB**
- Row count: **250,000 rows**
- Column count: **100 columns**

### 5.2 Behavior
- Files exceeding any hard limit must be rejected **before processing**
- Rejection message must:
  - clearly state the exceeded limit,
  - instruct the user to upload a smaller subset.

### 5.3 Rate Limiting
- Maximum **5 uploads per session per minute**
- Disable run buttons while processing is active

---

## 6. Security & Data Safety

### 6.1 File Safety
- Validate file extension and MIME type
- Do NOT execute macros or formulas
- Read Excel values only
- No dynamic code execution (no `eval`, `exec`, imports)

### 6.2 Resource Protection
- Cache profiling results by `(file_hash, contract_hash)`
- Abort long-running operations gracefully
- Hide internal error stack traces in production UI

### 6.3 Export Safety
- Prevent CSV/Excel formula injection:
  - Escape values beginning with `=`, `+`, `-`, or `@`

---

## 7. YAML Contract (Core Artifact)

### 7.1 Contract Format
- YAML only
- Human-readable
- Fully round-trippable (UI → YAML → UI)
- The YAML contract is designed to be portable: users can save it locally and re-upload it to re-run the same validation.

### 7.2 Contract Responsibilities
The contract defines:
- dataset metadata
- column schema
- column-level tests
- dataset-level tests
- foreign key membership checks (single-column v1 scope)
- failure handling policies
- remediation rules

### 7.3 Contract Lifecycle
- User may:
  - upload a contract to prefill the UI
  - modify any contract element
  - re-download the updated contract
- The system must not persist contracts

---

## 8. User Interface Requirements

### 8.1 Step-Based Flow
The UI must follow a clear progression:
1. Upload dataset
2. Review dataset summary
3. Define or load contract
4. Configure tests and remediation
5. Review results
6. Export artifacts

### 8.2 Terminology Tooltips (Mandatory)
Any term that a non-database user may not know **must include**:
- an info icon
- a hover or click tooltip
- a plain-English explanation
- an example where helpful

Required tooltip terms include (not limited to):
- UUID
- Monotonic
- Cardinality
- Primary Key
- Composite Key
- Referential Integrity
- Quarantine
- Coerce
- Strict Fail
- Outlier (IQR, Z-score)

---

## 9. Dataset Summary & Column Health

### 9.1 Dataset Summary Metrics
- Row count
- Column count
- Duplicate row count
- Null count per column
- Missing required columns
- Cardinality per column

### 9.2 Per-Column Health
- Inferred datatype vs declared datatype
- Percent of values conforming
- Percent invalid
- Top invalid tokens
- Warnings (e.g. high cardinality, sparse data)

---

## 10. Column Setup & Schema Definition

For each column, the user must be able to:
- Accept or rename the column
- Explicitly declare a datatype
- Add tests
- Select failure handling behavior
- Optionally add remediation actions

Supported datatypes include:
- string
- boolean
- integer
- float
- date
- timestamp

---

## 11. Date & Timestamp Rules (Critical)

### 11.1 Date Rule Requirements
When a column is declared as `date` or `timestamp`, the user must specify:
- **Exactly one target date format**
- Failure handling policy
- Whether remediation (coercion) is allowed

### 11.2 Accepted Behavior
- Columns may contain multiple date representations
- User declares ONE expected target format
- System may:
  - test values against the target format, and/or
  - coerce supported input formats into the target format (if enabled)

### 11.3 Date Parsing Options
- User may optionally enable:
  - acceptance of multiple known input formats (robust mode)
  - Excel serial date parsing
- If remediation is enabled:
  - all output dates must be normalized to the target format

### 11.4 No Fuzzy Guessing
- No implicit auto-detection
- No ambiguous parsing without explicit user opt-in

---

## 12. Data Quality Tests

### 12.1 Column-Level Tests
- Not null
- Type conformance
- Numeric range
- String length
- Enumerated allowed values (case-insensitive optional)
- Date window
- Uniqueness (null policy configurable)
- Monotonic
- Cardinality warnings
- Pattern validation:
  - Tier 1: presets
  - Tier 2: guided builder
  - Tier 3: advanced regex

### 12.2 Dataset-Level Tests
- Duplicate rows
- Primary key completeness
- Primary key uniqueness
- Composite key uniqueness
- Cross-field logical rules
- Outlier detection (IQR, Z-score; informational only)

---

## 13. Foreign Key (FK) Membership Check

### 13.1 Scope (v1)
- Optional FK file upload
- One FK column only
- One dataset column mapped to FK column

### 13.2 Behavior
- Dataset values must exist in FK set
- Same normalization rules apply to both sides (as defined by the dataset column rules)
- Failure handling options apply

---

## 14. Failure Handling Policies

For each test or column, the user must select one:
- Strict fail (block export)
- Set value to null
- Label failure in extra column
- Quarantine row
- Drop row

---

## 15. Remediation & Approval

- Remediation is optional
- Cleaned copy only (never in-place)
- Before applying changes:
  - show sample diffs
  - show impacted row and cell counts
- Single approval step to apply all changes

---

## 16. Reporting & Exports

### 16.1 Export Options (All Optional)
- Cleaned dataset
- YAML contract
- **HTML data quality report (only)**
- Standalone remediation summary (also included inside HTML report if remediation ran)

### 16.2 HTML Report Requirements
- Human-readable
- Suitable for emailing
- Includes:
  - dataset summary
  - test results
  - failing examples
  - remediation summary (if applied)
  - before/after metrics

---

## 17. Privacy & Session Control

- Clear privacy policy page
- Explicit statement:
  - no data storage
  - no databases
  - no reuse of uploaded files
- “Clear session now” button must:
  - immediately wipe all in-memory state

---

## 18. Feature Requests

- Feature requests are handled via **GitHub Discussions**
- App must link to Discussions page
- App may display a read-only list of top requests

---

## 19. Non-Goals (Explicit)

The following are **out of scope for v1**:
- AI-assisted validation or cleaning
- Persistent user accounts
- Background jobs or scheduling
- Multi-table joins
- Multi-sheet dataset processing
- JSON report export

---

## 20. Definition of Done

The application is considered complete when:
- All acceptance criteria above are met
- App runs reliably on Streamlit Community Cloud
- No data persists beyond a session
- YAML contracts can fully recreate validation behavior
- Outputs are professional and suitable for real-world use

---

# 21. YAML Contract Schema (v1)

This section defines the required YAML structure.  
The schema is designed for:
- deterministic parsing by the application,
- human readability/editability,
- round-tripping between UI and YAML.

## 21.1 Schema Overview

Top-level keys (all required unless stated optional):

- `contract_version` (required)
- `contract_id` (required; UUID string or user-provided)
- `created_at_utc` (required; ISO 8601)
- `app` (required; metadata)
- `limits` (optional; mirrors app caps for transparency)
- `dataset` (required)
- `columns` (required; list of column specs)
- `dataset_tests` (optional; list)
- `foreign_key_checks` (optional; list; v1 single-column membership)
- `exports` (optional; preferred export settings)

### 21.1.1 Enumerations (Must use these exact strings)

**Data types**
- `string`
- `boolean`
- `integer`
- `float`
- `date`
- `timestamp`

**Failure actions**
- `strict_fail`
- `set_null`
- `label_failure`
- `quarantine_row`
- `drop_row`

**Regex tiers**
- `preset`
- `builder`
- `advanced`

---

## 21.2 Top-Level Contract Keys

### 21.2.1 `contract_version`
- String, required.
- Example: `"1.0"`

### 21.2.2 `contract_id`
- String, required.
- May be a UUID.
- Example: `"c7f6b7c1-8d1d-4fe6-a48f-4e1c9cb4a1c2"`

### 21.2.3 `created_at_utc`
- ISO 8601 datetime string, required.
- Example: `"2025-12-27T20:15:00Z"`

### 21.2.4 `app`
- Object, required.
- Keys:
  - `name` (required) e.g., `"Data Doctor"`
  - `version` (required) e.g., `"0.1.0"`

### 21.2.5 `limits` (optional)
- Object.
- Provides transparency about caps used when the contract was created.
- Keys:
  - `max_upload_mb` (integer)
  - `max_rows` (integer)
  - `max_columns` (integer)

### 21.2.6 `dataset`
- Object, required.
- Keys:
  - `input_file_name` (optional; informational only)
  - `sheet_name` (optional; if Excel)
  - `header_row` (optional; default 1)
  - `delimiter` (optional; CSV)
  - `encoding` (optional; CSV)
  - `row_limit_behavior` (required)
    - `reject_if_over_limit` must be true in v1

---

## 21.3 Column Specification (`columns[]`)

Each entry in `columns` represents one dataset column and must include:

- `name` (required)  
- `rename_to` (optional; if renaming)
- `data_type` (required)
- `required` (required; boolean)
- `normalization` (optional; common preprocessing)
- `tests` (optional; list of tests)
- `remediation` (optional; list of remediation actions)
- `failure_handling` (required; default behavior for this column)

### 21.3.1 `normalization` (optional)
Normalization is applied before tests and remediation.

Allowed keys:
- `trim_whitespace` (boolean)
- `null_tokens` (list of strings to be treated as null)
- `case` (`none` | `lower` | `upper` | `title`)
- `remove_non_printable` (boolean)

### 21.3.2 `failure_handling` (required)
Defines the default action when a test fails and a more specific test-level action is not provided.

Keys:
- `action` (required; enum from Failure actions)
- `label_column_name` (optional; required if action is `label_failure`)
- `quarantine_export_name` (optional; used if action is `quarantine_row`)

### 21.3.3 Column Tests (`tests[]`)
Each test entry has:
- `type` (required; test type)
- `severity` (required; `error` or `warning`)
- `params` (optional; test-specific)
- `on_fail` (optional; overrides column default failure handling)

Supported column test `type` values:
- `not_null`
- `type_conformance`
- `range`
- `length`
- `enum`
- `uniqueness`
- `monotonic`
- `cardinality_warning`
- `pattern`
- `date_rule`
- `date_window`

### 21.3.4 Remediation (`remediation[]`)
Remediation actions are optional and only applied if user approved remediation in the UI.

Each remediation entry has:
- `type` (required)
- `params` (optional)

Supported remediation `type` values (v1):
- `trim_whitespace`
- `standardize_nulls`
- `normalize_case`
- `remove_non_printable`
- `deduplicate_rows` (dataset-level; typically not per column; may appear in dataset remediation instead)
- `numeric_cleanup`
- `boolean_normalization`
- `date_coerce`
- `categorical_standardize`
- `split_column`
- `custom_calculation`

---

## 21.4 Dataset-Level Tests (`dataset_tests[]`) (Optional)

Each dataset test entry has:
- `type` (required)
- `severity` (required; `error` or `warning`)
- `params` (optional)
- `on_fail` (optional; failure action)

Supported dataset test `type` values (v1):
- `duplicate_rows`
- `primary_key_completeness`
- `primary_key_uniqueness`
- `composite_key_uniqueness`
- `cross_field_rule`
- `outliers_iqr` (warning only)
- `outliers_zscore` (warning only)

---

## 21.5 Foreign Key Checks (`foreign_key_checks[]`) (Optional)

v1 supports only **single-column membership validation**.

Each FK check has:
- `name` (required; string)
- `dataset_column` (required)
- `fk_file` (required; informational only)
- `fk_sheet` (optional)
- `fk_column` (required)
- `normalization_inherit_from_dataset_column` (required; must be true in v1)
- `null_policy` (required; `allow_nulls` boolean)
- `on_fail` (required; failure action)

---

## 21.6 Exports (`exports`) (Optional)

- `report_html` (boolean; default true)
- `cleaned_dataset` (boolean)
- `contract_yaml` (boolean)
- `remediation_summary` (boolean)
- `output_format` (`csv` or `xlsx`; recommended default `csv`)

---

# 22. YAML Contract Examples

## 22.1 Minimal Contract (Schema Only)

```yaml
contract_version: "1.0"
contract_id: "c7f6b7c1-8d1d-4fe6-a48f-4e1c9cb4a1c2"
created_at_utc: "2025-12-27T20:15:00Z"
app:
  name: "Data Doctor"
  version: "0.1.0"

limits:
  max_upload_mb: 75
  max_rows: 250000
  max_columns: 100

dataset:
  input_file_name: "orders.xlsx"
  sheet_name: "Sheet1"
  row_limit_behavior:
    reject_if_over_limit: true

columns:
  - name: "Order ID"
    rename_to: "order_id"
    data_type: "string"
    required: true
    normalization:
      trim_whitespace: true
      null_tokens: ["", "NA", "N/A", "null", "None"]
      case: "none"
      remove_non_printable: true
    tests:
      - type: "not_null"
        severity: "error"
      - type: "uniqueness"
        severity: "error"
        params:
          allow_nulls: false
    failure_handling:
      action: "strict_fail"

  - name: "Order Date"
    rename_to: "order_date"
    data_type: "date"
    required: true
    normalization:
      trim_whitespace: true
      null_tokens: ["", "NA", "N/A"]
      case: "none"
      remove_non_printable: true
    tests:
      - type: "date_rule"
        severity: "error"
        params:
          target_format: "YYYY-MM-DD"
          mode: "simple"   # simple = target format only
          excel_serial_enabled: false
          allow_multi_input_formats: false
    failure_handling:
      action: "label_failure"
      label_column_name: "__data_doctor_errors__"

exports:
  report_html: true
  cleaned_dataset: false
  contract_yaml: true
  remediation_summary: false
  output_format: "csv"

## 22.2 Robust Date Coercion + Failure Policies

contract_version: "1.0"
contract_id: "e21b1a2f-3d1c-4c58-b7e7-2c5b6e1fa999"
created_at_utc: "2025-12-27T20:30:00Z"
app:
  name: "Data Doctor"
  version: "0.1.0"

dataset:
  input_file_name: "patients.csv"
  row_limit_behavior:
    reject_if_over_limit: true

columns:
  - name: "patient_id"
    data_type: "string"
    required: true
    tests:
      - type: "not_null"
        severity: "error"
      - type: "pattern"
        severity: "error"
        params:
          tier: "preset"
          preset_name: "uuid"
    failure_handling:
      action: "strict_fail"

  - name: "visit_date"
    data_type: "date"
    required: true
    normalization:
      trim_whitespace: true
      null_tokens: ["", "NA", "N/A", "NULL"]
      remove_non_printable: true
      case: "none"
    tests:
      - type: "date_rule"
        severity: "error"
        params:
          target_format: "YYYYMMDD"
          mode: "robust"
          excel_serial_enabled: true
          allow_multi_input_formats: true
          accepted_input_formats:
            - "YYYY-MM-DD"
            - "MM/DD/YYYY"
            - "DD/MM/YYYY"
            - "YYYYMMDD"
            - "MMDDYY"
            - "DD-MMM-YYYY"
    remediation:
      - type: "date_coerce"
        params:
          coerce_to_target_format: true
    failure_handling:
      action: "quarantine_row"
      quarantine_export_name: "quarantine_visit_date"

exports:
  report_html: true
  cleaned_dataset: true
  contract_yaml: true
  remediation_summary: true
  output_format: "csv"

## 22.3 Enum + Case-Insensitive + Numeric Cleanup

contract_version: "1.0"
contract_id: "3f08df3a-4d20-4b63-8e2b-88c4a1c86bb0"
created_at_utc: "2025-12-27T21:00:00Z"
app:
  name: "Data Doctor"
  version: "0.1.0"

dataset:
  input_file_name: "inventory.xlsx"
  sheet_name: "export"
  row_limit_behavior:
    reject_if_over_limit: true

columns:
  - name: "state"
    data_type: "string"
    required: true
    normalization:
      trim_whitespace: true
      case: "upper"
      null_tokens: ["", "NA", "N/A"]
      remove_non_printable: true
    tests:
      - type: "enum"
        severity: "error"
        params:
          allowed_values: ["TX", "CA", "NY", "FL"]
          case_insensitive: true
    remediation:
      - type: "categorical_standardize"
        params:
          mapping:
            "Texas": "TX"
            "Tx": "TX"
            "CALIFORNIA": "CA"
    failure_handling:
      action: "label_failure"
      label_column_name: "__data_doctor_errors__"

  - name: "unit_price"
    data_type: "float"
    required: true
    tests:
      - type: "type_conformance"
        severity: "error"
    remediation:
      - type: "numeric_cleanup"
        params:
          remove_commas: true
          remove_currency_symbols: true
          parentheses_as_negative: true
          on_parse_error: "set_null"
    failure_handling:
      action: "set_null"

exports:
  report_html: true
  cleaned_dataset: true
  contract_yaml: true
  remediation_summary: true
  output_format: "csv"

## 22.4 FK Membership Check (Single Column)

contract_version: "1.0"
contract_id: "b1d7c1a2-7714-4d18-b1f8-2f88cbbd7001"
created_at_utc: "2025-12-27T21:30:00Z"
app:
  name: "Data Doctor"
  version: "0.1.0"

dataset:
  input_file_name: "orders.csv"
  row_limit_behavior:
    reject_if_over_limit: true

columns:
  - name: "customer_id"
    data_type: "string"
    required: true
    normalization:
      trim_whitespace: true
      case: "none"
      null_tokens: ["", "NA", "N/A"]
      remove_non_printable: true
    tests:
      - type: "not_null"
        severity: "error"
    failure_handling:
      action: "strict_fail"

foreign_key_checks:
  - name: "customer_id_in_customer_master"
    dataset_column: "customer_id"
    fk_file: "customers.xlsx"
    fk_sheet: "Sheet1"
    fk_column: "customer_id"
    normalization_inherit_from_dataset_column: true
    null_policy:
      allow_nulls: false
    on_fail:
      action: "quarantine_row"
      quarantine_export_name: "quarantine_fk_customer_id"

exports:
  report_html: true
  cleaned_dataset: false
  contract_yaml: true
  remediation_summary: false
  output_format: "csv"

## 22.5 Pattern Validation: Builder Tier Example (No Regex Required)

contract_version: "1.0"
contract_id: "2b6c5b3d-4bb6-4c9a-a5c2-9b0fe11caa01"
created_at_utc: "2025-12-27T22:00:00Z"
app:
  name: "Data Doctor"
  version: "0.1.0"

dataset:
  input_file_name: "leads.csv"
  row_limit_behavior:
    reject_if_over_limit: true

columns:
  - name: "zip_code"
    data_type: "string"
    required: true
    normalization:
      trim_whitespace: true
      case: "none"
      null_tokens: ["", "NA", "N/A"]
      remove_non_printable: true
    tests:
      - type: "pattern"
        severity: "error"
        params:
          tier: "builder"
          builder:
            allowed_characters: ["digits"]
            length:
              exact: 5
            starts_with: null
            ends_with: null
    remediation:
      - type: "categorical_standardize"
        params:
          zip_left_pad_zeros: true
    failure_handling:
      action: "label_failure"
      label_column_name: "__data_doctor_errors__"

exports:
  report_html: true
  cleaned_dataset: true
  contract_yaml: true
  remediation_summary: true
  output_format: "csv"

## 22.6 Dataset-Level Tests Example (Primary Key + Duplicates + Cross Field)
contract_version: "1.0"
contract_id: "d8ce3e83-1b50-4b04-a4dd-7b1d730f1e10"
created_at_utc: "2025-12-27T22:30:00Z"
app:
  name: "Data Doctor"
  version: "0.1.0"

dataset:
  input_file_name: "claims.csv"
  row_limit_behavior:
    reject_if_over_limit: true

columns:
  - name: "claim_id"
    data_type: "string"
    required: true
    tests:
      - type: "not_null"
        severity: "error"
      - type: "uniqueness"
        severity: "error"
        params:
          allow_nulls: false
    failure_handling:
      action: "strict_fail"

  - name: "start_date"
    data_type: "date"
    required: true
    tests:
      - type: "date_rule"
        severity: "error"
        params:
          target_format: "YYYY-MM-DD"
          mode: "simple"
          allow_multi_input_formats: false
          excel_serial_enabled: false
    failure_handling:
      action: "set_null"

  - name: "end_date"
    data_type: "date"
    required: true
    tests:
      - type: "date_rule"
        severity: "error"
        params:
          target_format: "YYYY-MM-DD"
          mode: "simple"
          allow_multi_input_formats: false
          excel_serial_enabled: false
    failure_handling:
      action: "set_null"

dataset_tests:
  - type: "duplicate_rows"
    severity: "warning"

  - type: "primary_key_completeness"
    severity: "error"
    params:
      key_columns: ["claim_id"]

  - type: "primary_key_uniqueness"
    severity: "error"
    params:
      key_columns: ["claim_id"]

  - type: "cross_field_rule"
    severity: "error"
    params:
      rule_name: "start_before_end"
      if:
        all_not_null: ["start_date", "end_date"]
      assert:
        expression: "start_date <= end_date"

exports:
  report_html: true
  cleaned_dataset: false
  contract_yaml: true
  remediation_summary: false
  output_format: "csv"

---

## 23. Implementation Decisions (v1)

This section documents specific implementation decisions made during design review.

### 23.1 Pattern Presets (Regex-Based)

The following regex-based pattern presets are supported:

| Preset | Description |
|--------|-------------|
| `uuid` | Universally Unique Identifier |
| `email` | Email address |
| `phone_us` | US phone number |
| `zip_us_5` | US 5-digit ZIP code |
| `zip_us_9` | US 9-digit ZIP+4 code |
| `url` | URL/URI |
| `ipv4` | IPv4 address |
| `ipv6` | IPv6 address |

**Explicitly Excluded (Security/Privacy):**
- `ssn` (Social Security Number)
- `credit_card`
- `bank_account`
- `routing_number`
- Any high-security or financial identifier patterns

### 23.2 Date Format Notation

- Use human-readable tokens in contract: `YYYY`, `MM`, `DD`, `HH`, `mm`, `ss`, etc.
- Map internally to Python/pandas format codes.
- User declares exactly ONE target format per column.
- Column may contain multiple input date styles.
- If robust mode + remediation is enabled, coerce from selected input formats into the single target format.
- No fuzzy guessing without explicit robust-mode opt-in.

### 23.3 Cross-Field Expression Syntax (v1)

- Support simple comparisons only: `<`, `<=`, `>`, `>=`, `==`, `!=`
- Operands may be column references or literals.
- No arithmetic expressions in v1.
- If user needs arithmetic, they must first create a calculated column, then compare that column.

### 23.4 Error Label Format

When using `label_failure` action, errors are recorded as follows:

- **Format:** Pipe-delimited list of failing rule identifiers with optional short detail suffix.
- **Example:** `not_null|date_rule:invalid_format|enum:unexpected_value`
- **Optional additional columns:**
  - `__data_doctor_error_count__` (integer count of failures)
  - `__data_doctor_status__` (`PASS` or `FAIL`)

### 23.5 Outlier Detection Defaults

| Method | Default Threshold | Behavior |
|--------|-------------------|----------|
| IQR | 1.5 multiplier | Warning only (non-blocking) |
| Z-score | 3.0 | Warning only (non-blocking) |

- User-configurable in contract.
- Warnings only by default; do not block export.

### 23.6 Boolean Recognition

Case-insensitive, whitespace-trimmed recognition:

| True Tokens | False Tokens |
|-------------|--------------|
| `true`, `yes`, `1`, `t`, `y`, `on` | `false`, `no`, `0`, `f`, `n`, `off` |

Non-matching values follow column failure handling policy.

### 23.7 CSV Encoding

- **Default:** `utf-8`
- **Fallback order (if decode fails):** `utf-8-sig`, then `latin-1`
- **Manual override allowed:** `utf-8`, `utf-8-sig`, `latin-1`
- No auto-detection in v1.

### 23.8 Enum-Style Preset Validations (Non-Regex)

These presets use fixed allowed-value lists rather than regex patterns.

#### US States Presets

**Preset: `us_state_2_letter`** (case-insensitive)
```
AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY
```

**Preset: `us_state_full_name`** (case-insensitive)
```
Alabama, Alaska, Arizona, Arkansas, California, Colorado, Connecticut, Delaware, District of Columbia, Florida, Georgia, Hawaii, Idaho, Illinois, Indiana, Iowa, Kansas, Kentucky, Louisiana, Maine, Maryland, Massachusetts, Michigan, Minnesota, Mississippi, Missouri, Montana, Nebraska, Nevada, New Hampshire, New Jersey, New Mexico, New York, North Carolina, North Dakota, Ohio, Oklahoma, Oregon, Pennsylvania, Rhode Island, South Carolina, South Dakota, Tennessee, Texas, Utah, Vermont, Virginia, Washington, West Virginia, Wisconsin, Wyoming
```

**Preset: `us_state_code_or_name`** (case-insensitive)
Union of `us_state_2_letter` and `us_state_full_name`.

#### Countries Preset

**Preset: `country_iso3166_alpha2`** (ISO 3166-1 alpha-2, case-insensitive)
```
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ
BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ
CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ
DE DJ DK DM DO DZ
EC EE EG EH ER ES ET
FI FJ FK FM FO FR
GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY
HK HM HN HR HT HU
ID IE IL IM IN IO IQ IR IS IT
JE JM JO JP
KE KG KH KI KM KN KP KR KW KY KZ
LA LB LC LI LK LR LS LT LU LV LY
MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ
NA NC NE NF NG NI NL NO NP NR NU NZ
OM
PA PE PF PG PH PK PL PM PN PR PS PT PW PY
QA
RE RO RS RU RW
SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ
TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ
UA UG UM US UY UZ
VA VC VE VG VI VN VU
WF WS
YE YT
ZA ZM ZW
```

#### Units of Measure Presets

**Preset: `uom_ansi_x12`**
General ANSI/X12 UOM list (large list; separate from packaging subset).

**Preset: `uom_ansi_packaging`** (case-insensitive)

| Code | Description | Category |
|------|-------------|----------|
| EA | Each | General Packaging |
| PK | Pack | General Packaging |
| CT | Carton | General Packaging |
| CS | Case | General Packaging |
| BX | Box | General Packaging |
| BG | Bag | General Packaging |
| RL | Roll | General Packaging |
| TU | Tube | General Packaging |
| CN | Can | General Packaging |
| BT | Bottle | General Packaging |
| JR | Jar | General Packaging |
| PL | Pallet | Bulk / Logistics |
| SK | Skid | Bulk / Logistics |
| DR | Drum | Bulk / Logistics |
| TN | Tin | Bulk / Logistics |
| LB | Pound | Bulk / Logistics |
| KG | Kilogram | Bulk / Logistics |
| VL | Vial | Healthcare / Medical / Lab |
| AM | Ampule | Healthcare / Medical / Lab |
| SY | Syringe | Healthcare / Medical / Lab |
| KT | Kit | Healthcare / Medical / Lab |
| TR | Tray | Healthcare / Medical / Lab |
| DV | Device | Healthcare / Medical / Lab |
| FT | Foot | Length / Material |
| IN | Inch | Length / Material |
| YD | Yard | Length / Material |

---

## 24. YAML Validation Rules (Contract Self-Validation)

Before any dataset validation or remediation is performed, the application **must validate the YAML contract itself**.
Contract validation errors must block execution until resolved.

### 24.1 Required Contract Validation Checks

The system **must validate** the following conditions:

#### Top-Level Structure
- All required top-level keys **must exist**:
  - `contract_version`
  - `contract_id`
  - `created_at_utc`
  - `app`
  - `dataset`
  - `columns`

#### Column References
- Any column referenced in:
  - column-level tests
  - dataset-level tests
  - foreign key checks  
  **must exist** in the `columns[]` definition.

#### Data Types
- `data_type` values **must be one of the allowed enums**:
  - `string`
  - `boolean`
  - `integer`
  - `float`
  - `date`
  - `timestamp`

#### Failure Handling
- `failure_handling.action` **must be a valid enum**:
  - `strict_fail`
  - `set_null`
  - `label_failure`
  - `quarantine_row`
  - `drop_row`

- If `action: label_failure`:
  - `label_column_name` **must be provided**

- If `action: quarantine_row`:
  - `quarantine_export_name` **must be provided**

#### Date Rules
- Any `date_rule` test **must specify exactly one**:
  - `target_format`

- If `mode: robust`:
  - `accepted_input_formats` **must be provided**
  - `accepted_input_formats` **must be a non-empty list**

#### Foreign Key Checks (v1 Constraints)
- All foreign key checks **must include**:
  - `normalization_inherit_from_dataset_column: true`
- Only single-column FK membership checks are allowed in v1

---

### 24.2 Contract Validation Failure Behavior

If contract validation fails, the UI **must**:

- Display a **human-readable error message**
- Clearly indicate:
  - which YAML field is invalid or missing
  - why the field is invalid
- Provide **actionable guidance** on how to fix the issue
- Prevent dataset validation or remediation from running until the contract is valid

Contract validation errors **must not** expose stack traces or internal application details.

---
