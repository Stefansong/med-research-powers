# Changelog

## v6.4.1 (2026-09-24)

Fix release after a repository-wide audit of 6.4 (7 parallel reviews, each verified by an independent reviewer; every finding below was reproduced or checked against its source), in two rounds: the findings that gave wrong results or leaked data first, then every remaining finding. No new skills; several script CLIs gain options (listed below).

### Security and privacy
- `hooks/session-start.sh` printed `.mrp-state.json` values with dash `echo`, which interprets `\n` / `\c`: a crafted state file in a cloned repository could put a line **outside** the "data, not instructions" fence. Values are now printed with `printf %s`, control characters and backticks are dropped, and the 160-byte cut never splits a UTF-8 character. After a mid-task compaction Claude is told to continue instead of stopping to report the project state.
- `data_profile.py` printed identifier values whenever the column name was not on its fixed list (e.g. every patient name in a column called `患者`, a pathology-number range, dates of birth), and a headerless CSV turned the first patient's ID-card and phone numbers into column names. Identifiers are now also found by value (one value per patient, almost all different) and date of birth is always an identifier — their values are never printed; a first row that looks like data is not used as a header (`--header` / `--no-header` / `--skip-rows`). Privacy columns keep their quality checks; `drug_name`, `mRNA`, `Unnamed: 3` are no longer taken for names.

### Results that were silently wrong
- `data_profile.py`: a binary outcome coded `1.0/0.0` (any float export with a missing value) crashed `--outcome`; events were counted per row, so 6 patients with 3 rows each showed 18 events — now also per patient, the number that limits predictors. `未检测 / 暂无 / 不适用 / 待查 …` were not recognised as missing; `无` in a numeric column (transfusion volume) was always counted as missing — now kept and listed for confirmation; grouped ranges (`<60 / ≥60`) were reported as detection-limit values; `hospital_stay`, `tumor_site`, `中心静脉置管` were taken for centres and triggered GEE advice. Also: full-width digits, unmatched quotes (swallowed the rest of the file), trailing blank rows, month-first dates, strict JSON, symlinked report path.
- `patient_level_split.py`: per-stratum floor cuts sent strata of one patient to the test set (a continuous label gave `{test: 200}`), gave 21/5/4 for 0.7/0.2/0.1 of 30, and put every k-fold remainder in the last fold; missing labels crashed or left rows unassigned while the leakage check passed. Split sizes now follow the fractions exactly and every stratum is spread proportionally; missing labels form their own stratum; `--kfold 0` is an error; an existing `split` column is not overwritten.
- `power_analysis.proportion()` sized with Cohen's h, which under-sizes rare or extreme proportions (0.01 vs 0.05: 250 instead of 285 per group). It now uses the pooled-variance formula (Fleiss; the same n as R's `power.prop.test`), with `--continuity-correction`; NaN / infinite inputs are rejected.
- `randomization.py` defaulted to the public seed 42 and told users to write the seed and block sizes into `study-protocol.md`, which defeats allocation concealment. Without `--seed` an unpredictable seed is drawn (`secrets`) and kept only in the concealed summary; strata use independent random streams (seed + i made stratum 2 of seed 42 equal stratum 1 of seed 43); block lists end on a whole block when n allows.
- `assumption_tests.py` chose Student / Welch / Mann-Whitney from Levene and normality p-values. It now reports those tests as diagnostics only, recommends the design default (Welch; Welch ANOVA + Games-Howell) and names the rank-based alternative for use only when the SAP prespecifies it.
- `reproduce_check.py` accepted outputs outside `--cwd` and left a path empty when an output was never produced; `export_docx.py` read "8 pages" as an 8-word limit and "150-250 words" as 150.
- `export_docx.py` parsed Markdown line by line: soft-wrapped paragraphs split, code fences were read as headings, `####` and `---` were written literally, nested lists were flattened, table alignment rows became data rows, `\|` split cells and extra cells were dropped, nested emphasis and links stayed literal. It now has a block parser (fences, headings 1–6, rules, quotes, tables with alignment, nested lists, paragraphs; CJK soft wraps joined without a space) and a CommonMark-style inline pass (nested emphasis, `_x_` with word boundaries, code, real hyperlinks). Pandoc citation keys and extra table cells are listed in a new "Conversion notes" report section; full-width 【待补…】 placeholders are caught; a malformed overrides file gives one error line and exit 2.
- `reproduce_check.py`: a re-check no longer fails when the command names an output path; Ctrl-C / SIGTERM stop the whole analysis and put earlier outputs back; whole numbers must match exactly (default rtol 1e-12); xlsx formulas, SVG and `.gz` compared by content; differing screen output and run dates in outputs are flagged; `--exclude`, `--keep-last`; `.reproduce-check/` is git-ignored.
- `data_profile.py` (second round): `--not-id` for all-different measurements typed as IDs; only the patient ID groups rows (an `arm_id` never feeds event or cluster summaries); cp1252 mojibake flagged and UTF-16 read; line breaks in column names shown safely; "complete rows" ignores ID, privacy, remarks and empty columns; clear errors instead of tracebacks.
- `pub_style.py` cropped figures with `bbox_inches='tight'` (an 89 mm column came out 84.8 mm): figures are now saved at the exact journal width, TIFFs are RGB + LZW, significance brackets scale on log axes, and a missing p-value raises instead of printing "ns".
- Smaller: `get_journal_template.py --id` is case-insensitive and a malformed overrides file or missing `--yaml` gives one error line (exit 2); `mrp_state.py` honours `CLAUDE_CONFIG_DIR`, strips list values and explains a state file that is not a JSON object; `install.sh` no longer advertises `curl … | bash`.

