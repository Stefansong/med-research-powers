# 回归分析与临床预测模型 — 方法要点卡

> 适用：多因素回归（线性 / logistic / Cox）的两种用途——① 解释（病因）：估计某个暴露对结局的调整后效应；② 预测：建立并验证为个体计算风险的临床预测模型（含列线图）。　不适用：深度学习模型的训练细节（见 `ai-ml-sap-extension.md`）；诊断试验准确性评价（见 `diagnostic-accuracy-and-ai-evaluation.md`）；用倾向性评分估计治疗效应（见 `propensity-score.md`）；生存模型的比例风险、竞争风险等细节（见 `survival-analysis.md`）。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**任何变量与结局的关系（不做单因素筛选，不找切点）：
- 结局事件数：二分类结局看较少那一类的人数，生存结局看事件数——事件数（不是总人数）决定模型能放多少参数。
- 候选变量的"参数个数"：k 个水平的分类变量占 k−1 个参数，样条按自由度计；样本量计算用的是参数数，不是变量数。
- 连续变量的取值范围与分布（极端值、截断值、单位），用于预先定样条节点或变换。
- 每个候选变量和结局的缺失比例与形式（见 `missing-data.md`）。
- 数据来源结构：几个中心、时间跨度多长——决定能否做按中心或按时间的内部-外部验证（internal-external validation）；同一患者多条记录见 `clustered-and-repeated-data.md`。
- 预测变量之间是否有重复信息（同一指标两种单位；派生变量与原始变量同时在，如 BMI 与身高、体重）——只看预测变量之间，不看与结局。
- 预测模型：每个候选预测变量在"做出预测的时间点"是否已经能拿到（术后才有的指标不能用于术前预测）。

## 2. 计划里必须预先写明

第一句写清目的：**解释还是预测**。两者选变量和评价的方式完全不同，不能混用。

**解释（病因）模型**
- 暴露、结局、调整变量：先画 DAG（有向无环图，directed acyclic graph），按 DAG 选调整集；DAG 画不全时按 VanderWeele 2019 的原则：调整暴露的原因或结局的原因（或两者都是的变量），排除工具变量（只影响暴露、不直接影响结局），纳入未测共同原因的替代指标；不调整中介变量、对撞变量（collider）和暴露之后才发生的变量。
- 不按单因素 p 值或逐步回归挑调整变量：这样选出的是"与结局相关"的变量，不是混杂。
- 报告对象是暴露的效应（β / OR / HR 及 95% CI），同时给未调整估计；调整变量自己的系数不作解读。
- 连续暴露和连续混杂的函数形式（线性或样条）预先定；缺失与未测混杂的敏感性分析见 `missing-data.md` 和 `propensity-score.md`（E-value）。

