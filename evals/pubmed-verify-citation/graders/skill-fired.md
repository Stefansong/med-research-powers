---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?pubmed-search"'
min: 1
---

PASS if the `pubmed-search` skill was invoked (Skill tool call whose input names `mrp:pubmed-search`).
FAIL if it was not invoked.
