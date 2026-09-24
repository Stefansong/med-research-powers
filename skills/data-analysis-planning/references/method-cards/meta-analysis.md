# Meta 分析 — 方法要点卡

> 适用：系统综述中对多项研究的定量合并——干预效果、暴露与结局的关联、诊断准确性（诊断试验 Meta）。　不适用：网状 Meta（间接比较，需专门方法，报告看 `prisma-nma`）；个体患者数据（IPD）Meta 的一阶段模型；不做定量合并的范围综述（`prisma-scr`）。

## 1. 计划前先看数据的什么

这里的"数据"是从纳入研究里提取出来的研究级数据。只看结构和质量，**不看**各研究效应值的方向和大小，不先画森林图：
- 每个结局纳入几项研究、各是什么设计（RCT / 队列 / 病例对照 / 横断面）——设计不同的研究原则上分开合并。
- 结果以什么形式报告：事件数/总数、均数/SD、中位数/IQR、HR 及 CI、调整后还是未调整的效应；量表和单位是否一致。
- 零事件研究有几项，是否有两组都为零的研究。
- 多臂试验、同一队列的多篇报告（重复发表）、同一研究在多个时间点或多个结局上的结果——会造成重复计算或相关的效应值。
- 提取的完整度：缺 SD、缺 CI、只有图表没有数字的研究有多少，需要换算或向作者索取。
- 诊断试验 Meta：能否还原每项研究的 2×2 表（TP、FP、FN、TN）；各研究用的阈值是否相同。
- 偏倚风险评估结果的分布（高风险研究有几项），以便预先安排敏感性分析。

## 2. 计划里必须预先写明

