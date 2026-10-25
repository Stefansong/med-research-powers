# Changelog

## v6.5.0 (2026-10-25)

Fix release after a scored audit of 6.4.2 that found **22 major and about 130 minor problems**. The audit covered 12 dimensions, and every finding was adversarially verified. The problems were fixed in several rounds. Each round was followed by an independent adversarial verification that re-ran the reproductions, and what it still found open went into the next round. The `data_profile.py` privacy rules went through five such rounds. What is still open is listed under Known limitations. There are no new skills (still 20 skills, 7 commands and 240 journal entries), and the standards index grows to 54 entries. Several script CLIs gain options, and a few old invocations now stop with an error or give a different result (see Upgrading).

### Security and privacy
- `mrp_state.py` followed symlinks planted in a project: `.mrp-state.json.tmp` could overwrite any user file, and `.mrp-state.json` could read and copy any JSON file. A state file, `.tmp` file, profile or `journal-overrides.yaml` that is a symlink or not a regular file is now refused (exit 2, nothing written), and writes go through a newly created temp file. `show` / `show --json`, which the orchestrator runs at session start, printed every field unsanitised, bypassing the hook's whitelist. They now print only the schema's fields, as labelled data cleaned like the hook's, limited to the newest entries and 32 KB; a planted `_notice` key can no longer replace the label.
- `hooks/session-start.sh` let several things through: Unicode line/paragraph separators, NEL, bidi overrides, zero-width and tag characters, and a spoofed `<mrp-session-start>` tag. In a UTF-8 locale, an invalid byte could pull text from other fields into a value, and the hook followed symlinks with no size cap or timeout. It now drops C1 controls, `<` `>` and all format (Cf) and default-ignorable characters, never shows a value that is not valid UTF-8, parses byte by byte (`LC_ALL=C`), refuses a symlinked or non-regular state file, reads at most 64 KiB and has a 10 s `timeout` in `plugin.json`; it is tested under dash and bash.
- `data_profile.py` printed patient identifiers into the report that the skills read into the conversation (see its own section below).
- `reproduce_check.py --keep-last`, which the skill recommends, permanently deleted user files that an earlier check had moved aside and never put back. With `--keep-dir`, it also deleted user folders that merely looked like old checks. Moved files are now put back unless a run wrote them again. Each check folder records a sha256 manifest of its run, log and moved-aside copies in its status file, which is written atomically. A folder is pruned only when it has that status file and every file in it is either an earlier check's output that still matches the manifest or has an identical copy, compared by content, in place or in a kept check. A copy edited or added after the check, or a hand-edited version, keeps its folder; a check that was interrupted or could not record its manifest prunes nothing. The report says why a folder was kept and where the other copies of a version are.
- Allocation concealment: the documented RCT workflow wrote the randomisation list and its seed into the project's shared `tools/` folder, and a re-run silently overwrote the list and the only record of its seed. `randomization.py` now requires `--out` and refuses a path inside the project folder. It never overwrites an existing list or summary without `--force`, writes both files owner-only, and prints a concealment reminder. `data-collection-tools` no longer puts the list, the summary or the run command in `tools/`.
- `export_docx.py` could overwrite its own Markdown inputs or unrelated files through `--report`, `--supplementary` or `--output`; these are now refused. AI-benchmark inference scripts sent patient inputs to external model APIs with no check. They now do so only when every condition of the research-ethics rule on external AI services holds; by default only anonymised data are sent.
- SECURITY.md said the state files are git-ignored, which is true only in the plugin's own repository. It now tells you to add `/.mrp-state.json` to your project's `.gitignore`. The bug-report template warns not to paste patient data, identifiers or data values quoted in errors. In the eval workflow, the API key is given only to the eval step, and results are uploaded only on request.

