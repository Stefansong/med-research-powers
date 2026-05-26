# Med-Research-Powers（医学科研方法论框架）

[English](README.md) | [中文](README_CN.md)

**从假设到发表 —— 一个由 AI 强制执行的科研方法论框架，在错误发生之前就把它挡住。**

Med-Research-Powers（MRP）是一个 [Claude Code](https://claude.ai/code) 插件，把 AI 智能体变成严谨的科研助手。它不让 AI 跳过文献综述、滥用统计、忽视报告规范或编造参考文献，而是用一条带硬检查点的科研主线、6 道投稿前关卡、4 位审稿人模拟来强制约束——让你交出去的每一篇稿件都经得起审查。

灵感来自 [Superpowers](https://github.com/obra/superpowers)（软件工程方法论），针对临床与生物医学研究做了改造。

> **版本 6.2.1** · 20 个 skill · 20 个斜杠命令 · MIT 许可 · 作者 BTCH Uro AI Lab

---

## 一览

| | |
|---|---|
| **Skills** | 20 个 skill，覆盖完整科研流程 |
| **斜杠命令** | 20 个命令，可直接调用 |
| **研究类型** | 临床、基础/实验、AI/ML、定性、问卷/Delphi（统一入口路由） |
| **报告规范** | 42+ 项 —— CONSORT 2025、SPIRIT 2025、STROBE、PRISMA、TRIPOD+AI 2024、DECIDE-AI、CLAIM、IDEAL、ARRIVE 2.0、COREQ、CHERRIES …… |
| **期刊模板** | 234 本期刊，覆盖 30+ 专科 |
| **统计方法** | 15+ 类方法，配前提假设驱动的决策树 |
| **Python 脚本** | 5 个内置脚本（前提检验、效能分析、分析脚手架、绘图样式、.docx 导出） |
| **投稿前检查** | 6 道强制关卡，含 PubMed MCP 引用核验 |
| **同行评审** | 4 位审稿人模拟，0–100 量化评分 |
| **硬检查点** | 4 个锁定不可逆决策的确认关卡 |
| **导出格式** | Markdown、`.docx`（python-docx）、`.xlsx`（openpyxl） |

---

## 为什么需要 MRP

AI 科研智能体每次都会犯同样的错。MRP 用强制流程取代“凭感觉”：

| 没有 MRP | 有 MRP |
|---|---|
| 直接开跑分析 | 先定义假设（PICO / FINER） |
| 挑一个“看起来对”的统计检验 | 决策树基于**已验证**的前提假设选方法 |
| 用 CONSORT 2010 | 用 CONSORT 2025（31 个编号条目 / 含子项共 34 行；已正式取代 2010） |
| 写完稿子就说“完成” | 6 道关卡不合规就不让投 |
| 自信地编造参考文献 | PubMed MCP 自动核验每一条引用 |
| 只报 `p < 0.05`，没有效应量 | 必须给效应量 + 95% CI + 精确 p 值 |
| 忽视报告规范 | 从 42+ 项里匹配研究类型对应的规范 |
| AI 数据随机划分 | 患者级划分，提示数据泄漏与外部验证 |

**核心理念 —— 强制流程，而非建议：**

1. **先定义，再设计** —— PICO/FINER，没有假设不做分析。
2. **先计划，再执行** —— 任何检验前先有统计分析计划（SAP）。
3. **先核验，再投稿** —— 6 道投稿前关卡；CONSORT 2025 合规。
4. **脚本优于提示** —— 前提检验、样本量、绘图、导出都用可复用 Python。

---

## 快速开始

### 作为 Claude Code 插件安装（推荐）

```bash
git clone https://github.com/Stefansong/med-research-powers
cd med-research-powers
```

在 Claude Code 中：

```
/plugin install ./med-research-powers
```

只有插件方式会同时启用 session-start hook（自动发现 + 路由）。

### 交互式安装脚本（备选）

```bash
git clone https://github.com/Stefansong/med-research-powers
cd med-research-powers
./install.sh
```

脚本会检测平台、提供三种方式（插件 / 复制 / 软链接）并检查 Python 依赖。注意：复制和软链接方式只安装 skill，**不会**启用 session hook。

### 验证

新开一个 Claude Code 会话，试试：

```
/mrp:research-question
```

或者直接说 *“我想做一个 AI 辅助诊断的研究”* —— MRP 会自动路由到对应 skill。

### 第一个项目

```
你：  “我想研究 AI 能不能提升 CT 上膀胱癌的检出”

MRP： 用 research-question-formulation 定义 PICO + 假设
      → literature-synthesis 检索 PubMed + 预印本
      → study-design（Type C：AI/ML）设计验证研究
      → journal-selection 选目标期刊
      → data-analysis-planning 撰写 SAP
      → …（完整主线，每步后都有检查点）
```

---

## 研究主线（Pipeline）

![Med-Research-Powers Pipeline](docs/images/architecture-pipeline.png)

```
research-question-formulation → literature-synthesis → study-design → journal-selection →
data-analysis-planning → data-collection-tools → [你收集数据] →
statistical-analysis → figure-generation →
manuscript-writing → manuscript-export → peer-review-simulation → pre-submission-verification →
submission-preparation → [投稿] → revision-response
```

- **`study-design`** 是统一入口路由，覆盖 Type A（临床）、B（基础/实验）、C（AI/ML）、D（定性）、E（问卷/Delphi）。
- **`submission-preparation`** 负责投稿信撰写 + 投稿系统指南。
- **`revision-response`** 负责修稿策略 + 逐条回复审稿意见。
- 辅助 skill（`pubmed-search`、`data-collection-tools`、`manuscript-export`、`team-collaboration`）随时可调用。

### 硬检查点（不可跳过）

以下 4 个关卡锁定不可逆决策，必须获得**明确**确认——“无响应”绝不视为通过：

1. **`study-protocol.md`** —— 锁定研究类型 + 主要结局（事后改主要结局 = outcome switching）。
2. **`analysis-plan.md`（SAP）** —— 锁定分析策略（防 p-hacking 的核心机制）。
3. **`journal-selection-report.md`** —— 锁定目标期刊（决定后续格式与规格）。
4. **`submission-readiness-report.md`** —— 6 道关卡全部通过才能投稿。

### 快速模式与回溯

- **Fast-Track 快速模式** —— 当你说“一直做到最后 / 不用问我”，MRP 只在 4 个硬检查点暂停，软步骤自动推进。
- **回溯链接** —— 在下游发现问题（如投稿前检查时报告规范不合规）可回到上游 skill，修改后的产物会被重新验证。

---

## 20 个 Skill

### 主线 skill

| # | Skill | 何时使用 |
|---|-------|---------|
| 1 | **research-question-formulation** | 模糊想法需要明确的问题 + 假设（PICO/PIRD/FINER）。 |
| 2 | **literature-synthesis** | 系统检索与综述文献、寻找 research gap（PRISMA 流程）。 |
| 3 | **study-design** | 设计任意研究方案——临床/基础/AI-ML/定性/问卷（Type A–E 路由）。 |
| 4 | **journal-selection** | 选目标期刊（评分匹配 + 三梯队级联策略）。 |
| 5 | **data-analysis-planning** | 在任何检验**之前**撰写 SAP（statistical-analysis 的前置）。 |
| 6 | **data-collection-tools** | 根据 protocol 生成 CRF、标注表、REDCap 表、推理/评估脚本。 |
| 7 | **statistical-analysis** | 在真实数据上执行分析（需先完成 SAP）。 |
| 8 | **figure-generation** | 出版级图表（期刊样式、≥300 DPI、色盲友好）。 |
| 9 | **manuscript-writing** | 撰写原始研究或综述（5 种综述类型）。 |
| 10 | **manuscript-export** | 把 Markdown 导出为符合期刊排版的 `.docx`。 |
| 11 | **reporting-standards** | 把研究类型匹配到正确规范并检查合规。 |
| 12 | **peer-review-simulation** | 投稿前模拟同行评审（4 审稿人 + 0–100 评分）。 |
| 13 | **research-ethics** | 检查 IRB/IACUC、知情同意、隐私、注册、COI；起草伦理声明。 |
| 14 | **pre-submission-verification** | **强制** 6 道关卡终检——全部通过才能投。 |
| 15 | **submission-preparation** | 写投稿信 + 投稿系统指南（ScholarOne / Editorial Manager）。 |
| 16 | **revision-response** | 制定修稿策略 + 起草逐条回复信（rebuttal）。 |

### 辅助 / 元 skill

| # | Skill | 何时使用 |
|---|-------|---------|
| 17 | **pubmed-search** | 用 PubMed MCP 检索、核验引用、批量取元数据。 |
| 18 | **team-collaboration** | 项目适合多 agent 并行（通过 Task 工具派发）。 |
| 19 | **using-med-research-powers** | 编排器——路由、检查点、流程状态、用户记忆。 |
| 20 | **writing-mrp-skills** | 创建、测试、改进 MRP skill。 |

---

## 20 个斜杠命令

每个 skill 都可用自然语言触发；命令提供直接入口。

| 命令 | 作用 |
|------|------|
| `/mrp:research-question` | 把模糊想法变成 PICO 问题 + 假设 |
| `/mrp:literature-synthesis` | 系统文献检索与综述（PRISMA + gap map） |
| `/mrp:study-design` | 为任意研究类型设计方案（临床/基础/AI/定性/问卷） |
| `/mrp:journal-selection` | 选最合适的目标期刊（评分匹配 + 三梯队级联） |
| `/mrp:analyze-data` | 先计划**再**执行统计分析（计划 → 执行） |
| `/mrp:data-collection-tools` | 根据 protocol 生成 CRF、标注表与脚本 |
| `/mrp:figure-generation` | 出版级图表（期刊样式、≥300 DPI、色盲友好） |
| `/mrp:write-manuscript` | 撰写医学研究稿件 |
| `/mrp:manuscript-export` | Markdown → 符合期刊排版的 `.docx` |
| `/mrp:reporting-standards` | 把研究类型匹配到报告规范 |
| `/mrp:check-standards` | 报告规范合规检查（投稿前检查的 Gate 1） |
| `/mrp:pre-submission` | **强制** 6 道投稿前关卡核验 |
| `/mrp:peer-review` | 模拟同行评审（4 审稿人 + 评分） |
| `/mrp:research-ethics` | 检查伦理合规并起草伦理声明 |
| `/mrp:pubmed-search` | 检索 PubMed / 核验引用 / 取元数据 |
| `/mrp:submission-preparation` | 写投稿信 + 投稿系统指南 |
| `/mrp:revision-response` | 制定修稿策略 + 起草逐条回复 |
| `/mrp:team-collaboration` | 运行多 agent 并行科研任务 |
| `/mrp:using-mrp` | 编排器——路由规则、流程与检查点 |
| `/mrp:writing-mrp-skills` | 创建、测试、改进 MRP skill |

---

## 研究设计路由（Type A–E）

`study-design` 是单一入口，自动路由到对应方法学与报告规范：

| 类型 | 领域 | 示例 | 主要规范 |
|------|------|------|---------|
| **A** | 临床 | RCT、队列、横断面、交叉、非劣效、适应性、真实世界、注册研究 | CONSORT 2025 / SPIRIT 2025 / STROBE |
| **B** | 基础 / 实验 | 细胞、动物、分子（WB、qPCR、ELISA、流式、IF） | ARRIVE 2.0 |
| **C** | AI / ML | 影像、视频、LLM、器械 | TRIPOD+AI 2024 / DECIDE-AI / CLAIM / IDEAL |
| **D** | 定性 | 访谈、焦点小组、扎根理论、混合方法 | COREQ / SRQR |
| **E** | 问卷 / Delphi | 问卷、量表开发/验证、共识研究 | CHERRIES |

多类型研究可叠加相应模块。AI/ML 模块强制患者级数据划分、4 档样本量策略、类别不平衡处理与决策曲线分析（DCA）。

`manuscript-writing` 同样支持原始研究**以及** 5 种综述：叙述性、系统、meta 分析、scoping、mini-review。

---

## 报告规范（42+）

完整的机读索引见 [`skills/reporting-standards/references/checklists/standards-index.yaml`](skills/reporting-standards/references/checklists/standards-index.yaml)，结构化的 CONSORT 2025 清单见 [`consort-2025.yaml`](skills/reporting-standards/references/checklists/consort-2025.yaml)。

重点：**CONSORT 2025**（31 个编号条目 / 34 行）· **SPIRIT 2025** · **STROBE** · **PRISMA 2020** · **TRIPOD+AI 2024** · **DECIDE-AI** · **CLAIM 2020** · **IDEAL** · **ARRIVE 2.0** · **COREQ** · **SRQR** · **CHERRIES** · **STARD** · **CARE** 等。

> CONSORT 2010 已被正式取代 —— MRP 始终路由到 CONSORT 2025。

---

## 期刊模板（234）

**234 本期刊、覆盖 30+ 专科**的排版要求（字数限制、摘要格式、参考文献风格、章节结构、特殊栏目、投稿信与 ORCID 要求、投稿系统）见 [`skills/manuscript-writing/references/journal-templates.yaml`](skills/manuscript-writing/references/journal-templates.yaml)。

覆盖专科包括综合医学、肿瘤、心血管、消化/肝病、呼吸、神经、感染、血液、风湿免疫、肾脏、内分泌、精神、外科、泌尿、影像、AI/数字健康、儿科、妇产、急危重症、麻醉、骨科、眼科、皮肤、病理、耳鼻喉、公共卫生等。若某期刊未收录，MRP 会通过网络检索其“Instructions for Authors”。

---

## 统计分析

- **先计划**：`data-analysis-planning` 产出锁定的 SAP；没有 SAP，`statistical-analysis` 不能运行。
- **前提驱动**：[前提检验决策树](skills/data-analysis-planning/references/stat-method-decision-tree.yaml)自动选择参数 vs 非参数方法。
- **15+ 类方法**：均值比较、分类、相关/回归、生存、诊断准确性、纵向/混合模型、多重比较校正、组学，以及 AI/ML 评估（AUROC/AUPRC、DeLong、校准、DCA、自助 CI）。
- **可复现输出**：每次运行都产出清洗日志、分析日志、结果摘要，以及在 `data_clean.csv` 上运行的可复现脚本。

---

## 投稿前核验（6 道关卡）

`pre-submission-verification` 是强制环节，任一关卡不过就不让投稿：

1. **Gate 1 — 报告规范**（规范正确、条目全部映射）
2. **Gate 2 — 统计**（效应量、CI、精确 p 值、敏感性分析）
3. **Gate 3 — 引用核验**（每条引用经 PubMed MCP 核验）
4. **Gate 4 — 图表质量**（分辨率、色盲友好、图注）
5. **Gate 5 — 伦理与合规**（IRB/知情同意/注册/COI）
6. **Gate 6 — 形式**（结构、字数/参考文献限制、格式）

---

## 同行评审模拟（4 审稿人）

`peer-review-simulation` 派发 4 位审稿人，给出按目标期刊梯队校准的 0–100 评分：

- **R1 — 方法学** · **R2 — 临床/领域专家** · **R3 — 学术编辑** · **R4 — Devil's Advocate**

每位审稿人对 8 个维度打分，并按严重度（Critical / Major / Minor）标记问题，直接喂给 `revision-response`。

---

## 内置 Python 脚本

可复用、可调用的代码（不必每次从提示重写）：

| 脚本 | 用途 |
|------|------|
| `statistical-analysis/scripts/assumption_tests.py` | 正态性、方差齐性、完整前提检查；Cohen's d |
| `statistical-analysis/scripts/power_analysis.py` | 两组、诊断、生存设计的样本量/效能 |
| `statistical-analysis/scripts/analysis_template.py` | 在 `data_clean.csv` 上运行的可复现分析脚手架 |
| `figure-generation/scripts/pub_style.py` | 期刊图表样式、色盲友好配色、显著性标注 |
| `manuscript-export/scripts/export_docx.py` | 由期刊模板库驱动，Markdown → 符合期刊排版的 `.docx` |

---

## 流程状态与用户记忆

MRP 可以把项目状态和你的偏好**本地**保存在项目目录：

- **`.mrp-state.json`** —— 流程进度、已完成 skill、产物、当前阶段。新会话开始时 MRP 会提议续做：*“上次完成到 X，下一步 Y，继续？”*
- **`.mrp-user-profile.json`** —— 你的身份、研究领域、常投期刊、熟悉/不熟悉的方法、偏好的统计工具与图表风格。首次通过简短自我介绍建立，之后静默更新。

Schema 见 [`skills/using-med-research-powers/references/state-schemas.md`](skills/using-med-research-powers/references/state-schemas.md)。

**隐私：** 这些文件只存于本地项目目录，绝不上传。可随时删除，或说“忘记我的 [某项]”。MRP 绝不记录密码、患者数据或伦理批准号。

---

## 环境要求

- **Claude Code**（CLI、桌面端、网页端或 IDE 扩展）。
- **Python 3** 及 `pandas`、`numpy`、`scipy`、`statsmodels`、`matplotlib`、`python-docx`、`openpyxl`，用于统计、绘图与导出脚本（安装脚本会检查）。
- **PubMed MCP**（可选但推荐），用于引用核验与文献检索——工具以 `mcp__claude_ai_PubMed__*` 形式引用。

---

## 仓库结构

```
med-research-powers/
├── .claude-plugin/        plugin.json、marketplace.json
├── commands/              20 个斜杠命令（薄路由 → skill）
├── skills/                20 个 skill，每个含：SKILL.md + references/ + scripts/
├── hooks/                 session-start.sh（自动发现 + 路由）
├── docs/                  architecture.md、USER-MANUAL.md
├── install.sh             交互式安装脚本
├── README.md / README_CN.md
└── CHANGELOG.md
```

每个 skill 把推理逻辑留在 `SKILL.md`，把查表、模板、清单放进 `references/`，把可复用代码放进 `scripts/`——既保持上下文精简，又便于维护。

---

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。新 skill 遵循 `writing-mrp-skills` 规范：仅触发条件的 `description`（≤200 字符）、标准章节集合（Overview、When to Use、When NOT to Use、Workflow、Output、Common Mistakes、Convergence、Red Flags、衔接规则）、查阅型内容放 `references/`、固定代码放 `scripts/`。

---

## 许可与致谢

- **许可：** MIT（见 [LICENSE](LICENSE)）
- **作者：** BTCH Uro AI Lab
- **灵感来源：** [Superpowers](https://github.com/obra/superpowers)（作者 obra）

*Med-Research-Powers 强制方法论，但不替代你的判断、你的伦理委员会或你的统计师。请始终确认伦理状态，并请合格专家复核分析。*
