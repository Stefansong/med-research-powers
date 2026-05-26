---
name: data-collection-tools
description: Use when generating data collection instruments, scripts, and templates from a study protocol. Triggers on "生成标注表"、"做个数据收集表"、"写推理脚本"、"annotation template"、"CRF"、"数据录入表"、"REDCap"、"inference script".
---

# Data Collection Tools

## Overview

根据已确认的研究方案（study-protocol.md）自动生成数据收集所需的全部工具——标注模板、推理脚本、数据录入表、评分量表等。填补 study-design → statistical-analysis 之间的执行空白。

## When to Use

- 研究方案确认后，需要准备数据收集工具
- 需要 AI 推理脚本（VLM/LLM benchmark 研究）
- 需要专家标注/评分模板
- 需要临床数据录入表（CRF）
- 需要数据管理目录结构

## When NOT to Use

- 还没有研究方案 → 先完成 `study-design`
- 需要执行统计分析 → `statistical-analysis`
- 需要执行 AI 推理（不是生成脚本）→ 用户自行运行脚本

## Prerequisites

- **必须**有 `study-protocol.md`（确定研究设计、变量、结局指标）
- **推荐**有 `analysis-plan.md`（确定统计方法，影响数据格式）

## Study Type Router

不同研究类型需要不同的数据收集工具组合：

```
研究类型？
├── AI/ML Benchmark（VLM/LLM 评估）
│     → Prompt 模板 + 推理脚本 + 标注表 + 评分表 + 分析脚本
├── AI 诊断/预测模型
│     → 数据提取表 + 标注表（Ground Truth）+ 模型推理脚本 + 评估脚本
├── 临床研究（RCT / 队列 / 横断面）
│     → CRF（病例报告表）+ 数据字典 + 随机分组脚本（RCT）
├── 基础实验
│     → 实验记录表 + 数据录入模板 + 图像采集规范
└── 系统综述 / Meta 分析
      → 数据提取表 + 偏倚评估表 + PRISMA 流程图模板
```

## Workflow

### Step 1: 解析研究方案

```
读取 study-protocol.md → 提取:
  - 研究类型
  - 样本量和分组
  - 变量列表（自变量、因变量、协变量）
  - 结局指标（主要、次要）
  - 数据来源
  - 标注/评估流程
```

### Step 2: 生成工具（按研究类型）

#### A. AI/ML Benchmark 研究

工具清单见 `references/tool-catalog.yaml` 的 `ai_ml_benchmark`（Prompt 模板、推理脚本 `tools/vlm_inference.py`、标注/评分模板、分析脚本、数据目录）。生成逻辑如下：

**Prompt 模板生成逻辑:**
```
从 study-protocol.md 提取:
  → 任务维度列表
  → 每个任务的题型（MCQ / 开放题）
  → 每个任务的选项池（按术式/类别分组）
  → 组装为 JSON 格式
  → 包含 3 种 Prompt 变体（简洁/标准/详细）用于敏感性分析
```

**推理脚本生成逻辑:**
```
从 study-protocol.md 提取:
  → 评估的模型列表 + API 配置
  → 输入类型（图像/视频/文本）
  → 推理参数（temperature, max_tokens, seed）
  → 重复次数
  → 结果解析规则（MCQ 提取、开放题保存）
  → 生成 Python 脚本，支持:
     - 命令行参数（--model, --input-type, --data-dir）
     - 断点续传（已完成的样本跳过）
     - 错误重试（3 次）
     - 元数据记录（延迟、token、费用）
```

#### B. AI 诊断/预测模型

工具清单见 `references/tool-catalog.yaml` 的 `ai_diagnostic_prediction`（数据提取表、标注模板、标注指南、数据划分脚本、评估脚本）。

**数据划分脚本关键规则:**
- 按患者 ID 划分（不是按样本/图像）
- 支持分层抽样（保持类别比例）
- 支持交叉验证
- 记录划分种子（可复现）

