---
name: study-design
description: Use when designing any research study protocol (clinical/basic/AI-ML/qualitative/survey). Triggers on "研究类型"、"样本量"、"写protocol"、"RCT设计"、"动物模型"、"定性研究"、"问卷"、"Delphi"、"study design"、"sample size".
---

# Study Design

## Overview

所有类型研究的方案设计——临床、基础、AI/ML、定性、问卷调查。**设计由真实条件决定**：先分析病例/数据来源、事件数、资源等真实条件（Step 0），再判断研究类型，读取对应模块文件（`references/modules/` 下五个文件，见 Router 表），最终统一产出 `study-protocol.md`（文件内 `type:` 字段区分五类）。模板和模块里的表格是必须覆盖的清单，不是填空表。本文件只放路由、通用流程与通用规则；各类型的决策树、专属规则和专属 Common Mistakes / Convergence / Red Flags 都在模块文件里。

## Study Type Router

**设计前必须先确定研究类型。** 不同类型有完全不同的方法学、样本量逻辑和报告规范。

```
研究问题 → 什么类型的研究？
├── 涉及患者/临床数据的干预、暴露、诊断或预测？ → A. Clinical
│     （RCT、队列、病例对照、横断面、诊断准确性、预测模型、真实世界研究）
├── 涉及细胞/动物/分子实验？ → B. Basic Science
│     （WB、PCR、流式、动物模型、基因编辑、组织病理）
├── 核心是 AI/ML 模型的开发、验证或评估？ → C. AI/ML
│     （影像 AI、手术视频 AI、预测模型、LLM/VLM 评估、智能器械）
├── 探索性/理解"为什么"？ → D. Qualitative
│     （访谈、焦点小组、扎根理论、现象学、混合方法）
├── 问卷/调查/共识？ → E. Survey / Questionnaire / Delphi
│     （KAP 调查、量表开发验证、Delphi 共识）
└── 不确定 → 让用户描述研究问题与数据来源，再按上面判断
```

| 类型 | `type:` 值 | 读取模块 | 样本量逻辑 | 核心报告规范 |
|------|-----------|---------|-----------|-------------|
| Clinical Research | `clinical` | `references/modules/clinical.md` | Power analysis | CONSORT 2025 / STROBE / STARD / TRIPOD+AI |
| Basic Science | `basic` | `references/modules/basic-science.md` | 生物学重复 >= 3 + power（动物） | ARRIVE 2.0 |
| AI/ML Medical | `ai-ml` | `references/modules/ai-ml.md` | 患者级数据划分 + 外部验证 | TRIPOD+AI / CLAIM 2024 / CONSORT-AI / DECIDE-AI |
| Qualitative | `qualitative` | `references/modules/qualitative.md` | 信息饱和 | COREQ / SRQR |
| Survey/Delphi | `survey` | `references/modules/survey-delphi.md` | 公式计算 / 专家数 | CHERRIES / CROSS / STROBE / COSMIN |

判断规则：
- 既有临床数据又有 AI 模型 → 以"论文的主要贡献是什么"定：贡献是模型 → C；贡献是临床结论、AI 只是分析工具 → A，并加载 C 的数据划分与可复现性要求。
- 混合方法 → 主模块 D，定量部分再读 A 或 E。
- 判定后**只读取对应模块**，不要把五个模块全部加载。

## Prerequisites

- **必须**有明确的研究问题（`research-question.md`，来自 `research-question-formulation`）
- **推荐**已有文献综合（`literature-synthesis-summary.md`，用于 gap 定位与效应量来源）

## When to Use

- 需要为任意类型研究（临床/基础/AI-ML/定性/问卷）撰写方案时
- 需要确定研究类型、样本量逻辑或核心报告规范时
- 审稿人/伦理委员会要求补充正式 protocol 时

## When NOT to Use

- 还没有明确的研究问题 → 先做 `research-question-formulation`
- 已确定方案、要制定详细统计分析计划 → `data-analysis-planning`
- 要执行统计分析 → `statistical-analysis`
- 仅需检查某个报告规范条目 → `reporting-standards`
- 只是想改 protocol 里的一句话 → 直接改，不走流程

## Workflow（五类通用：Step 0 分析真实条件 + 5 步设计）

### Step 0: 分析真实条件（先分析，再设计）

