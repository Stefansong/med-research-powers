# 诊断准确性与 AI 模型评价 — 方法要点卡

> 适用：诊断试验；影像/病理/内镜/手术视频 AI 的分类或检测评价；AI 与医生对比；AI 辅助读片研究。　不适用：以风险概率为主要产出的预测模型开发（看 `regression-and-prediction-models.md`）；分割精度与标注一致性（看 `agreement-and-reliability.md`）；LLM/VLM 问答评测（看 `llm-vlm-evaluation.md`）。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**模型在测试集上的任何表现：
- 患者数与病灶/图像/视频数；每名患者有几条记录（1 条、2–5 条、>5 条各多少人）。
- 参考标准（金标准）阳性数、阴性数和患病率——整体、各中心、各数据集分别算。阳性很少时灵敏度的 CI 会很宽。
- 参考标准的来源（病理/随访/专家共识各占多少）；缺失或"无法判定"的例数。
- 数据来源：各中心、设备/扫描仪、时间段的例数；外部测试集是否来自不同中心或不同时间。
- 预先想做的亚组（性别、年龄段、病变大小/分期、中心）各有多少阳性例，够不够算出有意义的 CI。
- 读片者研究：读者人数与年资；每位读者读多少病例；是否每位读者读全部病例（全交叉设计）。
- 模型输出形式：连续概率、等级评分还是只有阳/阴性（决定能否做 ROC、校准和 DCA）。
- 检测/定位任务：每个病灶的标注框或轮廓是否齐全，一张图有几个病灶。

## 2. 计划里必须预先写明

- **分析单位**：按患者、按病灶还是按图像；患者级"阳性"的规则（任一病灶阳性 / 多数票）。
- **主要指标与 CI 方法**：灵敏度、特异度用 Wilson 或 Clopper-Pearson（精确法）；AUC 用 DeLong 或 bootstrap（B ≥ 2000，固定并报告种子，见 yaml `resampling`）。
- **阈值**：在开发/调参集上确定并写死（数值 + 确定准则，如约登指数、固定灵敏度 90%），测试集只用这个阈值。在测试集上另找"最佳阈值"只能作探索性结果（STARD 12a）。
- **PPV/NPV**：写明用哪个患病率。人为富集阳性的病例–对照式样本，要按目标人群患病率换算，不能直接报样本里的 PPV/NPV。
- **聚类**：同一患者多个病灶/多张图像时，用按患者重抽样的聚类 bootstrap、Obuchowski 聚类 AUC 方法，或先按患者汇总（细节见 `clustered-and-repeated-data.md`）。
- **数据划分按患者 ID**：同一患者的全部图像/帧只进一个集合（yaml `deep_learning_training.data_split_rules`；用 `patient_level_split.py` 划分并做泄漏检查）。
- **模型比较**：同一批病例上两个 AUC 用配对 DeLong；两个分类器在各自预定阈值下的灵敏度（只在有病者中）和特异度（只在无病者中）分别用 McNemar 配对比较。
- **概率输出**：校准（校准曲线、校准截距与斜率、Brier 分数）和决策曲线分析（DCA，decision curve analysis；阈值概率范围预先写明）；细节见 `regression-and-prediction-models.md`。
- **读片者研究**（多读者多病例，MRMC）：全交叉设计、读者 ≥ 5 名；分析用 Obuchowski-Rockette（OR）或 Dorfman-Berbaum-Metz（DBM）法，读者和病例都作随机效应，结论才能推广到"其他医生"。AI 辅助 vs 不辅助：同一批病例、阅片顺序随机、两次阅片之间设洗脱期（时长预先写明；本插件默认 ≥ 2 周，见 yaml `model_comparison.human_vs_ai`）；读者对参考标准设盲。
- **检测任务**：写明"命中"的判定规则（如预测框与标注框 IoU ≥ 0.5，或中心点落在病灶内）；报告指标（固定假阳性数下的灵敏度、FROC）。
- **亚组与公平性**：预先列出亚组和每个亚组要报的指标，做交互检验；未预先列出的一律标"探索性"。
- **样本量**：按预期灵敏度/特异度、可接受的 CI 宽度和患病率计算（先算有病、无病各需多少人，再换算总人数）；比较 AUC 按预期差值算功效；MRMC 按读者数算病例数。
- **不确定结果与缺失**：无法判读的指标结果、缺失的参考标准怎么处理（STARD 15、16）。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| 灵敏度/特异度/PPV/NPV + CI | `epiR::epi.tests(tab, method = "wilson")`；`binom::binom.confint(x, n, methods = "wilson")`（`"exact"` = Clopper-Pearson） | `statsmodels.stats.proportion.proportion_confint(k, n, method="wilson")`（`"beta"` = Clopper-Pearson） |
| ROC、AUC 及 CI | `pROC::roc()` + `pROC::ci.auc(r, method = "delong")` | `sklearn.metrics.roc_auc_score`；CI 用按患者重抽样的 bootstrap（Python 无公认的 DeLong 实现） |
| 两个相关 AUC 比较 | `pROC::roc.test(r1, r2, method = "delong", paired = TRUE)` | 无公认成熟包，建议用 R；或配对 bootstrap 求 AUC 差值的 CI |
| 两分类器配对比较 | `exact2x2::mcnemar.exact(tab)`；`mcnemar.test(tab)` | `statsmodels.stats.contingency_tables.mcnemar(tab, exact=True)` |
| 校准 | `rms::val.prob(p, y)`（校准截距、斜率、Brier） | `sklearn.calibration.calibration_curve`（只能分箱）；`sklearn.metrics.brier_score_loss`；校准截距、斜率用 `statsmodels` 手算（见 `regression-and-prediction-models.md`） |
| DCA | `dcurves::dca(y ~ p, data, thresholds = )` | `dcurves.dca(data, outcome=, modelnames=)` |
| MRMC 读片者研究 | `MRMCaov::mrmc(empirical_auc(truth, rating), test, reader, case, data)`；`RJafroc::StSignificanceTesting(ds, FOM = "Wilcoxon", method = "OR")` | 无公认成熟包，建议用 R |
| 检测任务（FROC） | `RJafroc::StSignificanceTesting(ds, FOM = "wAFROC")` | 无公认成熟包，建议用 R |
| 按患者划分 | 用插件脚本 `patient_level_split.py`（Python，命令行调用） | `patient_level_split.py`；`sklearn.model_selection.StratifiedGroupKFold` |
| 样本量 | `presize::prec_sens(sens, prev = , conf.width = )`、`prec_spec()`、`prec_auc()`；`pROC::power.roc.test()`；MRMC：`RJafroc::SsSampleSizeKGivenJ()` | `statsmodels.stats.proportion.samplesize_confint_proportion()`（得到的是有病或无病人数，再按患病率换算） |

