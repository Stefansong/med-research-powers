"""Schema of skills/manuscript-writing/references/journal-templates.yaml — every entry.

The `limits` block (decision D1) is what Gate 6 / export_docx.py check numbers against, so a
wrong type or an impossible value there gives a wrong ✅ / ⚠️ for real manuscripts.

Run from the repo root:  python3 -m pytest tests/test_journal_templates.py -q
"""
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
YAML = ROOT / "skills" / "manuscript-writing" / "references" / "journal-templates.yaml"
TEXT = YAML.read_text(encoding="utf-8")
DATA = yaml.safe_load(TEXT)
ENTRIES = DATA["templates"]
BY_ID = {e["id"]: e for e in ENTRIES}
HEADER = TEXT.split("\ndata_as_of:", 1)[0]

REQUIRED = {"id", "journal", "publisher", "IF_approx", "word_limit", "abstract", "references", "limits",
            "sections", "system", "family"}
OPTIONAL = {"figures", "tables", "special", "figure_format", "cover_letter", "orcid", "IF_year", "IF_source",
            "apc_year", "citation_style", "limits_by_type", "submission_url", "guidelines_checked",
            "guidelines_source"}
LIMIT_KEYS = {"body_words", "body_excludes", "abstract_words", "references", "figures", "tables",
              "display_items", "pages", "soft"}
EXCLUDES = {"abstract", "methods", "references", "figure_legends", "tables", "key_points"}
ARTICLE_TYPES = {"review", "systematic_review", "research_letter", "brief_report", "case_report"}
SYSTEMS = {"Editorial Manager", "ScholarOne", "eJournalPress", "Snapp", "IEEE Author Portal", "MDPI SuSy",
           "Frontiers", "JMIR", "eLife", "journal portal"}
STYLES = {"Vancouver", "AMA", "NEJM", "Lancet", "Nature", "Cell", "IEEE", "APA", "Harvard", "MDPI",
          "house style", "any"}
FAMILIES = {"lancet", "jama", "nature", "ieee", "standard"}
IDS = [e["id"] for e in ENTRIES]


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def check_limits(lim, where):
    """Return a list of schema problems of one `limits` mapping."""
    bad = []
    if not isinstance(lim, dict):
        return [f"{where}: not a mapping"]
    for k in set(lim) - LIMIT_KEYS:
        bad.append(f"{where}: unknown key {k}")
    v = {k: x for k, x in lim.items() if x is not None}
    for k in ("body_words", "abstract_words", "references", "figures", "tables", "display_items", "pages"):
        if k in v and not _int(v[k]):
            bad.append(f"{where}: {k} must be an int, got {v[k]!r}")
    if bad:
        return bad
    if "body_words" in v and v["body_words"] < 500:
        bad.append(f"{where}: body_words {v['body_words']} < 500 (a page or display-item count?)")
    if "pages" in v and not 1 <= v["pages"] <= 60:
        bad.append(f"{where}: pages {v['pages']} is not a small page count")
    if "abstract_words" in v and not 50 <= v["abstract_words"] <= 600:
        bad.append(f"{where}: abstract_words {v['abstract_words']} out of range")
    for k in ("references",):
        if k in v and not 5 <= v[k] <= 300:
            bad.append(f"{where}: {k} {v[k]} out of range")
    for k in ("figures", "tables", "display_items"):
        if k in v and not 1 <= v[k] <= 30:
            bad.append(f"{where}: {k} {v[k]} out of range")
    if "body_words" in v and "pages" in v:
        bad.append(f"{where}: body_words together with pages")
    if "display_items" in v and ({"figures", "tables"} & set(v)):
        bad.append(f"{where}: display_items together with figures/tables")
    if "body_excludes" in v:
        ex = v["body_excludes"]
        if not isinstance(ex, list) or not set(ex) <= EXCLUDES or len(ex) != len(set(ex)):
            bad.append(f"{where}: body_excludes {ex!r} not a list from {sorted(EXCLUDES)}")
        if "body_words" not in v:
            bad.append(f"{where}: body_excludes without body_words")
    elif "body_words" in v:
        bad.append(f"{where}: body_words without body_excludes")
    if "soft" in lim and lim["soft"] is not True:
        bad.append(f"{where}: soft must be true or absent, got {lim['soft']!r}")
    return bad


def entry_text(e):
    parts = [e.get(k) for k in ("word_limit", "abstract", "references", "figures", "tables")]
    parts += list(e.get("special") or [])
    return " ".join(str(p) for p in parts if p is not None).replace(",", "")


# ─── whole-file structure ──────────────────────────────────────────────────────

def test_ids_unique_case_insensitive():
    low = [i.lower() for i in IDS]
    assert len(low) == len(set(low))
    assert all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", i) for i in IDS)


