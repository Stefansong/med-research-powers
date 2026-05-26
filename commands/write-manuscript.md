---
description: Draft a medical research manuscript (invokes the manuscript-writing skill)
argument-hint: [section or manuscript context]
---

# Write Manuscript

Draft a medical research paper (original research or review).

Invoke the `manuscript-writing` skill, which contains the authoritative writing order, per-section rules, and prerequisite blocks. Pass through the user's context: $ARGUMENTS

The skill blocks if prerequisites are missing (`research-question.md`, `results-summary.md`, figures/tables) and routes to the responsible skill. It enforces the writing order (Methods → Results → Introduction → Discussion → Abstract → Title) and section rules (Results = data only; Discussion introduces no new data; Introduction funnels broad → gap → aim; correct tense).

## Mandatory next step
After the manuscript is complete, you MUST trigger `/pre-submission`. No exceptions.
