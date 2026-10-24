#!/usr/bin/env python3
"""
MRP Manuscript Export: Markdown → .docx
========================================
Converts manuscript markdown files to journal-formatted .docx for submission.

Usage:
    python3 export_docx.py --manuscript-dir ./manuscript --journal nature --output manuscript/manuscript.docx
    python3 export_docx.py --manuscript-dir ./manuscript --journal european-urology \
        --report export-report.md --supplementary            # also writes manuscript/supplementary.docx
    python3 export_docx.py --manuscript-dir ./manuscript --journal generic   # journal-neutral, no limit checks
    python3 export_docx.py --manuscript-dir ./manuscript --journal lancet --article-type review --report-only

The journal id must exist in journal-templates.yaml (bundled with manuscript-writing,
located relative to this script) or in a project-level journal-overrides.yaml; `generic`
(or `none`) gives a journal-neutral export (standard layout, no limit checks).
The `family` field of the template (lancet / jama / nature / ieee / standard) decides
section order and special elements; it is inferred from id/name if the field is absent.
Numeric limit checks use the entry's structured `limits` block (`limits_by_type.<type>` for
--article-type other than original); an entry without that block falls back to reading the
free-text fields conservatively (anything ambiguous is reported as "check manually").
The .docx gets page numbers and line numbers (library `defaults`; an entry's own
page_numbers / line_numbers, --no-page-numbers or --no-line-numbers turn them off).

Exit codes: 0 ok · 2 error — invalid arguments, unknown journal id, missing / unreadable input
file, malformed overrides / library YAML, missing dependency, or an output path that would
overwrite an input (one "Error: ..." line on stderr, no traceback)

Requirements:
    pip install python-docx pyyaml
"""

import argparse
import os
import re
import sys
import unicodedata
import zipfile
from pathlib import Path


def _missing(pkg, pip_name):
    print(f"Error: 缺少依赖 {pkg}（Missing dependency）。请先运行: pip install {pip_name}", file=sys.stderr)
    sys.exit(2)


try:
    import yaml
except ImportError:  # pragma: no cover
    _missing("PyYAML", "pyyaml")
try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    from docx.oxml.ns import qn, nsdecls
    from docx.oxml import parse_xml, OxmlElement
except ImportError:  # pragma: no cover
    _missing("python-docx", "python-docx")


HERE = Path(__file__).resolve().parent
DEFAULT_YAML = HERE.parent.parent / "manuscript-writing" / "references" / "journal-templates.yaml"
DEFAULT_OVERRIDES = "journal-overrides.yaml"

# ─── Journal family format configurations ────────────────────────────────────
# Fonts / spacing / section order per family. Journal-specific limits come from the YAML.

_BASE = {"font": "Times New Roman", "font_size": 12, "heading1_size": 14, "heading2_size": 13,
         "heading3_size": 12, "line_spacing": 2.0, "margin_cm": 2.54}

JOURNAL_FAMILIES = {
    "nature": {**_BASE, "section_order": [
        "title-page", "abstract", "introduction", "results", "discussion", "methods",
        "references", "figure-legends"], "special": ["reporting_summary"]},
    "lancet": {**_BASE, "section_order": [
        "title-page", "abstract", "research-in-context", "introduction", "methods", "results",
        "discussion", "conclusion", "references", "figure-legends"], "special": ["research_in_context"]},
    "jama": {**_BASE, "font_size": 11, "heading1_size": 13, "heading2_size": 12, "heading3_size": 11,
             "section_order": [
        "title-page", "key-points", "abstract", "introduction", "methods", "results", "discussion",
        "conclusion", "references", "figure-legends"], "special": ["key_points"]},
    "ieee": {**_BASE, "font_size": 10, "heading1_size": 12, "heading2_size": 11, "heading3_size": 10,
             "line_spacing": 1.0, "margin_cm": 1.91, "section_order": [
        "title-page", "abstract", "introduction", "related-work", "methods", "results", "discussion",
        "conclusion", "references", "figure-legends"], "special": ["index_terms"]},
    "standard": {**_BASE, "section_order": [
        "title-page", "abstract", "introduction", "methods", "results", "discussion", "conclusion",
        "references", "figure-legends"], "special": []},
}

SECTION_FILES = {
    "title-page": "title-page.md", "key-points": "key-points.md", "abstract": "abstract.md",
    "research-in-context": "research-in-context.md", "introduction": "introduction.md",
    "related-work": "related-work.md", "methods": "methods.md", "results": "results.md",
    "discussion": "discussion.md", "conclusion": "conclusion.md", "references": "references.md",
    "figure-legends": "figure-legends.md", "supplementary": "supplementary.md",
}
SECTION_TITLES = {"key-points": "Key Points", "research-in-context": "Research in Context"}
# Missing optional sections are noted with ℹ️; everything else in the family order gets ⚠️.
OPTIONAL_SECTIONS = {"conclusion", "related-work", "figure-legends"}
BODY_SECTIONS = ("introduction", "related-work", "methods", "results", "discussion", "conclusion")
# Thematic body files of narrative / mini reviews (manuscript-writing article-types): exported
# in numeric order right after the Introduction, counted as body text.
REVIEW_SECTION_RE = re.compile(r"^section-(\d+)(?:-.*)?\.md$", re.IGNORECASE)
# Journal-neutral export (--journal generic): standard layout, every family element optional.
GENERIC_IDS = ("generic", "none")
GENERIC_ORDER = ["title-page", "key-points", "abstract", "research-in-context", "introduction", "related-work",
                 "methods", "results", "discussion", "conclusion", "references", "figure-legends"]
# Matched case-insensitively against the markdown source of every block (tables and code included).
PLACEHOLDER_MARKERS = ("[pending]", "[tbd]", "[todo]", "placeholder", "[insert",
                       "[待补", "[待填", "【待补", "【待填", "［待补", "［待填")
# Bare markers: upper-case TODO / TBD / FIXME, 待补 / 待填 / 待核实 with or without brackets,
# and [ref] / [cite] / [citation needed]. ("XXX" is not one: blinded manuscripts use it on purpose.)
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b|待补|待填|待核实")
PLACEHOLDER_CI_RE = re.compile(r"\[(?:refs?|cite|citation(?: needed)?)\??\]", re.IGNORECASE)
CODE_FONT = "Courier New"
LINK_COLOR = RGBColor(0x05, 0x63, 0xC1)

# ─── Journal limits (decision D1) ────────────────────────────────────────────
# `limits:` keys of a journal-templates.yaml entry (all optional; missing / null = no limit known).
LIMIT_INT_KEYS = ("body_words", "abstract_words", "references", "figures", "tables", "display_items", "pages")
# body_excludes vocabulary = parts NOT counted in body_words; every part not listed is counted.
BODY_PARTS = ("abstract", "methods", "references", "figure_legends", "tables", "key_points")
# What the body bucket leaves out when nothing says otherwise (usual word-count convention).
CONVENTIONAL_EXCLUDES = ("abstract", "references", "figure_legends", "tables", "key_points")
ARTICLE_TYPES = ("original", "review", "systematic_review", "research_letter", "brief_report", "case_report")
UNVERIFIED_WARNING = ("limits not checked against the journal's current author guidelines; "
                      "confirm on the journal site before relying on them")


def infer_family(journal_id: str, name: str = "") -> str:
    """Same rule as the `family` field in journal-templates.yaml (fallback when the field is absent)."""
    s = f"{journal_id} {name}".lower()
    if any(k in s for k in ("lancet", "eclinical", "ebiomedicine")):
        return "lancet"
    if "jama" in s:
        return "jama"
    if any(k in s for k in ("nature", "npj", "scientific-reports", "scientific reports",
                            "communications-medicine", "communications medicine")):
        return "nature"
    if "ieee" in s:
        return "ieee"
    return "standard"


class TemplateFileError(Exception):
    """A template / overrides file that cannot be read, is not valid YAML, or has the wrong shape."""


def _read_yaml(path, required=False):
    """Parsed content of a YAML file (None when it does not exist and is not required)."""
    if not path or not os.path.exists(path):
        if required:
            raise TemplateFileError(f"file not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8-sig") as f:      # a UTF-8 BOM is accepted
            text = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise TemplateFileError(f"cannot read {path}: {exc}") from None
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
        raise TemplateFileError(f"{path} is not valid YAML{where}: "
                                f"{getattr(exc, 'problem', None) or ' '.join(str(exc).split())}") from None


def _load_templates(path, required=False):
    """Return (data_as_of, entries, defaults) from a templates YAML.

    A missing file gives (None, [], {}) unless required=True; an empty file means no entries.
    Raises TemplateFileError when the file cannot be read, is not valid YAML, or is not
    `templates:` + a list of mappings that each have an `id` (a bare top-level list of such
    mappings is also accepted) — same rules as manuscript-writing/scripts/get_journal_template.py.
    `defaults` is the top-level `defaults:` mapping (page / line numbers …), {} when absent."""
    data = _read_yaml(path, required)
    if data is None:
        return None, [], {}
    defaults = {}
    if isinstance(data, list):
        entries, data_as_of = data, None
    elif isinstance(data, dict):
        if "templates" not in data:
            raise TemplateFileError(f"{path} has no top-level `templates:` key "
                                    "(expected `templates:` followed by `- id: ...` entries)")
        entries, data_as_of = data["templates"] or [], data.get("data_as_of")
        defaults = data.get("defaults") if isinstance(data.get("defaults"), dict) else {}
    else:
        raise TemplateFileError(f"{path} must contain `templates:` with a list of entries, "
                                f"not a {type(data).__name__}")
    if not isinstance(entries, list):
        raise TemplateFileError(f"`templates` in {path} must be a list of entries, not a {type(entries).__name__}")
    for i, e in enumerate(entries, 1):
        if not isinstance(e, dict):
            raise TemplateFileError(f"entry #{i} in {path} is a {type(e).__name__} ({e!r}), not a mapping; "
                                    "each entry looks like `- id: ...` / `  journal: ...`")
        if not isinstance(e.get("id"), (str, int)) or not str(e["id"]).strip():
            raise TemplateFileError(f"entry #{i} in {path} has no `id` (a plain text id such as `the-prostate`)")
    return data_as_of, entries, defaults


