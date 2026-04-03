# AI Medical Study Design

Invoke the `ai-medical-study-design` skill for AI/ML medical research.

## Scope
Medical imaging AI, clinical NLP, LLM/VLM evaluation, surgical video AI, wearable/sensor AI, prediction models, device innovation.

## Workflow
1. Define AI task type (classification / segmentation / detection / prediction / NLP / LLM eval)
2. Select reporting standard (TRIPOD+AI / CLAIM / DECIDE-AI / TRIPOD-LLM / MVAL)
3. Dataset design:
   - Training / validation / test split (patient-level, NOT image-level)
   - External validation cohort (strongly recommended)
   - Temporal validation (if applicable)
4. Metrics selection → load `references/metrics-and-reporting.yaml`:
   - Performance: AUROC, AUPRC, sensitivity, specificity, Dice, mAP
   - Calibration: ECE, MCE, reliability diagram
   - Fairness: demographic parity, equalized odds, subgroup AUROC
   - Robustness: cross-site, temporal, domain shift analysis
5. Baseline comparison (human expert + existing methods)
6. Clinical utility: Decision Curve Analysis (DCA)

## Key Rules
- Same patient CANNOT be in both training and test sets
- AUROC alone is insufficient — must include calibration + DCA
- Report performance stratified by demographics (sex, age, race)
- Aggregate accuracy hides disparities

## Output
AI research protocol + metrics checklist.