### Results that were silently wrong
- `export_docx.py` Gate 6 limits were wrong in four ways: Nature's body limit was read as 6 words; IEEE TMI / JBHI page limits were read as 10-word limits; Methods were counted for Nature Medicine and Cancer Cell, whose limits exclude them; figure, reference and display-item checks gave ✅ for things never counted. Limits now come from the entry's structured `limits` block (see Journal data). Entries without one are read conservatively: ranges, minimums, "no fixed maximum" and page limits give "check manually", never a guessed number; in an override without a `limits` block, a "no limit" phrase applies only to its own subject and article type. The checks now count legends written as `**Figure 1.**`, `Fig. 1 |`, `## Figure 1` or `图1`; the highest figure or table number cited in the text, also in lists ("Figures 6 and 7", `图6、7`) and lower-case house styles ("(figure 7)"); `[1]` / `(1)` / bulleted reference lists; and combined display items. A Chinese number followed by a unit or measure word (`调查表300份`, `心电图24 h`) or a compound such as 心电图 or 调查表 is not counted as a figure or table citation. A count that cannot be determined, or may be too low, shows ❓, never ✅.
- `export_docx.py` turned range tildes into subscripts and merged the numbers (`18~65岁，体重50~80kg` → `1865岁，体重5080kg`). A tilde between digits now stays a tilde, and interpreted subscripts are listed. Also fixed: a whole CJK paragraph counted as one word (CJK characters are now counted one by one); legends inside body files counted toward the body limit; a UTF-8 BOM, multi-line placeholder comments and bare TODO / TBD / 待补 / [ref] slipped through; footnotes, inline HTML and `$math$` were written literally without a note; review `section-N-*.md` files were not exported; `figure-legends.md` was written to the project root but read only from `manuscript/` (both are read now, and the report names the file used); Key Points / Research in Context files with only `##` headings lost their title.
- `reproduce_check.py` gave wrong results in several cases: background processes left by a run wrote into the next run's outputs; identical DOCX / PPTX files were always "different"; symlinked directories inside outputs were followed; `--exclude` matched more than a shell glob; `.Rout` / `.smcl` / `.jsonl` outputs were compared by hash only; zero-padded IDs were compared as numbers (`007` = `07`), and the tolerance hid epoch timestamps; crashes exited 1 (the "differ" code) with no report. Caches outside `--outputs` that predate the check are flagged by name. The report no longer claims the runs started from scratch, because only `--outputs` is emptied. New `--compare-stderr`.
- `power_analysis.py`: `survival()` folded dropout into `n_total` and applied the default 10% silently. It now gives `total` before dropout and `total_adjusted` after (HR 0.7: 494 → 550; was a single 549), and states the default. `diagnostic()` rounded up twice (Se 0.9, prevalence 0.3: 461, was 464). It now warns when Se/Sp ± precision leaves [0, 1], with `--ci-method wilson`. Power ≤ alpha, and a design that needs more than 10⁹ per group, now give one line instead of nonsense n, a 300-digit n or a traceback; the power at 10⁹ is checked before refusing, so a design that needs just under it is still sized. Very large Cohen's d values are sized at ≥ 2 per group with a warning, instead of being refused.
- `assumption_tests.py`: per-group "Parametric / Non-parametric" verdicts contradicted the Welch default and are removed. Repeated measures defaulted to a Mauchly-gated Greenhouse-Geisser correction. The default is now a mixed model or GG-corrected RM-ANOVA, with Mauchly reported descriptively. Mauchly's p now has the second-order term, as in R and pingouin (7 subjects × 6 conditions: 0.491, was 0.409). Data containing inf were reported as normal. Rows with a missing group or subject ID were dropped silently; they are now counted in `rows_excluded`.
- `patient_level_split.py`: `0012` and `12` were merged into one patient. ID variants (trailing space, case, full-width forms) counted as different patients, so one patient could sit in two splits while the leakage check passed. IDs are now text, grouped after NFKC / trim / case folding, and the variants are listed. A continuous label, or strata of one patient, gave essentially the same split for every seed. `NA` / `null` values were emptied in the outputs. The "file may be cp1252" warning false-alarmed on GBK names (张喆), and its `latin-1` advice merged distinct IDs (李1 / 囝1). It now never suggests an encoding that merges patients. Outputs are written all-or-nothing, with new `--encoding` / `--output-encoding` options; a failed write removes the output folder it created, and a variants file left from an earlier run is named. A console that cannot print Chinese no longer makes it crash after writing.
- `randomization.py`: `--strata` without `--method stratified`, repeated factors and an empty `--ratio` / `--block-sizes` were silently ignored; they are now errors. Adding a centre or reordering factors changed existing strata's lists. Streams are now keyed by each stratum's factor=level pairs. The summary now records the seed as text, the package versions, the script's sha256 and the regenerate command.
- `pub_style.py` gave generic widths and matplotlib's default palette to every journal except 5 flagships. All Nature-, Lancet- and JAMA-family journals (by id or full name) now get their family's widths, and other journals get the Okabe-Ito palette. Figures from `save_figure` always failed `reproduce_check`; PDF / SVG / SVGZ / EPS output is now byte-reproducible, with per-format `metadata=` (kept in SVGZ too). `pgf` output without a TeX installation is refused before anything is written. Format names are case-insensitive: `'TIFF'` used to skip the RGB / LZW writer.
- `mrp_state.py`: `target_journal` was documented as a journal name, but every consumer needs the library id. `set target_journal=` now resolves names to ids and refuses unknown journals. `done` failed without a state file, which is now created on first use; a state file first created by `done`, `set`, `checkpoint` or `note` has no `next_step` (only `init` sets one). Wrong-typed fields, non-UTF-8 files, deeply nested JSON, >4300-digit integers and lone surrogates gave tracebacks; they now give one line and exit 2 and leave no `.tmp` file. Usage errors are one line too, and a console that cannot print Chinese no longer makes it crash after writing.
- Every script CLI reports errors as one line on stderr with exit 2, instead of a traceback or mixed exit codes.

