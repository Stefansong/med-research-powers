---
description: Match study type to its reporting guideline (CONSORT/STROBE/PRISMA/TRIPOD-AI...)
argument-hint: [study type or manuscript path]
---

# Reporting Standards

Match the study type to the correct reporting guideline and check item-by-item compliance.

Invoke the `reporting-standards` skill, which contains the authoritative study-type → standard mapping table and the full checklist index. Pass through the user's study type / manuscript: $ARGUMENTS

The skill selects the right standard(s) — e.g. CONSORT 2025 for RCTs (never the superseded 2010 version), STROBE for observational, PRISMA 2020 for systematic reviews, TRIPOD+AI for prediction models — and checks every item as ✅ / ⚠️ / ❌ / N/A. Zero Critical ❌ items are required to pass.

For the full MANDATORY submission gate (not just reporting compliance), use `/pre-submission`.
