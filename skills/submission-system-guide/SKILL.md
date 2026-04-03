---
name: submission-system-guide
description: Use when the user is ready to submit a manuscript and needs guidance on using journal submission systems. Triggers on "投稿系统"、"ScholarOne"、"EditorialManager"、"怎么投稿"、"上传论文"、"submission portal". Auto-triggers after cover-letter-writing completes.
---

# Submission System Guide

## Overview

投稿系统操作错误是被退稿的常见原因之一。文件格式不对、元数据填错、漏传 supplementary 都会导致系统自动退回。本 skill 引导用户完成投稿系统操作。

## When to Use

- 用户第一次向某期刊投稿
- `cover-letter-writing` 完成后 → 建议触发
- 用户问"怎么投稿"、"投稿系统怎么用"

## When NOT to Use

- 论文未完成 → 先 `manuscript-writing`
- 目标期刊未确定 → 先 `journal-selection`
- Cover Letter 未写 → 先 `cover-letter-writing`

## Workflow: Pre-Upload Checklist + System Guide

### Step 1: 识别投稿系统

| 投稿系统 | 使用期刊 |
|---------|---------|
| **ScholarOne / Manuscript Central** | Lancet 系列、JAMA 系列、BMJ、Nature 系列、多数 Wiley/T&F 期刊 |
| **Editorial Manager** | Cell 系列、Science、Elsevier 部分期刊、Springer Nature 部分 |
| **Bench>Press** | PLOS 系列 |
| **eJManager** | 部分中文 SCI 期刊 |
| **OJS (Open Journal Systems)** | 部分开源/学术期刊 |

### Step 2: 文件准备清单

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

### Step 3: 元数据填写

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

### Step 4: 上传与提交

1. **上传顺序**：通常 manuscript → figures → tables → supplementary → cover letter
2. **PDF 预览**：提交前系统会生成合并 PDF — **必须检查**
   - 图表是否正确嵌入
   - 公式是否正常显示
   - 页码是否连续
   - 作者信息是否完整
3. **最终提交**：点击 Submit 后会收到确认邮件
4. **保存确认**：截图或保存确认邮件中的 manuscript ID

### Step 5: 提交后跟踪

| 状态 | 含义 | 预计时间 |
|------|------|---------|
| Submitted | 已提交，等待编辑初审 | — |
| With Editor | 编辑在看 | 1-2 周 |
| Under Review | 已送审 | 2-8 周 |
| Decision Made | 有结果了 | — |
| Revise | 修改后重投 | — |

**正常审稿周期**：4-12 周。超过 12 周可发礼貌催稿邮件。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "PDF 预览不看也行" | 图表错位/公式乱码 = desk reject |
| "Suggested reviewers 随便填" | 好的建议能加速审稿 |
| "COI 声明写 None 就行" | 虚假 COI 声明 = 学术不端 |
| "文件大小没关系" | 某些系统限制 10MB，超大文件需压缩 |
| "投完不管了" | 跟踪状态，超时催稿 |

## Convergence

当以下条件满足时完成：
1. 所有必传文件已准备且格式正确
2. 元数据已完整填写
3. PDF 预览已检查无误
4. 用户已完成提交或知道如何操作

## 衔接规则

### 前置依赖
- **必须**有 `cover-letter-writing` 完成
- **必须**有 `pre-submission-verification` 全部通过

### 被动触发
- `cover-letter-writing` 完成后 → 建议触发

### 后续
- 投稿成功 → 等待审稿结果
- 收到审稿意见 → `responding-to-reviewers`
