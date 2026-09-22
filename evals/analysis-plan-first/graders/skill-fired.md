---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?data-analysis-planning"'
min: 1
---

PASS if the `data-analysis-planning` skill was invoked (Skill tool call whose input names `mrp:data-analysis-planning`).
FAIL if it was not invoked.
