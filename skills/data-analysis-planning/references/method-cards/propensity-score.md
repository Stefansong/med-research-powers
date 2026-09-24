# 倾向性评分（匹配与加权） — 方法要点卡

> 适用：观察性数据中估计某个二分类治疗或暴露（如手术方式 A vs B）的平均效应，且主要混杂因素已经测量。　不适用：RCT（随机化已经平衡了混杂）；三类及以上治疗或连续剂量（需广义倾向性评分，另议）；明显存在强的未测混杂又无法做敏感性分析；只想描述两组差异而不估计效应。混杂变量的选择原则同 `regression-and-prediction-models.md` 的"解释（病因）模型"部分。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**结局。计划阶段**不拟合**倾向性评分模型：PS 建模、匹配/加权和平衡检查全程不需要结局，放在 SAP 批准之后、读入结局之前完成（这时结局列先不读入；平衡定稿后才估计效应）。计划前只看下面这些：
- 治疗组与对照组的人数和比例：只用来判断所选方法**做不做得成**（如估 ATT 做 1:k 匹配时，对照够不够多、预计有多少治疗者匹配不上），**不**用来决定用匹配还是加权——那由下一节的目标效应决定。
- 每个候选混杂变量在什么时候测量：必须能分清"治疗决定之前"和"之后"。
- 混杂变量的缺失比例与形式：倾向性评分模型不能直接处理缺失，先按 `missing-data.md` 定处理方式。
- 分类变量有没有很少见的水平、某一组内某变量是否全为同一个值（会让倾向性评分接近 0 或 1、模型不收敛）。
- 结局事件总数（不按治疗组拆分），用来判断匹配/加权后还能不能估计效应。
- 同一患者多次治疗、多中心 → 见 `clustered-and-repeated-data.md`。

## 2. 计划里必须预先写明

