---
name: using-med-research-powers
description: Use when a research-process task is detected (选题、研究设计、数据分析、画图、写论文、投稿、修稿) or the user asks where their project stands. This is the MRP orchestrator — routes to the right skill and keeps project state.
---

# Using Med-Research-Powers (MRP)

## Overview

MRP 是一套覆盖"选题 → 设计 → 分析 → 写作 → 投稿 → 修稿"的医学科研方法论 skill。
本 skill 是总调度：判断用户要做的是不是研究流程级任务，路由到正确的 skill，记录项目进度，
并在三个不可逆的节点上要求用户明确确认。

优先级：用户自己的 CLAUDE.md > MRP skill > 默认行为。

### 核心原则：先分析，再计划，再决定，再执行

凡是要结合真实数据和真实需求的步骤（研究设计、分析计划、数据清洗与分析、数据收集工具、作图、写作），**一律不套现成模板或现成脚本**：

1. **分析**：先看清真实情况——数据长什么样、用户到底要回答什么问题、研究方案规定了什么、有什么约束。
2. **计划**：根据分析结果定制方案，写明每个选择的理由；模板只用来检查有没有漏项。
3. **决定**：关键选择给用户看；硬确认节点必须等用户同意。
4. **执行**：按确认后的计划现写代码或内容，执行后自检，偏离计划处记录理由。

**结局盲规则**（各 skill 引用这一条）：计划前**可以看**数据的结构和质量（变量、编码、缺失形式、事件总数、同一患者多条记录等），**不能看**变量与结局的关系（包括暴露/分组与结局，含按组画的结局图）——这些只能在分析计划确认后按计划执行，否则就成了看结果选方法。只在预测变量之间、不涉及结局的冗余检查可以做。用户明确要探索性分析时可以做，但标明 exploratory，不再拿它选 SAP 的方法。
插件里的固定脚本只做四类事：容易算错的公式（样本量）、防止致命错误的护栏（患者级划分、随机分组）、与数据无关的基础设施（状态、期刊模板、导出）、只报告不做决定的检查工具（数据体检、前提检验、重跑一致性）。分析代码本身由 AI 针对具体数据现写。

## When to Use

- 用户提出研究流程级任务：想研究某个问题、设计研究、算样本量、制定分析计划、跑统计、出图、写论文、选期刊、投稿、回复审稿意见。
- 用户问"我的项目做到哪了 / 下一步做什么"。
- 会话开始时项目目录里有 `.mrp-state.json`（hook 会提示）。

## When NOT to Use

- 单点小问题：改一句话、解释一个统计概念、算一个数、改一处格式。直接回答，不进流程（按组比较结局不算小问题，受结局盲规则约束）。
- 与科研无关的任务（写代码、处理文件等）。
- 用户明确说"不用走 MRP 流程"。

## Workflow

```
1. 会话开始
   - 项目目录有 .mrp-state.json → 一句话告知："上次完成到 [current_stage]，下一步是 [next_step]。继续？"
   - 没有 → 正常路由；第一个主线 skill 完成时创建状态文件（mrp_state.py init）

2. 收到用户消息
   - 研究流程级任务 → 查 Skill Routing 表 → 宣布 "Using [skill] to [目的]" → **用 Skill 工具调用该 skill**（如 `mrp:data-analysis-planning`），按它的完整流程执行；不要凭本表的一行摘要自己动手
   - 单点小问题 → 直接回答
   - 找输入文件时只在当前项目目录（和用户指明的路径）里找；找不到就直接问用户放在哪，不要在整个磁盘上搜索

3. 每个主线 skill 完成后（由该 skill 自己执行，本表是统一约定）
   a. 输出 3–5 行摘要（格式见下）
   b. 更新 .mrp-state.json（mrp_state.py done <skill> --output <产物> --next <下一个 skill>）
   c. 按 checkpoint_mode 决定：直接进入下一步 / 等用户确认；硬确认节点一律等待

4. 硬确认节点（3 个）→ 展示锁定内容 → 用户明确同意后 mrp_state.py checkpoint <name> confirmed
```

### 摘要格式（每个 skill 完成时）

```
✅ [skill 名] 已完成
📄 生成的文件：file1.md — 一句话说明
📊 关键决策：1–3 条
⚠️ 需要注意：如有
➡️ 建议下一步：[下一个 skill] — 做什么
```

