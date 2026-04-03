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

## AI/ML Research SAP Extension

当研究类型为 AI/ML（从 study-design Type C 传入）时，SAP 必须额外覆盖以下要素：

### 8. 模型架构选择
- 候选模型列表及选择依据（文献支持）
- 基线模型（baseline）定义
- 预训练策略（ImageNet / 领域预训练 / from scratch）

### 9. 训练策略
- Optimizer（Adam / SGD / AdamW）
- Learning rate + schedule（cosine annealing / step decay / warmup）
- Batch size + epochs + early stopping criteria
- 正则化（dropout rate, weight decay, data augmentation）
- Loss function（CE / Dice loss / Focal loss / weighted loss）
- 随机种子固定（reproducibility）
- Hardware（GPU 型号、训练时间）

### 10. 数据划分方案

| 数据量 | 推荐方案 | 注意事项 |
|--------|---------|---------|
| n > 1000 | 标准 train/val/test (60/20/20) | 按患者级别划分 |
| n = 200-1000 | 5-fold cross-validation | 每折的 test set 不重叠 |
| n < 200 | 迁移学习 + Leave-one-out 或 nested CV | 考虑外部预训练数据 |

关键规则：
- **必须按患者 ID 划分**（同一患者的多张图像不能分在不同集合）
- 报告划分的随机种子
- 报告各集合的类别分布

### 11. 数据增强策略
- 几何变换：rotation, flip, scaling, elastic deformation
- 强度变换：brightness, contrast, noise, blur
- 高级增强：CutMix, MixUp, mosaic（如适用）
- 测试时增强（TTA）：推理时是否使用
- 报告：所有增强参数和概率

### 12. 类别不平衡处理
- 数据层面：oversampling（SMOTE）, undersampling, balanced sampling
- 损失函数层面：weighted CE, focal loss, Dice loss
- 评估层面：不用 accuracy，用 AUROC/AUPRC/F1
- 报告：类别比例和采用的处理策略

### 13. 消融实验设计（Ablation Study）
- 每次去掉一个组件/模块，观察性能变化
- 必须包含：baseline → + component A → + component B → full model
- 用相同的数据划分和随机种子
- 报告：每个消融条件的所有评估指标

### 14. 模型比较统计检验
- Bootstrap 95% CI（重采样 1000-2000 次）
- DeLong test（比较两个 AUROC）
- McNemar test（比较两个分类器的错误模式）
- Wilcoxon signed-rank test（比较 K-fold 结果）
- 注意：不能只报告点估计，必须有 CI 和 p-value

### 15. 模型可解释性方案
- 分类任务：Grad-CAM, SHAP, attention visualization
- 分割任务：attention map, uncertainty map
- 报告：至少 3-5 例典型案例的可视化
- 是否需要临床医生评估可解释性输出？

### 16. 不确定性量化（如适用于安全关键应用）
- MC Dropout（推理时保持 dropout，多次前向传播）
- Deep Ensembles（多独立模型，用预测分歧）
- Test-Time Augmentation（推理时增强，用预测变异）
- 校准：Expected Calibration Error (ECE), reliability diagram

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "分析很简单不需要计划" | 无计划 = p-hacking 的温床 |
| "先看看数据再决定方法" | 看了数据再选方法 = 事后假设 |
| "只分析主要结局就行" | 必须预先指定所有计划分析 |
| "缺失数据直接删掉" | 必须说明缺失机制并选择对应处理策略 |
| "不需要敏感性分析" | 审稿人一定会要求 |

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
