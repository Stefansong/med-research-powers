---
description: Reporting-guideline compliance check only (CONSORT/STROBE/PRISMA/TRIPOD+AI…)
argument-hint: [study type or manuscript path]
disable-model-invocation: true
---

# Check Standards

Invoke the `reporting-standards` skill with the user's study type / manuscript: $ARGUMENTS

- **Scope:** reporting-guideline compliance only — the same content as Gate 1 of the pre-submission check. It does not cover statistics, claims, figures, ethics or formal requirements.
- **Output:** item-by-item compliance report (✅ / ⚠️ / ❌ / N/A) for the matched standard.
- **Full submission gate:** `/mrp:pre-submission` (all 6 gates) — required before any submission.
