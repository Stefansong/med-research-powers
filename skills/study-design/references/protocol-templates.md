# Protocol Templates — `study-protocol.md`

> **本模板是必须覆盖的章节清单，不是填空表：按本研究的实际情况写；不适用的章节写"不适用 + 理由"；禁止照抄示例中的数字、例数和措辞。**
> 方括号里的内容是"这一项要写什么"的提示，不是可直接采用的默认值；数字一律来自本研究的真实条件（SKILL.md Step 0）和样本量计算（Step 3）。

Section checklists for the single protocol file produced by `study-design`. All five study types
write the **same file name** `study-protocol.md`; the `type:` field in the header tells downstream
skills (`research-ethics`, `data-analysis-planning`, `data-collection-tools`, `manuscript-writing`)
which sections to expect. Router logic and judgment criteria stay in `SKILL.md` and
`references/modules/*.md`; this file holds only the section checklists.

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

Every type then starts with the same section, written from SKILL.md Step 0:

```markdown
## 0. 真实条件与设计理由
- 真实条件：[逐项写 Step 0 的结果——研究目的；数据来源（回顾性已有 / 前瞻性新收集，哪个系统、哪些年份）；
  每年可获得的病例数与预计事件数、同一患者是否有多条记录；中心数；随访可行性；资源与时间；伦理 / 注册限制；已有研究的结论（出处）]
- 未知项：[还不知道的条件 → 需要谁提供 → 会影响哪个设计决定]
- 设计选择：[选了什么设计、关键参数怎么定的]
- 理由：[依据上面哪几条真实条件；为什么没选更强的设计（如为什么不做 RCT / 前瞻性研究）]
```

---

## A. Clinical — `type: clinical`（章节对照 SPIRIT 2025）

SPIRIT 2025 只针对随机试验的 protocol（34 项、含子项共 53 行，本地清单 `${CLAUDE_PLUGIN_ROOT}/skills/reporting-standards/references/checklists/spirit-2025.yaml`）。下面每一行末尾的（SPIRIT 编号）指它对应的条目，53 行每行都有位置。观察性研究按同一结构写，只适用于试验的条目（随机化、盲法、DMC、试验监查等）写"不适用 + 理由"。