### data_profile.py

The check-up report is the only view of the data that the skills read into the conversation. 6.4.2 printed up to 15 levels of every category column, so names, record numbers, addresses and notes that its patterns missed went into the report (a column of doctors' names, a note naming a patient's relative), and so did a record or phone number typed into a numeric column in a form the phone pattern missed (`2345678`, `1.38001E+10`, `13,800,131,005`, shown as the maximum or an example) and every sheet name. The privacy rules below went through five fix rounds, each followed by independent adversarial verification. Pattern checks cannot promise more than this, so see Known limitations.

- **Patient unit.** Category levels, spelling variants, words in a number column and notes in a date cell are printed only when the script can tell patients apart: `--id <patient-ID column>`, or the new `--rows-are-patients` for one row per patient without an ID column. Without a patient unit, no category values are printed. Only the number of levels and the shares of the commonest and rarest one are shown, and one problem line says which flag to add, naming a probable ID column when there is one. Nothing makes "rows are patients" automatic. **Always pass `--id`**, or `--rows-are-patients`.
- **Automatic patient key (best effort).** For convenience the script still picks a patient ID by itself when exactly one column qualifies. The rule looks only at the column's name and its set of values, never at how many rows each value has. The name must clearly name the patient (patient_id, pid, subject_id, case_id, 患者编号, 住院号, 病案号, MRN, Hospital Number …) and hold no visit, time or sample word (visit, FU, day, week, POD, sample, 随访, 第, 次, 天, 入院 …). The values must repeat, with at least 10 different ones, and must not be visit, ordinal or sample labels (第1次, 随访一, V1, visit_1, FU1, D1, POD1, wk4, Session 4, 标本5, baseline, Roman I–XII, single letters, whole numbers from 0). The report header names the column it used and says to pass `--id` if that column numbers visits. When two columns qualify, neither is used, and one line names both. Per-row numbers (序号, No., visit_id, encounter, 检验号), a record number recognised only by its values and a name-like category (cities, eponyms) are never the key. A bare 1..k visit index under a patient-ID name cannot be told apart from patients numbered 1..N, and is used as the key.
- **Small cells.** With a patient unit, a text value is printed only when at least 5 patients hold it (each key value counts as one patient) and it is not shaped like an identifier. Identifier shapes include a personal name, a name in another script than the column's other values, a record number among values that are none, an address, and 7+ digits with any separator. The other values are counted ("另有 N 个低频取值未显示"), so in small pilot tables most levels are counted, not listed. Outcome levels follow the same rule, except plain codes (0/1, 是/否, 死亡/存活, CR/PR …). Masked levels keep their counts, so event counts are unchanged. Units, lab flags and example cells are printed when they are on a fixed list of known units and flags; others only with a patient unit and 5+ patients.
- **Long numbers.** A whole number of 7+ digits is never printed, however it is written (`13800131005`, `13800131005.00`, `1.38001E+10`, `13,800,131,005`). The statistics it could show read "不显示": min / max, percentiles, mean ± SD, examples and levels, also for `--time` and a numeric outcome. The problem list names the column. Viral loads or costs of a million or more therefore lose their maximum in the report, by design.
- **File, sheet and column names.** The file name and the chosen sheet name are printed only when they are made of ordinary words. The other sheet names are never printed, also not in the `--sheet` error. A column name that holds a person ("患者张三", "Dr. Smith", "Mary Smith CT", "Smith, Mary CT", "王一二左眼"), a record code or 7+ digits is replaced by its position (列4), and the problem list says why. Clinical words, eponym scales and terms (Child Pugh, Kaplan Meier, Gail Model, 王氏评分) and item, visit and date codes (SF36_01, V01_01, Hb_20230101) keep their names. A title row above the header (one or two cells, or a short line such as "患者：张三" or "XX医院") is never used as column names, and the problem list gives the `--skip-rows N` to use. Transposed tables (patients as columns, also named by their record numbers) get positional names and a note.
- **More identifier columns.** Dates of birth are recognised under headers in 20+ languages (bdate, DtNasc, fecha_nac, date de naissance, data di nascita, 生辰, 생년월일, дата рождения …), also written with spaces or full-width letters. So is any date column spanning 40+ years with most dates 30+ years back. A date column whose name names no event (d1, date1) shows an end lying 18+ years back as its year only. Also recognised: names (masked "张*", pinyin "ZHANG Wei", Tibetan, Japanese, Korean, accented Western), addresses that start with the house number or have no city, phone and ID-card numbers with spaces, hyphens or a country code, WeChat / QQ ids, a person named inside free text ("患者刘洋拒绝随访") and names under person-role headers (术者, 主治, surgeon). Birth weight, order and place are no longer dates of birth, and contact-named measurements (电话随访次数, 联系人数, phone_use_hours) keep their values.
- **Encodings.** A GBK file whose Chinese text is 男 / 女 is valid EUC-KR too, and could be read as Korean. Bytes that are valid GBK / GB18030 are now read as Chinese (Big5 when that reading is clearly more of a text, with a note). When the Korean or Japanese reading is clearly the text, a warning names `--encoding euc-kr`, `cp932` or `euc-jp`. No cell text is printed until the encoding is given, also when an explicit `--encoding` reads clearly worse. Only bytes that are not valid GB18030 are read as EUC-KR, Shift-JIS or EUC-JP. A UTF-8 file with one stray byte stays UTF-8 with a line-numbered warning, and a cp1252 file whose µ or ü appear only in values is flagged.
- **Censored values, units and flags.** A detection limit is one open end next to measured values, however many results fall below it, so `<0.1` stays censored. Groups that cover both sides of a cut point (`<60 / ≥60`, `0 / <20 / ≥20`, `≤6 / 7 / ≥8`, `≤2cm / 2-5cm / >5cm`) are categories. A lab censored at both ends (`<0.01 / 0.15 / >50`, also with a unit on every value) stays numeric. Units are read by their parts, and each unit is counted once whatever its spelling (×10⁹/L, x10^9/L, 10*9/L; IU/ml and IU/mL). ×10^n multipliers are applied (`5.29×10^5 IU/mL`). Lab flags before or after the number or the unit, in Chinese or as words (`5.6↑`, `H 9.6`, `9.6(偏高)`, `5.6 High`, `(危急值)`), are counted and stripped. Approximate values (`约500ml`, `500ml左右`, `12余年`, `approx. 5 mL`) are counted as written, with a problem line. Decimal commas and thousands separators before a unit (`5,4 mmol/L`, `12.345,67`) are read as numbers, and labels such as `阳性 16` or `约1次/周` stay categories. More missing spellings (未送检, 未采, 拒查, 不清楚, 未檢, 不詳) and censored spellings (`ND` in a lab column, BLQ, 低于检测下限) are recognised.
- **Layout, dates and IDs.** Two measurements in one cell (`120/80`, `120-80`, `3.5×2.1cm`, `3.5 cm x 2.1 cm`) get a hint to split them. Total rows (合计, Total:, 均值±标准差, a count such as "60人"), footer rows (注：…, 制表人：…) and a units row under the header are reported, because they would be counted as patients. New date spellings: `1/5/2022 0:00`, `2022-01-01T00:00:00Z`, `Jan-22`, `Wed Jan 16 2019`, yyyymmdd / yyyymm whole numbers (never IDs), and `19-01-16` read year first when the first part takes few values. Placeholder 1900-01-01 dates and time-of-day columns are reported, and one impossible yyyymmdd no longer turns a date column into text. A header word that recurs as a value (`复发` over 复发 / 未复发) stays a header. Stray quotes that merge lines into one cell are reported with their line numbers. Whole numbers that behave like record numbers are typed ID also in tables of 3–19 rows and in long tables, but no longer by chance ties in 50,000-row tables; round counts (213000) stay numeric.
- **Outcome.** Every column, the outcome too, is profiled the same way with and without `--outcome`, and the patient key is chosen without it. An `--outcome` that is the detected key stays the key, and the report says so. Spellings that differ only in case or spaces, and `1` / `1.0`, are one outcome value. 1/2 codes get per-patient counts per code, and a date outcome is reported as a date.
- **Options.** `--missing-tokens col=tok` applies a code to one column; an unknown column is an error. A number given for all columns is not applied in a 0/1 column, or inside or right next to a column's range (a 9 among scores 0–29, a 0 next to counts 1–3). The problem list says where it was and was not applied. `，` separates tokens, and negative values need no `=`. `--max-levels` must be at least 1 and never changes the outcome counts. A `--skip-rows` beyond the end of the file is a one-line error.
- **Speed.** Every pattern that reads raw cells is linear and length-capped. A 200,000-character cell takes about 0.5 s; it took over 10 minutes.

