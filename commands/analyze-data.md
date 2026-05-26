---
description: Plan then run statistical analysis (data-analysis-planning → statistical-analysis)
argument-hint: [data file or research context]
---

# Data Analysis

This command invokes TWO skills in sequence: first the `data-analysis-planning` skill, then the `statistical-analysis` skill. Pass through the user's data / context: $ARGUMENTS

1. Invoke the `data-analysis-planning` skill to produce `analysis-plan.md` (data overview, preprocessing, primary method + justification, sensitivity analyses). The user must confirm the plan before execution.
2. Then invoke the `statistical-analysis` skill to execute against the confirmed plan, test assumptions before any parametric test, report statistic + p-value + effect size + 95% CI per test, and produce `results-summary.md`.

These skills hold the authoritative blocking rules (no plan → no execution; no assumption test → no parametric test; no effect size → no results report).

## Mandatory next step
After completion, trigger `/figure-generation` for visualization.
