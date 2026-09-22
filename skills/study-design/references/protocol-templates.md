# Protocol Templates — `study-protocol.md`

Fill-in skeletons for the single protocol file produced by `study-design`. All five study types
write the **same file name** `study-protocol.md`; the `type:` field in the header tells downstream
skills (`research-ethics`, `data-analysis-planning`, `data-collection-tools`, `manuscript-writing`)
which sections to expect. Router logic and judgment criteria stay in `SKILL.md` and
`references/modules/*.md`; this file holds only the skeletons.

Common header for every type:

```markdown
# Study Protocol
type: clinical | basic | ai-ml | qualitative | survey
title: [研究标题]
version: 1.0 — [日期]
research_question: [来自 research-question.md 的一句话]
registration: [注册平台 + 注册号 / 计划注册日期 / N/A 及理由]
status: draft → confirmed（Hard Checkpoint 通过后改为 confirmed，并记录日期）
```

---

## A. Clinical — `type: clinical`（章节对照 SPIRIT 2025）

```markdown
# Study Protocol
type: clinical
title: [标题]
version: 1.0 — [日期]
research_question: [一句话]
registration: [ClinicalTrials.gov / ChiCTR 注册号，或"首例入组前注册（计划日期）"]
status: draft

## 1. 研究概要
- Design: [RCT 平行组 / 交叉 / 非劣效 / 群随机 / 前瞻性队列 / 回顾性队列 / 病例对照 / 横断面 / 诊断准确性 / 预测模型 / RWE]
- Framework: [优效 / 非劣效（Δ = [值]，依据 [来源]）/ 等效 / 关联 / 准确性]
- Setting: [单中心 / 多中心，机构名称]
- Reporting standard: [CONSORT 2025 / STROBE / STARD 2015 / TRIPOD+AI 2024 / RECORD …]

## 2. 研究对象
- Population: [目标人群]
- Inclusion criteria: [逐条，具体可操作]
- Exclusion criteria: [逐条]
- Recruitment: [来源、方式、时间窗]
- Withdrawal / discontinuation rules: [何时退出，退出后数据如何处理]

## 3. 干预与对照（干预性研究必填；观察性研究改为"暴露与比较"）
- Intervention: [名称、剂量/强度、频率、疗程、实施者、依从性监测]（按 TIDieR 写全）
- Comparator: [安慰剂 / 标准治疗 / 空白 / 阳性对照；为何选这个对照]
- Concomitant care: [允许 / 禁止的伴随治疗]
- 观察性研究：Exposure definition [定义、测量、时间窗] / Comparison group [定义]

## 4. 随机化、分配隐藏与盲法（干预性研究必填）
- Sequence generation: [方法（计算机随机 / 区组 / 分层，区组长度）]
- Allocation concealment: [中心化随机系统 / 密封不透光信封 / …]
- Implementation: [谁生成序列、谁入组、谁分配]
- Blinding: [谁被盲（受试者 / 实施者 / 结局评估者 / 统计师）；无法盲时的替代（评估者盲、客观结局）]
- Emergency unblinding: [条件与流程]

## 5. 结局指标与评估时点
- Primary outcome: [指标名 / 定义 / 测量工具 / 评估时点 / 分析指标（如 12 周时的组间均值差）]（只有一个）
- Secondary outcomes: [逐条，同样写全定义与时点]
- Safety / harms outcomes: [不良事件定义、分级标准、收集方式]
- Assessment schedule: [表：基线 / 干预期 / 随访各时点 × 各评估项]

## 6. 样本量计算（MANDATORY）
- Tool: `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py` 或 G*Power
- Effect size: [值 + 来源（文献 PMID / 预实验）]
- α = [0.05 双侧 / 0.025 单侧（非劣效）], power = [0.80 / 0.90]
- Allocation ratio: [1:1 / …]; 生存结局写所需事件数
- Dropout: [X]% → 最终样本量 N = [ ]（每组 [ ]）
- 观察性研究：说明估计的效应量 / 事件数与可用样本是否匹配

## 7. 随访计划
- Follow-up duration: [总时长]; visit schedule: [时点]
- Retention strategies: [提醒、交通补贴、多渠道联系]
- Loss to follow-up handling: [预设的缺失数据策略；详细方法在 SAP]

## 8. 变量定义
- 自变量 / 暴露、因变量 / 结局、混杂变量、协变量——每个都写定义、测量方式、单位、测量时点
- 数据字典由 `data-collection-tools` 据此生成

## 9. 数据收集与质控
- Sources: [EMR / 量表 / 检验 / 影像 / 访视]
- Instruments: [CRF / REDCap / …]
- Quality control: [双录入、范围核查、监查计划]
- Data management: [存储、去标识化、访问权限]

## 10. 统计分析概要（详细 SAP → `data-analysis-planning`）
- Analysis populations: [ITT / mITT / PP；非劣效试验 ITT 与 PP 都报告]
- Primary analysis: [方法一句话]
- Interim analyses / stopping rules: [如有]
- Subgroup / sensitivity analyses: [预设列表]

## 11. 伦理与注册（详细核对 → `research-ethics`）
- Ethics approval: [机构 / 批准号 / 待批]
- Informed consent: [书面 / 电子 / 豁免及理由]
- Registration: [平台 + 号；干预性研究首例入组前]
- Data sharing statement: [计划]

## 12. 时间线与分工
- Milestones: [伦理 → 注册 → 招募 → 随访结束 → 分析 → 投稿]
- Roles: [PI / 统计 / 数据管理 / 结局评估者]
```

