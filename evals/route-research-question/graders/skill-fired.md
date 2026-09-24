---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?research-question-formulation"'
min: 1
---

PASS if the `research-question-formulation` skill was invoked (Skill tool call whose input names `mrp:research-question-formulation`).
FAIL if it was not invoked.
