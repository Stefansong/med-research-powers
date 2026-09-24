# 基线表与组间比较 — 方法要点卡

> 适用：描述研究人群的基线表（Table 1）；两组或多组之间连续、分类、有序变量的比较及效应量；配对数据（同一批人前后两次、配对样本）的比较。　不适用：需要调整混杂才能回答的因果问题（见 `regression-and-prediction-models.md`、`propensity-score.md`）；生存结局（见 `survival-analysis.md`）；同一患者多条记录（见 `clustered-and-repeated-data.md`）。检验方法的选择分支以 `stat-method-decision-tree.yaml` 为准（默认 Welch，方法在计划里预先定，不按正态性/方差齐性预检验切换），本卡不重复决策树，只写要点与坑。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**分组与结局的关系（组间结局差异是结果，只能在 SAP 确认后按计划计算）：
- 研究设计与分组：RCT 还是观察性研究（决定基线表放不放 p 值）；分组变量怎么编码、每组多少人；有没有未分组、交叉到另一组、失访的人。
- 分析单位：一行是不是一个患者；同一患者多条记录（双侧肾、多个结石/病灶、多次随访）不能当独立样本。
- 配对结构：配对 ID 是否齐全、每对是否完整（术前/术后、配对的病例与对照）。
- 连续变量的整体分布：偏态、极端值、单位混录（如肌酐 mg/dL 与 μmol/L 混在一列）、截断值（"<0.1"、">1000"）——用来预先定"均值±SD 还是中位数(IQR)"。
- 分类变量：水平数、写法不一致（"男/M/1"）、很少见的水平（可能出现期望频数 <5）；有序变量的顺序是否编对。
- 缺失：每个变量缺多少、以什么形式缺（空值、"/"、"未查"、999）；Table 1 要报缺失（见 `missing-data.md`）。
- 多组：各组人数是否悬殊；分组本身是否有序（剂量、分期）——决定用趋势检验还是两两比较。

## 2. 计划里必须预先写明

- **Table 1 写什么**：变量清单；按什么分组、要不要"合计"列；连续变量用均值±SD 还是中位数(IQR) 的判定规则（如明显偏态或有截断值 → 中位数(IQR)），同一变量全文统一；分类变量 n(%)，百分比的分母是否包括缺失者。Table 1 要让读者能判断研究人群是谁、缺失多少（Hayes-Larson 2019）。
- **RCT 基线不做显著性检验、不放 p 值**：随机分组后的基线差异只能来自机会，p 值既证明不了"随机化成功"，也不能用来挑选调整变量；要调整的基线变量按预后重要性在方案里预先定（de Boer 2015）。需要量化差异时只报标准化均数差（SMD，standardized mean difference）作描述。
- **观察性研究**：Table 1 以描述为主，组间差异用 SMD 描述。|SMD| ≥ 0.1 常被当作"有意义的不平衡"，但这只是经验值，预后越重要的变量越要求平衡好（Austin 2009）。期刊要求 p 值时注明仅作描述，不据此选混杂。
- **每个比较的方法与效应量**（分支按 yaml `two_groups` / `multiple_groups`）：
  - **方法在计划里定死，不靠预检验来选**：两组独立的连续变量默认用 Welch t 检验（不假设两组方差相等），多组默认 Welch 方差分析 + Games-Howell。不要先做正态性检验（Shapiro-Wilk）、方差齐性检验（Levene），再按结果在 Student t、Welch、Mann-Whitney 之间切换——这种"先检验再选检验"的两步做法让最终用哪个检验取决于同一份数据：先做 Levene 再选 t 检验的两步法保不住名义的假阳性率，两组人数不等时无条件用 Welch 最稳妥（Zimmerman 2004）；先做正态性检验也会明显改变后续 t 检验和 Mann-Whitney 各自的假阳性率（Rochon 2012）。什么时候改用秩检验（Mann-Whitney / Kruskal-Wallis）或先取对数：在计划里按变量本身的性质定——已知明显偏态（如很多化验值）、有序等级、有上下限或截断值、样本很小。`assumption_tests.py` 的结果和 Q-Q 图只用来描述数据、记入分析日志；发现计划的方法明显不合适时，按"偏离 SAP"写明理由，不能悄悄换检验。
  - 连续、近似对称：均数差 + 95% CI（Welch）；需要跨研究比较时加 Hedges g（小样本校正后的 SMD）+ CI。
  - 连续、计划里定为按秩分析：Hodges-Lehmann 位置差（两组间所有两两差值的中位数）+ CI，或中位数差 + bootstrap CI；只报 Mann-Whitney 的 p 不够。
  - 有序结局（如 mRS 评分）：不调整时用 Mann-Whitney；要调整协变量或报一个共同 OR 时用比例优势模型（有序 logistic 回归：R `MASS::polr()` / `ordinal::clm()`，Python `statsmodels.miscmodels.ordinal_model.OrderedModel(..., distr="logit")`，它默认是 probit），并检查比例优势假设。
  - 二分类：率差（RD）、相对危险度（RR）、比值比（OR）+ 95% CI，写明 CI 算法（如 Newcombe、Miettinen-Nurminen）；RCT 的二分类结局要同时给绝对效应（RD）和相对效应（RR 或 OR）。
