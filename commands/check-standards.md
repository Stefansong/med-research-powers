# Check Reporting Standards

Invoke the `reporting-standards` skill AND `pre-submission-verification` skill.

**This command is MANDATORY before any manuscript submission. It cannot be skipped.**

## Workflow

### Step 1: Identify study type → select standard

| Study type | Primary standard |
|-----------|-----------------|
| RCT | CONSORT 2025 (30 items) |
| Observational | STROBE |
| Systematic review | PRISMA 2020 |
| Diagnostic accuracy | STARD 2015 |
| AI prediction model | TRIPOD+AI 2024 |
| LLM/VLM evaluation | TRIPOD-LLM 2024 |
| AI clinical evaluation | DECIDE-AI 2022 |
| Surgical innovation | IDEAL framework |
| Medical imaging AI | CLAIM 2020 |
| Animal study | ARRIVE 2.0 |

⚠️ **CONSORT 2010 is superseded. Always use CONSORT 2025.**

### Step 2: Check every item

For each checklist item, mark:
- ✅ Satisfied (note manuscript location)
- ⚠️ Partially satisfied (note what's missing)
- ❌ Not satisfied (provide fix recommendation)
- N/A with justification

### Step 3: Run 6-gate verification

| Gate | Check | Blocker? |
|------|-------|----------|
| 1. Reporting standards | 0 Critical ❌ items | YES |
| 2. Statistical completeness | Effect sizes + 95% CI for all outcomes | YES |
| 3. Claim verification | References real, data consistent, claims supported | YES |
| 4. Figure quality | Arial font, ≥300 DPI, axis labels, colorblind-safe | YES |
| 5. Ethics compliance | IRB number, consent statement, COI disclosure | YES |
| 6. Formal requirements | Word count, reference count, running title ≤50 chars | YES |

### Step 4: Generate report

Output `submission-readiness-report.md` with pass/fail for each gate.

**Any gate FAIL → block submission, list required fixes.**
