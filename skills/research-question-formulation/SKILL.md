---
name: research-question-formulation
description: Use when a user has a vague research idea and needs to define a clear question and hypothesis. Triggers on "我想研究..."、"这个课题怎么样"、"帮我想想选题"、"研究方向"、"科学问题".
---

# Research Question Formulation

## Overview

不允许在科学问题不明确的情况下开始任何分析或写作。用户说"帮我分析数据"时，先问清研究问题。

## When to Use

- 用户有模糊的研究想法
- 需要从临床观察提炼科学问题
- "帮我分析数据"但没有明确假设

## When NOT to Use

- 已有明确的 PICO 和假设 → 直接进 `study-design`
- 纯技术问题（如何做某种统计）→ `data-analysis-planning`

## Workflow: Socratic Questioning

每轮不超过 2-3 个问题，逐步收敛：

### Round 1: PICO / PIRD

**干预性研究 → 使用 PICO：**
- **P** (Population) — 研究对象？纳入/排除标准？
- **I** (Intervention/Exposure) — 干预/暴露因素？
- **C** (Comparison) — 对照是什么？
- **O** (Outcome) — 主要结局指标？次要结局？

**AI 诊断准确性研究 → 使用 PIRD：**
- **P** (Population) — 目标患者群？
- **I** (Index test) — 被评估的诊断方法（如"深度学习分析术中超声"）？
- **R** (Reference standard) — 参考标准/金标准（如"术后病理"）？
- **D** (Diagnosis of interest) — 目标诊断（如"胶质瘤切除边界残留"）？

**判断标准：** 如果研究核心是"某种方法能否准确诊断/检测/分割某种疾病"→ 用 PIRD；如果研究核心是"某种干预是否改善结局"→ 用 PICO。

### Round 2: FINER
- **F** (Feasible) — 数据/样本可获得？资源够？
- **I** (Interesting) — 对领域有什么意义？
- **N** (Novel) — 跟已有研究的区别？
- **E** (Ethical) — 有无伦理问题？
- **R** (Relevant) — 对临床实践的指导意义？

### Round 3: Hypothesis
- 零假设和备择假设
- 预期结果
- 如果结果不符预期的可能解释

## Output

生成 `research-question.md`：科学问题（一句话）→ PICO 分解 → 研究假设（H0/H1）→ FINER 评分（1-5）→ 预期结果 → 潜在局限性

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "先跑数据看看有什么" | 没有假设的分析 = 数据钓鱼 |
| "研究问题太窄了不好发表" | 精确的问题远好于模糊的大问题 |
| "不需要对照组" | 没有 C 的 PICO 不完整 |
| "结局指标以后再定" | 事后选择结局 = 结果偏倚 |
| "FINER 评估不重要" | 可行性低的完美问题等于零 |

## Convergence

当以下 3 个条件**全部**满足时停止追问：
1. PICO 四要素全部明确
2. 研究假设可以用统计语言表述
3. 用户确认问题定义准确

## 衔接规则

### 强制衔接
- 完成后 → 建议 `literature-synthesis`（了解现状）或 `study-design`（设计研究，内置 type router 自动路由）

### 被其他 skill 调用
- `data-analysis-planning` 发现没有明确假设 → 触发本 skill
- `manuscript-writing` 发现没有 `research-question.md` → 触发本 skill
