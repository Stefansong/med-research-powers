---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?(?:figure-generation|manuscript-writing|study-design|research-question-formulation|data-collection-tools)"'
min: 0
max: 0
arm: both
---

PASS if none of figure-generation, manuscript-writing, study-design, research-question-formulation or
data-collection-tools was invoked: the user asked for one artifact (Table 1) from data already collected, so the
skill must neither send them back to write a protocol or research question first nor run on into figures or writing.