以下内容写进研究方案并在 PROSPERO 等平台注册，**在提取结果之前**定好：
- **效应量**：二分类结局用 RR / OR / RD（病例对照研究只能用 OR；RD 表达绝对差别）；连续结局量表相同用 MD，不同用 SMD（Hedges' g）；生存结局用 HR（合并 log HR 及其 SE）。中位数/IQR 换算成均数/SD 的方法预先写明。
- **模型**：按研究间是否可能存在真实差异预先选定，默认随机效应；不能看了异质性检验结果再改。τ²（研究间方差）用 REML 估计（RevMan 现默认 REML，Cochrane Handbook v6.5 §10.10.4.4），不用 DerSimonian-Laird 默认值；合并效应的 CI 用 Hartung-Knapp-Sidik-Jonkman（HKSJ）法（IntHout 2014；Handbook 建议在 τ² > 0 且研究数 > 2 时使用）。研究只有 2–4 项时说明随机效应估计不稳定。
- **异质性**：报告 τ²、I²（及其 CI）、Q 检验和 95% 预测区间（研究数约 ≥ 5 项且漏斗图无明显不对称时报告，Handbook §10.10.4.3；IntHout 2016）。
- **小研究效应/发表偏倚**：研究数 ≥ 10 项才做漏斗图检验（Sterne 2011）；连续结局用 Egger 检验，OR 用 Harbord 或 Peters 检验，诊断试验用 Deeks 检验；剪补法只作敏感性分析。
- **亚组与 meta 回归**：只做方案里预先列出的少数几个变量，写明理由和预期方向；用亚组间差异检验（交互），不比较各亚组 P 值；研究数少时不做 meta 回归，结果一律视为跨研究的观察性发现。
- **敏感性分析**：留一法；剔除高偏倚风险研究；换 τ² 估计方法或固定效应模型；稀有事件换合并方法（Mantel-Haenszel / Peto）和连续性校正方式。
- **特殊数据**：零事件的连续性校正规则；多臂试验共享对照组的拆分；同一研究多个相关效应值时按什么规则只取一个，或改用多水平模型。
- **诊断试验 Meta**：用双变量随机效应模型（Reitsma 2005；无协变量时与 HSROC 等价）同时合并灵敏度和特异度；报告 SROC 曲线及 95% 置信区域和预测区域；各研究阈值不同时以 SROC/HSROC 为主。**首选按二项分布拟合的广义线性混合模型（binomial GLMM）**：直接用每项研究的 TP、FN、FP、TN 计数，有研究报告灵敏度或特异度 100%（某格为 0）时不需要连续性校正（Chu 2006）。`mada::reitsma()` 在 logit 尺度上用正态近似，只要任一研究有 0 格，默认给**所有研究的所有格子**都加 0.5（`correction = 0.5, correction.control = "all"`），会把合并的灵敏度、特异度往 0.5 方向拉；AI 研究里 100% 很常见，偏倚更明显——只在没有 0 格时使用，或作敏感性分析。研究少、数据稀疏、双变量模型不收敛时，退为灵敏度、特异度各自的单变量随机效应 logistic 模型（Takwoingi 2017）。
- **偏倚风险**：按设计选工具——RCT 用 RoB 2，非随机干预研究用 ROBINS-I，诊断试验用 QUADAS-2，预测模型用 PROBAST（回归或 AI/机器学习模型都可用更新版 PROBAST+AI，Moons 2025）；比较两种及以上检查准确性的研究（如 AI vs 医生、AI 辅助 vs 不辅助），在 QUADAS-2 之外再用 QUADAS-C 评价"比较"本身的偏倚（Yang 2021）；两名评价者独立评价后核对。
- **证据确定性**：每个主要结局分别做 GRADE 评级（偏倚风险、不一致性、间接性、不精确性、发表偏倚五个降级因素），做结果汇总表（Summary of Findings）。
- **数据提取**：两人独立提取，分歧的解决方式。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| 效应量计算 | `metafor::escalc(measure = "RR", ai = , bi = , ci = , di = )`（`"OR"`、`"SMD"` 等） | `statsmodels.stats.meta_analysis.effectsize_2proportions()`、`effectsize_smd()` |
| 随机效应合并（REML + HKSJ） | `metafor::rma(yi, vi, method = "REML", test = "knha")`；`meta::metagen(TE, seTE, sm = "RR", method.tau = "REML", method.random.ci = "HK", prediction = TRUE)` | `statsmodels.stats.meta_analysis.combine_effects(eff, var, method_re="pm", use_t=True)`：τ² 只有 Paule-Mandel/DL，没有 REML，结果表中 "random effect wls" 行为 HKSJ；功能不全，建议用 R |
| 二分类原始计数 | `meta::metabin(event.e, n.e, event.c, n.c, sm = "RR", method.tau = "REML", method.random.ci = "HK")` | 同上，建议用 R |
| 预测区间 | `predict(res)`（metafor，看 `pi.lb`/`pi.ub`）；meta 用 `prediction = TRUE` | 无公认成熟包，建议用 R |
| 漏斗图与检验 | `metafor::funnel()`、`metafor::regtest()`；`meta::metabias(m, method.bias = "Egger", k.min = 10)` | 无公认成熟包，建议用 R |
| 留一法 | `metafor::leave1out()`；`meta::metainf()` | 无公认成熟包，建议用 R |
| 亚组与 meta 回归 | `metafor::rma(yi, vi, mods = ~ x, test = "knha")`；`meta::metagen(..., subgroup = )`、`meta::metareg()` | 无公认成熟包，建议用 R |
| 诊断试验 Meta | 二项 GLMM（首选）：数据整理成长格式，每项研究两行——有病者行 `true = TP, n = TP + FN, sens = 1, spec = 0`，无病者行 `true = TN, n = TN + FP, sens = 0, spec = 1`；`lme4::glmer(cbind(true, n - true) ~ 0 + sens + spec + (0 + sens + spec \| study), family = binomial, data = long)`，`plogis(fixef(fit))` 即合并的灵敏度、特异度（Stata 用户可用 `metadta`）。无 0 格时也可用 `mada::reitsma(d)`（列名 TP、FN、FP、TN；`plot()` 画 SROC）。各研究报告多个阈值时看 `diagmeta` | 无公认成熟包，建议用 R |
| 偏倚风险图 | `robvis::rob_traffic_light(d, tool = "ROB2")`、`robvis::rob_summary()`（CRAN 版支持 ROB2、ROBINS-I、QUADAS-2；PROBAST 需另行制表） | 无，建议用 R |
| GRADE 结果汇总表 | 无 R 包，用 GRADEpro GDT 网页工具 | 同左 |

`meta::metabias()` 默认研究数 < 10 时不做检验，且对 OR 默认用 Harbord 检验、对诊断比值比用 Deeks 检验——不要为了出结果把 `k.min` 调小。mada 没有 Deeks 检验：先用 `meta::metabin(TP, TP + FN, FP, FP + TN, sm = "DOR")` 建一个诊断比值比对象，再对它做 `metabias()`。

## 4. 常见的坑

