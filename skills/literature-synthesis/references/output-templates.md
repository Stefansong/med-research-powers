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

### Supplementary Search（PRISMA "other methods" 分支）
| Source | Records Found | Included |
|--------|--------------|----------|
| Similar articles (PubMed, `find_related_articles`) | [N] | [n] |
| Citation tracking — reference lists checked manually | [N] | [n] |
| Citation tracking — citing articles (Google Scholar / WoS, manual) | [N] | [n] |
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
**Databases Searched:** PubMed, arXiv, Cochrane, ...

## Database 1: PubMed
- **Search query:** ("pancreatic cancer"[MeSH Terms] AND "artificial intelligence"[Title/Abstract])
- **Query translation (PubMed 返回):** [粘贴 query_translation，证明 MeSH 映射正确]
- **Filters:** 2020-2026, English, Human
- **Results:** [N] articles
- **Tool used:** PubMed MCP `search_articles`（via `pubmed-search` Mode 1）

## Database 2: arXiv
- **Search query:** site:arxiv.org medical image segmentation transformer
- **Filters:** cs.CV, 2023-2026
- **Results:** [N] articles
- **Tool used:** WebSearch

## Database 3: Google Scholar（如使用）
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
- **Source Database:** PubMed / arXiv / IEEE / Cochrane / ...
- **Study Type:** RCT / Cohort / Diagnostic accuracy / Prediction model / AI Validation / Systematic Review / ...
- **Sample Size:** n=[N]
- **Key Finding:** [1-2 句核心发现]
- **Relevance:** [与本研究的关系：支持 / 矛盾 / 方法参考 / Gap 证据]
- **Evidence Level:** [Oxford CEBM 2011 Level 1-5]
- **Bias Risk:** Low / Moderate / High / Unclear（工具：RoB 2 / ROBINS-I / NOS / QUADAS-2 / PROBAST）
- **Verified:** ✅ Verified (PubMed) / ⚠️ Not found / ❌ Mismatch / ⏳ Unverified (tool error) / ℹ️ Non-PubMed（DOI/WebSearch 核对，注明来源）

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

| # | Author, Year | Design | n | Key Finding | Relevance | Verified |
|---|-------------|--------|---|-------------|-----------|----------|
| 1 | [Author1], [Year] | RCT | 500 | [发现] | 直接相关 | ✅ |
| 2 | [Author2], [Year] | Cohort | 1200 | [发现] | 方法参考 | ✅ |
| 3 | [Author3], [Year] | AI Valid. | 300 | [发现] | Gap 证据 | ℹ️ arXiv, DOI checked |
...
```

Narrative 模式下 Key References Table 就是引用清单（不另生成 `literature-references.md`），每行必须带 Verified 状态。
