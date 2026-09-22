---
description: Simulate peer review to find problems before submission (4 reviewers + scoring)
argument-hint: [manuscript path]
disable-model-invocation: true
---

# Peer Review

Invoke the `peer-review-simulation` skill on the user's manuscript: $ARGUMENTS

- **Output:** `peer-review-simulation-report.md` (per-reviewer comments, 8-dimension scores, prioritized fix list)
- **Next step:** fix Critical/Major issues, then `pre-submission-verification` (`/mrp:pre-submission`).
