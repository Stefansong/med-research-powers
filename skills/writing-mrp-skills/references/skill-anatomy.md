# SKILL.md 的结构与内容分层

`writing-mrp-skills` Workflow 第 3 步写 SKILL.md 时查这一页。

## 正文结构（每节都要有）

```markdown
# Skill Name
## Overview            一句话核心原则
## When to Use         触发条件
## When NOT to Use     排除条件（防误触发）
## Workflow            步骤化流程（主体）；最后一步 = 摘要 + 更新 .mrp-state.json
## Output              明确的输出文件名 + 模板（模板长的放 references/）
## Common Mistakes     | 想法 | 现实 | 表，≥ 3 条
## Convergence         明确的完成 / 退出条件
## Red Flags — STOP    触发停止的信号
## 衔接规则            ### 强制衔接 / ### 前置依赖 / ### 可选衔接（三级都要写，哪级为空就写"无"）
```

## 内容分层与体量

| 内容类型 | 放哪里 | 原因 |
|----------|--------|------|
| 推理逻辑、判断标准 | SKILL.md | Claude 每次都需要 |
| Checklist 完整条目、决策树、指标表 | `references/*.yaml` | 按需加载，省上下文 |
| 模板、长表格、按类型分的模块 | `references/*.md` | 同上 |
| 工具与护栏（见 SKILL.md"脚本与模板的边界"） | `scripts/*.py` | Claude 调用而不是重写；给 CLI 与 `--help` |
| 方法要点（必做步骤、常见坑、推荐包、必报内容） | `references/method-cards/*.md` 之类 | 写代码时遵守的要点，不是代码模板 |
