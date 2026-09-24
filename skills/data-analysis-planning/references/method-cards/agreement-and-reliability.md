# 一致性与信度分析 — 方法要点卡

> 适用：评分者间/评分者内一致性（影像分级、病理评分、手术技能评分、AI 训练数据标注）；两种测量方法的一致性（新方法 vs 参考方法、AI 测量 vs 人工测量）；分割标注一致性。　不适用：以参考标准判断"对不对"的诊断准确性（看 `diagnostic-accuracy-and-ai-evaluation.md`）；问卷量表的效度与结构分析（另查 COSMIN）。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**评分者之间一致不一致：
- 评分对象数（患者/图像/病灶/视频）、评分者人数、每位评分者评了多少对象；是否每个对象都由同一批评分者评分（全交叉），还是不同对象由不同评分者评分——决定用哪种 ICC、哪种 kappa（见第 2 节）。
- 评分类型：二分类、无序多分类、有序等级（几级）、连续测量（单位、取值范围、有无"<0.1"这类截断值）、分割掩膜（体素间距、2D 还是 3D）。
- 类别分布：把所有评分者的评分合在一起，看各类别各占多少——某一类别极少或极多时，kappa 会被压低（kappa 悖论）。**不**按评分者分别列出类别分布来互相比较：那是在看评分者之间有没有系统差异，属于一致性结果。
- 缺失评分：谁缺、缺多少、缺在哪些对象上——决定用什么方法（见第 2、3 节：irr 包的 kappa 和 ICC 函数会把有缺失的对象整行删掉，且不提示）。
- 评分者内一致性：同一评分者重复评了多少对象，两次间隔多久，顺序是否打乱。
- 同一患者有几个病灶/几张图像（决定 CI 要不要按患者聚类）。
- 分割：目标结构大小的分布（小病灶多时 Dice 不稳定）、空掩膜（图上没有目标）的数量、各图像体素间距是否一致。

## 2. 计划里必须预先写明

- **研究目的**：评分者间、评分者内还是方法间一致性；结论要推广到哪些评分者（这几位 / 同类医生）。
- **指标按数据类型和评分设计选**：
  - 2 名评分者 × 无序分类 → Cohen's kappa；2 名 × 有序分级 → 加权 kappa（线性或二次权重，预先选定）。
  - ≥ 3 名评分者 × 分类：每个对象都由同一批评分者评（全交叉）→ Light's kappa（两两 Cohen's kappa 的平均）或 Conger's kappa；不同对象由不同评分者评 → Fleiss' kappa（它原本就是为这种设计提出的）。
  - ≥ 3 名评分者 × 有序分级 → 加权的多评分者系数（如加权 Gwet AC2、加权 Conger kappa）或有序 Krippendorff's alpha。
  - 有缺失评分 → Krippendorff's alpha 或 irrCAC 包的系数（按实际有的评分计算，不删整行）；类别分布极不平衡时加报 Gwet's AC1 作对照。
  - 连续测量 → ICC + Bland-Altman。
  - 分割 → 一个重叠指标（Dice）加一个边界指标（HD95 或归一化表面 Dice，NSD，写明容差毫米数），每例分别算再汇总（Maier-Hein 2024）。IoU 可由 Dice 直接换算（IoU = Dice ÷ (2 − Dice)），不能当作第二个独立证据。
- **始终同时报原始一致率**：患病率极端时 kappa 可能很低而一致率很高（Feinstein & Cicchetti 1990）；二分类加报阳性一致率与阴性一致率。
- **ICC 选型**（Koo & Li 2016），三个选择都要写明：
  - 模型：单向随机（每个对象由不同评分者评）/ 双向随机（评分者是随机样本，结论推广到同类评分者）/ 双向混合（只针对本研究这几位评分者）；
  - 类型：绝对一致（评分者之间的系统差异也算误差，临床测量一般选这个）/ 一致性（只看排序是否一致）；
  - 单位：单个评分者（临床上由一个人测量时）/ k 个评分者的平均（只有实际使用的就是 k 人平均值时才选）。
  - 对照：Shrout-Fleiss 的 ICC(1,1) = 单向随机；ICC(2,1) = 双向随机·绝对一致·单个；ICC(3,1) = 双向混合·一致性·单个。pingouin 的 ICC(A,1)/ICC(C,1) 即绝对一致/一致性——双向随机与双向混合的计算公式相同，差别只在结论能否推广。
