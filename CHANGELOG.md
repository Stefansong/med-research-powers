# Changelog

## v6.3.0 (2026-09-21)

Full review-and-upgrade release. A repository-wide audit (6 parallel reviews, every high-severity finding re-verified against source, scripts executed, CONSORT 2025 checked against the BMJ paper, plugin install/namespace verified on Claude Code 2.1.278) found four classes of problems — the plugin could not be installed as documented, several facts written into protocols/manuscripts were wrong, bundled scripts failed when called as documented, and three core mechanisms existed only as prose. This release fixes all of them.

### Breaking / migration
- **Plugin `name` is now `mrp`** (was `med-research-powers`), so the documented `/mrp:<command>` and `/mrp:<skill>` names finally match what Claude Code registers (the namespace prefix is always the plugin name). Install id is `mrp@med-research-powers`. Migration: `/plugin uninstall med-research-powers@med-research-powers` → `/plugin marketplace add Stefansong/med-research-powers` → `/plugin install mrp@med-research-powers`.
- **Commands reduced from 20 to 7** (`analyze-data`, `check-standards`, `peer-review`, `pre-submission`, `research-question`, `using-mrp`, `write-manuscript`). The 13 commands that shared a name with a skill were shadowed by the skill and only duplicated the skill list; call those skills as `/mrp:<skill>`. Remaining commands carry `disable-model-invocation: true` (user-only aliases).
- **Protocol output is always `study-protocol.md`** (with a `type:` field) for all five study types; `qualitative-protocol.md` / `survey-protocol.md` no longer exist.
- **User profile moved to `~/.claude/mrp-user-profile.json`** (per person, not per project) and is collected lazily; the 5-question interview at session start is gone.
- `install.sh` copy/symlink modes replaced by a single whole-repository symlink (`~/.claude/skills/med-research-powers`), which loads as a `mrp@skills-dir` plugin so hooks and `${CLAUDE_PLUGIN_ROOT}` keep working.

