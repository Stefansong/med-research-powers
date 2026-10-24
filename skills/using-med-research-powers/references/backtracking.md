# Pipeline 回溯表（Backward Links）

`using-med-research-powers` 在发现上游问题、需要回到前面的 skill 时读这张表。
回溯规则：修改后的产物标注修改原因和日期；下游依赖它的产物标记"需重新验证"。

**分析要变时按这三条走**（下表和各 skill 的衔接规则说法一致）：
- 已锁定的 SAP 里**原有分析的方法**要换（含体检发现数据与 SAP 假设不符）：SAP 写了预定备选或预案 → 留在 `statistical-analysis` 照做并记偏离；没写 → `data-analysis-planning` 修订 SAP（版本、日期、理由，由用户决定）→ `statistical-analysis`。
- SAP 之外的**新分析**（审稿人或用户要求）：`statistical-analysis` 直接做，先在 `analysis-log.md` 写明分析定义，标 post hoc / exploratory，不改 SAP 原文。
- SAP 只有描述性部分（快速路径只为 Table 1 写的），现在要做**结局分析**或按组的结局图：`data-analysis-planning` 补全 SAP（新版本，再过硬确认 2）→ `statistical-analysis`；这是计划内的分析，不按 post hoc 做。

| 当前阶段 | 发现的问题 | 回到 |
|----------|------------|------|
| 任何阶段 | 研究问题定义不准确 | research-question-formulation |
| statistical-analysis | 前提假设不满足 / 需改方法 / 体检与 SAP 假设不符 | 按上面第一条（SAP 有预定备选或预案 → 留在 statistical-analysis；没有 → data-analysis-planning → statistical-analysis） |
| statistical-analysis / figure-generation | 只有描述性 SAP，要做结局分析或按组的结局图 | 按上面第三条：data-analysis-planning 补全 SAP → statistical-analysis |
| manuscript-writing | 分析方法需调整 | 按上面第一条（要加 SAP 之外的分析 → 第二条） |
| peer-review-simulation | 方法 / 统计的 Critical 问题 | statistical-analysis（按上面第一、二条）；设计本身的缺陷（数据已收集、改不了）→ manuscript-writing 如实写进 Limitations，不改已锁定的主要结局 |
| peer-review-simulation | 写作 / 图表的 Critical 问题 | manuscript-writing / figure-generation |
| pre-submission Gate 1（报告规范） | 条目缺失 | manuscript-writing，再跑 reporting-standards |
| pre-submission Gate 2（统计） | 统计不完整 / 与 SAP 不符 | statistical-analysis |
| pre-submission Gate 3（引用与数据） | 引用不存在 / 数字不一致 | pubmed-search Mode 3 → manuscript-writing；数字与结果文件不符 → statistical-analysis |
| pre-submission Gate 4（图表） | 图表不合规 | figure-generation |
| pre-submission Gate 5（伦理） | 伦理声明缺失 | research-ethics |
| pre-submission Gate 6（形式） | 字数 / 引用数 / 图表数超限 | manuscript-writing（或换期刊 → journal-selection） |
| revision-response | 审稿人要求补充分析 | statistical-analysis（按上面第二条：post hoc，分析定义写进 `analysis-log.md`） |
| revision-response | 被拒需改投 | journal-selection → manuscript-writing（按新刊调整）→ pre-submission-verification → manuscript-export → submission-preparation |
| data-collection-tools | protocol 缺变量定义 | study-design |
