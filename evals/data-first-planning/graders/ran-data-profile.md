---
type: tool_used
tool: Bash
input_match: 'data_profile\.py'
min: 1
---

PASS if the assistant ran the bundled read-only data check-up `data_profile.py` (a Bash call whose command names it)
before writing the plan. This is the skill's real path, and a no-plugin baseline cannot know the script, so this
grader separates the arms. It needs the operator grant `--allow-tools "Bash(python3 *)"` (a case cannot grant Bash
to itself); without the grant Bash is removed from the run and this grader fails.
