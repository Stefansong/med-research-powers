# Study Protocol
type: ai-ml
title: Deep learning for bladder cancer detection on contrast-enhanced CT — a two-centre external validation against radiologists (synthetic example)
version: 1.0 — 2026-09-21
research_question: 在血尿患者的增强 CT 中，深度学习模型检测膀胱癌的诊断准确性是否不劣于放射科医生（PIRD）
registration: 建议在 ClinicalTrials.gov 或 OSF 注册诊断准确性研究方案（本示例未注册）
status: confirmed (hard checkpoint 1, 2026-09-21)

> Synthetic example produced with `study-design` (Type C module). Every number below is invented for illustration. Where a number needs a justification (sample size, non-inferiority margin, number of readers), the justification shown is also an illustrative assumption: it demonstrates what a real protocol must write down (method + inputs + source), not real evidence.

## 1. 研究概要
- Study type: 开发 + 外部验证（回顾性诊断准确性研究）
- Task: 患者级二分类（膀胱癌 有/无）+ 病灶定位
- Intended use: 血尿患者增强 CT 的第二阅片 / 分流提示，供泌尿科与放射科使用
- Reporting standard: STARD-AI（Nat Med 2025；本插件无本地清单，人工核对）+ STARD 2015 + CLAIM 2024（影像 AI）+ TRIPOD+AI 2024（模型开发部分）

## 2. 数据集来源、纳排与样本量
- Sources: 中心 A（开发 + 内部测试，2019-01–2023-12），中心 B（外部测试，2021-01–2024-06）
- Time window: 见上
- Inclusion / exclusion: 成年血尿患者的增强 CT 尿路成像（排泄期），按检查日期连续纳入；排除既往膀胱切除、图像伪影导致膀胱不可评估、无参考标准者
- Data volume（示例数字）: 中心 A 约 1,400 例（癌 320 / 非癌 1,080）；中心 B 约 400 例（癌 95 / 非癌 305）
- Sample size（外部测试集，示例假设）:
  - 精度法（Buderer 1996）：预期灵敏度 0.85、特异度 0.80（示例假设；真实研究取同类外部验证研究的报告值并写出处），95% CI 半宽 ≤ 0.075 → `power_analysis.py diagnostic --sensitivity 0.85 --specificity 0.80 --prevalence 0.24 --precision 0.075`：需癌 88 例、非癌 110 例，按患病率 24% 约 367 例；中心 B 约 400 例（癌 95 / 非癌 305）满足
  - 读片者研究：6 名读者 × 中心 B 全部病例（全交叉）。读者数和病例数按 MRMC 样本量方法确定，需要读者间和病例间方差参数——真实研究用预实验或同类研究的数据（`RJafroc::SsSampleSizeKGivenJ()`，或无预实验数据时用 `MRMCsamplesize`），并写明参数来源；本示例未做这一步
  - 模型开发部分（中心 A，深度学习图像分类）：没有公认的样本量公式（`pmsampsize` 针对回归类预测模型）；写明可用数据量，按 yaml `data_split` 选划分方式，并在 Limitations 讨论（TRIPOD+AI 第 10 条要求说明样本量是怎么定的）
- De-identification: DICOM 头去标识 + 面部区域外的盆腔图像；二次使用已在两中心伦理批准范围内

## 3. 患者级数据划分
- Strategy: 中心 A 按患者 60/20/20 划分 训练 / 验证 / 内部测试（n > 1000 → yaml `data_split` 的 hold-out 档）；中心 B 整体作为外部测试集，不参与任何调参
- Unit of split: 患者 ID
- Stratification: 按癌/非癌与年份
- Split seed: 20260921；划分脚本由 `data-collection-tools`（`patient_level_split.py`）生成，输出 `split_summary.json` 含泄漏检查

## 4. 标注流程与一致性
- Annotators: 2 名泌尿放射亚专科医师（8 年与 12 年经验）
- Protocol: 标注指南 v1.2；培训 30 例；标注时不看模型输出与病理结果
- Agreement: 病灶级 Dice + HD95（毫米；两者都为空掩膜的病例单独计数，不进平均）、患者级 Cohen's kappa（目标 ≥ 0.80）
- Adjudication: 分歧由第三名资深医师裁决

