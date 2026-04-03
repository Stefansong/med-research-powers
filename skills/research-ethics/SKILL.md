---
name: research-ethics
description: Use when checking ethical compliance of research involving human subjects, animals, or patient data. Auto-triggers when study-design or manuscript-writing involves human data. Triggers on "伦理"、"IRB"、"知情同意"、"数据隐私"、"IACUC"、"利益冲突".
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

## Checklist

### 1. 伦理审查（IRB / EC）
- [ ] 已获机构伦理委员会批准
- [ ] 批准编号已记录
- [ ] 方案在批准范围内
- [ ] 回顾性研究：已获知情同意豁免（需理由）

### 2. 动物实验伦理（IACUC）
- [ ] IACUC 批准
- [ ] 3R 原则（Replacement, Reduction, Refinement）
- [ ] 人道终点标准
- [ ] 麻醉/镇痛/安乐死方案（AVMA 指南）
- [ ] 操作人员资格证

### 3. 知情同意
- [ ] 前瞻性：书面知情同意
- [ ] 回顾性：豁免及理由
- [ ] 特殊群体：未成年人（监护人同意）/ 无法自主同意者
- [ ] 同意书含退出权利

### 4. 数据隐私
- [ ] 去标识化完成
- [ ] 符合法规（中国：个人信息保护法 / EU：GDPR / US：HIPAA）
- [ ] 数据存储安全（加密、访问控制）
- [ ] 跨境传输限制评估
- [ ] AI 平台使用限制：禁止上传含患者信息的原始数据

### 5. 研究注册
- [ ] 临床试验：已注册（ClinicalTrials.gov / ChiCTR），在首例入组前
- [ ] 系统综述：已注册（PROSPERO）

### 6. 利益冲突与数据共享
- [ ] 资金来源声明
- [ ] 利益冲突声明
- [ ] 数据共享计划（期刊日益要求）

## Methods 模板

```
本研究经[机构名称]伦理委员会批准（批准号：xxx），
符合赫尔辛基宣言原则。[所有参与者签署了书面知情同意书 /
经伦理委员会批准，本回顾性研究免除知情同意要求]。
```

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

## Red Flags — 提醒

- 没有伦理批准 → **提醒**用户在投稿前获得批准（不阻断流程）
- 数据含可识别患者信息 → 提醒用户注意隐私保护
- 禁止编造伦理审查批准信息

## 衔接规则

### 强制衔接
- 检查结果传入 `pre-submission-verification` 的 Gate 4

### 被动触发
- `study-design` 涉及人体/动物 → 自动触发
- `manuscript-writing` 的 Methods → 自动检查
