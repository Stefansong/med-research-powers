#!/usr/bin/env python3
"""
MRP repository consistency guard.

Run from anywhere:  python tools/check_consistency.py
Exit 1 and list every problem if anything is inconsistent; otherwise print one
summary line.  CHANGELOG.md is exempt from every check (it is history).

What it locks down (each block below is one lettered check):
  (a) one version string everywhere it is stated; no stray x.y.z anywhere else
  (b) on-disk counts (skills / commands / journals / standards / scripts) equal
      the expected numbers, and every number the docs claim equals the real one
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
      point at files that exist
  (i) no stale CONSORT counts ("31 numbered items", "34 rows", "42+", ...)
  (+) manifest hygiene, command frontmatter, bundled-script table, checkpoint
      count, profile path, no examples/showcase references
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("❌ PyYAML is required: pip install pyyaml  (or pip install -r requirements.txt)")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# ── Expected numbers (update these together with the files) ─────────────────
EXPECTED = {
    "skills": 20,
    "commands": 7,
    "journals": 240,
    "standards": 47,
    "scripts": 10,
    "checkpoints": 3,          # mandatory (hard) checkpoints: protocol / SAP / pre-submission
    "consort_items": 30,       # CONSORT 2025 — 30 items (42 rows incl. sub-items)
}
PLUGIN_NAME = "mrp"
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache"}
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

# No other x.y.z anywhere (tool versions like "Python 3.11.2" are tolerated).
TOOL_VERSION_CONTEXT = re.compile(
    r"(?:python|node|npm|pip|numpy|pandas|scipy|statsmodels|matplotlib|docx|openpyxl|pyyaml|"
    r"claude code|claude|r|spss|stata|sas|tensorflow|torch|pytorch|sklearn|scikit-learn)\s*v?=?\s*\d+\.\d+\.\d+",
    re.IGNORECASE)
DOI_OR_URL = re.compile(r"10\.\d{4,9}/\S+|https?://\S+")
for p in text_files(skip_dirs=LITERAL_SCAN_SKIP_DIRS):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        scan = DOI_OR_URL.sub(" ", line)          # DOIs and URLs are not versions
        for stray in re.findall(r"\bv?(\d+\.\d+\.\d+)\b", scan):
            if stray != VERSION and not TOOL_VERSION_CONTEXT.search(scan):
                err(f"(a) stray version {stray!r} in {rel(p)}:{ln} (expected only {VERSION!r})")

# ── (b) Counts on disk vs expected, and every documented number ──────────────
skill_dirs = sorted(d.name for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").is_file())
command_files = sorted(p.stem for p in (ROOT / "commands").glob("*.md"))
script_files = sorted(p for p in (ROOT / "skills").glob("*/scripts/*.py"))

journals_data = yaml.safe_load(read("skills/manuscript-writing/references/journal-templates.yaml"))
standards_data = yaml.safe_load(read("skills/reporting-standards/references/checklists/standards-index.yaml"))
n_journals = len(journals_data["templates"])
n_standards = len(standards_data["standards"])

actual = {
    "skills": len(skill_dirs),
    "commands": len(command_files),
    "journals": n_journals,
    "standards": n_standards,
    "scripts": len(script_files),
}
for key, real in actual.items():
    if real != EXPECTED[key]:
        err(f"(b) {key}: on-disk count {real} != expected {EXPECTED[key]} (update the files and EXPECTED in this guard)")

claim_files = ["README.md", "README_CN.md", ".claude-plugin/plugin.json",
               ".claude-plugin/marketplace.json", "docs/architecture.md", "docs/USER-MANUAL.md"]

# Every phrase that states one of the counts. Group 1 is the number.
COUNT_PATTERNS = {
    "skills": [
        r"\b(\d+)\s+skills\b",
        r"(\d+)\s*个\s*(?:skill|技能)",
        r"(?:skills|技能)\s*[（(](\d+)\s*个?[)）]",
    ],
    "commands": [
        r"\b(\d+)\s+(?:slash\s+)?commands\b",
        r"(\d+)\s*个\s*(?:斜杠)?命令",
        r"(?:commands|命令)\s*[（(](\d+)\s*个?[)）]",
    ],
    "journals": [
        r"\b(\d+)\s+journal(?:s|\s+templates)\b",
        r"(\d+)\s*(?:本|种|个)\s*期刊",
        r"(?:journal templates|期刊模板|期刊)\s*[（(](\d+)\s*(?:本|种|个)?[)）]",
    ],
    "standards": [
        r"\b(\d+)\s+(?:reporting\s+)?standards\b",
        r"(\d+)\s*(?:个|项|条|种)\s*(?:报告|医学)?规范",
        r"(?:standards|规范|规范速查)\s*[（(](\d+)\s*个?[)）]",
    ],
    "scripts": [
        r"\b(\d+)\s+(?:bundled\s+)?(?:python\s+)?scripts\b",
        r"(\d+)\s*个\s*(?:内置\s*)?(?:Python\s*)?脚本",
        r"(?:scripts|脚本)\s*[（(](\d+)\s*个?[)）]",
    ],
    "checkpoints": [
        r"\b(\d+)\s+(?:hard|mandatory)\s+checkpoints?\b",
        r"(\d+)\s*个\s*(?:硬|强制)(?:确认|检查点)",
    ],
}
for path in claim_files:
    for ln, line in enumerate(read(path).splitlines(), 1):
        for key, pats in COUNT_PATTERNS.items():
            for pat in pats:
                for m in re.finditer(pat, line, re.IGNORECASE):
                    n = int(m.group(1))
                    if n != EXPECTED[key]:
                        err(f"(b) {path}:{ln} claims {n} {key} (real: {EXPECTED[key]}): {m.group(0)!r}")

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

# ── (h) Relative links must resolve ──────────────────────────────────────────
LINK = re.compile(r"\]\(([^)\s]+)\)")
link_files = ["README.md", "README_CN.md", "CONTRIBUTING.md", "SECURITY.md"] + \
             [rel(p) for p in (ROOT / "docs").rglob("*.md")]
for path in link_files:
    if not (ROOT / path).is_file():
        continue
    for ln, line in enumerate(read(path).splitlines(), 1):
        for target in LINK.findall(line):
            if re.match(r"^(?:https?:|mailto:|#)", target):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            resolved = (ROOT / path).parent / clean
            if not resolved.exists():
                err(f"(h) {path}:{ln} links to {target}, which does not exist")

# ── (i) Stale CONSORT / standards counts ─────────────────────────────────────
STALE = ["31 numbered items", "34 rows", "31 项", "31 个编号", "共 34 行", "42+"]
for p in text_files(skip_dirs=LITERAL_SCAN_SKIP_DIRS):
    for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for s in STALE:
            if s in line:
                err(f"(i) {rel(p)}:{ln} still contains {s!r} (CONSORT 2025 = 30 items, 42 rows incl. sub-items; standards = {EXPECTED['standards']})")

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
      f"{actual['journals']} journals, {actual['standards']} standards, {actual['scripts']} scripts.")
