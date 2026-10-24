---
name: data-analysis-planning
description: Use when no analysis-plan.md exists yet, or only a descriptive one and outcome analyses are needed（没有分析计划或只有描述性计划时先制定）. Triggers on "帮我分析数据"、"用什么统计方法"、"分析策略"、"SAP"、"分析计划".
---

# Data Analysis Planning

## Overview

先弄清数据的真实情况和研究要回答的问题，再为这份数据定制统计分析计划（SAP），用户确认后才执行。四步：

1. **分析现状**：已有数据先做体检；数据还没收集就分析 protocol、CRF 和预期的数据特点；同时理清研究问题和约束（样本量、事件数、期刊要求）。
2. **定制 SAP**：每个方法和参数都要能从第 1 步的现状说出理由；SAP 的章节只用来检查有没有漏项，不是填空表。
3. **用户确认**：`analysis-plan.md` 是流水线的**硬确认 2**，用户明确同意后才能进入数据收集与分析。
4. **交给 `statistical-analysis` 执行**：执行时的任何偏离都记进 `analysis-log.md`。

> 总调度规则（直接调用本 skill 也适用，原文见 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`）：**结局盲**——计划前只看数据的结构和质量（Step 1），不看任何变量与结局的关系（交叉表、组间比较、相关、单因素筛选、试跑模型）；**患者级数据不进对话**——只看 `data_profile.py` 这类脚本输出的汇总；**缺前置产物**——说缺什么，light / auto 下先往下做并记缺口，不拒绝；**checkpoint_mode** 默认 light，但 SAP 是硬确认 2；**只要一个产物**时交付后停下。

看了结构再调整计划是合理且必要的（Step 2 第 3 点），调整写进 SAP 第 1 节。

## When to Use

- 研究方案（`study-protocol.md`）已确认，要在收集或分析数据之前定统计方法
- 回顾性研究的数据已经在手，但还没有 `analysis-plan.md`（没有 protocol 时走 Step 0 的快速路径）
- 用户说"帮我分析数据"但项目里还没有 `analysis-plan.md`
- 已确认的 SAP 只有描述性部分（Step 0 只为 Table 1 写的），现在要做结局分析或按组的结局图 → 补全这份 SAP（见 Step 0），不算 post hoc
- 审稿人要求补充 SAP

## When NOT to Use

- 已有确认的 `analysis-plan.md`，要执行其中的分析 → `statistical-analysis`（SAP 之外的新分析也在那里做，标 post hoc）
- 还没有研究方案、数据也还没收集 → `study-design`（SAP 里的结局、变量、样本量都来自 protocol）
- 还没有明确的研究问题 → `research-question-formulation`

## Workflow

### Step 0: 读取用户偏好与前置产物

1. 统计工具：用户已说明就用；否则读 `~/.claude/mrp-user-profile.json` 的 `preferred_stats_tool`；没有设置时默认 Python，不为此停下来问，在 SAP 草稿里写明"统计工具：Python（要用 R / SPSS / Stata 请说明，可保存为偏好）"。SAP 里推荐的包和代码示例按此语言写。
2. 读取 `study-protocol.md`：研究类型（Type A–E）、主要/次要结局、变量、样本量与先验效应量、分组与分层因素。
   **快速路径**（数据已在手、没有 protocol）：先体检（Step 1a），然后**只停一次**——同一条消息里：说明缺 protocol（记为缺口，要先补就说）；列出需要用户回答的问题（研究问题、主要结局的定义与时点、纳入/排除标准；能从数据和用户原话推断的给出推断值请用户核对）；附上据此写好的 SAP 草稿和 Step 4 的锁定项。用户一次回复即同时回答问题并完成硬确认 2（有修改就改完再给一次锁定项）。没有伦理记录时在同一条消息里提醒（回顾性研究也要审查或豁免）并记为缺口。
   **只要描述性结果**（如"给我出 Table 1"、人数流程）：快速 SAP 只写第 1–3 节，外加分组变量（按暴露 / 治疗分组，或不分组）、要列的变量和每个变量的汇总方式；不需要主要结局。确认后交给 `statistical-analysis`，它只执行这些条目、出完 Table 1 就停。按结局分组的"Table 1"（复发 vs 未复发）是在看变量与结局的关系——要么写进完整 SAP 作为预定分析，要么标 exploratory。之后要做结局分析时回本 skill 补全这份 SAP（版本号加一，第 1–3 节保留并按需更新，补写第 4–7 节，再过硬确认 2）；这是计划内的分析，不按 post hoc 做。
3. 若有 `journal-selection-report.md`（暂定期刊），记下其统计报告要求（如强制 CI、禁止基线 p 值）。
4. 读 `python3 "${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py" show --json` 的 notes：写着"SAP 前看过"的（SAP 确认前已经看过的结局关系，如探索性的分组 KM 图）照录进 SAP 第 1 节，并告诉用户这些不再用来选方法。

### Step 1: 数据现状分析（写 SAP 之前必须做）

**(a) 已有数据（回顾性研究、数据已收集）**

1. 先体检（只读，不改数据）：
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/data_profile.py" <数据文件> \
     --id <患者ID列> --outcome <结局列> --report data-profile.md
   ```
   xlsx 用 `--sheet` 选工作表；生存结局加 `--time <随访时间列>`；中心/术者列可用 `--cluster` 指定；报告把某个整数列当成 ID、其实是测量值（费用、计数）时加 `--not-id <列>` 重跑（列名里有换行的，用空格代替）。报告说第一行"已按没有表头处理"、而第一行其实是列名时，加 `--header` 重跑（指定的列找不到时，出错信息也会这样提示）。报告列类型、伪装缺失、截断值、数值存成文本（含 ↑↓ H L * 异常标记和数值列里的文字）、日期、缺失比例、离群计数、分类取值、重复 ID 与聚类、结局事件数（有 `--id` 时按患者计）、疑似隐私字段（只报列名；也按取值识别姓名、地址、病历号样式的列）、把几行并进一格的引号错误；它不算任何变量与结局的关系。按取值判为 ID 的整数列会在问题清单里列出，并给出要加的 `--not-id`。