- **目标效应（estimand）**：全人群平均效应（ATE）、治疗者平均效应（ATT）还是重叠人群效应（ATO）。它决定方法：最近邻匹配通常估 ATT，逆概率加权（IPTW）估 ATE，重叠权重估 ATO。
- **倾向性评分（PS）模型放哪些变量**：只放治疗之前测量的混杂因素和结局的危险因素，按 DAG 或临床知识预先列出；不放治疗之后才发生的变量（中介、并发症、住院天数等），也不放只影响治疗、不影响结局的变量。
- **PS 模型形式**：logistic 回归，连续变量可用样条、可加交互项；PS 模型好不好看协变量平衡，不看它的 C 统计量（Austin 2009）。
- **匹配方案**：1:1（或 1:k）最近邻、不放回，卡钳（caliper）= 0.2 × logit(PS) 的标准差（Austin 2011）；写明未匹配者怎么报告，以及目标人群因此发生的变化。
- **加权方案**：IPTW（是否用稳定化权重；极端权重的截断阈值预先定，常按权重分布的第 1 和第 99 百分位）（Austin & Stuart 2015），或重叠权重（自动压低 PS 接近 0 或 1 的人的权重）。截断是用一点偏倚换更小的方差，截断后的结果不再严格对应原来的目标效应：写明这一点，并报告不截断的结果作对照。
- **重叠（共同支持）检查**：画两组的 PS 分布；预先定重叠差时怎么办（限制人群，并说明新的目标人群是谁）。
- **平衡诊断**：匹配/加权后每个协变量的 SMD（|SMD| < 0.1 视为平衡，这是经验值，预后越重要的变量越要求平衡好）；连续变量的方差比（应接近 1）；Love 图。不用 p 值判断平衡（Austin 2009）。不平衡时改 PS 模型（加样条、交互项）→ 重新匹配/加权 → 再检查，全程不看结局。
- **效应估计与方差**：匹配后用考虑配对的方差（按配对 ID 的簇稳健标准误），匹配后的 Cox 模型同样按配对 ID 用稳健方差；加权后的 GLM 用稳健（三明治）方差或 bootstrap（Austin & Stuart 2015）。**加权后的 Cox 模型用 bootstrap**，每次重抽样都重新估 PS 和权重：模拟研究里只有 bootstrap 的标准误和 CI 覆盖率接近正确，稳健（三明治）方差和普通方差都有偏（Austin 2016）。可以在匹配/加权后的结局模型中再调整主要协变量。
- **混杂变量有缺失时**：用多重插补的话，在每份插补数据里分别估 PS、做匹配/加权和平衡检查、估计效应，再用 Rubin 规则合并各份的效应；插补模型要包含结局；不要先把各份的 PS 平均成一个再分析（Leyrat 2019；细节见 `missing-data.md`）。
- **敏感性分析**：E-value，点估计和 CI 中靠近 1 的那一端都要算（VanderWeele 2017）；换一种 PS 方法（匹配 ↔ 加权）；换卡钳或截断阈值；可加一个双重稳健估计——增广逆概率加权（AIPW）或目标最大似然估计（TMLE），它同时用 PS 模型和结局模型，两个模型有一个设定对，估计就不偏；写明用哪一种、两个模型各放哪些变量。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| 估 PS 并匹配 | `MatchIt::matchit(trt ~ x1 + x2, data = d, method = "nearest", distance = "glm", link = "linear.logit", caliper = 0.2)`（`std.caliper = TRUE` 是默认值，即以 logit PS 的标准差为单位）；取匹配后数据用 `match_data()` | 无公认成熟包，建议用 R；替代做法：`statsmodels` logit 估 PS，自写最近邻卡钳匹配（自己处理不放回和卡钳单位） |
| 加权 | `WeightIt::weightit(trt ~ x1 + x2, data = d, method = "glm", estimand = "ATE")`；重叠权重用 `estimand = "ATO"` | `statsmodels` 估 PS 后手算：ATE 权重为治疗组 1/PS、对照组 1/(1−PS)；重叠权重为治疗组 1−PS、对照组 PS |
| 平衡与重叠诊断 | `cobalt::bal.tab(m_out, stats = c("m", "v"), thresholds = c(m = 0.1))`；`love.plot()`；`bal.plot(m_out, var.name = "distance")` | 无成熟包：手算（加权）SMD 与方差比，用 matplotlib 画 PS 分布 |
| 匹配后效应与标准误 | `marginaleffects::avg_comparisons(fit, variables = "trt", vcov = ~subclass, wts = "weights", newdata = md)`（估 ATT 时 `newdata` 只取治疗组） | `statsmodels` GLM 的 `.fit(cov_type="cluster", cov_kwds={"groups": pair_id})` |
| 加权后效应与稳健标准误 | `WeightIt::glm_weightit()`（能把权重估计的不确定性算进去）；或 `survey::svyglm()`；`sandwich::vcovCL()` | `statsmodels.api.GLM(y, X, family=..., var_weights=w).fit(cov_type="HC0")`；不要用 `freq_weights`（会把权重当成真实人数，标准误偏小） |
| 匹配后的 Cox | `survival::coxph(Surv(t, e) ~ trt, data = md, weights = weights, robust = TRUE, cluster = subclass)` | `lifelines.CoxPHFitter().fit(df, "t", "e", weights_col="w", robust=True, cluster_col="pair")` |
| 加权后的 Cox（bootstrap 方差） | `WeightIt::coxph_weightit(Surv(t, e) ~ trt, data = d, weightit = W, vcov = "BS", R = 2000)`（`W` 是 `weightit()` 的结果；`"BS"` 在每个 bootstrap 样本里重新估权重，也可用 `"FWB"`） | 无现成包：现写 bootstrap——按患者有放回抽样，每次重新估 PS 和权重，再用 `lifelines.CoxPHFitter().fit(..., weights_col="w", robust=True)` 拟合，B ≥ 2000，取 log HR 的百分位 CI |
| 双重稳健（敏感性分析） | `AIPW` 包；`tmle::tmle()` | 无公认成熟包，建议用 R |
| E-value | `EValue::evalues.RR(est, lo, hi)`；`evalues.HR()`、`evalues.OR()` 用 `rare =` 说明结局是否少见（<15%） | 无成熟包，公式简单可手算：RR>1 时 E = RR + √(RR×(RR−1))，RR<1 先取倒数；结局常见时 OR、HR 要先换算成 RR |

