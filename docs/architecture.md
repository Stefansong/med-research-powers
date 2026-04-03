# Med-Research-Powers v6.0.0 Architecture

## 1. Full Pipeline Flow

```mermaid
flowchart TD
    START([User: Research Idea]) --> RQ

    subgraph PHASE1["Phase 1: Research Foundation"]
        RQ[research-question-formulation<br/>PICO + FINER + Hypothesis]
        LS[literature-synthesis<br/>Multi-DB Search + PRISMA Screening]
        SD{Study Type?}
        SD_C[study-design<br/>Clinical: RCT/Cohort/Cross-sectional]
        SD_B[basic-medical-study-design<br/>Cell/Animal/Molecular]
        SD_A[ai-medical-study-design<br/>AI/ML/Imaging/NLP/LLM]
        JS[journal-selection<br/>4-Step Matching + 3-Tier Ranking]
    end

    subgraph PHASE2["Phase 2: Analysis Engine"]
        DAP[data-analysis-planning<br/>SAP: 7-Section Analysis Plan]
        SA[statistical-analysis<br/>Data Cleaning + Execution + Scripts]
        FG[figure-generation<br/>pub_style.py + Journal Palettes]
    end

    subgraph PHASE3["Phase 3: Manuscript & QA"]
        MW[manuscript-writing<br/>IMRaD + Journal Templates 40+]
        RS[reporting-standards<br/>~45 Standards Matching]
        RE[research-ethics<br/>IRB / IACUC / Privacy]
        PRS[peer-review-simulation<br/>4 Reviewers + Editor Summary]
        PSV[pre-submission-verification<br/>6-Gate Mandatory Check]
    end

    subgraph PHASE4["Phase 4: Submission & Revision"]
        CL[cover-letter-writing<br/>4-Paragraph + Journal Fit]
        SSG[submission-system-guide<br/>ScholarOne/Editorial Manager]
        SUB([Submit to Journal])
        RVS[revision-strategy<br/>Comment Triage + Priority Matrix]
        RTR[responding-to-reviewers<br/>Response Letter]
    end

    RQ -->|research-question.md| LS
    LS -->|literature-synthesis-summary.md<br/>screening-log.md| SD
    SD -->|Clinical| SD_C
    SD -->|Basic Science| SD_B
    SD -->|AI/ML| SD_A
    SD_C -->|study-protocol.md| HC1
    SD_B -->|study-protocol.md| HC1
    SD_A -->|study-protocol.md| HC1

    HC1{{"HC #1: Protocol Approval<br/>Research type + Primary outcome LOCKED"}}
    HC1 --> JS
    JS -->|journal-selection-report.md| HC2
    HC2{{"HC #3: Journal Confirmed<br/>Format specs locked"}}
    HC2 --> DAP
    DAP -->|analysis-plan.md| HC3
    HC3{{"HC #2: SAP Approved<br/>Anti p-hacking lock"}}
    HC3 --> SA
    SA -->|results-summary.md<br/>analysis_script.py<br/>data-cleaning-log.md| FG
    FG -->|figures/*.tiff| MW

    RS -.->|checklist| MW
    RE -.->|reminder| MW

    MW -->|manuscript.md| PRS
    PRS -->|peer-review-report.md| PSV
    PSV -->|submission-readiness-report.md| HC4
    HC4{{"HC #4: 6-Gate ALL PASS<br/>Must confirm to proceed"}}
    HC4 --> CL
    CL -->|cover-letter.md| SSG
    SSG --> SUB
    SUB -->|Major/Minor Revision| RVS
    RVS -->|revision-plan.md| RTR
    RTR -->|response-letter.md| PSV2[Re-verify & Resubmit]

    SUB -->|Reject| RESUBMIT[Reformat & Resubmit]
    RESUBMIT --> JS

    style HC1 fill:#ff6b6b,stroke:#c0392b,color:#fff
    style HC2 fill:#ff6b6b,stroke:#c0392b,color:#fff
    style HC3 fill:#ff6b6b,stroke:#c0392b,color:#fff
    style HC4 fill:#ff6b6b,stroke:#c0392b,color:#fff
    style PSV fill:#e74c3c,stroke:#c0392b,color:#fff
    style PHASE1 fill:#eaf4fc,stroke:#3498db
    style PHASE2 fill:#eafcef,stroke:#27ae60
    style PHASE3 fill:#fef9e7,stroke:#f39c12
    style PHASE4 fill:#fdeef4,stroke:#e91e63
```

