# Revision Response

Invoke the `revision-response` skill to plan revision strategy and draft point-by-point responses after receiving a revision decision.

## Two Phases

### Phase 1: Revision Strategy
1. Parse all reviewer comments → categorize as Critical / Major / Minor / Reject candidate
2. Triage: which comments MUST be addressed, which can be respectfully declined
3. Generate `revision-plan.md` with timeline and priority order
4. For reject + resubmit: identify target journals and scope of rewrite

### Phase 2: Point-by-Point Response
1. Draft Response Letter for each reviewer comment
2. Format: Quote comment → Our response → Changes made (with line/page reference)
3. "Respectful disagreement" template for unjustified demands
4. Final letter uses journal-standard header (cover letter format)

## Output

| File | Description |
|------|-------------|
| `revision-plan.md` | Prioritized list of changes + strategy |
| `response-letter.md` | Point-by-point response to all reviewers |

## Mandatory next step
After revision and response letter complete → re-run `pre-submission-verification` before resubmission.
