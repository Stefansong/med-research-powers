---
name: literature-synthesis
description: Use when systematically searching and synthesizing research literature. Triggers on "帮我查文献"、"文献综述"、"research gap"、"相关研究"、"背景介绍怎么写"、"这个领域有什么研究".
---

# Literature Synthesis

## Overview

系统性检索和综合文献。不是随意列几篇——必须有检索策略、证据评价和 gap 分析。

## When to Use

- 了解研究现状、寻找 gap
- 写 Introduction 的背景综述
- 做正式的系统综述

## When NOT to Use

- 已经有明确的文献清单只需格式化 → 直接引用管理
- 做公众号文献解读 → `uro-ai-paper-interpreter`（如已安装）

## Workflow

### Step 1: 选择数据库

根据研究类型选择对应数据库组合：

| 研究类型 | 主数据库 | 补充数据库 | 工具 |
|---------|---------|-----------|------|
| 临床/生物医学 | **PubMed** | Cochrane, Embase | PubMed MCP + WebSearch |
| AI/ML 医学应用 | **PubMed** + **arXiv** | IEEE Xplore, ACM DL | PubMed MCP + WebSearch |
| 手术视频/器械 | **PubMed** + **IEEE Xplore** | Scopus | PubMed MCP + WebSearch |
| 系统综述/Meta | **PubMed** + **Cochrane** + **Embase** | Web of Science | PubMed MCP + WebSearch |
| 基础/分子生物 | **PubMed** | bioRxiv, medRxiv | PubMed MCP + WebSearch |
| 公卫/流行病学 | **PubMed** | WHO IRIS, Global Health | PubMed MCP + WebSearch |
| 中文文献补充 | **PubMed** | CNKI, 万方, VIP | WebSearch |

**原则：至少检索 2 个数据库。系统综述至少 3 个。**

### Step 2: 制定检索策略

根据 PICO 确定关键词 → 构建检索式（MeSH + free text + Boolean） → 分数据库执行

生成 `search-strategy.md` 记录完整检索策略（保证可复现）。

### Step 3: 执行检索（多数据库）

**🔀 Auto-Parallel：** 当目标数据库 ≥ 2 时，自动启动多个子 agent 并行检索各数据库（参考 `team-collaboration` skill）。每个子 agent 负责一个数据库，检索完成后主 agent 合并去重。

#### 数据库 A — PubMed（PubMed MCP，优先使用）

7 个 MCP 函数及使用场景：

| 函数 | 用途 | 使用时机 |
|------|------|---------|
| `search_articles` | 关键词/MeSH/Boolean 检索 | **主检索**——Step 3 核心步骤 |
| `get_article_metadata` | 获取文献详细元数据（作者、摘要、DOI） | 筛选后获取纳入文献的完整信息 |
| `get_full_text_article` | 获取 PMC 全文 | 全文筛选、提取关键数据、验证结论 |
| `find_related_articles` | 查找相似文献（基于标题/摘要/MeSH 相似度） | **滚雪球检索**——从核心文献扩展 |
| `convert_article_ids` | PMID ↔ PMCID ↔ DOI 互转 | 确认全文可用性、统一引用格式 |
| `lookup_article_by_citation` | 根据引用信息（作者+期刊+年份）查找 PMID | 已知引用但缺 PMID 时反查 |
| `get_copyright_status` | 查询文章版权和开放获取状态 | 系统综述中确认可引用/可复用的文献 |

**PubMed 检索式示例：**
```
# RCT 检索
"pancreatic cancer"[MeSH] AND "artificial intelligence"[Title/Abstract] AND "Clinical Trial"[Publication Type]

# 系统综述检索
("deep learning" OR "machine learning") AND "diagnostic accuracy"[Title/Abstract] AND "systematic review"[Publication Type]

# 时间限制
search_articles(query="...", date_from="2020", date_to="2026", sort="pub_date")
```

**PubMed 覆盖范围：** 医学、临床研究、公共卫生、生物学、遗传学、药学、免疫学、神经科学、生物医学工程。

