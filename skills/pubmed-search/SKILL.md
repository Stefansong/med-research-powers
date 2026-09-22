---
name: pubmed-search
description: Use when a task needs a PubMed MCP action (search string, MeSH mapping, quick single-database search, PMID lookup or citation verification). Triggers on "查PubMed"、"PMID"、"验证引用"、"检索式"、"MeSH".
---

# PubMed Search

## Overview

PubMed MCP 工具的封装——交互式检索式构建、批量元数据获取、引用验证、相似文献发现、全文提取、引用格式化。作为底层工具 skill 被 `literature-synthesis`、`pre-submission-verification`、`manuscript-writing`、`research-question-formulation` 调用，也可独立运行。

与 `literature-synthesis` 的分工：本 skill = 单库（PubMed）工具动作；综述级问题、多库综合、gap 分析 → `literature-synthesis`（它会回调本 skill 的 Mode）。

## When to Use

- 构建 PubMed 检索式（PICO → MeSH → Boolean）并快速看结果
- 批量获取文献元数据（作者、摘要、DOI、MeSH、引用格式）
- 验证引用文献的真实性（anti-hallucination）
- 从已知文献出发找相似文献
- 获取 PMC 全文进行数据提取
- 根据不完整引用信息（作者 + 年份 + 期刊）反查 PMID

## When NOT to Use

- 需要多数据库检索、筛选、证据评价、gap 分析 → `literature-synthesis`
- 搜索非 PubMed 数据库（arXiv、IEEE、Cochrane）→ `WebSearch`
- 纯 CS/AI 算法论文 → PubMed 不覆盖，用 `WebSearch` 搜 arXiv

## MCP Tool Reference

本 skill 使用 PubMed MCP 的 7 个函数。**函数名固定，前缀以当前会话的工具列表为准**：完整工具名是 `mcp__<server名>__<函数名>`，claude.ai 连接器的 server 名为 `claude_ai_PubMed`，本地常见为 `PubMed`。调用前先在工具列表里确认前缀；工具列表里没有任何 PubMed 函数 → 告诉用户未连接 PubMed MCP，不要伪造结果。

| 函数 | 关键参数 | 返回要点 | 典型场景 |
|------|---------|---------|---------|
| `search_articles` | `query`, `max_results`, 可选日期/类型过滤 | `pmids[]`, `total_count`, `query_translation`（PubMed 实际执行的检索式，含 MeSH 映射）；**不含** mesh_terms | 主题检索、检索式调试 |
| `get_article_metadata` | `pmids=[...]`（每批 ≤ 10） | 标题、作者、期刊、年份、DOI、摘要、`mesh_terms`、`identifiers`（含 `pmc`）、文章类型 | 筛选后取完整信息、MeSH 确认、验证 |
| `get_full_text_article` | `pmc_ids=[...]` | PMC 全文 | 数据提取、方法学核实 |
| `find_related_articles` | `pmids=[...]` | PubMed "Similar articles" 列表 | 从种子文献扩展 |
| `convert_article_ids` | `ids=[...]`, `id_type="pmid"` / `"doi"` / `"pmcid"` | PMID ↔ PMCID ↔ DOI | DOI 反查 PMID、确认全文可用性 |
| `lookup_article_by_citation` | 作者、年份、期刊、标题片段等 | 候选 PMID | 无 PMID/DOI 的引用反查 |
| `get_copyright_status` | `pmids` 或 `pmc_ids` | 版权 / OA 状态 | 确认可复用性 |

## Workflow

### Mode 1: Interactive Search Building（交互式检索构建）

用户有模糊的检索需求时，引导构建精确检索式。

```
Step 1: 提取关键概念
  用户描述 → 拆解为 PICO / PECO / PIRD 要素 → 每个要素列出同义词

Step 2: MeSH 映射（二选一）
  a) search_articles(query='"概念"[MeSH Terms]', max_results=3)
     → 读返回的 query_translation，看 PubMed 把它映射成了哪个 MeSH 主题词
  b) 对前 3 个命中 PMID 调 get_article_metadata(pmids=[...])
     → 读 mesh_terms 字段，确认领域内常用的 MeSH 术语
  → 如无合适 MeSH → 使用 free text "词组"[Title/Abstract]
  ⚠️ 多义词处理: "vision"、"model"、"learning" 等必须用引号短语 + [Title/Abstract]
     （如 "vision language model"[Title/Abstract]），避免自动展开到无关领域（如眼科视觉）

Step 3: 构建 Boolean 检索式
  组内 OR（同义词扩展）→ 组间 AND（概念交叉）→ 添加过滤器（日期、语言、出版类型）

Step 4: 执行并迭代
  → search_articles(query=构建的检索式)
  → 看 total_count 与前几条相关性
  → 过多 → 收窄（增加限制词）；过少 → 放宽（去限制、加同义词）；离题 → 改关键词
```

