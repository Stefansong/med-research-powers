---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?reporting-standards"'
min: 1
---

PASS if the `reporting-standards` skill was invoked (Skill tool call whose input names `mrp:reporting-standards`).
FAIL if it was not invoked.
