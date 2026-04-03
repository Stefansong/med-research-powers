---
name: writing-mrp-skills
description: Use when creating, testing, or improving a Med-Research-Powers skill. Triggers on "写新skill"、"创建技能"、"改进skill"、"贡献skill".
---

# Writing MRP Skills

## Overview

如何为 Med-Research-Powers 创建高质量的研究方法论 skill。
核心原则：如果你没看到 Claude 在没有这个 skill 时犯错，你就不知道 skill 应该教什么。

## SKILL.md 规范

### Frontmatter

```yaml
---
name: kebab-case-name
description: Use when [specific triggering conditions]. Triggers on "[中文触发词]"、"[英文触发词]".
---
```

**Description 规则：**
- 以 "Use when [条件]" 开头
- 包含中文触发词（用户多用中文）
- **绝不总结工作流**（否则 Claude 按 description 走捷径）
- 长度 ≤ 200 字符

### 正文结构

```markdown
# Skill Name

## Overview
一句话核心原则。

## When to Use
触发条件列表。

## When NOT to Use
排除条件（防止误触发）。

## Workflow
步骤化流程——这是 skill 的主体。

## Output
明确的输出文件名和格式模板。

## Common Mistakes
| 想法 | 现实 |
|------|------|
（每个 skill 至少 3 条）

## Convergence
何时这个 skill 的任务完成了——明确的退出条件。

## Red Flags — STOP
触发停止的信号。

## 衔接规则
### 强制衔接（不可跳过）
### 前置依赖（不满足则阻止）
### 可选衔接
```

### 内容分层

| 内容类型 | 放哪里 | 原因 |
|---------|--------|------|
| 推理逻辑、判断标准 | SKILL.md | Claude 每次都需要 |
| Checklist 完整条目 | references/*.yaml | 按需加载，节省上下文 |
| 决策树、指标表 | references/*.yaml | 同上 |
| 实验设计模板 | references/*.md | 同上 |
| 可复用的固定代码 | scripts/*.py | Claude 调用而非重写 |

### 质量标准

- [ ] Description 不总结工作流
- [ ] 有 Common Mistakes 表（≥3 条）
- [ ] 有明确的 Convergence 条件
- [ ] 有 Red Flags 列表
- [ ] 衔接分为"强制/前置依赖/可选"三级
- [ ] 查阅型内容在 references/，不在 SKILL.md
- [ ] 固定代码在 scripts/，不在 SKILL.md

## 测试方法

1. 给出一个典型研究场景
2. **不加载 skill** → 观察 Claude 默认行为（基线）
3. **加载 skill** → 观察行为变化
4. 如果变化不显著 → 重写 skill
5. 记录 Claude 的"借口"（Common Mistakes 的来源）

## 贡献流程

1. Fork med-research-powers 仓库
2. 在 `skills/` 下创建新目录
3. 按上述规范编写 SKILL.md
4. 测试（至少 1 个场景）
5. 提交 PR，说明：
   - 这个 skill 解决什么问题
   - 没有它时 Claude 的典型错误
   - 有了它后的改善
