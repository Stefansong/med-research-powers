#!/usr/bin/env python3
"""
MRP repository consistency guard.

Run from anywhere:  python tools/check_consistency.py
Exit 1 and list every problem if anything is inconsistent; otherwise print one
summary line.  CHANGELOG.md is exempt from every check (it is history).

What it locks down (each block below is one lettered check):
  (a) one version string everywhere it is stated; no stray x.y.z anywhere else
  (b) every count the docs state (skills / commands / journals / standards /
      checklists / scripts, journals with IF_year, journals with guidelines_checked)
      equals the number counted in the repo right now — nothing is hard-coded here,
      so adding a journal or a standard only fails until the docs are updated; the
      totals written in reference and data files (standards-index.yaml header, the
      journal library summary) are checked too
  (c) plugin name is `mrp`; no `/med-research-powers:` prefix; every `/mrp:x`
      names a real command or skill
  (d) no command file shares its name with a skill directory
  (e) no `sys.path.insert(0, 'scripts')`-style paths; bundled scripts are always
      referenced through ${CLAUDE_PLUGIN_ROOT}; every ${CLAUDE_PLUGIN_ROOT}/...
      path exists
  (f) SKILL.md frontmatter: name == directory, description starts "Use when"
      and <= 200 chars, file <= 500 lines, referenced references/ and scripts/
      paths exist
  (g) README.md and README_CN.md have the same number of H1/H2 headings and
      tables
  (h) relative links in README / README_CN / docs / CONTRIBUTING / SECURITY
      point at files that exist, and #anchors point at headings that exist
  (i) no stale CONSORT counts ("31 numbered items", "34 rows", "42+", ...)
  (j) every skill has at least one eval case that expects it to be invoked, and
      the case / tag counts in evals/README.md are real
  (k) GitHub workflows: third-party actions pinned to a commit SHA, the Claude Code
      CLI installed at an exact version, secrets only in the env of the step that
      uses them, no continue-on-error
  (+) manifest hygiene, command frontmatter, bundled-script table, checkpoint
      count, profile path, no examples/showcase references
"""

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError:  # pragma: no cover
    print("❌ PyYAML is required: pip install pyyaml  (or pip install -r requirements.txt)")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# ── Fixed facts (everything else is counted from the repo in (b)) ────────────
EXPECTED = {
    "checkpoints": 3,          # mandatory (hard) checkpoints: protocol / SAP / pre-submission
    "consort_items": 30,       # CONSORT 2025 — 30 items (42 rows incl. sub-items)
}
PLUGIN_NAME = "mrp"
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache", "results"}  # evals/results is git-ignored run output
# CHANGELOG is history; this guard and the tests quote the very strings they hunt for.
EXEMPT_FILES = {"CHANGELOG.md", "check_consistency.py"}
LITERAL_SCAN_SKIP_DIRS = {"tests"}
TEXT_EXTS = {".md", ".sh", ".yaml", ".yml", ".json", ".py", ".txt"}

errors = []


def err(msg):
    errors.append(msg)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def text_files(roots=(".",), exts=TEXT_EXTS, skip_dirs=()):
    """Yield every tracked-looking text file under the given roots."""
    skip = SKIP_DIRS | set(skip_dirs)
    for root in roots:
        base = ROOT / root
        if base.is_file():
            if base.suffix in exts and base.name not in EXEMPT_FILES:
                yield base
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix not in exts:
                continue
            if any(part in skip for part in p.relative_to(ROOT).parts):
                continue
            if p.name in EXEMPT_FILES:
                continue
            yield p


def strip_fences(text):
    """Remove fenced code blocks so headings/tables inside them are not counted."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def frontmatter(text):
    """Return (frontmatter dict, body) for a Markdown file with YAML frontmatter."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return None, text
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return {"__error__": str(e)}, m.group(2)
    return data, m.group(2)


# ── Manifests ────────────────────────────────────────────────────────────────
plugin = json.loads(read(".claude-plugin/plugin.json"))
marketplace = json.loads(read(".claude-plugin/marketplace.json"))
VERSION = plugin["version"]

# ── (a) Version ──────────────────────────────────────────────────────────────
version_sites = [
    ("README.md",              r"Version\s+v?(\d+\.\d+\.\d+)"),
    ("README_CN.md",           r"版本\s+v?(\d+\.\d+\.\d+)"),
    ("install.sh",             r"MRP_VERSION=\"(\d+\.\d+\.\d+)\""),
    ("hooks/session-start.sh", r"v(\d+\.\d+\.\d+)"),
    ("docs/architecture.md",   r"v(\d+\.\d+\.\d+)"),
    ("docs/USER-MANUAL.md",    r"版本[^\n]*?v?(\d+\.\d+\.\d+)"),
]
for key, found in (("marketplace.metadata.version", marketplace.get("metadata", {}).get("version")),
                   ("marketplace.plugins[0].version", marketplace["plugins"][0].get("version"))):
    if found != VERSION:
        err(f"(a) version mismatch: {key} = {found!r}, plugin.json = {VERSION!r}")
for path, pat in version_sites:
    m = re.search(pat, read(path))
    found = m.group(1) if m else None
    if found != VERSION:
        err(f"(a) version mismatch in {path}: found {found!r}, expected {VERSION!r}")