### New script options
- `export_docx.py`: `--article-type TYPE` checks that type's limits from `limits_by_type`. For a type the library has no limits for, the numeric checks are skipped and the report says so. `--journal generic` gives a journal-neutral export, so "convert to .docx" no longer has to ask for a journal. The .docx now has page numbers and continuous line numbers, which revision responses need (`--no-page-numbers` / `--no-line-numbers` turn them off). Unverified journal entries get a warning and ✅* instead of ✅, and the entry's 待核实 items head the report.
- `power_analysis.py` covered only two-sided superiority, although study-design pointed every sample size to it. It now sizes non-inferiority and equivalence designs (`--hypothesis`, `--margin`, `--lower-is-better`): two means with a shifted one-sided t-test and TOST with exact power, two proportions with the Farrington-Manning score test. The proportion designs warn when a group has fewer than 30 patients or fewer than 5 expected events or non-events, where the normal approximation is unreliable. Also new are `--sides 1` and a one-sided α that defaults to 0.025. `--help` says what is not covered: pmsampsize / pmvalsampsize, MRMC, multi-arm and group-sequential designs.
- `mrp_state.py note "<text>" [--skill <skill>]` records a note without marking a skill completed. An exploratory look before the SAP used to be recorded with `done`, which marked the skill completed. Notes are cleaned and capped at 480 bytes, and `show` prints the newest 5.
- `get_journal_template.py`: prints one warning line for an unverified entry, and one for the entry's 待核实 items; shows `checked` and `IF_year` columns; de-duplicates override ids case-insensitively.
- Also new: `data_profile.py --rows-are-patients` and `--missing-tokens col=tok`, `randomization.py --force`, `reproduce_check.py --compare-stderr`, `patient_level_split.py --encoding` / `--output-encoding`.

