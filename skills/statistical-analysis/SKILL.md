---
name: statistical-analysis
description: Use when executing statistical analysis on research data. Triggers on "跑分析"、"统计检验"、"回归"、"生存分析"、"差异分析"、"帮我算". Requires data-analysis-planning to be completed first.
---

# Statistical Analysis

## Overview

按 `analysis-plan.md` 逐步执行。所有分析必须生成可复现脚本，不允许只输出结果不给代码。

## When to Use

执行具体的统计分析、建模、检验。

## When NOT to Use

- 还没有分析计划 → 先用 `data-analysis-planning`
- 需要做图 → 用 `figure-generation`
- 选择方法阶段 → 用 `data-analysis-planning`

## Workflow

### Step 1: 数据加载与探索

```python
import pandas as pd, numpy as np
df = pd.read_csv('data.csv')
print(f"N={df.shape[0]}, vars={df.shape[1]}")
print(f"Missing:\n{df.isnull().sum()}")
print(f"Dtypes:\n{df.dtypes}")
print(f"Descriptive:\n{df.describe()}")
```

### Step 2: 数据清洗（按 analysis-plan.md Section 2 执行）

**原则：所有清洗操作必须生成 `data-cleaning-log.md` 并保留清洗脚本，确保可审计、可复现。**

#### 2.1 缺失数据处理

```python
# ─── 2.1 Missing Data Assessment ───
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(1)
print("[Cleaning] Missing data summary:")
print(pd.DataFrame({'n_missing': missing, 'pct': missing_pct}).query('n_missing > 0'))
```

| 缺失比例 | 策略 | 代码模板 |
|---------|------|---------|
| 0% | 无需处理 | — |
| <5% | 完整病例分析（需说明理由） | `df_clean = df.dropna(subset=[...])` |
| 5-20% | 多重插补（MICE，m≥20） | `from sklearn.impute import IterativeImputer` |
| >20% | 多重插补 + MNAR 敏感性分析 | 需额外分析假设 |
| 某变量>40% | 考虑该变量是否应纳入分析 | 与用户讨论 |

**必须记录：**
- 每个变量的缺失数量和比例
- Little's MCAR 检验结果（如适用）
- 选择的处理策略和理由
- 处理前后的样本量变化

#### 2.2 异常值检测与处理

```python
# ─── 2.2 Outlier Detection ───
from scipy import stats

for col in numeric_cols:
    z = np.abs(stats.zscore(df[col].dropna()))
    q1, q3 = df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    outliers_z = (z > 3).sum()
    outliers_iqr = ((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum()
    if outliers_z > 0 or outliers_iqr > 0:
        print(f"[Cleaning] {col}: {outliers_z} outliers (Z>3), {outliers_iqr} outliers (IQR)")
```

| 检测方法 | 适用场景 |
|---------|---------|
| Z-score > 3 | 近似正态的连续变量 |
| IQR × 1.5 | 偏态分布 |
| 临床合理范围 | 有医学意义的阈值（如年龄 0-120, BMI 10-80） |

**处理策略（必须在 analysis-plan.md 中预先指定）：**
- 保留并标注（推荐默认）
- Winsorize（截尾到 P1/P99）
- 移除（必须在敏感性分析中比较移除前后结果）

**禁止：** 不说明理由地删除异常值。

#### 2.3 数据类型校验与转换

```python
# ─── 2.3 Data Type Validation ───
# 检查分类变量编码
for col in categorical_cols:
    print(f"[Cleaning] {col}: {df[col].nunique()} levels — {df[col].value_counts().to_dict()}")

# 日期转换
# df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

# 变量重编码（如需要）
# df['stage'] = df['stage'].map({'I': 1, 'II': 2, 'III': 3, 'IV': 4})
```

检查项：
- [ ] 连续变量确实是 numeric 类型（非 object/string）
- [ ] 分类变量的 levels 正确（无拼写错误、无意外编码）
- [ ] 日期变量已正确解析
- [ ] 二分类变量的编码一致（0/1 或 Yes/No，不混用）
- [ ] 变量名与 `analysis-plan.md` 中的变量名一致