```markdown
# Study Protocol
type: clinical
title: [标题：写明设计、人群和干预，并标明是研究方案（protocol）]（SPIRIT 1a）
version: 1.0 — [日期]（版本号 + 日期，SPIRIT 2）
research_question: [一句话]
registration: [注册平台 + 注册号（含 URL）+ 注册日期；尚未注册写拟注册的平台]（SPIRIT 4）
status: draft

## 0. 真实条件与设计理由（见上方通用节）

## 1. 研究概要
- Structured summary: [设计与方法的结构化摘要，包含 WHO 试验注册数据集（WHO Trial Registration Data Set）的条目]（SPIRIT 1b）
- Background and rationale: [科学背景与依据，总结已发表和未发表研究中各干预的获益与危害]（SPIRIT 9a）；为什么选这个对照（SPIRIT 9b）
- Objectives: [与获益和危害相关的具体目标]（SPIRIT 10）
- Design: [RCT 平行组 / 交叉 / 非劣效 / 群随机 / 前瞻性队列 / 回顾性队列 / 病例对照 / 横断面 / 诊断准确性 / 预测模型 / RWE]；分配比例 [ ]；Framework: [优效 / 非劣效（Δ = [值]，依据 [来源]）/ 等效 / 探索性 / 关联 / 准确性]（SPIRIT 12）
- Setting: [场景（社区 / 医院）与地点（国家、中心名称）；单中心 / 多中心]（SPIRIT 13）
- Patient and public involvement: [患者与公众参与试验设计、实施和报告的具体做法或计划；没有就写"没有"并说明理由]（SPIRIT 11）
- Reporting standard: [CONSORT 2025 / STROBE / STARD 2015 / TRIPOD+AI 2024 / RECORD …]

## 2. 研究对象
- Population: [目标人群]
- Inclusion / exclusion criteria: [逐条，具体可操作]（SPIRIT 14a）
- Sites and intervention providers: [如适用：中心的入选标准，实施干预者（如外科医生、康复治疗师）的资质要求]（SPIRIT 14b）
- Recruitment: [来源、方式、时间窗；保证达到目标样本量的招募策略]（SPIRIT 20）

## 3. 干预与对照（干预性研究必填；观察性研究改为"暴露与比较"）
- Intervention and comparator: [名称、剂量/强度、频率、疗程；如何、何时、由谁实施；干预手册等材料在哪里获取]（SPIRIT 15a，按 TIDieR 写全）
- Comparator: [安慰剂 / 标准治疗 / 空白 / 阳性对照；选择理由写在第 1 节]
- Discontinuing or modifying the allocated intervention: [何时停止或调整（如因不良反应减量、受试者要求、病情好转 / 恶化）]（SPIRIT 15b）
- Adherence: [提高依从性的措施与监测方法（如药片回收、到课记录）]（SPIRIT 15c）
- Concomitant care: [允许 / 禁止的伴随治疗]（SPIRIT 15d）
- 观察性研究：Exposure definition [定义、测量、时间窗] / Comparison group [定义]

## 4. 随机化、分配隐藏与盲法（干预性研究必填）
- Sequence generation: [谁生成、用什么方法（计算机随机 …）]（SPIRIT 21a）；[简单随机还是限制性随机（区组 / 分层）、分层因素（如"按中心分层，区组长度随机可变"）]。**随机种子和具体区组长度不写进本 protocol**：它们记在单独的文件里，由负责分配的人保管在项目文件夹以外（`randomization.py` 拒绝写进项目文件夹），入组和分配干预的人看不到——知道种子和区组设置的人可以重新生成整张分配表（SPIRIT 21b）
- Allocation concealment: [中心化随机系统 / 按顺序编号、不透光的密封信封 / …；分配前如何隐藏序列]（SPIRIT 22）
- Implementation: [负责入组和负责分配的人能否接触分配序列]（SPIRIT 23）
- Blinding: [分配后谁被盲（受试者 / 实施者 / 结局评估者 / 数据分析者）；无法盲时的替代（评估者盲、客观结局）]（SPIRIT 24a）；[如何实现盲法，各干预外观等是否相似]（SPIRIT 24b）
- Emergency unblinding: [允许揭盲的情形与流程]（SPIRIT 24c）

## 5. 结局指标与评估时点
- Primary outcome: [测量变量（如收缩压）/ 分析指标（较基线变化、终值、至事件时间）/ 汇总方式（均值、中位数、比例）/ 评估时点]（只有一个；SPIRIT 16）
- Secondary outcomes: [逐条，同样写全以上四项]（SPIRIT 16）
- Harms: [不良事件如何定义、如何评估（系统收集 / 非系统收集）、分级标准]（SPIRIT 17）
- Participant timeline: [入组、干预（含导入期、洗脱期）、各项评估与访视的时间表；附 SPIRIT 2025 图 1 式的时间表图]（SPIRIT 18）

## 6. 样本量计算（MANDATORY；SPIRIT 19）
- Tool: `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py`（能算哪些设计看 `--help`）或 G*Power；群随机、交叉、重复测量等脚本不覆盖的设计用专门方法，并写明方法与出处
- Effect size / event rate: [值 + 出处：相近人群文献（PMID）/ 本中心预实验或历史数据（时间段、例数）/ 临床最小重要差异（依据）；"常用值"不算出处]
- α、power: [按设计选择并写理由（优效通常双侧；非劣效 / 等效为单侧，常用 0.025）]；非劣效 / 等效试验用 `power_analysis.py --hypothesis non-inferiority|equivalence --margin <Δ>`（单侧 α 默认 0.025；生存结局的非劣效脚本不覆盖）
- Allocation ratio: [按设计与理由]; 生存结局写所需事件数；群随机写 ICC（出处）、平均群大小与群大小的变异系数
- Dropout: [预计比例 + 依据（本中心既往随访或文献）] → 最终样本量 N = [按 Step 3 的计算结果填写]（每组 [ ]）
- Feasibility: [用 Step 0 的每年可获得例数 / 事件数核对：计划期内能否达到；不能达到时的调整]
- 观察性研究：说明估计的效应量 / 事件数与可用样本是否匹配

## 7. 随访计划
- Follow-up duration: [总时长]; visit schedule: [时点]
- Retention and complete follow-up: [提醒、交通补贴、多渠道联系；中止或偏离干预的受试者仍收集哪些结局数据]（SPIRIT 25b）
- Withdrawal: [何时退出，退出后已收集的数据如何处理]

## 8. 变量定义
- 自变量 / 暴露、因变量 / 结局、混杂变量、协变量——每个都写定义、测量方式、单位、测量时点
- 数据字典由 `data-collection-tools` 据此生成

## 9. 数据收集、管理与保密
- Data collection: [来源（EMR / 量表 / 检验 / 影像 / 访视）；保证数据质量的做法（重复测量、评估者培训）；测量工具及其已知信效度；CRF 在哪里获取]（SPIRIT 25a）
- Data management: [录入、编码、安全与存储；双录入、范围核查；数据管理细则在哪里获取]（SPIRIT 26）
- Confidentiality: [潜在与已入组受试者的个人信息在试验前、中、后如何收集、共享和保存]（SPIRIT 33）

## 10. 统计分析概要（详细 SAP → `data-analysis-planning`）
- Methods: [主要与次要结局（含危害）的组间比较方法，一句话]（SPIRIT 27a）
- Analysis populations: [每个分析纳入谁、按哪一组分析（ITT / mITT / PP；非劣效试验 ITT 与 PP 都报告）]（SPIRIT 27b）
- Missing data: [预设的处理方法；详细方法在 SAP]（SPIRIT 27c）
- Additional analyses: [预设的亚组 / 敏感性分析]（SPIRIT 27d）

## 11. 监查（干预性研究）
- Data monitoring committee: [组成、职责与汇报关系、是否独立于申办方和资助方、利益冲突、章程在哪里获取；不设 DMC 时写理由]（SPIRIT 28a）
- Interim analyses and stopping guidelines: [期中分析与停止规则；谁能看期中结果、谁做终止决定]（SPIRIT 28b）
- Trial monitoring: [监查的频率与流程；不做监查时写理由]（SPIRIT 29）

## 12. 伦理与注册（详细核对 → `research-ethics`）
- Ethics approval: [向哪个伦理委员会 / IRB 申请、何时申请；批准号或"待批"]（SPIRIT 30）
- Protocol amendments: [重要修改如何通知伦理委员会、注册平台、研究者和受试者]（SPIRIT 31）
- Informed consent: [谁、如何向受试者或其代理人获取知情同意 / 赞同（书面 / 电子 / 豁免及理由）]（SPIRIT 32a）；[附属研究使用数据和生物样本的额外同意，如适用]（SPIRIT 32b）
- Ancillary and post-trial care: [附加治疗与试验后照护；受试者因参加试验受到伤害时的补偿]（SPIRIT 34）
- Registration: [见文件头；干预性研究首例入组前注册]

## 13. 开放科学、资助与分工
- Protocol and SAP access: [protocol 和统计分析计划在哪里可以获取]（SPIRIT 5）
- Data sharing: [去标识的个体数据（含数据字典）、统计代码和其他材料在哪里、如何获取]（SPIRIT 6）
- Funding: [资金来源与其他支持（如药品供应）]（SPIRIT 7a）
- Conflicts of interest: [主要研究者与指导委员会成员的经济及其他利益冲突]（SPIRIT 7b）
- Dissemination: [向受试者、医务人员、公众传达结果的计划（注册平台报告、通俗摘要、发表）]（SPIRIT 8）
- Roles: [protocol 贡献者的姓名、单位与角色]（SPIRIT 3a）；[申办方名称与联系方式]（SPIRIT 3b）；[申办方与资助方在设计、实施、分析和报告中的角色与权限]（SPIRIT 3c）；[协调中心、指导委员会、终点裁定委员会、数据管理团队等的组成与职责，如适用]（SPIRIT 3d）

## 14. 时间线
- Milestones: [伦理 → 注册 → 招募 → 随访结束 → 分析 → 投稿]
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

## 0. 真实条件与设计理由（见上方通用节；"病例"换成样本 / 动物 / 细胞来源）

## 1. 研究概要
- Hypothesis: [H1；预期方向]
- Model system: [细胞系（来源、STR 鉴定、传代范围）/ 动物（物种、品系、性别、周龄）/ 临床样本]
- Overall design: [体外 → 功能验证 → 体内 → 临床样本验证，计划做到验证层级第 [X] 层]

## 2. 实验设计（每个实验一节；模板见 references/experiment-templates/）
### Experiment 1: [名称，如 WB 检测 X 蛋白表达]
- Purpose: [验证什么]
- Groups: [处理组 / 阴性对照 / 阳性对照 / 载体对照 / 特殊对照（同型、回补）]
- Biological replicates: n = [按第 4 节的依据填写；不少于 3]（定义：[独立传代 / 独立个体]）; technical replicates: [≥2]
- Readout: [指标、定量方法、单位]
- Blinding: [谁对分组不知情]
- Randomization: [方法]
### Experiment 2: …

## 3. 动物实验（如适用，按 ARRIVE 2.0；Essential 10 与实验单位的判定见 references/experiment-templates/animal-study.md）
- Species / strain / sex / age / weight / source: [ ]
- Experimental unit（先定它，再算样本量和分组；ARRIVE 2.0 第 1b 条）: [单只动物 / 笼 / 窝 + 理由：处理逐只给、同笼动物可分到不同组 → 单只动物；处理加在饲料 / 饮水 / 笼内环境或整笼处理 → 笼；处理给孕鼠 / 母鼠、看子代 → 窝]
- Housing & cage allocation（ARRIVE 2.0 第 15 条：饲养条件）: [饲养条件：设施级别（SPF / 普通级）、温湿度、光照周期、垫料、饲料与饮水（自由采食 / 限饲）、环境丰富化；每笼只数；混笼（笼作区组）还是整笼分组及理由——处理可能经笼互相影响时不能混笼；分析如何处理笼（随机效应 / 区组；笼为单位时按笼汇总）]
- Sample size（ARRIVE 2.0 第 2a、2b 条）: [主要结局、效应量来源、α、power、脱落率 → 每组实验单位数（笼为单位时是笼数）与总动物数]（`${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py`（只覆盖个体随机的常规设计，范围见 `--help`）或 G*Power；以笼 / 窝为单位、笼内再测多只时要考虑笼内相关）
- Randomization & blinding: [随机分配的对象是实验单位；分组方法；给药者 / 评估者盲]
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

## 0. 真实条件与设计理由（见上方通用节；另写清可用数据量、标注人力与算力）

## 1. 研究概要
- Study type: [开发+验证 / 外部验证 / 诊断准确性评估 / LLM-VLM benchmark / AI RCT / DECIDE-AI 早期评估 / 数据集构建]
- Task: [分类 / 检测 / 分割 / 回归 / 风险预测 / 生成式问答]
- Intended use: [使用场景、目标用户、在临床流程中的位置]
- Reporting standard: [TRIPOD+AI 2024 / CLAIM 2024 / STARD 2015（AI 指标检查另加 STARD-AI 2025，无本地清单）/ DECIDE-AI 2022 / CONSORT-AI 2020 / TRIPOD-LLM]

## 2. 数据集来源、纳排与样本量
- Sources: [中心 / 数据库 / 公开数据集名称与版本]
- Time window: [ ]
- Inclusion / exclusion: [患者级 + 数据级（如图像质量）]；纳入方式: [连续 / 随机 / 方便样本]
- Data volume: [患者数 / 样本数 / 类别分布]
- Sample size（MANDATORY，按研究类型选依据；第 3 节的验证方式不能代替样本量依据）:
  - 风险预测模型开发：Riley 方法（`pmsampsize`：候选参数数、结局发生率、预期 R² 或既往 C 统计量）
  - 外部验证集 / 测试集：按 Riley 的外部验证样本量方法，看 C 统计量、校准斜率、O/E 的 95% CI 能估多窄（`pmvalsampsize`；Riley 2021，doi:10.1002/sim.9025）；数据量已固定时，写出它能达到的精度，达不到目标的指标在 Limitations 里说明
  - 诊断准确性：按预期灵敏度/特异度和可接受的 95% CI 宽度，先算需要的有病、无病人数，再按患病率换算总人数（Buderer 1996；`power_analysis.py` 的 diagnostic 模式）
  - 读片者研究（AI vs 医生组、AI 辅助 vs 不辅助）：MRMC 样本量——读者数 × 病例数，方差参数来自预实验或同类研究，写明来源
  - 做法和 R / Python 包见 `${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/method-cards/` 的 `regression-and-prediction-models.md`、`diagnostic-accuracy-and-ai-evaluation.md`
  - [所用方法 + 每个输入值及出处 → 所需人数 / 事件数；与可获得的数据量对照]
- De-identification: [方式]；数据使用许可 / 伦理批准范围（二次使用需在批准范围内）

## 3. 验证方式与患者级数据划分
- Strategy: [规则只在 `${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/stat-method-decision-tree.yaml` 的 `deep_learning_training.data_split` 维护。按**模型类型**和**有效样本量**（按患者计的事件数 / 较少一类的人数）选，不看总人数：
  - 回归类及其他经典临床预测模型（logistic、Cox、惩罚回归）→ 用全部数据建模，内部验证用 bootstrap 乐观校正（每次重做全部建模步骤）或重复 k 折交叉验证，不做随机 hold-out
  - 要调超参数的 ML / 深度学习模型 → 嵌套交叉验证（内层调参、外层估计性能）；只有每个集合的事件数都够时才用按患者的训练 / 验证 / 测试划分，测试集按外部验证的样本量方法（第 2 节）核算 C 统计量和校准的精度
  - 外部 / 时间验证（另一中心或另一时间段）优于任何随机划分；声称模型可推广时必须有]
- Patients and events per set / fold: [每个集合 / 每折的患者数与事件数]
- Unit of split: 患者 ID（同一患者所有数据同一集合 / 同一折）
- Stratification: 按结局分层（多中心时可再按中心）
- Split seed: [固定值]；划分脚本由 `data-collection-tools` 生成（`patient_level_split.py`，含泄漏检查）

## 4. 标注流程与一致性
- Annotators: [人数、资历、年资]
- Protocol: [标注指南版本、培训、盲法（不看模型输出）]
- Agreement: [Cohen's / Fleiss' kappa / ICC，目标阈值及依据]
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
- Class imbalance handling: [方法与理由。类别加权、过采样 / 欠采样会让预测概率偏离真实风险（校准变差）：模型要输出风险概率时，优先不做纠正、改调决策阈值；若做了，必须在未重采样、未加权的数据上重新校准，并报告重新校准后的校准（van den Goorbergh 2022，doi:10.1093/jamia/ocac093）]

## 7. 评估指标与校准 / DCA
- Primary metric: [按 references/metrics-and-reporting.yaml 的任务类型选]
- Secondary metrics: [ ]
- Calibration: [calibration-in-the-large（校准截距）、校准斜率、平滑校准曲线、Brier；ECE 只作补充]（概率输出模型必填；生存结局在预先定的时间点上做）
- Clinical utility: [DCA]（临床预测模型必填）
- Comparison: [vs 现有模型 / vs 人类专家（AI alone / human alone / AI-assisted）；与医生比较时写读者人数、年资、是否全交叉，分析用 MRMC 方法（读者和病例都作随机效应）]
- Statistical analysis: [Bootstrap CI、DeLong、配对检验；详细 → `data-analysis-planning`]
- Subgroup / fairness: [按性别、年龄、中心分层]

## 8. 外部验证计划
- External cohort: [来源、时间、中心；与开发集的差异]
- Timing: [同期 / 后续研究]；无外部验证时写明理由并列入 Limitations
- Success criteria: [预设的性能下限及依据（如现有工具或专家的已报道水平，写出处）]

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
- Consent / waiver: [书面知情同意，或伦理委员会批准免除知情同意并写明满足的每一项条件（research-ethics checklist §3）]
- Data transfer: [数据存放与访问；是否出境（含云服务 / AI API 所在地）及出境途径；外部 AI 服务：默认只用匿名化数据或汇总结果，去标识化的患者级数据须满足 research-ethics checklist §4 的全部条件]

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

## 真实条件与设计理由（见上方通用节；"病例"换成能接触到的受访者与访谈资源）

## Methodology
[选择的方法论及理由]

## Philosophical Stance
[范式及认识论立场；研究者立场声明（reflexivity）]

## Participants
- Target population: [描述]
- Sampling strategy: [目的性抽样类型]
- Estimated sample size: [按本研究问题的宽窄、受访者同质程度和访谈深度估计的范围 + 理由] (until saturation; 饱和判断方式: [ ])
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

## 真实条件与设计理由（见上方通用节；"病例"换成可触达的目标人群、抽样框与发放渠道）

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
- Sample size: [按 Step 3 的计算结果填写] (计算依据: [公式和参数，见 references/survey-reference.yaml；预期比例 / 精度的出处；整群抽样乘设计效应，ICC 写出处])
- Expected response rate: [预计比例 + 依据（同类调查文献或预调查）]

## Psychometric Properties (if validation)
- Content validity: [方法]
- Construct validity: [EFA → CFA，分样本]
- Reliability: [Cronbach's alpha（每个单维分量表）, test-retest ICC]
- Criteria: [判定标准与出处（COSMIN，见 references/survey-reference.yaml 的 `psychometric_properties`）]

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
- Descriptive: [按变量类型与分布：频数(%) / 均值±SD / 中位数(IQR)]
- Factor analysis（量表开发 / 验证时）: [EFA 的提取与旋转方法 + 选择理由 → CFA（独立样本）]
- Reliability: [Cronbach's alpha / McDonald's omega / 重测 ICC，按研究目的选]
- Group comparisons: [如适用；详细 → `data-analysis-planning`]

## Ethics
- IRB approval: [pending]
- Informed consent: [在线同意/纸质签名]
- Anonymity: [匿名/保密]

## Reporting Standard
- [CHERRIES (web-based) / CROSS (survey methods) / STROBE (cross-sectional) / COSMIN (validation) / ACCORD（Delphi 等共识方法；无本地清单，需人工核对）]
```
