# Changelog

## v5.0.0 (2026-03-29)

### Architecture
- **Plugin system**: Added `.claude-plugin/plugin.json` for Claude Code plugin install
- **Session hook**: Added `hooks/session-start.sh` — auto-injects MRP context on every new session
- **Slash commands**: Added 5 commands (`/mrp:research-question`, `/mrp:analyze-data`, `/mrp:write-manuscript`, `/mrp:check-standards`, `/mrp:peer-review`)
- **Installer**: Added `install.sh` with interactive setup (plugin / copy / symlink)

### New Skills (3)
- `pre-submission-verification` — 5-gate mandatory check before submission (reporting standards → statistical completeness → figure quality → ethics → formal requirements)
- `responding-to-reviewers` — Systematic point-by-point reviewer response with revision tracking
- `writing-mrp-skills` — Meta-skill for creating and testing new MRP skills

### Skill Improvements (all 13 original)
- All SKILL.md files rewritten to unified format
- All descriptions changed to "Use when [condition]" format (no workflow summaries)
- Added Common Mistakes table to every skill
- Added Convergence signal (exit criteria) to every skill
- Added mandatory/prerequisite/optional linkage rules to every skill
- Content reduced ~23% through reference extraction

### Scripts (3 new)
- `figure-generation/scripts/pub_style.py` — Publication-quality matplotlib styling
- `statistical-analysis/scripts/assumption_tests.py` — Normality, homogeneity, test recommendation
- `statistical-analysis/scripts/power_analysis.py` — Sample size for 5 study designs

### References (10 new files)
- `reporting-standards/references/checklists/consort-2025.yaml` — Full 30-item checklist
- `reporting-standards/references/checklists/standards-index.yaml` — ~40 standards master index
- `data-analysis-planning/references/stat-method-decision-tree.yaml`
- `ai-medical-study-design/references/metrics-and-reporting.yaml`
- `basic-medical-study-design/references/experiment-templates/western-blot.md`
- `basic-medical-study-design/references/experiment-templates/qpcr.md`
- `basic-medical-study-design/references/experiment-templates/animal-study.md`

### Reporting Standards
- Updated CONSORT 2010 → **CONSORT 2025** (30 items, officially supersedes 2010)
- Updated SPIRIT 2013 → **SPIRIT 2025** (34 items)
- Added 23 new standards: DECIDE-AI, IDEAL, ROBINS-I, TIDieR, CONSORT-Harms, RECORD, STROCSS, PRISMA-P/ScR/S, TRIPOD-SRMA/Cluster, MI-CLAIM, AMSTAR 2, GRADE, SRQR, CHEERS, MINORS
- Total coverage: ~40 reporting standards + bias assessment tools

## v3.0.0 (2026-02)

- Initial release with 13 skills
- Core pipeline: research-question → study-design → analysis → writing
- Basic reporting standards coverage (16 standards)