2. 体检没覆盖的结构问题，按需现写**只读**检查代码（多张表按患者 ID 关联后还剩多少人、每人几条记录、每个中心/术者的例数、每人随访几次）。只统计结构，**不按结局或暴露分组算任何东西**，不改原始数据。
   预测变量之间的冗余检查（严重共线）只用真正的基线预测变量。随访时间、末次随访日期、复发部位、死亡原因、复发后治疗等**由结局派生或基线之后才产生的变量**不是预测变量：不进冗余检查，也不进候选变量表；发现数据里有这类列，在 SAP 第 2 节写明排除。
3. 有疑似隐私字段（姓名、身份证号、手机号、住院号等）→ 提醒用户在分析前去标识化；SAP 和后续产物里不出现这些值。隐私识别按列名和取值样式，认不出的标识（写法少见的人名、没有门牌号的地址等）仍可能出现在报告里：报告外发前人工看一遍。

**(b) 数据还没收集（前瞻性研究）**

分析 protocol 与 CRF/数据字典：每个变量的类型与编码、预计事件数（样本量 × 预期发生率）、聚类结构（每人几条记录、几个中心、几位术者）、哪些变量可能缺失及大概比例。写好"**数据到手后与预期不符时怎么办**"的预案，例如：事件数明显少于预期 → 按临床知识减少候选参数（合并类别、删去次要变量），仍不够就延长收集或把模型标为探索性（惩罚回归代替不了足够的事件数，见回归方法卡）；某关键变量缺失比预期多 → 按 yaml `missing_data` 重新论证缺失机制（"是否完整"可能与结局有关时用多重插补，并做 MNAR 敏感性分析），不按缺失百分比换方法。拿到数据后 `statistical-analysis` Step 1 会再体检，按预案处理并记录偏离。

两种情况的结论都整理成 SAP 第 1 节（见 Step 3）。

### Step 2: 选方法

1. 用 `references/stat-method-decision-tree.yaml` 缩小范围：两组连续变量先分配对/独立，独立两组默认 Welch t 检验，预期明显偏态、有序或有界时才预先改用秩检验或变换（不按前提检验的 p 值挑）；两组 × 有序结局用 Mann-Whitney / CMH 或比例优势回归，有序分组 × 二分类结局用 Cochran-Armitage 趋势检验或把等级当数值评分的 logistic 回归（2×K 表的趋势检验两个方向都成立，见 yaml）。缺失数据的规则**只在** yaml 的 `missing_data` 维护。
2. 只读本研究用到的方法要点卡（每张写了计划前看数据的什么、计划里必须写明什么、推荐的成熟包、常见的坑、必须报告的指标）：

