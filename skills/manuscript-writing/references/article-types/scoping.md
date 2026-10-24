# E. Scoping Review

> **章节结构是期刊的通用要求；内容必须来自本项目的实际产物，不写套话；缺少的数据写 `[待补：来源]` 占位，不编造。**

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。适用：目的是映射某领域"什么被研究了、什么没有"，而不是回答一个特定效应问题。

## 前置依赖

| 前置文件 | 必须/推荐 |
|---------|----------|
| `search-strategy.md` + `screening-log.md` | 必须 |
| `literature-references.md` | 必须 |
| PRISMA-ScR Checklist（`reporting-standards` 提供） | 必须 |
| Evidence Map / Charting Table | 必须 |
| 注册/方案（OSF、Figshare 等；PROSPERO 不接受 scoping review） | 推荐，未注册须说明 |
| 目标期刊对 scoping review 的上限（见下方"期刊上限"；模板库的 `limits` 只是原始研究的上限） | 必须 |

## 写作顺序

1. **Methods** — 框架、PCC、检索、筛选、charting
2. **Results** — PRISMA-ScR 流程图 → 研究特征 → Evidence Map
3. **Introduction** — 为什么用 scoping 而不是 systematic review（问题宽、证据类型杂、需先绘制版图）
4. **Discussion** — 版图上的空白与密集区 → 对后续系统综述/原始研究的建议
5. **Abstract** — 结构化
6. **Title** — 必须含 "scoping review"

## 章节规则

**Methods**：框架声明（Arksey & O'Malley / Levac / JBI）→ PCC（Population, Concept, Context）→ 检索（数据库 + 灰色文献）→ 筛选（双人）→ Data **Charting**（不叫 "extraction"；charting 表在过程中迭代更新须说明）→ **不做偏倚风险评估**（如做了须说明理由）

**Results**：PRISMA-ScR Flow Diagram → Study Characteristics → **Evidence Mapping**（表格/概念图/气泡图展示"什么被研究了、什么没有"）；不合并效应量

**Discussion**：概括版图 → 空白与方法学缺口 → 对政策/实践/研究的启示；局限性写检索范围与 charting 主观性

**Abstract**：结构化，小标题与字数**以目标期刊对 scoping review 的要求为准**（见"期刊上限"）。

## 期刊上限（字数 / 摘要 / 参考文献 / 图表）

`get_journal_template.py --id <id>` 输出的 `limits` 只是该刊**原始研究（Original Article）**的上限，不能套用到本类型。按顺序取：

1. 输出里的 `limits_by_type.<键>`（期刊把 scoping review 归入哪种文章类型，就用对应的键：多为 `systematic_review` 或 `review`）——库内只有条目原文写明了该类型上限的少数期刊才有；
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
├── results.md              ← 含 Evidence Map
├── discussion.md
├── conclusion.md
├── references.md
├── supplementary.md        ← 完整检索式、charting 表
└── prisma-scr-checklist.md ← PRISMA-ScR（22 项）逐条对应
```

## 报告规范

PRISMA-ScR（22 项）；完整清单由 `reporting-standards` 提供。
