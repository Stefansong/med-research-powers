---
name: reporting-standards
description: Use when checking manuscript compliance with reporting guidelines before submission. Triggers on "检查规范"、"CONSORT"、"STROBE"、"PRISMA"、"checklist"、"报告规范"、"投稿前检查"、"DECIDE-AI"、"IDEAL".
---

# Reporting Standards

## Overview

逐条检查论文是否符合对应的报告规范。大多数期刊要求随稿提交 checklist。

## When to Use

- 论文起草完成，准备投稿前
- 用户主动要求检查报告规范
- `manuscript-writing` 完成后（强制触发）

## When NOT to Use

- 论文仍在早期起草阶段（等各章节完成后再查）
- 选择研究设计阶段（→ 用 `study-design` 或 `ai-medical-study-design`）

## Workflow

### Step 1: 确定研究类型 → 匹配规范

加载 `references/checklists/standards-index.yaml` 查找对应规范。

核心路由（常用）：
- RCT → **CONSORT 2025**（⚠️ 不是 2010）
- 观察性 → STROBE
- 系统综述 → PRISMA 2020
- 诊断 → STARD 2015
- AI 预测 → TRIPOD+AI 2024
- AI 决策支持 → DECIDE-AI 2022
- 手术创新 → IDEAL
- 动物实验 → ARRIVE 2.0

### Step 2: 加载完整 checklist

读取 `references/checklists/` 目录中对应的 YAML 文件获取逐条检查项。

### Step 3: 逐条检查

对每一条标记：
- ✅ 已满足（标注论文位置：页码/章节/段落）
- ⚠️ 部分满足（说明缺什么）
- ❌ 未满足（给出修改建议）
- N/A 不适用（说明原因）

### Step 4: 生成报告

输出两个文件：

1. **规范检查报告**（给作者）— 含完成度、逐条状态、修改建议
2. **投稿 checklist**（给期刊）— 标注每条在论文中的页码/段落位置

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "用 CONSORT 2010 就行" | 2025 已正式取代 2010，期刊要求新版（30 项） |
| "报告规范投稿后再查" | 不合规直接 desk reject，返工成本是现在的 10 倍 |
| "STROBE 和 CONSORT 差不多" | 完全不同的规范，用错等于没用 |
| "AI 研究不需要临床报告规范" | CLAIM/DECIDE-AI/TRIPOD-AI 专门为 AI 医学研究设计 |
| "Checklist 打勾就行" | 必须标注论文中的具体位置（页码/段落），否则编辑退回 |

## Convergence

当以下条件全部满足时完成：
1. 已确定正确的报告规范
2. 每个 checklist 条目都已标记状态
3. 0 个 Critical ❌ 项（如有则必须修复后重查）
4. 已生成格式化的 checklist 文件

## Red Flags — STOP

- 使用了 CONSORT 2010 → 必须换 CONSORT 2025
- 研究类型不确定 → 先确认再查，用错规范等于没查
- 用户要求跳过某些条目 → 不可以，每条必须标记（至少标 N/A）

## 衔接规则

### 前置依赖
- **必须**有基本完成的论文（至少 Methods + Results）

### 强制衔接
- 发现 ❌ 涉及方法描述 → **必须**回 `manuscript-writing` 修改
- 发现 ❌ 涉及统计 → **必须**回 `statistical-analysis` 补充
- 发现 ❌ 涉及图表 → **必须**回 `figure-generation` 补充
- 本 skill 完成后 → 结果传入 `pre-submission-verification` 的 Gate 1
