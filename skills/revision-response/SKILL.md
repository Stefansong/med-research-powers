---
name: revision-response
description: Use when the user receives a journal revision or reject decision. Triggers on "怎么改"、"修改策略"、"大修"、"小修"、"审稿意见"、"revision"、"reviewer comments"、"回复审稿人"、"rebuttal"、"response letter".
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

将所有审稿意见逐条分为 4 类：**Critical**（关乎核心有效性，必须修复）、**Major**（重要但可
协商修复方式）、**Minor**（格式/表述，快速修复）、**Disagreeable**（要求不合理，礼貌反驳）。
完整定义与策略见 `references/revision-strategy.yaml`（`comment_classification`）。

### Step 2: 修改优先级排序

按"影响力 x 难度"矩阵排序。**核心原则：** 先 Critical（不修 = 拒稿）→ 再 High Impact +
Low Difficulty（最大性价比）→ 然后 Minor（展示态度）→ 最后 Disagreeable（精心措辞）。
完整矩阵见 `references/revision-strategy.yaml`（`priority_matrix` / `priority_order`）。

### Step 3: Response Letter 策略

**总原则：** Collaborative, not defensive. 即使审稿人明确错误，也用证据礼貌说明，绝不对抗；
要求不可能的实验时承认价值、说明原因、写入 limitation/future direction。按情况选择措辞模板，
见 `references/revision-strategy.yaml`（`response_strategy`）。

### Step 4: 修改后自检

修改完成后，自动触发以下检查：

- [ ] 每条审稿意见都有对应 response（无遗漏）
- [ ] 每个 response 都指出了具体修改位置（页码/行号）
- [ ] 修改后的论文通过 `pre-submission-verification` 重新检查
- [ ] 新增数据/分析与原有内容一致（无矛盾）
- [ ] Response Letter 语气 professional（无 defensive/aggressive 措辞）
- [ ] 修改后的字数仍在期刊限制内

### 改投策略（被拒后）——只做决策

本 skill 只负责**改投决策**：是 Appeal 还是改投。Cover-letter 重写/cascade-rewrite 的具体
机制属于 `submission-preparation`（owner），不在此重复。

#### 评估是否值得 Appeal
判断标准（编辑分歧大 / 审稿人事实错误 → 可 Appeal；方法被全盘否定 / desk reject → 改投）
见 `references/revision-strategy.yaml`（`appeal_decision`）。

#### 决定改投后的流程
1. 根据审稿意见改进论文（免费的专家建议，不要浪费）
2. 回到 `journal-selection` → 选择下一梯队期刊
3. `submission-preparation` → 由其负责重写 Cover Letter（cascade rewrite，含"已据同行评审
   改进"的可选措辞）。**本 skill 不重述 cover-letter 模板。**

### Phase 1 Output

生成 `revision-plan.md`（Summary + Priority Action List + Disagreeable Items + New
Analyses + Timeline）。完整模板见 `references/revision-templates.md`。

---

## Phase 2: Point-by-Point Response (逐条回复)

系统化回复审稿人意见。每条意见都必须有明确回应，修改必须可追踪。

### Step 1: 意见细分类

对每条审稿意见进一步细分类（方法学质疑 / 要求补充分析 / 文字改进 / 参考文献 / 不合理要求 /
相互矛盾的意见），每类有对应的应对策略。完整对照表见
`references/revision-strategy.yaml`（`sub_classification`）。

### Step 2: 逐条起草回复

对每条意见生成"Original comment → Response → Changes made（含页码/行号）"结构。**关键：每条
都必须有 response，每个修改都必须指出具体位置。** 模板见 `references/revision-templates.md`。

### Step 3: 修改追踪

生成 `revision-tracking.md`（Reviewer / Comment # / Type / Action / Manuscript Location /
Status 表）。模板见 `references/revision-templates.md`。

### Step 4: 补充分析（如需要）

审稿人常要求的补充分析：
- 亚组分析 → 触发 `statistical-analysis`
- 敏感性分析 → 触发 `statistical-analysis`
- 补充图表 → 触发 `figure-generation`
- 额外文献 → 触发 `literature-synthesis`

### Step 5: 生成 Response Letter

生成 `response-letter.md`（Dear Editor 开头 + 分 Reviewer 逐条回复 + Summary of Changes）。
模板见 `references/revision-templates.md`。

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

## Output

| 文件 | 内容 | 来源 |
|------|------|------|
| `revision-plan.md` | 意见分类汇总、优先级行动表、Disagreeable 应对、新增分析、时间表 | Phase 1 |
| `revision-tracking.md` | 逐条修改追踪表（含 manuscript 位置和状态） | Phase 2 Step 3 |
| `response-letter.md` | 分 Reviewer 的逐条 point-by-point 回复 + Summary of Changes | Phase 2 Step 5 |

模板见 `references/revision-templates.md`。改投时的 cover-letter 由 `submission-preparation`
生成（非本 skill 输出）。

## Red Flags — STOP

- 有审稿意见没有对应 response（遗漏）→ STOP，每条都必须回复，忽略 = 拒稿
- response 没有指出具体修改位置（页码/行号）→ 补充，审稿人需要快速定位
- 语气 defensive/aggressive、直接说"审稿人错了"→ 改为有证据的礼貌措辞
- 修改后未重新跑 `pre-submission-verification` → STOP，修改可能引入新的不一致
- 修改后字数超出期刊限制 → 精简
- 拖到截止日当天才提交 → 提前 3-5 天，留检查时间
- 改投时只改期刊名重投 / 在此重写 cover-letter → 交由 `submission-preparation` 做 cascade rewrite

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
- 改投 → `submission-preparation`（由其负责 cover-letter cascade rewrite + 投稿；本 skill 只做改投决策）
