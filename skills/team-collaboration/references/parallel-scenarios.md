# Team Collaboration — Parallel Scenario Templates

These four scenarios describe how the main agent dispatches parallel subagents with the
**Agent** tool (old name Task still works as an alias): in one message, issue N Agent calls,
each with one focused prompt that names the role, the task, the input files to read, the
**single output file it may write**, and the SKILL.md / references path it must follow.
Subagents never edit `manuscript/` or other shared files. The main agent waits for all
results, checks consistency, and merges serially.

PubMed MCP tool names are written `mcp__<server名>__<函数>`; the server name is whatever the
current session's tool list shows (claude.ai connector: `claude_ai_PubMed`; local servers are
commonly `PubMed`).

## 场景 1：并行文献检索

主代理判断："需要检索 3 个数据库，互相独立，可并行。" 在同一条消息里发起 3 个 Agent 调用：

- Agent 1 — PubMed 检索：按 `${CLAUDE_PLUGIN_ROOT}/skills/pubmed-search/SKILL.md` Mode 1，使用
  `mcp__<server名>__search_articles`。检索式：[具体检索式]。只写 `pubmed-results.md`（标题、PMID、摘要）。
- Agent 2 — arXiv 检索：使用 WebSearch `site:arxiv.org`。关键词：[具体关键词]。只写 `arxiv-results.md`。
- Agent 3 — Cochrane 检索：使用 WebSearch `site:cochranelibrary.com`。关键词：[具体关键词]。只写 `cochrane-results.md`。

→ 主代理：合并去重 → 统一格式 → `screening-log.md`

## 场景 2：多审稿人模拟（4-Reviewer Panel）

主代理（= Editor）在同一条消息里发起 **4 个 Agent 调用**，每个扮演一位审稿人，全部按
`${CLAUDE_PLUGIN_ROOT}/skills/peer-review-simulation/SKILL.md` 的 8 维度评分（0-100），评分标准与
分数→决策映射读 `${CLAUDE_PLUGIN_ROOT}/skills/peer-review-simulation/references/scoring-rubric.yaml`，
每位给出自己的 Recommendation（Accept / Minor / Major / Reject）：

- Agent 1 — Reviewer 1（方法学）：读取 `manuscript/*.md`。重点审查研究设计、统计方法、样本量、偏倚控制、可复现性。只写 `review-methods.md`。
- Agent 2 — Reviewer 2（临床/领域专家）：读取 `manuscript/*.md`。重点审查临床意义、可操作性、外推性、替代解释。只写 `review-clinical.md`。
- Agent 3 — Reviewer 3（学术编辑）：读取 `manuscript/*.md`。重点审查论文结构、语言质量、图表规范、参考文献、期刊匹配度。只写 `review-editor.md`。
- Agent 4 — Reviewer 4（Devil's Advocate）：读取 `manuscript/*.md`。挑战最强结论，寻找盲点，提出最不利解释，质疑最弱的方法学环节。只写 `review-devil.md`。

每个 prompt 末尾加：「不要修改 manuscript/ 下任何文件。」

→ 主代理：综合 4 份评审 → Editor Summary → 评分矩阵（不简单取平均，R4 的 Critical 问题可降级决策）
→ `peer-review-simulation-report.md`

## 场景 3：并行修稿（需用户同意）

主代理判断："多位审稿人的意见互相独立，可并行起草。" 在同一条消息里发起 N 个 Agent 调用（每位审稿人一个）。
**子代理只起草，不改稿**：每个只写自己的 `reviewerN-response.md`，其中包含
(a) 对该审稿人每条意见的 Severity / Stance / Sub-type（按
`${CLAUDE_PLUGIN_ROOT}/skills/revision-response/references/revision-strategy.yaml`），
(b) 逐条回复草稿，(c) **建议改动**——引用原段落 + 建议的新文字 + 位置，供主代理应用。

- Agent 1 — 处理 Reviewer 1 的全部意见（附上意见原文）。读取 `manuscript/*.md`。只写 `reviewer1-response.md`。
- Agent 2 — 处理 Reviewer 2 的全部意见（附上意见原文）。读取 `manuscript/*.md`。只写 `reviewer2-response.md`。
- Agent 3 — 补充分析：Reviewer 3 要求补充 [具体分析]。读取 `data_clean.csv` 与 `analysis-plan.md`，按
  `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/SKILL.md` 执行，结果标注 post hoc / exploratory。
  只写 `supplementary-analysis.md` + 对应脚本文件。

每个 prompt 末尾加：「禁止修改 manuscript/ 下任何文件，改动只能写成建议放在你的输出文件里。」

→ 主代理：**串行**应用各文件中的建议改动（同一段落被多位审稿人涉及时合并措辞并向用户说明）→
把 post hoc 分析记入 `analysis-log.md` → 组装 `response-letter.md` 与 `revision-tracking.md`

## 场景 4：多专家方案评审（需用户同意）

主代理在同一条消息里发起 3 个 Agent 调用：

- Agent 1 — 生物统计专家：审查 `study-protocol.md` 的样本量计算和分析计划。只写 `protocol-review-stats.md`。
- Agent 2 — 方法学专家：审查 `study-protocol.md` 的研究设计和偏倚控制。只写 `protocol-review-methods.md`。
- Agent 3 — AI 医学专家：审查 `study-protocol.md` 的 AI 模型设计和指标选择。只写 `protocol-review-ai.md`。

每个 prompt 末尾加：「不要修改 study-protocol.md。」

→ 主代理：综合三方意见 → 修改方案 → 回 `study-design` 的硬确认（protocol）
