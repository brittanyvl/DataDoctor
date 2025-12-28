# Data Doctor  
## Branding Guidelines & Visual Identity

**Product name:** Data Doctor  
**Tagline:** *Spreadsheet diagnostics you can trust.*

---

## 1. Brand Purpose

Data Doctor is a friendly, professional data diagnostics application designed for business users who work with spreadsheet-style data.

The product helps users:
- understand what is wrong with their data,
- decide how to fix it,
- and communicate data issues clearly to others.

The brand must feel calm, trustworthy, clear, and non-technical.

---

## 2. Target Audience

Primary users:
- Supply chain professionals
- Finance and accounting users
- Marketing operations
- Admin and operations roles
- Excel power users

Design assumption:
Users are comfortable with spreadsheets but are not developers or data engineers.

---

## 3. Brand Personality

Data Doctor should feel:
- Friendly
- Professional
- Calm
- Reassuring
- Clear

It must never feel:
- Intimidating
- Academic
- Condescending
- Overly playful
- Like an “AI magic” tool

---

## 4. Voice & Tone Guidelines

### 4.1 Tone Rules
- Use plain English
- Prefer explanations over labels
- Avoid technical jargon unless explained via tooltip or glossary
- Use neutral, non-judgmental language

### 4.2 Copy Examples

Preferred:
- “We found 12 rows with missing values.”
- “This is common in spreadsheet data.”
- “You can choose how to handle this issue.”

Avoid:
- “Validation failed.”
- “Schema violation detected.”
- “Execution error.”

---

## 5. Medical-Themed Language (Light Use Only)

Allowed (syntactical guidance only):
- Doctor
- Diagnostics
- Diagnosis
- Checkup
- Findings
- Treatment (only when user opts in)
- Summary
- Results

Disallowed:
- Surgery
- Emergency
- Critical condition
- ICU
- Heavy or cartoon medical imagery

Rule:
If it sounds inappropriate in a professional email, do not use it.

---

## 6. Visual Identity Overview

### 6.1 Design Aesthetic
- Clean
- Light
- Modern
- Calm
- High readability

Think:
A modern clinic that works with spreadsheets.

---

## 7. Typography (Required)

### 7.1 Primary Font (UI + App)

**Inter**

Usage:
- App UI
- Headings
- Body text
- Buttons
- Tables
- Sidebar

Rationale:
- Highly readable
- Neutral and professional
- Optimized for screens
- Widely supported

Fallback stack:
Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif

### 7.2 Monospace Font (Code / YAML / IDs)

**JetBrains Mono**

Usage:
- YAML contracts
- Code blocks
- Identifiers
- Sample values

Fallback stack:
JetBrains Mono, SFMono-Regular, Consolas, "Liberation Mono", monospace

---

## 8. Color Palette (Hex Codes)

### 8.1 Primary Brand Colors

Primary Green (Health / Success):
#2F855A

Usage:
- “Healthy” indicators
- Passed checks
- Success badges
- Positive summaries

Do NOT:
- Use as a background fill for large areas
- Use for primary buttons everywhere

---

Primary Slate (Text / Structure):
#2D3748

Usage:
- Headings
- Primary text
- Navigation elements
- Sidebar titles

---

### 8.2 Secondary & Support Colors

Secondary Gray (UI Backgrounds / Borders):
#EDF2F7

Usage:
- App background sections
- Card backgrounds
- Table striping
- Dividers

---

Muted Amber (Warnings / Needs Attention):
#D69E2E

Usage:
- Warnings
- “Needs attention” indicators
- Non-blocking issues

---

Restrained Red (Errors / Failures):
#C53030

Usage:
- Blocking issues
- Errors that require user action

Rules:
- Use sparingly
- Always pair with explanatory text
- Never rely on color alone

---

### 8.3 Neutral Colors

White:
#FFFFFF

Usage:
- Main backgrounds
- HTML report background

Light Gray:
#F7FAFC

Usage:
- Alternate table rows
- Subtle section separation

---

## 9. Color Usage Rules (Non-Negotiable)

- Green = healthy / passed
- Amber = needs attention
- Red = issue found
- Never use color alone to communicate meaning
- Pair all color indicators with text labels
- Maintain consistent color meaning across app and HTML report

---

## 10. Application UI Branding Rules (Streamlit)

### 10.1 App Header
Must display:
- Data Doctor
- Tagline: “Spreadsheet diagnostics you can trust.”

### 10.2 Navigation
- Step-based progression
- Sidebar used for:
  - navigation
  - high-level status summaries
  - help and glossary access

### 10.3 Buttons
- Action-oriented language
- One primary action per page

Preferred:
- “Run diagnostics”
- “Review findings”
- “Download report”

Avoid:
- “Submit”
- “Execute”
- “Apply pipeline”

---

## 11. Tooltips & Help

- Any non-obvious data term must include an info icon
- Tooltips must:
  - use plain English
  - match glossary definitions exactly
  - avoid technical shorthand

Glossary wording must not be rephrased in UI copy.

---

## 12. HTML Report Branding (Critical)

### 12.1 Report Purpose
- Clear communication of data issues
- Professional and forwardable
- Subtle promotion of Data Doctor

### 12.2 Required Report Elements
- Title: “Data Doctor – Data Quality Report”
- Tagline: “Spreadsheet diagnostics you can trust.”
- Date/time generated
- Summary section at top
- Clear section headers
- Readable tables (print-friendly)

### 12.3 Attribution
The report must include:

“Generated by Data Doctor — Spreadsheet diagnostics you can trust.”

Include a visible but non-promotional link back to the app.

---

## 13. Consistency Rules

- Same terminology everywhere (app, report, tooltips, glossary)
- Same phrasing for the same actions everywhere
- Same color meanings everywhere
- Same fonts everywhere
- No ad-hoc styling exceptions

---

## 14. Brand Guardrails

Do NOT:
- Use AI-first language
- Over-automate or oversell
- Use fear-based messaging
- Over-medicalize visuals

The product must feel:
- Safe
- Trustworthy
- Calm
- Designed for real business users

---

## 15. Internal Brand Statement

Data Doctor is a calm, professional spreadsheet diagnostics tool that helps non-technical business users understand, trust, and improve their data—clearly, safely, and without intimidation.

---