### Methodology
- Decision tree and method cards agree: Welch by default, no Shapiro-Wilk/Levene pre-test route; rank-based tests chosen in the SAP on design grounds. Cochran-Armitage correctly described for 2×K tables; proportional-odds regression added. Batch effects modelled as a covariate (ComBat / `removeBatchEffect` for visualisation only).
- Calibration intercept (calibration-in-the-large), slope and a flexible curve are the primary calibration measures everywhere (ECE/MCE secondary); caveats on NRI/IDI and on SMOTE/oversampling; time-to-event calibration and decision curves for prognostic models.
- Method-card recipes that gave wrong answers fixed: the Python calibration intercept (it computed the joint recalibration intercept), a rank-deficient patsy spline, sklearn L1 without standardisation; penalised regression is no longer presented as a cure for too few events; no global `na_values` with `999`. Binomial-GLMM DTA meta-analysis, AI-versus-reader-panel MRMC guidance, PROBAST+AI, QUADAS-C, CHART and STARD-AI (Nat Med 2025) added, each checked on PubMed.
- Study design: the Type C protocol template has a sample-size section (Riley/pmsampsize, Buderer, MRMC); the protocol states the randomisation method, not the seed or block sizes (SPIRIT 2025 item 21b); explainability no longer attributed to DECIDE-AI; optional-stopping advice removed. Human genetic resources are administered by 国家卫生健康委员会 since 2024-05-01. Gate 2 multiplicity follows the SAP; calibration and error-rate parity replace demographic parity.
- Second round of method-card fixes: bootstrap variance for weighted Cox, PS fitted after SAP approval, MI + PS within each imputed set; GEE small-cluster corrections with t tests on K−p df; design effect for unequal clusters; ad hoc HKSJ; cluster-adjusted McNemar and reader-study washout; kappa chosen by rater design, Dice + a boundary metric; LLM-judge bias controls; missingness-vs-outcome checks only after SAP approval.
- Standards index: STROCSS 2024, AGREE II dated 2010, MI-CLAIM and COSMIN 2.0 item counts corrected, IDEAL Pre-IDEAL stage added; bias/appraisal tools labelled with `type:` (still 47 entries, not used for the Gate 1 reporting check).
- Example project: illustrative numbers labelled, external test set justified with Buderer, 6-reader MRMC design instead of two-reader DeLong, STARD mapping redone from the local checklist, 60/20/20 split.

### Workflow
- Missing prerequisites no longer block: Claude says what is missing and why, offers to create it or to continue with the gap recorded, and follows the user's choice. The three hard checkpoints stay.
- Existing retrospective data take a quick SAP path and go straight to `statistical-analysis`; `data-collection-tools` is only for data still to be collected. Light mode no longer waits for tool-list approval; auto mode records `confirmed_by: auto`; a request for one artifact (a section, a figure, a SAP) stops after delivering it.
- `figure-generation`: restyling an existing figure needs no SAP; outcome-by-group plots before the SAP only as labelled exploratory work.
- Trigger words tightened ("写完了", "docx", "注册", "帮我算" …); English triggers added; conducting a systematic review routes to `literature-synthesis`, not `manuscript-writing`.
- The orchestrator now calls the target skill before any file check (an empty project directory used to make it stop and ask for files instead of routing — found by the new `route-manuscript-writing` eval); missing inputs are handled by the called skill.
- `statistical-analysis` writes every result and the patient flow to `results/` files, and the reproducibility gate compares screen output too; outcome-derived and post-baseline variables are excluded from pre-SAP redundancy checks and from candidate predictors; `journal-selection` no longer ties the tier to the design label (a retrospective study can reach Q1).
- Context: the orchestrator is back under 250 lines (backtracking table moved to `references/backtracking.md`); the outcome-blind rule is stated once and referenced elsewhere; repeated profile, checkpoint and state boilerplate replaced by one-line references.

