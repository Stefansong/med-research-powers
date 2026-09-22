---
name: literature-synthesis
description: Use when searching several databases and synthesizing evidence into a gap map (retrieval + synthesis, no writing). Triggers on "帮我查文献"、"文献综述"、"research gap"、"相关研究"、"这个领域有什么研究"、"快速调研".
---

# Literature Synthesis

## Overview

多数据库检索 + 证据评价 + gap 分析。不是随意列几篇——必须有可复现的检索策略、逐篇验证和按主题组织的证据图。本 skill 只做**检索与综合**，不写论文段落（Introduction / 综述正文交给 `manuscript-writing`）。

与 `pubmed-search` 的分工：`pubmed-search` = 单库（PubMed）快速检索、PMID/引用验证、MeSH 与检索式、全文获取；本 skill = 综述级问题、gap 定位、多库综合。本 skill 的 PubMed 部分全部通过调用 `pubmed-search` 的 Mode 完成。

## When to Use

- 了解研究现状、寻找 gap（选题后、设计前）
- 为写 Introduction 收集背景证据（Narrative 模式）
- 做正式的系统综述 / Meta 分析的检索与筛选（Systematic 模式）

## When NOT to Use

- 只需查一篇文献、验证一个 PMID、构建一条检索式 → `pubmed-search`
- 已经有明确的文献清单只需格式化 → `pubmed-search` Mode 6
- 要把综合结果写成 Introduction 或综述正文 → `manuscript-writing`（读取本 skill 的产物）

## Workflow

### Step 0: 选择模式

| 模式 | 触发场景 | 产物 | 跳过的步骤 |
|------|---------|------|-----------|
| **Narrative** | 写 Introduction 背景、快速调研、选题阶段了解现状、为 protocol 找效应量先例 | `search-strategy.md` + `literature-synthesis-summary.md` | PRISMA 四文件、逐篇排除编码、全文筛选记录 |
| **Systematic** | 正式系统综述 / Meta 分析 / 范围综述、需要 PRISMA 流程图、期刊要求可复现筛选 | 全部 4 个文件 | 无 |

判断规则：用户说"系统综述 / Meta / PRISMA / 要注册 PROSPERO" → Systematic；其他一律默认 Narrative，并告诉用户"当前是快速模式，需要 PRISMA 级筛选时说一声"。Narrative 模式仍然要求：检索式记录、至少 2 个数据库、每条引用有验证状态。

### Step 1: 选择数据库

| 研究类型 | 主数据库 | 补充数据库 | 工具 |
|---------|---------|-----------|------|
| 临床/生物医学 | **PubMed** | Cochrane, Embase | PubMed MCP + WebSearch |
| AI/ML 医学应用 | **PubMed** + **arXiv** | IEEE Xplore, ACM DL | PubMed MCP + WebSearch |
| 手术视频/器械 | **PubMed** + **IEEE Xplore** | Scopus | PubMed MCP + WebSearch |
| 系统综述/Meta | **PubMed** + **Cochrane** + **Embase** | Web of Science | PubMed MCP + WebSearch |
| 基础/分子生物 | **PubMed** | bioRxiv, medRxiv | PubMed MCP + WebSearch |
| 公卫/流行病学 | **PubMed** | WHO IRIS, Global Health | PubMed MCP + WebSearch |
| 中文文献补充 | **PubMed** | CNKI, 万方, VIP | WebSearch / 用户手动 |

**原则：至少检索 2 个数据库。Systematic 模式至少 3 个。**

### Step 2: 制定检索策略

根据 PICO/PECO/PIRD 确定关键概念 → 每个概念列同义词 → **调用 `pubmed-search` Mode 1** 构建检索式（MeSH + free text + Boolean）→ 其他数据库改写为各自语法。

生成 `search-strategy.md` 记录完整检索策略（保证可复现），含 PubMed 返回的 `query_translation`。

### Step 3: 执行检索（多数据库）

**并行：** 目标数据库 ≥ 2 时，可用子代理工具（当前名 Agent，旧名 Task）并行检索各数据库（参考 `team-collaboration`），每个子代理负责一个数据库，主代理合并去重。

#### 数据库 A — PubMed（全部通过 `pubmed-search`）

- 检索式构建与执行 → **调用 `pubmed-search` Mode 1**
- 筛选后批量获取纳入文献元数据 → **调用 `pubmed-search` Mode 2**
- 全文筛选时获取 PMC 全文 → **调用 `pubmed-search` Mode 5**
- 引用验证 → **调用 `pubmed-search` Mode 3**（写入 Verified 字段）

