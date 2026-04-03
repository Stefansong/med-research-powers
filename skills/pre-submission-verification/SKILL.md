---
name: pre-submission-verification
description: Use when a manuscript is declared complete or ready for submission. Triggers on "写完了"、"可以投了"、"定稿"、"差不多了"、"投稿"、"submission"、"cover letter". Also auto-triggers when manuscript-writing completes. MANDATORY — cannot be skipped.
---

# Pre-Submission Verification

## Overview

投稿前的强制安全门。如同手术前的 checklist，不通过就不能上台。

## When to Use

- 用户声称论文"完成"或"准备投稿"时 → **自动触发**
- manuscript-writing skill 宣布完成时 → **自动触发**
- 用户要求生成 Cover Letter 时 → **自动触发**
- 用户直接调用 `/mrp:check-standards` 时

## When NOT to Use

- 论文仍在起草阶段（各章节未完成）
- 纯粹的写作修改（措辞调整、语法修正）

## Workflow: 6-Gate Verification

**全部通过才能投稿。任何 Gate 失败 → 阻止投稿 → 列出修改项。**

### Gate 1: 报告规范合规

调用 `reporting-standards` skill：
- 确定研究类型 → 选择对应规范
- 逐条检查（✅ / ⚠️ / ❌）
- **合格标准：0 个 ❌ Critical 项**

### Gate 2: 统计完整性

- [ ] 所有主要结局报告了效应量 + 95% CI（不只 p 值）
- [ ] p 值报告精确值（不只 p < 0.05）
- [ ] 多重比较已做校正（Bonferroni / Holm / FDR），且在 Methods 和 Results 中明确说明
- [ ] 敏感性分析已完成并报告（缺失数据假设、异常值影响、替代分析方法）
- [ ] 样本量计算依据已写入 Methods（先验计算，非事后）
- [ ] 统计软件及版本已标注
- [ ] 完整的分析脚本（Python/R）已生成，包含版本、随机种子、参数注释
- [ ] 脚本输出数字与论文 Results 逐项核对一致
- [ ] 与 SAP 的任何偏差已在 Methods 中说明理由
- [ ] 探索性分析已明确标注为"exploratory"，与预定分析区分

### Gate 3: Claim Verification（内容真实性验证）

**验证论文中的每个事实断言都有数据支撑，防止 AI 幻觉和数据不一致。**

Phase A — 参考文献真实性（**优先使用 PubMed MCP 自动验证**）：
- [ ] 每篇引用的文献确实存在 → 用 PubMed MCP `search_articles` 或 `get_article_metadata` 验证 PMID/DOI
- [ ] 引用的结论与原文一致 → 用 PubMed MCP `get_full_text_article` 交叉核对关键结论
- [ ] 无编造的文献 → PubMed MCP 查无结果的引用标记为 ❌ SUSPICIOUS
- [ ] 用 `convert_article_ids` 统一 PMID/DOI 格式，确保引用一致性

Phase B — 数据一致性：
- [ ] Abstract 中的数字与 Results 一致
- [ ] 正文中的数字与 Tables/Figures 一致
- [ ] Results 中的数字与 `results-summary.md` 一致
- [ ] 同一数据在不同位置引用时数值相同

Phase C — Claims-Evidence 对应：
- [ ] 每个 "我们发现..."/"结果表明..." 断言都有对应的统计结果
- [ ] Conclusion 中的每个结论都有 Results 支撑
- [ ] 没有过度推断（如观察性研究推因果）

Phase D — 方法-结果匹配：
- [ ] Methods 中描述的每个分析在 Results 中都有结果
- [ ] Results 中没有 Methods 未描述的分析（后加的需标注）
- [ ] SAP 中预定的分析与实际报告的分析一致，偏差已说明

Phase E — 预定 vs 探索性分析区分：
- [ ] Methods 明确区分"预定分析"和"探索性分析"
- [ ] 每个探索性结论标注为 "exploratory"
- [ ] 未预先计划的"显著"结果未作为主要结论呈现