### Data and evals
- Journal data: all JAMA-family journals and Circulation / Circulation Research on eJournalPress (were ScholarOne); NEJM on ScholarOne in `submission-systems.yaml` (JAMA and NEJM were swapped); Modern Pathology and Laboratory Investigation published by Elsevier; Blood published by Elsevier for ASH. 70 journals re-checked against their author guidelines (new `guidelines_checked` / `guidelines_source` fields): limits corrected for Nature, Nature Medicine, NEJM, Lancet, JCO, BJU International, Journal of Urology, Circulation, Blood, ARD, Cancer Cell and others; 21 impact factors refreshed with year and source (63 entries now carry `IF_year`); citation style added to 38 more entries. Most publisher sites were unreachable from the review environment, so these values come from search snippets on the journals' official domains; 170 entries were not re-checked, and values that could not be verified carry a 待核实 note. `submission-systems.yaml` gains a `data_as_of` line.
- Evals: 27 cases (was 9) — a routing case for every one of the 20 skills and 4 over-trigger negatives ("写完了" about a year-end report, splitting a restaurant bill, registering a 12306 account, converting meeting notes to .docx); all 26 routing and negative cases passed in a 1-run check. The negative graders also catch an MRP skill invoked without the `mrp:` prefix. `data-first-planning`: numbers corrected (400 patients, 668 rows, 23 patient-level events), its judge no longer rewards skipping prerequisites, and a new grader checks that `data_profile.py` actually ran (needs `--scaffold --allow-tools "Bash(python3 *)"` and the OS sandbox; not yet confirmed passing). The manual eval workflow runs routing + negative by default and adds the scaffold, Bash grant and sandbox packages only for the `behavior` tag.
- Tests: 362 (was 116), incl. `tests/test_mrp_state.py`.

---

## v6.4.0 (2026-09-23)

**Analyse first, then plan, then decide, then execute.** Wherever the work depends on real data or real needs, MRP no longer applies a template or a canned script: Claude first examines the actual situation, then tailors the plan, the user decides, and only then is code or content written — followed by a self-check.

### The rule, and its methodological boundary
- Before the analysis plan is confirmed, Claude **may and must** look at the data's structure and quality (variables, coding, disguised missing values, censored strings, event totals, repeated records per patient, cluster sizes), but **must not** look at associations with the outcome (including exposure/group versus outcome) — outcome-blind redundancy checks among predictors are fine — otherwise "look at the data first" would become choosing methods after seeing results. This boundary is written into the orchestrator, both analysis skills, every method card and the skill-authoring guide.
- Templates (protocol sections, SAP sections, figure types, tool catalogue, article structures) are now **must-cover checklists**, not fill-in forms: write what fits this study, mark the rest "not applicable + reason", never copy example numbers.
- `scripts/` keeps only tools and guard-rails — formulas that are easy to get silently wrong (sample size), checks against study-breaking errors (patient-level split, randomization), infrastructure (state, journal lookup, export) and read-only checkers. Analysis code is written for each dataset.

### Analysis skills rewritten
- `data-analysis-planning`: new Step 1 "data situation" — for existing data, the read-only `data_profile.py` plus ad-hoc read-only checks; for prospective studies, the protocol/CRF and a contingency plan for when the data differ. SAP §1 is now "data situation and the choices it drives" (e.g. events → number of predictors; several stones per patient → GEE/mixed model). Methods are chosen with the decision tree plus the method cards.
- `statistical-analysis`: re-profiles the data against SAP §1 (minor mismatches logged; mismatches that affect the primary analysis go back to the user), writes cleaning and analysis code for this dataset in the user's language (R or Python) with every block tagged to its SAP item, then a mandatory **self-check**: re-run from scratch (`reproduce_check.py`), patient counts that connect step by step, a SAP → code → result table, and every deviation logged with its impact.
- **Ten method cards** (`skills/data-analysis-planning/references/method-cards/`): baseline & group comparison, regression & clinical prediction models (nomograms), survival analysis, propensity scores, missing data, diagnostic accuracy & AI evaluation, clustered & repeated data, meta-analysis, agreement & reliability, LLM/VLM evaluation. Each gives what to check in the data before planning, what the plan must prespecify, vetted R/Python packages (every package and function checked against CRAN/PyPI), common pitfalls, required reporting items and the matching reporting guideline, with DOI-referenced sources. They are rules to follow, not code to paste.

