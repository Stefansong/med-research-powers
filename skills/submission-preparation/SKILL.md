---
name: submission-preparation
description: Use when a manuscript is ready for submission — covers cover letter writing and submission system guidance. Triggers on "cover letter"、"投稿信"、"致编辑信"、"写推荐信给编辑"、"投稿系统"、"ScholarOne"、"EditorialManager"、"怎么投稿"、"上传论文"、"submission portal". Auto-triggers after journal-selection completes and before submission.
---

# Submission Preparation

## Overview

投稿准备的完整流程——Cover Letter 写作 + 投稿系统操作指南。Step 1 撰写高质量 Cover Letter 抓住编辑注意力；Step 2 引导完成投稿系统操作，避免因文件格式或元数据错误被退稿。

## When to Use

- `journal-selection` 完成后 → **自动触发**
- 用户要求写 cover letter / 投稿信
- 论文被拒后需要改投另一期刊 → 重写 cover letter
- 用户第一次向某期刊投稿
- 用户问"怎么投稿"、"投稿系统怎么用"

## When NOT to Use

- 论文尚未完成 → 先 `manuscript-writing`
- 目标期刊未确定 → 先 `journal-selection`
- 回复审稿意见 → `revision-response`
- `pre-submission-verification` 未通过 → 先修正问题

---

## Step 1: Cover Letter Writing

Cover Letter 是编辑看到的第一样东西。一封好的 Cover Letter 让编辑送审；一封差的 Cover Letter 导致直接 desk reject——即使论文本身很好。

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

### 期刊风格适配

不同期刊的 Cover Letter 期望不同：

| 期刊类型 | 风格偏好 |
|---------|---------|
| **Nature/Science/Cell** | 强调 broad impact，跨学科意义，简洁有力 |
| **Lancet/JAMA/BMJ/NEJM** | 强调 clinical relevance，patient impact，policy implication |
| **Specialty journals** | 强调领域内 gap，技术贡献，实用价值 |
| **Methods journals** | 强调方法创新，reproducibility，benchmark 结果 |
| **Open access (PLOS/BMC)** | 强调 rigor，透明性，数据可用性 |

### Cover Letter Output

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

### 改投适配（Cascade Rewrite）

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

### Red Flags — STOP

- Cover letter 超过 1 页 → 精简
- 没有提及目标期刊的任何特征 → 补充 Journal Fit
- "Dear Sir/Madam" → 查找编辑姓名（如果能确认）
- 声称论文"首次"/"唯一"但无依据 → 验证或删除
- 抄袭另一篇论文的 cover letter → 重写

---

## Step 2: Submission System Guide

投稿系统操作错误是被退稿的常见原因之一。文件格式不对、元数据填错、漏传 supplementary 都会导致系统自动退回。

### 2.1: 识别投稿系统

| 投稿系统 | 使用期刊 |
|---------|---------|
| **ScholarOne / Manuscript Central** | Lancet 系列、JAMA 系列、BMJ、Nature 系列、多数 Wiley/T&F 期刊 |
| **Editorial Manager** | Cell 系列、Science、Elsevier 部分期刊、Springer Nature 部分 |
| **Bench>Press** | PLOS 系列 |
| **eJManager** | 部分中文 SCI 期刊 |
| **OJS (Open Journal Systems)** | 部分开源/学术期刊 |

### 2.2: 文件准备清单

**必传文件：**
- [ ] Main manuscript（.docx 优先，部分期刊接受 .pdf 或 LaTeX）
- [ ] Cover Letter（通常粘贴到系统文本框，非上传文件）
- [ ] Figures（单独上传，TIFF/EPS/PDF 格式，≥300 DPI）
- [ ] Tables（嵌入正文或单独上传，取决于期刊）
- [ ] Title Page（部分期刊要求单独上传，含所有作者信息）

**可能需要的文件：**
- [ ] Supplementary Materials（附录、扩展数据）
- [ ] Reporting Checklist（CONSORT/STROBE/PRISMA 填好的 checklist）
- [ ] Conflict of Interest forms（某些期刊要求 ICMJE COI 表格）
- [ ] Ethics approval certificate（伦理批准扫描件）
- [ ] Data Availability Statement
- [ ] Author contribution statement（CRediT taxonomy）