**PubMed 不覆盖：** 纯 CS/AI 算法论文、纯物理/数学、非生物医学工程、社会科学。

#### 数据库 B — arXiv / IEEE / ACM（WebSearch）

**适用于：** AI/ML 医学研究必须补充检索算法类文献。

```
# arXiv 检索（通过 WebSearch）
WebSearch(query="site:arxiv.org medical image segmentation transformer 2024 2025")

# IEEE Xplore 检索
WebSearch(query="site:ieeexplore.ieee.org surgical video AI deep learning")

# ACM Digital Library 检索
WebSearch(query="site:dl.acm.org clinical NLP large language model evaluation")
```

#### 数据库 C — Cochrane Library（WebSearch）

**适用于：** 系统综述、Meta 分析、临床指南证据。

```
WebSearch(query="site:cochranelibrary.com [主题] systematic review")
```

#### 数据库 D — Google Scholar（WebSearch，补充）

**适用于：** 灰色文献、会议论文、预印本、引用追踪。

```
WebSearch(query="[关键词] site:scholar.google.com")
```

**注意：** Google Scholar 不支持精确的 Boolean 检索式，适合补充检索，不适合作为主检索。

#### 数据库 E — 预印本（WebSearch）

**适用于：** 最新未发表的研究、快速了解前沿。

```
# medRxiv（临床/公卫预印本）
WebSearch(query="site:medrxiv.org [主题]")

# bioRxiv（基础生物预印本）
WebSearch(query="site:biorxiv.org [主题]")
```

**注意：** 预印本未经同行评审，引用时必须标注"preprint"。

### Step 4: 文献筛选（必须记录每一步）

筛选流程严格按 PRISMA 2020 流程图执行，每一步的数量和排除原因都必须记录到 `screening-log.md`。

#### Phase 1 — 去重
- 合并所有数据库检索结果
- 基于 DOI/PMID/标题匹配去除重复
- 记录：各数据库原始数量、重复数量、去重后数量

#### Phase 2 — 题目/摘要筛选
- 按纳入/排除标准逐篇审阅题目和摘要
- 每篇排除的文献记录排除原因（分类编码）
- 用 `get_article_metadata` 获取摘要内容
- 记录：筛选数量、排除数量（按原因分类）

#### Phase 3 — 全文筛选
- 用 `convert_article_ids` 查 PMCID → 用 `get_full_text_article` 获取全文
- 无法获取全文的尝试 WebFetch 获取或标记为 "full text unavailable"
- 逐篇按纳入/排除标准审阅全文
- 每篇排除的文献记录排除原因
- 记录：全文获取数量、排除数量（按原因分类）、最终纳入数量

#### Phase 4 — 补充检索
- 对纳入文献用 `find_related_articles` 滚雪球
- 手动检查纳入文献的参考文献列表
- 新发现的文献重复 Phase 2-3 流程
- 记录：补充检索来源和新增纳入数量

### Step 5: 证据评价

每篇评价：研究类型和证据等级（Oxford CEBM）、偏倚风险（RCT: RoB 2 / 非随机: ROBINS-I / 观察性: NOS）、结果适用性

### Step 6: 证据综合

**按主题组织**（不按时间或作者）：
- 已知（明确的证据）
- 未知（缺乏证据的领域）
- 争议（证据不一致的领域）
- 本研究的定位（解决哪个 gap）

## Output（必须生成的文件）

### 文件 1: `screening-log.md`（筛选记录 — PRISMA 流程图数据源）

