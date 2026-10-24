# Contributing to Med-Research-Powers

感谢你对 MRP 的贡献兴趣！以下是参与方式。（English summary at the end.）

## 如何贡献

### 报告问题

在 GitHub Issues 中报告：
- Claude 跳过了某个应该触发的 skill
- Skill 内容有错误（如报告规范条目不准确）
- 脚本运行出错
- 建议新增的 skill 或改进

安全问题请不要发公开 issue，按 [SECURITY.md](SECURITY.md) 私下报告。

### 贡献新 Skill

1. Fork 仓库
2. 阅读 `skills/writing-mrp-skills/SKILL.md` 了解 skill 编写规范
3. 在 `skills/` 下创建新目录（目录名 = frontmatter 的 `name`）
4. 按规范编写 SKILL.md
5. 测试（至少 1 个真实场景）
6. 提交 PR

PR 说明需包含：
- 这个 skill 解决什么问题
- 没有它时 Claude 的典型错误
- 有了它后的改善

### 贡献期刊模板

如果你发现某个期刊不在 `skills/manuscript-writing/references/journal-templates.yaml` 中：

1. 从期刊官网的 "Instructions for Authors" 提取关键规范
2. 按现有 YAML 格式添加条目（字数限制、摘要格式、参考文献样式、特殊要求）
3. 提交 PR，说明期刊名、IF（注明 JCR 年份）、所属专科

## 提交前必须做的事

```bash
pip install -r requirements.txt pytest
python tools/check_consistency.py   # 版本、计数、路径、链接与锚点、每个 skill 有评测用例、SKILL.md 规范
pytest tests/ -q                     # 内置脚本、hook 和一致性守卫的测试
```

需要 **Python 3.10 或更新版本**（CI 在 3.10 和 3.12 上测试；`requirements.txt` 的 `>=` 是最低版本——注释写明哪些是代码必需的、哪些是测试过的最旧版本，CI 另有一个任务在 Python 3.10 上按这些最低版本原样安装后跑全部测试；新依赖也要写 `>=`）。两个都通过再提 PR。CI 会再跑一遍，另加 `ruff check --select F,E9`、shellcheck、固定版本的 `claude plugin validate --strict` 和 hook 冒烟测试，全部是阻断项。

## 版本号：每个用户可见的改动都要 bump

已安装的用户通过 `/plugin update` 拿更新，而 Claude Code 只在 `version` 字符串变化时才认为有新版本。**不 bump 版本号的推送永远到不了已安装用户。** 所以只要改了 skill、command、hook、脚本或 references 里的任何用户可见内容，就要：

1. 同时改这 9 处版本号（`check_consistency.py` 会验证它们一致）：
   `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`（`metadata.version` 和 `plugins[0].version` 两处）、`README.md`（"Version x.y.z"）、`README_CN.md`（"版本 x.y.z"）、`install.sh`（`MRP_VERSION`）、`hooks/session-start.sh`、`docs/architecture.md`、`docs/USER-MANUAL.md`
2. 在 `CHANGELOG.md` 加一条
3. 打 tag：`claude plugin tag .`（生成 `mrp--vX.Y.Z`）或 `git tag vX.Y.Z`

补丁号：修错别字、修 bug；次版本号：新 skill / 新规范 / 新脚本；主版本号：流水线或产物名变化。

## 新增内容时要同步更新的文件

数量不在守卫里写死：`check_consistency.py` 每次从仓库实时统计 skill、命令、期刊、规范（及其中带逐条清单的条数）、脚本和评测用例，再与 README、README_CN、`docs/`、CONTRIBUTING、SECURITY、hook、两个 manifest 写的数字逐一比对；SKILL.md、命令文件里的期刊/规范总数，以及 `skills/*/references/` 下文件写明的总数（如 standards-index.yaml 开头的 "(N standards)"、期刊库末尾的 "N journals total"）也会核对。范围（"1–2 个期刊"）、候选数（"3 target journals"）不算总数。