轻量模式下紧接着直接进入下一步，不额外提问；逐步模式下末尾加一句"继续，还是先修改？"。用户只要一个产物（一节 Methods、一张图、一份 SAP）时不自动推进：交付后停下，摘要里提示下一步。

## 确认方式（checkpoint_mode）

| 模式 | 行为 | 何时用 |
|------|------|--------|
| `light`（默认） | 每步只出摘要并自动推进；只在 3 个硬确认处停下等用户 | 大多数情况 |
| `step` | 每步出摘要后等用户说"继续" | 用户说"逐步确认 / 每步问我" |
| `auto` | 硬确认也只提示不等待：锁定内容照常写入，文件头记 `status: confirmed` + `confirmed_by: auto`，下游照常接受 | 用户说"一直做到底 / 不用问我" |

用户切换模式时执行 `mrp_state.py set checkpoint_mode=<mode>`；用户同意时也可存入全局画像。

### 三个硬确认（任何模式下都要展示锁定内容）

| # | 节点 | 产物 | 锁定什么 | 为什么不可逆 |
|---|------|------|----------|--------------|
| 1 | study-design 完成后 | `study-protocol.md` | 研究类型、主要结局、样本量、对照 | 事后改主要结局 = outcome switching |
| 2 | data-analysis-planning 完成后 | `analysis-plan.md` | 统计分析计划（SAP） | 防 p-hacking；之后的偏离必须记录理由 |
| 3 | pre-submission-verification 完成后 | `submission-readiness-report.md` | 6 个 Gate 全部通过 | 任何 Gate 失败不能投稿，必须回去修 |

目标期刊是**软确认**：study-design 后暂定一个，manuscript-writing 前复核一次，随时可换。

除硬确认外，skill 在缺少只有用户知道的信息时也会停下来问（例如真实数据从哪个系统导出、字段怎么写）——这是补信息，不是走形式；问的时候一次问全。

### 用户响应的处理

| 用户说 | 行为 |
|--------|------|
| "继续 / 好 / 下一步" | 进入建议的下一个 skill |
| "等一下，把 X 改成 Y" | 修改当前产物后重新出摘要 |
| "跳过 [skill]" | 记录跳过原因进入再下一步；pre-submission-verification 不能跳过 |
| "回到 [skill]" | 按回溯表回到上游 skill，下游产物标记"需重新验证" |
| 直接给了新指令 | 按新指令路由；当前步骤视为已确认（硬确认节点除外） |

## Pipeline（主线顺序）

```
research-question-formulation
→ literature-synthesis
→ study-design                      [硬确认 1：study-protocol.md]
→ research-ethics                   （伦理审查 / 注册，必须在收集数据前）
→ journal-selection                 （暂定目标期刊，软确认）
→ data-analysis-planning            [硬确认 2：analysis-plan.md]
→ data-collection-tools             （只在还要收集数据时；数据已在手则跳过）
→ [用户收集数据]
→ statistical-analysis
→ figure-generation
→ manuscript-writing                （写作前复核目标期刊）
→ peer-review-simulation
→ pre-submission-verification       [硬确认 3：6-Gate 全过]
→ manuscript-export
→ submission-preparation
→ [投稿] → revision-response → 回到 pre-submission-verification → manuscript-export → 修回
```

辅助 skill（不在主线上，被调用或随时可用）：`pubmed-search`（被 literature-synthesis / pre-submission-verification Gate 3 / manuscript-writing 调用）、`reporting-standards`（被 Gate 1 调用）、`team-collaboration`（需要并行子代理时）、`writing-mrp-skills`（改进 MRP 自身）、本 skill。

用户可以从中间任何一步进入（例如已有数据直接做分析）。**缺前置产物时**（各 skill 的"前置依赖"都按这条办，不拒绝）：一句话告诉用户缺什么、为什么要紧；给两个选择——现在补（说出最快的补法），或先往下做并记下缺口（`mrp_state.py done … --note "缺 X"`，涉及分析的同时写进 `analysis-log.md`）；按用户的选择办，auto 模式默认先往下做。
硬确认不因此跳过：确证性分析前 SAP 必须已确认（已有数据时走 `data-analysis-planning` 快速路径，研究问题和主要结局直接写进 SAP 一起确认；不要 SAP 就只能做标明 exploratory 的分析）；投稿和投稿版导出前必须过 6-Gate。已收集好的数据不走 `data-collection-tools`，SAP 确认后直接 `statistical-analysis`。

