---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?peer-review-simulation"'
min: 1
---

PASS if the `peer-review-simulation` skill was invoked (Skill tool call whose input names `mrp:peer-review-simulation`).
FAIL if it was not invoked.