## 2. 6-Gate Pre-Submission Verification

```mermaid
flowchart LR
    subgraph GATE["6-Gate Verification (ALL must pass)"]
        G1[Gate 1<br/>Reporting Standards<br/>CONSORT/STROBE/PRISMA...]
        G2[Gate 2<br/>Statistical Completeness<br/>Effect Size + CI + Scripts]
        G3[Gate 3<br/>Claim Verification<br/>PubMed MCP Auto-Check]
        G4[Gate 4<br/>Figure Quality<br/>DPI + Font + Colorblind]
        G5[Gate 5<br/>Ethics Compliance<br/>IRB + Consent + COI]
        G6[Gate 6<br/>Formal Requirements<br/>Word Count + References]
    end

    G1 --> G2 --> G3 --> G4 --> G5 --> G6
    G6 -->|ALL PASS| READY([READY TO SUBMIT])
    G1 -->|FAIL| FIX1[Back to manuscript-writing]
    G2 -->|FAIL| FIX2[Back to statistical-analysis]
    G3 -->|FAIL| FIX3[Verify references via PubMed MCP]
    G4 -->|FAIL| FIX4[Back to figure-generation]
    G5 -->|FAIL| FIX5[Back to research-ethics]
    G6 -->|FAIL| FIX6[Adjust formatting]

    style READY fill:#27ae60,color:#fff
    style G3 fill:#3498db,color:#fff
```

## 3. Peer Review Simulation

```mermaid
flowchart TD
    MS([Manuscript]) --> R1 & R2 & R3 & R4

    R1["Reviewer 1<br/>Methodologist<br/>Design, Stats, Bias"]
    R2["Reviewer 2<br/>Clinical Expert<br/>Significance, Applicability"]
    R3["Reviewer 3<br/>Academic Editor<br/>Structure, Language, Fit"]
    R4["Reviewer 4<br/>Devil's Advocate<br/>Challenge + Blind Spots"]

    R1 & R2 & R3 & R4 --> SCORE["8-Dimension Scoring<br/>(0-100 per dimension)"]
    SCORE --> ES["Editor Summary<br/>(NOT simple average)"]
    ES --> CAL["Journal Calibration<br/>(adjust by target IF)"]

    CAL --> D1["80-100: Accept/Minor"]
    CAL --> D2["65-79: Minor Revision"]
    CAL --> D3["50-64: Major Revision"]
    CAL --> D4["<50: Reject"]

    style R4 fill:#e74c3c,color:#fff
    style ES fill:#2c3e50,color:#fff
```

## 4. Literature Synthesis: Multi-Database Search

```mermaid
flowchart TD
    PICO([PICO Keywords]) --> STRATEGY[Search Strategy]

    STRATEGY --> DB1 & DB2 & DB3 & DB4 & DB5

    DB1["PubMed<br/>(PubMed MCP)<br/>7 functions"]
    DB2["arXiv<br/>(WebSearch)<br/>AI/ML papers"]
    DB3["Cochrane<br/>(WebSearch)<br/>Systematic reviews"]
    DB4["IEEE / ACM<br/>(WebSearch)<br/>Engineering/CS"]
    DB5["medRxiv / bioRxiv<br/>(WebSearch)<br/>Preprints"]

    DB1 & DB2 & DB3 & DB4 & DB5 --> DEDUP[Deduplication]
    DEDUP --> SCREEN1["Title/Abstract Screening<br/>(get_article_metadata)"]
    SCREEN1 --> SCREEN2["Full-Text Screening<br/>(get_full_text_article)"]
    SCREEN2 --> SNOW["Snowball Search<br/>(find_related_articles)"]
    SNOW --> INCLUDED[Included Studies]

    INCLUDED --> OUT1[search-strategy.md]
    INCLUDED --> OUT2[screening-log.md<br/>PRISMA Flow Data]
    INCLUDED --> OUT3[literature-references.md<br/>Structured Records]
    INCLUDED --> OUT4[literature-synthesis-summary.md<br/>Known/Unknown/Controversial]

    style DB1 fill:#3498db,color:#fff
    style DB2 fill:#e67e22,color:#fff
    style DB3 fill:#2ecc71,color:#fff
    style DB4 fill:#9b59b6,color:#fff
    style DB5 fill:#1abc9c,color:#fff
```

