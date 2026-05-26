---
description: Orchestrator for all MRP skills — routing rules, pipeline, and checkpoints
---

# Using Med-Research-Powers

The orchestrator entry point for the whole med-research-powers pipeline.

Invoke the `using-med-research-powers` meta-skill, which contains the authoritative routing rules, full skill pipeline, hard-checkpoint nodes, and state/memory files. Pass through any user context: $ARGUMENTS

Key points the skill enforces: the 1% rule (even a 1% chance a skill applies → invoke it), read full SKILL.md before acting, report + ask after every skill, and 4 hard checkpoints requiring explicit user confirmation — protocol approval (study-design), SAP approval (data-analysis-planning), journal confirmation (journal-selection), and 6-gate pass (pre-submission-verification). State persists in `.mrp-state.json`; user preferences in `.mrp-user-profile.json`.