```markdown
# Screening Log

**Date:** [日期]
**Research Question:** [一句话]

## PRISMA Flow Diagram Data

### Identification
| Database | Records Found |
|----------|--------------|
| PubMed | [N] |
| arXiv | [N] |
| Cochrane | [N] |
| IEEE Xplore | [N] |
| Other: [名称] | [N] |
| **Total** | **[N]** |
| Duplicates removed | -[N] |
| **After deduplication** | **[N]** |

### Screening — Title/Abstract
| Decision | Count |
|----------|-------|
| Screened | [N] |
| Excluded | -[N] |
| → Not relevant topic | [n] |
| → Wrong study type | [n] |
| → Wrong population | [n] |
| → Not in English/Chinese | [n] |
| → Conference abstract only | [n] |
| → Other: [reason] | [n] |
| **Passed to full-text** | **[N]** |

### Screening — Full Text
| Decision | Count |
|----------|-------|
| Full text assessed | [N] |
| Full text unavailable | [n] (listed below) |
| Excluded | -[N] |
| → Does not meet inclusion criteria | [n] |
| → Insufficient data reported | [n] |
| → Duplicate cohort/dataset | [n] |
| → Wrong outcome | [n] |
| → Other: [reason] | [n] |
| **Included from database search** | **[N]** |

### Supplementary Search
| Source | Records Found | Included |
|--------|--------------|----------|
| Snowball (find_related_articles) | [N] | [n] |
| Reference list check | [N] | [n] |
| Expert recommendation | [N] | [n] |
| **Total supplementary included** | | **[N]** |

### Final
| | Count |
|---|-------|
| **Total included in synthesis** | **[N]** |

## Exclusion Details (Full Text Phase)

| # | Author, Year | PMID/DOI | Exclusion Reason |
|---|-------------|----------|-----------------|
| 1 | [Author], [Year] | [ID] | [具体原因] |
| 2 | [Author], [Year] | [ID] | [具体原因] |
...

## Full Text Unavailable

| # | Author, Year | PMID/DOI | Action Taken |
|---|-------------|----------|-------------|
| 1 | [Author], [Year] | [ID] | Contacted author / Used abstract only / Excluded |
...
```

**用途：** 直接生成 PRISMA 2020 流程图 + 满足 `reporting-standards` 检查要求。

### 文件 2: `search-strategy.md`（检索策略记录）

```markdown
# Search Strategy

**Date:** [日期]
**Research Question:** [一句话]
**Databases Searched:** PubMed, arXiv, Cochrane, ...

## Database 1: PubMed
- **Search query:** ("pancreatic cancer"[MeSH] AND "artificial intelligence"[Title/Abstract])
- **Filters:** 2020-2026, English, Human
- **Results:** [N] articles
- **Tool used:** PubMed MCP `search_articles`

## Database 2: arXiv
- **Search query:** site:arxiv.org medical image segmentation transformer
- **Filters:** cs.CV, 2023-2026
- **Results:** [N] articles
- **Tool used:** WebSearch

## Snowball Search
- **Seed articles:** [核心文献 PMID 列表]
- **Tool used:** PubMed MCP `find_related_articles`
- **Additional results:** [N] articles
```

### 文件 3: `literature-references.md`（结构化文献清单）

**每篇纳入的文献必须保存以下字段：**

```markdown
# Literature References

## Included Studies ([N] total)

### 1. [Author] et al., [Year]
- **Title:** [完整标题]
- **Journal:** [期刊名]
- **PMID:** [如有]
- **DOI:** [如有]
- **PMCID:** [如有，表示全文可获取]
- **Source Database:** PubMed / arXiv / IEEE / Cochrane / ...
- **Study Type:** RCT / Cohort / AI Validation / Systematic Review / ...
- **Sample Size:** n=[N]
- **Key Finding:** [1-2 句核心发现]
- **Relevance:** [与本研究的关系：支持 / 矛盾 / 方法参考 / Gap 证据]
- **Evidence Level:** [Oxford CEBM 1a-5]
- **Bias Risk:** Low / Moderate / High / Unclear
- **Verified:** ✅ PubMed MCP confirmed / ⚠️ Manual check needed

### 2. [Author] et al., [Year]
...

## Excluded Studies (with reasons)

| # | Author, Year | Reason for Exclusion |
|---|-------------|---------------------|
| 1 | Smith, 2022 | Not human subjects |
| 2 | Lee, 2021 | Duplicate of PMID 12345 |
...
```