# No other x.y.z anywhere (tool versions like "Python 3.11.2" are tolerated, and so are
# pinned dependencies: "ruff==0.16.9", "numpy>=1.23.5", "@anthropic-ai/claude-code@2.1.308" and a GitHub
# Action pinned to a commit with its tag in the comment, "actions/checkout@<sha>  # v7.0.1").
TOOL_VERSION_CONTEXT = re.compile(
    r"(?:python|node|npm|pip|numpy|pandas|scipy|statsmodels|matplotlib|docx|openpyxl|pyyaml|pytest|ruff|"
    r"shellcheck|claude code|claude|r|spss|stata|sas|tensorflow|torch|pytorch|sklearn|scikit-learn)"
    r"\s*(?:v|[<>=~!]=?|==)?\s*\d+\.\d+\.\d+"
    r"|@[\w-]+/[\w.-]+@\d+\.\d+\.\d+"
    r"|^\s*-?\s*uses:\s*[\w.-]+/[\w./-]+@[0-9a-f]{40}\s+#\s*v\d+\.\d+\.\d+\s*$",
    re.IGNORECASE)
DOI_OR_URL = re.compile(r"10\.\d{4,9}/\S+|https?://\S+")
# Section numbers in cited guidance ("Cochrane Handbook §10.10.4.4", "section 2.3.1") are not versions.
SECTION_REF = re.compile(r"(?:§|[Ss]ection\s*|第\s*)\d+(?:\.\d+)+")
for p in text_files(skip_dirs=LITERAL_SCAN_SKIP_DIRS):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        scan = SECTION_REF.sub(" ", DOI_OR_URL.sub(" ", line))   # DOIs, URLs, section numbers are not versions
        for stray in re.findall(r"\bv?(\d+\.\d+\.\d+)\b", scan):
            if stray != VERSION and not TOOL_VERSION_CONTEXT.search(scan):
                err(f"(a) stray version {stray!r} in {rel(p)}:{ln} (expected only {VERSION!r})")

