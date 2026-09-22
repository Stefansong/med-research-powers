# PubMed Search — Output Templates & Reference Formats

Loaded on demand by pubmed-search. Keep the 6-Mode workflow (reasoning) in
SKILL.md; this file holds static templates and the reference-format lookup.

PubMed MCP tools are called by their full name `mcp__<server名>__<函数名>`; the function
names are fixed (`search_articles`, `get_article_metadata`, `get_full_text_article`,
`find_related_articles`, `convert_article_ids`, `lookup_article_by_citation`,
`get_copyright_status`) and the server name comes from the current session's tool list
(`claude_ai_PubMed` for the claude.ai connector, commonly `PubMed` for a local server).

## Mode 3 — Citation Verification Report

Five statuses only: ✅ Verified / ⚠️ Not found / ❌ Mismatch / ⏳ Unverified (tool error) / ℹ️ Non-PubMed.

```markdown
## Citation Verification Report

**Total:** [N] citations — ✅ [n] · ⚠️ [n] · ❌ [n] · ⏳ [n] · ℹ️ [n]
**Batches:** [k] × 10（> 40 条时分批，逐批追加到本表）

| # | Citation | PMID | Status | Notes |
|---|---------|------|--------|-------|
| 1 | Smith et al., 2024, Lancet | 39123456 | ✅ Verified | — |
| 2 | Lee et al., 2023, Nature | — | ⚠️ Not found | Query succeeded, no hit; ask user for DOI |
| 3 | Wang et al., 2022, JAMA | 35678901 | ❌ Mismatch | Year is 2021, not 2022 |
| 4 | Chen et al., 2020, Eur Urol | — | ⏳ Unverified (tool error) | get_article_metadata timed out; retry pending |
| 5 | Goodfellow et al., 2016 (book) | — | ℹ️ Non-PubMed | Book; checked via publisher DOI |
| 6 | Vaswani et al., 2017, NeurIPS | — | ℹ️ Non-PubMed | arXiv:1706.03762 checked via WebSearch |
```

Rules recap: ⚠️ only after a successful query with no hit; ⏳ never counts as "does not exist";
ℹ️ entries are verified outside PubMed and must say how.

## Mode 6 — Reference Format Lookup

| 格式 | 适用期刊 | 示例 |
|------|---------|------|
| Vancouver | Lancet, BMJ, EU, JU | Smith J, Lee K. Title. J Name. 2024;1(2):3-4. doi:10.xxxx/xxxxx |
| AMA (JAMA) | JAMA 家族 | Smith J, Lee K. Title. J Name. 2024;1(2):3-4. doi:XX |
| Nature | Nature 家族, npj | Smith, J. & Lee, K. Title. J. Name 1, 3–4 (2024). |
| APA 7th | 心理学/教育 | Smith, J., & Lee, K. (2024). Title. J Name, 1(2), 3–4. |
| IEEE | IEEE JBHI, TMI | [1] J. Smith and K. Lee, "Title," J. Name, vol. 1, no. 2, pp. 3–4, 2024. |
