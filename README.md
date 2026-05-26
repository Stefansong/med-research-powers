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
| **Peer Review** | 4-reviewer simulation with 0–100 quantitative scoring |
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

Four gates lock irreversible decisions and require **explicit** user approval — "no response" never counts as approval:

1. **`study-protocol.md`** — locks study type + primary outcome (changing the primary outcome later = outcome switching).
2. **`analysis-plan.md` (SAP)** — locks the analysis strategy (the core anti-p-hacking mechanism).
3. **`journal-selection-report.md`** — locks the target journal (drives format + specs downstream).
4. **`submission-readiness-report.md`** — all 6 gates must pass before submission.

### Fast-Track & backward links

- **Fast-Track Mode** — when you say "run it all the way through" / "don't ask me", MRP pauses only at the 4 hard checkpoints and auto-advances soft steps.
- **Backward links** — discovering a problem downstream (e.g. a reporting-standard failure during pre-submission) lets MRP route back to the upstream skill; revised artifacts are re-validated.

---

## The 20 Skills

### Pipeline skills

| # | Skill | Use it when… |
|---|-------|--------------|
| 1 | **research-question-formulation** | A vague idea needs a clear question + hypothesis (PICO/PIRD/FINER). |
| 2 | **literature-synthesis** | Searching & synthesizing literature; finding the research gap (PRISMA flow). |
| 3 | **study-design** | Designing any protocol — clinical / basic / AI-ML / qualitative / survey (Type A–E router). |
| 4 | **journal-selection** | Choosing a target journal (scored matching + 3-tier cascade strategy). |
| 5 | **data-analysis-planning** | Writing the SAP **before** any test runs (prerequisite for statistical-analysis). |
| 6 | **data-collection-tools** | Generating CRFs, annotation templates, REDCap forms, inference/eval scripts from the protocol. |
| 7 | **statistical-analysis** | Executing the analysis on real data (requires a completed SAP). |
| 8 | **figure-generation** | Producing publication-quality figures (journal styles, ≥300 DPI, colorblind-safe). |
| 9 | **manuscript-writing** | Drafting original research or a review (5 review types). |
| 10 | **manuscript-export** | Exporting Markdown → journal-formatted `.docx`. |
| 11 | **reporting-standards** | Matching the study type to the correct guideline & checking compliance. |
| 12 | **peer-review-simulation** | Simulating peer review (4 reviewers + 0–100 scoring) before submission. |
| 13 | **research-ethics** | Checking IRB/IACUC, consent, privacy, registration, COI; drafting the ethics statement. |
| 14 | **pre-submission-verification** | **MANDATORY** 6-gate final check — all gates must pass to submit. |
| 15 | **submission-preparation** | Writing the cover letter + submission-system guidance (ScholarOne / Editorial Manager). |
| 16 | **revision-response** | Planning the revision strategy + drafting the point-by-point rebuttal. |

### Support & meta skills

| # | Skill | Use it when… |
|---|-------|--------------|
| 17 | **pubmed-search** | Searching PubMed, verifying citations, or fetching metadata via the PubMed MCP. |
| 18 | **team-collaboration** | A project benefits from multi-agent parallel work (dispatched via the Task tool). |
| 19 | **using-med-research-powers** | The orchestrator — routing, checkpoints, pipeline state, user memory. |
| 20 | **writing-mrp-skills** | Creating, testing, or improving an MRP skill. |

---

## The 20 Slash Commands

Every skill is reachable in plain language; commands give you a direct entry point.

| Command | What it does |
|---------|--------------|
| `/mrp:research-question` | Turn a vague idea into a PICO question + hypothesis |
| `/mrp:literature-synthesis` | Systematic literature search & synthesis (PRISMA + gap map) |
| `/mrp:study-design` | Design a protocol for any study type (clinical/basic/AI/qualitative/survey) |
| `/mrp:journal-selection` | Choose the best target journal (scored matching + 3-tier cascade) |
| `/mrp:analyze-data` | Plan **then** run statistical analysis (planning → execution) |
| `/mrp:data-collection-tools` | Generate CRFs, annotation templates & scripts from the protocol |
| `/mrp:figure-generation` | Publication-quality figures (journal styles, ≥300 DPI, colorblind-safe) |
| `/mrp:write-manuscript` | Draft a medical research manuscript |
| `/mrp:manuscript-export` | Convert Markdown → journal-formatted `.docx` |
| `/mrp:reporting-standards` | Match study type to its reporting guideline |
| `/mrp:check-standards` | Reporting-guideline compliance check (Gate 1 of pre-submission) |
| `/mrp:pre-submission` | **MANDATORY** 6-gate pre-submission verification |
| `/mrp:peer-review` | Simulate peer review (4 reviewers + scoring) |
| `/mrp:research-ethics` | Check ethical compliance & draft the ethics statement |
| `/mrp:pubmed-search` | Search PubMed / verify citations / fetch metadata |
| `/mrp:submission-preparation` | Write the cover letter + submission-system guidance |
| `/mrp:revision-response` | Plan revision strategy + draft point-by-point responses |
| `/mrp:team-collaboration` | Run multi-agent parallel research tasks |
| `/mrp:using-mrp` | Orchestrator — routing rules, pipeline & checkpoints |
| `/mrp:writing-mrp-skills` | Create, test, or improve an MRP skill |

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

## Reporting Standards (42+)

The full, machine-readable index lives in [`skills/reporting-standards/references/checklists/standards-index.yaml`](skills/reporting-standards/references/checklists/standards-index.yaml), with a structured CONSORT 2025 checklist in [`consort-2025.yaml`](skills/reporting-standards/references/checklists/consort-2025.yaml).