### Methodology
- Data split and validation for prediction models now follow one rule, shared by Type C, the AI/ML SAP extension and the decision tree. The method is chosen by model type and events per patient, not by total n: regression models are developed on all data with bootstrap optimism correction, with no random hold-out; tuned ML / DL uses nested CV, or a patient-level split only when every part has enough events; external or temporal validation is preferred, and required for generalisability claims; splits are by patient and stratified by outcome; penalised regression is no longer offered as the cure for too few events. The example project uses nested CV instead of a 60/20/20 split.
- LLM / VLM card: the repeated-run GLMM lacked the question × model random intercept, which inflates type I error. It is now `(1 | question_id) + (1 | question_id:model)`, with a per-question paired t-test / McNemar as the Python alternative. Run-to-run agreement uses Fleiss' kappa / Krippendorff's alpha.
- Decision tree and cards: no pre-test gating is left (paired differences, Pearson vs Spearman, Mauchly → GG); missing-data methods are chosen by mechanism and Hughes' complete-case rules, not a % grid; mediation uses counterfactual methods; the causal and survival branches match the cards (estimand, overlap weights, AIPW / TMLE, RMST, cause-specific vs Fine-Gray). Recipe fixes: L1 intercept back-transform, `pmvalsampsize` scoped to binary outcomes, HKSJ with k = 2, statsmodels DL τ² not truncated, and `mixedlm` z-tests flagged. New: a single-cell section (pseudobulk). The cards' Python recipes are now run in the tests.
- Study design: protocol template A has a slot for each SPIRIT 2025 item (53 rows); crossover trials have no two-stage carry-over pre-test; cluster design effects allow unequal cluster sizes; Delphi studies report with ACCORD; qPCR is analysed on the ΔCq scale with ≥ 2 reference genes (MIQE 2.0), and Western blots get linear-range checks and total-protein normalisation; animal studies define the experimental unit and cage effects (ARRIVE 2.0); surveys use a design effect for cluster sampling and COSMIN criteria.
- Research ethics (China): the checklist now covers PIPL health-data rules (sensitive personal information, separate consent, PIPIA, entrusted processing), cross-border transfer mechanisms with the 2024 thresholds, human-genetic-resources information and IIT filing (国家医学研究登记备案信息系统). De-identified data are not treated as anonymised. External AI services, the plugin's own chat included, get anonymised data or aggregates unless every listed condition holds. Consent-waiver conditions are cumulative, and exemption from review has preconditions. Items not verified against the official text are marked 待核实. Gate 5 accepts a documented exemption instead of an approval number and checks IIT filing; Gate 2 checks `reproduce-check.md`.
- Systematic reviews are honest about database access. Systematic mode used to treat WebSearch `site:` queries as database searches, list Embase / WoS / Scopus that no tool can search, and let one AI agent screen and extract. Now Claude searches only PubMed itself; Embase, Cochrane Library, WoS and Scopus are run by the user from a ready search string and imported, or reported as "Not searched"; WebSearch is supplementary only, and team-collaboration no longer sends one subagent per database; two independent reviewers are required, at least one of them human, with agreement and AI-tool use reported (PRISMA 2020 items 8/9); there is a GRADE step, ROBINS-E and PROBAST+AI are in use, and scoping reviews register on OSF, not PROSPERO.
- AI-use disclosure: the cover letter, submission metadata and response letter that the plugin drafts had no AI-use or preprint disclosure. The cover letter now declares both (ICMJE) and names the exact title and article type. Gate 3 requires the disclosure whatever the journal asks, revision-response updates it, and `submission-systems.yaml` lists the AI-assisted-technology fields.
- Surgical and device innovation was routed to the IDEAL framework, which the Gate 1 reporting check excludes. The IDEAL Reporting Guidelines (Bilbro 2021) are now the reporting standard, and the framework stays for staging.
- Standards index: **54 entries** (was 47). New: STARD-AI 2025 (primary for AI diagnostic accuracy), TARGET 2025 (target trial emulation), CHART 2025 (chatbot health advice), IDEAL Reporting Guidelines 2021, ACCORD 2024, ROBINS-E and PROBAST+AI. Every entry without a local checklist has a PubMed-checked reference. CONSORT-AI, RECORD and SPIRIT-AI are checked item by item. Metadata fixes: PRISMA-DTA, MOOSE, GRADE, TRIPOD 2015 and CONSORT-AI.
- p = 0.06: "不显著就是不显著" is replaced by estimate + CI. H0/H1 are required only for hypothesis-testing studies.

