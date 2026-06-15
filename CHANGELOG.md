# Changelog

## v6.2.3 (2026-06-15)

Consistency & runtime-correctness pass. Closes the gaps the v6.2.2 audit missed (the hook and installer were *not* "already current") and adds a CI guard so this class of drift can't recur.

### Bug Fixes
- **Version drift** — `plugin.json`/`marketplace.json` were at 6.2.2 while the `session-start.sh` hook, `install.sh`, `README*.md`, and `docs/` still said 6.2.1. Unified every version string at **6.2.3**.
- **`session-start.sh`**: the always-injected rule said "CONSORT 2025 — 30 items", contradicting the corrected `reporting-standards`/README count. Fixed to **31 numbered items / 34 rows**. Also removed a duplicated `python3 -c "import docx"` probe.
- **Runtime script paths** — `manuscript-export`, `figure-generation`, `statistical-analysis`, and `study-design` referenced plugin scripts (`export_docx.py`, `pub_style.py`, `analysis_template.py`, `power_analysis.py`) by skill-relative paths that don't resolve from the user's working directory. Now anchored to `${CLAUDE_PLUGIN_ROOT}/skills/.../scripts/...`.
- **Standards count** — corrected the "42+ reporting standards" claim to the real **41** across manifests, README*, and docs (the on-disk index has 41 entries); fixed the resulting broken TOC anchor in `USER-MANUAL.md`.
- Removed a stray `plugin.json.bak.*` backup from `.claude-plugin/`; added `*.bak*`/`*.orig` to `.gitignore`.

### Tooling
- Added `tools/check_consistency.py` — asserts a single version string everywhere, that claimed counts (20 skills / 20 commands / 234 journals / 41 standards) match disk, and that plugin scripts are referenced via `${CLAUDE_PLUGIN_ROOT}`.
- Added `.github/workflows/ci.yml` — runs the guard plus JSON/YAML validation and `compileall` on every push and PR.

---

## v6.2.2 (2026-05-26)

Consistency & bug-fix pass (multi-agent audit + re-verification). No behavioural changes to the dynamic `session-start.sh` hook or `install.sh` (already current).

### Bug Fixes
- **`manuscript-export/scripts/export_docx.py`**: read the journal list from the `templates:` key (was `journals:`, which never matched) — the 234-journal formatting library now actually loads per-journal word/reference limits. Removed 3 non-existent IDs from `JOURNAL_FAMILY_MAP`, and removed `[N]` from placeholder detection (caused false positives in template tables).
- **`journal-selection`**: corrected the scoring denominator (25 → 45, matching the weighted formula) and rescaled tier thresholds (≥36 / ≥29 / ≥22) and report columns to `/45`.
- Reconciled the AI data-split bands into a single identical 4-band table (`n>1000 / 200-1000 / 50-200 / <50`) across `study-design`, `data-analysis-planning`, and `stat-method-decision-tree.yaml`.
- Fixed broken/relative reference paths (cross-skill `journal-templates.yaml`, `assumption_tests.py`, etc.) and stale skill names (`ai-medical-study-design` → `study-design`).

### Skill Quality (writing-mrp-skills compliance)
- Trimmed all over-length `description` fields to ≤200 chars (e.g. `study-design` 622 → 192).
- Added missing `## Output` / `## Red Flags — STOP` sections and normalized `衔接规则` to the three canonical tiers across skills.
- Content layering: moved lookup tables, templates, and checklists into `references/`, and reusable code into `scripts/` (new `analysis_template.py`), to keep `SKILL.md` lean. Removed ~115 lines of inline Python in `manuscript-export` that duplicated `export_docx.py`.
- `team-collaboration`: removed the fabricated `Agent(name=…, prompt=…)` API; dispatch is now via the Task tool. Reconciled the reviewer panel to 4 (methods/clinical/editor/devil's-advocate).
- Ethics standardized as Gate 5; PubMed MCP tools fully prefixed `mcp__claude_ai_PubMed__`.
- `reporting-standards`: CONSORT 2025 count corrected to 31 numbered items / 34 rows; unified "TRIPOD+AI 2024" naming; added CLAIM routing for AI imaging; removed an unverified `mval` entry.
- De-duplicated the cover-letter / cascade-rewrite mechanics into `submission-preparation` (single owner).

### Commands
- Added slash-menu `description:` frontmatter to all 20 commands; converted them to thin routers that name their target skill.
- De-duplicated the study-type→standard and 6-gate tables (now defer to the skills); split `check-standards` (reporting-guideline check) vs `pre-submission` (mandatory 6-gate).

### Docs
- Rewrote `README.md` and `README_CN.md`: corrected and internally consistent counts (20 skills / 20 commands / 234 journals / 42+ standards / 6 gates), removed stale pre-6.x architecture; corrected counts in `docs/`.

---

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
