---
description: Choose the best target journal (scored matching + 3-tier cascade strategy)
argument-hint: [research context or artifacts]
---

# Journal Selection

Choose the best target journal for the manuscript.

Invoke the `journal-selection` skill, which contains the authoritative multi-dimension scoring rubric, 3-tier recommendation (Reach / Target / Safety), and submission-spec extraction. Pass through the user's research context: $ARGUMENTS

The skill produces `journal-selection-report.md` (ranked journals + specs + cascade strategy).

## Hard Checkpoint
The user must confirm the target journal — format specs are locked for downstream writing.

## Mandatory next step
After confirmation, proceed to `/analyze-data` or `/write-manuscript` (apply journal format).
