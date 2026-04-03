---
name: responding-to-reviewers
description: Use when drafting point-by-point responses to peer review comments. Triggers on "审稿意见"、"revision"、"reviewer comments"、"大修"、"小修"、"回复审稿人"、"rebuttal"、"response letter".
---

# Responding to Reviewers

## Overview

系统化回复审稿人意见。每条意见都必须有明确回应，修改必须可追踪。

## When to Use

- 用户收到期刊审稿意见需要回复
- 用户需要修改论文并撰写 response letter

## When NOT to Use

- 投稿前的自我检查 → 用 `peer-review-simulation`
- 论文结构或方法问题 → 用对应的写作/分析 skill

## Workflow

### Step 1: 意见分类

对每条审稿意见分类：

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

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "这条意见不合理，直接忽略" | 每条都必须回复，忽略 = 拒稿 |
| "审稿人错了，直接说他错了" | 用证据礼貌说明，不要对抗 |
| "补充分析太多做不了" | 与编辑沟通哪些可行，不要沉默 |
| "Response letter 简短写写就行" | 详细、有理有据的回复大幅提高接收概率 |
| "改了就行不用标注位置" | 审稿人需要快速找到修改处 |

## Convergence

当以下条件全部满足时完成：
1. 每条审稿意见都有对应回复
2. 所有要求的补充分析已完成
3. 修改追踪表中所有条目状态为 ✅
4. Response letter 格式完整
5. 修改后的论文已通过 `pre-submission-verification` 再次检查

## 衔接规则

### 前置依赖
- **必须**有审稿意见（用户提供）

### 强制衔接
- 审稿人要求补充分析 → 触发 `statistical-analysis`
- 审稿人要求补充图表 → 触发 `figure-generation`
- 审稿人要求补充文献 → 触发 `literature-synthesis`
- 修改完成后 → **必须**再次触发 `pre-submission-verification`