MCP 函数名、参数、前缀写法（`mcp__<server名>__<函数>`，server 名以当前会话工具列表为准）以 `pubmed-search` SKILL.md 为准，本 skill 不重复。

**PubMed 覆盖：** 医学、临床研究、公共卫生、生物学、遗传学、药学、免疫学、神经科学、生物医学工程。
**PubMed 不覆盖：** 纯 CS/AI 算法论文、纯物理/数学、非生物医学工程、社会科学。

#### 数据库 B — arXiv / IEEE / ACM（WebSearch）

AI/ML 医学研究必须补充检索算法类文献：

```
WebSearch(query="site:arxiv.org medical image segmentation transformer 2024 2025")
WebSearch(query="site:ieeexplore.ieee.org surgical video AI deep learning")
WebSearch(query="site:dl.acm.org clinical NLP large language model evaluation")
```

#### 数据库 C — Cochrane Library（WebSearch）

系统综述、Meta 分析、临床指南证据：`WebSearch(query="site:cochranelibrary.com [主题] systematic review")`

#### 数据库 D — Google Scholar（用户手动）

Google Scholar 无法通过 WebSearch 得到文献结果。需要灰色文献、会议论文或引文追踪时：给用户一条检索字符串，请用户在 Scholar 手动检索后把结果（标题 + 作者 + 年份 + 链接）粘贴回来，记入 `search-strategy.md` 的 "Google Scholar" 段。

#### 数据库 E — 预印本（WebSearch）

`WebSearch(query="site:medrxiv.org [主题]")` / `WebSearch(query="site:biorxiv.org [主题]")`。预印本未经同行评审，引用时必须标注 "preprint"。

### Step 4: 文献筛选

**Narrative 模式：** 合并去重 → 按相关性挑选核心文献（通常 15-40 篇）→ 逐篇核对标题/摘要 → 直接进入 Step 5。不做排除编码，不生成 `screening-log.md`。

**Systematic 模式：** 严格按 PRISMA 2020 流程图执行，每一步的数量和排除原因都记录到 `screening-log.md`：

- **Phase 1 — 去重：** 合并所有数据库结果，按 DOI/PMID/标题匹配去重；记录各库原始数、重复数、去重后数
- **Phase 2 — 题目/摘要筛选：** 按纳入/排除标准逐篇审阅（摘要来自 `pubmed-search` Mode 2）；每篇排除记录原因（分类编码）
- **Phase 3 — 全文筛选：** `pubmed-search` Mode 5 获取 PMC 全文；无法获取的尝试 WebFetch 或标记 "full text unavailable"；逐篇审阅并记录排除原因
- **Phase 4 — 补充检索（唯一的滚雪球步骤）：**
  - 对纳入文献调用 `pubmed-search` Mode 4（Similar articles，PubMed 相似文献，**不是**引文追踪）
  - 引文追踪为**手动步骤**：逐篇检查纳入文献的参考文献列表；施引文献由用户在 Google Scholar / Web of Science 手动查询后粘贴
  - 新发现的文献重复 Phase 2-3；记录来源与新增纳入数

### Step 5: 证据评价

每篇纳入文献评价三项：

1. **研究类型与证据等级**：Oxford CEBM 2011 Levels of Evidence（Level 1-5）
2. **偏倚风险**，工具按研究类型选：

   | 研究类型 | 工具 |
   |---------|------|
   | RCT | Cochrane RoB 2 |
   | 非随机干预研究 | ROBINS-I |
   | 队列 / 病例对照 | Newcastle-Ottawa Scale（满分 9） |
   | 诊断准确性 | QUADAS-2 |
   | 预测模型（含 AI） | PROBAST |
   | 系统综述本身 | AMSTAR 2 |

3. **结果适用性**：人群、场景、结局定义是否与本研究一致

### Step 6: 证据综合

**按主题组织**（不按时间或作者）：已知（明确证据）/ 未知（缺乏证据）/ 争议（证据不一致）/ 本研究的定位（解决哪个 gap）。写入 `literature-synthesis-summary.md`。

### Step 7: 验证并记录状态

- PubMed 覆盖的引用全部经 `pubmed-search` Mode 3 验证；arXiv/IEEE/预印本等非 PubMed 来源用 DOI 或 WebSearch 核对并标 ℹ️ Non-PubMed
- 输出 3-5 行摘要（产物、gap 结论、待注意），然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 literature-synthesis，登记产物，`next_step` 设为 study-design）

## Output

完整模板见 `references/output-templates.md`。字段清单：

