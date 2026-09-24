---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?manuscript-writing"'
min: 1
---

PASS if the `manuscript-writing` skill was invoked (Skill tool call whose input names `mrp:manuscript-writing`).
FAIL if it was not invoked.
