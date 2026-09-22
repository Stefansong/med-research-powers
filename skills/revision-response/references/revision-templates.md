# Revision Response Templates

Loaded on demand by revision-response. Keep judgment/reasoning in SKILL.md;
this file holds the static output-file templates.

NOTE: cover-letter / cascade-rewrite templates are NOT here. When改投, defer to
`submission-preparation` (owner of cover-letter rewrite mechanics).

## `revision-plan.md`（Phase 1 Output）

```markdown
# Revision Plan

**Journal:** [期刊名]
**Decision:** Major Revision / Minor Revision
**Deadline:** [修改截止日期]
**Date:** [日期]

## Summary
- Total comments: [N]
- Severity — Critical: [N] | Major: [N] | Minor: [N]
- Stance — Accept: [N] | Partial: [N] | Rebut: [N]

## Priority Action List

| # | Reviewer | Comment # | Severity | Stance | Sub-type | Comment Summary | Difficulty | Priority | Action |
|---|----------|-----------|----------|--------|----------|-----------------|------------|----------|--------|
| 1 | R1 | 2 | Critical | Accept | 方法学质疑 | [摘要] | High | P1 | [具体修改] |
| 2 | R2 | 1 | Critical | Partial | 要求补充分析 | [摘要] | Medium | P1 | [post hoc 分析 + 记入 analysis-log.md] |
| 3 | R1 | 4 | Major | Accept | 文字改进 | [摘要] | Low | P2 | [具体修改] |
| 4 | R2 | 5 | Minor | Rebut | 不合理要求 | [摘要] | Low | P3 | [礼貌说明 + 引用] |
...

## Rebut Items (needs careful response)
1. R2 Comment 5 (Minor / Rebut): [问题] → Strategy: [证据 + 措辞]
2. R3 Comment 3 (Major / Rebut): [问题] → Strategy: [证据 + 措辞]

## New Analyses/Experiments Required
- [ ] [分析1] — post hoc / exploratory，记入 analysis-log.md SAP 偏差 — estimated time: [X days]
- [ ] [分析2] — estimated time: [X days]

## Timeline
- Week 1: P1 (all Critical) + new analyses
- Week 2: P2 Major revisions + rewrite
- Week 3: P3/P4 Minor fixes + Response Letter (Rebut items last, with care)
- Week 4: Re-run pre-submission-verification → manuscript-export → resubmit
```

## Per-comment 回复模板（Phase 2 Step 2）

```
## Reviewer [X], Comment [Y]

**Original comment:**
> [引用审稿人原文]

**Response:**
[回应内容——感谢/解释/同意/礼貌反驳]

**Changes made:**
[具体修改描述]
- Page X, Line Y: [修改内容]
- Page X, Paragraph Z: [新增内容]
（或 "No changes made — see explanation above."）
```

## `revision-tracking.md`（Phase 2 Step 3）

```markdown
| Reviewer | Comment # | Severity | Stance | Sub-type | Action | Manuscript Location | Status |
|----------|-----------|----------|--------|----------|--------|---------------------|--------|
| R1 | 1 | Critical | Accept | 方法学质疑 | Added sensitivity analysis | Methods ¶3, Results ¶5 | ✅ |
| R1 | 2 | Minor | Accept | 文字改进 | Revised wording | Discussion ¶2 | ✅ |
| R2 | 1 | Major | Partial | 要求补充分析 | Added post hoc subgroup analysis (labelled exploratory; analysis-log.md) | Results Table 3, Methods ¶6 | ✅ |
| R2 | 3 | Minor | Rebut | 不合理要求 | Rebutted with evidence | Response letter only | ✅ |
```

## Response Letter 模板（Phase 2 Step 5）

```markdown
# Response to Reviewers

Dear Editor,

Thank you for the opportunity to revise our manuscript [ID]. We appreciate the constructive comments from the reviewers. Below is our point-by-point response. All changes in the revised manuscript are highlighted in [red/track changes].

---

## Response to Reviewer 1

[逐条回复]

## Response to Reviewer 2

[逐条回复]

## Response to Reviewer 3 (if applicable)

[逐条回复]

---

## Summary of Changes

[主要修改的概括性描述]
```
