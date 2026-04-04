# Changelog

## v6.2.1 (2026-04-03)

### Bug Fixes
- Fixed 6 stale commands pointing to merged/deleted skills
- Fixed `session-start.sh` referencing old skill names (basic-medical-study-design, ai-medical-study-design, responding-to-reviewers, etc.)
- Fixed README_CN.md journal count (229 → 234)
- Registered `session-start.sh` hook in `plugin.json` (was present but never executed)
- Fixed `settings.local.json` python3 permission rule syntax

### Commands
- Removed 6 stale commands: `ai-study-design`, `basic-study-design`, `cover-letter`, `responding-to-reviewers`, `revision-strategy`, `submission-guide`
- Added 3 missing commands: `pubmed-search`, `manuscript-export`, `data-collection-tools`
- Updated `study-design` command to reflect unified type router (A/B/C/D/E)

### Infrastructure
- `session-start.sh` rewritten as dynamic hook: raw JSON dump of `.mrp-state.json` and `.mrp-user-profile.json`; routing table suppressed for ongoing projects; ACTION REQUIRED prompt when no user profile found

---

## v6.2.0 (2026-04-03)

### New Skills (4, from v6.0.0 → v6.2.0)
- `pubmed-search` — PubMed MCP deep integration (6 modes: interactive search, batch metadata, citation verification, snowball search, full-text extraction, reference formatting)
- `manuscript-export` — Export Markdown manuscript to journal-formatted .docx via python-docx
- `data-collection-tools` — Auto-generate data collection instruments from study protocol (CRF, inference scripts, annotation templates, PRISMA tables)
- `team-collaboration` — Multi-agent parallel research workflow coordination

### Skill Consolidation (26 → 20 skills)
- `study-design` — Unified type router replacing 3 separate skills (clinical/basic/AI-ML) + added qualitative and survey types (Type A–E)
- `revision-response` — Merged `revision-strategy` + `responding-to-reviewers`
- `submission-preparation` — Merged `cover-letter-writing` + `submission-system-guide`
- Removed standalone: `ai-medical-study-design`, `basic-medical-study-design`, `qualitative-study-design`, `survey-design`

### Improvements
- Journal templates: 68 → 234 journals across 30+ specialties
- Reporting standards: 40 → 42+ (added TRIPOD-LLM 2024, CONSORT-AI 2020)
- `data-analysis-planning`: Added AI/ML SAP Extension (sections 8–16)
- `research-question-formulation`: Added PIRD framework for AI diagnostic accuracy studies
- `manuscript-writing`: Added NMA (network meta-analysis) support
- All skills: selective constraints replacing blanket downstream blocking; 4 hard checkpoints preserved

---

## v6.0.0 (2026-03-30)

### Architecture Rewrite
- Migrated from skills-only to full Claude Code plugin (`.claude-plugin/`)
- Added `marketplace.json` for plugin marketplace listing
- Added `.mrp-state.json` session persistence specification
- Added `.mrp-user-profile.json` cross-session user memory specification
- Added `using-med-research-powers` orchestrator skill with full pipeline map, checkpoint protocol, and backward link rules
- Added `pre-submission-verification` upgraded to 6-Gate (added Gate 6: PubMed MCP claim verification)

### Reporting Standards
- Updated CONSORT 2010 → **CONSORT 2025** (30 items)
- Updated SPIRIT 2013 → **SPIRIT 2025**
- Total coverage: 40+ reporting standards

---

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
