---
name: study-design
description: Use when designing any research study protocol. Triggers on "怎么设计研究"、"样本量"、"研究类型"、"写protocol"、"研究方案"、"RCT设计"、"队列设计"、"交叉试验"、"非劣效"、"适应性试验"、"真实世界"、"注册研究"、"crossover"、"non-inferiority"、"adaptive"、"real-world"、"registry"、"Western blot"、"PCR"、"ELISA"、"流式"、"免疫荧光"、"转染"、"敲除"、"动物模型"、"细胞培养"、"体外实验"、"体内实验"、"模型评估"、"benchmark"、"ground truth"、"标注"、"AUROC"、"TRIPOD-AI"、"CLAIM"、"DECIDE-AI"、"IDEAL"、"手术创新"、"器械开发"、"定性研究"、"访谈"、"焦点小组"、"扎根理论"、"现象学"、"主题分析"、"qualitative"、"interview"、"focus group"、"thematic analysis"、"grounded theory"、"mixed methods"、"问卷"、"调查研究"、"survey"、"questionnaire"、"Delphi"、"Likert"、"量表开发"、"量表验证"、"信效度"、"CHERRIES"、"共识研究".
---

# Study Design

## Overview

所有类型研究的方案设计——临床、基础、AI/ML、定性、问卷调查。根据研究问题自动路由到对应的设计模块。

## Study Type Router

**设计前必须先确定研究类型。** 不同类型有完全不同的方法学、样本量逻辑和报告规范。

```
研究问题 → 什么类型的研究？
├── 涉及患者/临床数据？ → A. Clinical Research
│     （RCT、队列、病例对照、横断面、诊断准确性、预测模型、真实世界研究）
├── 涉及细胞/动物/分子实验？ → B. Basic Science
│     （WB、PCR、流式、动物模型、基因编辑、组织病理）
├── 涉及 AI/ML 模型？ → C. AI/ML Medical Research
│     （影像 AI、手术视频 AI、预测模型、LLM 评估、智能器械）
├── 探索性/理解"为什么"？ → D. Qualitative Research
│     （访谈、焦点小组、扎根理论、现象学、混合方法）
├── 问卷/调查/共识？ → E. Survey / Questionnaire / Delphi
│     （KAP 调查、量表开发验证、Delphi 共识）
└── 不确定 → 描述研究问题，由 Router 判断
```

| 类型 | 代号 | 样本量逻辑 | 核心报告规范 |
|------|------|-----------|-------------|
| Clinical Research | `clinical` | Power analysis | CONSORT / STROBE / STARD / TRIPOD |
| Basic Science | `basic` | 生物学重复 >= 3 | ARRIVE 2.0 |
| AI/ML Medical | `ai-ml` | 数据集划分 + 外部验证 | TRIPOD-AI / CLAIM / CONSORT-AI |
| Qualitative | `qualitative` | 信息饱和 | COREQ / SRQR |
| Survey/Delphi | `survey` | 公式计算 / 专家数 | CHERRIES / STROBE / COSMIN |

## Prerequisites（通用）

- **必须**有明确的研究问题（`research-question-formulation`）
- **推荐**已有初步文献综述（`literature-synthesis`）

---

## A. Clinical Research

### 适用范围

RCT（含交叉、非劣效、适应性、平台、实效性试验）、队列、病例对照、横断面、诊断准确性、预测模型、真实世界研究、注册研究。

### 研究类型决策树

```
研究问题
├── 评估干预效果？
│     ├── 可以随机？
│     │     ├── 标准平行组 → RCT（CONSORT 2025）
│     │     ├── 每个受试者接受所有干预 → 交叉试验（Crossover）
│     │     ├── 验证不差于标准疗法 → 非劣效/等效试验
│     │     ├── 中间分析调整设计 → 适应性试验（Adaptive）
│     │     ├── 多干预共享对照 → 平台试验（Platform）
│     │     ├── 真实临床环境 → 实效性试验（Pragmatic, PRECIS-2）
│     │     └── 单个患者多次交替 → N-of-1 试验
│     └── 不能随机？ → 准实验 / 队列
├── 探索暴露-结局关系？
│     ├── 前瞻性 → 前瞻性队列（STROBE）
│     ├── 回顾性 → 回顾性队列 / 病例对照
│     ├── 嵌套在队列中 → 巢式病例对照
│     └── 横断面 → 横断面研究
├── 利用已有真实世界数据？
│     ├── 电子病历/医保数据库 → 真实世界研究（RWE, RECORD）
│     └── 疾病注册数据库 → 注册研究（Registry Study）
├── 诊断/检测准确性？ → STARD
├── 预测模型？ → TRIPOD
├── 综合证据？ → 系统综述/Meta（PRISMA）
└── 描述性？ → 病例报告/系列（CARE）
```