Highlights: **CONSORT 2025** (31 numbered items / 34 rows) · **SPIRIT 2025** · **STROBE** · **PRISMA 2020** · **TRIPOD+AI 2024** · **DECIDE-AI** · **CLAIM 2020** · **IDEAL** · **ARRIVE 2.0** · **COREQ** · **SRQR** · **CHERRIES** · **STARD** · **CARE** · and more.

> CONSORT 2010 is officially superseded — MRP always routes to CONSORT 2025.

---

## Journal Templates (234)

Formatting requirements (word limits, abstract format, reference style, section structure, special boxes, cover-letter & ORCID requirements, submission system) for **234 journals across 30+ specialties** live in [`skills/manuscript-writing/references/journal-templates.yaml`](skills/manuscript-writing/references/journal-templates.yaml).

Specialties covered include general medicine, oncology, cardiology, GI/hepatology, respiratory, neurology, infectious disease, hematology, rheumatology, nephrology, endocrinology, psychiatry, surgery, urology, radiology, AI/digital health, pediatrics, OB/GYN, emergency/critical care, anesthesiology, orthopedics, ophthalmology, dermatology, pathology, ENT, public health, and more. If a journal isn't listed, MRP fetches its "Instructions for Authors" via web search.

---

## Statistical Analysis

- **Planning first**: `data-analysis-planning` produces a locked SAP; `statistical-analysis` cannot run without it.
- **Assumption-driven**: an [assumption-test decision tree](skills/data-analysis-planning/references/stat-method-decision-tree.yaml) auto-selects parametric vs non-parametric methods.
- **15+ method categories**: comparison of means, categorical, correlation/regression, survival, diagnostic accuracy, longitudinal/mixed models, multiplicity correction, omics, and AI/ML evaluation (AUROC/AUPRC, DeLong, calibration, DCA, bootstrap CIs).
- **Reproducible output**: every run produces a cleaning log, an analysis log, a results summary, and a reproducible script operating on `data_clean.csv`.

---

## Pre-Submission Verification (6 gates)

`pre-submission-verification` is mandatory and blocks submission until every gate passes:

1. **Gate 1 — Reporting standards** (correct guideline, all items mapped)
2. **Gate 2 — Statistics** (effect sizes, CIs, exact p-values, sensitivity analyses)
3. **Gate 3 — Claim verification** (every citation checked via the PubMed MCP)
4. **Gate 4 — Figure quality** (resolution, colorblind safety, legends)
5. **Gate 5 — Ethics & compliance** (IRB/consent/registration/COI)
6. **Gate 6 — Formal** (structure, word/reference limits, formatting)

---

## Peer-Review Simulation (4 reviewers)

`peer-review-simulation` dispatches a 4-reviewer panel and produces a 0–100 score calibrated to the target journal tier:

- **R1 — Methodologist** · **R2 — Clinical/Domain expert** · **R3 — Academic editor** · **R4 — Devil's Advocate**

Each reviewer scores 8 dimensions and flags issues by severity (Critical / Major / Minor), feeding directly into `revision-response`.

---

## Bundled Python Scripts

Reusable, callable code (not re-written from prompts each time):

| Script | Purpose |
|--------|---------|
| `statistical-analysis/scripts/assumption_tests.py` | Normality, variance, and full assumption checks; Cohen's d |
| `statistical-analysis/scripts/power_analysis.py` | Sample size / power for two-group, diagnostic, and survival designs |
| `statistical-analysis/scripts/analysis_template.py` | Reproducible analysis scaffold operating on `data_clean.csv` |
| `figure-generation/scripts/pub_style.py` | Journal figure styling, colorblind-safe palettes, significance bars |
| `manuscript-export/scripts/export_docx.py` | Markdown → journal-formatted `.docx`, driven by the journal template library |

---

## State Tracking & User Memory

MRP can persist project state and your preferences **locally** in the project directory:

- **`.mrp-state.json`** — pipeline progress, completed skills, artifacts, current stage. On a new session MRP offers to resume: *"Last completed: X. Next: Y. Continue?"*
- **`.mrp-user-profile.json`** — your role, research domains, favorite journals, familiar/unfamiliar methods, preferred stats tool & figure style. Built once via a short intro, then updated quietly.

Schemas: [`skills/using-med-research-powers/references/state-schemas.md`](skills/using-med-research-powers/references/state-schemas.md).

**Privacy:** these files are stored only in your local project directory and never uploaded. Delete them any time, or say "forget my [field]". MRP never records passwords, patient data, or ethics-approval numbers.

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
├── install.sh             interactive installer
├── README.md / README_CN.md
└── CHANGELOG.md
```

Each skill keeps reasoning in `SKILL.md` and pushes lookup tables, templates, and checklists into `references/`, and reusable code into `scripts/` — so context stays lean and content stays maintainable.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills follow the spec in `writing-mrp-skills`: a trigger-only `description` (≤200 chars), the standard section set (Overview, When to Use, When NOT to Use, Workflow, Output, Common Mistakes, Convergence, Red Flags, 衔接规则), lookup content in `references/`, and fixed code in `scripts/`.

---

## License & Credits

- **License:** MIT (see [LICENSE](LICENSE))
- **Author:** BTCH Uro AI Lab
- **Inspired by:** [Superpowers](https://github.com/obra/superpowers) by obra

*Med-Research-Powers enforces methodology; it does not replace your judgment, your IRB, or your statistician. Always confirm ethics status and verify analyses with a qualified expert.*
