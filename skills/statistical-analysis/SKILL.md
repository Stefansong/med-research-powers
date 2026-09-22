---
name: statistical-analysis
description: Use when analysis-plan.md already exists and the analysis must now be run on collected data（已有分析计划时执行分析）. Triggers on "跑分析"、"统计检验"、"回归"、"生存分析"、"差异分析"、"帮我算".
---

# Statistical Analysis

## Overview

按 `analysis-plan.md` 逐步执行。所有分析必须生成可复现脚本，不允许只输出结果不给代码。本 skill 只"执行"计划，不"制定"计划——方法选择在 `data-analysis-planning` 完成。

## When to Use

- 已有 `analysis-plan.md`，数据已收集完毕，要执行统计分析、建模、检验
- 审稿人要求的补充分析（须标注 post hoc / exploratory 并记录 SAP 偏差）

## When NOT to Use

- 还没有 `analysis-plan.md` → 先用 `data-analysis-planning`（"帮我分析数据"但无计划时也归它）
- 需要做图 → `figure-generation`
- 要改方法、加分析 → 回 `data-analysis-planning` 更新 SAP，再回来执行

## Scripts

四个脚本都在插件目录，运行目录是用户项目，必须用 `${CLAUDE_PLUGIN_ROOT}` 定位：

| 脚本 | 用途 | 一行可运行示例 |
|------|------|---------------|
| `data_cleaning.py` | 缺失概览、Z/IQR/临床范围异常值、类型检查、`data-cleaning-log.md` | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/data_cleaning.py" data.csv --continuous age,bmi --categorical sex --range age=0:120` |
| `assumption_tests.py` | 正态性 / 方差齐性 / 配对差值检验 + 方法推荐（JSON） | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/assumption_tests.py" data_clean.csv --value outcome --group arm` |
| `power_analysis.py` | 先验样本量复核（two-groups / proportion / survival / diagnostic / correlation） | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py" survival --hr 0.7 --event-rate 0.5` |
| `analysis_template.py` | `analysis_script.py` 的骨架（环境打印、随机种子、分段结构） | `cp "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/analysis_template.py" analysis_script.py` |

在 Python 里导入时同样不能写相对路径：

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                "skills", "statistical-analysis", "scripts"))
from assumption_tests import full_check, effect_size_cohens_d
from data_cleaning import missing_summary, detect_outliers, check_types
```

缺依赖时脚本会直接提示 `pip install ...`（scipy / statsmodels / pandas），按提示安装即可。

## Workflow

### Step 0: 核对前置条件

1. 读取 `analysis-plan.md`，列出计划中的全部分析（主要、次要、亚组、敏感性）及各自的方法与前提假设
2. 确认原始数据文件（默认 `data.csv`）存在；变量名与 SAP 一致
3. 缺任一项 → 停，不要"先跑着看看"

### Step 1: 数据加载与探索

```python
import pandas as pd, numpy as np
df = pd.read_csv('data.csv')
print(f"N={df.shape[0]}, vars={df.shape[1]}")
print(df.dtypes); print(df.describe(include='all'))
```

只看结构、类型、范围，**不看组间结果**（防止看到结果后改方法）。

### Step 2: 数据清洗（按 analysis-plan.md Section 2 执行）

**原则：所有清洗操作必须生成 `data-cleaning-log.md` 并保留清洗脚本，确保可审计、可复现。** 原始 `data.csv` 永不修改，清洗后另存 `data_clean.csv`，后续所有分析只用 `data_clean.csv`。

用 `data_cleaning.py` 完成 2.1–2.4（脚本默认只报告不改数据；每个清洗动作都要用参数显式指定，并且必须是 SAP 里预先写明的）：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/data_cleaning.py" data.csv \
  --out data_clean.csv --log data-cleaning-log.md \
  --continuous age,bmi,psa --categorical sex,stage --dates visit_date \
  --range age=0:120 bmi=10:80 \
  --complete-case outcome        # 仅当 SAP 规定完整病例分析
  # --winsorize psa              # 仅当 SAP 规定截尾到 P1/P99
  # --recode sex=Male:0,Female:1 --drop-cols free_text
```

#### 2.1 缺失数据

脚本输出每个变量的缺失数和比例，并按下表给出默认策略；**缺失规则的唯一维护处是** `${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/stat-method-decision-tree.yaml` 的 `missing_data`（比例 × 机制二维表），以 SAP 中已选定的策略为准。

| 缺失比例 | 默认策略 |
|---------|---------|
| <5% | 完整病例分析（需说明理由）或多重插补 |
| 5–20% | 多重插补（m ≥ 20）+ Rubin 合并 |
| >20% | 多重插补 + MNAR 敏感性分析（tipping point） |
| 某变量 >40% | 与用户讨论该变量是否纳入 |

