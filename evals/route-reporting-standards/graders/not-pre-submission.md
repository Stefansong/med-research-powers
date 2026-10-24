---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:)?pre-submission-verification"'
min: 0
max: 0
arm: both
---

PASS if `pre-submission-verification` was NOT invoked — a one-guideline check on one section is `reporting-standards`, not the 6-gate pre-submission check.

Single-arm guard: read this case under `--ablation none`. In a two-arm run the `skill-fired` grader is only an
indicator and a no-plugin baseline passes this guard trivially (it has no MRP skills to invoke), so both arms score
1.0 and the run says nothing about routing.
