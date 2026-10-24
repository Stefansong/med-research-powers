---
description: Plan then run statistical analysis (data-analysis-planning → statistical-analysis)
argument-hint: [data file or research context]
disable-model-invocation: true
---

# Analyze Data

Route by whether a Statistical Analysis Plan already exists. User context: $ARGUMENTS

- **No `analysis-plan.md` in the project** → invoke the `data-analysis-planning` skill.
  Output: `analysis-plan.md`. This is mandatory checkpoint 2 — wait for the user's explicit approval of the plan before any confirmatory test runs (in auto mode the plan is written with `confirmed_by: auto`). With data in hand and no protocol, the skill's quick path asks its questions and shows the draft plan in one message, so the user confirms once; a request for descriptive output only (e.g. Table 1 by treatment group) gets a short descriptive plan. Data already collected → no `data-collection-tools` step; go on to `statistical-analysis` once the plan is approved.
- **`analysis-plan.md` has only the descriptive part (written for a Table 1) and the user now wants outcome analyses** → invoke `data-analysis-planning` again to complete the plan (new version, checkpoint 2 again); this is planned analysis, not post hoc.
- **`analysis-plan.md` already exists (approved)** → invoke the `statistical-analysis` skill.
  Output: `results-summary.md` + `analysis-log.md`. If the user asked for one result only (e.g. Table 1), stop after delivering it and just name the next step. Analyses not in the plan (e.g. a reviewer's request) are done there as post hoc, defined first in `analysis-log.md`.
- **Next step:** `figure-generation` (`/mrp:figure-generation`), then `manuscript-writing`.