- **解释标准事先写明**：ICC 按 95% CI 判断，< 0.5 差、0.5–0.75 中等、0.75–0.9 良好、> 0.9 优秀（Koo & Li 2016）。
- **Bland-Altman**：分析前定好临床可接受的一致性界限（Δ）；检查比例误差（差值随均值变化，做差值对均值的回归）和差值离散度随测量值增大的情况（考虑对数变换或百分比差值）；给出偏倚和一致性界限的 95% CI；每人多次测量时用适用于重复测量/嵌套数据的方法。
- **分割指标规则**：两者都为空掩膜时怎么记；HD95 用毫米（按体素间距换算），不用像素；按病灶还是按病例汇总；小结构单独报告（Maier-Hein 2024）。软件默认值会悄悄决定空掩膜怎么算，要按这里的规则显式设置（见第 3 节 monai 的说明）。
- **标注研究设计**：评分者人数（≥ 2，需要多数票时 ≥ 3）与资质；独立评分，对彼此结果、临床信息、参考标准和模型输出设盲；有书面标注规范，用不在研究样本里的练习集做校准培训；分歧的裁决流程（上级专家裁决或共识讨论）及最终标签如何产生；评分者内重复评分的间隔与顺序随机。
- **聚类**：同一患者多个病灶时，CI 用按患者重抽样的 bootstrap（见 `clustered-and-repeated-data.md`）。
- **样本量**：按 kappa 或 ICC 的预期值和可接受的 CI 宽度计算。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| Cohen's kappa / 加权 kappa | `irr::kappa2(ratings, weight = "squared")`（`"equal"` = 线性权重；`"unweighted"` = 不加权） | `sklearn.metrics.cohen_kappa_score(y1, y2, weights="quadratic")`；要 CI 用 `statsmodels.stats.inter_rater.cohens_kappa(table, wt="quadratic")`（输入列联表） |
| Fleiss' kappa（不同对象由不同评分者评） | `irr::kappam.fleiss(ratings, detail = TRUE)` | `statsmodels.stats.inter_rater.fleiss_kappa(aggregate_raters(data)[0])` |
| ≥ 3 名评分者、全交叉 | `irr::kappam.light(ratings)`；`irrCAC::conger.kappa.raw(ratings)`（有序时加 `weights = "quadratic"` 等） | 无公认成熟包：Light's kappa 用 `sklearn.metrics.cohen_kappa_score` 两两计算后取平均 |
| 有序 / 有缺失 / 类别极不平衡 | `irr::kripp.alpha(t(ratings), method = "ordinal")`（输入是评分者 × 对象矩阵，缺失记 NA）；`irrCAC::gwet.ac1.raw(ratings)`（AC1；加 `weights = "quadratic"` 为 AC2）、`irrCAC::krippen.alpha.raw(ratings)`（缺失评分不删整行） | `krippendorff.alpha(reliability_data=矩阵, level_of_measurement="ordinal")`（评分者 × 对象，缺失记 `np.nan`） |
| ICC | `irr::icc(ratings, model = "twoway", type = "agreement", unit = "single")`；`psych::ICC(x)`（一次给出 6 种） | `pingouin.intraclass_corr(data, targets=, raters=, ratings=)`（0.6 版输出 ICC(1,1)、ICC(A,1)、ICC(C,1) 及 k 个平均的版本，含 95% CI） |
| Bland-Altman | `SimplyAgree::agreement_limit(x = "x", y = "y", data = d, data_type = "simple", prop_bias = TRUE)`；每人多次测量用 `data_type = "reps"`、嵌套数据用 `"nest"`，这两种都必须同时给受试者编号 `id = "id"`（否则无法按人处理重复测量） | `pingouin.plot_blandaltman(x, y, confidence=0.95)`；`statsmodels.graphics.agreement.mean_diff_plot(m1, m2)`（比例误差需现算） |
| 分割一致性 | 无常用 R 包，建议用 Python | `monai.metrics.compute_dice`、`compute_hausdorff_distance(..., percentile=95, spacing=)`、`compute_surface_dice(..., class_thresholds=[容差毫米数], spacing=)`（NSD）；`medpy.metric.binary.dc`、`hd95(result, reference, voxelspacing=)` |
| 样本量（按 CI 宽度） | `presize::prec_kappa(kappa, raters = , n_category = , props = , conf.width = )`；`presize::prec_icc(rho, k, conf.width = )` | 无公认成熟包，建议用 R |

