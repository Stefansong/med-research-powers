---
name: data-collection-tools
description: Use when generating data collection instruments, scripts, and templates from a confirmed study protocol and analysis plan. Triggers on "生成标注表"、"做个数据收集表"、"写推理脚本"、"随机分组"、"数据划分"、"CRF"、"数据录入表"、"REDCap".
---

# Data Collection Tools

## Overview

根据已确认的研究方案（`study-protocol.md`）和分析计划（`analysis-plan.md`）生成数据收集所需的全部工具——标注模板、推理脚本、数据录入表、随机分组表、数据划分脚本等。填补 data-analysis-planning → statistical-analysis 之间的执行空白：工具的变量名、格式、分组、划分都要和 SAP 对得上，否则分析阶段要返工。

## When to Use

- `analysis-plan.md` 已确认（硬确认 2 通过），要准备数据收集工具
- 需要 AI 推理脚本（VLM/LLM benchmark 研究）
- 需要专家标注/评分模板、临床数据录入表（CRF）、数据管理目录结构
- 需要随机分组表（RCT）或患者级数据划分（AI 研究）

## When NOT to Use

- 还没有研究方案 → 先完成 `study-design`
- 还没有分析计划 → 先完成 `data-analysis-planning`（变量名和数据格式由它决定）
- 需要执行统计分析 → `statistical-analysis`
- 需要执行 AI 推理（不是生成脚本）→ 用户自行运行脚本

## Prerequisites

- **必须**有 `study-protocol.md`（研究设计、变量、结局指标；A/B/C/D/E 五类统一用这个文件名，`type:` 字段区分）
- **必须**有 `analysis-plan.md`（统计方法、变量命名、数据格式、划分/分层方案）

## Scripts

两个固定逻辑的脚本在插件目录，运行目录是用户项目，用 `${CLAUDE_PLUGIN_ROOT}` 定位；生成项目工具时**复制或调用**它们，不要临场重写（数据泄漏的高风险点）：

| 脚本 | 用途 | 一行可运行示例 |
|------|------|---------------|
| `patient_level_split.py` | 患者级 train/val/test 或 K 折划分，可按标签分层，固定 seed，输出各集类别分布 + 泄漏检查 | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/data-collection-tools/scripts/patient_level_split.py" labels.csv --patient-col patient_id --label-col label --seed 42 --out-dir data/splits` |
| `randomization.py` | 简单 / 区组 / 分层随机分组表，固定 seed，输出分配表 + 汇总 | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/data-collection-tools/scripts/randomization.py" --method stratified --n-per-stratum 40 --strata site=A,B sex=M,F --arms Control,Treatment --seed 42 --out tools/allocation.csv` |

样本量不在本 skill 算：protocol 的先验样本量用 `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py`（见 `references/tool-catalog.yaml`）。

## Study Type Router

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

### Step 1: 解析研究方案与分析计划

```
读取 study-protocol.md → 研究类型、样本量与分组、变量列表、结局指标、数据来源、标注/评估流程
读取 analysis-plan.md  → 变量命名（snake_case）、数据格式（长表/宽表）、分层因素、划分方案与 seed
```

两份文件冲突时以 `analysis-plan.md` 为准并提示用户回 SAP 核对。

### Step 2: 生成工具（按研究类型）

#### A. AI/ML Benchmark 研究

工具清单见 `references/tool-catalog.yaml` 的 `ai_ml_benchmark`。生成逻辑：

**Prompt 模板：** 从 `study-protocol.md` 的 Type C 模块提取任务维度列表、每个任务的题型（MCQ / 开放题）、选项池（按术式/类别分组）→ 组装为 JSON，包含 3 种 Prompt 变体（简洁/标准/详细）用于敏感性分析。

**推理脚本：** 从 protocol 提取评估的模型列表 + API 配置、输入类型（图像/视频/文本）、推理参数（temperature, max_tokens, seed）、重复次数、结果解析规则（MCQ 提取、开放题保存）→ 生成 Python 脚本，支持命令行参数（--model, --input-type, --data-dir）、断点续传（已完成的样本跳过）、错误重试（3 次）、元数据记录（延迟、token、费用）。

#### B. AI 诊断/预测模型

工具清单见 `references/tool-catalog.yaml` 的 `ai_diagnostic_prediction`。

**数据划分脚本 = `patient_level_split.py`**：把它复制为项目的 `tools/data_split.py`（或在 `tools/README.md` 写明调用命令），按 SAP 第 10 节的方案（hold-out / K 折）、分层标签、seed 运行；把生成的 `split_summary.json`（各集患者数、类别分布、泄漏检查 passed）附到 SAP。

#### C. 临床研究

工具清单见 `references/tool-catalog.yaml` 的 `clinical`。

