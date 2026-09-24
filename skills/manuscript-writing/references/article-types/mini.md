# F. Mini-Review

> **章节结构是期刊的通用要求；内容必须来自本项目的实际产物，不写套话；缺少的数据写 `[待补：来源]` 占位，不编造。**

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。适用：短篇聚焦（通常 2000–3000 词）、多为领域专家受邀撰写的综述；不需要系统检索、不需要 PRISMA。

## 前置依赖

| 前置文件 | 必须/推荐 |
|---------|----------|
| 主题明确（一句话能说清"本文只讨论 X 的 Y 方面"） | 必须 |
| `literature-references.md` | 推荐 |
| 目标期刊模板（Mini-review 的字数/参考文献上限通常比 full review 严格得多） | 必须 |

## 写作顺序

1. **一句话主题 + 2–3 个小节标题** — 先定骨架
2. **Focused Sections** — 每节 3–6 段
3. **Introduction** — 1–2 段
4. **Conclusion / Outlook** — 1 段
5. **Abstract** — 非结构化，字数以模板为准（常见 100–200 词）
6. **Title** — 短、具体

## 结构（最简洁）

```
Title
Abstract（非结构化，字数以期刊模板为准）
Introduction（1–2 段：主题意义 + 本文目的）
[2–3 Focused Sections]（聚焦讨论一个窄主题）
Conclusion / Outlook（1 段）
References（上限以期刊模板为准，常见 ≤30–50）
```

**注意：** 不需要系统检索，不需要 PRISMA；字数以期刊模板为准（常见 2000–3000 词）。一张概念图/汇总表能显著提高可读性。

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

> 与 Narrative Review 相同：`manuscript-export` 不识别 `section-N-*.md`，导出前把各节合并进 `discussion.md`（或按期刊要求的单一正文文件）。

## 报告规范

无强制规范。