### Skills and evals
- Each skill names the orchestrator's core rules in one line with a pointer, so a skill invoked directly still applies them. The remaining prerequisite blocks are now warnings. "Only one artifact asked for → stop after delivering it" is stated in the skills.
- Fewer stops: "Table 1 from this CSV" took 2–3 forced stops and a full SAP. It now needs a short descriptive SAP confirmed once, and that SAP can be extended (checkpoint 2) before any outcome analysis. In light / auto mode, a missing prerequisite is recorded, not asked about. The quick path shows its questions and the SAP in one message.
- `figure-generation` has one rule for grouped outcome plots before the SAP: ask once, quick SAP or exploratory, and record the look with `mrp_state.py note`. Legends go to `manuscript/figure-legends.md`.
- Analysis changes, reviewer-requested analyses and resubmissions are now routed the same way by the backtracking table, revision-response, statistical-analysis, manuscript-writing, journal-selection and submission-preparation. Reviewer analyses are post hoc, not SAP deviations or amendments, also in the revision references (`revision-strategy.yaml`, `revision-templates.md`), the routing lines and the parallel revision scenario. Their definition is written down before they run, and they are reported in Methods labelled as post hoc.
- The data check-up commands in statistical-analysis and data-analysis-planning pass `--id` (or `--rows-are-patients`) and say what the report hides without it.
- Analysis and figure code copies the helper scripts into the project instead of importing from the plugin install path. research-question-formulation and pubmed-search work without the PubMed MCP (E-utilities via WebFetch).
- peer-review-simulation will not review a manuscript the user received as a reviewer without the editor's written permission.
- ⏳ Unverified is defined the same way in every skill (tool error, found only by web search, or not checked). English triggers added for figure-generation, data-collection-tools and writing-mrp-skills.
- Evals: **32 cases** (was 27): new `route-data-collection-inference`, `negative-p-value-threshold` and three behaviour cases with deterministic graders (KM before the SAP, Table 1 quick SAP, confidential peer review). Routing cases are documented as single-arm only; in a two-arm run, 4 scored 1.0 without the plugin. The `data-first-planning` graders check the script's per-patient count in the trace, the 23 patient-level events and the stop at the SAP checkpoint. The confidential-review grader fails a reply that simulates a review of the confidential manuscript in any form found so far: a reviewer label followed by comments on this manuscript, critique, a single decision or scores. It passes refusals that list the reviewer roles, give a generic outline or list the possible decisions. Its regex is generated by the new `tools/build_review_grader_regex.py` (a test keeps the two in sync) and checked on 85 simulated reviews and 95 refusals in Python and JavaScript. Because a regex cannot catch every free-form review, an LLM judge (`no-review-judge`, weight 2) backs it up. Behaviour runs use `--judge-model sonnet`.

