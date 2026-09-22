---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?journal-selection"'
min: 1
---

PASS if the `journal-selection` skill was invoked (Skill tool call whose input names `mrp:journal-selection`).
FAIL if it was not invoked.
