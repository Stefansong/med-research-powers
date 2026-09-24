# 缺失数据 — 方法要点卡

> 适用：任何分析中协变量、暴露或结局有缺失（包括"/"、"未查"、999 这类伪装缺失）时的判断、处理与报告。　不适用：按"缺失比例 × 缺失机制"选策略的阈值规则（<5% / 5–20% / >20%，单个变量 >40%）——只在 `stat-method-decision-tree.yaml` 的 `missing_data` 维护，本卡只引用、不重复；生存数据的删失（删失不是缺失，见 `survival-analysis.md`）。

## 1. 计划前先看数据的什么

只看结构和质量。比较"缺失者与非缺失者"的基线特征是为了判断缺失机制，**不借此看**暴露/分组与结局的关系；"是否缺失"与结局的关系（如结局在完整者和不完整者中各是多少）也是结局关联，计划前同样不看：
- 先把伪装缺失找出来：空单元格之外的 "/"、"未查"、"不详"、"NA"、"—"、999/9999、不可能为 0 的指标记成了 0。用只读检查列出每个变量的非数字取值及其频数（`data_profile.py` + 现写的只读检查），逐个确认哪些代表缺失。"<0.1"、">1000" 是截断值，不是缺失，要单独处理并记录。
- 每个变量的缺失数与比例；不完整病例（分析要用的变量中任一有缺失的患者）占多少——决定插补份数 m。
- 缺失模式：单调（中途退出后全缺）还是零散；哪些变量总是一起缺（同一项检查的一组指标）；缺失是否集中在某个中心、某个时间段、某个数据来源（如某中心没开展这项检查）。
- 缺失原因：问临床和数据管理人员——"未查"是因为病情轻所以没查（可能是非随机缺失），还是设备没开展（更接近随机）。
- 结局有没有缺失、主要暴露有没有缺失（两者的处理和报告要求不同）。
- 辅助变量：有没有与缺失变量相关、但不在分析模型里的变量（可以放进插补模型）。

## 2. 计划里必须预先写明

- **先计划、再核对**：先写分析模型和缺失的处理方式，拿到数据后核对计划是否仍然合适，再按计划分析并完整报告（TARMOS 框架，Lee 2021）。
- **选哪一格**：每个关键变量的预期或实际缺失比例，按 yaml `missing_data` 的比例 × 机制表写明选了哪一格、为什么。
- **缺失机制的判断思路**：
  - MCAR（完全随机缺失）无法被证明，只能被否定：Little 检验显著 → 不是 MCAR；不显著也不能说明就是 MCAR。
  - MAR（给定已观测变量之后随机缺失）是多重插补的前提；靠临床知识和辅助变量让它更可信。
  - MNAR（缺失与未观测到的值本身有关，如病情越重越不来复查）不能用数据检验，只能做敏感性分析。
- **完整病例分析什么时候可以接受**：对多数回归模型，只要"是否完整"与结局无关（给定模型里的协变量之后），完整病例的估计就不偏——即使暴露或混杂是 MNAR；反过来，"是否完整"与结局有关时完整病例有偏（Hughes 2019）。缺失很少且这个条件说得通时可作主要分析，但要写理由，并报告少了多少人。这个条件在计划阶段只能靠临床知识来论证；如果想用数据检查（如以"是否完整"为因变量、把结局也放进去的 logistic 模型，Hughes 2019 的做法），就把这项检查预先写进 SAP，SAP 批准后再做并报告结果，不能在定计划之前先跑。
- **多重插补（MICE，链式方程多重插补）**：
  - 插补模型必须包含结局，以及分析模型中的全部变量（暴露、全部协变量，以及交互项、非线性项），再加辅助变量（Hughes 2019；White 2011）；有聚类时插补也要考虑聚类（见 `clustered-and-repeated-data.md`）。生存结局放事件指示变量和 Nelson-Aalen 累积风险，不放原始时间（`mice::nelsonaalen()` 文档引 White & Royston 2009）。
  - 每个变量的插补方法：连续变量用预测均值匹配（PMM），二分类用 logistic，无序多分类用多项 logistic，有序用有序 logistic（mice 的默认设置即如此）；偏态变量用 PMM 可避免插出不可能的值。
  - 派生变量（BMI、eGFR、比值、量表总分、交互项、平方项）二选一并写明：被动插补（先插补原始成分，再按公式算派生变量），或把派生变量当作普通变量一起插补（White 2011）。
  - 插补份数 m：经验规则是 m ≥ 不完整病例的百分比（如 30% 的病例有缺失 → m ≥ 30）（White 2011），与 yaml 的 m ≥ 20 取较大者；写明迭代次数、随机种子和收敛检查（迹线图）。
  - 合并：每份数据分别分析，再用 Rubin 规则合并估计值与方差；OR、HR 在对数尺度上合并；不能把 m 份数据平均成一份再分析。
  - 与其他步骤的先后顺序要写明：预测模型的 bootstrap 验证在插补数据里怎么做；倾向性评分分析在每份插补数据里分别估 PS、做匹配/加权和平衡检查、估计效应，再用 Rubin 规则合并各份的效应（插补模型包含结局），不要先把各份的 PS 平均成一个再分析（Leyrat 2019；见 `propensity-score.md`）。
