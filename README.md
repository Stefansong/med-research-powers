# Med-Research-Powers

[English](README.md) | [中文](README_CN.md)

**From hypothesis to publication — a guided research methodology framework that catches bad science before it happens.**

Med-Research-Powers (MRP) is a [Claude Code](https://claude.ai/code) plugin that turns AI agents into rigorous research assistants. Instead of letting an AI skip the literature review, misuse statistics, ignore reporting standards, or hallucinate references, MRP instructs Claude to follow a guided research pipeline with 3 mandatory checkpoints, a 6-gate pre-submission verification, and a 4-reviewer peer-review simulation — so every manuscript that leaves your desk is audit-ready.

Inspired by [Superpowers](https://github.com/obra/superpowers) (software-engineering methodology), adapted for clinical and biomedical research.

> **Version 6.3.0** · 20 skills · 7 slash commands · MIT License · by BTCH Uro AI Lab

---

## At a Glance

| | |
|---|---|
| **Skills** | 20 skills covering the full research pipeline — every skill is callable as `/mrp:<skill-name>` |
| **Slash Commands** | 7 commands for the most common entry points |
| **Study Designs** | Clinical, basic/bench, AI/ML, qualitative, survey/Delphi (one unified router) |
| **Reporting Standards** | 47 standards — CONSORT 2025, SPIRIT 2025, STROBE, PRISMA 2020, TRIPOD+AI 2024, DECIDE-AI, CLAIM 2024, IDEAL, ARRIVE 2.0, COREQ, CHERRIES, COSMIN … |
| **Journal Templates** | 240 journals across 30+ specialties |
| **Statistical Methods** | 15+ method categories with an assumption-driven decision tree |
| **Python Scripts** | 10 bundled scripts (assumptions, power, cleaning, analysis scaffold, figure styling, .docx export, journal-template lookup, patient-level split, randomization, pipeline state) |
| **Pre-Submission** | 6-gate verification with PubMed MCP citation checking |
| **Peer Review** | 4-reviewer simulation with 0–100 quantitative scoring across 8 dimensions |
| **Mandatory Checkpoints** | 3 decisions that always wait for your explicit approval: protocol, analysis plan, pre-submission report |
| **Export** | Markdown → `.docx` (python-docx script); `.xlsx` tables via a pandas/openpyxl snippet in `manuscript-writing` |

---

## Why MRP Exists

AI research agents make the same mistakes every time. MRP replaces "best-effort guessing" with a guided workflow:

| Without MRP | With MRP |
|---|---|
| Jumps straight to analysis | Defines the hypothesis first (PICO / FINER) |
| Picks a statistical test "that seems right" | Decision tree selects the test based on **verified** assumptions |
| Uses CONSORT 2010 | Uses CONSORT 2025 (30 items, 42 rows incl. sub-items; officially supersedes 2010) |
| Writes a manuscript and declares "done" | 6-gate verification before any submission step |
| Fabricates references confidently | Every citation is checked against PubMed (automatically when a PubMed MCP is configured, otherwise by DOI / web search) |
| Reports `p < 0.05` with no effect size | Requires effect size + 95% CI + exact p-value |
| Ignores reporting standards | Matches study type to the correct standard from 47 options |
| Splits AI data randomly | Patient-level splits; flags data leakage and external validation |

**Core philosophy — guided workflows, not suggestions:**

1. **Define before design** — PICO/FINER framework; no analysis without a hypothesis.
2. **Plan before execute** — a Statistical Analysis Plan (SAP) before any test runs.
3. **Verify before submit** — 6-gate pre-submission check; CONSORT 2025 compliance.
4. **Scripts over prompts** — reusable Python for assumption tests, sample size, figures, and export.

MRP is prompt-level guidance: the pipeline, checkpoints and gates are instructions Claude follows, not code that intercepts tool calls. It makes skipping steps unlikely and visible — it does not make it impossible.

---

## Quick Start

### Install as a Claude Code plugin (recommended)

In Claude Code:

```
/plugin marketplace add Stefansong/med-research-powers
/plugin install mrp@med-research-powers
```

From a local clone instead:

```bash
git clone https://github.com/Stefansong/med-research-powers
```

```
/plugin marketplace add ./med-research-powers
/plugin install mrp@med-research-powers
```

For development, load the checkout directly without installing: `claude --plugin-dir ./med-research-powers`

### Installer script (alternative)

```bash
git clone https://github.com/Stefansong/med-research-powers
cd med-research-powers
./install.sh              # interactive; or ./install.sh --method 1|2
```

The script offers two methods: **1)** the plugin install above (runs `claude plugin marketplace add` + `claude plugin install` when the `claude` CLI is available, otherwise prints the two slash commands), or **2)** a symlink of the whole checkout to `~/.claude/skills/med-research-powers`, which Claude Code loads as the plugin `mrp@skills-dir` — the session hook and `${CLAUDE_PLUGIN_ROOT}` work in both. It also checks the Python packages listed in `requirements.txt`. On Windows use method 1.

### Upgrading from 6.2.x

The plugin was renamed from `med-research-powers` to `mrp` (so the commands are `/mrp:…`). Uninstall the old name first, then install as above:

```
/plugin uninstall med-research-powers@med-research-powers
```

### Verify

```bash
claude plugin list        # should list mrp@med-research-powers (or mrp@skills-dir)
```

