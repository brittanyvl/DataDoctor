# DataDoctor Roadmap

This document outlines planned enhancements to Data Doctor. Features are organized by category—no timelines, just a clear vision of where we're headed.

> **Note**: Some features listed here already have backend implementations and are awaiting UI integration. These are marked with a star.

---

## Statistical Analysis & Anomaly Detection

Catch unusual data points that may indicate errors, fraud, or data quality issues before they cause downstream problems.

| Feature | Description |
|---------|-------------|
| **Outlier Detection (IQR)** ⭐ | Flag values that fall outside 1.5x the interquartile range. Useful for catching data entry errors in numeric fields like prices, quantities, or ages. |
| **Outlier Detection (Z-Score)** ⭐ | Identify values more than N standard deviations from the mean. Better for normally distributed data where you want statistical precision. |
| **Expected Row Count** | Declare how many rows you expect (exact, min, max). Catch truncated exports or runaway duplicates before processing. 

---

## Relational Integrity

Ensure your data maintains proper relationships before loading into databases or joining with other datasets.

| Feature | Description |
|---------|-------------|

| **Composite Key Uniqueness** ⭐ | Validate uniqueness across multiple columns combined (e.g., `customer_id` + `order_date`). Critical for fact tables and transactional data. |
| **Foreign Key Validation** | Check that values exist in a reference table before loading. Catch orphaned records that would fail referential integrity constraints. |
| **Cardinality Checks** | Validate expected relationships (one-to-one, one-to-many). Ensure a customer has at most one primary address, or an order has at least one line item. |

---

## Advanced Data Cleansing

Transform messy, inconsistent data into clean, standardized formats ready for analysis or loading.

| Feature | Description |
|---------|-------------|
| **Column Splitting** ⭐ | Split a single column into multiple columns on a delimiter. Turn "City, State" into separate `city` and `state` columns. |

**Smart Splitting Presets** — Common patterns with built-in intelligence:

| Preset | What It Does |
|--------|--------------|
| **City, State** | Split on comma, trim whitespace, validate state abbreviations. Handles "Austin, TX" and "New York, NY" cleanly. |
| **First Name / Last Name** | Split on last space only, keeping "Mary Jane Watson" as "Mary Jane" + "Watson". Flags names with no space or unusual patterns for review. |
| **Full Address** | Parse street, city, state, ZIP from a single address field using pattern recognition. |
| **Date Components** | Split dates into year, month, day columns for easier filtering and grouping. |
| **Email → Username + Domain** | Split on @ to separate local part from domain for analysis or validation. |
| **File Path → Folder + Filename** | Extract directory path and filename from full paths. |
| **Phone → Area Code + Number** | Parse US phone numbers into area code and local number components. |
| **Custom Delimiter** | Split on any character or string (pipe, tab, semicolon, etc.) with control over max splits. |

> Each preset includes validation to flag rows that don't match the expected pattern, so you can review edge cases before they cause problems.

| Feature | Description |
|---------|-------------|
| **Text Parsing** | Extract specific patterns from text using regex capture groups. Pull area codes from phone numbers or domains from email addresses. |
| **Column Concatenation** | Combine multiple columns into one with a separator. Create full names from first/last, or composite keys from multiple fields. |
| **Fill Null Values** | Replace nulls with a default value, the column mean, or values from another column. Handle missing data systematically. |
| **Clamp Numeric Ranges** | Force values into a valid range (e.g., percentages between 0-100). Fix out-of-bounds values instead of just flagging them. |

---

## Calculated Fields & Formulas

Generate new columns and derive values without leaving the tool or writing code.

| Feature | Description |
|---------|-------------|
| **Basic Math Operations** | Add, subtract, multiply, or divide columns to create calculated fields. Compute `total = quantity * unit_price` or `margin = revenue - cost`. |
| **UUID Generation** | Generate unique identifiers from column values or combinations. Create stable surrogate keys for records lacking natural keys. |
| **Hash Generation** | Create MD5 or SHA256 hashes from column combinations. Build deduplication keys or anonymize sensitive values. |
| **Conditional Logic** | Apply IF/THEN rules to derive values. Set `status = "overdue"` when `due_date < today`, or categorize values into buckets. |

---

## Lookup & Join Assistance

Combine data from multiple sources with confidence, catching mismatches before they become problems.

| Feature | Description |
|---------|-------------|
| **VLOOKUP-Style Enrichment** | Add columns from a reference file based on a matching key. Enrich order data with customer details or product attributes. |
| **Join Preview** | See what would match, what wouldn't, and why—before committing. Understand the impact of a join without modifying your data. |
| **Fuzzy Matching** | Match similar but not identical values (typos, abbreviations, formatting differences). Find "Microsoft Corp" when looking up "Microsoft Corporation". |

---

## Batch Processing & Automation

Scale validation beyond one-off manual runs to handle recurring data flows.

| Feature | Description |
|---------|-------------|
| **Multi-File Processing** | Apply the same contract to multiple files at once. Validate an entire folder of monthly exports in a single run. |
| **Scheduled Validation** | Watch folders or trigger validation on a schedule. Catch data quality issues as soon as new files arrive. This would be an advanced feature that works when running the app locally.  |

---

## Integrations

Connect Data Doctor to your existing data ecosystem.

| Feature | Description |
|---------|-------------|
| **Google Sheets** | Import directly from and export back to Google Sheets. Validate collaborative spreadsheets without download/upload cycles. |
| **SQL File Export** | Generate INSERT statements from your cleaned data, automatically batched into groups of 999 rows to respect database limits. Choose your dialect (PostgreSQL, MySQL, SQL Server) and get a ready-to-run .sql file. |
| **Cloud Storage** | Connect to S3, Google Cloud Storage, or Azure Blob. Process files where they live without local downloads. |
| **Database Export** | Write cleaned data directly to PostgreSQL, MySQL, or other databases. Complete the pipeline from raw file to production table. |

---

## Have a Feature Idea?

We'd love to hear what would make Data Doctor more useful for your workflow.

[Open a feature request](https://github.com/brittanyvl/DataDoctor/issues) on GitHub.