### 特殊试验设计要点

| 设计 | 关键差异 | 样本量 | 报告规范 |
|------|---------|--------|---------|
| **交叉试验** | 洗脱期设计、期间效应、序列效应检验 | 通常比平行组少（同一受试者做对照） | CONSORT extension for crossover |
| **非劣效试验** | 非劣效界值（Δ）确定是核心、单侧检验、PP 分析优先于 ITT | 通常比优效大（需排除Δ） | CONSORT extension for non-inferiority |
| **适应性试验** | 预设适应规则、统计方法调整（alpha spending）、独立数据监查委员会 | 分阶段计算 | CONSORT-Adaptive |
| **平台试验** | 多臂共享对照、干预可进出、Master Protocol | 按臂计算 | 无统一规范，参考 CONSORT |
| **实效性试验** | PRECIS-2 评估实效性程度、宽纳入、真实环境 | 通常较大 | CONSORT-Pragmatic |
| **真实世界研究** | 目标试验模拟（Target Trial Emulation）、混杂控制（PS/IPTW）、不朽时间偏倚 | 按效应量计算 | RECORD (STROBE extension) |
| **注册研究** | 数据完整性、随访丢失、变量定义标准化 | 通常为既有数据量 | STROBE / RECORD |

### Protocol 模板 (`study-protocol.md`)

#### 1. 研究概要
标题、研究类型、注册号（ClinicalTrials.gov / ChiCTR）

#### 2. 研究对象
纳入标准（具体可操作）、排除标准、招募方式

#### 3. 样本量计算（MANDATORY）
使用 `statistical-analysis/scripts/power_analysis.py` 或 G*Power。
必须确认：预期效应量来源（文献/预实验）、α、β、脱落率。

#### 4. 变量定义
自变量、因变量、混杂变量、协变量——每个都要有定义、测量方式、单位。

#### 5. 数据收集
时间点、方式（EMR/量表/检验/影像）、质控措施、缺失数据预案

#### 6. SAP 概要
详细 SAP → `data-analysis-planning`

#### 7. 伦理合规
→ `research-ethics`

---

## B. Basic Science (Cell / Animal / Molecular)

### 适用范围

细胞实验、动物实验、分子生物学、蛋白质实验、基因编辑、组织病理、药理学、微生物学、免疫学等基础研究。

### Core Principles

#### 1. 对照设置（不允许跳过）

每个实验必须包含：
- **阴性对照** — 证明效应不是背景噪声
- **阳性对照** — 证明系统能检测到效应
- **载体对照** — 排除溶剂/载体效应（如 DMSO）
- **特殊对照**：同型对照（抗体实验）、回补对照（基因功能研究）

#### 2. 重复设计（审稿人最常抓的问题）

| 类型 | 含义 | 论文中 n 值 | 最低要求 |
|------|------|-----------|---------|
| 生物学重复 | 独立样本/个体 | **n = 生物学重复数** | >= 3 |
| 技术重复 | 同一样本重复检测 | 不算 n | >= 2 |

**关键判断**：3 个独立传代的细胞分别做实验 = n=3; 同一批细胞分 3 个孔 = n=1

#### 3. 盲法

- 动物实验：分组、给药、评估由不同人完成
- 病理评分：评分者不知道分组
- WB 定量：先定量再查看分组
- 图像分析：自动化定量优于主观评估

#### 4. 随机化

- 动物实验：随机数表/软件分组（必须说明方法）
- 细胞板：注意边缘效应，随机化位置
- 检测顺序：随机化（避免系统误差）

### Experiment Templates

具体实验设计模板在 `references/experiment-templates/` 目录：
- `western-blot.md` — WB 设计、抗体信息、定量方法
- `qpcr.md` — qPCR 设计、引物信息、DDCt 分析
- `animal-study.md` — 动物信息、伦理、ARRIVE 2.0 要求

根据实验类型加载对应模板。

### Validation Layers

一个发现被接受通常需要多层验证：

