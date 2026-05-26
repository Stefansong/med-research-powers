---
description: Run multi-agent parallel research tasks (lead + specialist agents)
argument-hint: [tasks to parallelize]
---

# Team Collaboration

Run independent research subtasks in parallel with multiple agents.

Invoke the `team-collaboration` skill, which contains the authoritative preset scenarios (parallel literature search, parallel analysis + writing, 4-reviewer simulation, parallel revision, multi-expert protocol review), the lead/specialist orchestration model, and decomposition rules. Pass through the user's tasks: $ARGUMENTS

## Key Rule
Only independent subtasks can be parallelized — tasks with sequential dependencies cannot.
