---
name: reporting-standards
description: Use when checking a manuscript item by item against its reporting guideline (called by pre-submission Gate 1 or on request). Triggers on "检查规范"、"报告规范"、"CONSORT"、"STROBE"、"PRISMA"、"TRIPOD"、"checklist".
---

# Reporting Standards

## Overview

逐条检查论文是否符合对应的报告规范，并产出可随稿提交的 checklist。用错规范等于没查；
没有位置标注的 ✅ 不算 ✅。

## When to Use

- 由 `pre-submission-verification` 的 Gate 1 **强制调用**（这是主要入口）
- 用户主动要求检查报告规范（"帮我过一遍 CONSORT"、`/mrp:check-standards`）时可单独触发

## When NOT to Use

- 论文仍在早期起草阶段（至少 Methods + Results 完成后再查）
- 选择研究设计阶段（→ `study-design`）；写 protocol 时用 SPIRIT 2025 / PRISMA-P，不用本 skill
- 统计、图表、伦理、字数等其他投稿门禁（→ `pre-submission-verification` Gate 2–6）

## Workflow

### Step 1: 确定研究类型 → 匹配规范

1. 先看 `study-protocol.md` 的 `type:` 字段和 Methods 里的设计描述；不确定就问用户，不要猜。
2. 加载 `references/checklists/standards-index.yaml`（47 条规范）查找对应条目；主规范 + `use_with`
   扩展一起列出。带 `type:` 字段的条目（`bias_tool` / `appraisal_tool` / `framework`，如 RoB 2、ROBINS-I、NOS、
   QUADAS-2、AMSTAR 2、GRADE、IDEAL）用来评价纳入研究或证据，不是报告规范，不能用来做稿件的报告完整性检查（Gate 1）。

核心路由（常用）：

| 研究类型 | 规范 | 本地逐条 checklist |
|---------|------|:---:|
| RCT | **CONSORT 2025**（⚠️ 不是 2010；30 项，含子项共 42 行） | ✅ `consort-2025.yaml` |
| 队列 / 病例对照 / 横断面 | STROBE | ✅ `strobe.yaml` |
| 系统综述 / Meta 分析 | PRISMA 2020 | ✅ `prisma-2020.yaml` |
| 诊断准确性 | STARD 2015 | ✅ `stard-2015.yaml` |
| 预测模型（回归 / 机器学习） | TRIPOD+AI 2024 | ✅ `tripod-ai.yaml` |
| 动物实验 | ARRIVE 2.0 | ✅ `arrive-2.yaml` |
| AI 医学影像 | CLAIM 2024（44 项） | ✅ `claim-2024.yaml` |
| AI 决策支持早期临床评估 | DECIDE-AI 2022 | ✅ `decide-ai.yaml` |
| LLM / VLM 评估 | TRIPOD-LLM 2025 | 索引 + 官方来源 |
| 手术 / 器械创新 | IDEAL | 索引 + 官方来源 |
| 问卷 / 网络调查 | CROSS 2021 / CHERRIES | ✅ `cross-2021.yaml` / `cherries.yaml` |
| 非劣效 / 等效 RCT | CONSORT 2025 + 非劣效扩展 | 主规范 ✅，扩展按官方来源 |
| AI 干预 RCT / 其 protocol | CONSORT-AI / SPIRIT-AI（+ SPIRIT 2025） | ✅ `consort-ai.yaml` / `spirit-ai.yaml` / `spirit-2025.yaml` |
| 常规数据 / 登记研究 | STROBE + RECORD | ✅ `record.yaml` |
| 范围综述 | PRISMA-ScR | ✅ `prisma-scr.yaml` |
| 经济学评价 / 质量改进 / 病例报告 | CHEERS 2022 / SQUIRE 2.0 / CARE | ✅ 各有本地清单 |

### Step 2: 加载 checklist

- 索引条目有 `file:` 字段（47 条中有 21 条有本地逐条清单：consort-2025、consort-ai、spirit-2025、spirit-ai、tidier、trend、record、strobe、prisma-2020、prisma-scr、stard、tripod-2015、tripod-ai、claim、decide-ai、arrive、cherries、cross、care、squire、cheers，文件名见索引 `file:`）→
  读取 `references/checklists/<file>`，按 `sections[].items[]` **逐行**检查；行的 `text` 就是官方条目原文。
- 索引条目没有 `file:` → 给出 `reference` 与 EQUATOR Network 链接，提示用户下载官方 checklist 人工
  核对；本 skill 只做按章节的粗检，**不要凭记忆编造条目文本**，也不能据此宣布 Gate 1 通过。
