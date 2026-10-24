# Study Protocol
type: ai-ml
title: Deep learning for bladder cancer detection on contrast-enhanced CT — a two-centre external validation against radiologists (synthetic example)
version: 1.0 — 2026-09-21
research_question: 在血尿患者的增强 CT 中，深度学习模型检测膀胱癌的诊断准确性是否不劣于放射科医生（PIRD）
registration: 建议在 ClinicalTrials.gov 或 OSF 注册诊断准确性研究方案（本示例未注册）
status: confirmed (hard checkpoint 1, 2026-09-21)

> Synthetic example produced with `study-design` (Type C module). Every number below is invented for illustration. Where a number needs a justification (sample size, non-inferiority margin, number of readers), the justification shown is also an illustrative assumption: it demonstrates what a real protocol must write down (method + inputs + source), not real evidence. Numbers that a real study would still have to source are marked 示例假设.

## 0. 真实条件与设计理由
- 真实条件：
  - 研究目的：评估 3D CNN 在血尿患者增强 CT 上检出膀胱癌的准确性，并与放射科医生比较；结果用于讨论分流阈值（`research-question.md`）
  - 数据来源：回顾性已有数据——两家中心 PACS 中已归档的 CT 尿路成像，加膀胱镜、病理和随访记录；中心 A 2019-01–2023-12，中心 B 2021-01–2024-06
  - 病例数与事件数：中心 A 约 1,400 例（癌 320，已按 §2 的全部纳排标准排除）；中心 B 400 例（癌 95，已排除膀胱切除史和无参考标准者，尚未按图像质量排除——见未知项）。同一患者有多次 CT 时只用第一次；同一患者的多个病灶只进病灶级分析，并按患者聚类
  - 中心数：2；两中心的扫描仪厂商和对比剂方案不同
  - 随访可行性：阴性者需随访 ≥ 12 个月，两中心的随访记录都可查
  - 资源与时间：2 名标注医师 × 3 个月；6 名放射科医生各读中心 B 全部可评估病例（至多 400 例）× 2 轮；院内算力 2 × H100
  - 伦理 / 注册限制：二次使用在两中心伦理批准范围内；数据不出院
  - 已有研究：快速查重命中 41 篇，外部验证 + 与医生比较者 6 篇，均为单中心（`research-question.md` §4）
- 未知项：
  - MRMC 方差成分（读者间、病例间方差及其交互）→ 需要读片预实验（2 名读者 × 约 60 例，不进入正式分析）或同类 MRMC 研究的报告值 → 决定 6 名读者是否够（影响主要终点的功效，见 §2）
  - 中心 B 按图像质量排除后的可评估例数和癌例数 → 需中心 B 影像科提供 → §2 的精度按排除前的 400 例 / 癌 95 例算，是上限；拿到可评估例数后用同样的方法重算，癌少于 88 例时灵敏度 CI 半宽达不到 0.075（写入 Limitations）
- 设计选择：回顾性、连续纳入的诊断准确性研究；中心 A 开发模型（嵌套交叉验证，不做随机 hold-out）；中心 B 整体作外部测试集，并在其上做 6 名读者的 MRMC 读片比较
- 理由：只有已归档的回顾性数据，不能写成前瞻性研究；按检查日期连续纳入以减少谱偏倚；用另一家、不同厂商的中心作外部验证，比在中心 A 内随机拆分更能回答"能否推广"；没有做前瞻性或随机对照评价（AI 辅助能否改善患者结局），因为这一阶段要先确认外部准确性，前瞻性评价放到后续研究（DECIDE-AI）

## 1. 研究概要
- Study type: 开发 + 外部验证（回顾性诊断准确性研究）
- Task: 患者级二分类（膀胱癌 有/无）+ 病灶定位
- Intended use: 血尿患者增强 CT 的第二阅片 / 分流提示，供泌尿科与放射科使用
- Reporting standard: STARD-AI（Nat Med 2025；本插件无本地清单，人工核对）+ STARD 2015 + CLAIM 2024（影像 AI）+ TRIPOD+AI 2024（模型开发部分）

