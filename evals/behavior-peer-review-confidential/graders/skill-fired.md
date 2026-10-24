---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?(?:peer-review-simulation|using-med-research-powers)"'
min: 1
---

PASS if `peer-review-simulation` (or the orchestrator that routes to it) was invoked. Indicator only in a two-arm run.