def _fail(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(2)


class InputError(Exception):
    """A manuscript file that cannot be read, or a manuscript folder without sections (exit 2)."""


# ─── Free-text limits (fallback for entries without a `limits` block) ────────
# Read conservatively: a value that cannot be read as one maximum gives None and a
# "check manually" note — never a guessed number.

_NUM_RE = re.compile(r"\d[\d,]*")
_RANGE_RE = re.compile(r"(\d[\d,]*)\s*(?:-|–|—|to)\s*~?\s*(\d[\d,]*)")
# "unlimited", "no limit", "no hard / fixed / formal / strict limit", "no fixed word limit", "no (fixed) maximum".
# Only when it comes before the first number: in "3000 words (no limit on references)" it is about something else.
_NO_LIMIT_RE = re.compile(r"unlimited|\bno(?:\s+[a-z-]+){0,2}\s+(?:limits?|maximum)\b|\bno\s+strict\b|"
                          r"\bnot\s+limited\b")
# What a "no limit" phrase names (_no_limit_scope): another article type, the original article, a part.
_SCOPE_TOKEN_RE = re.compile(
    r"\b(?:(?P<other_type>(?:systematic |narrative |invited |mini-?)?reviews?|meta-analys[ie]s|(?:research )?letters?"
    r"|correspondence|case (?:reports?|series)|editorials?|commentar(?:y|ies)|perspectives?|viewpoints?|opinions?"
    r"|(?:brief|short|rapid) (?:reports?|communications?|articles?|papers?)|technical notes?"
    r"|special (?:articles?|reports?)|consensus (?:statements?|papers?)|(?:study )?protocols?"
    r"|other (?:article )?(?:types?|articles?|papers?|submissions?))"
    r"|(?P<original>(?:original|research)(?: research| investigations?| contributions?| articles?| papers?| reports?)*"
    r"|full(?:-length)? (?:articles?|papers?)|articles?|papers?|submissions?|manuscripts?)"
    r"|(?P<words>words?|word count|(?:main |body )?text|body|length)"
    r"|(?P<abstract>abstracts?|summary)"
    r"|(?P<references>references?|reference list|citations?|bibliography)"
    r"|(?P<figures>figures?|figs?|illustrations?|images?|photographs?)"
    r"|(?P<tables>tables?)"
    r"|(?P<display>display items?)"
    r"|(?P<misc>legends?|captions?|supplement\w*|appendi\w+|online|methods|key points|keywords?|authors?|title"
    r"|pages?))\b")
# the parts named that mean "this limit", per part (_read_limit's `part`); "words" alone is handled apart
_PART_TOKENS = {"words": set(), "abstract": {"abstract"}, "references": {"references"},
                "figures": {"figures", "display"}, "tables": {"tables", "display"}}
_CLAUSE_END_RE = re.compile(r"[;()\[\]—]|,(?!\d)|\.\s")
_NUM_OR_SIGN_RE = re.compile(r"[≤<≥>~]|\d[\d,]*")
_SCOPE_PREP_RE = re.compile(r"\s*(?:(?:is|are)\s+)?(?:for|on|to|in|of|regarding|concerning)\s+(?:the\s+|all\s+|any\s+)?"
                            r"(?:(?:total\s+)?number\s+of\s+)?")
_SEE_GUIDELINES_RE = re.compile(r"\bsee (?:the )?(?:author|journal)(?:'s)? guidelines")
# a minimum, not a maximum: "more than 30 expected", "at least 20", "≥30", "minimum 3000"
_MIN_RE = re.compile(r"\bmore than\b|\bat least\b|\bminimum\b|\bmin\.|≥|>=|(?<![<≤])>\s*\d")
# a guidance value, not a hard limit (exceeding it is reported with ℹ️, not ⚠️)
_SOFT_RE = re.compile(r"recommend|guidance|guideline|ideally|usually|\babout\b|approximately|\bapprox\b|"
                      r"\baround\b|~\s*\d|flexible|not strictly enforced|suggested|preferably")
# a page count: page / pages / pp / 页 right after the number or up to two words later ("8–10 printed pages")
_PAGE_UNIT_RE = re.compile(r"\s*(?:[^\W\d_]+[ \t-]+){0,2}?(?:pages?\b|pp\b|页)")
# the other numbers of a text that are not limits of the same thing: $ amounts, "6000-word limit", dpi, %
_NOT_A_LIMIT_AFTER_RE = re.compile(r"\s*(?:-\s*word|dpi|%|/\s*page)")
_PER_ITEM_RE = re.compile(r"each\b[^;,)]*?\bcounts?\b[^;,)]*?(\d[\d,]*)\s*words")


def _no_limit_scope(s, m, part):
    """What the "no limit" phrase `m` in `s` is about: ('this' | 'other' | 'unclear', names, (start, end) of
    its clause, which stops at a number). 'this' when it names nothing ('no fixed limit (…)', 'unlimited,
    Vancouver'), the original article or this part ('no reference limit' for references); 'other' when it
    names another article type ('no limit for reviews') or another part ('no limit on references' for the
    word limit, 'no limit on supplementary figures'); 'unclear' when it is about something not recognised
    ('no limit in the guide') or names a part when `part` is not known."""
    start = max([d.end() for d in _CLAUSE_END_RE.finditer(s, 0, m.start())]
                + [n.end() for n in _NUM_OR_SIGN_RE.finditer(s, 0, m.start())], default=0)
    end = min([d.start() for d in _CLAUSE_END_RE.finditer(s, m.end())][:1]
              + [n.start() for n in _NUM_OR_SIGN_RE.finditer(s, m.end())][:1], default=len(s))
    names = {t.lastgroup for t in _SCOPE_TOKEN_RE.finditer(m.group(0))}             # "no reference limit"
    before = list(_SCOPE_TOKEN_RE.finditer(s, start, m.start()))                     # "references not limited"
    if before and re.fullmatch(r"[\s:=–-]*(?:(?:is|are)\s+)?", s[before[-1].end():m.start()]):
        names.add(before[-1].lastgroup)
    prep = _SCOPE_PREP_RE.match(s, m.end(), end)                                    # "no limit for reviews"
    if prep:
        after = [t.lastgroup for t in _SCOPE_TOKEN_RE.finditer(s, prep.end(), end)]
        if not after and not re.fullmatch(r"\s*(?:number|count|size|quantity)?\s*", s[prep.end():end]):
            return "unclear", names, (start, end)
        names.update(after)
    else:                                                                           # "unlimited references"
        t = _SCOPE_TOKEN_RE.match(s, m.end() + len(s[m.end():end]) - len(s[m.end():end].lstrip()), end)
        if t:
            names.add(t.lastgroup)
    if "other_type" in names and "original" not in names:
        return "other", names, (start, end)
    parts = names - {"other_type", "original", "words"}          # "words" alone: the word limit or the abstract
    if (parts or "words" in names) and part is None:
        return "unclear", names, (start, end)
    if parts:
        this = parts & _PART_TOKENS[part] and "misc" not in parts
    else:
        this = "words" not in names or part in ("words", "abstract")
    return ("this" if this else "other"), names, (start, end)


def _read_limit(value, kind="words", part=None):
    """Read one free-text limit. Returns {value, soft, pages, no_limit, note}:
    '≤40, Vancouver' → 40; '150-250 words' → 250 (the upper bound); '≤100 (recommended)' → 100, soft;
    'unlimited' / 'no fixed maximum' / 'no strict limit (typically …)' → no_limit; '8 pages' /
    '≤10 pages' / '8–10 printed pages' → pages (a page count is not a word count); 'more than 30' →
    None + note (a minimum); 'typically …', a word limit mixed with display-item counts, a word range
    with qualifiers ('5000–6000 (Basic / Clinical …)') or a limit on figure parts → None + note.
    'no limit' / 'see author guidelines' after the number ('3000 words (no limit on references)',
    '≤40 (no limit for reviews)') do not cancel it; 'see author guidelines' alone → None + note.
    `part` (words / abstract / references / figures / tables; from `kind` when not given) is what the
    limit is about: a "no limit" before the number counts only when it is about this part and the
    original article — 'no limit for reviews; ≤40' → 40, 'no limit on references; 3000 words' → 3000 for
    the word limit; when it is unclear what it is about → None + note, never no_limit; a number followed by
    'no limit for original articles' → None + note.
    A second, larger maximum in the same text (another article type) is named in the note."""
    out = {"value": None, "soft": False, "pages": None, "no_limit": False, "note": None}
    s = str(value if value is not None else "").strip().lower()
    if not s:
        return out
    part = part or {"words": "words", "abstract": "abstract"}.get(kind)
    first = _NUM_RE.search(s)
    other = []
    for m in _NO_LIMIT_RE.finditer(s, 0, first.start() if first else len(s)):
        scope, _, (start, end) = _no_limit_scope(s, m, part)
        if scope == "this":
            out["no_limit"] = True
            return out
        if scope == "unclear":
            out["note"] = (f"the template says '{s[start:end].strip()}' — unclear which limit that is about, "
                           "so it was not read as 'no limit'")
            return out
        other.append((start, end))
    for start, end in other:          # about another article type / part: read the rest of the text
        s = s[:start] + " " * (end - start) + s[end:]
    if other:
        first = _NUM_RE.search(s)
        if not first:
            out["note"] = (f"the template says '{str(value).strip()}' — that 'no limit' is about another article "
                           "type or part, not this limit")
            return out
    before_number = s[:first.start()] if first else s
    if _SEE_GUIDELINES_RE.search(before_number):
        out["note"] = "the template refers to the journal's author guidelines instead of giving a number"
        return out
    if "typically" in s or (kind == "words" and "display item" in s):
        out["note"] = "the template gives typical values, not one limit"
        return out
    if _MIN_RE.search(s):
        out["note"] = "the template states a minimum, not a maximum"
        return out
    if not first:
        return out
    rng = _RANGE_RE.match(s, first.start())
    end = rng.end() if rng else first.end()
    num = int((rng.group(2) if rng else first.group(0)).replace(",", ""))
    if _PAGE_UNIT_RE.match(s[end:]):
        if kind == "words":
            out["pages"] = num
        else:
            out["note"] = "the template gives a page count"
        return out
    if rng and kind == "words" and s[end:].strip(" .") not in ("", "words"):
        out["note"] = f"the template gives a range ({rng.group(0)}) with qualifiers, not one limit"
        return out
    if re.search(r"pieces|panels|(?<!not counting )figure parts", s):
        out["note"] = "the limit counts figure parts / pieces, which this script does not count"
        return out
    for m in _NO_LIMIT_RE.finditer(s, end):     # "≤40 for reviews; no limit for original articles"
        scope, names, (start, stop) = _no_limit_scope(s, m, part)
        if scope == "this" and "original" in names:
            out["note"] = (f"the template gives {num} but also says '{s[start:stop].strip()}' — check which "
                           "applies")
            return out
    out["value"], out["soft"] = num, bool(_SOFT_RE.search(_SEE_GUIDELINES_RE.sub(" ", s)))
    notes = []
    others = []
    for m in _NUM_RE.finditer(s, end):
        n = int(m.group(0).replace(",", ""))
        if n > num and not s[:m.start()].endswith("$") and not _NOT_A_LIMIT_AFTER_RE.match(s, m.end()):
            others.append(m.group(0))
    if others:
        notes.append(f"the template also gives {', '.join(others)} (another article type or case?) — "
                     f"{num} was used; check which applies")
    out["note"] = "; ".join(notes) or None
    return out


def _parse_limit(value):
    """The maximum a free-text limit states, or None (see _read_limit)."""
    return _read_limit(value)["value"]


_PART_PATTERNS = (
    ("abstract", re.compile(r"abstracts?\b|summary paragraph")),
    ("methods", re.compile(r"methods\b")),
    ("references", re.compile(r"references?\b|reference list|bibliography")),
    ("figure_legends", re.compile(r"legends?\b|captions?\b")),
    ("tables", re.compile(r"tables?\b")),
    ("key_points", re.compile(r"key points")),
)
_EXCL_VERB_RE = re.compile(r"\b(?:excluding|excludes?|exclusive of|not including|not counting|without)\b")
_INCL_VERB_RE = re.compile(r"\b(?:including|includes?|inclusive of|incl\.)")


def _body_parts_from_text(word_limit_text, references_text=""):
    """(excluded, included) parts named in the free text: 'excluding abstract, Methods, references
    and figure legends', 'including main figure legends; excluding STAR Methods …', 'summary
    paragraph + body text', and a references field saying they are 'counted in the N-word limit'."""
    excluded, included = set(), set()
    s = str(word_limit_text or "").lower()
    for clause in re.split(r"[;()]", s):
        verb = _EXCL_VERB_RE.search(clause)
        target = excluded
        if not verb:
            verb, target = _INCL_VERB_RE.search(clause), included
        if not verb:
            continue
        for item in re.split(r",|\band\b|/|\+|\bor\b", clause[verb.end():]):
            if "supplement" in item:             # "supplemental legends" are not the main text
                continue
            target.update(part for part, rx in _PART_PATTERNS if rx.search(item))
    if re.search(r"(?:abstract|summary paragraph)\s*\+", s):
        included.add("abstract")
    r = str(references_text or "").lower()
    if re.search(r"count(?:ed|s)? (?:in|within|toward|towards|against) (?:the )?(?:\d[\d,]*-?\s*)?word", r):
        included.add("references")
    return excluded, included - excluded


def _combined_display_items(entry):
    f, t = str(entry.get("figures") or "").lower(), str(entry.get("tables") or "").lower()
    return bool(re.search(r"combined|display items?", f) or re.search(r"combined|included in", t))


def _free_text_limits(entry):
    """D1 limits read from the free-text fields (entries without a `limits` block)."""
    w = _read_limit(entry.get("word_limit"), "words")
    a = _read_limit(re.sub(r"\d+\s*headings?", "", str(entry.get("abstract") or "")), "abstract")
    r = _read_limit(entry.get("references"), "count", "references")
    f = _read_limit(entry.get("figures"), "count", "figures")
    t = _read_limit(entry.get("tables"), "count", "tables")
    limits = {k: None for k in LIMIT_INT_KEYS}
    limits.update(body_words=w["value"], pages=w["pages"], abstract_words=a["value"], references=r["value"])
    read = {"body_words": (w, "word_limit"), "abstract_words": (a, "abstract"), "references": (r, "references")}
    if _combined_display_items(entry):
        di = f if f["value"] is not None or f["note"] else t
        limits["display_items"] = di["value"]
        read["display_items"] = (di, "figures" if di is f else "tables")
    else:
        limits["figures"], limits["tables"] = f["value"], t["value"]
        read.update(figures=(f, "figures"), tables=(t, "tables"))
    soft = {k for k, (rd, _) in read.items() if rd["soft"]}
    notes = [f"`{field}`: {rd['note']} — check manually (template: {entry.get(field)!r})"
             for k, (rd, field) in read.items() if rd["note"]]
    return limits, soft, notes


def _no_limit_keys(entry):
    """Limit keys whose free text says outright that there is no limit ('unlimited', 'no fixed limit')."""
    keys = set()
    for key, field, part in (("body_words", "word_limit", "words"), ("abstract_words", "abstract", "abstract"),
                             ("references", "references", "references"), ("figures", "figures", "figures"),
                             ("tables", "tables", "tables"), ("display_items", "figures", "figures")):
        if _read_limit(entry.get(field), "count", part)["no_limit"]:
            keys.add(key)
    return keys


def _limits_block(block, name):
    """Validate one structured limits mapping; returns (limits, soft, unknown_keys)."""
    if not isinstance(block, dict):
        raise TemplateFileError(f"`{name}` must be a mapping (body_words, abstract_words, references, …), "
                                f"not a {type(block).__name__}")
    limits, soft, unknown = {k: None for k in LIMIT_INT_KEYS}, False, []
    limits["body_excludes"] = None
    for key, v in block.items():
        if key in LIMIT_INT_KEYS:
            if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
                raise TemplateFileError(f"`{name}.{key}` must be a whole number or null, not {v!r}")
            limits[key] = v
        elif key == "body_excludes":
            if v is not None and (not isinstance(v, list) or any(p not in BODY_PARTS for p in v)):
                raise TemplateFileError(f"`{name}.body_excludes` must be a list of {', '.join(BODY_PARTS)}, "
                                        f"not {v!r}")
            limits[key] = None if v is None else [p for p in BODY_PARTS if p in v]
        elif key == "soft":
            if v is not None and not isinstance(v, bool):
                raise TemplateFileError(f"`{name}.soft` must be true or false, not {v!r}")
            soft = bool(v)
        else:
            unknown.append(str(key))
    return limits, soft, unknown


def _journal_limits(entry, article_type, journal_name):
    """The numeric limits export_docx checks, per decision D1: the entry's `limits` block (or
    `limits_by_type.<article_type>`), else the free text read conservatively (original only)."""
    res = {"limits": None, "source": None, "soft": set(), "notes": [], "skip_reason": None,
           "body_rule": "convention", "combined": False}
    by_type = entry.get("limits_by_type")
    if by_type is not None and not isinstance(by_type, dict):
        raise TemplateFileError("`limits_by_type` must be a mapping of article types "
                                f"({', '.join(ARTICLE_TYPES[1:])})")
    block, name = None, None
    if article_type == "original":
        if entry.get("limits") is not None:
            block, name = entry["limits"], "limits"
    elif by_type and by_type.get(article_type) is not None:
        block, name = by_type[article_type], f"limits_by_type.{article_type}"
    else:
        res["skip_reason"] = (f"The library has no {article_type.replace('_', ' ')} limits for {journal_name} — "
                              "check the journal's author guidelines; numeric limits were not checked.")
        return res
    if block is not None:
        limits, soft, unknown = _limits_block(block, name)
        res.update(limits=limits, source=f"`{name}`", soft=set(LIMIT_INT_KEYS) if soft else set())
        if unknown:
            res["notes"].append(f"unknown key(s) in `{name}` ignored: {', '.join(unknown)}")
    else:
        limits, soft, notes = _free_text_limits(entry)
        limits["body_excludes"] = None
        res.update(limits=limits, source="free-text fields (the entry has no `limits` block)", soft=soft,
                   notes=notes, combined=_combined_display_items(entry))
    if res["limits"]["body_excludes"] is not None:
        res["body_rule"] = "library"
    else:
        excluded, included = _body_parts_from_text(entry.get("word_limit"), entry.get("references"))
        res["limits"]["body_excludes"] = [p for p in BODY_PARTS
                                          if p in excluded or (p in CONVENTIONAL_EXCLUDES and p not in included)]
        res["body_rule"] = "template text" if excluded or included else "convention"
    if res["limits"]["pages"] is not None and res["limits"]["body_words"] is None:
        res["notes"].append(f"the journal limits pages ({res['limits']['pages']}), not words — this script "
                            "cannot count pages; check the page count in the journal's own template")
    return res


def _switch(value):
    """False for page_numbers / line_numbers values that turn the feature off."""
    return not (value is False or value is None or str(value).strip().lower() in ("none", "no", "off", "false", ""))


def _numbering(entry, defaults, no_page=False, no_line=False):
    """(page_numbers, line_numbers, source): page_numbers = (header|footer, center|right) or None;
    line_numbers = Word restart rule (continuous / newPage / newSection) or None.
    The entry's own page_numbers / line_numbers win over the library `defaults`."""
    def pick(key):
        if key in entry:
            return entry[key], "journal entry"
        if key in defaults:
            return defaults[key], "library defaults"
        return True, "export default"
    page_v, page_src = pick("page_numbers")
    line_v, line_src = pick("line_numbers")
    page = line = None
    if _switch(page_v) and not no_page:
        s = str(page_v).lower()
        right = "right" in s and "center" not in s and "centre" not in s
        page = ("header" if "top" in s else "footer", "right" if right else "center")
    if _switch(line_v) and not no_line:
        s = str(line_v).lower()
        line = ("newPage" if re.search(r"restart|each page|per page", s)
                else "newSection" if "section" in s else "continuous")
    src = (f"page numbers: {page_src if not no_page else '--no-page-numbers'}; "
           f"line numbers: {line_src if not no_line else '--no-line-numbers'}")
    return page, line, src


def _base_config(family):
    return {k: (list(v) if isinstance(v, list) else v) for k, v in JOURNAL_FAMILIES[family].items()}


def get_journal_config(journal_id: str, yaml_path=None, overrides_path=None, article_type="original",
                       no_page_numbers=False, no_line_numbers=False) -> dict:
    """Merge the family format with the journal's own limits from the YAML (overrides first).
    `generic` / `none` (when no entry has that id) gives a journal-neutral config without limits.
    Exits with code 2 when the id is unknown or a template file / limits block is malformed."""
    if article_type not in ARTICLE_TYPES:
        _fail(f"--article-type must be one of {', '.join(ARTICLE_TYPES)}, not {article_type!r}")
    try:
        _, overrides, _ = _load_templates(overrides_path)
    except TemplateFileError as exc:
        _fail(f"overrides file: {exc}")
    try:
        data_as_of, library, defaults = _load_templates(yaml_path)
    except TemplateFileError as exc:
        _fail(f"journal library (--yaml): {exc}")
    entry, source = None, None
    for src, entries in (("overrides", overrides), ("library", library)):
        entry = next((e for e in entries if str(e.get("id", "")).lower() == str(journal_id).lower()), None)
        if entry is not None:
            source = src
            break
    if entry is None and str(journal_id).lower() in GENERIC_IDS:
        config = _base_config("standard")
        page, line, num_src = _numbering({}, defaults, no_page_numbers, no_line_numbers)
        config.update({
            "journal_id": "generic", "journal_name": "Journal-neutral (no journal selected)", "family": "standard",
            "section_order": list(GENERIC_ORDER), "generic": True, "data_as_of": data_as_of,
            "optional_sections": set(GENERIC_ORDER) - {"title-page", "abstract", "introduction", "methods",
                                                       "results", "discussion", "references"},
            "article_type": article_type, "verified": True, "limits": {k: None for k in LIMIT_INT_KEYS},
            "limits_checked": False, "limits_source": None, "soft_keys": set(), "no_limit_keys": set(),
            "limit_notes": [], "body_rule": "convention", "per_item_words": None,
            "skip_reason": ("Journal-neutral export (`--journal generic`): no journal limits were checked — "
                            "export again with the target journal's id before submission."),
            "page_numbers": page, "line_numbers": line, "numbering_source": num_src, "special_yaml": [],
        })
        config["limits"]["body_excludes"] = list(CONVENTIONAL_EXCLUDES)
        return config
    if entry is None:
        _fail(f"journal id '{journal_id}' not found in {yaml_path}"
              + (f" or {overrides_path}" if overrides_path else "")
              + " — find the id with: python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/"
              f"get_journal_template.py --search {str(journal_id).split('-')[0]} ; a journal that is not in the "
              "library goes into ./journal-overrides.yaml (same structure, pass --overrides); "
              "--journal generic exports without journal limits")
    family = str(entry.get("family") or infer_family(entry.get("id", ""), entry.get("journal", ""))).lower()
    if family not in JOURNAL_FAMILIES:
        family = infer_family(entry.get("id", ""), entry.get("journal", ""))
    name = entry.get("journal", journal_id)
    try:
        lim = _journal_limits(entry, article_type, name)
    except TemplateFileError as exc:
        _fail(f"{'overrides file' if source == 'overrides' else 'journal library (--yaml)'}, "
              f"entry `{entry.get('id')}`: {exc}")
    limits = lim["limits"] or {k: None for k in LIMIT_INT_KEYS}
    # The free-text fields describe the original article: their "no fixed limit" and "each table / figure
    # counts N words" do not carry over to limits_by_type.
    original = article_type == "original"
    per_item = original and _PER_ITEM_RE.search(
        " ".join(str(entry.get(k) or "") for k in ("word_limit", "figures", "tables")).lower())
    limits_source = lim["source"]
    if limits_source and not limits_source.startswith("free-text"):
        limits_source = f"{'journal-overrides' if source == 'overrides' else 'library'} {limits_source}"
    page, line, num_src = _numbering(entry, defaults, no_page_numbers, no_line_numbers)
    config = _base_config(family)
    config.update({
        "journal_id": entry.get("id", journal_id),
        "journal_name": name,
        "family": family,
        "generic": False,
        "entry_source": source,
        "data_as_of": data_as_of,
        "article_type": article_type,
        "verified": bool(entry.get("guidelines_checked")),
        "guidelines_checked": entry.get("guidelines_checked"),
        "limits": limits,
        "limits_checked": lim["limits"] is not None,
        "limits_source": limits_source,
        "skip_reason": lim["skip_reason"],
        "soft_keys": lim["soft"],
        "no_limit_keys": _no_limit_keys(entry) if original else set(),
        "limit_notes": lim["notes"],
        "body_rule": lim["body_rule"],
        "combined": lim["combined"],
        "per_item_words": int(per_item.group(1).replace(",", "")) if per_item else None,
        "word_limit_raw": entry.get("word_limit"),
        "abstract_raw": entry.get("abstract"),
        "ref_limit_raw": entry.get("references"),
        "fig_limit_raw": entry.get("figures"),
        "table_limit_raw": entry.get("tables"),
        # the numbers checked, under their pre-D1 names
        "word_limit": limits["body_words"], "abstract_limit": limits["abstract_words"],
        "ref_limit": limits["references"], "fig_limit": limits["figures"], "table_limit": limits["tables"],
        "page_numbers": page, "line_numbers": line, "numbering_source": num_src,
        "special_yaml": entry.get("special") or [],
    })
    return config


# ─── Markdown parsing: blocks ────────────────────────────────────────────────
#
# parse_markdown() first splits the text into blocks — fenced code, ATX / setext headings,
# thematic breaks, block quotes, pipe tables, (nested) lists, paragraphs — and parse_inline()
# then formats the text of one block. It is a deliberate subset of CommonMark + GFM tables +
# Pandoc ^sup^ / ~sub~ (no markdown library is available):
#   * consecutive lines form one paragraph (soft wrap), joined with a space — or with nothing
#     between CJK characters; a line ending in two spaces or "\" keeps its line break;
#   * 4-space indented code blocks are NOT recognised (indented prose stays prose): use fences;
#   * numbered items keep their literal numbers (no Word auto-numbering).

_FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")
_FENCE_CLOSE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*$")
_ATX_RE = re.compile(r"^[ \t]*(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
_HR_RE = re.compile(r"^[ \t]*(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
_SETEXT_RE = re.compile(r"^[ \t]*(?:={3,}|-{3,})[ \t]*$")
_QUOTE_RE = re.compile(r"^[ \t]*>")
_LIST_RE = re.compile(r"^([ \t]*)(?:([-*+])|(\d{1,9})([.)]))[ \t]+(\S.*)$")
_DELIM_CELL_RE = re.compile(r":?-+:?")
_BOLD_LABEL_RE = re.compile(r"^\s*(?:\*\*|__)\S")


def is_placeholder(text: str) -> bool:
    """[TBD] / [TODO] / [pending] / [INSERT … / placeholder / [待补…] (any case), bare TODO / TBD /
    FIXME (upper case), 待补 / 待填 / 待核实, [ref] / [cite] / [citation needed]."""
    low = text.lower()
    return (any(mk in low for mk in PLACEHOLDER_MARKERS) or bool(PLACEHOLDER_RE.search(text))
            or bool(PLACEHOLDER_CI_RE.search(text)))


def html_comments(text: str):
    """[(line, comment body)] for every <!-- ... --> outside fenced code, multi-line ones included
    (line = where the comment starts)."""
    hits = []
    for is_region, start, chunk in _fenced_chunks(text):
        if is_region:
            for m in re.finditer(r"<!--(.*?)-->", chunk, re.DOTALL):
                hits.append((start + chunk.count("\n", 0, m.start()), m.group(1)))
    return hits


def find_comment_placeholders(text: str):
    """Scan the RAW text (before comments are stripped) for <!-- PLACEHOLDER / TODO / TBD ... --> —
    also when the marker is on a later line of a multi-line comment."""
    hits = []
    for ln, body in html_comments(text):
        if re.match(r"\s*(placeholder|todo|tbd|pending|待补|待填)", body, re.IGNORECASE) or is_placeholder(body):
            hits.append((ln, ("<!-- " + " ".join(body.split()))[:86] + " -->"))
    return hits


def _fence_open(line):
    m = _FENCE_RE.match(line)
    if not m or (m.group(2)[0] == "`" and "`" in m.group(3)):  # ```code``` on one line is a code span
        return None
    return m


def _fence_closes(line, marker):
    m = _FENCE_CLOSE_RE.match(line)
    return bool(m) and m.group(1)[0] == marker[0] and len(m.group(1)) >= len(marker)


def _comment_open_after(line, inside):
    """Whether an HTML comment is still open at the end of `line` (given the state before it)."""
    k = 0
    while True:
        if inside:
            end = line.find("-->", k)
            if end < 0:
                return True
            inside, k = False, end + 3
        else:
            start = line.find("<!--", k)
            if start < 0:
                return False
            inside, k = True, start + 4


def _fenced_chunks(text: str):
    """[(is_region, first_line, chunk)]: runs of lines outside fenced code (where <!-- --> comments
    count) and the lines of fenced code blocks; "\\n".join(chunk for ...) == text."""
    chunks, region, start, fence, inside = [], [], 1, None, False

    def flush():
        if region:
            chunks.append((True, start, "\n".join(region)))
            region.clear()

    for n, line in enumerate(text.split("\n"), 1):
        if fence is None:
            m = None if inside else _fence_open(line)
            if m is None:
                if not region:
                    start = n
                region.append(line)
                inside = _comment_open_after(line, inside)
                continue
            flush()
            fence = m.group(2)
        elif _fence_closes(line, fence):
            fence = None
        chunks.append((False, n, line))
    flush()
    return chunks


def strip_html_comments(text: str) -> str:
    """Remove <!-- ... --> but keep line numbers stable (newlines inside comments are preserved).
    Fenced code blocks are left untouched; an unclosed <!-- is left as text."""
    return "\n".join(re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), chunk, flags=re.DOTALL)
                     if is_region else chunk for is_region, _, chunk in _fenced_chunks(text))


def _indent_width(prefix):
    w = 0
    for ch in prefix:
        w = w + 4 - w % 4 if ch == "\t" else w + 1
    return w


def _is_escaped(s, idx):
    n = 0
    while idx - n - 1 >= 0 and s[idx - n - 1] == "\\":
        n += 1
    return n % 2 == 1


def _has_pipe(s):
    return any(ch == "|" and not _is_escaped(s, k) for k, ch in enumerate(s))


def _split_row(line):
    """Cells of a pipe-table row: outer pipes optional, `\\|` is a literal pipe inside a cell."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not _is_escaped(s, len(s) - 1):
        s = s[:-1]
    cells, buf, k = [], [], 0
    while k < len(s):
        ch = s[k]
        if ch == "\\" and k + 1 < len(s):
            buf.append("|" if s[k + 1] == "|" else s[k:k + 2])
            k += 2
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        k += 1
    cells.append("".join(buf).strip())
    return cells


def _is_delim_row(line):
    """A table alignment row such as |---|:-:|--:| (outer pipes optional, one dash is enough)."""
    if not _has_pipe(line):
        return False
    return all(_DELIM_CELL_RE.fullmatch(c) for c in _split_row(line))


def _is_decorative_sep(line):
    """A separator row inside a table body (|---|---|); '| - | - |' is data (dashes as missing values)."""
    return _is_delim_row(line) and any(":" in c or c.count("-") >= 2 for c in _split_row(line))


def _alignment(cell):
    left, right = cell.startswith(":"), cell.endswith(":")
    return "center" if left and right else "right" if right else "left" if left else None


def _starts_table(lines, i):
    s = lines[i].strip()
    if not _has_pipe(s):
        return False
    if i + 1 < len(lines) and _is_delim_row(lines[i + 1]):
        return True                                     # GFM: header row + alignment row
    return len(s) > 1 and s.startswith("|") and s.endswith("|")   # |a|b| rows without an alignment row


def _block_kind(lines, i):
    """What line i starts: fence / heading / rule / quote / table / list, or None (paragraph text)."""
    line = lines[i]
    if _fence_open(line):
        return "fence"
    m = _ATX_RE.match(line)
    if m and m.group(2).strip():
        return "heading"
    if _HR_RE.match(line):
        return "rule"
    if _QUOTE_RE.match(line):
        return "quote"
    if _starts_table(lines, i):
        return "table"
    if _LIST_RE.match(line):
        return "list"
    return None


def _interrupts_paragraph(lines, i):
    kind = _block_kind(lines, i)
    if kind == "list":  # CommonMark: only a bullet or an item numbered 1 may interrupt a paragraph
        m = _LIST_RE.match(lines[i])     # (so a wrapped line starting "2019. Patients" stays text)
        return m.group(2) is not None or int(m.group(3)) == 1
    return kind is not None


def _parse_fence(lines, i, elements):
    m = _fence_open(lines[i])
    indent, marker = len(m.group(1)), m.group(2)
    body, j = [], i + 1
    while j < len(lines) and not _fence_closes(lines[j], marker):
        line = lines[j]
        body.append(line[min(indent, len(line) - len(line.lstrip(" \t"))):])
        j += 1
    el = {"type": "code", "line": i + 1, "lang": (m.group(3).split() or [""])[0], "lines": body}
    if j >= len(lines):
        while body and not body[-1].strip():
            body.pop()
        el["warnings"] = [(i + 1, f"code fence `{marker}` is never closed — everything after it "
                                  "was exported as code")]
    el["src"] = [(i + 2 + k, t) for k, t in enumerate(body)]
    elements.append(el)
    return j + 1


def _parse_paragraph(lines, i, elements, indent_level=0, entry_re=None):
    src, j = [(i + 1, lines[i])], i + 1
    while j < len(lines) and lines[j].strip():
        if not indent_level and _SETEXT_RE.match(lines[j]):          # Title \n ===  /  Title \n ---
            level = 1 if lines[j].strip()[0] == "=" else 2
            elements.append({"type": "heading", "level": level, "line": i + 1, "src": src})
            return j + 1
        if _interrupts_paragraph(lines, j) or (entry_re and entry_re.match(lines[j])):
            break
        src.append((j + 1, lines[j]))
        j += 1
    el = {"type": "paragraph", "line": i + 1, "src": src}
    if indent_level:
        el["indent_level"] = indent_level
    labels = [ln for ln, t in src[1:] if _BOLD_LABEL_RE.match(t)]
    if labels:
        el["warnings"] = [(i + 1, f"lines {i + 1}–{src[-1][0]} were joined into one paragraph (Markdown soft "
                                  f"wrap), but line(s) {', '.join(map(str, labels))} start with a bold label — "
                                  "if they are separate paragraphs, put a blank line between them")]
    elements.append(el)
    return j


def _parse_quote(lines, i, elements):
    para, n = [], len(lines)

    def flush():
        if para:
            elements.append({"type": "quote", "line": para[0][0], "src": list(para)})
            para.clear()

    while i < n:
        line = lines[i]
        if _QUOTE_RE.match(line):
            content = re.sub(r"^[\s>]+", "", line)   # nested '> >' is flattened into one quote
            if content.strip():
                para.append((i + 1, content))
            else:
                flush()
        elif para and line.strip() and _block_kind(lines, i) is None:
            para.append((i + 1, line))               # lazy continuation of the quoted paragraph
        else:
            break
        i += 1
    flush()
    return i


def _parse_table(lines, i, elements):
    n, start = len(lines), i
    aligns = []
    if _is_delim_row(lines[i]) and i + 1 < n and _has_pipe(lines[i + 1]):
        aligns = [_alignment(c) for c in _split_row(lines[i])]  # table that starts with |---|
        i += 1
    header, header_line = _split_row(lines[i]), i + 1
    i += 1
    gfm = i < n and _is_delim_row(lines[i])
    if gfm:
        aligns = [_alignment(c) for c in _split_row(lines[i])]
        i += 1
    rows, row_lines, warnings = [], [], []
    while i < n:
        line, s = lines[i], lines[i].strip()
        if not s:
            break
        if gfm:
            ok = _has_pipe(s) and _block_kind(lines, i) in (None, "table")
        else:
            ok = len(s) > 1 and s.startswith("|") and s.endswith("|")
        if not ok:
            break
        if not _is_decorative_sep(line):
            cells = _split_row(line)
            while len(cells) > len(header) and not cells[-1]:
                cells.pop()                               # trailing empty cells carry nothing
            if len(cells) > len(header):
                warnings.append((i + 1, f"table row has {len(cells)} cells but the header has {len(header)} — "
                                        "the table was widened so no cell is lost; check the header"))
            rows.append(cells)
            row_lines.append(i + 1)
        i += 1
    elements.append({"type": "table", "line": header_line, "headers": header, "rows": rows,
                     "row_lines": row_lines, "aligns": aligns, "warnings": warnings})
    return max(i, start + 1)


def _parse_list(lines, i, elements):
    """Consecutive list items (any nesting) with their wrapped / lazy continuation lines and
    indented continuation paragraphs. Nesting comes from indentation: an item indented at least
    2 columns more than an open item's marker is its child."""
    stack, item, n = [], None, len(lines)   # stack: marker indents of the open items, outermost first
    while i < n:
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j >= n:
                return n
            kind = _block_kind(lines, j)
            if kind == "list":
                i, item = j, None
                continue
            ind = _indent_width(lines[j][:len(lines[j]) - len(lines[j].lstrip(" \t"))])
            if kind is None and stack and ind >= stack[0] + 2:   # indented paragraph inside an item
                while len(stack) > 1 and ind < stack[-1] + 2:
                    stack.pop()
                i, item = _parse_paragraph(lines, j, elements, indent_level=len(stack)), None
                continue
            return j
        kind = _block_kind(lines, i)
        if kind == "list":
            m = _LIST_RE.match(line)
            ind = _indent_width(m.group(1))
            while stack and ind < stack[-1] + 2:
                stack.pop()
            item = {"type": "bullet" if m.group(2) else "numbered", "level": len(stack),
                    "line": i + 1, "src": [(i + 1, m.group(5))]}
            if m.group(3):
                item["number"], item["delim"] = m.group(3), m.group(4)
            stack.append(ind)
            elements.append(item)
        elif kind is None and item is not None:
            item["src"].append((i + 1, line))      # wrapped / lazy continuation line of the item
        else:
            return i                               # a heading, fence, rule, quote or table ends the list
        i += 1
    return i


def _is_cjk(ch):
    """East Asian wide / fullwidth character (Han, kana, CJK punctuation); Hangul is excluded
    because Korean separates words with spaces."""
    if not ch:
        return False
    o = ord(ch)
    if 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F or 0xA960 <= o <= 0xA97F or 0xAC00 <= o <= 0xD7FF:
        return False
    return unicodedata.east_asian_width(ch) in ("W", "F")


def _is_cjk_punct(ch):
    return _is_cjk(ch) and unicodedata.category(ch).startswith("P")


def _joins_without_space(left, right):
    a, b = left.rstrip("*_~^`")[-1:], right.lstrip("*_~^`")[:1]
    if not a or not b:
        return False
    if (_is_cjk(a) and _is_cjk(b)) or _is_cjk_punct(a) or _is_cjk_punct(b):
        return True
    # ambiguous-width quotes and dashes (“ ” ‘ ’ — …) next to CJK text
    amb = lambda ch: unicodedata.category(ch).startswith("P") and unicodedata.east_asian_width(ch) == "A"
    return (_is_cjk(a) and amb(b)) or (_is_cjk(b) and amb(a))


def _join_lines(parts):
    """Join the source lines of one paragraph (Markdown soft wrap). A line ending in two spaces
    or a backslash keeps its line break (returned as '\\n')."""
    pieces = []
    for k, raw in enumerate(parts):
        s, hard = raw.strip(), False
        if k < len(parts) - 1:
            if (len(s) - len(s.rstrip("\\"))) % 2 == 1:
                hard, s = True, s[:-1].rstrip()
            elif raw.endswith("  "):
                hard = True
        pieces.append((s, hard))
    out = pieces[0][0] if pieces else ""
    for (_, hard), (s, _) in zip(pieces, pieces[1:]):
        out += "\n" + s if hard else s if _joins_without_space(out, s) else " " + s
    return out


def parse_markdown(text: str, entry_re=None):
    """Turn markdown into a list of block dicts, each with a 1-based `line` and `src` =
    [(line, source text)] (used for placeholder / citation scanning). Types:
    heading(level, text) · paragraph(text[, indent_level]) · bullet / numbered(level, text[, number,
    delim]) · quote(text) · code(lines, lang) · rule · table(headers, rows, row_lines, aligns).
    Blocks may carry `warnings` = [(line, message)] for the export report.
    `entry_re`: a line it matches starts a new paragraph (one reference "[12] …" / one legend
    "Figure 2. …" per line in references.md / figure-legends.md, even without blank lines)."""
    lines, elements, i = text.split("\n"), [], 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        kind = _block_kind(lines, i)
        if kind == "fence":
            i = _parse_fence(lines, i, elements)
        elif kind == "heading":
            m = _ATX_RE.match(lines[i])
            elements.append({"type": "heading", "level": len(m.group(1)), "line": i + 1,
                             "src": [(i + 1, m.group(2))]})
            i += 1
        elif kind == "rule":
            elements.append({"type": "rule", "line": i + 1, "src": []})
            i += 1
        elif kind == "quote":
            i = _parse_quote(lines, i, elements)
        elif kind == "table":
            i = _parse_table(lines, i, elements)
        elif kind == "list":
            i = _parse_list(lines, i, elements)
        else:
            i = _parse_paragraph(lines, i, elements, entry_re=entry_re)
    for el in elements:
        if el["type"] in ("heading", "paragraph", "bullet", "numbered", "quote"):
            el["text"] = _join_lines([t for _, t in el["src"]])
    return elements


# ─── Markdown parsing: inline ────────────────────────────────────────────────
#
# Tokens: backslash escapes, `code`, [text](url) links, <https://…> autolinks, ![image](…) (kept
# as literal text), Pandoc citations [@key] / @key (kept as literal text, keys collected),
# ^sup^, ~sub~, ~~strike~~, <sup>/<sub>/<br>, and * / _ delimiter runs, which are paired with
# the CommonMark delimiter algorithm (so ***x***, **a *b* c** and *a **b** c* nest correctly).
# Only CLOSED, non-empty markers are formatting; a lone ~ ^ * is ordinary text ("~90%", "2^10").
# A tilde that follows a digit is a range ("18~65岁", "IQR 2~5"), never the start of a subscript,
# and a subscript never contains CJK text or a , ; — so "18~65岁，体重50~80kg" stays as written.

_ESCAPABLE = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
_SUP_RE = re.compile(r"\^([^\s^]+?)\^")                  # ^superscript^ (no spaces inside)
_SUB_RE = re.compile(r"~([^\s~]+?)~")                    # ~subscript~ (no spaces inside)
_SUB_FORBIDDEN = frozenset(",;，；、")
_STRIKE_RE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")
_AUTOLINK_RE = re.compile(r"<((?:https?|ftp)://[^\s<>]+|mailto:[^\s<>]+|[\w.+-]+@[\w-]+(?:\.[\w-]+)+)>")
_HTML_INLINE_RE = re.compile(r"<(sup|sub)>(.*?)</\1>|<br\s*/?>", re.IGNORECASE)
_CITE_KEY = r"-?@(\{[^{}\s]+\}|\w(?:[\w:.#$%&+?~/-]*\w)?)"
_CITE_RE = re.compile(r"(?<![\w@])" + _CITE_KEY)
_CITE_AT_RE = re.compile(_CITE_KEY)
_WRAP_ATTR = {"strong": "bold", "em": "italic", "strike": "strike"}


def _run_length(s, i, ch):
    j = i
    while j < len(s) and s[j] == ch:
        j += 1
    return j - i


def _find_backticks(s, start, run):
    """Index of the next run of exactly `run` backticks at or after `start`, or -1."""
    k = start
    while True:
        k = s.find("`", k)
        if k < 0:
            return -1
        r = _run_length(s, k, "`")
        if r == run:
            return k
        k += r


def _match_bracket(s, i):
    """Index of the ']' closing the '[' at s[i] (escapes and code spans skipped), or None."""
    depth, k = 0, i
    while k < len(s):
        ch = s[k]
        if ch == "\\":
            k += 2
            continue
        if ch == "`":
            run = _run_length(s, k, "`")
            end = _find_backticks(s, k + run, run)
            k = end + run if end >= 0 else k + run
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return None


def _link_destination(s, k):
    """Parse '(url "title")' starting at s[k]; returns (url, index after ')') or None."""
    n = len(s)
    if k >= n or s[k] != "(":
        return None
    k += 1
    while k < n and s[k] in " \t":
        k += 1
    if k < n and s[k] == "<":
        end = s.find(">", k + 1)
        if end < 0:
            return None
        url, k = s[k + 1:end], end + 1
    else:
        start, depth = k, 0
        while k < n and not s[k].isspace():
            if s[k] == "\\":
                k += 2
                continue
            if s[k] == "(":
                depth += 1
            elif s[k] == ")":
                if depth == 0:
                    break
                depth -= 1
            k += 1
        url = s[start:min(k, n)]
    while k < n and s[k] in " \t":
        k += 1
    if k < n and s[k] in "\"'(":
        end = s.find({'"': '"', "'": "'", "(": ")"}[s[k]], k + 1)
        if end < 0:
            return None
        k = end + 1
        while k < n and s[k] in " \t":
            k += 1
    if k < n and s[k] == ")":
        return re.sub(r"\\(.)", r"\1", url), k + 1
    return None


def _is_punct(ch):
    return bool(ch) and unicodedata.category(ch)[0] in "PS"


def _delimiter(ch, count, prev, nxt):
    ws_prev, ws_next = not prev or prev.isspace(), not nxt or nxt.isspace()
    p_prev, p_next = _is_punct(prev), _is_punct(nxt)
    if ch == "*":
        # Lenient: opens unless followed by a space (or by punctuation right after a Latin letter /
        # digit — the footnote marks in "Age*, BMI*"), closes unless preceded by a space. Keeps
        # "**方法：**本研究" and "**Background:**Text" bold; "2 * 3" and "marked with *" stay literal.
        latin_prev = bool(prev) and prev.isalnum() and not _is_cjk(prev)
        can_open = not ws_next and not (p_next and latin_prev)
        can_close = not ws_prev
    else:
        # CommonMark rules for "_": no intraword emphasis, so snake_case_names stay untouched.
        left = not ws_next and (not p_next or ws_prev or p_prev)
        right = not ws_prev and (not p_prev or ws_next or p_next)
        can_open = left and (not right or p_prev)
        can_close = right and (not left or p_next)
    return {"t": "delim", "ch": ch, "n": count, "orig": count, "open": can_open, "close": can_close}


def _subscript_ok(s, i, m):
    """Pandoc ~x~ only where it cannot be a range: not right after a digit, no CJK / , ; inside."""
    if i and unicodedata.category(s[i - 1]) == "Nd":
        return False
    return not any(_is_cjk(ch) or ch in _SUB_FORBIDDEN for ch in m.group(1))


def _tokenize(s, cites, subs=None):
    nodes, buf, i, n = [], [], 0, len(s)

    def flush():
        if buf:
            nodes.append({"t": "text", "s": "".join(buf)})
            buf.clear()

    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n and s[i + 1] in _ESCAPABLE:
            buf.append(s[i + 1])
            i += 2
            continue
        if c == "`":
            run = _run_length(s, i, "`")
            end = _find_backticks(s, i + run, run)
            if end < 0:
                buf.append("`" * run)
                i += run
                continue
            code = s[i + run:end]
            if len(code) > 2 and code[0] == code[-1] == " " and code.strip():
                code = code[1:-1]
            flush()
            nodes.append({"t": "code", "s": code})
            i = end + run
            continue
        if c == "!" and s.startswith("[", i + 1):
            close = _match_bracket(s, i + 1)
            dest = _link_destination(s, close + 1) if close is not None else None
            if dest:                        # images are not embedded: keep ![alt](path) as text
                buf.append(s[i:dest[1]])
                i = dest[1]
                continue
        elif c == "[":
            close = _match_bracket(s, i)
            if close is not None:
                dest = _link_destination(s, close + 1)
                if dest:
                    flush()
                    nodes.append({"t": "link", "url": dest[0], "c": _inline_tree(s[i + 1:close], None, subs)})
                    i = dest[1]
                    continue
                keys = [m.group(1) for m in _CITE_RE.finditer(s, i + 1, close)]
                if keys:                    # Pandoc citation: keep the text, collect the keys
                    if cites is not None:
                        cites.extend(keys)
                    buf.append(s[i:close + 1])
                    i = close + 1
                    continue
        elif c == "<":
            m = _AUTOLINK_RE.match(s, i)
            if m:
                url = m.group(1)
                flush()
                nodes.append({"t": "link", "url": url if ":" in url.split("@")[0] else "mailto:" + url,
                              "c": [{"t": "text", "s": url}]})
                i = m.end()
                continue
            m = _HTML_INLINE_RE.match(s, i)
            if m:
                flush()
                nodes.append({"t": m.group(1).lower(), "s": m.group(2)} if m.group(1) else {"t": "text", "s": "\n"})
                i = m.end()
                continue
        elif c in "*_":
            run = _run_length(s, i, c)
            flush()
            nodes.append(_delimiter(c, run, s[i - 1] if i else "", s[i + run] if i + run < n else ""))
            i += run
            continue
        elif c == "^":
            m = _SUP_RE.match(s, i)
            if m:
                flush()
                nodes.append({"t": "sup", "s": m.group(1)})
                i = m.end()
                continue
        elif c == "~":
            m = _STRIKE_RE.match(s, i)
            if m:
                flush()
                nodes.append({"t": "strike", "c": _inline_tree(m.group(1), cites, subs)})
                i = m.end()
                continue
            m = _SUB_RE.match(s, i)
            if m and _subscript_ok(s, i, m):
                flush()
                if subs is not None:
                    subs.append(m.group(0))
                nodes.append({"t": "sub", "s": m.group(1)})
                i = m.end()
                continue
        elif c == "@" and cites is not None and not (i and (s[i - 1].isalnum() or s[i - 1] in "_@")):
            m = _CITE_AT_RE.match(s, i)     # in-text Pandoc citation (@smith2020 says …); e-mails excluded
            if m:
                cites.append(m.group(1))
                buf.append(m.group(0))
                i = m.end()
                continue
        buf.append(c)
        i += 1
    flush()
    return nodes


def _as_text(node):
    return {"t": "text", "s": node["ch"] * node["n"]} if node["t"] == "delim" else node


def _resolve_emphasis(nodes):
    """CommonMark 'process emphasis': pair * / _ delimiter runs into em / strong nodes."""
    i = 0
    while i < len(nodes):
        cur = nodes[i]
        if cur["t"] != "delim" or not cur["close"]:
            i += 1
            continue
        j = i - 1
        while j >= 0:
            op = nodes[j]
            if (op["t"] == "delim" and op["ch"] == cur["ch"] and op["open"]
                    and not ((op["close"] or cur["open"]) and (op["orig"] + cur["orig"]) % 3 == 0
                             and not (op["orig"] % 3 == 0 and cur["orig"] % 3 == 0))):
                break
            j -= 1
        if j < 0:                                   # no opener: a closer that cannot open is text
            if not cur["open"]:
                nodes[i] = _as_text(cur)
            i += 1
            continue
        op = nodes[j]
        use = 2 if op["n"] >= 2 and cur["n"] >= 2 else 1
        op["n"] -= use
        cur["n"] -= use
        wrapped = {"t": "strong" if use == 2 else "em", "c": [_as_text(x) for x in nodes[j + 1:i]]}
        repl = ([op] if op["n"] else []) + [wrapped] + ([cur] if cur["n"] else [])
        nodes[j:i + 1] = repl
        i = j + len(repl) - (1 if cur["n"] else 0)
    return [_as_text(x) for x in nodes]


def _inline_tree(text, cites, subs=None):
    return _resolve_emphasis(_tokenize(text, cites, subs))


def _flatten(nodes, attrs, out):
    for nd in nodes:
        t = nd["t"]
        if t in _WRAP_ATTR:
            _flatten(nd["c"], {**attrs, _WRAP_ATTR[t]: True}, out)
        elif t == "link":
            _flatten(nd["c"], {**attrs, "url": nd["url"]} if nd["url"] else attrs, out)
        elif nd["s"]:
            a = attrs if t == "text" else {**attrs, t: True}
            if out and out[-1][1] == a:
                out[-1] = (out[-1][0] + nd["s"], a)
            else:
                out.append((nd["s"], a))


def parse_inline(text: str, cites=None):
    """[(chunk, attrs)] for one block of text; attrs keys: bold, italic, strike, sup, sub, code, url.
    Pandoc citation keys found in the text are appended to `cites` when a list is given."""
    out = []
    _flatten(_inline_tree(text, cites), {}, out)
    return out


def citation_keys(text: str):
    """Pandoc citation keys ([@key], [see @a; @b, p. 3], in-text @key) — kept as literal text."""
    keys = []
    _inline_tree(text, keys)
    return keys


def _new_hyperlink(paragraph, url):
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True))
    paragraph._p.append(link)
    return link


