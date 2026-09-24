---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?using-med-research-powers"'
min: 1
---

PASS if the `using-med-research-powers` skill was invoked (Skill tool call whose input names `mrp:using-med-research-powers`).
FAIL if it was not invoked.
