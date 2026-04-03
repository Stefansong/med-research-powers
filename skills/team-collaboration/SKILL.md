---
name: team-collaboration
description: Use when a research project benefits from multi-agent parallel work. Triggers on "多人协作"、"并行分析"、"分工"、"同时做". Spawns multiple sub-agents to work on independent tasks simultaneously.
---

# Team Collaboration

## Overview

将研究任务分解为可并行的独立子任务，启动多个子 agent 同时执行，主 agent 负责协调和合并结果。

## When to Use

- 多个独立分析维度需要同时推进
- 系统综述需要同时检索多个数据库
- 论文修回需要同时处理多个审稿人意见
- 需要多专业视角同时评审方案
- 项目时间紧迫

## When NOT to Use

- 简单线性任务（一个 skill 就够）
- 任务之间有严格顺序依赖（必须先有 SAP 才能分析）
- 用户偏好逐步确认每一步

## Auto-Parallel Rules（自动并行触发）

以下场景由主 agent **自动启动**子 agent 并行执行，无需用户确认：

| 触发时机 | 并行内容 | 理由 |
|---------|---------|------|
| `literature-synthesis` 进入 Step 3（执行检索）且目标数据库 ≥ 2 | 每个数据库一个子 agent 同时检索 | 数据库之间完全独立，无数据依赖 |
| `peer-review-simulation` 进入 Step 1（4-Reviewer Panel） | 4 个审稿人角色各一个子 agent | 审稿人独立评审，天然并行 |

以下场景由主 agent **向用户建议**并行，确认后启动：

| 触发时机 | 并行内容 | 需要确认的原因 |
|---------|---------|---------------|
| `revision-strategy` 发现多个审稿人意见互相独立 | 每位审稿人的意见由一个子 agent 处理 | 不同审稿人可能要求修改同一段落 |
| `study-design` 完成后需要多专家评审 | 统计 + 方法学 + AI 专家并行评审 | 评审意见可能需要协调 |

**建议话术：**
```
────────────────────────────────────────
💡 检测到可并行的独立子任务：

  • 子任务 A: [描述]
  • 子任务 B: [描述]
  • 子任务 C: [描述]

并行执行可以加速进度。是否启动？
────────────────────────────────────────
```

## Workflow

### Step 1: 识别可并行的子任务

主 agent 分析当前阶段，将任务分解为**互不依赖**的子任务：

```
主 Agent 分析:
  "这 3 个任务之间没有数据依赖，可以并行"
  → 子任务 A: [描述]
  → 子任务 B: [描述]
  → 子任务 C: [描述]
```

**关键判断：** 只有输入数据互不依赖的任务才能并行。

### Step 2: 启动子 agent

使用 Agent tool 并行启动多个子 agent：

```
Agent(name="statistician", prompt="你是生物统计专家。任务：[具体任务]。读取 [具体文件]，输出 [具体文件]。")
Agent(name="writer", prompt="你是医学写作专家。任务：[具体任务]。读取 [具体文件]，输出 [具体文件]。")
Agent(name="reviewer", prompt="你是审稿人模拟器。任务：[具体任务]。读取 [具体文件]，输出 [具体文件]。")
```

**每个子 agent 的 prompt 必须包含：**
1. 明确的角色定位
2. 具体的任务描述
3. 需要读取的输入文件
4. 需要生成的输出文件
5. 需要遵守的 SKILL.md 路径

### Step 3: 等待 + 合并

主 agent 等待所有子 agent 完成，然后：
- 审查每个子 agent 的输出
- 检查输出之间的一致性（如：数字是否对得上）
- 合并到主项目文件
- 向用户报告合并结果

## 场景模板

### 场景 1：并行文献检索

