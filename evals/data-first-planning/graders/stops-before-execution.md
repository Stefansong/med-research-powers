---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?(?:statistical-analysis|data-collection-tools)"'
min: 0
max: 0
arm: both
---

PASS if neither `statistical-analysis` nor `data-collection-tools` was invoked: the plan is hard checkpoint 2, so the
run must stop for the user's confirmation instead of executing the analysis, and the data are already collected, so
collection tools are never the next step.