# ── (b) Counts in the repo, and every number the docs state ──────────────────
skill_dirs = sorted(d.name for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").is_file())
command_files = sorted(p.stem for p in (ROOT / "commands").glob("*.md"))
script_files = sorted(p for p in (ROOT / "skills").glob("*/scripts/*.py"))

journals_data = yaml.safe_load(read("skills/manuscript-writing/references/journal-templates.yaml"))
standards_data = yaml.safe_load(read("skills/reporting-standards/references/checklists/standards-index.yaml"))
journal_entries = [j for j in journals_data["templates"] if isinstance(j, dict)]


def has_value(entry, key):
    v = entry.get(key)
    return v is not None and str(v).strip() != ""


standard_entries = [s for s in standards_data["standards"] if isinstance(s, dict)]
actual = {
    "skills": len(skill_dirs),
    "commands": len(command_files),
    "journals": len(journals_data["templates"]),
    "standards": len(standards_data["standards"]),
    "checklists": sum(has_value(s, "file") for s in standard_entries),   # standards with a checklist YAML
    "scripts": len(script_files),
    "if_year": sum(has_value(j, "IF_year") for j in journal_entries),
    "guidelines_checked": sum(has_value(j, "guidelines_checked") for j in journal_entries),
    "checkpoints": EXPECTED["checkpoints"],
}
COUNT_LABEL = {"if_year": "journals with IF_year", "guidelines_checked": "journals with guidelines_checked",
               "checklists": "item-by-item checklists"}

# Files whose every count is checked; files (skills, commands, evals) where only the library
# totals are — a SKILL.md legitimately says "4 个 skill" or "1–2 个期刊"; and reference / data
# files, where only explicit totals are ("Master Index (54 standards)", "240 journals total",
# "all 54 standards", "共 54 项规范") — the journal library lists "Urology: 11 journals" per
# specialty and a method reference says "Report against 2 standards: MIAME and MINSEQE".
claim_files = ["README.md", "README_CN.md", ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
               "CONTRIBUTING.md", "SECURITY.md", "hooks/session-start.sh", "install.sh"] + \
              sorted(rel(p) for p in (ROOT / "docs").rglob("*.md"))
library_claim_files = sorted(rel(p) for p in (ROOT / "skills").glob("*/SKILL.md")) + \
                      sorted(rel(p) for p in (ROOT / "commands").glob("*.md")) + ["evals/README.md"]
reference_claim_files = sorted(rel(p) for p in (ROOT / "skills").glob("*/references/**/*")
                               if p.is_file() and p.suffix in {".md", ".yaml", ".yml"})

# A number ("240", "1,240"), never the tail of "1,240" or a part of "6.4.2". Group 1 of every pattern.
NUM = r"(?<![\d.])(?<!\d,)(\d{1,3}(?:,\d{3})+|\d+)"
# Up to three words between number and noun ("46 domain-specific compliance standards"), but not
# a selection or a delta ("3 target journals", "2 new skills").
NOT_ADJ = (r"(?:of|the|and|or|in|with|target|candidate|recommended|suggested|selected|shortlisted|matching|"
           r"matched|top|preferred|backup|alternative|other|more|additional|new|extra|example|sample)\b")
ADJ = rf"(?:(?!{NOT_ADJ})[A-Za-z][\w/-]*\s+){{0,3}}"
CJK = r"(?:(?!候选|目标|推荐|备选|首选|其他|其它|新增|额外|示例)[一-鿿]){0,4}?"   # "42 本常投期刊"
# "from N options" is the standards library only beside wording that clearly means it ("the correct
# standard from 54 options", "from 54 options: the reporting standards"), not "the summary statistic
# from 3 options ... the standard deviation" or "picks the standard from 2 options when ...".
STD_LIB = (r"(?:reporting\s+(?:standards?|guidelines?)|standards\s+(?:index|library)|"   # not "Python standard library"
           r"(?:correct|right|appropriate|applicable|matching|best[- ]fitting)\s+(?:reporting\s+)?standard)\b")
# Every phrase that states one of the counts.
COUNT_PATTERNS = {
    "skills": [
        rf"\b{NUM}\s+{ADJ}skills\b",
        rf"\b{NUM}-skills?\b",
        rf"{NUM}\s*个\s*{CJK}\s*(?:skill|技能)",
        rf"(?:skills|技能)\s*[（(]{NUM}\s*个?[)）]",
    ],
    "commands": [
        rf"\b{NUM}\s+{ADJ}commands\b",
        rf"{NUM}\s*个\s*{CJK}命令",
        rf"(?:commands|命令)\s*[（(]{NUM}\s*个?[)）]",
    ],
    "journals": [
        rf"\b{NUM}\s+{ADJ}(?:journals|journal\s+templates)\b",
        # a bare "templates" is the journal library, but "6 templates for the article types" is not
        rf"\b{NUM}\s+templates\b(?!\s+(?:for|of)\s+(?!.{{0,30}}\bjournals?\b))",
        rf"\b{NUM}-journal\b",
        rf"{NUM}\s*(?:本|种|个)\s*{CJK}期刊",
        rf"{NUM}\s*(?:个|套|份)\s*模板",
        rf"(?:journal templates|期刊模板|期刊)\s*[（(]{NUM}\s*(?:本|种|个)?[)）]",
    ],
    "standards": [
        rf"\b{NUM}\s+{ADJ}standards\b",
        rf"\b{NUM}\s+{ADJ}reporting\s+guidelines\b",
        rf"\b{NUM}-standard\b",
        rf"\b{NUM}\s+reporting\s*<br\s*/?>\s*standards\b",                # mermaid node "54 Reporting<br/>Standards"
        rf"\b{STD_LIB}.*?\bfrom\s+{NUM}\s+options\b",                      # "the correct standard from 54 options"
        rf"\bfrom\s+{NUM}\s+options\b(?=.*\b{STD_LIB})",                   # "from 54 options: the reporting standards"
        rf"{NUM}\s*(?:个|项|条|种)\s*{CJK}(?:规范|报告指南)",
        rf"(?:standards|规范|规范速查)\s*[（(]{NUM}\s*个?[)）]",
    ],
    "checklists": [
        rf"\b{NUM}\s+{ADJ}checklists\b",
        rf"\b{NUM}\s+(?:with|have|has|ship\s+with)\s+an?\s+{ADJ}checklist\b",     # "21 with a local checklist"
        rf"\b{NUM}\s+of\s+(?:the\s+)?\d+\s+(?:reporting\s+)?standards\b(?=.*checklist)",
        rf"{NUM}\s*(?:个|项|份|套)\s*{CJK}(?:checklist|核查清单|核对清单|逐条清单)",   # not "10 个脚本的清单"
        rf"规范中\s*(?:有\s*)?{NUM}\s*(?:个|项)(?=.*checklist)",                 # "54 项规范中有 21 项附带 checklist"
    ],
    "scripts": [
        rf"\b{NUM}\s+{ADJ}scripts\b",
        rf"{NUM}\s*个\s*{CJK}(?:Python\s*)?脚本",
        rf"(?:scripts|脚本)\s*[（(]{NUM}\s*个?[)）]",
    ],
    "checkpoints": [
        rf"\b{NUM}\s+(?:hard|mandatory)\s+checkpoints?\b",
        rf"{NUM}\s*个\s*(?:硬|强制)(?:确认|检查点)",
    ],
}
LIBRARY_PATTERNS = {   # no adjectives in between: "3 个候选期刊" in a SKILL.md is not the library size
    "journals": [rf"\b{NUM}\s+(?:journals|journal\s+templates)\b", rf"{NUM}\s*(?:本|种|个)\s*期刊"],
    "standards": [rf"\b{NUM}\s+(?:reporting\s+)?standards\b", rf"\b{NUM}\s+reporting\s+guidelines\b",
                  rf"{NUM}\s*(?:个|项|条|种)\s*(?:报告|医学)?规范", rf"{NUM}\s*(?:个|项|条|种)\s*报告指南"],
    "skills": [rf"\ball\s+{NUM}\s+(?:MRP\s+)?skills\b", rf"(?:全部|所有)\s*{NUM}\s*个\s*(?:skill|技能)"],
}


def explicit_totals(noun, cn_noun):
    """Wording that states the size of the whole library (reference / data files)."""
    return [
        rf"\b(?:index|library|catalog(?:ue)?)\s*[(（]\s*{NUM}\s+{noun}\s*[)）]",            # "Master Index (54 standards)"
        # "240 journals total", "54 standards in total", not "2 standards in all mixed designs"
        rf"\b{NUM}\s+{noun}\s+(?:in\s+total\b|(?:total|in\s+all)\b(?![\s-]+(?!(?:and|or|but)\b)\w))",
        # "all 54 standards", "a total of 54 standards (in the index)", not "all 3 journals in this family"
        rf"\b(?:all|total\s+of)\s+(?:the\s+|these\s+)?{NUM}\s+{noun}"
        rf"(?!\s+(?:in|of|from|within)\s+(?!(?:the\s+|this\s+)?(?:index|library|plugin|repo(?:sitory)?|MRP)\b))",
        rf"\b(?:library|index|plugin|MRP)\s+(?:of|has|holds|contains|lists|covers|includes|ships|bundles)\s+"
        rf"{NUM}\s+{noun}",                                                               # "the library holds 54 standards"
        rf"(?:共|总共|一共|总计|合计|全部|所有)\s*(?:收录|包含|包括|含|有)?\s*{NUM}\s*{cn_noun}",   # "共 54 项规范"
        rf"(?:(?<!数据)库|本插件|MRP)[^\d，。；,;:：]{{0,8}}?{NUM}\s*{cn_noun}",                # "规范库收录 54 项规范"
    ]


REFERENCE_PATTERNS = {
    "journals": explicit_totals(r"(?:journals|(?:journal\s+)?templates)\b", r"(?:本|种|个)\s*期刊"),
    "standards": explicit_totals(r"(?:(?:reporting\s+)?standards|reporting\s+guidelines)\b",
                                 r"(?:个|项|条|种)\s*(?:(?:报告|医学)?规范|报告指南)"),
    "checklists": explicit_totals(r"(?:item-by-item\s+)?checklists\b",
                                  r"(?:个|项|份|套)\s*(?:checklist|核查清单|核对清单|逐条清单)"),
    "skills": explicit_totals(r"(?:MRP\s+)?skills\b", r"个\s*(?:skill|技能)"),
}
# In a sentence about IF_year or guidelines_checked, "N journals" counts those entries...
SUBSET_CONTEXT = {
    "if_year": re.compile(r"IF_year"),
    "guidelines_checked": re.compile(
        r"guidelines_checked|(?:re-?checked|verified)\b.{0,60}(?:author guidelines|instructions for authors)"
        r"|(?:核对|核实|复核).{0,20}(?:投稿指南|作者指南|稿约)", re.IGNORECASE),
}
SUBSET_EXTRA = [rf"\b{NUM}\s+{ADJ}entries\b", rf"{NUM}\s*(?:个|条)\s*{CJK}条目",
                rf"\b{NUM}\s+of\s+(?:the\s+)?\d+\s+", rf"期刊中\s*(?:有\s*)?{NUM}\s*(?:本|个|种)",
                rf"\b(?!(?:19|20)\d\d\b){NUM}\s+(?:have|has|carry|carries|with)\b"]   # "82 have `IF_year`"
# ...but the whole library is meant in "of the 240 journals", "240 本期刊中", "The 240 journals include".
TOTAL_BEFORE = re.compile(r"\b(?:of|among|out\s+of)\s+(?:the\s+|all\s+|these\s+)?$|/\s*$|(?:共|全部)\s*$",
                          re.IGNORECASE)
TOTAL_AFTER = re.compile(r"\s*(?:本|种|个)?\s*期刊中|\s*(?:journals|journal\s+templates|entries)\s*,?\s*"
                         r"(?:include|includes|including|contain|contains|of\s+which|among\s+(?:them|which))\b",
                         re.IGNORECASE)
# A range ("1–2 个期刊", "1 到 2 本", "2 to 4 skills"), "30+" or a compound ("top-5") is not a total;
# "扩展到 99 项规范" and "Framework - 99 skills" are (no number before the dash or 到).
RANGE_BEFORE = re.compile(r"(?<![\d.])\d[\d,]*\s*(?:[–~～至到-]|\bto\b)\s*$|[A-Za-z]-$", re.IGNORECASE)
RANGE_AFTER = re.compile(r"\s*[–~～+-]\s*\d")
# ...but in "Standards went from 47 to 99 standards" the second number is the new total.
CHANGE_BEFORE = re.compile(r"\b(?:went|gone|grew|grown|increased|rose|risen|expanded|jumped|climbed|moved|changed|"
                           r"bumped|extended|raised|dropped|fell|fallen|decreased|shrank|shrunk|reduced)\s+"
                           r"(?:up\s+|down\s+)?from\s+\d[\d,]*\s+to\s*$", re.IGNORECASE)
# For the reference libraries, a count of one is the singular ("填写 1 份核查清单"; the English patterns
# need the plural anyway), and a short list naming exactly N items right after the count is that set,
# not the library ("STARD has 2 checklists: one for the abstract and one for the full text",
# "follows 2 reporting guidelines (STARD and CLAIM)").
LIBRARY_KINDS = {"journals", "standards", "checklists"}
SHORT_LIST = 9
NAMED_LIST = re.compile(r"\s*(?:[:：]\s*(?P<colon>.+)|[(（](?P<paren>[^)）]+)[)）])")
LIST_SEP = re.compile(r"\s*(?:[,，、/+&]|\band\b|\bor\b|以及|和|与|及|或)\s*", re.IGNORECASE)
SENTENCE = re.compile(r"(?<=[.;!?])\s+|[。；！？]")


def names_items(after, n):
    """True when `after` (the text right after a count of n) lists exactly n items."""
    m = NAMED_LIST.match(after)
    if not m or n > SHORT_LIST:
        return False
    items = LIST_SEP.split((m.group("colon") or m.group("paren")).strip().rstrip(".…"))
    return sum(1 for item in items if item.strip()) == n


def compiled(patterns):
    return {kind: [re.compile(p, re.IGNORECASE) for p in pats] for kind, pats in patterns.items()}


SUBSET_EXTRA_RX = [re.compile(p, re.IGNORECASE) for p in SUBSET_EXTRA]


def count_claims(text, patterns):
    """Yield (line, kind, number, phrase) for every count stated in `text` (patterns from compiled())."""
    for ln, line in enumerate(text.splitlines(), 1):
        if not re.search(r"\d", line):
            continue
        for sentence in SENTENCE.split(line):
            subset = next((k for k, rx in SUBSET_CONTEXT.items() if rx.search(sentence)), None)
            found, named = {}, set()
            for kind, pats in patterns.items():
                for rx in pats + (SUBSET_EXTRA_RX if kind == "journals" and subset else []):
                    for m in rx.finditer(sentence):
                        before, after = sentence[:m.start(1)], sentence[m.end(1):]
                        if (RANGE_BEFORE.search(before) and not CHANGE_BEFORE.search(before)) \
                                or RANGE_AFTER.match(after):
                            continue
                        n = int(m.group(1).replace(",", ""))
                        if kind in LIBRARY_KINDS and (n == 1 or names_items(sentence[m.end():], n)):
                            named.add(m.start(1))
                            continue
                        k = kind
                        if kind == "journals" and subset and not (TOTAL_BEFORE.search(before)
                                                                 or TOTAL_AFTER.match(after)):
                            k = subset
                        found.setdefault((m.start(1), k), (n, m.group(0)))
            for (pos, kind), (n, phrase) in sorted(found.items()):
                if pos not in named:
                    yield ln, kind, n, phrase


for paths, patterns in ((claim_files, COUNT_PATTERNS), (library_claim_files, LIBRARY_PATTERNS),
                        (reference_claim_files, REFERENCE_PATTERNS)):
    patterns = compiled(patterns)
    for path in paths:
        if not (ROOT / path).is_file():
            continue
        for ln, kind, n, phrase in count_claims(read(path), patterns):
            if n != actual[kind]:
                err(f"(b) {path}:{ln} claims {n} {COUNT_LABEL.get(kind, kind)} (repo has {actual[kind]}): {phrase!r}")

# The standards index's own header lists the checklist files of the entries that have one:
# "(21 of 54: consort-2025, consort-ai, ...)".
index_path = "skills/reporting-standards/references/checklists/standards-index.yaml"
header = " ".join(ln.lstrip("# ") for ln in read(index_path).split("\nstandards:", 1)[0].splitlines())
m = re.search(r"\((\d+) of (\d+):\s*([^)]*)\)", header)
if m:
    listed = {s.strip() for s in m.group(3).split(",") if s.strip()}
    with_file = {Path(str(s["file"])).stem for s in standard_entries if has_value(s, "file")}
    if (int(m.group(1)), int(m.group(2))) != (actual["checklists"], actual["standards"]) or listed != with_file:
        err(f"(b) {index_path} header says '({m.group(1)} of {m.group(2)}: ...)' but {actual['checklists']} of "
            f"{actual['standards']} entries have a `file:`; not listed: {sorted(with_file - listed)}, "
            f"listed but no entry has that file: {sorted(listed - with_file)}")

# The CONSORT 2025 entry in the index must carry the real item count.
consort = next((s for s in standards_data["standards"] if s.get("id") == "consort-2025"), None)
if consort is None:
    err("(b) standards-index.yaml has no consort-2025 entry")
else:
    items = str(consort.get("items", ""))
    if not items.startswith(str(EXPECTED["consort_items"])):
        err(f"(b) standards-index.yaml consort-2025 items = {items!r}, expected {EXPECTED['consort_items']} "
            f"(30 items, 42 rows incl. sub-items)")

# ── (c) Command prefix ───────────────────────────────────────────────────────
if plugin.get("name") != PLUGIN_NAME:
    err(f"(c) plugin.json name is {plugin.get('name')!r}, must be {PLUGIN_NAME!r} (commands are /{PLUGIN_NAME}:<x>)")
if marketplace["plugins"][0].get("name") != PLUGIN_NAME:
    err(f"(c) marketplace.json plugins[0].name is {marketplace['plugins'][0].get('name')!r}, must be {PLUGIN_NAME!r}")
if marketplace.get("name") != "med-research-powers":
    err(f"(c) marketplace.json name is {marketplace.get('name')!r}, expected 'med-research-powers'")

known_slash = set(skill_dirs) | set(command_files)
for p in text_files(exts={".md", ".sh"}):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if "/med-research-powers:" in line:
            err(f"(c) {rel(p)}:{ln} uses the old command prefix /med-research-powers: (plugin name is {PLUGIN_NAME})")
        for name in re.findall(r"/mrp:([a-z0-9][a-z0-9-]*)", line):
            if name not in known_slash:
                err(f"(c) {rel(p)}:{ln} references /mrp:{name}, which is neither a command nor a skill")

# ── (d) Commands must not shadow skills ──────────────────────────────────────
for name in command_files:
    if name in skill_dirs:
        err(f"(d) commands/{name}.md has the same name as skills/{name}/ (the skill wins; delete the command)")

# ── (e) Script paths ─────────────────────────────────────────────────────────
bundled_scripts = {p.name for p in script_files}
SCRIPT_REF = re.compile(r"(?:[\w.$@{}-]+/)*scripts/([\w-]+\.py)")
for p in text_files(roots=("skills", "commands", "docs", "README.md", "README_CN.md"),
                    exts={".md", ".sh", ".yaml", ".yml"}):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if re.search(r"""sys\.path\.insert\(\s*0\s*,\s*['"]scripts['"]\s*\)""", line):
            err(f"(e) {rel(p)}:{ln} uses sys.path.insert(0, 'scripts') — use ${{CLAUDE_PLUGIN_ROOT}}/skills/<skill>/scripts")
        elif "sys.path.insert(" in line and "CLAUDE_PLUGIN_ROOT" not in line:
            err(f"(e) {rel(p)}:{ln} sys.path.insert without CLAUDE_PLUGIN_ROOT")
        for m in SCRIPT_REF.finditer(line):
            if "CLAUDE_PLUGIN_ROOT" not in line:
                err(f"(e) {rel(p)}:{ln} references {m.group(0)} without ${{CLAUDE_PLUGIN_ROOT}}")
            if m.group(1) not in bundled_scripts:
                err(f"(e) {rel(p)}:{ln} references scripts/{m.group(1)}, which is not a bundled script")

# Every ${CLAUDE_PLUGIN_ROOT}/... path must exist (placeholders like <skill> are skipped).
PLUGIN_ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)")
for p in text_files(exts={".md", ".sh", ".yaml", ".yml", ".json"}):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for target in PLUGIN_ROOT_PATH.findall(line):
            # placeholders such as <skill>/<file>.py stop the match early, so only the
            # concrete prefix is checked
            target = target.rstrip("./")
            if not target:
                continue
            if not (ROOT / target).exists():
                err(f"(e) {rel(p)}:{ln} ${{CLAUDE_PLUGIN_ROOT}}/{target} does not exist")

