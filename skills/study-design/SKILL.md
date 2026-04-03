---
name: study-design
description: Use when designing a clinical research study protocol. Triggers on "怎么设计研究"、"样本量"、"研究类型"、"写protocol"、"研究方案"、"RCT设计"、"队列设计". For basic science use basic-medical-study-design; for AI/ML use ai-medical-study-design.
---

# Study Design

## Overview

根据研究问题选择最合适的研究类型，制定完整的研究方案（protocol）。

## When to Use

临床研究设计：RCT、队列、病例对照、横断面、诊断准确性、预测模型。

## When NOT to Use

- 基础实验（细胞/动物）→ `basic-medical-study-design`
- AI/ML 交叉研究 → `ai-medical-study-design`
- 已有设计只需分析 → `data-analysis-planning`

## Study Type Decision Tree

```
研究问题
├── 评估干预效果？
│     ├── 可以随机？ → RCT（CONSORT 2025）
│     └── 不能随机？ → 准实验 / 队列
├── 探索暴露-结局关系？
│     ├── 前瞻性 → 前瞻性队列（STROBE）
│     ├── 回顾性 → 回顾性队列 / 病例对照
│     └── 横断面 → 横断面研究
├── 诊断/检测准确性？ → STARD
├── 预测模型？ → TRIPOD
├── 综合证据？ → 系统综述/Meta（PRISMA）
└── 描述性？ → 病例报告/系列（CARE）
```

## Protocol Document (`study-protocol.md`)

### 1. 研究概要
标题、研究类型、注册号（ClinicalTrials.gov / ChiCTR）

### 2. 研究对象
纳入标准（具体可操作）、排除标准、招募方式

### 3. 样本量计算（MANDATORY）
使用 `statistical-analysis/scripts/power_analysis.py` 或 G*Power。
必须确认：预期效应量来源（文献/预实验）、α、β、脱落率。

### 4. 变量定义
自变量、因变量、混杂变量、协变量——每个都要有定义、测量方式、单位。

### 5. 数据收集
时间点、方式（EMR/量表/检验/影像）、质控措施、缺失数据预案

### 6. SAP 概要
详细 SAP → `data-analysis-planning`

### 7. 伦理合规
→ `research-ethics`

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "样本量够大应该没问题" | 必须做正式 power analysis |
| "纳入标准写宽一点好" | 过宽 = 异质性大 = 效应被稀释 |
| "混杂因素不用特别考虑" | 未调整的混杂 = 虚假关联 |
| "先收数据再写 protocol" | 先注册 protocol 再收数据才可信 |
| "横断面也能推因果" | 横断面只能看关联，不能推因果 |

## Convergence

当以下条件全部满足时完成：
1. 研究类型已确定且合理
2. 样本量计算有明确依据
3. 纳入/排除标准具体可操作
4. 主要结局指标有明确定义
5. 已识别主要混杂因素
6. `study-protocol.md` 已生成
7. **⚠️ Hard Checkpoint：用户已审阅并确认研究方案**

## Hard Checkpoint：研究方案审批

`study-protocol.md` 生成后，**必须**向用户完整展示方案并获得明确确认，才能进入下一步。

### 审批报告格式

```
────────────────────────────────────────
⚠️ 研究方案审批 (Hard Checkpoint)

📄 生成文件：study-protocol.md

📋 方案摘要：
  • 研究类型：[RCT / 队列 / 横断面 / ...]
  • 研究对象：[纳入标准概要]
  • 样本量：N=[X]（依据：[效应量来源]，α=[X]，power=[X]）
  • 主要结局：[指标名称 + 定义]
  • 对照/比较：[对照组设定]
  • 预计周期：[数据收集时间]

⚠️ 需要用户确认：
  1. 研究类型是否正确？（RCT vs 队列 vs 横断面 影响整个分析策略）
  2. 样本量是否可行？（能否在预期时间内招到足够样本）
  3. 纳入/排除标准是否合理？（过严→招不到人，过宽→异质性大）
  4. 主要结局指标是否是你最关心的？（事后更改主要结局 = 学术不端）
  5. 是否需要伦理审查？（涉及人体数据 → 必须）
  6. 是否需要临床试验注册？（干预性研究 → 必须）

🔒 确认后，研究方案将锁定。后续偏差需在 analysis-log.md 中记录理由。
────────────────────────────────────────
请审阅上述方案，确认后回复"确认"以继续。
如需修改请告诉我具体调整内容。
```

### 为什么这是 Hard Checkpoint

- **研究类型**决定了后续所有分析方法、报告规范、审稿标准
- **主要结局**一旦确定，后续不能随意更改（事后更换 = outcome switching = 学术不端）
- **样本量**决定了研究的可行性和统计功效
- **protocol 注册**后不可大幅更改（ClinicalTrials.gov / ChiCTR 有记录）

### 确认后锁定的内容

| 锁定项 | 后续能否更改 |
|--------|-------------|
| 研究类型 | ❌ 不能更改 |
| 主要结局指标 | ❌ 不能更改（只能添加为次要结局） |
| 样本量目标 | ⚠️ 可调整但需说明理由 |
| 纳入/排除标准 | ⚠️ 可微调但需在 Methods 中说明 |
| 统计方法（SAP 中）| ⚠️ 偏差需在 analysis-log.md 中记录 |

## 衔接规则

### 前置依赖
- **必须**有 PICO 和假设（`research-question-formulation`）

### 强制衔接
- 涉及人体/患者数据 → **提醒**用户检查伦理合规（`research-ethics`），不强制阻断流程
- **⚠️ 用户确认方案后** → 传递给 `journal-selection`（早期选刊）
- **⚠️ 用户确认方案后** → 传递给 `data-analysis-planning` 制定 SAP
