# Data Doctor

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45+-FF4B4B.svg)](https://streamlit.io)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen.svg)](https://datadoctor.streamlit.app)

**Diagnose and treat your spreadsheet ailments.**

Data Doctor is a free, privacy-first data quality tool that helps you validate, clean, and standardize your spreadsheet data through an intuitive guided workflow—no account required.

[**Try the Live Demo**](https://datadoctor.streamlit.app) | [Report Issues](https://github.com/brittanyvl/DataDoctor/issues)


![Data Doctor Interface](assets/screenshots/homepage.png)



---

## The Problem

Data quality issues cost organizations time, money, and trust. Yet existing solutions present significant barriers:

- **Enterprise tools are expensive** — Pricing models exclude individuals and small teams
- **Complex setup required** — Many tools need database connections, API configurations, or IT involvement
- **Privacy concerns** — Cloud-based validators often require uploading sensitive data to third-party servers
- **Account fatigue** — Another username and password just to validate a CSV
- **Technical barriers** — Regex patterns and validation rules intimidate non-technical users

## The Solution

Data Doctor addresses each of these pain points:

| Problem | Data Doctor Solution |
|---------|---------------------|
| Expensive tools | **100% free**, open source |
| Complex setup | **Browser-based**, no installation needed |
| Privacy concerns | **In-memory processing only**—your data never touches a database |
| Account requirements | **No accounts**—save your rules as portable YAML files |
| Technical barriers | **Guided workflow** with progressive complexity |

---

## Key Features

### Guided 5-Step Workflow

Data Doctor uses a **medical metaphor** to make data quality approachable:

| Step | Name | Purpose |
|------|------|---------|
| 1 | **Data Check-In** | Upload your file, configure columns, preview data |

![Data Doctor Interface](assets/screenshots/step1_1.png)
![Data Doctor Interface](assets/screenshots/step1_2.png)

| 2 | **Order Diagnostics** | Define validation rules and quality checks |

![Data Doctor Interface](assets/screenshots/step2_2.png)
![Data Doctor Interface](assets/screenshots/step2_3.png)

| 3 | **Order Treatments** | Configure data cleansing and remediation |

![Data Doctor Interface](assets/screenshots/step3_1.png)

| 4 | **Review Findings** | See validation results with actionable details |

![Data Doctor Interface](assets/screenshots/step4_1.png)
![Data Doctor Interface](assets/screenshots/step4_2.png)

| 5 | **Download Reports** | Export cleaned data, reports, and reusable contracts |

![Data Doctor Interface](assets/screenshots/Step5_1.png)
![Data Doctor HTML Report](assets/screenshots/htmlreport_1.png)
![Data Doctor YAML Contract](assets/screenshots/yamlcontract.png)

> **Design Decision**: A wizard pattern with clear progression reduces cognitive load compared to single-page forms with dozens of options. Users see only what's relevant at each stage.

### Smart Sidebar Navigation

The persistent sidebar provides constant orientation:

- **Real-time status indicators** — See at a glance: file loaded, rules configured, issues found
- **Step navigation** — Jump back to completed steps, see what's ahead
- **Clear Session** — One-click reset with celebratory feedback
- **Privacy notice** — Constant reminder that your data stays in-memory

![Sidebar Navigation](assets/screenshots/sidebar.png)


> **Design Decision**: A sidebar keeps navigation visible without consuming vertical space. Status indicators reduce anxiety about "did my upload work?" questions.

### Comprehensive Validation Engine

#### Column-Level Tests (11 types)

| Test | Purpose | Example Use Case |
|------|---------|------------------|
| `not_null` | Ensure required fields have values | Customer email must exist |
| `type_conformance` | Validate data types | Price must be numeric |
| `range` | Check numeric bounds | Quantity between 1-1000 |
| `length` | Validate string length | SKU must be 8 characters |
| `enum` | Restrict to allowed values | Status in [pending, shipped, delivered] |
| `uniqueness` | Detect duplicates | Order ID must be unique |
| `monotonic` | Verify ordering | Invoice numbers always increase |
| `cardinality` | Flag unusual distributions | Warning if all values unique |
| `pattern` | Regex validation | Email format, phone numbers |
| `date_rule` | Date format consistency | Dates must be YYYY-MM-DD |
| `date_window` | Date range validation | Order date within last 2 years |

#### Dataset-Level Tests (7 types)

| Test | Purpose |
|------|---------|
| `duplicate_rows` | Find exact duplicate records |
| `primary_key_completeness` | Ensure key columns have no nulls |
| `primary_key_uniqueness` | Verify key combinations are unique |
| `composite_key_uniqueness` | Multi-column uniqueness checks |
| `cross_field_rule` | Logical relationships between columns |
| `outliers_iqr` | Statistical outlier detection (IQR method) |
| `outliers_zscore` | Statistical outlier detection (Z-score method) |

#### Cross-Field Validation

Define logical rules that span multiple columns:

```yaml
# Example: Ship date must be on or after order date
cross_field_rule:
  rule_name: "Ship date after order date"
  if:
    all_not_null: ["order_date", "ship_date"]
  assert:
    expression: "order_date <= ship_date"
```

> **Design Decision**: Separating column-level from dataset-level tests mirrors how data professionals think about quality—individual field validity vs. relational integrity.

### 3-Tier Regex Pattern System

Pattern validation scales to user expertise:

**Tier 1: Preset Patterns** — One-click selection for common formats
- Email, US Phone, ZIP codes (5 and 9 digit)
- URLs, UUIDs, IPv4/IPv6 addresses
- Numeric-only, alphanumeric, letters-only

**Tier 2: Pattern Builder** — Visual construction without regex knowledge
- Select allowed character types (digits, letters, etc.)
- Set length constraints (exact, min, max)
- Define required prefixes/suffixes

**Tier 3: Custom Regex** — Full regex support for advanced users

> **Design Decision**: Progressive complexity ensures non-technical users aren't intimidated while power users retain full control.

### Data Cleansing Options

14 remediation transformers handle common data issues:

| Category | Transformers |
|----------|-------------|
| **Text Cleanup** | trim_whitespace, normalize_case, remove_punctuation, remove_non_printable |
| **Null Handling** | standardize_nulls, fill_null |
| **Numeric** | numeric_cleanup (currency, commas, percentages), clamp_range |
| **Type Coercion** | boolean_normalization, date_coerce |
| **Categorical** | categorical_standardize (value mapping) |
| **Structural** | split_column, deduplicate_rows |

**Failure Handling Strategies:**

| Strategy | Behavior |
|----------|----------|
| `strict_fail` | Stop processing on first error |
| `set_null` | Replace invalid values with null |
| `label_failure` | Mark errors but continue (adds error columns) |
| `quarantine_row` | Move failing rows to separate output |
| `drop_row` | Remove failing rows from output |

### YAML Data Contracts

The contract system enables **reusability without accounts**:

```yaml
# Example contract snippet
contract_version: "1.0"
columns:
  - name: email
    data_type: string
    required: true
    tests:
      - type: pattern
        params:
          preset: email
    failure_handling:
      action: label_failure
```

**Benefits:**
- **Portable** — Download your rules, share with teammates, version control in Git
- **Human-readable** — YAML is easy to review and modify
- **Complete** — Preserves import settings, column renames, and transformations
- **No vendor lock-in** — Your validation logic belongs to you

> **Design Decision**: YAML contracts solve the "how do I save my work without creating an account?" problem. Users get persistence and shareability while we maintain zero data storage.

### Privacy-First Architecture

Data Doctor was designed with privacy as a feature, not an afterthought:

| Aspect | Implementation |
|--------|----------------|
| **Data Storage** | None—all processing happens in RAM |
| **Session Isolation** | Each user session is independent |
| **Data Lifecycle** | Cleared on browser close or manual reset |
| **Export Security** | Formula injection prevention on all outputs |
| **Transparency** | In-app privacy policy, visible privacy notice |

> **Design Decision**: Privacy constraints actually simplified architecture. No database, no user management, no data retention policies—just ephemeral, session-scoped processing.

### Demo Mode

Explore without uploading sensitive data:

- Pre-loaded sample dataset with intentional quality issues
- Contextual explanations for each validation rule
- See the full workflow without risk

---

## Technical Architecture

```
src/
├── ui/                      # Streamlit pages and components
│   ├── step_upload.py       # Step 1: File upload and configuration
│   ├── step_contract.py     # Step 2: Validation rule definition
│   ├── step_cleaning.py     # Step 3: Remediation configuration
│   ├── step_results.py      # Step 4: Validation execution and results
│   ├── step_export.py       # Step 5: Export and download
│   ├── components.py        # Reusable UI components (40+ functions)
│   ├── theme.py             # Centralized styling and brand colors
│   └── tooltips.py          # 25+ contextual help definitions
│
├── validation/              # Validation engine
│   ├── column_tests.py      # 11 column-level test implementations
│   ├── dataset_tests.py     # 7 dataset-level test implementations
│   ├── engine.py            # Validation orchestration
│   ├── foreign_key.py       # Referential integrity checks
│   └── results.py           # Result dataclasses
│
├── remediation/             # Data cleansing
│   ├── transformers.py      # 14 transformation implementations
│   ├── engine.py            # Remediation orchestration
│   └── diff.py              # Before/after change tracking
│
├── contract/                # YAML contract system
│   ├── schema.py            # Dataclass definitions (430+ lines)
│   ├── parser.py            # YAML serialization/deserialization
│   ├── builder.py           # Contract generation from DataFrames
│   └── validator.py         # Contract validation
│
├── presets/                 # Built-in patterns and enums
│   ├── patterns.py          # 11 regex presets + pattern builder
│   └── enums.py             # 6 enum presets (US states, countries, UOMs)
│
├── reporting/               # Export generation
│   └── html_report.py       # Interactive HTML report generation
│
├── file_handling/           # File I/O
│   ├── loader.py            # CSV/Excel parsing
│   └── export.py            # Output generation with formula protection
│
└── session.py               # Session state management
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **UI Framework** | Streamlit 1.45+ | Reactive Python-based web UI |
| **Data Processing** | Pandas, NumPy | DataFrame operations and analysis |
| **Validation** | Custom engine | Dataclass-based rule execution |
| **Excel Support** | openpyxl | Read/write .xlsx files |
| **YAML** | PyYAML | Contract serialization |
| **Deployment** | Streamlit Community Cloud | Free hosting with HTTPS |

---

## Quick Start

### Live Demo
Visit [datadoctor.streamlit.app](https://datadoctor.streamlit.app) to try it immediately.

### Local Development

```bash
# Clone the repository
git clone https://github.com/brittanyvl/DataDoctor.git
cd DataDoctor

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage Examples

### Example 1: Validate Email and Phone Columns

1. Upload your CSV with customer data
2. In Step 2, select the `email` column and add a **pattern** test with the `email` preset
3. Select the `phone` column and add a **pattern** test with the `phone_us` preset
4. Run validation and review which rows have invalid formats
5. Export the labeled data with error columns for review

### Example 2: Find Duplicate Orders

1. Upload your orders CSV
2. In Step 2, add a **dataset-level test**: `duplicate_rows`
3. Optionally specify subset columns (e.g., just `order_id`)
4. Run validation to see duplicate row indices and counts

### Example 3: Cross-Field Date Validation

1. Upload data with `order_date` and `ship_date` columns
2. In Step 2, add a **cross_field_rule** dataset test:
   - Condition: both dates are not null
   - Assertion: `order_date <= ship_date`
3. Validation flags rows where items "shipped" before being ordered

### Example 4: Create a Reusable Contract

1. Complete Steps 1-3 with your validation rules
2. In Step 5, download the YAML contract
3. Next month, upload the new data file
4. Select "Use Existing Contract" and upload your saved YAML
5. Same rules applied automatically—no reconfiguration needed

---

## Design Decisions

### Why Streamlit?

Streamlit enables rapid development of data-focused applications with Python-only code. For a portfolio project demonstrating data engineering skills, it keeps the focus on the domain logic rather than frontend infrastructure.

### Why In-Memory Processing?

Privacy-first architecture eliminates entire categories of concerns: no database security, no data retention policies, no GDPR compliance complexity. The constraint became a feature.

### Why YAML Contracts?

Users expect to save their work. Traditional approaches require user accounts and database storage. YAML contracts provide portability and persistence while maintaining zero server-side data retention. Bonus: they're version-controllable in Git.

### Why a Medical Metaphor?

"Data Check-In," "Diagnostics," and "Treatments" are more approachable than "ETL Pipeline Configuration." The metaphor guides users through an unfamiliar process with familiar concepts.

### Why 5 Steps?

Research on wizard design suggests 5-7 steps as optimal. Fewer feels rushed; more feels endless. Each step has a clear purpose and tangible output.

---

## Future Enhancements

- **API endpoint** for programmatic validation in CI/CD pipelines
- **Additional presets** for industry-specific patterns (healthcare, finance)
- **Batch processing** for multiple files with the same contract
- **Comparison mode** to diff two versions of the same dataset

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## About

Data Doctor is a portfolio project demonstrating full-stack product development with Python. It showcases:

- **Product Thinking** — Problem identification, user research, iterative design
- **UX Design** — Progressive disclosure, contextual help, clear workflows
- **Privacy by Design** — Architecture decisions driven by user trust
- **Data Engineering** — Validation patterns, transformation pipelines, schema design
- **Clean Code** — Modular architecture, comprehensive typing, separation of concerns

Built by a data professional who got tired of explaining to stakeholders why their "clean" data had 47 different spellings of "California."

---

*Found a bug? Have a feature request? [Open an issue](https://github.com/brittanyvl/DataDoctor/issues)*
