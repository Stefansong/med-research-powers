---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?(?:figure-generation|data-analysis-planning)"'
min: 1
---

PASS if `figure-generation` (or `data-analysis-planning`, which owns the quick SAP this request needs) was invoked.
Indicator only in a two-arm run.
