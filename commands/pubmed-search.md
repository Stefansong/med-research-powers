# PubMed Search

Invoke the `pubmed-search` skill to search PubMed, verify citations, or retrieve article metadata using PubMed MCP tools.

## Modes

| Mode | When to use |
|------|-------------|
| **Mode 1: Interactive Search** | Build a complex PubMed query from a research topic (PICO → MeSH → Boolean) |
| **Mode 2: Batch Metadata** | Retrieve full metadata for a list of PMIDs |
| **Mode 3: Citation Verification** | Verify references exist and match (anti-hallucination) |
| **Mode 4: Snowball Search** | Discover related articles from 1-5 seed PMIDs |
| **Mode 5: Full Text** | Retrieve PMC full text for data extraction |
| **Mode 6: Reference Formatting** | Format references in Vancouver / AMA / Nature / APA / IEEE |

## MCP Tools Used

`search_articles` · `get_article_metadata` · `get_full_text_article` · `find_related_articles` · `convert_article_ids` · `lookup_article_by_citation` · `get_copyright_status`

## Output

- `search-strategy.md` — reproducible search query + result count
- Citation verification report (✅ Verified / ⚠️ Not found / ❌ Mismatch)
- Formatted reference list (target journal style)

## Called by

`literature-synthesis` · `pre-submission-verification` (Gate 3 claim verification) · `manuscript-writing` (reference formatting)
