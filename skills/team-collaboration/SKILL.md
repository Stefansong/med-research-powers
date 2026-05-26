---
name: team-collaboration
description: Use when a research project benefits from multi-agent parallel work on independent subtasks. Triggers on "多人协作"、"并行分析"、"分工"、"同时做"、"parallel".
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
| `revision-response` 发现多个审稿人意见互相独立 | 每位审稿人的意见由一个子 agent 处理 | 不同审稿人可能要求修改同一段落 |
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

用 **Task 工具**并行派发多个 subagent —— 在同一轮里发起 N 个独立的 Task 调用，它们会并行执行。每个 Task 携带一段聚焦的 prompt，描述该 subagent 的角色和任务。例如：一个 Task 让生物统计专家完成 [具体任务]，另一个 Task 让医学写作专家完成 [具体任务]，再一个 Task 让审稿人模拟器完成 [具体任务]，三者同时运行。

**每个 Task 的 prompt 必须包含：**
1. 明确的角色定位
2. 具体的任务描述
3. 需要读取的输入文件
4. 需要生成的输出文件
5. 需要遵守的 SKILL.md 路径

> 注意：Claude Code 的子 agent 工具就是 **Task 工具**，没有 `Agent(...)` 这种 API。派发并行子任务一律通过 Task 工具。

### Step 3: 等待 + 合并

主 agent 等待所有子 agent 完成，然后：
- 审查每个子 agent 的输出
- 检查输出之间的一致性（如：数字是否对得上）
- 合并到主项目文件
- 向用户报告合并结果

## 场景模板

四个常用并行场景的 Task 派发模板（① 并行文献检索 ② 多审稿人模拟 4-Reviewer Panel ③ 并行修稿 ④ 多专家方案评审）见 `references/parallel-scenarios.md`。每个场景都用 Task 工具派发并行 subagent，并说明主 agent 如何合并结果。

> 多审稿人模拟（场景 2）固定派发 **4 个 subagent**：R1 方法学、R2 临床/领域、R3 学术编辑、R4 Devil's Advocate，与 `peer-review-simulation` 的 4-Reviewer Panel 一致。

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

## Output

主 agent 合并所有 subagent 的结果后生成 `team-collaboration-merge.md`，记录：每个 subagent 的任务与产出文件、一致性检查结论（数字是否对得上、有无冲突）、合并到主项目的内容、以及给用户的报告。各 subagent 自身的产出文件（如 `review-methods.md`、`pubmed-results.md` 等）由对应场景定义。

## Convergence

当以下条件满足时完成：
1. 所有子 agent（Task）已返回结果
2. 主 agent 已审查每个输出
3. 输出之间无不一致
4. 合并文件已生成
5. 向用户报告合并结果

## Red Flags — STOP

- 任务之间存在顺序依赖却强行并行 → 停止，改为顺序执行
- subagent 产出数字互相矛盾 → 不得直接合并，以 `analysis_script.py` 实际运行结果为准后再合并
- 试图跨 Hard Checkpoint 并行 → 阻止，必须先确认再继续
- 出现 `Agent(name=..., prompt=...)` 之类调用 → 错误，Claude Code 只有 Task 工具，立即改用 Task 派发

## 衔接规则

### 前置依赖
- 当前阶段必须已分解出**互不依赖**的子任务（无严格顺序依赖）

### 强制衔接
- `peer-review-simulation` 进入 4-Reviewer Panel → 自动用 Task 并行派发 4 个审稿人 subagent
- `literature-synthesis` 检索 ≥ 2 个数据库 → 自动用 Task 每库一个 subagent 并行检索
- 并行完成后 → 回到主 pipeline 的 Checkpoint 报告流程（不能跨 Hard Checkpoint 并行）

### 可选衔接
- `revision-response` 多审稿人意见互相独立 → 建议并行处理（需用户确认，可能改同段落）
- `study-design` 完成后需多专家评审 → 建议统计/方法学/AI 专家并行评审（需用户确认）
