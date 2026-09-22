---
description: Plan then run statistical analysis (data-analysis-planning → statistical-analysis)
argument-hint: [data file or research context]
disable-model-invocation: true
---

# Analyze Data

Route by whether a Statistical Analysis Plan already exists. User context: $ARGUMENTS

- **No `analysis-plan.md` in the project** → invoke the `data-analysis-planning` skill.
  Output: `analysis-plan.md`. This is mandatory checkpoint 2 — wait for the user's explicit approval of the plan before any test runs.
- **`analysis-plan.md` already exists (approved)** → invoke the `statistical-analysis` skill.
  Output: `results-summary.md` + `analysis-log.md`.
- **Next step:** `figure-generation` (`/mrp:figure-generation`), then `manuscript-writing`.
