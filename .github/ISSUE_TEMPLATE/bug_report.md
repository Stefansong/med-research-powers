---
name: Bug report / 问题反馈
about: A skill gave wrong guidance, a script failed, or the plugin did not install
labels: bug
---

**MRP version** (`claude plugin list`): 
**Claude Code version** (`claude --version`): 
**Skill / script / command involved**: 

**What happened** (paste the prompt and the relevant part of Claude's reply or the script's error):

**What should have happened**:

**Checks** (tick what you ran):
- [ ] `python3 tools/check_consistency.py` passes on main
- [ ] `python3 -m pytest tests -q` passes
- [ ] The wrong fact/number is quoted with its source (paper, guideline page) so it can be fixed, not guessed
