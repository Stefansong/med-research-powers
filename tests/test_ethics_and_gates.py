"""Regression tests for the ethics, gate and front-end skills (research-ethics, pre-submission-verification,
research-question-formulation, peer-review-simulation, pubmed-search).

These skills are advice, not code, so the tests pin the advice that was wrong before: de-identified data treated as
enough for external AI APIs and no concrete China data rules (PIPL, cross-border transfer), consent-waiver reasons
offered as alternatives, Gate 5 demanding an approval number from exempt studies, no investigator-initiated
research filing, H0/H1 forced on descriptive and prediction studies, a hard stop without the PubMed MCP, no
confidentiality guard for manuscripts under review, and no reproducibility evidence in Gate 2.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
ETHICS = SKILLS / "research-ethics"
PSV = SKILLS / "pre-submission-verification"
RQF = SKILLS / "research-question-formulation"


def _read(path):
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def checklist():
    return yaml.safe_load(_read(ETHICS / "references" / "ethics-checklist.yaml"))


@pytest.fixture(scope="module")
def gates():
    return yaml.safe_load(_read(PSV / "references" / "gates-checklist.yaml"))


def _section(checklist, sid):
    (sec,) = [s for s in checklist["sections"] if s["id"] == sid]
    return [str(i) for i in sec["items"]]


def _items_with(items, *words):
    return [i for i in items if all(w in i for w in words)]


# ── MB-2: concrete China health-data rules; de-identified is not anonymised ──────────────────

def test_checklist_keeps_six_sections(checklist):
    assert [s["id"] for s in checklist["sections"]] == [1, 2, 3, 4, 5, 6]
    assert "methods_statement_template" in checklist


def test_pipl_health_data_rules_are_concrete(checklist):
    privacy = _section(checklist, 4)
    text = "\n".join(privacy)
    assert _items_with(privacy, "敏感个人信息", "第二十八条", "医疗健康", "特定的目的", "充分的必要性")
    assert _items_with(privacy, "单独同意", "第二十九条")
    assert _items_with(privacy, "第十三条", "合法性基础")
    assert _items_with(privacy, "第二十一条", "受托方")                    # entrusted processing agreement
    assert _items_with(privacy, "个人信息保护影响评估", "第五十五条", "三年")
    assert _items_with(privacy, "第三十八条", "安全评估", "标准合同", "认证")
    flows = _items_with(privacy, "促进和规范数据跨境流动规定")
    assert flows and "敏感个人信息没有数量豁免" in flows[0] and "1 万人" in flows[0]
    assert _items_with(privacy, "人类遗传资源信息", "实施细则", "备份")
    assert "待核实" in text, "rules that could not be verified must say so"


def test_deidentified_is_not_anonymised(checklist):
    privacy = _section(checklist, 4)
    (defs,) = _items_with(privacy, "去标识化", "匿名化", "第七十三条")
    assert "仍是个人信息" in defs and "不属于个人信息" in defs
    # the old item listed 匿名化 as one more de-identification method
    assert not _items_with(privacy, "删除直接标识符 / 假名化 / 匿名化")


def test_external_ai_needs_anonymised_data_or_all_conditions(checklist):
    privacy = _section(checklist, 4)
    old = "使用外部模型 API 前确认数据已去标识化且不违反"
    assert not any(old in i for i in privacy), "de-identification alone must not clear an external AI API"
    (ai,) = _items_with(privacy, "外部 AI 服务（云端大模型 API")
    assert "默认只发送匿名化数据或汇总结果" in ai
    assert "仍是敏感个人信息" in ai and "同时满足以下全部条件" in ai
    for cond in ("合法性基础", "委托处理协议", "个人信息保护影响评估", "出境程序", "数据持有方", "伦理委员会"):
        assert cond in ai, cond
    assert "运行本插件的 AI 会话" in ai          # the chat itself is an external AI service


def test_ethics_skill_red_flag_covers_deidentified_data():
    skill = _read(ETHICS / "SKILL.md")
    flags = skill.split("## Red Flags")[1].split("## ")[0]
    (line,) = [ln for ln in flags.splitlines() if "外部 AI 服务" in ln]
    assert "去标识化" in line and "匿名化" in line and "STOP" in line
    assert "去标识化（脱敏）后仍是个人信息" in skill


# ── MB-3: China investigator-initiated clinical research filing ─────────────────────────────

def test_iit_registration_in_checklist_and_gate5(checklist, gates):
    reg = _section(checklist, 5)
    (iit,) = _items_with(reg, "国家医学研究登记备案信息系统")
    assert "国卫科教发〔2024〕32号" in iit and "第二十六条" in iit and "不替代" in iit
    assert any("国家医学研究登记备案信息系统" in str(i) for i in gates["gate_5"]["items"])


# ── MB-4: waiver conditions are cumulative; exemption from review has preconditions ─────────

def test_consent_waiver_conditions_are_cumulative(checklist):
    consent = _section(checklist, 3)
    assert not _items_with(consent, "数据已去标识化 / 无法联系 / 风险极小")
    (waiver,) = _items_with(consent, "免除知情同意", "同时满足")
    assert "CIOMS" in waiver and "最小风险" in waiver
    assert _items_with(consent, "去标识化", "本身不是免除知情同意的理由")


def test_exemption_from_review_has_preconditions(checklist):
    review = _section(checklist, 1)
    (exempt,) = _items_with(review, "第三十二条", "不涉及敏感个人信息")
    assert "匿名化" in exempt and "去标识化" in exempt
    assert _items_with(review, "免除审查要有书面依据")


# ── MB-5 / SB-10: Gate 5 accepts a documented exemption instead of an approval number ──────

def test_gate5_accepts_documented_exemption(gates):
    items = [str(i) for i in gates["gate_5"]["items"]]
    assert "伦理审查批准号已写入 Methods，且与 ethics-statement.md 一致" not in items
    (review,) = _items_with(items, "批准号", "免除伦理审查", "书面依据")
    assert "两样都没有才 ❌" in review
    assert _items_with(items, "免除知情同意")


def test_presubmission_red_flag_does_not_block_exempt_studies():
    skill = _read(PSV / "SKILL.md")
    assert "- 没有伦理批准号但要投稿 → 阻止" not in skill
    flags = skill.split("## Red Flags")[1].split("## ")[0]
    (line,) = [ln for ln in flags.splitlines() if "伦理批准号" in ln]
    assert "免除审查" in line
    gate5_row = [ln for ln in skill.splitlines() if ln.startswith("| 5 伦理与合规")][0]
    assert "免除审查" in gate5_row


def test_ethics_and_presubmission_agree_on_exemption():
    ethics = _read(ETHICS / "SKILL.md")
    conv = ethics.split("## Convergence")[1].split("## ")[0]
    assert "免除审查的书面依据" in conv
    assert "免除审查的书面依据" in ethics.split("Gate 5 →")[1].splitlines()[0]
    template = yaml.safe_load(_read(ETHICS / "references" / "ethics-checklist.yaml"))["methods_statement_template"]
    assert "批准号" in template and "免除伦理审查" in template


# ── SB-11: research-question-formulation works without the PubMed MCP ──────────────────────

def test_rqf_has_fallback_without_pubmed_mcp():
    skill = _read(RQF / "SKILL.md")
    novel = skill.split("**N（Novel）必须做一次快速查重：**")[1].split("### Round 3")[0]
    assert "不依赖 PubMed MCP" in novel
    assert "WebFetch" in novel and "eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi" in novel
    assert "WebSearch" in novel and "补充线索" in novel
    assert "告诉用户用的是哪条途径" in novel and "待查重" in novel
    assert "不需要 PubMed MCP" in skill.split("### 前置依赖")[1]


def test_pubmed_search_no_longer_hard_stops():
    skill = _read(SKILLS / "pubmed-search" / "SKILL.md")
    assert "告知用户并停止" not in skill
    fallback = skill.split("### 没有 PubMed MCP 时")[1].split("## Workflow")[0]
    assert "esearch.fcgi" in fallback and "esummary.fcgi" in fallback
    assert "⏳ Unverified" in fallback          # web-search hits are never reported as verified


UNVERIFIED_DEFINED_IN = [SKILLS / "pubmed-search" / "SKILL.md",
                         SKILLS / "pubmed-search" / "references" / "output-templates.md",
                         SKILLS / "literature-synthesis" / "SKILL.md",
                         SKILLS / "literature-synthesis" / "references" / "output-templates.md",
                         PSV / "SKILL.md", PSV / "references" / "gates-checklist.yaml",
                         PSV / "references" / "readiness-report-template.md"]


@pytest.mark.parametrize("path", UNVERIFIED_DEFINED_IN, ids=lambda p: str(p.relative_to(SKILLS)))
def test_unverified_status_is_defined_like_the_gate_3_legend(path):
    """pubmed-search Mode 3 defined ⏳ as "(tool error)" only, while its own fallback (and the Gate 3 legend)
    keep a citation found only by web search, or not checked at all, at ⏳ Unverified."""
    text = _read(path)
    assert "Unverified (tool error)" not in text                    # the old "tool error only" label
    defs = [ln for ln in text.splitlines()
            if re.match(r"\s*(?:\|\s*⏳ Unverified|- \"⏳ Unverified \()", ln)        # a table row / checklist label
            or ("⏳ Unverified" in ln and "ℹ️ Non-PubMed" in ln)]                    # a one-line legend
    assert defs, f"{path.name}: no definition of ⏳ Unverified found"
    for ln in defs:
        assert re.search(r"web search|WebSearch", ln), ln
    if path.name == "SKILL.md" and path.parent.name == "pubmed-search":
        mode3 = text.split("### Mode 3")[1].split("### Mode 4")[0]
        assert re.search(r"只凭 WebSearch 找到[^\n]*→ ⏳", mode3)         # the verification steps say so too


# ── SC-13: confidentiality guard for manuscripts received for review ────────────────────────

def test_peer_review_simulation_confidentiality_guard():
    skill = _read(SKILLS / "peer-review-simulation" / "SKILL.md")
    desc = re.search(r"^description: (.*)$", skill, re.M).group(1)
    assert desc.startswith("Use when") and "user's own" in desc
    overview = skill.split("## Overview")[1].split("## When to Use")[0]
    assert "只用于用户自己的稿件" in overview and "保密" in overview and "ICMJE" in overview
    not_use = skill.split("## When NOT to Use")[1].split("## ")[0]
    assert "别人投来的稿件" in not_use
    flags = skill.split("## Red Flags")[1].split("## ")[0]
    assert any("审稿人身份" in ln and "STOP" in ln for ln in flags.splitlines())


# ── SC-14: H0/H1 only for hypothesis-testing studies ───────────────────────────────────────

def test_h0_h1_only_for_hypothesis_testing_studies():
    skill = _read(RQF / "SKILL.md")
    round3 = skill.split("### Round 3")[1].split("### Round 4")[0]
    assert "- 零假设和备择假设（能用统计语言表述）" not in round3
    rows = {ln.split("|")[1].strip(): ln for ln in round3.splitlines() if ln.startswith("| ") and "---" not in ln}
    desc = [v for k, v in rows.items() if k.startswith("描述性")][0]
    pred = [v for k, v in rows.items() if k.startswith("预测模型")][0]
    assert "H0" not in desc and "estimand" in desc
    assert "H0" not in pred and "性能指标" in pred
    output = skill.split("## Output")[1].split("## ")[0]
    (item3,) = [ln for ln in output.splitlines() if ln.startswith("3. ")]
    assert "仅假设检验型研究" in item3 and "估计目标" in item3
    conv = skill.split("## Convergence")[1].split("## ")[0]
    (item2,) = [ln for ln in conv.splitlines() if ln.startswith("2. ")]
    assert "假设检验型研究" in item2 and "估计目标" in item2


# ── CG-13: Gate 2 checks the reproducibility evidence ──────────────────────────────────────

def test_gate2_checks_reproduce_check_report(gates):
    g2 = gates["gate_2"]
    assert "reproduce-check.md" in g2["inputs"]
    (item,) = [str(i) for i in g2["items"] if "reproduce-check.md" in str(i)]
    assert "退出码 0" in item and "--compare-stdout" in item and "❌" in item
    skill = _read(PSV / "SKILL.md")
    row = [ln for ln in skill.splitlines() if ln.startswith("| 2 统计完整性")][0]
    assert "reproduce-check.md" in row and "退出码 0" in row


def test_gate2_wording_matches_reproduce_check_report():
    """Gate 2 reads the words reproduce_check.py writes; keep them in step."""
    src = _read(SKILLS / "statistical-analysis" / "scripts" / "reproduce_check.py")
    assert re.search(r'0:\s*"一致"', src), "report verdict for exit 0 must stay 「一致」"
    assert re.search(r'2:\s*"未完成', src), "report verdict for exit 2 must stay 「未完成…」"
    assert "未计入结论" in src
    assert '"屏幕输出（stdout）"' in src and '"错误输出（stderr）"' in src     # the line labels Gate 2 names


# ── Round 2: Gate 2 must not fail a consistent run because the script writes to stderr ─────

def _gate2_reproduce_item(gates):
    (item,) = [str(i) for i in gates["gate_2"]["items"] if "reproduce-check.md" in str(i)]
    return item


def test_gate2_accepts_uncounted_stderr_but_not_uncounted_stdout(tmp_path, gates):
    """R / Python packages print start-up messages to stderr; a consistent check run as statistical-analysis
    says (--compare-stdout only) must pass Gate 2 as the gate is written."""
    (tmp_path / "a.py").write_text(
        "import os, sys\n"
        "os.makedirs('results', exist_ok=True)\n"
        "open('results/r.csv', 'w').write('x,y\\n1,2\\n')\n"
        "print('[SAP 4.1] OR 1.23 (95% CI 1.01-1.50)')\n"
        "print('Loading required package: foo', file=sys.stderr)\n", encoding="utf-8")
    report = tmp_path / "reproduce-check.md"
    script = SKILLS / "statistical-analysis" / "scripts" / "reproduce_check.py"
    proc = subprocess.run([sys.executable, str(script), "--cmd", f'"{sys.executable}" a.py', "--outputs", "results/",
                           "--compare-stdout", "--report", str(report)],
                          cwd=str(tmp_path), capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    lines = report.read_text(encoding="utf-8").splitlines()
    assert "- 结论：**一致**" in lines
    uncounted = [ln for ln in lines if "未计入结论" in ln]
    assert uncounted and all(ln.startswith("- 错误输出（stderr）") for ln in uncounted)
    assert any(ln.startswith("- 屏幕输出（stdout）") and "未计入结论" not in ln for ln in lines)
    item = _gate2_reproduce_item(gates)
    assert "没有「未计入结论」字样" not in item            # the old rule failed this run
    assert "「屏幕输出（stdout）」一行没有「未计入结论」" in item
    assert "「错误输出（stderr）」一行写「未计入结论」不算问题" in item
    assert "不要为了过 Gate 而加" in item and "需要留意" in item


def test_readiness_template_lists_every_reproduce_check_verdict():
    template = _read(PSV / "references" / "readiness-report-template.md")
    (row,) = [ln for ln in template.splitlines() if ln.startswith("| 2. Statistical completeness")]
    assert "一致 / 不一致 / 未完成 / 缺失" in row


# ── Round 2: a consent waiver is not an alternative to approval / exemption from review ──────

def test_consent_waiver_does_not_replace_approval_or_exemption(gates):
    skill = _read(PSV / "SKILL.md")
    flags = skill.split("## Red Flags")[1].split("## ")[0]
    (line,) = [ln for ln in flags.splitlines() if "伦理批准号" in ln]
    assert "或免除知情同意的伦理委员会批准" not in line
    assert "免除知情同意不能代替" in line
    items = [str(i) for i in gates["gate_5"]["items"]]
    (consent,) = _items_with(items, "知情同意声明")
    assert "满足的各项条件" in consent and "不能代替" in consent
    ethics = _read(ETHICS / "SKILL.md")
    (eflag,) = [ln for ln in ethics.split("## Red Flags")[1].splitlines() if "没有伦理批准就要开始收集数据" in ln]
    assert "书面依据的免除审查" in eflag and "免除知情同意不能代替" in eflag
    assert "必须先取得批准或豁免" not in ethics


# ── Round 2: checklist cross-reference and separate consent in §3 ────────────────────────────

def test_review_section_cross_reference_points_at_the_exemption_items(checklist):
    review = _section(checklist, 1)
    assert not _items_with(review, "见本节最后两条")
    assert "见本节以“免除审查”开头的两条" in review[0]
    exemption = [i for i in review if i.startswith("免除审查")]
    assert len(exemption) == 2 and any("第三十二条" in i for i in exemption)


def test_consent_form_ai_training_needs_separate_consent(checklist):
    consent = _section(checklist, 3)
    assert not _items_with(consent, "后两者需单独同意")
    (uses,) = _items_with(consent, "同意书", "AI 模型训练")
    for word in ("单独同意", "第二十九条", "第二十三条", "第三十九条", "待核实"):
        assert word in uses, word
    assert "以同意为依据处理医疗健康信息（含 AI 模型训练、二次使用）须取得个人的单独同意" in uses


def test_scoping_reviews_register_outside_prospero(checklist):
    reg = _section(checklist, 5)
    (scoping,) = _items_with(reg, "范围综述")
    assert "OSF" in scoping and "PROSPERO 不接受范围综述" in scoping


# ── Round 2: Gate 3 AI-use disclosure per ICMJE, consistent with revision-response ──────────

def test_gate3_ai_disclosure_not_only_when_journal_asks(gates):
    items = [str(i) for i in gates["gate_3"]["phase_F"]["items"]]
    assert "期刊要求时，在 Methods 或 Acknowledgements 声明 AI 工具的使用方式" not in items
    (ai,) = _items_with(items, "ICMJE")
    assert "不只在期刊要求时" in ai and "Acknowledgements" in ai and "Methods" in ai
    assert "submission-preparation Paragraph 4" in ai
    revision = _read(SKILLS / "revision-response" / "SKILL.md")
    assert "按 ICMJE 在修回稿相应位置更新 AI 使用声明" in revision
