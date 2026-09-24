# 聚类与重复测量数据 — 方法要点卡

> 适用：观测之间不独立的数据——同一患者多条记录（多个结石/病灶、双侧肾、多次随访）、多中心、同一术者多台手术（手术视频研究）、同一视频多帧、同一病例多道题。　不适用：整群随机试验的随机化与样本量设计细节（另查 CONSORT-Cluster 相关文献）；中断时间序列（见 yaml `time_series`）。

## 1. 计划前先看数据的什么

只看结构和质量，**不看**暴露/分组与结局的关系：
- 层级结构有几层（帧 ⊂ 视频 ⊂ 患者 ⊂ 术者 ⊂ 中心）；每一层的 ID 字段是否齐全、唯一、前后写法一致。
- 每一层的个数（中心数、术者数、患者数）和聚类大小的分布（最小、中位数、最大；只有 1 条记录的聚类占多少）。
- 结局在聚类内是否有变化：多少聚类内部结局全相同（全阳性或全阴性）。
- 暴露/分组在哪一层变化：患者层（如手术方式）还是病灶层（如结石位置）——决定模型怎么写，也决定哪一层的个数才是真正的样本量。
- 重复测量：随访时间点是否统一、每人测了几次、缺失是中途脱落还是间断缺失。
- 聚类大小本身的分布（如每人结石数），为判断"聚类大小是否可能与结局有关"做准备——只看分布，不看它与结局的关联。
- 前瞻性研究还没有数据：写下预期的聚类数、平均聚类大小、组内相关系数（ICC）的文献值或预实验值。

## 2. 计划里必须预先写明

- **分析单位与推断对象**：结论针对患者、病灶还是手术；样本量按独立单位（患者/术者）计，不按帧或病灶的条数计。
- **处理方式**（选一种为主要分析，并写理由）：
  - 按上一层汇总：如每名患者一个结局（任一结石残留 = 阳性），之后按普通独立数据分析；
  - GEE（广义估计方程，generalized estimating equations）：估计"人群平均效应"；写明工作相关结构（exchangeable 可交换 / AR(1) 自回归 / independence 独立），配稳健（三明治）标准误；
  - 混合效应模型（mixed-effects model）：估计"同一聚类内的条件效应"；写明随机截距（每名患者/术者有自己的基线），是否加随机斜率（如学习曲线斜率因术者而异）。
- **GEE 还是混合模型**：想回答"对整个人群平均而言，暴露使结局变化多少"→ GEE；想回答"对同一名患者/同一位术者而言"，或需要估计术者间差异、ICC → 混合模型。连续结局的线性模型两者的系数含义相同；logistic 等非线性模型两者的 OR 含义不同（混合模型的条件 OR 通常离 1 更远），不能混着解读（Hubbard 2010）。
- **聚类数少时的校正**：聚类数少于约 40 个时，GEE 的三明治标准误偏小、I 类错误膨胀（Li & Redden 2015）→ 用偏差校正的方差（Mancl-DeRouen、Kauermann-Carroll 或 Fay-Graubard）并用 t 分布（自由度约为聚类数减参数个数）。聚类大小差别大时 Fay-Graubard 更稳。线性混合模型用 REML 估计，自由度用 Kenward-Roger 或 Satterthwaite。中心只有 2–3 个时估计不了中心间方差，把中心作为固定效应（哑变量）或分层因素。
- **多层结构**：逐层写明怎么处理（如帧先按视频汇总；视频嵌套在术者内 → 术者随机截距）。
- **ICC 与设计效应**：设计效应 DE = 1 + (m − 1) × ICC（m 为平均聚类大小），有效样本量 = 总观测数 ÷ DE；前瞻性研究按 DE 放大样本量（yaml `clustered_data`）。
- **随机效应结构预先定好**：随机斜率、相关结构不能看了结果再加减；写明不收敛或奇异拟合（方差估计为 0）时的简化顺序。
- **AI 研究的数据划分**：按患者划分；手术视频研究要把结论推广到新术者时按术者划分（`patient_level_split.py` 的 `--patient-col` 填术者 ID）。
- **敏感性分析**：换一种处理方式重做（如 GEE vs 按患者汇总）；聚类大小可能与结局有关时（结石越多越容易残留），加一个按患者汇总或按"1/聚类大小"加权的分析。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| GEE | `geepack::geeglm(y ~ x, id = patient_id, family = binomial, corstr = "exchangeable")`（数据须先按 id 排序，同一聚类的行连在一起） | `statsmodels.formula.api.gee("y ~ x", groups="patient_id", data=df, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable())` |
| GEE 小样本校正 | `glmtoolbox::glmgee()` 后 `vcov(fit, type = "bias-corrected")`（Mancl-DeRouen）；`geesmv::GEE.var.kc()` / `geesmv::GEE.var.fg()` | `GEE(...).fit(cov_type="bias_reduced")`（Mancl-DeRouen） |
| 线性混合模型 | 用 `lmerTest::lmer()` 拟合（公式见表下；语法与 `lme4::lmer()` 相同），自由度与 P 值：`summary(fit, ddf = "Kenward-Roger")`（需要装 `pbkrtest`）。直接用 `lme4::lmer()` 拟合时 `summary()` 会静默忽略 `ddf`，只给 t 值、不给自由度和 P 值；已拟合的对象可先 `lmerTest::as_lmerModLmerTest(fit)` 转换 | `statsmodels.formula.api.mixedlm("y ~ x", df, groups="surgeon_id")` |
| 二分类/计数结局的混合模型 | `lme4::glmer(..., family = binomial)`（公式见表下） | 无公认成熟的频率学派实现（`BinomialBayesMixedGLM` 是贝叶斯近似），建议用 R，或改用 GEE |
| 由模型算 ICC | `performance::icc(fit)` | 由 `MixedLM` 的方差分量现算：随机截距方差 ÷（随机截距方差 + 残差方差） |
| 按患者/术者划分 | 用插件脚本 `patient_level_split.py`（Python，命令行调用） | `patient_level_split.py`；`sklearn.model_selection.GroupKFold` / `StratifiedGroupKFold` |

