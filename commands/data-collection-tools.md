---
description: Generate data collection instruments, scripts, and templates from a study protocol
argument-hint: [research type or study-protocol.md]
---

# Data Collection Tools

Generate data collection instruments, scripts, and templates from a confirmed study protocol.

Invoke the `data-collection-tools` skill, which contains the authoritative research-type → tools router (AI benchmark, AI diagnostic, clinical RCT/cohort, basic science, systematic review) and the output directory structure. Pass through the user's research type / protocol: $ARGUMENTS

## Prerequisite
Requires `study-protocol.md` — run `/study-design` first.

## Mandatory next step
After tools are ready and data collected, proceed to `/analyze-data`.
