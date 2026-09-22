---
name: manuscript-writing
description: Use when drafting a medical research manuscript (original research or review). Triggers on "写论文"、"写稿子"、"写Methods"、"写综述"、"manuscript"、"systematic review"、"meta-analysis"、"narrative review".
---

# Manuscript Writing

## Overview

撰写医学研究论文——支持原始研究（IMRaD）和综述类文章（Narrative / Systematic / Meta-Analysis / Scoping / Mini-Review）。核心原则：**不虚构数据、结果或参考文献；每一个数字都能回溯到 `results-summary.md`。**

## When to Use

写论文、写综述、写摘要、写某一个章节；已有 `results-summary.md` 或文献综合结果，准备成稿。

## When NOT to Use

- 排版导出 .docx → `manuscript-export`（在 `pre-submission-verification` 之后）
- 逐条核对报告规范（CONSORT/STROBE/PRISMA…）→ `reporting-standards`
- 还没选期刊、不知道投哪 → `journal-selection`
- 只改一句话、只算一个数 → 直接回答，不走本 skill 流程

## Article Type Router

**写作前必须先确定文章类型**，然后**只读取**对应的类型文件（每类一个文件，含前置依赖、写作顺序、章节规则、Output Structure）：

```
用户需求 → 什么类型？
  ├── 有自己的数据/实验结果？ → Original Research (IMRaD)
  └── 综合已有文献？
        ├── 需要系统检索 + PRISMA？
        │     ├── 需要统计合并？ → Meta-Analysis（含 NMA）
        │     ├── 目的是映射证据范围？ → Scoping Review
        │     └── 目的是回答特定问题？ → Systematic Review
        ├── 短篇聚焦 (≤3000 词)？ → Mini-Review
        └── 自由组织主题？ → Narrative Review
```

| 类型 | 代号 | 结构 | 典型字数 | 报告规范 | 类型文件 |
|------|------|------|---------|---------|---------|
| Original Research | `original` | IMRaD | 3000–5000 | CONSORT 2025 / STROBE / TRIPOD+AI / CLAIM 2024 等 | `references/article-types/original.md` |
| Narrative Review | `narrative` | 主题式 | 4000–8000 | 无强制（SANRA 自评） | `references/article-types/narrative.md` |
| Systematic Review | `systematic` | PRISMA | 6000–12000 | PRISMA 2020 | `references/article-types/systematic.md` |
| Meta-Analysis / NMA | `meta` | PRISMA + Stats | 6000–12000 | PRISMA 2020 (+ MOOSE / PRISMA-NMA) | `references/article-types/meta.md`（在 systematic.md 之上追加） |
| Scoping Review | `scoping` | 映射式 | 5000–10000 | PRISMA-ScR | `references/article-types/scoping.md` |
| Mini-Review | `mini` | 短篇聚焦 | 2000–3000 | 无强制 | `references/article-types/mini.md` |

"典型字数"只是经验值；**实际上限一律以目标期刊模板为准**。

## Workflow

### Step 0：读取用户画像（懒采集）

读取 `~/.claude/mrp-user-profile.json` 的 `preferences.favorite_journals`。文件或字段不存在 → 只问这一个问题（"你常投的期刊有哪些？"），并问是否保存到该文件；用户跳过则不保存。它只用于 Step 2 的默认候选，不替代 `journal-selection`。

### Step 1：确定文章类型

按 Router 判定类型 → 读取对应 `references/article-types/<type>.md` → 按其"前置依赖"表检查文件是否齐全。缺必须项 → 停，先补齐（原始研究例外：Methods 和 Introduction 不依赖 `results-summary.md`，可以先写）。

### Step 2：确定目标期刊并加载模板（软确认）

目标期刊来源优先级：`journal-selection-report.md` 首选 → `.mrp-state.json` 的 `target_journal` → 画像的 `favorite_journals` → 询问用户。写作前**复核一次**："目标期刊仍是 X 吗？"——这是软确认，用户随时可换，换刊后重新加载模板即可，不需要回头重跑流程。

加载模板只用脚本（见下方 Journal Template 节），**禁止整读 `journal-templates.yaml`**。

### Step 3：按类型文件的写作顺序逐章写作

