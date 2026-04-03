---
name: pubmed-search
description: Use when performing PubMed literature searches, verifying citations, extracting article data, or building search strategies using PubMed MCP tools. Triggers on "查PubMed"、"检索文献"、"verify reference"、"这篇文献存在吗"、"帮我找这篇论文"、"MeSH"、"PMID"、"搜论文"、"文献真实性".
---

# PubMed Search

## Overview

PubMed MCP 工具的深度封装——提供交互式检索构建、批量元数据获取、引用验证、相关文献发现和全文提取能力。作为底层工具 skill 被 `literature-synthesis`、`pre-submission-verification`、`manuscript-writing` 等上层 skill 调用。

## When to Use

- 构建复杂的 PubMed 检索式（PICO → MeSH → Boolean）
- 批量获取文献元数据（作者、摘要、DOI、引用格式）
- 验证引用文献的真实性（anti-hallucination）
- 从已知文献出发发现相关研究（滚雪球）
- 获取 PMC 全文进行数据提取
- 根据不完整引用信息（作者+年份+期刊）反查 PMID
- 了解某主题的发表趋势

## When NOT to Use

- 需要完整的系统性文献综述流程 → `literature-synthesis`（调用本 skill 作为子步骤）
- 搜索非 PubMed 数据库（arXiv、IEEE、Cochrane）→ 用 `WebSearch`
- 纯 CS/AI 算法论文 → PubMed 不覆盖，用 `WebSearch` 搜 arXiv

## MCP Tool Reference

本 skill 封装以下 7 个 PubMed MCP 函数：

| 函数 | 用途 | 典型场景 |
|------|------|---------|
| `search_articles` | 关键词/MeSH/Boolean 检索 | 主题检索、构建文献库 |
| `get_article_metadata` | 批量获取文献详细信息 | 筛选后获取纳入文献完整信息 |
| `get_full_text_article` | 获取 PMC 全文 | 数据提取、方法学细节核实 |
| `find_related_articles` | 查找相似文献 | 滚雪球检索、扩展检索 |
| `convert_article_ids` | PMID ↔ PMCID ↔ DOI 互转 | 确认全文可用性、统一标识符 |
| `lookup_article_by_citation` | 根据引用信息反查 PMID | 已知引用缺 PMID 时反查 |
| `get_copyright_status` | 查询版权和 OA 状态 | 系统综述中确认可引用性 |

## Workflow

### Mode 1: Interactive Search Building（交互式检索构建）

用户有模糊的检索需求时，引导构建精确检索式。

```
Step 1: 提取关键概念
  用户描述 → 拆解为 PICO 要素 → 每个要素列出同义词

Step 2: MeSH 映射
  对每个关键概念:
  → search_articles(query="[概念]"[MeSH Terms], max_results=3)
  → 从返回结果的 mesh_terms 字段确认正确的 MeSH 术语
  → 如无合适 MeSH → 使用 free text [Title/Abstract]
  ⚠️ 多义词处理: 对 "vision"、"model"、"learning" 等多义词，
     必须使用引号短语检索（如 "vision language model"[Title/Abstract]）
     避免 MeSH 自动展开导致大量无关结果（如 "vision" → 眼科视觉）

Step 3: 构建 Boolean 检索式
  组内 OR（同义词扩展）→ 组间 AND（概念交叉）
  → 添加过滤器（日期、语言、出版类型）

Step 4: 执行并迭代
  → search_articles(query=构建的检索式)
  → 检查结果数量和相关性
  → 如过多 → 收窄（增加限制词）
  → 如过少 → 放宽（去除限制、增加同义词）
  → 如离题 → 修改关键词
```

**输出:** 打印最终检索式 + 结果数量，保存到 `search-strategy.md`

### Mode 2: Batch Metadata Retrieval（批量元数据获取）

从一组 PMID 快速获取完整文献信息。

```
输入: PMID 列表（从 search_articles 返回或用户提供）
→ get_article_metadata(pmids=[列表])
→ 提取: 标题、作者、期刊、年份、DOI、摘要、MeSH、文章类型
→ 格式化输出（表格或引用格式）
```

**批量限制:** 每次最多 10 个 PMID，超过则分批调用。

### Mode 3: Citation Verification（引用验证）

验证引用文献是否真实存在——**防止 AI 幻觉**。

```
对每条待验证引用:
  1. 如有 PMID → get_article_metadata(pmids=[PMID])
     → 确认标题、作者、年份是否匹配
     → 如 MCP 返回 INVALID_PARAMETERS 或解析错误 → 视同 PMID 不存在，标记 ⚠️
  2. 如有 DOI → convert_article_ids 转换为 PMID → 同上
  3. 如仅有作者+年份+期刊 → lookup_article_by_citation
     → 如找到 → 标记 ✅ Verified
     → 如未找到 → 标记 ⚠️ Not found in PubMed
  4. 如找到但信息不匹配 → 标记 ❌ Mismatch (报告差异)
  5. 如 MCP 工具报错（连接失败/参数异常）→ 标记 ⚠️ Not found（不要误判为系统错误）
```