---

## B. Basic Science — `type: basic`

```markdown
# Study Protocol
type: basic
title: [标题]
version: 1.0 — [日期]
research_question: [一句话；写清假设的分子/细胞机制]
registration: N/A（动物实验写 IACUC 批准号）
status: draft

## 1. 研究概要
- Hypothesis: [H1；预期方向]
- Model system: [细胞系（来源、STR 鉴定、传代范围）/ 动物（物种、品系、性别、周龄）/ 临床样本]
- Overall design: [体外 → 功能验证 → 体内 → 临床样本验证，计划做到验证层级第 [X] 层]

## 2. 实验设计（每个实验一节；模板见 references/experiment-templates/）
### Experiment 1: [名称，如 WB 检测 X 蛋白表达]
- Purpose: [验证什么]
- Groups: [处理组 / 阴性对照 / 阳性对照 / 载体对照 / 特殊对照（同型、回补）]
- Biological replicates: n = [≥3]（定义：[独立传代 / 独立个体]）; technical replicates: [≥2]
- Readout: [指标、定量方法、单位]
- Blinding: [谁对分组不知情]
- Randomization: [方法]
### Experiment 2: …

## 3. 动物实验（如适用，按 ARRIVE 2.0）
- Species / strain / sex / age / weight / source / housing: [ ]
- Sample size: [效应量来源、α、power、脱落率 → 每组 n]（`${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py` 或 G*Power）
- Randomization & blinding: [分组方法；给药者 / 评估者盲]
- Humane endpoints / anesthesia / analgesia / euthanasia: [ ]
- IACUC approval: [批准号 / 待批]

## 4. 样本量与重复方案
- 每个实验的生物学重复数及依据（power / 文献先例 / 预实验后重算）
- 排除标准：[数据点排除的预设规则，如污染、失败的对照]

## 5. 数据记录与图表要求
- 原始数据保存：[全膜图 / 原始图像 / 仪器导出文件]
- 图表：展示个体数据点；比例尺；门控策略；"representative of n=X"
- 统计：[方法概要；详细 → `data-analysis-planning`]

## 6. 试剂与关键材料
- 抗体（公司、货号、克隆号、稀释比）、引物序列、细胞系来源、动物来源许可证号

## 7. 伦理与生物安全
- IACUC / IRB（临床样本）批准；人类遗传资源相关审批（如涉及中国人类遗传资源采集/出境/国际合作）
- 生物安全等级、废弃物处理

## 8. 时间线
- [预实验 → 正式实验 → 验证实验 → 投稿]
```

---

## C. AI/ML — `type: ai-ml`

```markdown
# Study Protocol
type: ai-ml
title: [标题]
version: 1.0 — [日期]
research_question: [一句话；PIRD 或 PICO]
registration: [诊断准确性 / 预测模型研究建议注册（ClinicalTrials.gov / ChiCTR / OSF）；AI RCT 必须注册]
status: draft

## 1. 研究概要
- Study type: [开发+验证 / 外部验证 / 诊断准确性评估 / LLM-VLM benchmark / AI RCT / DECIDE-AI 早期评估 / 数据集构建]
- Task: [分类 / 检测 / 分割 / 回归 / 风险预测 / 生成式问答]
- Intended use: [使用场景、目标用户、在临床流程中的位置]
- Reporting standard: [TRIPOD+AI 2024 / CLAIM 2024 / STARD 2015 / DECIDE-AI 2022 / CONSORT-AI 2020 / TRIPOD-LLM]

## 2. 数据集来源与纳排
- Sources: [中心 / 数据库 / 公开数据集名称与版本]
- Time window: [ ]
- Inclusion / exclusion: [患者级 + 数据级（如图像质量）]
- Data volume: [患者数 / 样本数 / 类别分布]
- De-identification: [方式]；数据使用许可 / 伦理批准范围（二次使用需在批准范围内）

## 3. 患者级数据划分
- Strategy: [按 `${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/stat-method-decision-tree.yaml` 的 `deep_learning_training.data_split` 分档：hold-out / 5-fold CV / 迁移学习 + nested CV / LOOCV]
- Unit of split: 患者 ID（同一患者所有数据同一集合 / 同一折）
- Stratification: [按类别 / 中心]
- Split seed: [固定值]；划分脚本由 `data-collection-tools` 生成

## 4. 标注流程与一致性
- Annotators: [人数、资历、年资]
- Protocol: [标注指南版本、培训、盲法（不看模型输出）]
- Agreement: [Cohen's / Fleiss' kappa / ICC，目标阈值]
- Adjudication: [共识讨论 / 多数投票 / 专家裁决]

## 5. Ground Truth 定义
- Reference standard: [病理 / 随访结局 / 专家共识 / 已验证量表]
- Timing relative to index data: [ ]
- Known limitations of the reference: [ ]

## 6. 模型与训练
- Architecture / baseline models: [ ]
- Pretraining / transfer learning: [数据集、权重来源]
- Hyperparameters to report: optimizer, learning rate, schedule, batch size, epochs, early stopping, regularization
- Data augmentation: [类型、参数范围、概率；测试集不增强]
- Class imbalance handling: [方法与理由]

## 7. 评估指标与校准 / DCA
- Primary metric: [按 references/metrics-and-reporting.yaml 的任务类型选]
- Secondary metrics: [ ]
- Calibration: [校准曲线、Brier、ECE]（概率输出模型必填）
- Clinical utility: [DCA]（临床预测模型必填）
- Comparison: [vs 现有模型 / vs 人类专家（AI alone / human alone / AI-assisted）]
- Statistical analysis: [Bootstrap CI、DeLong、配对检验；详细 → `data-analysis-planning`]
- Subgroup / fairness: [按性别、年龄、中心分层]

## 8. 外部验证计划
- External cohort: [来源、时间、中心；与开发集的差异]
- Timing: [同期 / 后续研究]；无外部验证时写明理由并列入 Limitations
- Success criteria: [预设的性能下限]

## 9. 可复现性
- Seed: [固定值]; environment: [requirements.txt / Docker]; hardware: [ ]
- Code & weights: [GitHub + Zenodo DOI / 推理 API]
- Data availability statement: [ ]

## 10. Prompt 标准化（LLM / VLM 研究必填）
- Models & versions: [名称、版本号、访问日期、API / 本地]
- Prompts: [每个任务的完整 prompt；简洁 / 标准 / 详细三种变体用于敏感性分析]
- Inference parameters: temperature = [ ], max_tokens = [ ], seed = [ ], repeats = [ ]
- Output parsing: [MCQ 抽取规则 / 开放题评分量表与评分者]
- Contamination check: [测试集是否可能在训练语料中]

## 11. 可解释性与安全
- Explainability method: [Grad-CAM / SHAP / …]; case selection: typical / best / worst
- Failure mode analysis: [错误分类体系]
- Human-AI interaction & safety monitoring（DECIDE-AI 场景）: [ ]

## 12. 伦理与数据治理（详细核对 → `research-ethics`）
- Ethics approval: [批准号；二次使用数据是否在批准范围内]
- Consent / waiver: [ ]
- Data transfer: [跨境 / 云平台限制；禁止上传可识别数据到外部 AI 平台]

## 13. 报告规范映射
- [规范名] → [protocol 中对应章节] （逐条映射，投稿前由 `reporting-standards` 检查）
```

---

## D. Qualitative — `type: qualitative`

```markdown
# Study Protocol
type: qualitative
title: [标题]
version: 1.0 — [日期]
research_question: [描述性/解释性问题，不是假设检验]
registration: N/A（或 OSF 预注册）
status: draft

## Methodology
[选择的方法论及理由]

## Philosophical Stance
[范式及认识论立场；研究者立场声明（reflexivity）]

## Participants
- Target population: [描述]
- Sampling strategy: [目的性抽样类型]
- Estimated sample size: [范围] (until saturation; 饱和判断方式: [ ])
- Inclusion/exclusion criteria: [列表]
- Recruitment method: [描述]

## Data Collection
- Method: [访谈/焦点小组/观察/...]
- Interview guide / Discussion guide: [附录]
- Duration: [预计时长]
- Recording: [音频/视频/笔记]
- Transcription: [逐字/摘要]

## Data Analysis
- Method: [反思性主题分析 / 编码本式主题分析 / 框架分析 / 扎根理论 / IPA / 内容分析]
- Coding approach: [归纳/演绎/混合]
- Software: [NVivo/ATLAS.ti/...]
- Coding quality: [编码本式/内容分析 → 编码者数 + 一致性方法；反思性主题分析/IPA → 反思日志 + 审计轨迹 + 同行 debriefing]

## Trustworthiness
- Credibility: [成员检核/三角验证/...]
- Transferability: [厚描述]
- Dependability: [审计轨迹]
- Confirmability: [反思日志]

## Ethics
- Informed consent process（含录音同意）
- Confidentiality and anonymization
- IRB approval: [pending]

## Reporting Standard
- [COREQ (interviews/focus groups) / SRQR (alternative)]
```

---

## E. Survey — `type: survey`

```markdown
# Study Protocol
type: survey
title: [标题]
version: 1.0 — [日期]
research_question: [描述性问题]
registration: N/A（或 OSF 预注册）
status: draft

## Survey Type
[Cross-sectional / Questionnaire development / Validation / Delphi]

## Questionnaire
- Name: [量表名称]
- Dimensions: [维度列表]
- Items: [条目数]
- Response format: [Likert 5/7 点 / 二分类 / VAS / ...]
- Development process: [新开发流程 / 已有量表引用 / 翻译与回译]

## Target Population
[描述]

## Sampling
- Strategy: [抽样方法]
- Inclusion/exclusion criteria
- Sample size: [N] (计算依据: [公式和参数，见 references/survey-reference.yaml])
- Expected response rate: [%]

## Psychometric Properties (if validation)
- Content validity: [方法]
- Construct validity: [EFA → CFA，分样本]
- Reliability: [Cronbach's alpha, test-retest ICC]

## Delphi (if applicable)
- Expert panel: [人数、资格标准]
- Rounds: [计划轮数，最多 4]
- Consensus criteria（预先定义）: [同意率 / IQR / 中位数]
- Stopping rule: [ ]

## Data Collection
- Method: [在线/纸质/混合]
- Platform: [REDCap/问卷星/...]
- Period: [时间范围]
- Reminders: [策略]

## Analysis Plan
- Descriptive: 频数(%)、均值±SD
- Factor analysis: EFA (principal axis, oblimin rotation) → CFA
- Reliability: Cronbach's alpha, ICC
- Group comparisons: [如适用；详细 → `data-analysis-planning`]

## Ethics
- IRB approval: [pending]
- Informed consent: [在线同意/纸质签名]
- Anonymity: [匿名/保密]

## Reporting Standard
- [CHERRIES (web-based) / CROSS (survey methods) / STROBE (cross-sectional) / COSMIN (validation)]
```