聚类 bootstrap 没有通用包，要现写：以患者为单位有放回抽样，每次带上该患者的全部病灶/图像，重算指标，B ≥ 2000，取百分位 CI。

## 4. 常见的坑

- 在测试集上找约登最优阈值，再用同一测试集报灵敏度/特异度：结果偏乐观，样本越小越严重（Leeflang 2008）。
- 把病灶/图像/帧当独立样本：n 虚高、CI 过窄；同一患者的图像同时进了训练集和测试集（数据泄漏）。
- 只报准确率：患病率低时准确率高没有意义。至少报灵敏度、特异度和混淆矩阵。
- 在富集阳性的样本里直接报 PPV/NPV，当成临床上的阳性/阴性预测值。
- 同一批病例上比较两个模型，却用了独立样本的检验（应配对：DeLong / McNemar）。
- 只报 AUC 不报校准：AUC 高的模型，给出的概率也可能整体偏高或偏低。
- 读片者研究只报读者平均值、把读者当固定效应，结论推广不到其他医生；AI 辅助阅片没有洗脱期、顺序不随机。
- 参考标准由看过模型结果的人判定；只有部分患者做了参考标准（部分核实偏倚）。
- 亚组很多却没预先指定，只挑"显著"的报。

## 5. 结果必须报告

- 流程图：患者数 → 病灶/图像数，每一步排除的原因和人数；各集合的患者数、阳性数、患病率。
- 按预定阈值的 2×2 表；灵敏度、特异度、PPV、NPV 及 95% CI，注明 CI 方法和所用患病率。
- AUC 及 95% CI（方法；是否按患者聚类）；模型比较的差值、95% CI 和 P 值。
- 阈值的数值与来源（哪个数据集、什么准则）；探索性阈值的结果单独标出。
- 概率输出：校准曲线、校准截距/斜率、Brier 分数；DCA 曲线及阈值概率范围。
- MRMC：每位读者和汇总的指标，AI 辅助前后差值及 95% CI，分析方法（OR/DBM）与软件版本。
- 预先指定亚组的指标及 CI、交互检验；失败病例分析（错在哪类病例）。
- 不确定结果与缺失的数量及处理；软件与包版本、随机种子。

## 6. 对应报告规范

- `stard`（STARD 2015，本地清单 `stard-2015.yaml`）：重点 12a（阈值是预先定的还是探索的）、15–16（不确定结果与缺失）、18（样本量）、19（流程图）、23–24（2×2 表与 CI）。
- `claim`（CLAIM 2024，`claim-2024.yaml`）：影像 AI；重点 19–20（数据划分及划分层级）、21（测试集样本量）、28–29（指标与不确定性）、38–39（诊断性能及 CI、失败分析）。
- `tripod-ai`（TRIPOD+AI 2024）：模型输出概率或属风险预测时；重点 12e、14（公平性）、15（阈值如何确定）、23a（含亚组的 CI）。
- `decide-ai`（DECIDE-AI 2022）：AI 辅助决策的早期临床评价。STARD-AI 暂无本地清单，需人工核对官方版本。

## 参考

- DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. *Biometrics*. 1988;44(3):837-845. doi:10.2307/2531595
- Obuchowski NA. Nonparametric analysis of clustered ROC curve data. *Biometrics*. 1997;53(2):567-578. doi:10.2307/2533958
- Leeflang MM, Moons KG, Reitsma JB, Zwinderman AH. Bias in sensitivity and specificity caused by data-driven selection of optimal cutoff values: mechanisms, magnitude, and solutions. *Clin Chem*. 2008;54(4):729-737. doi:10.1373/clinchem.2007.096032
- Obuchowski NA, Bullen J. Multireader diagnostic accuracy imaging studies: fundamentals of design and analysis. *Radiology*. 2022;303(1):26-34. doi:10.1148/radiol.211593