### Other skills
- `study-design`: new Step 0 "real conditions" (case sources, expected events, centres, follow-up, resources, ethics) that drive the design; sample-size parameters must cite a real source; protocol templates, modules and experiment templates no longer contain numbers that invite copying.
- `data-collection-tools`: first analyses where the data really come from (HIS/EMR, PACS, LIS, video system, paper CRF — export formats, field names, who records what), then proposes a tool list with reasons for the user to confirm; the tool catalogue is optional, not a set to generate in full.
- `figure-generation`: a `figure-plan.md` (what question each figure answers, chart type, main text vs supplement, journal limits) comes before drawing; figure code is written for the data, `pub_style.py` only handles journal styling.
- `manuscript-writing`: a `manuscript-outline.md` maps every point to a project artifact before drafting; every number in Results must trace to an analysis output; SAP deviations must appear in Methods or Limitations.
- Orchestrator: states the rule; routes by invoking the target skill with the Skill tool (not by acting on the one-line routing summary); looks for inputs only inside the project directory and asks when they are missing; skills pause outside hard checkpoints only to collect information only the user has.

### Scripts (still 10)
- Removed `analysis_template.py` (the coding rules now live in `statistical-analysis/SKILL.md`).
- `data_cleaning.py` → **`data_profile.py`**: a read-only check-up for CSV/TSV/XLSX (UTF-8/GBK/GB18030): disguised missing values ("未查", "/", 999 …, context-aware so a "无" category is not miscounted), censored strings ("<0.1"), numbers stored as text, unparseable dates, repeated patient IDs and cluster sizes, outcome distribution and event totals only (never associations), possible identifier columns reported by name and count only. Never writes to the data.
- New **`reproduce_check.py`**: runs an analysis command twice in fresh processes and compares every output (tables cell by cell with tolerances, JSON by value, text numbers with tolerance); exit 0 identical / 1 different / 2 failed; earlier outputs are moved aside, never deleted.
- `export_docx.py`: `[待补…]` placeholders are now detected.

### Evals and tooling
- New behaviour eval `evals/data-first-planning` (scaffolded messy data; the plan must be built from its features): 2/2 runs passed all graders (with the 6.4.0 graders; the case was reworked in 6.4.1). Routing smoke cases re-run after the orchestrator change: pre-submission 3/3, the others passed.
- Guard: section numbers in cited guidance ("§10.10.4.4") are no longer mistaken for stray versions. Tests: 116 (new: data profile, reproduce check; plus the v6.3.1 session-hook tests).

---

## v6.3.1 (2026-09-22)

Patch release: the SessionStart hook could not read a state file that was not indented, and CI was carrying a guard that failed silently. No skill content changed.

### Fixed
- `hooks/session-start.sh` read the whitelisted fields of `.mrp-state.json` with a line-anchored `sed`, so it silently reported nothing when the state file was not indented one field per line (a single-line or hand-edited file). The key is now matched anywhere on a line; the indented files `mrp_state.py` writes behave exactly as before. New `tests/test_session_start_hook.py` pins the contract across indented, single-line and CRLF state files, including the rule that non-whitelisted fields never reach the context.

### Changed
- CI: the `Hook smoke test (crafted .mrp-state.json)` step is no longer `continue-on-error`. It was passing silently with `exit 1` and a warning because of the parsing bug above; now that the hook is format-agnostic the guard actually enforces SECURITY.md's contract, and its annotations are errors rather than warnings.
- CI: bumped `actions/checkout` v4 → v7, `actions/setup-python` v5 → v7, `actions/setup-node` v4 → v7 and `actions/upload-artifact` v4 → v7, off the deprecated Node 20 runtime. None of the breaking changes in those majors apply here (no `pull_request_target`/`workflow_run` triggers, no `pip-install` input, no implicit non-npm caching, unchanged `upload-artifact` inputs).

---

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