```r
lmerTest::lmer(y ~ x + (1 | surgeon_id), data = d)                  # 术者随机截距；summary(fit, ddf = "Kenward-Roger")
lme4::glmer(y ~ x + (1 | patient_id), family = binomial, data = d)  # 二分类结局
```

二分类结局的 ICC 在潜变量尺度上算：随机截距方差 ÷（随机截距方差 + π²/3）；报告时写明用的哪种算法。

## 4. 常见的坑

- 把帧、病灶或随访记录当独立样本算 n 和 P 值：CI 过窄，假阳性增多。
- 建模时考虑了聚类，数据划分却按图像/帧随机分：同一患者或同一术者同时进训练集和测试集。
- 以为 ICC 很小就可以忽略聚类：DE 还取决于聚类大小，每个视频上千帧时，ICC 很小 DE 也很大。
- 用 GEE 的系数解释"某一位术者"，或把混合模型的 OR 当成人群平均效应。
- 聚类数少仍用普通三明治标准误 + z 检验。
- 看了结果才决定加不加随机斜率、换不换相关结构；模型不收敛、奇异拟合却不报告。
- 双侧器官（左右肾）各算一例却不说明，也不按患者处理相关性。
- 多结石/多病灶患者在病灶级分析里权重过大，结论被少数病灶多的患者左右。

## 5. 结果必须报告

- 每一层的个数（中心、术者、患者、病灶/帧）和聚类大小分布；流程图里每一层的人数对得上。
- 所用方法：汇总规则 / GEE 工作相关结构 / 混合模型的随机效应结构；小样本校正方法和自由度方法。
- 效应量及 95% CI，并写明是人群平均效应还是条件效应。
- ICC（或方差分量）及其计算方式；前瞻性研究的设计效应。
- 收敛与奇异拟合情况；敏感性分析结果与主要分析是否一致。
- 软件与包版本。

## 6. 对应报告规范

- 先按研究类型选主规范：观察性研究 `strobe`（12a 统计方法、12e 敏感性分析）；诊断研究 `stard`；影像 AI `claim`（20：数据划分在哪一层互不重叠）。
- 预测模型用聚类数据（多中心）：`tripod-ai`（12d、23b：跨聚类的异质性）+ `tripod-cluster`（TRIPOD-Cluster 2023，仓库索引有条目，无本地清单，需人工核对）。
- 整群随机试验：`consort-2025` + `consort-cluster`（CONSORT-Cluster 2012，无本地清单，需人工核对）。

## 参考

- Hubbard AE, Ahern J, Fleischer NL, et al. To GEE or not to GEE: comparing population average and mixed models for estimating the associations between neighborhood risk factors and health. *Epidemiology*. 2010;21(4):467-474. doi:10.1097/EDE.0b013e3181caeb90
- Mancl LA, DeRouen TA. A covariance estimator for GEE with improved small-sample properties. *Biometrics*. 2001;57(1):126-134. doi:10.1111/j.0006-341x.2001.00126.x
- Li P, Redden DT. Small sample performance of bias-corrected sandwich estimators for cluster-randomized trials with binary outcomes. *Stat Med*. 2015;34(2):281-296. doi:10.1002/sim.6344
- Killip S, Mahfoud Z, Pearce K. What is an intracluster correlation coefficient? Crucial concepts for primary care researchers. *Ann Fam Med*. 2004;2(3):204-208. doi:10.1370/afm.141
