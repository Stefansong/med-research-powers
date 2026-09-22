# Study Protocol
type: ai-ml
title: Deep learning for bladder cancer detection on contrast-enhanced CT — a two-centre external validation against radiologists (synthetic example)
version: 1.0 — 2026-09-21
research_question: 在血尿患者的增强 CT 中，深度学习模型检测膀胱癌的诊断准确性是否不劣于放射科医生（PIRD）
registration: 建议在 ClinicalTrials.gov 或 OSF 注册诊断准确性研究方案（本示例未注册）
status: confirmed (hard checkpoint 1, 2026-09-21)

> Synthetic example produced with `study-design` (Type C module). Every number below is invented for illustration.

## 1. 研究概要
- Study type: 开发 + 外部验证（回顾性诊断准确性研究）
- Task: 患者级二分类（膀胱癌 有/无）+ 病灶定位
- Intended use: 血尿患者增强 CT 的第二阅片 / 分流提示，供泌尿科与放射科使用
- Reporting standard: STARD 2015（主）+ CLAIM 2024（影像 AI）+ TRIPOD+AI 2024（模型开发部分）

## 2. 数据集来源与纳排
- Sources: 中心 A（开发 + 内部测试，2019-01–2023-12），中心 B（外部测试，2021-01–2024-06）
- Time window: 见上
- Inclusion / exclusion: 成年血尿患者的增强 CT 尿路成像（排泄期）；排除既往膀胱切除、图像伪影导致膀胱不可评估、无参考标准者
- Data volume: 中心 A 约 1,400 例（癌 320 / 非癌 1,080）；中心 B 约 400 例（癌 95 / 非癌 305）
- De-identification: DICOM 头去标识 + 面部区域外的盆腔图像；二次使用已在两中心伦理批准范围内

## 3. 患者级数据划分
- Strategy: 中心 A 按患者 8:1:1 划分 训练 / 验证 / 内部测试（n > 1000 → hold-out 档）；中心 B 整体作为外部测试集，不参与任何调参
- Unit of split: 患者 ID
- Stratification: 按癌/非癌与年份
- Split seed: 20260921；划分脚本由 `data-collection-tools`（`patient_level_split.py`）生成，输出 `split_summary.json` 含泄漏检查

## 4. 标注流程与一致性
- Annotators: 2 名泌尿放射亚专科医师（8 年与 12 年经验）
- Protocol: 标注指南 v1.2；培训 30 例；标注时不看模型输出与病理结果
- Agreement: 病灶级 Dice、患者级 Cohen's kappa（目标 ≥ 0.80）
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
- Class imbalance handling: 加权交叉熵 + 分层采样

## 7. 评估指标与校准 / DCA
- Primary metric: 外部测试集患者级 AUROC（模型 vs 医生，非劣效界值 0.05）
- Secondary metrics: 灵敏度 / 特异度（Youden 阈值 + 预设高灵敏度阈值）、AUPRC、病灶级检出率（按大小分层）
- Calibration: 校准曲线、Brier score、ECE
- Clinical utility: DCA（阈值概率 5–40%）
- Comparison: 2 名医生独立阅片（AI alone vs human alone vs AI-assisted，第二轮洗脱期 8 周）
- Statistical analysis: DeLong 比较 AUROC；Bootstrap 2,000 次 CI；详细 → `analysis-plan.md`
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
- STARD 2015 item 5–9（参与者、检查、参考标准）→ §2、§4、§5；item 12–13（阈值、缺失数据）→ §7、`analysis-plan.md`；item 19–25（结果）→ manuscript Results
- CLAIM 2024 数据 / Ground truth / 划分 / 模型 / 评估 → §2–§7；可复现性 → §9
- TRIPOD+AI 2024 模型开发与验证条目 → §6–§8；fairness → §7