### Fixed — installation and packaging
- README / README_CN / USER-MANUAL / install.sh: `/plugin install ./med-research-powers` and `/plugin install https://…` (not valid syntax) replaced by the two-step marketplace flow; added `--plugin-dir` dev flow, 6.2.x migration and an Uninstall section.
- marketplace.json: removed `"strict": false` (conflicted with the hooks declared in plugin.json); plugin.json gains `homepage`/`repository`; hook command path is quoted.
- install.sh: runs `claude plugin marketplace add … && claude plugin install …` when the CLI is present; `--method 1|2`, non-interactive default; `pip install docx` → `python-docx`; verification via `claude plugin list` (the hook's text is context for Claude, not visible to the user). New `requirements.txt`.

### Fixed — facts that were wrong
- **CONSORT 2025 has 30 items (42 rows incl. sub-items), not "31 items / 34 rows"** (Hopewell et al., BMJ 2025;389:e081123). `consort-2025.yaml` rewritten from Table 1 of the statement with official numbering (1a/1b … 21a-d … 30), new/revised flags and `critical` markers; hook, orchestrator, README, docs corrected.
- `power_analysis.survival()` doubled the required event count (`* (1 + ratio)` applied twice): HR 0.7, 1:1 now gives ≈247 events / 549 patients (was 494 / 1098).
- `assumption_tests.full_check()` recommended a t-test when every group had n<8 (`all([])` is True); now non-parametric with a warning.
- team-collaboration: the sub-agent tool is **Agent** (Task is the legacy alias); the Red Flag that forbade `Agent(...)` is removed.
- submission-systems.yaml: Lancet uses Editorial Manager, Nature uses its own MTS (eJournalPress), Science uses eJP; added eJP and Snapp categories.
- pubmed-search: real MCP parameter names (`find_related_articles(pmids=[…])`, `convert_article_ids(ids=[…], id_type=…)`), `mesh_terms` comes from `get_article_metadata`, and a tool error is now `⏳ Unverified` instead of "reference does not exist". Hard-coded `mcp__claude_ai_PubMed__` prefix removed everywhere — the server name follows the session's tool list.
- reporting-standards index: CLAIM 2024 (44 items), TRIPOD-SRMA/-Cluster 2023, TRIPOD-LLM 2025, Newcastle-Ottawa max 9, DECIDE-AI 17+10, CARE 2013 (E&E 2017), PROBAST+AI note. Added CHERRIES, CROSS, COSMIN, TREND, CONSORT non-inferiority extension → **46 standards**.
- journal-templates.yaml (now **240 journals**): every entry has a `family` field (lancet / jama / nature / ieee / standard) and the file carries a `data_as_of` rule. **41 frequently targeted journals** (all urology, radiology and AI/digital-health titles plus top general, oncology and surgery journals) now hold the publisher-reported **JCR 2025 (or 2024) impact factor with `IF_year` and `IF_source`**; 9 APCs updated with `apc_year`. About twenty author-guideline corrections from the journals' own pages (e.g. European Urology 2500 words / abstract ≤250 / combined 5 display items, Radiology 3000 words / ≤35 references, World J Urol and npj Digital Medicine on Snapp, J Urol on Editorial Manager, IEEE Author Portal for TMI/JBHI). Six journals added from their author guidelines: Urologic Oncology, Journal of Endourology, European Journal of Radiology, Abdominal Radiology, JAMIA, Cancers. eLife / eClinicalMedicine "no APC" corrected; European Urology family abstract headings updated to the 2023 format; Nature-family submission systems corrected.
- study-design: non-inferiority now requires ITT **and** PP; qualitative coding rules follow the methodology (codebook vs reflexive TA/IPA); ACE naming; data-split bands `200 ≤ n ≤ 1000` / `50 ≤ n < 200`; CLAIM 2024 throughout; regression vs risk-prediction metrics separated.
- Smaller: decision tree (paired → normality of differences; ordinal two-group → Mann-Whitney/CMH), multiple imputation example (`sample_posterior=True` + Rubin's rules), RCT baseline tables use SMD not p-values, peer-review score→decision matches the rubric, journal-selection tiers by rank not by matching score, Beall's List replaced by Think.Check.Submit/DOAJ/COPE, PROSPERO wording per PRISMA 2020 item 24a.

### Fixed — scripts that did not run as documented
- statistical-analysis and figure-generation examples used `sys.path.insert(0, 'scripts')` (fails from a project directory); all script calls are now `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/…`, checked by the guard.
- export_docx.py: `encoding="utf-8"` everywhere (crashed on GBK Windows); unpaired `~ ^ *` are kept verbatim (were silently deleted — "~90%" became "90%"); journal family read from YAML (Nature/Lancet/JAMA order and Key Points / Research in Context now work for all 234 journals, not 19); word count split into body / abstract / references; unknown journal id exits 2; placeholders inside HTML comments detected; Heading 3 styled; literal reference numbering; `--supplementary` and `--report-only` implemented.
- pub_style.py: font fallback chain with a single warning, significance bracket height as a fraction of the axis, 600 dpi for line art, real per-journal figure widths (Nature verified; others approximate).
- power_analysis.py: `diagnostic()` takes specificity, `proportion()` returns both groups, clear `ValueError` on boundary inputs, friendly missing-dependency messages, argparse CLI.

### Implemented — mechanisms that existed only as prose
- **Project state**: `skills/using-med-research-powers/scripts/mrp_state.py` is the single writer of `.mrp-state.json`; every main-line skill ends with `mrp_state.py done <skill> --output … --next …`; hard checkpoints are recorded; the session-start hook reads only five whitelisted string fields.
- **User profile**: lazy, global; `journal-selection`, `data-analysis-planning` and `figure-generation` read one field each and ask a single question when it is missing.
- **Journal templates**: `skills/manuscript-writing/scripts/get_journal_template.py --id/--search/--list` (with project-level `journal-overrides.yaml`); whole-file reads of the 133 KB YAML are forbidden.
- **Pipeline**: research-ethics on the main line before data collection; peer-review before pre-submission; manuscript-export after pre-submission; journal-selection is a soft confirmation. **Three** hard checkpoints (protocol, SAP, pre-submission). Default confirmation mode is `light` (summary + auto-continue); `step` and `auto` are opt-in. The "1% Rule" is gone: pipeline for research-process tasks, direct answers for small questions.
- study-design split into a 184-line router plus `references/modules/{clinical,basic-science,ai-ml,qualitative,survey-delphi}.md`; Type B and C protocol templates added (C includes patient-level split, ground truth, calibration/DCA, prompt standardisation); Type A template now has intervention/comparator, randomisation, blinding, outcomes and follow-up sections.
- literature-synthesis: Narrative vs Systematic mode; bias tools mapped by design (RoB 2 / ROBINS-I / NOS / QUADAS-2 / PROBAST); templates moved to `references/`.
- New scripts: `data_cleaning.py`, `patient_level_split.py`, `randomization.py`, `get_journal_template.py`, `mrp_state.py` (10 bundled scripts in total).
- **21 of 47 standards now ship with a per-item checklist YAML transcribed from the source paper** (never from memory): CONSORT 2025, CONSORT-AI, SPIRIT 2025, SPIRIT-AI, TIDieR, TREND, RECORD, STROBE, PRISMA 2020, PRISMA-ScR, STARD 2015, TRIPOD 2015, TRIPOD+AI 2024, CLAIM 2024, DECIDE-AI, ARRIVE 2.0, CHERRIES, CROSS 2021, CARE 2013, SQUIRE 2.0, CHEERS 2022. Each file names author/journal/DOI/PMCID and marks `critical` items for Gate 1; the index says explicitly which standards have no local file and forbids inventing items for them. A `tripod-2015` index entry was added (47 standards).

### Hook
- Rewritten: a two-line reminder plus, when `$CLAUDE_PROJECT_DIR/.mrp-state.json` exists, five whitelisted fields in a fenced block labelled as data. No routing table, no questionnaire, no `python3` probe, no whole-file `cat` (that allowed prompt injection from a cloned repository). See `SECURITY.md`.

### Tooling and CI
- `tools/check_consistency.py` rewritten: versions in 8 places, on-disk counts vs every number claimed in docs, plugin name vs command prefix, no command/skill name clashes, script paths must use `${CLAUDE_PLUGIN_ROOT}` and exist, SKILL.md frontmatter/length/reference-path checks, README ↔ README_CN structure sync, dead relative links, stale CONSORT counts.
- `tests/` (pytest, 100 tests) covering all bundled scripts plus the structure of every reporting-standard checklist and the index; CI runs the guard, tests, `sh -n`/shellcheck, a hook smoke test, a whitelist-leak test and `claude plugin validate --strict`.
- `evals/`: eight `claude plugin eval` cases (six routing cases — study-design, data-analysis-planning, pubmed-search, pre-submission-verification, journal-selection, revision-response — and two negative cases that must not start the pipeline), deterministic graders only; `.github/workflows/evals.yml` runs them on demand.
- `examples/ai-bladder-ct/`: a clearly synthetic example project (state file, research question, Type C protocol) showing what MRP artifacts look like.
- `.github/`: bug and skill-request issue templates, PR checklist, Dependabot for Actions.
- Docs: README/README_CN rewritten in sync; USER-MANUAL deduplicated against README; architecture.md aligned; 4 unreferenced images removed and the remaining one re-encoded (2.3 MB → 52 KB); `SECURITY.md`, `CONTRIBUTING.md` release checklist, `.gitignore` additions.

### Known limitations
- Impact factors for the ~200 less frequently targeted journals are still JCR 2022 values (no `IF_year` field); NEJM, the JAMA family, Wiley titles (BJU International, Neurourology and Urodynamics, The Prostate, International Journal of Urology), JCO and Cancer Research could not be verified because their sites block automated access — skills therefore always state the year and re-check the top candidates on the web. Missing journals can be added locally via `journal-overrides.yaml`.
- 26 of 47 standards have index entries with official sources but no local per-item checklist; COREQ and SRQR are paywalled and were deliberately not transcribed from memory.

---

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
