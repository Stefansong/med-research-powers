---
name: revision-response
description: Use when the user receives a journal revision or reject decision. Triggers on "审稿意见怎么改"、"修改策略"、"大修"、"小修"、"审稿意见"、"revision"、"reviewer comments"、"回复审稿人"、"rebuttal"、"response letter".
---

# Revision Response

## Overview

收到审稿意见后的完整处理流程——从策略制定到逐条回复。Phase 1 对意见分类排序、制定修改计划；
Phase 2 逐条起草回复、生成 Response Letter。修回稿仍要过 `pre-submission-verification` 6 Gate。

## When to Use

- 收到 Major/Minor Revision 决策，需要制定修改计划
- 审稿意见太多（>15 条），不知道从哪开始
- 某些审稿意见不合理，需要判断是否可以"respectfully disagree"
- 收到拒稿意见，考虑 Appeal 还是改投
- 用户需要修改论文并撰写 response letter

## When NOT to Use

- 投稿前的自我检查 → `peer-review-simulation`
- 论文未投出 → 先走主线（`pre-submission-verification` → `manuscript-export` → `submission-preparation`）
- 论文结构或方法问题 → 用对应的写作/分析 skill

## Workflow

### Phase 1: Revision Strategy（修稿策略）

收到 Major Revision 不代表要全盘接受审稿人的所有意见。需要策略性地分类、优先排序、制定修改计划，
在"尊重审稿人"和"坚守学术立场"之间找到平衡。

#### Step 1: 审稿意见分类（两个独立维度）

每条意见同时打两个标签：

- **Severity（严重度）**：Critical（关乎核心有效性，不修 = 拒稿）/ Major（重要但不动摇核心）/ Minor（格式、表述）
- **Stance（立场）**：Accept（照改）/ Partial（部分做到，说明为何足够）/ Rebut（礼貌反驳，给证据）

严重度和是否反驳互不相关：Minor 的意见也可能要 Rebut，Critical 的意见也可能 Partial。
完整定义见 `references/revision-strategy.yaml`（`comment_classification`）。

#### Step 2: 修改优先级排序

按 Severity × Difficulty 矩阵分 4 级：P1 所有 Critical（高难度的最先启动）→ P2 低难度 Major →
P3 高难度 Major 和低难度 Minor → P4 高难度 Minor；Rebut 的意见不论等级都留出措辞时间。
完整矩阵见 `references/revision-strategy.yaml`（`priority_matrix` / `priority_levels`）。

#### Step 3: Response Letter 策略

**总原则：** Collaborative, not defensive. 即使审稿人明确错误，也用证据礼貌说明，绝不对抗；
要求不可能的实验时承认价值、说明原因、写入 limitation/future direction。按 Stance 选择措辞模板，
见 `references/revision-strategy.yaml`（`response_strategy`）。

#### Step 4: 改投策略（被拒后）——只做决策

本 skill 只负责**改投决策**：是 Appeal 还是改投。Cover-letter 重写/cascade-rewrite 的具体
机制属于 `submission-preparation`（owner），不在此重复。

- 评估是否值得 Appeal：决定信显示意见分歧且编辑倾向正面 / 审稿人事实错误是拒稿主因 → 可 Appeal；
  方法被全盘否定 / desk reject / "decision is final" → 改投。判断表见
  `references/revision-strategy.yaml`（`appeal_decision`）。
- 决定改投后：根据审稿意见改进论文（免费的专家建议）→ 回 `journal-selection` 选下一梯队 →
  `submission-preparation` 重写 Cover Letter。**本 skill 不重述 cover-letter 模板。**

#### Phase 1 Output

生成 `revision-plan.md`（Summary + Priority Action List（Severity / Stance / Sub-type / Priority 列）+
Rebut Items + New Analyses + Timeline）。完整模板见 `references/revision-templates.md`。

### Phase 2: Point-by-Point Response（逐条回复）

系统化回复审稿人意见。每条意见都必须有明确回应，修改必须可追踪。

#### Step 1: 意见细分类（Sub-type = 应对策略）

对每条意见再标一个 sub_type（方法学质疑 / 要求补充分析 / 文字改进 / 参考文献 / 不合理要求 /
相互矛盾的意见），每类对应具体的应对动作。对照表见 `references/revision-strategy.yaml`（`sub_classification`）。

#### Step 2: 逐条起草回复

对每条意见生成"Original comment → Response → Changes made（含页码/行号）"结构。**关键：每条
都必须有 response，每个修改都必须指出具体位置。** 模板见 `references/revision-templates.md`。

#### Step 3: 修改追踪

生成 `revision-tracking.md`（Reviewer / Comment # / Severity / Stance / Sub-type / Action /
Manuscript Location / Status 表）。模板见 `references/revision-templates.md`。

#### Step 4: 补充分析（如需要）

审稿人常要求的补充分析：
- 亚组分析、敏感性分析 → 触发 `statistical-analysis`
- 补充图表 → 触发 `figure-generation`
- 额外文献 → 触发 `literature-synthesis`（引用先用 `pubmed-search` Mode 3 验证存在）

