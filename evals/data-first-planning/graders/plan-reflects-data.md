---
type: llm
weight: 2
---

The project contains a synthetic data.csv with: several rows per patient (one row per stone), disguised missing codes ("未查", "/"), censored lab strings such as "<0.1", and only about 30 recurrence events for 12 candidate predictors.

PASS if the statistical analysis plan in the final reply explicitly uses at least TWO of these concrete features of this dataset to justify method choices — for example: aggregating to one row per patient or using GEE / mixed models because of multiple stones per patient; recoding "未查" and "/" to missing and planning imputation; a prespecified rule for "<0.1"; limiting the number of predictors, using penalised regression, or citing the Riley sample-size criteria because events are few.

FAIL if the plan is generic and could apply to any dataset, or if it selects predictors by looking at their association with recurrence (for example univariable p-values or "screen variables with p < 0.1") before the plan is fixed.
