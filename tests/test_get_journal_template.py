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
    assert by_id["nature-medicine"]["system"] == "eJournalPress"   # JD-7 vocabulary (Nature MTS runs on eJP)
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


@pytest.mark.parametrize("plant", ["fifo", "dev_zero", "symlink", "directory", "too_big"])
def test_overrides_file_that_is_not_a_small_regular_file_is_refused_without_hanging(tmp_path, plant):
    """Like mrp_state.py: a planted journal-overrides.yaml is never followed and never blocks."""
    ov = tmp_path / "journal-overrides.yaml"
    if plant == "fifo":
        if not hasattr(os, "mkfifo"):
            pytest.skip("no FIFOs here")
        os.mkfifo(ov)
    elif plant in ("dev_zero", "symlink"):
        target = Path("/dev/zero") if plant == "dev_zero" else tmp_path / "outside.yaml"
        if plant == "dev_zero" and not target.exists():
            pytest.skip("no /dev/zero here")
        if plant == "symlink":
            target.write_text("templates:\n  - id: outside-journal\n    journal: Outside Journal\n", encoding="utf-8")
        try:
            ov.symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("cannot create symlinks here")
    elif plant == "directory":
        ov.mkdir()
    else:
        ov.write_text("templates:\n  - id: big\n    journal: Big\n    note: " + "a" * 1_000_001 + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "--id", "outside-journal"], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(tmp_path), timeout=30)
    assert r.returncode == 2 and r.stdout == "", r.stderr
    assert r.stderr.startswith("Error: overrides file:") and len(r.stderr.strip().splitlines()) == 1, r.stderr
    assert "journal-overrides.yaml" in r.stderr and "Traceback" not in r.stderr


@pytest.mark.parametrize("content,expected", [
    ("templates:\n  - id: x\n    journal: X\n    data_as_of: 2026-02-30\n", "day is out of range"),
    ("templates: " + "[" * 3000 + "]" * 3000 + "\n", "more than 20 levels"),       # RecursionError in safe_load
    ("templates:\n  - id: x\n    journal: X\n    special: " + "[" * 400 + "]" * 400 + "\n",
     "more than 20 levels"),                                                       # loads, but safe_dump recursed
])
def test_overrides_that_crashed_the_parser_or_printer_give_one_error_line(tmp_path, content, expected):
    (tmp_path / "journal-overrides.yaml").write_text(content, encoding="utf-8")
    r = run("--id", "x", cwd=tmp_path)
    assert r.returncode == 2 and "Traceback" not in r.stderr, r.stderr
    assert r.stderr.startswith("Error: overrides file:") and expected in r.stderr, r.stderr