**临床预测模型**
- 样本量：按 Riley 方法用 `pmsampsize` 计算。输入：候选参数总数；预期 R²（Cox-Snell 或 Nagelkerke R²，取既往模型乐观校正后的值，宁可保守）；二分类结局再加结局发生率，预期 R² 也可由既往模型的 C 统计量换算（`cstatistic` 只对二分类结局有效）；生存结局再加总体事件率、预测时间点和预计平均随访时间（`rate`、`timepoint`、`meanfup`，时间单位一致），`pmsampsize` 此时不能用 C 统计量换算，要用既往研究报告的 R²，没报告时按 Riley 2020 的说明从其他统计量推算。二分类或生存结局要同时满足：预期收缩 ≤10%（收缩因子 ≥0.9）、表观与校正后 Nagelkerke R² 之差 ≤0.05、平均风险的估计误差在 ±0.05 以内（Riley 2020）。
- 候选预测变量按文献和临床知识预先列出。不用单因素筛选；不推荐逐步回归（系数有偏、预测变差）；确实要减少变量时用惩罚回归（LASSO、弹性网）（Efthimiou 2024）。**惩罚回归不能弥补样本量不足**：有效样本小时，惩罚参数本身估得很不准，越是需要收缩的时候越不可靠（Riley 2021；Van Calster 2020）。事件数达不到 `pmsampsize` 的要求时，先按临床知识预先减少候选参数（合并类别、删去次要变量），仍不够就把模型标为探索性，不要指望 LASSO 补救。
- 连续变量保持连续：非线性用限制性立方样条（RCS，restricted cubic spline），节点数（常用 3–5 个）和位置预先定；不按数据找"最佳切点"二分类（Efthimiou 2024）。
- 缺失：多重插补（见 `missing-data.md`），并写明插补与内部验证怎样嵌套（如每份插补数据内各做 bootstrap）。
- 内部验证：bootstrap 乐观校正，每个 bootstrap 样本里重做全部建模步骤（包括变量选择、惩罚参数选择）；不用一次性随机拆分（浪费数据、降低效能）（Efthimiou 2024）。写明 bootstrap 次数与随机种子。
- 性能指标：区分度——C 统计量（AUC）+ 95% CI；校准——calibration-in-the-large（平均预测风险与实际发生率是否一致）、校准斜率、平滑校准曲线（Van Calster 2019）；临床效用——决策曲线分析（DCA，decision curve analysis），阈值概率范围按临床理由预先定。ECE 等分箱指标只作补充。NRI、IDI 不是恰当的性能指标（校准差的模型也可能显得"更好"），期刊要求时只作补充，并与 DCA 净获益及校准、区分度的变化一起报告（Hilden 2014；Kerr 2014）。
- 生存结局的预后模型（Cox、列线图）：校准和 DCA 都在预先定的时间点 t（如 3 年）上做——t 时刻的预测风险 = 1 − 该时刻预测生存率，与考虑删失后的实际发生率（KM 或平滑方法）比较；不能把"随访中是否发生事件"当二分类结局套用上面的二分类校准和 DCA（McLernon 2023；Austin 2020）。有竞争风险时用累积发生率（见 `survival-analysis.md`）。
- 外部验证：验证数据的来源（其他中心或其他时间段）、样本量（`pmvalsampsize`）、表现不理想时的更新方法（重新校准截距或斜率）。
- 呈现：最终模型的完整公式（截距 + 全部系数，含样条项）；列线图（nomogram）只是把公式画成图的一种展示方式，不能替代验证。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| 画 DAG、找调整集 | `dagitty::adjustmentSets(dag, exposure = "X", outcome = "Y", type = "minimal")`（也可用 dagitty.net 网页） | 无公认成熟包，建议用 dagitty.net 网页或 R（pgmpy 有相关功能，但接口正在变动） |
| 解释性回归 | `glm(y ~ x + z, family = binomial, data = d)`；`survival::coxph()` | `statsmodels.formula.api.logit()` / `ols()`；`sklearn` 的 `LogisticRegression` 默认带 L2 惩罚，不要用它报告 OR |
| 预测模型样本量 | 二分类：`pmsampsize::pmsampsize(type = "b", cstatistic = <预期C>, parameters = <候选参数数>, prevalence = <发生率>)`；生存：`pmsampsize(type = "s", csrsquared = <预期 Cox-Snell R²>, parameters = , rate = <事件率>, timepoint = <预测时间点>, meanfup = <平均随访>)` | `pmsampsize`（Riley 团队出的 Python 版，需 Python ≥3.12）：`from pmsampsize.pmsampsize import pmsampsize` |
| 外部验证样本量 | `pmvalsampsize::pmvalsampsize(type = "b", ...)` | `pmvalsampsize`（目前只支持二分类结局） |
| 连续变量的样条 | `rms::lrm(y ~ rcs(age, 4) + ..., data = d, x = TRUE, y = TRUE)`；Cox 用 `rms::cph()` | `statsmodels` 公式里用 `cr(age, df=3, constraints="center")`（自然三次样条，与 RCS 同类，3 个自由度，参数数与 `rcs(age, 4)` 相同，但默认节点位置不同）。不能写成不带约束的 `cr(age, df=4)` 再配截距：样条各列加起来恒等于 1，与截距重复，模型照样"收敛"，但系数和标准误没有意义（标准误极大或为 NaN）；要么加 `constraints="center"`，要么公式里 `- 1` 去掉截距 |
| 惩罚回归 | `glmnet::cv.glmnet(x, y, family = "binomial", alpha = 1)` | 先标准化再惩罚：`make_pipeline(StandardScaler(), LogisticRegressionCV(l1_ratios=(1.0,), solver="saga", scoring="neg_log_loss", max_iter=5000))`。glmnet 默认把预测变量标准化（`standardize = TRUE`），sklearn 不会——不标准化时惩罚力度和入选变量随测量单位改变；`scoring` 不写时按准确率选惩罚参数。要每折重新标准化，用 `GridSearchCV` 包住整个 Pipeline。系数在标准化尺度上，报告原单位的模型要除以 `scaler.scale_` 换算（1.8 版起用 `l1_ratios`，`penalty` 参数已弃用） |
| bootstrap 内部验证 | `rms::validate(fit, method = "boot", B = <次数>)`；`rms::calibrate(fit, method = "boot", B = <次数>)`（默认 B=40 偏少；Cox 模型要给时间点 `u`，见下方生存模型行） | 无公认成熟包：用 `sklearn` / `statsmodels` 自写循环——每次重做全部建模步骤，在原数据上算性能，求平均乐观值 |
| C 统计量 + CI | `pROC::ci.auc(roc_obj, method = "delong")`；生存模型 `survival::concordance()` | `sklearn.metrics.roc_auc_score` + `scipy.stats.bootstrap` |
| 校准（二分类） | `CalibrationCurves::val.prob.ci.2(p, y)`（calibration-in-the-large、斜率、C 统计量及其 CI，平滑校准曲线）；手算：calibration-in-the-large = `glm(y ~ 1, offset = qlogis(p), family = binomial)` 的截距，斜率 = `glm(y ~ qlogis(p), family = binomial)` 的斜率。注意 `rms::val.prob(p, y)` 输出的 "Intercept" 来自截距和斜率同时估计的模型，不是 calibration-in-the-large（模型过拟合、斜率 <1 时两者不同） | `sklearn.calibration.calibration_curve` 只能分箱。calibration-in-the-large：`sm.GLM(y, np.ones(len(y)), family=sm.families.Binomial(), offset=logit(p)).fit()` 的截距；斜率：另拟合 `sm.GLM(y, sm.add_constant(logit(p)), family=sm.families.Binomial())` 取 logit(p) 的系数（`logit` 来自 `scipy.special`）。不要用第二个模型的截距当 calibration-in-the-large |
| DCA（二分类） | `dcurves::dca(y ~ p_model, data = d, thresholds = seq(<下限>, <上限>, by = 0.01))` | `dcurves.dca(data=df, outcome="y", modelnames=["p_model"], thresholds=...)` |
| 生存模型：t 时刻的校准 | `rms::calibrate(fit, u = <t>, method = "boot", B = <次数>)`（`fit` 用 `cph(..., x = TRUE, y = TRUE, surv = TRUE, time.inc = <t>)` 拟合）；外部验证：`riskRegression::Score(list(model = fit), formula = Surv(time, status) ~ 1, data = val, times = <t>, plots = "calibration")` 后 `plotCalibration()`（同时给 t 时刻的 AUC 和 Brier） | `lifelines.calibration.survival_probability_calibration(cph, df, t0=<t>)`（平滑校准曲线及 ICI、E50；`cph` 为 lifelines 的回归模型） |
| 生存模型：t 时刻的 DCA | `dcurves::dca(Surv(time, status) ~ risk_t, data = d, time = <t>, thresholds = )`，`risk_t` 为 t 时刻预测风险（1 − 预测生存率） | `dcurves.dca(data=df, outcome="status", modelnames=["risk_t"], time=<t>, time_to_outcome_col="time", thresholds=...)` |
| 列线图 | `rms::nomogram(fit)`（先 `dd <- datadist(d); options(datadist = "dd")`） | 无公认成熟包，建议用 R |