### Journal data
- **Machine-readable limits.** Every entry (240) has a `limits` block for an original article, generated from the free text and reviewed by hand. Its keys are `body_words` + `body_excludes`, `abstract_words`, `references`, `figures` / `tables` or a combined `display_items`, `pages` and `soft`. Nothing is guessed. Ranges without a stated maximum, minimums, uncountable per-figure word rules and values a 待核实 item calls unstated are null. `limits_by_type` holds other article types where stated (systematic review: Lancet, BMJ, European Radiology, Abdominal Radiology; review and brief report: European Journal of Radiology). The review, systematic, scoping and mini-review guides no longer apply original-article limits; other types go into `journal-overrides.yaml`.
- **Unverified entries are flagged.** About 160 unchecked entries were served as authoritative limits with no warning; spot checks found errors in 6 of 7 high-traffic ones. The 146 entries without `guidelines_checked` now carry a warning in `get_journal_template.py` and in the skills, and ✅* in the export report. In checked entries, values that a 待核实 item calls unconfirmed are no longer enforced: Clinical Cancer Research, Circulation, Neurology, JASN, CJASN, Neurosurgery and the Nature Medicine abstract. Guidance-only reference caps are no longer hard limits: Nature Medicine, npj Digital Medicine, Blood and Blood Advances.
- 14 entries whose check was recorded only in `special` now carry `guidelines_checked` / `guidelines_source` (94 checked entries, was 80). World Journal of Urology's 3000-word limit is checked again. Clinical Cancer Research limits and the BJU International submission system are marked 待核实. `system` and the new `citation_style` field (103 entries) use fixed vocabularies, with portal addresses moved to `submission_url`.

### Engineering
- CI was one Python 3.11 job with unpinned dependencies, no lint and a non-blocking plugin validate. Actions are now pinned to commit SHAs (`persist-credentials: false`, job timeouts); tests run on Python 3.10 and 3.12, plus a job that installs exactly the `requirements.txt` lower bounds on Python 3.10; ruff (pyflakes + syntax errors) and shellcheck are blocking; `claude plugin validate --strict` is blocking, with a pinned Claude Code. The manual eval workflow defaults to routing + negative; the 6.4.1 entry said so, but it defaulted to `smoke`.
- `requirements.txt` has lower bounds (scipy ≥ 1.11, statsmodels ≥ 0.14, matplotlib ≥ 3.6, pandas ≥ 1.5, numpy ≥ 1.23, python-docx ≥ 1.1, openpyxl ≥ 3.1, PyYAML ≥ 6.0). Python 3.10 is the documented minimum.
- `tools/check_consistency.py` computes counts from the repo. It also checks `IF_year` / `guidelines_checked` counts, counts in all docs, the hook and SKILL.md files, `#anchors`, eval coverage per skill and workflow pinning. It now has its own tests and caught `plugin.json` / `marketplace.json` still saying 47 standards. Docs were re-checked: README said 46 standards and 42 entries with `IF_year`, where 82 exist. The USER-MANUAL example now shows Welch's t-test.
- Tests: 3392 (was 362). 8 test files are new (consistency guard, method-card recipes, docs examples, ethics and gates, journal templates, skill rules, standards content, study design). The export, power analysis, split / randomisation, study-design and skill-rule tests were mutation-checked; the study-design checks are negation-aware and caught 47 of 47 meaning-reversing mutations. A flaky `reproduce_check` test is now deterministic.

