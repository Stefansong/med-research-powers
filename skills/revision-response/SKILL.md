---
name: revision-response
description: Use when the user receives a revision decision and needs to plan strategy + draft point-by-point responses. Triggers on "怎么改"、"修改策略"、"大修"、"小修"、"revision plan"、"reviewer要求太多"、"审稿意见"、"revision"、"reviewer comments"、"回复审稿人"、"rebuttal"、"response letter".
---

# Revision Response

## Overview

收到审稿意见后的完整处理流程——从策略制定到逐条回复。Phase 1 对意见分类排序、制定修改计划；Phase 2 逐条起草回复、生成 Response Letter。

## When to Use

- 收到 Major/Minor Revision 决策，需要制定修改计划
- 审稿意见太多（>15 条），不知道从哪开始
- 某些审稿意见不合理，需要判断是否可以"respectfully disagree"
- 收到拒稿意见，考虑改投策略
- 用户收到期刊审稿意见需要回复
- 用户需要修改论文并撰写 response letter

## When NOT to Use

- 投稿前的自我检查 → `peer-review-simulation`
- 论文未投出 → 先完成投稿流程
- 论文结构或方法问题 → 用对应的写作/分析 skill

---

## Phase 1: Revision Strategy (修稿策略)

收到 Major Revision 不代表要全盘接受审稿人的所有意见。需要策略性地分类、优先排序、制定修改计划，在"尊重审稿人"和"坚守学术立场"之间找到平衡。

### Step 1: 审稿意见分类

将所有审稿意见逐条分为 4 类：

| 类别 | 定义 | 策略 |
|------|------|------|
| **Critical** | 关乎论文核心有效性（设计缺陷、统计错误、数据问题） | **必须修复**，否则一定被拒 |
| **Major** | 重要但可协商（增加分析、补充数据、修改解释） | **强烈建议修复**，但修复方式可以讨论 |
| **Minor** | 格式、表述、小的补充 | **快速修复**，展示认真态度 |
| **Disagreeable** | 审稿人要求不合理或基于误解 | **礼貌反驳**，提供证据 |

### Step 2: 修改优先级排序

按"影响力 x 难度"矩阵排序：

```
              Low Difficulty    High Difficulty
High Impact   ★★★ DO FIRST     ★★ PLAN CAREFULLY
Low Impact    ★★ DO QUICKLY    ★ CONSIDER COST
```

**排序原则：**
1. 先修 Critical（不修 = 拒稿）
2. 再修 High Impact + Low Difficulty（最大性价比）
3. 然后 Minor（展示态度）
4. 最后处理 Disagreeable（需要精心措辞）

### Step 3: Response Letter 策略

**总原则：** Collaborative, not defensive.

| 情况 | Response 策略 |
|------|-------------|
| 审稿人完全正确 | "We thank the reviewer... We have revised..." |
| 审稿人大致正确但要求过度 | "We agree with the concern... We have addressed it by [less extensive but sufficient approach]..." |
| 审稿人基于误解 | "We appreciate the comment. We may not have been clear enough. [Clarify]... We have revised the text to be more explicit." |
| 审稿人明确错误 | "We respectfully note that [factual correction with reference]. However, we have added [X] to address the underlying concern." |
| 审稿人要求不可能的实验 | "We agree this would strengthen the study. Unfortunately, [reason]. We have added this as a limitation and future direction." |

### Step 4: 修改后自检

修改完成后，自动触发以下检查：

- [ ] 每条审稿意见都有对应 response（无遗漏）
- [ ] 每个 response 都指出了具体修改位置（页码/行号）
- [ ] 修改后的论文通过 `pre-submission-verification` 重新检查
- [ ] 新增数据/分析与原有内容一致（无矛盾）
- [ ] Response Letter 语气 professional（无 defensive/aggressive 措辞）
- [ ] 修改后的字数仍在期刊限制内

### 改投策略（被拒后）

如果收到 Reject 决策：

#### 评估是否值得 Appeal
| 条件 | 建议 |
|------|------|
| 编辑同意但审稿人意见分歧大 | 可以 Appeal |
| 审稿人有明显的事实性错误 | 可以 Appeal，附上证据 |
| 审稿人全部认为方法有严重问题 | 不建议 Appeal，改投 |
| Desk reject（未送审） | 不建议 Appeal，改投 |