| 分析内容 | 要点卡 |
|---|---|
| 基线表、两组/多组比较、效应量 | `references/method-cards/baseline-and-group-comparison.md` |
| 解释性回归、临床预测模型、列线图、内部/外部验证 | `references/method-cards/regression-and-prediction-models.md` |
| KM、log-rank、Cox、竞争风险、不朽时间偏倚 | `references/method-cards/survival-analysis.md` |
| 倾向性评分匹配/加权、平衡性检查、E-value | `references/method-cards/propensity-score.md` |
| 缺失机制、多重插补与合并、敏感性分析 | `references/method-cards/missing-data.md` |
| 诊断准确性、ROC/AUC、阈值、读片者研究、校准与 DCA | `references/method-cards/diagnostic-accuracy-and-ai-evaluation.md` |
| 同一患者多条记录、多中心、术者聚类（GEE / 混合模型） | `references/method-cards/clustered-and-repeated-data.md` |
| Meta 分析 | `references/method-cards/meta-analysis.md` |
| kappa、ICC、Bland-Altman、分割标注一致性 | `references/method-cards/agreement-and-reliability.md` |
| LLM/VLM 评测 | `references/method-cards/llm-vlm-evaluation.md` |

3. 每个选择都要回到 Step 1 的现状说明理由，例如：
   - 事件数 → 多因素模型能纳入几个预测变量（按 Riley 标准核对；不够就按临床知识预先减少变量、合并类别；惩罚回归能减轻过拟合，但事件很少时它本身也不稳定，代替不了足够的样本量，见回归方法卡）
   - 同一患者多条记录 / 多中心 / 同一术者多台手术 → GEE、混合模型，或按患者汇总
   - 可能的缺失机制、缺的是哪些变量、"是否完整"会不会与结局有关 → 完整病例分析还是多重插补（m 份 + Rubin 合并），以及 MNAR 敏感性分析；缺失比例要报告、决定 m，但不按百分比阈值选方法（yaml `missing_data`）
   - 截断值、编码混乱、单位不统一 → 在第 2 节写清处理规则
   - 某组人数很少、某类取值很少 → 精确检验、合并类别或换指标

   前提假设在 SAP 里写明怎么诊断（残差图、Q-Q 图、`${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/assumption_tests.py`）和明显偏离时的预定备选。

### Step 3: 写 `analysis-plan.md`

每节按本研究的实际情况写；不适用的写"不适用 + 理由"；不照抄本文件或要点卡里的示例数字和措辞。

#### 1. 数据现状与由此做出的选择
- 数据来源、采集时间、行数与患者数（protocol 预期 vs 实际）、变量清单及类型、层级关系（每人几条记录、几个中心/术者）
- 体检结论：结局事件总数、各分组人数、关键变量的缺失比例与形式、截断值、编码与单位问题（引用 `data-profile.md`；前瞻性研究写预期值与预案）
- 由此做出的选择：逐条写"现状 → 选择 → 理由"，分析单位、主要方法、协变量个数、缺失处理等每个设计选择都要有一条

#### 2. 数据预处理
- **缺失值**：按 yaml `missing_data`（按可能的缺失机制和"是否完整是否与结局有关"选，Hughes 2019 的判断规则）写每个关键变量的缺失比例、可能的机制及理由、处理策略、Rubin 合并、MNAR 敏感性分析
- **伪装缺失与截断值**：哪些写法算缺失（"未查"、"/"、999 …）；"<0.1" 这类值怎么处理（取检测限、检测限的一半，或按删失数据处理）及理由
- **异常值**：检测方法（IQR / Z-score / 临床合理范围）+ 处理策略（保留并标注 / Winsorize / 移除并做敏感性分析）——策略在这里定，`statistical-analysis` 只执行
- 数据转换、单位统一、变量重编码、派生变量定义；多张表的合并与按患者汇总规则

#### 3. 描述性统计
- 连续变量：均值±SD（近似正态）或中位数(IQR)（偏态）；分类变量：频数(%)
- 组间基线比较：RCT 用 SMD、不做 p 值检验；观察性研究可报 p 值或 SMD