**输出:** 验证报告

```markdown
## Citation Verification Report

| # | Citation | PMID | Status | Notes |
|---|---------|------|--------|-------|
| 1 | Smith et al., 2024, Lancet | 39123456 | ✅ Verified | — |
| 2 | Lee et al., 2023, Nature | — | ⚠️ Not in PubMed | May be non-biomedical |
| 3 | Wang et al., 2022, JAMA | 35678901 | ❌ Mismatch | Year is 2021, not 2022 |
```

### Mode 4: Snowball Search（滚雪球检索）

从核心文献出发发现相关研究。

```
输入: 1-5 篇核心文献的 PMID
→ 对每篇: find_related_articles(pmid=PMID)
→ 合并结果并去重（基于 PMID）
→ get_article_metadata 获取元数据
→ 按相关性排序，推荐 Top 10
```

### Mode 5: Full Text Extraction（全文提取）

获取 PMC 全文用于数据提取。

```
Step 1: convert_article_ids(pmids=[列表]) → 获取 PMCID
Step 2: 有 PMCID 的 → get_full_text_article(pmc_ids=[列表])
Step 3: 无 PMCID 的 → 标记 "Full text not in PMC"
Step 4: 从全文提取用户需要的信息（方法、样本量、关键数据等）
```

### Mode 6: Reference Formatting（引用格式化）

将 PubMed 元数据转换为目标期刊的引用格式。

```
输入: PMID 列表 + 目标格式（Vancouver / AMA / APA / Nature）
→ get_article_metadata(pmids=[列表])
→ 按目标格式组装引用字符串
→ 输出格式化引用列表
```

**支持的格式:**

| 格式 | 适用期刊 | 示例 |
|------|---------|------|
| Vancouver | Lancet, BMJ, EU, JU | Smith J, Lee K. Title. J Name. 2024;1(2):3-4. doi:10.xxxx/xxxxx |
| AMA (JAMA) | JAMA 家族 | Smith J, Lee K. Title. J Name. 2024;1(2):3-4. doi:XX |
| Nature | Nature 家族, npj | Smith, J. & Lee, K. Title. J. Name 1, 3–4 (2024). |
| APA 7th | 心理学/教育 | Smith, J., & Lee, K. (2024). Title. J Name, 1(2), 3–4. |
| IEEE | IEEE JBHI, TMI | [1] J. Smith and K. Lee, "Title," J. Name, vol. 1, no. 2, pp. 3–4, 2024. |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "搜到 0 结果说明没有相关文献" | 可能是检索式太窄——放宽 MeSH 或换同义词 |
| "PubMed 有所有文献" | PubMed 不覆盖纯 CS/AI/物理/工程类论文 |
| "随便复制一个 PMID" | PMID 错误会导致引用完全错误——必须验证 |
| "全文都能在 PMC 获取" | 仅约 600 万篇有 PMC 全文，多数需通过其他途径获取 |
| "我记得这篇文献说了..." | 必须用 get_article_metadata 验证，AI 记忆不可靠 |
| "一次检索就够了" | 用 find_related_articles 滚雪球 + 迭代检索式 |

## Red Flags — STOP

- **禁止编造 PMID** — 必须从 search_articles 或 lookup_article_by_citation 获取
- **禁止引用未验证的文献** — 每条引用必须通过 Mode 3 验证
- **不确定文献是否存在 → 明确告知用户**，不要猜测
- **PubMed MCP 返回错误时** → 说明连接问题，不要伪造结果

## Convergence

根据 Mode 不同：
- Mode 1: 检索式构建完成 + 结果数量合理 + 相关性确认
- Mode 2: 所有 PMID 的元数据已获取并格式化
- Mode 3: 所有引用已标记验证状态（✅/⚠️/❌）
- Mode 4: 滚雪球结果已去重并推荐 Top N
- Mode 5: 可获取的全文已提取 + 不可获取的已标记
- Mode 6: 所有引用已按目标格式输出

## 衔接规则

### 被上层 skill 调用

| 调用 skill | 使用 Mode | 场景 |
|-----------|----------|------|
| `literature-synthesis` | Mode 1, 2, 4, 5 | 完整检索流程 |
| `pre-submission-verification` | Mode 3 | Gate 3 引用验证 |
| `manuscript-writing` | Mode 6 | References 格式化 |
| `research-question-formulation` | Mode 1 | 初步文献调研 |

### 独立使用

用户直接说"帮我查 PubMed"、"这个 PMID 对不对"、"帮我格式化引用" → 直接执行对应 Mode。

### 前置依赖

无——可独立运行，也可被其他 skill 调用。