# ── (f) SKILL.md frontmatter and referenced paths ────────────────────────────
REL_PATH_REF = re.compile(r"[`(]((?:references|scripts)/[^`()\s<>{}*]+)[`)]")
for skill in skill_dirs:
    skill_md = ROOT / "skills" / skill / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    fm, body = frontmatter(text)
    where = f"skills/{skill}/SKILL.md"
    if fm is None:
        err(f"(f) {where} has no YAML frontmatter")
        continue
    if "__error__" in fm:
        err(f"(f) {where} frontmatter is not valid YAML: {fm['__error__']}")
        continue
    if fm.get("name") != skill:
        err(f"(f) {where} frontmatter name {fm.get('name')!r} != directory name {skill!r}")
    desc = str(fm.get("description", "")).strip()
    if not desc.startswith("Use when"):
        err(f"(f) {where} description must start with 'Use when' (starts with {desc[:30]!r})")
    if len(desc) > 200:
        err(f"(f) {where} description is {len(desc)} chars (max 200)")
    n_lines = len(text.splitlines())
    if n_lines > 500:
        err(f"(f) {where} is {n_lines} lines (max 500)")
    seen = set()
    for m in REL_PATH_REF.finditer(text):
        target = m.group(1).rstrip(".,;:")
        if target in seen:
            continue
        seen.add(target)
        if not (ROOT / "skills" / skill / target).exists():
            err(f"(f) {where} references {target}, which does not exist under skills/{skill}/")