#### 4. 主要分析
为每个研究目标写明：统计方法及选择理由（对应第 1 节）、前提假设及诊断方式（残差 / Q-Q 图、配对差值、比例风险、球形性）、明显偏离时的预定备选方法、效应量指标 + 95% CI、协变量与调整策略、执行时要读的方法要点卡。

#### 5. 次要分析和亚组分析
预先指定的亚组及其合理性说明、交互效应检验（报告交互 p 值，不只报亚组内 p 值）、亚组数 >3 时的校正。

#### 6. 敏感性分析
至少一种替代方法、缺失数据敏感性（完整病例 vs 插补；MNAR tipping point）、异常值影响、（观察性研究）未测混杂 E-value、（聚类数据）换一种聚类处理方式。

#### 7. 多重比较策略
- 主要结局：不校正（单一主要结局）
- 多个次要结局：Bonferroni / Holm / FDR
- 组学数据：BH-FDR；置换检验 ≥1000 次、bootstrap ≥2000 次（yaml `resampling`）

组学研究 → 参考 `references/omics-methods.md`（非靶向/靶向代谢组学、蛋白质组学、转录组学/基因组学、单细胞转录组、多组学整合）。

#### 8–16. AI/ML 研究追加部分
研究类型为 AI/ML（study-design Type C）时追加 9 个部分，内容要求见 `references/ai-ml-sap-extension.md`：

8 模型架构选择 · 9 训练策略（超参可复现） · 10 数据划分方案 · 11 数据增强策略 · 12 类别不平衡处理 · 13 消融实验 · 14 模型比较统计检验 · 15 模型可解释性方案 · 16 不确定性量化

三条硬规则（其余见 reference）：
- 验证与数据划分规则只在 yaml 的 `deep_learning_training.data_split` 维护：按模型类型和有效样本量（按患者计的事件数）选，不按总人数分档——回归类预测模型用全部数据建模 + bootstrap 乐观校正（不做随机 hold-out），要调参的 ML/DL 用嵌套交叉验证或事件数足够的按患者划分，外部 / 时间验证优先；**必须按患者 ID 划分并按结局分层**，报告随机种子与各集合的患者数、事件数和类别分布
- 评估指标、数据划分、Ground Truth 定义必须与 Type C `study-protocol.md` 一致；新增指标标记 post-hoc / exploratory
- 不能只报点估计：每个指标 95% CI + 比较检验（DeLong / McNemar / bootstrap / 置换）

### Step 4: 硬确认 2

把关键锁定项列给用户：第 1 节里最关键的几条"现状 → 选择"、主要结局及其分析方法、亚组清单、缺失/异常值策略、多重比较策略、AI 研究的数据划分与指标（只要描述性结果时：分组变量、变量清单与汇总方式、缺失处理）。快速路径下这一步和 Step 0 的问题是同一条消息。**等用户明确同意**后在文件头写 `status: confirmed` 与日期，并执行 `python3 "${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py" checkpoint sap confirmed`。auto 模式按总调度照写 `confirmed_by: auto`，摘要里提醒用户这份 SAP 还没人审过。

### Step 5: 更新项目状态