先把下面几项弄清楚。项目文件里没有的，**一次性列成清单问用户**，不要自己假设：

| 条件 | 要弄清什么 | 从哪来 |
|------|-----------|--------|
| 研究问题与目的 | 要回答的核心问题；结果用来做什么（改临床决策 / 为后续研究做准备 / 申请基金） | `research-question.md` |
| 病例 / 数据来源 | 回顾性已有数据还是前瞻性新收集；已有数据在哪个系统、覆盖哪些年份、关键变量有没有记录 | 用户 |
| 病例数与事件数 | 每年可获得的病例数；主要结局预计有多少个事件（事件数决定能做多复杂的分析）；同一患者会不会有多条记录（多个病灶 / 双侧 / 多次随访） | 用户（科室统计、HIS 查询）+ 文献 |
| 中心数 | 单中心 / 多中心；各中心能提供多少例、记录标准是否一致 | 用户 |
| 随访可行性 | 能随访多久、用什么方式、预计失访多少 | 用户 + 本中心既往经验 |
| 资源与时间 | 入组、随访、标注、统计的人手；经费、设备；截止时间 | 用户 |
| 伦理 / 注册限制 | 已有数据的使用是否在批准范围内；能否前瞻入组、能否随机；是否必须注册 | 用户 + `research-ethics` 的规则 |
| 已有研究的结论 | 已知的效应量 / 事件率（写出处）；已有研究的设计缺陷，本研究要补什么 | `literature-synthesis-summary.md` |

五类研究都做这一步：基础研究把"病例"换成样本 / 动物 / 细胞来源，定性研究换成能接触到的受访者；与本类型无关的项写"不适用"。暂时查不到的写"未知：需 [谁] 提供"，并说明它会影响哪个设计决定。

然后回答"在这些条件下，哪种设计最能回答这个问题"：只有回顾性数据就不能写成前瞻性研究；预计事件数太少，就考虑多中心、延长入组期、换更常见的结局或减少变量。结论写进 `study-protocol.md` 的"真实条件与设计理由"一节（写法见 `references/protocol-templates.md`）：选了什么设计、依据哪些真实条件、为什么没选更强的设计。

### Step 1: 确定研究类型并读取模块

按 Router 判定 `type:`，向用户复述一句"我判断这是 [类型]，因为 [理由]"，然后读取 Router 表里对应的模块文件（`references/modules/clinical.md` / `basic-science.md` / `ai-ml.md` / `qualitative.md` / `survey-delphi.md` 之一）。模块内有该类型的决策树（细分设计）和专属规则，后续每一步都按模块要求补充细节。决策树里的细分设计（如 RCT / 前瞻性队列 / 回顾性队列）按 Step 0 的真实条件选，不是"证据等级越高越好"。

### Step 2: 界定研究对象与比较

- 纳入/排除标准（具体、可操作，写成能逐条核对的句子）
- 对照或比较对象（临床：对照组；基础：阴性/阳性/载体对照；AI：基线模型 / 人类专家 / 现有工具；定性：不设对照，改写"抽样策略"；问卷：目标人群与抽样框）
- 数据来源与时间窗（前瞻采集 / 回顾性数据库 / 公开数据集 / 动物模型）

### Step 3: 论证样本量或数据规模

先写参数从哪来，再算数字：
- **预期效应量 / 事件率 / 比例必须有真实来源**：相近人群、相近设计的文献（写 PMID，并说明为什么能借用）；本中心预实验或历史数据（写时间段与例数）；或临床上有意义的最小差异（写依据）。"常用值"（如"取中等效应量""事件率按一半估计"）不是来源。
- 按模块逻辑给出数字：power analysis（效应量、α、β、脱落率；生存结局按事件数）/ 生物学重复数 / 数据划分方案 + 外部验证 / 信息饱和范围 / 调查公式。样本量脚本统一用 `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py`。
- **用 Step 0 的可获得病例数核对可行性**：计划期内能不能达到所需例数 / 事件数。达不到就改设计（多中心、延长入组期、换结局、减少变量）并写理由，**不要反过来改小参数去凑手头的例数**。
- 回顾性研究的例数由已有数据决定：用真实的可用例数与事件数说明能支撑什么分析（能纳入几个变量、能检出多大的差异——在看结果之前按固定例数计算，不是用观察到的效应算"事后 power"）。
- 写不出依据 → 不要编一个数字，改写"需预实验 / 需文献效应量"并列为待办。

