# Med-Research-Powers

[English](README.md) | [中文](README_CN.md)

**From hypothesis to publication — an AI-enforced research methodology framework that prevents bad science before it happens.**

Med-Research-Powers (MRP) is a [Claude Code](https://claude.ai/code) plugin that transforms AI coding agents into rigorous research assistants. Instead of letting AI skip literature reviews, misuse statistics, ignore reporting standards, or hallucinate references, MRP enforces a mandatory pipeline with hard checkpoints, 6-gate pre-submission verification, and 4-reviewer peer review simulation — so every manuscript that leaves your desk is audit-ready.

Inspired by [Superpowers](https://github.com/obra/superpowers) (software engineering methodology), adapted for clinical and biomedical research.

---

## At a Glance

| | |
|---|---|
| **Skills** | 24 skills covering the full research pipeline |
| **Slash Commands** | 24 commands for direct invocation |
| **Reporting Standards** | ~42 standards including CONSORT 2025, STROBE, PRISMA, TRIPOD-AI, DECIDE-AI |
| **Journal Templates** | 68 journals across 22 specialties |
| **Statistical Methods** | 15+ method categories with decision tree |
| **Python Scripts** | 3 bundled scripts (assumptions, power analysis, figure styling) |
| **Pre-Submission** | 6-gate mandatory verification with PubMed MCP claim checking |
| **Peer Review** | 4-reviewer simulation with 0-100 quantitative scoring |
| **Hard Checkpoints** | 4 mandatory approval gates that lock critical decisions |
| **Export Formats** | Markdown, .docx (python-docx), .xlsx (openpyxl) |

---

## Why MRP Exists

AI research agents make the same mistakes every time:

| Without MRP | With MRP |
|---|---|
| Jumps straight to analysis | Define hypothesis first (PICO/FINER) |
| Picks a statistical test "that seems right" | Decision tree selects test based on verified assumptions |
| Uses CONSORT 2010 | Uses CONSORT 2025 (30 items, officially supersedes 2010) |
| Writes manuscript, declares "done" | 6-gate verification blocks submission until compliant |
| Fabricates references confidently | PubMed MCP auto-verifies every citation |
| Reports p < 0.05, no effect size | Requires effect size + 95% CI + exact p-value |
| Ignores reporting standards | Matches study type to correct standard from ~42 options |

**Core philosophy: enforced workflows, not suggestions.**

1. **Define before design** -- PICO/FINER framework, no analysis without a hypothesis
2. **Plan before execute** -- Statistical analysis plan (SAP) before any test runs
3. **Verify before submit** -- 6-gate pre-submission check, CONSORT 2025 compliance
4. **Scripts over prompts** -- Reusable Python scripts for assumption tests, sample size, figure styling

---

## Quick Start

### Install as Claude Code Plugin (recommended)

```bash
git clone https://github.com/Stefansong/med-research-powers
cd med-research-powers
```

In Claude Code:
```
/plugin install ./med-research-powers
```

### Interactive Installer (alternative)

```bash
git clone https://github.com/Stefansong/med-research-powers
cd med-research-powers
./install.sh
```

The installer detects your platform, offers three install methods (plugin / copy / symlink), and checks Python dependencies.

### Verify Installation

Start a new Claude Code session. You should see the MRP auto-discovery message. Try:

```
/mrp:research-question
```

Or just say: *"I want to design a study on AI-assisted diagnosis"* -- MRP will automatically route to the correct skill.

### First Research Project

```
You:  "I want to study whether AI can improve bladder cancer detection on CT"

MRP:  Using research-question-formulation to define PICO + hypothesis
      → literature-synthesis to search PubMed + arXiv
      → ai-medical-study-design to design the validation study
      → journal-selection to pick target journal
      → data-analysis-planning to create SAP
      → ... (full pipeline with checkpoints at every step)
```

---

## Pipeline

### Architecture Overview

![Med-Research-Powers Pipeline](docs/images/architecture-pipeline.png)

Skipping any step blocks downstream skills. Backward links allow returning to upstream skills when issues are discovered later.

### Pipeline Flow

```
research-question → literature-synthesis → study-design → journal-selection →
data-analysis-planning → data-collection-tools → [user collects data] →
statistical-analysis → figure-generation →
manuscript-writing → manuscript-export → pre-submission-verification →
cover-letter-writing → submission-system-guide → [submit] →
revision-strategy → responding-to-reviewers
```

**Utility skills** (callable at any point): `pubmed-search`, `research-ethics`, `reporting-standards`

### Fast-Track Mode

For experienced users: say "go all the way" or "don't ask me" to skip soft checkpoints. Only the 4 hard checkpoints (protocol, SAP, journal, pre-submission) will pause for confirmation.

### System Architecture

![System Architecture](docs/images/system-architecture.png)

The meta-skill `using-med-research-powers` acts as the central orchestrator, routing tasks to 21 skills across 5 clusters. Infrastructure components (`session-start.sh` hook, `.mrp-state.json` session persistence, `.mrp-user-profile.json` user memory, `plugin.json` command registration) and external integrations (PubMed MCP) form the outer ring.

---

## Slash Commands (21)

Commands are grouped by pipeline phase. Use `/mrp:<command>` to invoke directly.

### Phase 1 -- Research Foundation

| Command | Purpose |
|---|---|
| `/mrp:research-question` | Formulate research question using PICO/FINER framework |
| `/mrp:literature-synthesis` | Multi-database literature search + PRISMA screening |
| `/mrp:study-design` | Clinical research protocol design (RCT, cohort, cross-sectional) |
| `/mrp:basic-study-design` | Bench science experiment design (cell, animal, molecular) |
| `/mrp:ai-study-design` | AI/ML medical research design (imaging, NLP, LLM evaluation) |
| `/mrp:journal-selection` | Target journal matching with 4-step scoring + 3-tier ranking |

### Phase 2 -- Analysis & Data Collection

| Command | Purpose |
|---|---|
| `/mrp:analyze-data` | Plan and execute statistical analysis with reproducible scripts |
| `/mrp:data-tools` | Generate data collection tools (inference scripts, CRFs, annotation templates) |
| `/mrp:figure-generation` | Publication-quality figures with journal-specific palettes |

### Phase 3 -- Manuscript & QA

| Command | Purpose |
|---|---|
| `/mrp:write-manuscript` | Write manuscript (original research IMRaD or review articles) with journal template |
| `/mrp:export-manuscript` | Export manuscript Markdown to .docx with journal-specific formatting |
| `/mrp:reporting-standards` | Match study type to reporting guideline (~42 standards) |
| `/mrp:research-ethics` | Ethics compliance: IRB, IACUC, informed consent, COI |
| `/mrp:peer-review` | Simulate 4-reviewer peer review with quantitative scoring |
| `/mrp:check-standards` | Check reporting standard compliance |
| `/mrp:pre-submission` | 6-Gate mandatory pre-submission verification |

### Phase 4 -- Submission & Revision

| Command | Purpose |
|---|---|
| `/mrp:cover-letter` | Cover letter writing with cascade rewrite for different journals |
| `/mrp:submission-guide` | Submission system operation guide (ScholarOne, Editorial Manager) |
| `/mrp:revision-strategy` | Revision planning + reviewer comment triage |
| `/mrp:responding-to-reviewers` | Point-by-point response letter |

### Meta

| Command | Purpose |
|---|---|
| `/mrp:using-mrp` | Meta-skill: routing, checkpoints, user memory, pipeline state |
| `/mrp:pubmed-search` | Deep PubMed search: interactive query building, citation verification, reference formatting |
| `/mrp:team-collaboration` | Multi-agent parallel research tasks |
| `/mrp:writing-mrp-skills` | How to create new MRP skills |

---

## Skills (24)

Skills are auto-triggered based on natural language intent. You do not need to memorize commands -- just describe what you need.

### Foundation Layer (6 skills)

| Skill | Auto-triggers on | Output |
|---|---|---|
| `research-question-formulation` | "I want to study...", research ideas, PICO | `research-question.md` |
| `literature-synthesis` | literature review, research gap, background | 4 files: search strategy, screening log, references, synthesis summary |
| `study-design` | clinical study design, RCT, cohort | `study-protocol.md` |
| `basic-medical-study-design` | cell, animal, molecular, WB, qPCR | `study-protocol.md` |
| `ai-medical-study-design` | AI, ML, imaging, surgical video, LLM | `study-protocol.md` |
| `journal-selection` | which journal, impact factor, journal fit | `journal-selection-report.md` |

### Analysis Layer (4 skills)

| Skill | Auto-triggers on | Output |
|---|---|---|
| `data-analysis-planning` | analysis strategy, SAP, which test to use | `analysis-plan.md` |
| `data-collection-tools` | generate scripts, CRF, annotation template | `tools/` directory with scripts, templates, README |
| `statistical-analysis` | run analysis, regression, survival analysis | 4 files: cleaning log, script, analysis log, results summary |
| `figure-generation` | figures, charts, visualization | Publication-ready TIFF files |

### Manuscript Layer (6 skills)

| Skill | Auto-triggers on | Output |
|---|---|---|
| `manuscript-writing` | write manuscript, Introduction, Methods, review article | `manuscript/` directory (IMRaD or review structure) |
| `manuscript-export` | export to Word, docx, format for submission | `manuscript.docx` with journal-specific formatting |
| `reporting-standards` | CONSORT, STROBE, PRISMA, checklist | Matched checklist with compliance status |
| `research-ethics` | IRB, ethics, informed consent | Ethics compliance reminder |
| `peer-review-simulation` | review my paper, what would reviewers say | `peer-review-simulation-report.md` |
| `pre-submission-verification` | "done", "ready to submit", finalized | `submission-readiness-report.md` |

### Submission Layer (4 skills)

| Skill | Auto-triggers on | Output |
|---|---|---|
| `cover-letter-writing` | cover letter, submission letter | `cover-letter.md` |
| `submission-system-guide` | how to submit, upload, ScholarOne | Submission checklist |
| `revision-strategy` | revision, major/minor, reviewer comments | `revision-plan.md` |
| `responding-to-reviewers` | reviewer response, point-by-point | `response-letter.md` |

### Utility Layer (1 skill)

| Skill | Auto-triggers on | Output |
|---|---|---|
| `pubmed-search` | PubMed search, verify citation, PMID, format references | Search results, verification reports, formatted references |

### Meta Layer (3 skills)

| Skill | Auto-triggers on | Output |
|---|---|---|
| `using-med-research-powers` | Any research-related task (orchestrator) | Routing + checkpoint management + session resume |
| `team-collaboration` | parallel, team, simultaneous tasks | Coordinated multi-agent output |
| `writing-mrp-skills` | create new skill, modify skill | Skill template |

### Study Type Routing

```
Research type?
+-- Clinical trial / observational  --> study-design
+-- Bench / cell / animal           --> basic-medical-study-design
+-- AI / ML / imaging / devices     --> ai-medical-study-design
+-- Multiple types                  --> combine as needed
```

---

## Hard Checkpoints

Four decisions are irreversible in real research. MRP locks them behind mandatory user approval -- no silent pass-through, no default confirmation.

| # | Checkpoint | When | What gets locked | Why |
|---|---|---|---|---|
| HC #1 | Protocol Approval | After `study-design` | Research type, primary outcome | Changing primary outcome post-hoc = outcome switching = research misconduct |
| HC #2 | SAP Approval | After `data-analysis-planning` | Statistical methods, analysis plan | Prevents p-hacking; all deviations must be documented |
| HC #3 | Journal Confirmed | After `journal-selection` | Target journal, format specs | Downstream writing and formatting depend on this choice |
| HC #4 | 6-Gate Verification | After `pre-submission-verification` | Submission readiness | All 6 gates must pass before proceeding to submission |

---

## Checkpoint Protocol

Every skill reports its output before advancing. No silent transitions.

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
|---|---|
| "continue" / "next" | Proceed to suggested next skill |
| "wait" / requests changes | Modify current output, re-report |
| "skip [skill]" | Record reason, advance (except pre-submission-verification) |
| "go back to [skill]" | Backtrack to specified skill |

---

## 6-Gate Pre-Submission Verification

![6-Gate Verification](docs/images/6-gate-verification.png)

Triggers automatically when you say "done" or "ready to submit". All gates must pass. Any failure blocks submission and routes back to the responsible skill.

### Gate Details

| Gate | Checks | Fail action |
|---|---|---|
| **1. Reporting Standards** | Matches study type to correct standard; checks every item (CONSORT 2025: 30 items). 0 Critical failures required. | Back to `manuscript-writing` |
| **2. Statistical Completeness** | Effect sizes + 95% CI (not just p-values), exact p-values, multiple comparison correction, sensitivity analysis, reproducible scripts, SAP deviation documentation | Back to `statistical-analysis` |
| **3. Claim Verification** | (A) Reference authenticity via PubMed MCP -- verifies every PMID/DOI exists. (B) Data consistency -- numbers match across Abstract, Results, Tables. (C) Claims-evidence alignment. (D) Methods-results matching. (E) Pre-specified vs exploratory distinction. (F) AI hallucination detection. | Fix references / data |
| **4. Figure Quality** | Arial/Helvetica font, >=6pt minimum, >=300 DPI (line art >=600), axis labels + units, colorblind-safe palette, figure legends | Back to `figure-generation` |
| **5. Ethics Compliance** | IRB approval number in Methods, informed consent statement, COI disclosure, funding source, data availability statement, trial registration (if applicable) | Back to `research-ethics` |
| **6. Formal Requirements** | Word count within journal limit, abstract word count, reference count, running title <=50 chars, 3-6 keywords, abbreviations expanded on first use, author info complete | Adjust formatting |

---

## 4-Reviewer Peer Review Simulation

![Peer Review Simulation](docs/images/peer-review-simulation.png)

Simulates a realistic editorial process with four independent reviewers, quantitative scoring, and journal-calibrated predictions.

### Reviewer Panel

| Reviewer | Role | Focus |
|---|---|---|
| R1 -- Methodologist | Study design expert | Design validity, statistical methods, sample size, bias control, reproducibility |
| R2 -- Clinical Expert | Domain specialist | Clinical significance, applicability, external validity, alternative explanations |
| R3 -- Academic Editor | Journal gatekeeper | Structure, language quality, figure standards, reference completeness, journal fit |
| R4 -- **Devil's Advocate** | Adversarial reviewer | Challenges strongest conclusions, finds blind spots, proposes worst-case interpretations |

The Devil's Advocate is not destructive -- it prepares you for the hardest questions real reviewers will ask.

### 8-Dimension Scoring (0-100)

| Dimension | Weight | Scale |
|---|---|---|
| Originality | 15% | 0-30: repetitive / 31-60: incremental / 61-80: meaningful / 81-100: breakthrough |
| Methodology | 20% | 0-30: flawed / 31-60: improvable / 61-80: sound / 81-100: innovative |
| Results | 15% | 0-30: unreliable / 31-60: partial / 61-80: solid / 81-100: compelling |
| Clinical Impact | 15% | 0-30: none / 31-60: limited / 61-80: meaningful / 81-100: practice-changing |
| Writing Quality | 10% | 0-30: unclear / 31-60: needs polish / 61-80: clear / 81-100: elegant |
| Figures & Tables | 10% | 0-30: substandard / 31-60: acceptable / 61-80: professional / 81-100: publication-grade |
| References | 5% | 0-30: insufficient / 31-60: basic / 61-80: comprehensive / 81-100: authoritative |
| Reproducibility | 10% | 0-30: not reproducible / 31-60: partial / 61-80: reproducible / 81-100: fully transparent |

### Editor Summary and Journal Calibration

The Editor Summary is not a simple average. It follows real editorial behavior:

- If any reviewer flags a **Critical** issue, the decision drops to Major Revision regardless of scores
- If >=2 reviewers recommend Reject, the decision is Reject regardless of average
- Scores are calibrated against the target journal's tier:

| Journal Tier | Calibration |
|---|---|
| Top (IF > 30): Nature, Lancet, JAMA | Scores adjusted -10 to -15 |
| High (IF 10-30): Specialty top journals | Scores adjusted -5 to -10 |
| Mid (IF 5-10): Mainstream journals | No adjustment |
| Entry (IF < 5): Entry-level journals | Scores adjusted +5 |

### Decision Mapping

| Calibrated Score | Prediction |
|---|---|
| 80-100 | Accept / Minor Revision |
| 65-79 | Minor Revision |
| 50-64 | Major Revision |
| < 50 | Reject |

Auto-Parallel: 4 reviewers run as separate sub-agents in parallel, then the main agent produces the Editor Summary.

---

## Multi-Database Literature Search

![Multi-Database Literature Search](docs/images/literature-search.png)

MRP searches across multiple databases simultaneously, with PubMed MCP as the primary engine.

### PubMed MCP Functions

| Function | Purpose |
|---|---|
| `search_articles` | Keyword / MeSH / Boolean search -- primary search engine |
| `get_article_metadata` | Retrieve full metadata (authors, abstract, DOI) for screening |
| `get_full_text_article` | Access PMC full text for detailed screening and data extraction |
| `find_related_articles` | Snowball search from seed articles |
| `convert_article_ids` | PMID / PMCID / DOI conversion for reference consistency |
| `lookup_article_by_citation` | Reverse lookup when citation info is available but PMID is not |
| `get_copyright_status` | Check open access and reuse permissions |

### Database Selection by Study Type

| Research Type | Primary | Supplementary |
|---|---|---|
| Clinical / Biomedical | PubMed | Cochrane, Embase |
| AI/ML Medical | PubMed + arXiv | IEEE Xplore, ACM DL |
| Systematic Review | PubMed + Cochrane + Embase | Web of Science |
| Basic / Molecular | PubMed | bioRxiv, medRxiv |
| Surgical Video / Devices | PubMed + IEEE | Scopus |

### Output Files (4)

| File | Content |
|---|---|
| `search-strategy.md` | Complete reproducible search strategy per database |
| `screening-log.md` | PRISMA flow diagram data with counts at every stage |
| `literature-references.md` | Structured records for every included study |
| `literature-synthesis-summary.md` | Evidence map: Known / Unknown / Controversial + research gap |

---

## Statistical Methods Coverage

The decision tree (`stat-method-decision-tree.yaml`) covers 15+ method categories:

| Category | Methods |
|---|---|
| **Two Groups** | Independent/paired t-test, Welch's t-test, Mann-Whitney U, Wilcoxon signed-rank, Chi-squared, Fisher's exact |
| **Multiple Groups** | One-way ANOVA + Tukey, Welch's ANOVA + Games-Howell, Kruskal-Wallis + Dunn's, Friedman + Nemenyi, repeated-measures ANOVA |
| **Correlation / Regression** | Pearson, Spearman, linear regression, logistic regression, Poisson / negative binomial |
| **Survival Analysis** | Log-rank, Kaplan-Meier, Cox proportional hazards, competing risks (Fine-Gray), AFT models, time-varying covariates |
| **Longitudinal / Mixed Models** | Linear mixed models (LMM), generalized estimating equations (GEE), repeated-measures ANOVA |
| **Causal Inference** | Propensity score (matching, IPTW, stratification), instrumental variables (2SLS), difference-in-differences |
| **Mediation Analysis** | Baron-Kenny, causal mediation (natural direct/indirect effects), bootstrap CIs |
| **Missing Data** | MCAR testing (Little's test), multiple imputation (MICE, m>=20), MNAR sensitivity, tipping point analysis |
| **Clustered Data** | ICC calculation, design effect, random intercept/slope models, cluster-robust GEE |
| **Interaction / Subgroup** | Interaction terms, forest plots, pre-specified vs exploratory labeling |
| **High-Dimensional / Omics** | PCA, UMAP/t-SNE, DESeq2, edgeR, limma, FDR correction, batch effect removal (ComBat) |
| **Interrupted Time Series** | Segmented regression, ARIMA, controlled ITS |
| **Multiple Comparison** | Bonferroni, Holm, Benjamini-Hochberg FDR |
| **Assumption Tests** | Shapiro-Wilk, D'Agostino-Pearson, Levene's, Mauchly's sphericity, Schoenfeld residuals |

The statistical analysis pipeline flows through 6 steps: Load -> Clean (missing data, outliers, type validation) -> Assumption Tests -> Execute Analysis -> Sample Size -> Generate Output (4 files: `data-cleaning-log.md`, `analysis_script.py`, `analysis-log.md`, `results-summary.md`).

---

## Journal Template Library

68 journals across 22 specialties, each with complete formatting specifications.

| Specialty | Journals |
|---|---|
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
- **Lancet family** (10 sub-journals): all require Research in Context panel
- **JAMA family** (8 sub-journals): all require Key Points box
- **Nature family** (6 sub-journals): all require Reporting Summary

If the target journal is not in the template library, MRP uses WebSearch to retrieve "Instructions for Authors" and extract specifications.

---

## Reporting Standards Coverage (~42)

### Standards by Study Type

| Category | Standards |
|---|---|
| **Clinical Trials** | CONSORT 2025 (30 items), CONSORT-AI, CONSORT-Cluster, SPIRIT 2025 (34 items), SPIRIT-AI, TIDieR, CONSORT-Harms |
| **Observational** | STROBE (22 items), RECORD, STROCSS |
| **Systematic Reviews** | PRISMA 2020 (27 items), PRISMA-P, PRISMA-ScR, PRISMA-S, PRISMA-DTA, PRISMA-NMA, TRIPOD-SRMA, AMSTAR 2, GRADE |
| **Guidelines Appraisal** | AGREE II (23 items) |
| **Meta-analysis of Observational** | MOOSE (35 items) |
| **Diagnostic** | STARD 2015 (30 items) |
| **AI & Prediction** | TRIPOD+AI 2024 (27 items), TRIPOD-LLM, TRIPOD-Cluster, CLAIM (40 items), MI-CLAIM, DECIDE-AI (17 items), PROBAST |
| **Surgery & Devices** | IDEAL framework (5 stages), MVAL |
| **Qualitative** | COREQ (32 items), SRQR (21 items) |
| **Preclinical** | ARRIVE 2.0 (21 items) |
| **Other** | CARE (case reports), SQUIRE (QI), CHEERS (health economics) |
| **Bias Assessment Tools** | Cochrane RoB 2, ROBINS-I, NOS, MINORS, QUADAS-2 |

> **CONSORT 2010 is officially superseded.** MRP uses CONSORT 2025 (30 items). [Hopewell et al., BMJ/JAMA/Lancet/Nature Medicine/PLOS Medicine, April 2025]

---

## Python Scripts

Three bundled scripts provide reproducible computation for common research tasks.

| Script | Location | Purpose | Key Features |
|---|---|---|---|
| `assumption_tests.py` | `statistical-analysis/scripts/` | Statistical assumption testing | Normality (Shapiro-Wilk, D'Agostino-Pearson), homogeneity (Levene's), automatic test recommendation, Cohen's d with CI |
| `power_analysis.py` | `statistical-analysis/scripts/` | Sample size calculation | 5 study designs: two-group comparison, proportion, diagnostic accuracy, survival, correlation. Includes dropout adjustment. |
| `pub_style.py` | `figure-generation/scripts/` | Publication-quality matplotlib styling | Journal-specific color palettes (Nature, Lancet, JAMA, NEJM), colorblind-safe options, Arial font, 300+ DPI export |

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

MRP uses Claude Code's Agent tool to parallelize independent research tasks, with the main agent coordinating results.

### Auto-Parallel (no confirmation needed)

| Trigger | Parallel tasks |
|---|---|
| Literature synthesis with >=2 databases | One sub-agent per database, simultaneous search |
| Peer review simulation | 4 sub-agents as independent reviewers, parallel evaluation |

### User-Confirmed Parallel

| Trigger | Parallel tasks |
|---|---|
| Revision with independent reviewer comments | One sub-agent per reviewer's feedback |
| Protocol design needing multi-expert review | Statistics + methodology + AI expert agents |

### Merge Rules

- Sub-agent outputs are checked for numerical consistency before merging
- Conflicting modifications to the same section require main agent resolution
- If a sub-agent discovers it needs another agent's data, parallelism stops and shifts to sequential

---

## User Memory System

MRP remembers user preferences across sessions via `.mrp-user-profile.json` in the project directory.

### What Gets Remembered

| Category | Examples |
|---|---|
| **Profile** | Role (PI / PhD student / postdoc), department, institution, expertise level |
| **Research domains** | Urology, medical AI, oncology, epidemiology |
| **Familiar methods** | RCT, cohort, deep learning, survival analysis |
| **Unfamiliar methods** | Bayesian, mediation analysis (triggers extra explanations) |
| **Preferred journals** | Tracked with submission count per journal |
| **Tool preferences** | Python / R / SPSS / Stata, figure style (Nature / Lancet / JAMA) |
| **History** | Past projects, outcomes, common reviewer feedback patterns |

### How Memory is Used

| Skill | Memory usage |
|---|---|
| `journal-selection` | Prioritizes previously targeted journals |
| `data-analysis-planning` | Generates scripts in preferred language (Python/R) |
| `figure-generation` | Applies preferred figure style |
| `manuscript-writing` | Auto-loads journal template based on favorite journals |
| `peer-review-simulation` | Focuses on historically weak areas |
| `statistical-analysis` | Provides extra explanation for unfamiliar methods |

### First-Time Setup

On first use (no `.mrp-user-profile.json` found), MRP asks 5 quick questions about your role, research area, preferred journals, familiar methods, and analysis tool. You can answer or skip.

### Privacy

- Memory is stored locally only -- never uploaded to any service
- Delete `.mrp-user-profile.json` at any time to clear all memory
- Say "forget my [field]" to remove specific entries

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

On session start, MRP checks for `.mrp-state.json` and reports: "Last completed: [stage]. Next step: [skill]. Continue?"

---

## .docx and .xlsx Export

Most journals require Word format for submission. MRP generates submission-ready exports.

| File | Format | Purpose | Dependency |
|---|---|---|---|
| `manuscript.docx` | Word | Main submission file (Times New Roman 12pt, double-spaced, 2.54cm margins) | `python-docx` |
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
| `writing-plans` | `study-design` / `basic-study-design` / `ai-study-design` | Three specialized design skills by research domain |
| `test-driven-development` | `data-analysis-planning` | SAP = test plan; anti-p-hacking = anti-regression |
| `executing-plans` | `statistical-analysis` | Reproducible scripts = reproducible builds |
| `requesting-code-review` | `peer-review-simulation` | 4 reviewers replace code reviewers |
| `verification-before-completion` | `pre-submission-verification` | 6-gate system replaces CI/CD checks |
| `receiving-code-review` | `responding-to-reviewers` | Point-by-point response = code review response |
| `finishing-a-development-branch` | `journal-selection` + `cover-letter-writing` | Journal targeting replaces merge/deploy |
| `writing-skills` | `writing-mrp-skills` | Same meta-skill for extensibility |
| -- | `literature-synthesis` | No software equivalent; research requires evidence review |
| -- | `reporting-standards` | No software equivalent; ~42 domain-specific compliance standards |
| -- | `research-ethics` | No software equivalent; IRB/IACUC requirements |

---

## Project Structure

```
med-research-powers/
|-- .claude-plugin/
|   +-- plugin.json                    # Plugin metadata (v6.1.0, 24 commands)
|-- hooks/
|   +-- session-start.sh              # Auto-injects routing table on session start
|-- commands/                          # 24 slash command definitions
|   +-- *.md
|-- skills/                            # 24 skill definitions
|   |-- */SKILL.md                     # Skill logic (triggers, workflow, output)
|   |-- */scripts/                     # Bundled Python scripts
|   +-- */references/                  # On-demand reference data (YAML/MD)
|       |-- journal-templates.yaml     # 68 journal formatting templates
|       |-- standards-index.yaml       # ~42 reporting standards index
|       |-- stat-method-decision-tree.yaml  # Statistical method selection
|       |-- consort-2025.yaml          # Full 30-item CONSORT 2025 checklist
|       |-- metrics-and-reporting.yaml # AI study metrics + reporting mapping
|       +-- experiment-templates/      # WB, qPCR, animal study (ARRIVE 2.0)
|-- docs/
|   +-- architecture.md               # Mermaid architecture diagrams
|-- examples/
|   +-- showcase/                      # Real pipeline output examples
|-- install.sh                         # Interactive installer
|-- CONTRIBUTING.md
|-- CHANGELOG.md
+-- LICENSE (MIT)
```

---

## Applicable Research Types

| Domain | Study Types |
|---|---|
| **Clinical** | RCT, cohort, case-control, cross-sectional, diagnostic accuracy |
| **AI/ML** | Medical imaging AI, surgical video AI, LLM/VLM evaluation, prediction models, clinical NLP, wearable/sensor AI |
| **Basic Science** | Cell biology, animal models, molecular biology, histopathology, Western blot, qPCR |
| **Evidence Synthesis** | Narrative review, systematic review, meta-analysis, scoping review, mini-review |
| **Omics** | Metabolomics, proteomics, genomics, multi-omics integration |
| **Devices** | Smart instruments, wearables, human factors, sensor systems, IDEAL framework staging |
| **Evidence Synthesis** | Systematic reviews, meta-analysis, network meta-analysis, scoping reviews, narrative reviews, clinical guidelines |
| **Other** | Medical education, quality improvement, case reports, health economics |

---

## Showcase

See real pipeline artifacts in [`examples/showcase/`](examples/showcase/) -- complete outputs from running MRP on actual research projects, including research questions, analysis plans, manuscripts, review reports, and submission readiness checks.

*Contributions welcome -- run the pipeline on your research and submit a PR.*

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

**Ways to contribute:**

- **New skills** -- Read `skills/writing-mrp-skills/SKILL.md` for the authoring guide, create a skill in `skills/`, and submit a PR
- **Specialty packs** -- Journal configs, MeSH terms, assessment tools for your specialty (place in `packs/your-specialty/`)
- **Reporting standards** -- Add or update checklists in `reporting-standards/references/checklists/`
- **Journal templates** -- Add entries to `journal-templates.yaml` following the existing structure
- **Bug reports** -- File issues for skills that should trigger but don't, incorrect checklist items, or script errors

PR descriptions should include: what problem the contribution solves, what Claude gets wrong without it, and how it improves with it.

---

## License

[MIT](LICENSE)

---

## Acknowledgments

- [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent -- the software engineering methodology framework that inspired this project
- [EQUATOR Network](https://www.equator-network.org/) -- the authoritative source for reporting guidelines
- [PubMed MCP](https://github.com/anthropics/claude-code) -- enabling automated literature verification