```
主 Agent:
  "需要检索 3 个数据库，互相独立，可并行"

Agent(name="pubmed-search", prompt="
  检索 PubMed，使用 PubMed MCP search_articles。
  检索式：[具体检索式]
  输出：pubmed-results.md（标题、PMID、摘要）")

Agent(name="arxiv-search", prompt="
  检索 arXiv，使用 WebSearch site:arxiv.org。
  关键词：[具体关键词]
  输出：arxiv-results.md")

Agent(name="cochrane-search", prompt="
  检索 Cochrane，使用 WebSearch site:cochranelibrary.com。
  关键词：[具体关键词]
  输出：cochrane-results.md")

→ 主 Agent: 合并去重 → 统一格式 → screening-log.md
```

### 场景 2：多审稿人模拟

```
主 Agent (= Editor):

Agent(name="reviewer-methods", prompt="
  你是方法学审稿人。读取 manuscript/*.md。
  重点审查：研究设计、统计方法、样本量、偏倚控制。
  按 skills/peer-review-simulation/SKILL.md 的 8 维度评分（0-100）。
  输出：review-methods.md")

Agent(name="reviewer-clinical", prompt="
  你是临床专家审稿人。读取 manuscript/*.md。
  重点审查：临床意义、可操作性、外推性。
  输出：review-clinical.md")

Agent(name="reviewer-devil", prompt="
  你是 Devil's Advocate。读取 manuscript/*.md。
  挑战最强结论，寻找盲点，提出最不利解释。
  输出：review-devil.md")

→ 主 Agent: 综合 3 份评审 → Editor Summary → 评分矩阵
```

### 场景 3：并行修稿

```
主 Agent:
  "3 位审稿人的意见互相独立，可并行处理"

Agent(name="fix-reviewer1", prompt="
  处理 Reviewer 1 的全部意见（attached）。
  修改对应论文段落，生成 response。
  输出：reviewer1-response.md + 修改后的段落")

Agent(name="fix-reviewer2", prompt="
  处理 Reviewer 2 的全部意见（attached）。
  输出：reviewer2-response.md + 修改后的段落")

Agent(name="new-analysis", prompt="
  Reviewer 3 要求补充 [具体分析]。
  读取 data_clean.csv，执行分析。
  输出：supplementary-analysis.md + 脚本")

→ 主 Agent: 合并修改 → 检查无冲突 → 组装 Response Letter
```

### 场景 4：多专家方案评审

```
主 Agent:

Agent(name="stats-reviewer", prompt="
  你是生物统计教授。审查 study-protocol.md 的样本量计算和分析计划。
  输出：protocol-review-stats.md")

Agent(name="methods-reviewer", prompt="
  你是方法学专家。审查 study-protocol.md 的研究设计和偏倚控制。
  输出：protocol-review-methods.md")

Agent(name="ai-reviewer", prompt="
  你是 AI 医学专家。审查 study-protocol.md 的 AI 模型设计和指标选择。
  输出：protocol-review-ai.md")

→ 主 Agent: 综合三方意见 → 修改方案 → Hard Checkpoint 确认
```

## 合并规则

| 情况 | 处理 |
|------|------|
| 子 agent 输出数字不一致 | 以 `analysis_script.py` 实际运行结果为准 |
| 子 agent 对同一文件有不同修改 | 主 agent 逐段合并，冲突处手动决策 |
| 子 agent 发现需要另一个 agent 的数据 | 停止并行，转为顺序执行 |
| 子 agent 完成质量不达标 | 主 agent 提供反馈，重新启动该子 agent |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "所有任务都并行更快" | 有顺序依赖的任务并行会出错 |
| "子 agent 不需要详细 prompt" | prompt 越具体，输出越可控 |
| "并行完直接合并就行" | 必须检查输出一致性再合并 |
| "agent 越多越好" | 2-4 个最高效，过多增加协调成本 |

## Convergence

当以下条件满足时完成：
1. 所有子 agent 已返回结果
2. 主 agent 已审查每个输出
3. 输出之间无不一致
4. 合并文件已生成
5. 向用户报告合并结果

## 衔接规则

### 触发方式
- 用户主动请求"并行/分工/同时做"
- 主 agent 识别当前阶段有可并行的独立子任务并建议

### 限制
- 不能跨 Hard Checkpoint 并行（必须先确认再继续）
- 并行完成后回到主 pipeline 的 Checkpoint 报告流程
