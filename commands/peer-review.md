# Peer Review Simulation

Invoke the `peer-review-simulation` skill to identify problems before submission.

## Workflow

Simulate **4 reviewers** with different perspectives + **0-100 quantitative scoring**.

### Reviewer Panel
1. **Methodologist** — study design, statistics, sample size, bias, reproducibility
2. **Clinical Expert** — clinical significance, applicability, alternative explanations
3. **Editor** — structure, language, figures, references, journal fit
4. **Devil's Advocate** — challenges strongest conclusions, finds blind spots, proposes worst-case alternative explanations

### Scoring (8 dimensions, 0-100)
Originality (15%), Methodology (20%), Results (15%), Clinical Impact (15%),
Writing Quality (10%), Figures (10%), References (5%), Reproducibility (10%)

| Score | Decision |
|-------|----------|
| 80-100 | Accept / Minor Revision |
| 65-79 | Minor Revision |
| 50-64 | Major Revision |
| <50 | Reject |

### Severity
Each specific comment also gets: Critical / Major / Minor / Suggestion.

## Output
`peer-review-simulation-report.md` with scoring matrix + per-reviewer comments + priority fix list.

## Blocking rule
If ANY Critical issue → **block** submission. Must fix and re-run.
Devil's Advocate claim issues → triggers `pre-submission-verification` Gate 3.