## Skill Routing

| Skill | 触发 |
|-------|------|
| research-question-formulation | 模糊研究想法、要明确假设、PICO |
| literature-synthesis | 查文献做综合、research gap、系统综述 / Meta 分析的检索与筛选（不写作） |
| pubmed-search | PMID / 引用验证 / 检索式 / MeSH / 单库快速检索 |
| study-design | 研究设计、样本量、protocol（临床 / 基础 / AI / 定性 / 问卷，内置 Type A–E 路由） |
| research-ethics | 伦理、IRB、知情同意、注册、隐私、人类遗传资源 |
| journal-selection | 投哪个期刊、选刊、期刊要求 |
| data-analysis-planning | 没有 analysis-plan.md 时"帮我分析数据"、制定 SAP |
| data-collection-tools | 收集数据前：CRF、标注表、患者级数据划分、随机分组脚本 |
| statistical-analysis | 已有 analysis-plan.md 时执行分析、跑统计 |
| figure-generation | 画图 / 作图 / 出图、期刊图规范 |
| manuscript-writing | 写论文各章节（原始研究 + 5 种综述的成稿） |
| manuscript-export | Markdown → .docx、期刊排版、字数/图表数检查 |
| reporting-standards | CONSORT / STROBE / PRISMA 等报告规范逐条检查 |
| peer-review-simulation | 模拟审稿、审稿人会挑什么毛病 |
| pre-submission-verification | 论文写完了 / 可以投了 / 定稿（6-Gate，强制） |
| submission-preparation | Cover letter、投稿系统操作 |
| revision-response | 审稿意见怎么改、逐条回复 |
| team-collaboration | 多子代理并行（多库检索、4 审稿人、并行修稿） |
| writing-mrp-skills | 写新 skill / 改进 skill |
| using-med-research-powers | 路由、状态、确认节点（本 skill） |

研究类型路由全部在 `study-design` 内部：临床 → A；基础（细胞/动物/分子）→ B；AI/ML → C；定性 → D；问卷/调查/Delphi → E。

## Pipeline 回溯（Backward Links）

| 当前阶段 | 发现的问题 | 回到 |
|----------|------------|------|
| 任何阶段 | 研究问题定义不准确 | research-question-formulation |
| statistical-analysis | 前提假设不满足 / 需改方法 | data-analysis-planning（修改 SAP，记录偏离理由） |
| manuscript-writing | 分析方法需调整 | data-analysis-planning → statistical-analysis |
| peer-review-simulation | 方法学 Critical 问题 | study-design（只能改写法与局限，不能改已锁定的主要结局） |
| pre-submission Gate 1（报告规范） | 条目缺失 | manuscript-writing，再跑 reporting-standards |
| pre-submission Gate 2（统计） | 统计不完整 / 与 SAP 不符 | statistical-analysis |
| pre-submission Gate 3（引用与数据） | 引用不存在 / 数字不一致 | pubmed-search Mode 3 → manuscript-writing |
| pre-submission Gate 4（图表） | 图表不合规 | figure-generation |
| pre-submission Gate 5（伦理） | 伦理声明缺失 | research-ethics |
| pre-submission Gate 6（形式） | 字数 / 引用数 / 图表数超限 | manuscript-writing（或换期刊 → journal-selection） |
| revision-response | 审稿人要求补充分析 | statistical-analysis（标注 post hoc，写入 SAP 偏离记录） |
| revision-response | 被拒需改投 | journal-selection → manuscript-export |
| data-collection-tools | protocol 缺变量定义 | study-design |

回溯规则：修改后的产物标注修改原因和日期；下游依赖它的产物标记"需重新验证"。

## Session State（项目状态）