- **MNAR 敏感性分析**：delta 调整——在插补值上加（或乘）一个偏移 δ，表示"缺失者比同类的已观测者更差或更好"，δ 的取值要有临床依据；tipping point 分析——逐步加大 δ，找到让结论翻转的 δ，并讨论这个 δ 在临床上是否可能（Cro 2020）。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| 伪装缺失转为缺失值 | 读入时 `read.csv(..., na.strings = c("", "/", "未查", "不详"))`；已读入的用 `naniar::replace_with_na(d, replace = list(x = c(999, 9999)))` | 按列写：`pandas.read_csv(..., na_values={"plt": ["/", "未查", "999"], "crea": ["/", "未查"]})`；已读入的用 `df["plt"] = df["plt"].replace(999, np.nan)`。不要给 `na_values` 传一个全表通用的列表并在里面放 999：编号、计数、化验值里真实的 999（连同 999.0）会被一起变成缺失，而且不报错。每列哪些写法代表缺失，先对照编码手册和 `data_profile.py` 的结果逐列确认 |
| 缺失概况与模式 | `naniar::miss_var_summary()`、`gg_miss_upset()`；`mice::md.pattern()` | `missingno.matrix()`、`missingno.heatmap()`；`df.isna().mean()` |
| Little MCAR 检验 | `naniar::mcar_test(d)` | `pyampute.exploration.mcar_statistical_tests.MCARTest(method="little").little_mcar_test(df)` |
| 多重插补 | `mice::mice(d, m = <m>, method = <按变量指定>, predictorMatrix = <矩阵>, maxit = <迭代次数>, seed = <种子>)` | `statsmodels.imputation.mice.MICEData(df)` + `MICE(formula, model_class, imp_data).fit(n_burnin=..., n_imputations=<m>)`；或 `sklearn` 的 `IterativeImputer(sample_posterior=True, random_state=i)` 循环 m 次 |
| 预测变量矩阵 | `mice::make.predictorMatrix()`；`mice::quickpred(d, include = c(<结局>, <分析变量>))`（用 `include` 强制纳入结局和分析变量） | `MICEData.set_imputer(<变量名>, formula=...)` 逐个指定插补公式 |
| 生存结局的插补 | `d$H0 <- mice::nelsonaalen(d, time, status)`，把 `H0` 和事件指示变量放进插补模型 | 无专门工具：用 `lifelines.NelsonAalenFitter` 算出每人的累积风险，作为插补变量 |
| 合并（Rubin 规则） | `with(imp, glm(...))` 后 `mice::pool()`（默认用 Barnard-Rubin 小样本自由度） | `MICE.fit()` 已内置合并；`IterativeImputer` 路线要自己按 Rubin 规则合并（公式见表下） |
| 派生变量被动插补 | `meth["bmi"] <- "~I(weight / height^2)"`，并在 predictorMatrix 里不让 BMI 反过来预测身高、体重 | 无公认成熟包：插补原始成分后，在每份数据里重新计算派生变量 |
| MNAR delta / tipping point | `mice(..., post = <表达式>)` 在插补值上加 δ，对一组 δ 循环 | 无公认成熟包：插补后在插补位置加 δ 再分析，对一组 δ 循环（手写） |

`IterativeImputer` 路线的 Rubin 规则：第 i 份插补数据（i = 1…m）得到估计值 q_i 和它的方差 U_i（SE 的平方；OR、HR 先取对数）。