## 2. 数据集来源、纳排与样本量
- Sources: 中心 A（开发，2019-01–2023-12），中心 B（外部测试，2021-01–2024-06）
- Time window: 见上
- Inclusion / exclusion: 成年血尿患者的增强 CT 尿路成像（排泄期），按检查日期连续纳入；排除既往膀胱切除、图像伪影导致膀胱不可评估、无参考标准者
- Data volume（示例数字）: 中心 A 约 1,400 例（癌 320 / 非癌 1,080）；中心 B 400 例（癌 95 / 非癌 305；图像质量排除前，见 §0 未知项）
- Sample size — 外部测试集（数据量已固定，下面说明它能支撑多精确的估计）: 中心 B 共 400 例（癌 95 例，患病率约 24%；这是图像质量排除前的数字，下面的精度都是上限，排除后按可评估例数重算）
  - 灵敏度 / 特异度精度（Buderer 1996）：预期灵敏度 0.85、特异度 0.80（示例假设；真实研究取同类外部验证研究的报告值并写出处），95% CI 半宽 ≤ 0.075 → `power_analysis.py diagnostic --sensitivity 0.85 --specificity 0.80 --prevalence 0.24 --precision 0.075`：需癌 88 例、非癌 110 例，按患病率 24% 约 363 例；中心 B 排除前（癌 95 / 非癌 305）满足，图像质量排除后癌仍须 ≥ 88 例
  - 区分度与校准的精度（Riley 的外部验证样本量方法：Riley 2021，doi:10.1002/sim.9025；Riley 2024，doi:10.1136/bmj-2023-074821；真实研究用 `pmvalsampsize` 算）：预期 C 统计量 0.90（示例假设）、模型校准良好时，400 例、95 个事件 → C 统计量 95% CI 宽约 0.07（Riley 2024 示例的目标是 ≤ 0.1，满足）；O/E 95% CI 约 0.84–1.19，即观察到的癌比例约在 0.20–0.28 之间；校准斜率 95% CI 宽约 0.42（没有线性预测值分布的资料，按 Riley 2024 的兜底假设：癌与非癌中各服从方差相同的正态分布）。Riley 2024 示例对校准斜率的目标是 CI 宽 ≤ 0.3，按同样假设约需 800 例——中心 B 达不到，所以外部测试集上的校准只作描述（报告估计值与 CI），不据此下"校准良好"的结论，写入 Limitations
  - 读片者研究（MRMC）：6 名读者 × 中心 B 全部可评估病例（至多 400 例；全交叉）。病例数已由中心 B 固定，能调的是读者数。主要终点（模型 vs 读者组平均 AUROC 的非劣效，界值 0.05）的功效要用 MRMC 方差成分算（Obuchowski-Rockette 法；Hillis 2011，doi:10.1016/j.acra.2010.09.007；`RJafroc::SsSampleSizeKGivenJ()` 输入预实验数据或方差参数，无预实验数据时 `MRMCsamplesize`）。本示例没有这些参数：6 名读者是示例假设，列为 §0 的未知项——正式读片前用预实验估计方差成分并重算；功效 < 80% 时增加读者，按 protocol 修订记录
  - 模型开发部分（中心 A，深度学习图像分类）：没有公认的样本量公式（`pmsampsize` 针对回归类预测模型）；写明可用数据量与事件数（约 1,400 例、癌 320 例），按 yaml `data_split` 选验证方式（§3），并在 Limitations 讨论（TRIPOD+AI 第 10 条要求说明样本量是怎么定的）
- De-identification: DICOM 头去标识 + 面部区域外的盆腔图像；二次使用已在两中心伦理批准范围内

