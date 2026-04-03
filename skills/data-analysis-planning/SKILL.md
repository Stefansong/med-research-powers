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

### 可选
- 组学数据 → `references/omics-methods.md`