- **多组**：先做整体检验，还是只比较预先指定的几对；事后检验方法（Tukey / Games-Howell / Dunn / Nemenyi，见 yaml `multiple_groups`）；多重比较校正（见 yaml `correction`）；分组有序时用趋势检验（见 yaml `ordered_groups_binary_outcome`）。
- **配对**：配对单位怎么定义；配对不完整时怎么处理（只用完整的对，或改用混合模型，写理由）。
- **结局层级**：一个主要结局；次要结局的校正策略；没写进 SAP 的比较只能标为探索性。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| Table 1（含 SMD） | `tableone::CreateTableOne(vars, strata = "grp", data = d)` 后 `print(tab, smd = TRUE, test = FALSE, nonnormal = c(...))`；或 `gtsummary::tbl_summary(by = grp)` 后接 `add_difference(test = everything() ~ "smd")` | `tableone.TableOne(df, columns=[...], categorical=[...], nonnormal=[...], groupby="grp", smd=True, pval=False)` |
| 两组均数差 + CI | `t.test(y ~ grp, data = d)`（默认即 Welch） | `scipy.stats.ttest_ind(a, b, equal_var=False)`，结果对象的 `.confidence_interval()` |
| Hedges g + CI | `effectsize::hedges_g(y ~ grp, data = d)` | `statsmodels.stats.meta_analysis.effectsize_smd(...)`（返回校正后的 g 及其方差，可算 CI）；`pingouin.compute_effsize(x, y, eftype="hedges")` 只给点估计 |
| 非正态位置差 + CI | `wilcox.test(y ~ grp, data = d, conf.int = TRUE)`（Hodges-Lehmann 估计） | `scipy.stats.mannwhitneyu` 只给 p；位置差或中位数差的 CI 用 `scipy.stats.bootstrap` |
| 二分类 RD / RR / OR + CI | `epiR::epi.2by2(tab, method = "cohort.count")`；RD 的 CI 也可用 `DescTools::BinomDiffCI(x1, n1, x2, n2, method = "mn")` | `statsmodels.stats.contingency_tables.Table2x2(tab)` 的 `riskratio_confint()`、`oddsratio_confint()`；`statsmodels.stats.proportion.confint_proportions_2indep(..., compare="diff")` |
| 多组事后比较 | `TukeyHSD()`；`rstatix::games_howell_test()`；`rstatix::dunn_test(p.adjust.method = "holm")`；Friedman 之后 `PMCMRplus::frdAllPairsNemenyiTest()`；基于模型的对比 `emmeans::emmeans()` + `contrast(method = "pairwise", adjust = "holm")` | `statsmodels.stats.multicomp.pairwise_tukeyhsd(y, g, use_var="unequal")`（即 Games-Howell）；`scikit_posthocs.posthoc_dunn(df, val_col=..., group_col=..., p_adjust="holm")`；`scikit_posthocs.posthoc_nemenyi_friedman()` |
| p 值校正 | `p.adjust(p, method = "holm")` | `statsmodels.stats.multitest.multipletests(p, method="holm")` |
| 配对 | `t.test(x, y, paired = TRUE)`；`wilcox.test(x, y, paired = TRUE, conf.int = TRUE)`；`mcnemar.test()`；配对率差的 CI：`exact2x2::mcnemarExactDP()` | `scipy.stats.ttest_rel`；`scipy.stats.wilcoxon`；`statsmodels.stats.contingency_tables.mcnemar(tab, exact=True)` |

