---
name: literature-synthesis
description: Use when searching several databases and synthesizing evidence into a gap map (retrieval + synthesis, no writing). Triggers on "帮我查文献"、"文献综述"、"做系统综述"、"做Meta分析"、"research gap"、"这个领域有什么研究"、"快速调研".
---

# Literature Synthesis

## Overview

多数据库检索 + 证据评价 + gap 分析。不是随意列几篇——必须有可复现的检索策略、逐篇验证和按主题组织的证据图。本 skill 只做**检索与综合**，不写论文段落（Introduction / 综述正文交给 `manuscript-writing`）。

与 `pubmed-search` 的分工：`pubmed-search` = 单库（PubMed）快速检索、PMID/引用验证、MeSH 与检索式、全文获取；本 skill = 综述级问题、gap 定位、多库综合。本 skill 的 PubMed 部分全部通过调用 `pubmed-search` 的 Mode 完成。

> 总调度规则（直接调用本 skill 也适用，原文见 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`）：**缺前置产物**——说缺什么，light / auto 下先往下做并记缺口，不拒绝；**checkpoint_mode** 默认 light，只在 3 个硬确认处等；**只要一个产物**时交付后停下。

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

判断规则：用户说"系统综述 / Meta / PRISMA / 范围综述 / scoping review / 要注册 PROSPERO" → Systematic；其他一律默认 Narrative，并告诉用户"当前是快速模式，需要 PRISMA 级筛选时说一声"。Narrative 模式仍然要求：检索式记录、至少 2 个检索来源、每条引用有验证状态。范围综述走 Systematic 的检索与筛选流程（报告规范 PRISMA-ScR），但不做 GRADE，单篇质量评价可选（PRISMA-ScR item 12 "If done"）；注册见衔接规则（PROSPERO 不接受范围综述）。

### Step 1: 选择数据库

| 研究类型 | 主数据库 | 补充来源 |
|---------|---------|-----------|
| 临床/生物医学 | **PubMed** | Cochrane CENTRAL, Embase |
| AI/ML 医学应用 | **PubMed** + **arXiv** | IEEE Xplore, ACM DL |
| 手术视频/器械 | **PubMed** + **IEEE Xplore** | Scopus |
| 系统综述/Meta | **PubMed** + **Cochrane CENTRAL** + **Embase** | Web of Science |
| 基础/分子生物 | **PubMed** | bioRxiv, medRxiv |
| 公卫/流行病学 | **PubMed** | WHO IRIS, Global Health |
| 中文文献补充 | **PubMed** | CNKI, 万方, VIP |

**每个来源能怎么检索（必须照实记录，不能把补充检索写成数据库检索）：**

| 来源 | 本插件能做什么 | 在 `search-strategy.md` / PRISMA 里记为 |
|------|---------------|--------------------------------------|
| PubMed / MEDLINE | PubMed MCP（`pubmed-search` Mode 1）——**真正的数据库检索**：检索式、`query_translation`、结果数都可复现 | 数据库检索（PRISMA "Identification via databases"） |
| Embase、Cochrane Library（CENTRAL / CDSR）、Web of Science、Scopus、IEEE Xplore、ACM DL、CINAHL、CNKI / 万方 / VIP 等 | **可用工具都检索不了**（需订阅或机构登录；WebSearch 不是它们的检索接口）→ 给用户该库语法的完整检索式，用户在库内运行并导出结果（见 Step 3 来源 B） | 用户运行并导入 → 数据库检索；用户没跑 → **"Not searched"**，Methods 与局限性如实写明 |
| arXiv、medRxiv、bioRxiv、Cochrane 网页等 | WebSearch `site:` 查询——**只作补充**：只能给检索词和域名限制，不能按分类/日期/语言过滤，结果按网页排名、不完整也不可复现 | **"Web search (supplementary)"**，进 PRISMA "other methods" 分支，不计入数据库数 |
| Google Scholar、引文追踪、专家推荐 | 用户手动检索后粘贴 | PRISMA "other methods" |

**原则：** Narrative 模式至少 2 个检索来源（PubMed + 至少 1 个其他来源；WebSearch 补充检索可以算，但要标明是补充）。Systematic 模式：PubMed + **至少 2 个由用户在库内运行并导入结果的数据库**（如 Embase、Cochrane CENTRAL）；WebSearch 不计数。用户无法访问时照实标 "Not searched"，并告诉用户：这样的检索不全面，Methods 和局限性里不能写成"全面检索"。

### Step 2: 制定检索策略

根据 PICO/PECO/PIRD 确定关键概念 → 每个概念列同义词 → **调用 `pubmed-search` Mode 1** 构建检索式（MeSH + free text + Boolean）→ 其他数据库改写为各自语法（用户运行的检索式与 PubMed 检索式在概念上等价）。

生成 `search-strategy.md` 记录完整检索策略（保证可复现），含 PubMed 返回的 `query_translation`。

### Step 3: 执行检索（多数据库）

**并行：** 只有本插件自己能执行的检索才派子代理（当前名 Agent，旧名 Task）：PubMed（MCP，数据库 A）和 WebSearch 补充检索（来源 C），主代理合并去重。来源 B 的库（Embase、Cochrane Library、WoS、Scopus 等）**不派子代理**——子代理同样检索不了，由用户运行并导入，导入后一起去重。子代理交回的 WebSearch 结果一律按来源 C 记为 "Web search (supplementary)"，不写成某数据库的检索（如"Cochrane 检索"），不计入数据库数。用 `team-collaboration` 场景 1 并行时同样按这条分配。

#### 数据库 A — PubMed（全部通过 `pubmed-search`）

- 检索式构建与执行 → **调用 `pubmed-search` Mode 1**
- 筛选后批量获取纳入文献元数据 → **调用 `pubmed-search` Mode 2**
- 全文筛选时获取 PMC 全文 → **调用 `pubmed-search` Mode 5**
- 引用验证 → **调用 `pubmed-search` Mode 3**（写入 Verified 字段）

MCP 函数名、参数、前缀写法（`mcp__<server名>__<函数>`，server 名以当前会话工具列表为准）以 `pubmed-search` SKILL.md 为准，本 skill 不重复。

**PubMed 覆盖：** 医学、临床研究、公共卫生、生物学、遗传学、药学、免疫学、神经科学、生物医学工程。
**PubMed 不覆盖：** 纯 CS/AI 算法论文、纯物理/数学、非生物医学工程、社会科学。

#### 来源 B — 订阅数据库（Embase / Cochrane Library / Web of Science / Scopus / IEEE Xplore 等，用户运行）

可用工具都检索不了这些库，**不要**用 WebSearch `site:` 冒充。做法：

1. 把 PubMed 检索式改写成该库语法，每库一段写进 `search-strategy.md`，可直接复制运行——如 Embase.com（Emtree `'term'/exp` + `:ti,ab,kw`）、Cochrane Library（`[mh "term"]` + `:ti,ab,kw`）、Web of Science（`TS=(...)`）、Scopus（`TITLE-ABS-KEY(...)`）；写明需要用户核对的主题词映射。
2. 请用户在该库运行，记下检索日期、平台（如 Embase.com / Ovid）和结果数，导出全部记录（RIS / CSV / BibTeX）交回。
3. 导入后与 PubMed 结果合并去重（Step 4 Phase 1），各库原始数照用户导出记录填。
4. 用户无法访问 → 该库在 `search-strategy.md` 和 `screening-log.md` 标 "Not searched（原因）"，不编结果数。

#### 来源 C — arXiv / 预印本 / IEEE·ACM·Cochrane 网页（WebSearch，仅作补充；IEEE Xplore / ACM DL 的数据库检索见来源 B）

AI/ML 医学研究要补充算法类文献，预印本可补充最新证据，但 WebSearch 只接受检索词和域名限制，**不能**按 arXiv 分类、日期、语言过滤，结果按网页排名、既不完整也不可复现：

```
WebSearch(query="site:arxiv.org medical image segmentation transformer")
WebSearch(query="site:ieeexplore.ieee.org surgical video AI deep learning")
WebSearch(query="site:medrxiv.org [主题]")
```

- 在 `search-strategy.md` 记为 "Web search (supplementary)"：查询原文、日期、"Filters: none（WebSearch 不支持过滤）"、筛出的记录数；年份等限制在筛选阶段按纳入标准人工执行，并照实写明
- PRISMA 流程图里进 "other methods" 分支，不计入数据库数
- 需要正式检索 arXiv / IEEE Xplore / ACM DL → 按来源 B 给用户站内检索式，由用户运行并导出
- 预印本未经同行评审，引用时必须标注 "preprint"

#### 来源 D — Google Scholar（用户手动）

Google Scholar 无法通过 WebSearch 得到文献结果。需要灰色文献、会议论文或引文追踪时：给用户一条检索字符串，请用户在 Scholar 手动检索后把结果（标题 + 作者 + 年份 + 链接）粘贴回来，记入 `search-strategy.md` 的 "Google Scholar" 段（PRISMA "other methods"）。

### Step 4: 文献筛选

**Narrative 模式：** 合并去重 → 按相关性挑选核心文献（通常 15-40 篇）→ 逐篇核对标题/摘要 → 直接进入 Step 5。不做排除编码，不生成 `screening-log.md`。

**Systematic 模式：** 严格按 PRISMA 2020 流程图执行，每一步的数量和排除原因都记录到 `screening-log.md`。

**评价者（PRISMA 2020 item 8 / 9）：** 题目/摘要筛选、全文筛选、数据提取和偏倚评价都由**两名评价者独立**完成，**其中至少一名是人**（研究者或合作者）。Claude 最多担任其中一名评价者（AI 辅助），不能单独决定纳入或排除；推荐两名人类评价者、Claude 作辅助。

- 两人各自记录决定（互不参考）→ 比对 → 分歧经讨论或由第三名（人类）评价者裁决
- 每个阶段记录一致性（一致百分比及 Cohen's κ）和分歧解决方式
- Claude 参与任何一步时记录：模型名称与版本、使用日期、用于哪些步骤、判定标准 / 提示词存放位置、人工如何核对（如 AI 排除的记录全部由人复核）
- 这些写进 Methods：PRISMA 2020 item 8 / 9 要求说明每条记录由几名评价者筛选 / 提取、是否独立，以及 "if applicable, details of automation tools used in the process"；投稿时 AI 使用声明见 `submission-preparation`

- **Phase 1 — 去重：** 合并所有数据库结果（PubMed + 用户导入的数据库），按 DOI/PMID/标题匹配去重；记录各库原始数、重复数、去重后数；WebSearch 补充记录单独计入 other methods
- **Phase 2 — 题目/摘要筛选：** 两名评价者按纳入/排除标准独立逐篇审阅（PubMed 记录的摘要来自 `pubmed-search` Mode 2，用户导入记录的摘要取自其导出文件）；每篇排除记录原因（分类编码）
- **Phase 3 — 全文筛选：** `pubmed-search` Mode 5 获取 PMC 全文；无法获取的尝试 WebFetch 或标记 "full text unavailable"；两名评价者独立逐篇审阅并记录排除原因
- **Phase 4 — 补充检索（唯一的滚雪球步骤）：**
  - 对纳入文献调用 `pubmed-search` Mode 4（Similar articles，PubMed 相似文献，**不是**引文追踪）
  - 引文追踪为**手动步骤**：逐篇检查纳入文献的参考文献列表；施引文献由用户在 Google Scholar / Web of Science 手动查询后粘贴
  - 新发现的文献重复 Phase 2-3；记录来源与新增纳入数

### Step 5: 证据评价

每篇纳入文献评价三项（Systematic 模式由两名独立评价者完成，见 Step 4）：

1. **研究类型与证据等级**：Oxford CEBM 2011 Levels of Evidence（Level 1-5）
2. **偏倚风险**，工具按研究类型选（引用见 `reporting-standards` 的 standards-index.yaml，`type: bias_tool` 条目）：

   | 研究类型 | 工具 |
   |---------|------|
   | RCT | Cochrane RoB 2 |
   | 非随机干预研究 | ROBINS-I（2016；ROBINS-I V2 已在 riskofbias.info 以草案发布，用前核对官网当前版本） |
   | 暴露效应的队列研究 | ROBINS-E（2024） |
   | 病例对照等没有合适 ROBINS 工具的观察性设计 | Newcastle-Ottawa Scale（满分 9）——只在期刊 / 既定方案要求或没有合适 ROBINS 工具时用；逐项报告，不只给总分，并说明其效度有争议（Stang 2010） |
   | 诊断准确性 | QUADAS-2（比较两种检查或 AI vs 医生时另加 QUADAS-C，见 Meta 分析方法卡） |
   | 预测模型（回归或 AI） | PROBAST+AI（2025，更新并可替代 PROBAST 2019） |
   | 系统综述本身 | AMSTAR 2 |

3. **结果适用性**：人群、场景、结局定义是否与本研究一致

**证据确定性（Systematic 模式，范围综述除外）：** 对每个主要结局分别做 GRADE——五个降级因素（偏倚风险、不一致性、间接性、不精确性、发表偏倚），观察性证据可因大效应、剂量反应关系、所有可能的混杂只会削弱效应而升级；两名评价者（至少一名是人）评定，逐项写明降级 / 升级理由，填入 `literature-synthesis-summary.md` 的 Certainty of Evidence 表（PRISMA 2020 item 15 / 22）。要做定量合并时，方法按 `data-analysis-planning` 的 Meta 分析方法卡（`${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/method-cards/meta-analysis.md`，同样要求两名评价者独立提取与评价、每个结局做 GRADE）预先写进方案。

### Step 6: 证据综合

**按主题组织**（不按时间或作者）：已知（明确证据）/ 未知（缺乏证据）/ 争议（证据不一致）/ 本研究的定位（解决哪个 gap）。写入 `literature-synthesis-summary.md`。

### Step 7: 验证并记录状态

- PubMed 覆盖的引用全部经 `pubmed-search` Mode 3 验证；arXiv/IEEE/预印本等非 PubMed 来源用 DOI 或 WebSearch 核对并标 ℹ️ Non-PubMed
- 输出 3-5 行摘要（产物、gap 结论、待注意），然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 literature-synthesis，登记产物，`next_step` 设为 study-design）

## Output

完整模板见 `references/output-templates.md`。字段清单：

| 文件 | 模式 | 必含字段 |
|------|------|---------|
| `search-strategy.md` | 两者 | 日期、研究问题、模式、各来源的检索方式（MCP 数据库检索 / 用户运行并导入 / Web search 补充 / Not searched）+ 检索式 + 实际用到的过滤器 + 结果数、PubMed `query_translation`、补充检索（Similar articles 种子 PMID；手动引文追踪记录） |
| `literature-synthesis-summary.md` | 两者 | 主题、模式、检索/纳入数量、Evidence Map（Known / Unknown / Controversial）、Research Gap、Key References Table（每行带 Verified 状态）；Systematic 模式另含每个主要结局的 GRADE Certainty of Evidence 表 |
| `screening-log.md` | Systematic | 评价者（人数、身份、是否独立、AI 工具及其用途）、各阶段一致性与分歧解决、PRISMA 各阶段数量（Identification / Title-Abstract / Full Text / Supplementary / Final）、全文阶段逐篇排除原因、全文不可获取清单 |
| `literature-references.md` | Systematic | 每篇：标题、期刊、PMID/DOI/PMCID、来源库、研究类型、样本量、核心发现、相关性、证据等级（CEBM 2011）、偏倚风险 + 工具、Verified 状态（5 态） |

Verified 状态统一用 5 态：✅ Verified / ⚠️ Not found / ❌ Mismatch / ⏳ Unverified (tool error / web search only / not checked) / ℹ️ Non-PubMed（定义见 `pubmed-search` Mode 3）。

**这 4 个文件是下游 skill 的输入：**
- `literature-synthesis-summary.md` → `study-design`（gap 定位、效应量先例）、`manuscript-writing`（Introduction）
- `literature-references.md` → `manuscript-writing`（引用管理）、`pre-submission-verification` Gate 3（引用验证）
- `search-strategy.md` + `screening-log.md` → `manuscript-writing`（Methods 检索描述）、`reporting-standards`（PRISMA / PRISMA-S）、`figure-generation`（PRISMA 流程图）

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "随便引几篇就行" | 必须有系统的检索策略，Narrative 模式也要记录检索式 |
| "只搜 PubMed 就够了" | AI 研究必须补算法文献（arXiv/IEEE）；Systematic 模式 PubMed 之外至少 2 个由用户在库内运行并导入的数据库 |
| "`site:cochranelibrary.com` 搜过就算检索了 Cochrane" | WebSearch 不是数据库检索，只作补充、记入 other methods；正式检索由用户在库内运行检索式并导入结果，否则标 "Not searched" |
| "Claude 一个人筛完、提取完就行" | Systematic 模式要两名独立评价者、至少一名是人；记录一致性、分歧解决和 AI 工具使用 |
| "范围综述也注册 PROSPERO" | PROSPERO 不接受范围综述；protocol 注册到 OSF Registries 等或公开发表 |
| "只引用支持我观点的文献" | 确认偏倚——必须包含不一致的证据 |
| "这篇文献我记得大概说了..." | 必须用 `pubmed-search` Mode 3 验证文献存在且结论准确，禁止编造 |
| "按时间顺序排列文献" | 按主题组织，揭示 gap |
| "相似文章就是引文追踪" | `pubmed-search` Mode 4 给的是 PubMed "Similar articles"；引文追踪要手动查参考文献与施引文献 |
| "写 Introduction 也要走完 PRISMA" | Narrative 模式只要 2 个文件；PRISMA 只用于 Systematic 模式 |
| "预印本和正式发表一样引用" | 预印本必须标注 "preprint"，正式发表后应更新引用 |

## Convergence

当以下条件全部满足时完成：
1. 模式已选定并告知用户；检索策略已记录且可复现（包含所有数据库的检索式）
2. Narrative 模式至少 2 个检索来源；Systematic 模式 PubMed + 至少 2 个由用户运行并导入的数据库——做不到的已标 "Not searched" 并告知用户检索不全面；WebSearch 结果全部标为补充检索
3. 文献筛选流程完整（含跨数据库去重；Systematic 模式有 PRISMA 各阶段数量、两名独立评价者（至少一名是人）、一致性与分歧解决记录、AI 工具使用记录）
4. 关键文献已做证据评价（等级 + 按类型选的偏倚工具）；Systematic 模式（范围综述除外）每个主要结局已有 GRADE 评级
5. Research gap 已明确识别
6. 本研究的定位已清晰
7. PubMed 覆盖的引用已通过 `pubmed-search` Mode 3 验证；其余来源已通过 DOI/WebSearch 核对并标注 ℹ️ Non-PubMed；工具报错的 ⏳ Unverified 已重试，仍是 ⏳ 的（含只凭 WebSearch 找到的 PubMed 类文献）已列给用户人工核对
8. 对应模式的产物文件已生成，`.mrp-state.json` 已更新

## Red Flags — STOP

- 禁止编造不存在的文献
- 禁止引用文献但歪曲其结论
- 不确定文献是否存在 → 明确告知用户，不要用"可能存在"糊弄
- 工具报错（⏳）不等于文献不存在 → 重试或改用 DOI/WebSearch，不要直接删掉
- 用户要求"直接写 Introduction" → 先完成综合产物，再交给 `manuscript-writing`
- 想把 WebSearch `site:` 结果写成某数据库的检索结果数，或给没检索的库编数字 → 停止，标为补充检索或 "Not searched"
- 想派子代理"检索 Cochrane / Embase / WoS / Scopus" → 停止，子代理也检索不了；按来源 B 把检索式交给用户
- Systematic 模式只有 Claude 一人筛选 / 提取 / 评价 → 停止，请用户安排至少一名人类评价者独立完成

## 衔接规则

### 强制衔接（不可跳过）
- 完成后 → `study-design`（读取 `literature-synthesis-summary.md` 做 gap 定位与效应量先例）
- 产物被以下 skill 读取：`manuscript-writing`（Introduction、Methods 检索描述、引用）、`pre-submission-verification` Gate 3（`literature-references.md`）、`reporting-standards`（PRISMA / PRISMA-S）、`figure-generation`（PRISMA 流程图）

### 前置依赖（缺了按总调度"缺前置产物时"处理）
- 建议先有 `research-question.md`（`research-question-formulation`）；没有时可独立使用，但必须先和用户确认一句话研究问题再检索

### 可选衔接
- 单条引用验证、格式化、PMID 反查 → 直接 `pubmed-search`
- Systematic 模式要注册（`research-ethics` 第 5 节会核对）→ 系统综述 / Meta：数据提取前注册 PROSPERO；范围综述：PROSPERO 不接受（以 PROSPERO 当前 eligibility 页面为准），protocol 注册到 OSF Registries（有 Generalized Systematic Review Registration 表单）或公开发表 protocol
- PubMed 与 WebSearch 补充检索并行 → `team-collaboration` 场景 1（只派这两类子代理；来源 B 由用户运行，见 Step 3）
- Narrative 模式结束后用户要升级为系统综述 → 重跑 Step 4 Systematic，复用已有检索式