**缺失机制**：Little's MCAR 检验在 scipy / statsmodels / sklearn 里没有现成实现。可用 R `naniar::mcar_test()` 或 Python 包 `pyampute`（`from pyampute.exploration.mcar_statistical_tests import MCARTest`）；两者都装不了时用替代做法并在日志里写明：按"该变量是否缺失"分组，比较其他变量的分布（t 检验 / χ²，或 `missingno` 缺失模式图）——有系统差异则不能按 MCAR 处理，按 MAR 做多重插补并做敏感性分析。

**多重插补必须是"多"重**：`IterativeImputer` 默认只给一份插补值，不是 MI。正确做法是生成 m 份数据集、各自分析、再用 Rubin 规则合并：

```python
import numpy as np, pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
import statsmodels.api as sm

m = 20
estimates, variances = [], []
for i in range(m):
    imp = IterativeImputer(sample_posterior=True, random_state=i, max_iter=10)
    df_i = pd.DataFrame(imp.fit_transform(df_clean[num_cols]), columns=num_cols)
    fit = sm.OLS(df_i['outcome'], sm.add_constant(df_i[['exposure', 'age']])).fit()
    estimates.append(fit.params['exposure']); variances.append(fit.bse['exposure'] ** 2)

q_bar = np.mean(estimates)                      # Rubin: 合并点估计
u_bar = np.mean(variances)                      # 插补内方差
b = np.var(estimates, ddof=1)                   # 插补间方差
t_var = u_bar + (1 + 1 / m) * b                 # 总方差
print(f"pooled beta={q_bar:.3f}, SE={np.sqrt(t_var):.3f}")
```

`sample_posterior=True` 让每次插补从后验分布抽样（否则 m 份结果完全相同）；`random_state=i` 保证 m 份不同且可复现。也可以直接用 `statsmodels.imputation.mice.MICEData` + `MICE(...).fit(n_imputations=20)`，它内置 Rubin 合并。日志中记录 m、插补模型包含的变量、合并后的估计。

#### 2.2 异常值

脚本同时给出 Z>3、IQR×1.5 和临床合理范围三种计数；处理策略必须是 SAP 预先指定的：保留并标注（默认）/ Winsorize 到 P1/P99（`--winsorize`）/ 移除（`--drop-out-of-range`，且必须在敏感性分析中比较移除前后）。**禁止不说明理由地删除异常值。**

#### 2.3 类型校验

脚本报告：连续变量含非数字、分类变量大小写/空格不一致、日期无法解析。检查项：
- [ ] 连续变量是 numeric 类型；分类变量 levels 正确；日期已解析
- [ ] 二分类编码一致（0/1 或 Yes/No，不混用）
- [ ] 变量名与 `analysis-plan.md` 一致

#### 2.4 产出

`data_clean.csv` + `data-cleaning-log.md`（脚本按 `references/output-templates.md` 第 1 节格式生成，把表中 `[填写理由]` 补齐）。

### Step 3: 前提假设检验

```python
result = full_check(group1, group2, paired=False)    # 或 paired=True（自动按完整配对过滤、检验差值正态性）
print(result['recommended_test'], result['warnings'])
```

规则：任一组 n<8 → 正态性无法检验，脚本按非参数处理并给 warning；配对 >2 组 → 不做 Levene，改在 RM-ANOVA 里用 Mauchly 球形检验 / Greenhouse-Geisser 校正。**前提不满足就切换到非参数方法**，并把切换记录为 SAP 偏差。方法对照表：`${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/stat-method-decision-tree.yaml`。

### Step 4: 执行分析

按 `analysis-plan.md` 逐条执行，先主要分析，再次要、亚组、敏感性。每个分析必须报告：

| 必须报告 | 说明 |
|---------|------|
| 统计量 + 值 | 如 t=2.35, F=4.12, χ²=8.91 |
| p 值 | 精确值，如 p=0.023（p<0.001 时写 p<0.001） |
| 效应量 | Cohen's d / OR / HR / η² 等 |
| 95% CI | 效应量的置信区间 |
| 样本量 | 每组 n（含缺失后实际进入分析的 n） |

### Step 5: 样本量复核（仅先验）

`power_analysis.py` 在这里**只用于复核** `study-protocol.md` 里的先验样本量计算（参数是否抄对、实际入组是否达到）。**禁止用观察到的效应量算"事后 power"**——它只是 p 值的换算，审稿人会直接指出。样本不足时如实写进 Limitations。

### Step 6: 生成输出文件

