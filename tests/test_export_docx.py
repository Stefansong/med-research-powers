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