#### 2.4 生成清洁数据集

```python
# ─── 2.4 Export Clean Dataset ───
print(f"[Cleaning] Original N={len(df)}, Clean N={len(df_clean)}, Removed={len(df)-len(df_clean)}")
df_clean.to_csv('data_clean.csv', index=False)
```

**必须保留原始数据文件（`data.csv`），清洗后数据另存（`data_clean.csv`）。后续所有分析使用 `data_clean.csv`。**

#### 输出: `data-cleaning-log.md`

```markdown
# Data Cleaning Log

**Date:** [日期]
**Input:** data.csv (N=[原始行数], vars=[变量数])
**Output:** data_clean.csv (N=[清洗后行数])
**Records removed:** [N] ([X]%)

## Missing Data

| Variable | N Missing | % Missing | Strategy | Justification |
|----------|----------|-----------|----------|---------------|
| [var1] | [N] | [X%] | Complete case | <5%, MCAR (Little's p=X) |
| [var2] | [N] | [X%] | Multiple imputation (m=20) | MAR assumed |
...

## Outliers

| Variable | N Outliers | Method | Action | Justification |
|----------|-----------|--------|--------|---------------|
| [var1] | [N] | IQR | Retained | Within clinical range |
| [var2] | [N] | Z>3 | Winsorized to P1/P99 | Biologically implausible values |
...

## Data Type Corrections

| Variable | Original Type | Corrected Type | Notes |
|----------|--------------|----------------|-------|
| [var1] | object | float64 | Removed non-numeric entries (N=[X]) |
| [var2] | string | datetime | Format: YYYY-MM-DD |
...

## Recoding

| Variable | Original Coding | New Coding | Reason |
|----------|----------------|------------|--------|
| [var1] | "Male"/"Female" | 0/1 | Required for regression |
...

## Before vs After Summary

| Metric | Before | After |
|--------|--------|-------|
| Total N | [X] | [X] |
| Complete cases | [X] ([X%]) | [X] ([X%]) |
| Variables | [X] | [X] |
```

### Step 3: 前提假设检验（使用脚本）

```python
import sys; sys.path.insert(0, 'scripts')
from assumption_tests import full_check, effect_size_cohens_d

result = full_check(group1, group2, paired=False)
print(f"Recommended: {result['recommended_test']}")
```

**如果前提不满足，自动切换到非参数方法。** 方法选择参考 `data-analysis-planning` skill 中的 `stat-method-decision-tree.yaml` 决策树（路径：`skills/data-analysis-planning/references/stat-method-decision-tree.yaml`）。

### Step 4: 执行分析

按 `analysis-plan.md` 逐步执行。每个分析输出必须包含：

| 必须报告 | 说明 |
|---------|------|
| 统计量 + 值 | 如 t=2.35, F=4.12, χ²=8.91 |
| p 值 | 精确值，如 p=0.023（不只 p<0.05） |
| 效应量 | Cohen's d / OR / HR / η² 等 |
| 95% CI | 效应量的置信区间 |
| 样本量 | 每组 n |

### Step 5: 样本量计算（如需要）

```python
from power_analysis import two_groups, diagnostic, survival
result = two_groups(effect_size=0.5, power=0.80, dropout=0.15)
```

### Step 6: 生成输出文件（4 个必须）

#### 文件 1: `analysis_script.py`（完整可执行源代码）

**必须满足：** 任何人拿到数据文件 + 这个脚本，可以一键复现所有结果。

