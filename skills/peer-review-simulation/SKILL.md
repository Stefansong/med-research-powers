---
name: peer-review-simulation
description: Use when simulating peer review to identify problems before submission. Triggers on "帮我审一下"、"有什么问题"、"投稿前检查"、"模拟审稿"、"reviewer会怎么看".
---

# Peer Review Simulation

## Overview

模拟 4 位审稿人（含 Devil's Advocate），按 0-100 量化评分 + 严重程度分级。Critical 问题必须修复才能投稿。

## When to Use

- 投稿前预判审稿人反应
- 论文完成后自我检查

## When NOT to Use

- 收到真实审稿意见 → `revision-response`
- 检查报告规范 → `reporting-standards`

## Workflow

### Step 1: 4-Reviewer Panel

**🔀 Auto-Parallel：** 自动启动 4 个子 agent，每个扮演一位审稿人角色，并行独立评审论文（参考 `team-collaboration` skill）。评审完成后主 agent 作为 Editor 综合决策。

#### Reviewer 1 — 方法学专家
研究设计、统计方法、样本量、偏倚控制、可复现性、前提假设验证

#### Reviewer 2 — 临床/领域专家
临床意义、可操作性、外推性、替代解释、实践相关性

#### Reviewer 3 — 学术编辑
论文结构、语言质量、图表规范、参考文献、期刊匹配度

#### Reviewer 4 — Devil's Advocate（魔鬼代言人）
**专门唱反调**。职责：
- 挑战最强的结论——"如果这个发现是假阳性呢？"
- 寻找作者自己不会注意到的盲点
- 提出最不利的替代解释
- 质疑方法学中最弱的环节
- 模拟最苛刻的审稿人可能提出的问题

**Devil's Advocate 不是为了否定论文，而是帮助作者提前准备最难回答的问题。**

### Step 2: 0-100 量化评分

每位 Reviewer 对 8 个维度打分（0-100），综合分 = 加权平均。

8 维度权重与评分标准、综合分→决策映射见 `references/scoring-rubric.yaml`。打分时加载该文件逐维度判定。

### Step 3: Editor Summary（编辑综合决策）

**不是简单取平均分。** 模拟真实编辑行为：

1. **综合 4 位 Reviewer 意见**，识别共识和分歧
2. **加权 Devil's Advocate**：如果 R4 发现 Critical 问题，即使其他 3 位评分高，也应降级决策
3. **给出 Editor's Recommendation**（不等于平均分）：
   - 如果所有 Reviewer 无 Critical → 按平均分决策
   - 如果 ≥1 个 Critical 问题 → 降至 Major Revision，无论平均分
   - 如果 ≥2 位 Reviewer 建议 Reject → Reject，无论平均分
4. **预测审稿轮次**：
   - Accept / Minor → "1 轮，2 位 Reviewer 复审"
   - Major → "1-2 轮 Major Revision，原 4 位 Reviewer 复审"
   - Reject → "Desk reject 或 2-3 位 Reviewer 直接拒稿"

### Step 3b: 期刊校准（如已指定目标期刊）

同一篇论文投不同期刊，审稿标准不同。期刊层级校准表（Top/High/Mid/Entry 各档分数调整）见 `references/scoring-rubric.yaml` 的 `journal_calibration`。

如果用户指定了 Target Journal，在评分矩阵后添加：
- **Raw Score:** [未校准分数]
- **Calibrated Score (for [期刊名]):** [校准后分数]
- **Calibration note:** "[期刊名] (IF=X) 审稿标准 [高于/等于/低于] 平均水平"

### Step 4: 问题严重程度分级

每条具体意见仍按严重程度分级（Critical / Major / Minor / Suggestion）。各级别含义与处理方式见 `references/scoring-rubric.yaml` 的 `severity_grading`。

## Output

生成 `peer-review-simulation-report.md`，含 4×8 评分矩阵、4 位 Reviewer 的分级意见、Editor Summary、优先修改清单、最弱维度。完整报告模板见 `references/report-template.md`。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "模拟审稿太严了" | 真实审稿只会更严 |
| "Devil's Advocate 太刻薄" | 他提出的问题就是真实审稿人会问的 |
| "分数高就不用改了" | 60-79 分的论文大概率要 Major Revision |
| "Minor 问题先不管" | 积累的 Minor 给审稿人留下粗心印象 |
| "模拟一次就够了" | 修复后再跑一次确认分数提升 |

## Convergence

当以下条件全部满足时完成：
1. 四个 Reviewer 角度均已覆盖（含 Devil's Advocate）
2. 8 维度评分矩阵已生成
3. 所有 Critical 和 Major 问题已列出并有修改建议
4. Devil's Advocate 的挑战问题已列出防御策略
5. 修改优先级清单已生成

## Red Flags — STOP

- 存在 Critical 问题 → **阻止投稿流程**，要求先修复
- 综合分 < 50 → 建议重大修改后再提交审稿模拟
- Devil's Advocate 发现数据一致性问题 → 转交 `pre-submission-verification` Gate 3

## 衔接规则

### 前置依赖
- **必须**有基本完成的论文（`manuscript-writing`）

### 强制衔接
- 发现 Critical 问题 → 回到对应 skill 修复
- Devil's Advocate 发现 claim 问题 → 触发 `pre-submission-verification` Gate 3
- 全部修复后 → `pre-submission-verification` 做最终检查

### 可选衔接
- 需要 4 位审稿人并行评审 → `team-collaboration`（4-Reviewer Panel 并行）
- 修复后想确认得分提升 → 再次运行本 skill 复评
- 涉及报告规范缺陷 → `reporting-standards` 逐条核对