- 每章写入 `manuscript/<section>.md`（文件名见 Output）；写作时对照类型文件的章节规则与报告规范条目。
- 每写完一章，对照模板的 `word_limit` / `abstract` 字数**实时检查**，超限先删冗余再压缩。
- 未定稿处用 `<!-- PLACEHOLDER: 说明 -->` 或 `[TBD]` 标注，**不要用看起来像真数据的占位值**（导出脚本会检测这些标记）。
- 引用：写作时标记来源（PMID/DOI）；格式化用 `pubmed-search` Mode 6；写综述 Methods 检索策略可用 Mode 1。调用 PubMed MCP 时写法为 `mcp__<server名>__get_article_metadata(pmids=[...])`，server 名以当前会话工具列表为准（claude.ai 连接器为 `claude_ai_PubMed`，本地常见为 `PubMed`）。引用状态标记：✅ Verified / ⚠️ Not found / ❌ Mismatch / ⏳ Unverified (tool error，重试) / ℹ️ Non-PubMed（用 DOI/WebSearch 核对）；最终逐条验证由 `pre-submission-verification` Gate 3 完成。

### Step 4：期刊特殊元素

按模板 `special` 字段补齐：JAMA 家族 → `key-points.md`；Lancet 家族（含 eClinicalMedicine、eBioMedicine）→ `research-in-context.md`；European Urology 家族 → Patient Summary + Take Home Message；Nature 家族 → Reporting Summary、Data/Code availability。

### Step 5：自检与收尾

1. 对照 Convergence 逐条自检；语言规则检查（见 Language Rules）。
2. 输出 3–5 行摘要（产物清单、目标期刊与字数、待注意的 placeholder），默认直接进入下一步；用户要求"逐步确认"时等确认。
3. 更新项目目录 `.mrp-state.json`（`python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`，记录 `completed_skills` 与 `artifacts.manuscript/`）。
4. 下一步 → `peer-review-simulation`。

## Journal Template（期刊排版规范）

模板库：`references/journal-templates.yaml`，234 个期刊（顶层键 `data_as_of` + `templates`），按专科分区。它是字数、摘要格式、参考文献样式、特殊要求、投稿系统、期刊家族（`family`）的**唯一数据源**——不要在本文件重复期刊清单。

**只用脚本读取（文件 3600 多行，整读会截断且浪费上下文）：**

```bash
# 精确取一条（默认同时查项目目录 ./journal-overrides.yaml，命中则优先）
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --id european-urology
# 不确定 id：模糊搜索 id/名称/专科分区（词首匹配）
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --search urol
# 按专科列表 / 机器可读
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --list --specialty urology
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --id nature --json
```

找不到 id 时脚本 exit 1 并提示 `--search`。输出里的 `IF_approx` 是 **JCR 2022** 值、APC 是 2022 价（见 `data_as_of`），引用时必须标年份，选刊结论以 `journal-selection` 的 WebSearch 复核为准。

**目标期刊不在库中：** 用 WebSearch 找期刊 "Instructions for Authors"，把提取到的规范写入**项目目录**的 `journal-overrides.yaml`（与库文件相同结构：`templates:` 下一条含 `id / journal / publisher / word_limit / abstract / references / figures / tables / sections / special / system / family`），字段不确定的写 `verify`。脚本默认读取 `./journal-overrides.yaml`（或 `--overrides <路径>`），同 id 时覆盖库内条目。**不要改插件安装目录里的 `journal-templates.yaml`**——更新插件会丢失。

## Output

所有章节以 Markdown 生成，放在项目目录 `manuscript/`（各类型的完整结构见类型文件）。原始研究的通用结构：

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── methods.md
├── results.md
├── discussion.md
├── references.md
├── supplementary.md            ← 可选
├── figure-legends.md           ← 可选（figure-generation 产物）
├── key-points.md               ← 可选：JAMA 家族必须（Question / Findings / Meaning）
└── research-in-context.md      ← 可选：Lancet 家族必须（Evidence before / Added value / Implications）
```

文件名与 `manuscript-export` 的 section id 一一对应：`key-points` 与 `research-in-context` 由导出脚本按期刊 `family` 决定是否纳入及位置（JAMA：Key Points 在 Abstract 之前；Lancet：Research in Context 在 Introduction 之前；其他家族有这两个文件也不会导出，报告里会提示）。综述类的 `section-N-*.md` 导出前需合并进 `discussion.md`。

数据表格需要 Excel 时（可选）：

```python
import pandas as pd
with pd.ExcelWriter("manuscript_tables.xlsx", engine="openpyxl") as writer:
    table1.to_excel(writer, sheet_name="Table 1", index=False)
