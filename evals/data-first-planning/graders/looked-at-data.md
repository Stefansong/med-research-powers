---
type: tool_used
tool: Read
input_match: 'data\.csv'
min: 1
---

PASS if the assistant opened data.csv (looked at the real data) before writing the plan. The case grants no shell, so
the read-only check-up has to be done with Read/Grep instead of data_profile.py; in normal use the skill runs data_profile.py.
