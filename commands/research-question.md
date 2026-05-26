---
description: Turn a vague idea into a clear PICO question + hypothesis (research-question-formulation)
argument-hint: [research idea or topic]
---

# Research Question Formulation

Turn a vague research idea into a clear, testable question.

Invoke the `research-question-formulation` skill, which contains the authoritative Socratic PICO workflow, FINER scoring, hypothesis formulation, and convergence criteria. Pass through the user's idea: $ARGUMENTS

The skill produces `research-question.md` and converges only when PICO is fully explicit, the hypothesis is stated in statistical terms (H0/H1), and the user confirms.

## Mandatory next step
After completion, suggest `/literature-synthesis` (check existing evidence) or `/study-design` (if the landscape is already known).