# ── (g) README.md and README_CN.md keep the same structure ───────────────────
def structure(path):
    body = strip_fences(read(path)) + "\n"
    h1 = len(re.findall(r"^# ", body, re.MULTILINE))
    h2 = len(re.findall(r"^## ", body, re.MULTILINE))
    tables = len(re.findall(r"(?:^\|.*\n)+", body, re.MULTILINE))
    return {"H1": h1, "H2": h2, "tables": tables}

en, cn = structure("README.md"), structure("README_CN.md")
for k in en:
    if en[k] != cn[k]:
        err(f"(g) README.md has {en[k]} {k}, README_CN.md has {cn[k]} — keep both files in sync")

# ── (h) Relative links and #anchors must resolve ────────────────────────────
LINK = re.compile(r"\]\(([^)\s]+)\)")
link_files = ["README.md", "README_CN.md", "CONTRIBUTING.md", "SECURITY.md"] + \
             [rel(p) for p in (ROOT / "docs").rglob("*.md")]


def heading_anchors(path):
    """The #anchors GitHub generates for a Markdown file's headings (plus explicit <a id/name>)."""
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r"<a\s+(?:name|id)=\"([^\"]+)\"", text))
    seen = {}
    for line in strip_fences(text).splitlines():
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", m.group(1).strip().lower())   # [text](url) → text
        t = re.sub(r"<[^>]+>", "", t)
        slug = re.sub(r"[^\w\- ]", "", t).replace(" ", "-")   # GitHub: drop punctuation, spaces → -
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        anchors.add(slug if n == 0 else f"{slug}-{n}")
    return anchors


