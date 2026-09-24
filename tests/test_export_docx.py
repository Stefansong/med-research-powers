"""Tests for skills/manuscript-export/scripts/export_docx.py.

Run from the repo root:  python3 -m pytest tests/test_export_docx.py -q
Requires: python-docx, pyyaml (same as the script itself).
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("docx")
pytest.importorskip("yaml")
from docx import Document  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "manuscript-export" / "scripts" / "export_docx.py"
YAML = ROOT / "skills" / "manuscript-writing" / "references" / "journal-templates.yaml"

MINIMAL = {
    "title-page.md": "# Deep learning for bladder cancer on CT\n\n**Authors:** A. Author^1^\n",
    "abstract.md": ("# Abstract\n\n**Background:** Detection is hard.\n\n**Methods:** We trained a CNN.\n\n"
                    "**Results:** Sensitivity ~90%.\n\n**Conclusions:** Promising.\n"),
    "key-points.md": "# Key Points\n\n**Question:** Does it work?\n\n**Findings:** Yes.\n\n**Meaning:** Useful.\n",
    "research-in-context.md": ("# Research in Context\n\n**Evidence before this study:** Little.\n\n"
                               "**Added value of this study:** Some.\n\n**Implications:** More trials.\n"),
    "introduction.md": ("# Introduction\n\nPrior work reported ~90% sensitivity using 2^10 images.[1]\n\n"
                        "<!-- PLACEHOLDER: add funding sentence -->\n"),
    "methods.md": "# Methods\n\nWe included adults with *suspected* cancer; H~2~O was **not** used.\n",
    "results.md": ("# Results\n\n**Table 1.** Baseline characteristics\n\n"
                   "| Variable | Cases | Controls |\n|---|---|---|\n| Age | 65 | 63 |\n\n"
                   "**Figure 1.** ROC curve.\n"),
    "discussion.md": "# Discussion\n\nOur model achieved high sensitivity.\n",
    "references.md": ("# References\n\n1. Smith J. Bladder cancer on CT. *Radiology*. 2020;295:1-9.\n"
                      "2. Doe A. Deep learning in urology. Eur Urol. 2021;80:10-20.\n"),
    "supplementary.md": "# Supplementary\n\n**eTable 1.** Extra\n\n| A | B |\n|---|---|\n| 1 | 2 |\n",
}


@pytest.fixture
def manuscript(tmp_path):
    d = tmp_path / "manuscript"
    d.mkdir()
    for name, content in MINIMAL.items():
        (d / name).write_text(content, encoding="utf-8")
    return d


def run_export(manuscript_dir, journal, out, *extra, env=None):
    cmd = [sys.executable, str(SCRIPT), "--manuscript-dir", str(manuscript_dir), "--journal", journal,
           "--output", str(out), "--yaml", str(YAML), *extra]
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=str(manuscript_dir.parent), env=full_env)


def headings(docx_path):
    return [p.text for p in Document(str(docx_path)).paragraphs if p.style.name.startswith("Heading")]


def full_text(docx_path):
    return "\n".join(p.text for p in Document(str(docx_path)).paragraphs)


@pytest.mark.parametrize("journal", ["european-urology", "nature", "lancet", "jama-network-open"])
def test_export_exits_zero_and_writes_docx(manuscript, tmp_path, journal):
    out = tmp_path / f"{journal}.docx"
    r = run_export(manuscript, journal, out, "--report", str(tmp_path / f"{journal}-report.md"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert out.exists() and out.stat().st_size > 0
    assert (tmp_path / f"{journal}-report.md").exists()


def test_nature_order_is_i_r_d_m(manuscript, tmp_path):
    out = tmp_path / "nature.docx"
    assert run_export(manuscript, "nature", out).returncode == 0
    h = headings(out)
    idx = [h.index(x) for x in ("Introduction", "Results", "Discussion", "Methods")]
    assert idx == sorted(idx), h


def test_standard_order_is_i_m_r_d(manuscript, tmp_path):
    out = tmp_path / "eu.docx"
    assert run_export(manuscript, "european-urology", out).returncode == 0
    h = headings(out)
    idx = [h.index(x) for x in ("Introduction", "Methods", "Results", "Discussion")]
    assert idx == sorted(idx), h


def test_lancet_includes_research_in_context(manuscript, tmp_path):
    out = tmp_path / "lancet.docx"
    r = run_export(manuscript, "lancet", out)
    assert r.returncode == 0
    h = headings(out)
    assert "Research in Context" in h
    assert h.index("Research in Context") < h.index("Introduction")
    assert "Key Points" not in h  # not part of the Lancet family order
    assert "research-in-context" in r.stdout


def test_jama_includes_key_points(manuscript, tmp_path):
    out = tmp_path / "jama.docx"
    r = run_export(manuscript, "jama-network-open", out)
    assert r.returncode == 0
    h = headings(out)
    assert "Key Points" in h
    assert h.index("Key Points") < h.index("Abstract")
    assert "Research in Context" not in h


def test_unpaired_markers_survive_in_body(manuscript, tmp_path):
    out = tmp_path / "eu.docx"
    assert run_export(manuscript, "european-urology", out).returncode == 0
    text = full_text(out)
    assert "~90%" in text
    assert "2^10" in text
    assert "**" not in text and "~2~" not in text  # closed pairs were converted


def test_placeholder_is_reported(manuscript, tmp_path):
    report = tmp_path / "report.md"
    r = run_export(manuscript, "european-urology", tmp_path / "eu.docx", "--report", str(report))
    assert r.returncode == 0
    txt = report.read_text(encoding="utf-8")
    assert "PLACEHOLDER" in txt and "⚠️" in txt
    assert "introduction.md:" in txt


def test_missing_family_section_is_flagged(manuscript, tmp_path):
    (manuscript / "key-points.md").unlink()
    r = run_export(manuscript, "jama-network-open", tmp_path / "jama.docx")
    assert r.returncode == 0
    assert "⚠️" in r.stdout and "key-points.md" in r.stdout


def test_word_buckets_are_separate(manuscript, tmp_path):
    r = run_export(manuscript, "european-urology", tmp_path / "eu.docx")
    assert r.returncode == 0
    assert "| Abstract |" in r.stdout
    assert "| References (numbered entries) | 2 |" in r.stdout
    body_line = next(l for l in r.stdout.splitlines() if l.startswith("| Body ("))
    body_words = int(body_line.split("|")[2].strip())
    assert 0 < body_words < 40  # abstract / title page / references are not in the body bucket


def test_unknown_journal_exits_2(manuscript, tmp_path):
    r = run_export(manuscript, "no-such-journal-xyz", tmp_path / "x.docx")
    assert r.returncode == 2
    assert "--search" in r.stderr
    assert not (tmp_path / "x.docx").exists()


def test_supplementary_flag_writes_second_docx(manuscript, tmp_path):
    out = tmp_path / "manuscript" / "manuscript.docx"
    r = run_export(manuscript, "european-urology", out, "--supplementary")
    assert r.returncode == 0
    assert (tmp_path / "manuscript" / "supplementary.docx").exists()
    assert "supplementary.docx" in r.stdout


def test_runs_under_c_locale(manuscript, tmp_path):
    env = {"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "PYTHONIOENCODING": ""}
    r = run_export(manuscript, "lancet", tmp_path / "lancet.docx", "--report", str(tmp_path / "r.md"), env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Research in Context" in headings(tmp_path / "lancet.docx")


# ─── unit tests of the inline formatter ──────────────────────────────────────

def _load_module():
    spec = importlib.util.spec_from_file_location("export_docx", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _runs(mod, text):
    doc = Document()
    p = doc.add_paragraph()
    mod.add_formatted_text(p, text, {"font": "Times New Roman"})
    return [(r.text, bool(r.bold), bool(r.italic), bool(r.font.superscript), bool(r.font.subscript))
            for r in p.runs]


def test_inline_formatting_keeps_unpaired_markers():
    mod = _load_module()
    assert "".join(t for t, *_ in _runs(mod, "~90% sensitivity")) == "~90% sensitivity"
    assert "".join(t for t, *_ in _runs(mod, "2^10")) == "2^10"
    assert "".join(t for t, *_ in _runs(mod, "marked with * were")) == "marked with * were"
    assert mod.plain_text("~90% and 2^10") == "~90% and 2^10"


def test_inline_formatting_converts_closed_pairs():
    mod = _load_module()
    assert ("bold", True, False, False, False) in _runs(mod, "**bold**")
    assert ("it", False, True, False, False) in _runs(mod, "*it*")
    assert ("2", False, False, True, False) in _runs(mod, "10^2^")
    assert ("2", False, False, False, True) in _runs(mod, "H~2~O")
    assert "".join(t for t, *_ in _runs(mod, "H~2~O")) == "H2O"


@pytest.mark.parametrize("value,limit", [
    ("≤40, Vancouver", 40),
    ("150-250 words", 250),          # a range: the upper bound, not the first number
    ("200–300 words", 300),
    ("2,500 words", 2500),
    ("8 pages", None),               # a page limit is not a word limit (ieee-jbhi)
    ("≤10 pages", None),             # ieee-tmi
    ("unlimited", None),
])
def test_parse_limit(value, limit):
    spec = importlib.util.spec_from_file_location("export_docx", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._parse_limit(value) == limit


@pytest.mark.parametrize("value", [
    "no hard limit (~25 per 1,000 words; up to ~150 for Reviews), Nature",
    "no fixed limit (figure legends ≤350 words each)",
    "no formal limit",
    "no strict limit",
    "8–10 printed pages including figures, tables and references (~650 words per page)",
    "≤10 double-column pages",
])
def test_parse_limit_no_limit_and_page_phrases(value):
    assert _load_module()._parse_limit(value) is None


@pytest.mark.parametrize("value,limit", [
    ("≤100 (recommended), AMA", 100),     # soft limits still give a number (a ⚠️ at most)
    ("flexible (usually <100)", 100),
    ("3000 words, 6 pages", 3000),        # the page count belongs to another number
])
def test_parse_limit_soft_limits_keep_their_number(value, limit):
    assert _load_module()._parse_limit(value) == limit


# ─── malformed journal-overrides.yaml ────────────────────────────────────────

@pytest.mark.parametrize("content", [
    "- just a string\n- another\n",                  # a list of strings
    "journals:\n  - id: x\n",                        # a mapping without `templates`
    "just some text\n",                              # a scalar
    "templates:\n  id: x\n",                         # `templates` is not a list
    "templates:\n  - journal: No Id Journal\n",      # an entry without `id`
    "templates: [\n",                                # invalid YAML
])
def test_malformed_overrides_exit_2_with_one_error_line(manuscript, tmp_path, content):
    ov = tmp_path / "bad-overrides.yaml"
    ov.write_text(content, encoding="utf-8")
    out = tmp_path / "x.docx"
    r = run_export(manuscript, "european-urology", out, "--overrides", str(ov))
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Traceback" not in r.stderr
    errors = [l for l in r.stderr.splitlines() if l.startswith("Error:")]
    assert len(errors) == 1 and errors[0].startswith("Error: overrides file:"), r.stderr
    assert not out.exists()


def test_malformed_default_overrides_in_cwd_is_an_error(manuscript, tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text("templates: 42\n", encoding="utf-8")  # cwd = tmp_path
    r = run_export(manuscript, "european-urology", tmp_path / "x.docx")
    assert r.returncode == 2 and "Error: overrides file:" in r.stderr and "Traceback" not in r.stderr


def test_empty_overrides_file_is_accepted(manuscript, tmp_path):
    ov = tmp_path / "empty.yaml"
    ov.write_text("", encoding="utf-8")
    r = run_export(manuscript, "european-urology", tmp_path / "x.docx", "--overrides", str(ov))
    assert r.returncode == 0, r.stderr


def test_missing_named_overrides_warns_and_uses_library(manuscript, tmp_path):
    r = run_export(manuscript, "european-urology", tmp_path / "x.docx", "--overrides", str(tmp_path / "nope.yaml"))
    assert r.returncode == 0, r.stderr
    assert "Warning: overrides file not found" in r.stderr


def test_valid_overrides_entry_is_used(manuscript, tmp_path):
    ov = tmp_path / "ov.yaml"
    ov.write_text("templates:\n  - id: my-journal\n    journal: My Journal\n    family: jama\n"
                  "    word_limit: 3000 words\n", encoding="utf-8")
    out = tmp_path / "mine.docx"
    r = run_export(manuscript, "my-journal", out, "--overrides", str(ov))
    assert r.returncode == 0, r.stderr
    assert "Key Points" in headings(out)


# ─── Markdown block parsing (the .docx is opened and inspected) ──────────────

@pytest.fixture(scope="module")
def mod():
    return _load_module()


def export_md(mod, tmp_path, md, section="results.md", journal="european-urology"):
    """Export one section file; returns (Document, stats, report text)."""
    d = tmp_path / "ms"
    d.mkdir(exist_ok=True)
    (d / section).write_text(md, encoding="utf-8")
    config = mod.get_journal_config(journal, str(YAML))
    out = tmp_path / "out.docx"
    stats = mod.build_docx(str(d), config, str(out))
    return Document(str(out)), stats, mod.generate_report(stats, config, str(out))


def paras(doc):
    return [(p.style.name, p.text) for p in doc.paragraphs]


def texts(doc):
    return [p.text for p in doc.paragraphs if p.text]


def test_soft_wrapped_lines_join_into_one_paragraph(mod, tmp_path):
    md = ("# Results\n\nThe first line of a paragraph\nthat was soft-wrapped\n   over three lines.\n\n"
          "Second paragraph.\n")
    doc, stats, _ = export_md(mod, tmp_path, md)
    assert texts(doc) == ["Results", "The first line of a paragraph that was soft-wrapped over three lines.",
                          "Second paragraph."]
    assert stats["words"]["results"] == 14


def test_cjk_lines_join_without_space(mod, tmp_path):
    md = "中文第一行\n第二行。\n\n结果显示，\nAUC 为 0.9\n\nEnglish words\n中文\n\n**结果**\n显示良好\n"
    doc, _, _ = export_md(mod, tmp_path, md)
    assert texts(doc) == ["中文第一行第二行。", "结果显示，AUC 为 0.9", "English words 中文", "结果显示良好"]


def test_hard_line_break_is_kept(mod, tmp_path):
    doc, _, _ = export_md(mod, tmp_path, "Line one  \nLine two\\\nLine three\n")
    assert texts(doc) == ["Line one\nLine two\nLine three"]


def test_bold_label_lines_joined_are_reported(mod, tmp_path):
    doc, stats, report = export_md(mod, tmp_path, "**Background:** Hard.\n**Methods:** A CNN.\n", "abstract.md")
    assert texts(doc) == ["Background: Hard. Methods: A CNN."]
    assert any(w.startswith("abstract.md:1 — lines 1–2 were joined") for w in stats["warnings"])
    assert "put a blank line between them" in report


def test_fenced_code_block_is_verbatim(mod, tmp_path):
    md = ("Intro text.\n\n```python\n# not a heading\nx = **not bold** * 2\n    indented\n"
          "<!-- kept inside code -->\n```\n\n~~~\n## also code\n- not a bullet\n~~~\n")
    doc, stats, _ = export_md(mod, tmp_path, md)
    assert not any(s.startswith("Heading") or s.startswith("List") for s, _ in paras(doc))
    code = [p for p in doc.paragraphs if p.text.startswith("# not a heading")]
    assert len(code) == 1
    assert code[0].text == "# not a heading\nx = **not bold** * 2\n    indented\n<!-- kept inside code -->"
    assert all(r.font.name == "Courier New" and not r.bold for r in code[0].runs)
    assert "## also code\n- not a bullet" in texts(doc)
    assert stats["words"]["results"] == 2          # code is not counted as words


def test_unclosed_fence_is_reported(mod, tmp_path):
    doc, stats, report = export_md(mod, tmp_path, "Text.\n\n```\ncode to the end\n")
    assert "code to the end" in texts(doc)
    assert any("never closed" in w for w in stats["warnings"]) and "never closed" in report


def test_strip_html_comments_skips_code_fences(mod):
    raw = "a <!-- x -->b\n```\n<!-- keep -->\n```\n<!--\nmulti\n-->c\n"
    out = mod.strip_html_comments(raw)
    assert out.split("\n") == ["a b", "```", "<!-- keep -->", "```", "", "", "c", ""]


def test_heading_levels_4_to_6(mod, tmp_path):
    doc, _, _ = export_md(mod, tmp_path, "#### Level four\n\n##### Level five ##\n\n###### Level six\n")
    assert paras(doc) == [("Heading 4", "Level four"), ("Heading 5", "Level five"), ("Heading 6", "Level six")]


def test_horizontal_rules_are_not_text(mod, tmp_path):
    doc, _, _ = export_md(mod, tmp_path, "Above.\n\n---\n\n***\n\n_ _ _\n\nBelow.\n")
    assert texts(doc) == ["Above.", "Below."]
    rules = [p for p in doc.paragraphs if not p.text]
    assert len(rules) == 3 and all("w:pBdr" in p._p.xml for p in rules)


def test_setext_headings(mod, tmp_path):
    doc, _, _ = export_md(mod, tmp_path, "Main title\n===\n\nSub title\n---\n\nText.\n")
    assert paras(doc) == [("Heading 1", "Main title"), ("Heading 2", "Sub title"), ("Normal", "Text.")]


def test_nested_lists_keep_level(mod, tmp_path):
    md = ("- top item that\n  wraps onto a second line\n  - second level\n    - third level\n"
          "      - fourth level\n- back to top\n\n"
          "1. one\n   1. sub-one\n   - sub-bullet\n2. two\n\n   Continuation paragraph of two.\n")
    doc, stats, _ = export_md(mod, tmp_path, md)
    assert paras(doc) == [
        ("List Bullet", "top item that wraps onto a second line"),
        ("List Bullet 2", "second level"),
        ("List Bullet 3", "third level"),
        ("List Bullet 3", "fourth level"),       # deepest style the template has
        ("List Bullet", "back to top"),
        ("List Number", "1. one"),
        ("List Number 2", "1. sub-one"),
        ("List Bullet 2", "sub-bullet"),
        ("List Number", "2. two"),
        ("List Continue", "Continuation paragraph of two."),
    ]
    numbered = [p for p in doc.paragraphs if p.style.name.startswith("List Number")]
    assert all('w:numId w:val="0"' in p._p.xml for p in numbered)     # literal numbers, no auto-numbering
    assert numbered[1].paragraph_format.left_indent > numbered[0].paragraph_format.left_indent


def test_nested_reference_items_are_not_counted(mod, tmp_path):
    md = "# References\n\n1. Smith J. A. 2020.\n   1. erratum note\n2. Doe A. B. 2021.\n"
    _, stats, _ = export_md(mod, tmp_path, md, "references.md")
    assert stats["ref_count"] == 2


def test_table_alignment_row_and_escaped_pipe(mod, tmp_path):
    md = "| Centre | Left | Right |\n|:-:|:--|--:|\n| 1 | a \\| b | 3 |\n"
    doc, stats, _ = export_md(mod, tmp_path, md)
    (t,) = doc.tables
    assert [[c.text for c in r.cells] for r in t.rows] == [["Centre", "Left", "Right"], ["1", "a | b", "3"]]
    assert [c.paragraphs[0].alignment for c in t.rows[1].cells] == [
        mod.WD_ALIGN_PARAGRAPH.CENTER, mod.WD_ALIGN_PARAGRAPH.LEFT, mod.WD_ALIGN_PARAGRAPH.RIGHT]
    assert stats["table_count"] == 1 and not stats["warnings"]


def test_table_without_outer_pipes(mod, tmp_path):
    md = "Caption line\nGroup | *n* | Mean\n--- | --- | ---\nA | 10 | 1.5\nB | 12 | 2.5\n\nAfter.\n"
    doc, stats, _ = export_md(mod, tmp_path, md)
    (t,) = doc.tables
    assert [[c.text for c in r.cells] for r in t.rows] == [
        ["Group", "n", "Mean"], ["A", "10", "1.5"], ["B", "12", "2.5"]]
    assert texts(doc) == ["Caption line", "After."]


def test_table_extra_cells_are_kept_and_reported(mod, tmp_path):
    md = "| A | B |\n|---|---|\n| 1 | 2 | 3 |\n| 4 | 5 | |\n"
    doc, stats, report = export_md(mod, tmp_path, md)
    (t,) = doc.tables
    assert [[c.text for c in r.cells] for r in t.rows] == [["A", "B", ""], ["1", "2", "3"], ["4", "5", ""]]
    assert len(stats["warnings"]) == 1 and stats["warnings"][0].startswith("results.md:3 — table row has 3 cells")
    assert "results.md:3 — table row has 3 cells but the header has 2" in report


def test_inline_nested_emphasis(mod):
    assert _runs(mod, "***x***") == [("x", True, True, False, False)]
    assert _runs(mod, "**a *b* c**") == [("a ", True, False, False, False), ("b", True, True, False, False),
                                         (" c", True, False, False, False)]
    assert _runs(mod, "*a **b** c*") == [("a ", False, True, False, False), ("b", True, True, False, False),
                                         (" c", False, True, False, False)]
    assert mod.plain_text("***x*** **a *b* c**") == "x a b c"
    assert _runs(mod, "**方法：**本研究")[0] == ("方法：", True, False, False, False)
    assert mod.plain_text("Age*, BMI* and 0.82***") == "Age*, BMI* and 0.82***"


def test_underscore_emphasis_respects_word_boundaries(mod):
    runs = _runs(mod, "_italic_ and __bold__ but snake_case_names, file_1_v2.csv and __init__.py")
    assert ("italic", False, True, False, False) in runs
    assert ("bold", True, False, False, False) in runs
    text = "".join(t for t, *_ in runs)
    assert "snake_case_names" in text and "file_1_v2.csv" in text


def test_inline_code_escapes_and_html_tags(mod):
    doc = Document()
    p = doc.add_paragraph()
    mod.add_formatted_text(p, r"Use `a*b*c` with \*literal\* stars, x<sup>2</sup>, ~~old~~", {"font": "Arial"})
    assert p.text == "Use a*b*c with *literal* stars, x2, old"
    code = [r for r in p.runs if r.text == "a*b*c"]
    assert code and code[0].font.name == "Courier New"
    assert any(r.text == "2" and r.font.superscript for r in p.runs)
    assert any(r.text == "old" and r.font.strike for r in p.runs)


def test_links_become_hyperlinks(mod):
    doc = Document()
    p = doc.add_paragraph()
    mod.add_formatted_text(p, "See [the **protocol**](https://example.org/p?a=1) and <https://doi.org/10.1/x>; "
                              "![Figure 1](fig1.png) stays.", {"font": "Arial"})
    assert p.text == "See the protocol and https://doi.org/10.1/x; ![Figure 1](fig1.png) stays."
    assert [(h.text, h.url) for h in p.hyperlinks] == [("the protocol", "https://example.org/p?a=1"),
                                                         ("https://doi.org/10.1/x", "https://doi.org/10.1/x")]
    assert any(r.bold for r in p.hyperlinks[0].runs)
    assert mod.plain_text("[text](http://x.org)") == "text"


def test_pandoc_citations_are_kept_and_reported(mod, tmp_path):
    md = ("Prior work [@smith2020; @doe2021, p. 3] and @lee2019 disagree.\n"
          "Contact a.b@hospital.org or see [the site](https://x.org/@user).\n\n"
          "| Study | Ref |\n|---|---|\n| X | [@smith2020] |\n")
    doc, stats, report = export_md(mod, tmp_path, md)
    assert "[@smith2020; @doe2021, p. 3] and @lee2019" in texts(doc)[0]
    assert sorted({k for k, _ in stats["citations"]}) == ["doe2021", "lee2019", "smith2020"]
    assert "Citation keys not converted (3)" in report
    assert "`@smith2020` — results.md:1, results.md:6" in report
    assert "@hospital" not in report and "@user" not in report


def test_no_conversion_notes_when_clean(manuscript, tmp_path):
    report = tmp_path / "r.md"
    assert run_export(manuscript, "european-urology", tmp_path / "eu.docx", "--report", str(report)).returncode == 0
    assert "## Conversion notes\n- ✅ Nothing to note" in report.read_text(encoding="utf-8")


@pytest.mark.parametrize("snippet", [
    "Median follow-up was [待补：来源] months.",
    "AUC ［待补］ in the test set.",
    "AUC 【待补】 in the test set.",
    "Sites: [待填].",
    "| Metric | Value |\n|---|---|\n| AUC | 【待补】 |",
    "<!-- 待补：基金号 -->",
])
def test_chinese_placeholders_are_reported(mod, tmp_path, snippet):
    _, stats, report = export_md(mod, tmp_path, f"# Results\n\n{snippet}\n")
    assert stats["placeholders"] and stats["placeholders"][0].startswith("results.md:")
    assert "待" in stats["placeholders"][0]
    assert "No placeholders detected" not in report
