# AI/ML Research SAP Extension — Sections 8–16

Reference for `data-analysis-planning` when the study is Type C (AI/ML, from `study-design`).
`analysis-plan.md` must add the nine sections below to the standard seven. Every metric,
data split and Ground Truth definition must match the Type C `study-protocol.md`; anything
new is labelled **post-hoc / exploratory**.

Lookup tables live in `stat-method-decision-tree.yaml` (keys named per section) — do not
copy them into the SAP, cite the choice and the reason.

---

## 8. 模型架构选择

- 候选模型（≥2）+ 一个简单基线（logistic regression / 经典 ML / 现有临床评分）
- 预训练策略：ImageNet / 领域预训练 / 自监督；写明权重来源
- 选择依据：任务类型（分类 / 分割 / 检测 / LLM-VLM 评估）+ 数据量（见第 10 节）
- yaml：`deep_learning_classification` / `deep_learning_segmentation` / `deep_learning_detection`

## 9. 训练策略（超参数必须可复现）

必报项（yaml `deep_learning_training.hyperparameter_reporting.required`）：optimizer、learning_rate、lr_schedule、batch_size、epochs、early_stopping、weight_decay、dropout。推荐项：warmup_steps、gradient_clipping、mixed_precision、seed。
早停和模型选择只能用验证集，不能用测试集。

## 10. 数据划分方案

按样本量分档的划分方案**只在** yaml `deep_learning_training.data_split` 维护（study-design Type C 引用同一表）。SAP 里写：
- 所选方案 + 理由（n 落在哪一档）
- **必须按患者 ID 划分**（同一患者的所有图像/切片/帧在同一集合或同一折）——写明患者级划分逻辑和患者级标签规则（多数票 / 任一阳性）
- 随机种子；各集合 / 各折的患者数、样本数、类别分布（用 `${CLAUDE_PLUGIN_ROOT}/skills/data-collection-tools/scripts/patient_level_split.py` 生成，其 `split_summary.json` 直接贴入）
- 外部验证集来源（不同中心 / 时间段），n < 50 时外部验证为强制项

## 11. 数据增强策略

- 预先列出几何 / 强度 / 高级增强（yaml `deep_learning_training.augmentation`）及参数范围
- 只在训练集做增强；测试集禁止增强（TTA 除外，且 TTA 要预先声明）

## 12. 类别不平衡处理

- 数据层（过采样 / 欠采样 / SMOTE）或损失层（weighted CE / focal / dice / combo）——预先选定
- **模型要输出风险概率时慎用**：重采样和类别加权会把预测概率整体推向少数类，校准变差，AUROC 并不提高（van den Goorbergh 2022，doi:10.1093/jamia/ocac093）。优先不做校正、改用阈值调整灵敏度；确要校正时，在未重采样的数据上重新校准，并报告重新校准后的校准指标（yaml `deep_learning_training.class_imbalance.warning`）
- 评估层面**不用 accuracy**：主指标 AUROC / AUPRC / F1（yaml `deep_learning_training.class_imbalance`）

## 13. 消融实验

- 序列：baseline → +A → +B → full；固定相同数据划分与随机种子
- 每一步报告主指标 + 95% CI；消融也是预先指定的分析，不是事后补做

## 14. 模型比较统计检验

不能只报点估计——每个指标都要 95% CI + 比较检验：

| 比较 | 检验 | yaml |
|------|------|------|
| 两条 ROC 曲线 | DeLong test | `deep_learning_classification.comparison` |
| 任一指标的 CI | Bootstrap（B ≥ 2000） | `resampling.bootstrap_ci` |
| 两个分类器的错误模式 | McNemar test | `deep_learning_classification.comparison` |
| 同一测试集上两个分割模型 | Paired Wilcoxon（Dice / HD95 逐例） | `deep_learning_segmentation.comparison` |
| 多模型 | Bootstrap 或置换检验（≥1000 次） | `model_comparison.multi_model` |
| AI vs 人类 / AI 辅助人类 | 同一测试集、同等信息、盲法；≥2 周 washout；多读者多病例（MRMC）分析，读者与病例都作随机效应——AI 单独 vs 医生组时 AI 作固定读者；不对每位医生分别做 DeLong（见方法要点卡 `diagnostic-accuracy-and-ai-evaluation.md`） | `model_comparison.human_vs_ai` |

分割任务指标与 study-design metrics 表一致：Dice / IoU 为主，**95th percentile Hausdorff distance (HD95)** 与 average surface distance 为次要，体积一致性用 Bland-Altman。

## 15. 模型可解释性方案

- 方法按模型类型选：Grad-CAM（CNN）/ SHAP（任何模型，特征级）/ Attention maps（Transformer）/ 不确定性图（分割）——yaml `explainability`
- 报告 ≥3–5 个典型案例：typical / best / worst，并说明选例规则（预先定，避免挑好看的）

## 16. 不确定性量化

- 安全关键应用（手术导航、诊断、治疗规划）必须做：MC Dropout（N ≥ 30 次前向）/ Deep Ensembles（M = 5）/ TTA——yaml `uncertainty_quantification`
- 校准（输出概率的模型都要做）：以 calibration-in-the-large（校准截距）、校准斜率和平滑校准曲线为主，另报 Brier；ECE / MCE 依赖分箱方式，只作补充并写明分箱（yaml `deep_learning_classification.calibration`；做法见方法要点卡 `regression-and-prediction-models.md`）；临床预测模型另加 DCA（净获益）。NRI / IDI 不是恰当的性能指标，只在期刊要求时与 DCA 一起作补充

---

## SAP 特有判断（yaml 里没有的）

- 指标、划分、Ground Truth 必须与 Type C protocol 一致；新增指标标记为 post-hoc / exploratory
- 样本量：沿用 protocol 已锁定的计算——风险预测模型按 Riley 方法（`pmsampsize`），灵敏度/特异度按可接受的 CI 宽度（Buderer 法），读片者研究按 MRMC 方法；第 10 节的按 n 分档只决定怎么划分数据，不能代替样本量依据（做法见方法要点卡 `regression-and-prediction-models.md`、`diagnostic-accuracy-and-ai-evaluation.md`）
- 报告规范对应：影像 AI → CLAIM 2024（44 项）；预测模型 → TRIPOD+AI；诊断准确性 → STARD-AI（Nat Med 2025，doi:10.1038/s41591-025-03953-8）+ STARD 2015；LLM → TRIPOD-LLM（Nat Med 2025）。`reporting-standards` 有 CLAIM 2024、TRIPOD+AI、STARD 2015 的本地逐条清单；**STARD-AI 和 TRIPOD-LLM 没有本地清单**（STARD-AI 也不在规范索引里），要对照官方全文人工核对
- 公平性与稳健性（按性别 / 年龄 / 中心分层的 AUROC 与校准，跨中心 / 跨时间验证）在 SAP 里预先列为次要分析（yaml 无此节；见 study-design `metrics-and-reporting.yaml` 的 `fairness_and_bias` / `robustness`）
