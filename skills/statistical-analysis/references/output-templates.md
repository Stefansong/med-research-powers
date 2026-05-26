# Statistical Analysis — Output Templates

Markdown templates for the output files produced by the `statistical-analysis` skill.
Fill in the bracketed placeholders. Do not invent numbers.

---

## 1. `data-cleaning-log.md`

```markdown
# Data Cleaning Log

**Date:** [日期]
**Input:** data.csv (N=[原始行数], vars=[变量数])
**Output:** data_clean.csv (N=[清洗后行数])
**Records removed:** [N] ([X]%)

## Missing Data

| Variable | N Missing | % Missing | Strategy | Justification |
|----------|----------|-----------|----------|---------------|
| [var1] | [N] | [X%] | Complete case | <5%, MCAR (Little's p=X) |
| [var2] | [N] | [X%] | Multiple imputation (m=20) | MAR assumed |
...

## Outliers

| Variable | N Outliers | Method | Action | Justification |
|----------|-----------|--------|--------|---------------|
| [var1] | [N] | IQR | Retained | Within clinical range |
| [var2] | [N] | Z>3 | Winsorized to P1/P99 | Biologically implausible values |
...

## Data Type Corrections

| Variable | Original Type | Corrected Type | Notes |
|----------|--------------|----------------|-------|
| [var1] | object | float64 | Removed non-numeric entries (N=[X]) |
| [var2] | string | datetime | Format: YYYY-MM-DD |
...

## Recoding

| Variable | Original Coding | New Coding | Reason |
|----------|----------------|------------|--------|
| [var1] | "Male"/"Female" | 0/1 | Required for regression |
...

## Before vs After Summary

| Metric | Before | After |
|--------|--------|-------|
| Total N | [X] | [X] |
| Complete cases | [X] ([X%]) | [X] ([X%]) |
| Variables | [X] | [X] |
```

---

## 2. `analysis-log.md`

```markdown
# Analysis Execution Log

**Date:** [日期]
**Script:** analysis_script.py
**Data File:** data_clean.csv (N=[N], vars=[N])

## Pre-Analysis Checks

| Check | Result | Action |
|-------|--------|--------|
| Missing data (%) | [变量: X%] | [处理方式] |
| Outliers detected | [N] in [变量] | [保留/移除/Winsorize，理由] |
| Normality (Shapiro-Wilk) | Group A: p=[X], Group B: p=[X] | [参数/非参数] |
| Homogeneity (Levene) | p=[X] | [t-test/Welch's] |

## Analysis Execution

### Analysis 1: [名称] (对应 analysis-plan.md Section 4.1)
- **Method:** [实际使用的方法]
- **Plan vs Actual:** [是否与 SAP 一致？不一致的原因]
- **Result:** stat=[X], p=[X], effect=[X] (CI: [X–X])
- **Interpretation:** [一句话解释]

### Analysis 2: [名称]
...

## Deviations from Analysis Plan

| # | Planned | Actual | Reason |
|---|---------|--------|--------|
| 1 | Independent t-test | Welch's t-test | Levene p=0.02, variance unequal |
| 2 | [计划方法] | [实际方法] | [原因] |

## Sensitivity Analysis Results

| Primary Result | Sensitivity Check | Consistent? |
|---------------|-------------------|-------------|
| [主要发现] | [替代方法] | ✅ / ⚠️ |
| [主要发现] | [排除异常值] | ✅ / ⚠️ |
| [主要发现] | [不同缺失处理] | ✅ / ⚠️ |

## Issues Encountered
- [如有：分析中遇到的问题和解决方式]
```

---

## 3. `results-summary.md`

```markdown
# Results Summary

**Research Question:** [一句话]
**Date:** [日期]
**Analysis Script:** analysis_script.py

## Sample Characteristics

| Variable | Total (N=[X]) | Group A (n=[X]) | Group B (n=[X]) | p-value |
|----------|:---:|:---:|:---:|:---:|
| Age, mean±SD | X±X | X±X | X±X | [X] |
| Male, n(%) | X(X%) | X(X%) | X(X%) | [X] |
...

## Primary Outcome

| Outcome | Group A | Group B | Difference | 95% CI | p-value | Effect Size | 95% CI |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| [主要结局] | X±X | X±X | X | [X–X] | [X] | d=[X] | [X–X] |

**Method:** [统计方法]
**Interpretation:** [一句话结论，区分统计显著性和临床意义]

## Secondary Outcomes

| # | Outcome | Result | p-value | Effect Size (95% CI) |
|---|---------|--------|---------|---------------------|
| 1 | [次要结局1] | [结果] | [X] | [X (X–X)] |
| 2 | [次要结局2] | [结果] | [X] | [X (X–X)] |

**Multiple comparison correction:** [方法], adjusted p-values shown

## Subgroup Analyses

| Subgroup | n | Effect Size (95% CI) | Interaction p |
|----------|---|---------------------|---------------|
| [亚组1] | [X] | [X (X–X)] | [X] |
| [亚组2] | [X] | [X (X–X)] | — |

## Sensitivity Analyses

| Analysis | Primary Result Confirmed? | Notes |
|----------|:---:|-------|
| [替代方法] | ✅ | [简要说明] |
| [排除异常值] | ✅ | [简要说明] |
| [不同缺失处理] | ⚠️ | [差异说明] |

## Key Numbers for Abstract
- Primary outcome: [一句话，含数字]
- Main effect size: [d/OR/HR = X, 95% CI X–X, p=X]
- Sample: N=[X] ([X] in Group A, [X] in Group B)

## Figures Needed
- [ ] Figure 1: [描述] → `figure-generation`
- [ ] Figure 2: [描述] → `figure-generation`
- [ ] Table 1: Baseline characteristics (above)
- [ ] Table 2: Primary and secondary outcomes (above)
```
