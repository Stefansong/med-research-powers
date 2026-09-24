#!/usr/bin/env python3
"""
MRP Manuscript Export: Markdown → .docx
========================================
Converts manuscript markdown files to journal-formatted .docx for submission.

Usage:
    python3 export_docx.py --manuscript-dir ./manuscript --journal nature --output manuscript/manuscript.docx
    python3 export_docx.py --manuscript-dir ./manuscript --journal european-urology \
        --report export-report.md --supplementary            # also writes manuscript/supplementary.docx

The journal id must exist in journal-templates.yaml (bundled with manuscript-writing,
located relative to this script) or in a project-level journal-overrides.yaml.
The `family` field of the template (lancet / jama / nature / ieee / standard) decides
section order and special elements; it is inferred from id/name if the field is absent.

Exit codes: 0 ok · 1 usage / missing files / missing dependency · 2 unknown journal id, or a
malformed overrides / library YAML (one "Error: ..." line, no traceback)

Requirements:
    pip install python-docx pyyaml
"""

import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path


def _missing(pkg, pip_name):
    sys.exit(f"缺少依赖 {pkg}（Missing dependency）。请先运行: pip install {pip_name}")


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
# Matched case-insensitively against the markdown source of every block (tables and code included).
PLACEHOLDER_MARKERS = ("[pending]", "[tbd]", "[todo]", "placeholder", "[insert",
                       "[待补", "[待填", "【待补", "【待填", "［待补", "［待填")
CODE_FONT = "Courier New"
LINK_COLOR = RGBColor(0x05, 0x63, 0xC1)


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


def _load_templates(path, required=False):
    """Return (data_as_of, entries) from a templates YAML.

    A missing file gives (None, []) unless required=True; an empty file means no entries.
    Raises TemplateFileError when the file cannot be read, is not valid YAML, or is not
    `templates:` + a list of mappings that each have an `id` (a bare top-level list of such
    mappings is also accepted) — same rules as manuscript-writing/scripts/get_journal_template.py."""
    if not path or not os.path.exists(path):
        if required:
            raise TemplateFileError(f"file not found: {path}")
        return None, []
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise TemplateFileError(f"cannot read {path}: {exc}") from None
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
        raise TemplateFileError(f"{path} is not valid YAML{where}: "
                                f"{getattr(exc, 'problem', None) or ' '.join(str(exc).split())}") from None
    if data is None:
        return None, []
    if isinstance(data, list):
        entries, data_as_of = data, None
    elif isinstance(data, dict):
        if "templates" not in data:
            raise TemplateFileError(f"{path} has no top-level `templates:` key "
                                    "(expected `templates:` followed by `- id: ...` entries)")
        entries, data_as_of = data["templates"] or [], data.get("data_as_of")
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
    return data_as_of, entries