**文件命名规范：**
- 避免空格和特殊字符
- 推荐格式：`Figure1.tiff`、`Table1.docx`、`SupplementaryMethods.pdf`
- 某些系统自动重命名，无需担心

### 2.3: 元数据填写

投稿系统通常要求填写：

| 字段 | 注意事项 |
|------|---------|
| Article type | Original Article / Review / Letter / Brief Communication — 选错会被退 |
| Title | 与正文标题完全一致 |
| Running title | ≤50 字符，某些系统必填 |
| Abstract | 粘贴全文，检查字数限制 |
| Keywords | 3-6 个，用 MeSH 术语优先 |
| Author list | 顺序、单位、邮箱必须准确；通讯作者标注 |
| ORCID | 越来越多期刊强制要求通讯作者 ORCID |
| Funding | 基金号、资助机构全称 |
| COI | 所有作者的利益冲突声明 |
| Suggested reviewers | 2-4 位，避免同单位或合作者 |
| Excluded reviewers | 有利益冲突的审稿人 |
| Trial registration | 临床试验注册号（如适用） |

### 2.4: 上传与提交

1. **上传顺序**：通常 manuscript → figures → tables → supplementary → cover letter
2. **PDF 预览**：提交前系统会生成合并 PDF — **必须检查**
   - 图表是否正确嵌入
   - 公式是否正常显示
   - 页码是否连续
   - 作者信息是否完整
3. **最终提交**：点击 Submit 后会收到确认邮件
4. **保存确认**：截图或保存确认邮件中的 manuscript ID

### 2.5: 提交后跟踪

| 状态 | 含义 | 预计时间 |
|------|------|---------|
| Submitted | 已提交，等待编辑初审 | — |
| With Editor | 编辑在看 | 1-2 周 |
| Under Review | 已送审 | 2-8 周 |
| Decision Made | 有结果了 | — |
| Revise | 修改后重投 | — |

**正常审稿周期**：4-12 周。超过 12 周可发礼貌催稿邮件。

---

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "Cover letter 就是走个形式" | 高 IF 期刊的 desk reject 有 40%+ 在编辑看完 cover letter 后决定 |
| "越详细越好" | 超过 1 页 = 编辑不看。简洁是尊重 |
| "附上全部摘要" | 编辑会看论文本身，cover letter 不要复制粘贴 |
| "说 'novel' 就够了" | 没有具体比较的 'novel' 是空话 |
| "不需要提审稿人建议" | 好的审稿人建议帮编辑省时间，增加好感 |
| "被拒后原封不动投下一个" | 编辑可能是同一圈子的人，会看出来 |
| "PDF 预览不看也行" | 图表错位/公式乱码 = desk reject |
| "Suggested reviewers 随便填" | 好的建议能加速审稿 |
| "COI 声明写 None 就行" | 虚假 COI 声明 = 学术不端 |
| "文件大小没关系" | 某些系统限制 10MB，超大文件需压缩 |
| "投完不管了" | 跟踪状态，超时催稿 |

## Convergence

当以下条件全部满足时完成：
1. Cover Letter 4 段结构完整（Step 1）
2. Hook 有具体的核心 claim（不是空泛描述）
3. Novelty 有与具体文献的比较
4. Journal Fit 引用了目标期刊的近期文章
5. 所有必要声明已包含
6. Cover Letter 总长度不超过 1 页（约 350-450 words）
7. 所有必传文件已准备且格式正确（Step 2）
8. 元数据已完整填写（Step 2）
9. PDF 预览已检查无误（Step 2）
10. 用户已完成提交或知道如何操作

## 衔接规则

### 前置依赖
- **必须**有完成的论文（`manuscript-writing`）
- **必须**有确定的目标期刊（`journal-selection`）
- **必须**有 `pre-submission-verification` 全部通过

### 被动触发
- `journal-selection` 完成后 → 自动触发
- 论文被拒后需要改投 → 用户请求触发

### 强制衔接
- 如果 `pre-submission-verification` 未通过 → 阻止生成 cover letter

### 后续
- 投稿成功 → 等待审稿结果
- 收到审稿意见 → `revision-response`