### Step 4: 定义结局、变量与偏倚控制

- 主要结局只有一个（含定义、测量方式、评估时点）；其余为次要结局
- 变量表：自变量/暴露、因变量/结局、混杂/协变量——每个都有定义与单位
- 偏倚控制按类型：随机化/分配隐藏/盲法/混杂调整（A）；对照/重复/盲评（B）；患者级划分/标注一致性/外部验证（C）；可信度策略（D）；应答率/抽样偏倚（E）
- 选定报告规范（名称与 `reporting-standards` 索引一致；索引里没有的标"无本地清单，需人工核对"）

### Step 5: 生成 protocol → 审批 → 记录状态

1. 按 `references/protocol-templates.md` 中对应 `type:` 的章节清单写 `study-protocol.md`：清单只用来查漏，内容按本研究的真实条件写；不适用的章节写"不适用 + 理由"；确实未知的写 `TBD: [需要什么]`；不照抄模板或模块里的示例数字、例数和措辞
2. 按模块的 Convergence 与本文件的通用 Convergence 自查
3. 进入 **Hard Checkpoint**（见下），等待用户明确确认
4. 确认后把 `status:` 改为 `confirmed`，然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 study-design、`artifacts` 登记 `study-protocol.md`、`next_step` 设为 research-ethics）

## Output

**唯一产物：`study-protocol.md`**（五类同名，`type:` 字段区分：`clinical` / `basic` / `ai-ml` / `qualitative` / `survey`）。

章节清单按类型取自 `references/protocol-templates.md` 的 A–E 部分（用来查漏，不是填空表）。无论哪一类，文件都必须含：

| 章节 | 内容 |
|------|------|
| 头部 | `type` / `title` / `version` / `research_question` / `registration` / `status` |
| 真实条件与设计理由 | Step 0 的条件清单；选了什么设计、依据哪些条件、为什么不选更强的设计 |
| 研究概要 | 设计类型、场景、报告规范 |
| 研究对象 / 数据来源 | 纳入排除、招募或数据获取方式 |
| 比较 / 对照 | 按类型（对照组 / 实验对照 / 基线模型 / 抽样策略） |
| 样本量 / 数据规模 | 数字 + 依据 + 参数来源 |
| 结局 / 变量 / 评估 | 主要与次要结局、评估时点、变量定义 |
| 偏倚控制 | 随机化/盲法/混杂 或 划分/标注 或 可信度 或 应答率 |
| 分析概要 | 一段话；详细 SAP 交给 `data-analysis-planning` |
| 伦理与注册 | 批准状态、同意/豁免、注册号；详细核对交给 `research-ethics` |
| 报告规范映射 | 规范名 → protocol 章节 |

下游读取方：`research-ethics`（伦理与注册章节）、`journal-selection`（研究概要）、`data-analysis-planning`（结局、变量、分析概要；前瞻性研究还读"真实条件"里的预计事件数与数据结构）、`data-collection-tools`（变量表、数据来源、标注流程、Prompt 标准化章节）、`manuscript-writing`（Methods，含设计理由）。

## Common Mistakes（通用）

| 想法 | 现实 |
|------|------|
| "照模板写 protocol" | 设计要由真实的病例来源、事件数和资源决定，模板只用来查漏 |
| "先收数据再写 protocol" | 先写并注册 protocol 再收数据才可信；回顾性研究也要先定分析方案 |
| "混杂因素不用特别考虑" | 未调整的混杂 = 虚假关联 |
| "样本量写个大概就行 / 效应量取个常用值" | 没有依据的数字审稿人一眼看穿；参数要写出处（文献或预实验），写不出依据就写待办 |
| "主要结局多列几个，总有一个显著" | 一个主要结局；多个 = 多重比较 + 结果选择性报告 |
| "五个模块都看一遍更保险" | 只读判定的模块；混合方法才读第二个 |
| "报告规范投稿前再说" | 规范决定 Methods 要记录什么，设计阶段就要选定 |

## Convergence（通用）