## 4. 常见的坑

- 解释与预测混用：拿预测模型"入选的变量"谈病因；或在病因研究里用 AUC 证明"暴露很重要"。
- 单因素 p<0.05（或 <0.1）的变量才进多因素：逐个检验忽略了变量之间的关系，会丢掉有用的信息（Efthimiou 2024）；解释模型里还会漏掉真正的混杂。
- 把逐步回归当作主要方法：系数估计有偏、预测表现变差（Efthimiou 2024），换一份样本选出的变量也常常不同。
- 把解释模型里每个调整变量都写成"独立危险因素"：调整集是为暴露选的，其他变量的系数没有同样的含义。
- 连续变量按中位数或 ROC"最佳切点"二分：丢信息、切点依赖样本、效应被夸大。
- 只报 AUC 不报校准；或只给一个校准检验的 p 值，不给校准斜率和校准曲线。
- 把 `rms::val.prob` 的 "Intercept"、或截距和斜率同时估计的模型里的截距，当作 calibration-in-the-large 报告。
- 为"类别不平衡"做过采样、欠采样或 SMOTE：预测概率被系统性抬高，校准变差，AUC 并不提高（van den Goorbergh 2022）；需要调灵敏度时改阈值即可。
- 生存模型把"随访期间是否发生事件"当二分类结局做校准或 DCA，忽略删失。
- 以为用了 LASSO 就不用管样本量。
- 样本不大还按 70/30 拆分做"内部验证"；bootstrap 时只对最终模型重抽样、不重做变量选择——乐观被低估。
- 把"每个变量 10 个事件"当作样本量够用的充分条件；应按 Riley 方法算。
- 以为画了列线图就等于"模型验证过了"。
- 校准斜率明显 <1（预测过于极端，提示过拟合）却不报告、不讨论。
- 试了多种算法，挑 AUC 最高的报告，而比较方法和选择标准没有预先写明。