## 5. Statistical Analysis Data Flow

```mermaid
flowchart TD
    DATA[(data.csv)] --> LOAD[Step 1: Load & Explore]
    LOAD --> CLEAN[Step 2: Data Cleaning]

    subgraph CLEANING["Data Cleaning"]
        C1[2.1 Missing Data<br/>MCAR/MAR/MNAR Assessment]
        C2[2.2 Outlier Detection<br/>Z-score / IQR / Clinical Range]
        C3[2.3 Type Validation<br/>Encoding + Variable Matching]
        C4[2.4 Export Clean Data]
    end

    CLEAN --> C1 --> C2 --> C3 --> C4
    C4 --> CLEAN_DATA[(data_clean.csv)]
    C4 --> LOG1[data-cleaning-log.md]

    CLEAN_DATA --> ASSUME[Step 3: Assumption Tests<br/>assumption_tests.py]
    ASSUME --> TREE{stat-method-decision-tree.yaml}

    TREE --> EXEC[Step 4: Execute Analysis<br/>Per analysis-plan.md]

    subgraph METHODS["Available Methods (v6)"]
        M1[Two-Group / Multi-Group]
        M2[Survival + Competing Risks]
        M3[Mixed Models / GEE]
        M4[Propensity Score]
        M5[Multiple Imputation]
        M6[Mediation Analysis]
        M7[Omics / High-Dimensional]
        M8[Interrupted Time Series]
        M9[Interaction / Subgroup]
    end

    EXEC --> M1 & M2 & M3 & M4 & M5 & M6 & M7 & M8 & M9

    EXEC --> SCRIPT[analysis_script.py<br/>Reproducible Code]
    EXEC --> LOG2[analysis-log.md<br/>Decisions + SAP Deviations]
    EXEC --> RESULTS[results-summary.md<br/>Tables + Key Numbers]

    RESULTS --> FIG[figure-generation]
    RESULTS --> MANUSCRIPT[manuscript-writing]

    style CLEANING fill:#fff3cd,stroke:#ffc107
    style METHODS fill:#d1ecf1,stroke:#0dcaf0
```

## 6. Checkpoint Protocol

```mermaid
flowchart TD
    subgraph SOFT["Soft Checkpoint (report + ask)"]
        S1["research-question<br/>Report PICO + confirm"]
        S2["literature-synthesis<br/>Report gap + confirm"]
        S3["statistical-analysis<br/>Report results + confirm"]
        S4["figure-generation<br/>Report figures + confirm"]
        S5["manuscript-writing<br/>Report sections + confirm"]
        S6["peer-review-simulation<br/>Report scores + confirm"]
        S7["cover-letter-writing<br/>Report draft + confirm"]
        S8["submission-system-guide<br/>Report checklist + confirm"]
    end

    subgraph HARD["Hard Checkpoint (MUST confirm, locks content)"]
        H1["HC #1: study-protocol.md<br/>Locks: research type,<br/>primary outcome"]
        H2["HC #2: analysis-plan.md<br/>Locks: statistical methods,<br/>anti p-hacking"]
        H3["HC #3: journal-selection<br/>Locks: target journal,<br/>format specs"]
        H4["HC #4: 6-Gate verification<br/>ALL gates must pass<br/>to proceed"]
    end

    S1 --> S2 --> H1
    H1 --> H3 --> H2
    H2 --> S3 --> S4 --> S5 --> S6 --> H4
    H4 --> S7 --> S8

    style HARD fill:#ffe0e0,stroke:#e74c3c
    style SOFT fill:#e0f0ff,stroke:#3498db
    style H1 fill:#ff6b6b,color:#fff
    style H2 fill:#ff6b6b,color:#fff
    style H3 fill:#ff6b6b,color:#fff
    style H4 fill:#ff6b6b,color:#fff
```

## 7. Plugin Architecture

