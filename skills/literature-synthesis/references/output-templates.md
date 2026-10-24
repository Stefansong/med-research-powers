# Literature Synthesis — Output Templates

Loaded on demand by `literature-synthesis/SKILL.md` Output section. SKILL.md keeps only the
field list; this file holds the full fill-in skeletons for the four output files.

- **Narrative 模式**只生成文件 2（`search-strategy.md`）和文件 4（`literature-synthesis-summary.md`）。
- **Systematic 模式**生成全部 4 个文件。

---

## 文件 1: `screening-log.md`（筛选记录 — PRISMA 2020 流程图数据源；Systematic 模式）

```markdown
# Screening Log

**Date:** [日期]
**Research Question:** [一句话]
**Mode:** Systematic

## Reviewers（PRISMA 2020 item 8 / 9）

| Stage | Reviewer 1 | Reviewer 2 | Independent? | Agreement (% / Cohen's κ) | Disagreements resolved by |
|-------|-----------|-----------|--------------|---------------------------|---------------------------|
| Title/abstract screening | [姓名缩写，人] | [姓名缩写，人 / AI 辅助：模型名称 + 版本] | Yes | [x% / κ = x.xx] | [讨论 / 第三名评价者（人）] |
| Full-text screening | [ ] | [ ] | Yes | [ ] | [ ] |
| Data extraction | [ ] | [ ] | Yes | [ ] | [ ] |
| Risk of bias | [ ] | [ ] | Yes | [ ] | [ ] |
| GRADE | [ ] | [ ] | Yes | — | [ ] |

至少一名评价者是人；Claude 最多担任其中一名。

### Automation / AI tools used（无则写 "None"）
| Tool (name, version) | Date(s) used | Stage(s) | How used | Human verification |
|----------------------|--------------|----------|----------|--------------------|
| [模型名称 + 版本] | [日期] | [如 Title/abstract screening] | [判定标准 / 提示词存放位置] | [如 AI 排除的记录全部由人复核] |

## PRISMA Flow Diagram Data

### Identification
| Source | How searched | Records Found |
|--------|--------------|--------------|
| PubMed | PubMed MCP (`search_articles`) | [N] |
| Embase | Run by user on [平台], exported [日期] | [N] |
| Cochrane CENTRAL | Run by user, exported [日期] | [N] |
| Web of Science | Not searched（[原因，如无访问权限]） | — |
| Other database: [名称] | [Run by user / Not searched] | [N / —] |
| **Total (databases)** | | **[N]** |
| Duplicates removed | | -[N] |
| **After deduplication** | | **[N]** |

WebSearch `site:` 查询（arXiv、medRxiv、IEEE 网页等）不是数据库检索，记在下方 Supplementary Search，不计入本表。

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

### Supplementary Search（PRISMA "other methods" 分支）
| Source | Records Found | Included |
|--------|--------------|----------|
| Similar articles (PubMed, `find_related_articles`) | [N] | [n] |
| Citation tracking — reference lists checked manually | [N] | [n] |
| Citation tracking — citing articles (Google Scholar / WoS, manual) | [N] | [n] |
| Web search (supplementary): [site:arxiv.org …] | [N] | [n] |
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

**用途：** 直接生成 PRISMA 2020 流程图（`figure-generation`）+ 满足 `reporting-standards` 的 PRISMA 检查。

---

## 文件 2: `search-strategy.md`（检索策略记录；两种模式都生成）

```markdown
# Search Strategy

**Date:** [日期]
**Research Question:** [一句话]
**Mode:** Narrative / Systematic
**Databases Searched:** PubMed (MCP); Embase, Cochrane CENTRAL (run by user)
**Not searched:** [库名 + 原因，如 Web of Science — no access；无则写 None]
**Supplementary web searches:** [arXiv / medRxiv via WebSearch；无则写 None]

## Database 1: PubMed
- **Search query:** ("pancreatic cancer"[MeSH Terms] AND "artificial intelligence"[Title/Abstract])
- **Query translation (PubMed 返回):** [粘贴 query_translation，证明 MeSH 映射正确]
- **Filters:** 2020-2026, English, Human
- **Results:** [N] articles
- **Tool used:** PubMed MCP `search_articles`（via `pubmed-search` Mode 1）

## Database 2: Embase（用户运行）
- **Search query (Embase.com syntax):** ('pancreas cancer'/exp OR 'pancreatic cancer':ti,ab,kw) AND ('artificial intelligence'/exp OR 'deep learning':ti,ab,kw)
- **Run by:** [用户姓名缩写] on [平台] on [日期]
- **Filters:** [用户实际用的限制]
- **Results:** [N] records（来自用户导出的 [RIS/CSV] 文件）
- **Tool used:** none — Claude 不能检索 Embase；检索式由 Claude 起草、用户运行并导出

