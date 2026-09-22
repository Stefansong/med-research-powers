# Peer Review Simulation — Report Template

Output file: `peer-review-simulation-report.md`

Score → decision mapping and journal tiers come from `scoring-rubric.yaml`
(80-100 Accept/Minor · 65-79 Minor · 50-64 Major · 30-49 Major (risky) · 0-29 Reject).

```markdown
# Peer Review Simulation Report

**Target Journal:** [期刊名]（档位：综合顶刊 / 专科 Top / 主流 / 入门）
**Date:** [日期]
**Overall Score:** [加权平均分]/100
**Decision Prediction:** [Accept/Minor/Major/Reject]

## Scoring Matrix

| Dimension | R1 (Methods) | R2 (Clinical) | R3 (Editor) | R4 (Devil's Adv.) | Avg |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Originality | /100 | /100 | /100 | /100 | /100 |
| Methodology | /100 | /100 | /100 | /100 | /100 |
| Results | /100 | /100 | /100 | /100 | /100 |
| Clinical Impact | /100 | /100 | /100 | /100 | /100 |
| Writing Quality | /100 | /100 | /100 | /100 | /100 |
| Figures & Tables | /100 | /100 | /100 | /100 | /100 |
| References | /100 | /100 | /100 | /100 | /100 |
| Reproducibility | /100 | /100 | /100 | /100 | /100 |
| **Weighted Total** | **X** | **X** | **X** | **X** | **X** |
| **Recommendation** | Accept/Minor/Major/Reject | Accept/Minor/Major/Reject | Accept/Minor/Major/Reject | Accept/Minor/Major/Reject | — |

## Reviewer 1 — Methodologist
**Recommendation:** Accept / Minor / Major / Reject
### Critical Issues
1. [问题 + 修改建议]
### Major Issues
...
### Minor Issues
...

## Reviewer 2 — Clinical Expert
**Recommendation:** Accept / Minor / Major / Reject
...

## Reviewer 3 — Editor
**Recommendation:** Accept / Minor / Major / Reject
...

## Reviewer 4 — Devil's Advocate
**Recommendation:** Accept / Minor / Major / Reject
### Key Challenges
1. [最强的反面论点 + 建议的防御策略]
2. [最弱的方法学环节 + 加强建议]
3. [最可能被质疑的结论 + 证据补强方案]

## Editor Summary
**Editor's Recommendation:** [Accept/Minor/Major/Reject]
**Rationale:** [综合判断，不是简单平均——说明为什么；≥1 个 Critical → 至少 Major；≥2 位建议 Reject → Reject]
**Predicted Review Rounds:** [1轮/2轮/Reject]
**Raw Score:** [未校准分数]/100
**Calibrated Score (for [期刊名], [档位]):** [校准后分数]/100
**Calibration note:** [期刊名] 属于 [档位]，审稿标准 [高于/等于/低于] 平均水平

## Priority Fix List
1. [最紧急] (Critical, from R1)
2. [次紧急] (Critical, from R4)
...

## Weakest Dimensions (lowest scores)
1. [维度名]: [平均分]/100 — [改进建议]
2. [维度名]: [平均分]/100 — [改进建议]

## Next step
- 0 Critical → `pre-submission-verification`（6-Gate 检查）
- ≥1 Critical → 回对应 skill 修复后再跑一次本 skill
```