Then, in a new Claude Code session, try `/mrp:research-question` — or simply say *"I want to design a study on AI-assisted diagnosis"* and MRP routes to the right skill.

### Your first project

```
You:  "I want to study whether AI can improve bladder-cancer detection on CT"

MRP:  research-question-formulation → PICO + hypothesis        (research-question.md)
      → literature-synthesis        → evidence map + gap
      → study-design (Type C: AI/ML) → study-protocol.md        [checkpoint 1: you approve]
      → research-ethics              → ethics-statement.md
      → journal-selection            → provisional target journal
      → data-analysis-planning       → analysis-plan.md         [checkpoint 2: you approve]
      → … the rest of the pipeline, with a short summary after each step
```

---

## The Pipeline

![Med-Research-Powers Pipeline](docs/images/architecture-pipeline.jpg)

```
research-question-formulation
→ literature-synthesis
→ study-design                      [checkpoint 1: study-protocol.md]
→ research-ethics                   (approval / registration before any data collection)
→ journal-selection                 (provisional target journal — soft confirmation)
→ data-analysis-planning            [checkpoint 2: analysis-plan.md]
→ data-collection-tools
→ [you collect data]
→ statistical-analysis
→ figure-generation
→ manuscript-writing
→ peer-review-simulation
→ pre-submission-verification       [checkpoint 3: submission-readiness-report.md — 6 gates]
→ manuscript-export
→ submission-preparation
→ [submit] → revision-response
```

- **`study-design`** is a unified router covering Type A (clinical), B (basic/bench), C (AI/ML), D (qualitative), and E (survey/Delphi). Every type writes the same file, `study-protocol.md` (a `type:` field says which).
- **`research-ethics`** sits on the main line: approval and registration come before data collection, not at submission time.
- **`peer-review-simulation`** runs before the 6-gate check, and **`manuscript-export`** runs after it — so a failed gate never means re-exporting a `.docx`.
- Auxiliary skills (`pubmed-search`, `reporting-standards`, `team-collaboration`, `using-med-research-powers`, `writing-mrp-skills`) are called by other skills or usable any time.

### Mandatory checkpoints

Three decisions are irreversible in real research. Claude is instructed to stop at each one and wait for your explicit approval — "no response" never counts as approval:

| # | Checkpoint | After | What you confirm | Why it matters |
|---|---|---|---|---|
| 1 | **`study-protocol.md`** | `study-design` | Study type, primary outcome, comparator | Changing the primary outcome later = outcome switching = research misconduct |
| 2 | **`analysis-plan.md` (SAP)** | `data-analysis-planning` | Statistical methods, analysis strategy | The anti-p-hacking record; every later deviation is documented |
| 3 | **`submission-readiness-report.md`** | `pre-submission-verification` | All 6 gates pass | Nothing is exported or submitted before this |

The target journal is a **soft** confirmation: `journal-selection` proposes it early, you can change it any time, and it is re-checked once before writing and once before submission.

### Backward links

Discovering a problem downstream (e.g. a reporting-standard failure at pre-submission) sends MRP back to the upstream skill; revised artifacts are re-validated on the way forward.

---

## The 20 Skills

Skills trigger from natural-language intent — you do not need to memorize names — and every one can also be invoked directly as `/mrp:<skill-name>`. They are organized in six layers.

### Foundation Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 1 | **research-question-formulation** | A vague idea needs a clear question + hypothesis (PICO/PIRD/FINER). | `research-question.md` |
| 2 | **literature-synthesis** | Searching & synthesizing literature; finding the research gap (PRISMA flow). | `search-strategy.md`, `screening-log.md`, `literature-references.md`, `literature-synthesis-summary.md` |
| 3 | **study-design** | Designing any protocol — clinical / basic / AI-ML / qualitative / survey (Type A–E router). | `study-protocol.md` |
| 4 | **research-ethics** | Checking IRB/IACUC, consent, privacy, registration, COI before data collection; drafting the ethics statement. | `ethics-statement.md` |
| 5 | **journal-selection** | Choosing a provisional target journal (scored matching + 3-tier cascade strategy). | `journal-selection-report.md` |

### Analysis Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 6 | **data-analysis-planning** | Writing the SAP **before** any test runs (prerequisite for statistical-analysis). | `analysis-plan.md` |
| 7 | **data-collection-tools** | Generating CRFs, annotation templates, REDCap forms, inference/eval scripts from the protocol. | `tools/` directory (scripts, templates, README) |
| 8 | **statistical-analysis** | Executing the analysis on real data (requires an approved SAP). | `results-summary.md` + `analysis-log.md` (plus `analysis_script.py`, `data-cleaning-log.md`) |
| 9 | **figure-generation** | Producing publication-quality figures (journal styles, ≥300 DPI, colorblind-safe). | Publication-ready TIFF/PDF files |

### Manuscript Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 10 | **manuscript-writing** | Drafting original research or a review (5 review types). | `manuscript/` directory (IMRaD or review structure) |
| 11 | **peer-review-simulation** | Simulating peer review (4 reviewers + 8-dimension 0–100 scoring) before the gates. | `peer-review-simulation-report.md` |
| 12 | **pre-submission-verification** | The final 6-gate check — mandatory checkpoint 3. | `submission-readiness-report.md` |
| 13 | **manuscript-export** | Exporting Markdown → journal-formatted `.docx` after the gates pass. | `manuscript.docx` + `export-report.md` |
| 14 | **reporting-standards** | Matching the study type to the correct guideline & checking compliance (Gate 1 content). | Matched checklist + compliance status |

