---
description: Draft a medical research manuscript (invokes the manuscript-writing skill)
argument-hint: [section or manuscript context]
disable-model-invocation: true
---

# Write Manuscript

Invoke the `manuscript-writing` skill with the user's context: $ARGUMENTS

The skill owns the prerequisites, writing order and per-section rules — follow it, do not improvise.

- **Output:** `manuscript/*.md` (one file per section)
- **Next step:** `peer-review-simulation` (`/mrp:peer-review`), then `pre-submission-verification` (`/mrp:pre-submission`) before any submission.
