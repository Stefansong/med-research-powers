---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?submission-preparation"'
min: 1
---

PASS if the `submission-preparation` skill was invoked (Skill tool call whose input names `mrp:submission-preparation`).
FAIL if it was not invoked.
