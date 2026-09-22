---
name: submission-preparation
description: Use when the verified, exported manuscript needs a cover letter and submission-portal guidance. Triggers on "cover letter"、"投稿信"、"致编辑信"、"投稿系统"、"ScholarOne"、"怎么投稿"、"submission portal".
---

# Submission Preparation

## Overview

投稿准备的完整流程——Cover Letter 写作 + 投稿系统操作指南。Step 1 撰写高质量 Cover Letter 抓住编辑注意力；
Step 2 引导完成投稿系统操作，避免因文件格式或元数据错误被退稿。

## When to Use

- `pre-submission-verification` 6 个 Gate 全部通过、且 `manuscript-export` 已生成 `manuscript.docx` + `export-report.md` 后 → **自动进入**（主线最后一步）
- 用户要求写 cover letter / 投稿信
- 论文被拒后需要改投另一期刊 → 由 `revision-response` 的改投决策触发，重写 cover letter
- 用户问"怎么投稿"、"投稿系统怎么用"

## When NOT to Use

- 论文尚未完成 → 先 `manuscript-writing`
- 目标期刊未确定 → 先 `journal-selection`
- 回复审稿意见 → `revision-response`
- `pre-submission-verification` 未通过或 `manuscript-export` 未完成 → 先补齐（本 skill 不生成 .docx）

## Workflow

### Step 0: 复核目标期刊（软确认）

目标期刊是软确认，投稿前复核一次：读取 `journal-selection-report.md` 与
`submission-readiness-report.md` 的 Target Journal 是否一致；用户想换刊 → 回 `journal-selection`，
换刊后 Gate 6（字数/格式）和 `manuscript-export` 需要重跑。

### Step 1: Cover Letter Writing

Cover Letter 是编辑看到的第一样东西。一封好的 Cover Letter 让编辑送审；一封差的 Cover Letter 可能导致
直接 desk reject——即使论文本身很好。

**原则：不超过 1 页。编辑每天看很多 cover letter，你只有几十秒抓住注意力。**

#### Paragraph 1: Hook（为什么这个发现重要）

- 一句话点明研究解决的问题
- 连接到 clinical/public health significance
- **禁止**以 "Dear Editor, we are pleased to submit..." 开头（太老套）
- **推荐**以研究发现的核心 claim 开头

> ✅ "Early AI-assisted detection of pancreatic cancer on CT could reduce stage IV diagnosis by 30%—yet no validated model exists for routine screening."
>
> ❌ "We are pleased to submit our manuscript entitled '...' for your consideration."

#### Paragraph 2: Novelty（比现有研究好在哪）

- 明确说明与最相关的 2-3 篇已发表研究的区别
- 用具体数据/方法差异，不用"comprehensive"、"novel"等空洞词
- **模板：** "Unlike [Author et al., Year] who [方法/局限], we [改进点], achieving [具体结果]."

#### Paragraph 3: Journal Fit（为什么投这个期刊）

- 引用该期刊近期发表的 1-2 篇相关文章
- 说明本研究如何补充/延伸这些工作
- 说明目标读者群为什么需要这个研究
- **禁止**只说"your journal is prestigious"（编辑知道，不需要你说）

#### Paragraph 4: Declarations（必要声明）

- 论文未在其他期刊审稿中（mandatory）
- 所有作者已审阅并同意投稿（mandatory）
- 利益冲突声明（如有）
- 临床试验注册号（如适用）
- 建议审稿人 2–4 位（如期刊要求；避免同单位或合作者）
- 排除审稿人（如有利益冲突）

#### 期刊风格适配 + 模板

不同期刊的 Cover Letter 期望不同（强调 impact / clinical relevance / 领域 gap /
方法创新 / rigor）。完整的**期刊风格对照表**和**4 段 `cover-letter.md` 模板**见
`references/cover-letter-template.md`。

#### 改投适配（Cascade Rewrite）

本 skill 是全插件 cover-letter / cascade-rewrite 机制的 **OWNER**。被期刊 A 拒稿后改投
期刊 B 时，核心原则：**不要只改期刊名重投**——重写 Paragraph 1（hook 角度）和 Paragraph 3
（journal fit），并视情况在 Paragraph 2 提及已据同行评审改进。完整的重写步骤和改投对比表模板见
`references/cover-letter-template.md`。

（注：`revision-response` 只决定"是否改投"；一旦决定改投，重写机制由本 skill 负责。）

### Step 2: Submission System Guide

投稿系统操作错误是被退稿的常见原因之一。文件格式不对、元数据填错、漏传 supplementary 都会导致系统自动退回。

判断逻辑（reasoning）保留在此；所有静态查表见 `references/submission-systems.yaml`。

#### 2.1: 识别投稿系统

先用 `${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --id <期刊id>`
读该刊的 `system` 字段；没有条目时按出版商家族查 `references/submission-systems.yaml`
（`submission_systems`）：ScholarOne（JAMA 系列、BMJ、多数 Wiley/T&F）、Editorial Manager（Lancet 系列、
Cell、Elsevier、PLOS、多数 Springer）、eJournalPress（Nature 系列 MTS、Science、NEJM、PNAS）、
Snapp（Springer Nature 新刊）、OJS（部分开源期刊）。期刊会迁移系统，**以期刊 Submit 页为准**。