1. 单一方法结果（最弱）
2. 不同方法验证同一结论（如 qPCR + WB）
3. 功能验证（过表达/敲除/抑制剂）
4. 体内验证（动物实验验证体外发现）
5. 临床样本验证

审稿人期望至少达到第 2-3 层。

### Figure Requirements

- WB：全膜图（越来越多期刊要求）
- 显微镜图：比例尺 + 放大倍数
- 流式图：展示门控策略
- 定量图：展示个体数据点（不只画柱状图）
- 代表性图片：标注 "representative of n=X experiments"

---

## C. AI/ML Medical Research

### 适用范围

医学影像 AI、手术视频 AI、临床预测模型、LLM/VLM 评估、数字健康、医学 NLP、智能医疗器械。

### 研究类型决策树

```
研究目标？
├── 开发新 AI 模型？
│     ├── 有临床验证？ → 开发+验证研究（TRIPOD type 2b/3）
│     └── 仅技术验证？ → 技术开发研究
├── 评估已有 AI 模型/工具？
│     ├── 诊断准确性？ → STARD-AI
│     ├── 临床效果？ → RCT（CONSORT-AI 2020）
│     ├── 多模型对比？ → Benchmark（TRIPOD-LLM）
│     ├── 可用性？ → 人因工程（混合方法）
│     └── AI 决策支持早期评估？ → DECIDE-AI 2022
├── 构建数据集/标注体系？
│     ├── 影像数据集？ → Datasheets for Datasets
│     ├── 视频标注？ → 标注一致性（Kappa/ICC）
│     └── Benchmark 集？ → Benchmark 论文
├── 开发新设备/传感器？
│     ├── 按 IDEAL 框架定位阶段
│     ├── Stage 1 原理验证 → Bench-top
│     ├── Stage 2a-2b 可行性 → Pilot / 前瞻性队列
│     └── Stage 3 对比验证 → RCT / Bland-Altman
└── 综合 AI 医学证据？
      ├── 系统综述 → PRISMA + PRISMA-S
      └── Meta 分析 → PRISMA + QUADAS-2/PROBAST
```

### Core Design Elements

#### 1. Dataset
- 训练/验证/测试必须独立（禁止 data leakage）
- 同一患者的数据不能分在训练和测试集
- 优先外部验证（不同中心/时间段）
- 必须报告：来源、时间范围、纳入排除标准、数据量、类别分布、去标识化方式

#### 2. Ground Truth
- 标注者资历和数量
- 标注一致性（Cohen's Kappa / Fleiss' Kappa / ICC）
- 争议解决机制（共识讨论 / 多数投票 / 专家裁决）
- 标注流程是否盲法

#### 3. Performance Metrics
按任务类型选择指标 → 加载 `references/metrics-and-reporting.yaml`

#### 4. Human-AI Comparison
- 相同信息输入（公平对比条件）
- 说明专家水平（年资、例数）
- 最好三组：AI alone / Human alone / AI-assisted Human
- 阅片 washout period

#### 5. Reproducibility
- 代码开源（GitHub + DOI via Zenodo）
- 模型权重共享或推理 API
- 环境配置（requirements.txt / Docker）
- 随机种子固定

### Reporting Standards

研究类型→规范映射 → 加载 `references/metrics-and-reporting.yaml` 的 mapping 部分。

---

## D. Qualitative Research

### 适用范围

探索性研究（理解"为什么"和"如何"）、访谈/焦点小组/观察/民族志、扎根理论、现象学、叙事研究、混合方法研究。

**定性研究有独立的方法论体系——不是"没有数字的定量研究"。** 样本量逻辑、数据收集、分析方法、质量评价标准全部不同。

### Methodology Router

```
研究目的？
├── 生成理论（从数据中构建理论）→ Grounded Theory
├── 理解个体经验（深入某种体验的本质）→ Phenomenology
├── 描述文化/群体行为 → Ethnography
├── 探索个人生活故事 → Narrative Inquiry
├── 理解特定案例的复杂性 → Case Study
├── 描述和分类主题/模式 → Thematic Analysis（最常用）
├── 理解话语建构 → Discourse Analysis
├── 定性 + 定量结合 → Mixed Methods
└── 不确定 → 先从 Thematic Analysis 开始
```

### Workflow

#### Step 1: 明确研究范式