- 主规范 + 扩展（如 CONSORT 2025 + CONSORT-AI）：主规范逐条，扩展按上一条处理。

### Step 3: 逐条检查

对每一行标记，并写明论文中的位置（页码 + 章节/段落）：

- ✅ 已满足（必须有位置）
- ⚠️ 部分满足（说明缺什么）
- ❌ 未满足（给出具体修改建议：加在哪、加什么）
- N/A 不适用（必须写原因）

**Critical 的定义：** checklist YAML 中 `critical: true` 的条目（每个文件头部有说明；ARRIVE 2.0 的
Essential 10 全部为 critical）。**Gate 1 通过 = 0 个 critical ❌**；非 critical 的 ❌ 和 ⚠️ 写入报告、
建议修复，但不单独阻止。

### Step 4: 生成报告

输出两个文件（模板见 `references/output-templates.md`）：

1. `reporting-checklist-<standard>.md` —— 给期刊随稿提交，每行带页码/章节位置
2. `reporting-compliance-report.md` —— 给作者：计数表、critical ❌ 清单、其余 ❌/⚠️、N/A 理由、Gate 1 结论

### Step 5: 交回调用方

- critical ❌ > 0 → 回 `manuscript-writing` 修改对应章节，改完重跑本 skill
- critical ❌ = 0 → 把两个文件交给 `pre-submission-verification` Gate 1

## Output

| 文件 | 内容 | 读者 |
|------|------|------|
| `reporting-checklist-<standard>.md` | 逐条状态 + 论文位置（`<standard>` = 索引 id，如 `consort-2025`） | 期刊（随稿提交） |
| `reporting-compliance-report.md` | 计数表、critical ❌ 清单与修改建议、Gate 1 PASS/FAIL | 作者 / Gate 1 |

模板见 `references/output-templates.md`。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "用 CONSORT 2010 就行" | 2025 已正式取代 2010，期刊要求新版（30 项，含子项共 42 行） |
| "报告规范投稿后再查" | 不合规直接 desk reject，返工成本是现在的 10 倍 |
| "STROBE 和 CONSORT 差不多" | 完全不同的规范，用错等于没用 |
| "AI 研究不需要临床报告规范" | CLAIM 2024 / DECIDE-AI / TRIPOD+AI 2024 专门为 AI 医学研究设计 |
| "Checklist 打勾就行" | 必须标注论文中的具体位置（页码/段落），否则编辑退回 |
| "索引里有名字就能逐条查" | 47 条中只有 21 条有本地逐条 checklist（其余 26 条如 COREQ、SRQR、MOOSE、AMSTAR 2、QUADAS-2 等），其余要下载官方 checklist 人工核对 |
| "有几个 ❌ 也无所谓" | critical ❌ 一个都不能有；非 critical 的也会被审稿人挑出来 |

## Convergence

当以下条件全部满足时完成：
1. 已确定正确的报告规范（主规范 + 扩展）
2. 有本地 checklist 的规范：每一行都已标记状态和位置；无本地 checklist 的：已给出官方来源和人工核对提示
3. `reporting-compliance-report.md` 给出了 critical ❌ 数量和 Gate 1 结论
4. `reporting-checklist-<standard>.md` 已生成

## Red Flags — STOP

- 使用了 CONSORT 2010 / TRIPOD 2015 / PRISMA 2009 / STARD 2003 → 必须换新版
- 研究类型不确定 → 先确认再查
- 用户要求跳过某些条目 → 不可以，每条必须标记（至少标 N/A 并写原因）
- 想给没有本地 checklist 的规范"写几条差不多的条目" → 停止，改为引用官方来源

## 衔接规则

### 前置依赖
- **必须**有基本完成的论文（`manuscript/*.md`，至少 Methods + Results）
- 研究类型明确（`study-protocol.md` 的 `type:` 或用户说明）

### 强制衔接
- 由 `pre-submission-verification` Gate 1 调用 → 完成后把两个产物交回 Gate 1
- 任何 critical ❌ → 回 `manuscript-writing` 修改对应章节（缺的若是分析或图表本身，由
  `manuscript-writing` 再调用 `statistical-analysis` / `figure-generation`），改完重跑本 skill

### 可选衔接
- 研究类型 / 规范不确定 → 先回 `study-design` 确认设计
- 需把 checklist 随稿提交 → `submission-preparation` 一并打包
- AI 研究需配套规范 → 同时参照 CLAIM 2024 / DECIDE-AI / TRIPOD+AI（见 standards-index.yaml）
