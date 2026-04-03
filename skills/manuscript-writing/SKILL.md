---
name: manuscript-writing
description: Use when drafting a medical research manuscript (original research or review articles). Triggers on "写论文"、"写稿子"、"写Introduction"、"写Methods"、"写Discussion"、"manuscript"、"投稿"、"写综述"、"review article"、"systematic review"、"meta-analysis"、"narrative review"、"scoping review"、"mini-review".
---

# Manuscript Writing

## Overview

撰写医学研究论文——支持原始研究（IMRaD）和综述类文章（Narrative / Systematic / Meta-Analysis / Scoping / Mini-Review）。不允许虚构数据或结果。

## When to Use

写论文、写综述、写摘要、写各个章节。

## When NOT to Use

- 格式排版导出 → `manuscript-export`
- 检查投稿规范 → `reporting-standards`

## Article Type Router

**写作前必须先确定文章类型。** 不同类型有不同的结构、前置依赖和写作流程。

```
用户需求 → 什么类型？
  ├── 有自己的数据/实验结果？ → Original Research (IMRaD)
  └── 综合已有文献？
        ├── 需要系统检索 + PRISMA？
        │     ├── 需要统计合并？ → Meta-Analysis
        │     ├── 目的是映射证据范围？ → Scoping Review
        │     └── 目的是回答特定问题？ → Systematic Review
        ├── 短篇聚焦 (≤3000字)？ → Mini-Review
        └── 自由组织主题？ → Narrative Review
```

| 类型 | 代号 | 结构 | 典型字数 | 报告规范 |
|------|------|------|---------|---------|
| Original Research | `original` | IMRaD | 3000-5000 | CONSORT/STROBE/TRIPOD 等 |
| Narrative Review | `narrative` | 主题式 | 4000-8000 | 无强制 |
| Systematic Review | `systematic` | PRISMA | 6000-12000 | PRISMA 2020 |
| Meta-Analysis | `meta` | PRISMA + Stats | 6000-12000 | PRISMA 2020 + MOOSE |
| Scoping Review | `scoping` | 映射式 | 5000-10000 | PRISMA-ScR |
| Mini-Review | `mini` | 短篇聚焦 | 2000-3000 | 无强制 |

## Prerequisites（按类型 + 按章节拆分）

### Original Research

| 章节 | 前置依赖 | 必须/推荐 |
|------|---------|----------|
| Methods | `study-protocol.md` + `analysis-plan.md` | 必须 |
| Introduction | `research-question.md` + `literature-synthesis-summary.md` | 必须 |
| Results | `results-summary.md` + 图表文件 | 必须 |
| Discussion | Results 章节已完成 | 必须 |
| Abstract | 全文各章节已完成 | 必须 |
| Title | Abstract 已完成 | 推荐 |

**可以在没有 results-summary.md 的情况下先写 Methods 和 Introduction。**

### Narrative Review

| 前置依赖 | 必须/推荐 |
|---------|----------|
| `literature-synthesis-summary.md` + `literature-references.md` | 必须 |
| `journal-selection-report.md` | 推荐 |
| `research-question.md` | 推荐（帮助聚焦范围） |

### Systematic Review / Meta-Analysis

| 前置依赖 | 必须/推荐 |
|---------|----------|
| PROSPERO 注册号 | 必须（SR/MA） |
| `search-strategy.md` + `screening-log.md` | 必须 |
| `literature-references.md` | 必须 |
| PRISMA 2020 Checklist | 必须 |
| 偏倚评估结果（RoB 2 / NOS / ROBINS-I） | 必须 |
| Meta 分析统计结果 + 森林图（仅 Meta） | 必须 |

### Scoping Review

| 前置依赖 | 必须/推荐 |
|---------|----------|
| `search-strategy.md` + `screening-log.md` | 必须 |
| `literature-references.md` | 必须 |
| PRISMA-ScR Checklist | 必须 |
| Evidence Map / Charting Table | 必须 |

### Mini-Review

| 前置依赖 | 必须/推荐 |
|---------|----------|
| 主题明确 | 必须 |
| `literature-references.md` | 推荐 |

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

---

## A. Original Research — IMRaD

### Writing Order

**不按论文顺序，按推荐的写作效率顺序：**

1. **Methods** — 最客观，最容易写
2. **Results** — 基于已有分析结果
3. **Introduction** — 现在更清楚 gap 在哪
4. **Discussion** — 需要最多思考
5. **Abstract** — 概括已完成全文
6. **Title** — 精炼到一句话

### Section Rules

