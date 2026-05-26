---
description: Simulate peer review to find problems before submission (4 reviewers + scoring)
argument-hint: [manuscript path]
---

# Peer Review Simulation

Stress-test the manuscript before submission by simulating reviewers.

Invoke the `peer-review-simulation` skill, which contains the authoritative 4-reviewer panel (Methodologist, Clinical Expert, Editor, Devil's Advocate), the 8-dimension 0-100 scoring rubric, decision thresholds, and severity tagging. Pass through the user's manuscript: $ARGUMENTS

The skill produces `peer-review-simulation-report.md` (scoring matrix + per-reviewer comments + priority fix list).

## Blocking rule
Any Critical issue blocks submission — fix and re-run. Devil's Advocate claim issues route to `/pre-submission` (Gate 3, claim verification).
