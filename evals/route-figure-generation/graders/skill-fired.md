---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?figure-generation"'
min: 1
---

PASS if the `figure-generation` skill was invoked (Skill tool call whose input names `mrp:figure-generation`).
FAIL if it was not invoked.