#### C. 临床研究

工具清单见 `references/tool-catalog.yaml` 的 `clinical`（CRF、数据字典、筛选表、随机分组脚本、样本量计算）。

**CRF 生成逻辑:**
```
从 study-protocol.md 提取:
  → 纳入/排除标准变量
  → 基线特征变量（人口学、临床特征）
  → 干预/暴露变量
  → 主要/次要结局变量
  → 时间点（基线、随访）
  → 组装为 Excel（每行一个患者，每列一个变量）
  → 附 Sheet 2: 数据字典
```

#### D. 基础实验

工具清单见 `references/tool-catalog.yaml` 的 `basic_experiment`（实验记录表、图像采集规范、数据录入模板）。

#### E. 系统综述 / Meta 分析

工具清单见 `references/tool-catalog.yaml` 的 `systematic_review_meta`（数据提取表、偏倚评估表、PRISMA 模板、双人筛选记录）。

### Step 3: 生成数据目录结构

按 `references/tool-catalog.yaml` 的 `project_directory_structure` 创建标准化项目目录（`data/{raw,processed,annotations/{annotator_*,consensus},splits}` + `tools/` + `results/` + `analysis/` + `manuscript/` + `.mrp-state.json`）。原始数据放 `data/raw/` 且永不修改。

### Step 4: 输出清单 + 使用指南

生成 `tools/README.md`，列出所有工具、用途和使用方法。

## Output

| 文件 | 必须/可选 | 说明 |
|------|---------|------|
| `tools/README.md` | 必须 | 工具使用指南 |
| `tools/prompts.json` | AI Benchmark | Prompt 模板 |
| `tools/vlm_inference.py` | AI Benchmark | 推理脚本 |
| `tools/annotation_template.csv` | AI/诊断 | 标注模板 |
| `tools/scoring_template.csv` | AI Benchmark | 评分模板 |
| `tools/analysis_pipeline.py` | 所有类型 | 分析脚本 |
| `tools/CRF.xlsx` | 临床研究 | 病例报告表 |
| `tools/data_dictionary.md` | 临床研究 | 数据字典 |
| `tools/data_split.py` | AI/诊断 | 数据划分脚本 |
| `data/` 目录结构 | 所有类型 | 标准化目录 |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "数据收集格式以后再定" | 事后转换数据格式费时费力，必须提前设计 |
| "Excel 随便建个表就行" | 没有数据字典的 Excel = 未来的噩梦 |
| "标注不需要指南" | 标注一致性取决于标注指南的清晰度 |
| "数据按图像/帧划分就行" | 按患者 ID 划分，防止数据泄漏 |
| "推理脚本跑一次就行" | 需要重复 3 次检查一致性 + 断点续传 |
| "变量名随便起" | 标准化命名（snake_case），与 analysis-plan.md 一致 |

## Convergence

当以下条件全部满足时完成：
1. 研究类型已识别，对应工具组合已生成
2. 所有变量名与 `analysis-plan.md` 一致
3. 数据目录结构已创建
4. `tools/README.md` 使用指南已生成
5. 用户确认工具可用

## Red Flags — STOP

- **禁止在没有 study-protocol.md 的情况下生成工具** — 工具必须基于确认的方案
- **数据划分必须按患者级别** — 绝不按图像/帧级别划分
- **CRF 变量必须有数据字典** — 裸变量名不可接受

## 衔接规则

### 前置依赖
- **必须**: `study-protocol.md`
- **推荐**: `analysis-plan.md`

### 被上层 skill 调用
- `study-design` 完成后 → 自动建议触发本 skill

### 强制衔接
- 工具生成后 → 用户执行数据收集 → 数据就绪后触发 `statistical-analysis`

### 可选衔接
- 推理脚本需要 Prompt 设计指导 → 参考 `study-protocol.md` 的 Prompt 标准化章节
- 标注模板需要引用格式化 → 调用 `pubmed-search` Mode 6
