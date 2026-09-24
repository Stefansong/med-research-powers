---
name: data-collection-tools
description: Use when data still have to be collected and collection tools must be built from the protocol and SAP. Triggers on "生成标注表"、"做个数据收集表"、"写推理脚本"、"随机分组"、"数据划分"、"CRF"、"数据录入表"、"REDCap".
---

# Data Collection Tools

## Overview

根据已确认的研究方案（`study-protocol.md`）、分析计划（`analysis-plan.md`）和**真实的数据来源**，生成本研究真正需要的数据收集工具——标注模板、推理脚本、数据录入表、随机分组表、数据划分脚本等。顺序固定：先分析要收哪些变量、数据实际从哪来、谁来填 → 列出工具清单和理由 → 按 checkpoint_mode 确认 → 再生成。`references/tool-catalog.yaml` 只是可选工具目录，不是必须全套生成。填补 data-analysis-planning → statistical-analysis 之间的执行空白：工具的变量名、格式、分组、划分都要和 SAP 对得上，否则分析阶段要返工。

## When to Use

- `analysis-plan.md` 已确认（硬确认 2 通过），要准备数据收集工具
- 需要 AI 推理脚本（VLM/LLM benchmark 研究）
- 需要专家标注/评分模板、临床数据录入表（CRF）、数据管理目录结构
- 需要随机分组表（RCT）或患者级数据划分（AI 研究）

## When NOT to Use

- 还没有研究方案 → 先完成 `study-design`
- 还没有分析计划 → 先完成 `data-analysis-planning`（变量名和数据格式由它决定）
- 数据已经收集好（回顾性研究、已有导出表）→ 不需要本 skill，SAP 确认后直接 `statistical-analysis`
- 需要执行统计分析 → `statistical-analysis`
- 需要执行 AI 推理（不是生成脚本）→ 用户自行运行脚本

## Scripts

两个固定逻辑的脚本在插件目录，运行目录是用户项目，用 `${CLAUDE_PLUGIN_ROOT}` 定位；生成项目工具时**复制或调用**它们，不要临场重写（数据泄漏的高风险点）：

| 脚本 | 用途 | 一行可运行示例 |
|------|------|---------------|
| `patient_level_split.py` | 患者级 train/val/test 或 K 折划分，可按标签分层，固定 seed，输出各集类别分布 + 泄漏检查 | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/data-collection-tools/scripts/patient_level_split.py" labels.csv --patient-col patient_id --label-col label --seed 42 --out-dir data/splits` |
| `randomization.py` | 简单 / 区组 / 分层随机分组表 + 汇总（seed 的规矩见 C 节） | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/data-collection-tools/scripts/randomization.py" --method stratified --n-per-stratum 40 --strata site=A,B sex=M,F --arms Control,Treatment --out tools/allocation.csv` |

这两个是护栏脚本（出错会让研究作废，而且肉眼很难发现），所以固定下来；其余工具（CRF、数据字典、提取表、推理脚本等）都按本研究的真实数据来源现写。表中命令的参数只是示例：列名、分层因素、每层例数、划分的 seed 一律按 protocol / SAP 填（随机分组的 seed 见 C 节）。

样本量不在本 skill 算：protocol 的先验样本量用 `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py`（见 `references/tool-catalog.yaml`）。

## Study Type Router

常见工具组合如下，只作参考；实际要哪些，由 Step 2 的真实数据来源分析和 Step 3 的清单决定。

```
研究类型（study-protocol.md 的 type 字段）？
├── AI/ML Benchmark（VLM/LLM 评估）
│     → Prompt 模板 + 推理脚本 + 标注表 + 评分表 + 分析脚本
├── AI 诊断/预测模型
│     → 数据提取表 + 标注表（Ground Truth）+ 患者级划分脚本 + 评估脚本
├── 临床研究（RCT / 队列 / 横断面）
│     → CRF（病例报告表）+ 数据字典 + 筛选表 + 随机分组表（RCT）
├── 基础实验
│     → 实验记录表 + 数据录入模板 + 图像采集规范
└── 系统综述 / Meta 分析
      → 数据提取表 + 偏倚评估表 + PRISMA 流程图模板
```

