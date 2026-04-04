# Manuscript Export

Invoke the `manuscript-export` skill to convert manuscript Markdown files to journal-formatted .docx for submission.

## Workflow

1. Load target journal template from `journal-templates.yaml` (font, spacing, margins, section order)
2. Collect all `manuscript/*.md` section files
3. Generate `manuscript.docx` using `scripts/export_docx.py`
4. Quality check: word count, reference count, figure count vs journal limits
5. Placeholder scan: flag any `[TBD]`, `[TODO]`, `<!-- PLACEHOLDER -->` remaining

## Journal Family Formatting

| Family | Font | Line spacing | Section order | Special |
|--------|------|-------------|---------------|---------|
| Nature | Times New Roman 12pt | 2.0 | I-R-D-M | Reporting Summary |
| Lancet | Times New Roman 12pt | 2.0 | I-M-R-D | Research in Context panel |
| JAMA | Times New Roman 11pt | 2.0 | I-M-R-D | Key Points box |
| Standard IMRaD | Times New Roman 12pt | 2.0 | I-M-R-D | — |

## Output

| File | Description |
|------|-------------|
| `manuscript/manuscript.docx` | Main submission file |
| `manuscript/supplementary.docx` | Supplementary (if applicable) |
| `export-report.md` | Format + word count QC report |

## Mandatory next step
After export → `pre-submission-verification` (6-Gate check before submission).
