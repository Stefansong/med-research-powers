---
name: ai-medical-study-design
description: Use when designing AI/ML medical research including imaging AI, surgical video analysis, prediction models, LLM evaluation, wearables, or smart devices. Triggers on "模型评估"、"benchmark"、"ground truth"、"标注"、"AUROC"、"TRIPOD-AI"、"CLAIM"、"DECIDE-AI"、"IDEAL"、"手术创新"、"器械开发".
---

# AI Medical Study Design

## Overview

AI 医学交叉研究需要同时满足技术规范和临床规范。两边都不能少。

## When to Use

医学影像 AI、手术视频 AI、临床预测模型、LLM/VLM 评估、数字健康、医学 NLP、智能医疗器械。

## When NOT to Use

- 纯临床研究（无 AI 组件）→ `study-design`
- 纯基础实验 → `basic-medical-study-design`

## Study Type Decision Tree

```
研究目标？
├── 开发新 AI 模型？
│     ├── 有临床验证？ → 开发+验证研究（TRIPOD type 2b/3）
│     └── 仅技术验证？ → 技术开发研究
├── 评估已有 AI 模型/工具？
│     ├── 诊断准确性？ → STARD-AI
│     ├── 临床效果？ → RCT（CONSORT-AI 2020）
│     ├── 多模型对比？ → Benchmark（TRIPOD-LLM）
│     ├── 可用性？ → 人因工程（混合方法）
│     └── AI 决策支持早期评估？ → DECIDE-AI 2022
├── 构建数据集/标注体系？
│     ├── 影像数据集？ → Datasheets for Datasets
│     ├── 视频标注？ → 标注一致性（Kappa/ICC）
│     └── Benchmark 集？ → Benchmark 论文
├── 开发新设备/传感器？
│     ├── 按 IDEAL 框架定位阶段
│     ├── Stage 1 原理验证 → Bench-top
│     ├── Stage 2a-2b 可行性 → Pilot / 前瞻性队列
│     └── Stage 3 对比验证 → RCT / Bland-Altman
└── 综合 AI 医学证据？
      ├── 系统综述 → PRISMA + PRISMA-S
      └── Meta 分析 → PRISMA + QUADAS-2/PROBAST
```

## Core Design Elements

### 1. Dataset
- 训练/验证/测试必须独立（禁止 data leakage）
- 同一患者的数据不能分在训练和测试集
- 优先外部验证（不同中心/时间段）
- 必须报告：来源、时间范围、纳入排除标准、数据量、类别分布、去标识化方式

### 2. Ground Truth
- 标注者资历和数量
- 标注一致性（Cohen's Kappa / Fleiss' Kappa / ICC）
- 争议解决机制（共识讨论 / 多数投票 / 专家裁决）
- 标注流程是否盲法

### 3. Performance Metrics
按任务类型选择指标 → 加载 `references/metrics-and-reporting.yaml`

### 4. Human-AI Comparison
- 相同信息输入（公平对比条件）
- 说明专家水平（年资、例数）
- 最好三组：AI alone / Human alone / AI-assisted Human
- 阅片 washout period

### 5. Reproducibility
- 代码开源（GitHub + DOI via Zenodo）
- 模型权重共享或推理 API
- 环境配置（requirements.txt / Docker）
- 随机种子固定

## Reporting Standards

研究类型→规范映射 → 加载 `references/metrics-and-reporting.yaml` 的 mapping 部分。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "Accuracy 95% 说明模型很好" | 类别不平衡时 Accuracy 毫无意义，必须看 AUROC/AUPRC |
| "训练集上效果好就行" | 没有独立测试集/外部验证的结果不可信 |
| "数据随机划分就行" | 同一患者不能同时在训练和测试集 |
| "AUROC 高就有临床价值" | 必须做 DCA 评估临床净获益 |
| "这是 AI 研究不需要临床规范" | 需要同时满足技术和临床两套规范 |
| "我的器械直接做 RCT" | 先用 IDEAL 定位阶段，Stage 1-2 不适合 RCT |
| "AI 评估不用报告可用性" | DECIDE-AI 要求报告人机交互和用户体验 |

## Convergence

当以下条件全部满足时完成：
1. 研究类型已明确，对应报告规范已确定
2. 数据集方案完整（来源、划分、标注流程）
3. 评估指标已选择并有依据
4. 人机对比方案已设计（如适用）
5. 可复现性方案已规划

## 衔接规则

### 强制衔接
- 模型评估完成后 → **必须**触发 `reporting-standards` 检查 TRIPOD-AI / CLAIM / DECIDE-AI
- 涉及手术/器械创新 → **必须**按 IDEAL 框架定位阶段

### 前置依赖
- **必须**有明确的研究问题（`research-question-formulation`）

### 可选
- 数据集准备好后 → `data-analysis-planning`
- 论文写作时 → `manuscript-writing`
