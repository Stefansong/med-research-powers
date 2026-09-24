---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?statistical-analysis"'
min: 1
---

PASS if the `statistical-analysis` skill was invoked (Skill tool call whose input names `mrp:statistical-analysis`).
FAIL if it was not invoked.
