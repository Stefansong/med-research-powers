---
name: manuscript-export
description: Use when exporting manuscript markdown into journal-formatted .docx for submission. Triggers on "导出Word"、"生成docx"、"投稿格式"、"排版"、"格式化论文"、"export manuscript"、"docx". Auto-triggers after writing.
---

# Manuscript Export

## Overview

将 Markdown 稿件导出为符合目标期刊排版规范的 .docx 文件。读取 `journal-templates.yaml` 自动应用格式，一键生成投稿用文件。

## When to Use

- 论文各章节写好后需要导出 .docx 投稿
- 需要重新排版为另一个期刊的格式
- 需要生成 Supplementary Materials .docx
- 用户说"帮我排版"、"导出 Word"

## When NOT to Use

- 还在写论文内容 → `manuscript-writing`
- 需要生成图表 → `figure-generation`
- 仅需要格式检查 → `reporting-standards`

## Prerequisites

- `manuscript/` 目录下至少有 1 个章节 .md 文件
- `journal-selection-report.md`（确定目标期刊）或用户指定期刊名
- Python `python-docx` 包已安装

## Workflow

### Step 1: 确定目标期刊格式

```
1. 读取 journal-selection-report.md → 获取首选期刊
2. 从 ../manuscript-writing/references/journal-templates.yaml 加载期刊模板
3. 如期刊不在模板库 → 用 WebSearch 检索 "Instructions for Authors"
   → 提取关键规范 → 临时构建格式配置
4. 向用户确认格式配置
```

### Step 2: 收集稿件文件

```
扫描 manuscript/ 目录:
  ├── title-page.md
  ├── abstract.md
  ├── introduction.md
  ├── results.md
  ├── discussion.md
  ├── methods.md
  ├── references.md
  └── supplementary.md (可选)

检查:
  → 哪些文件存在？
  → 哪些是 placeholder（含 <!-- PLACEHOLDER --> 标记）？
  → 缺失文件 → 警告用户但不阻断（允许部分导出）
```

### Step 3: 生成 .docx

调用现成脚本 `scripts/export_docx.py` 完成导出，**不要手写转换代码**：

```bash
python3 scripts/export_docx.py \
  --manuscript-dir ./manuscript \
  --journal <journal-id> \
  --yaml ../manuscript-writing/references/journal-templates.yaml \
  --output manuscript/manuscript.docx \
  --report export-report.md
```

脚本自动完成：
- 按期刊家族（Nature / Lancet / JAMA / IEEE / 标准 IMRaD）设置字体、字号、行距、页边距
- 按期刊要求排列章节顺序（见下表）
- Markdown → docx 元素转换（见转换规则表）
- 表格格式化（表头加粗 + 灰底）、Nature/Lancet/JAMA 特殊要素
- 统计字数 / 参考文献 / 表格、Placeholder 检测、生成导出报告

> 期刊 ID 必须存在于 `../manuscript-writing/references/journal-templates.yaml`；
> 未知期刊先走 Step 1 的 WebSearch 流程补全模板，再导出。

#### 章节顺序（按期刊要求）

| 期刊家族 | 章节顺序 |
|---------|---------|
| **Nature 系** | Title → Abstract → Introduction → Results → Discussion → Methods → References |
| **Lancet 系** | Title → Abstract → Research in Context → Introduction → Methods → Results → Discussion → References |
| **JAMA 系** | Title → Key Points → Abstract → Introduction → Methods → Results → Discussion → References |
| **标准 IMRaD** | Title → Abstract → Introduction → Methods → Results → Discussion → References |

#### Markdown → docx 转换规则

| Markdown | docx 元素 |
|---------|----------|
| `# Heading` | Heading 1 (bold, 14pt) |
| `## Heading` | Heading 2 (bold, 13pt) |
| `### Heading` | Heading 3 (bold, 12pt) |
| `**bold**` | Bold run |
| `*italic*` | Italic run |
| `^superscript^` | Superscript run |
| `~subscript~` | Subscript run |
| `- item` | Bullet list |
| `1. item` | Numbered list |
| `> quote` | Block quote (italic, indented) |
| `<!-- comment -->` | 过滤掉，不输出 |
| 空行 | 段落分隔 |
| `\| table \|` | docx Table (带边框) |

### Step 4: 质量检查

导出后自动检查：

