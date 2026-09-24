---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?data-collection-tools"'
min: 1
---

PASS if the `data-collection-tools` skill was invoked (Skill tool call whose input names `mrp:data-collection-tools`).
FAIL if it was not invoked.
