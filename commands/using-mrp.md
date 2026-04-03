# Using Med-Research-Powers

Invoke the `using-med-research-powers` meta-skill — the orchestrator for all MRP skills.

## Core Rules
1. **1% Rule** — even 1% chance a skill applies → invoke it
2. **Read before acting** — read full SKILL.md, not just description
3. **Checkpoint** — report + ask after every skill completion
4. **Hard Checkpoints** — 4 nodes require explicit user confirmation:
   - Protocol approval (study-design)
   - SAP approval (data-analysis-planning)
   - Journal confirmation (journal-selection)
   - 6-Gate pass (pre-submission-verification)
5. **User Memory** — load `.mrp-user-profile.json` on startup; create if missing

## Pipeline
```
research-question → literature-synthesis → study-design → journal-selection →
data-analysis-planning → statistical-analysis → figure-generation →
manuscript-writing → pre-submission-verification → cover-letter-writing →
submission-system-guide → [submit] → revision-strategy → responding-to-reviewers
```

## State
- `.mrp-state.json` — tracks pipeline progress (resume across sessions)
- `.mrp-user-profile.json` — user preferences and history