Phase F — AI 生成内容标记：
- [ ] 检查是否有典型的 AI 幻觉模式（过于对称的数据、编造的 p 值、不存在的引用）
- [ ] 确认所有数据来自实际分析，非 AI 生成

### Gate 4: 图表质量

- [ ] 字体 Arial / Helvetica
- [ ] 最小字号 ≥ 6pt（缩放后）
- [ ] 分辨率 ≥ 300 DPI（线条图 ≥ 600 DPI）
- [ ] 所有坐标轴有标签和单位
- [ ] 图例清晰完整
- [ ] 色盲友好配色
- [ ] 每张图有对应的 Figure Legend

### Gate 5: 伦理与合规

调用 `research-ethics` skill：
- [ ] 伦理审查批准号已写入 Methods
- [ ] 知情同意声明或豁免说明
- [ ] 利益冲突声明
- [ ] 资金来源声明
- [ ] 数据可用性声明
- [ ] 临床试验注册号（如适用）

### Gate 6: 形式检查

- [ ] 正文字数在目标期刊限制内
- [ ] 摘要字数在限制内
- [ ] 参考文献数量在限制内
- [ ] Running title / Short title ≤ 50 字符
- [ ] 关键词 3-6 个
- [ ] 所有缩写首次出现已展开
- [ ] 作者信息完整（单位、通讯作者、ORCID）
- [ ] 页码连续

## Output

生成 `submission-readiness-report.md`：

```markdown
# Submission Readiness Report

**Target Journal:** [期刊名]
**Date:** [日期]
**Overall Status:** ✅ READY / ❌ NOT READY

| Gate | Status | Critical Issues | Action Items |
|------|--------|----------------|--------------|
| 1. Reporting standards | ✅/❌ | [数量] | [列表] |
| 2. Statistical completeness | ✅/❌ | [数量] | [列表] |
| 3. Claim verification | ✅/❌ | [数量] | [列表] |
| 4. Figure quality | ✅/❌ | [数量] | [列表] |
| 5. Ethics compliance | ✅/❌ | [数量] | [列表] |
| 6. Formal requirements | ✅/❌ | [数量] | [列表] |

## Fix List (Priority Order)
1. [最紧急]
2. [次紧急]
...
```

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "报告规范以后再查" | 投稿后补改成本是现在的 10 倍 |
| "审稿人不会在意格式" | 格式不合规直接 desk reject |
| "效应量不重要，p 值够了" | 越来越多期刊强制要求效应量 |
| "伦理声明可以用模板" | 必须有真实的批准号 |
| "图表可以后期再改" | 审稿人看图表决定第一印象 |
| "AI 写的内容我看过了没问题" | 必须逐条验证引用真实性和数据一致性（Gate 3）|
| "数据在 Results 和 Abstract 里一样的" | 经常不一样——手动核对或让 Gate 3 检查 |

## Convergence

当且仅当 6 个 Gate 全部 ✅ 时，宣布论文可以投稿。

**Gate 3 (Claim Verification) 特别重要**：发现编造的参考文献或数据不一致是学术不端红线，必须彻底修复后重新验证。

## Red Flags — STOP

- 用户要求跳过某个 Gate → 拒绝，解释为什么每个 Gate 都是必要的
- 没有伦理批准号但要投稿 → 阻止，要求用户先获得批准
- 使用了 CONSORT 2010 → 提醒必须用 CONSORT 2025

## 衔接规则

### 前置依赖
- **必须**有完成的论文（`manuscript-writing`）

### 被动触发
- `manuscript-writing` 完成后 → 自动触发
- 用户说"写完了/可以投了/定稿" → 自动触发

### 强制衔接
- Gate 失败涉及统计 → 回 `statistical-analysis`
- Gate 失败涉及图表 → 回 `figure-generation`
- Gate 失败涉及伦理 → 回 `research-ethics`
- 全部通过 → 可以进入投稿流程