| 文件 | 模式 | 必含字段 |
|------|------|---------|
| `search-strategy.md` | 两者 | 日期、研究问题、模式、各数据库检索式 + 过滤器 + 结果数 + 工具、PubMed `query_translation`、补充检索（Similar articles 种子 PMID；手动引文追踪记录） |
| `literature-synthesis-summary.md` | 两者 | 主题、模式、检索/纳入数量、Evidence Map（Known / Unknown / Controversial）、Research Gap、Key References Table（每行带 Verified 状态） |
| `screening-log.md` | Systematic | PRISMA 各阶段数量（Identification / Title-Abstract / Full Text / Supplementary / Final）、全文阶段逐篇排除原因、全文不可获取清单 |
| `literature-references.md` | Systematic | 每篇：标题、期刊、PMID/DOI/PMCID、来源库、研究类型、样本量、核心发现、相关性、证据等级（CEBM 2011）、偏倚风险 + 工具、Verified 状态（5 态） |

Verified 状态统一用 5 态：✅ Verified / ⚠️ Not found / ❌ Mismatch / ⏳ Unverified (tool error) / ℹ️ Non-PubMed（定义见 `pubmed-search` Mode 3）。

**这 4 个文件是下游 skill 的输入：**
- `literature-synthesis-summary.md` → `study-design`（gap 定位、效应量先例）、`manuscript-writing`（Introduction）
- `literature-references.md` → `manuscript-writing`（引用管理）、`pre-submission-verification` Gate 3（引用验证）
- `search-strategy.md` + `screening-log.md` → `manuscript-writing`（Methods 检索描述）、`reporting-standards`（PRISMA / PRISMA-S）、`figure-generation`（PRISMA 流程图）

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "随便引几篇就行" | 必须有系统的检索策略，Narrative 模式也要记录检索式 |
| "只搜 PubMed 就够了" | AI 研究必须加 arXiv/IEEE；Systematic 模式至少 3 个数据库 |
| "只引用支持我观点的文献" | 确认偏倚——必须包含不一致的证据 |
| "这篇文献我记得大概说了..." | 必须用 `pubmed-search` Mode 3 验证文献存在且结论准确，禁止编造 |
| "按时间顺序排列文献" | 按主题组织，揭示 gap |
| "相似文章就是引文追踪" | `pubmed-search` Mode 4 给的是 PubMed "Similar articles"；引文追踪要手动查参考文献与施引文献 |
| "写 Introduction 也要走完 PRISMA" | Narrative 模式只要 2 个文件；PRISMA 只用于 Systematic 模式 |
| "预印本和正式发表一样引用" | 预印本必须标注 "preprint"，正式发表后应更新引用 |

## Convergence

当以下条件全部满足时完成：
1. 模式已选定并告知用户；检索策略已记录且可复现（包含所有数据库的检索式）
2. 至少 2 个数据库已检索（Systematic 模式至少 3 个）
3. 文献筛选流程完整（含跨数据库去重；Systematic 模式有 PRISMA 各阶段数量）
4. 关键文献已做证据评价（等级 + 按类型选的偏倚工具）
5. Research gap 已明确识别
6. 本研究的定位已清晰
7. PubMed 覆盖的引用已通过 `pubmed-search` Mode 3 验证；其余来源已通过 DOI/WebSearch 核对并标注 ℹ️ Non-PubMed；没有任何引用处于 ⏳ Unverified 未重试状态
8. 对应模式的产物文件已生成，`.mrp-state.json` 已更新

## Red Flags — STOP

- 禁止编造不存在的文献
- 禁止引用文献但歪曲其结论
- 不确定文献是否存在 → 明确告知用户，不要用"可能存在"糊弄
- 工具报错（⏳）不等于文献不存在 → 重试或改用 DOI/WebSearch，不要直接删掉
- 用户要求"直接写 Introduction" → 先完成综合产物，再交给 `manuscript-writing`

## 衔接规则

### 强制衔接（不可跳过）
- 完成后 → `study-design`（读取 `literature-synthesis-summary.md` 做 gap 定位与效应量先例）
- 产物被以下 skill 读取：`manuscript-writing`（Introduction、Methods 检索描述、引用）、`pre-submission-verification` Gate 3（`literature-references.md`）、`reporting-standards`（PRISMA / PRISMA-S）、`figure-generation`（PRISMA 流程图）

### 前置依赖（不满足则阻止）
- 建议先有 `research-question.md`（`research-question-formulation`）；没有时可独立使用，但必须先和用户确认一句话研究问题再检索

### 可选衔接
- 单条引用验证、格式化、PMID 反查 → 直接 `pubmed-search`
- Systematic 模式要注册 → 提醒 PROSPERO（`research-ethics` 第 5 节会核对）
- 多数据库并行检索 → `team-collaboration`
- Narrative 模式结束后用户要升级为系统综述 → 重跑 Step 4 Systematic，复用已有检索式
