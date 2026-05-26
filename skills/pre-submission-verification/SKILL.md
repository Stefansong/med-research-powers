---
name: pre-submission-verification
description: Use when a manuscript is declared complete or ready for submission (MANDATORY gate). Triggers on "写完了"、"可以投了"、"定稿"、"差不多了"、"投稿"、"submission"、"cover letter".
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

六个 Gate 的逐条检查清单见 `references/gates-checklist.yaml`。逐 Gate 加载并核对，每条标 ✅ / ⚠️ / ❌。各 Gate 概览与路由判断：

- **Gate 1 — 报告规范合规**：调用 `reporting-standards` skill，确定研究类型选对应规范，合格标准 = 0 个 ❌ Critical 项。
- **Gate 2 — 统计完整性**：效应量+95%CI、精确 p 值、多重比较校正、敏感性分析、先验样本量、脚本与 Results 逐项一致等。失败 → 回 `statistical-analysis`。
- **Gate 3 — Claim Verification（内容真实性验证）**：6 个 Phase（A 参考文献真实性 / B 数据一致性 / C Claims-Evidence 对应 / D 方法-结果匹配 / E 预定 vs 探索性 / F AI 生成内容标记）。Phase A **优先使用 PubMed MCP 自动验证**：`mcp__claude_ai_PubMed__search_articles`、`mcp__claude_ai_PubMed__get_article_metadata`、`mcp__claude_ai_PubMed__get_full_text_article`、`mcp__claude_ai_PubMed__convert_article_ids`；查无结果的引用标记为 ❌ SUSPICIOUS。这是防 AI 幻觉的核心 Gate。
- **Gate 4 — 图表质量**：字体、字号、DPI、坐标轴标签、色盲友好、Figure Legend。失败 → 回 `figure-generation`。
- **Gate 5 — 伦理与合规**：调用 `research-ethics` skill，核对伦理批准号、知情同意/豁免、利益冲突、资金来源、数据可用性、试验注册号。失败 → 回 `research-ethics`。
- **Gate 6 — 形式检查**：字数限制、Running title、关键词、缩写、作者信息、页码等。

> 路由原则：Gate 失败时不要自行修补深层问题，而是路由回对应的专责 skill（统计→`statistical-analysis`、图表→`figure-generation`、伦理→`research-ethics`、规范→`reporting-standards`），修复后回到本 skill 重新验证。

## Output

生成 `submission-readiness-report.md`：6 个 Gate 的状态表（✅/❌ + Critical 数量 + Action Items）与优先级修改清单。完整报告模板见 `references/readiness-report-template.md`。

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
- Gate 1 失败涉及报告规范 → 回 `reporting-standards`
- Gate 2 失败涉及统计 → 回 `statistical-analysis`
- Gate 4 失败涉及图表 → 回 `figure-generation`
- Gate 5 失败涉及伦理 → 回 `research-ethics`
- 全部通过 → 可以进入投稿流程

### 可选衔接
- 全部 Gate 通过 → `submission-preparation`（Cover Letter + 投稿系统指引）
- 投稿前想预判审稿人反应 → `peer-review-simulation`
- Gate 3 发现 claim/数据问题需多任务并行修复 → `team-collaboration`
