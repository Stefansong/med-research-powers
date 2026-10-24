# F. Mini-Review

> **章节结构是期刊的通用要求；内容必须来自本项目的实际产物，不写套话；缺少的数据写 `[待补：来源]` 占位，不编造。**

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。适用：短篇聚焦（通常 2000–3000 词）、多为领域专家受邀撰写的综述；不需要系统检索、不需要 PRISMA。

## 前置依赖

| 前置文件 | 必须/推荐 |
|---------|----------|
| 主题明确（一句话能说清"本文只讨论 X 的 Y 方面"） | 必须 |
| `literature-references.md` | 推荐 |
| 目标期刊对 Mini-review 的上限（通常比 full review 严格得多；模板库的 `limits` 只是原始研究的上限，见下方"期刊上限"） | 必须 |

## 写作顺序

1. **一句话主题 + 2–3 个小节标题** — 先定骨架
2. **Focused Sections** — 每节 3–6 段
3. **Introduction** — 1–2 段
4. **Conclusion / Outlook** — 1 段
5. **Abstract** — 非结构化，字数以期刊对 Mini-review 的要求为准（常见 100–200 词）
6. **Title** — 短、具体

## 结构（最简洁）

```
Title
Abstract（非结构化，字数以期刊对本类型的要求为准）
Introduction（1–2 段：主题意义 + 本文目的）
[2–3 Focused Sections]（聚焦讨论一个窄主题）
Conclusion / Outlook（1 段）
References（上限以期刊对本类型的要求为准，常见 ≤30–50）
```

**注意：** 不需要系统检索，不需要 PRISMA；字数以期刊对本类型的要求为准（常见 2000–3000 词）。一张概念图/汇总表能显著提高可读性。

## 期刊上限（字数 / 摘要 / 参考文献 / 图表）

`get_journal_template.py --id <id>` 输出的 `limits` 只是该刊**原始研究（Original Article）**的上限，不能套用到本类型。按顺序取：

1. 库里没有 Mini-review 的上限：输出里的 `limits_by_type.review` 是该刊 **full review** 的上限（通常宽得多），只有期刊作者指南写明 Mini-review 与 Review 用同一组上限时才能直接用；
2. 其余情况 → 到期刊 author guidelines 查 Mini-review 的字数、摘要、参考文献、图表上限：把 `--id` 输出的整条复制进项目目录 `journal-overrides.yaml`（同 id 的条目会整条替换库内条目），把 Mini-review 的上限写进其中的 `limits_by_type.review`（没有单独的 Mini-review 键；这份 overrides 只服务本项目，替换掉 full review 的数字），并写 `guidelines_checked: YYYY-MM` 与 `guidelines_source: <URL>`；
3. 查不到的上限不填，并告诉用户需要人工确认——**不要**拿原始研究或 full review 的数字代替。

导出时 `manuscript-export` 加 `--article-type review`，按 overrides 里的这组上限检查；项目目录没有这份 overrides 时，`--article-type review` 用的是库里 full review 的上限（或没有上限），对 Mini-review 不算检查过，要在报告里注明。

## Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── section-1-[theme].md
├── section-2-[theme].md
├── section-3-[theme].md   ← 可选
├── conclusion.md
├── references.md
└── figure-legends.md      ← 可选
```

> 与 Narrative Review 相同：`manuscript-export` 按数字顺序把 `section-N-*.md` 排在 Introduction 之后导出，不必合并。

## 报告规范

无强制规范。