#### 改投流程
1. 根据审稿意见改进论文（免费的专家建议，不要浪费）
2. 回到 `journal-selection` → 选择下一梯队期刊
3. `submission-preparation` → 重写 Cover Letter（适配新期刊）
4. **可选**在 Cover Letter 中提及："This manuscript has been improved based on peer review feedback from [不点名期刊]."

### Phase 1 Output

生成 `revision-plan.md`：

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

---

## Phase 2: Point-by-Point Response (逐条回复)

系统化回复审稿人意见。每条意见都必须有明确回应，修改必须可追踪。

### Step 1: 意见细分类

对每条审稿意见进一步细分类：

| 类型 | 策略 | 示例 |
|------|------|------|
| 方法学质疑 | 感谢 → 补充分析/解释 → 展示证据 | "请解释为什么不用 X 方法" |
| 要求补充分析 | 评估可行性 → 执行或解释不可行原因 | "请增加亚组分析" |
| 文字改进 | 接受 → 修改 → 标注位置 | "第3段表述不清" |
| 参考文献 | 补充或解释已有引用充分 | "请引用 Smith 2024" |
| 不合理要求 | 礼貌解释 → 引用文献支持 | "请将队列改为 RCT" |
| 相互矛盾的意见 | 说明矛盾 → 采取平衡方案 → 请编辑裁决 | R1 要缩短 vs R2 要扩展 |

### Step 2: 逐条起草回复

对每条意见使用以下模板：

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

### Step 3: 修改追踪

生成 `revision-tracking.md`：

```markdown
| Reviewer | Comment # | Type | Action | Manuscript Location | Status |
|----------|-----------|------|--------|-------------------|--------|
| R1 | 1 | 方法学 | Added sensitivity analysis | Methods ¶3, Results ¶5 | ✅ |
| R1 | 2 | 文字 | Revised wording | Discussion ¶2 | ✅ |
| R2 | 1 | 补充分析 | Added subgroup analysis | Results Table 3 | ✅ |
| R2 | 3 | 不合理 | Rebutted with evidence | Response letter only | ✅ |
```

### Step 4: 补充分析（如需要）

审稿人常要求的补充分析：
- 亚组分析 → 触发 `statistical-analysis`
- 敏感性分析 → 触发 `statistical-analysis`
- 补充图表 → 触发 `figure-generation`
- 额外文献 → 触发 `literature-synthesis`

### Step 5: 生成 Response Letter

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

---

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "审稿人的每个要求都必须接受" | 可以 respectfully disagree，但需要证据 |
| "改完直接交，不用再检查" | 修改可能引入新的不一致 |
| "Response Letter 越短越好" | 太短显得不认真；太长显得 defensive |
| "被拒了这论文没希望了" | 大多数论文被拒后改投成功发表 |
| "审稿意见不合理就不理" | 即使不同意，也必须 respond |
| "拖到最后一天再交" | 提前 3-5 天交，留出检查时间 |
| "这条意见不合理，直接忽略" | 每条都必须回复，忽略 = 拒稿 |
| "审稿人错了，直接说他错了" | 用证据礼貌说明，不要对抗 |
| "补充分析太多做不了" | 与编辑沟通哪些可行，不要沉默 |
| "Response letter 简短写写就行" | 详细、有理有据的回复大幅提高接收概率 |
| "改了就行不用标注位置" | 审稿人需要快速找到修改处 |

## Convergence

当以下条件全部满足时完成：
1. 所有审稿意见已分类和排序（Phase 1）
2. 每条意见有明确的 action plan（Phase 1）
3. 修改时间表已制定（Phase 1）
4. Disagreeable items 有防御策略（Phase 1）
5. 每条审稿意见都有对应回复（Phase 2）
6. 所有要求的补充分析已完成（Phase 2）
7. 修改追踪表中所有条目状态为 ✅（Phase 2）
8. Response letter 格式完整（Phase 2）
9. 修改后的论文已通过 `pre-submission-verification` 再次检查

## 衔接规则

### 前置依赖
- **必须**有收到的审稿意见（用户提供）

### 强制衔接
- 审稿人要求补充分析 → 触发 `statistical-analysis`
- 审稿人要求补充图表 → 触发 `figure-generation`
- 审稿人要求补充文献 → 触发 `literature-synthesis`
- 修改完成后 → **必须**再次触发 `pre-submission-verification`

### 被动触发
- 收到 Major/Minor Revision → 自动触发
- 收到 Reject → 触发改投策略部分

### 可选衔接
- 改投 → `journal-selection`（重新选刊）
- 改投 → `submission-preparation`（重写 Cover Letter + 投稿）
