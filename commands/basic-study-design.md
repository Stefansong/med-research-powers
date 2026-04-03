# Basic Medical Study Design

Invoke the `basic-medical-study-design` skill for bench science experiments.

## Scope
Cell biology, animal models, molecular biology, histopathology, Western blot, qPCR, flow cytometry.

## Workflow
1. Define hypothesis and experimental groups (treatment vs control)
2. Select experiment type → load reference template:
   - `references/western-blot.md` — WB experiment design
   - `references/qpcr.md` — qPCR experiment design
   - `references/animal-study.md` — Animal study (ARRIVE 2.0)
3. Design controls (positive, negative, vehicle)
4. Sample size: biological replicates (NOT technical replicates; 3 wells ≠ n=3)
5. Randomization and blinding plan
6. Data collection and analysis plan

## Key Rules
- Biological replicate = independent experiment, NOT duplicate wells
- SD not SEM for data presentation (SEM is cosmetic reduction)
- Animal experiments MUST be randomized
- WB requires densitometric quantification (not "visually obvious")

## Output
Experiment protocol document.