**Methods**: 研究设计、参与者、变量定义、统计方法（可复现程度）、伦理声明、样本量、软件版本
**Results**: 参与者流程图 → 基线表 → 主要结局 → 次要结局 → 亚组。**禁止**在 Results 讨论意义。
**Introduction**: 漏斗形（背景→已知→gap→本研究目的）。通常 3-4 段。
**Discussion**: 主要发现→与文献比较→机制→临床意义→局限性→结论。**禁止**引入 Results 中没有的数据。
**Abstract**: 结构化（Background/Methods/Results/Conclusions），250-350 字。
**Title**: 含研究设计类型 + 关键变量，≤20 词。

### Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── methods.md
├── results.md
├── discussion.md
├── references.md
└── supplementary.md
```

---

## B. Narrative Review

### Writing Order

1. **Outline** — 确定 3-5 个主题板块
2. **Thematic Sections** — 每个板块独立写作
3. **Introduction** — 明确综述范围和目的
4. **Discussion / Future Directions** — 整合各板块、指出趋势
5. **Conclusion** — 高度凝练
6. **Abstract** — 概括全文

### Section Rules

**Introduction (3-4 段)**: 主题背景 → 为什么需要这篇综述 → 综述范围和目的
**Thematic Sections (3-5 个)**: 每个主题一个 section，内部按逻辑组织（不按时间/作者排列）。每个 section 末尾有小结（1-2 句）。
**Discussion / Current Challenges**: 综合各主题板块的交叉发现 → 当前挑战
**Future Directions**: 基于 gap 提出研究方向。每个方向需有依据。
**Conclusion (1-2 段)**: 凝练全文核心要点，**不引入新信息**。
**Abstract**: 非结构化，150-300 字，概括范围+主要发现+结论。

### Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── section-1-[theme].md      ← 按主题命名
├── section-2-[theme].md
├── section-3-[theme].md
├── section-4-[theme].md      ← 可选
├── discussion.md              ← 含 Current Challenges + Future Directions
├── conclusion.md
└── references.md
```

---

## C. Systematic Review

### Writing Order

1. **Methods** — 最客观（检索策略、筛选标准、偏倚评估方法）
2. **Results** — PRISMA 流程图 → 纳入研究特征 → 偏倚评估 → 综合结果
3. **Introduction** — 已有综述的不足 → 本综述的目的
4. **Discussion** — 主要发现 → 证据质量 → 局限性 → 启示
5. **Abstract** — 结构化
6. **Title** — 必须含 "systematic review"

### Section Rules

**Methods（必须详细）**:
- Protocol and Registration（PROSPERO 编号）
- Eligibility Criteria（PICO 框架）
- Information Sources（数据库列表 + 检索日期）
- Search Strategy（完整检索式，附 Appendix）
- Study Selection Process（双人独立筛选 + 分歧解决）
- Data Extraction（提取变量列表）
- Risk of Bias Assessment（工具：RoB 2 / NOS / ROBINS-I）
- Synthesis Methods（叙述性综合 / 定量合并）
- Certainty of Evidence（GRADE，如适用）

**Results**:
- Study Selection → **PRISMA Flow Diagram（必须）**
- Study Characteristics → 纳入研究汇总表
- Risk of Bias → 偏倚风险汇总图
- Synthesis Results → 按结局分组报告

**Discussion**: 主要发现 → 与已有综述对比 → 证据质量（GRADE）→ 局限性 → 临床/研究启示

### Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── methods.md
├── results.md
├── discussion.md
├── conclusion.md
├── references.md
├── supplementary.md
│   ├── appendix-search-strategy.md
│   ├── appendix-excluded-studies.md
│   └── appendix-rob-details.md
└── prisma-checklist.md
```

---

## D. Meta-Analysis

**在 Systematic Review 基础上，Methods 和 Results 额外包含：**

### Methods 增加

- Effect Measure（OR / RR / HR / MD / SMD）
- Heterogeneity Assessment（I², Cochran Q, τ²）
- Model Selection（Random-effects vs Fixed-effects + 选择理由）
- Subgroup Analysis（预先指定的亚组变量 + 理由）
- Sensitivity Analysis（逐一排除法 / leave-one-out）
- Publication Bias（Funnel plot + Egger's test / Begg's test）
- Software（R meta/metafor, RevMan, Stata metan）

### Results 增加

- **Forest Plot（必须）** — 主要结局
- Heterogeneity（I², p-value, τ²）
- Subgroup Forest Plots
- **Funnel Plot** — 发表偏倚
- Sensitivity Analysis Results
- GRADE Evidence Table（推荐）

---

## E. Scoping Review

### Section Rules

**Methods**: 框架声明（Arksey & O'Malley / JBI）→ PCC（Population, Concept, Context）→ 检索 → 筛选 → Data Charting（不是 "extraction"）→ **不做偏倚评估**

**Results**: PRISMA-ScR Flow Diagram → Study Characteristics → **Evidence Mapping**（表格/概念图/气泡图展示"什么被研究了、什么没有"）

### Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── methods.md
├── results.md              ← 含 Evidence Map
├── discussion.md
├── conclusion.md
├── references.md
└── prisma-scr-checklist.md
```