### Upgrading
- Python 3.10 or later is required. `randomization.py` needs `--out` outside the project and `--force` to replace a list. Stratified lists made with 6.4.x cannot be regenerated from their seed with this version; block and simple lists are unchanged.
- `patient_level_split.py` gives a different split than 6.4.x for the same seed (the summary now records the script's sha256 and numpy version). `export_docx.py` checks original-article limits unless `--article-type` is given.
- `data_profile.py` shows no category values unless it can tell patients apart: pass `--id <patient-ID column>`, or `--rows-are-patients` for one row per patient. With a patient unit, levels held by fewer than 5 patients are counted, not listed. `--max-levels 0` is now an error. In the JSON, `source.sheets` is gone (use `source.n_sheets`, `sheet_index`, `sheet` and `file_shown`); `privacy_units`, `source.codec` / `encoding_doubt` and `id_structure[].key_status` are new.
- `reproduce_check.py` check folders made before this version have no content manifest, so `--keep-last` keeps them; delete them by hand once you have reviewed them.

### Known limitations
- Journal data: 146 of the 240 entries are still unverified against current author guidelines. They are flagged, not corrected, and 26 entries carry 待核实 items. The impact factors of the 158 entries without `IF_year` are still JCR 2022 values, 137 entries have no `citation_style`, and no entries were added. Most publisher sites (nature.com, ashpublications.org, aacrjournals.org …) were unreachable from the build environment.
- Skills were not trimmed. Total SKILL.md text grew by about 24% (139,793 → 173,101 characters over the 20 files, against 6.4.2) with the rules added here, so loading skills costs more context.
- Behaviour evals have not been run in a sandbox. None of the new or changed eval cases has run against a model, and neither has the new `no-review-judge` LLM judge, because the build environment had no API key and no `bubblewrap` / `socat`. `data-first-planning` has still never run with Bash in the OS sandbox. Treat the first results as a calibration run.
- Windows paths and file locking are untested. Scripts, hook and CI were exercised only on Linux.
- `data_profile.py` finds identifiers with heuristics, so the report can still show identifying text in unusual layouts. One example is a column named like a patient ID that actually holds visit labels in a form the rule does not know: each label then counts as a patient, and a value one patient repeats at 5 visits is shown. Another is a Korean or Japanese file decoded as Chinese without `--encoding`, when its bytes do not clearly read as Korean or Japanese. Lower-case pinyin names in column names (`zhang_wei`), an initial with a surname (`J. Testperson`) and a file name with a short patient code (`P0042.csv`) are not masked either. Pass `--id` (or `--rows-are-patients`) and treat the report as patient data.
- `patient_level_split.py`'s "file may be cp1252" warning can miss some Western-encoded files.
- `tools/check_consistency.py` can still read a subset count in a SKILL.md as a library total and flag it.
- With `PYTHONUTF8=0` under `LC_ALL=C`, `mrp_state.py` refuses non-ASCII arguments (a Chinese note, a journal name) with one line and exit 2; use a UTF-8 locale or `PYTHONUTF8=1`.

---

## v6.4.2 (2026-10-11)

Journal data patch: **27 more entries re-checked** against the journals' own author-guideline pages; **160 of the 240 entries remain unverified** (no `guidelines_checked`). No skill, script or count changes.

- **Re-checked (27, `guidelines_checked: 2026-09` + `guidelines_source`)**: JAMA, JAMA Oncology, JAMA Surgery, The BMJ, BJS, BMC Medicine, and 21 Wolters Kluwer journals — Medicine, Annals of Surgery, Hepatology, Neurology, CORR, AJSP, JASN, CJASN, Chinese Medical Journal, International Journal of Surgery, Neurosurgery, Plastic and Reconstructive Surgery, Transplantation, Investigative Radiology, Obstetrics & Gynecology, Anesthesiology, European Journal of Anaesthesiology, Anesthesia & Analgesia, Nursing Research, Spine, Otology & Neurotology. The pages were read directly in a browser (Wolters Kluwer instructions via their ovid.com / Editorial Manager copies); Neurology, JASN and CJASN come from search snippets of the official pages and say so in a `special` item.
- **Limits corrected** (13 word limits, 13 abstracts, 15 reference fields, 12 figure/table fields), e.g. The BMJ sets no fixed word limit for research articles and allows 250–300-word abstracts (400 for CONSORT/PRISMA); JAMA, JAMA Oncology and JAMA Surgery allow 5 tables and/or figures in total, not 5 of each; Annals of Surgery 3000 words, ≤50 references, ≤5 figures + tables; Hepatology 6000 words including references, ≤8 figures + tables; Transplantation 4000 words and ≤30 references (January 2026 revision); Spine 2700 words; Neurosurgery 2750 words; Anesthesia & Analgesia 4000 words with a ≤400-word abstract; Obstetrics & Gynecology ≤30 references and ≤5 figures + tables; Nursing Research 16 pages; BJS has no reference limit.
- **Other corrections**: submission system for Neurology (eJournalPress) and for Chinese Medical Journal, Neurosurgery, Plastic and Reconstructive Surgery, Anesthesiology, Anesthesia & Analgesia and Spine (Editorial Manager, not ScholarOne); International Journal of Surgery is published by Wolters Kluwer; citation style added to 9 more entries (141 entries still give only a count); 21 impact factors refreshed with `IF_year` / `IF_source` (82 entries now carry `IF_year`). Wolters Kluwer's ovid.com pages show the IF without a year; their category sizes are JCR 2025's, so they are recorded as 2025 (rule added to the file header).
- **Not guessed**: where a page does not state a limit the library had (e.g. no reference cap for JAMA Original Investigation), the value is kept and a `待核实` item says so (17 entries). The Journal of Urology guidelines and the Lancet family pages could not be read and are unchanged.
- **The remaining 160 entries are not being refreshed in bulk.** The file header now says to look up a journal's current author guidelines whenever an entry without `guidelines_checked` is used.

---

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

**Correction (added in v6.5.0):** the "Data and evals" bullet above says "70 journals re-checked … 170 entries were not re-checked", and that overstates the count. At v6.4.1 only 53 entries carried `guidelines_checked`. Another 15 recorded the check only as a "Guidelines checked: … (accessed 2026-09)" item in `special`, which no script reads: BJS, Cancers, European Radiology, European Urology, European Urology Focus, European Urology Oncology, IEEE JBHI, IEEE TMI, JAMIA, npj Digital Medicine, Prostate Cancer and Prostatic Diseases, Radiology, Urologic Oncology, Urology and World Journal of Urology. The library thus recorded 68 checks, not 70, and 172 entries had none. BJS got the fields in v6.4.2 and the other 14 in v6.5.0.

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
