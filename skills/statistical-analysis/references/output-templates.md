# Statistical Analysis — Output Templates

Markdown templates for the output files produced by the `statistical-analysis` skill.
They are checklists of what each file must cover, not forms to copy: fill every bracketed
placeholder from the real data and code, write "不适用 + 理由" for rows that do not apply,
and never copy the example wording or numbers. Do not invent numbers.

---

## 1. `data-cleaning-log.md`

Written by hand while the cleaning code is written (Step 2); every action must point to the
SAP item that prescribes it and to the code that performs it.

```markdown
# Data Cleaning Log

**Date:** [日期]
**Raw data:** [原始数据文件] (N=[原始行数], vars=[变量数], sha256=[前 12 位]; 体检报告 data-profile.md)
**Cleaning code:** [analysis_script.py 或清洗脚本]（`# SAP 2.x` 各段）
**Output:** [清洗后数据文件] (N=[清洗后行数])
**Records removed:** [N] ([X]%)

## Cleaning Actions

| # | SAP item | Action | Variables | Rows affected | Code location |
|---|----------|--------|-----------|---------------|---------------|
| 1 | [SAP 2.x] | [例：把体检发现的伪装缺失写法转成缺失] | [变量] | [N] | [文件 `# SAP 2.x`] |
| 2 | [SAP 2.x] | [例：截断值按 SAP 规定的规则处理] | [变量] | [N] | [文件 `# SAP 2.x`] |
...

## Missing Data

| Variable | N Missing (incl. disguised) | % Missing | Strategy (SAP item) | Justification |
|----------|-----------------------------|-----------|---------------------|---------------|
| [var] | [N] | [X%] | [SAP 规定的策略，如完整病例 / 多重插补 m=[m] + Rubin] | [比例与机制判断依据：Little's test 或"缺失 vs 未缺失"组间比较] |
...

## Outliers

| Variable | N flagged | Method | Action (SAP item) | Justification |
|----------|-----------|--------|-------------------|---------------|
| [var] | [N] | [IQR / Z>3 / 临床合理范围] | [保留并标注 / Winsorize / 移除 + 敏感性分析] | [理由] |
...

## Data Type Corrections

| Variable | Original | Corrected | Notes |
|----------|----------|-----------|-------|
| [var] | [如 文本（含单位/截断值）] | [如 数值] | [转换规则与无法转换的条数] |
...

## Recoding and Derived Variables

| Variable | Original Coding | New Coding / Definition | SAP item | Reason |
|----------|----------------|-------------------------|----------|--------|
| [var] | [原编码] | [新编码或派生定义] | [SAP 2.x] | [理由] |
...

## Merging / Aggregation (if any)

| Step | Rows before | Rows after | Patients | Rule (SAP item) |
|------|-------------|------------|----------|-----------------|
| [如 按患者 ID 合并化验表] | [N] | [N] | [N] | [SAP 2.x] |

## Before vs After Summary

| Metric | Before | After |
|--------|--------|-------|
| Total N (rows) | [X] | [X] |
| Patients | [X] | [X] |
| Complete cases | [X] ([X%]) | [X] ([X%]) |
| Variables | [X] | [X] |
```

---

## 2. `analysis-log.md`

```markdown
# Analysis Execution Log

**Date:** [日期]
**Script:** [analysis_script.py / analysis_script.R]（环境与包版本见脚本输出开头）
**Data File:** [清洗后数据文件] (N=[N], vars=[N])
**Random seed:** [种子]

## Data Check vs SAP Section 1

| SAP assumption | Planned | Found (data-profile.md) | Minor / affects primary analysis | Action |
|----------------|---------|-------------------------|----------------------------------|--------|
| 样本量 / 患者数 | [X] | [X] | [ ] | [继续 / 已停下并由用户决定（日期）] |
| 结局事件数 | [X] | [X] | [ ] | [ ] |
| 关键变量缺失 | [X%] | [X%] | [ ] | [ ] |
| 聚类结构 | [如 每人 1 条] | [实际] | [ ] | [ ] |

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
- **Result:** stat=[X], p=[X], effect=[X] (CI: [X–X]), n=[X]
- **Interpretation:** [一句话解释]

### Analysis 2: [名称]
...

## SAP 对照表

| SAP item | Planned analysis | Code location | Result location | Status |
|----------|------------------|---------------|-----------------|--------|
| [4.1] | [计划的分析] | [文件 `# SAP 4.1`] | [results/xxx.csv 或输出行] | [已做 / 未做：理由 / 有偏离：见下表 #] |
| [5.1] | ... | ... | ... | ... |

## 自检结果

### 重跑一致性
- Command: [reproduce_check.py 的完整命令]
- Result: [一致 / 不一致 → 修改后一致]；比较文件 [N] 个；报告 [reproduce-check.md]

### 人数流（可直接画 CONSORT / STROBE 流程图）

| Step | Patients | Records | Note |
|------|----------|---------|------|
| 原始数据 | [N] | [N] | |
| 排除：[原因] | −[N] | −[N] | |
| 清洗后 | [N] | [N] | |
| 进入主要分析 | [N] | [N] | [缺失 [N]] |
| 进入 [其他分析] | [N] | [N] | |

- 前后相减是否对得上：[是 / 否 → 原因]

### 偏离
- 所有偏离已列入下表并写明理由与影响：[是 / 否]

## Deviations from Analysis Plan

| # | SAP item | Planned | Actual | Reason | Impact on results |
|---|----------|---------|--------|--------|-------------------|
| 1 | [4.x] | [计划方法] | [实际方法] | [如 前提检验不满足：Levene p=[X]] | [对结论的影响] |
| 2 | [ ] | [ ] | [ ] | [ ] | [ ] |

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

| Variable | Total (N=[X]) | Group A (n=[X]) | Group B (n=[X]) | SMD / p-value |
|----------|:---:|:---:|:---:|:---:|
| Age, mean±SD | X±X | X±X | X±X | [X] |
| Male, n(%) | X(X%) | X(X%) | X(X%) | [X] |
...

> 基线表最后一列：**RCT 不填 p 值**（随机分组后的基线差异只能来自机会，显著性检验没有意义，CONSORT 明确不推荐），改用标准化均数差 SMD（|SMD| < 0.1 视为均衡）。观察性研究可报 p 值或 SMD；倾向评分匹配后一律报 SMD。

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