```python
"""
Statistical Analysis Script — Generated by Med-Research-Powers
================================================================
Research Question: {research_question}
Analysis Plan: analysis-plan.md
Date: {date}
Author: {author}
================================================================
Environment:
  Python: {version}
  pandas: {pd_version}
  scipy: {scipy_version}
  statsmodels: {sm_version}
Random Seed: 42
================================================================
"""

import sys, os
import pandas as pd
import numpy as np
from scipy import stats
np.random.seed(42)

# Print environment for reproducibility
print(f"Python {sys.version}")
for pkg in ['pandas', 'numpy', 'scipy', 'statsmodels']:
    print(f"{pkg} {__import__(pkg).__version__}")

# ─── 0. Data Loading ───
df = pd.read_csv('data.csv')
print(f"\n[Data] N={df.shape[0]}, Variables={df.shape[1]}")
print(f"[Data] Missing values:\n{df.isnull().sum()[df.isnull().sum()>0]}")

# ─── 1. Descriptive Statistics ───
# (按 analysis-plan.md Section 3 执行)

# ─── 2. Assumption Tests ───
# (调用 assumption_tests.py)

# ─── 3. Primary Analysis ───
# (按 analysis-plan.md Section 4 逐条执行)
# 每个分析输出: 统计量、p值、效应量、95% CI、样本量

# ─── 4. Secondary / Subgroup Analysis ───
# (按 analysis-plan.md Section 5 执行)

# ─── 5. Sensitivity Analysis ───
# (按 analysis-plan.md Section 6 执行)

# ─── 6. Export Results ───
# results.to_csv('results_tables.csv', index=False)
```

**脚本结构要求：**
- 每个分析段用 `# ─── N. Title ───` 分隔，与 `analysis-plan.md` 章节一一对应
- 每个统计检验前有注释说明目的和对应的假设
- 每个结果用 `print()` 输出，格式：`[Analysis N] test_name: stat=X.XX, p=X.XXXX, effect_size=X.XX (95% CI: X.XX–X.XX), n1=X, n2=X`
- 脚本末尾导出结果表格为 CSV

#### 文件 2: `analysis-log.md`（分析执行日志）

记录分析过程中的每一步决策和发现：

```markdown
# Analysis Execution Log

**Date:** [日期]
**Script:** analysis_script.py
**Data File:** data.csv (N=[N], vars=[N])

## Pre-Analysis Checks

| Check | Result | Action |
|-------|--------|--------|
| Missing data (%) | [变量: X%] | [处理方式] |
| Outliers detected | [N] in [变量] | [保留/移除/Winsorize，理由] |
| Normality (Shapiro-Wilk) | Group A: p=[X], Group B: p=[X] | [参数/非参数] |
| Homogeneity (Levene) | p=[X] | [t-test/Welch's] |

## Analysis Execution

### Analysis 1: [名称] (对应 analysis-plan.md Section 4.1)
- **Method:** [实际使用的方法]
- **Plan vs Actual:** [是否与 SAP 一致？不一致的原因]
- **Result:** stat=[X], p=[X], effect=[X] (CI: [X–X])
- **Interpretation:** [一句话解释]

### Analysis 2: [名称]
...

## Deviations from Analysis Plan

| # | Planned | Actual | Reason |
|---|---------|--------|--------|
| 1 | Independent t-test | Welch's t-test | Levene p=0.02, variance unequal |
| 2 | [计划方法] | [实际方法] | [原因] |

## Sensitivity Analysis Results

| Primary Result | Sensitivity Check | Consistent? |
|---------------|-------------------|-------------|
| [主要发现] | [替代方法] | ✅ / ⚠️ |
| [主要发现] | [排除异常值] | ✅ / ⚠️ |
| [主要发现] | [不同缺失处理] | ✅ / ⚠️ |

## Issues Encountered
- [如有：分析中遇到的问题和解决方式]
```

#### 文件 3: `results-summary.md`（结果报告）

供 `manuscript-writing` 直接使用的结构化结果报告：