当以下条件**全部**满足时，本 skill 完成：
1. Step 0 的真实条件已分析（未知项已列为待办），protocol 写明了设计理由
2. 研究类型已判定并向用户说明理由，对应模块已读取
3. 研究对象、比较/对照、数据来源已具体可操作
4. 样本量/数据规模的参数有真实出处，并已用可获得的病例数核对可行性
5. 主要结局（或主要研究问题）唯一且有定义与评估时点
6. 偏倚控制措施已按类型写入
7. 报告规范已选定并映射到 protocol 章节
8. `study-protocol.md` 已生成，模块的 Convergence 条目全部满足
9. **Hard Checkpoint 已获用户明确确认**，`status: confirmed`，`.mrp-state.json` 已更新

## Red Flags — STOP（通用）

- **禁止虚构数据、效应量或先例文献**来凑样本量
- **禁止为了配合手头的病例数反推效应量或事件率**——先有参数来源再算样本量；例数不够就改设计或写进局限
- **禁止事后更换主要结局指标**（outcome switching = 学术不端）
- **禁止跳过 Hard Checkpoint 直接进入 SAP 或数据收集**
- **禁止用一个模块的规则套另一类研究**（如用 power analysis 定定性样本量、用 kappa 评反思性主题分析）
- 用户要求"先把 protocol 写出来再定研究问题" → STOP，回到 `research-question-formulation`

## Hard Checkpoint：研究方案审批

`study-protocol.md` 生成后，**必须**向用户展示方案摘要并获得明确确认，才能进入下一步。这是流水线 3 个硬确认中的第 1 个（protocol / SAP / pre-submission）。

报告格式复用 `using-med-research-powers` 的统一 Checkpoint 报告（生成的文件 / 关键决策 / 需要注意 / 建议下一步），"关键决策"里写：**关键设计选择与理由（基于哪些真实条件，例如"只有 [年份] 的回顾性数据、每年约 [N] 例、预计 [E] 个事件 → 选 [设计]；不选 [更强的设计]，因为 [理由]"）**、研究类型、研究对象概要、样本量与依据（参数出处）、主要结局定义、对照/比较、预计周期、是否需伦理审查与注册。**只追加下面的"锁定项"段**：

```
🔒 确认后锁定的内容：
  | 锁定项 | 后续能否更改 |
  | 研究类型 | 不能更改 |
  | 主要结局指标 | 不能更改（只能添加为次要结局） |
  | 样本量目标 | 可调整但需说明理由 |
  | 纳入/排除标准 | 可微调但需在 Methods 中说明 |
  | 统计方法（SAP 中） | 偏差需在 analysis-log.md 中记录 |
请审阅方案，回复"确认"以继续；如需修改请说明具体调整内容。
```

为什么必须等确认：研究类型决定后续所有分析方法、报告规范、审稿标准；主要结局一旦确定不能随意更改；样本量决定可行性与统计功效；protocol 注册后不可大幅更改。

确认方式按用户设定的 `checkpoint_mode`：默认等待明确同意；"一直做到底"模式下只提示不等待，但锁定内容照样写进 `study-protocol.md`。

## 衔接规则

### 强制衔接（不可跳过）
- 确认后 → **自动进入 `research-ethics`**（执行其 Step 1-2：判断适用范围 + 逐条核对 checklist；伦理与注册必须在收集任何数据之前完成）
- 然后 → `journal-selection`（暂定目标期刊，软确认，可随时更换）
- 然后 → `data-analysis-planning`（制定 SAP，第 2 个硬确认）
- 涉及动物实验 → protocol 必须按 ARRIVE 2.0 写，投稿前由 `reporting-standards` 检查
- C 类涉及手术/器械创新 → 必须按 IDEAL 框架定位阶段后再选设计

### 前置依赖（不满足则阻止）
- **必须**有 `research-question.md`（`research-question-formulation`）；没有就先回去做，不要在本 skill 里临时凑 PICO
- **推荐**有 `literature-synthesis-summary.md`（缺少时提醒：效应量与 gap 定位缺文献支撑）

### 可选衔接
- 需要文献支持效应量或先例 → `literature-synthesis`（Narrative 模式即可）
- 涉及组学数据 → 参考 `${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/omics-methods.md`
- 问卷开发前需探索构念 → 先走 D. Qualitative，再回 E. Survey
- 混合方法 → 定量部分路由回 A. Clinical 或 E. Survey
- 确认后需要数据收集工具（CRF / 标注表 / 推理脚本）→ `data-collection-tools`（在 SAP 之后）