### Submission Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 15 | **submission-preparation** | Writing the cover letter + submission-system guidance (ScholarOne / Editorial Manager / eJournalPress / Snapp). | `cover-letter.md` |
| 16 | **revision-response** | Planning the revision strategy + drafting the point-by-point rebuttal. | `revision-plan.md`, `revision-tracking.md`, `response-letter.md` |

### Utility Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 17 | **pubmed-search** | Searching PubMed, verifying citations, or fetching metadata via the PubMed MCP. | Search results, verification reports, formatted references |

### Meta Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 18 | **team-collaboration** | A project benefits from multi-agent parallel work (sub-agents via the Agent tool). | Coordinated multi-agent output |
| 19 | **using-med-research-powers** | The orchestrator — routing, checkpoints, pipeline state, user memory. | Routing + checkpoint management + session resume |
| 20 | **writing-mrp-skills** | Creating, testing, or improving an MRP skill. | Skill template |

---

## The 7 Slash Commands

Commands are shortcuts for the most common entry points. Every other skill is invoked as `/mrp:<skill-name>` (for example `/mrp:study-design`, `/mrp:journal-selection`, `/mrp:manuscript-export`).

| Command | What it does | Routes to |
|---------|--------------|-----------|
| `/mrp:research-question` | Turn a vague idea into a PICO question + hypothesis | `research-question-formulation` |
| `/mrp:analyze-data` | No `analysis-plan.md` yet → write the SAP; SAP approved → run the analysis | `data-analysis-planning` → `statistical-analysis` |
| `/mrp:write-manuscript` | Draft a medical research manuscript (IMRaD or review) | `manuscript-writing` |
| `/mrp:peer-review` | Simulate peer review (4 reviewers + 8-dimension scoring) | `peer-review-simulation` |
| `/mrp:check-standards` | Reporting-guideline check only (the content of Gate 1) | `reporting-standards` |
| `/mrp:pre-submission` | The full 6-gate pre-submission verification — checkpoint 3 | `pre-submission-verification` |
| `/mrp:using-mrp` | Orchestrator — routing rules, pipeline & checkpoints | `using-med-research-powers` |

Commands are user-invoked only (`disable-model-invocation: true`), so they never double-trigger with the skills.

---

## Confirmation Modes

What goes through the pipeline: research-workflow tasks — topic, design, analysis, writing, submission, revision. A small one-off question (rephrase a sentence, compute one number) is answered directly without the pipeline.

| Mode | How to switch | Behaviour |
|------|---------------|-----------|
| **Light** (default) | — | After each skill Claude posts a 3–5 line summary (artifacts, key decisions, things to watch) and continues; it waits only at the 3 mandatory checkpoints |
| **Step** | "ask me at every step" / "逐步确认" | Waits for your OK after every skill |
| **Auto** | "run it all the way through" / "一直做到底" | Mandatory checkpoints are announced but not waited for; the content that would have been confirmed is still written into the artifact |

The light summary looks like this:

```
[study-design] done → study-protocol.md (Type C, AI diagnostic accuracy)
Key decisions: primary outcome = AUROC on external test set; patient-level split
Watch: sample size assumes prevalence 30% — confirm with local data
Checkpoint 1 — please approve the protocol before I continue.
```

"Go back to `<skill>`" at any time backtracks to that skill; revised artifacts are re-validated.

---

## Study-Design Router (Types A–E)

`study-design` is a single entry point that routes to the appropriate methodology and reporting standard:

| Type | Domain | Examples | Primary standard(s) |
|------|--------|----------|---------------------|
| **A** | Clinical | RCT, cohort, cross-sectional, crossover, non-inferiority, adaptive, real-world, registry | CONSORT 2025 / SPIRIT 2025 / STROBE |
| **B** | Basic / bench | cell, animal, molecular (WB, qPCR, ELISA, flow, IF) | ARRIVE 2.0 |
| **C** | AI / ML | imaging, video, LLM, device | TRIPOD+AI 2024 / DECIDE-AI / CLAIM 2024 / IDEAL |
| **D** | Qualitative | interview, focus group, grounded theory, mixed methods | COREQ / SRQR |
| **E** | Survey / Delphi | questionnaires, scale development/validation, consensus | CHERRIES / CROSS / COSMIN |

Multi-type studies stack the relevant modules. The AI/ML module requires patient-level data splits, a 4-band sample-size strategy, class-imbalance handling, and decision-curve analysis.

`manuscript-writing` similarly handles original research **plus** 5 review types: narrative, systematic, meta-analysis, scoping, and mini-review.

---

## 6-Gate Pre-Submission Verification

Claude is instructed to run `pre-submission-verification` whenever you say "done" or "ready to submit", and not to move on to export or the cover letter until every gate passes and you confirm the report (checkpoint 3). Any failure routes back to the responsible skill.

