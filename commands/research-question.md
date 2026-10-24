---
description: Turn a vague idea into a clear PICO question + hypothesis (research-question-formulation)
argument-hint: [research idea or topic]
disable-model-invocation: true
---

# Research Question

Invoke the `research-question-formulation` skill with the user's idea: $ARGUMENTS

- **Output:** `research-question.md` (PICO / PECO / PIRD, FINER score with a recorded novelty search, H0/H1 for hypothesis-testing studies or aims and estimands for descriptive and prediction-model studies). Works without the PubMed MCP (the novelty search then uses PubMed E-utilities via WebFetch, or the user runs it).
- **Next step:** `literature-synthesis` (`/mrp:literature-synthesis`) to map the existing evidence, then `study-design`.