def add_formatted_text(paragraph, text: str, config: dict, base_bold=False, base_italic=False, size=None):
    """Add text with inline markdown formatting; unmatched markers are written verbatim.
    Links become real hyperlinks; `code` is set in Courier New."""
    link, link_url = None, None
    for chunk, a in parse_inline(text):
        run = paragraph.add_run(chunk)
        run.font.name = CODE_FONT if a.get("code") else config["font"]
        if size:
            run.font.size = Pt(size)
        run.bold = a.get("bold") or base_bold or None
        run.italic = a.get("italic") or base_italic or None
        if a.get("sup"):
            run.font.superscript = True
        if a.get("sub"):
            run.font.subscript = True
        if a.get("strike"):
            run.font.strike = True
        url = a.get("url")
        if url:
            run.font.underline = True
            run.font.color.rgb = LINK_COLOR
            if link is None or url != link_url:
                link, link_url = _new_hyperlink(paragraph, url), url
            link.append(run._r)            # move the run inside <w:hyperlink>
        else:
            link = link_url = None


def plain_text(text: str) -> str:
    """Text as it will appear in the .docx (markers of closed spans removed, link text only)."""
    return "".join(chunk for chunk, _ in parse_inline(text))


def _set_style_font(style, font_name: str):
    """Set a style's font for Latin + East Asian text and drop theme fonts that would override it."""
    style.font.name = font_name
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        rpr.append(rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rfonts.attrib.pop(qn(attr), None)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), font_name)


