"""Script outputs quoted in the user docs (README, README_CN, docs/USER-MANUAL.md) must match the scripts."""
import os
import re
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")
pytest.importorskip("statsmodels")
pytest.importorskip("pandas")   # patient_level_split exits without pandas
ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.join(ROOT, "skills", "statistical-analysis", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "skills", "data-collection-tools", "scripts"))
from assumption_tests import full_check  # noqa: E402
from patient_level_split import patient_key  # noqa: E402
from power_analysis import diagnostic, survival, two_groups  # noqa: E402

READMES = ["README.md", "README_CN.md"]


def doc(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def line_with(name, needle):
    lines = [ln for ln in doc(name).splitlines() if needle in ln]
    assert lines, f"{name} has no line containing {needle!r}"
    return lines


def test_user_manual_recommended_test_example_matches_full_check():
    # SS-9 / DOC-4: the manual still showed "Independent t-test" after the Welch default.
    m = re.search(r"print\(result\['recommended_test'\]\)\s*#\s*e\.g\.\s*\"([^\"]+)\"", doc("docs/USER-MANUAL.md"))
    assert m, "docs/USER-MANUAL.md no longer shows the recommended_test example"
    rng = np.random.default_rng(0)
    res = full_check(rng.normal(10, 2, 40), rng.normal(11, 2, 40), paired=False)
    assert m.group(1) == res["recommended_test"]


def test_user_manual_sample_size_comments_match_power_analysis():
    text = doc("docs/USER-MANUAL.md")
    m = re.search(r"two_groups\(effect_size=0\.5, power=0\.80, dropout=0\.15\)\s*#\s*→ n_per_group=(\d+)\D+(\d+)", text)
    assert m
    r = two_groups(effect_size=0.5, power=0.80, dropout=0.15)
    assert (int(m.group(1)), int(m.group(2))) == (r["n_per_group"], r["n1_adjusted"])
    m = re.search(r"diagnostic\(sensitivity=0\.90, prevalence=0\.3, precision=0\.05\)\s*#\s*→ n_diseased=(\d+), n_total=(\d+)", text)
    assert m
    r = diagnostic(sensitivity=0.90, prevalence=0.3, precision=0.05)
    assert (int(m.group(1)), int(m.group(2))) == (r["n_diseased"], r["n_total"])
    m = re.search(r"survival\(hazard_ratio=0\.7, event_rate=0\.4, dropout=0\.1\)\s*#[^\n]*?约 (\d+) 例事件", text)
    assert m
    assert int(m.group(1)) == survival(hazard_ratio=0.7, event_rate=0.4, dropout=0.1)["events_needed"]


@pytest.mark.parametrize("readme, pattern", [
    ("README.md", r"dropout=0\.15\)\s*#\s*n_per_group (\d+), (\d+) per group"),
    ("README_CN.md", r"dropout=0\.15\)\s*#\s*每组 (\d+) 例，按 15% 脱落放大后每组 (\d+) 例"),
])
def test_readme_two_groups_comment_matches_power_analysis(readme, pattern):
    m = re.search(pattern, doc(readme))
    assert m, f"{readme} no longer shows the two_groups result"
    r = two_groups(effect_size=0.5, power=0.80, dropout=0.15)
    assert (int(m.group(1)), int(m.group(2))) == (r["n_per_group"], r["n1_adjusted"])


@pytest.mark.parametrize("readme, merged, separate", [
    ("README.md", "leading / trailing spaces", "inner space"),
    ("README_CN.md", "首尾空格", "中间多一个空格"),
])
def test_readme_patient_id_matching_matches_patient_key(readme, merged, separate):
    # The script table said "spellings that differ only in spaces" were merged; patient_key
    # only strips surrounding whitespace, so "P 001" stays a different patient.
    assert patient_key(" p001 ") == patient_key("P001") == patient_key("Ｐ００１")
    assert patient_key("P 001") != patient_key("P001")
    row = line_with(readme, "`patient_level_split.py` | `data-collection-tools/scripts/`")[0]
    assert merged in row and separate in row, row


@pytest.mark.parametrize("name, legend, web", [
    ("README.md", "⏳ Unverified (", "web search"),
    ("README_CN.md", "⏳ Unverified（", "网络检索"),
    ("docs/architecture.md", "⏳ Unverified (", "web search"),
])
def test_unverified_legend_names_web_search_only_citations(name, legend, web):
    # pubmed-search Mode 3 keeps a citation found only by web search at ⏳ Unverified, so the
    # Gate 3 legend must not define ⏳ as "tool error" alone.
    for ln in line_with(name, legend):
        entry = ln.split(legend, 1)[1].split("ℹ️", 1)[0]
        assert web in entry, ln


def test_architecture_search_flowchart_ieee_is_user_run():
    # literature-synthesis: IEEE Xplore / ACM DL cannot be searched by Claude's tools; the user runs
    # the search string. The flowchart showed them as a WebSearch source.
    nodes = [ln for ln in doc("docs/architecture.md").splitlines() if re.match(r'\s*DB\d+\["', ln)]
    ieee = [ln for ln in nodes if "IEEE" in ln]
    assert ieee, "literature-search flowchart has no IEEE node"
    for ln in ieee:
        assert "WebSearch" not in ln and "user runs" in ln, ln
