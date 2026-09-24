# 生存分析 — 方法要点卡

> 适用：结局是"从某个起点到某事件发生的时间"，且有删失（随访结束或失访时事件尚未发生）的数据：总生存、无复发生存、结石复发时间、移植物失功时间等。　不适用：固定时间点的二分类结局且没有删失（见 `baseline-and-group-comparison.md`、`regression-and-prediction-models.md`）；同一患者可以多次发生的复发事件（需复发事件模型，另议）；建立预后预测模型时，除本卡外还要遵守 `regression-and-prediction-models.md`（其中有固定时间点 t 的校准与 DCA 做法，生存模型不能套用二分类结局的校准和 DCA）。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**分组的生存曲线或 HR（那是结果）：
- 时间零点（time zero）：从诊断、手术还是随机化开始算；数据里有没有这个日期；分组/暴露在时间零点是否已经确定——要到随访中才知道的（如"术后是否接受辅助治疗"），有不朽时间偏倚的风险（见第 2 节）。
- 日期质量：格式是否统一、有无缺失、逻辑错误（事件日期早于手术日期、随访日期晚于数据截止日）、是否只精确到月或年。
- 事件编码：是 0/1 还是多类（如 1 = 目标事件、2 = 竞争事件、0 = 删失）；死因能不能拿到（判断有没有竞争风险）。
- 事件总数（不按组拆分）和各组人数；删失的比例和原因（失访，还是到研究截止日仍无事件）。
- 随访时间：中位随访（用反向 KM 算，见第 2 节）、最长随访；失访是否集中在某个时期或某个中心。
- 同一患者多条记录（多次复发、双侧器官）→ 见 `clustered-and-repeated-data.md`。
- 随访中会变化的变量（治疗开始或更换、复查指标）——决定要不要用时间依赖协变量。

## 2. 计划里必须预先写明

- **结局定义**：什么算事件、什么算删失（死于其他原因是删失还是竞争事件）、时间零点、随访截止日。
- **描述**：Kaplan-Meier（KM）曲线 + 风险人数表（number at risk）；关键时间点的生存率及 95% CI；中位生存时间及 95% CI（未达到时写"未达到"）。
- **组间比较**：log-rank 检验（分层随机的试验用分层 log-rank）；效应量用 Cox 模型的风险比（HR）及 95% CI。
- **Cox 模型**：协变量怎么选（解释性研究按 DAG，预测模型按 `regression-and-prediction-models.md`）；能放多少协变量由事件数决定，不由总人数决定。
- **比例风险（PH）假设**：用 Schoenfeld 残差检验（R 的 `cox.zph`），并结合残差随时间变化的图判断（Grambsch 1994）。不满足时的预案：
  - 不满足的是调整变量 → 按它分层（分层 Cox）；
  - 不满足的是主要暴露 → 加暴露与时间的交互项（HR 随时间变化，分时段报告），或改报限制平均生存时间（RMST，restricted mean survival time）之差，截止时间 τ 预先定；加速失效时间（AFT）模型见 yaml `survival_extended`。
- **竞争风险**：存在会阻止目标事件发生的其他事件（如死于其他原因）时，用累积发生率函数（CIF，cumulative incidence function）描述，不用 1−KM；组间比较用 Gray 检验。回归模型按问题选：病因问题用病因别风险模型（cause-specific hazard，把竞争事件当删失的 Cox）；估计个体的绝对风险（预后）用 Fine-Gray 亚分布风险模型（Austin 2016）。两类模型回答的问题不同，必要时两者都报并分别解释。
- **不朽时间偏倚（immortal time bias）**：暴露要到时间零点之后才确定时，不能按最终的暴露状态从零点开始比较——暴露组在"确定暴露之前"那段时间不可能发生事件，会让暴露虚假地显得有益（Suissa 2008）。处理：把暴露作为时间依赖协变量（start–stop 计数过程格式），或做 landmark 分析（预先定 landmark 时间点，只纳入该时点仍存活且未发生事件的人，按该时点的暴露状态分组，从该时点重新计时）。
- **随访时间**：中位随访用反向 KM 法（把删失当"事件"、把事件当删失）（Schemper 1996）。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| KM 曲线 + 风险人数表 | `survival::survfit(Surv(time, status) ~ grp, data = d)`，再 `ggsurvfit::ggsurvfit()` + `add_risktable()`；或 `survminer::ggsurvplot(fit, risk.table = TRUE)` | `lifelines.KaplanMeierFitter` + `lifelines.plotting.add_at_risk_counts()` |
| log-rank | `survival::survdiff(Surv(time, status) ~ grp, data = d)` | `lifelines.statistics.logrank_test()`；多组 `multivariate_logrank_test()` |
| Cox + PH 检验 | `survival::coxph()` 后 `cox.zph(fit)`，并 `plot(cox.zph(fit))` 看残差图 | `lifelines.CoxPHFitter` 后 `check_assumptions()`；或 `lifelines.statistics.proportional_hazard_test()` |
| PH 不满足时 | 分层 `coxph(Surv(time, status) ~ trt + strata(center))`；时间交互 `coxph(Surv(time, status) ~ trt + tt(trt), data = d, tt = function(x, t, ...) x * log(t))`（公式里必须写 `tt(trt)` 项，否则 `tt =` 参数被静默忽略、不报错）；RMST `survRM2::rmst2(time, status, arm, tau = <τ>)` | 分层 `CoxPHFitter().fit(..., strata=["center"])`；RMST `lifelines.utils.restricted_mean_survival_time(kmf, t=<τ>, return_variance=True)`（组间差值的 CI 需自己算或 bootstrap） |
| 竞争风险：CIF 与 Gray 检验 | `cmprsk::cuminc(ftime, fstatus, group)` | CIF：`lifelines.AalenJohansenFitter` 或 `sksurv.nonparametric.cumulative_incidence_competing_risks`；Gray 检验无公认成熟包 |
| Fine-Gray / 病因别 Cox | `cmprsk::crr(ftime, fstatus, cov1, failcode = 1, cencode = 0)`，或 `survival::finegray()` 生成数据后 `coxph()`；病因别：`coxph()`，竞争事件设为删失 | Fine-Gray 无公认成熟包，建议用 R；病因别 Cox 用 `CoxPHFitter`（竞争事件设为删失） |
| 时间依赖协变量 | `survival::tmerge()` 生成 start–stop 数据后 `coxph(Surv(tstart, tstop, event) ~ ...)` | `lifelines.utils.to_long_format()` + `add_covariate_to_timeline()`，再用 `lifelines.CoxTimeVaryingFitter` |
| 中位随访（反向 KM） | `survfit(Surv(time, status == 0) ~ 1, data = d)` | `KaplanMeierFitter().fit(T, event_observed=(E == 0))`（只有删失才算"事件"；不要写 `1 - E`：按 0/1/2 编码竞争风险时，竞争事件会变成 −1，lifelines 不报错但结果错） |

