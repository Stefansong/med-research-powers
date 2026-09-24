# Med-Research-Powers 用户手册

> **版本**: v6.4.1 | **仓库**: https://github.com/Stefansong/med-research-powers

本手册只讲"怎么装、怎么用、出了问题怎么办"。skill 清单、命令表、报告规范表、期刊库这些参考内容都在 [README_CN.md](../README_CN.md)（英文版 [README.md](../README.md)），这里只给链接，不再复制一遍。

---

## 目录

1. [这是什么](#1-这是什么)
2. [安装](#2-安装)
3. [快速开始](#3-快速开始)
4. [完整工作流](#4-完整工作流pipeline)
5. [Skill、命令与参考资料](#5-skill命令与参考资料)
6. [内置脚本怎么调用](#6-内置脚本怎么调用)
7. [常见场景示例](#7-常见场景示例)
8. [常见问题 FAQ](#8-常见问题-faq)
9. [故障排查](#9-故障排查)

---

## 1. 这是什么

Med-Research-Powers（MRP）是一套**医学科研方法论框架**，以 Claude Code 插件的形式运行。它解决一个核心问题：

> AI 辅助写代码时会跳步骤、不测试、不规划。AI 辅助做科研时也一样——跳过文献调研、用错统计方法、忽略报告规范、生成不可复现的分析。

MRP 用 **20 个 skill** 覆盖从"我想研究一个课题"到"论文投出去"的完整流程，并在 3 个关键节点要求你明确同意——研究方案、分析计划、投稿前核验报告。机制是提示词层面的引导：Claude 被指示不跳步、不越过节点，但这不是代码级的拦截。

### 与其他工具的区别

| 特性 | 通用学术框架 | Med-Research-Powers |
|------|------------|-------------------|
| 报告规范 | 不覆盖或仅提 APA | 47 项报告规范（CONSORT 2025、DECIDE-AI、IDEAL……） |
| 伦理审查 | 不涉及 | 主线上有 research-ethics：收集数据前检查 IRB/IACUC、知情同意、数据隐私 |
| 实验设计 | 不涉及 | WB/qPCR/动物实验设计模板 |
| 样本量计算 | 不涉及 | 内置 5 种场景的 Python 脚本 |
| 统计假设检验 | 不涉及 | 内置自动检验 + 方法推荐脚本 |
| 研究类型路由 | 通用 | 统一 study-design 路由：临床 / 基础 / AI-ML / 定性 / 问卷 |
| 投稿验证 | 基本检查 | 6-Gate（含 Claim Verification 防 AI 幻觉） |
| 审稿模拟 | 基本 | 4 审稿人（含 Devil's Advocate）+ 0-100 评分 |

### 设计灵感

MRP 的架构灵感来自 [Superpowers](https://github.com/obra/superpowers)——一套软件工程方法论框架。核心理念相同：**先想后做、流程引导、质量门控**。只是把"先写测试再写代码"换成了"先写分析计划再跑统计"。

---

## 2. 安装

插件名是 `mrp`，marketplace 名是 `med-research-powers`，所以安装 id 是 `mrp@med-research-powers`，命令前缀是 `/mrp:`。

### 方式 1：从 GitHub 安装（推荐）

在 Claude Code 里输入两条命令：

```
/plugin marketplace add Stefansong/med-research-powers
/plugin install mrp@med-research-powers
```

以后更新：`/plugin update mrp@med-research-powers`。

### 方式 2：从本地克隆安装

```bash
git clone https://github.com/Stefansong/med-research-powers.git
```

```
/plugin marketplace add ./med-research-powers
/plugin install mrp@med-research-powers
```

开发调试时可以不安装、临时加载：`claude --plugin-dir ./med-research-powers`。

### 方式 3：安装脚本

```bash
git clone https://github.com/Stefansong/med-research-powers.git
cd med-research-powers
./install.sh                # 交互式选择
./install.sh --method 1     # 非交互：插件安装（有 claude 命令行就直接执行，没有就打印上面两条命令）
./install.sh --method 2     # 非交互：把整个仓库软链到 ~/.claude/skills/med-research-powers
```

方式 2 的软链接会被 Claude Code 当作插件 `mrp@skills-dir` 加载：session hook 和 `${CLAUDE_PLUGIN_ROOT}` 都有效，改源文件立即生效，适合开发。脚本最后会检查 `requirements.txt` 里的 Python 包，缺哪个提示哪个（例如 `python-docx`，不是 `docx`）。

> **Windows**：请用方式 1 或 2。Git Bash 下的 `ln -s` 只是复制，不会随仓库更新，脚本会自动改走插件方式。

### 从 6.2.x 升级

6.3 起插件名从 `med-research-powers` 改成了 `mrp`。旧版本要先卸载，再按上面任一方式安装：

```
/plugin uninstall med-research-powers@med-research-powers
```

旧版本放在项目目录里的 `.mrp-user-profile.json` 不再读取；6.3 起的用户画像是全局文件 `~/.claude/mrp-user-profile.json`，各 skill 用到某个字段时才会问你一次（见 README 的 "User Memory"）。

### 验证安装

```bash
claude plugin list
```

列表里应该有 `mrp@med-research-powers`（或 `mrp@skills-dir`）。然后新开一个会话，输入 `/mrp:research-question` 或直接说"帮我设计一个研究"。

> session-start hook 的输出是加进 Claude 上下文的，**不会显示给你**，所以"看到引导信息"不是验证方法，`claude plugin list` 才是。

### Python 依赖（可选）

MRP 的 skill 本身不依赖 Python。要用内置脚本（数据体检、重跑核对、前提检验、样本量、绘图、.docx 导出、期刊模板抽取、患者级划分、随机分组、流程状态）时安装：

```bash
pip install -r requirements.txt
```

包含：scipy、statsmodels、matplotlib、pandas、numpy、python-docx、openpyxl、pyyaml。

### 卸载

```
/plugin uninstall mrp@med-research-powers
```

软链接方式：`rm ~/.claude/skills/med-research-powers`。项目里的 `.mrp-state.json` 和全局的 `~/.claude/mrp-user-profile.json` 可自行删除。

---

## 3. 快速开始

### 3 分钟体验

1. 在 Claude Code 中说：**"我想研究 AI 辅助前列腺 MRI 诊断的准确性"**
2. Claude 会自动调用 `research-question-formulation`，按 PICO 框架逐步追问
3. 追问完成后生成 `research-question.md`
4. Claude 给出 3–5 行摘要，然后进入 `literature-synthesis`；到 `study-design` 生成 `study-protocol.md` 时停下来等你批准（确认节点 1）

### 7 个命令

| 你想做什么 | 输入什么 |
|-----------|---------|
| 构建研究问题 | `/mrp:research-question` 或"帮我想想选题" |
| 分析数据 | `/mrp:analyze-data`——没有 `analysis-plan.md` 先做计划，有了就执行统计 |
| 写论文 | `/mrp:write-manuscript` 或"帮我写 Introduction" |
| 模拟审稿 | `/mrp:peer-review` 或"帮我审一下" |
| 只查报告规范 | `/mrp:check-standards`（Gate 1 的内容） |
| 投稿前完整核验 | `/mrp:pre-submission`（6 道关卡，投稿前必做） |
| 看路由 / 从上次继续 | `/mrp:using-mrp` |

其余 skill 直接用 `/mrp:<skill 名>` 调用，例如 `/mrp:study-design`、`/mrp:journal-selection`、`/mrp:manuscript-export`。命令只能你手动调用，不会和 skill 重复触发。

---

## 4. 完整工作流（Pipeline）

```
research-question-formulation
→ literature-synthesis
→ study-design                      [确认节点 1：study-protocol.md]
→ research-ethics                   （伦理批准 / 注册在收集数据之前）
→ journal-selection                 （暂定目标期刊，软确认，随时可换）
→ data-analysis-planning            [确认节点 2：analysis-plan.md]
→ data-collection-tools             （只在数据还没收集时；已有数据跳过）
→ [你收集数据]
→ statistical-analysis
→ figure-generation
→ manuscript-writing
→ peer-review-simulation
→ pre-submission-verification       [确认节点 3：submission-readiness-report.md，6 道关卡]
→ manuscript-export
→ submission-preparation
→ [投稿] → revision-response
```

### 3 个必须确认的节点

| # | 节点 | 你确认什么 |
|---|------|-----------|
| 1 | `study-protocol.md` | 研究类型、主要结局、对照——事后改主要结局就是 outcome switching |
| 2 | `analysis-plan.md`（SAP） | 统计方法、分析策略——之后的每处偏离都要记录 |
| 3 | `submission-readiness-report.md` | 6 道关卡全部通过——通过前不导出、不投稿 |

目标期刊是软确认：`journal-selection` 早期给一个暂定期刊，写作前和投稿前各复核一次。

### 确认方式

- **轻量确认（默认）**：每个 skill 完成后 Claude 给 3–5 行摘要（产物、关键决策、待注意）然后继续，只在 3 个节点等你。
- **逐步确认**：说"逐步确认"或"每步问我"，每步都等你。
- **一直做到底**：说"一直做到底"，3 个节点只提示不等待，但该由你确认的内容仍会写进产物。
- 随时说"回到 `<skill>`"回溯。

### 哪些事走流程

研究流程级的任务（选题、设计、分析、写作、投稿、修稿）进入 MRP 流程；单点小问题（改一句话、算一个数）直接回答，不走流程。

### 会话恢复

每个主线 skill 结束时会更新项目目录里的 `.mrp-state.json`。新会话开始时 hook 读取其中的项目名、当前阶段和下一步，Claude 会问"上次做到 X，下一步是 Y，继续吗？"。hook 只读这几个短字段、不执行文件里的任何内容（见 [SECURITY.md](../SECURITY.md)）。

---

## 5. Skill、命令与参考资料

这些内容 README 里已经有完整版本，这里只给入口：

- **20 个 skill 的用途与产物**：README_CN 的 [20 个 Skill](../README_CN.md#20-个-skill)（分基础 / 分析 / 稿件 / 投稿 / 工具 / 元六层）。
- **7 个命令**：README_CN 的 [7 个斜杠命令](../README_CN.md#7-个斜杠命令)。
- **研究设计路由（Type A–E）**：README_CN 的 [研究设计路由](../README_CN.md#研究设计路由type-ae)。
- **6 道投稿前关卡与引用核验状态**：README_CN 的 [6 道投稿前核验](../README_CN.md#6-道投稿前核验)。
- **4 位审稿人与评分**：README_CN 的 [同行评审模拟](../README_CN.md#4-位审稿人同行评审模拟)。
- **47 项报告规范**：README_CN 的 [报告规范](../README_CN.md#报告规范47)；机读索引在 `skills/reporting-standards/references/checklists/standards-index.yaml`，CONSORT 2025 逐条清单在同目录 `consort-2025.yaml`（30 项，含子项共 42 行）。
- **240 本期刊模板**：README_CN 的 [期刊模板](../README_CN.md#期刊模板240)；数据文件 `skills/manuscript-writing/references/journal-templates.yaml`（IF/APC 标注了年份，引用前请复核）。
- **统计方法覆盖**：README_CN 的 [统计方法覆盖范围](../README_CN.md#统计方法覆盖范围)；决策树 `skills/data-analysis-planning/references/stat-method-decision-tree.yaml`。
- **架构图**：[architecture.md](architecture.md)。

---

## 6. 内置脚本怎么调用

10 个脚本的清单和用途见 README_CN 的 [内置 Python 脚本](../README_CN.md#内置-python-脚本)。调用时**永远**通过 `${CLAUDE_PLUGIN_ROOT}`——这是 Claude Code 在插件运行时设置的安装目录。运行目录通常是你的项目，所以只写 `'scripts'` 这种相对路径一定找不到模块。

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), "skills", "statistical-analysis", "scripts"))
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), "skills", "figure-generation", "scripts"))

# 前提检验 + 方法推荐（assumption_tests.py）
from assumption_tests import full_check, effect_size_cohens_d
result = full_check(group1, group2, paired=False)
print(result['recommended_test'])          # e.g. "Independent t-test"
# ↑ 只作描述、记入分析日志；用哪个检验以 SAP 为准（两组独立默认 Welch），不按这里的推荐临时换检验
d = effect_size_cohens_d(group1, group2)
print(f"Cohen's d = {d['cohens_d']} ({d['magnitude']})")

# 样本量（power_analysis.py）
from power_analysis import two_groups, diagnostic, survival
r = two_groups(effect_size=0.5, power=0.80, dropout=0.15)   # → n_per_group=64, adjusted=76
r = diagnostic(sensitivity=0.90, prevalence=0.3, precision=0.05)
r = survival(hazard_ratio=0.7, event_rate=0.4)             # 事件数按 Schoenfeld 公式，1:1 时约 247 例事件

# 期刊风格（pub_style.py）
from pub_style import setup, save_figure
colors, width = setup(journal='nature', single_column=True)  # nature / lancet / jama / nejm / default
save_figure(fig, 'figure1', formats=('tiff', 'pdf'))
```

命令行方式也一样加前缀，例如：

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py" --id european-urology
```

### 主要参考文件

| 文件 | 位置 | 内容 |
|------|------|------|
| `standards-index.yaml` | reporting-standards/references/checklists/ | 47 项报告规范的主索引 |
| `consort-2025.yaml` | reporting-standards/references/checklists/ | CONSORT 2025 逐条清单（30 项，含子项共 42 行） |
| `stat-method-decision-tree.yaml` | data-analysis-planning/references/ | 统计方法选择指南 |
| `omics-methods.md` | data-analysis-planning/references/ | 组学分析流程 |
| `metrics-and-reporting.yaml` | study-design/references/ | AI 研究指标 + 规范映射 |
| `survey-reference.yaml` | study-design/references/ | 问卷/Delphi 设计参考表（Type E） |
| `experiment-templates/` | study-design/references/ | WB、qPCR、动物实验设计模板 |
| `journal-templates.yaml` | manuscript-writing/references/ | 240 本期刊格式模板 |
| `state-schemas.md` | using-med-research-powers/references/ | `.mrp-state.json` 与用户画像的 schema |
| `backtracking.md` | using-med-research-powers/references/ | 发现上游问题时回到哪个 skill（当前阶段 × 问题 → 回溯目标） |

---

## 7. 常见场景示例

### 场景 1：从零开始一个 AI 影像诊断研究

```
你："我想做一个用 AI 辅助前列腺 MRI PI-RADS 评分的研究"
```

MRP 会依次触发：
1. `research-question-formulation` → PICO 追问 → `research-question.md`
2. `literature-synthesis` → 检索 + 研究空白
3. `study-design`（路由到 Type C: AI/ML）→ 识别为"AI 辅助诊断" → 推荐 STARD + CLAIM 2024 → 讨论 ground truth 标注方案 → `study-protocol.md`，**停下来等你批准**
4. `research-ethics` → 回顾性影像数据的伦理豁免 / 批准、数据去标识 → `ethics-statement.md`
5. `journal-selection` → 暂定期刊
6. `data-analysis-planning` → SAP：AUROC + DCA + 亚组分析 → `analysis-plan.md`，**停下来等你批准**
7. ……后续跟着 pipeline 走

### 场景 2：论文写完了要投稿

```
你："论文差不多写完了，帮我检查一下再投 BJU International"
```

MRP 先跑 `peer-review-simulation`（4 位审稿人 + 评分，报告 `peer-review-simulation-report.md`），修完 Critical/Major 问题后跑 `pre-submission-verification`：
- Gate 1：检查 STARD / CLAIM / STROBE（取决于研究类型）
- Gate 2：统计完整性
- Gate 3：引用真实性（配置了 PubMed MCP 就自动核验，否则用 DOI / 网络检索核对）、数据一致性
- Gate 4–6：图表、伦理、形式

6 道关卡都过、你确认 `submission-readiness-report.md` 之后，才进入 `manuscript-export`（生成 `manuscript.docx`）和 `submission-preparation`（投稿信）。

### 场景 3：收到审稿意见

```
你："收到 BJU Int 的大修意见，审稿人要我补亚组分析和解释样本量偏小的问题"
```

MRP 触发 `revision-response`：
- 逐条分类意见 → `revision-plan.md`
- 补充亚组分析 → 调用 `statistical-analysis`，并标注为 post hoc / 探索性分析、记录 SAP 偏离
- 生成 `response-letter.md`（逐条回复 + 修改位置）和 `revision-tracking.md`
- 修改后再跑一次 `pre-submission-verification`

### 场景 4：设计智能穿刺针的可行性研究

```
你："我想发表智能 PCNL 穿刺针的概念验证数据"
```

MRP 识别为器械创新 → `study-design`（路由到 Type C: AI/ML，含器械/IDEAL 路径）→ IDEAL 框架 → 定位为 Stage 1 (Idea) → 建议写 case report / case series 格式 → 参考 CARE 规范

---

## 8. 常见问题 FAQ

### Q: MRP 会帮我写论文吗？

MRP 不会替你写论文。它帮你确保**方法学正确、规范合规、结果可靠**。具体的科学判断——研究问题怎么定、数据怎么解读、临床意义是什么——必须由你来做。MRP 是你的方法学顾问，不是代笔。

### Q: 我只想查个 p 值，一定要走完整 pipeline 吗？

不需要。单点小问题（算一个数、改一句话）直接回答，不走流程。只有研究流程级的任务（选题、设计、分析、写作、投稿、修稿）才进入 MRP 主线。

### Q: 每一步都要我确认吗？

默认不用。轻量确认模式下每个 skill 完成后只给一段摘要就继续，只有研究方案、分析计划、投稿前核验报告这 3 处会等你。想每步都确认就说"逐步确认"；想一口气做完就说"一直做到底"。

### Q: CONSORT 2010 和 2025 有什么区别？为什么必须用 2025？

CONSORT 2025 从 2010 版的 25 项变为 30 项（含子项共 42 行），新增了开放科学、患者与公众参与、危害评估等条目，并修订、合并了部分旧条目。2025 年 4 月 BMJ、JAMA、Lancet、Nature Medicine、PLOS Medicine 同时发布并宣布 2010 版正式被取代。现在投稿用 2010 版清单会被编辑退回。

### Q: 我做基础研究不做临床，MRP 对我有用吗？

有用。`study-design` 的 Type B（基础/实验）路径覆盖细胞/动物/分子实验的设计规范（对照设置、生物学重复 vs 技术重复、盲法、随机化）。内置 Western blot、qPCR、动物实验的设计模板。还有 ARRIVE 2.0 报告规范检查。

### Q: 我的研究跨了多个类型（比如 AI 分析病理切片 + 动物实验验证），怎么办？

`study-design` 是统一路由技能，可在同一研究中叠加多个 Type：涉及 AI 的部分走 Type C（CLAIM 2024 + TRIPOD+AI），涉及动物的部分走 Type B（ARRIVE 2.0）。两个路径可在同一个研究中同时生效，产物仍是同一个 `study-protocol.md`。

### Q: Python 脚本是必须的吗？

不是。脚本是为了提高效率和可复现——Claude 直接 import 就行，不用每次重写代码。即使不装 Python 依赖，MRP 的所有 skill 仍然正常工作，只是 Claude 会自行生成等效代码。

### Q: 没有 PubMed MCP 能用吗？

能。没有 PubMed MCP 时，文献检索和引用核验退化为 DOI / 网络检索的人工核对，Gate 3 会把无法核验的引用标为待确认，而不是直接判定不存在。配置任意一个提供 7 个标准函数的 PubMed MCP server 后就会自动核验。

### Q: 怎么贡献新的 skill？

阅读 `skills/writing-mrp-skills/SKILL.md`，按规范编写 → 测试 → 提交 PR。核心要求：description 以 "Use when" 开头、不总结工作流、必须有 Common Mistakes 表、必须有收敛信号、全文 ≤ 500 行。提交前跑 `python tools/check_consistency.py` 和 `pytest tests/`（见 [CONTRIBUTING.md](../CONTRIBUTING.md)）。

---

## 9. 故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| 输入 `/mrp:research-question` 被当成普通文本 | 插件没装上，或装的是 6.2.x 的旧名 `med-research-powers`（旧版命令前缀是旧插件名，不是 `/mrp:`） | `claude plugin list` 看有没有 `mrp@…`；旧版先 `/plugin uninstall med-research-powers@med-research-powers` 再重装 |
| `/plugin install ./med-research-powers` 报错 | 这不是 Claude Code 支持的语法 | 两步走：先 `/plugin marketplace add ./med-research-powers`，再 `/plugin install mrp@med-research-powers` |
| 装完看不到"引导信息" | hook 的输出进的是 Claude 的上下文，本来就不显示给用户 | 用 `claude plugin list` 验证；新会话直接说一句研究相关的话看是否路由 |
| 脚本 `ModuleNotFoundError` | `sys.path` 里加的是相对路径（如只写 `'scripts'`），而运行目录是你的项目 | 按第 6 节用 `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts` |
| `.docx` 导出报 `No module named docx` | 没装 python-docx | `pip install -r requirements.txt`（包名是 `python-docx`，不是 `docx`） |
| 中文 Windows 下脚本读 YAML 报 `UnicodeDecodeError` | 系统默认编码是 GBK | 升级到 6.3 或更新版本（脚本已统一 `encoding="utf-8"`）；仍有问题请提 issue |
| 提示找不到 `mcp__…__search_articles` | 没有配置 PubMed MCP，或 server 名和文档示例不同 | 在 Claude Code 里配置一个 PubMed MCP server；工具前缀以你会话里的工具列表为准（如 `mcp__PubMed__search_articles`） |
| 新会话没有"从上次继续" | `.mrp-state.json` 不在项目根目录，或从子目录启动 | 在项目根目录启动 Claude Code；确认文件在 `$CLAUDE_PROJECT_DIR` 下 |
| Windows 上 `./install.sh --method 2` 没有软链接 | Git Bash 的 `ln -s` 是复制 | 用方式 1（插件安装） |
| 更新后行为没变 | Claude Code 只在 `version` 变化时拉新版本 | `/plugin update mrp@med-research-powers`，然后重启会话 |

---

## 附录：项目结构

```
med-research-powers/
├── .claude-plugin/                   # plugin.json（name: mrp, v6.4.1）、marketplace.json
├── .github/workflows/ci.yml          # 一致性守卫、pytest、shellcheck、plugin validate、hook 冒烟
├── hooks/session-start.sh            # 启动时读取 .mrp-state.json，报告恢复点
├── commands/ (7)                     # 斜杠命令（薄路由 → skill）
├── skills/ (20)                      # 技能
│   ├── using-med-research-powers/    # 编排器
│   │   └── scripts/ (mrp_state.py)
│   ├── research-question-formulation/
│   ├── literature-synthesis/
│   ├── study-design/                 # 统一 Type A–E 路由
│   │   └── references/
│   │       ├── metrics-and-reporting.yaml      # AI 指标 + 规范映射 (Type C)
│   │       ├── survey-reference.yaml         # 问卷/Delphi 参考表 (Type E)
│   │       └── experiment-templates/ (WB, qPCR, animal)  # Type B
│   ├── research-ethics/
│   ├── journal-selection/
│   ├── data-analysis-planning/
│   │   └── references/ (decision tree, omics)
│   ├── data-collection-tools/
│   │   └── scripts/ (patient_level_split.py, randomization.py)
│   ├── statistical-analysis/
│   │   └── scripts/ (assumption_tests.py, power_analysis.py, data_profile.py, reproduce_check.py)
│   ├── figure-generation/
│   │   └── scripts/ (pub_style.py)
│   ├── manuscript-writing/
│   │   ├── references/journal-templates.yaml   # 240 本期刊模板
│   │   └── scripts/ (get_journal_template.py)
│   ├── manuscript-export/
│   │   └── scripts/ (export_docx.py)
│   ├── reporting-standards/
│   │   └── references/checklists/ (standards-index, consort-2025)
│   ├── peer-review-simulation/
│   ├── pre-submission-verification/
│   ├── submission-preparation/
│   ├── revision-response/
│   ├── pubmed-search/
│   ├── team-collaboration/
│   └── writing-mrp-skills/
├── docs/                             # architecture.md、本手册、images/
├── tools/check_consistency.py        # 仓库一致性守卫
├── tests/                            # 内置脚本的 pytest 测试
├── install.sh                        # 安装脚本（插件 / 软链接）
├── requirements.txt                  # 内置脚本的 Python 依赖
├── CONTRIBUTING.md · SECURITY.md · CHANGELOG.md · LICENSE
└── README.md · README_CN.md
```

---

*Med-Research-Powers 由 BTCH Uro AI Lab 开发维护。*
*灵感来自 [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent。*
