---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?manuscript-export"'
min: 1
---

PASS if the `manuscript-export` skill was invoked (Skill tool call whose input names `mrp:manuscript-export`).
FAIL if it was not invoked.