```markdown
# Results Summary

**Research Question:** [一句话]
**Date:** [日期]
**Analysis Script:** analysis_script.py

## Sample Characteristics

| Variable | Total (N=[X]) | Group A (n=[X]) | Group B (n=[X]) | p-value |
|----------|:---:|:---:|:---:|:---:|
| Age, mean±SD | X±X | X±X | X±X | [X] |
| Male, n(%) | X(X%) | X(X%) | X(X%) | [X] |
...

## Primary Outcome

| Outcome | Group A | Group B | Difference | 95% CI | p-value | Effect Size | 95% CI |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| [主要结局] | X±X | X±X | X | [X–X] | [X] | d=[X] | [X–X] |

**Method:** [统计方法]
**Interpretation:** [一句话结论，区分统计显著性和临床意义]

## Secondary Outcomes

| # | Outcome | Result | p-value | Effect Size (95% CI) |
|---|---------|--------|---------|---------------------|
| 1 | [次要结局1] | [结果] | [X] | [X (X–X)] |
| 2 | [次要结局2] | [结果] | [X] | [X (X–X)] |

**Multiple comparison correction:** [方法], adjusted p-values shown

## Subgroup Analyses

| Subgroup | n | Effect Size (95% CI) | Interaction p |
|----------|---|---------------------|---------------|
| [亚组1] | [X] | [X (X–X)] | [X] |
| [亚组2] | [X] | [X (X–X)] | — |

## Sensitivity Analyses

| Analysis | Primary Result Confirmed? | Notes |
|----------|:---:|-------|
| [替代方法] | ✅ | [简要说明] |
| [排除异常值] | ✅ | [简要说明] |
| [不同缺失处理] | ⚠️ | [差异说明] |

## Key Numbers for Abstract
- Primary outcome: [一句话，含数字]
- Main effect size: [d/OR/HR = X, 95% CI X–X, p=X]
- Sample: N=[X] ([X] in Group A, [X] in Group B)

## Figures Needed
- [ ] Figure 1: [描述] → `figure-generation`
- [ ] Figure 2: [描述] → `figure-generation`
- [ ] Table 1: Baseline characteristics (above)
- [ ] Table 2: Primary and secondary outcomes (above)
```

**4 个文件的关系：**
- `data-cleaning-log.md` → **清洗记录**（可审计）→ 供 `manuscript-writing` Methods 写数据预处理段落
- `analysis_script.py` → **源代码**（可复现）→ 含清洗 + 分析完整流程
- `analysis-log.md` → **过程记录**（可追溯）→ 供 Gate 3 追踪 SAP 偏差
- `results-summary.md` → **结果报告**（供下游使用）→ 供 `manuscript-writing` Results 写作

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "数据看起来正态的" | 用 Shapiro-Wilk 检验，不要肉眼判断 |
| "p=0.06 接近显著" | 不显著就是不显著，报告精确值 |
| "多做几个检验总有显著的" | p-hacking，必须做多重比较校正 |
| "只报 p<0.05" | 必须报精确 p 值 + 效应量 + CI |
| "用 Excel 算就行" | 生成可复现的 Python/R 脚本 |
| "不做敏感性分析也行" | 审稿人一定会要求，主动做 |

## Convergence

当以下条件全部满足时完成：
1. `analysis-plan.md` 中每个预定分析都已执行
2. 所有前提假设已验证并记录在 `analysis-log.md`
3. 效应量 + 95% CI 已计算
4. 敏感性分析确认结果稳健
5. 与 SAP 的偏差已在 `analysis-log.md` 中说明
6. 4 个输出文件全部生成：
   - `data-cleaning-log.md`（清洗过程可审计）
   - `analysis_script.py`（可独立运行，一键复现）
   - `analysis-log.md`（分析过程可追溯）
   - `results-summary.md`（结果可直接用于写作）

## Red Flags — STOP

- 没有 analysis-plan.md → **阻止执行**，先做计划
- 跳过假设检验直接用参数方法 → 停，先检验
- 只报告"显著"的结果 → 必须报告所有预定分析

## 衔接规则

### 前置依赖
- **必须**有 `analysis-plan.md`（`data-analysis-planning` 生成）

### 强制衔接
- 完成后 → **必须**触发 `figure-generation` 做数据可视化
- `results-summary.md` → 传递给 `manuscript-writing`（Results 写作）
- `analysis_script.py` → 传递给 `pre-submission-verification` Gate 2（脚本可复现性检查）
- `analysis-log.md` → 传递给 `pre-submission-verification` Gate 3（SAP 偏差追踪）