---

## F. Mini-Review

### Section Rules

**结构最简洁：**

```
Title
Abstract (非结构化, 100-200 words)
Introduction (1-2 段: 主题意义 + 本文目的)
[2-3 Focused Sections] (聚焦讨论一个窄主题)
Conclusion / Outlook (1 段)
References (≤30-50)
```

**注意：** 不需要系统检索，不需要 PRISMA，通常是领域专家受邀撰写。字数控制在 2000-3000 词。

---

## Language Rules（所有类型通用）

- Methods/Results: 过去时
- Introduction/Discussion: 引用已有知识用现在时
- Review 综述主体: 用现在时描述已有研究发现（"Smith et al. report that..."）
- 避免 "significantly" 的非统计学用法
- 避免 "prove"（用 "support" / "suggest"）
- 综述中避免过度罗列（"A found X. B found Y. C found Z."）→ 应综合性叙述

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "先写 Introduction" | Methods 最容易（原始研究）；Outline 最先做（综述） |
| "Results 里解释一下结果" | Results 只放数据，解释留给 Discussion |
| "Discussion 补充几个新分析" | 禁止引入 Results 没有的数据 |
| "Abstract 最后随便改改" | Abstract 是审稿人最先读的，必须精心写 |
| "用 significantly 强调重要性" | 在论文里 significantly 只能指统计学显著 |
| "结论可以写得激进一点" | 结论不能超出数据/证据支持的范围 |
| "综述按时间顺序排列文献" | 必须按主题组织，揭示 gap 和趋势 |
| "综述就是列文献" | 必须综合分析，而不是逐篇罗列 |
| "Systematic Review 不需要注册" | PROSPERO 注册是 PRISMA 2020 的要求 |
| "Scoping Review 需要偏倚评估" | Scoping Review 明确不做质量评价 |
| "Meta 分析用 Fixed-effects 就行" | 必须报告异质性，I²>50% 通常用 Random-effects |
| "没有数据就不能开始写论文" | Methods 和 Introduction 不依赖数据，可以先写 |

## Output 文件生成

### Markdown 输出（默认）

所有章节以 Markdown 格式生成（结构见各类型的 Output Structure），便于版本控制和协作编辑。

### .docx 导出（投稿用）

写作完成后 → 调用 `manuscript-export` skill 自动导出。

### .xlsx 导出（数据表格）

将 `results-summary.md` 中的表格导出为 Excel 格式：

```python
import pandas as pd
with pd.ExcelWriter('manuscript_tables.xlsx', engine='openpyxl') as writer:
    table1.to_excel(writer, sheet_name='Table 1', index=False)
    table2.to_excel(writer, sheet_name='Table 2', index=False)
```

**依赖安装：** `pip install openpyxl`

## Convergence

当以下条件全部满足时完成：
1. 所有章节均已完成（按文章类型要求）
2. 所有图表已在正文引用
3. 参考文献完整
4. 语言规范检查通过
5. 字数在目标期刊限制内（加载 journal-templates.yaml 检查）
6. 期刊特殊要求已满足（如 Key Points box、Research in Context panel）
7. 综述类：PRISMA Checklist 已完成（如适用）

## 衔接规则

### 前置依赖（按类型拆分，见 Prerequisites 章节）

**核心原则：** 可以在没有 results-summary.md 的情况下先写 Methods 和 Introduction。

### 强制衔接
- 完成后 → 建议触发 `manuscript-export`（.docx 导出）
- 导出后 → **必须**触发 `pre-submission-verification`（不可跳过）

### 可选
- 写综述 Introduction 时 → 可调用 `pubmed-search` Mode 6 格式化引用
- 写 Methods 检索策略时 → 可调用 `pubmed-search` Mode 1 构建检索式
- 需要数据表格 → 导出 `manuscript_tables.xlsx`（使用 openpyxl）