## Workflow

### Step 1: 解析研究方案与分析计划 → 变量需求清单

```
读取 study-protocol.md → 研究类型、样本量与分组、变量列表、结局指标、数据来源、标注/评估流程
读取 analysis-plan.md  → 变量命名（snake_case）、编码与单位、数据格式（长表/宽表）、分层因素、划分方案与 seed
```

列出"需要收集的变量清单"：每个变量对应 SAP 的哪一条（主要结局 / 协变量 / 分层因素 / 划分标签……）、在哪些时点测量。SAP 用不到的变量不收，也不能超出伦理批准的范围。两份文件冲突时以 `analysis-plan.md` 为准并提示用户回 SAP 核对。

### Step 2: 分析真实数据来源

逐个变量（或按变量组）弄清楚：

| 要弄清什么 | 例如 |
|-----------|------|
| 数据从哪来 | HIS/EMR、PACS、LIS、手术视频系统、纸质 CRF、问卷平台、随访电话 |
| 导出格式与字段名 | 能否批量导出；导出成 Excel / CSV / DICOM / 视频文件；原始字段名、单位、编码（如诊断编码的版本）、缺失和截断值的写法（空白、"未查"、"<0.1"） |
| 谁在什么时间填写或导出 | 研究护士入组时、主刀术后当天、随访员按随访时点、信息科一次性导出 |
| 已有哪些现成表格可复用 | 科室已有的随访表、专病数据库、以前项目的 REDCap / CRF |

项目文件里没有的，一次列成清单问用户，不要猜；最好请用户给一份**去标识化**的导出样例或字段列表，字段名和编码以它为准。

### Step 3: 列出工具清单和理由 → 按 checkpoint_mode 确认

把计划写进 `tools/README.md` 的"工具清单"一节，每个工具写：用途、覆盖哪些变量 / SAP 条目、为什么需要（为什么不能直接用现成表格或系统导出）、谁在什么时候用。同时写明**不生成**哪些常见工具及原因（例如变量都能从 HIS 导出 → 不做手填 CRF，只做数据字典和导出字段对照）。

`references/tool-catalog.yaml` 是可选工具目录，用来查漏，**不是必须全套生成**。

按 `checkpoint_mode`：`step` 等用户确认清单后再生成；`light` / `auto` 在摘要里列出清单后直接生成，用户随时可以改。Step 2 没问到的来源假设标"待核实"写进 `tools/README.md`。

### Step 4: 按确认的清单生成工具

下面按研究类型写生成要点；每类的常见工具见 `references/tool-catalog.yaml` 对应条目，只生成 Step 3 确认过的。

#### A. AI/ML Benchmark 研究

常见工具见 `references/tool-catalog.yaml` 的 `ai_ml_benchmark`。生成逻辑：

**Prompt 模板：** 从 `study-protocol.md` 的 Type C 模块提取任务维度列表、每个任务的题型（MCQ / 开放题）、选项池（按术式/类别分组）→ 组装为 JSON，包含 3 种 Prompt 变体（简洁/标准/详细）用于敏感性分析。

**推理脚本：** 从 protocol 提取评估的模型列表 + API 配置、输入类型（图像/视频/文本）、推理参数（temperature, max_tokens, seed）、重复次数、结果解析规则（MCQ 提取、开放题保存）→ 生成 Python 脚本，支持命令行参数（--model, --input-type, --data-dir）、断点续传（已完成的样本跳过）、错误重试（3 次）、元数据记录（延迟、token、费用）。

#### B. AI 诊断/预测模型

常见工具见 `references/tool-catalog.yaml` 的 `ai_diagnostic_prediction`。

