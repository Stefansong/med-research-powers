---
name: research-question-formulation
description: Use when a user has a vague research idea and needs to define a clear question and hypothesis. Triggers on "我想研究..."、"这个课题怎么样"、"帮我想想选题"、"研究方向"、"科学问题".
---

# Research Question Formulation

## Overview

不允许在科学问题不明确的情况下开始任何分析或写作。用户说"帮我分析数据"时，先问清研究问题。本 skill 是流水线起点，产物 `research-question.md` 是 `literature-synthesis` 和 `study-design` 的输入。

## When to Use

- 用户有模糊的研究想法
- 需要从临床观察提炼科学问题
- "帮我分析数据"但没有明确假设

## When NOT to Use

- 已有明确的 PICO/PECO/PIRD 和假设 → 直接进 `study-design`
- 纯技术问题（如何做某种统计）→ `data-analysis-planning`
- 只想改一句话的措辞 → 直接改，不走流程

## Workflow: Socratic Questioning

每轮不超过 2-3 个问题，逐步收敛。

### Round 1: 选框架并填要素

**判断标准（先定研究类型，再选框架）：**
- 研究核心是"某种干预是否改善结局"，且干预可以由研究者分配 → **PICO**
- 研究核心是"某种暴露/因素与结局的关系"，暴露**不可干预或不宜干预**（吸烟、基因型、BMI、既往病史、环境暴露）→ **PECO**
- 研究核心是"某种方法能否准确诊断/检测/分割某种疾病" → **PIRD**
- 描述性研究（患病率、单臂可行性、预后因素筛选）→ 用 PICO/PECO 的 P + O，明确写"本设计无对照"

**PICO（干预性）：** P 研究对象、纳入/排除 · I 干预 · C 对照 · O 主要/次要结局
**PECO（暴露/病因）：** P 研究对象 · E 暴露的定义与测量 · C 未暴露/不同暴露水平 · O 结局
**PIRD（诊断准确性）：** P 目标患者群 · I 被评估的诊断方法（如"深度学习分析术中超声"）· R 参考标准/金标准（如"术后病理"）· D 目标诊断（如"胶质瘤切除边界残留"）

**关于对照（C）：** 缺 C 时**先确认研究类型是否本就无对照**——单臂研究、患病率/横断面描述、预后因素筛选、量表开发本来就没有对照组，这时不追问，改为要求写清"与什么基准比较"（历史数据、文献值、无）。只有干预性或暴露-结局研究缺 C 才继续追问，不要凑一个对照。

### Round 2: FINER

每项打 1-5 分，锚点如下（1 分与 5 分各一句话，中间按程度取）：

| 项 | 1 分 | 5 分 |
|----|------|------|
| **F** Feasible | 数据/样本/技术/经费中至少一项现在拿不到，也没有获取路径 | 数据已在手或有明确获取途径，样本量可达，团队会做全部方法 |
| **I** Interesting | 只有本课题组关心，同行不会追问结果 | 结果无论阳性阴性，领域内都会想知道 |
| **N** Novel | 同样人群、同样方法、同样结局已有多篇发表 | 快速查重找不到相同研究，或只在人群/方法/结局上有清晰的增量 |
| **E** Ethical | 存在无法通过伦理审查的设计（如剥夺有效治疗） | 无伦理障碍，或有成熟的知情同意/豁免路径 |
| **R** Relevant | 结果不会改变任何临床决策或指南 | 结果能直接影响诊疗选择、指南或政策 |

**N（Novel）必须做一次快速查重：** 调用 `pubmed-search` Mode 1（快速查重用法）——用 P + I/E + O 的核心词构建一条检索式，看 `total_count` 与前 5 条标题；已有高度相似研究 → 与用户讨论增量点或调整问题，并把检索式与结果数记进 `research-question.md`。

### Round 3: Hypothesis

- 零假设和备择假设（能用统计语言表述）
- 预期结果
- 如果结果不符预期的可能解释

### Round 4: 输出并记录状态

生成 `research-question.md`（见 Output），向用户复述一句话研究问题请其确认；确认后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加本 skill，登记 `research-question.md`，`next_step` 设为 literature-synthesis）。

## Output

生成 `research-question.md`：
1. 科学问题（一句话）
2. 框架分解（PICO / PECO / PIRD，按 Round 1 判断选用；无对照设计写明基准）
3. 研究假设（H0 / H1）
4. FINER 评分（每项 1-5 分 + 一句理由；N 项附快速查重检索式与结果数）
5. 预期结果
6. 潜在局限性

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "先跑数据看看有什么" | 没有假设的分析 = 数据钓鱼 |
| "研究问题太窄了不好发表" | 精确的问题远好于模糊的大问题 |
| "不需要对照组" | 干预/暴露研究缺 C 就不完整；先确认是不是单臂/患病率等本无对照的设计 |
| "暴露也套 PICO" | 不可干预的暴露用 PECO，否则会误把关联写成因果 |
| "结局指标以后再定" | 事后选择结局 = 结果偏倚 |
| "FINER 评估不重要" | 可行性低的完美问题等于零 |
| "肯定没人做过" | 必须查重，N 项不能凭感觉打分 |

## Convergence

当以下条件**全部**满足时停止追问：
1. 研究框架要素全部明确——干预性用 **PICO**，暴露/病因用 **PECO**，诊断准确性用 **PIRD**；按研究类型选对框架且无缺项（本无对照的设计已写明基准）
2. 研究假设可以用统计语言表述
3. FINER 已打分，N 项有快速查重记录
4. 用户确认问题定义准确，`research-question.md` 已生成，`.mrp-state.json` 已更新

## Red Flags — STOP

- 用户说"先跑数据看看" / 没有假设就要分析 → STOP，先定义研究问题
- 干预/暴露研究缺 C，或 PIRD 缺 Reference standard → 继续追问，不要凑数（先排除本无对照的设计）
- 结局指标含糊或"以后再定" → STOP，事后选结局 = 结果偏倚
- 研究问题大而空（如"AI 在医学的应用"）→ 收窄到可检验的具体问题
- 用错框架（干预性研究套 PIRD，诊断准确性研究套 PICO，不可干预暴露套 PICO）→ 重新判断研究类型
- 用户要求跳过本 skill 直接分析或写作 → STOP

## 衔接规则

### 强制衔接（不可跳过）
- 完成后**必须进入 `literature-synthesis`（了解现状、找 gap）或 `study-design`（设计研究）之一，不可直接跳到分析/写作**。默认顺序：`literature-synthesis` → `study-design`；用户已有充分文献基础时可直接 `study-design`
- Round 2 的 N 项 → 调用 `pubmed-search` Mode 1 快速查重

### 前置依赖（不满足则阻止）
- 无——本 skill 是流程起点，可独立运行

### 可选衔接
- `data-analysis-planning` 发现没有明确假设 → 触发本 skill
- `manuscript-writing` 发现没有 `research-question.md` → 触发本 skill
- 查重发现相同研究已发表 → 与用户讨论改变人群/方法/结局，或转为验证/外部验证研究