anchor_cache = {}
for path in link_files:
    if not (ROOT / path).is_file():
        continue
    for ln, line in enumerate(read(path).splitlines(), 1):
        for target in LINK.findall(line):
            if re.match(r"^(?:https?:|mailto:)", target):
                continue
            clean, _, frag = target.partition("#")
            resolved = (ROOT / path).parent / clean if clean else ROOT / path
            if clean and not resolved.exists():
                err(f"(h) {path}:{ln} links to {target}, which does not exist")
                continue
            if not frag or resolved.suffix != ".md" or not resolved.is_file():
                continue
            key = resolved.resolve()
            if key not in anchor_cache:
                anchor_cache[key] = heading_anchors(resolved)
            if unquote(frag).lower() not in anchor_cache[key]:
                err(f"(h) {path}:{ln} links to {target}, but {rel(resolved)} has no heading with anchor #{unquote(frag)}")

# ── (i) Stale CONSORT / standards counts ─────────────────────────────────────
STALE = ["31 numbered items", "34 rows", "31 项", "31 个编号", "共 34 行", "42+"]
for p in text_files(skip_dirs=LITERAL_SCAN_SKIP_DIRS):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for s in STALE:
            if s in line:
                err(f"(i) {rel(p)}:{ln} still contains {s!r} (CONSORT 2025 = 30 items, 42 rows incl. sub-items; standards = {actual['standards']})")