**CRF 生成逻辑：** 从 protocol 提取纳入/排除标准变量、基线特征、干预/暴露、主要/次要结局、时间点（基线、随访）→ Excel（每行一个患者，每列一个变量）+ Sheet 2 数据字典。变量名与 SAP 一致。

**随机分组（RCT）= `randomization.py`**：按 protocol 的分配比、区组大小、分层因素与 seed 生成 `tools/allocation.csv`；分配表由与入组无关的人员保管（分配隐藏），seed 与区组设置写入 protocol。

#### D. 基础实验

工具清单见 `references/tool-catalog.yaml` 的 `basic_experiment`。

#### E. 系统综述 / Meta 分析

工具清单见 `references/tool-catalog.yaml` 的 `systematic_review_meta`。

### Step 3: 生成数据目录结构

按 `references/tool-catalog.yaml` 的 `project_directory_structure` 创建标准化项目目录（`data/{raw,processed,annotations/{annotator_*,consensus},splits}` + `tools/` + `results/` + `analysis/` + `manuscript/` + `.mrp-state.json`）。原始数据放 `data/raw/` 且永不修改。

### Step 4: 输出清单 + 使用指南 + 更新状态

生成 `tools/README.md`，列出所有工具、用途和使用方法（含上面两个脚本的调用命令）。输出 3–5 行摘要，然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 data-collection-tools 及产物、`next_step` 设为 statistical-analysis，`current_stage` 标记为"用户收集数据中"）。

## Output

| 文件 | 必须/可选 | 说明 |
|------|---------|------|
| `tools/README.md` | 必须 | 工具使用指南 |
| `tools/prompts.json` | AI Benchmark | Prompt 模板 |
| `tools/vlm_inference.py` | AI Benchmark | 推理脚本 |
| `tools/annotation_template.csv` | AI Benchmark / AI 诊断 | 标注模板 |
| `tools/scoring_template.csv` | AI Benchmark | 评分模板 |
| `tools/analysis_pipeline.py` | AI Benchmark | 结果汇总脚本（与 `tool-catalog.yaml` 一致；正式统计分析由 `statistical-analysis` 生成 `analysis_script.py`） |
| `tools/data_split.py` + `data/splits/split_summary.json` | AI 诊断 | 患者级划分（来自 `patient_level_split.py`） |
| `tools/CRF.xlsx` | 临床研究 | 病例报告表 |
| `tools/data_dictionary.md` | 临床研究 | 数据字典 |
| `tools/allocation.csv` | RCT | 随机分组表（来自 `randomization.py`） |
| `data/` 目录结构 | 所有类型 | 标准化目录 |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "数据收集格式以后再定" | 事后转换数据格式费时费力，必须提前设计 |
| "Excel 随便建个表就行" | 没有数据字典的 Excel = 未来的噩梦 |
| "标注不需要指南" | 标注一致性取决于标注指南的清晰度 |
| "数据按图像/帧划分就行" | 按患者 ID 划分，防止数据泄漏（用 `patient_level_split.py`） |
| "随机分组 Excel 拉个随机数就行" | 要固定 seed、区组/分层、分配隐藏，全部写进 protocol |
| "推理脚本跑一次就行" | 需要重复 3 次检查一致性 + 断点续传 |
| "变量名随便起" | 标准化命名（snake_case），与 `analysis-plan.md` 一致 |

## Convergence

当以下条件全部满足时完成：
1. 研究类型已识别，对应工具组合已生成
2. 所有变量名与 `analysis-plan.md` 一致
3. 数据目录结构已创建
4. `tools/README.md` 使用指南已生成
5. 用户确认工具可用；`.mrp-state.json` 已更新

## Red Flags — STOP

- **禁止在没有 `study-protocol.md` 或 `analysis-plan.md` 的情况下生成工具** — 工具必须基于确认的方案与 SAP
- **数据划分必须按患者级别** — 绝不按图像/帧级别划分
- **随机分组表交给招募者** → 停，分配隐藏被破坏
- **CRF 变量必须有数据字典** — 裸变量名不可接受

## 衔接规则

### 前置依赖（不满足则阻止）
- **必须**：`study-protocol.md`（`study-design`，硬确认 1）
- **必须**：`analysis-plan.md`（`data-analysis-planning`，硬确认 2）

### 强制衔接（不可跳过）
- `data-analysis-planning` 完成后 → 本 skill 生成工具
- 工具生成后 → 用户执行数据收集 → 数据就绪后 → `statistical-analysis`
- 最后一步固定为更新 `.mrp-state.json`（Step 4）

### 可选衔接
- 推理脚本需要 Prompt 设计指导 → 参考 `study-protocol.md` 的 Type C 模块（任务定义、Prompt 设置、评估流程）
- 标注模板需要引用格式化 → 调用 `pubmed-search` Mode 6
- 伦理批件规定的数据范围 → `ethics-statement.md`（`research-ethics`），收集的变量不得超出批准范围
