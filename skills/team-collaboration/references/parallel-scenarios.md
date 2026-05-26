# Team Collaboration — Parallel Scenario Templates

These four scenarios describe how the main agent dispatches parallel subagents
**via the Task tool**. Each Task call carries one focused prompt that names the
role, the task, the input files to read, the output file to write, and the
SKILL.md path the subagent must follow. The main agent then waits for all Task
results and merges them.

## 场景 1：并行文献检索

主 Agent 判断："需要检索 3 个数据库，互相独立，可并行。" 用 Task 工具一次性派发 3 个并行 subagent：

- Task 1 — PubMed 检索：检索 PubMed，使用 PubMed MCP `mcp__claude_ai_PubMed__search_articles`。检索式：[具体检索式]。输出：`pubmed-results.md`（标题、PMID、摘要）。
- Task 2 — arXiv 检索：使用 WebSearch `site:arxiv.org`。关键词：[具体关键词]。输出：`arxiv-results.md`。
- Task 3 — Cochrane 检索：使用 WebSearch `site:cochranelibrary.com`。关键词：[具体关键词]。输出：`cochrane-results.md`。

→ 主 Agent：合并去重 → 统一格式 → `screening-log.md`

## 场景 2：多审稿人模拟（4-Reviewer Panel）

主 Agent（= Editor）用 Task 工具派发 **4 个并行 subagent**，每个扮演一位审稿人，全部按 `skills/peer-review-simulation/SKILL.md` 的 8 维度评分（0-100）：

- Task 1 — Reviewer 1（方法学）：读取 `manuscript/*.md`。重点审查研究设计、统计方法、样本量、偏倚控制、可复现性。输出：`review-methods.md`。
- Task 2 — Reviewer 2（临床/领域专家）：读取 `manuscript/*.md`。重点审查临床意义、可操作性、外推性、替代解释。输出：`review-clinical.md`。
- Task 3 — Reviewer 3（学术编辑）：读取 `manuscript/*.md`。重点审查论文结构、语言质量、图表规范、参考文献、期刊匹配度。输出：`review-editor.md`。
- Task 4 — Reviewer 4（Devil's Advocate）：读取 `manuscript/*.md`。挑战最强结论，寻找盲点，提出最不利解释，质疑最弱的方法学环节。输出：`review-devil.md`。

→ 主 Agent：综合 4 份评审 → Editor Summary → 评分矩阵（不简单取平均，R4 的 Critical 问题可降级决策）

## 场景 3：并行修稿

主 Agent 判断："多位审稿人的意见互相独立，可并行处理。" 用 Task 工具派发 N 个并行 subagent（每位审稿人一个）：

- Task 1 — 处理 Reviewer 1 的全部意见（附上意见原文）。修改对应论文段落，生成 response。输出：`reviewer1-response.md` + 修改后的段落。
- Task 2 — 处理 Reviewer 2 的全部意见（附上意见原文）。输出：`reviewer2-response.md` + 修改后的段落。
- Task 3 — 补充分析：Reviewer 3 要求补充 [具体分析]。读取 `data_clean.csv`，执行分析。输出：`supplementary-analysis.md` + 脚本。

→ 主 Agent：合并修改 → 检查无冲突 → 组装 Response Letter

## 场景 4：多专家方案评审

主 Agent 用 Task 工具派发 3 个并行 subagent：

- Task 1 — 生物统计教授：审查 `study-protocol.md` 的样本量计算和分析计划。输出：`protocol-review-stats.md`。
- Task 2 — 方法学专家：审查 `study-protocol.md` 的研究设计和偏倚控制。输出：`protocol-review-methods.md`。
- Task 3 — AI 医学专家：审查 `study-protocol.md` 的 AI 模型设计和指标选择。输出：`protocol-review-ai.md`。

→ 主 Agent：综合三方意见 → 修改方案 → Hard Checkpoint 确认