| Gate | Checks | Fail action |
|------|--------|-------------|
| **1. Reporting Standards** | Matches study type to the correct standard; checks every item (CONSORT 2025: 30 items, 42 rows incl. sub-items). 0 Critical failures required. | `reporting-standards` → fix in `manuscript-writing` |
| **2. Statistical Completeness** | Effect sizes + 95% CI (not just p-values), exact p-values, multiple-comparison correction, sensitivity analysis, reproducible scripts, SAP-deviation documentation | Back to `statistical-analysis` |
| **3. Claim Verification** | (A) Reference authenticity via `pubmed-search` — every PMID/DOI is looked up. (B) Data consistency — numbers match across Abstract, Results, Tables. (C) Claims–evidence alignment. (D) Methods–results matching. (E) Pre-specified vs exploratory distinction. (F) AI-hallucination patterns. | Fix references / data |
| **4. Figure Quality** | Arial/Helvetica font, ≥6 pt minimum, ≥300 DPI (line art ≥600), axis labels + units, colorblind-safe palette, figure legends | Back to `figure-generation` |
| **5. Ethics & Compliance** | IRB approval number in Methods, informed-consent statement, COI disclosure, funding source, data-availability statement, trial registration (if applicable) | Back to `research-ethics` |
| **6. Formal Requirements** | Word count within journal limit, abstract word count, reference count, running title ≤50 chars, 3–6 keywords, abbreviations expanded on first use, complete author info | Adjust formatting |

Citation verification statuses used in Gate 3: ✅ Verified · ⚠️ Not found (query succeeded, no hit) · ❌ Mismatch (found, but authors/year/title differ) · ⏳ Unverified (tool error — retry, this is *not* "does not exist") · ℹ️ Non-PubMed (books, guidelines, arXiv — checked by DOI / web search).

---

## 4-Reviewer Peer-Review Simulation

`peer-review-simulation` simulates a realistic editorial process with four independent reviewers, quantitative scoring, and journal-calibrated predictions. It runs before the 6-gate check and feeds directly into `revision-response`.

### Reviewer Panel

| Reviewer | Role | Focus |
|----------|------|-------|
| **R1 — Methodologist** | Study-design expert | Design validity, statistical methods, sample size, bias control, reproducibility |
| **R2 — Clinical / Domain Expert** | Domain specialist | Clinical significance, applicability, external validity, alternative explanations |
| **R3 — Academic Editor** | Journal gatekeeper | Structure, language quality, figure standards, reference completeness, journal fit |
| **R4 — Devil's Advocate** | Adversarial reviewer | Challenges the strongest conclusions, finds blind spots, proposes worst-case interpretations |

The Devil's Advocate is not destructive — it prepares you for the hardest questions real reviewers will ask.

### 8-Dimension Scoring (0–100)

| Dimension | Weight | Scale |
|-----------|--------|-------|
| Originality | 15% | 0–30 repetitive / 31–60 incremental / 61–80 meaningful / 81–100 breakthrough |
| Methodology | 20% | 0–30 flawed / 31–60 improvable / 61–80 sound / 81–100 innovative |
| Results | 15% | 0–30 unreliable / 31–60 partial / 61–80 solid / 81–100 compelling |
| Clinical Impact | 15% | 0–30 none / 31–60 limited / 61–80 meaningful / 81–100 practice-changing |
| Writing Quality | 10% | 0–30 unclear / 31–60 needs polish / 61–80 clear / 81–100 elegant |
| Figures & Tables | 10% | 0–30 substandard / 31–60 acceptable / 61–80 professional / 81–100 publication-grade |
| References | 5% | 0–30 insufficient / 31–60 basic / 61–80 comprehensive / 81–100 authoritative |
| Reproducibility | 10% | 0–30 not reproducible / 31–60 partial / 61–80 reproducible / 81–100 fully transparent |

### Editor Summary & Decision

The Editor Summary is not a simple average — it follows real editorial behavior: any **Critical** issue drops the decision to Major Revision regardless of scores; ≥2 reviewers recommending Reject means Reject. Scores are then calibrated to the target journal's tier (tiers live in [`scoring-rubric.yaml`](skills/peer-review-simulation/references/scoring-rubric.yaml)).

| Calibrated Score | Prediction |
|------------------|------------|
| 80–100 | Accept / Minor Revision |
| 65–79 | Minor Revision |
| 50–64 | Major Revision |
| 30–49 | Major Revision (risky) |
| 0–29 | Reject |