# ── (j) Evals: every skill has a case; evals/README.md numbers are real ──────
def eval_cases():
    """{case name: {"tags": [...], "graders": [frontmatter dicts]}} for evals/<case>/prompt.md."""
    cases = {}
    for d in sorted((ROOT / "evals").iterdir()):
        prompt = d / "prompt.md"
        if not d.is_dir() or not prompt.is_file():
            continue
        fm, _ = frontmatter(prompt.read_text(encoding="utf-8"))
        if not fm or "__error__" in fm:
            err(f"(j) evals/{d.name}/prompt.md has no valid frontmatter")
            fm = {}
        graders = []
        for g in sorted((d / "graders").glob("*.md")):
            gfm, _ = frontmatter(g.read_text(encoding="utf-8"))
            if gfm and "__error__" not in gfm:
                graders.append(gfm)
        tags = fm.get("tags") or []
        cases[d.name] = {"tags": [str(t) for t in tags] if isinstance(tags, list) else [str(tags)], "graders": graders}
    return cases


def expects_skill(grader, skill):
    """True for a grader that passes only when `skill` was invoked (not a "must not be invoked" one)."""
    if grader.get("type") != "tool_used" or grader.get("tool") != "Skill":
        return False
    try:
        if int(grader.get("min", 1)) < 1 or grader.get("max") == 0:
            return False
    except (TypeError, ValueError):
        return False
    pattern = str(grader.get("input_match", ""))
    probes = (f'{{"skill": "{PLUGIN_NAME}:{skill}"}}', f'{{"skill": "{skill}"}}')
    try:
        rx = re.compile(pattern)
    except re.error:
        return re.search(rf"(?<![\w-]){re.escape(skill)}(?![\w-])", pattern) is not None
    return any(rx.search(probe) for probe in probes)


cases = eval_cases()
for skill in skill_dirs:
    if not any(expects_skill(g, skill) for c in cases.values() for g in c["graders"]):
        err(f"(j) skill {skill!r} has no eval case: add evals/route-{skill}/ with a Skill tool_used grader "
            f"(min: 1) whose input_match names it")

if (ROOT / "evals" / "README.md").is_file():
    for ln, line in enumerate(read("evals/README.md").splitlines(), 1):
        for m in re.finditer(r"\bThere are (\d+) cases\b|共\s*(\d+)\s*个(?:评测)?用例", line):
            n = int(m.group(1) or m.group(2))
            if n != len(cases):
                err(f"(j) evals/README.md:{ln} says {n} eval cases (evals/ has {len(cases)})")
        m = re.match(r"^\|\s*`([\w-]+)`\s*\|\s*(\d+)\b", line)
        if m:
            tag, n = m.group(1), int(m.group(2))
            real = sum(tag in c["tags"] for c in cases.values())
            if n != real:
                err(f"(j) evals/README.md:{ln} says tag {tag!r} has {n} cases (evals/ has {real})")

