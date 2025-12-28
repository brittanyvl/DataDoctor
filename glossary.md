# Data Doctor — Glossary

This glossary explains data quality and validation terms used throughout the **Data Doctor** application.  
Definitions are written for users who are comfortable with spreadsheets but may not be familiar with database or data engineering terminology.

---

## Cardinality
**What it means:**  
The number of **distinct values** in a column.

**Why it matters:**  
- Low cardinality columns are often categories (e.g., status, state).
- Very high cardinality may indicate IDs, free text, or messy data.

**Example:**  
A column with values `["TX", "CA", "TX", "NY"]` has a cardinality of **3**.

---

## Coerce
**What it means:**
To **convert values into the expected type or format** when possible.

**Why it matters:**
Coercion allows the system to fix common issues (e.g., turning `"1,200"` into `1200`) instead of failing immediately.

**Example:**
`"01/07/2025"` → `2025-01-07`

---

## Composite Key
**What it means:**  
A key made up of **multiple columns together** that uniquely identify a row.

**Why it matters:**  
Sometimes no single column is unique, but a combination is.

**Example:**  
`order_id + line_number`

---

## Data Cleaning
**What it means:**
Automated transformations applied to data to fix formatting issues, standardize values, and remove unwanted characters.

**Why it matters:**
Data cleaning ensures consistent formatting across your dataset without manually editing each value.

**Common data cleaning actions:**
- Trim whitespace (remove leading/trailing spaces)
- Normalize case (convert to lowercase, UPPERCASE, or Title Case)
- Remove special characters (control characters, null bytes)
- Remove punctuation marks
- Standardize dates to a consistent format
- Clean numeric formatting (remove currency symbols, commas)

---

## Diagnostics
**What it means:**
The validation tests and rules that Data Doctor runs against your data to identify quality issues.

**Why it matters:**
Diagnostics help you discover problems in your data before they cause issues downstream. Think of it like a health checkup for your spreadsheet.

**Examples:**
- Checking for missing required values
- Validating data types (text, numbers, dates)
- Ensuring values fall within expected ranges
- Detecting duplicate rows
- Verifying pattern compliance (emails, phone numbers)

---

## Date Format
**What it means:**
The specific way a date is written.

**Why it matters:**
Dates like `01/07/25` can be ambiguous. Data Doctor requires you to explicitly state the expected format.

**Examples:**
- `YYYY-MM-DD` → `2025-01-07`
- `MM/DD/YYYY` → `01/07/2025`
- `YYYYMMDD` → `20250107`

---

## Excel Serial Date
**What it means:**  
A numeric value Excel uses internally to represent dates.

**Why it matters:**  
Dates may appear as numbers like `45321` instead of readable dates.

**Example:**  
`45321` → `2024-01-01` (depending on Excel system)

---

## Enumerated Values (Enum)
**What it means:**  
A **fixed list of allowed values** for a column.

**Why it matters:**  
Ensures consistency and prevents unexpected or misspelled values.

**Example:**  
Allowed values: `["TX", "CA", "NY"]`

---

## Failure Handling
**What it means:**  
What Data Doctor should do when a rule or test fails.

**Common options:**
- **Strict fail** – Stop processing
- **Set null** – Replace invalid value with null
- **Label failure** – Mark the row as invalid
- **Quarantine row** – Move row to a separate dataset
- **Drop row** – Remove the row entirely

---

## Foreign Key (FK)
**What it means:**  
A value in one dataset that must exist in another dataset.

**Why it matters:**  
Ensures references are valid (e.g., customer IDs exist in the customer list).

**Example:**  
`orders.customer_id` must exist in `customers.customer_id`

---

## Monotonic
**What it means:**  
Values **always increase (or stay the same)** as you move down the column.

**Why it matters:**  
Useful for timestamps, sequence numbers, or IDs that should never go backwards.

**Example:**  
`1, 2, 3, 4, 4, 5` → monotonic  
`1, 3, 2` → not monotonic

---

## Null
**What it means:**  
A missing or empty value.

**Why it matters:**  
Nulls can break calculations, joins, and reporting if not handled intentionally.

**Examples of null tokens:**  
`""`, `"NA"`, `"N/A"`, `"null"`, `"None"`

---

## Outlier
**What it means:**  
A value that is **unusually large or small** compared to the rest of the data.

**Why it matters:**  
Outliers may indicate errors, data entry issues, or rare but valid cases.

**Common methods used:**
- IQR (Interquartile Range)
- Z-score

---

## Pattern Validation
**What it means:**  
Checking that values follow a specific structure.

**Why it matters:**  
Ensures consistency for IDs, ZIP codes, emails, etc.

**Examples:**  
- ZIP code must be exactly 5 digits  
- UUID format  
- Numeric-only strings

---

## Primary Key
**What it means:**  
A column that **uniquely identifies each row**.

**Why it matters:**  
Primary keys prevent duplicate records and enable reliable joins.

**Example:**  
`order_id`

---

## Quarantine
**What it means:**  
Removing problematic rows from the main dataset and placing them in a **separate output**.

**Why it matters:**  
Allows you to keep clean data while still reviewing what failed.

---

## Referential Integrity
**What it means:**  
Ensuring relationships between datasets remain valid.

**Why it matters:**  
Prevents orphaned records (e.g., orders without customers).

---

## Strict Fail
**What it means:**  
Stop processing immediately when a rule fails.

**Why it matters:**  
Useful when data must be perfect before use.

---

## Timestamp
**What it means:**
A date **and time**, optionally including timezone information.

**Examples:**
- `2025-01-07 14:32:10`
- `2025-01-07T14:32:10Z`

---

## Treatments
**What it means:**
The data cleaning and remediation actions that Data Doctor applies to fix issues found during diagnostics.

**Why it matters:**
Treatments automatically correct common data problems, saving you from manually editing each cell. Think of it like medicine for your spreadsheet after the diagnosis.

**Examples:**
- Trimming extra whitespace from text
- Standardizing date formats
- Normalizing case (uppercase, lowercase)
- Removing duplicate rows
- Filling or flagging null values
- Cleaning numeric formatting

---

## Text (String)
**What it means:**
A data type for storing textual values like names, descriptions, codes, and other character-based data.

**Why it matters:**
Text columns can contain any characters and are often validated using pattern matching, length limits, or approved value lists.

**Examples:**
- Names: `"John Smith"`
- Codes: `"ABC123"`
- Descriptions: `"This is a product description."`

---

## Type Conformance
**What it means:**  
Checking whether values match the declared data type.

**Why it matters:**  
Prevents mixing numbers, text, and dates in the same column.

**Example:**  
A numeric column containing `"abc"` fails type conformance.

---

## Uniqueness
**What it means:**  
Ensuring values in a column do not repeat.

**Why it matters:**  
Often required for IDs and keys.

**Example:**  
`[1, 2, 3]` → unique  
`[1, 2, 2]` → not unique

---

## YAML Contract
**What it means:**  
A human-readable configuration file that defines:
- schema
- rules
- tests
- remediation behavior

**Why it matters:**  
Allows you to re-run the same validation logic consistently without storing data.

---

## Z-Score
**What it means:**  
A statistical measure of how far a value is from the average.

**Why it matters:**  
Used to flag potential outliers.

---

## UUID
**What it means:**  
A Universally Unique Identifier.

**Why it matters:**  
Often used as an ID that should never repeat.

**Example:**  
`550e8400-e29b-41d4-a716-446655440000`

---
