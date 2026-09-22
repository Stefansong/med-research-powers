---
name: pre-submission-verification
description: Use when a manuscript is declared complete and must pass the 6-gate check before export (mandatory checkpoint 3). Triggers on "写完了"、"可以投了"、"定稿"、"六道门"、"pre-submission"、"readiness".
---

# Pre-Submission Verification

## Overview

投稿前的强制检查点（硬确认 3）。如同手术前的 checklist：6 个 Gate 全部通过、用户确认
`submission-readiness-report.md` 后，才进入 `manuscript-export` 生成 .docx。

## When to Use

- `peer-review-simulation` 完成、Critical/Major 问题修完后 → **自动进入**（主线下一步）
- 用户声称论文"写完了 / 可以投了 / 定稿" → 自动触发
- 用户直接调用 `/mrp:pre-submission`
- `revision-response` 修改完成后 → 再次触发（修回稿同样要过 6 Gate）

## When NOT to Use

- 论文仍在起草阶段（各章节未完成）→ 先 `manuscript-writing`
- 纯粹的写作修改（措辞调整、语法修正）
- 只想查报告规范 → `/mrp:check-standards`（= 本 skill 的 Gate 1 内容）
- 还没做模拟审稿 → 先 `peer-review-simulation`（顺序：审稿模拟 → 本 skill → 导出）

## Workflow: 6-Gate Verification

**全部通过才能进入导出与投稿。任何 Gate 失败 → 列出修改项 → 回对应 skill → 修复后重跑该 Gate。**

六个 Gate 的逐条清单见 `references/gates-checklist.yaml`。逐 Gate 加载并核对，每条标 ✅ / ⚠️ / ❌ / N/A。
各 Gate 的输入、通过标准与失败去向：

| Gate | 内容 | 主要输入 | 通过标准 | 失败 → 回 |
|------|------|---------|---------|----------|
| 1 报告规范 | 调用 `reporting-standards`（有本地 checklist 的规范逐条查） | `reporting-compliance-report.md` | **0 个 critical ❌**（critical 由 checklist YAML 定义） | `manuscript-writing` → 重跑 `reporting-standards` |
| 2 统计完整性 | 效应量+95%CI、精确 p、多重比较、敏感性分析、先验样本量、脚本与 Results 一致、**与 SAP 的偏差已说明** | `analysis-plan.md`、`results-summary.md`、`analysis-log.md` | 各条 ✅ | `statistical-analysis` |
| 3 Claim Verification | A 引用真实性 / B 数据一致 / C 断言有据 / D 方法-结果匹配 / E 预定 vs 探索 / F AI 内容 | `manuscript/*.md`、`results-summary.md` | A 通过且 B–F ✅ | 引用 → 作者核对；数据 → `statistical-analysis` / `manuscript-writing` |
| 4 图表质量 | 字体、字号、DPI、坐标轴、色盲友好、legend、编号对应 | 图文件、`figure-legends.md` | 各条 ✅ | `figure-generation` |
| 5 伦理与合规 | 读取 `ethics-statement.md`，与稿件声明段逐项核对 | `ethics-statement.md`（无则先跑 `research-ethics`） | 各条 ✅ | `research-ethics` |
| 6 形式检查 | 在 **Markdown 稿**上数正文/摘要字数、引用数、图表数、running title、关键词、缩写、作者信息 | `manuscript/*.md`、`journal-selection-report.md` | 各条 ✅ | `manuscript-writing` |

### Gate 3 Phase A：引用验证怎么做

调用 `pubmed-search` 的 **Mode 3**（Citation Verification），不在本 skill 里重述其流程。要点：
有 PMID 用 `get_article_metadata`；有 DOI 用 `convert_article_ids` 转 PMID；只有作者+年份+期刊用
`lookup_article_by_citation`；引用 ≥ 10 条时分批（每批 ≤ 10 条），先查支撑主要结论的引用。
工具名写作 `mcp__<server名>__<函数>`，server 名以当前会话工具列表为准（claude.ai 连接器为
`claude_ai_PubMed`，本地常见为 `PubMed`）。

每条引用只用这 5 种状态：

| 状态 | 含义 | Gate 3 处理 |
|------|------|------------|
| ✅ Verified | 找到且标题/作者/年份相符 | 通过 |
| ⚠️ Not found | 查询成功但无命中 | 作者提供原文 PDF / DOI 页面，否则删除 |
| ❌ Mismatch | 找到但作者/年份/标题不符 | 按 PubMed 记录修正，或删除 |
| ⏳ Unverified (tool error) | 工具报错或连接失败 | **不等于不存在**；重试一次，仍失败则列为待人工核对，Gate 3 不能因此判通过 |
| ℹ️ Non-PubMed | 书籍、指南、arXiv 等 | 用 DOI / WebSearch 核对 |

