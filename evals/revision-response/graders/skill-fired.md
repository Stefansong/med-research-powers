---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?revision-response"'
min: 1
---

PASS if the `revision-response` skill was invoked (Skill tool call whose input names `mrp:revision-response`).
FAIL if it was not invoked.