## 4. 常见的坑

- 用 t 检验或卡方检验的 p 值判断匹配后是否平衡：匹配后样本变小，p 值自然变大（Austin 2009）。
- PS 模型里放了治疗之后的变量（术后并发症、住院天数），或只影响治疗的变量。
- 用 PS 模型的 C 统计量评价 PS 模型：它反映不了有没有漏掉重要混杂、模型设定对不对（Austin 2009）；PS 越能"预测"治疗，两组的重叠往往越差。
- 匹配后仍按独立样本算标准误；加权后用普通回归的标准误（把权重当真实人数）——CI 过窄；加权 Cox 只用稳健方差、不做 bootstrap（Austin 2016）。
- 卡钳单位用错：0.2 是 logit(PS) 标准差的倍数，不是 PS 本身相差 0.2（Austin 2011）。
- 大量治疗者没匹配上却不报告，仍按全部治疗者来解读结论。
- 不检查 IPTW 的极端权重（少数人权重几十上百），估计很不稳定；要报告权重分布。
- 以为 PS 能处理未测混杂，不做 E-value 等敏感性分析（VanderWeele 2017）。
- 看着结局反复换匹配方案或 PS 模型——这就是 p-hacking；方案要在看结局之前定稿。
- 匹配后再做一张"基线 p 值表"来证明两组可比。

## 5. 结果必须报告

- PS 模型包含的变量及理由；目标效应（ATE / ATT / ATO）。
- 匹配：方法、比例、卡钳（写明单位）、是否放回；匹配前后每组人数和未匹配人数。
- 加权：权重类型、是否稳定化或截断、权重分布（最小、最大、均值）、有效样本量。
- 两组的 PS 分布图（重叠情况）。
- 匹配/加权前后每个协变量的 SMD（连续变量加方差比），用表或 Love 图。
- 匹配/加权后的效应（RD、RR、OR 或 HR）及 95% CI 和方差估计方法；同时给未调整估计。
- E-value（点估计和 CI 限）；其他 PS 方法的结果是否一致。

## 6. 对应报告规范

- `strobe` 的 12a（统计方法，含怎样控制混杂）、12e（敏感性分析）、16a（未调整与调整估计及 95% CI）；用电子病历、医保等常规收集的数据时加 `record`。
- 仓库索引里没有专门的倾向性评分报告规范；平衡表、PS 分布图、E-value 等按本卡第 5 节自查。

## 参考

- Austin PC. Optimal caliper widths for propensity-score matching when estimating differences in means and differences in proportions in observational studies. *Pharm Stat*. 2011;10(2):150-161. doi:10.1002/pst.433
- Austin PC. Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples. *Stat Med*. 2009;28(25):3083-3107. doi:10.1002/sim.3697
- Austin PC, Stuart EA. Moving towards best practice when using inverse probability of treatment weighting (IPTW) using the propensity score to estimate causal treatment effects in observational studies. *Stat Med*. 2015;34(28):3661-3679. doi:10.1002/sim.6607
- VanderWeele TJ, Ding P. Sensitivity analysis in observational research: introducing the E-value. *Ann Intern Med*. 2017;167(4):268-274. doi:10.7326/M16-2607
- Austin PC. Variance estimation when using inverse probability of treatment weighting (IPTW) with survival analysis. *Stat Med*. 2016;35(30):5642-5655. doi:10.1002/sim.7084
- Leyrat C, Seaman SR, White IR, et al. Propensity score analysis with partially observed covariates: how should multiple imputation be used? *Stat Methods Med Res*. 2019;28(1):3-19. doi:10.1177/0962280217713032