#### 2.2: 文件准备

必传文件（manuscript.docx / cover letter / figures / tables / title page）+ 可能需要的文件
（supplementary / reporting checklist（`reporting-checklist-<standard>.md`）/ COI / 伦理批准 /
数据可用性声明 / CRediT）。完整清单和命名规范见 `references/submission-systems.yaml`（`file_preparation`）。
`manuscript.docx` 来自 `manuscript-export`，本 skill 不重新导出。

#### 2.3: 元数据填写

投稿系统要求填写 article type、title、abstract、keywords、author list、ORCID、funding、
COI、suggested/excluded reviewers、trial registration 等。**article type 选错会被直接退**，
**title 必须与正文完全一致**。完整字段及注意事项见 `references/submission-systems.yaml`
（`metadata_fields`）。

#### 2.4: 上传与提交

按 manuscript → figures → tables → supplementary → cover letter 顺序上传。**提交前必须检查
系统生成的合并 PDF**（图表嵌入、公式、页码、作者信息）。提交后保存 manuscript ID。
完整步骤见 `references/submission-systems.yaml`（`upload_and_submit`）。

#### 2.5: 提交后跟踪

状态含义（Submitted / With Editor / Under Review / Decision Made / Revise）及预计时间见
`references/submission-systems.yaml`（`post_submission_status`）。**正常审稿周期 4-12 周，
超过 12 周可发礼貌催稿邮件。**

### Step 3: 收尾

1. 输出 3–5 行摘要（cover letter 就绪、投稿系统、待传文件清单、manuscript ID 待填）——轻量确认。
2. 更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：
   `completed_skills` 追加 submission-preparation 及产物、`next_step` 设为 "等待审稿意见 → revision-response"）。

## Output

| 文件 | 内容 | 来源 |
|------|------|------|
| `cover-letter.md` | 4 段 Cover Letter（Hook / Novelty / Journal Fit / Declarations） | Step 1，模板见 `references/cover-letter-template.md` |
| 改投对比表（嵌入 cover-letter.md 或单独） | 期刊 A vs B 的 hook 角度、引用文章、修改原因 | Cascade Rewrite，模板见 `references/cover-letter-template.md` |
| 投稿操作记录（写入 `submission-log.md`） | 投稿系统、已传文件清单、metadata、manuscript ID、提交日期 | Step 2 |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "Cover letter 就是走个形式" | 编辑在送审前先读 cover letter，它决定论文是否进入审稿 |
| "越详细越好" | 超过 1 页 = 编辑不看。简洁是尊重 |
| "附上全部摘要" | 编辑会看论文本身，cover letter 不要复制粘贴 |
| "说 'novel' 就够了" | 没有具体比较的 'novel' 是空话 |
| "不需要提审稿人建议" | 好的审稿人建议帮编辑省时间，增加好感 |
| "被拒后原封不动投下一个" | 编辑可能是同一圈子的人，会看出来 |
| "PDF 预览不看也行" | 图表错位/公式乱码 = desk reject |
| "Suggested reviewers 随便填" | 2–4 位、避免同单位/合作者；好的建议能加速审稿 |
| "COI 声明写 None 就行" | 虚假 COI 声明 = 学术不端 |
| "Nature 系用 Editorial Manager" | Nature 系用自家 MTS（eJP 架构）；Lancet 才是 Editorial Manager |
| "投完不管了" | 跟踪状态，超时催稿 |

## Red Flags — STOP

- Cover letter 超过 1 页 → 精简
- 没有提及目标期刊的任何特征 → 补充 Journal Fit
- "Dear Sir/Madam" → 查找编辑姓名（如果能确认）
- 声称论文"首次"/"唯一"但无依据 → 验证或删除
- 抄袭/原封不动复用另一篇论文（或前一期刊）的 cover letter → 重写
- 虚假 COI 声明 → 学术不端，必须如实填写
- 未检查系统生成的合并 PDF 就点 Submit → 图表错位/公式乱码 = desk reject
- `pre-submission-verification` 未通过或没有 `manuscript.docx` 就投稿 → STOP，先补齐

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
10. 用户已完成提交或知道如何操作，`.mrp-state.json` 已更新

## 衔接规则

### 强制衔接（不可跳过）
- 前接 `manuscript-export`（`manuscript.docx` + `export-report.md`）；`pre-submission-verification` 必须已全部通过
- 投稿后收到审稿意见 → `revision-response`
- 完成后 → 更新 `.mrp-state.json`

### 前置依赖（不满足则阻止）
- **必须**有完成的论文（`manuscript-writing`）与导出稿（`manuscript-export`）
- **必须**有确定的目标期刊（`journal-selection`，投稿前复核一次）
- **必须**有 `submission-readiness-report.md` 且 6 Gate 全部通过

### 可选衔接
- 论文被拒后需要改投 → 由 `revision-response` 做改投决策 → `journal-selection` 重选 → 本 skill 重写 cover letter
- 用户想换目标期刊 → `journal-selection`（换刊后重跑 Gate 6 与 `manuscript-export`）
