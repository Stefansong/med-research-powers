# PubMed Search — Output Templates & Reference Formats

Loaded on demand by pubmed-search. Keep the 6-Mode workflow (reasoning) in
SKILL.md; this file holds static templates and the reference-format lookup.

All PubMed MCP tools carry the full prefix `mcp__claude_ai_PubMed__`.

## Mode 3 — Citation Verification Report

```markdown
## Citation Verification Report

| # | Citation | PMID | Status | Notes |
|---|---------|------|--------|-------|
| 1 | Smith et al., 2024, Lancet | 39123456 | ✅ Verified | — |
| 2 | Lee et al., 2023, Nature | — | ⚠️ Not in PubMed | May be non-biomedical |
| 3 | Wang et al., 2022, JAMA | 35678901 | ❌ Mismatch | Year is 2021, not 2022 |
```

## Mode 6 — Reference Format Lookup

| 格式 | 适用期刊 | 示例 |
|------|---------|------|
| Vancouver | Lancet, BMJ, EU, JU | Smith J, Lee K. Title. J Name. 2024;1(2):3-4. doi:10.xxxx/xxxxx |
| AMA (JAMA) | JAMA 家族 | Smith J, Lee K. Title. J Name. 2024;1(2):3-4. doi:XX |
| Nature | Nature 家族, npj | Smith, J. & Lee, K. Title. J. Name 1, 3–4 (2024). |
| APA 7th | 心理学/教育 | Smith, J., & Lee, K. (2024). Title. J Name, 1(2), 3–4. |
| IEEE | IEEE JBHI, TMI | [1] J. Smith and K. Lee, "Title," J. Name, vol. 1, no. 2, pp. 3–4, 2024. |
