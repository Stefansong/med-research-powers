---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?research-ethics"'
min: 1
---

PASS if the `research-ethics` skill was invoked (Skill tool call whose input names `mrp:research-ethics`).
FAIL if it was not invoked.
