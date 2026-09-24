---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?team-collaboration"'
min: 1
---

PASS if the `team-collaboration` skill was invoked (Skill tool call whose input names `mrp:team-collaboration`).
FAIL if it was not invoked.
