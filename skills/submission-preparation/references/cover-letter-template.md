# Cover Letter Templates & Lookup

Loaded on demand by submission-preparation Step 1. Keep the judgment (paragraph
goals, hooks, novelty framing) in SKILL.md; this file is the static template +
journal-style lookup.

This skill is the **OWNER** of cover-letter and cascade-rewrite mechanics for the
whole plugin. `revision-response` defers here for any cover-letter rewrite.

## 期刊风格适配（Journal-style lookup）

不同期刊的 Cover Letter 期望不同：

| 期刊类型 | 风格偏好 |
|---------|---------|
| **Nature/Science/Cell** | 强调 broad impact，跨学科意义，简洁有力 |
| **Lancet/JAMA/BMJ/NEJM** | 强调 clinical relevance，patient impact，policy implication |
| **Specialty journals** | 强调领域内 gap，技术贡献，实用价值 |
| **Methods journals** | 强调方法创新，reproducibility，benchmark 结果 |
| **Open access (PLOS/BMC)** | 强调 rigor，透明性，数据可用性 |

## Cover Letter 模板（生成 `cover-letter.md`）

```markdown
Dear [Editor Name / "Editor-in-Chief"],

[Paragraph 1: Hook — 2-3 sentences. Sentence 1: "Please consider our [article type],
"[exact title, identical to the manuscript]", for publication in [journal]." Then the core
finding (numbers copied from Results / Abstract, with CI) + significance]

[Paragraph 2: Novelty — 3-4 sentences, comparison with existing work]

[Paragraph 3: Journal Fit — 2-3 sentences, why this journal + this audience]

[Paragraph 4: Declarations —
 - This manuscript is not under consideration elsewhere; all authors approved the submission.
 - Competing interests: [statement]. Trial registration: [registry + number, if applicable].
 - Use of AI-assisted technology: [None was used.] / [We used [tool name, version] to
   [purpose, e.g. language editing of the Discussion / screening titles and abstracts as a
   second reviewer / drafting analysis code]; the authors reviewed and edited all output and take
   full responsibility for the content. This use is described in the [Acknowledgments / Methods].]
 - Preprint: [None.] / [A previous version was posted on [server] ([DOI / URL]) on [date].]
 - Suggested / excluded reviewers: [if the journal asks]]

Sincerely,
[Corresponding Author Name]
[Affiliation]
[Email]
```

声明的写法：

- **AI 使用**按 ICMJE Recommendations（2026 年 1 月更新，第 V 部分）：投稿时声明是否用了 AI 辅助技术；用了就在 cover letter
  和稿件相应位置都说明——写作辅助写进 Acknowledgments，数据收集 / 分析 / 作图写进 Methods；写明工具和用途；AI 不能
  列为作者。用本插件（Claude）起草、筛选文献、写分析代码或作图都算，工具名写实际使用的模型名称和版本。三处
  （cover letter、稿件、投稿系统的 "AI-assisted technology use" 字段）写法一致。
- **预印本**按 ICMJE 关于重叠发表的建议：投稿前或审稿期间发布的预印本都告知期刊并给出链接；期刊是否接受预印本以其
  作者指南为准（投稿系统 "Preprint" 字段同样填写）。
- ICMJE 原文在 2026-10 整理时无法直接打开（icmje.org 不可达），以上按其页面的检索摘要整理；投稿前到 icmje.org
  和期刊作者指南核对当前措辞（待核实）。
- 稿件没有的数字、"first / only" 一类说法不写进 cover letter（见 SKILL.md Paragraph 1）。

## 改投适配（Cascade Rewrite）— resubmission 重写机制

当论文被期刊 A 拒稿后改投期刊 B 时（由 `revision-response` 的改投决策触发后在此执行重写）：

1. **不要**只改期刊名就重投（编辑能看出来）
2. **修改 Paragraph 3** → 解释为什么期刊 B 的读者需要这个研究
3. **修改 Paragraph 1** → 根据期刊 B 的 scope 调整 hook 角度
4. **如果**前一个期刊的审稿意见有建设性 → 在 Paragraph 2 中提及已根据同行评审改进
   （可选措辞："This manuscript has been improved based on peer review feedback."，不点名前一期刊）
5. **生成**改投对比表：

| 元素 | 期刊 A 版本 | 期刊 B 版本 | 修改原因 |
|------|-------------|-------------|---------|
| Hook 角度 | [原角度] | [新角度] | [期刊 scope 差异] |
| 引用的期刊文章 | [期刊 A 的文章] | [期刊 B 的文章] | [匹配新读者群] |