## Database 3: Web of Science
- **Status:** Not searched — [原因]；已在 Methods / 局限性中写明

## Supplementary web search: arXiv（WebSearch，补充检索）
- **Search query:** site:arxiv.org medical image segmentation transformer
- **Filters:** none — WebSearch 只接受检索词和域名限制，不能按 arXiv 分类或日期过滤；年份限制在筛选时按纳入标准人工执行
- **Records screened:** [N]（不完整、不可复现；PRISMA "other methods"）
- **Tool used:** WebSearch

## Google Scholar（如使用）
- **Search string:** [用户手动检索时输入的字符串]
- **Results pasted by user:** [N] records（Claude 不能直接检索 Scholar，由用户手动检索后粘贴）

## Supplementary Search
- **Similar articles (PubMed):** seed PMIDs [列表] → `find_related_articles` → [N] new records
- **Citation tracking (manual):** reference lists of [N] included studies checked; citing articles via [Google Scholar / WoS]
```

---

## 文件 3: `literature-references.md`（结构化文献清单；Systematic 模式）

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
- **Source:** PubMed (MCP) / Embase, CENTRAL, … (user-run export) / Web search (supplementary: arXiv, medRxiv, …) / Citation tracking / ...
- **Study Type:** RCT / Cohort / Diagnostic accuracy / Prediction model / AI Validation / Systematic Review / ...
- **Sample Size:** n=[N]
- **Key Finding:** [1-2 句核心发现]
- **Relevance:** [与本研究的关系：支持 / 矛盾 / 方法参考 / Gap 证据]
- **Evidence Level:** [Oxford CEBM 2011 Level 1-5]
- **Bias Risk:** Low / Moderate / High / Unclear（工具：RoB 2 / ROBINS-I / ROBINS-E / NOS / QUADAS-2 / PROBAST+AI；两名评价者独立）
- **Verified:** ✅ Verified (PubMed) / ⚠️ Not found / ❌ Mismatch / ⏳ Unverified (tool error / web search only / not checked) / ℹ️ Non-PubMed（DOI/WebSearch 核对，注明来源）

### 2. [Author] et al., [Year]
...

## Excluded Studies (with reasons)

| # | Author, Year | Reason for Exclusion |
|---|-------------|---------------------|
| 1 | Smith, 2022 | Not human subjects |
| 2 | Lee, 2021 | Duplicate of PMID 12345 |
...
```

---

## 文件 4: `literature-synthesis-summary.md`（证据综合；两种模式都生成）

```markdown
# Literature Synthesis Summary

**Topic:** [研究主题]
**Date:** [日期]
**Mode:** Narrative / Systematic
**Total articles screened:** [N] (PubMed: [n], Embase (user-run): [n], CENTRAL (user-run): [n], web search (supplementary): [n], ...)
**Not searched:** [库名 + 原因 / None]
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

## Certainty of Evidence（GRADE；Systematic 模式，范围综述除外）

| Outcome | No. of studies (participants) | Risk of bias | Inconsistency | Indirectness | Imprecision | Publication bias | Upgrading (observational) | Certainty |
|---------|-------------------------------|--------------|---------------|--------------|-------------|------------------|---------------------------|-----------|
| [结局 1] | [k (n)] | [Not serious / Serious (−1) + 理由] | [ ] | [ ] | [ ] | [ ] | [Large effect / Dose-response / Confounding / None] | ⊕⊕⊕◯ Moderate |

每个主要结局一行，逐项写明降级 / 升级理由；评定人见 `screening-log.md` 的 Reviewers 表。

## Research Gap（本研究定位）
[本研究要解决的具体 gap，引用上述 Unknown/Controversial 证据]

## Key References Table

| # | Author, Year | Design | n | Key Finding | Relevance | Verified |
|---|-------------|--------|---|-------------|-----------|----------|
| 1 | [Author1], [Year] | RCT | 500 | [发现] | 直接相关 | ✅ |
| 2 | [Author2], [Year] | Cohort | 1200 | [发现] | 方法参考 | ✅ |
| 3 | [Author3], [Year] | AI Valid. | 300 | [发现] | Gap 证据 | ℹ️ arXiv, DOI checked |
...
```

Narrative 模式下 Key References Table 就是引用清单（不另生成 `literature-references.md`），每行必须带 Verified 状态。
