# 诊断准确性与 AI 模型评价 — 方法要点卡

> 适用：诊断试验；影像/病理/内镜/手术视频 AI 的分类或检测评价；AI 与医生对比；AI 辅助读片研究。　不适用：以风险概率为主要产出的预测模型开发（看 `regression-and-prediction-models.md`）；分割精度与标注一致性（看 `agreement-and-reliability.md`）；LLM/VLM 问答评测（看 `llm-vlm-evaluation.md`）。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**模型在测试集上的任何表现：
- 患者数与病灶/图像/视频数；每名患者有几条记录（1 条、2–5 条、>5 条各多少人）。
- 参考标准（金标准）阳性数、阴性数和患病率——整体、各中心、各数据集分别算。阳性很少时灵敏度的 CI 会很宽。
- **这里允许看什么、不允许看什么**（与 `data-analysis-planning` 的"计划前不做变量 × 结局交叉表"不矛盾）：诊断准确性研究要回答的是"指标检查（模型/医生读片）× 参考标准"的关系，所以只数参考标准本身——整体患病率、各中心/各数据集/各预定亚组里各有多少阳性和阴性——属于数据结构，用来估算 CI 能有多宽，允许；但不比较各水平之间患病率的高低、不做检验，更不能把指标检查结果、模型输出或候选预测变量与参考标准交叉（那就是在看结果）。研究其实是在开发风险预测模型、亚组变量又是候选预测变量时，按 `regression-and-prediction-models.md` 的规则，只看结局总数，不按预测变量拆分。
- 参考标准的来源（病理/随访/专家共识各占多少）；缺失或"无法判定"的例数。
- 数据来源：各中心、设备/扫描仪、时间段的例数；外部测试集是否来自不同中心或不同时间。
- 预先写进方案的亚组（性别、年龄段、病变大小/分期、中心）各有多少阳性例、阴性例（只数人数，见上一条），够不够算出有意义的 CI。
- 读片者研究：读者人数与年资；每位读者读多少病例；是否每位读者读全部病例（全交叉设计）。
- 模型输出形式：连续概率、等级评分还是只有阳/阴性（决定能否做 ROC、校准和 DCA）。
- 检测/定位任务：每个病灶的标注框或轮廓是否齐全，一张图有几个病灶。

## 2. 计划里必须预先写明