## 4. 常见的坑

- 有竞争风险时用 1−KM 估计发生率：结果偏高（Austin 2016）。
- 把 Fine-Gray 的亚分布 HR 当普通 HR 解读：它对应的是累积发生率，不是"仍在风险中的人"发生事件的速度；病因问题要用病因别 HR。
- 按"随访中才确定的状态"（是否接受了后续治疗、是否达到缓解）从时间零点分组，或排除早期死亡者——不朽时间偏倚（Suissa 2008）。
- 用全体患者（含已死亡者）观察时间的中位数当"中位随访"：会低估随访，应该用反向 KM（Schemper 1996）。
- 只报 log-rank 的 p，不报 HR 和 CI；KM 曲线不附风险人数表；曲线尾部人数很少时过度解读。
- 曲线明显交叉仍只报一个 HR；不做 PH 检验。
- 把 PH 检验 p>0.05 当作"PH 一定成立"：样本小时检验效能低，要结合残差图看。
- 用"随访期间是否发生事件"做 logistic 回归：忽略了删失和每个人随访长短不同。
- 事件很少却放很多协变量（事件数决定模型能有多复杂）。
- 删失可能与预后有关（病重者更容易失访）却不讨论。

## 5. 结果必须报告

- 每组人数、事件数、删失数；中位随访时间（反向 KM）及其 IQR 或范围。
- KM 曲线附风险人数表；关键时间点的生存率（95% CI）；中位生存时间（95% CI）或"未达到"。
- HR（95% CI）与 p 值；调整了哪些协变量；事件数与协变量个数（每个协变量平均对应多少事件）。
- PH 假设的检验方法、结果和处理方式。
- 竞争风险：CIF 曲线、Gray 检验、所用模型（病因别 / Fine-Gray）及各自的 HR。
- RMST（如用）：τ 的取值和理由、各组 RMST 及差值的 95% CI。
- landmark 分析（如用）：landmark 时间点及理由、纳入与排除的人数。

## 6. 对应报告规范

- 观察性队列：`strobe` 的 12d（失访怎么处理）、14c（随访时间汇总）、15（结局事件数）、16a（未调整与调整后的 HR 及 95% CI）。
- RCT：`consort-2025` 的 14（结局的分析指标，如 time to event）、26（每组结果、效应量及其精度）。
- 预后预测模型：`tripod-ai` 的 20a（参与者流程与随访时间）、20b（事件数、随访时间、缺失）等，其余见 `regression-and-prediction-models.md`。

## 参考

- Grambsch PM, Therneau TM. Proportional hazards tests and diagnostics based on weighted residuals. *Biometrika*. 1994;81(3):515-526. doi:10.1093/biomet/81.3.515
- Austin PC, Lee DS, Fine JP. Introduction to the analysis of survival data in the presence of competing risks. *Circulation*. 2016;133(6):601-609. doi:10.1161/CIRCULATIONAHA.115.017719
- Suissa S. Immortal time bias in pharmaco-epidemiology. *Am J Epidemiol*. 2008;167(4):492-499. doi:10.1093/aje/kwm324
- Schemper M, Smith TL. A note on quantifying follow-up in studies of failure time. *Control Clin Trials*. 1996;17(4):343-346. doi:10.1016/0197-2456(96)00075-x
