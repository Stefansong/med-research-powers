# Research Question Formulation

Invoke the `research-question-formulation` skill to define a clear research question.

## Workflow

1. **Socratic questioning** — Ask PICO elements one by one (Population, Intervention/Exposure, Comparison, Outcome)
2. **FINER evaluation** — Score Feasibility, Interest, Novelty, Ethics, Relevance (1-5 each)
3. **Hypothesis formulation** — State H0 and H1 in statistical terms
4. **Generate `research-question.md`** — Structured document for downstream skills

## Convergence

Stop when ALL three conditions are met:
1. PICO four elements are all explicit
2. Hypothesis can be stated in statistical language
3. User confirms the question definition is accurate

## Mandatory next step

After completion → suggest `literature-synthesis` (to check existing evidence) or `study-design` / `ai-medical-study-design` (if user already knows the landscape).
