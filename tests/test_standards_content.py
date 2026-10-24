"""Regression tests for the reporting-standards index, literature-synthesis and submission-preparation content.

These files are advice, not code, so the checks pin what was wrong before: index entries without a local
checklist and without any reference, surgical innovation routed to a non-reporting framework, STARD-AI /
TARGET / CHART missing, `use_with` pointing at a bias tool, systematic-review searches that no tool can run
presented as database searches, single-reviewer AI screening, no GRADE step, PROSPERO for scoping reviews,
and cover letters with no AI-use / preprint declaration or with an invented headline number. References
are pinned by DOI (each DOI was resolved in PubMed when it was added).
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
RS = ROOT / "skills" / "reporting-standards"
CHECKLISTS = RS / "references" / "checklists"
LS = ROOT / "skills" / "literature-synthesis"
SP = ROOT / "skills" / "submission-preparation"
METRICS = ROOT / "skills" / "study-design" / "references" / "metrics-and-reporting.yaml"
DOI_OR_URL = re.compile(r"10\.\d{4,9}/\S+|https?://\S+")


def _read(path):
    return path.read_text(encoding="utf-8")


def _index():
    return {s["id"]: s for s in yaml.safe_load(_read(CHECKLISTS / "standards-index.yaml"))["standards"]}


# ── standards-index.yaml ─────────────────────────────────────────────────────

def test_every_entry_without_a_local_checklist_has_a_reference():
    # SKILL.md Step 2 hands the user `reference` for these entries; an empty one invites citing from memory
    missing = [i for i, s in _index().items() if not s.get("file") and not DOI_OR_URL.search(str(s.get("reference", "")))]
    assert missing == []


@pytest.mark.parametrize("sid, doi", [
    ("stard-ai", "10.1038/s41591-025-03953-8"),
    ("target", "10.1136/bmj-2025-087179"),
    ("chart", "10.1136/bmjmed-2025-001632"),
    ("ideal-reporting", "10.1097/SLA.0000000000004180"),
    ("accord", "10.1371/journal.pmed.1004326"),
])
def test_current_reporting_guidelines_are_indexed_as_reporting_guidelines(sid, doi):
    s = _index()[sid]
    assert "type" not in s, f"{sid} is a reporting guideline, it must not carry a non-reporting `type`"
    assert doi in s["reference"]


def test_ideal_framework_stays_a_framework_and_points_to_the_reporting_guidelines():
    ideal = _index()["ideal"]
    assert ideal["type"] == "framework"
    assert "ideal-reporting" in ideal["for"]


@pytest.mark.parametrize("sid, doi", [
    ("robins-e", "10.1016/j.envint.2024.108602"),
    ("probast-ai", "10.1136/bmj-2024-082505"),
    ("robins-i", "10.1136/bmj.i4919"),
    ("rob-2", "10.1136/bmj.l4898"),
    ("quadas-2", "10.7326/0003-4819-155-8-201110180-00009"),
])
def test_bias_tools_are_typed_and_cited(sid, doi):
    s = _index()[sid]
    assert s["type"] == "bias_tool" and doi in s["reference"]


def test_robins_i_mentions_v2_and_nos_carries_its_caveat():
    idx = _index()
    assert "ROBINS-I V2" in idx["robins-i"]["note"] and "riskofbias.info" in idx["robins-i"]["note"]
    nos = idx["nos"]["note"]
    assert "10.1007/s10654-010-9491-z" in nos and "ROBINS-E" in nos


def test_use_with_names_only_existing_reporting_guidelines():
    idx = _index()
    for sid, s in idx.items():
        target = s.get("use_with")
        if target:
            assert target in idx, f"{sid}: use_with {target!r} is not an index id"
            assert "type" not in idx[target], f"{sid}: use_with {target!r} is a {idx[target]['type']}, not a guideline"


def test_index_metadata_is_not_overstated():
    idx = _index()
    assert "Required when" not in idx["moose"].get("note", "")
    assert "5 dimensions" not in idx["grade"]["for"]
    assert "rated up" in idx["grade"]["note"]


def test_index_header_counts_match_the_entries():
    text = _read(CHECKLISTS / "standards-index.yaml")
    idx = _index()
    with_file = sum(1 for s in idx.values() if s.get("file"))
    assert f"({len(idx)} standards)" in text
    assert f"{with_file} of {len(idx)}:" in text


# ── reporting-standards SKILL.md / output templates ──────────────────────────

def _routing_table():
    """Rows of the Step 1 routing table only, as {study type: guideline cell}."""
    skill = _read(RS / "SKILL.md")
    table = skill.split("核心路由（常用）：")[1].split("### Step 2")[0]
    rows = {}
    for line in table.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("研究类型",) and not set(cells[0]) <= set("-: "):
            rows[cells[0]] = cells[1]
    return rows


@pytest.mark.parametrize("study_type, guideline", [
    ("AI 诊断准确性", "STARD-AI"),
    ("目标试验模拟", "TARGET"),
    ("聊天机器人健康建议", "CHART"),
    ("手术 / 器械创新", "IDEAL Reporting Guidelines"),
    ("Delphi / 共识", "ACCORD"),
])
def test_reporting_skill_routes_new_guidelines_and_ideal_reporting(study_type, guideline):
    # the study type must have its own routing row whose guideline cell names the guideline (a mention in
    # another table, e.g. Common Mistakes, does not route anything)
    rows = _routing_table()
    matches = [cell for study, cell in rows.items() if study.startswith(study_type)]
    assert matches, f"no routing row for {study_type!r}"
    assert guideline in matches[0]


def test_partial_manuscript_items_count_as_not_reported_for_gate_1():
    # a status outside ✅/⚠️/❌/N/A would slip past "Gate 1 = 0 critical ❌"
    skill = _read(RS / "SKILL.md")
    assert re.findall(r"(?<!❌ )未写", skill) == [], "未写 must always be the ❌ 未写 sub-status"
    step3 = skill.split("### Step 3")[1].split("### Step 4")[0]
    assert "❌ 未写" in step3 and "critical ❌" in step3
    templates = _read(RS / "references" / "output-templates.md")
    legend = next(line for line in templates.splitlines() if line.startswith("Status legend:"))
    assert "❌ 未写" in legend and "counts as ❌" in legend
    assert re.findall(r"(?<!❌ )未写", templates) == []


def test_reporting_skill_counts_match_the_index():
    skill = _read(RS / "SKILL.md")
    idx = _index()
    with_file = sum(1 for s in idx.values() if s.get("file"))
    assert f"（{len(idx)} 条规范）" in skill
    assert f"{len(idx)} 条中有 {with_file} 条" in skill
    assert f"其余 {len(idx) - with_file} 条" in skill


def test_extensions_with_a_local_checklist_are_checked_item_by_item():
    skill = _read(RS / "SKILL.md")
    assert "扩展按上一条处理" not in skill
    templates = _read(RS / "references" / "output-templates.md")
    section3 = templates.split("## 3.")[1]
    examples = re.search(r"字段的规范（如 ([^；]+)；", section3).group(1).split("、")
    idx = _index()
    by_name = {s["name"].split(" ")[0].upper(): s for s in idx.values()}
    for name in examples:
        entry = by_name[name.upper()]
        assert not entry.get("file"), f"{name} is given as a no-checklist example but has {entry['file']}"


def test_tripod_2015_red_flag_matches_the_index():
    skill = _read(RS / "SKILL.md")
    assert "TRIPOD 2015 / PRISMA 2009" not in skill
    assert "tripod-2015" in _index() and "tripod-2015.yaml" in skill


def test_consort_ai_is_not_said_to_be_in_the_consort_2025_extension_list():
    consort_ai = _read(CHECKLISTS / "consort-ai.yaml")
    assert "lists CONSORT-AI" not in consort_ai
    note = yaml.safe_load(_read(CHECKLISTS / "consort-2025.yaml"))["extensions_still_current"]["note"]
    named = note.split("(", 1)[1].split(")", 1)[0]
    assert "CONSORT-AI" not in named


# ── literature-synthesis ─────────────────────────────────────────────────────

def test_systematic_search_does_not_present_web_search_as_a_database_search():
    skill = _read(LS / "SKILL.md")
    assert 'WebSearch(query="site:cochranelibrary.com' not in skill
    assert "Not searched" in skill and "Web search (supplementary)" in skill
    assert "Embase" in skill and "用户在库内运行" in skill
    templates = _read(LS / "references" / "output-templates.md")
    assert "cs.CV" not in templates, "WebSearch cannot apply an arXiv category filter"
    assert "Filters:** none" in templates


def test_parallel_search_dispatches_subagents_only_for_searches_the_tools_can_run():
    # team-collaboration scenario 1 used to send one subagent per "database", Cochrane via WebSearch site:
    skill = _read(LS / "SKILL.md")
    step3 = skill.split("### Step 3")[1].split("#### 数据库 A")[0]
    assert "不派子代理" in step3 and "Web search (supplementary)" in step3 and "team-collaboration" in step3
    links = skill.split("## 衔接规则")[1]
    assert "多数据库并行检索 → `team-collaboration`" not in links
    tc_line = next(line for line in links.splitlines() if "`team-collaboration`" in line)
    assert "来源 B 由用户运行" in tc_line


def test_systematic_mode_requires_two_independent_reviewers_one_human_and_grade():
    skill = _read(LS / "SKILL.md")
    assert "两名评价者独立" in skill and "至少一名是人" in skill
    assert "details of automation tools used in the process" in skill
    prisma = yaml.safe_load(_read(CHECKLISTS / "prisma-2020.yaml"))
    item8 = next(i["text"] for s in prisma["sections"] for i in s["items"] if i["id"] == "8")
    assert "details of automation tools used in the process" in item8   # quoted from the real item
    assert "GRADE" in skill and "Certainty of Evidence" in skill
    templates = _read(LS / "references" / "output-templates.md")
    assert "## Reviewers" in templates and "Cohen's κ" in templates and "Automation / AI tools used" in templates
    assert "## Certainty of Evidence" in templates


def test_bias_tool_table_uses_current_tools():
    skill = _read(LS / "SKILL.md")
    table = skill.split("2. **偏倚风险**")[1].split("3. **结果适用性**")[0]
    for tool in ("ROBINS-E", "PROBAST+AI", "ROBINS-I V2"):
        assert tool in table
    nos_row = next(line for line in table.splitlines() if "Newcastle-Ottawa" in line)
    assert "Stang" in nos_row
    assert "| 预测模型（回归或 AI） | PROBAST |" not in table


def test_scoping_reviews_are_not_sent_to_prospero():
    skill = _read(LS / "SKILL.md")
    assert "Systematic 模式要注册 → 提醒 PROSPERO" not in skill
    assert "PROSPERO 不接受范围综述" in skill and "OSF" in skill


# ── submission-preparation ───────────────────────────────────────────────────

def test_cover_letter_declares_ai_use_and_preprints():
    skill = _read(SP / "SKILL.md")
    declarations = skill.split("#### Paragraph 4: Declarations")[1].split("####")[0]
    assert "AI 使用声明" in declarations and "ICMJE" in declarations and "预印本" in declarations
    template = _read(SP / "references" / "cover-letter-template.md")
    assert "Use of AI-assisted technology" in template and "Preprint:" in template


def test_cover_letter_hook_names_title_and_type_and_uses_manuscript_numbers():
    skill = _read(SP / "SKILL.md")
    hook = skill.split("#### Paragraph 1")[1].split("#### Paragraph 2")[0]
    good = [line for line in hook.splitlines() if line.startswith("> ✅")]
    assert good and all("30%" not in line for line in good)
    assert "完整标题" in hook and "文章类型" in hook


# ── study-design metrics-and-reporting.yaml ──────────────────────────────────

def test_metrics_mapping_uses_stard_ai_and_ideal_reporting():
    rows = {r["study"]: r for r in yaml.safe_load(_read(METRICS))["mapping"]}
    assert rows["AI-assisted diagnosis (diagnostic accuracy)"]["primary"].startswith("STARD-AI")
    device = rows["Medical device/instrument innovation"]["primary"]
    assert device.startswith("IDEAL Reporting Guidelines") and "10.1097/SLA.0000000000004180" in device
    idx = _index()
    for ref in re.findall(r"index id ([a-z0-9-]+)", _read(METRICS)):
        assert ref in idx, f"metrics-and-reporting.yaml names index id {ref!r}, which does not exist"


def test_metrics_surgical_video_row_uses_stard_ai_for_diagnostic_framing():
    rows = {r["study"]: r for r in yaml.safe_load(_read(METRICS))["mapping"]}
    primary = rows["Surgical video AI"]["primary"]
    assert primary.startswith("STARD-AI") and "index id stard-ai" in primary
    assert not primary.startswith("STARD 2015")


# acronym-style guideline / tool names: STARD-AI, TRIPOD+AI, QUADAS-C, ... and plain CONSORT, CLAIM, ...
GUIDELINE_TOKEN = re.compile(r"\b[A-Z][A-Z0-9]*(?:[-+][A-Za-z0-9]+)+|\b[A-Z]{4,}\b")


def test_metrics_names_are_indexed_or_listed_as_exceptions_with_an_inline_source():
    # the header promises the index gives the reference for every name; a name outside the index must be
    # listed in the header and cited right where it is used
    text = _read(METRICS)
    header = text.split("## Performance Metrics")[0]
    idx = _index()
    names = [s["name"] for s in idx.values()]
    dumps = [yaml.safe_dump(s, allow_unicode=True) for s in idx.values()]
    for row in yaml.safe_load(text)["mapping"]:
        cells = f'{row["primary"]} {row["supplement"]}'
        for tok in sorted(set(GUIDELINE_TOKEN.findall(re.sub(r"doi:\S+", "", cells)))):
            if any(n.startswith(tok) for n in names) or any(tok in d for d in dumps):
                continue
            assert tok in header, f"{row['study']}: {tok} is not in the index and not listed in the header"
            near = cells[cells.index(tok):cells.index(tok) + 200]
            assert "not in the index" in near and re.search(r"10\.\d{4,9}/", near), f"{tok} has no inline source"
    assert "ISO 14155" in header
    device = next(r for r in yaml.safe_load(text)["mapping"] if "ISO 14155" in r["supplement"])
    assert "not in the index" in device["supplement"]
