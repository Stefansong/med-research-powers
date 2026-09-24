---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?writing-mrp-skills"'
min: 1
---

PASS if the `writing-mrp-skills` skill was invoked (Skill tool call whose input names `mrp:writing-mrp-skills`).
FAIL if it was not invoked.