## 3. 验证方式与患者级数据划分
- Rule: 按 yaml `deep_learning_training.data_split`——由模型类型和事件数决定，不看总人数。本模型是要调超参数的 3D CNN → 嵌套交叉验证；中心 A 内不做随机 hold-out：20% 的 hold-out 只有约 280 例、癌约 64 例，按 §2 同样的假设，校准斜率 95% CI 宽约 0.51，远超目标，而且这些病例不再参与建模；嵌套交叉验证的外层合并预测让全部 320 例癌都参与内部性能估计
- Strategy: 中心 A 内嵌套交叉验证——外层 5 折（每折约 280 例、癌约 64 例）只用来估计内部性能，内层 5 折用于调参与早停；外层合并的 out-of-fold 预测（全部 320 例癌都参与）用来确定 §7 的两个阈值。最终模型用同一调参流程在中心 A 全部数据上重训
- External test: 中心 B 整体作为外部测试集，不参与任何调参、阈值选择或校准——可推广性的结论只依据中心 B
- Patients and events per fold: 每折的患者数、癌例数和类别分布写入 `split_summary.json`
- Unit of split: 患者 ID（同一患者的所有序列和切片在同一折）
- Stratification: 按结局（癌 / 非癌）分层，再按检查年份（分层标签用"结局 × 年份"的组合）
- Split seed: 20260921；外层折由 `data-collection-tools`（`patient_level_split.py --kfold 5`，按患者、按结局分层）生成，内层折在每个外层训练集内用同一脚本生成；输出的 `split_summary.json` 含泄漏检查

## 4. 标注流程与一致性
- Annotators: 2 名泌尿放射亚专科医师（8 年与 12 年经验）
- Protocol: 标注指南 v1.2；培训 30 例；标注时不看模型输出与病理结果
- Agreement: 病灶级 Dice + HD95（毫米；两者都为空掩膜的病例单独计数，不进平均）、患者级 Cohen's kappa（目标 ≥ 0.80，示例假设）
- Adjudication: 分歧由第三名资深医师裁决

## 5. Ground Truth 定义
- Reference standard: 膀胱镜 + TURBT 病理（阳性）；膀胱镜阴性且随访 ≥ 12 个月无新发（阴性）
- Timing relative to index data: 参考标准在 CT 后 90 天内
- Blinding of reference-standard assessors: 参考标准是在临床诊疗中得到的，膀胱镜医生和病理医生看得到临床信息和当时的 CT 报告，但看不到模型输出（模型是事后运行的）；写入 Limitations
- Known limitations of the reference: 随访阴性可能漏掉极小病灶（写入 Limitations）

## 6. 模型与训练
- Architecture / baseline models: 3D ResNet-50 变体；基线 2D ResNet-34 逐层聚合
- Pretraining / transfer learning: 公开 CT 预训练权重（来源与版本记录在代码库）
- Hyperparameters to report: AdamW，lr 1e-4 余弦退火，batch 8，≤ 100 epochs，early stopping（内层验证折 AUROC 10 epochs 不升）
- Data augmentation: 随机旋转 ±10°、强度抖动 ±10%、随机裁剪；测试集不增强
- Class imbalance handling: 不做类别加权或重采样——中心 A 癌 : 非癌约 1 : 3.4，不属于严重不平衡，而加权或重采样会把预测概率推离真实风险（van den Goorbergh 2022，doi:10.1093/jamia/ocac093）；按结局分层划分保证每折都有足够的癌例

## 7. 评估指标与校准 / DCA
- Primary metric: 外部测试集患者级 AUROC——模型单独 vs 6 名放射科医生组的平均 AUROC；非劣效：差值（模型 − 医生组）95% CI 下限 > −0.05
- Non-inferiority margin 0.05 的依据（示例假设）：真实研究要写出处，如临床专家共识认为 AUROC 相差 0.05 以内不改变分流决策，或既往研究中医生之间 AUROC 的差异范围
- Secondary metrics: 灵敏度 / 特异度（两个阈值都在中心 A 嵌套交叉验证的 out-of-fold 预测上确定并写死：约登指数阈值 + 灵敏度 ≥ 0.95 处的高灵敏度阈值；外部测试集只用这两个阈值）、AUPRC、病灶级检出率（按大小分层）
- Calibration: calibration-in-the-large（校准截距）与校准斜率、平滑校准曲线、Brier score（外部测试集；精度有限，见 §2，只作描述）
- Clinical utility: DCA（阈值概率 5–40%，示例假设：真实研究按临床上会改变处理的风险范围定并写依据）
- Comparison: 多读者多病例（MRMC）设计——6 名放射科医生（年资 3–5 年、>10 年各 3 名）读中心 B 全部病例，每例按 5 级可信度评分（用于算 AUROC）；AI alone vs human alone vs AI-assisted，阅片顺序随机，两轮之间洗脱期 8 周（示例假设，理由写病例被记住的风险）；读者能看到年龄、性别和血尿类型（与临床阅片一致），看不到参考标准、病理和随访结果
- Statistical analysis: AI 单独 vs 医生组——MRMC 分析，AI 作固定读者，读者和病例作随机效应（RJafroc `StSignificanceTestingCadVsRad()`）；AI 辅助 vs 不辅助——Obuchowski-Rockette 法（MRMCaov / RJafroc）；不对每位医生分别做 DeLong。配对 DeLong 只用于同一批病例上两个模型之间（3D 模型 vs 2D 基线）；其余指标按患者 bootstrap 2,000 次求 CI；详细 → `analysis-plan.md`
- Subgroup / fairness: 性别、年龄（<60 / ≥60）、肿瘤大小、中心