The four reviewers run as separate sub-agents in parallel (Claude Code's Agent tool, formerly named Task); the main agent then produces the Editor Summary. Issues are flagged by severity (Critical / Major / Minor / Suggestion).

---

## Multi-Database Literature Search

`literature-synthesis` searches across multiple databases, with the PubMed MCP as the primary engine.

### PubMed MCP Functions

The 7 function names are fixed; the tool prefix is `mcp__<server>__<function>`, where `<server>` is whatever your session's tool list shows (the claude.ai connector is `claude_ai_PubMed`; a local server is commonly `PubMed`):

| Function | Purpose |
|----------|---------|
| `search_articles` | Keyword / MeSH / Boolean search — returns `pmids`, `total_count`, `query_translation` |
| `get_article_metadata` | Full metadata (authors, abstract, DOI, MeSH terms) for screening |
| `get_full_text_article` | PMC full text (`pmc_ids=[...]`) for detailed screening and data extraction |
| `find_related_articles` | Similar-article search from seed PMIDs (`pmids=[...]`) |
| `convert_article_ids` | PMID / PMCID / DOI conversion (`ids=[...]`, `id_type="pmid"|"doi"|"pmcid"`) |
| `lookup_article_by_citation` | Reverse lookup when citation details are known but the PMID is not |
| `get_copyright_status` | Open-access status and reuse permissions |

### Database Selection by Study Type

| Research Type | Primary | Supplementary |
|---------------|---------|---------------|
| Clinical / Biomedical | PubMed | Cochrane, Embase |
| AI/ML Medical | PubMed + arXiv | IEEE Xplore, ACM DL |
| Systematic Review | PubMed + Cochrane + Embase | Web of Science |
| Basic / Molecular | PubMed | bioRxiv, medRxiv |
| Surgical Video / Devices | PubMed + IEEE | Scopus |

### Output Files (4)

| File | Content |
|------|---------|
| `search-strategy.md` | Complete reproducible search strategy per database |
| `screening-log.md` | PRISMA flow-diagram data with counts at every stage |
| `literature-references.md` | Structured records for every included study |
| `literature-synthesis-summary.md` | Evidence map: Known / Unknown / Controversial + research gap |

---

## Statistical Methods Coverage

- **Planning first**: `data-analysis-planning` produces the SAP you approve at checkpoint 2; `statistical-analysis` is instructed not to run without it.
- **Assumption-driven**: an [assumption-test decision tree](skills/data-analysis-planning/references/stat-method-decision-tree.yaml) selects parametric vs non-parametric methods.
- **Reproducible output**: the analysis pipeline flows through 6 steps — Load → Clean (missing data, outliers, type validation) → Assumption Tests → Execute Analysis → Sample Size → Generate Output — producing `data-cleaning-log.md`, `analysis_script.py`, `analysis-log.md`, `results-summary.md`, all operating on `data_clean.csv`.

The decision tree covers 15+ method categories:

| Category | Methods |
|----------|---------|
| **Two Groups** | Independent/paired t-test, Welch's t-test, Mann-Whitney U, Wilcoxon signed-rank, Chi-squared, Fisher's exact |
| **Multiple Groups** | One-way ANOVA + Tukey, Welch's ANOVA + Games-Howell, Kruskal-Wallis + Dunn's, Friedman + Nemenyi, repeated-measures ANOVA |
| **Correlation / Regression** | Pearson, Spearman, linear regression, logistic regression, Poisson / negative binomial |
| **Survival Analysis** | Log-rank, Kaplan-Meier, Cox proportional hazards, competing risks (Fine-Gray), AFT models, time-varying covariates |
| **Longitudinal / Mixed Models** | Linear mixed models (LMM), generalized estimating equations (GEE), repeated-measures ANOVA |
| **Causal Inference** | Propensity score (matching, IPTW, stratification), instrumental variables (2SLS), difference-in-differences |
| **Mediation Analysis** | Baron-Kenny, causal mediation (natural direct/indirect effects), bootstrap CIs |
| **Missing Data** | MCAR testing (Little's test), multiple imputation (MICE, m≥20), MNAR sensitivity, tipping-point analysis |
| **Clustered Data** | ICC calculation, design effect, random intercept/slope models, cluster-robust GEE |
| **Interaction / Subgroup** | Interaction terms, forest plots, pre-specified vs exploratory labeling |
| **High-Dimensional / Omics** | PCA, UMAP/t-SNE, DESeq2, edgeR, limma, FDR correction, batch-effect removal (ComBat) |
| **Interrupted Time Series** | Segmented regression, ARIMA, controlled ITS |
| **Diagnostic & AI/ML Evaluation** | AUROC/AUPRC, DeLong, calibration, decision-curve analysis, bootstrap CIs |
| **Multiple Comparison** | Bonferroni, Holm, Benjamini-Hochberg FDR |
| **Assumption Tests** | Shapiro-Wilk, D'Agostino-Pearson, Levene's, Mauchly's sphericity, Schoenfeld residuals |

---

## Reporting Standards (47)

The full, machine-readable index lives in [`skills/reporting-standards/references/checklists/standards-index.yaml`](skills/reporting-standards/references/checklists/standards-index.yaml). **21 of the 47 standards ship with an item-by-item checklist YAML transcribed from the source paper** (CONSORT 2025, CONSORT-AI, SPIRIT 2025, SPIRIT-AI, TIDieR, TREND, RECORD, STROBE, PRISMA 2020, PRISMA-ScR, STARD 2015, TRIPOD 2015, TRIPOD+AI, CLAIM 2024, DECIDE-AI, ARRIVE 2.0, CHERRIES, CROSS, CARE, SQUIRE 2.0, CHEERS 2022); for the rest the index gives the official source and Claude is told not to invent items.

### Standards by Study Type

| Category | Standards |
|----------|-----------|
| **Clinical Trials** | CONSORT 2025 (30 items, 42 rows incl. sub-items), CONSORT-AI, CONSORT-Cluster, CONSORT non-inferiority extension, TREND (non-randomised trials), SPIRIT 2025 (34 items, protocols only), SPIRIT-AI, TIDieR, CONSORT-Harms |
| **Observational** | STROBE (22 items), RECORD, STROCSS |
| **Systematic Reviews** | PRISMA 2020 (27 items), PRISMA-P, PRISMA-ScR, PRISMA-S, PRISMA-DTA, PRISMA-NMA, TRIPOD-SRMA (2023), AMSTAR 2, GRADE |
| **Guidelines Appraisal** | AGREE II (23 items) |
| **Meta-analysis of Observational** | MOOSE (35 items) |
| **Diagnostic** | STARD 2015 (30 items) |
| **AI & Prediction** | TRIPOD 2015 (22 items, legacy), TRIPOD+AI 2024 (27 items), TRIPOD-LLM (2025), TRIPOD-Cluster (2023, 19 items), CLAIM 2024 (44 items; supersedes CLAIM 2020), MI-CLAIM, DECIDE-AI (17 AI-specific + 10 generic items), PROBAST |
| **Surgery & Devices** | IDEAL framework (5 stages) |
| **Qualitative** | COREQ (32 items), SRQR (21 items) |
| **Surveys & Instruments** | CHERRIES (web surveys), CROSS (cross-sectional surveys), COSMIN (measurement instruments) |
| **Preclinical** | ARRIVE 2.0 (21 items) |
| **Other** | CARE (case reports), SQUIRE (QI), CHEERS (health economics) |
| **Bias Assessment Tools** | Cochrane RoB 2, ROBINS-I, Newcastle-Ottawa Scale (max 9), MINORS, QUADAS-2 |

> **CONSORT 2010 is officially superseded** — MRP always routes to CONSORT 2025 (30 items, 42 rows incl. sub-items). [Hopewell et al., BMJ 2025; doi:10.1136/bmj-2024-081123]

---

## Journal Templates (240)

Formatting requirements (word limits, abstract format, reference style, section structure, special boxes, cover-letter & ORCID requirements, submission system) for **240 journals across 30+ specialties** live in [`skills/manuscript-writing/references/journal-templates.yaml`](skills/manuscript-writing/references/journal-templates.yaml). Skills fetch one entry at a time with `get_journal_template.py` instead of reading the whole file.

| Specialty | Journals |
|-----------|----------|
| **General Top Tier** | Nature, Nature Medicine, Lancet, NEJM, JAMA, BMJ, Annals of Internal Medicine |
| **General Mid Tier** | BMC Medicine, Medicine |
| **Oncology** | JCO, Lancet Oncology, JAMA Oncology, Annals of Oncology, Cancer Research |
| **Surgery** | Annals of Surgery, JAMA Surgery, BJS, Surgical Endoscopy |
| **Urology** | European Urology, Journal of Urology, BJU International |
| **Cardiology** | European Heart Journal, JACC, Circulation |
| **Gastroenterology** | Gastroenterology, Gut, Hepatology |
| **Respiratory** | Lancet Respiratory, AJRCCM, CHEST |
| **Neurology** | Lancet Neurology, Neurology, JAMA Neurology |
| **Radiology & Imaging** | Radiology, European Radiology, Medical Image Analysis |
| **AI / Digital Health** | npj Digital Medicine, Lancet Digital Health, JMIR, IEEE JBHI |
| **Pediatrics** | Lancet Child, JAMA Pediatrics, Pediatrics |
| **Orthopedics** | JBJS, CORR |
| **Ophthalmology** | Ophthalmology, JAMA Ophthalmology |
| **Dermatology** | JAMA Dermatology, BJD |
| **Pathology** | Modern Pathology, AJSP |
| **Infectious Disease** | Lancet ID, CID |
| **Endocrinology** | Diabetes Care, Lancet Diabetes |
| **Nephrology** | JASN |
| **Psychiatry** | Lancet Psychiatry, JAMA Psychiatry |
| **Systematic Reviews** | Cochrane Database, Systematic Reviews |
| **Open Access** | PLOS Medicine, PLOS ONE, Nature Communications, Scientific Reports |
| **Chinese SCI** | Chinese Medical Journal, Science Bulletin, Signal Transduction, eClinicalMedicine |

Each template includes: word limit, abstract format (structured/unstructured), reference style and limit, figure/table limits, section structure, special requirements (Key Points box, Research in Context panel, Reporting Summary), submission system, and ORCID policy. The journal-family rules (Lancet / JAMA / Nature sub-journals) are kept in that file only.

Impact factors and APCs carry their vintage: 41 frequently targeted journals (urology, radiology, AI/digital health, top general and oncology titles) have `IF_year`/`IF_source` fields with the publisher-reported JCR 2025 or 2024 value; the rest still hold JCR 2022 values (`data_as_of` explains the rule). Skills always state the year and re-check the top candidates on the web before you rely on them. If a journal isn't listed, MRP fetches its "Instructions for Authors" via web search.

---

## Bundled Python Scripts

Reusable, callable code (not re-written from prompts each time). Skills call them through `${CLAUDE_PLUGIN_ROOT}`, which Claude Code sets to the plugin's install directory.

| Script | Location | Purpose |
|--------|----------|---------|
| `assumption_tests.py` | `statistical-analysis/scripts/` | Normality (Shapiro-Wilk, D'Agostino-Pearson), homogeneity (Levene's), automatic test recommendation, Cohen's d with CI |
| `power_analysis.py` | `statistical-analysis/scripts/` | Sample size / power across designs: two-group, proportion, diagnostic accuracy, survival, correlation — with dropout adjustment |
| `analysis_template.py` | `statistical-analysis/scripts/` | Reproducible analysis scaffold operating on `data_clean.csv` |
| `data_cleaning.py` | `statistical-analysis/scripts/` | Missing-data, outlier and type-validation cleaning with an audit log (`data-cleaning-log.md`) |
| `pub_style.py` | `figure-generation/scripts/` | Journal figure styling (Nature, Lancet, JAMA, NEJM palettes), colorblind-safe options, ≥300 DPI export, significance bars |
| `export_docx.py` | `manuscript-export/scripts/` | Markdown → journal-formatted `.docx`, driven by the journal template library; writes `export-report.md` |
| `get_journal_template.py` | `manuscript-writing/scripts/` | Extract one journal's entry by id from the 240-journal YAML (no whole-file reads) |
| `patient_level_split.py` | `data-collection-tools/scripts/` | Patient-level train / validation / test split (no leakage across sets) |
| `randomization.py` | `data-collection-tools/scripts/` | Block / stratified randomization lists for RCTs |
| `mrp_state.py` | `using-med-research-powers/scripts/` | Read and update `.mrp-state.json` at the end of each pipeline skill |

Usage example:

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), "skills", "statistical-analysis", "scripts"))
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), "skills", "figure-generation", "scripts"))

