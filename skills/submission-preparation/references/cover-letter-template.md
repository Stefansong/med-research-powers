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

[Paragraph 1: Hook — 2-3 sentences, core finding + significance]

[Paragraph 2: Novelty — 3-4 sentences, comparison with existing work]

[Paragraph 3: Journal Fit — 2-3 sentences, why this journal + this audience]

[Paragraph 4: Declarations — 3-4 sentences, standard statements]

Sincerely,
[Corresponding Author Name]
[Affiliation]
[Email]
```

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
