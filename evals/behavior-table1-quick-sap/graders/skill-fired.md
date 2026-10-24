---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?(?:data-analysis-planning|statistical-analysis)"'
min: 1
---

PASS if `data-analysis-planning` (quick descriptive SAP) or `statistical-analysis` (which sends a request without a
confirmed plan to the quick path) was invoked. Indicator only in a two-arm run.
