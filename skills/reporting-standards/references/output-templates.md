# Reporting Standards — Output Templates

Loaded on demand by reporting-standards Step 4. Two files are produced per check.

## 1. `reporting-checklist-<standard>.md`（给期刊，随稿提交）

文件名中的 `<standard>` 用 standards-index.yaml 的 `id`（如 `reporting-checklist-consort-2025.md`、
`reporting-checklist-strobe.md`）。一稿用了主规范 + 扩展（如 CONSORT 2025 + CONSORT-AI）时各出一份。

```markdown
# <Standard name> Checklist

**Manuscript:** [题目]
**Standard:** <name> (<reference>)
**Checked on:** [日期]

| Item | Topic | Checklist item | Reported on page / section | Status |
|------|-------|----------------|----------------------------|--------|
| 1a | Title and structured abstract | Identification as a randomised trial | p.1, Title | ✅ |
| 2 | Trial registration | Name of trial registry, identifying number ... | p.3, Methods ¶1 | ✅ |
| 8 | Patient and public involvement | Details of patient or public involvement ... | — | ❌ |
| 12b | Eligibility criteria | If applicable, eligibility criteria for sites ... | — | N/A (single-site, no site criteria) |
| ... | ... | ... | ... | ... |

Status legend: ✅ reported · ⚠️ partially reported · ❌ not reported · N/A not applicable (reason given)
```

规则：
- 每一行都要有位置（页码 + 章节/段落），期刊编辑按这一列核对；没有位置的 ✅ 不算 ✅。
- N/A 必须写原因。
- 逐条 `text` 直接取自 checklist YAML，不要改写。

## 2. `reporting-compliance-report.md`（给作者）

```markdown
# Reporting Compliance Report

**Manuscript:** [题目]
**Study type:** [RCT / cohort / diagnostic accuracy / prediction model / ...]
**Standard(s):** <name> [+ extensions]
**Checklist source:** references/checklists/<file>.yaml（逐条核对）
                     / 无本地 checklist —— 按 <reference> 的官方 checklist 人工核对
**Date:** [日期]

## Summary

| | Count |
|---|---|
| Total rows checked | N |
| ✅ Reported | N |
| ⚠️ Partial | N |
| ❌ Not reported | N |
| ❌ on **critical** items | N  ← Gate 1 passes only when this is 0 |
| N/A | N |

**Gate 1 verdict:** PASS / FAIL（critical ❌ = N）

## Critical ❌ (must fix before submission)

| Item | Topic | What is missing | Where to add | Fix |
|------|-------|-----------------|--------------|-----|
| 16a | Sample size | No sample size calculation in Methods | Methods, "Sample size" | 补充假设（效应量、α、power、脱落率）与计算结果 |

## Other ❌ / ⚠️ (fix recommended)

| Item | Topic | Status | What is missing | Fix |
|------|-------|--------|-----------------|-----|
| 8 | Patient and public involvement | ❌ | Not mentioned | 加一句 "No patient or public involvement" 或描述实际参与 |

## N/A items and reasons

- 12b — single-site trial, no site-level eligibility criteria

## Next step

- critical ❌ > 0 → 回 `manuscript-writing` 修改对应章节，改完重跑本 skill
- critical ❌ = 0 → 把 `reporting-checklist-<standard>.md` 交给 `pre-submission-verification` Gate 1
```

## 3. 无本地 checklist 时的报告写法

standards-index.yaml 里没有 `file:` 字段的规范（如 CONSORT-AI、RECORD、CHEERS、CROSS），不要凭记忆
编造条目文本。`reporting-compliance-report.md` 的 Checklist source 写"无本地 checklist"，Summary 只
给出按论文章节的粗检（题目/摘要/方法/结果/讨论各缺什么），并在 Next step 写明：

> 请从 <reference> / EQUATOR Network (https://www.equator-network.org/) 下载官方 checklist，
> 逐条人工核对后再进入 Gate 1；本报告不构成 Gate 1 通过依据。