from assumption_tests import full_check          # assumption testing
result = full_check(group1, group2, paired=False)
print(f"Recommended test: {result['recommended_test']}")

from power_analysis import two_groups            # sample size
result = two_groups(effect_size=0.5, power=0.80, dropout=0.15)

from pub_style import apply_style                # publication figure styling
apply_style('lancet')
```

Install the dependencies with `pip install -r requirements.txt`.

---

## Multi-Agent Parallel Collaboration

MRP uses Claude Code's sub-agent tool (**Agent**, formerly named Task) to parallelize independent research tasks, with the main agent coordinating results (`team-collaboration`).

### Auto-Parallel (no confirmation needed)

| Trigger | Parallel tasks |
|---------|----------------|
| Literature synthesis with ≥2 databases | One sub-agent per database, simultaneous search |
| Peer-review simulation | 4 sub-agents as independent reviewers, parallel evaluation |

### User-Confirmed Parallel

| Trigger | Parallel tasks |
|---------|----------------|
| Revision with independent reviewer comments | One sub-agent per reviewer's feedback, each writing its own file; the main agent merges |
| Protocol design needing multi-expert review | Statistics + methodology + AI expert agents |

### Merge Rules

- Sub-agent outputs are checked for numerical consistency before merging.
- Sub-agents never write the same manuscript file; the main agent merges sequentially and resolves conflicts.
- If a sub-agent discovers it needs another agent's data, parallelism stops and shifts to sequential execution.

---

## User Memory

MRP remembers a few preferences across projects in one global file, `~/.claude/mrp-user-profile.json` (per person, not per project). There is no start-up questionnaire: a field is collected lazily — the first time a skill needs it and it is missing, Claude asks that one question and offers to save the answer.

| Skill | Field it reads | Used for |
|-------|----------------|----------|
| `journal-selection` | `preferences.favorite_journals` | Prioritizes journals you have targeted before |
| `data-analysis-planning` | `preferences.preferred_stats_tool` | Generates scripts in your language (Python / R / SPSS / Stata) |
| `figure-generation` | `preferences.preferred_figure_style` | Applies your figure style (nature / lancet / jama / nejm) |

### Privacy

- Stored locally only — never uploaded to any service.
- Delete `~/.claude/mrp-user-profile.json` at any time to clear it, or say "forget my [field]".
- MRP never records passwords, patient data, or ethics-approval numbers.

---

## Session State

MRP tracks research progress in `.mrp-state.json` in your project directory, so a new session can pick up where the last one stopped. Each pipeline skill ends by updating it with `mrp_state.py`; the session-start hook reads a few short fields from it and reports *"Last completed: [stage]. Next step: [skill]. Continue?"* (see [SECURITY.md](SECURITY.md) for exactly what the hook reads).

```json
{
  "project": "AI-assisted bladder-cancer detection on CT",
  "current_stage": "data-analysis-planning",
  "completed_skills": [
    {"skill": "research-question-formulation", "date": "2026-09-01", "outputs": ["research-question.md"]},
    {"skill": "study-design", "date": "2026-09-05", "outputs": ["study-protocol.md"]}
  ],
  "artifacts": {
    "research-question.md": {"version": 1},
    "study-protocol.md": {"version": 2, "change_log": "Primary outcome clarified after checkpoint 1"}
  },
  "target_journal": "European Urology",
  "checkpoint_mode": "light",
  "next_step": "data-analysis-planning"
}
```

Fields: `project`, `current_stage`, `completed_skills[{skill, date, outputs[]}]`, `artifacts{}`, `target_journal`, `checkpoint_mode` (`"light"` | `"step"` | `"auto"`), `next_step`. Schema: [`skills/using-med-research-powers/references/state-schemas.md`](skills/using-med-research-powers/references/state-schemas.md). The file stays in your local project directory and is never uploaded.

---

## .docx Export

Most journals require Word format for submission. After the 6 gates pass, `manuscript-export` produces the submission files:

| File | Produced by | Notes |
|------|-------------|-------|
| `manuscript.docx` | `export_docx.py` | Journal-formatted main file (font, spacing, section order and special panels from the journal template) |
| `export-report.md` | `export_docx.py` | Word counts (body / abstract / references separately), reference & figure counts, leftover placeholders |
| `figures/*.tiff` | `figure-generation` (`pub_style.py`) | Figure files, ≥300 DPI (line art ≥600) |
| Tables `.xlsx` | pandas / openpyxl snippet in `manuscript-writing` | Not a bundled script — run the snippet when a journal wants tables as a separate workbook |

Title page and supplementary material are drafted as Markdown by `manuscript-writing`; convert them with the same script when the journal requires separate files.

---

## Architecture Comparison: Superpowers vs MRP

MRP adapts the Superpowers methodology framework from software engineering to medical research.

| Superpowers (Software Engineering) | Med-Research-Powers (Medical Research) | Adaptation rationale |
|---|---|---|
| `brainstorming` | `research-question-formulation` | Structured PICO/FINER instead of freeform ideation |
| `writing-plans` | `study-design` (Type A–E router) | A single design skill routing across research domains |
| `test-driven-development` | `data-analysis-planning` | SAP = test plan; anti-p-hacking = anti-regression |
| `executing-plans` | `statistical-analysis` | Reproducible scripts = reproducible builds |
| `requesting-code-review` | `peer-review-simulation` | 4 reviewers replace code reviewers |
| `verification-before-completion` | `pre-submission-verification` | 6-gate system replaces CI/CD checks |
| `receiving-code-review` | `revision-response` | Point-by-point response = code-review response |
| `finishing-a-development-branch` | `journal-selection` + `submission-preparation` | Journal targeting + cover letter replace merge/deploy |
| `writing-skills` | `writing-mrp-skills` | Same meta-skill for extensibility |
| — | `literature-synthesis` | No software equivalent; research requires evidence review |
| — | `reporting-standards` | No software equivalent; 46 domain-specific compliance standards |
| — | `research-ethics` | No software equivalent; IRB/IACUC requirements |

---

## Requirements

- **Claude Code** (CLI, desktop, web, or IDE extension).
- **Python 3** with the packages in [`requirements.txt`](requirements.txt) (`scipy`, `statsmodels`, `matplotlib`, `pandas`, `numpy`, `python-docx`, `openpyxl`, `pyyaml`) for the bundled scripts — the skills themselves work without them.
- **PubMed MCP** (optional but recommended): any MCP server that exposes the 7 functions above (`search_articles`, `get_article_metadata`, `find_related_articles`, `lookup_article_by_citation`, `convert_article_ids`, `get_full_text_article`, `get_copyright_status`). Tools are addressed as `mcp__<server>__<function>`; the server name comes from your session's tool list (`claude_ai_PubMed` for the claude.ai connector, commonly `PubMed` locally). With it configured, citations are verified automatically; without it, verification falls back to manual DOI / web-search checks.

---

## Repository Layout

```
med-research-powers/
├── .claude-plugin/        plugin.json (name: mrp), marketplace.json
├── .github/               ci.yml (guard, pytest, shellcheck, plugin validate, hook smoke test), evals.yml (manual), issue/PR templates
├── commands/              7 slash commands (thin routers → skills)
├── skills/                20 skills, each: SKILL.md + references/ + scripts/
├── hooks/                 session-start.sh (reads .mrp-state.json, reports the resume point)
├── docs/                  architecture.md, USER-MANUAL.md, images/
├── tools/                 check_consistency.py — repository guard (versions, counts, paths, links)
├── tests/                 pytest suite for the bundled scripts
├── evals/                 `claude plugin eval` cases — skill routing regression (see evals/README.md)
├── examples/              a synthetic example project (state file, research question, Type C protocol)
├── install.sh             installer (plugin / symlink)
├── requirements.txt       Python packages for the bundled scripts
├── README.md / README_CN.md
└── CHANGELOG.md · CONTRIBUTING.md · SECURITY.md · LICENSE
```

Each skill keeps reasoning in `SKILL.md` and pushes lookup tables, templates, and checklists into `references/`, and reusable code into `scripts/` — so context stays lean and content stays maintainable.

---

## Uninstall

```
/plugin uninstall mrp@med-research-powers
```

Optionally remove the marketplace too: `/plugin marketplace remove med-research-powers`. If you used the symlink method: `rm ~/.claude/skills/med-research-powers`. Project files created by MRP (`.mrp-state.json`, the artifacts) and the global `~/.claude/mrp-user-profile.json` are yours to keep or delete.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills follow the spec in `writing-mrp-skills`: a trigger-only `description` (≤200 chars, starts with "Use when"), the standard section set (Overview, When to Use, When NOT to Use, Workflow, Output, Common Mistakes, Convergence, Red Flags, 衔接规则), lookup content in `references/`, fixed code in `scripts/`, and SKILL.md ≤ 500 lines. Run `python tools/check_consistency.py` and `pytest tests/` before opening a PR.

**Ways to contribute:**

- **New skills** — read `skills/writing-mrp-skills/SKILL.md`, create a skill in `skills/`, and submit a PR.
- **Specialty packs** — journal configs, MeSH terms, assessment tools for your specialty.
- **Reporting standards** — add or update checklists in `skills/reporting-standards/references/checklists/`.
- **Journal templates** — add entries to `journal-templates.yaml` following the existing structure.
- **Bug reports** — file issues for skills that should trigger but don't, incorrect checklist items, or script errors. Security concerns: see [SECURITY.md](SECURITY.md).

---

## License & Credits

- **License:** MIT (see [LICENSE](LICENSE))
- **Author:** BTCH Uro AI Lab
- **Inspired by:** [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent — the software-engineering methodology framework behind this project

### Acknowledgments

- [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent — the methodology framework that inspired MRP
- [EQUATOR Network](https://www.equator-network.org/) — the authoritative source for reporting guidelines
- The PubMed MCP servers (community and claude.ai connector) built on NCBI E-utilities — they make automated citation verification possible; MRP does not bundle one

*Med-Research-Powers guides methodology; it does not replace your judgment, your IRB, or your statistician. Always confirm ethics status and verify analyses with a qualified expert.*
