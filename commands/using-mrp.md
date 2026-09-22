---
description: Orchestrator for all MRP skills — routing rules, pipeline, and checkpoints
argument-hint: [what you want to do]
disable-model-invocation: true
---

# Using MRP

Invoke the `using-med-research-powers` skill with the user's context: $ARGUMENTS

The skill owns the routing table, the pipeline order, the 3 mandatory checkpoints (protocol / SAP / pre-submission) and the `.mrp-state.json` update step.

- **Output:** the matching skill is started, or the resume point from `.mrp-state.json` is reported.
- **Next step:** whatever the skill routes to. Any skill can also be called directly as `/mrp:<skill-name>`.
