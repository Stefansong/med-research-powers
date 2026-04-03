# Data Analysis

Invoke `data-analysis-planning` first, then `statistical-analysis` to execute.

## Workflow

### Phase 1: Plan (data-analysis-planning)
1. Document data overview (source, sample size, variables)
2. Define preprocessing strategy (missing data, outliers, transformations)
3. Specify primary analysis method with justification
4. Plan sensitivity analyses
5. **Generate `analysis-plan.md`** — user must confirm before execution

### Phase 2: Execute (statistical-analysis)
1. Load data and verify against plan
2. **Test assumptions BEFORE running any parametric test** (use `scripts/assumption_tests.py` if available)
3. Execute each planned analysis, generating reproducible Python/R scripts
4. Report: statistic + p-value + effect size + 95% CI for every test
5. Run sensitivity analyses
6. **Generate `results-summary.md`**

## Blocking rules

- **No analysis-plan.md → block execution.** Plan first.
- **No assumption testing → block parametric tests.** Test first.
- **No effect sizes → block results reporting.** p-value alone is insufficient.

## Mandatory next step

After completion → **must** trigger `figure-generation` for data visualization.
