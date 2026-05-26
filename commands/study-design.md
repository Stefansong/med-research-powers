---
description: Design a research protocol for any study type (clinical/basic/AI/qualitative/survey)
argument-hint: [research description]
---

# Study Design

Unified entry point for designing a study protocol across all research types.

Invoke the `study-design` skill, which contains the authoritative type router (clinical, basic science, AI/ML, qualitative, survey), the core steps including MANDATORY sample-size/power analysis, and downstream handoffs. Just describe the research and pass it through: $ARGUMENTS

The skill produces `study-protocol.md`.

## Hard Checkpoint
The user must confirm the protocol — research type and primary outcome are LOCKED after confirmation.

## Mandatory next step
After confirmation, proceed to `/journal-selection`, `/data-collection-tools`, and `/analyze-data` (planning).