# ── (k) GitHub workflows ─────────────────────────────────────────────────────
PINNED_ACTION = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")
for wf in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
    where = rel(wf)
    try:
        flow = yaml.safe_load(wf.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        err(f"(k) {where} is not valid YAML: {e}")
        continue
    if "secrets." in json.dumps(flow.get("env", {})):
        err(f"(k) {where}: a secret is in the workflow-level env — give it only to the step that needs it")
    for job_name, job in (flow.get("jobs") or {}).items():
        job = job or {}
        if "secrets." in json.dumps(job.get("env", {})):
            err(f"(k) {where} job {job_name!r}: a secret is in the job env — give it only to the step that needs it")
        if job.get("continue-on-error"):
            err(f"(k) {where} job {job_name!r} has continue-on-error (CI checks must block)")
        for step in job.get("steps") or []:
            uses = str(step.get("uses", ""))
            if uses and not uses.startswith(("./", "docker://")) and not PINNED_ACTION.match(uses):
                err(f"(k) {where} job {job_name!r}: {uses!r} is not pinned to a commit SHA")
            if step.get("continue-on-error"):
                err(f"(k) {where} job {job_name!r}: step {step.get('name') or uses!r} has continue-on-error")
            for m in re.finditer(r"@anthropic-ai/claude-code(@\S*)?", str(step.get("run", ""))):
                if not re.fullmatch(r"@\d+\.\d+\.\d+", m.group(1) or ""):
                    err(f"(k) {where} job {job_name!r}: install @anthropic-ai/claude-code at an exact version "
                        f"(found {m.group(0)!r})")

# ── (+) Extra hygiene ────────────────────────────────────────────────────────
if "strict" in marketplace["plugins"][0]:
    err('(+) marketplace.json plugins[0] still has "strict" (remove it; plugin.json is the manifest)')
for key in ("homepage", "repository"):
    if not plugin.get(key):
        err(f"(+) plugin.json is missing {key!r}")
hooks = plugin.get("hooks", {}).get("SessionStart", [])
hook_cmds = [h.get("command", "") for entry in hooks for h in entry.get("hooks", [])]
if not hook_cmds:
    err("(+) plugin.json has no SessionStart hook")
for cmd in hook_cmds:
    if "${CLAUDE_PLUGIN_ROOT}" not in cmd:
        err(f"(+) hook command {cmd!r} must be anchored on ${{CLAUDE_PLUGIN_ROOT}}")
    script = cmd.replace('"', "").replace("${CLAUDE_PLUGIN_ROOT}/", "")
    if not (ROOT / script).is_file():
        err(f"(+) hook command points at {script}, which does not exist")
    elif not os.access(ROOT / script, os.X_OK):
        err(f"(+) {script} is not executable (chmod +x)")

for name in command_files:
    fm, _ = frontmatter(read(f"commands/{name}.md"))
    if not fm or "__error__" in fm:
        err(f"(+) commands/{name}.md has no valid frontmatter")
        continue
    if fm.get("disable-model-invocation") is not True:
        err(f"(+) commands/{name}.md must set disable-model-invocation: true")
    if not fm.get("description"):
        err(f"(+) commands/{name}.md has no description")

# README "Bundled Python Scripts" table must list exactly the scripts on disk.
disk_scripts = {f"{p.parent.parent.name}/scripts/{p.name}" for p in script_files}
for path, heading in (("README.md", "## Bundled Python Scripts"), ("README_CN.md", "## 内置 Python 脚本")):
    text = read(path)
    start = text.find(heading)
    if start < 0:
        err(f"(+) {path} has no '{heading}' section")
        continue
    section = text[start:]
    nxt = section.find("\n## ", 1)
    section = section[:nxt] if nxt > 0 else section
    listed = set()
    for row in section.splitlines():
        m = re.match(r"^\|\s*`([\w-]+\.py)`\s*\|\s*`([\w-]+)/scripts/`", row)
        if m:
            listed.add(f"{m.group(2)}/scripts/{m.group(1)}")
    for missing in sorted(disk_scripts - listed):
        err(f"(+) {path} bundled-scripts table does not list {missing}")
    for phantom in sorted(listed - disk_scripts):
        err(f"(+) {path} bundled-scripts table lists {phantom}, which does not exist")

# requirements.txt: every package has a ">=" lower bound (CI installs exactly those on Python 3.10),
# optionally an upper bound and an environment marker ("tomli>=2.0; python_version < '3.11'").
for ln, line in enumerate(read("requirements.txt").splitlines(), 1):
    req = line.split("#", 1)[0].strip()
    if req and not re.match(r"^[A-Za-z0-9_.-]+>=\d+(?:\.\d+)*(?:\s*,\s*<[^;\s]+)?(?:\s*;\s*\S.*)?$", req):
        err(f"(+) requirements.txt:{ln} {req!r} needs a lower bound (name>=version)")

# examples/showcase was deleted in 6.2.1 — nothing may still point at it.
for p in text_files(exts={".md"}):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if "examples/showcase" in line:
            err(f"(+) {rel(p)}:{ln} references examples/showcase, which no longer exists")

# The user profile is global (~/.claude/mrp-user-profile.json), not per project.
profile_files = ["README.md", "README_CN.md", "docs/USER-MANUAL.md", "docs/architecture.md", "hooks/session-start.sh"] + \
                [f"skills/{s}/SKILL.md" for s in skill_dirs]
GLOBAL_PATH = re.compile(r"(?:~|\$\{?HOME\}?|\$\{?CLAUDE_CONFIG_DIR\}?)/\.claude/|CLAUDE_CONFIG_DIR|home\.expanduser|expanduser")
for path in profile_files:
    for ln, line in enumerate(read(path).splitlines(), 1):
        if "mrp-user-profile.json" in line and not GLOBAL_PATH.search(line):
            err(f"(+) {path}:{ln} mentions mrp-user-profile.json without its global path ~/.claude/mrp-user-profile.json")

# ── Report ───────────────────────────────────────────────────────────────────
if errors:
    print(f"❌ consistency check FAILED ({len(errors)} issue(s)):")
    for e in errors:
        print(f"   - {e}")
    sys.exit(1)

print(f"✅ consistency OK — v{VERSION}: {actual['skills']} skills, {actual['commands']} commands, "
      f"{actual['journals']} journals ({actual['if_year']} with IF_year, {actual['guidelines_checked']} with "
      f"guidelines_checked), {actual['standards']} standards, {actual['scripts']} scripts, {len(cases)} eval cases.")
