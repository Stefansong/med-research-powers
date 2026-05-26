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
- Critical: [N] | Major: [N] | Minor: [N] | Disagreeable: [N]

## Priority Action List

| # | Reviewer | Category | Comment Summary | Difficulty | Action |
|---|----------|----------|----------------|------------|--------|
| 1 | R1 | Critical | [摘要] | High | [具体修改] |
| 2 | R2 | Critical | [摘要] | Medium | [具体修改] |
| 3 | R1 | Major | [摘要] | Low | [具体修改] |
...

## Disagreeable Items (needs careful response)
1. R2 Comment 5: [问题] → Strategy: [反驳方式]
2. R3 Comment 3: [问题] → Strategy: [反驳方式]

## New Analyses/Experiments Required
- [ ] [分析1] — estimated time: [X days]
- [ ] [分析2] — estimated time: [X days]

## Timeline
- Week 1: Critical fixes + new analyses
- Week 2: Major revisions + rewrite
- Week 3: Minor fixes + Response Letter
- Week 4: Re-run pre-submission-verification + submit
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
| Reviewer | Comment # | Type | Action | Manuscript Location | Status |
|----------|-----------|------|--------|-------------------|--------|
| R1 | 1 | 方法学 | Added sensitivity analysis | Methods ¶3, Results ¶5 | ✅ |
| R1 | 2 | 文字 | Revised wording | Discussion ¶2 | ✅ |
| R2 | 1 | 补充分析 | Added subgroup analysis | Results Table 3 | ✅ |
| R2 | 3 | 不合理 | Rebutted with evidence | Response letter only | ✅ |
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