两种语言默认值不同：R 的 `t.test` 默认 Welch，`scipy.stats.ttest_ind` 默认 `equal_var=True`（Student t），Python 要显式写 `equal_var=False`；计划里写明用 Welch（本卡默认）。

## 4. 常见的坑

- RCT 基线表放 p 值，或写"基线 p>0.05，两组可比"；更糟的是按基线 p 值决定调整谁（de Boer 2015）。
- 观察性研究用"p>0.05"说明两组相似：样本大时很小的差异也显著，样本小时很大的差异也不显著；应看 SMD。
- 只报 p 值不报效应量和 CI；把"差异无统计学意义"写成"两组没有差异"（Greenland 2016）。
- 连续变量的描述方式看着顺眼就换；用均值±SEM 描述数据分布（SEM 反映均值估计的精度，不是个体之间的离散程度）。
- 结局常见时把 OR 当 RR 解读（OR 比 RR 离 1 更远）。
- 先做 Shapiro-Wilk / Levene，再按结果在 Student t、Welch、Mann-Whitney 之间选：选择本身依赖数据，最终检验的假阳性率不再是名义水平（Zimmerman 2004）；默认 Welch，按秩分析的理由写在计划里。
- 多组时不校正就做所有两两 t 检验；或整体检验不显著，仍挑出"显著"的两两比较来报告。
- 配对数据按独立样本分析（或反过来）；只用完整配对却不报告丢了多少对。
- 百分比分母不清（含不含缺失者）；Table 1 不报缺失。
- 同一患者多条记录当独立样本（见 `clustered-and-repeated-data.md`）。

## 5. 结果必须报告

- Table 1：每组 n；连续变量均值±SD 或中位数(IQR)（注明是哪种）；分类变量 n(%)；每个变量的缺失人数；RCT 不放 p 值，观察性研究或倾向性评分后放 SMD。
- 每个比较：各组的描述统计量；效应量（均数差、位置差、RD、RR、OR 或 Hedges g）及 95% CI；所用检验的名称；精确 p 值（p<0.001 时写 p<0.001）；实际进入分析的人数。
- 二分类结局同时给绝对效应和相对效应。
- 多组：整体检验结果；事后比较的方法与校正后的 p（或同时置信区间）。
- 配对：配对数、差值的均值或中位数及其 95% CI。

## 6. 对应报告规范

- RCT：`consort-2025` 的 25（每组基线特征表）、21a（组间比较的统计方法）、26（每组结果、效应量及其精度，二分类结局同时给绝对与相对效应）。
- 观察性研究：`strobe` 的 14a（参与者特征）、14b（每个变量的缺失人数）、16a（未调整与调整后的估计及其 95% CI）；用电子病历、医保等常规收集的数据时加 `record`。

## 参考

- de Boer MR, Waterlander WE, Kuijper LDJ, Steenhuis IHM, Twisk JWR. Testing for baseline differences in randomized controlled trials: an unhealthy research behavior that is hard to eradicate. *Int J Behav Nutr Phys Act*. 2015;12:4. doi:10.1186/s12966-015-0162-z
- Austin PC. Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples. *Stat Med*. 2009;28(25):3083-3107. doi:10.1002/sim.3697
- Hayes-Larson E, Kezios KL, Mooney SJ, Lovasi G. Who is in this study, anyway? Guidelines for a useful Table 1. *J Clin Epidemiol*. 2019;114:125-132. doi:10.1016/j.jclinepi.2019.06.011
- Zimmerman DW. A note on preliminary tests of equality of variances. *Br J Math Stat Psychol*. 2004;57(Pt 1):173-181. doi:10.1348/000711004849222
- Rochon J, Gondan M, Kieser M. To test or not to test: preliminary assessment of normality when comparing two independent samples. *BMC Med Res Methodol*. 2012;12:81. doi:10.1186/1471-2288-12-81
- Greenland S, Senn SJ, Rothman KJ, et al. Statistical tests, P values, confidence intervals, and power: a guide to misinterpretations. *Eur J Epidemiol*. 2016;31(4):337-350. doi:10.1007/s10654-016-0149-3
