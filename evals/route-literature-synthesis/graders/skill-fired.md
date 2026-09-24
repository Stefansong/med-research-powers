---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?literature-synthesis"'
min: 1
---

PASS if the `literature-synthesis` skill was invoked (Skill tool call whose input names `mrp:literature-synthesis`).
FAIL if it was not invoked.
