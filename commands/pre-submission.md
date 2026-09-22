---
description: 6-gate pre-submission verification — mandatory checkpoint before submitting
argument-hint: [manuscript path]
disable-model-invocation: true
---

# Pre-Submission

Invoke the `pre-submission-verification` skill on the user's manuscript: $ARGUMENTS

The skill defines the 6 gates and their pass/fail criteria — apply them as written there.

- **Output:** `submission-readiness-report.md`. This is mandatory checkpoint 3 — the user must explicitly confirm the report before moving on.
- **Next step:** `manuscript-export` (`/mrp:manuscript-export`) to produce `manuscript.docx`, then `submission-preparation` (`/mrp:submission-preparation`) for the cover letter.
- For a reporting-guideline-only check (Gate 1 content), use `/mrp:check-standards`.
