## What changed and why

## Checklist
- [ ] `python3 tools/check_consistency.py` passes (versions, counts, paths, frontmatter, links)
- [ ] `python3 -m pytest tests -q` passes (if scripts changed, tests were added/updated)
- [ ] Every fact/number added (item counts, word limits, IF) has a source URL or DOI in the file
- [ ] New reporting-standard checklists are transcribed from the source paper (header names the DOI/PMCID)
- [ ] README.md and README_CN.md changed together; CHANGELOG.md has an entry
- [ ] Version bumped in `.claude-plugin/plugin.json` and `marketplace.json` if users should receive this change
- [ ] `claude plugin eval . --tag smoke --ablation none --runs 1` still routes correctly (if skill descriptions changed)