| 范式 | 核心假设 | 适用场景 |
|------|---------|---------|
| 建构主义 | 现实是社会建构的 | 探索主观经验、意义建构 |
| 后实证主义 | 客观现实存在但不能完全认知 | 混合方法、验证性定性研究 |
| 批判理论 | 关注权力和不平等 | 健康不平等、患者赋权 |
| 实用主义 | 关注"什么有效" | 混合方法、实施科学 |

#### Step 2: 选择数据收集方法

| 方法 | 适用 | 样本量指导 | 注意事项 |
|------|------|-----------|---------|
| 半结构化访谈 | 深入个体经验 | 12-30 人（至信息饱和） | 需要访谈提纲（interview guide） |
| 焦点小组 | 群体互动和共识 | 3-6 组，每组 6-10 人 | 需要讨论指南和主持人 |
| 参与观察 | 行为和环境 | 按场景而非人数 | 需要观察记录框架 |
| 文件分析 | 政策、病历、媒体 | 按饱和 | 需要分析框架 |
| 日记/日志 | 纵向个人体验 | 10-20 人 | 需要结构化模板 |

#### Step 3: 抽样策略

**定性研究不用随机抽样。** 使用目的性抽样（purposive sampling）：

| 策略 | 说明 | 适用 |
|------|------|------|
| 最大变异抽样 | 选择差异最大的案例 | 探索经验的广度 |
| 同质抽样 | 选择相似的案例 | 深入理解特定群体 |
| 典型案例 | 选择"普通"案例 | 描述典型经验 |
| 极端/偏离案例 | 选择极端情况 | 理解边界和例外 |
| 滚雪球 | 已有参与者推荐 | 难以接触的群体 |
| 理论抽样 | 根据正在生成的理论选择 | 扎根理论（边分析边抽样） |

#### Step 4: 样本量——信息饱和

**定性研究不做 power analysis。** 样本量由信息饱和（saturation）决定：

- 当新数据不再产生新的主题/编码时 → 饱和
- 必须在方法中报告饱和评估方式
- 常见范围：访谈 12-30 人，焦点小组 3-6 组
- 扎根理论通常需要 20-30 人
- 现象学通常 5-25 人

#### Step 5: 数据分析方法

| 方法 | 流程 | 适用 | 软件 |
|------|------|------|------|
| **主题分析** | 熟悉数据 → 初始编码 → 寻找主题 → 回顾主题 → 定义主题 → 报告 | 最通用 | NVivo, ATLAS.ti, MAXQDA |
| **框架分析** | 索引 → 图表 → 映射 → 解释 | 政策研究 | NVivo |
| **扎根理论编码** | 开放编码 → 轴心编码 → 选择性编码 → 核心类别 | 理论生成 | NVivo, MAXQDA |
| **诠释现象学分析（IPA）** | 逐案阅读 → 初始注释 → 主题生成 → 跨案比较 | 个人深度体验 | 手工 / NVivo |
| **内容分析** | 编码 → 类别 → 频次 | 偏定量的定性 | MAXQDA |

#### Step 6: 质量评价（Rigor）

**定性研究用可信度（Trustworthiness）替代效度/信度：**

| 定量对应 | 定性标准 | 确保策略 |
|---------|---------|---------|
| 内部效度 | 可信性（Credibility） | 成员检核、三角验证、长时间沉浸、负面案例分析 |
| 外部效度 | 可迁移性（Transferability） | 厚描述（thick description）、清晰的情境描述 |
| 信度 | 可依赖性（Dependability） | 审计轨迹、编码一致性（多编码者 + Cohen's kappa） |
| 客观性 | 可确认性（Confirmability） | 反思日志、三角验证、原始数据引用 |

#### Step 7: 混合方法设计（如适用）

| 设计类型 | 说明 | 图示 |
|---------|------|------|
| 收敛设计 (Convergent) | 定量定性同时进行，最后整合 | QUAN + QUAL → 比较 |
| 解释性序贯 (Explanatory Sequential) | 先定量 → 用定性解释结果 | QUAN → qual |
| 探索性序贯 (Exploratory Sequential) | 先定性 → 用定量验证发现 | QUAL → quan |
| 嵌入设计 (Embedded) | 一种方法嵌入另一种中 | QUAN(qual) 或 QUAL(quan) |

### Output: `qualitative-protocol.md`

