---
description: MANDATORY 6-gate pre-submission verification — all gates must pass to submit
argument-hint: [manuscript path]
---

# Pre-Submission Verification

The canonical **MANDATORY** check before any manuscript submission. This is the authoritative 6-gate verification — it cannot be skipped.

Invoke the `pre-submission-verification` skill, which contains the authoritative 6-gate table and per-gate pass/fail criteria. Pass through the user's manuscript: $ARGUMENTS

The 6 gates (all must pass): (1) Reporting standards, (2) Statistical completeness, (3) Claim verification, (4) Figure quality, (5) Ethics compliance, (6) Formal requirements. Any gate FAIL blocks submission and routes back to the responsible skill.

## Hard Checkpoint
The user must explicitly confirm all 6 gates pass before proceeding to cover letter and submission. The skill produces `submission-readiness-report.md` (pass/fail per gate + fix list).

For a lighter reporting-guideline-only check, use `/check-standards`. For the next step after passing, use `/submission-preparation`.