文件：项目目录下的 `.mrp-state.json`，**只通过脚本写**：
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`

| 命令 | 何时用 |
|------|--------|
| `init --project "<名称>"` | 第一个主线 skill 开始前（文件不存在时） |
| `done <skill> --output <文件> [--output ...] --next <下一个 skill>` | 每个主线 skill 完成时 |
| `set target_journal="..." / checkpoint_mode=light` | 暂定期刊、切换确认方式 |
| `checkpoint protocol|sap|pre_submission confirmed` | 用户通过硬确认时 |
| `show [--json]` | 会话开始 / 用户问进度 |

字段：`project`、`current_stage`、`next_step`、`checkpoint_mode`、`target_journal`、`hard_checkpoints{}`、`completed_skills[]`、`artifacts{}`、`notes[]`。完整 schema 见 [`references/state-schemas.md`](references/state-schemas.md)。
hook 只读其中 5 个字符串字段（见仓库 SECURITY.md）。

## User Profile（用户画像，全局）

文件：`~/.claude/mrp-user-profile.json`（按人不按项目，所有项目共用）。
**不在会话开始时集中提问。** 只有下面三个 skill 在用到某字段时读一次；缺就只问这一个问题，并问用户要不要保存：

| Skill | 字段 | 命令 |
|-------|------|------|
| journal-selection | `favorite_journals` | `mrp_state.py profile get favorite_journals`（exit 3 = 未设置） |
| data-analysis-planning | `preferred_stats_tool` | `mrp_state.py profile get preferred_stats_tool` |
| figure-generation | `preferred_figure_style` | `mrp_state.py profile get preferred_figure_style` |

写入：`mrp_state.py profile set <field> <value>` / `profile add <列表字段> <值>`。其他字段（role、research_domains、methods_familiar 等）只在用户主动提到时记录。

隐私：文件只在本机；用户可以随时说"忘记我的 X"（对应字段清空）或删除文件；不记录密码、患者数据、伦理批件号。

## Output

本 skill 不产出研究文件；它维护 `.mrp-state.json` 与 `~/.claude/mrp-user-profile.json`，并保证每个主线 skill 完成时有统一格式的摘要。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "用户随口问个统计概念，也走一遍流程" | 单点问题直接回答；流程只给研究流程级任务 |
| "每一步都停下来问一句更安全" | 只有 3 个节点不可逆；其余步骤的产物本身就是可检查的文件，摘要 + 自动推进即可 |
| "记住用户偏好就先问 5 个问题" | 用到哪个字段再问哪个；没人用的字段不采集 |
| "状态文件让 Claude 记在心里就行" | 状态只以 `.mrp-state.json` 为准，且只用脚本写，否则新会话无法恢复 |
| "论文写完就可以投了" | 必须经过 pre-submission-verification 的 6 个 Gate |
| "拿个现成模板/脚本改改就能用" | 数据的编码、缺失、聚类结构和研究需求各不相同；先分析真实情况再定制，模板只用来查漏 |

## Convergence

一个项目在本 skill 视角下"走完"的条件：`hard_checkpoints` 三项均 confirmed，`completed_skills` 含 submission-preparation，`next_step` 为等待审稿意见。修稿阶段视为新一轮：revision-response → pre-submission-verification → manuscript-export。

## Red Flags — STOP

| 想法 | 现实 |
|------|------|
| "直接跑个 t 检验就行" | 方法来自已确认的 SAP，不临场挑检验；先看哪些变量和结局有关再定方法就是事后假设 |
| "这个分析很简单不需要计划" | 无 SAP = p-hacking 温床 |
| "样本量够大没问题" | 必须有正式的先验样本量计算 |
| "p < 0.05 就是显著" | 效应量 + CI + 临床意义综合判断 |
| "Accuracy 95% 模型很好" | 类别不平衡时看 AUROC / AUPRC，并做校准与 DCA |
| "数据随机划分就行" | 同一患者不能同时在训练集和测试集 |
| "回顾性不需要伦理" | 需要伦理审查或书面豁免，且在收集数据前 |
| "用 CONSORT 2010 就行" | CONSORT 2025 已取代 2010（30 项，含子项共 42 行） |
| "主要结局改一下没关系" | protocol 确认后主要结局锁定；改动 = 需公开说明的 protocol 修改 |

## 衔接规则

### 强制衔接（不可跳过）
- 每个主线 skill 完成 → 更新 `.mrp-state.json` → 按 checkpoint_mode 进入下一步。
- 3 个硬确认节点必须得到用户明确同意（auto 模式除外，但锁定内容照常写入）。

### 前置依赖
- 本 skill 本身无前置；各 skill 的前置产物缺失时，按 Pipeline 节的"缺前置产物时"规则处理。

### 可选衔接
- 需要并行（多库检索、4 审稿人、并行修稿）→ `team-collaboration`。
- 用户想改进 MRP 自身 → `writing-mrp-skills`。