```markdown
# Qualitative Study Protocol

## Research Question
[描述性/解释性问题，不是假设检验]

## Methodology
[选择的方法论及理由]

## Philosophical Stance
[范式及认识论立场]

## Participants
- Target population: [描述]
- Sampling strategy: [目的性抽样类型]
- Estimated sample size: [范围] (until saturation)
- Inclusion/exclusion criteria: [列表]
- Recruitment method: [描述]

## Data Collection
- Method: [访谈/焦点小组/观察/...]
- Interview guide / Discussion guide: [附录]
- Duration: [预计时长]
- Recording: [音频/视频/笔记]
- Transcription: [逐字/摘要]

## Data Analysis
- Method: [主题分析/扎根理论/IPA/...]
- Coding approach: [归纳/演绎/混合]
- Software: [NVivo/ATLAS.ti/...]
- Number of coders: [N] + inter-coder reliability method

## Trustworthiness
- Credibility: [成员检核/三角验证/...]
- Transferability: [厚描述]
- Dependability: [审计轨迹]
- Confirmability: [反思日志]

## Ethics
- Informed consent process
- Confidentiality and anonymization
- IRB approval: [pending]

## Reporting Standard
- [COREQ (interviews/focus groups) / SRQR (alternative)]
```

---

## E. Survey / Questionnaire / Delphi

### 适用范围

横断面调查（KAP）、问卷/量表开发与验证、Delphi 共识研究、需求评估调查、医学教育调查。

**问卷/调查研究有独立的方法学要求——不是"发个问卷收数据"这么简单。**

### Survey Type Router

```
研究目的？
├── 描述群体特征（KAP/患病率/满意度）→ Cross-sectional Survey
├── 开发新问卷/量表 → Questionnaire Development
├── 验证已有问卷 → Validation Study
├── 专家共识 → Delphi Study
├── 纵向变化 → Longitudinal Survey (→ 考虑 A. Clinical 队列)
└── 在线调查 → Web-based Survey (报告: CHERRIES)
```

### Workflow

#### Step 1: 问卷设计

**新开发问卷：**

```
1. 概念框架 (Conceptual Framework)
   → 明确测量的构念（construct）
   → 文献综述确定维度
   → 访谈/焦点小组获取条目（→ 可调用 D. Qualitative）

2. 条目生成 (Item Generation)
   → 每个维度 3-5 倍条目（预留筛选空间）
   → 条目措辞规则：
     - 避免双重否定
     - 每条只测一个概念
     - 避免引导性措辞
     - 适合目标人群的阅读水平

3. 专家内容效度 (Content Validity)
   → 5-10 位专家评审
   → 计算 I-CVI（条目水平）和 S-CVI（量表水平）
   → I-CVI >= 0.78, S-CVI/Ave >= 0.90

4. 认知访谈 (Cognitive Interviewing)
   → 5-10 位目标人群测试
   → 出声思维法（Think-aloud）
   → 修改不清楚的条目

5. 预试验 (Pilot Testing)
   → n >= 30
   → 检查完成时间、天花板/地板效应、缺失率
```

**使用已有问卷：**

```
→ 确认原始量表的信效度证据
→ 如需翻译：正向翻译 → 回译 → 专家审核 → 预试验
→ 需要在目标人群重新验证信效度
```

#### Step 2: 测量属性（量表验证）

| 属性 | 方法 | 标准 |
|------|------|------|
| **内容效度** | 专家评审 + I-CVI/S-CVI | I-CVI >= 0.78 |
| **结构效度** | EFA → CFA | EFA: KMO > 0.7, 因子载荷 > 0.4; CFA: CFI > 0.90, RMSEA < 0.08 |
| **收敛效度** | AVE | AVE > 0.50 |
| **区分效度** | sqrt(AVE) > 因子间相关 | Fornell-Larcker 准则 |
| **效标效度** | 与金标准/已验证量表相关 | Pearson/Spearman r |
| **内部一致性** | Cronbach's alpha / McDonald's omega | alpha >= 0.70 |
| **重测信度** | ICC (test-retest, 2-4 周) | ICC >= 0.70 |
| **反应度** | SRM / Effect Size (干预前后) | 如适用 |

**样本量：** EFA 至少条目数 x 5-10；CFA 至少 200 人

#### Step 3: 抽样策略

