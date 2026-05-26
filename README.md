# Med-Research-Powers

[English](README.md) | [中文](README_CN.md)

**From hypothesis to publication — an AI-enforced research methodology framework that prevents bad science before it happens.**

Med-Research-Powers (MRP) is a [Claude Code](https://claude.ai/code) plugin that turns AI agents into rigorous research assistants. Instead of letting an AI skip the literature review, misuse statistics, ignore reporting standards, or hallucinate references, MRP enforces a guided research pipeline with hard checkpoints, a 6-gate pre-submission verification, and a 4-reviewer peer-review simulation — so every manuscript that leaves your desk is audit-ready.

Inspired by [Superpowers](https://github.com/obra/superpowers) (software-engineering methodology), adapted for clinical and biomedical research.

> **Version 6.2.1** · 20 skills · 20 slash commands · MIT License · by BTCH Uro AI Lab

---

## At a Glance

| | |
|---|---|
| **Skills** | 20 skills covering the full research pipeline |
| **Slash Commands** | 20 commands for direct invocation |
| **Study Designs** | Clinical, basic/bench, AI/ML, qualitative, survey/Delphi (one unified router) |
| **Reporting Standards** | 42+ standards — CONSORT 2025, SPIRIT 2025, STROBE, PRISMA, TRIPOD+AI 2024, DECIDE-AI, CLAIM, IDEAL, ARRIVE 2.0, COREQ, CHERRIES … |
| **Journal Templates** | 234 journals across 30+ specialties |
| **Statistical Methods** | 15+ method categories with an assumption-driven decision tree |
| **Python Scripts** | 5 bundled scripts (assumptions, power analysis, analysis scaffold, figure styling, .docx export) |
| **Pre-Submission** | 6-gate mandatory verification with PubMed MCP claim checking |
| **Peer Review** | 4-reviewer simulation with 0–100 quantitative scoring across 8 dimensions |
| **Hard Checkpoints** | 4 approval gates that lock irreversible decisions |
| **Export Formats** | Markdown, `.docx` (python-docx), `.xlsx` (openpyxl) |

---

## Why MRP Exists

AI research agents make the same mistakes every time. MRP replaces "best-effort guessing" with enforced workflows:

| Without MRP | With MRP |
|---|---|
| Jumps straight to analysis | Defines the hypothesis first (PICO / FINER) |
| Picks a statistical test "that seems right" | Decision tree selects the test based on **verified** assumptions |
| Uses CONSORT 2010 | Uses CONSORT 2025 (31 numbered items / 34 rows; officially supersedes 2010) |
| Writes a manuscript and declares "done" | 6-gate verification blocks submission until compliant |
| Fabricates references confidently | PubMed MCP auto-verifies every citation |
| Reports `p < 0.05` with no effect size | Requires effect size + 95% CI + exact p-value |
| Ignores reporting standards | Matches study type to the correct standard from 42+ options |
| Splits AI data randomly | Patient-level splits; flags data leakage and external validation |

**Core philosophy — enforced workflows, not suggestions:**

1. **Define before design** — PICO/FINER framework; no analysis without a hypothesis.
2. **Plan before execute** — a Statistical Analysis Plan (SAP) before any test runs.
3. **Verify before submit** — 6-gate pre-submission check; CONSORT 2025 compliance.
4. **Scripts over prompts** — reusable Python for assumption tests, sample size, figures, and export.

---

## Quick Start

### Install as a Claude Code plugin (recommended)

```bash
git clone https://github.com/Stefansong/med-research-powers
cd med-research-powers
```

In Claude Code:

```
/plugin install ./med-research-powers
```

The plugin path is the only install method that also enables the session-start hook (auto-discovery + routing).

### Interactive installer (alternative)

```bash
git clone https://github.com/Stefansong/med-research-powers
cd med-research-powers
./install.sh
```

The installer detects your platform, offers three methods (plugin / copy / symlink), and checks Python dependencies. Note: the copy and symlink methods install skills only — they do **not** enable the session hook.

### Verify

Start a new Claude Code session and try:

```
/mrp:research-question
```

Or simply say *"I want to design a study on AI-assisted diagnosis"* — MRP routes to the correct skill automatically.

### Your first project

```
You:  "I want to study whether AI can improve bladder-cancer detection on CT"

MRP:  Using research-question-formulation to define PICO + hypothesis
      → literature-synthesis to search PubMed + preprints
      → study-design (Type C: AI/ML) to design the validation study
      → journal-selection to pick the target journal
      → data-analysis-planning to write the SAP
      → … (full pipeline, with a checkpoint after every step)
```

---

## The Pipeline

![Med-Research-Powers Pipeline](docs/images/architecture-pipeline.png)

```
research-question-formulation → literature-synthesis → study-design → journal-selection →
data-analysis-planning → data-collection-tools → [you collect data] →
statistical-analysis → figure-generation →
manuscript-writing → manuscript-export → peer-review-simulation → pre-submission-verification →
submission-preparation → [submit] → revision-response
```

- **`study-design`** is a unified router covering Type A (clinical), B (basic/bench), C (AI/ML), D (qualitative), and E (survey/Delphi).
- **`submission-preparation`** owns cover-letter writing + submission-system guidance.
- **`revision-response`** owns revision strategy + point-by-point reviewer responses.
- Auxiliary skills (`pubmed-search`, `data-collection-tools`, `manuscript-export`, `team-collaboration`) are callable any time.

### Hard Checkpoints (cannot be skipped)

Four decisions are irreversible in real research. MRP locks them behind **explicit** user approval — "no response" never counts as approval:

| # | Checkpoint | When | What gets locked | Why it matters |
|---|---|---|---|---|
| HC #1 | **`study-protocol.md`** | After `study-design` | Study type, primary outcome | Changing the primary outcome later = outcome switching = research misconduct |
| HC #2 | **`analysis-plan.md` (SAP)** | After `data-analysis-planning` | Statistical methods, analysis strategy | The core anti-p-hacking mechanism; all deviations must be documented |
| HC #3 | **`journal-selection-report.md`** | After `journal-selection` | Target journal, format specs | Downstream writing + formatting depend on this choice |
| HC #4 | **`submission-readiness-report.md`** | After `pre-submission-verification` | Submission readiness | All 6 gates must pass before submission |

### Fast-Track & backward links

- **Fast-Track Mode** — when you say "run it all the way through" / "don't ask me", MRP pauses only at the 4 hard checkpoints and auto-advances soft steps.
- **Backward links** — discovering a problem downstream (e.g. a reporting-standard failure during pre-submission) lets MRP route back to the upstream skill; revised artifacts are re-validated.

---

## The 20 Skills

Skills auto-trigger from natural-language intent — you do not need to memorize commands. They are organized in six layers.

### Foundation Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 1 | **research-question-formulation** | A vague idea needs a clear question + hypothesis (PICO/PIRD/FINER). | `research-question.md` |
| 2 | **literature-synthesis** | Searching & synthesizing literature; finding the research gap (PRISMA flow). | 4 files: search strategy, screening log, references, synthesis summary |
| 3 | **study-design** | Designing any protocol — clinical / basic / AI-ML / qualitative / survey (Type A–E router). | `study-protocol.md` |
| 4 | **journal-selection** | Choosing a target journal (scored matching + 3-tier cascade strategy). | `journal-selection-report.md` |

### Analysis Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 5 | **data-analysis-planning** | Writing the SAP **before** any test runs (prerequisite for statistical-analysis). | `analysis-plan.md` |
| 6 | **data-collection-tools** | Generating CRFs, annotation templates, REDCap forms, inference/eval scripts from the protocol. | `tools/` directory (scripts, templates, README) |
| 7 | **statistical-analysis** | Executing the analysis on real data (requires a completed SAP). | 4 files: cleaning log, script, analysis log, results summary |
| 8 | **figure-generation** | Producing publication-quality figures (journal styles, ≥300 DPI, colorblind-safe). | Publication-ready TIFF files |

### Manuscript Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 9 | **manuscript-writing** | Drafting original research or a review (5 review types). | `manuscript/` directory (IMRaD or review structure) |
| 10 | **manuscript-export** | Exporting Markdown → journal-formatted `.docx`. | `manuscript.docx` |
| 11 | **reporting-standards** | Matching the study type to the correct guideline & checking compliance. | Matched checklist + compliance status |
| 12 | **peer-review-simulation** | Simulating peer review (4 reviewers + 8-dimension 0–100 scoring) before submission. | `peer-review-simulation-report.md` |
| 13 | **research-ethics** | Checking IRB/IACUC, consent, privacy, registration, COI; drafting the ethics statement. | Ethics compliance statement |
| 14 | **pre-submission-verification** | **MANDATORY** 6-gate final check — all gates must pass to submit. | `submission-readiness-report.md` |

### Submission Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 15 | **submission-preparation** | Writing the cover letter + submission-system guidance (ScholarOne / Editorial Manager). | `cover-letter.md` + `submission-checklist.md` |
| 16 | **revision-response** | Planning the revision strategy + drafting the point-by-point rebuttal. | `revision-plan.md` + `response-letter.md` |

### Utility Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 17 | **pubmed-search** | Searching PubMed, verifying citations, or fetching metadata via the PubMed MCP. | Search results, verification reports, formatted references |

### Meta Layer

| # | Skill | Use it when… | Output |
|---|-------|--------------|--------|
| 18 | **team-collaboration** | A project benefits from multi-agent parallel work (dispatched via the Task tool). | Coordinated multi-agent output |
| 19 | **using-med-research-powers** | The orchestrator — routing, checkpoints, pipeline state, user memory. | Routing + checkpoint management + session resume |
| 20 | **writing-mrp-skills** | Creating, testing, or improving an MRP skill. | Skill template |

---

## The 20 Slash Commands

Every skill is reachable in plain language; commands give you a direct entry point. Use `/mrp:<command>` to invoke directly. Commands are grouped by pipeline phase.

### Phase 1 — Research Foundation

| Command | What it does |
|---------|--------------|
| `/mrp:research-question` | Turn a vague idea into a PICO question + hypothesis |
| `/mrp:literature-synthesis` | Multi-database literature search & synthesis (PRISMA + gap map) |
| `/mrp:study-design` | Design a protocol for any study type (clinical/basic/AI/qualitative/survey) |
| `/mrp:journal-selection` | Choose the best target journal (scored matching + 3-tier cascade) |

### Phase 2 — Analysis & Data Collection

| Command | What it does |
|---------|--------------|
| `/mrp:analyze-data` | Plan **then** run statistical analysis (planning → execution) |
| `/mrp:data-collection-tools` | Generate CRFs, annotation templates & scripts from the protocol |
| `/mrp:figure-generation` | Publication-quality figures (journal styles, ≥300 DPI, colorblind-safe) |

### Phase 3 — Manuscript & QA

| Command | What it does |
|---------|--------------|
| `/mrp:write-manuscript` | Draft a medical research manuscript (IMRaD or review) |
| `/mrp:manuscript-export` | Convert Markdown → journal-formatted `.docx` |
| `/mrp:reporting-standards` | Match study type to its reporting guideline (42+ standards) |
| `/mrp:check-standards` | Reporting-guideline compliance check (Gate 1 of pre-submission) |
| `/mrp:research-ethics` | Check ethical compliance & draft the ethics statement |
| `/mrp:peer-review` | Simulate peer review (4 reviewers + 8-dimension scoring) |
| `/mrp:pre-submission` | **MANDATORY** 6-gate pre-submission verification |

### Phase 4 — Submission & Revision

| Command | What it does |
|---------|--------------|
| `/mrp:submission-preparation` | Write the cover letter + submission-system guidance |
| `/mrp:revision-response` | Plan revision strategy + draft point-by-point responses |

### Meta & Utility

| Command | What it does |
|---------|--------------|
| `/mrp:pubmed-search` | Search PubMed / verify citations / fetch metadata |
| `/mrp:team-collaboration` | Run multi-agent parallel research tasks |
| `/mrp:using-mrp` | Orchestrator — routing rules, pipeline & checkpoints |
| `/mrp:writing-mrp-skills` | Create, test, or improve an MRP skill |

---

## Checkpoint Protocol

Every skill reports its output before advancing — no silent transitions.

### Report Format

After each skill completes, MRP outputs a structured report:

```
--------------------------------------
[Skill Name] completed

Generated files:
  - [file1.md] -- [description]
  - [file2.py] -- [description]

Key findings:
  - [1-3 critical findings or decisions]

Attention needed:
  - [issues requiring user judgment]

Suggested next step: [next skill] -- [purpose]
--------------------------------------
Continue? Or modify the current output?
```

### Confirmation Rules

| User response | MRP behavior |
|---------------|--------------|
| "continue" / "next" | Proceed to the suggested next skill |
| "wait" / requests changes | Modify the current output, then re-report |
| "skip [skill]" | Record the reason and advance (except `pre-submission-verification`) |
| "go back to [skill]" | Backtrack to the specified skill; revised artifacts are re-validated |

A hard checkpoint never auto-passes: "no response" is never treated as approval.

---

## Study-Design Router (Types A–E)

`study-design` is a single entry point that routes to the appropriate methodology and reporting standard:

| Type | Domain | Examples | Primary standard(s) |
|------|--------|----------|---------------------|
| **A** | Clinical | RCT, cohort, cross-sectional, crossover, non-inferiority, adaptive, real-world, registry | CONSORT 2025 / SPIRIT 2025 / STROBE |
| **B** | Basic / bench | cell, animal, molecular (WB, qPCR, ELISA, flow, IF) | ARRIVE 2.0 |
| **C** | AI / ML | imaging, video, LLM, device | TRIPOD+AI 2024 / DECIDE-AI / CLAIM / IDEAL |
| **D** | Qualitative | interview, focus group, grounded theory, mixed methods | COREQ / SRQR |
| **E** | Survey / Delphi | questionnaires, scale development/validation, consensus | CHERRIES |

Multi-type studies stack the relevant modules. The AI/ML module enforces patient-level data splits, a 4-band sample-size strategy, class-imbalance handling, and decision-curve analysis.

`manuscript-writing` similarly handles original research **plus** 5 review types: narrative, systematic, meta-analysis, scoping, and mini-review.

---

## 6-Gate Pre-Submission Verification

`pre-submission-verification` triggers automatically when you say "done" or "ready to submit". It is mandatory and blocks submission until every gate passes. Any failure routes back to the responsible skill.

| Gate | Checks | Fail action |
|------|--------|-------------|
| **1. Reporting Standards** | Matches study type to the correct standard; checks every item (CONSORT 2025: 31 numbered items / 34 rows). 0 Critical failures required. | Back to `manuscript-writing` |
| **2. Statistical Completeness** | Effect sizes + 95% CI (not just p-values), exact p-values, multiple-comparison correction, sensitivity analysis, reproducible scripts, SAP-deviation documentation | Back to `statistical-analysis` |
| **3. Claim Verification** | (A) Reference authenticity via the PubMed MCP — verifies every PMID/DOI exists. (B) Data consistency — numbers match across Abstract, Results, Tables. (C) Claims–evidence alignment. (D) Methods–results matching. (E) Pre-specified vs exploratory distinction. (F) AI-hallucination detection. | Fix references / data |
| **4. Figure Quality** | Arial/Helvetica font, ≥6 pt minimum, ≥300 DPI (line art ≥600), axis labels + units, colorblind-safe palette, figure legends | Back to `figure-generation` |
| **5. Ethics & Compliance** | IRB approval number in Methods, informed-consent statement, COI disclosure, funding source, data-availability statement, trial registration (if applicable) | Back to `research-ethics` |
| **6. Formal Requirements** | Word count within journal limit, abstract word count, reference count, running title ≤50 chars, 3–6 keywords, abbreviations expanded on first use, complete author info | Adjust formatting |

---

## 4-Reviewer Peer-Review Simulation

`peer-review-simulation` simulates a realistic editorial process with four independent reviewers, quantitative scoring, and journal-calibrated predictions, feeding directly into `revision-response`.

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

### Editor Summary & Journal Calibration

The Editor Summary is not a simple average — it follows real editorial behavior:

- If any reviewer flags a **Critical** issue, the decision drops to Major Revision regardless of scores.
- If ≥2 reviewers recommend Reject, the decision is Reject regardless of the average.
- Scores are calibrated against the target journal's tier:

| Journal Tier | Calibration |
|--------------|-------------|
| Top (IF > 30): Nature, Lancet, JAMA | Scores adjusted −10 to −15 |
| High (IF 10–30): specialty top journals | Scores adjusted −5 to −10 |
| Mid (IF 5–10): mainstream journals | No adjustment |
| Entry (IF < 5): entry-level journals | Scores adjusted +5 |

### Decision Mapping

| Calibrated Score | Prediction |
|------------------|------------|
| 80–100 | Accept / Minor Revision |
| 65–79 | Minor Revision |
| 50–64 | Major Revision |
| < 50 | Reject |

The four reviewers run as separate sub-agents in parallel (dispatched via the Task tool); the main agent then produces the Editor Summary. Issues are flagged by severity (Critical / Major / Minor).

---

## Multi-Database Literature Search

`literature-synthesis` searches across multiple databases, with the PubMed MCP as the primary engine.

### PubMed MCP Functions

All tools are referenced as `mcp__claude_ai_PubMed__*`:

| Function | Purpose |
|----------|---------|
| `search_articles` | Keyword / MeSH / Boolean search — primary search engine |
| `get_article_metadata` | Retrieve full metadata (authors, abstract, DOI) for screening |
| `get_full_text_article` | Access PMC full text for detailed screening and data extraction |
| `find_related_articles` | Snowball search from seed articles |
| `convert_article_ids` | PMID / PMCID / DOI conversion for reference consistency |
| `lookup_article_by_citation` | Reverse lookup when citation info is available but the PMID is not |
| `get_copyright_status` | Check open-access status and reuse permissions |

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

- **Planning first**: `data-analysis-planning` produces a locked SAP; `statistical-analysis` cannot run without it.
- **Assumption-driven**: an [assumption-test decision tree](skills/data-analysis-planning/references/stat-method-decision-tree.yaml) auto-selects parametric vs non-parametric methods.
- **Reproducible output**: the analysis pipeline flows through 6 steps — Load → Clean (missing data, outliers, type validation) → Assumption Tests → Execute Analysis → Sample Size → Generate Output — producing 4 files: `data-cleaning-log.md`, `analysis_script.py`, `analysis-log.md`, `results-summary.md`, all operating on `data_clean.csv`.

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

## Reporting Standards (42+)

The full, machine-readable index lives in [`skills/reporting-standards/references/checklists/standards-index.yaml`](skills/reporting-standards/references/checklists/standards-index.yaml), with a structured CONSORT 2025 checklist in [`consort-2025.yaml`](skills/reporting-standards/references/checklists/consort-2025.yaml).

### Standards by Study Type

| Category | Standards |
|----------|-----------|
| **Clinical Trials** | CONSORT 2025 (31 numbered items / 34 rows), CONSORT-AI, CONSORT-Cluster, SPIRIT 2025, SPIRIT-AI, TIDieR, CONSORT-Harms |
| **Observational** | STROBE (22 items), RECORD, STROCSS |
| **Systematic Reviews** | PRISMA 2020 (27 items), PRISMA-P, PRISMA-ScR, PRISMA-S, PRISMA-DTA, PRISMA-NMA, TRIPOD-SRMA, AMSTAR 2, GRADE |
| **Guidelines Appraisal** | AGREE II (23 items) |
| **Meta-analysis of Observational** | MOOSE (35 items) |
| **Diagnostic** | STARD 2015 (30 items) |
| **AI & Prediction** | TRIPOD+AI 2024 (27 items), TRIPOD-LLM, TRIPOD-Cluster, CLAIM (40 items), MI-CLAIM, DECIDE-AI (17 items), PROBAST |
| **Surgery & Devices** | IDEAL framework (5 stages), MVAL |
| **Qualitative** | COREQ (32 items), SRQR (21 items) |
| **Preclinical** | ARRIVE 2.0 (21 items) |
| **Other** | CARE (case reports), SQUIRE (QI), CHEERS (health economics), CHERRIES (surveys) |
| **Bias Assessment Tools** | Cochrane RoB 2, ROBINS-I, NOS, MINORS, QUADAS-2 |

> **CONSORT 2010 is officially superseded** — MRP always routes to CONSORT 2025 (31 numbered items / 34 rows). [Hopewell et al., BMJ/JAMA/Lancet/Nature Medicine/PLOS Medicine, April 2025]

---

## Journal Templates (234)

Formatting requirements (word limits, abstract format, reference style, section structure, special boxes, cover-letter & ORCID requirements, submission system) for **234 journals across 30+ specialties** live in [`skills/manuscript-writing/references/journal-templates.yaml`](skills/manuscript-writing/references/journal-templates.yaml).

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

Each template includes: word limit, abstract format (structured/unstructured), reference style and limit, figure/table limits, section structure, special requirements (Key Points box, Research in Context panel, Reporting Summary), submission system, and ORCID policy.

**Journal family patterns:**
- **Lancet family** — all sub-journals require a Research in Context panel
- **JAMA family** — all sub-journals require a Key Points box
- **Nature family** — all sub-journals require a Reporting Summary

If a journal isn't listed, MRP fetches its "Instructions for Authors" via web search.

---

## Bundled Python Scripts

Reusable, callable code (not re-written from prompts each time):

| Script | Location | Purpose |
|--------|----------|---------|
| `assumption_tests.py` | `statistical-analysis/scripts/` | Normality (Shapiro-Wilk, D'Agostino-Pearson), homogeneity (Levene's), automatic test recommendation, Cohen's d with CI |
| `power_analysis.py` | `statistical-analysis/scripts/` | Sample size / power across designs: two-group, proportion, diagnostic accuracy, survival, correlation — with dropout adjustment |
| `analysis_template.py` | `statistical-analysis/scripts/` | Reproducible analysis scaffold operating on `data_clean.csv` |
| `pub_style.py` | `figure-generation/scripts/` | Journal figure styling (Nature, Lancet, JAMA, NEJM palettes), colorblind-safe options, Arial font, ≥300 DPI export, significance bars |
| `export_docx.py` | `manuscript-export/scripts/` | Markdown → journal-formatted `.docx`, driven by the journal template library |

Usage example:

```python
# Assumption testing
from assumption_tests import full_check
result = full_check(group1, group2, paired=False)
print(f"Recommended test: {result['recommended_test']}")

# Sample size calculation
from power_analysis import two_groups
result = two_groups(effect_size=0.5, power=0.80, dropout=0.15)

# Publication figure styling
from pub_style import apply_style
apply_style('lancet')
```

---

## Multi-Agent Parallel Collaboration

MRP uses Claude Code's **Task tool** to parallelize independent research tasks, with the main agent coordinating results (`team-collaboration`).

### Auto-Parallel (no confirmation needed)

| Trigger | Parallel tasks |
|---------|----------------|
| Literature synthesis with ≥2 databases | One sub-agent per database, simultaneous search |
| Peer-review simulation | 4 sub-agents as independent reviewers, parallel evaluation |

### User-Confirmed Parallel

| Trigger | Parallel tasks |
|---------|----------------|
| Revision with independent reviewer comments | One sub-agent per reviewer's feedback |
| Protocol design needing multi-expert review | Statistics + methodology + AI expert agents |

### Merge Rules

- Sub-agent outputs are checked for numerical consistency before merging.
- Conflicting modifications to the same section require main-agent resolution.
- If a sub-agent discovers it needs another agent's data, parallelism stops and shifts to sequential execution.

---

## User Memory System

MRP remembers user preferences across sessions via `.mrp-user-profile.json` in the project directory.

### What Gets Remembered

| Category | Examples |
|----------|----------|
| **Profile** | Role (PI / PhD student / postdoc), department, institution, expertise level |
| **Research domains** | Urology, medical AI, oncology, epidemiology |
| **Familiar methods** | RCT, cohort, deep learning, survival analysis |
| **Unfamiliar methods** | Bayesian, mediation analysis (triggers extra explanations) |
| **Preferred journals** | Tracked with submission count per journal |
| **Tool preferences** | Python / R / SPSS / Stata, figure style (Nature / Lancet / JAMA) |
| **History** | Past projects, outcomes, common reviewer-feedback patterns |

### How Memory is Used

| Skill | Memory usage |
|-------|--------------|
| `journal-selection` | Prioritizes previously targeted journals |
| `data-analysis-planning` | Generates scripts in the preferred language (Python/R) |
| `figure-generation` | Applies the preferred figure style |
| `manuscript-writing` | Auto-loads the journal template based on favorite journals |
| `peer-review-simulation` | Focuses on historically weak areas |
| `statistical-analysis` | Provides extra explanation for unfamiliar methods |

### First-Time Setup

On first use (no `.mrp-user-profile.json` found), MRP asks 5 quick questions about your role, research area, preferred journals, familiar methods, and analysis tool. You can answer or skip; the profile is then updated quietly over time.

### Privacy

- Memory is stored locally only — never uploaded to any service.
- Delete `.mrp-user-profile.json` at any time to clear all memory.
- Say "forget my [field]" to remove specific entries.
- MRP never records passwords, patient data, or ethics-approval numbers.

---

## Session State Management

MRP tracks research progress in `.mrp-state.json`, enabling cross-session continuity.

```json
{
  "project": "Research title",
  "created": "2026-04-02",
  "current_stage": "data-analysis-planning",
  "target_journal": "European Urology",
  "completed_skills": [
    {"skill": "research-question-formulation", "output": "research-question.md", "date": "..."},
    {"skill": "study-design", "output": "study-protocol.md", "date": "..."}
  ],
  "artifacts": {
    "research-question.md": {"version": 1, "date": "..."},
    "analysis-plan.md": {"version": 2, "change_log": "Revised after lit review"}
  }
}
```

On session start, MRP checks for `.mrp-state.json` and reports: *"Last completed: [stage]. Next step: [skill]. Continue?"*

Schemas for both state files: [`skills/using-med-research-powers/references/state-schemas.md`](skills/using-med-research-powers/references/state-schemas.md). These files are stored only in your local project directory and never uploaded.

---

## .docx & .xlsx Export

Most journals require Word format for submission. MRP generates submission-ready exports via `manuscript-export`.

| File | Format | Purpose | Dependency |
|------|--------|---------|------------|
| `manuscript.docx` | Word | Main submission file (Times New Roman 12 pt, double-spaced, 2.54 cm margins) | `python-docx` |
| `manuscript_tables.xlsx` | Excel | Separate table upload (baseline, outcomes, subgroups as sheets) | `openpyxl` |
| `title-page.docx` | Word | Separate title page (some journals require this) | `python-docx` |
| `supplementary.docx` | Word | Supplementary materials | `python-docx` |
| `figures/*.tiff` | TIFF | Figure files (generated by `figure-generation`) | `matplotlib` |

Install dependencies: `pip install python-docx openpyxl`

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
| — | `reporting-standards` | No software equivalent; 42+ domain-specific compliance standards |
| — | `research-ethics` | No software equivalent; IRB/IACUC requirements |

---

## Requirements

- **Claude Code** (CLI, desktop, web, or IDE extension).
- **Python 3** with `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `python-docx`, `openpyxl` for the statistical, figure, and export scripts (the installer checks these).
- **PubMed MCP** (optional but recommended) for citation verification and literature search — tools are referenced as `mcp__claude_ai_PubMed__*`.

---

## Repository Layout

```
med-research-powers/
├── .claude-plugin/        plugin.json, marketplace.json
├── commands/              20 slash commands (thin routers → skills)
├── skills/                20 skills, each: SKILL.md + references/ + scripts/
├── hooks/                 session-start.sh (auto-discovery + routing)
├── docs/                  architecture.md, USER-MANUAL.md
├── examples/showcase/     real pipeline output examples
├── install.sh             interactive installer
├── README.md / README_CN.md
└── CHANGELOG.md
```

Each skill keeps reasoning in `SKILL.md` and pushes lookup tables, templates, and checklists into `references/`, and reusable code into `scripts/` — so context stays lean and content stays maintainable.

---

## Showcase

See real pipeline artifacts in [`examples/showcase/`](examples/showcase/) — complete outputs from running MRP on actual research projects, including research questions, analysis plans, manuscripts, review reports, and submission-readiness checks.

*Contributions welcome — run the pipeline on your research and submit a PR.*

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills follow the spec in `writing-mrp-skills`: a trigger-only `description` (≤200 chars), the standard section set (Overview, When to Use, When NOT to Use, Workflow, Output, Common Mistakes, Convergence, Red Flags, 衔接规则), lookup content in `references/`, and fixed code in `scripts/`.

**Ways to contribute:**

- **New skills** — read `skills/writing-mrp-skills/SKILL.md`, create a skill in `skills/`, and submit a PR.
- **Specialty packs** — journal configs, MeSH terms, assessment tools for your specialty.
- **Reporting standards** — add or update checklists in `reporting-standards/references/checklists/`.
- **Journal templates** — add entries to `journal-templates.yaml` following the existing structure.
- **Bug reports** — file issues for skills that should trigger but don't, incorrect checklist items, or script errors.

---

## License & Credits

- **License:** MIT (see [LICENSE](LICENSE))
- **Author:** BTCH Uro AI Lab
- **Inspired by:** [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent — the software-engineering methodology framework behind this project

### Acknowledgments

- [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent — the methodology framework that inspired MRP
- [EQUATOR Network](https://www.equator-network.org/) — the authoritative source for reporting guidelines
- [PubMed MCP](https://github.com/Stefansong/med-research-powers) — enabling automated literature verification

*Med-Research-Powers enforces methodology; it does not replace your judgment, your IRB, or your statistician. Always confirm ethics status and verify analyses with a qualified expert.*