def set_cell_shading(cell, color_hex: str):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'))


# Schema order of <w:pPr> children, so borders / shading / numbering land where Word expects them.
_PPR_ORDER = ("w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr", "w:widowControl",
              "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd", "w:tabs", "w:suppressAutoHyphens",
              "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE",
              "w:autoSpaceDN", "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
              "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc", "w:textDirection",
              "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr",
              "w:sectPr", "w:pPrChange")


def _insert_ppr_child(paragraph, element):
    tag = "w:" + element.tag.split("}")[1]
    paragraph._p.get_or_add_pPr().insert_element_before(element, *_PPR_ORDER[_PPR_ORDER.index(tag) + 1:])


# ─── Counting helpers ────────────────────────────────────────────────────────

def count_words(text: str, stats=None) -> int:
    """Words as journals count them: space-separated words, except that every CJK character
    (Han / kana; punctuation excluded) counts as one, like a character count (字数).
    Tokens without a letter or digit ('—', '|') are not words."""
    n = cjk = 0
    for tok in text.split():
        rest = []
        for ch in tok:
            if _is_cjk(ch):
                cjk += unicodedata.category(ch)[0] in "LN"
                rest.append(" ")
            else:
                rest.append(ch)
        n += sum(1 for w in "".join(rest).split() if any(c.isalnum() for c in w))
    if stats is not None:
        stats["cjk_chars"] += cjk
    return n + cjk


