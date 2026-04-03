---
name: manuscript-writing
description: Use when drafting a medical research manuscript in IMRaD structure. Triggers on "写论文"、"写稿子"、"写Introduction"、"写Methods"、"写Discussion"、"manuscript"、"投稿". Must have completed analysis results before writing.
---

# Manuscript Writing

## Overview

基于已完成的分析结果按 IMRaD 结构写论文。不允许虚构数据或结果。

## When to Use

写论文、写摘要、写各个章节。

## When NOT to Use

- 还没有分析结果 → 先完成 `statistical-analysis`
- 格式排版 → `medical-paper-formatter`（如已安装）
- 检查投稿规范 → `reporting-standards`

## Prerequisites (block if missing)

- `research-question.md` — 科学问题定义
- `analysis-plan.md` — 分析计划
- `results-summary.md` — 分析结果
- `journal-selection-report.md` — 目标期刊（决定格式）
- 图表文件

缺少任何一项 → 先触发对应技能。

## Journal Template（期刊排版规范）

**写作前必须加载目标期刊模板。** 模板文件：`references/journal-templates.yaml`

```
加载流程：
1. 从 journal-selection-report.md 获取目标期刊
2. 加载 journal-templates.yaml 中对应模板
3. 按模板设定字数限制、摘要格式、章节结构、参考文献格式
4. 写作过程中实时检查是否超限
```

**模板库覆盖 40+ 期刊，按专科分类（持续扩充）：**

| 类别 | 期刊 |
|------|------|
| **综合顶刊** | Nature, Nature Medicine, Lancet, NEJM, JAMA, BMJ, Annals of Internal Medicine |
| **肿瘤** | JCO, Lancet Oncology, JAMA Oncology, Annals of Oncology, Cancer Research |
| **外科** | Annals of Surgery, JAMA Surgery, BJS, Surgical Endoscopy |
| **泌尿** | European Urology, Journal of Urology, BJU International |
| **心血管** | European Heart Journal, JACC, Circulation |
| **消化/肝病** | Gastroenterology, Gut, Hepatology |
| **呼吸** | Lancet Respiratory, AJRCCM, CHEST |
| **神经** | Lancet Neurology, Neurology, JAMA Neurology |
| **影像** | Radiology, European Radiology, Medical Image Analysis |
| **AI/数字健康** | npj Digital Medicine, Lancet Digital Health, JMIR, IEEE JBHI |
| **儿科** | Lancet Child, JAMA Pediatrics, Pediatrics |
| **骨科** | JBJS, CORR |
| **眼科/皮肤/病理** | Ophthalmology, JAMA Dermatology, Modern Pathology 等 |
| **感染/内分泌/肾脏/精神** | Lancet ID, Diabetes Care, JASN, Lancet Psychiatry 等 |
| **系统综述** | Cochrane Database, Systematic Reviews |
| **开放获取** | PLOS Medicine, PLOS ONE, Nature Communications, Scientific Reports |
| **中国 SCI** | Chinese Medical Journal, Science Bulletin, Signal Transduction, eClinicalMedicine |

**期刊家族速查：**
- **Lancet 家族**（均要求 Research in Context panel）：10 个子刊
- **JAMA 家族**（均要求 Key Points box）：8 个子刊
- **Nature 家族**（均要求 Reporting Summary）：6 个子刊

详见 `references/journal-templates.yaml`（含每个期刊的字数、摘要格式、参考文献样式、特殊要求、投稿系统）。

**如果目标期刊不在模板库中：** 用 WebSearch 检索期刊的 "Instructions for Authors" 页面，提取关键规范并补充到 `journal-templates.yaml`。

## Writing Order

**不按论文顺序，按推荐的写作效率顺序：**

1. **Methods** — 最客观，最容易写
2. **Results** — 基于已有分析结果
3. **Introduction** — 现在更清楚 gap 在哪
4. **Discussion** — 需要最多思考
5. **Abstract** — 概括已完成全文
6. **Title** — 精炼到一句话

## Section Rules

**Methods**: 研究设计、参与者、变量定义、统计方法（可复现程度）、伦理声明、样本量、软件版本
**Results**: 参与者流程图 → 基线表 → 主要结局 → 次要结局 → 亚组。**禁止**在 Results 讨论意义。
**Introduction**: 漏斗形（背景→已知→gap→本研究目的）。通常 3-4 段。
**Discussion**: 主要发现→与文献比较→机制→临床意义→局限性→结论。**禁止**引入 Results 中没有的数据。
**Abstract**: 结构化（Background/Methods/Results/Conclusions），250-350 字。
**Title**: 含研究设计类型 + 关键变量，≤20 词。