| 你新增的是 | 必须同步更新 |
|-----------|-------------|
| **一个 skill** | `skills/<name>/SKILL.md`（frontmatter `name` = 目录名、description 以 "Use when" 开头且 ≤200 字符、≤500 行）；`README.md` 与 `README_CN.md` 的 Skills 表（标题带数量）和仓库结构；`docs/architecture.md` 的 Skills 子图；`skills/using-med-research-powers/SKILL.md` 的路由表；`hooks/session-start.sh` 的路由表（如有）；至少一个评测用例 `evals/route-<name>/`（`prompt.md` + 一个 `min: 1` 的 Skill `tool_used` grader，守卫会查）及 `evals/README.md` 的用例数；所有写着 "N skills / N 个 skill" 的地方；版本号 |
| **一条报告规范** | `skills/reporting-standards/references/checklists/standards-index.yaml`（如有逐条清单，再加 `checklists/<id>.yaml`，并更新该文件开头 "(N of M: …)" 的清单文件列表，守卫会核对）；`README.md` / `README_CN.md` 的 "Reporting Standards" 表；`docs/architecture.md` 的 mindmap；所有写着 "N reporting standards / N 项报告规范" 的地方（含 README 标题 "Reporting Standards (N)" 和指向它的锚点 `#报告规范N`；守卫会逐一报错）；版本号 |
| **一本期刊** | `skills/manuscript-writing/references/journal-templates.yaml`（含 `family:` 字段与 IF/APC 年份）；所有写着 "N journals / N 本期刊" 的地方（含 README 标题和锚点；带 `IF_year`、`guidelines_checked` 的期刊数也会被核对）；版本号 |
| **一个命令** | `commands/<name>.md`（不能与任何 skill 同名；frontmatter 加 `disable-model-invocation: true`）；两份 README 的 Slash Commands 表（标题带数量）；`install.sh` 结尾的命令列表；所有写着 "N commands / N 个命令" 的地方；版本号 |
| **一张方法要点卡** | `skills/data-analysis-planning/references/method-cards/<file>.md`（固定 7 节结构，包名核实 CRAN/PyPI，规则附文献 DOI）+ 同目录 `README.md` 索引 + `data-analysis-planning/SKILL.md` 的卡片清单；版本号 |
| **一个脚本**（只限工具与护栏：易算错的公式、防致命错误的检查、基础设施、只报告的检查工具；**分析代码不做成脚本**） | `skills/<skill>/scripts/<file>.py` + `tests/test_<file>.py`；两份 README 的 "Bundled Python Scripts" 表（守卫会比对表和磁盘）；SKILL.md 里用 `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<file>.py` 调用；`requirements.txt`（如有新依赖，写上代码需要的最低版本 `>=`）；所有写着 "N scripts / N 个脚本" 的地方；版本号 |

## PR Checklist

- [ ] `python tools/check_consistency.py` 通过
- [ ] `pytest tests/ -q` 通过（改了脚本就要有对应测试）
- [ ] 版本号已 bump（9 处一致）且 `CHANGELOG.md` 有条目
- [ ] `README.md` 与 `README_CN.md` 同步修改（标题与表格数量一致）
- [ ] 脚本路径一律 `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<file>.py`，没有 `sys.path.insert(0, 'scripts')`
- [ ] 硬事实有出处（规范条目数、期刊要求、投稿系统），CONSORT 2025 = 30 项（含子项共 42 行）
- [ ] 中文行文用易懂的话，不自造术语；措辞诚实（"Claude is instructed to…" 而不是 "系统强制/拦截"）
- [ ] PR 说明写清：解决什么问题、没有它时的典型错误、有了它后的改善

## SKILL.md 规范速查

```yaml
---
name: kebab-case-name            # 必须等于目录名
description: Use when [条件]. Triggers on "[中文]"、"[英文]".   # ≤200 字符，不总结工作流
---
```

必须包含的部分：
- Overview（一句话）
- When to Use / When NOT to Use
- Workflow
- Output（产物文件名）
- Common Mistakes 表
- Convergence 信号
- 衔接规则（强制/前置/可选），最后一步固定为"更新 .mrp-state.json"

全文 ≤ 500 行；查表、模板、清单放 `references/`，固定代码放 `scripts/`；文中引用的 `references/…`、`scripts/…` 路径必须真实存在（守卫会查）。

## 代码风格

- Python 脚本遵循 PEP 8，`open()` 一律带 `encoding="utf-8"`，通过 `ruff check --select F,E9`；最低支持 Python 3.10
- YAML 用 2 空格缩进
- Markdown 用 ATX 风格标题（`#`）
- Shell 脚本通过 `shellcheck`

## 许可

贡献的内容将以 MIT License 发布。

---

## English summary

- **Before every PR**: `pip install -r requirements.txt pytest && python tools/check_consistency.py && pytest tests/ -q` on **Python 3.10 or later**. CI runs the tests on Python 3.10 and 3.12, once more with the exact minimum versions from `requirements.txt` on 3.10, plus `ruff check --select F,E9`, shellcheck, `claude plugin validate --strict` (pinned Claude Code release) and hook smoke tests — all blocking.
- **Bump the version for every user-visible change** — installed users only receive updates when the `version` string changes. The version is stated in 9 places (`plugin.json`, the two `version` fields of `marketplace.json`, both READMEs, `install.sh`, the hook, `docs/architecture.md`, `docs/USER-MANUAL.md`); the guard verifies they agree. Add a CHANGELOG entry and tag the release.
- **Adding a skill / standard / journal / command / script** means updating the corresponding index or table in both READMEs, `docs/architecture.md`, every place that states the count (the guard counts the repo itself and compares every stated number, including README headings and the anchors that point at them), an eval case under `evals/` for a new skill, and (for scripts) a test under `tests/`. The table above lists every file per kind of change.
- **SKILL.md rules**: frontmatter `name` equals the directory name; `description` starts with "Use when", ≤200 characters, no workflow summary; ≤500 lines; lookup content in `references/`, code in `scripts/`; every referenced relative path must exist; scripts are always called via `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<file>.py`.
- **Wording**: describe the mechanism honestly ("Claude is instructed to…", "mandatory checkpoint"), never "enforced/blocked/locked".
- Security issues: see [SECURITY.md](SECURITY.md) — do not open a public issue.