**输出:** 最终检索式 + `query_translation` + 结果数量，保存到 `search-strategy.md`。
**快速查重用法**（被 `research-question-formulation` Round 2 调用）：只跑 Step 1-4 一轮，返回 total_count 与前 5 条标题，用于判断题目是否已有人做过；不生成文件。

### Mode 2: Batch Metadata Retrieval（批量元数据获取）

```
输入: PMID 列表（来自 search_articles 或用户提供）
→ get_article_metadata(pmids=[列表])   # 每次 ≤ 10 个，超过分批
→ 提取: 标题、作者、期刊、年份、DOI、摘要、mesh_terms、identifiers.pmc、文章类型
→ 格式化输出（表格或引用格式）
```

### Mode 3: Citation Verification（引用验证）

验证引用文献是否真实存在——**防止 AI 幻觉**。每条引用按下面顺序处理，结果只能是 5 种状态之一：

| 状态 | 含义 | 何时使用 |
|------|------|---------|
| ✅ Verified | 找到且作者/年份/标题一致 | 查询成功并匹配 |
| ⚠️ Not found | 查询成功但无命中 | PubMed 查过、确实没有 |
| ❌ Mismatch | 找到但作者/年份/标题不符 | 报告差异，让用户改引用 |
| ⏳ Unverified (tool error) | 工具报错、连接失败、参数异常 | **不等于文献不存在**；提示重试或换途径 |
| ℹ️ Non-PubMed | 书籍、指南、arXiv、会议论文、网页 | 改用 DOI / WebSearch 核对，注明来源 |

```
对每条待验证引用:
  1. 有 PMID → get_article_metadata(pmids=[PMID])
       → 匹配 → ✅；不匹配 → ❌（写出差异）；返回空 → ⚠️
  2. 无 PMID 有 DOI → convert_article_ids(ids=[DOI], id_type="doi") → 得到 PMID 后同 1
       → 转换无结果 → 可能非 PubMed 收录 → 走 4
  3. 只有作者 + 年份 + 期刊（典型 Vancouver 引用）→ lookup_article_by_citation
       → 找到 → 用 get_article_metadata 核对标题后 ✅ / ❌；未找到 → ⚠️
  4. 明显非 PubMed 类型（书籍、指南、arXiv、标准文件）→ ℹ️，用 DOI 或 WebSearch 核对
  5. 任一步工具报错 → ⏳，记录错误信息，重试一次；仍失败则保留 ⏳ 交给用户
```

**批量建议：** 引用 > 40 条时按 10 条一批处理，每批输出中间结果并累计到同一张报告表；先处理有 PMID/DOI 的（快），再处理需要 `lookup_article_by_citation` 的。

**输出:** Citation Verification Report（模板与 5 态示例见 `references/output-templates.md`）。

### Mode 4: Similar Articles（相似文献 / 滚雪球）

```
输入: 1-5 篇核心文献的 PMID
→ find_related_articles(pmids=[PMID 列表])
→ 合并结果并去重（基于 PMID）
→ get_article_metadata 获取元数据（分批 ≤ 10）
→ 按相关性排序，推荐 Top 10
```

说明：这是 PubMed 的 "Similar articles"（基于词频相似度），**不是**引文追踪。需要参考文献/施引文献追踪时由上层 skill 手动完成。

### Mode 5: Full Text Extraction（全文提取）

```
Step 1: 取 PMCID —— 二选一
        a) convert_article_ids(ids=[PMID 列表], id_type="pmid") → 读 PMCID
        b) get_article_metadata 返回的 identifiers.pmc（Mode 2 已取过时直接用）
Step 2: 有 PMCID 的 → get_full_text_article(pmc_ids=[列表])
Step 3: 无 PMCID 的 → 标记 "Full text not in PMC"
Step 4: 从全文提取用户需要的信息（方法、样本量、关键数据等）
```