| 策略 | 适用 | 优缺点 |
|------|------|--------|
| 简单随机 | 有完整名册 | 最无偏但需要抽样框 |
| 分层随机 | 确保亚组代表性 | 需要分层变量信息 |
| 整群 | 以机构/科室为单位 | 方便但设计效应增大 |
| 便利 | 难以随机 | 最常见但偏倚最大，必须讨论 |
| 配额 | 确保特定比例 | 类似分层但非随机 |
| 滚雪球 | 难以接触的群体 | 偏倚大，适合探索性 |

#### Step 4: 样本量计算

**横断面调查：**
```
n = Z^2 x p x (1-p) / d^2
  Z = 1.96 (95% CI)
  p = 预期比例 (不确定时用 0.5)
  d = 精度 (通常 0.05)
  → 修正有限总体: n_adj = n / (1 + n/N)
  → 修正应答率: n_final = n_adj / expected_response_rate
```

**量表验证：** 条目数 x 5-10（EFA）; >= 200（CFA）

**Delphi：** 通常 15-30 位专家，无统一公式

#### Step 5: Delphi 方法（如适用）

```
Round 1: 开放式问题 → 收集意见
  |
Round 2: 结构化问卷 → Likert 评分 + 排序
  | (反馈汇总结果)
Round 3: 修改后再评 → 检查共识
  | (如未达标)
Round 4: 最终确认（通常不超过 4 轮）

共识标准:
  → >= 70-80% 同意率（没有统一标准，需预先定义）
  → 或 IQR <= 1（Likert 1-9）
  → 或 中位数 >= 7/9

报告: 需说明轮数、专家数、退出率、共识定义
```

#### Step 6: 数据收集

| 方式 | 工具 | 优势 | 劣势 |
|------|------|------|------|
| 在线 | REDCap, 问卷星, SurveyMonkey, Google Forms | 快速、低成本、自动录入 | 覆盖偏倚、低应答率 |
| 纸质 | 打印问卷 | 高应答率、无数字鸿沟 | 数据录入工作量大 |
| 电话 | 电话访问 | 适合老年人群 | 成本高、社会赞许偏倚 |
| 面对面 | 现场填写 | 最高应答率 | 成本最高 |

**在线调查报告规范: CHERRIES checklist**

### Output: `survey-protocol.md`

```markdown
# Survey Study Protocol

## Research Question
[描述性问题]

## Survey Type
[Cross-sectional / Questionnaire development / Validation / Delphi]

## Questionnaire
- Name: [量表名称]
- Dimensions: [维度列表]
- Items: [条目数]
- Response format: [Likert 5/7 点 / 二分类 / VAS / ...]
- Development process: [新开发流程 / 已有量表引用]

## Target Population
[描述]

## Sampling
- Strategy: [抽样方法]
- Inclusion/exclusion criteria
- Sample size: [N] (计算依据: [公式和参数])
- Expected response rate: [%]

## Psychometric Properties (if validation)
- Content validity: [方法]
- Construct validity: [EFA → CFA]
- Reliability: [Cronbach's alpha, test-retest ICC]

## Data Collection
- Method: [在线/纸质/混合]
- Platform: [REDCap/问卷星/...]
- Period: [时间范围]
- Reminders: [策略]

## Analysis Plan
- Descriptive: 频数(%)、均值±SD
- Factor analysis: EFA (principal axis, oblimin rotation) → CFA
- Reliability: Cronbach's alpha, ICC
- Group comparisons: [如适用]

## Ethics
- IRB approval: [pending]
- Informed consent: [在线同意/纸质签名]
- Anonymity: [匿名/保密]

## Reporting Standard
- [CHERRIES (web-based) / STROBE (cross-sectional) / COSMIN (validation)]
```

---

## Common Mistakes（全类型合并）

### 通用

| 想法 | 现实 |
|------|------|
| "先收数据再写 protocol" | 先注册 protocol 再收数据才可信 |
| "混杂因素不用特别考虑" | 未调整的混杂 = 虚假关联 |

### A. Clinical

| 想法 | 现实 |
|------|------|
| "样本量够大应该没问题" | 必须做正式 power analysis |
| "纳入标准写宽一点好" | 过宽 = 异质性大 = 效应被稀释 |
| "横断面也能推因果" | 横断面只能看关联，不能推因果 |

### B. Basic Science

| 想法 | 现实 |
|------|------|
| "做了 3 个复孔就是 n=3" | 技术重复，只算 n=1 |
| "不需要阴性对照" | 没有对照的结果不可解读 |
| "WB 肉眼可见就不用定量" | 必须灰度值定量 |
| "SD 太大换成 SEM" | 数据美化，用 SD 如实反映变异 |
| "动物实验不用随机分组" | 必须随机，否则分配偏倚 |
| "只展示最好看的那次 WB" | 基于所有重复的定量数据 |
| "统计不显著但趋势明显" | 趋势不是证据，增加样本量或改设计 |

