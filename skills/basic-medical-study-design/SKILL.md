---
name: basic-medical-study-design
description: Use when designing bench/lab experiments including cell studies, animal models, molecular biology, or tissue analysis. Triggers on "Western blot"、"PCR"、"ELISA"、"流式"、"免疫荧光"、"转染"、"敲除"、"动物模型"、"细胞培养"、"体外实验"、"体内实验".
---

# Basic Medical Study Design

## Overview

基础研究的核心：对照、重复、盲法、随机化。缺少任何一个，结果不可信。

## When to Use

涉及细胞实验、动物实验、分子生物学、蛋白质实验、基因编辑、组织病理、药理学、微生物学、免疫学等基础研究。

## When NOT to Use

- 临床患者数据研究 → `study-design`
- AI/ML 模型评估 → `ai-medical-study-design`
- 纯统计分析 → `data-analysis-planning`

## Core Principles

### 1. 对照设置（不允许跳过）

每个实验必须包含：
- **阴性对照** — 证明效应不是背景噪声
- **阳性对照** — 证明系统能检测到效应
- **载体对照** — 排除溶剂/载体效应（如 DMSO）
- **特殊对照**：同型对照（抗体实验）、回补对照（基因功能研究）

### 2. 重复设计（审稿人最常抓的问题）

| 类型 | 含义 | 论文中 n 值 | 最低要求 |
|------|------|-----------|---------|
| 生物学重复 | 独立样本/个体 | **n = 生物学重复数** | ≥ 3 |
| 技术重复 | 同一样本重复检测 | 不算 n | ≥ 2 |

**关键判断**：3 个独立传代的细胞分别做实验 = n=3 ✅；同一批细胞分 3 个孔 = n=1 ❌

### 3. 盲法

- 动物实验：分组、给药、评估由不同人完成
- 病理评分：评分者不知道分组
- WB 定量：先定量再查看分组
- 图像分析：自动化定量优于主观评估

### 4. 随机化

- 动物实验：随机数表/软件分组（必须说明方法）
- 细胞板：注意边缘效应，随机化位置
- 检测顺序：随机化（避免系统误差）

## Experiment Templates

具体实验设计模板在 `references/experiment-templates/` 目录：
- `western-blot.md` — WB 设计、抗体信息、定量方法
- `qpcr.md` — qPCR 设计、引物信息、ΔΔCt 分析
- `animal-study.md` — 动物信息、伦理、ARRIVE 2.0 要求

根据实验类型加载对应模板。

## Validation Layers

一个发现被接受通常需要多层验证：

1. 单一方法结果（最弱）
2. 不同方法验证同一结论（如 qPCR + WB）
3. 功能验证（过表达/敲除/抑制剂）
4. 体内验证（动物实验验证体外发现）
5. 临床样本验证

审稿人期望至少达到第 2-3 层。

## Figure Requirements

- WB：全膜图（越来越多期刊要求）
- 显微镜图：比例尺 + 放大倍数
- 流式图：展示门控策略
- 定量图：展示个体数据点（不只画柱状图）
- 代表性图片：标注 "representative of n=X experiments"

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "做了 3 个复孔就是 n=3" | 技术重复，只算 n=1 |
| "不需要阴性对照" | 没有对照的结果不可解读 |
| "WB 肉眼可见就不用定量" | 必须灰度值定量 |
| "SD 太大换成 SEM" | 数据美化，用 SD 如实反映变异 |
| "动物实验不用随机分组" | 必须随机，否则分配偏倚 |
| "只展示最好看的那次 WB" | 基于所有重复的定量数据 |
| "统计不显著但趋势明显" | 趋势不是证据，增加样本量或改设计 |

## Convergence

当以下条件全部满足时完成：
1. 对照组完整（阴性+阳性+载体，如适用）
2. 重复方案明确（生物学 ≥ 3，技术 ≥ 2）
3. 盲法和随机化方案已确定
4. 样本量有依据（power analysis 或文献先例）
5. 伦理审查已确认（动物实验需 IACUC）

## 衔接规则

### 强制衔接
- 涉及动物实验 → **必须**检查 ARRIVE 2.0（`reporting-standards`）
- 涉及临床样本 → **提醒**用户检查伦理审查（`research-ethics`）

### 前置依赖
- **必须**有明确的研究问题（`research-question-formulation`）

### 可选
- 涉及 AI 辅助分析（如病理图像 AI）→ `ai-medical-study-design`
- 涉及组学数据 → 参考 `data-analysis-planning/references/omics-methods.md`