按下方 Output 表生成 4 个文件。`analysis_script.py` 以 `analysis_template.py` 为起点，要求：
- 加载 `data_clean.csv`（不是 `data.csv`）；每段用 `# ─── N. Title ───` 分隔并与 SAP 章节一一对应
- 每个检验前有注释说明目的与假设；结果用 `print()` 输出：`[Analysis N] test: stat=X.XX, p=X.XXXX, effect=X.XX (95% CI: X.XX–X.XX), n1=X, n2=X`
- 末尾导出结果表 CSV；任何人拿到数据 + 脚本可一键复现

### Step 7: 更新项目状态

输出 3–5 行摘要（产物、关键决策、待注意），然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 statistical-analysis 及 4 个产物、`artifacts` 登记 `results-summary.md` 与 `analysis-log.md`、`next_step` 设为 figure-generation），直接进入 `figure-generation`（默认轻量确认，不等待）。

## Output

| 文件 | 必须 | 内容 | 模板 | 下游 |
|------|------|------|------|------|
| `data-cleaning-log.md` | 是 | 缺失、异常值、类型校正、重编码、清洗前后 N | `references/output-templates.md` §1 | `manuscript-writing` Methods 数据预处理段 |
| `analysis_script.py` | 是 | 清洗 + 分析完整源代码，一键复现 | `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/analysis_template.py` | `pre-submission-verification` Gate 2（可复现性） |
| `analysis-log.md` | 是 | 前提检验、逐条执行记录、与 SAP 的偏差、敏感性分析、问题 | `references/output-templates.md` §2 | `pre-submission-verification` Gate 3（SAP 偏差追踪） |
| `results-summary.md` | 是 | 样本特征、主要/次要/亚组/敏感性结果、Key Numbers、所需图表清单 | `references/output-templates.md` §3 | `figure-generation`、`manuscript-writing` Results |

`results-summary.md` 的基线表：RCT 不填 p 值（随机化后差异只能来自机会），用标准化均数差 SMD 描述均衡性；观察性研究可报 p 值或 SMD。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "数据看起来正态的" | 用 Shapiro-Wilk / D'Agostino 检验，不要肉眼判断 |
| "p=0.06 接近显著" | 不显著就是不显著，报告精确值 |
| "多做几个检验总有显著的" | p-hacking，必须做多重比较校正 |
| "只报 p<0.05" | 必须报精确 p 值 + 效应量 + CI |
| "IterativeImputer 跑一次就是多重插补" | 一次只是单次插补；要 m 份 + Rubin 合并 |
| "结果不显著，算个事后 power 说明样本不够" | 事后 power 是 p 值的换算，没有信息量；写进 Limitations 即可 |
| "用 Excel 算就行" | 生成可复现的 Python/R 脚本 |
| "不做敏感性分析也行" | 审稿人一定会要求，主动做 |

## Convergence

当以下条件全部满足时完成：
1. `analysis-plan.md` 中每个预定分析都已执行
2. 所有前提假设已验证并记录在 `analysis-log.md`
3. 效应量 + 95% CI 已计算
4. 敏感性分析确认结果稳健
5. 与 SAP 的偏差已在 `analysis-log.md` 中说明
6. 4 个输出文件全部生成（见 Output）
7. `.mrp-state.json` 已更新

## Red Flags — STOP

- 没有 `analysis-plan.md` → **停止执行**，先做计划
- 跳过假设检验直接用参数方法 → 停，先检验
- 只报告"显著"的结果 → 必须报告所有预定分析
- 在原始 `data.csv` 上直接分析 → 停，走 Step 2
- 看到结果后想换方法 / 换主要结局 → 停，回 SAP 并记录偏差

## 衔接规则

### 前置依赖（不满足则阻止）
- **必须**有 `analysis-plan.md`（`data-analysis-planning` 生成，硬确认 2 已通过）
- **必须**有数据文件（用户按 `data-collection-tools` 生成的工具收集完毕）

### 强制衔接（不可跳过）
- 完成后 → `figure-generation`（读取 `results-summary.md` 的"Figures Needed"）
- `results-summary.md` → `manuscript-writing`（Results 写作）
- `analysis_script.py` → `pre-submission-verification` Gate 2；`analysis-log.md` → Gate 3
- 最后一步固定为更新 `.mrp-state.json`（Step 7）

### 可选衔接
- 需要调整方法 / 新增分析 → 回 `data-analysis-planning` 更新 SAP，并在 `analysis-log.md` 记录偏差
- 审稿意见触发的补充分析（`revision-response`）→ 一律标注 post hoc / exploratory
- 结果报告规范检查 → `reporting-standards`（CONSORT / STROBE / TRIPOD 等）