### 文件 4: `literature-synthesis-summary.md`（证据综合）

```markdown
# Literature Synthesis Summary

**Topic:** [研究主题]
**Date:** [日期]
**Total articles screened:** [N] (PubMed: [n], arXiv: [n], Cochrane: [n], ...)
**Total articles included:** [N]

## Evidence Map

### Known（已知，有明确证据）
1. [发现1] — supported by [Author1, Year; Author2, Year]
2. [发现2] — supported by [Author3, Year]

### Unknown（未知，证据不足）
1. [Gap1] — no studies found on [topic]
2. [Gap2] — only 1 small study (n=30, [Author, Year])

### Controversial（争议，证据不一致）
1. [争议点] — [Author1, Year] found X, but [Author2, Year] found Y
   - Possible explanation: [方法差异/人群差异/...]

## Research Gap（本研究定位）
[本研究要解决的具体 gap，引用上述 Unknown/Controversial 证据]

## Key References Table

| # | Author, Year | Design | n | Key Finding | Relevance |
|---|-------------|--------|---|-------------|-----------|
| 1 | [Author1], [Year] | RCT | 500 | [发现] | 直接相关 |
| 2 | [Author2], [Year] | Cohort | 1200 | [发现] | 方法参考 |
| 3 | [Author3], [Year] | AI Valid. | 300 | [发现] | Gap 证据 |
...
```

**这 3 个文件是下游 skill 的输入：**
- `literature-references.md` → `manuscript-writing`（引用管理）、`pre-submission-verification` Gate 3（引用验证）
- `literature-synthesis-summary.md` → `manuscript-writing`（Introduction 写作）、`study-design`（Gap 定位）
- `search-strategy.md` → `reporting-standards`（PRISMA 检索报告）

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "随便引几篇就行" | 必须有系统的检索策略 |
| "只搜 PubMed 就够了" | AI 研究必须加 arXiv/IEEE；系统综述至少 3 个数据库 |
| "只引用支持我观点的文献" | 确认偏倚——必须包含不一致的证据 |
| "这篇文献我记得大概说了..." | 必须用 PubMed MCP 验证文献存在且结论准确，禁止编造 |
| "按时间顺序排列文献" | 按主题组织，揭示 gap |
| "检索一次就够了" | 用 `find_related_articles` 滚雪球 + 补充检索 |
| "预印本和正式发表一样引用" | 预印本必须标注 "preprint"，正式发表后应更新引用 |

## Convergence

当以下条件全部满足时完成：
1. 检索策略已记录且可复现（包含所有数据库的检索式）
2. 至少 2 个数据库已检索（系统综述至少 3 个）
3. 文献筛选流程完整（含跨数据库去重）
4. 关键文献已做证据评价
5. Research gap 已明确识别
6. 本研究的定位已清晰
7. 所有引用文献已通过 PubMed MCP 验证真实性

## Red Flags — STOP

- 禁止编造不存在的文献
- 禁止引用文献但歪曲其结论
- 不确定文献是否存在 → 明确告知用户

## 衔接规则

### 前置依赖
- 建议先有 PICO（`research-question-formulation`），但也可独立使用

### 强制衔接
- 完成后 → `literature-synthesis-summary.md` 传递给 `study-design`（Gap 定位）
- 完成后 → `literature-references.md` 传递给 `manuscript-writing`（引用管理）
- 完成后 → `search-strategy.md` + `screening-log.md` 传递给 `reporting-standards`（PRISMA 流程图 + 检索报告）

### 被下游 skill 调用
- `pre-submission-verification` Gate 3 → 读取 `literature-references.md` 验证引用真实性
- `manuscript-writing` Introduction → 读取 `literature-synthesis-summary.md` 写背景
- `manuscript-writing` Methods → 读取 `search-strategy.md` + `screening-log.md` 写检索方法描述
- `figure-generation` → 读取 `screening-log.md` 生成 PRISMA 流程图