```text
合并估计   q̄ = mean(q_i)
组内方差   Ū = mean(U_i)            组间方差 B = var(q_i)（分母 m − 1）
总方差     T = Ū + (1 + 1/m)·B      合并 SE = √T
自由度     λ = (1 + 1/m)·B / T;  ν_old = (m − 1) / λ²
           ν_obs = (ν_com + 1)/(ν_com + 3) · ν_com · (1 − λ)   （ν_com：数据没有缺失时的残差自由度，n − 参数数）
           ν = ν_old · ν_obs / (ν_old + ν_obs)                 （Barnard-Rubin 小样本校正，与 mice::pool() 一致）
95% CI     q̄ ± t(ν, 0.975) · √T      （对数尺度上算完再取指数）
```

## 4. 常见的坑

- "/"、"未查"、999 没转成缺失就进入分析（999 被当成真实数值）；或反过来，全表统一把 999 当缺失，把真实的 999 也删了；或把截断值 "<0.1" 当缺失删掉。
- 默认删除缺失（软件自动做完整病例分析）却不报告删了多少、为什么；不同模型的样本量不一样也不说明。
- 单次插补（均值/中位数填补、`IterativeImputer` 只跑一次、末次观测结转 LOCF）当主要分析：低估不确定性，还可能有偏。
- 插补模型不包含结局：会把协变量与结局的关联拉向 0（White 2011）。
- 插补模型比分析模型"窄"（漏了交互项、非线性项、聚类结构）：插补与分析对不上。
- 把 m 份插补数据平均成一份再分析；或在每份插补数据里各自选变量、各报各的。
- m 太小：mice 默认 m = 5，要按不完整病例百分比设定。
- 把 Little 检验不显著当作"证明是 MCAR"。
- 对缺失超过 40% 的变量硬插补却不讨论（yaml：先讨论是否保留）。
- 只报插补后的结果，不报完整病例结果作对照。
- 预测模型只在开发时插补，没说明实际使用时输入缺失怎么办。

## 5. 结果必须报告

- 每个变量的缺失人数与比例（Table 1 或补充表）；不完整病例比例；每个分析实际纳入的人数。
- 缺失处理方法：完整病例或多重插补；多重插补要报软件与版本、插补模型包含的变量（含结局和辅助变量）、各变量的插补方法、m、迭代次数、随机种子、合并方法。
- 缺失机制的判断依据（临床理由 + 缺失者与非缺失者的基线比较）。
- 主要结果（多重插补）与完整病例结果并列；MNAR 敏感性分析的 δ 取值范围及 tipping point。

## 6. 对应报告规范

- 观察性研究：`strobe` 的 12c（缺失怎么处理）、14b（每个变量的缺失人数）；常规收集的数据加 `record` 的 12.2（数据清洗方法）。
- RCT：`consort-2025` 的 21c（分析中缺失怎么处理）、26（每个结局在该时间点有数据的人数）。
- 预测模型：`tripod-ai` 的 11（缺失处理）、20b（缺失数据量）、27a（模型实际使用时输入缺失怎样处理）。

## 参考

- White IR, Royston P, Wood AM. Multiple imputation using chained equations: issues and guidance for practice. *Stat Med*. 2011;30(4):377-399. doi:10.1002/sim.4067
- Hughes RA, Heron J, Sterne JAC, Tilling K. Accounting for missing data in statistical analyses: multiple imputation is not always the answer. *Int J Epidemiol*. 2019;48(4):1294-1304. doi:10.1093/ije/dyz032
- Lee KJ, Tilling KM, Cornish RP, et al. Framework for the treatment and reporting of missing data in observational studies: the Treatment And Reporting of Missing data in Observational Studies framework. *J Clin Epidemiol*. 2021;134:79-88. doi:10.1016/j.jclinepi.2021.01.008
- Leyrat C, Seaman SR, White IR, et al. Propensity score analysis with partially observed covariates: how should multiple imputation be used? *Stat Methods Med Res*. 2019;28(1):3-19. doi:10.1177/0962280217713032
- Cro S, Morris TP, Kenward MG, Carpenter JR. Sensitivity analysis for clinical trials with missing continuous outcome data using controlled multiple imputation: a practical guide. *Stat Med*. 2020;39(21):2815-2842. doi:10.1002/sim.8569