```

## Language Rules（所有类型通用）

- Methods/Results：过去时；Introduction/Discussion 引用已有知识：现在时
- 综述主体：用现在时描述已有研究发现（"Smith et al. report that..."）
- 避免 "significantly" 的非统计学用法；避免 "prove"（用 "support" / "suggest"）
- 效应量必须带 95% CI；p 值写精确值（p=0.03，不写 p<0.05；p<0.001 例外）
- 综述避免逐篇罗列（"A found X. B found Y."）→ 综合性叙述
- 缩写首次出现给全称；同一概念全文用同一术语

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "先写 Introduction" | 原始研究 Methods 最容易先写；综述先做 Outline |
| "Results 里解释一下结果" | Results 只放数据，解释留给 Discussion |
| "Discussion 补充几个新分析" | 禁止引入 Results 没有的数据 |
| "Abstract 最后随便改改" | Abstract 是审稿人最先读的，必须精心写，字数以模板为准 |
| "用 significantly 强调重要性" | 论文里 significantly 只能指统计学显著 |
| "结论可以写得激进一点" | 结论不能超出数据/证据支持的范围 |
| "综述按时间顺序排列文献" | 必须按主题组织，揭示 gap 和趋势 |
| "Systematic Review 不需要注册" | PRISMA 2020 item 24a 要求报告注册信息；未注册必须写明 |
| "Scoping Review 需要偏倚评估" | Scoping Review 明确不做质量评价 |
| "I²>50% 就改用随机效应" | 模型预先指定；I² 只用于报告异质性，不是事后换模型的依据 |
| "把整个 journal-templates.yaml 读进来看" | 3600 多行，Read 会截断到前 2000 行，后半部分期刊会被误判"不在库中"；只用脚本取一条 |
| "期刊不在库里就改插件目录的 YAML" | 写项目目录 `journal-overrides.yaml`，更新插件不丢失 |
| "没有数据就不能开始写论文" | Methods 和 Introduction 不依赖数据，可以先写 |

## Convergence

当以下条件全部满足时完成：
1. 所有章节均已完成（按类型文件的 Output Structure）
2. 所有图表已在正文引用，编号连续
3. 参考文献完整、每条有 PMID/DOI 或标注 ℹ️ Non-PubMed
4. 语言规范检查通过
5. 正文与摘要字数在目标期刊模板限制内（用脚本取到的 `word_limit` / `abstract`）
6. 期刊特殊要求已满足（Key Points / Research in Context / Patient Summary 等）
7. 综述类：PRISMA / PRISMA-ScR checklist 已完成（如适用）
8. `.mrp-state.json` 已更新

## Red Flags — STOP

- Results 中没有的数字出现在 Discussion / Abstract → 停，禁止引入未分析的数据
- 虚构数据、结果或参考文献 → 绝对禁止，立即停止
- 缺少必须的前置文件（按类型文件的前置依赖表）就开始写对应章节 → 停，先补齐
- "significantly" 用于非统计学语境 / "prove" 表述 → 停，改为规范措辞
- 准备整读 `journal-templates.yaml` → 停，改用 `get_journal_template.py`

**警告（不阻断）：** Systematic Review / Meta-Analysis 没有注册号 → 提醒用户在 Methods 与 Abstract 明确写"未注册"及原因（PRISMA 2020 item 24a），并说明部分期刊要求注册。

## 衔接规则

### 前置依赖（不满足则阻止）
- 按类型文件的前置依赖表（原始研究：`study-protocol.md` + `analysis-plan.md` + `results-summary.md`；综述：`literature-synthesis` 产物）
- 目标期刊：来自 `journal-selection-report.md`（软确认，可随时更换）

### 强制衔接（不可跳过）
- 完成后 → `peer-review-simulation`（模拟审稿）→ `pre-submission-verification`（6-Gate 硬确认）→ `manuscript-export`（.docx）→ `submission-preparation`
- 写作前 → 复核目标期刊一次（软确认；未选刊则先 `journal-selection`）
- 完成后 → 更新 `.mrp-state.json`

### 可选衔接
- 参考文献格式化 → `pubmed-search` Mode 6；综述检索策略 → `pubmed-search` Mode 1
- 写作中发现研究问题定义不清 → 回 `research-question-formulation`；分析需调整 → 回 `data-analysis-planning`（修改须标注为与 SAP 的偏离）
- 涉及人体/动物数据的 Methods 伦理声明 → `research-ethics` 的 `ethics-statement.md`
- 需要图表 → `figure-generation`；需要报告规范逐条核对 → `reporting-standards`