支撑主要结论的关键引用（≤ 10 篇）还要核对"引用的结论与原文一致"：有 PMCID 时用
`get_full_text_article`，否则核对摘要。

### Gate 6：为什么在 Markdown 上查

主线顺序是 本 skill → `manuscript-export` → `submission-preparation`，所以检查时还没有 .docx。
用导出脚本的只报告模式统计，不生成 .docx：
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-export/scripts/export_docx.py --manuscript-dir manuscript --journal <期刊id> --report-only --report gate6-report.md`
（正文只算 Introduction–Discussion，不含题页、摘要、参考文献、图表说明；摘要与参考文献数单独列出；同时报告占位符与图表数）。期刊限制用
`${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --id <期刊id>` 取。
最终 .docx 与 `export-report.md` 由 `manuscript-export` 生成，其字数应与本 Gate 一致。

> 路由原则：Gate 失败时不要自行修补深层问题，而是路由回对应的专责 skill，修复后回到本 skill 重新验证。

### 收尾：硬确认 3 + 状态更新

1. 生成 `submission-readiness-report.md`（模板见 `references/readiness-report-template.md`）。
2. **等用户明确确认**报告（这是 3 个硬确认之一；用户说过"一直做到底"时只提示不等待，但要把结论写进报告）。
3. 更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：
   `completed_skills` 追加 pre-submission-verification 及产物、`next_step` 设为 manuscript-export）。
4. 6 Gate 全 ✅ → 进入 `manuscript-export`；否则按 Fix List 回对应 skill。

## Output

生成 `submission-readiness-report.md`：6 个 Gate 的状态表（✅/❌ + critical 数量 + Action Items）、
Gate 3 引用状态计数（5 态）、优先级修改清单、下一步。完整模板见 `references/readiness-report-template.md`。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "报告规范以后再查" | 投稿后补改成本是现在的 10 倍 |
| "审稿人不会在意格式" | 格式不合规直接 desk reject |
| "效应量不重要，p 值够了" | 越来越多期刊强制要求效应量 |
| "伦理声明可以用模板" | 必须有真实的批准号，且与 ethics-statement.md 一致 |
| "图表可以后期再改" | 审稿人看图表决定第一印象 |
| "AI 写的内容我看过了没问题" | 必须逐条验证引用真实性和数据一致性（Gate 3）|
| "数据在 Results 和 Abstract 里一样的" | 经常不一样——让 Gate 3 Phase B 逐个数字核对 |
| "PubMed 查不到就是假的" | 工具报错是 ⏳ Unverified，不是 ⚠️ Not found；非 PubMed 来源另查 |
| "先导出 .docx 再检查" | 顺序是先过 6 Gate 再导出，否则每次修改都要重导 |

## Convergence

当且仅当 6 个 Gate 全部 ✅、`submission-readiness-report.md` 已生成并获用户确认、`.mrp-state.json`
已更新时，宣布论文可以进入 `manuscript-export`。

**Gate 3 特别重要**：发现编造的参考文献或数据不一致是学术不端红线，必须彻底修复后重新验证。

## Red Flags — STOP

- 用户要求跳过某个 Gate → 拒绝，解释为什么每个 Gate 都是必要的
- 没有伦理批准号但要投稿 → 阻止，要求用户先获得批准
- 使用了 CONSORT 2010 → 提醒必须用 CONSORT 2025（30 项，含子项共 42 行）
- 有 ⏳ Unverified 的引用却想标为通过 → 停止，先重试或人工核对
- 想用"差不多"的字数估计代替计数 → 停止，按 Gate 6 的方法数

## 衔接规则

### 前置依赖
- **必须**有完成的论文（`manuscript/*.md`，来自 `manuscript-writing`）
- **必须**已做过 `peer-review-simulation` 且 Critical 问题已修复（`peer-review-simulation-report.md`）
- 推荐有：`analysis-plan.md`、`results-summary.md`、`ethics-statement.md`、`journal-selection-report.md`

### 强制衔接
- 前接 `peer-review-simulation`；后接 `manuscript-export`（生成 `manuscript.docx` + `export-report.md`）→ `submission-preparation`
- Gate 1 失败 → `manuscript-writing` 修改 → 重跑 `reporting-standards`
- Gate 2 失败 → `statistical-analysis`；Gate 4 失败 → `figure-generation`；Gate 5 失败 → `research-ethics`；Gate 6 失败 → `manuscript-writing`
- Gate 3 Phase A → 调用 `pubmed-search` Mode 3
- 完成后 → 更新 `.mrp-state.json`

### 可选衔接
- Gate 3 发现 claim/数据问题需多任务并行修复 → `team-collaboration`
- `revision-response` 修改完成后 → 再次运行本 skill
