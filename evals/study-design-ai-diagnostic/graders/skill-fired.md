---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?study-design"'
min: 1
---

PASS if the `study-design` skill was invoked (Skill tool call whose input names `mrp:study-design`).
FAIL if it was not invoked.