- 先看森林图，再决定固定还是随机效应、做哪些亚组、剔除哪项"离群"研究。
- 用 I² 大小或异质性检验 P 值决定模型；把 I² 当成异质性的绝对大小（I² 受研究精度影响，τ² 和预测区间才反映效应在研究间差多少）。
- DerSimonian-Laird + 正态分布 CI：研究少时 CI 过窄，假阳性多。
- 不到 10 项研究做 Egger 检验；把漏斗图不对称全归因于发表偏倚（也可能来自异质性或真实的小研究效应）。
- 同一队列的多篇报告重复纳入；多臂试验的共享对照组被计算两次。
- 中位数/IQR 当均数/SD 直接用；调整和未调整的效应混在一起合并。
- RCT 与观察性研究混在一起合并。
- 诊断试验 Meta 分别合并灵敏度和特异度（忽略两者的相关和阈值效应），或只用单个指标的 I² 描述异质性（反映不了阈值效应和两指标的相关）。
- GRADE 只给整篇综述评一次，而不是每个结局分别评。

## 5. 结果必须报告

- PRISMA 流程图；纳入研究特征表；每项研究的偏倚风险（红绿灯图）和汇总图。
- 每个结局：合并效应及 95% CI（写明模型、τ² 估计方法、CI 方法）、τ²、I²（及 CI）、Q 检验 P 值、95% 预测区间；森林图（含各研究权重）。
- 亚组与 meta 回归结果（亚组间差异检验），标明预先指定还是探索性。
- 敏感性分析结果（留一法、剔除高风险研究等）与主要结果是否一致。
- 漏斗图及检验结果；研究数不足 10 项时写明未做及原因。
- 诊断试验 Meta：合并灵敏度、特异度及 CI，SROC 曲线（置信区域与预测区域），研究间方差与相关系数。
- 每个主要结局的 GRADE 结果汇总表，逐项写明降级理由。
- 注册号、与方案的偏离及理由；软件与包版本。

## 6. 对应报告规范

- `prisma-2020`（PRISMA 2020，本地清单 `prisma-2020.yaml`）：重点 13a–13f（合成方法、异质性、敏感性分析）、14（报告偏倚评估）、15（证据确定性评估）、19–22（各研究结果、合成结果、报告偏倚、证据确定性）。
- 以下在仓库索引中有条目、无本地清单，需按官方清单人工核对：`prisma-dta`（诊断试验）、`moose`（观察性研究 Meta，与 PRISMA 2020 合用）、`prisma-s`（检索报告）、`prisma-p`（方案）、`tripod-srma`（预测模型的系统综述）、`prisma-nma`（网状 Meta）。
- 偏倚风险工具：`rob-2`、`robins-i`、`quadas-2`、`probast`（索引条目已注明 AI 模型可用 PROBAST+AI）；QUADAS-C 仓库索引无条目，按原文人工核对；证据确定性：`grade`；综述方法学质量自查：`amstar-2`。

## 参考

- IntHout J, Ioannidis JP, Borm GF. The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method. *BMC Med Res Methodol*. 2014;14:25. doi:10.1186/1471-2288-14-25
- IntHout J, Ioannidis JP, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. *BMJ Open*. 2016;6(7):e010247. doi:10.1136/bmjopen-2015-010247
- Sterne JA, Sutton AJ, Ioannidis JP, et al. Recommendations for examining and interpreting funnel plot asymmetry in meta-analyses of randomised controlled trials. *BMJ*. 2011;343:d4002. doi:10.1136/bmj.d4002
- Reitsma JB, Glas AS, Rutjes AW, et al. Bivariate analysis of sensitivity and specificity produces informative summary measures in diagnostic reviews. *J Clin Epidemiol*. 2005;58(10):982-990. doi:10.1016/j.jclinepi.2005.02.022
- Chu H, Cole SR. Bivariate meta-analysis of sensitivity and specificity with sparse data: a generalized linear mixed model approach. *J Clin Epidemiol*. 2006;59(12):1331-1332. doi:10.1016/j.jclinepi.2006.06.011
- Takwoingi Y, Guo B, Riley RD, Deeks JJ. Performance of methods for meta-analysis of diagnostic test accuracy with few studies or sparse data. *Stat Methods Med Res*. 2017;26(4):1896-1911. doi:10.1177/0962280215592269
- Moons KGM, Damen JAA, Kaul T, et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. *BMJ*. 2025;388:e082505. doi:10.1136/bmj-2024-082505
- Yang B, Mallett S, Takwoingi Y, et al. QUADAS-C: a tool for assessing risk of bias in comparative diagnostic accuracy studies. *Ann Intern Med*. 2021;174(11):1592-1599. doi:10.7326/M21-2234