## Language Rules

- Methods/Results: 过去时
- Introduction/Discussion: 引用已有知识用现在时
- 避免 "significantly" 的非统计学用法
- 避免 "prove"（用 "support" / "suggest"）

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "先写 Introduction" | Methods 最容易，先写它效率最高 |
| "Results 里解释一下结果" | Results 只放数据，解释留给 Discussion |
| "Discussion 补充几个新分析" | 禁止引入 Results 没有的数据 |
| "Abstract 最后随便改改" | Abstract 是审稿人最先读的，必须精心写 |
| "用 significantly 强调重要性" | 在论文里 significantly 只能指统计学显著 |
| "结论可以写得激进一点" | 结论不能超出数据支持的范围 |

## Output 文件生成

### Markdown 输出（默认）

所有章节以 Markdown 格式生成，便于版本控制和协作编辑：

```
manuscript/
├── title-page.md          ← 标题页（标题、作者、通讯信息）
├── abstract.md            ← 摘要（按期刊格式：结构化/非结构化）
├── introduction.md
├── methods.md
├── results.md
├── discussion.md
├── references.md           ← 参考文献列表
└── supplementary.md        ← 补充材料
```

### .docx 导出（投稿用）

大多数期刊要求 .docx 格式投稿。使用 Python `python-docx` 生成：

```python
# ─── Generate .docx for submission ───
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# 设置默认样式（按期刊要求）
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'  # 或 Arial，按期刊要求
font.size = Pt(12)
style.paragraph_format.line_spacing = 2.0  # 双倍行距

# 页边距
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)

# Title Page
doc.add_heading('Title', level=1)
doc.add_paragraph('Running title: ...')
doc.add_paragraph('Authors: ...')
doc.add_paragraph('Affiliations: ...')
doc.add_paragraph('Corresponding author: ...')
doc.add_paragraph(f'Word count: ...')
doc.add_page_break()

# Abstract
doc.add_heading('Abstract', level=1)
# ... 按结构化/非结构化写入

# 各章节
for section_file in ['introduction.md', 'methods.md', 'results.md', 'discussion.md']:
    # 读取 markdown 并转换为 docx 段落
    pass

doc.save('manuscript.docx')
```

**依赖安装：** `pip install python-docx`

### .xlsx 导出（数据表格）

将 `results-summary.md` 中的表格导出为 Excel 格式，供审稿人查看和期刊排版：

```python
# ─── Generate .xlsx for tables ───
import pandas as pd

# Table 1: Baseline characteristics
table1 = pd.DataFrame({...})
# Table 2: Primary and secondary outcomes
table2 = pd.DataFrame({...})
# Table 3: Subgroup analysis
table3 = pd.DataFrame({...})

with pd.ExcelWriter('manuscript_tables.xlsx', engine='openpyxl') as writer:
    table1.to_excel(writer, sheet_name='Table 1 - Baseline', index=False)
    table2.to_excel(writer, sheet_name='Table 2 - Outcomes', index=False)
    table3.to_excel(writer, sheet_name='Table 3 - Subgroups', index=False)
```

**依赖安装：** `pip install openpyxl`

### 导出清单

| 文件 | 格式 | 用途 |
|------|------|------|
| `manuscript.docx` | Word | 投稿主文件（大多数期刊要求） |
| `manuscript_tables.xlsx` | Excel | 表格数据（部分期刊要求单独上传） |
| `title-page.md` → `.docx` | Word | 标题页（部分期刊要求单独上传） |
| `figures/*.tiff` | TIFF | 图表文件（`figure-generation` 生成） |
| `supplementary.docx` | Word | 补充材料 |

## Convergence

当以下条件全部满足时完成：
1. IMRaD 各章节均已完成
2. 所有图表已在正文引用
3. 参考文献完整
4. 语言规范检查通过
5. 字数在目标期刊限制内（加载 journal-templates.yaml 检查）
6. 期刊特殊要求已满足（如 Key Points box、Research in Context panel）

## 衔接规则

### 前置依赖
- **必须**有 `results-summary.md` 和图表
- **推荐**有 `journal-selection-report.md`（确定排版格式）

### 强制衔接
- 完成后 → **必须**触发 `pre-submission-verification`（不可跳过）

### 可选
- 用户要求 .docx → 生成 `manuscript.docx`（使用 python-docx）
- 用户要求表格导出 → 生成 `manuscript_tables.xlsx`（使用 openpyxl）