# A legend / caption starts its block: "Figure 2. …", "**Fig. 3 | …**", "## Figure 1", "Figure 1a:",
# "Figure 4 Kaplan–Meier …", "图1 …", "Table 1. …", "表 2：…" ("Figure 1 shows …" is running text).
_CAPTION_TAIL = r"(?:[A-Za-z](?![A-Za-z]))?\s*(?:[.:：|｜—–]|-\s|$|\s+(?=[A-Z㐀-鿿]))"
_FIG_CAPTION_RE = re.compile(r"\s*(?:Figure|FIGURE|Fig\.?|FIG\.?|图)\s*(\d{1,3})" + _CAPTION_TAIL)
_TAB_CAPTION_RE = re.compile(r"\s*(?:Table|TABLE|Tab\.|表)\s*(\d{1,3})" + _CAPTION_TAIL)
# In-text mentions ("Figure 3", "Figs. 2–4", "如图1所示", "Table 2"); supplementary ones are skipped.
# 图N / 表N / 图 N is a citation whatever comes before it (对图3, 结合表2, 通过图4, 比较图2与图3 …), except
# where 图 / 表 ends a known word: 发表5篇, 代表4级, 试图9次, 列表3项, 地图3张, 意图 / 示意图2, 时间表2 ….
# The words, by what comes before 图 / 表; ("外", "此另…"): 外表 is a word, but 此外表5 is 此外 + 表5.
_CJK_COMPOUND_PREFIXES = {
    "图": ("试", "企", ("意", "注留"), "地", "蓝", "版", "构", "截", "绘", "力"),
    "表": ("发", "代", "列", "图", "报", "仪", ("外", "此另以之除额"), ("量", "变剂含数质流测总本入用"), "课", "制",
          "时间", "时刻", "统计", "日程", "一览"),
}


def _cjk_cite(char):
    guards = []
    for prefix in _CJK_COMPOUND_PREFIXES[char]:
        word, unless = (prefix, "") if isinstance(prefix, str) else prefix
        guards.append(f"(?<!(?<![{unless}]){word})" if unless else f"(?<!{word})")
    return "".join(guards) + char + r"\s*(\d{1,3})(?!\d)(?:\s*[-–—~～至]\s*(\d{1,3})(?!\d))?"


_FIG_CITE_RE = re.compile(r"(?<![A-Za-z])(?:Figures?|FIGURES?|Figs?\.?|FIGS?\.?)\s*(\d{1,3})(?!\d)"
                          r"(?:\s*(?:[-–—]|to)\s*(\d{1,3})(?!\d))?|" + _cjk_cite("图"))
_TAB_CITE_RE = re.compile(r"(?<![A-Za-z])(?:Tables?|TABLES?|Tabs?\.)\s*(\d{1,3})(?!\d)"
                          r"(?:\s*(?:[-–—]|to)\s*(\d{1,3})(?!\d))?|" + _cjk_cite("表"))
# right before a mention, it is not a main one: Supplementary Figure 2, 附图1, 补充表2, 补充材料表1, 扩展数据图1
_NOT_MAIN_RE = re.compile(r"(?:supplement\w*|extended data|appendix|online|"
                          r"(?:附录?|补充|扩展数据|在线)(?:材料|资料|数据|文件)?(?:中的?)?)\s*$", re.IGNORECASE)
# One reference per line in references.md: "[12] …" / "(12) …" (numbered "12. …" items are lists);
# up to 3 digits, so a wrapped line starting with a year "(2020) …" is not a new reference.
_REF_ENTRY_RE = re.compile(r"^[ \t]{0,3}(?:\[\d{1,3}\]|\(\d{1,3}\))[ \t]*\S")
# One legend per line in figure-legends.md.
_LEGEND_LINE_RE = re.compile(r"^[ \t]{0,3}(?:[*_]{1,3}|#{1,6}[ \t]+)?[ \t]*(?:Figure|FIGURE|Fig\.?|FIG\.?|图|"
                             r"Table|TABLE|表)\s*\d")
_CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
# Markdown that is written as literal text (OS-7): reported so it can be fixed before submission.
_UNSUPPORTED = (
    (re.compile(r"\[\^[^\]\s]+\]"),
     "Markdown footnote `[^n]` kept as literal text — put the note in the text or use the journal's footnote style"),
    (re.compile(r"^[ \t]{0,3}\[(?!\^)[^\]]+\]:[ \t]*\S"),
     "reference-style link definition `[id]: url` kept as literal text — use inline links `[text](url)`"),
    (re.compile(r"\[[^\]]*\]\[[^\]]*\]"),
     "reference-style link `[text][id]` kept as literal text — use inline links `[text](url)`"),
    (re.compile(r"</?(?!(?:sup|sub|br)\b)[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>", re.IGNORECASE),
     "inline HTML kept as literal text (only <sup>, <sub> and <br> are converted)"),
    (re.compile(r"\$\$|(?<![\\$\w])\$(?=\S)[^$\n]*?(?<=\S)\$(?!\d)"),
     "TeX math `$…$` kept as literal text — use Unicode symbols or Word's equation editor"),
)
_SUB_NOTE = ("`~x~` set as subscript (Pandoc rule; a tilde right after a digit, as in 18~65, stays a "
             "tilde) — check these are meant as subscripts; write `\\~` for a literal tilde")


def caption_kind(plain: str):
    """('figure' | 'table', number) when a block starts like a legend / caption, else None."""
    for kind, rx in (("figure", _FIG_CAPTION_RE), ("table", _TAB_CAPTION_RE)):
        m = rx.match(plain)
        if m:
            return kind, int(m.group(1))
    return None


def cited_numbers(plain: str, rx) -> set:
    """Figure / table numbers mentioned in running text (both ends of '2–4'); 'Supplementary
    Figure 2', 'Extended Data Fig. 1', 'eFigure 1', 'Figure S1', '附图1', '补充表2' are not main figures."""
    nums = set()
    for m in rx.finditer(plain):
        if not _NOT_MAIN_RE.search(plain[max(0, m.start() - 25):m.start()]):
            nums.update(int(g) for g in m.groups() if g)
    return nums


def subscripts(text: str):
    """The ~x~ spans parse_inline sets as subscript (listed in the conversion notes)."""
    subs = []
    _inline_tree(text, None, subs)
    return subs


def _note(stats, icon, filename, line, message, example=None):
    stats["notes"].append((icon, filename, line, message, example))


# ─── Document builder ────────────────────────────────────────────────────────

# <w:sectPr> children that follow <w:lnNumType> in the schema.
_SECTPR_AFTER_LNNUM = ("w:pgNumType", "w:cols", "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
                       "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid", "w:printerSettings",
                       "w:sectPrChange")


def _add_page_numbers(section, where, align):
    """A PAGE field in the footer (or header), centred or right-aligned."""
    part = section.header if where == "header" else section.footer
    p = part.paragraphs[0] if part.paragraphs else part.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if align == "right" else WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr=" PAGE "><w:r><w:t>1</w:t></w:r></w:fldSimple>'))


def _add_line_numbers(section, restart):
    """Word line numbering on every line (restart: continuous / newPage / newSection)."""
    sect_pr = section._sectPr
    for old in sect_pr.findall(qn("w:lnNumType")):
        sect_pr.remove(old)
    sect_pr.insert_element_before(
        parse_xml(f'<w:lnNumType {nsdecls("w")} w:countBy="1" w:restart="{restart}"/>'), *_SECTPR_AFTER_LNNUM)


def _new_document(config: dict):
    doc = Document()
    normal = doc.styles["Normal"]
    _set_style_font(normal, config["font"])
    normal.font.size = Pt(config["font_size"])
    normal.paragraph_format.line_spacing = config["line_spacing"]
    normal.paragraph_format.space_after = Pt(0)
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Cm(config["margin_cm"])
        section.left_margin = section.right_margin = Cm(config["margin_cm"])
        if config.get("page_numbers"):
            _add_page_numbers(section, *config["page_numbers"])
        if config.get("line_numbers"):
            _add_line_numbers(section, config["line_numbers"])
    for level in range(1, 7):
        h = doc.styles[f"Heading {level}"]
        _set_style_font(h, config["font"])
        h.font.size = Pt(config.get(f"heading{min(level, 3)}_size", 12))
        h.font.bold = True
        h.font.color.rgb = RGBColor(0, 0, 0)
    return doc


def _styled(doc, base, level):
    """`base`, `base 2`, `base 3` for list level 0 / 1 / 2+ — the deepest one the template has."""
    for lvl in range(min(level, 2), -1, -1):
        name = base if lvl == 0 else f"{base} {lvl + 1}"
        if name in doc.styles:
            return name
    return None


def _add_heading(doc, level):
    while level > 1 and f"Heading {level}" not in doc.styles:
        level -= 1
    return doc.add_heading("", level=level)


def _add_code_block(doc, lines, config):
    p = doc.add_paragraph()
    _insert_ppr_child(p, parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="F2F2F2"/>'))
    fmt = p.paragraph_format
    fmt.line_spacing = 1.0
    fmt.left_indent = Cm(0.5)
    fmt.space_before = fmt.space_after = Pt(6)
    run = p.add_run("\n".join(lines))       # verbatim: '\n' → line break, leading spaces preserved
    run.font.name = CODE_FONT
    run.font.size = Pt(max(8, config["font_size"] - 2))


def _add_rule(doc):
    p = doc.add_paragraph()
    _insert_ppr_child(p, parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" '
                                   'w:space="1" w:color="auto"/></w:pBdr>'))


def _new_stats():
    return {"words": {}, "body_keys": [], "ref_count": 0, "ref_unnumbered": 0, "ref_file": False,
            "fig_numbers": set(), "fig_cited": set(), "fig_embedded": 0, "fig_legends": 0,
            "legends_unrecognised": 0, "table_count": 0, "table_numbers": set(), "table_cited": set(),
            "legend_words": 0, "table_words": 0, "cjk_chars": 0,
            "placeholders": [], "warnings": [], "notes": [], "citations": [], "sections_included": [],
            "missing_required": [], "missing_optional": [], "not_exported": [], "review_sections": [],
            "legends_file": None, "legends_note": None}


_TEXT_BLOCKS = ("heading", "paragraph", "bullet", "numbered", "quote")


def _render_elements(doc, elements, config, section_id, filename, stats, kind="other"):
    """Write parsed elements into `doc`; update word / figure / table / reference / placeholder /
    citation stats. kind: body (main text) · references · legends (figure-legends.md) ·
    supplementary · other (title page, abstract, key points, research in context).
    In body files, legend / caption blocks ('**Figure 1.** …', 'Table 2. …') are not body text."""
    words = 0
    for el in elements:
        t = el["type"]
        scan = list(el.get("src", [(el["line"], el.get("text", ""))]))  # (line, source) for placeholders
        if t == "heading":
            add_formatted_text(_add_heading(doc, el["level"]), el["text"], config)
        elif t == "paragraph":
            style = _styled(doc, "List Continue", el["indent_level"] - 1) if el.get("indent_level") else None
            add_formatted_text(doc.add_paragraph(style=style), el["text"], config)
        elif t == "bullet":
            add_formatted_text(doc.add_paragraph(style=_styled(doc, "List Bullet", el["level"])),
                               el["text"], config)
        elif t == "numbered":
            # Literal "N. text" — no Word auto-numbering, so references and body lists never chain.
            p = doc.add_paragraph(style=_styled(doc, "List Number", el["level"]))
            _insert_ppr_child(p, parse_xml(f'<w:numPr {nsdecls("w")}><w:ilvl w:val="0"/>'
                                           '<w:numId w:val="0"/></w:numPr>'))   # numbering off
            p.paragraph_format.left_indent = Cm(0.75 * (el["level"] + 1))
            p.paragraph_format.first_line_indent = Cm(-0.75)
            add_formatted_text(p, f"{el['number']}{el.get('delim', '.')} {el['text']}", config)
        elif t == "quote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.27)
            add_formatted_text(p, el["text"], config, base_italic=True)
        elif t == "code":
            _add_code_block(doc, el["lines"], config)   # verbatim, not counted as words
        elif t == "rule":
            _add_rule(doc)
        elif t == "table":
            _add_table(doc, el["headers"], el["rows"], config, el.get("aligns"))
            stats["table_count"] += 1
            scan = [(el["line"], " | ".join(el["headers"]))]
            scan += [(ln, " | ".join(row)) for ln, row in zip(el["row_lines"], el["rows"])]
            stats["table_words"] += sum(count_words(plain_text(c), stats)
                                        for c in list(el["headers"]) + [c for row in el["rows"] for c in row])
        if t in _TEXT_BLOCKS:
            plain = plain_text(el["text"])
            n = 0 if t == "heading" else count_words(plain, stats)
            top = t in ("heading", "quote") or (t == "paragraph" and not el.get("indent_level")) or \
                (t in ("bullet", "numbered") and el["level"] == 0)
            cap = caption_kind(plain) if top and kind in ("body", "legends", "supplementary") else None
            if cap:
                (stats["fig_numbers"] if cap[0] == "figure" else stats["table_numbers"]).add(cap[1])
            if cap and kind == "body":
                stats["legend_words" if cap[0] == "figure" else "table_words"] += n
            else:
                words += n
            if kind == "body":
                stats["fig_cited"] |= cited_numbers(plain, _FIG_CITE_RE)
                stats["table_cited"] |= cited_numbers(plain, _TAB_CITE_RE)
            elif kind == "legends" and top and not cap and t != "heading":
                if t == "numbered":                          # "1. Kaplan–Meier curves …"
                    stats["fig_numbers"].add(int(el["number"]))
                else:
                    stats["legends_unrecognised"] += 1
            elif kind == "references" and top and t != "heading":
                if t in ("numbered", "bullet") or _REF_ENTRY_RE.match(el["src"][0][1]):
                    stats["ref_count"] += 1
                elif t == "paragraph":
                    stats["ref_unnumbered"] += 1
            if t in ("bullet", "numbered") and re.match(r"#{1,6}\s", el["text"]):
                _note(stats, "⚠️", filename, el["line"], "heading inside a list item kept as text (`- # …`)")
        if t != "code" and kind in ("body", "legends", "supplementary"):
            cells = [el.get("text", "")] if t != "table" else list(el["headers"]) + [c for r in el["rows"] for c in r]
            stats["fig_embedded"] += sum(len(_IMAGE_RE.findall(_CODE_SPAN_RE.sub(" ", c))) for c in cells)
        for ln, src in scan:
            if is_placeholder(src):
                stats["placeholders"].append(f"{filename}:{ln} — {src.strip()[:80]}")
            if t == "code":
                continue
            stats["citations"] += [(key, f"{filename}:{ln}") for key in citation_keys(src)]
            for sub in subscripts(src):
                _note(stats, "ℹ️", filename, ln, _SUB_NOTE, sub)
            bare = _CODE_SPAN_RE.sub(" ", src)
            for rx, msg in _UNSUPPORTED:
                m = rx.search(bare)
                if m:
                    _note(stats, "⚠️", filename, ln, msg, m.group(0)[:30])
        stats["warnings"] += [f"{filename}:{ln} — {msg}" for ln, msg in el.get("warnings", [])]
    stats["words"][section_id] = stats["words"].get(section_id, 0) + words


_ALIGN = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER, "right": WD_ALIGN_PARAGRAPH.RIGHT}