## 5. Ground Truth 定义
- Reference standard: 膀胱镜 + TURBT 病理（阳性）；膀胱镜阴性且随访 ≥ 12 个月无新发（阴性）
- Timing relative to index data: 参考标准在 CT 后 90 天内
- Known limitations of the reference: 随访阴性可能漏掉极小病灶（写入 Limitations）

## 6. 模型与训练
- Architecture / baseline models: 3D ResNet-50 变体；基线 2D ResNet-34 逐层聚合
- Pretraining / transfer learning: 公开 CT 预训练权重（来源与版本记录在代码库）
- Hyperparameters to report: AdamW，lr 1e-4 余弦退火，batch 8，≤ 100 epochs，early stopping（验证 AUROC 10 epochs 不升）
- Data augmentation: 随机旋转 ±10°、强度抖动 ±10%、随机裁剪；测试集不增强
- Class imbalance handling: 加权交叉熵 + 分层采样（加权会把预测概率整体推高：训练后在中心 A 验证集上做 logistic 重新校准，再输出概率）

## 7. 评估指标与校准 / DCA
- Primary metric: 外部测试集患者级 AUROC——模型单独 vs 6 名放射科医生组的平均 AUROC；非劣效：差值（模型 − 医生组）95% CI 下限 > −0.05
- Non-inferiority margin 0.05 的依据（示例假设）：真实研究要写出处，如临床专家共识认为 AUROC 相差 0.05 以内不改变分流决策，或既往研究中医生之间 AUROC 的差异范围
- Secondary metrics: 灵敏度 / 特异度（两个阈值都在中心 A 验证集上确定并写死：约登指数阈值 + 验证集灵敏度 ≥ 0.95 处的高灵敏度阈值；外部测试集只用这两个阈值）、AUPRC、病灶级检出率（按大小分层）
- Calibration: 校准截距（calibration-in-the-large）与校准斜率、平滑校准曲线、Brier score（外部测试集）
- Clinical utility: DCA（阈值概率 5–40%）
- Comparison: 多读者多病例（MRMC）设计——6 名放射科医生（年资 3–5 年、>10 年各 3 名）读中心 B 全部病例，每例按 5 级可信度评分（用于算 AUROC）；AI alone vs human alone vs AI-assisted，阅片顺序随机，两轮之间洗脱期 8 周；读者对参考标准和临床随访结果设盲
- Statistical analysis: AI 单独 vs 医生组——MRMC 分析，AI 作固定读者，读者和病例作随机效应（RJafroc `StSignificanceTestingCadVsRad()`）；AI 辅助 vs 不辅助——Obuchowski-Rockette 法（MRMCaov / RJafroc）；不对每位医生分别做 DeLong。配对 DeLong 只用于同一批病例上两个模型之间（3D 模型 vs 2D 基线）；其余指标按患者 bootstrap 2,000 次求 CI；详细 → `analysis-plan.md`
- Subgroup / fairness: 性别、年龄（<60 / ≥60）、肿瘤大小、中心

## 8. 外部验证计划
- External cohort: 中心 B（不同扫描仪厂商与对比剂方案）
- Timing: 同期
- Success criteria: 外部 AUROC ≥ 0.85，且非劣效检验成立

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
- Consent / waiver: 回顾性去标识数据，知情同意豁免
- Data transfer: 数据不出院；模型在院内算力训练；不上传可识别数据到外部平台

## 13. 报告规范映射
- STARD 2015（条目编号按本插件 `stard-2015.yaml`）：5（前瞻/回顾设计）→ §1；6–9（纳入标准、识别方式、地点与时间、连续纳入）→ §2；10a（指标检查）→ §6、§7；10b、11、12b（参考标准、选择理由、阳性定义）→ §5；12a（指标检查阈值的定义与依据）→ §7；13a、13b（读者 / 参考标准评估者设盲）→ §4、§5、§7；14（准确性的估计与比较方法）→ §7；15、16（不确定结果、缺失数据）→ `analysis-plan.md`；17（亚组等变异分析）→ §7；18（样本量）→ §2；19–25（结果）→ manuscript Results；28–29（注册、方案获取）→ 文件头
- STARD-AI 新增或修改的条目：本插件无本地清单，投稿前对照官方全文人工逐条核对
- CLAIM 2024 数据 / Ground truth / 划分 / 模型 / 评估 → §2–§7；可复现性 → §9
- TRIPOD+AI 2024 模型开发与验证条目 → §6–§8；fairness → §7
