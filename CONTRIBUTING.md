# Contributing to Med-Research-Powers

感谢你对 MRP 的贡献兴趣！以下是参与方式。

## 如何贡献

### 报告问题

在 GitHub Issues 中报告：
- Claude 跳过了某个应该触发的 skill
- Skill 内容有错误（如报告规范条目不准确）
- 脚本运行出错
- 建议新增的 skill 或改进

### 贡献新 Skill

1. Fork 仓库
2. 阅读 `skills/writing-mrp-skills/SKILL.md` 了解 skill 编写规范
3. 在 `skills/` 下创建新目录
4. 按规范编写 SKILL.md
5. 测试（至少 1 个真实场景）
6. 提交 PR

PR 说明需包含：
- 这个 skill 解决什么问题
- 没有它时 Claude 的典型错误
- 有了它后的改善

### 贡献专科扩展包

如果你是某个专科的医生/研究者，欢迎贡献专科特定的内容：
- 专科期刊配置（字数限制、参考文献格式）
- 专科特定的检索词和 MeSH terms
- 专科特定的评估工具或量表

放在 `packs/your-specialty/` 下。

## SKILL.md 规范速查

```yaml
---
name: kebab-case-name
description: Use when [条件]. Triggers on "[中文]"、"[英文]".
---
```

必须包含的部分：
- Overview（一句话）
- When to Use / When NOT to Use
- Workflow
- Common Mistakes 表
- Convergence 信号
- 衔接规则（强制/前置/可选）

不要在 description 中总结工作流。

## 代码风格

- Python 脚本遵循 PEP 8
- YAML 用 2 空格缩进
- Markdown 用 ATX 风格标题（`#`）

## 许可

贡献的内容将以 MIT License 发布。