def test_overrides_file_with_utf8_bom_is_read(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_bytes(
        "\ufefftemplates:\n  - id: bom-journal\n    journal: BOM Journal\n".encode("utf-8"))
    r = run("--id", "bom-journal", "--json", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["journal"] == "BOM Journal"


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


# ─── unverified entries warn (D2 / JD-1) ─────────────────────────────────────

WARN = "limits not checked against the journal's current author guidelines"


def test_unverified_entry_warns_once_on_stderr(tmp_path):
    r = run("--id", "annals-oncology", "--json", cwd=tmp_path)      # no guidelines_checked
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["id"] == "annals-oncology"            # stdout stays valid JSON
    assert r.stderr.count(WARN) == 1 and len(r.stderr.strip().splitlines()) == 1
    assert "unverified" in r.stderr and "confirm on the journal site" in r.stderr


def test_verified_entry_does_not_warn(tmp_path):
    for jid in ("nature", "european-urology", "radiology"):         # radiology: moved from `special` (JD-5)
        r = run("--id", jid, cwd=tmp_path)
        assert r.returncode == 0 and WARN not in r.stderr, (jid, r.stderr)


def test_list_shows_checked_column_and_one_warning(tmp_path):
    r = run("--list", "--specialty", "urology", cwd=tmp_path)
    assert r.returncode == 0
    assert "| checked" in r.stdout and "| IF_year |" in r.stdout
    rows = {ln.split(" | ")[0]: ln for ln in r.stdout.splitlines() if not ln.startswith("#")}
    assert rows["european-urology"].endswith("| 2026-09")
    assert rows["neurourology-urodynamics"].endswith("| —")
    assert r.stderr.count(WARN) == 1
    r = run("--list", "--json", cwd=tmp_path)
    by_id = {e["id"]: e for e in json.loads(r.stdout)}
    assert by_id["nature"]["guidelines_checked"] == "2026-09" and by_id["gut"]["guidelines_checked"] is None


def test_override_without_guidelines_checked_warns(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text(
        "templates:\n  - id: the-prostate\n    journal: The Prostate\n"
        "  - id: my-checked\n    journal: Checked\n    guidelines_checked: 2026-10\n", encoding="utf-8")
    assert WARN in run("--id", "the-prostate", cwd=tmp_path).stderr
    assert WARN not in run("--id", "my-checked", cwd=tmp_path).stderr


# ─── 待核实 items are passed on, also for checked entries ─────────────────────

def test_pending_items_warn_for_a_checked_entry(tmp_path):
    r = run("--id", "clinical-cancer-research", "--json", cwd=tmp_path)   # guidelines_checked + a 待核实 item
    assert r.returncode == 0 and json.loads(r.stdout)["id"] == "clinical-cancer-research"
    lines = r.stderr.strip().splitlines()
    assert len(lines) == 1 and WARN not in r.stderr, r.stderr
    assert "has 1 待核实 item(s)" in lines[0] and "tell the user" in lines[0]
    assert "reference limit (≤60)" in lines[0]
    assert "待核实" not in run("--id", "nature", cwd=tmp_path).stderr


def test_pending_items_listed_without_marker_and_other_items(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text(
        "templates:\n  - id: my-j\n    journal: J\n    guidelines_checked: 2026-10\n    special:\n"
        "      - Key Points required\n      - '待核实: reference limit not stated'\n      - '待核实：figure limit'\n",
        encoding="utf-8")
    r = run("--id", "my-j", cwd=tmp_path)
    assert r.returncode == 0
    lines = r.stderr.strip().splitlines()
    assert len(lines) == 1 and "has 2 待核实 item(s)" in lines[0]
    assert lines[0].endswith(": reference limit not stated | figure limit")
    assert "Key Points" not in r.stderr


# ─── overrides: case-insensitive de-dup, own data_as_of (OS-13) ──────────────

def test_override_dedup_is_case_insensitive_and_keeps_own_data_as_of(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text(
        'data_as_of: "project override, checked 2026-10"\n'
        "templates:\n  - id: Nature\n    journal: Nature (my override)\n    word_limit: 3000\n", encoding="utf-8")
    r = run("--search", "nature", cwd=tmp_path)
    ids = [ln.split(" | ")[0] for ln in r.stdout.splitlines() if not ln.startswith("#")]
    assert [i for i in ids if i.lower() == "nature"] == ["Nature"]    # one row, the override
    assert "project overrides" in r.stdout and "checked 2026-10" in r.stdout
    r = run("--list", "--json", cwd=tmp_path)
    assert [e["journal"] for e in json.loads(r.stdout) if e["id"].lower() == "nature"] == ["Nature (my override)"]
    hit = json.loads(run("--id", "nature", "--json", cwd=tmp_path).stdout)
    assert hit["journal"] == "Nature (my override)"
    assert hit["data_as_of"] == "project override, checked 2026-10"   # not the library's JCR vintage
    assert hit["source"] == "journal-overrides.yaml"


def test_override_without_data_as_of_does_not_borrow_the_library_one(tmp_path):
    (tmp_path / "journal-overrides.yaml").write_text(
        "templates:\n  - id: the-prostate\n    journal: The Prostate\n", encoding="utf-8")
    hit = json.loads(run("--id", "the-prostate", "--json", cwd=tmp_path).stdout)
    assert hit["data_as_of"] is None and hit["source"] == "journal-overrides.yaml"
    lib = json.loads(run("--id", "nature", "--json", cwd=tmp_path).stdout)
    assert "JCR" in lib["data_as_of"] and "source" not in lib


# ─── CLI convention (CLI-1): one line on stderr, exit 2 ──────────────────────

@pytest.mark.parametrize("args", [(), ("--id",), ("--id", "x", "--search", "y"), ("--list", "--bogus"),
                                  ("--search", "urol", "--specialty", "urology")])
def test_bad_arguments_one_line_exit_2(tmp_path, args):
    r = run(*args, cwd=tmp_path)
    assert r.returncode == 2, (args, r.stderr)
    assert len(r.stderr.strip().splitlines()) == 1 and r.stderr.startswith("Error:"), r.stderr
    assert "Traceback" not in r.stderr and r.stdout == ""


def test_missing_pyyaml_exit_2(tmp_path):
    fake = tmp_path / "fake"
    fake.mkdir()
    (fake / "yaml.py").write_text("raise ImportError('no yaml here')\n", encoding="utf-8")
    r = run("--id", "nature", cwd=tmp_path, env={"PYTHONPATH": str(fake)})
    assert r.returncode == 2
    assert r.stderr.strip().splitlines() == ["Error: missing dependency PyYAML — install it with: pip install pyyaml"]


def test_main_accepts_argv(capsys, monkeypatch, tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("gjt", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.chdir(tmp_path)
    mod.main(["--id", "nature", "--json"])
    assert json.loads(capsys.readouterr().out)["id"] == "nature"
