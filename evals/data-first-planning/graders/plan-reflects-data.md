---
type: llm
weight: 2
---

The project contains a synthetic data.csv with: several rows per patient (one row per stone), disguised missing codes ("未查", "/"), censored lab strings such as "<0.1", and 400 patients (668 stone rows) of whom only 23 had a recurrence (37 rows if one wrongly counts per stone) for 12 candidate predictors.

PASS if the statistical analysis plan in the final reply explicitly uses at least TWO of these concrete features of this dataset to justify method choices — for example: aggregating to one row per patient or using GEE / mixed models because of multiple stones per patient; recoding "未查" and "/" to missing and planning imputation; a prespecified rule for "<0.1"; counting events per patient rather than per row; limiting the number of predictors or citing the Riley sample-size criteria because events are few (offering penalised regression as the fix for too few events does not count on its own).

FAIL if the plan is generic and could apply to any dataset; if it selects predictors by looking at their association with recurrence (for example univariable p-values or "screen variables with p < 0.1") before the plan is fixed; or if it sends the user to build data-collection tools (CRF, collection forms) for these already-collected data instead of going on to the analysis once the plan is confirmed.