irr 包的 `kappa2()`、`kappam.fleiss()`、`kappam.light()`、`icc()` 会先删掉任何有缺失评分的对象，而且不提示：有缺失时报告实际纳入的对象数，或换用上表能处理缺失的函数。monai 各函数的默认值不一样：`compute_dice`、`compute_iou` 默认 `include_background=True, ignore_empty=True`（真值为空掩膜的例子记为 NaN，不计入平均），`compute_hausdorff_distance`、`compute_surface_dice` 默认 `include_background=False`——按第 2 节的空掩膜规则显式写出这两个参数。

## 4. 常见的坑

- 用相关系数（Pearson r）或配对 t 检验代表一致性：两种方法可以高度相关却差得很远（Bland & Altman 1986）。
- 只报 kappa 不报原始一致率；类别极不平衡时 kappa 很低，就下结论说"一致性差"。
- 有序分级用了不加权 kappa；看了结果再挑线性还是二次权重。
- ICC 不写模型、类型、单位；用"k 人平均"的 ICC 夸大单人测量的可靠性；选"一致性"类型掩盖评分者之间的系统差异。可以并列列出 ICC(1,1)、ICC(A,1)、ICC(C,1) 来判断有无系统差异，但主要结果的形式必须事先定好，不能看了数值再挑。
- 评分者看过彼此的结果、看过参考标准或模型输出；用研究病例做培训。
- 只报裁决后的"共识标签"，不报裁决前的一致性。
- Bland-Altman 没有事先定可接受范围；忽略比例误差；把同一人的多次测量当独立点。
- Dice 只报平均值：小病灶 Dice 天生偏低，空掩膜处理不说明，HD 用像素而不是毫米；把 Dice 和 IoU 当成两个独立证据一起报，却没有边界指标。
- ≥ 3 名评分者、每人都评了全部对象，却默认用 Fleiss' kappa；有缺失评分时软件悄悄删掉整行，报告的对象数和实际不符。
- 同一患者的多个病灶当独立对象算 CI。

## 5. 结果必须报告

- 评分对象数、评分者人数与资质、培训方式、盲法、评分者内重复评分的间隔。
- 分类评分：列联表（或各类别分布）、原始一致率、一致性系数的种类（Cohen / Light / Conger / Fleiss kappa、Krippendorff's alpha、Gwet's AC1）与权重及 95% CI；有缺失评分时写明怎么处理、实际纳入多少对象。
- ICC 写成"ICC（模型、类型、单位）= 数值（95% CI）"，并注明软件和函数。
- Bland-Altman：偏倚及 95% CI、95% 一致性界限及其 CI、比例误差检验结果、Bland-Altman 图；与事先定的可接受范围对照。
- 分割：每例 Dice 和边界指标（HD95 或 NSD，写明容差）的中位数（IQR）和分布图；空掩膜规则及所用软件的参数设置；按结构分别报告。
- 裁决前一致性、分歧数量与裁决方式、最终标签的产生规则。

## 6. 对应报告规范

- 影像 AI 的标注：`claim`（CLAIM 2024，本地清单 `claim-2024.yaml`）16–18：参考标准标注的来源、测试集标注步骤、评分者间/内变异的测量及分歧处理。
- 诊断研究中的读片：`stard` 13a/13b（读片者与参考标准评估者的盲法）。
- 问卷/量表的信度研究：`cosmin`（COSMIN 报告指南 2.0 版，2025；仓库索引有条目，无本地清单，需人工核对）。
- 信度与一致性研究的专门报告指南 GRRAS（Kottner J, et al. J Clin Epidemiol 2011;64(1):96-106, doi:10.1016/j.jclinepi.2010.03.002）：仓库索引暂无条目，需按官方清单人工核对。

## 参考

- Koo TK, Li MY. A guideline of selecting and reporting intraclass correlation coefficients for reliability research. *J Chiropr Med*. 2016;15(2):155-163. doi:10.1016/j.jcm.2016.02.012
- Bland JM, Altman DG. Statistical methods for assessing agreement between two methods of clinical measurement. *Lancet*. 1986;1(8476):307-310. doi:10.1016/S0140-6736(86)90837-8
- Feinstein AR, Cicchetti DV. High agreement but low kappa: I. The problems of two paradoxes. *J Clin Epidemiol*. 1990;43(6):543-549. doi:10.1016/0895-4356(90)90158-L
- Maier-Hein L, Reinke A, Godau P, et al. Metrics reloaded: recommendations for image analysis validation. *Nat Methods*. 2024;21(2):195-212. doi:10.1038/s41592-023-02151-z