```mermaid
flowchart TD
    subgraph PLUGIN["med-research-powers (Plugin)"]
        PJ[".claude-plugin/plugin.json<br/>v6.0.0 | 5 commands registered"]
        HOOK["hooks/session-start.sh<br/>Injects routing table on startup"]
        META["skills/using-med-research-powers<br/>Orchestrator: 1% Rule + Checkpoints"]
    end

    subgraph COMMANDS["Slash Commands (/mrp:*)"]
        CMD1["/mrp:research-question"]
        CMD2["/mrp:analyze-data"]
        CMD3["/mrp:write-manuscript"]
        CMD4["/mrp:check-standards"]
        CMD5["/mrp:peer-review"]
    end

    subgraph SKILLS["20 Skills"]
        SK_F["Foundation (6)<br/>research-question, literature-synthesis,<br/>study-design, basic-study, ai-study,<br/>journal-selection"]
        SK_A["Analysis (3)<br/>data-analysis-planning,<br/>statistical-analysis,<br/>figure-generation"]
        SK_M["Manuscript & QA (5)<br/>manuscript-writing, reporting-standards,<br/>research-ethics, peer-review-simulation,<br/>pre-submission-verification"]
        SK_S["Submission (4)<br/>cover-letter-writing,<br/>submission-system-guide,<br/>revision-strategy,<br/>responding-to-reviewers"]
        SK_X["Meta (2)<br/>using-med-research-powers,<br/>writing-mrp-skills"]
    end

    subgraph SCRIPTS["Python Scripts"]
        PY1["assumption_tests.py<br/>Normality + Homogeneity + Cohen's d (CI)"]
        PY2["power_analysis.py<br/>5 designs: t-test, proportion,<br/>diagnostic, survival, correlation"]
        PY3["pub_style.py<br/>Journal palettes: Nature, Lancet,<br/>JAMA, NEJM + Colorblind safe"]
    end

    subgraph REFS["Reference Data"]
        R1["stat-method-decision-tree.yaml<br/>15+ method categories"]
        R2["standards-index.yaml<br/>~45 reporting standards"]
        R3["consort-2025.yaml<br/>30-item checklist"]
        R4["journal-templates.yaml<br/>40+ journals, 16 specialties"]
        R5["metrics-and-reporting.yaml<br/>AI metrics + fairness + robustness"]
        R6["Experiment templates<br/>WB, qPCR, Animal (ARRIVE 2.0)"]
    end

    subgraph STATE["State Management"]
        ST1[".mrp-state.json<br/>Session persistence"]
        ST2["Artifact versioning<br/>Track changes across skills"]
    end

    PJ --> HOOK
    HOOK --> META
    META --> SKILLS
    COMMANDS --> SKILLS
    SKILLS --> SCRIPTS
    SKILLS --> REFS
    SKILLS --> STATE

    style PLUGIN fill:#2c3e50,color:#fff
    style COMMANDS fill:#8e44ad,color:#fff
    style SCRIPTS fill:#27ae60,color:#fff
    style REFS fill:#2980b9,color:#fff
    style STATE fill:#d35400,color:#fff
```

## 8. Reporting Standards Coverage Map

```mermaid
mindmap
  root(("~45 Reporting<br/>Standards"))
    Clinical Trials
      CONSORT 2025
      CONSORT-AI
      CONSORT-Cluster
      SPIRIT 2025
      SPIRIT-AI
      TIDieR
      CONSORT-Harms
    Observational
      STROBE
      RECORD
      STROCSS
    Systematic Reviews
      PRISMA 2020
      PRISMA-P
      PRISMA-ScR
      PRISMA-S
      PRISMA-DTA
      PRISMA-NMA
      TRIPOD-SRMA
      AMSTAR 2
      GRADE
    Guidelines
      AGREE II
    Obs Meta-Analysis
      MOOSE
    Diagnostic
      STARD 2015
    AI & Prediction
      TRIPOD+AI 2024
      TRIPOD-LLM
      TRIPOD-Cluster
      CLAIM
      MI-CLAIM
      DECIDE-AI
      PROBAST
    Surgery
      IDEAL
      MVAL
    Qualitative
      COREQ
      SRQR
    Other
      ARRIVE 2.0
      CARE
      SQUIRE
      CHEERS
    Bias Tools
      RoB 2
      ROBINS-I
      NOS
      MINORS
      QUADAS-2
```
