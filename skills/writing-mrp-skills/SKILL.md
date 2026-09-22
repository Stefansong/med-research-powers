---
name: writing-mrp-skills
description: Use when creating, testing, or improving a Med-Research-Powers skill. Triggers on "写新skill"、"创建技能"、"改进skill"、"贡献skill"、"skill 不触发"、"skill 太长".
---

# Writing MRP Skills

## Overview

如何为 Med-Research-Powers 写一个真正改变 Claude 行为的方法论 skill。
核心原则：**如果你没看到 Claude 在没有这个 skill 时犯错，你就不知道 skill 应该教什么。**

## When to Use

- 要新增一个 skill，或把一段反复出现的方法学要求固化成 skill。
- 现有 skill 触发不准（该触发不触发、不该触发乱触发）、太长、引用路径失效、与其他 skill 冲突。
- 提交 PR 之前的自检。

## When NOT to Use

- 只是改一处错别字或一个数字——直接改，跑一遍守卫即可。
- 想改的是用户项目里的 CLAUDE.md 或个人 skill，而不是 MRP 仓库。

## Workflow

1. **先找到错误**：给一个典型研究场景，不加载 skill 观察 Claude 的默认行为，记下它的"借口"（这是 Common Mistakes 表的来源）。
2. **写 frontmatter**（规则见下）。
3. **按正文结构写 SKILL.md**，推理与判断放正文，查阅型内容放 `references/`，固定代码放 `scripts/`。
4. **接上流水线**：在衔接规则里写清强制 / 前置依赖 / 可选三级，并让上下游 skill 与总调度（`using-med-research-powers`）的 Pipeline 一致；主线 skill 的最后一步固定为"输出摘要 → `mrp_state.py done ...`"。
5. **自检**：`python3 tools/check_consistency.py`（版本、计数、路径、frontmatter、行数、命令前缀）+ `python3 -m pytest tests -q`（若改了脚本）。
6. **对比测试**：同一场景加载 skill 后再跑一次；变化不显著就重写。官方 `claude plugin eval` 可把"5 个提示词是否触发正确 skill"做成回归。

### Frontmatter 规则

```yaml
---
name: kebab-case-name          # 必须等于目录名
description: Use when [触发条件]. Triggers on "[中文触发词]"、"[英文触发词]".
---
```

- `description` 以 "Use when" 开头，含中文触发词，≤ 200 字符，**不总结工作流**（否则 Claude 按 description 走捷径而不读正文）。
- 触发词不要与相邻 skill 同义（例如"投稿"不能同时出现在 4 个 skill 里）；写清边界（"已有 analysis-plan.md 时" vs "没有时"）。
- 不要写 `mcp__claude_ai_PubMed__` 这类硬编码工具前缀；写"PubMed MCP 的 `search_articles`（前缀以会话工具列表为准）"。

### 正文结构（每节都要有）

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

### 内容分层与体量

| 内容类型 | 放哪里 | 原因 |
|----------|--------|------|
| 推理逻辑、判断标准 | SKILL.md | Claude 每次都需要 |
| Checklist 完整条目、决策树、指标表 | `references/*.yaml` | 按需加载，省上下文 |
| 模板、长表格、按类型分的模块 | `references/*.md` | 同上 |
| 可复用的固定代码 | `scripts/*.py` | Claude 调用而不是重写；给 CLI 与 `--help` |

- **SKILL.md ≤ 500 行**（官方建议）；MRP 目标 ≤ 250 行。超了就把按类型分的模块拆到 references 下的 modules 子目录（study-design 是范例），SKILL.md 只留 router。
- 大文件（如 240 条期刊库）必须提供按 id 抽取的脚本或 grep 命令，**禁止让 Claude 整读**。
- 脚本路径一律 `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<file>.py`；Python 里用
  `sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), "skills", "<skill>", "scripts"))`，
  绝不把一个相对目录名（如 scripts）直接塞进 sys.path——运行目录是用户项目，不是插件目录。
- 跨 skill 引用文件也用 `${CLAUDE_PLUGIN_ROOT}/skills/<other-skill>/...`，不用 `../`。

## Output

- 新目录 `skills/<name>/`：`SKILL.md`（必有）+ `references/`、`scripts/`（按需）。
- 如新增脚本：`tests/test_<script>.py` 最小冒烟测试。
- 同步更新的文件（守卫会检查计数与引用）：`README.md`、`README_CN.md`、`docs/architecture.md`、`docs/USER-MANUAL.md`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 的 skill 数或脚本表，`tools/check_consistency.py` 的 `EXPECTED`；见 CONTRIBUTING.md 的清单。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "description 把流程写清楚 Claude 就会照做" | Claude 会只看 description 走捷径；description 只写何时用 |
| "内容都放 SKILL.md 方便看" | 每行都是常驻 token；查阅型内容放 references/ 按需读 |
| "写个 command 和 skill 同名方便调用" | 同名 command 被 skill 遮蔽，还让 skill 列表出现重复条目 |
| "路径写相对的就行" | 运行目录是用户项目，相对路径解析失败；必须用 `${CLAUDE_PLUGIN_ROOT}` |
| "规范条目数我记得是 N" | 报告规范条目数、期刊字数限制等必须查原文并写来源 |

## Convergence

- 守卫与测试全绿；
- 同一场景下加载 skill 前后 Claude 的行为有可观察的差别（至少一个"借口"被消除）；
- 上下游 skill 与总调度 Pipeline 对该 skill 的产物名、位置、衔接说法一致。

## Red Flags — STOP

- 想在 SKILL.md 里内嵌一个 100 行以上的代码块 → 抽成 `scripts/`。
- 想凭记忆写某个报告规范的逐条清单 → 先拿到原文（PubMed MCP 全文 / 官方 PDF）。
- 新 skill 的触发词与已有 skill 重叠 → 先改 description 边界，再考虑是否真的需要新 skill。

## 衔接规则

### 强制衔接
- 新增或改名 skill 后必须运行 `tools/check_consistency.py` 并更新 CONTRIBUTING 清单中的文件。

### 前置依赖
- 无（元 skill）。

### 可选衔接
- 想验证触发准确率 → `claude plugin eval`（见官方文档）；想做多场景对比 → `team-collaboration` 并行跑基线与加载版。

## 贡献流程

1. Fork 仓库，在 `skills/` 下创建新目录，按上述规范编写。
2. 测试至少 1 个场景（基线 vs 加载）。
3. 提交 PR，说明：这个 skill 解决什么问题；没有它时 Claude 的典型错误；有了它后的改善；守卫与测试结果。
