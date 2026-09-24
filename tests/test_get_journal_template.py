"""Tests for skills/manuscript-writing/scripts/get_journal_template.py and journal-templates.yaml.

Run from the repo root:  python3 -m pytest tests/test_get_journal_template.py -q
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "manuscript-writing" / "scripts" / "get_journal_template.py"
YAML = ROOT / "skills" / "manuscript-writing" / "references" / "journal-templates.yaml"
FAMILIES = {"lancet", "jama", "nature", "ieee", "standard"}


def run(*args, cwd=None, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(cwd or ROOT),
                          env={**os.environ, **(env or {})})


# ─── the data file ───────────────────────────────────────────────────────────

def test_yaml_structure_and_count():
    with open(YAML, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "templates" in data and "data_as_of" in data
    assert "JCR 2022" in data["data_as_of"]
    templates = data["templates"]
    assert len(templates) == 240
    ids = [t["id"] for t in templates]
    assert len(ids) == len(set(ids))
    assert all(t.get("family") in FAMILIES for t in templates)
    by_id = {t["id"]: t for t in templates}
    assert by_id["lancet-neurology"]["family"] == "lancet"
    assert by_id["jama-network-open"]["family"] == "jama"
    assert by_id["nature"]["family"] == "nature"
    assert by_id["eclinical-medicine"]["family"] == "lancet"
    assert by_id["ieee-tmi"]["family"] == "ieee"
    assert by_id["european-urology"]["family"] == "standard"
    assert by_id["nature-medicine"]["system"] == "Nature MTS (eJournalPress)"
    assert "Key findings and limitations" in by_id["european-urology"]["abstract"]
    assert not any("no APC" in s for s in by_id["eclinical-medicine"].get("special", []))


# ─── the script ──────────────────────────────────────────────────────────────

def test_id_lookup_json(tmp_path):
    r = run("--id", "nature", "--json", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    entry = json.loads(r.stdout)
    assert entry["id"] == "nature" and entry["family"] == "nature"
    assert "JCR 2022" in entry["data_as_of"]


def test_id_lookup_yaml_snippet(tmp_path):
    r = run("--id", "european-urology", cwd=tmp_path)
    assert r.returncode == 0
    assert "id: european-urology" in r.stdout
    assert "family: standard" in r.stdout
    assert "≤250 words" in r.stdout  # UTF-8 output intact


def test_unknown_id_exits_1_and_hints_search(tmp_path):
    r = run("--id", "no-such-journal", cwd=tmp_path)
    assert r.returncode == 1
    assert "--search" in r.stderr


def test_search_lists_candidates(tmp_path):
    r = run("--search", "urol", cwd=tmp_path)
    assert r.returncode == 0
    assert "european-urology" in r.stdout and "bju-international" in r.stdout


def test_list_with_specialty_filter(tmp_path):
    r = run("--list", "--specialty", "urology", cwd=tmp_path)
    assert r.returncode == 0
    assert "european-urology" in r.stdout
    assert "lancet |" not in r.stdout
    r_all = run("--list", cwd=tmp_path)
    assert r_all.stdout.count("\n") >= 240


def test_overrides_file_wins(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text(
        "templates:\n"
        "  - id: the-prostate\n    journal: The Prostate\n    publisher: Wiley\n"
        "    IF_approx: verify\n    word_limit: 4000\n    abstract: structured, ≤250 words\n"
        "    references: no limit\n    sections: IMRaD\n    system: ScholarOne\n    family: standard\n"
        "  - id: nature\n    journal: Nature (override)\n    word_limit: 9999\n",
        encoding="utf-8")
    r = run("--id", "the-prostate", "--json", cwd=tmp_path)  # default --overrides ./journal-overrides.yaml
    assert r.returncode == 0 and json.loads(r.stdout)["journal"] == "The Prostate"
    r = run("--id", "nature", "--json", "--overrides", str(tmp_path / "journal-overrides.yaml"), cwd=tmp_path)
    assert json.loads(r.stdout)["word_limit"] == 9999
    r = run("--id", "nature", "--json", cwd=ROOT)  # no overrides file here → library entry
    assert json.loads(r.stdout)["journal"] == "Nature"


def test_runs_under_c_locale(tmp_path):
    env = {"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "PYTHONIOENCODING": ""}
    r = run("--id", "lancet", cwd=tmp_path, env=env)
    assert r.returncode == 0, r.stderr
    assert "id: lancet" in r.stdout


# ─── v6.4.1: malformed / missing files → clear message, exit 2, no traceback ────

@pytest.mark.parametrize("content,expected", [
    ("templates:\n  - just-a-string\n", "not a mapping"),
    ("- a\n- b\n", "not a mapping"),                              # bare list of strings
    ("journal: The Prostate\nword_limit: 4000\n", "no top-level `templates:`"),
    ("templates:\n  id: x\n", "must be a list"),
    ("just a scalar\n", "must contain `templates:`"),
    ("templates: [\n  - id: x\n", "not valid YAML (line 2"),
    ("templates:\n  - journal: No Id Journal\n", "has no `id`"),
])
def test_malformed_overrides_exit_2_with_message(tmp_path, content, expected):
    (tmp_path / "journal-overrides.yaml").write_text(content, encoding="utf-8")
    for args in (("--id", "nature"), ("--search", "urol"), ("--list",)):
        r = run(*args, cwd=tmp_path)
        assert r.returncode == 2, (args, r.stdout, r.stderr)
        assert "Traceback" not in r.stderr
        assert r.stderr.startswith("Error: overrides file:") and expected in r.stderr, r.stderr
        assert "journal-overrides.yaml" in r.stderr


def test_empty_overrides_file_is_fine(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text("", encoding="utf-8")
    r = run("--id", "nature", "--json", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["id"] == "nature"


def test_wrong_yaml_path_says_file_not_found(tmp_path):
    r = run("--id", "nature", "--yaml", str(tmp_path / "missing.yaml"), cwd=tmp_path)
    assert r.returncode == 2
    assert "file not found" in r.stderr and "missing.yaml" in r.stderr
    assert "No template with id" not in r.stderr
    r = run("--list", "--yaml", str(tmp_path), cwd=tmp_path)    # a directory, not a file
    assert r.returncode == 2 and "cannot read" in r.stderr and "Traceback" not in r.stderr


def test_explicit_missing_overrides_warns_but_uses_library(tmp_path):
    r = run("--id", "nature", "--json", "--overrides", str(tmp_path / "nope.yaml"), cwd=tmp_path)
    assert r.returncode == 0
    assert "overrides file not found" in r.stderr
    assert json.loads(r.stdout)["journal"] == "Nature"


def test_id_lookup_is_case_insensitive(tmp_path):
    r = run("--id", "European-Urology", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "id: european-urology" in r.stdout


def test_overrides_with_dates_still_print_json(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text(
        "templates:\n  - id: the-prostate\n    journal: The Prostate\n    checked: 2026-09-01\n", encoding="utf-8")
    r = run("--id", "the-prostate", "--json", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["checked"] == "2026-09-01"
