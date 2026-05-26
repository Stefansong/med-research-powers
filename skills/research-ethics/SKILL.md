---
name: research-ethics
description: Use when checking ethical compliance of research involving human subjects, animals, or patient data. Triggers on "伦理"、"IRB"、"知情同意"、"数据隐私"、"IACUC"、"利益冲突".
---

# Research Ethics

## Overview

伦理合规贯穿整个研究过程。涉及人体数据时主动提醒用户检查，但不强制阻断研究流程。用户负责确保已获得必要的伦理审批。

## When to Use

- 涉及人体研究、患者数据、知情同意
- 涉及动物实验
- 涉及数据隐私
- `study-design` 或 `manuscript-writing` 阶段自动检查

## When NOT to Use

- 纯计算/模拟研究，不涉及人体或动物数据
- 公开数据集（但仍需确认原始数据已获伦理批准）

## Workflow

### Step 1: 判断适用范围

确认研究是否涉及人体、患者数据、动物实验或数据隐私。纯计算/模拟且不触及上述数据 → 见 When NOT to Use；否则继续。

### Step 2: 加载并逐条核对 checklist

加载 `references/ethics-checklist.yaml`，逐条核对 6 个章节：
1. 伦理审查（IRB / EC）
2. 动物实验伦理（IACUC）
3. 知情同意
4. 数据隐私
5. 研究注册
6. 利益冲突与数据共享

每条标记状态（已满足 / 缺失 / N/A 并说明原因）。涉及人体取 1/3/4/5/6，涉及动物取 2，公开数据集仍需确认原始数据已获伦理批准。

### Step 3: 撰写 Methods 伦理声明

用 `references/ethics-checklist.yaml` 中的 `methods_statement_template` 生成伦理声明，填入真实批准号与知情同意/豁免表述，写入论文 Methods。

### Step 4: 生成输出并提醒

汇总核对结果，生成 `ethics-statement.md`（见 Output）。缺失项以**提醒**形式告知用户（不阻断流程）。

## Output

生成 `ethics-statement.md`，包含：
- 6 章节逐条核对状态（已满足 / 缺失 / N/A）
- 伦理审批号与知情同意/豁免状态
- 数据隐私合规结论
- 利益冲突、资金来源、数据共享声明
- 可直接粘贴进论文 Methods 的伦理声明段落
- 缺失项清单（标注为需用户在投稿前补齐的提醒）

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "回顾性研究不需要伦理" | 需要伦理审查或正式豁免 |
| "伦理批准号以后再补" | 事后补办多数机构不接受 |
| "数据已经脱敏了没问题" | 仍需确认脱敏方式和法规合规 |
| "把患者数据传给 AI 分析" | 禁止上传含可识别信息的数据到 AI 平台 |
| "利益冲突就写'无'" | 必须认真评估并如实声明 |

## Convergence

当以下条件全部满足时完成：
1. 伦理审查状态已确认（批准号或豁免说明）
2. 知情同意状况已明确
3. 数据隐私合规已检查
4. 利益冲突声明已准备
5. 论文 Methods 中已写入伦理声明

## Red Flags — STOP

- 没有伦理批准 → **提醒**用户在投稿前获得批准（不阻断流程）
- 数据含可识别患者信息 → 提醒用户注意隐私保护
- 禁止编造伦理审查批准信息 → 绝不虚构批准号或委员会名称

## 衔接规则

### 前置依赖
- 研究确实涉及人体/患者数据/动物，或处于 `study-design` / `manuscript-writing` 阶段（被动触发）

### 强制衔接
- 检查结果传入 `pre-submission-verification` 的 **Gate 5**（伦理与合规）
- `study-design` 涉及人体/动物 → 自动触发本 skill
- `manuscript-writing` 的 Methods → 自动检查伦理声明

### 可选衔接
- 需把伦理声明并入投稿材料 → `submission-preparation`
- 临床试验/系统综述未注册 → 提醒在 `study-design` 阶段先注册（ClinicalTrials.gov / ChiCTR / PROSPERO）
