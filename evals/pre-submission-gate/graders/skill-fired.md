---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?pre-submission-verification"'
min: 1
---

PASS if the `pre-submission-verification` skill was invoked (Skill tool call whose input names `mrp:pre-submission-verification`).
FAIL if it was not invoked.
