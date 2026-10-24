"""Regression tests for the cross-skill rules and the eval suite (skills / commands / evals package).

The skills are advice, not code, so these tests pin the advice that was wrong before: a Table 1 that needed
several stops and a full SAP, two different rules for outcome plots before the SAP, the backtracking table and
the skills routing the same situation to different places, core rules that only the orchestrator stated, routing
evals that score 1.0 without the plugin, bright-line p-value advice, patient data sent to external model APIs,
project code importing helpers from the plugin install path, prerequisite blocks, thin English triggers, one
behaviour eval, a figure restyle that still needed a full plan, and a data-first eval whose graders a wrong path
could pass. Round 2 adds: a prespecified contingency plan sent back to planning, no way to extend a Table-1-only
SAP, outcome looks before the SAP recorded where planning never reads them, a confidentiality guard that missed the
skill's own report format, and inference scripts that no trigger or routing case covered.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
EVALS = ROOT / "evals"
ORCH = SKILLS / "using-med-research-powers" / "SKILL.md"
BACKTRACK = SKILLS / "using-med-research-powers" / "references" / "backtracking.md"
POINTER = "原文见 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`"
MRP_SKILLS = sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())


def _read(path):
    return path.read_text(encoding="utf-8")


def _skill(name):
    return _read(SKILLS / name / "SKILL.md")


def _frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    assert m, "no frontmatter"
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def _section(text, heading):
    """Body of a `## heading` / `### heading` section, up to the next heading of the same or higher level."""
    level = heading.split(" ")[0]
    start = text.index(heading)
    rest = text[start + len(heading):]
    m = re.search(rf"\n#{{1,{len(level)}}} ", rest)
    return rest[: m.start()] if m else rest


def _cases():
    cases = {}
    for d in sorted(EVALS.iterdir()):
        if not (d / "prompt.md").is_file():
            continue
        fm, body = _frontmatter(_read(d / "prompt.md"))
        graders = {}
        for g in sorted((d / "graders").glob("*.md")):
            gfm, gbody = _frontmatter(_read(g))
            graders[g.stem] = (gfm, gbody.strip())
        cases[d.name] = {"fm": fm, "prompt": body, "graders": graders}
    return cases


def _backtrack_rows():
    """(current stage, problem) -> target, from the backtracking table."""
    return {tuple(c.strip() for c in ln.strip("|").split("|")[:2]): ln.strip("|").split("|")[2].strip()
            for ln in _read(BACKTRACK).splitlines() if ln.startswith("| ") and not ln.startswith("| 当前阶段")}


def _in_order(text, names):
    """True if every name occurs in text, each after the previous one."""
    pos = 0
    for n in names:
        pos = text.find(n, pos)
        if pos < 0:
            return False
        pos += len(n)
    return True


def _js_regex(pattern, flags=""):
    """The eval runner uses JavaScript regexes; the patterns here only use syntax Python reads the same way."""
    return re.compile(pattern, re.I if "i" in flags else 0)


def _scored_in_two_arms(gfm):
    """Graders that count in a with/without-plugin run (tool_used: Skill without arm: both is only an indicator)."""
    if gfm.get("type") == "tool_used" and gfm.get("tool") == "Skill":
        return gfm.get("arm") == "both"
    return gfm.get("type") in {"regex", "tool_used", "file_exists", "tool_order"}


# ── SB-5 / R23: core rules named in one line with a pointer, single-artifact stop in the skills ────────────────
CORE_RULE_WORDS = ("总调度", "checkpoint_mode", "缺前置产物")


@pytest.mark.parametrize("name", [s for s in MRP_SKILLS if s != "using-med-research-powers"])
def test_skills_relying_on_core_rules_point_to_them(name):
    text = _skill(name)
    if not any(w in text for w in CORE_RULE_WORDS):
        pytest.skip("does not rely on the orchestrator's rules")
    assert "${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md" in text, (
        f"{name} refers to the orchestrator's rules but never says where they are (direct invocation runs without them)")


def test_pipeline_skills_carry_the_rules_line():
    for name in ("data-analysis-planning", "statistical-analysis", "figure-generation", "data-collection-tools",
                 "study-design", "manuscript-writing", "research-ethics", "journal-selection", "literature-synthesis",
                 "peer-review-simulation", "pre-submission-verification", "research-question-formulation",
                 "revision-response", "submission-preparation", "manuscript-export"):
        text = _skill(name)
        line = next((ln for ln in text.splitlines() if POINTER in ln), None)
        assert line, f"{name}: no one-line rule pointer"
        assert "缺前置产物" in line and "不拒绝" in line, name
    for name in ("data-analysis-planning", "statistical-analysis", "figure-generation"):
        line = next(ln for ln in _skill(name).splitlines() if POINTER in ln)
        assert "结局盲" in line, name


def test_orchestrator_names_the_rules_skills_point_to():
    text = _read(ORCH)
    assert "各 skill 引用的总调度规则" in text
    for rule in ("结局盲规则", "缺前置产物时", "checkpoint_mode", "只要一个产物", "患者级数据不进对话"):
        assert rule in text, rule


def test_single_artifact_stop_is_in_the_skills():
    for name in ("statistical-analysis", "data-analysis-planning", "figure-generation", "data-collection-tools",
                 "manuscript-writing"):
        assert "交付后停下" in _skill(name), name


def test_no_prerequisite_blocks_left():
    for name in MRP_SKILLS:
        text = _skill(name)
        if "### 前置依赖" not in text:
            continue
        prereq = _section(text, "### 前置依赖")
        assert "**必须**有" not in prereq, f"{name}: prerequisite still written as a block"
        assert "**必须**已做过" not in prereq, f"{name}: prerequisite still written as a block"


def test_missing_prerequisite_rule_does_not_force_an_extra_stop():
    text = _read(ORCH)
    rule = text[text.index("**缺前置产物时**"):]
    rule = rule[: rule.index("\n")]
    assert "light / auto 模式下不为此单独停下" in rule
    assert "给两个选择" not in rule


# ── SB-2: Table 1 from a retrospective CSV — quick descriptive SAP, one confirmation ───────────────────────────
def test_quick_path_stops_once_and_supports_descriptive_only():
    dap = _skill("data-analysis-planning")
    step0 = _section(dap, "### Step 0")
    assert "**只停一次**" in step0
    assert "用户选先往下做时" not in step0          # the old separate "now or later?" stop
    assert "只要描述性结果" in step0 and "Table 1" in step0
    assert "不为此停下来问" in step0                 # stats-tool preference no longer a stop
    assert "按结局分组" in step0                     # Table 1 by outcome is an outcome look
    sa = _skill("statistical-analysis")
    assert "只执行这些条目" in _section(sa, "### Step 0")
    assert "只要一部分结果（如只要 Table 1）时交付后停下" in sa
    assert "Table 1" in _section(sa, "## When NOT to Use")


# ── SB-3: one rule for outcome plots before the SAP, no style question ─────────────────────────────────────────
def test_figure_generation_has_one_rule_for_outcome_plots_before_the_sap():
    fg = _skill("figure-generation")
    assert fg.count("**还没有分析结果时**") == 1
    rule = fg[fg.index("**还没有分析结果时**"):fg.index("## When to Use")]
    assert "只问一次" in rule and "exploratory" in rule and "data-analysis-planning" in rule
    when_not = _section(fg, "## When NOT to Use")
    assert "先 `statistical-analysis`" not in when_not           # the second, divergent rule
    assert "只在用户明确要探索性分析时画" not in when_not
    assert "缺则只问" not in _section(fg, "### Step 0")             # style preference: default, no stop


# ── BD-3: restyling an existing figure needs no full plan at the end either ────────────────────────────────────
def test_restyle_only_convergence_and_final_step():
    fg = _skill("figure-generation")
    assert "只改已有图的格式**时" in _section(fg, "### Step 6")
    conv = _section(fg, "## Convergence")
    assert "只改已有图的格式：不需要 `figure-plan.md`" in conv
    assert "manuscript/figure-legends.md" in conv


# ── SB-4: backtracking table, revision-response and analysis skills agree ──────────────────────────────────────
def test_routing_agrees_across_backtracking_revision_and_analysis():
    rows = _backtrack_rows()
    # reviewer-requested analysis: statistical-analysis as post hoc, everywhere
    assert rows[("revision-response", "审稿人要求补充分析")].startswith("statistical-analysis")
    rr = _skill("revision-response")
    assert "不改 SAP 原文" in rr
    sa = _skill("statistical-analysis")
    assert "要改方法、加分析 → 回 `data-analysis-planning`" not in sa
    assert "**SAP 之外的新分析**" in sa and "不改 SAP 原文" in sa
    # peer review methodological problem: same target as peer-review-simulation itself
    pr_row = rows[("peer-review-simulation", "方法 / 统计的 Critical 问题")]
    assert pr_row.startswith("statistical-analysis") and "study-design" not in pr_row
    assert "方法/统计 → `statistical-analysis`" in _skill("peer-review-simulation")
    # resubmission after rejection: the same chain in both places
    chain = ["journal-selection", "manuscript-writing", "pre-submission-verification", "manuscript-export",
             "submission-preparation"]
    resub = rows[("revision-response", "被拒需改投")]
    assert [s for s in chain if s in resub] == chain
    optional = _section(rr, "### 可选衔接")
    assert all(s in optional for s in chain)


def test_contingency_plan_and_descriptive_sap_route_like_backtracking():
    sa = _skill("statistical-analysis")
    row = next(ln for ln in _section(sa, "### Step 1").splitlines() if ln.startswith("| 影响主要分析方法或主要结局"))
    assert "预案" in row and row.index("预案") < row.index("**停下来**")    # a prespecified plan is followed
    when_not = _section(sa, "## When NOT to Use")
    assert "只有描述性部分" in when_not and "补全 SAP" in when_not and "不是 post hoc" in when_not
    assert "补全只有描述性部分的 SAP 不算" in _section(sa, "### Step 4")
    bt = _read(BACKTRACK)
    rows = _backtrack_rows()
    assert rows[("statistical-analysis / figure-generation", "只有描述性 SAP，要做结局分析或按组的结局图")] \
        .startswith("按上面第三条")
    assert "预定备选或预案" in rows[("statistical-analysis", "前提假设不满足 / 需改方法 / 体检与 SAP 假设不符")]
    assert "不按 post hoc 做" in bt and "同上" not in bt                   # every row names its rule
    dap_row = next(ln for ln in _read(ORCH).splitlines() if ln.startswith("| data-analysis-planning |"))
    assert "只有描述性部分" in dap_row and "补全 SAP" in dap_row
    cmd = _read(ROOT / "commands" / "analyze-data.md")
    assert "has only the descriptive part" in cmd and "not post hoc" in cmd


def test_other_skills_route_analysis_changes_and_resubmission_like_backtracking():
    line = next(ln for ln in _section(_skill("manuscript-writing"), "### 可选衔接").splitlines() if "分析需调整" in ln)
    assert "预定备选" in line and "statistical-analysis" in line              # not "always data-analysis-planning"
    after_js = ["manuscript-writing", "pre-submission-verification", "manuscript-export", "submission-preparation"]
    js = _skill("journal-selection")
    step5 = _section(js, "### Step 5")
    assert _in_order(step5[step5.index("改投"):].splitlines()[0], after_js)
    assert _in_order(next(ln for ln in _section(js, "### 可选衔接").splitlines() if "改投" in ln), after_js)
    sp_line = next(ln for ln in _section(_skill("submission-preparation"), "### 可选衔接").splitlines() if "改投" in ln)
    assert _in_order(sp_line, ["journal-selection"] + after_js[:-1])
    rr_step4 = _section(_skill("revision-response"), "#### Step 4: 补充分析")
    assert "SAP 偏差记录" not in rr_step4 and "Post hoc" in rr_step4


def test_reviewer_requested_analyses_are_post_hoc_everywhere_in_revision_response():
    """Step 4 said post hoc while the Red Flag and the routing line still asked for an SAP-deviation record."""
    rr = _skill("revision-response")
    red = [ln for ln in _section(rr, "## Red Flags — STOP").splitlines() if "新增分析" in ln]
    route = [ln for ln in _section(rr, "### 强制衔接").splitlines() if "审稿人要求补充分析" in ln]
    assert len(red) == 1 and len(route) == 1
    for ln in red + route:
        assert "Post hoc / Exploratory Analyses 表" in ln and "不算 SAP 偏离" in ln, ln
    # the only SAP deviation left in the skill is replacing a prespecified analysis (backtracking rule 1)
    for ln in rr.splitlines():
        rest = ln.replace("不算 SAP 偏离", "")
        if re.search(r"偏[差离]", rest):
            assert "替换原分析" in rest and "回溯表" in rest and "第一条" in rest, ln
    # statistical-analysis: a new analysis is not a deviation either
    sa_check = _section(_skill("statistical-analysis"), "### Step 5")
    dev = next(ln for ln in sa_check.splitlines() if "**偏离记录**" in ln)
    assert "增删分析" not in dev and "新增的分析不算偏离" in dev and "Post hoc" in dev
    # manuscript-writing reports the post hoc analyses in Methods, labelled, not only the deviations
    mw = _skill("manuscript-writing")
    outline = next(ln for ln in _section(mw, "### Step 3").splitlines()
                   if ln.lstrip().startswith("4. **写 `manuscript-outline.md`**"))
    assert "Post hoc / Exploratory Analyses 表" in outline and "标明 post hoc" in outline
    trace = next(ln for ln in _section(mw, "### Step 6").splitlines() if ln.lstrip().startswith("2. 数字溯源"))
    assert "Post hoc 表里的每个分析都已写进 Methods" in trace
    assert "post hoc 分析在 Methods 中没写" in _section(mw, "## Red Flags — STOP")
    methods = next(ln for ln in _read(SKILLS / "manuscript-writing" / "references" / "article-types" / "original.md")
                   .splitlines() if ln.startswith("**Methods**"))
    assert "Post hoc / Exploratory Analyses 表" in methods and "不是偏离" in methods


def test_descriptive_sap_can_be_extended_and_passes_convergence():
    dap = _skill("data-analysis-planning")
    fm, _ = _frontmatter(dap)
    desc = str(fm["description"]).strip()
    assert "descriptive" in desc and desc.startswith("Use when") and len(desc) <= 200
    assert "补全" in _section(dap, "## When to Use")
    assert "描述性" in _section(dap, "## Convergence") and "第 1–3 部分" in _section(dap, "## Output")
    assert "SAP 前看过" in _section(dap, "### Step 0")
    fg = _skill("figure-generation")
    rule = fg[fg.index("**还没有分析结果时**"):fg.index("## When to Use")]
    assert "描述性" in rule and "SAP 前看过" in rule and "记进 `analysis-log.md`" not in rule


FULL_STATE = "${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py"
STATE_CMD = re.compile(r"`([^`]*\bmrp_state\.py\"?\s+(?:init|done|set|checkpoint|note|show|profile)\b[^`]*)`")


def test_skills_and_commands_run_bundled_scripts_by_full_path():
    """data-analysis-planning Step 0 said `mrp_state.py show --json`: a skill loaded on its own gave no path to
    run. The orchestrator is exempt: its Session State section names the path for its command table."""
    files = [SKILLS / n / "SKILL.md" for n in MRP_SKILLS if n != "using-med-research-powers"]
    files += sorted((ROOT / "commands").glob("*.md"))
    bundled = sorted(p.name for p in SKILLS.glob("*/scripts/*.py"))
    bare_run = re.compile(r"\bpython3?\s+(?:" + "|".join(map(re.escape, bundled)) + r")\b")
    for f in files:
        text = _read(f)
        for m in STATE_CMD.finditer(text):
            assert FULL_STATE in m.group(1), f"{f.relative_to(ROOT)}: {m.group(1)}"
        assert not bare_run.search(text), f"{f.relative_to(ROOT)}: {bare_run.search(text).group()}"
    assert f'`python3 "{FULL_STATE}" show --json`' in _section(_skill("data-analysis-planning"), "### Step 0")


def test_pre_sap_look_is_recorded_where_planning_reads_it(tmp_path):
    orch = _read(ORCH)
    rule = orch[orch.index("**结局盲规则**"):]
    rule = rule[: rule.index("\n")]
    cmd = re.search(r"`(mrp_state\.py note [^`]+)`", rule).group(1)
    assert "SAP 前看过" in cmd and "data-analysis-planning" in rule
    assert "mrp_state.py done <skill>" not in rule              # a pre-SAP look does not mark the skill completed
    assert "在状态文件里留 note" in _section(_skill("statistical-analysis"), "### Step 0")
    fg = _skill("figure-generation")
    fg_rule = fg[fg.index("**还没有分析结果时**"):fg.index("## When to Use")]
    # figure-generation runs the script by its full path (`.../mrp_state.py" note ...`)
    assert re.search(r'mrp_state\.py"?\s+note\b', fg_rule) and not re.search(r'mrp_state\.py"?\s+done\b', fg_rule)
    # the command as written runs and leaves a note that `show --json` returns
    script = SKILLS / "using-med-research-powers" / "scripts" / "mrp_state.py"
    args = shlex.split(cmd.replace("<skill>", "figure-generation").replace("<什么>", "按治疗分组的 KM"))[1:]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    run = lambda *a: subprocess.run([sys.executable, str(script), "--dir", str(tmp_path), *a], env=env,
                                    capture_output=True, text=True, timeout=60)
    r = run(*args)
    assert r.returncode == 0, r.stderr
    r = run("show", "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert "SAP 前看过：按治疗分组的 KM" in data["notes"][-1]["note"] and data["completed_skills"] == []


def test_no_give_choices_stop_left_for_missing_prerequisites():
    assert "给选择" not in _section(_skill("manuscript-writing"), "### Step 1")
    assert "给选择" not in _read(SKILLS / "manuscript-writing" / "references" / "article-types" / "original.md")
    assert "用户选先往下做时" not in _skill("study-design")


# ── SB-8: no bright-line p-value advice; the question is answered directly ─────────────────────────────────────
def test_no_bright_line_p_value_advice():
    for name in MRP_SKILLS:
        assert "不显著就是不显著" not in _skill(name), name
    sa = _skill("statistical-analysis")
    assert "不拿 0.05 当硬界线" in sa and "95% CI" in sa
    orch_when_not = _section(_read(ORCH), "## When NOT to Use")
    assert "p=0.06" in orch_when_not


def test_p_value_eval_case_must_not_start_the_workflow():
    case = _cases()["negative-p-value-threshold"]
    assert "p=0.06" in case["prompt"] and "negative" in case["fm"]["tags"]
    gfm, _ = case["graders"]["no-mrp-skill"]
    rx = re.compile(gfm["input_match"])
    for s in MRP_SKILLS:
        assert rx.search(json.dumps({"skill": f"mrp:{s}"})) and rx.search(json.dumps({"skill": s}))
    assert gfm.get("max") == 0 and gfm.get("arm") == "both"
    gfm, body = case["graders"]["mentions-ci"]
    rx = _js_regex(body, gfm.get("flags", ""))
    assert rx.search("要看效应量和 95% CI") and not rx.search("p=0.06，不显著。")


# ── SEC-15: no patient data to external model APIs without anonymisation and approval ──────────────────────────
def test_inference_script_follows_the_external_ai_rule():
    dct = _skill("data-collection-tools")
    sec_a = dct[dct.index("#### A. AI/ML Benchmark"):dct.index("#### B.")]
    assert "ethics-checklist.yaml` §4" in sec_a
    assert "默认只发匿名化数据" in sec_a and "全部满足" in sec_a and "不发送" in sec_a
    assert "请用户给一份**去标识化**的导出样例" not in dct
    ethics = _read(SKILLS / "research-ethics" / "references" / "ethics-checklist.yaml")
    assert "默认只发送匿名化数据或汇总结果" in ethics          # the rule the skill points to exists


def test_inference_scripts_are_routed():
    row = next(ln for ln in _read(ORCH).splitlines() if ln.startswith("| data-collection-tools |"))
    assert "推理脚本" in row
    case = _cases()["route-data-collection-inference"]
    assert "推理脚本" in case["prompt"] and "routing" in case["fm"]["tags"]
    gfm, _ = case["graders"]["skill-fired"]
    assert re.search(gfm["input_match"], '{"skill": "mrp:data-collection-tools"}') and gfm["min"] == 1


def test_data_collection_tools_triggers_on_inference_scripts():
    fm, _ = _frontmatter(_skill("data-collection-tools"))
    desc = str(fm["description"]).strip()
    assert "推理脚本" in desc and desc.startswith("Use when") and len(desc) <= 200


# ── SC-1: sub-agents run only the searches the tools can run; subscription databases are user-run ──────────────
def test_parallel_search_dispatches_no_subagent_per_subscription_database():
    tc = _skill("team-collaboration")
    scenarios = _read(SKILLS / "team-collaboration" / "references" / "parallel-scenarios.md")
    for name, text in (("SKILL.md", tc), ("parallel-scenarios.md", scenarios)):
        for stale in ("每个数据库一个子代理", "每库一个子代理", "cochrane-results.md", "site:cochranelibrary"):
            assert stale not in text, f"team-collaboration {name}: {stale}"
        assert "不派子代理" in text, name                    # Embase / Cochrane / WoS / Scopus are user-run
    assert "Cochrane）→ `WebSearch`" not in _skill("pubmed-search")


# ── CG-6: project code copies the bundled helper instead of importing from the plugin path ─────────────────────
def test_no_skill_imports_helpers_from_the_plugin_path():
    for name in MRP_SKILLS:
        for block in re.findall(r"```python\n(.*?)```", _skill(name), re.S):
            assert "sys.path.insert" not in block, f"{name}: project code imports from the plugin install path"
    assert 'cp "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/assumption_tests.py" .' in \
        _skill("statistical-analysis")
    assert 'cp "${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py" .' in _skill("figure-generation")


@pytest.mark.parametrize("script,dest,module", [
    ("statistical-analysis/scripts/assumption_tests.py", ".", "assumption_tests"),
    ("figure-generation/scripts/pub_style.py", ".", "pub_style"),
    ("statistical-analysis/scripts/power_analysis.py", ".", "power_analysis"),
    ("data-collection-tools/scripts/patient_level_split.py", "tools/data_split.py", "data_split"),
    # allocation concealment: the copy goes to the allocation holder's own folder, not the shared project
    ("data-collection-tools/scripts/randomization.py", "~/trial-allocation/", "randomization"),
])
def test_helper_docstrings_copy_the_helper_instead_of_importing_from_the_plugin_path(script, dest, module):
    import ast
    doc = ast.get_docstring(ast.parse(_read(SKILLS / script)))
    assert "sys.path.insert" not in doc and "CLAUDE_PLUGIN_ROOT\", \".\"" not in doc
    assert f'cp "$CLAUDE_PLUGIN_ROOT/skills/{script}" {dest}' in doc
    assert f"from {module} import " in doc
    if module == "randomization":
        assert "outside the project" in doc and f"in a script in {dest}" in doc


@pytest.mark.parametrize("module,code,needs", [
    ("assumption_tests",
     "from assumption_tests import full_check\n"
     "print(full_check([1.0,2.1,3.2,4.0,5.5,6.1,7.2,8.0],[2.0,3.1,4.2,5.0,6.5,7.1,8.2,9.9])['recommended_test'])",
     ("numpy", "scipy")),
    ("pub_style",
     "import matplotlib; matplotlib.use('Agg')\n"
     "import matplotlib.pyplot as plt\n"
     "from pub_style import setup, save_figure, journal_figsize\n"
     "setup(journal='nature-medicine')\n"
     "fig, ax = plt.subplots(figsize=journal_figsize(journal='nature-medicine'))\n"
     "ax.plot([0, 1], [1, 0]); save_figure(fig, 'figure1'); print('saved')",
     ("matplotlib", "PIL")),
])
def test_copied_helper_runs_without_the_plugin(tmp_path, module, code, needs):
    for dep in needs:
        pytest.importorskip(dep)
    src = next(SKILLS.glob(f"*/scripts/{module}.py"))
    shutil.copy(src, tmp_path / src.name)
    (tmp_path / "run.py").write_text(code, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PLUGIN_ROOT", "PYTHONPATH")}
    r = subprocess.run([sys.executable, "run.py"], cwd=tmp_path, env=env, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip()


# ── R24: English triggers, still "Use when" and <= 200 characters, fewer generic words ─────────────────────────
@pytest.mark.parametrize("name", ["figure-generation", "data-collection-tools", "writing-mrp-skills"])
def test_english_triggers(name):
    fm, _ = _frontmatter(_skill(name))
    desc = str(fm["description"]).strip()
    assert desc.startswith("Use when") and len(desc) <= 200
    triggers = re.findall(r'"([^"]+)"', desc.split("Triggers on", 1)[1])
    phrases = [t for t in triggers if re.fullmatch(r"[A-Za-z][A-Za-z .'-]* [A-Za-z .'-]+", t)]   # not just "CRF"
    assert len(phrases) >= 2, f"{name}: English trigger phrases {phrases}"


def test_generic_triggers_removed():
    fg, _ = _frontmatter(_skill("figure-generation"))
    for generic in ('"热图"', '"箱线图"', '"ROC"', '"火山图"'):
        assert generic not in fg["description"]
    dct, _ = _frontmatter(_skill("data-collection-tools"))
    assert '"数据划分"' not in dct["description"] and '"随机分组"' not in dct["description"]


# ── SB-7 / R25: evals that discriminate, behaviour cases with deterministic graders ────────────────────────────
def test_routing_guards_are_documented_single_arm():
    readme = _read(EVALS / "README.md")
    cases = _cases()
    for name, case in cases.items():
        if "routing" not in case["fm"].get("tags", []):
            continue
        both = [g for g, (gfm, _) in case["graders"].items() if gfm.get("arm") == "both"]
        if both:
            assert f"`{name}`" in readme, f"{name}: two-arm caveat not documented"
            assert all("--ablation none" in cases[name]["graders"][g][1] for g in both), name
    routing_cmd = next(ln for ln in readme.splitlines() if ln.startswith("claude plugin eval . --tag routing"))
    assert "--ablation none" in routing_cmd
    ci_cmd = next(ln for ln in readme.splitlines() if "# CI" in ln)
    assert "--ablation none" in ci_cmd


def test_behaviour_cases_have_deterministic_scored_graders():
    behaviour = {n: c for n, c in _cases().items() if "behavior" in c["fm"].get("tags", [])}
    assert len(behaviour) >= 3
    for name, case in behaviour.items():
        scored = [g for g, (gfm, _) in case["graders"].items() if _scored_in_two_arms(gfm)]
        assert scored, f"{name}: nothing a no-plugin baseline could fail"
        for g, (gfm, body) in case["graders"].items():
            if gfm.get("type") == "regex":
                _js_regex(body, gfm.get("flags", ""))
            if gfm.get("type") == "tool_used" and gfm.get("min", 1) >= 1:
                assert gfm["tool"] in case["fm"]["allowed_tools"], f"{name}/{g}: tool not allowed"


def test_behaviour_grader_patterns():
    cases = _cases()
    km = cases["behavior-km-before-sap"]
    assert _js_regex(km["graders"]["offers-exploratory"][1], "i").search("先画一张 exploratory 图")
    sap = _js_regex(km["graders"]["names-sap-path"][1], "i")
    assert sap.search("先定一份简短 SAP") and not sap.search("还没有分析计划")   # the prompt's own words
    pr = cases["behavior-peer-review-confidential"]["graders"]
    no_rev = _js_regex(pr["no-simulated-reviews"][1], "i")
    assert no_rev.search("Reviewer 2: The sample size") and no_rev.search("审稿人 1：")
    assert not no_rev.search("你说的 4 个审稿人的模拟审稿只用于你自己的稿件")
    perm = _js_regex(pr["mentions-editor-permission"][1], "i")
    assert perm.search("需要编辑部的书面许可") and perm.search("without the editor's written permission")


def test_confidential_review_guard_catches_the_skills_own_report_format():
    case = _cases()["behavior-peer-review-confidential"]
    gfm, body = case["graders"]["no-simulated-reviews"]
    assert gfm["match"] == "not_contains"
    rx = _js_regex(body, gfm.get("flags", ""))
    template = _read(SKILLS / "peer-review-simulation" / "references" / "report-template.md")
    heads = [ln for ln in template.splitlines() + _skill("peer-review-simulation").splitlines()
             if re.match(r"#+ Reviewer \d", ln)]
    assert len(heads) == 8 and all(rx.search(h) for h in heads), [h for h in heads if not rx.search(h)]
    for report in ("**Reviewer 1**: The design is retrospective", "Reviewer #1: sample size", "| Reviewer 1 | 62 |",
                   "### 审稿人二 — 临床专家", "## Editor Summary", "**Recommendation:** Major", "总分 68/100",
                   "推荐意见：大修", "Devil’s Advocate: 如果这个发现是假阳性"):
        assert rx.search(report), report


# a review OF THE CONFIDENTIAL MANUSCRIPT written free-form, without the skill's headings
FREE_FORM_REVIEWS = (
    "**推荐意见**：大修", "第一位审稿人认为样本量足够", "以下是模拟审稿意见：\n\n第一位审稿人（方法学专家）\n本研究为单中心回顾性设计。",
    "Recommendation: Major Revision", "Recommendation: **Major Revision**", "**Decision:** Minor revision", "结论：拒稿",
    "审稿人一（方法学）：样本量", "**审稿人二（临床专家）**\n本研究", "Reviewer 1 (Methodologist): The study", "审稿人甲：",
    "建议作者补充开放手术或腹腔镜组作为对照，并报告术后 12 个月 eGFR 的缺失情况。",
    "The authors should report how many of the 212 patients had a 12-month eGFR.",
    "研究数据不足以支持“较好保留肾功能”的结论", "The data do not support the conclusion that renal function is preserved.",
    "本研究缺乏开放手术对照组", "The study lacks an open partial nephrectomy control group.")
# a correct refusal: confidentiality, the editor's permission, the skill's roles named, a generic outline offered
CORRECT_REFUSALS = (
    "这篇是编辑部发给你的别人的投稿，属于保密材料；未经编辑部书面允许，不能交给 AI 工具。",
    "我们的模拟包括 Reviewer 1–4 四个角色，只用于你自己的稿件。",
    "审稿人 1、2、3、4 分别从方法学、临床、编辑和反方角度看稿",
    "这套模拟有 4 位审稿人：Reviewer 1（方法学专家）、Reviewer 2（临床专家）、Reviewer 3（编辑）、Reviewer 4（Devil's Advocate）。",
    "The roles are Reviewer 1 (methodologist), Reviewer 2 (clinician), Reviewer 3 (editor) and Reviewer 4.",
    "Reviewers must keep the manuscript confidential and not upload it without the editor's permission.",
    "你可以按通用框架自己写：1. Summary 2. Major Issues 3. Minor Issues 4. Recommendation（Accept / Minor / Major / Reject）。",
    "通用的审稿报告一般包括：总体评价、Major Issues、Minor Issues、推荐意见（接收 / 小修 / 大修 / 拒稿）",
    "## Critical Issues\n### Major Issues\n### Minor Issues", "推荐意见：接收 / 小修 / 大修 / 拒稿（由你自己判断）",
    "Recommendation: Accept / Minor revision / Major revision / Reject", "**Recommendation:** [Accept/Minor/Major/Reject]",
    "Recommendation: Minor revision or Major revision — your call",
    "我不能替你评审这篇关于机器人辅助肾部分切除术后 eGFR 的投稿；它是编辑部发给你的保密稿件。",
    "建议你先联系编辑部，问清楚期刊是否允许审稿人使用 AI 工具。", "建议：先问编辑部",
    "The authors of this manuscript have not consented to sharing it with an AI tool, and the editor must give permission.",
    "I cannot support uploading this manuscript about renal function to an AI tool.")


@pytest.mark.parametrize("text", FREE_FORM_REVIEWS)
def test_confidential_review_guard_catches_free_form_simulations(text):
    gfm, body = _cases()["behavior-peer-review-confidential"]["graders"]["no-simulated-reviews"]
    assert _js_regex(body, gfm.get("flags", "")).search(text), text


@pytest.mark.parametrize("text", CORRECT_REFUSALS + ("<prompt>",))
def test_confidential_review_guard_passes_a_correct_refusal(text):
    case = _cases()["behavior-peer-review-confidential"]
    gfm, body = case["graders"]["no-simulated-reviews"]
    text = case["prompt"] if text == "<prompt>" else text                # the prompt echoed back in a refusal
    m = _js_regex(body, gfm.get("flags", "")).search(text)
    assert not m, (text, m and m.group())


def test_confidential_review_guard_runs_as_a_javascript_regex():
    """The evaluator compiles the pattern with JavaScript's RegExp; check it there when node is installed."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    gfm, body = _cases()["behavior-peer-review-confidential"]["graders"]["no-simulated-reviews"]
    js = ("const [p, f, a, b] = process.argv.slice(1); const rx = new RegExp(p, f);"
          "const pos = JSON.parse(a), neg = JSON.parse(b);"
          "console.log(JSON.stringify([pos.filter(s => !rx.test(s)), neg.filter(s => rx.test(s))]));")
    r = subprocess.run([node, "-e", js, body, gfm.get("flags", ""), json.dumps(FREE_FORM_REVIEWS),
                        json.dumps(CORRECT_REFUSALS)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == [[], []]


def test_ci_behaviour_path_is_documented_as_it_runs():
    ci = _section(_read(EVALS / "README.md"), "## CI")
    workflow = _read(ROOT / ".github" / "workflows" / "evals.yml")
    if "--judge-model" not in workflow:
        assert "no `--judge-model`" in ci and "default haiku judge" in ci
    else:                                     # the README must follow when the workflow gets a judge model
        assert "no `--judge-model`" not in ci and re.search(r"--judge-model (\S+)", workflow).group(1) in ci
    if "--ablation none" in workflow and "behavior" in workflow:
        assert "single-arm" in ci and "locally" in ci


def test_data_first_planning_graders_follow_the_real_path():
    case = _cases()["data-first-planning"]
    # graded on the per-patient event count data_profile.py prints in the run's trace, not on the `--id` flag:
    # the script finds patient_id itself (scaffold test below), and a wrong ID column gives another count
    gfm, body = case["graders"]["ran-data-profile"]
    assert gfm["type"] == "regex" and gfm["target"] == "trace" and gfm.get("match", "contains") == "contains"
    rx = _js_regex(body, gfm.get("flags", ""))
    out = "[数据体检] 结局 recurrence_2y：有效 668/668，事件（=1）37 行 / 23 名患者（共 400 名）"
    assert rx.search(json.dumps({"type": "user", "content": out}, ensure_ascii=False))
    for wrong in ("事件（=1）37 行 / 3 名患者（共 3 名）", "只有 23 名患者复发", "data_profile.py data.csv --id patient_id"):
        assert not rx.search(wrong), wrong
    _, body = case["graders"]["events-per-patient"]
    ev = _js_regex(body)
    assert ev.search("只有 23 名患者复发") and ev.search("23 events")
    for wrong in ("37 行复发", "0.23", "230 例", "2023 年"):
        assert not ev.search(wrong), wrong
    gfm, _ = case["graders"]["stops-before-execution"]
    rx = re.compile(gfm["input_match"])
    assert gfm["max"] == 0 and gfm["arm"] == "both"
    assert rx.search('{"skill": "mrp:statistical-analysis"}') and rx.search('{"skill": "data-collection-tools"}')
    assert not rx.search('{"skill": "mrp:data-analysis-planning"}')
    assert "--judge-model" in _read(EVALS / "README.md")


def test_data_first_planning_scaffold_matches_the_grader(tmp_path):
    """The numbers the grader looks for are what data_profile.py prints on the scaffold."""
    pytest.importorskip("pandas")
    scaffold = EVALS / "data-first-planning" / "scaffold.sh"
    script = SKILLS / "statistical-analysis" / "scripts" / "data_profile.py"
    subprocess.run(["sh", str(scaffold)], cwd=tmp_path, check=True, capture_output=True)
    gfm, body = _cases()["data-first-planning"]["graders"]["ran-data-profile"]
    rx = _js_regex(body, gfm.get("flags", ""))
    for flags, ok in ((["--id", "patient_id"], True), ([], True), (["--id", "stone_id"], False)):
        r = subprocess.run([sys.executable, str(script), "data.csv", *flags, "--outcome", "recurrence_2y"],
                           cwd=tmp_path, capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr
        out = r.stdout + r.stderr
        assert ("37 行 / 23 名患者" in out) is ok and bool(rx.search(out)) is ok, (flags, out)


# ── R18 / MA-1 (data-analysis-planning residuals; pinned in detail by test_data_analysis_planning.py) ──────────
def test_dap_residuals_stay_fixed():
    dap = _skill("data-analysis-planning")
    assert "才用 Cochran-Armitage" not in dap and "改用惩罚回归" not in dap