- **分析单位**：按患者、按病灶还是按图像；患者级"阳性"的规则（任一病灶阳性 / 多数票）。
- **主要指标与 CI 方法**：灵敏度、特异度用 Wilson 或 Clopper-Pearson（精确法）；AUC 用 DeLong 或 bootstrap（B ≥ 2000，固定并报告种子，见 yaml `resampling`）。
- **阈值**：在开发/调参集上确定并写死（数值 + 确定准则，如约登指数、固定灵敏度 90%），测试集只用这个阈值。在测试集上另找"最佳阈值"只能作探索性结果（STARD 12a）。
- **PPV/NPV**：写明用哪个患病率。人为富集阳性的病例–对照式样本，要按目标人群患病率换算，不能直接报样本里的 PPV/NPV。
- **聚类**：同一患者多个病灶/多张图像时，AUC 用按患者重抽样的聚类 bootstrap 或 Obuchowski 聚类 AUC 方法，或先按患者汇总；配对比较灵敏度/特异度时，普通 McNemar 检验假设每名患者只贡献一对结果，多病灶时要改用聚类校正的 McNemar（Obuchowski 1998；Durkalski 2003）或聚类 bootstrap（细节见 `clustered-and-repeated-data.md`）。
- **数据划分按患者 ID**：同一患者的全部图像/帧只进一个集合（yaml `deep_learning_training.data_split_rules`；用 `patient_level_split.py` 划分并做泄漏检查）。
- **模型比较**：同一批病例上两个模型（不是模型对医生组）的 AUC 用配对 DeLong；两个分类器在各自预定阈值下的灵敏度（只在有病者中）和特异度（只在无病者中）分别用 McNemar 配对比较（多病灶时用上一条的聚类校正版）。
- **概率输出**：校准（平滑校准曲线、calibration-in-the-large 与校准斜率、Brier 分数；ECE 只作补充）和决策曲线分析（DCA，decision curve analysis；阈值概率范围预先写明）；细节见 `regression-and-prediction-models.md`。
- **读片者研究**（多读者多病例，MRMC）：全交叉设计、读者 ≥ 5 名（本插件采用的经验下限，不是规范的硬性数字；读者越少，结论越难推广，具体人数按 MRMC 样本量计算定）；分析用 Obuchowski-Rockette（OR）或 Dorfman-Berbaum-Metz（DBM）法，读者和病例都作随机效应，结论才能推广到"其他医生"。AI 辅助 vs 不辅助：同一批病例、阅片顺序随机、两次阅片之间设洗脱期。洗脱期多长没有统一标准（已发表的读片研究约 2–6 周），预先写明时长和理由；本插件的下限是 ≥ 2 周（yaml `model_comparison.human_vs_ai`），病例少、特征鲜明、容易被记住时要更长。另一种设计是顺序阅片：同一次阅片中先独立读并记录结果，再看 AI 输出后决定是否修改，不需要洗脱期；它回答的是"看到 AI 后会不会改判"，只在 AI 的预期用法就是"先自己读、再参考 AI"时合适——选哪种设计按 AI 的预期用法预先写明。读者对参考标准设盲。
- **AI 单独 vs 一组医生**（"AI 是否达到医生水平"）：AI 是一个固定的"读者"，医生是从医生群体里抽出的样本，要按读者和病例都随机的 MRMC 方法比较 AI 与医生组的平均表现（如 RJafroc 的 `StSignificanceTestingCadVsRad()`，默认方法 1T-RRRC；iMRMC 也可处理非全交叉设计）。不要拿 AI 和每位医生分别做 DeLong、再数"赢了几位"，也不要把医生的平均 AUC 当成一个没有抽样误差的固定值来比——都会把读者当固定效应，CI 过窄。医生只有 1–2 名时，只能描述性地和这几位比较，结论不推广到"医生"。
- **检测任务**：写明"命中"的判定规则（如预测框与标注框 IoU ≥ 0.5，或中心点落在病灶内）；报告指标（固定假阳性数下的灵敏度、FROC）。
- **亚组与公平性**：预先列出亚组和每个亚组要报的指标，做交互检验；未预先列出的一律标"探索性"。
- **样本量**：按预期灵敏度/特异度、可接受的 CI 宽度和患病率计算（Buderer 1996：先算有病、无病各需多少人，再换算总人数）；比较 AUC 按预期差值算功效；MRMC 按读者数算病例数——需要读者间、病例间方差等参数，来自预实验数据或已发表的同类研究（`RJafroc::SsSampleSizeKGivenJ()` 可输入预实验数据集或这些方差参数），没有预实验数据时可用 `MRMCsamplesize`（其中 `sampleSize_Standalone()` 用于单独评价 AI）；写明参数来源。
- **不确定结果与缺失**：无法判读的指标结果、缺失的参考标准怎么处理（STARD 15、16）。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| 灵敏度/特异度/PPV/NPV + CI | `epiR::epi.tests(tab, method = "wilson")`；`binom::binom.confint(x, n, methods = "wilson")`（`"exact"` = Clopper-Pearson） | `statsmodels.stats.proportion.proportion_confint(k, n, method="wilson")`（`"beta"` = Clopper-Pearson） |
| ROC、AUC 及 CI | `pROC::roc()` + `pROC::ci.auc(r, method = "delong")` | `sklearn.metrics.roc_auc_score`；CI 用按患者重抽样的 bootstrap（Python 无公认的 DeLong 实现） |
| 两个相关 AUC 比较 | `pROC::roc.test(r1, r2, method = "delong", paired = TRUE)` | 无公认成熟包，建议用 R；或配对 bootstrap 求 AUC 差值的 CI |
| 两分类器配对比较 | `exact2x2::mcnemar.exact(tab)`；`mcnemar.test(tab)`。多病灶（聚类）：`clust.bin.pair::clust.bin.pair(ak, bk, ck, dk, method = "obuchowski")`（或 `"durkalski"`；每名患者一行 2×2 计数，可用 `paired.to.contingency()` 整理） | `statsmodels.stats.contingency_tables.mcnemar(tab, exact=True)`；多病灶时无公认成熟包，用按患者重抽样的聚类 bootstrap 求差值的 CI |
| 校准 | `CalibrationCurves::val.prob.ci.2(p, y)`（calibration-in-the-large、斜率、Brier、平滑校准曲线）；`rms::val.prob(p, y)` 的 "Intercept" 不是 calibration-in-the-large（见 `regression-and-prediction-models.md`） | `sklearn.calibration.calibration_curve`（只能分箱）；`sklearn.metrics.brier_score_loss`；calibration-in-the-large 与斜率用 `statsmodels` 分两个模型算（写法见 `regression-and-prediction-models.md`） |
| DCA | `dcurves::dca(y ~ p, data, thresholds = )` | `dcurves.dca(data, outcome=, modelnames=)` |
| MRMC 读片者研究 | `MRMCaov::mrmc(empirical_auc(truth, rating), test, reader, case, data)`；`RJafroc::StSignificanceTesting(ds, FOM = "Wilcoxon", method = "OR")` | 无公认成熟包，建议用 R |
| AI 单独 vs 医生组 | `RJafroc::StSignificanceTestingCadVsRad(ds, FOM = "Wilcoxon")`（AI 作固定读者，医生和病例随机；数据集里第一个读者须是 AI）；`iMRMC::doIMRMC()`（可处理非全交叉设计） | 无公认成熟包，建议用 R |
| 检测任务（FROC） | `RJafroc::StSignificanceTesting(ds, FOM = "wAFROC")` | 无公认成熟包，建议用 R |
| 按患者划分 | 用插件脚本 `patient_level_split.py`（Python，命令行调用） | `patient_level_split.py`；`sklearn.model_selection.StratifiedGroupKFold` |
| 样本量 | `presize::prec_sens(sens, prev = , conf.width = )`、`prec_spec()`、`prec_auc()`（`conf.width` 是 CI 的**全宽**，默认按 Wilson 法）；`pROC::power.roc.test()`；MRMC：`RJafroc::SsSampleSizeKGivenJ()`（需预实验数据或方差参数）、`MRMCsamplesize::sampleSize_MRMC()` / `sampleSize_Standalone()` | `statsmodels.stats.proportion.samplesize_confint_proportion(proportion, half_length)`：第二个参数是 CI 的**半宽**（全宽的一半），且只用 Wald 法，灵敏度/特异度接近 0.9–1 时不准；建议用 R，或在 Python 里用 `proportion_confint(k, n, method="wilson")` 从小到大试 n，取 CI 全宽达标的最小 n。得到的是有病或无病人数，再按患病率换算 |