**数据划分脚本 = `patient_level_split.py`**：把它复制为项目的 `tools/data_split.py`（或在 `tools/README.md` 写明调用命令），按 SAP 第 10 节（数据划分方案）的方案（hold-out / K 折）、分层标签、seed 运行；把生成的 `split_summary.json`（各集患者数、类别分布、泄漏检查 passed）附到 SAP。

#### C. 临床研究

常见工具见 `references/tool-catalog.yaml` 的 `clinical`。

**CRF / 数据字典生成逻辑：** 字段来自 Step 1 的变量需求清单（纳入/排除判定、基线特征、干预/暴露、主要/次要结局、各时点），不从通用模板复制字段。变量名与 SAP 一致；编码、单位、取值范围按 Step 2 的真实来源定（如 LIS 导出的单位和"<0.1"写法、HIS 的诊断编码版本、系统里"未查"的写法），数据字典逐项写明"来源系统 / 原始字段名 / 原始写法 → 分析用变量名与编码"。表格结构按数据结构定：每位患者一条记录 → 宽表（每行一个患者）；同一患者有多个病灶或多次随访 → 长表或分表，保留患者 ID 与记录 ID。

**随机分组（RCT）= `randomization.py`**：按 protocol 的分配比和分层因素生成 `tools/allocation.csv`；不给 `--seed` 时脚本自取不可预测的 seed，只记在旁边的 `*_summary.json`（`--seed` 只用于重新生成同一份表，别用 42 这类好记的数）。分配表、seed、区组大小由与入组无关的人员单独受限保管（分配隐藏），**不写进 `study-protocol.md`**；protocol 只写方法（如"按中心分层、区组大小随机变化"）。

#### D. 基础实验

常见工具见 `references/tool-catalog.yaml` 的 `basic_experiment`；记录表的字段按本实验的读数、仪器导出格式和操作者来定。

#### E. 系统综述 / Meta 分析

常见工具见 `references/tool-catalog.yaml` 的 `systematic_review_meta`；提取表的字段按本综述的 PICO、结局指标和计划的合并方法来定。

### Step 5: 生成数据目录结构

按 `references/tool-catalog.yaml` 的 `project_directory_structure` 创建项目目录（`data/{raw,processed,annotations/{annotator_*,consensus},splits}` + `tools/` + `results/` + `analysis/` + `manuscript/` + `.mrp-state.json`），按本研究实际裁剪（没有标注就不建 `annotations/`，几位标注者就建几个子目录）。原始数据放 `data/raw/` 且永不修改。

### Step 6: 输出清单 + 使用指南 + 更新状态

补全 `tools/README.md`：数据来源分析（Step 2）、确认后的工具清单（Step 3）、每个工具的用途和使用方法（含上面两个脚本的调用命令）。输出 3–5 行摘要，然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 data-collection-tools 及产物、`next_step` 设为 statistical-analysis，`current_stage` 标记为"用户收集数据中"）。

## Output

除 `tools/README.md` 外，下表其余文件只在 Step 3 确认的清单里有时才生成；表中是常见文件名，不是必交清单。