@pytest.mark.parametrize("jid", IDS)
def test_entry_schema(jid):
    e = BY_ID[jid]
    assert REQUIRED <= set(e), sorted(REQUIRED - set(e))
    assert set(e) <= REQUIRED | OPTIONAL, sorted(set(e) - REQUIRED - OPTIONAL)
    assert e["family"] in FAMILIES
    assert e["system"] in SYSTEMS, e["system"]
    if "submission_url" in e:
        assert isinstance(e["submission_url"], str) and " " not in e["submission_url"]
        assert not e["submission_url"].startswith(("http://", "https://"))
    if "citation_style" in e:
        assert e["citation_style"] in STYLES, e["citation_style"]
    assert check_limits(e["limits"], "limits") == []
    lbt = e.get("limits_by_type")
    if lbt is not None:
        assert isinstance(lbt, dict) and lbt and set(lbt) <= ARTICLE_TYPES, lbt
        for t, lim in lbt.items():
            assert lim and check_limits(lim, f"limits_by_type.{t}") == []


@pytest.mark.parametrize("jid", IDS)
def test_guidelines_checked_format(jid):
    e = BY_ID[jid]
    gc, src = e.get("guidelines_checked"), e.get("guidelines_source")
    if gc is not None:
        assert isinstance(gc, str) and re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", gc), gc
        assert isinstance(src, str) and re.match(r"https?://\S+$", src), src
    else:
        assert src is None, "guidelines_source without guidelines_checked"
    # provenance lives in the fields, not in `special` (JD-5)
    for s in e.get("special") or []:
        assert not re.match(r"(Guidelines checked|Source): https?://\S+ \(accessed", str(s)), s


@pytest.mark.parametrize("jid", IDS)
def test_limits_numbers_come_from_the_entry_text(jid):
    """Every number in `limits` / `limits_by_type` appears in the entry's own free text."""
    e = BY_ID[jid]
    text = entry_text(e)
    blocks = [e["limits"]] + list((e.get("limits_by_type") or {}).values())
    for lim in blocks:
        for k, v in lim.items():
            if _int(v):
                assert re.search(rf"(?<!\d){v}(?!\d)", text), f"{k}={v} not in the text of {jid}"


@pytest.mark.parametrize("jid", IDS)
def test_limits_never_guess(jid):
    e = BY_ID[jid]
    lim = {k: v for k, v in e["limits"].items() if v is not None}
    wl = str(e["word_limit"]).lower()
    if re.match(r"no (strict|fixed|maximum)", wl):
        assert "body_words" not in lim
    if "typically" in wl:
        assert "body_words" not in lim or lim.get("soft") is True
    if re.match(r"(≤\s*)?[\d–-]+\s+(printed\s+)?pages?\b", wl):                # a page limit, not words
        assert "body_words" not in lim and _int(lim.get("pages")), lim
    figs, tabs = str(e.get("figures") or ""), str(e.get("tables") or "")
    if "combined" in figs or tabs.startswith("included in") or "combined" in tabs:
        assert not {"figures", "tables"} & set(lim)
    if re.search(r"more than \d+ expected", str(e["references"])):
        assert "references" not in lim                                   # a minimum, not a cap


# what a 待核实 item names → the `limits` keys that must then be null
PENDING_KEYS = ((re.compile(r"(?<!abstract )\bword\b|\btext\b"), ("body_words",)),
                (re.compile(r"\babstract\b(?! (?:headings|format)\b)"), ("abstract_words",)),
                (re.compile(r"\breference"), ("references",)),
                (re.compile(r"\bfigure"), ("figures", "display_items")),
                (re.compile(r"\btable"), ("tables", "display_items")))


def pending_keys(e):
    """`limits` keys named by the entry's 待核实 items (values the last check could not confirm)."""
    keys = set()
    for s in e.get("special") or []:
        s = str(s)
        if s.startswith("待核实"):
            keys |= {k for pat, ks in PENDING_KEYS if pat.search(s) for k in ks}
    return keys


@pytest.mark.parametrize("jid", [e["id"] for e in ENTRIES if e.get("guidelines_checked")])
def test_pending_values_of_checked_entries_are_not_limits(jid):
    """A checked entry would give a plain ✅ for its limits, so a value a 待核实 item calls not
    stated / not confirmed / not re-checked must stay null (the free text keeps it)."""
    e = BY_ID[jid]
    lim = {k for k, v in e["limits"].items() if v is not None}
    assert not pending_keys(e) & lim, (sorted(pending_keys(e) & lim), e.get("special"))


# guidance wording in a free-text field: the number is not a hard limit
GUIDANCE = re.compile(r"recommended|\(guideline\)|as a guideline|not strictly|typically|ideally|approximately|"
                      r"\babout\b|~|flexible|usually", re.I)
FIELD_KEYS = {"word_limit": ("body_words",), "abstract": ("abstract_words",), "references": ("references",),
              "figures": ("figures", "display_items"), "tables": ("tables",)}


