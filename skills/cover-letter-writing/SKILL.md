---
name: cover-letter-writing
description: Use when a manuscript is ready for submission and needs a cover letter. Triggers on "cover letter"、"投稿信"、"致编辑信"、"写推荐信给编辑". Auto-triggers after journal-selection completes and before submission.
---

# Cover Letter Writing

## Overview

Cover Letter 是编辑看到的第一样东西。一封好的 Cover Letter 让编辑送审；一封差的 Cover Letter 导致直接 desk reject——即使论文本身很好。

## When to Use

- `journal-selection` 完成后 → **自动触发**
- 用户要求写 cover letter / 投稿信
- 论文被拒后需要改投另一期刊 → 重写 cover letter

## When NOT to Use

- 论文尚未完成 → 先 `manuscript-writing`
- 目标期刊未确定 → 先 `journal-selection`
- 回复审稿意见 → `responding-to-reviewers`

## Workflow: 4-Paragraph Structure

**原则：不超过 1 页。编辑每天看 20+ cover letters，你有 30 秒抓住注意力。**

### Paragraph 1: Hook（为什么这个发现重要）

- 一句话点明研究解决的问题
- 连接到 clinical/public health significance
- **禁止**以 "Dear Editor, we are pleased to submit..." 开头（太老套）
- **推荐**以研究发现的核心 claim 开头

> ✅ "Early AI-assisted detection of pancreatic cancer on CT could reduce stage IV diagnosis by 30%—yet no validated model exists for routine screening."
>
> ❌ "We are pleased to submit our manuscript entitled '...' for your consideration."

### Paragraph 2: Novelty（比现有研究好在哪）

- 明确说明与最相关的 2-3 篇已发表研究的区别
- 用具体数据/方法差异，不用"comprehensive"、"novel"等空洞词
- **模板：** "Unlike [Author et al., Year] who [方法/局限], we [改进点], achieving [具体结果]."

### Paragraph 3: Journal Fit（为什么投这个期刊）

- 引用该期刊近期发表的 1-2 篇相关文章
- 说明本研究如何补充/延伸这些工作
- 说明目标读者群为什么需要这个研究
- **禁止**只说"your journal is prestigious"（编辑知道，不需要你说）

### Paragraph 4: Declarations（必要声明）

- 论文未在其他期刊审稿中（mandatory）
- 所有作者已审阅并同意投稿（mandatory）
- 利益冲突声明（如有）
- 临床试验注册号（如适用）
- 建议审稿人 2-3 位（如期刊要求）
- 排除审稿人（如有利益冲突）

## 期刊风格适配

不同期刊的 Cover Letter 期望不同：

| 期刊类型 | 风格偏好 |
|---------|---------|
| **Nature/Science/Cell** | 强调 broad impact，跨学科意义，简洁有力 |
| **Lancet/JAMA/BMJ/NEJM** | 强调 clinical relevance，patient impact，policy implication |
| **Specialty journals** | 强调领域内 gap，技术贡献，实用价值 |
| **Methods journals** | 强调方法创新，reproducibility，benchmark 结果 |
| **Open access (PLOS/BMC)** | 强调 rigor，透明性，数据可用性 |

## Output

生成 `cover-letter.md`：

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

## 改投适配（Cascade Rewrite）

当论文被期刊 A 拒稿后改投期刊 B 时：

1. **不要**只改期刊名就重投（编辑能看出来）
2. **修改 Paragraph 3** → 解释为什么期刊 B 的读者需要这个研究
3. **修改 Paragraph 1** → 根据期刊 B 的 scope 调整 hook 角度
4. **如果**前一个期刊的审稿意见有建设性 → 在 Paragraph 2 中提及已根据同行评审改进
5. **生成**改投对比表：

| 元素 | 期刊 A 版本 | 期刊 B 版本 | 修改原因 |
|------|-------------|-------------|---------|
| Hook 角度 | [原角度] | [新角度] | [期刊 scope 差异] |
| 引用的期刊文章 | [期刊 A 的文章] | [期刊 B 的文章] | [匹配新读者群] |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "Cover letter 就是走个形式" | 高 IF 期刊的 desk reject 有 40%+ 在编辑看完 cover letter 后决定 |
| "越详细越好" | 超过 1 页 = 编辑不看。简洁是尊重 |
| "附上全部摘要" | 编辑会看论文本身，cover letter 不要复制粘贴 |
| "说 'novel' 就够了" | 没有具体比较的 'novel' 是空话 |
| "不需要提审稿人建议" | 好的审稿人建议帮编辑省时间，增加好感 |
| "被拒后原封不动投下一个" | 编辑可能是同一圈子的人，会看出来 |

## Convergence

当以下条件满足时完成：
1. 4 段结构完整
2. Hook 有具体的核心 claim（不是空泛描述）
3. Novelty 有与具体文献的比较
4. Journal Fit 引用了目标期刊的近期文章
5. 所有必要声明已包含
6. 总长度不超过 1 页（约 350-450 words）

## Red Flags — STOP

- Cover letter 超过 1 页 → 精简
- 没有提及目标期刊的任何特征 → 补充 Journal Fit
- "Dear Sir/Madam" → 查找编辑姓名（如果能确认）
- 声称论文"首次"/"唯一"但无依据 → 验证或删除
- 抄袭另一篇论文的 cover letter → 重写

## 衔接规则

### 前置依赖
- **必须**有完成的论文（`manuscript-writing`）
- **必须**有确定的目标期刊（`journal-selection`）

### 被动触发
- `journal-selection` 完成后 → 自动触发
- 论文被拒后需要改投 → 用户请求触发

### 强制衔接
- 完成后 → 可以进入投稿流程
- 如果 `pre-submission-verification` 未通过 → 阻止生成 cover letter