| 文件 | 必须 / 常见于 | 说明 |
|------|---------|------|
| `tools/README.md` | 必须 | 数据来源分析 + 工具清单与理由 + 使用指南 |
| `tools/prompts.json` | AI Benchmark | Prompt 模板 |
| `tools/vlm_inference.py` | AI Benchmark | 推理脚本 |
| `tools/annotation_template.csv` | AI Benchmark / AI 诊断 | 标注模板 |
| `tools/scoring_template.csv` | AI Benchmark | 评分模板 |
| `tools/analysis_pipeline.py` | AI Benchmark | 结果汇总脚本（与 `tool-catalog.yaml` 一致；正式统计分析由 `statistical-analysis` 生成 `analysis_script.py`） |
| `tools/data_split.py` + `data/splits/split_summary.json` | AI 诊断 | 患者级划分（来自 `patient_level_split.py`） |
| `tools/CRF.xlsx` | 临床研究 | 病例报告表 |
| `tools/data_dictionary.md` | 临床研究 | 数据字典 |
| `tools/allocation.csv` + `*_summary.json` | RCT | 随机分组表与含 seed 的汇总（`randomization.py`，受限保管） |
| `data/` 目录结构 | 所有类型 | 按本研究裁剪的项目目录 |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "照工具目录全套生成，字段用通用示例" | 目录只是可选清单：按真实数据来源决定要哪些工具（HIS 能导出的变量不必再手填）；字段名、编码、取值范围从 SAP 和导出样例推出来 |
| "数据收集格式以后再定" | 事后转换数据格式费时费力，必须提前设计 |
| "Excel 随便建个表就行" | 没有数据字典的 Excel = 未来的噩梦 |
| "标注不需要指南" | 标注一致性取决于标注指南的清晰度 |
| "数据按图像/帧划分就行" | 按患者 ID 划分，防止数据泄漏（用 `patient_level_split.py`） |
| "随机分组 Excel 拉个随机数就行" | 用脚本，区组/分层；protocol 只写方法，分配表、seed、区组大小单独保管（分配隐藏） |
| "推理脚本跑一次就行" | 按 protocol 规定的重复次数运行、检查一致性 + 断点续传 |
| "变量名随便起" | 标准化命名（snake_case），与 `analysis-plan.md` 一致 |

## Convergence

当以下条件全部满足时完成：
1. 变量需求清单与真实数据来源分析已完成（来源不明的已问用户，或在 `auto` 模式下标"待核实"）
2. 工具清单（含理由）已按 checkpoint_mode 展示或确认，工具按清单生成
3. 所有变量名与 `analysis-plan.md` 一致；编码与取值范围和真实来源对得上（数据字典写明对应关系）
4. 数据目录结构已创建
5. `tools/README.md` 已写好（来源分析 + 工具清单 + 使用指南）
6. `.mrp-state.json` 已更新

## Red Flags — STOP

- 没有 protocol / SAP 就要生成工具 → 先说明返工风险；用户仍要做时，变量标"待与 SAP 核对"
- **不知道数据从哪来、谁来填、导出长什么样就开始生成 CRF / 提取表** → 停，先做 Step 2
- **想临场重写数据划分或随机分组代码** → 停，复制或调用 `patient_level_split.py` / `randomization.py`
- **数据划分必须按患者级别** — 绝不按图像/帧级别划分
- **随机分组表交给招募者** → 停，分配隐藏被破坏
- **CRF 变量必须有数据字典** — 裸变量名不可接受

## 衔接规则

### 前置依赖（缺了按总调度"缺前置产物时"处理）
- `study-protocol.md`（`study-design`，硬确认 1；A–E 五类同名，`type:` 区分）
- `analysis-plan.md`（`data-analysis-planning`，硬确认 2；变量命名、数据格式、划分/分层方案）

### 强制衔接（不可跳过）
- `data-analysis-planning` 完成且数据还要收集 → 本 skill 生成工具
- 工具生成后 → 用户执行数据收集 → 数据就绪后 → `statistical-analysis`
- 最后一步固定为更新 `.mrp-state.json`（Step 6）

### 可选衔接
- `tools/README.md` 的数据来源分析（导出格式、缺失和截断值的写法）→ `statistical-analysis` 做数据体检时可以对照
- 推理脚本需要 Prompt 设计指导 → 参考 `study-protocol.md` 的 Type C 模块（任务定义、Prompt 设置、评估流程）
- 标注模板需要引用格式化 → 调用 `pubmed-search` Mode 6
- 伦理批件规定的数据范围 → `ethics-statement.md`（`research-ethics`），收集的变量不得超出批准范围