聚类 bootstrap 没有通用包，要现写：以患者为单位有放回抽样，每次带上该患者的全部病灶/图像，重算指标，B ≥ 2000，取百分位 CI。Obuchowski 聚类 AUC 本卡没有核实到成熟的 R/Python 实现，一般就用这种聚类 bootstrap 代替。

## 4. 常见的坑

- 在测试集上找约登最优阈值，再用同一测试集报灵敏度/特异度：结果偏乐观，样本越小越严重（Leeflang 2008）。
- 把病灶/图像/帧当独立样本：n 虚高、CI 过窄；同一患者的图像同时进了训练集和测试集（数据泄漏）。
- 只报准确率：患病率低时准确率高没有意义。至少报灵敏度、特异度和混淆矩阵。
- 在富集阳性的样本里直接报 PPV/NPV，当成临床上的阳性/阴性预测值。
- 同一批病例上比较两个模型，却用了独立样本的检验（应配对：DeLong / McNemar）。
- 只报 AUC 不报校准：AUC 高的模型，给出的概率也可能整体偏高或偏低。
- 读片者研究只报读者平均值、把读者当固定效应，结论推广不到其他医生；AI 辅助阅片没有洗脱期、顺序不随机。
- "AI vs 医生"时把 AI 和每位医生分别做 DeLong，或只和 2 名医生比较就下"AI 达到/超过医生水平"的结论。
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

- 指标检查是 AI 时，以 STARD-AI（Sounderajah 2025，在 STARD 2015 基础上新增或修改 18 条）为主：仓库还没有 STARD-AI 的本地清单，也不在规范索引里，要对照官方全文人工逐条核对，并同时满足下面 STARD 2015 的条目。
- `stard`（STARD 2015，本地清单 `stard-2015.yaml`）：重点 12a（阈值是预先定的还是探索的）、15–16（不确定结果与缺失）、18（样本量）、19（流程图）、23–24（2×2 表与 CI）。
- `claim`（CLAIM 2024，`claim-2024.yaml`）：影像 AI；重点 19–20（数据划分及划分层级）、21（测试集样本量）、28–29（指标与不确定性）、38–39（诊断性能及 CI、失败分析）。
- `tripod-ai`（TRIPOD+AI 2024）：模型输出概率或属风险预测时；重点 12e、14（公平性）、15（阈值如何确定）、23a（含亚组的 CI）。
- `decide-ai`（DECIDE-AI 2022）：AI 辅助决策的早期临床评价。

## 参考

- DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. *Biometrics*. 1988;44(3):837-845. doi:10.2307/2531595
- Obuchowski NA. Nonparametric analysis of clustered ROC curve data. *Biometrics*. 1997;53(2):567-578. doi:10.2307/2533958
- Leeflang MM, Moons KG, Reitsma JB, Zwinderman AH. Bias in sensitivity and specificity caused by data-driven selection of optimal cutoff values: mechanisms, magnitude, and solutions. *Clin Chem*. 2008;54(4):729-737. doi:10.1373/clinchem.2007.096032
- Buderer NM. Statistical methodology: I. Incorporating the prevalence of disease into the sample size calculation for sensitivity and specificity. *Acad Emerg Med*. 1996;3(9):895-900. doi:10.1111/j.1553-2712.1996.tb03538.x
- Sounderajah V, Guni A, Liu X, et al. The STARD-AI reporting guideline for diagnostic accuracy studies using artificial intelligence. *Nat Med*. 2025;31(10):3283-3289. doi:10.1038/s41591-025-03953-8
- Obuchowski NA. On the comparison of correlated proportions for clustered data. *Stat Med*. 1998;17(13):1495-1507. doi:10.1002/(SICI)1097-0258(19980715)17:13<1495::AID-SIM863>3.0.CO;2-I
- Durkalski VL, Palesch YY, Lipsitz SR, Rust PF. Analysis of clustered matched-pair data. *Stat Med*. 2003;22(15):2417-2428. doi:10.1002/sim.1438
- Obuchowski NA, Bullen J. Multireader diagnostic accuracy imaging studies: fundamentals of design and analysis. *Radiology*. 2022;303(1):26-34. doi:10.1148/radiol.211593
