---
description: Search PubMed, verify citations, or fetch article metadata via PubMed MCP
argument-hint: [topic, PMIDs, or citation to verify]
---

# PubMed Search

Search PubMed, verify citations (anti-hallucination), or retrieve article metadata via PubMed MCP tools.

Invoke the `pubmed-search` skill, which contains the authoritative mode router (interactive search, batch metadata, citation verification, snowball, full text, reference formatting) and the PubMed MCP tool list. Pass through the user's topic / PMIDs / citation: $ARGUMENTS

## Called by
`/literature-synthesis`, `/pre-submission` (Gate 3 claim verification), and `/write-manuscript` (reference formatting).