@pytest.mark.parametrize("jid", IDS)
def test_guidance_values_are_not_hard_limits(jid):
    """`soft` covers a whole block, so a guidance-only value next to hard limits stays null."""
    e = BY_ID[jid]
    lim = {k for k, v in e["limits"].items() if v is not None}
    if e["limits"].get("soft") is True:
        return
    for field, keys in FIELD_KEYS.items():
        if GUIDANCE.search(str(e.get(field) or "")):
            assert not set(keys) & lim, (field, e.get(field), e["limits"])


@pytest.mark.parametrize("jid", [e["id"] for e in ENTRIES if e.get("limits_by_type")])
def test_by_type_word_counts_follow_the_journals_own_rule(jid):
    """The texts do not say what a review / brief-report count includes, so it is counted like the
    journal's original articles — never more leniently."""
    e = BY_ID[jid]
    base = e["limits"].get("body_excludes")
    for t, lim in e["limits_by_type"].items():
        if lim.get("body_words") is not None and base is not None:
            assert set(lim["body_excludes"]) == set(base), (t, lim["body_excludes"], base)


def test_mini_review_guide_does_not_borrow_full_review_limits():
    mini = (YAML.parent / "article-types" / "mini.md").read_text(encoding="utf-8")
    section = mini.split("## 期刊上限", 1)[1].split("\n## ", 1)[0]
    assert "full review" in section and "本类型用 `review`；" not in section
    assert "不要**拿原始研究或 full review 的数字代替" in section


def test_header_documents_the_vocabularies():
    for word in sorted(LIMIT_KEYS | EXCLUDES | ARTICLE_TYPES | SYSTEMS | STYLES):
        assert word in HEADER, f"{word!r} is used in the data but not documented in the file header"
    assert "limits_by_type" in HEADER and "UNVERIFIED" in HEADER


# ─── real entries that were misread before (ED-1 / JD-2) ──────────────────────

def test_known_entries():
    nat = BY_ID["nature"]["limits"]
    assert nat["body_words"] == 4300 and nat["soft"] is True and "methods" in nat["body_excludes"]
    assert "abstract" not in nat["body_excludes"]                        # summary paragraph is counted
    for jid in ("nature-medicine", "cancer-cell", "cell-research"):
        assert "methods" in BY_ID[jid]["limits"]["body_excludes"], jid
    assert BY_ID["nature-medicine"]["limits"]["display_items"] == 6
    assert BY_ID["ieee-tmi"]["limits"] == {"pages": 10, "abstract_words": 250}
    assert BY_ID["ieee-jbhi"]["limits"]["pages"] == 14 and "body_words" not in BY_ID["ieee-jbhi"]["limits"]
    assert "references" not in BY_ID["hepatology"]["limits"]["body_excludes"]   # 6000 including references
    assert "abstract" not in BY_ID["prostate-cancer-prostatic-diseases"]["limits"]["body_excludes"]
    assert BY_ID["nejm"]["limits"] == {"body_words": 2700, "body_excludes": ["abstract", "references",
                                       "figure_legends", "tables", "key_points"], "abstract_words": 250,
                                       "references": 40, "display_items": 5}
    assert BY_ID["lancet"]["limits_by_type"]["systematic_review"]["body_words"] == 3500
    assert BY_ID["european-radiology"]["limits_by_type"]["systematic_review"]["figures"] == 12
    # "3000 (excluding abstract and references; each table or figure counts as 250 words)": the 3000 is the
    # limit; export_docx.py adds the 250 per table / figure in a row of its own (so tables are not counted twice)
    wju = BY_ID["world-journal-urology"]
    assert wju["word_limit"].startswith("3000 (excluding abstract and references; each table or figure counts as 250")
    assert wju["limits"]["body_words"] == 3000
    assert {"abstract", "references", "tables"} <= set(wju["limits"]["body_excludes"])
    assert "each figure as 250 words" not in HEADER and "each table / figure as N words" in HEADER
    # 待核实 values (JD-4) and guidance-only reference caps are not enforced as limits
    assert BY_ID["clinical-cancer-research"]["limits"] == {"body_words": 5000, "body_excludes": [
        "abstract", "references", "figure_legends", "tables", "key_points"]}
    for jid in ("nature-medicine", "npj-digital-medicine", "blood", "blood-advances"):
        assert "references" not in BY_ID[jid]["limits"], jid
    ejr = BY_ID["european-journal-radiology"]
    assert ejr["limits_by_type"]["review"] == {"body_words": 6000, "body_excludes": ["tables", "key_points"]}
    # the strictest-reading assumption behind limits_by_type is relayed by get_journal_template.py --id
    assert any(str(s).startswith("待核实") and "limits_by_type" in str(s) and "strictest reading" in str(s)
               for s in ejr["special"])
    assert not any("confirm on the Guide for Authors" in str(s) and not str(s).startswith("待核实")
                   for s in ejr["special"])


def test_verified_counts():
    checked = [e for e in ENTRIES if e.get("guidelines_checked")]
    assert len(ENTRIES) == 240
    assert len(checked) == 94                                             # 80 + 14 moved out of `special`