输出 3–5 行摘要，然后 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py done data-analysis-planning --output analysis-plan.md [--output data-profile.md] --next <data-collection-tools（数据还要收集）| statistical-analysis（数据已在手）>`。用户要的是结果（Table 1、一张图）而不只是 SAP 时，确认后直接进入 `statistical-analysis`；只要 SAP 时交付后停下。

## Output

- `analysis-plan.md`（SAP，Statistical Analysis Plan）
  - 临床/基础/调查研究：第 1–7 部分；AI/ML 研究：第 1–16 部分（第 8–16 部分按 `references/ai-ml-sap-extension.md`）；只要描述性结果的快速 SAP（Step 0）：第 1–3 部分 + 分组变量与各变量的汇总方式
  - 文件头：`status: draft | confirmed`、确认日期、对应的 `study-protocol.md` 版本、所用统计工具（来自 preferred_stats_tool）、已有数据时写体检的数据文件名与 sha256
- `data-profile.md`（已有数据时）：`data_profile.py` 生成的体检报告，SAP 第 1 节引用
- 定稿后的任何偏离由 `statistical-analysis` 记录在 `analysis-log.md` 并说明理由

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "分析很简单不需要计划" | 无计划 = p-hacking 的温床 |
| "'未查'、'/'、999 读进来就是正常值" | 先体检；哪些写法算缺失、截断值怎么处理要在第 2 节写明 |
| "只分析主要结局就行" | 必须预先指定所有计划分析 |
| "缺失数据直接删掉" / "缺失超过某个百分比就必须插补" | 按可能的缺失机制和"是否完整是否与结局有关"选策略（yaml `missing_data`）并预先写明；比例不是选方法的依据 |
| "两组比较先做正态性、方差齐性检验再挑方法" | 方法在 SAP 里预先定：独立两组默认 Welch，配对默认对差值做配对 t 检验；前提检验只作诊断 |
| "样本多（如 >1000 例）就按 60/20/20 随机拆分" | 划分按模型类型和事件数定：回归类预测模型不做随机拆分，用 bootstrap 内部验证；外部 / 时间验证优先（yaml `data_split`） |
| "有序结局只能用某一种检验" | 两组 × 有序结局用 Mann-Whitney/CMH 或比例优势（有序 logistic）回归；2×K 表的 Cochran-Armitage 趋势检验两个方向都成立，结果与 Mann-Whitney 接近 |
| "不需要敏感性分析" | 审稿人一定会要求 |

## Convergence

当以下条件全部满足时完成：
1. SAP 第 1 节写明了数据现状（已有数据：体检结论；前瞻性研究：预期特点与预案）和每个选择的理由
2. 每个统计方法的前提假设与备选方法已列出
3. 多重比较校正策略已确定
4. 缺失数据与异常值处理策略已明确（引用 yaml 规则并写明所选项）
5. 敏感性分析已规划
6. AI/ML 研究：第 8–16 部分齐全，指标与 protocol 一致
7. `analysis-plan.md` 已生成并经用户确认（硬确认 2），`.mrp-state.json` 已更新

只写描述性部分的快速 SAP（Step 0，如只为 Table 1）：第 2、3、5 项不适用，第 4 项只写缺失与异常值在描述表里怎么呈现。

## Red Flags — STOP

- **计划前已经算过变量与结局的关联**（违反结局盲规则）→ 停：这些结果不能用来选方法；告诉用户看过什么，并在 SAP 第 1 节如实记录
- **禁止在执行分析后修改主要结局或主要分析方法**（偏离须记录在 `analysis-log.md`）
- **禁止反复尝试多种方法只报告"显著"的那个**（p-hacking）
- **禁止把未预先指定的亚组分析当作确证性结论**（必须标记 exploratory）
- **AI/ML：禁止用测试集调参或在测试集上做数据增强**（数据泄漏）
- **AI/ML：禁止只报告点估计**（必须有 95% CI 和统计检验）
- 没有 `study-protocol.md`、也没问清主要结局（只要描述性结果时：分组变量）就锁定 SAP → 停，先走快速路径或 `study-design`
- 已有数据却没做 Step 1 体检就写 SAP → 停，先体检

## 衔接规则

### 前置依赖（缺了按总调度"缺前置产物时"处理）
- 已确认的 `study-protocol.md`（`study-design`，硬确认 1）；数据已在手时可走 Step 0 快速路径
- 已完成 `research-ethics`（伦理/注册在收集数据之前；回顾性数据也要审查或豁免）
- **推荐**有 `journal-selection-report.md`（暂定期刊的统计报告要求，软确认，可随时更换）
- 已有数据时数据文件必须可读（Step 1a）；还没有数据时按 Step 1b 分析 protocol 与 CRF

### 强制衔接（不可跳过）
- `analysis-plan.md` 经硬确认 2 后 → 数据还要收集：`data-collection-tools`（按 SAP 的变量名与数据格式生成收集工具）；数据已在手：直接 `statistical-analysis`
- 数据收集完成后 → `statistical-analysis` 按本计划执行（开头会再体检一次，对照 SAP 第 1 节）
- 最后一步固定为更新 `.mrp-state.json`（Step 5）

### 可选衔接
- 组学数据 → `references/omics-methods.md`
- AI/ML → `references/ai-ml-sap-extension.md`；报告规范逐条清单 → `reporting-standards`
- 审稿阶段补充分析（`revision-response`）→ 不改 SAP，在 `statistical-analysis` 按其 Step 4 末尾作 post hoc / exploratory 分析；只有要替换 SAP 里原有的分析时才回本 skill 修订（回溯表第一条）
