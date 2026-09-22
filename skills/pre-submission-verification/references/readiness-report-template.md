# Pre-Submission Verification — Readiness Report Template

Output file: `submission-readiness-report.md`

```markdown
# Submission Readiness Report

**Manuscript:** [题目]
**Target Journal:** [期刊名]（软确认，可更换）
**Date:** [日期]
**Overall Status:** ✅ READY FOR EXPORT / ❌ NOT READY
**User confirmation (hard checkpoint 3):** [pending / confirmed on <date> / auto-mode: not awaited]

| Gate | Status | Critical issues | Action Items |
|------|--------|-----------------|--------------|
| 1. Reporting standards (<standard>) | ✅/❌ | critical ❌ = [N]（非 critical ❌ [N]、⚠️ [N]） | [列表] |
| 2. Statistical completeness | ✅/❌ | [N] | [列表] |
| 3. Claim verification | ✅/❌ | [N] | [列表] |
| 4. Figure quality | ✅/❌ | [N] | [列表] |
| 5. Ethics compliance | ✅/❌ | [N] | [列表] |
| 6. Formal requirements | ✅/❌ | [N] | [列表] |

## Gate 3 Phase A — citation status

| Status | Count | Notes |
|--------|-------|-------|
| ✅ Verified | [N] | |
| ⚠️ Not found | [N] | [编号列表 → 作者提供原文或删除] |
| ❌ Mismatch | [N] | [编号 + 差异] |
| ⏳ Unverified (tool error) | [N] | [编号 → 待人工核对；不计为通过] |
| ℹ️ Non-PubMed | [N] | [编号 → DOI / WebSearch 核对结果] |

Key-citation content check (≤ 10): [N] checked, [N] consistent with source, [N] need rewording.

## Gate 6 — counts (Markdown manuscript)

| Item | Manuscript | Journal limit | OK? |
|------|-----------|---------------|-----|
| Body words (Intro–Discussion) | [N] | [N] | ✅/❌ |
| Abstract words | [N] | [N] | ✅/❌ |
| References | [N] | [N] | ✅/❌ |
| Figures / Tables | [N] / [N] | [N] / [N] | ✅/❌ |

## Fix List (Priority Order)
1. [最紧急 — Gate X, item, 回哪个 skill]
2. [次紧急]
...

## Next step
- All gates ✅ and confirmed → `manuscript-export`（生成 manuscript.docx + export-report.md）→ `submission-preparation`
- Any gate ❌ → 按 Fix List 回对应 skill，修复后重跑该 Gate
```
