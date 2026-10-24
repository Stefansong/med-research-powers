---
name: writing-mrp-skills
description: Use when creating, testing, or improving a Med-Research-Powers skill. Triggers on "写新skill"、"改进skill"、"skill 不触发"、"skill 太长"、"write a new MRP skill"、"improve this skill"、"skill not triggering".
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
3. **按正文结构写 SKILL.md**，推理与判断放正文，查阅型内容放 `references/`，只有工具和护栏放 `scripts/`（见下方"脚本与模板的边界"）。凡是要结合真实数据或需求的 skill，Workflow 必须按"先分析真实情况 → 再计划 → 用户决定 → 再执行"排步骤。
4. **接上流水线**：在衔接规则里写清强制 / 前置依赖 / 可选三级（前置产物缺失一律按总调度的"缺前置产物时"规则，不写"不满足则阻止"），并让上下游 skill 与总调度（`using-med-research-powers`）的 Pipeline 和回溯表 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/references/backtracking.md` 一致；主线 skill 的最后一步固定为"输出摘要 → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py done ...`"（插件脚本一律写全路径，skill 单独加载时也能运行），用户只要一个产物时交付后停下。用到总调度规则的 skill 在 Overview 后用**一行**点名这些规则并指向 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`（照抄现有 skill 的"总调度规则"那一行），这样直接调用该 skill 时规则也在，但不复制全文。
5. **自检**：`python3 tools/check_consistency.py`（版本、计数、路径、frontmatter、行数、命令前缀、每个 skill 至少一个评测用例）+ `python3 -m pytest tests -q`。
6. **对比测试**：同一场景加载 skill 后再跑一次；变化不显著就重写。加评测用例 `evals/<case>/`（写法见 `evals/README.md`）：`tool_used: Skill` 的路由 grader 在两臂（with / without plugin）运行里只作指标、不计分，所以路由用例只按单臂（`--ablation none`）读；要证明插件有用，再加一个确定性的结果 grader（`regex` 查回复里只有按 skill 做才会出现的内容，或 `tool_used` 查调用了插件脚本）。

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

### 正文结构与内容分层

九个固定小节（Overview … 衔接规则）和"什么内容放 SKILL.md / references / scripts"的对照表见 `references/skill-anatomy.md`；SKILL.md 只放 Claude 每次都要用的推理与判断。

### 脚本与模板的边界

- **AI 现写**（随数据和问题变化）：清洗代码、分析代码、建模、出表、作图代码、CRF/标注表的具体字段、论文内容。不要为这些写"通用脚本"或"骨架模板"让 Claude 填空。
- **scripts/ 只放四类**：容易算错且错了看不出来的公式（样本量，优先包装成熟包）；一旦出错研究作废的护栏（患者级划分泄漏检查、随机分组）；与数据无关的基础设施（状态、期刊模板查询、导出）；只报告、不替用户做决定的检查工具（数据体检、前提检验、重跑一致性）。
- **模板 = 必须覆盖的清单**：protocol 章节、SAP 章节、图型表、工具目录都只用来查漏；不适用的写"不适用 + 理由"；示例里不放会被照抄的具体数字（用 `[按……填写]` 占位）。

- **SKILL.md ≤ 500 行**（官方建议）；MRP 目标 ≤ 250 行。超了就把按类型分的模块拆到 references 下的 modules 子目录（study-design 是范例），SKILL.md 只留 router。
- 大文件（如 240 条期刊库）必须提供按 id 抽取的脚本或 grep 命令，**禁止让 Claude 整读**。
- 脚本路径一律 `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<file>.py`；运行目录是用户项目，不是插件目录，绝不把一个相对目录名（如 scripts）塞进 sys.path。
- 用户项目里的分析 / 作图代码要能脱离插件复现：要用插件里的 Python 模块时，SKILL.md 让 Claude 先 `cp "${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<module>.py" .` 再从项目里的副本 import，不从插件安装路径 import（范例：statistical-analysis 的 `assumption_tests.py`、figure-generation 的 `pub_style.py`）；这样的模块必须是单文件、运行时不读插件里的其他文件。只在命令行跑一次、结果写进日志的检查工具可以直接用插件路径。
- 跨 skill 引用文件也用 `${CLAUDE_PLUGIN_ROOT}/skills/<other-skill>/...`，不用 `../`。

## Output

- 新目录 `skills/<name>/`：`SKILL.md`（必有）+ `references/`、`scripts/`（按需）。
- 如新增脚本：`tests/test_<script>.py` 最小冒烟测试。
- 至少一个评测用例 `evals/route-<name>/`（`tool_used: Skill` grader，`min: 1`，`input_match` 写出 skill 名），并更新 `evals/README.md` 的用例数和标签表（守卫会核对）。
- 同步更新的文件（守卫从仓库数出计数，再核对文档里写的数字与引用）：`README.md`、`README_CN.md`、`docs/architecture.md`、`docs/USER-MANUAL.md`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 的 skill 数或脚本表；见 CONTRIBUTING.md 的清单。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "description 把流程写清楚 Claude 就会照做" | Claude 会只看 description 走捷径；description 只写何时用 |
| "内容都放 SKILL.md 方便看" | 每行都是常驻 token；查阅型内容放 references/ 按需读 |
| "写个通用分析脚本，Claude 改改变量名就能跑" | 真实数据千差万别；分析代码按数据现写，scripts/ 只放工具和护栏 |
| "写个 command 和 skill 同名方便调用" | 同名 command 被 skill 遮蔽，还让 skill 列表出现重复条目 |
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
- 想验证触发准确率 → `claude plugin eval`（命令和两臂 / 单臂的读法见 `evals/README.md`）；想做多场景对比 → `team-collaboration` 并行跑基线与加载版。

## 贡献流程

按上面的 Workflow 写并测过 → 提 PR；PR 说明和提交前检查见仓库 `CONTRIBUTING.md`（"贡献新 Skill"与 PR Checklist）。