### C. AI/ML

| 想法 | 现实 |
|------|------|
| "Accuracy 95% 说明模型很好" | 类别不平衡时 Accuracy 毫无意义，必须看 AUROC/AUPRC |
| "训练集上效果好就行" | 没有独立测试集/外部验证的结果不可信 |
| "数据随机划分就行" | 同一患者不能同时在训练和测试集 |
| "AUROC 高就有临床价值" | 必须做 DCA 评估临床净获益 |
| "这是 AI 研究不需要临床规范" | 需要同时满足技术和临床两套规范 |
| "我的器械直接做 RCT" | 先用 IDEAL 定位阶段，Stage 1-2 不适合 RCT |
| "AI 评估不用报告可用性" | DECIDE-AI 要求报告人机交互和用户体验 |

### D. Qualitative

| 想法 | 现实 |
|------|------|
| "样本量越大越好" | 定性追求深度不是广度，饱和是停止标准 |
| "随机抽样更科学" | 目的性抽样才是定性研究的正确策略 |
| "不需要理论框架" | 必须声明认识论立场和方法论依据 |
| "编码就是贴标签" | 编码是分析过程，需要持续比较和反思 |
| "一个人编码就行" | 至少两人独立编码 + 一致性检验 |
| "结果用频次报告" | 主题的丰富度比频次更重要 |
| "定性不需要伦理审查" | 访谈涉及个人经验，必须伦理审查 + 知情同意 |
| "定性研究不严谨" | 有完整的质量评价框架（Trustworthiness） |

### E. Survey/Delphi

| 想法 | 现实 |
|------|------|
| "问卷随便写几个问题就行" | 需要概念框架、条目生成、专家审核、认知访谈、预试验 |
| "Cronbach's alpha > 0.7 就行了" | 还需要结构效度（EFA/CFA）、收敛/区分效度 |
| "样本越大越好" | 大样本 + 低应答率 = 偏倚比小样本 + 高应答率更严重 |
| "便利抽样没问题" | 必须在 Limitations 中讨论选择偏倚 |
| "翻译量表直接用" | 必须回译 + 目标人群信效度重新验证 |
| "Delphi 两轮就够了" | 至少 2 轮有反馈的评分，通常 3 轮 |
| "同意率 51% 就是共识" | 预先定义共识标准，通常 >= 70-80% |
| "在线调查不需要伦理审查" | 收集人类受试者数据都需要伦理审查 |

## Convergence（按类型）

### A. Clinical — 完成条件
1. 研究类型已确定且合理
2. 样本量计算有明确依据
3. 纳入/排除标准具体可操作
4. 主要结局指标有明确定义
5. 已识别主要混杂因素
6. `study-protocol.md` 已生成
7. **Hard Checkpoint：用户已审阅并确认研究方案**

### B. Basic Science — 完成条件
1. 对照组完整（阴性+阳性+载体，如适用）
2. 重复方案明确（生物学 >= 3，技术 >= 2）
3. 盲法和随机化方案已确定
4. 样本量有依据（power analysis 或文献先例）
5. 伦理审查已确认（动物实验需 IACUC）

### C. AI/ML — 完成条件
1. 研究类型已明确，对应报告规范已确定
2. 数据集方案完整（来源、划分、标注流程）
3. 评估指标已选择并有依据
4. 人机对比方案已设计（如适用）
5. 可复现性方案已规划

### D. Qualitative — 完成条件
1. 方法论选择有明确理由
2. 抽样策略和样本量范围已确定
3. 数据收集工具（访谈提纲等）已设计
4. 分析方法已选择
5. 质量保障策略已规划
6. 伦理考量已覆盖
7. 报告规范已确定（COREQ / SRQR）

### E. Survey/Delphi — 完成条件
1. 问卷/量表设计完成或已有量表确认
2. 抽样策略和样本量已确定
3. 信效度验证计划已规划（如适用）
4. 数据收集方式和平台已选定
5. 分析计划已明确
6. 伦理审查已考虑
7. 报告规范已确定

## Red Flags — STOP

