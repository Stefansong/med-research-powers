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

Exit codes: 0 ok · 1 usage / missing files / missing dependency · 2 unknown journal id

Requirements:
    pip install python-docx pyyaml
"""

import argparse
import os
import re
import sys
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
    from docx.oxml.ns import qn, nsdecls
    from docx.oxml import parse_xml
except ImportError:  # pragma: no cover
    _missing("python-docx", "python-docx")


HERE = Path(__file__).resolve().parent
DEFAULT_YAML = HERE.parent.parent / "manuscript-writing" / "references" / "journal-templates.yaml"

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
PLACEHOLDER_MARKERS = ("[pending]", "[tbd]", "[todo]", "placeholder", "[insert", "[待补充]", "[待填")


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


def _load_templates(path):
    """Return (data_as_of, entries) from a templates YAML; ([] if the file does not exist)."""
    if not path or not os.path.exists(path):
        return None, []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if isinstance(data, list):
        return None, data
    return data.get("data_as_of"), data.get("templates") or []


def _first_int(value):
    m = re.search(r"\d[\d,]*", str(value or ""))
    return int(m.group(0).replace(",", "")) if m else None


def _parse_limit(value):
    """'≤40, Vancouver' → 40; 'unlimited' / 'no limit' / None → None."""
    s = str(value or "").lower()
    if not s or "unlimited" in s or "no limit" in s or "no strict" in s or "included in" in s:
        return None
    return _first_int(s)


def get_journal_config(journal_id: str, yaml_path=None, overrides_path=None) -> dict:
    """Merge the family format with the journal's own limits from the YAML (overrides first).
    Exits with code 2 when the id is unknown."""
    _, overrides = _load_templates(overrides_path)
    data_as_of, library = _load_templates(yaml_path)
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


# ─── Markdown parsing ────────────────────────────────────────────────────────

def find_comment_placeholders(text: str):
    """Scan the RAW text (before comments are stripped) for <!-- PLACEHOLDER / TODO / TBD ... -->."""
    hits = []
    for ln, line in enumerate(text.split("\n"), 1):
        if re.search(r"<!--\s*(placeholder|todo|tbd|pending|待补充)", line, re.IGNORECASE):
            hits.append((ln, line.strip()[:90]))
    return hits


def strip_html_comments(text: str) -> str:
    """Remove <!-- ... --> but keep line numbers stable (newlines inside comments are preserved)."""
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)


def parse_markdown(text: str):
    """Turn markdown into a list of element dicts (with 1-based `line`). Table rows are grouped;
    every other non-blank line is one element (one line = one paragraph)."""
    elements, table = [], None

    def flush_table():
        nonlocal table
        if table is not None:
            elements.append(table)
            table = None

    for ln, raw in enumerate(text.split("\n"), 1):
        s = raw.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue  # separator row
            if table is None:
                table = {"type": "table", "line": ln, "headers": cells, "rows": [], "row_lines": []}
            else:
                table["rows"].append(cells)
                table["row_lines"].append(ln)
            continue
        flush_table()
        if not s:
            continue
        if (m := re.match(r"^(#{1,3})\s+(.*)", s)):
            elements.append({"type": "heading", "level": len(m.group(1)), "text": m.group(2), "line": ln})
        elif re.match(r"^[-*+]\s+", s):
            elements.append({"type": "bullet", "text": re.sub(r"^[-*+]\s+", "", s), "line": ln})
        elif (m := re.match(r"^(\d+)[.)]\s+(.*)", s)):
            elements.append({"type": "numbered", "number": m.group(1), "text": m.group(2), "line": ln})
        elif s.startswith(">"):
            elements.append({"type": "quote", "text": s.lstrip("> "), "line": ln})
        else:
            elements.append({"type": "paragraph", "text": s, "line": ln})
    flush_table()
    return elements


# Only CLOSED, non-empty markers are formatting; a lone ~ ^ * is ordinary text ("~90%", "2^10").
INLINE_RE = re.compile(
    r"\*\*(?P<b>[^\s*](?:[^*]*?[^\s*])?)\*\*"     # **bold**
    r"|\*(?P<i>[^\s*](?:[^*]*?[^\s*])?)\*"        # *italic*
    r"|\^(?P<sup>[^\s^]+?)\^"                      # ^superscript^ (no spaces inside)
    r"|~(?P<sub>[^\s~]+?)~"                        # ~subscript~ (no spaces inside)
)


def add_formatted_text(paragraph, text: str, config: dict, base_bold=False, base_italic=False, size=None):
    """Add text with inline markdown formatting; unmatched markers are written verbatim."""
    def add_run(chunk, bold=False, italic=False, sup=False, sub=False):
        if not chunk:
            return
        run = paragraph.add_run(chunk)
        run.font.name = config["font"]
        if size:
            run.font.size = Pt(size)
        run.bold = bold or base_bold or None
        run.italic = italic or base_italic or None
        if sup:
            run.font.superscript = True
        if sub:
            run.font.subscript = True

    pos = 0
    for m in INLINE_RE.finditer(text):
        add_run(text[pos:m.start()])
        if m.group("b") is not None:
            add_run(m.group("b"), bold=True)
        elif m.group("i") is not None:
            add_run(m.group("i"), italic=True)
        elif m.group("sup") is not None:
            add_run(m.group("sup"), sup=True)
        else:
            add_run(m.group("sub"), sub=True)
        pos = m.end()
    add_run(text[pos:])


def plain_text(text: str) -> str:
    """Text as it will appear in the .docx (markers of closed spans removed)."""
    return INLINE_RE.sub(lambda m: next(g for g in m.groups() if g is not None), text)


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
    for level in (1, 2, 3):
        h = doc.styles[f"Heading {level}"]
        _set_style_font(h, config["font"])
        h.font.size = Pt(config.get(f"heading{level}_size", 12))
        h.font.bold = True
        h.font.color.rgb = RGBColor(0, 0, 0)
    return doc


def _render_elements(doc, elements, config, section_id, filename, stats):
    """Write parsed elements into `doc`; update word / table / placeholder stats."""
    words = 0
    for el in elements:
        texts = [(el["line"], el.get("text", ""))]  # (line, visible text) pairs scanned for placeholders
        if el["type"] == "heading":
            h = doc.add_heading("", level=el["level"])
            add_formatted_text(h, el["text"], config)
        elif el["type"] == "paragraph":
            add_formatted_text(doc.add_paragraph(), el["text"], config)
            words += len(plain_text(el["text"]).split())
        elif el["type"] == "bullet":
            add_formatted_text(doc.add_paragraph(style="List Bullet"), el["text"], config)
            words += len(plain_text(el["text"]).split())
        elif el["type"] == "numbered":
            # Literal "N. text" — no Word auto-numbering, so references and body lists never chain.
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.first_line_indent = Cm(-0.75)
            add_formatted_text(p, f"{el['number']}. {el['text']}", config)
            words += len(plain_text(el["text"]).split())
            if section_id == "references":
                stats["ref_count"] += 1
        elif el["type"] == "quote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.27)
            add_formatted_text(p, el["text"], config, base_italic=True)
            words += len(plain_text(el["text"]).split())
        elif el["type"] == "table":
            _add_table(doc, el["headers"], el["rows"], config)
            stats["table_count"] += 1
            texts = [(el["line"], " | ".join(el["headers"]))]
            texts += [(ln, " | ".join(row)) for ln, row in zip(el["row_lines"], el["rows"])]
        for ln, t in texts:
            if any(mk in t.lower() for mk in PLACEHOLDER_MARKERS):
                stats["placeholders"].append(f"{filename}:{ln} — {t[:80]}")
    stats["words"][section_id] = stats["words"].get(section_id, 0) + words


def _add_table(doc, headers, rows, config):
    if not headers:
        return
    n_cols = len(headers)
    table = doc.add_table(rows=1 + len(rows), cols=n_cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    size = config["font_size"] - 1
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        add_formatted_text(cell.paragraphs[0], header, config, base_bold=True, size=size)
        set_cell_shading(cell, "D9D9D9")
    for r, row in enumerate(rows):
        for c in range(min(len(row), n_cols)):
            add_formatted_text(table.rows[r + 1].cells[c].paragraphs[0], row[c], config, size=size)
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
    stats = {"words": {}, "ref_count": 0, "fig_legends": 0, "fig_embedded": 0, "table_count": 0,
             "placeholders": [], "sections_included": [], "missing_required": [], "missing_optional": [],
             "not_exported": []}
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
    stats = {"words": {}, "ref_count": 0, "table_count": 0, "placeholders": []}
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
        "- Word counts cover paragraphs, list items and quotes; headings and table cells are excluded — "
        "treat them as approximate.",
        "- Figures are **not** embedded: `![...]()` lines are kept as text; upload final figure files separately.",
        "- Numbered items (`1. `) are written as literal text, not Word auto-numbering, so lists never chain.",
        "- Unpaired `~`, `^`, `*` are kept verbatim; only closed pairs (`~x~`, `^x^`, `*x*`, `**x**`) are formatted.",
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
    ap.add_argument("--overrides", default="journal-overrides.yaml",
                    help="Project-level overrides YAML, consulted first (default: ./journal-overrides.yaml)")
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

    config = get_journal_config(args.journal, args.yaml, args.overrides)
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
