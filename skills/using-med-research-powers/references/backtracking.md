# Pipeline 回溯表（Backward Links）

`using-med-research-powers` 在发现上游问题、需要回到前面的 skill 时读这张表。
回溯规则：修改后的产物标注修改原因和日期；下游依赖它的产物标记"需重新验证"。

| 当前阶段 | 发现的问题 | 回到 |
|----------|------------|------|
| 任何阶段 | 研究问题定义不准确 | research-question-formulation |
| statistical-analysis | 前提假设不满足 / 需改方法 | data-analysis-planning（修改 SAP，记录偏离理由） |
| manuscript-writing | 分析方法需调整 | data-analysis-planning → statistical-analysis |
| peer-review-simulation | 方法学 Critical 问题 | study-design（只能改写法与局限，不能改已锁定的主要结局） |
| pre-submission Gate 1（报告规范） | 条目缺失 | manuscript-writing，再跑 reporting-standards |
| pre-submission Gate 2（统计） | 统计不完整 / 与 SAP 不符 | statistical-analysis |
| pre-submission Gate 3（引用与数据） | 引用不存在 / 数字不一致 | pubmed-search Mode 3 → manuscript-writing |
| pre-submission Gate 4（图表） | 图表不合规 | figure-generation |
| pre-submission Gate 5（伦理） | 伦理声明缺失 | research-ethics |
| pre-submission Gate 6（形式） | 字数 / 引用数 / 图表数超限 | manuscript-writing（或换期刊 → journal-selection） |
| revision-response | 审稿人要求补充分析 | statistical-analysis（标注 post hoc，写入 SAP 偏离记录） |
| revision-response | 被拒需改投 | journal-selection → manuscript-export |
| data-collection-tools | protocol 缺变量定义 | study-design |