```
□ 字数统计（与期刊限制比较）
  → 正文字数（不含 Abstract/Methods/References）
  → Abstract 字数
  → 如超限 → 警告并标注超出多少
□ 参考文献数量（与期刊限制比较）
□ 图表数量（与期刊限制比较）
□ 格式验证
  → 字体是否正确
  → 行距是否正确
  → 章节顺序是否正确
  → 页边距是否正确
□ Placeholder 检测
  → 搜索 [pending]、[TBD]、[TODO]、PLACEHOLDER
  → 列出所有 placeholder 位置
```

### Step 5: 输出报告

```
────────────────────────────────────────
✅ Manuscript Export Complete

📄 生成的文件:
  • manuscript.docx (主文件) — [N] 页, [N] 字
  • supplementary.docx (补充材料) — [如生成]

📏 格式检查:
  • 期刊: [journal name]
  • 字数: [N] / [limit] ✅ or ⚠️ 超出 [N] 字
  • 参考文献: [N] / [limit] ✅ or ⚠️
  • 图表: [N] / [limit] ✅ or ⚠️
  • 章节顺序: ✅ [Nature/IMRaD/...]

⚠️ Placeholder 警告:
  • [file:line] — "[placeholder text]"

➡️ 建议下一步: pre-submission-verification
────────────────────────────────────────
```

## Output

| 文件 | 说明 |
|------|------|
| `manuscript/manuscript.docx` | 投稿主文件 |
| `manuscript/supplementary.docx` | 补充材料（如有） |
| `manuscript/title-page.docx` | 标题页（部分期刊要求单独上传） |
| `export-report.md` | 导出质量报告 |

## Journal Family Quick Reference

| 家族 | 字体 | 行距 | 章节顺序 | 特殊要求 |
|------|------|------|---------|---------|
| Nature | Times New Roman 12pt | 2.0 | I-R-D-M | Reporting Summary |
| Lancet | Times New Roman 12pt | 2.0 | I-M-R-D | Research in Context panel |
| JAMA | Times New Roman 11pt | 2.0 | I-M-R-D | Key Points box |
| Elsevier (EU, JU) | Times New Roman 12pt | 2.0 | I-M-R-D | Highlights (3-5 bullets) |
| Springer (SE, IJCARS) | Times New Roman 12pt | 2.0 | I-M-R-D | — |
| IEEE (JBHI, TMI) | Times New Roman 10pt | 1.0 | I-RW-M-E-R-D-C | Double-column, 8 pages |
| Wiley (BJU) | Times New Roman 12pt | 2.0 | I-M-R-D | — |

**详细规范:** 加载 `../manuscript-writing/references/journal-templates.yaml`

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "直接复制粘贴到 Word 就行" | Markdown 格式不会自动转换，会丢失结构和格式 |
| "所有期刊格式都一样" | Nature 系 Methods 放最后，JAMA 需要 Key Points，Lancet 需要 RiC panel |
| "字数不需要检查" | 超限会被 desk rejection，必须导出后检查 |
| "表格用截图就行" | 多数期刊要求可编辑的表格，不接受图片形式 |
| "参考文献手动排版" | 用 pubmed-search Mode 6 自动格式化，减少人工错误 |
| "Supplementary 不需要格式" | 部分期刊对 Supplementary 有单独的格式要求 |

## Convergence

当以下条件全部满足时完成：
1. .docx 文件已生成
2. 格式与目标期刊匹配（字体/行距/章节顺序/页边距）
3. 字数/图表/参考文献数量检查完成
4. Placeholder 已清零或已标注警告
5. 导出报告已生成

## Red Flags — STOP

- **不要在导出时修改论文内容** — 本 skill 只负责格式转换，内容修改回 `manuscript-writing`
- **不要忽略字数超限** — 必须明确告知用户
- **不要跳过 Placeholder 检测** — Placeholder 投稿会被 desk reject

## 衔接规则

### 前置依赖
- **必须**有 `manuscript/` 下至少 1 个章节 .md 文件
- **推荐**有 `journal-selection-report.md`（确定格式）

### 被上层 skill 调用
- `manuscript-writing` 完成后 → 自动建议触发本 skill
- `revision-response` 修改后 → 重新导出

### 强制衔接
- 导出完成后 → 建议 `pre-submission-verification`

### 可选衔接
- 需要切换目标期刊 → 重新加载模板 → 重新导出
- 需要格式化参考文献 → 调用 `pubmed-search` Mode 6