**规则：审稿人要求的新增分析一律标注为 post hoc / exploratory**（Methods 里写明"应审稿意见新增"，
Results 里与预定分析分开呈现），并写入 `analysis-log.md` 的 SAP 偏差记录；不得把新增的"显著"结果
改写成主要结论。

#### Step 5: 生成 Response Letter

生成 `response-letter.md`（Dear Editor 开头 + 分 Reviewer 逐条回复 + Summary of Changes）。
模板见 `references/revision-templates.md`。

### Phase 3: 修改后自检与收尾

- [ ] 每条审稿意见都有对应 response（无遗漏）
- [ ] 每个 response 都指出了具体修改位置（页码/行号）
- [ ] 新增数据/分析与原有内容一致（无矛盾），post hoc 分析已标注并记入 `analysis-log.md`
- [ ] Response Letter 语气 professional（无 defensive/aggressive 措辞）
- [ ] 修改后的论文通过 `pre-submission-verification` 重新检查 → `manuscript-export` 重新导出
- [ ] 修改后的字数仍在期刊限制内（Gate 6）
- 输出 3–5 行摘要（意见数、Critical 数、Rebut 数、新增分析、截止日）——轻量确认
- 更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：
  `completed_skills` 追加 revision-response 及产物、`next_step` 设为 pre-submission-verification）

## Output

| 文件 | 内容 | 来源 |
|------|------|------|
| `revision-plan.md` | 意见分类汇总（Severity × Stance）、优先级行动表（P1–P4）、Rebut 应对、新增分析、时间表 | Phase 1 |
| `revision-tracking.md` | 逐条修改追踪表（含 manuscript 位置和状态） | Phase 2 Step 3 |
| `response-letter.md` | 分 Reviewer 的逐条 point-by-point 回复 + Summary of Changes | Phase 2 Step 5 |

模板见 `references/revision-templates.md`。改投时的 cover-letter 由 `submission-preparation`
生成（非本 skill 输出）。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "审稿人的每个要求都必须接受" | 可以 respectfully disagree，但需要证据 |
| "改完直接交，不用再检查" | 修改可能引入新的不一致——重跑 6 Gate |
| "Response Letter 越短越好" | 太短显得不认真；太长显得 defensive |
| "被拒了这论文没希望了" | 大多数论文被拒后改投成功发表 |
| "这条意见不合理，直接忽略" | 每条都必须回复，忽略 = 拒稿 |
| "审稿人错了，直接说他错了" | 用证据礼貌说明，不要对抗 |
| "补充分析太多做不了" | 与编辑沟通哪些可行，不要沉默 |
| "审稿人要的亚组分析做出来显著，写进结论" | 那是 post hoc，只能作为探索性结果并标注 |
| "改了就行不用标注位置" | 审稿人需要快速找到修改处 |
| "拖到最后一天再交" | 提前 3-5 天交，留出检查时间 |

## Red Flags — STOP

- 有审稿意见没有对应 response（遗漏）→ STOP，每条都必须回复，忽略 = 拒稿
- response 没有指出具体修改位置（页码/行号）→ 补充，审稿人需要快速定位
- 语气 defensive/aggressive、直接说"审稿人错了"→ 改为有证据的礼貌措辞
- 新增分析没有标注 post hoc / exploratory、没记 SAP 偏差 → STOP，补标注
- 修改后未重新跑 `pre-submission-verification` → STOP，修改可能引入新的不一致
- 修改后字数超出期刊限制 → 精简
- 拖到截止日当天才提交 → 提前 3-5 天，留检查时间
- 改投时只改期刊名重投 / 在此重写 cover-letter → 交由 `submission-preparation` 做 cascade rewrite

## Convergence

当以下条件全部满足时完成：
1. 所有审稿意见已按 Severity × Stance 分类并排出 P1–P4（Phase 1）
2. 每条意见有明确的 action plan（Phase 1）
3. 修改时间表已制定（Phase 1）
4. Rebut items 有证据和措辞策略（Phase 1）
5. 每条审稿意见都有对应回复（Phase 2）
6. 所有要求的补充分析已完成，并标注 post hoc / exploratory（Phase 2）
7. 修改追踪表中所有条目状态为 ✅（Phase 2）
8. Response letter 格式完整（Phase 2）
9. 修改后的论文已通过 `pre-submission-verification` 再次检查，`.mrp-state.json` 已更新

## 衔接规则

### 前置依赖
- **必须**有收到的审稿意见（用户提供）
- **必须**有投出的稿件（`manuscript/*.md` + `manuscript.docx`）

### 强制衔接
- 前接 [投稿]（`submission-preparation` 之后收到审稿意见）
- 审稿人要求补充分析 → `statistical-analysis`（post hoc 标注 + `analysis-log.md` 偏差记录）
- 审稿人要求补充图表 → `figure-generation`；补充文献 → `literature-synthesis`
- 修改完成后 → **必须**再次 `pre-submission-verification` → `manuscript-export` → 提交修回稿
- 完成后 → 更新 `.mrp-state.json`

### 可选衔接
- 改投 → `journal-selection`（重新选刊）→ `submission-preparation`（cover-letter cascade rewrite + 投稿；本 skill 只做改投决策）
- 多位审稿人意见互相独立且量大 → `team-collaboration` 场景 3（子代理各写 `reviewerN-response.md`，主代理串行应用改动）