def _fail(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(2)


def _first_int(value):
    m = re.search(r"\d[\d,]*", str(value or ""))
    return int(m.group(0).replace(",", "")) if m else None


# "no limit", "no hard limit", "no fixed word limit", "no strict …", "unlimited", "included in …"
_NO_LIMIT_RE = re.compile(r"unlimited|included in|\bno\s+strict\b|\bno(?:\s+[a-z-]+){0,2}\s+limits?\b")
# a page count: page / pages / pp / 页 right after the number or up to two words later ("8–10 printed pages")
_PAGE_UNIT_RE = re.compile(r"\s*(?:[^\W\d_]+[ \t-]+){0,2}?(?:pages?\b|pp\b|页)")


def _parse_limit(value):
    """'≤40, Vancouver' → 40; '150-250 words' → 250 (the upper bound);
    'unlimited' / 'no limit' / 'no hard limit (~25 per 1,000 words)' / a page limit
    ('8 pages', '≤10 pages', '8–10 printed pages') / None → None
    (a page count is not a word count, so it is not checked against words)."""
    s = str(value or "").lower()
    if not s or _NO_LIMIT_RE.search(s):
        return None
    m = re.search(r"(\d[\d,]*)\s*(?:-|–|—|to)\s*(\d[\d,]*)", s)
    unit = s[m.end():] if m else s[(re.search(r"\d[\d,]*", s) or re.search(r"$", s)).end():]
    if _PAGE_UNIT_RE.match(unit):
        return None
    if m:
        return int(m.group(2).replace(",", ""))
    return _first_int(s)


def get_journal_config(journal_id: str, yaml_path=None, overrides_path=None) -> dict:
    """Merge the family format with the journal's own limits from the YAML (overrides first).
    Exits with code 2 when the id is unknown or a template file is malformed."""
    try:
        _, overrides = _load_templates(overrides_path)
    except TemplateFileError as exc:
        _fail(f"overrides file: {exc}")
    try:
        data_as_of, library = _load_templates(yaml_path)
    except TemplateFileError as exc:
        _fail(f"journal library (--yaml): {exc}")
    entry = None
    for e in overrides + library:
        if str(e.get("id", "")).lower() == journal_id.lower():
            entry = e
            break
    if entry is None:
        print(f"❌ Journal id '{journal_id}' not found in {yaml_path}"
              + (f" or {overrides_path}" if overrides_path else "") + ".\n"
              "   Find the id with: python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/"
              f"get_journal_template.py --search {journal_id.split('-')[0]}\n"
              "   Journal not in the library? Add it to ./journal-overrides.yaml (same structure) "
              "and pass --overrides ./journal-overrides.yaml", file=sys.stderr)
        sys.exit(2)
    family = str(entry.get("family") or infer_family(entry.get("id", ""), entry.get("journal", ""))).lower()
    if family not in JOURNAL_FAMILIES:
        family = infer_family(entry.get("id", ""), entry.get("journal", ""))
    config = {k: (list(v) if isinstance(v, list) else v) for k, v in JOURNAL_FAMILIES[family].items()}
    config.update({
        "journal_id": entry.get("id", journal_id),
        "journal_name": entry.get("journal", journal_id),
        "family": family,
        "data_as_of": data_as_of,
        "word_limit_raw": entry.get("word_limit"),
        "word_limit": _parse_limit(entry.get("word_limit")),
        "word_limit_excludes_methods": "excluding methods" in str(entry.get("word_limit", "")).lower(),
        "abstract_raw": entry.get("abstract"),
        "abstract_limit": _parse_limit(re.sub(r"\d+\s*headings?", "", str(entry.get("abstract") or ""))),
        "ref_limit_raw": entry.get("references"),
        "ref_limit": _parse_limit(entry.get("references")),
        "fig_limit_raw": entry.get("figures"),
        "fig_limit": _parse_limit(entry.get("figures")),
        "fig_limit_combined": "combined" in str(entry.get("figures", "")).lower(),
        "table_limit_raw": entry.get("tables"),
        "table_limit": _parse_limit(entry.get("tables")),
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


def find_comment_placeholders(text: str):
    """Scan the RAW text (before comments are stripped) for <!-- PLACEHOLDER / TODO / TBD ... -->."""
    hits = []
    for ln, line in enumerate(text.split("\n"), 1):
        if re.search(r"<!--\s*(placeholder|todo|tbd|pending|待补|待填)", line, re.IGNORECASE):
            hits.append((ln, line.strip()[:90]))
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


def strip_html_comments(text: str) -> str:
    """Remove <!-- ... --> but keep line numbers stable (newlines inside comments are preserved).
    Fenced code blocks are left untouched; an unclosed <!-- is left as text."""
    out, region, fence, inside = [], [], None, False

    def flush():
        if region:
            out.append(re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"),
                              "\n".join(region), flags=re.DOTALL))
            region.clear()

    for line in text.split("\n"):
        if fence is None:
            m = None if inside else _fence_open(line)
            if m is None:
                region.append(line)
                inside = _comment_open_after(line, inside)
                continue
            flush()
            fence = m.group(2)
        elif _fence_closes(line, fence):
            fence = None
        out.append(line)
    flush()
    return "\n".join(out)


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


def _parse_paragraph(lines, i, elements, indent_level=0):
    src, j = [(i + 1, lines[i])], i + 1
    while j < len(lines) and lines[j].strip():
        if not indent_level and _SETEXT_RE.match(lines[j]):          # Title \n ===  /  Title \n ---
            level = 1 if lines[j].strip()[0] == "=" else 2
            elements.append({"type": "heading", "level": level, "line": i + 1, "src": src})
            return j + 1
        if _interrupts_paragraph(lines, j):
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


def parse_markdown(text: str):
    """Turn markdown into a list of block dicts, each with a 1-based `line` and `src` =
    [(line, source text)] (used for placeholder / citation scanning). Types:
    heading(level, text) · paragraph(text[, indent_level]) · bullet / numbered(level, text[, number,
    delim]) · quote(text) · code(lines, lang) · rule · table(headers, rows, row_lines, aligns).
    Blocks may carry `warnings` = [(line, message)] for the export report."""
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
            i = _parse_paragraph(lines, i, elements)
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

_ESCAPABLE = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
_SUP_RE = re.compile(r"\^([^\s^]+?)\^")                  # ^superscript^ (no spaces inside)
_SUB_RE = re.compile(r"~([^\s~]+?)~")                    # ~subscript~ (no spaces inside)
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


def _tokenize(s, cites):
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
                    nodes.append({"t": "link", "url": dest[0], "c": _inline_tree(s[i + 1:close], None)})
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
                nodes.append({"t": "strike", "c": _inline_tree(m.group(1), cites)})
                i = m.end()
                continue
            m = _SUB_RE.match(s, i)
            if m:
                flush()
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


def _inline_tree(text, cites):
    return _resolve_emphasis(_tokenize(text, cites))


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


# ─── Document builder ────────────────────────────────────────────────────────

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
    return {"words": {}, "ref_count": 0, "fig_legends": 0, "fig_embedded": 0, "table_count": 0,
            "placeholders": [], "warnings": [], "citations": [], "sections_included": [],
            "missing_required": [], "missing_optional": [], "not_exported": []}


def _render_elements(doc, elements, config, section_id, filename, stats):
    """Write parsed elements into `doc`; update word / table / placeholder / citation stats."""
    words = 0
    for el in elements:
        kind = el["type"]
        scan = list(el.get("src", [(el["line"], el.get("text", ""))]))  # (line, source) for placeholders
        if kind == "heading":
            add_formatted_text(_add_heading(doc, el["level"]), el["text"], config)
        elif kind == "paragraph":
            style = _styled(doc, "List Continue", el["indent_level"] - 1) if el.get("indent_level") else None
            add_formatted_text(doc.add_paragraph(style=style), el["text"], config)
            words += len(plain_text(el["text"]).split())
        elif kind == "bullet":
            add_formatted_text(doc.add_paragraph(style=_styled(doc, "List Bullet", el["level"])),
                               el["text"], config)
            words += len(plain_text(el["text"]).split())
        elif kind == "numbered":
            # Literal "N. text" — no Word auto-numbering, so references and body lists never chain.
            p = doc.add_paragraph(style=_styled(doc, "List Number", el["level"]))
            _insert_ppr_child(p, parse_xml(f'<w:numPr {nsdecls("w")}><w:ilvl w:val="0"/>'
                                           '<w:numId w:val="0"/></w:numPr>'))   # numbering off
            p.paragraph_format.left_indent = Cm(0.75 * (el["level"] + 1))
            p.paragraph_format.first_line_indent = Cm(-0.75)
            add_formatted_text(p, f"{el['number']}{el.get('delim', '.')} {el['text']}", config)
            words += len(plain_text(el["text"]).split())
            if section_id == "references" and el["level"] == 0:
                stats["ref_count"] += 1
        elif kind == "quote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.27)
            add_formatted_text(p, el["text"], config, base_italic=True)
            words += len(plain_text(el["text"]).split())
        elif kind == "code":
            _add_code_block(doc, el["lines"], config)   # verbatim, not counted as words
        elif kind == "rule":
            _add_rule(doc)
        elif kind == "table":
            _add_table(doc, el["headers"], el["rows"], config, el.get("aligns"))
            stats["table_count"] += 1
            scan = [(el["line"], " | ".join(el["headers"]))]
            scan += [(ln, " | ".join(row)) for ln, row in zip(el["row_lines"], el["rows"])]
        for ln, t in scan:
            if any(mk in t.lower() for mk in PLACEHOLDER_MARKERS):
                stats["placeholders"].append(f"{filename}:{ln} — {t.strip()[:80]}")
            if kind != "code":
                stats["citations"] += [(key, f"{filename}:{ln}") for key in citation_keys(t)]
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


def _read_section(manuscript_dir, section_id, stats):
    """Read one section file; returns (raw_text, elements) and records comment placeholders."""
    filename = SECTION_FILES[section_id]
    path = os.path.join(manuscript_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    for ln, snippet in find_comment_placeholders(raw):
        stats["placeholders"].append(f"{filename}:{ln} — {snippet}")
    return raw, parse_markdown(strip_html_comments(raw))


def count_figures(raw_text: str):
    """(set of legend numbers from '**Figure N.**' / '**Fig. N**', number of embedded images '![')."""
    legends = set(re.findall(r"\*\*\s*Fig(?:ure|\.)?\s*(\d+)\s*[.:]?\s*\*\*", raw_text, re.IGNORECASE))
    return legends, raw_text.count("![")


def build_docx(manuscript_dir: str, config: dict, output_path: str) -> dict:
    """Build the main .docx following the family section order. Returns stats."""
    stats = _new_stats()
    doc = _new_document(config)
    prev, legend_numbers = None, set()
    for section_id in config["section_order"]:
        filename = SECTION_FILES.get(section_id)
        if not filename or not os.path.exists(os.path.join(manuscript_dir, filename)):
            (stats["missing_optional"] if section_id in OPTIONAL_SECTIONS
             else stats["missing_required"]).append(section_id)
            continue
        # Page breaks only after title page / abstract and before references.
        if prev in ("title-page", "abstract") or (section_id == "references" and prev is not None):
            doc.add_page_break()
        raw, elements = _read_section(manuscript_dir, section_id, stats)
        if section_id in SECTION_TITLES and not any(e["type"] == "heading" for e in elements):
            doc.add_heading(SECTION_TITLES[section_id], level=1)
        _render_elements(doc, elements, config, section_id, filename, stats)
        if section_id != "references":
            legends, embedded = count_figures(raw)
            legend_numbers |= legends  # the same figure may be captioned in results.md and figure-legends.md
            stats["fig_embedded"] += embedded
        stats["sections_included"].append(section_id)
        prev = section_id
    stats["fig_legends"] = len(legend_numbers)
    if not stats["sections_included"]:
        sys.exit(f"❌ No manuscript sections found in {manuscript_dir} "
                 f"(expected files like {', '.join(SECTION_FILES[s] for s in config['section_order'][:4])} ...)")
    used = {SECTION_FILES[s] for s in config["section_order"]} | {"supplementary.md"}
    stats["not_exported"] = sorted(f for f in os.listdir(manuscript_dir) if f.endswith(".md") and f not in used)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return stats


def export_supplementary(manuscript_dir: str, config: dict, output_path: str):
    """Export supplementary.md as its own .docx (same family formatting). Returns stats or None."""
    if not os.path.exists(os.path.join(manuscript_dir, "supplementary.md")):
        return None
    stats = _new_stats()
    doc = _new_document(config)
    raw, elements = _read_section(manuscript_dir, "supplementary", stats)
    _render_elements(doc, elements, config, "supplementary", "supplementary.md", stats)
    legends, stats["fig_embedded"] = count_figures(raw)
    stats["fig_legends"] = len(legends)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return stats


# ─── Report ──────────────────────────────────────────────────────────────────

def _status(count, limit):
    if limit is None:
        return f"{count} | — | ℹ️ no limit stated"
    return f"{count} | ≤{limit} | " + ("✅" if count <= limit else f"⚠️ 超出 {count - limit}")


def _conversion_notes(stats, supp_stats):
    """Report lines for unconverted citation keys and conversion warnings (tables, fences, joins)."""
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
    return lines or ["- ✅ Nothing to note (no unconverted citation keys, table cell mismatches or unclosed "
                     "code fences)"]


def generate_report(stats: dict, config: dict, output_path: str, supp_path=None, supp_stats=None,
                    supp_requested=False) -> str:
    w = stats["words"]
    body_secs = [s for s in BODY_SECTIONS if s in w]
    body = sum(w[s] for s in body_secs)
    body_label = " + ".join(body_secs) if body_secs else "—"
    if config.get("word_limit_excludes_methods") and "methods" in w:
        body -= w["methods"]
        body_label += " (Methods excluded, as the limit says)"
    figs = max(stats["fig_legends"], stats["fig_embedded"])
    fig_note = f"legends: {stats['fig_legends']}, embedded images: {stats['fig_embedded']}"
    if config.get("fig_limit_combined"):
        fig_row = f"| Figures + tables (combined limit) | {_status(figs + stats['table_count'], config['fig_limit'])} |"
    else:
        fig_row = (f"| Figures ({fig_note}) | {_status(figs, config['fig_limit'])} |\n"
                   f"| Tables | {_status(stats['table_count'], config['table_limit'])} |")
    other = [s for s in ("title-page", "key-points", "research-in-context", "figure-legends") if s in w]
    other_rows = "\n".join(f"| {s} | {w[s]} | — | ℹ️ not counted against the limit |" for s in other)

    lines = [
        "# Manuscript Export Report", "",
        "## File",
        f"- **Output:** `{output_path}`",
        f"- **Journal:** {config.get('journal_name')} (`{config.get('journal_id')}`) — family: **{config.get('family')}**",
        f"- **Format:** {config['font']} {config['font_size']}pt, {config['line_spacing']}x spacing, "
        f"{config['margin_cm']} cm margins",
        f"- **Template data:** {config.get('data_as_of') or 'unknown vintage'}", "",
        "## Counts (body / abstract / references are counted separately)",
        "| Bucket | Count | Limit | Status |", "|---|---:|---:|---|",
        f"| Body ({body_label}) | {_status(body, config['word_limit'])} |",
        f"| Abstract | {_status(w.get('abstract', 0), config['abstract_limit'])} |",
        f"| References (numbered entries) | {_status(stats['ref_count'], config['ref_limit'])} |",
        fig_row,
        *([other_rows] if other_rows else []),
        "",
        f"- Raw limits from template: word_limit = {config.get('word_limit_raw')!r}; abstract = "
        f"{config.get('abstract_raw')!r}; references = {config.get('ref_limit_raw')!r}; figures = "
        f"{config.get('fig_limit_raw')!r}; tables = {config.get('table_limit_raw')!r}", "",
        "## Sections",
        f"- **Order ({config['family']} family):** {' → '.join(config['section_order'])}",
        f"- **Included:** {', '.join(stats['sections_included'])}",
    ]
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
        "- Word counts cover paragraphs, list items and quotes; headings, table cells and code blocks are "
        "excluded — treat them as approximate.",
        "- Consecutive lines form one paragraph (Markdown soft wrap; no space is added between CJK characters). "
        "Separate paragraphs with a blank line; end a line with two spaces or `\\` to keep a line break.",
        "- Figures are **not** embedded: `![...]()` lines are kept as text; upload final figure files separately.",
        "- Numbered items (`1. `) are written as literal text, not Word auto-numbering, so lists never chain; "
        "nested lists keep their level.",
        "- Unpaired `~`, `^`, `*` are kept verbatim; only closed pairs (`~x~`, `^x^`, `*x*`, `**x**`, `_x_`) "
        "are formatted. `[text](url)` becomes a hyperlink; fenced code blocks are copied verbatim.",
        "- Page breaks: after the title page, after the abstract, and before the references only.",
    ]
    return "\n".join(lines) + "\n"


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="MRP Manuscript Export (Markdown → journal-formatted .docx)")
    ap.add_argument("--manuscript-dir", required=True, help="Directory containing the section .md files")
    ap.add_argument("--journal", required=True, help="Journal id from journal-templates.yaml / overrides")
    ap.add_argument("--output", default="manuscript/manuscript.docx", help="Output .docx path")
    ap.add_argument("--yaml", default=str(DEFAULT_YAML), help="journal-templates.yaml (default: bundled)")
    ap.add_argument("--overrides", default=None,
                    help=f"Project-level overrides YAML, consulted first (default: ./{DEFAULT_OVERRIDES} "
                         "if it exists)")
    ap.add_argument("--report", default=None, help="Write the export report to this .md path")
    ap.add_argument("--supplementary", nargs="?", const="__default__", default=None,
                    help="Also export supplementary.md → supplementary.docx (optional: output path)")
    ap.add_argument("--report-only", action="store_true",
                    help="Only compute the report (word counts, figures/tables, placeholders); write no .docx. "
                         "Used by pre-submission-verification Gate 6.")
    args = ap.parse_args()

    if not os.path.isdir(args.manuscript_dir):
        sys.exit(f"❌ manuscript dir not found: {args.manuscript_dir}")
    if not os.path.exists(args.yaml):
        sys.exit(f"❌ journal-templates.yaml not found at {args.yaml} (pass --yaml)")
    if args.overrides and not os.path.exists(args.overrides):
        print(f"Warning: overrides file not found: {args.overrides}; using the library only", file=sys.stderr)

    config = get_journal_config(args.journal, args.yaml, args.overrides or DEFAULT_OVERRIDES)
    print(f"Exporting for: {config['journal_name']} [{config['family']} family]")
    print(f"Format: {config['font']} {config['font_size']}pt, {config['line_spacing']}x spacing")
    print(f"Section order: {' → '.join(config['section_order'])}")

    if args.report_only:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = build_docx(args.manuscript_dir, config, os.path.join(tmpdir, "report-only.docx"))
        report = generate_report(stats, config, "(report-only — no .docx written)", None, None,
                                 supp_requested=False)
        print(report)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to {args.report}")
        return

    stats = build_docx(args.manuscript_dir, config, args.output)

    supp_path = supp_stats = None
    if args.supplementary is not None:
        supp_path = (str(Path(args.output).parent / "supplementary.docx")
                     if args.supplementary == "__default__" else args.supplementary)
        supp_stats = export_supplementary(args.manuscript_dir, config, supp_path)

    report = generate_report(stats, config, args.output, supp_path, supp_stats,
                             supp_requested=args.supplementary is not None)
    print(report)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {args.report}")


if __name__ == "__main__":
    main()
