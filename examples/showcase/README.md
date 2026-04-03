# Pipeline Showcase

Real artifacts from running the Med-Research-Powers pipeline on actual research projects.

## What's here

Each subdirectory contains the complete output of one pipeline run:

```
showcase/
├── README.md (this file)
└── vlm-benchmark-study/          ← Example: VLM surgical video evaluation
    ├── 01-research-question.md    ← PICO + FINER + hypothesis
    ├── 02-search-strategy.md      ← PubMed search strategy
    ├── 03-study-protocol.md       ← Study design (TRIPOD-LLM)
    ├── 04-analysis-plan.md        ← SAP with decision tree
    ├── 05-results-summary.md      ← Statistical results
    ├── 06-figures/                ← Publication-quality figures
    ├── 07-manuscript-draft.md     ← IMRaD manuscript
    ├── 08-reporting-checklist.md  ← TRIPOD-LLM compliance check
    ├── 09-peer-review-report.md   ← 4-reviewer simulation (incl. Devil's Advocate)
    ├── 10-submission-readiness.md ← 5-Gate + Claim Verification report
    └── 11-response-to-reviewers.md ← (after real review)
```

## How to contribute a showcase

Run the full MRP pipeline on your research, then copy all generated artifacts here:

1. Create a subdirectory named after your study
2. Number files in pipeline order (01-, 02-, ...)
3. Redact any patient data or unpublished results if needed
4. Submit a PR

## Why this matters

- Shows users what MRP actually produces (better than any documentation)
- Serves as regression test — if a pipeline run produces worse output than the showcase, something broke
- Demonstrates the mandatory pipeline: question → design → analysis → writing → verification
