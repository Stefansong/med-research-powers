---
description: Reporting-guideline compliance check against the manuscript's required standard
argument-hint: [study type or manuscript path]
---

# Check Reporting Standards

A focused reporting-guideline compliance check — confirms the manuscript meets its required reporting standard (CONSORT/STROBE/PRISMA/TRIPOD-AI...).

Invoke the `reporting-standards` skill, which contains the authoritative study-type → standard mapping table and full checklists. Pass through the user's study type / manuscript: $ARGUMENTS

The skill identifies the study type, selects the right standard(s) (always CONSORT 2025, never the superseded 2010), and checks every item as ✅ / ⚠️ / ❌ / N/A. Zero Critical ❌ items are required to pass.

## Scope note
This is a lighter, reporting-standards-only check. It is **not** the full submission gate. The complete MANDATORY pre-submission check is the 6-gate verification in `/pre-submission` (reporting standards is Gate 1 of 6). Run `/pre-submission` before submitting.