def _add_table(doc, headers, rows, config, aligns=None):
    if not headers:
        return
    n_cols = max([len(headers)] + [len(r) for r in rows])    # extra cells widen the table (reported)
    headers = list(headers) + [""] * (n_cols - len(headers))
    aligns = list(aligns or []) + [None] * n_cols
    table = doc.add_table(rows=1 + len(rows), cols=n_cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    size = config["font_size"] - 1
    for r, row in enumerate([headers] + list(rows)):
        for c, text in enumerate(row):
            cell = table.rows[r].cells[c]
            add_formatted_text(cell.paragraphs[0], text, config, base_bold=(r == 0), size=size)
            if aligns[c]:
                cell.paragraphs[0].alignment = _ALIGN[aligns[c]]
            if r == 0:
                set_cell_shading(cell, "D9D9D9")
    doc.add_paragraph()


def _read_section(path, filename, stats, entry_re=None):
    """Read one section file (UTF-8; a BOM is dropped); returns (raw_text, elements) and records
    comment placeholders and the other comments that are removed. Raises InputError."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            raw = f.read()
    except UnicodeDecodeError:
        raise InputError(f"{path} is not UTF-8 text — save it as UTF-8 and export again") from None
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc.strerror or exc}") from None
    flagged = set()
    for ln, snippet in find_comment_placeholders(raw):
        stats["placeholders"].append(f"{filename}:{ln} — {snippet}")
        flagged.add(ln)
    for ln, _ in html_comments(raw):
        if ln not in flagged:
            _note(stats, "ℹ️", filename, ln, "HTML comment removed (not exported)")
    return raw, parse_markdown(strip_html_comments(raw), entry_re)


def review_sections(manuscript_dir):
    """section-N-*.md files of a thematic (narrative / mini) review, in numeric order."""
    found = []
    for name in os.listdir(manuscript_dir):
        m = REVIEW_SECTION_RE.match(name)
        if m and os.path.isfile(os.path.join(manuscript_dir, name)):
            found.append((int(m.group(1)), name.lower(), name))
    return [name for _, _, name in sorted(found)]


def _shown(path):
    try:
        rel = os.path.relpath(path)
    except ValueError:                                  # another drive (Windows)
        return path
    return path if rel.startswith("..") else rel


def _contains(folder, path):
    """Whether `path` lies inside `folder` (both absolute)."""
    try:
        return os.path.commonpath([folder, path]) == folder
    except ValueError:                                  # another drive (Windows)
        return False


def find_legends_file(manuscript_dir):
    """(path or None, note or None): <manuscript-dir>/figure-legends.md, else figure-legends.md in
    the project folder — the manuscript folder's parent, or the current directory when the
    manuscript folder lies inside it (where figure-generation writes it). A figure-legends.md in
    a current directory that does not contain the manuscript folder belongs to another project."""
    name = SECTION_FILES["figure-legends"]
    inside = os.path.join(manuscript_dir, name)
    bases = [(os.path.dirname(os.path.abspath(manuscript_dir)),
              "the project folder, where figure-generation writes it")]
    cwd = os.getcwd()
    if any(_contains(f(cwd), f(manuscript_dir)) for f in (os.path.abspath, os.path.realpath)):
        bases.append((cwd, "the current folder, which contains the manuscript folder"))
    outside, seen = [], {os.path.realpath(inside)}
    for base, where in bases:
        p = os.path.join(base, name)
        if os.path.isfile(p) and os.path.realpath(p) not in seen:
            outside.append((p, where))
            seen.add(os.path.realpath(p))
    if os.path.isfile(inside):
        if outside:
            return inside, (f"⚠️ `{_shown(outside[0][0])}` also exists and was NOT exported — only "
                            f"`{_shown(inside)}` was used; merge the two")
        return inside, None
    if outside:
        return outside[0][0], (f"ℹ️ `{_shown(inside)}` does not exist: the legends were read from "
                               f"`{_shown(outside[0][0])}` ({outside[0][1]})")
    return None, None


def build_docx(manuscript_dir: str, config: dict, output_path: str) -> dict:
    """Build the main .docx following the family section order (thematic review sections
    section-N-*.md right after the Introduction). Returns stats; raises InputError."""
    stats = _new_stats()
    doc = _new_document(config)
    review = review_sections(manuscript_dir)
    optional = set(config.get("optional_sections", OPTIONAL_SECTIONS))
    if review:
        optional |= {"methods", "results"}             # a thematic review has no Methods / Results
    plan = []
    for section_id in config["section_order"]:
        if section_id == "figure-legends":
            path, stats["legends_note"] = find_legends_file(manuscript_dir)
            inside = bool(path) and os.path.realpath(os.path.dirname(path)) == os.path.realpath(manuscript_dir)
            label = SECTION_FILES[section_id] if inside or not path else _shown(path)
            stats["legends_file"] = _shown(path) if path else None
        else:
            path, label = os.path.join(manuscript_dir, SECTION_FILES[section_id]), SECTION_FILES[section_id]
        if path and os.path.isfile(path):
            plan.append((section_id, path, label))
        else:
            (stats["missing_optional"] if section_id in optional else stats["missing_required"]).append(section_id)
        if section_id == "introduction":
            plan += [("review", os.path.join(manuscript_dir, name), name) for name in review]
    prev = None
    for section_id, path, label in plan:
        # Page breaks only after title page / abstract and before references.
        if prev in ("title-page", "abstract") or (section_id == "references" and prev is not None):
            doc.add_page_break()
        kind = ("body" if section_id in BODY_SECTIONS or section_id == "review" else
                "references" if section_id == "references" else
                "legends" if section_id == "figure-legends" else "other")
        entry_re = {"references": _REF_ENTRY_RE, "legends": _LEGEND_LINE_RE}.get(kind)
        _, elements = _read_section(path, label, stats, entry_re)
        if section_id in SECTION_TITLES and not any(e["type"] == "heading" for e in elements):
            doc.add_heading(SECTION_TITLES[section_id], level=1)
        key = os.path.splitext(label)[0] if section_id == "review" else section_id
        _render_elements(doc, elements, config, key, label, stats, kind)
        if kind == "body":
            stats["body_keys"].append(key)
        if section_id == "review":
            stats["review_sections"].append(label)
        stats["ref_file"] = stats["ref_file"] or section_id == "references"
        stats["sections_included"].append(key)
        prev = section_id
    stats["fig_legends"] = len(stats["fig_numbers"])
    if not stats["sections_included"]:
        raise InputError(f"no manuscript sections found in {manuscript_dir} (expected files like "
                         f"{', '.join(SECTION_FILES[s] for s in config['section_order'][:4])} ...)")
    used = {SECTION_FILES[s] for s in config["section_order"]} | {"supplementary.md"} | set(review)
    stats["not_exported"] = sorted(f for f in os.listdir(manuscript_dir)
                                   if f.endswith(".md") and f not in used and not _is_earlier_output(
                                       os.path.join(manuscript_dir, f), "--report"))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return stats


def export_supplementary(manuscript_dir: str, config: dict, output_path: str):
    """Export supplementary.md as its own .docx (same family formatting). Returns stats or None."""
    path = os.path.join(manuscript_dir, "supplementary.md")
    if not os.path.exists(path):
        return None
    stats = _new_stats()
    doc = _new_document(config)
    _, elements = _read_section(path, "supplementary.md", stats)
    _render_elements(doc, elements, config, "supplementary", "supplementary.md", stats, "supplementary")
    stats["fig_legends"] = len(stats["fig_numbers"])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return stats


# ─── Report ──────────────────────────────────────────────────────────────────

_PART_LABELS = {"abstract": "abstract", "methods": "Methods", "references": "references",
                "figure_legends": "figure legends", "tables": "tables", "key_points": "key points"}


def _status(count, key, config, uncertain=None):
    """'count | limit | status' cells. `uncertain` = why the count may be incomplete (shown instead of ✅).
    Never ✅ for a limit that was not checked; ✅* when the journal entry is unverified (D2)."""
    shown = "?" if count is None else (f"≥{count}" if uncertain else str(count))
    if not config.get("limits_checked"):
        return f"{shown} | — | ℹ️ not checked"
    limit = config["limits"].get(key)
    if limit is None:
        if key in config.get("no_limit_keys", ()):
            return f"{shown} | — | ℹ️ no fixed limit (template)"
        return f"{shown} | — | ℹ️ no limit in the library — check the journal's guidelines"
    if count is None:
        return f"{shown} | ≤{limit} | ❓ not counted — {uncertain or 'check manually'}"
    if count > limit:
        if key in config.get("soft_keys", ()):
            return f"{shown} | ≤{limit} | ℹ️ {count - limit} above the guidance value (not a hard limit)"
        return f"{shown} | ≤{limit} | ⚠️ 超出 {count - limit}"
    if uncertain:
        return f"{shown} | ≤{limit} | ❓ {uncertain}"
    return f"{shown} | ≤{limit} | " + ("✅" if config.get("verified", True) else "✅*")


def _figure_count(stats):
    """(count, uncertain reason, detail): the highest of distinct legend numbers, the highest figure
    number cited in the text, and embedded images."""
    legends, cited = stats["fig_numbers"], max(stats["fig_cited"], default=0)
    count = max(len(legends), cited, stats["fig_embedded"])
    detail = (f"legends: {len(legends)}, highest number cited: {cited or '—'}, "
              f"embedded images: {stats['fig_embedded']}")
    reason = None
    if stats["legends_unrecognised"] and not legends:
        reason = (f"{stats['legends_file'] or 'figure-legends.md'} has {stats['legends_unrecognised']} "
                  "block(s) but none starts with 'Figure N' — count the figures manually")
    return count, reason, detail


def _table_count(stats):
    cited = max(stats["table_cited"], default=0)
    count = max(stats["table_count"], len(stats["table_numbers"]), cited)
    detail = (f"Markdown tables: {stats['table_count']}, captions: {len(stats['table_numbers'])}, "
              f"highest number cited: {cited or '—'}")
    return count, None, detail


def _reference_count(stats):
    if not stats["ref_file"]:
        return None, "references.md not found"
    entries, loose = stats["ref_count"], stats["ref_unnumbered"]
    if not entries and loose:
        return loose, (f"references.md has {loose} paragraph(s) without numbers or bullets — counted "
                       "one per paragraph; check")
    if loose > 1:
        return entries, f"{loose} paragraph(s) in references.md are not numbered and were not counted"
    return entries, None


def _body_count(stats, config):
    """(words, counted labels, not-counted labels) per the limit's body_excludes (D1)."""
    w, lim = stats["words"], config["limits"]
    excludes = set(lim["body_excludes"] if lim.get("body_excludes") is not None else CONVENTIONAL_EXCLUDES)
    counted, total = [], 0
    for key in stats["body_keys"]:
        if key == "methods" and "methods" in excludes:
            continue
        counted.append(key)
        total += w.get(key, 0)
    extra = {"abstract": w.get("abstract", 0), "key_points": w.get("key-points", 0), "tables": stats["table_words"],
             "figure_legends": w.get("figure-legends", 0) + stats["legend_words"], "references": w.get("references", 0)}
    for part, n in extra.items():
        if part not in excludes and n:
            counted.append(_PART_LABELS[part])
            total += n
    not_counted = [_PART_LABELS[p] for p in BODY_PARTS if p in excludes and (p != "methods" or "methods" in w)]
    return total, counted, not_counted


def _conversion_notes(stats, supp_stats):
    """Report lines for unconverted citation keys, conversion warnings (tables, fences, joins) and
    notes on what was interpreted or left as text (subscripts, removed comments, footnotes, HTML …)."""
    supp = supp_stats or {}
    cites = list(stats.get("citations", [])) + [(k, f"supplementary: {loc}") for k, loc in supp.get("citations", [])]
    warns = list(stats.get("warnings", [])) + [f"supplementary: {w}" for w in supp.get("warnings", [])]
    lines = []
    if cites:
        by_key = {}
        for key, loc in cites:
            by_key.setdefault(key, []).append(loc)
        lines.append(f"- ⚠️ **Citation keys not converted ({len(by_key)}):** Pandoc citations such as `[@key]` "
                     "are kept as literal text — replace them with numbered references (pubmed-search Mode 6) "
                     "before submission")
        for key, locs in list(by_key.items())[:40]:
            more = f" (+{len(locs) - 3} more)" if len(locs) > 3 else ""
            lines.append(f"  - `@{key}` — {', '.join(locs[:3])}{more}")
        if len(by_key) > 40:
            lines.append(f"  - … and {len(by_key) - 40} more keys")
    lines += [f"- ⚠️ {w}" for w in warns[:40]]
    if len(warns) > 40:
        lines.append(f"- ⚠️ … and {len(warns) - 40} more")
    grouped = {}
    for icon, filename, ln, msg, example in list(stats.get("notes", [])) + list(supp.get("notes", [])):
        g = grouped.setdefault((icon, filename, msg), ([], []))
        if ln not in g[0]:
            g[0].append(ln)
        if example and example not in g[1]:
            g[1].append(example)
    for (icon, filename, msg), (lns, examples) in sorted(grouped.items(), key=lambda kv: kv[0][0] != "⚠️"):
        where = f"{filename}:{', '.join(map(str, lns[:8]))}" + (f" (+{len(lns) - 8} more)" if len(lns) > 8 else "")
        eg = f" (e.g. `{'`, `'.join(examples[:3])}`)" if examples else ""
        lines.append(f"- {icon} {where} — {msg}{eg}")
    return lines or ["- ✅ Nothing to note (no unconverted citation keys, table cell mismatches, unclosed code "
                     "fences, interpreted `~x~` subscripts, removed comments or unsupported Markdown)"]


def _numbering_text(config):
    page, line = config.get("page_numbers"), config.get("line_numbers")
    p = "no page numbers"
    if page:
        p = f"page numbers {'top' if page[0] == 'header' else 'bottom'} {'right' if page[1] == 'right' else 'centre'}"
    restart = {"newPage": "restart on each page", "newSection": "restart in each section"}
    ln = f"line numbers ({restart.get(line, 'continuous')})" if line else "no line numbers"
    return f"{p}, {ln} — {config.get('numbering_source', 'export default')}"


def generate_report(stats: dict, config: dict, output_path: str, supp_path=None, supp_stats=None,
                    supp_requested=False) -> str:
    w, lim = stats["words"], config["limits"]
    body, counted, not_counted = _body_count(stats, config)
    figs, fig_reason, fig_detail = _figure_count(stats)
    tabs, tab_reason, tab_detail = _table_count(stats)
    refs, ref_reason = _reference_count(stats)
    abstract = w.get("abstract")
    combined = lim.get("display_items") is not None or bool(config.get("combined"))
    body_cells = _status(body, "body_words", config)
    per_item = config.get("per_item_words")
    per_item_row, per_item_notes = None, []
    if per_item and config.get("limits_checked"):
        # "each table or figure counts as N words": the text alone within the limit is not a pass
        per_item_row = (f"| Body + {per_item} words per table / figure (template rule; {figs + tabs} tables / "
                        f"figures) | {_status(body + per_item * (figs + tabs), 'body_words', config, fig_reason)} |")
        if body_cells.endswith(("✅", "✅*")):
            body_cells = body_cells.rsplit("|", 1)[0] + "| ℹ️ text only — see the next row"
        if lim.get("body_words") is None:
            per_item_notes.append(
                f"the template counts each table / figure as {per_item} words against its word limit, but the "
                "library entry has no `body_words` — compare the 'Body + "
                f"{per_item} words per table / figure' count with the template's word_limit below")
    rows = [f"| Body ({' + '.join(counted) or '—'}) | {body_cells} |"] + ([per_item_row] if per_item_row else [])
    abstract_reason = None if abstract is not None else "abstract.md not found"
    rows += [f"| Abstract | {_status(abstract, 'abstract_words', config, abstract_reason)} |",
             f"| References (entries) | {_status(refs, 'references', config, ref_reason)} |"]
    if combined:
        rows.append(f"| Display items (figures {figs} + tables {tabs}; combined limit) | "
                    f"{_status(figs + tabs, 'display_items', config, fig_reason)} |")
    if not combined or lim.get("figures") is not None:
        rows.append(f"| Figures ({fig_detail}) | {_status(figs, 'figures', config, fig_reason)} |")
    if not combined or lim.get("tables") is not None:
        rows.append(f"| Tables ({tab_detail}) | {_status(tabs, 'tables', config, tab_reason)} |")
    if lim.get("pages") is not None and config.get("limits_checked"):
        rows.append(f"| Pages | — | ≤{lim['pages']} pages | ℹ️ not counted by this script — check the page "
                    "count of the formatted manuscript |")
    for s in ("title-page", "key-points", "research-in-context", "figure-legends"):
        if s in w:
            part = {"key-points": "key points", "figure-legends": "figure legends"}.get(s)
            rows.append(f"| {s} | {w[s]} | — | ℹ️ " + ("counted in Body |" if part in counted
                                                        else "not counted against the limit |"))
    if stats["legend_words"]:
        rows.append(f"| Figure legends inside body files | {stats['legend_words']} | — | ℹ️ "
                    + ("counted in Body |" if "figure legends" in counted else "not counted in Body |"))

    head = []
    if config.get("limits_checked") and not config.get("verified", True):
        head.append(f"- ⚠️ **Unverified journal entry:** {UNVERIFIED_WARNING}.")
    special = config.get("special_yaml") or []
    pending = [re.sub(r"^待核实\s*[:：]?\s*", "", str(s).strip())       # values the last check could not confirm;
               for s in (special if isinstance(special, list) else [special])   # their limits are null (JD-4)
               if str(s).strip().startswith("待核实")]
    if pending:
        head.append(f"- ⚠️ **Unconfirmed in the library (待核实):** {' | '.join(pending)} — confirm on the journal site.")
    if config.get("generic"):
        head.append(f"- ℹ️ {config['skip_reason']}")
    else:
        head.append(f"- **Article type:** {config.get('article_type', 'original').replace('_', ' ')}"
                    + (f" — limits from the {config['limits_source']}" if config.get("limits_source") else ""))
        if config.get("skip_reason"):
            head.append(f"- ℹ️ {config['skip_reason']}")
    rule = {"library": "as the entry's `body_excludes` says",
            "template text": "as the template text says",
            "convention": "usual convention — the library does not say which parts the limit covers; check the "
                          "journal's guidelines"}[config.get("body_rule", "convention")]
    if not config.get("limits_checked"):
        rule = "usual convention"
    notes = [f"- Body counts {', '.join(counted) or '—'}; not counted: {', '.join(not_counted) or '—'} ({rule})."]
    notes += [f"- ℹ️ Check manually — {n}" for n in list(config.get("limit_notes", [])) + per_item_notes]
    legend_nums = sorted(stats["fig_numbers"])
    if legend_nums and max(stats["fig_cited"], default=0) > max(legend_nums):
        notes.append(f"- ⚠️ The text cites Figure {max(stats['fig_cited'])}, but legends were found only for "
                     f"Figure {', '.join(map(str, legend_nums))} — add the missing legends")
    if stats["cjk_chars"]:
        notes.append(f"- ℹ️ CJK text: each Chinese / Japanese character counts as one word, punctuation not counted "
                     f"({stats['cjk_chars']} CJK characters); other text is counted in space-separated words. "
                     "Journals differ in how they count CJK text (some count punctuation) — check the journal's rule.")
    if config.get("limits_checked") and not config.get("verified", True):
        notes.append("- ✅* = within the library value, but this entry has not been checked against the journal's "
                     "current author guidelines")

    lines = [
        "# Manuscript Export Report", "",
        "## File",
        f"- **Output:** `{output_path}`",
        f"- **Journal:** {config.get('journal_name')} (`{config.get('journal_id')}`) — family: **{config.get('family')}**",
        f"- **Format:** {config['font']} {config['font_size']}pt, {config['line_spacing']}x spacing, "
        f"{config['margin_cm']} cm margins; {_numbering_text(config)}",
        f"- **Template data:** {config.get('data_as_of') or 'unknown vintage'}", "",
        "## Counts (body / abstract / references are counted separately)",
        *head, *([""] if head else []),
        "| Bucket | Count | Limit | Status |", "|---|---:|---:|---|",
        *rows,
        "",
        *notes,
    ]
    if not config.get("generic"):
        lines.append(f"- Raw limits from template: word_limit = {config.get('word_limit_raw')!r}; abstract = "
                     f"{config.get('abstract_raw')!r}; references = {config.get('ref_limit_raw')!r}; figures = "
                     f"{config.get('fig_limit_raw')!r}; tables = {config.get('table_limit_raw')!r}")
    lines += [
        "",
        "## Sections",
        f"- **Order ({config['family']} family):** {' → '.join(config['section_order'])}",
        f"- **Included:** {', '.join(stats['sections_included'])}",
    ]
    if stats["review_sections"]:
        lines.append(f"- ℹ️ Review sections exported after the Introduction (body text): "
                     f"{', '.join(stats['review_sections'])}")
    if stats["legends_file"]:
        lines.append(f"- Figure legends: `{stats['legends_file']}`")
    if stats["legends_note"]:
        lines.append(f"- {stats['legends_note']}")
    for s in stats["missing_required"]:
        lines.append(f"- ⚠️ **Missing:** `{SECTION_FILES[s]}` — expected by the {config['family']} family "
                     f"section order; it was skipped")
    if stats["missing_optional"]:
        lines.append(f"- ℹ️ Optional sections not present: {', '.join(stats['missing_optional'])}")
    if stats["not_exported"]:
        lines.append(f"- ℹ️ Files in the manuscript folder that are not part of this family's order "
                     f"(not exported): {', '.join(stats['not_exported'])}")
    if config.get("special_yaml"):
        lines += ["", "## Journal special requirements (from template — check manually)"]
        lines += [f"- {s}" for s in config["special_yaml"]]
    lines += ["", "## Placeholder warnings"]
    all_ph = list(stats["placeholders"]) + [f"supplementary: {p}" for p in (supp_stats or {}).get("placeholders", [])]
    lines += [f"- ⚠️ {p}" for p in all_ph[:40]] or ["- ✅ No placeholders detected"]
    if len(all_ph) > 40:
        lines.append(f"- ⚠️ … and {len(all_ph) - 40} more")
    lines += ["", "## Conversion notes", *_conversion_notes(stats, supp_stats)]
    lines += ["", "## Supplementary"]
    if supp_stats:
        lines.append(f"- ✅ `{supp_path}` written ({supp_stats['words'].get('supplementary', 0)} words, "
                     f"{supp_stats['table_count']} tables)")
    elif supp_requested:
        lines.append("- ⚠️ `--supplementary` requested but supplementary.md was not found")
    else:
        lines.append("- not requested (add `--supplementary` to export supplementary.md separately)")
    lines += [
        "", "## Notes",
        "- Word counts cover paragraphs, list items and quotes; headings, code blocks, table cells and legend / "
        "caption paragraphs (\"**Figure 1.** …\", \"Table 2. …\") are counted separately — treat them as "
        "approximate. Each CJK character counts as one word.",
        "- Figures = the highest of: distinct legend numbers (\"Figure N\" / \"Fig. N\" / \"图N\" at the start of a "
        "block), the highest figure number cited in the text, embedded `![...]()` images (outside comments and "
        "code). References = numbered, bulleted or \"[N]\" / \"(N)\" entries of references.md.",
        "- Consecutive lines form one paragraph (Markdown soft wrap; no space is added between CJK characters). "
        "Separate paragraphs with a blank line; end a line with two spaces or `\\` to keep a line break.",
        "- Figures are **not** embedded: `![...]()` lines are kept as text; upload final figure files separately.",
        "- Numbered items (`1. `) are written as literal text, not Word auto-numbering, so lists never chain; "
        "nested lists keep their level.",
        "- Unpaired `~`, `^`, `*` are kept verbatim; only closed pairs (`~x~`, `^x^`, `*x*`, `**x**`, `_x_`) "
        "are formatted, and a `~` right after a digit (ranges such as 18~65) is never a subscript. "
        "`[text](url)` becomes a hyperlink; fenced code blocks are copied verbatim.",
        "- Page breaks: after the title page, after the abstract, and before the references only.",
    ]
    return "\n".join(lines) + "\n"


# ─── Entry point ─────────────────────────────────────────────────────────────

def _is_earlier_output(path, flag):
    """Whether an existing file is an earlier export report (--report) or a .docx (other flags)."""
    try:
        if flag == "--report":
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                return f.readline().startswith("# Manuscript Export Report")
        with zipfile.ZipFile(path) as z:
            return "word/document.xml" in z.namelist()
    except (OSError, zipfile.BadZipFile):
        return False


def _input_files(manuscript_dir, *others):
    """Every file the export reads: the manuscript .md files (earlier reports excluded), a
    figure-legends.md outside the manuscript folder, the journal library and overrides."""
    files = [os.path.join(manuscript_dir, f) for f in os.listdir(manuscript_dir) if f.lower().endswith(".md")]
    files = [f for f in files if not _is_earlier_output(f, "--report")]
    legends, _ = find_legends_file(manuscript_dir)
    return files + ([legends] if legends else []) + [p for p in others if p and os.path.exists(p)]


def _check_outputs(outputs, inputs):
    """Refuse (exit 2) an output path that is one of the inputs, a directory, the same file as
    another output, a .docx output not ending in .docx, or an existing file that is not an
    earlier export (report / .docx)."""
    real_inputs = {os.path.realpath(p) for p in inputs}
    seen = {}
    for flag, path in outputs:
        real = os.path.realpath(path)
        if os.path.isdir(path):
            _fail(f"{flag} {path} is a directory")
        if real in real_inputs:
            _fail(f"{flag} {path} is one of the files the export reads — it would be overwritten; choose another path")
        if real in seen:
            _fail(f"{flag} and {seen[real]} name the same file ({path})")
        seen[real] = flag
        if flag != "--report" and not path.lower().endswith(".docx"):
            _fail(f"{flag} must be a .docx path, not {path}")
        if os.path.exists(path) and not _is_earlier_output(path, flag):
            _fail(f"{path} already exists and is not an earlier export "
                  f"{'report' if flag == '--report' else '.docx'} — choose another path or move it away")


class _Parser(argparse.ArgumentParser):
    def error(self, message):             # one line on stderr, exit 2 (argparse prints a usage block)
        _fail(f"{message} (see --help)")


def _article_type(value):
    v = value.strip().lower().replace("-", "_")
    if v not in ARTICLE_TYPES:
        raise argparse.ArgumentTypeError(f"invalid --article-type {value!r} (choose from {', '.join(ARTICLE_TYPES)})")
    return v


def _write_report(path, report):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
    except OSError as exc:
        _fail(f"cannot write the report {path}: {exc.strerror or exc}")
    print(f"Report saved to {path}")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = _Parser(description="MRP Manuscript Export (Markdown → journal-formatted .docx)")
    ap.add_argument("--manuscript-dir", required=True, help="Directory containing the section .md files")
    ap.add_argument("--journal", required=True,
                    help="Journal id from journal-templates.yaml / overrides; `generic` (or `none`) = "
                         "journal-neutral export without limit checks")
    ap.add_argument("--article-type", type=_article_type, default="original", metavar="TYPE",
                    help=f"{' / '.join(ARTICLE_TYPES)} (default: original). Other types use the entry's "
                         "limits_by_type; without one, numeric limits are not checked")
    ap.add_argument("--output", default="manuscript/manuscript.docx", help="Output .docx path")
    ap.add_argument("--yaml", default=str(DEFAULT_YAML), help="journal-templates.yaml (default: bundled)")
    ap.add_argument("--overrides", default=None,
                    help=f"Project-level overrides YAML, consulted first (default: ./{DEFAULT_OVERRIDES} "
                         "if it exists)")
    ap.add_argument("--report", default=None, help="Write the export report to this .md path")
    ap.add_argument("--supplementary", nargs="?", const="__default__", default=None,
                    help="Also export supplementary.md → supplementary.docx (optional: output .docx path)")
    ap.add_argument("--report-only", action="store_true",
                    help="Only compute the report (word counts, figures/tables, placeholders); write no .docx. "
                         "Used by pre-submission-verification Gate 6.")
    ap.add_argument("--no-page-numbers", action="store_true", help="Do not add page numbers")
    ap.add_argument("--no-line-numbers", action="store_true", help="Do not add line numbers")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.manuscript_dir):
        _fail(f"manuscript dir not found: {args.manuscript_dir}")
    if not os.path.isfile(args.yaml):
        _fail(f"journal-templates.yaml not found at {args.yaml} (pass --yaml)")
    if args.overrides and not os.path.exists(args.overrides):
        print(f"Warning: overrides file not found: {args.overrides}; using the library only", file=sys.stderr)
    overrides = args.overrides or DEFAULT_OVERRIDES

    config = get_journal_config(args.journal, args.yaml, overrides, args.article_type,
                                args.no_page_numbers, args.no_line_numbers)
    supp_path = None
    if args.supplementary is not None and not args.report_only:
        supp_path = (str(Path(args.output).parent / "supplementary.docx")
                     if args.supplementary == "__default__" else args.supplementary)
    outputs = ([] if args.report_only else [("--output", args.output)])
    outputs += ([("--supplementary", supp_path)] if supp_path else [])
    outputs += ([("--report", args.report)] if args.report else [])
    _check_outputs(outputs, _input_files(args.manuscript_dir, args.yaml, overrides))

    print(f"Exporting for: {config['journal_name']} [{config['family']} family]")
    print(f"Format: {config['font']} {config['font_size']}pt, {config['line_spacing']}x spacing")
    print(f"Section order: {' → '.join(config['section_order'])}")
    if config.get("limits_checked") and not config.get("verified", True):
        print(f"⚠️ {config['journal_name']}: {UNVERIFIED_WARNING}")

    try:
        if args.report_only:
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                stats = build_docx(args.manuscript_dir, config, os.path.join(tmpdir, "report-only.docx"))
            report = generate_report(stats, config, "(report-only — no .docx written)", None, None,
                                     supp_requested=False)
        else:
            stats = build_docx(args.manuscript_dir, config, args.output)
            supp_stats = export_supplementary(args.manuscript_dir, config, supp_path) if supp_path else None
            report = generate_report(stats, config, args.output, supp_path, supp_stats,
                                     supp_requested=args.supplementary is not None)
    except InputError as exc:
        _fail(str(exc))
    except OSError as exc:
        _fail(f"cannot write {exc.filename or args.output}: {exc.strerror or exc}")
    print(report)
    if args.report:
        _write_report(args.report, report)


if __name__ == "__main__":
    main()
