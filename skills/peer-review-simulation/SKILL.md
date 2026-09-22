---
name: peer-review-simulation
description: Use when simulating peer review of a finished manuscript before the pre-submission check. Triggers on "帮我审一下"、"模拟审稿"、"reviewer会怎么看"、"审稿人会问什么"、"peer review".
---

# Peer Review Simulation

## Overview

模拟 4 位审稿人（含 Devil's Advocate），按 0-100 量化评分 + 严重程度分级，由主代理扮演编辑综合决策。
Critical 问题必须修复后才进入 `pre-submission-verification`。

## When to Use

- `manuscript-writing` 完成后 → **自动进入**（主线：manuscript-writing → 本 skill → pre-submission-verification）
- 用户想预判审稿人反应、准备最难回答的问题
- 修复后想确认得分是否提升（再跑一次）

## When NOT to Use

- 收到真实审稿意见 → `revision-response`
- 只想查报告规范 → `reporting-standards`
- 论文还没写完（缺章节）→ 先 `manuscript-writing`

## Workflow

### Step 1: 4-Reviewer Panel（并行）

用子代理工具（**Agent**，旧名 Task 仍可用作别名）在同一条消息里并行派发 4 位审稿人，每个带聚焦的
prompt（角色、读取 `manuscript/*.md`、按本文件 8 维度打分、输出文件名）。派发模板见
`${CLAUDE_PLUGIN_ROOT}/skills/team-collaboration/references/parallel-scenarios.md` 场景 2。审稿人只写各自的
`review-methods.md` / `review-clinical.md` / `review-editor.md` / `review-devil.md`，不改稿件。
评审完成后主代理作为 Editor 综合决策。

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

每位 Reviewer 对 8 个维度打分（0-100），综合分 = 加权平均，并按分数给出自己的
Recommendation（Accept / Minor / Major / Reject）。

8 维度权重与评分标准、综合分 → 决策映射见 `references/scoring-rubric.yaml`（唯一权威表）：
80-100 Accept/Minor · 65-79 Minor · 50-64 Major · 30-49 Major (risky) · 0-29 Reject。
打分时加载该文件逐维度判定。

### Step 3: Editor Summary（编辑综合决策）

**不是简单取平均分。** 模拟真实编辑行为：

1. **综合 4 位 Reviewer 意见**，识别共识和分歧
2. **加权 Devil's Advocate**：如果 R4 发现 Critical 问题，即使其他 3 位评分高，也应降级决策
3. **给出 Editor's Recommendation**（不等于平均分）：
   - 所有 Reviewer 无 Critical → 按 `scoring-rubric.yaml` 的分数映射决策
   - ≥1 个 Critical 问题 → 至少 Major Revision，无论平均分
   - ≥2 位 Reviewer 建议 Reject → Reject，无论平均分
4. **预测审稿轮次**：
   - Accept / Minor → "1 轮，2 位 Reviewer 复审"
   - Major → "1-2 轮 Major Revision，原 4 位 Reviewer 复审"
   - Reject → "Desk reject 或 2-3 位 Reviewer 直接拒稿"

### Step 3b: 期刊校准（如已指定目标期刊）

同一篇论文投不同期刊，审稿标准不同。校准按期刊**在学科内的位置**分档（综合顶刊 / 专科 Top /
主流 / 入门），**不用绝对 IF**——BJU International、World J Urol、Urology 这类专科主流期刊不是
"入门刊"。档位从 `journal-selection-report.md` 的梯队、JCR/中科院分区或本专科排名判断；引用 IF
数值时标年份并建议 WebSearch 复核。各档调整幅度见 `references/scoring-rubric.yaml` 的
`journal_calibration`。

如果用户指定了 Target Journal，在评分矩阵后添加：
- **Raw Score:** [未校准分数]
- **Calibrated Score (for [期刊名], [档位]):** [校准后分数]
- **Calibration note:** "[期刊名] 属于 [档位]，审稿标准 [高于/等于/低于] 平均水平"

### Step 4: 问题严重程度分级

每条具体意见仍按严重程度分级（Critical / Major / Minor / Suggestion）。各级别含义与处理方式见
`references/scoring-rubric.yaml` 的 `severity_grading`。

### Step 5: 收尾

1. 生成 `peer-review-simulation-report.md`（模板见 `references/report-template.md`）。
2. 输出 3–5 行摘要（综合分、Editor 决策、Critical 数、最弱维度、下一步）——轻量确认，不等待。
3. 更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：
   `completed_skills` 追加 peer-review-simulation 及产物、`next_step` 设为 pre-submission-verification）。
4. 0 Critical → 进入 `pre-submission-verification`；≥1 Critical → 回对应 skill 修复后再跑一次本 skill。

## Output

生成 `peer-review-simulation-report.md`，含 4×8 评分矩阵（每位 Reviewer 一行 Recommendation）、
4 位 Reviewer 的分级意见、Editor Summary（Raw / Calibrated Score）、优先修改清单、最弱维度、下一步。
完整报告模板见 `references/report-template.md`。4 位审稿人各自的 `review-*.md` 是中间文件。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "模拟审稿太严了" | 真实审稿只会更严 |
| "Devil's Advocate 太刻薄" | 他提出的问题就是真实审稿人会问的 |
| "分数高就不用改了" | 50-64 分 = Major Revision，65-79 分也只是 Minor；≥80 才可能直接接收 |
| "Minor 问题先不管" | 积累的 Minor 给审稿人留下粗心印象 |
| "模拟一次就够了" | 修复后再跑一次确认分数提升 |
| "IF 低的期刊就是入门刊" | 校准看期刊在本专科的位置，不看绝对 IF |
| "4 位审稿人一个接一个跑" | 4 位互不依赖，应并行派发 |

## Convergence

当以下条件全部满足时完成：
1. 四个 Reviewer 角度均已覆盖（含 Devil's Advocate），每位给出 Recommendation
2. 8 维度评分矩阵已生成
3. 所有 Critical 和 Major 问题已列出并有修改建议
4. Devil's Advocate 的挑战问题已列出防御策略
5. 修改优先级清单已生成，`.mrp-state.json` 已更新

## Red Flags — STOP

- 存在 Critical 问题 → **不进入 `pre-submission-verification`**，要求先修复
- 综合分 < 50 → 建议重大修改后再提交审稿模拟
- Devil's Advocate 发现数据一致性问题 → 转交 `pre-submission-verification` Gate 3
- 审稿人子代理直接改了 `manuscript/` → 停止，审稿人只写各自的 review 文件

## 衔接规则

### 前置依赖
- **必须**有完成的论文（`manuscript/*.md`，来自 `manuscript-writing`）

### 强制衔接
- 前接 `manuscript-writing`；后接 `pre-submission-verification`（0 Critical 后进入）
- 发现 Critical 问题 → 回到对应 skill 修复（方法/统计 → `statistical-analysis`，写作 → `manuscript-writing`，图表 → `figure-generation`）
- Devil's Advocate 发现 claim 问题 → 交 `pre-submission-verification` Gate 3 处理
- 4-Reviewer Panel 用 Agent 并行派发，模板见 `team-collaboration`
- 完成后 → 更新 `.mrp-state.json`

### 可选衔接
- 修复后想确认得分提升 → 再次运行本 skill 复评
- 涉及报告规范缺陷 → `reporting-standards` 逐条核对
