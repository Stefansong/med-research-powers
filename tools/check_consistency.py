#!/usr/bin/env python3
"""
MRP repository consistency guard.

Prevents the drift this repo has accumulated in the past:
  - version strings out of sync across manifests / hook / installer / docs
  - claimed counts (skills / commands / journals / reporting standards)
    not matching what is actually on disk
  - plugin scripts referenced by skill-relative paths that won't resolve at
    runtime (must use ${CLAUDE_PLUGIN_ROOT})

Run from the repo root:  python tools/check_consistency.py
Exits non-zero (and prints every failure) if anything is inconsistent.
CHANGELOG.md is intentionally exempt — it is historical.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def err(msg):
    errors.append(msg)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


# ── 1. Version is identical everywhere it is stated ──────────────────────────
plugin = json.loads(read(".claude-plugin/plugin.json"))
VERSION = plugin["version"]

# (file, regex that must capture the version in group 1)
version_sites = [
    (".claude-plugin/marketplace.json", r'"version":\s*"([0-9.]+)"'),
    ("README.md",                       r"Version\s+([0-9.]+)"),
    ("README_CN.md",                    r"版本\s+([0-9.]+)"),
    ("install.sh",                      r"Installer.*?v([0-9.]+)|v([0-9.]+)\s+Installer"),
    ("hooks/session-start.sh",          r"MRP\)?\s+v([0-9.]+)"),
    ("docs/architecture.md",            r"Architecture.*?v?([0-9.]+)|v([0-9.]+)\s+Architecture"),
    ("docs/USER-MANUAL.md",             r"版本.*?v([0-9.]+)"),
]
for path, pat in version_sites:
    text = read(path)
    m = re.search(pat, text)
    found = next((g for g in (m.groups() if m else []) if g), None) if m else None
    if found != VERSION:
        err(f"version mismatch in {path}: found {found!r}, expected {VERSION!r}")

# No *other* x.y.z version may appear in tracked non-CHANGELOG files.
for path, _ in version_sites:
    for stray in set(re.findall(r"\b\d+\.\d+\.\d+\b", read(path))):
        if stray != VERSION and stray.startswith(VERSION.split(".")[0] + "."):
            err(f"stray version {stray!r} in {path} (expected only {VERSION!r})")


# ── 2. Claimed counts match what is on disk ──────────────────────────────────
n_skills = len(list((ROOT / "skills").glob("*/SKILL.md")))
n_commands = len(list((ROOT / "commands").glob("*.md")))

journals_yaml = read("skills/manuscript-writing/references/journal-templates.yaml")
n_journals = len(re.findall(r"^  - id:", journals_yaml, re.MULTILINE))

standards_yaml = read("skills/reporting-standards/references/checklists/standards-index.yaml")
n_standards = len(re.findall(r"^  - id:", standards_yaml, re.MULTILINE))

claim_files = ["README.md", "README_CN.md", ".claude-plugin/plugin.json",
               ".claude-plugin/marketplace.json", "docs/architecture.md", "docs/USER-MANUAL.md"]
blob = "\n".join(read(f) for f in claim_files)

checks = [
    ("skills",             n_skills,    20),
    ("commands",           n_commands,  20),
    ("journal templates",  n_journals,  234),
    ("reporting standards", n_standards, 41),
]
for label, actual, expected in checks:
    if actual != expected:
        err(f"{label}: on-disk count {actual} != expected {expected} "
            f"(update both the files and this guard)")

# The documented numbers must equal the real ones (catches "42+" style drift).
for label, actual, _ in checks:
    if label == "reporting standards" and re.search(r"\b42\+", blob):
        err(f'docs still claim "42+" {label}; real count is {actual}')
    if label == "journal templates" and str(actual) not in blob:
        err(f'docs never state the real {label} count ({actual})')


# ── 3. Plugin scripts must be referenced via ${CLAUDE_PLUGIN_ROOT} ───────────
PLUGIN_SCRIPTS = ("export_docx.py", "pub_style.py", "analysis_template.py",
                  "power_analysis.py", "assumption_tests.py")
for skill_md in (ROOT / "skills").glob("*/SKILL.md"):
    for ln, line in enumerate(skill_md.read_text(encoding="utf-8").splitlines(), 1):
        for script in PLUGIN_SCRIPTS:
            # an invocation/path reference (has a slash) but no plugin-root anchor
            if re.search(rf"\S*/{script}", line) and "CLAUDE_PLUGIN_ROOT" not in line:
                rel = skill_md.relative_to(ROOT)
                err(f"{rel}:{ln} references {script} without ${{CLAUDE_PLUGIN_ROOT}}")


# ── Report ───────────────────────────────────────────────────────────────────
if errors:
    print(f"❌ consistency check FAILED ({len(errors)} issue(s)):")
    for e in errors:
        print(f"   - {e}")
    sys.exit(1)

print(f"✅ consistency OK — v{VERSION}: "
      f"{n_skills} skills, {n_commands} commands, "
      f"{n_journals} journals, {n_standards} standards.")
