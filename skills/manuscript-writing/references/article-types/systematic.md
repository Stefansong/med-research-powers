# C. Systematic Review（不含定量合并）

> **章节结构是期刊的通用要求；内容必须来自本项目的实际产物，不写套话；缺少的数据写 `[待补：来源]` 占位，不编造。**

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。需要统计合并时改读 `meta.md`（在本文件基础上追加）。

## 前置依赖

| 前置文件 | 必须/推荐 |
|---------|----------|
| 注册信息：PROSPERO 等注册号，**或**明确说明未注册及原因（PRISMA 2020 item 24a 要求报告注册信息，未注册须写明） | 必须 |
| `search-strategy.md` + `screening-log.md`（`literature-synthesis` 产物） | 必须 |
| `literature-references.md`（`literature-synthesis` Systematic 模式产物：逐篇研究类型、样本量、核心发现、偏倚风险） | 必须 |
| PRISMA 2020 Checklist（`reporting-standards` 提供） | 必须 |
| 偏倚风险评估结果（RoB 2 / ROBINS-I / ROBINS-E（暴露的队列研究）/ NOS（满分 9，仅在必要时并说明局限）/ QUADAS-2（诊断准确性）/ PROBAST+AI（预测模型）） | 必须 |
| 目标期刊对 Systematic Review 的上限（见下方"期刊上限"；模板库的 `limits` 只是原始研究的上限） | 必须 |

## 写作顺序

1. **Methods** — 最客观（检索策略、筛选标准、偏倚评估方法）
2. **Results** — PRISMA 流程图 → 纳入研究特征 → 偏倚评估 → 综合结果
3. **Introduction** — 已有综述的不足 → 本综述的目的（PICO）
4. **Discussion** — 主要发现 → 证据质量 → 局限性 → 启示
5. **Abstract** — 结构化（PRISMA 2020 for Abstracts）
6. **Title** — 必须含 "systematic review"

## 章节规则

**Methods（必须详细，PRISMA 2020 items 3–15）**
- Protocol and Registration（注册号 + 注册平台；未注册则说明）
- Eligibility Criteria（PICO 框架 + 研究类型、语言、年份）
- Information Sources（数据库列表 + 各库最后检索日期；写明哪些库由用户运行检索并导入、哪些未检索；WebSearch 补充检索写在 other methods）
- Search Strategy（至少一个数据库的完整检索式，其余附 Appendix）
- Study Selection Process（两名评价者独立筛选，至少一名是人；分歧解决方式与一致性；用了 AI / 自动化工具时写明名称、版本、用途和人工核对方式——PRISMA 2020 item 8）
- Data Extraction（提取变量列表；两名评价者独立提取，至少一名是人；AI 工具同上——PRISMA 2020 item 9）
- Risk of Bias Assessment（工具按研究类型：RoB 2 / ROBINS-I / ROBINS-E / NOS（仅在必要时）/ QUADAS-2 / PROBAST+AI）
- Synthesis Methods（叙述性综合的分组与呈现方式；如做定量合并见 `meta.md`）
- Certainty of Evidence（GRADE，如适用）

**Results**
- Study Selection → **PRISMA 2020 Flow Diagram（必须）**，各环节数字与 `screening-log.md` 一致
- Study Characteristics → 纳入研究汇总表（从 `literature-references.md` 整理）
- Risk of Bias → 汇总图/表
- Synthesis Results → 按结局分组报告；叙述性综合不得用"票数法"（多少研究显著）代替效应方向与大小

**Discussion**：主要发现 → 与已有综述对比 → 证据质量（GRADE）→ 局限性（证据层面 + 综述过程层面）→ 临床/研究启示

**Abstract**：结构化，小标题与字数**以目标期刊对 Systematic Review 的要求为准**（见"期刊上限"）；须含注册号（或"未注册"）与纳入研究数。

## 期刊上限（字数 / 摘要 / 参考文献 / 图表）

`get_journal_template.py --id <id>` 输出的 `limits` 只是该刊**原始研究（Original Article）**的上限，不能套用到本类型。按顺序取：

1. 输出里的 `limits_by_type.<键>`（本类型与 Meta-Analysis 都用 `systematic_review`）——库内只有条目原文写明了该类型上限的少数期刊才有；
2. 没有 → 到期刊 author guidelines 查本文章类型的字数、摘要、参考文献、图表上限：把 `--id` 输出的整条复制进项目目录 `journal-overrides.yaml`（同 id 的条目会整条替换库内条目），在其中加 `limits_by_type.<键>`，并写 `guidelines_checked: YYYY-MM` 与 `guidelines_source: <URL>`；
3. 查不到的上限不填，并告诉用户需要人工确认——**不要**拿原始研究的数字代替。

导出时 `manuscript-export` 加 `--article-type <键>`，按这组上限检查。

## Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── methods.md
├── results.md
├── discussion.md
├── conclusion.md
├── references.md
├── supplementary.md            ← 含：完整检索式 / 排除研究清单及理由 / 偏倚评估明细
└── prisma-checklist.md         ← PRISMA 2020（27 项）逐条对应页码
```

## 报告规范

PRISMA 2020（27 项）+ PRISMA 2020 for Abstracts；诊断准确性综述加 PRISMA-DTA；完整清单由 `reporting-standards` 提供。