## 8. 外部验证计划
- External cohort: 中心 B（不同扫描仪厂商与对比剂方案）
- Timing: 同期
- Success criteria: 外部 AUROC ≥ 0.85（示例假设：真实研究写出处，如现有工具或医生在同类人群中已报道的 AUROC），且非劣效检验成立

## 9. 可复现性
- Seed: 20260921；environment: requirements.txt + Docker 镜像；hardware: 2 × H100
- Code & weights: GitHub（发表时公开）+ Zenodo DOI；推理脚本随文提供
- Data availability statement: 去标识的外部测试集特征表按合理请求提供；影像不公开

## 10. Prompt 标准化
- 不适用（非 LLM / VLM 研究）

## 11. 可解释性与安全
- Explainability method: Grad-CAM；展示 典型 / 最佳 / 最差 各 5 例
- Failure mode analysis: 假阴性按病灶大小与位置分类；假阳性按血凝块 / 小梁化 / 憩室分类
- Human-AI interaction & safety monitoring: 本研究为回顾性，不涉及；前瞻性评估另按 DECIDE-AI

## 12. 伦理与数据治理
- Ethics approval: 两中心 IRB 批准（编号记录在 `ethics-statement.md`）；二次使用在批准范围内
- Consent / waiver: 回顾性数据，伦理委员会批准免除知情同意（写明满足的每一项条件：不豁免无法开展（患者多已失访、例数大）、风险不超过最小风险、具有重要社会价值；去标识化是保护措施，不是豁免理由）
- Data transfer: 数据不出院；模型在院内算力训练；患者级数据（含去标识化数据）不发给外部平台或外部 AI 服务，对外只给汇总结果

## 13. 报告规范映射
- STARD 2015（条目编号按本插件 `stard-2015.yaml`，34 行全部映射）：1、2（标题与结构化摘要中标明诊断准确性研究）→ manuscript Title / Abstract；3（背景、指标检查的预期用途与临床角色）→ §1 Intended use + `research-question.md`；4（目的与假设）→ 文件头 research_question + `research-question.md` §3；5（前瞻/回顾设计）→ §1；6–9（纳入标准、识别方式、地点与时间、连续纳入）→ §2；10a（指标检查）→ §6、§7；10b、11、12b（参考标准、选择理由、阳性定义）→ §5；12a（指标检查阈值的定义与依据）→ §7；13a（指标检查的读者能否看到临床信息和参考标准结果）→ §7 Comparison；13b（参考标准评估者能否看到临床信息和指标检查结果）→ §5；14（准确性的估计与比较方法）→ §7；15、16（不确定结果、缺失数据）→ `analysis-plan.md`；17（亚组等变异分析）→ §7；18（样本量）→ §2；19–25（结果）→ manuscript Results；26、27（局限、临床意义）→ manuscript Discussion；28–29（注册、方案获取）→ 文件头；30（资助与资助方角色）→ manuscript 声明部分
- STARD-AI 新增或修改的条目：本插件无本地清单，投稿前对照官方全文人工逐条核对
- CLAIM 2024 数据 / Ground truth / 划分 / 模型 / 评估 → §2–§7；可复现性 → §9
- TRIPOD+AI 2024 模型开发与验证条目 → §2（样本量，第 10 条）、§3、§6–§8；fairness → §7
