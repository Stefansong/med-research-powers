---
description: Turn a vague idea into a clear PICO question + hypothesis (research-question-formulation)
argument-hint: [research idea or topic]
disable-model-invocation: true
---

# Research Question

Invoke the `research-question-formulation` skill with the user's idea: $ARGUMENTS

- **Output:** `research-question.md` (PICO, FINER score, H0/H1)
- **Next step:** `literature-synthesis` (`/mrp:literature-synthesis`) to map the existing evidence, then `study-design`.
