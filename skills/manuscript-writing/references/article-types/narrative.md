# B. Narrative Review

> **章节结构是期刊的通用要求；内容必须来自本项目的实际产物，不写套话；缺少的数据写 `[待补：来源]` 占位，不编造。**

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。适用：自由组织主题、不要求系统检索的综述（含受邀综述、教学性综述、State-of-the-art review）。

## 前置依赖

| 前置文件 | 必须/推荐 |
|---------|----------|
| `literature-synthesis-summary.md` + `literature-references.md` | 必须 |
| `journal-selection-report.md`（或 `.mrp-state.json` 的 `target_journal`） | 推荐 |
| `research-question.md` | 推荐（帮助聚焦范围） |
| 目标期刊对 Review 的上限（见下方"期刊上限"；模板库的 `limits` 只是原始研究的上限） | 必须 |

## 写作顺序

1. **Outline** — 确定 3–5 个主题板块（按概念/机制/临床问题组织，不按时间或作者）
2. **Thematic Sections** — 每个板块独立写作
3. **Introduction** — 明确综述范围、目的与文献来源说明（即使不是系统综述，也应交代检索了哪些数据库、时间范围）
4. **Discussion / Current Challenges + Future Directions** — 整合各板块、指出趋势
5. **Conclusion** — 高度凝练
6. **Abstract** — 概括全文

## 章节规则

**Introduction（3–4 段）**：主题背景 → 为什么需要这篇综述（已有综述的不足/新证据出现）→ 综述范围和目的

**Thematic Sections（3–5 个）**：每个主题一个 section，内部按逻辑组织。每个 section 末尾 1–2 句小结。图表：至少 1 张概念图/汇总表帮助读者。

**Discussion / Current Challenges**：综合各主题板块的交叉发现 → 当前挑战与争议

**Future Directions**：基于 gap 提出研究方向，每个方向需有依据（引用）。

**Conclusion（1–2 段）**：凝练全文核心要点，**不引入新信息**。

**Abstract**：多为非结构化，字数**以目标期刊对 Review 的要求为准**（见"期刊上限"）；概括范围 + 主要发现 + 结论。

## 期刊上限（字数 / 摘要 / 参考文献 / 图表）

`get_journal_template.py --id <id>` 输出的 `limits` 只是该刊**原始研究（Original Article）**的上限，不能套用到本类型。按顺序取：

1. 输出里的 `limits_by_type.<键>`（本类型用 `review`）——库内只有条目原文写明了该类型上限的少数期刊才有；
2. 没有 → 到期刊 author guidelines 查本文章类型的字数、摘要、参考文献、图表上限：把 `--id` 输出的整条复制进项目目录 `journal-overrides.yaml`（同 id 的条目会整条替换库内条目），在其中加 `limits_by_type.<键>`，并写 `guidelines_checked: YYYY-MM` 与 `guidelines_source: <URL>`；
3. 查不到的上限不填，并告诉用户需要人工确认——**不要**拿原始研究的数字代替。

导出时 `manuscript-export` 加 `--article-type <键>`，按这组上限检查。

## Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── section-1-[theme].md      ← 按主题命名
├── section-2-[theme].md
├── section-3-[theme].md
├── section-4-[theme].md      ← 可选
├── discussion.md              ← 含 Current Challenges + Future Directions
├── conclusion.md
├── references.md
└── figure-legends.md          ← 可选
```

> `manuscript-export` 把主题式 `section-N-*.md` 按 N 的数字顺序（1, 2, … 10）排在 `introduction.md` 之后导出，计入正文字数；有这些文件时不要求 methods.md / results.md。文件名必须是 `section-<数字>-<主题>.md`。

## 报告规范

无强制规范；建议参考 SANRA（Scale for the Assessment of Narrative Review Articles）自评 6 项：问题的合理性、目的陈述、文献检索说明、引用规范、科学推理、数据呈现。
