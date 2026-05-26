---
description: Convert manuscript Markdown to journal-formatted .docx for submission
argument-hint: [manuscript dir or target journal]
---

# Manuscript Export

Convert manuscript Markdown files to a journal-formatted .docx.

Invoke the `manuscript-export` skill, which contains the authoritative journal-family formatting table (font, spacing, section order, special panels) and the export workflow. Pass through the user's target journal / manuscript: $ARGUMENTS

The skill loads the journal template, generates `manuscript.docx` (+ supplementary if applicable), runs the word/reference/figure-count QC, scans for leftover placeholders, and produces `export-report.md`.

## Mandatory next step
After export, run `/pre-submission` (mandatory 6-gate check before submission).