### 全类型通用
- **禁止虚构数据或结果**
- **禁止事后更换主要结局指标**（outcome switching = 学术不端）

### D. Qualitative 特有
- **禁止用 power analysis 决定定性研究样本量** — 用信息饱和
- **禁止随机抽样用于定性研究** — 用目的性抽样
- **禁止单人编码无一致性检验** — 至少双人独立编码
- **禁止没有认识论声明** — 必须声明研究范式

### E. Survey 特有
- **禁止未经验证的自编量表直接用于正式研究** — 至少需要内容效度 + 预试验
- **禁止忽略应答率** — 必须报告应答率，低于 60% 需要讨论偏倚
- **禁止 EFA 和 CFA 用同一份数据** — 必须分样本或使用独立数据集

## Hard Checkpoint：研究方案审批

Protocol（`study-protocol.md` / `qualitative-protocol.md` / `survey-protocol.md`）生成后，**必须**向用户完整展示方案并获得明确确认，才能进入下一步。

### 审批报告格式

```
--------------------------------------------
WARN 研究方案审批 (Hard Checkpoint)

FILE 生成文件：[study-protocol.md / qualitative-protocol.md / survey-protocol.md]

SUMMARY 方案摘要：
  - 研究类型：[Clinical / Basic / AI-ML / Qualitative / Survey]
  - 研究对象：[纳入标准概要]
  - 样本量：N=[X]（依据：[效应量来源/饱和/公式]）
  - 主要结局/主要问题：[指标名称 + 定义]
  - 对照/比较：[对照组设定]
  - 预计周期：[数据收集时间]

WARN 需要用户确认：
  1. 研究类型是否正确？
  2. 样本量是否可行？
  3. 纳入/排除标准是否合理？
  4. 主要结局/研究问题是否是你最关心的？
  5. 是否需要伦理审查？
  6. 是否需要注册？（干预性研究 → 必须）

LOCK 确认后，研究方案将锁定。后续偏差需在 analysis-log.md 中记录理由。
--------------------------------------------
请审阅上述方案，确认后回复"确认"以继续。
如需修改请告诉我具体调整内容。
```

### 为什么这是 Hard Checkpoint

- **研究类型**决定了后续所有分析方法、报告规范、审稿标准
- **主要结局**一旦确定，后续不能随意更改（事后更换 = outcome switching = 学术不端）
- **样本量**决定了研究的可行性和统计功效
- **protocol 注册**后不可大幅更改（ClinicalTrials.gov / ChiCTR 有记录）

### 确认后锁定的内容

| 锁定项 | 后续能否更改 |
|--------|-------------|
| 研究类型 | 不能更改 |
| 主要结局指标 | 不能更改（只能添加为次要结局） |
| 样本量目标 | 可调整但需说明理由 |
| 纳入/排除标准 | 可微调但需在 Methods 中说明 |
| 统计方法（SAP 中）| 偏差需在 analysis-log.md 中记录 |

## 衔接规则

### 前置依赖
- **必须**有 PICO/研究问题（`research-question-formulation`）
- **推荐**: `literature-synthesis`

### 强制衔接（按类型）
- **A. Clinical**: 涉及人体/患者数据 → **提醒**用户检查伦理合规（`research-ethics`），不强制阻断流程
- **B. Basic**: 涉及动物实验 → **必须**检查 ARRIVE 2.0（`reporting-standards`）；涉及临床样本 → **提醒**伦理审查
- **C. AI/ML**: 模型评估完成后 → **必须**触发 `reporting-standards` 检查 TRIPOD-AI / CLAIM / DECIDE-AI；涉及手术/器械创新 → **必须**按 IDEAL 框架定位阶段
- **D. Qualitative**: 完成后 → `manuscript-writing`（定性研究的论文结构不是标准 IMRaD）；混合方法 → 定量部分路由回 A. Clinical
- **E. Survey**: 完成后 → `data-analysis-planning`（确定统计方法）

### 用户确认方案后
- → 传递给 `journal-selection`（早期选刊）
- → 传递给 `data-analysis-planning` 制定 SAP

### 可选
- 涉及 AI 辅助分析（如病理图像 AI）→ 走 C 模块
- 涉及组学数据 → 参考 `data-analysis-planning/references/omics-methods.md`
- 需要文献支持 → `literature-synthesis`
- 涉及伦理 → `research-ethics`
- 问卷开发前探索 → 先走 D. Qualitative，再回 E. Survey
