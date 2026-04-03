# Study Design

Invoke the `study-design` skill for clinical research, `basic-medical-study-design` for bench science, or `ai-medical-study-design` for AI/ML studies.

## Routing
- Clinical trial / observational → `study-design`
- Cell / animal / molecular → `basic-medical-study-design`
- AI / ML / imaging / devices → `ai-medical-study-design`
- Multiple types → combine as needed

## Workflow
1. Select study type (RCT / cohort / case-control / cross-sectional / diagnostic / prediction)
2. Define participants (inclusion/exclusion criteria)
3. **Sample size calculation** (MANDATORY — use `power_analysis.py`)
4. Define variables (independent, dependent, confounders)
5. Data collection plan (timepoints, methods, quality control)
6. SAP outline → detailed plan in `data-analysis-planning`
7. Ethics considerations → reminder to check `research-ethics`

## Output
`study-protocol.md` — complete research protocol.

## Hard Checkpoint
**User must confirm the protocol before proceeding.** Research type and primary outcome are LOCKED after confirmation.

## Mandatory next step
After confirmation → `journal-selection` (early journal targeting) + `data-analysis-planning` (SAP).
