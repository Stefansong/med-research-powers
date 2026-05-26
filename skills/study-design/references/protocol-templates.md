# Protocol Templates

Static output templates for the three protocol document types produced by `study-design`.
Load the relevant template when generating the corresponding protocol file. Router logic and
judgment criteria stay in `SKILL.md`; this file holds only the fill-in skeletons.

---

## A. Clinical — `study-protocol.md`

### 1. 研究概要
标题、研究类型、注册号（ClinicalTrials.gov / ChiCTR）

### 2. 研究对象
纳入标准（具体可操作）、排除标准、招募方式

### 3. 样本量计算（MANDATORY）
使用 `skills/statistical-analysis/scripts/power_analysis.py` 或 G*Power。
必须确认：预期效应量来源（文献/预实验）、α、β、脱落率。

### 4. 变量定义
自变量、因变量、混杂变量、协变量——每个都要有定义、测量方式、单位。

### 5. 数据收集
时间点、方式（EMR/量表/检验/影像）、质控措施、缺失数据预案

### 6. SAP 概要
详细 SAP → `data-analysis-planning`

### 7. 伦理合规
→ `research-ethics`

---

## D. Qualitative — `qualitative-protocol.md`

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

## E. Survey — `survey-protocol.md`

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