## 5. 结果必须报告

- 解释模型：暴露的未调整与调整后效应及 95% CI；调整变量清单及选择依据（DAG 可放补充材料）；进入模型的人数与事件数；连续变量的函数形式。
- 预测模型：参与者流程；样本量计算（`pmsampsize` 的输入与结果）；每个分析的人数与事件数；完整模型（截距与全部系数，或可获取的代码/模型对象）。
- 性能：表观与乐观校正后的 C 统计量（95% CI）、校准斜率、calibration-in-the-large、校准曲线图、DCA 曲线及阈值范围；外部验证给同样的指标，并比较开发人群与验证人群的差异。
- 列线图（如有）附对应的完整公式。

## 6. 对应报告规范

- 预测模型开发或验证：`tripod-ai`（TRIPOD+AI 2024），重点 9a（候选预测变量怎么选）、10（样本量）、11（缺失）、12b（预测变量的函数形式）、12c（建模步骤与内部验证方法）、12e（性能指标）、21（每个分析的人数与事件数）、22（完整模型）、23a（性能及 CI）；期刊仍要求 2015 版时用 `tripod-2015`；多中心数据加 `tripod-cluster`（仓库索引有条目，无本地清单，需人工核对）；偏倚风险自查可用 `probast`（机器学习 / AI 模型用更新版 PROBAST+AI，Moons 2025）。
- 解释性回归（观察性研究）：`strobe` 的 12a（统计方法，含怎样控制混杂）、16a（未调整与调整估计，说明调整了哪些混杂及理由）、16b（连续变量分组时报告切点）。

## 参考

- Riley RD, Ensor J, Snell KIE, et al. Calculating the sample size required for developing a clinical prediction model. *BMJ*. 2020;368:m441. doi:10.1136/bmj.m441
- Efthimiou O, Seo M, Chalkou K, Debray T, Egger M, Salanti G. Developing clinical prediction models: a step-by-step guide. *BMJ*. 2024;386:e078276. doi:10.1136/bmj-2023-078276
- Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. *BMJ*. 2024;385:e078378. doi:10.1136/bmj-2023-078378
- Riley RD, Snell KIE, Martin GP, et al. Penalization and shrinkage methods produced unreliable clinical prediction models especially when sample size was small. *J Clin Epidemiol*. 2021;132:88-96. doi:10.1016/j.jclinepi.2020.12.005
- Van Calster B, van Smeden M, De Cock B, Steyerberg EW. Regression shrinkage methods for clinical prediction models do not guarantee improved performance: simulation study. *Stat Methods Med Res*. 2020;29(11):3166-3178. doi:10.1177/0962280220921415
- Van Calster B, McLernon DJ, van Smeden M, Wynants L, Steyerberg EW. Calibration: the Achilles heel of predictive analytics. *BMC Med*. 2019;17(1):230. doi:10.1186/s12916-019-1466-7
- McLernon DJ, Giardiello D, Van Calster B, et al. Assessing performance and clinical usefulness in prediction models with survival outcomes: practical guidance for Cox proportional hazards models. *Ann Intern Med*. 2023;176(1):105-114. doi:10.7326/M22-0844
- Austin PC, Harrell FE Jr, van Klaveren D. Graphical calibration curves and the integrated calibration index (ICI) for survival models. *Stat Med*. 2020;39(21):2714-2742. doi:10.1002/sim.8570
- Moons KGM, Damen JAA, Kaul T, et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. *BMJ*. 2025;388:e082505. doi:10.1136/bmj-2024-082505
- Hilden J, Gerds TA. A note on the evaluation of novel biomarkers: do not rely on integrated discrimination improvement and net reclassification index. *Stat Med*. 2014;33(19):3405-3414. doi:10.1002/sim.5804
- Kerr KF, Wang Z, Janes H, McClelland RL, Psaty BM, Pepe MS. Net reclassification indices for evaluating risk prediction instruments: a critical review. *Epidemiology*. 2014;25(1):114-121. doi:10.1097/EDE.0000000000000018
- van den Goorbergh R, van Smeden M, Timmerman D, Van Calster B. The harm of class imbalance corrections for risk prediction models: illustration and simulation using logistic regression. *J Am Med Inform Assoc*. 2022;29(9):1525-1534. doi:10.1093/jamia/ocac093
- VanderWeele TJ. Principles of confounder selection. *Eur J Epidemiol*. 2019;34(3):211-219. doi:10.1007/s10654-019-00494-6
