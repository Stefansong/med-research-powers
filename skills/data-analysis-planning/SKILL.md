---
name: data-analysis-planning
description: Use when planning statistical analysis before execution. Triggers on "帮我分析数据"、"用什么统计方法"、"分析策略"、"SAP"、"分析计划". Must complete before statistical-analysis can run.
---

# Data Analysis Planning

## Overview

先写分析计划再跑分析——如同 TDD 先写测试再写代码。防止 p-hacking 和事后假设。

## When to Use

- 拿到数据要开始分析时
- 需要确定统计方法时
- 审稿人要求补充 SAP 时

## When NOT to Use

- 执行已有分析计划 → `statistical-analysis`
- 还没有明确的研究问题 → `research-question-formulation`

## Workflow

生成 `analysis-plan.md`，包含以下 7 个部分：

### 1. 数据概览
数据来源、采集时间、样本量（预期 vs 实际）、变量清单及类型

### 2. 数据预处理
- 缺失值：MCAR → 完整病例分析 / MAR → 多重插补 / MNAR → 敏感性分析
- 异常值：IQR / Z-score / 临床合理范围
- 数据转换、变量重编码规则

### 3. 描述性统计
- 连续变量：均值±SD（正态）或中位数(IQR)（非正态）
- 分类变量：频数(%)
- 组间基线比较

### 4. 主要分析
为每个研究目标明确：统计方法、前提假设验证方式、效应量指标、多重比较校正。

方法选择 → 加载 `references/stat-method-decision-tree.yaml`

### 5. 次要分析和亚组分析
预先指定的亚组及其合理性说明、交互效应检验

### 6. 敏感性分析
至少一种替代方法、缺失数据敏感性、异常值影响

### 7. 多重比较策略
- 主要结局：不校正
- 多个次要结局：Bonferroni / Holm / FDR
- 组学数据：BH-FDR

组学研究 → 参考 `references/omics-methods.md`（覆盖：非靶向/靶向代谢组学、蛋白质组学、转录组学/基因组学、多组学整合）

## Output

唯一交付物：`analysis-plan.md`（即 SAP, Statistical Analysis Plan）。

- 临床/基础/调查研究：包含上述 7 个部分（数据概览 → 多重比较策略）
- AI/ML 研究：额外包含第 8-16 部分（见下方 AI/ML Research SAP Extension）
- 必须在执行分析**之前**定稿并经用户确认（防止 p-hacking）
- 定稿后偏差须记录在 `analysis-log.md` 中并说明理由

## AI/ML Research SAP Extension

当研究类型为 AI/ML（从 study-design Type C 传入）时，SAP 必须额外覆盖第 8-16 部分。

**方法细节**（模型架构 / 训练超参 / 数据增强 / 类别不平衡 / 消融实验 / 模型比较检验 DeLong/McNemar/Bootstrap / 可解释性 Grad-CAM/SHAP / 不确定性量化 MC Dropout/ECE）→ 加载 `references/stat-method-decision-tree.yaml` 的 AI/ML 部分（`deep_learning_*`、`model_comparison`、`uncertainty_quantification`、`explainability`）。

SAP 必须列出的额外章节：

- **8. 模型架构选择** — 候选模型 + 基线 + 预训练策略（依据见 yaml）
- **9. 训练策略** — 超参须可复现（必报项见 yaml `deep_learning_training.hyperparameter_reporting`）
- **10. 数据划分方案** — 见下表（按患者级别划分）
- **11. 数据增强策略** — 须**预先**规划；禁止在测试集做增强（TTA 除外）
- **12. 类别不平衡处理** — 评估层面**不用 accuracy**，用 AUROC/AUPRC/F1
- **13. 消融实验** — baseline → +A → +B → full，固定相同划分与随机种子
- **14. 模型比较统计检验** — 不能只报点估计，必须有 95% CI 和 p-value
- **15. 模型可解释性方案** — ≥3-5 例典型案例（typical/best/worst）
- **16. 不确定性量化** — 安全关键应用须做（含校准 ECE + reliability diagram）

### 数据划分方案（与 study-design Type C 共用同一表）

| 数据量 | 推荐方案 | 关键策略 |
|--------|---------|---------|
| n > 1000 | 标准 train/val/test (60/20/20) | 按患者级别划分 |
| n = 200-1000 | K-fold cross-validation (K=5) | 每折按患者划分，报告均值±SD |
| n = 50-200 | 迁移学习 + nested CV | 使用预训练权重（ImageNet/领域预训练）|
| n < 50 | **强警告**：深度学习样本不足；改用 leave-one-out CV 或经典 ML，外部验证为**强制**项 | 在 Limitations 中充分讨论 |

SAP 特有判断（不在 yaml 中）：
- **必须按患者 ID 划分**（同一患者的多张图像不能分在不同集合）——SAP 须写明患者级划分逻辑
- 报告划分的**随机种子**和各集合的**类别分布**
- 这些指标必须与 study-design Type C protocol 一致；新增指标标记为 post-hoc / exploratory

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "分析很简单不需要计划" | 无计划 = p-hacking 的温床 |
| "先看看数据再决定方法" | 看了数据再选方法 = 事后假设 |
| "只分析主要结局就行" | 必须预先指定所有计划分析 |
| "缺失数据直接删掉" | 必须说明缺失机制并选择对应处理策略 |
| "不需要敏感性分析" | 审稿人一定会要求 |

## Red Flags — STOP

- **禁止在查看数据/结果后再选择统计方法或假设**（事后假设 = HARKing）
- **禁止在执行分析后修改主要结局或主要分析方法**（偏差须记录在 `analysis-log.md`）
- **禁止反复尝试多种方法只报告"显著"的那个**（p-hacking）
- **禁止把未预先指定的亚组分析当作确证性结论**（必须标记 exploratory）
- **AI/ML：禁止用测试集调参或在测试集上做数据增强**（数据泄漏）
- **AI/ML：禁止只报告点估计**（必须有 95% CI 和统计检验）

## Convergence

当以下条件全部满足时完成：
1. 每个统计方法的前提假设已列出
2. 多重比较校正策略已确定
3. 缺失数据处理策略已明确
4. 敏感性分析已规划
5. `analysis-plan.md` 已生成并经用户确认

## 衔接规则

### 前置依赖
- **必须**有明确的研究问题和假设（`research-question-formulation`）

### 强制衔接
- 计划完成后 → 传递给 `statistical-analysis` 执行

### 与 study-design Type C 的衔接
- 从 Type C protocol 接收：评估指标、数据划分方案、Ground Truth 定义
- SAP 中这些指标必须与 protocol 一致
- 如需新增指标 → 标记为 post-hoc / exploratory

### 可选
- 组学数据 → `references/omics-methods.md`
