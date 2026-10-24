---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:mrp:|(?:using-med-research-powers|research-question-formulation|literature-synthesis|pubmed-search|study-design|research-ethics|journal-selection|data-analysis-planning|data-collection-tools|statistical-analysis|figure-generation|manuscript-writing|manuscript-export|reporting-standards|peer-review-simulation|pre-submission-verification|submission-preparation|revision-response|team-collaboration|writing-mrp-skills)")'
min: 0
max: 0
arm: both
---

PASS if no MRP skill was invoked, with or without the `mrp:` prefix: "is p=0.06 significant?" is a single-point
question that the orchestrator answers directly (its When NOT to Use names this example), not a reason to start the
planning or analysis workflow. Scored in both arms.