### Mode 6: Reference Formatting（引用格式化）

```
输入: PMID 列表 + 目标格式（Vancouver / AMA / APA / Nature / IEEE）
→ get_article_metadata(pmids=[列表])
→ 按目标格式组装引用字符串
→ 输出格式化引用列表
```

支持的格式及示例（Vancouver / AMA / Nature / APA 7th / IEEE，含适用期刊）见 `references/output-templates.md`。

## Output

| Mode | 输出 |
|------|------|
| Mode 1 | 最终检索式 + `query_translation` + 结果数量，保存到 `search-strategy.md`（快速查重用法不落盘） |
| Mode 2 | 格式化的文献元数据（表格或引用格式） |
| Mode 3 | Citation Verification Report（5 态，模板见 `references/output-templates.md`） |
| Mode 4 | 去重后的相似文献 + Top N 推荐 |
| Mode 5 | 提取的全文信息 + 不可获取文献的标记 |
| Mode 6 | 目标格式的引用列表 |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "搜到 0 结果说明没有相关文献" | 可能是检索式太窄——看 `query_translation`，放宽 MeSH 或换同义词 |
| "PubMed 有所有文献" | PubMed 不覆盖纯 CS/AI/物理/工程类论文，这类标 ℹ️ Non-PubMed |
| "随便复制一个 PMID" | PMID 错误会导致引用完全错误——必须验证 |
| "工具报错就是文献不存在" | 报错 = ⏳ Unverified，重试或换途径；只有查询成功无命中才是 ⚠️ |
| "全文都能在 PMC 获取" | 仅部分文献有 PMC 全文，多数需通过其他途径获取 |
| "我记得这篇文献说了..." | 必须用 `get_article_metadata` 验证，AI 记忆不可靠 |
| "search_articles 会返回 MeSH" | 它只返回 pmids / total_count / query_translation；MeSH 在 `get_article_metadata` 的 mesh_terms |

## Convergence

根据 Mode 不同：
- Mode 1: 检索式构建完成 + 结果数量合理 + 相关性确认（快速查重：给出 total_count 与前 5 条标题）
- Mode 2: 所有 PMID 的元数据已获取并格式化
- Mode 3: 所有引用已标记 5 态之一，⏳ 已至少重试一次
- Mode 4: 相似文献已去重并推荐 Top N
- Mode 5: 可获取的全文已提取 + 不可获取的已标记
- Mode 6: 所有引用已按目标格式输出

## Red Flags — STOP

- **禁止编造 PMID** — 必须来自 `search_articles` 或 `lookup_article_by_citation` 的返回
- **禁止引用未验证的文献** — 每条引用必须通过 Mode 3 验证
- **禁止把 ⏳ Unverified 当 ⚠️ Not found 处理**（会把真实文献删掉）
- **不确定文献是否存在 → 明确告知用户**，不要猜测
- **PubMed MCP 未连接或报错时** → 如实说明，不要伪造结果

## 衔接规则

### 强制衔接（不可跳过）
- 任何 PubMed 调用 → 使用会话工具列表里的完整工具名（`mcp__<server名>__<函数名>`），函数名与参数按上表
- 验证引用真实性时 → **必须**走 Mode 3，禁止凭记忆判断文献是否存在

### 前置依赖（不满足则阻止）
- 会话中存在 PubMed MCP 工具；没有 → 告知用户并停止，不要用 WebSearch 冒充 PubMed 结果
- 被上层 skill 调用时按下表选择 Mode：

| 调用 skill | 使用 Mode | 场景 |
|-----------|----------|------|
| `research-question-formulation` | Mode 1（快速查重用法） | Round 2 的 N（Novel）项：看题目是否已有人做过 |
| `literature-synthesis` | Mode 1, 2, 3, 4, 5 | 完整检索、筛选、验证、相似文献扩展 |
| `pre-submission-verification` | Mode 3 | Gate 3 引用验证（> 40 条分批） |
| `manuscript-writing` | Mode 3, 6 | 写作中新增引用的验证与 References 格式化 |

### 可选衔接
- 用户直接说"帮我查 PubMed"、"这个 PMID 对不对"、"帮我格式化引用" → 独立执行对应 Mode
- Mode 1 输出的 `search-strategy.md` → 可供 `literature-synthesis` 复用
