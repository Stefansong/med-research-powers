#!/usr/bin/env python3
"""Fetch ONE journal template instead of reading the whole 3,600-line YAML.

Usage (the YAML is located relative to this script; cwd does not matter):
  get_journal_template.py --id european-urology [--json] [--overrides ./journal-overrides.yaml]
  get_journal_template.py --search urol            # fuzzy match on id / name → candidate list
  get_journal_template.py --list [--specialty urology]
A project-level overrides file (same `templates:` structure) is searched first.
Exit code 0 = found, 1 = not found or bad usage.
"""
import argparse, json, os, re, sys

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency PyYAML: pip install pyyaml")

DEFAULT_YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "journal-templates.yaml")
LIST_KEYS = ("id", "journal", "IF_approx", "family", "category")


def load(path):
    """Return (data_as_of, entries); each entry gets `category` from the '# ═══ / # NAME' banners."""
    if not path or not os.path.exists(path):
        return None, []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    data = yaml.safe_load(text) or {}
    entries = data if isinstance(data, list) else data.get("templates") or []
    cat, cats, prev = "", {}, ""
    for line in text.splitlines():
        if line.lstrip().startswith("#") and "═" in prev:
            cat = line.lstrip("# ").strip()
        if (m := re.match(r"^\s*- id:\s*(\S+)", line)):
            cats[m.group(1)] = cat
        prev = line
    for e in entries:
        e.setdefault("category", cats.get(e.get("id"), ""))
    return (None if isinstance(data, list) else data.get("data_as_of")), entries


def main():
    ap = argparse.ArgumentParser(description="Look up a journal template by id / keyword")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--id"), g.add_argument("--search"), g.add_argument("--list", action="store_true")
    ap.add_argument("--specialty", help="with --list: filter by category / id / name keyword")
    ap.add_argument("--json", action="store_true"), ap.add_argument("--overrides", default="journal-overrides.yaml")
    ap.add_argument("--yaml", default=DEFAULT_YAML, help="library file (default: bundled)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _, overrides = load(a.overrides)
    data_as_of, library = load(a.yaml)
    seen, entries = set(), []
    for e in overrides + library:  # overrides win on duplicate id
        if e.get("id") and e["id"] not in seen:
            seen.add(e["id"]), entries.append(e)
    if a.id:
        hit = next((e for e in entries if str(e.get("id", "")).lower() == a.id.lower()), None)
        if not hit:
            sys.exit(f"No template with id '{a.id}'. Try: --search {a.id.split('-')[0]}")
        hit = {**hit, "data_as_of": data_as_of}
        print(json.dumps(hit, ensure_ascii=False, indent=2) if a.json
              else yaml.safe_dump(hit, allow_unicode=True, sort_keys=False, width=200), end="")
        return
    key = (a.search or a.specialty or "").lower()
    pat = re.compile(r"(?<![a-z0-9])" + re.escape(key), re.I)  # keyword must start a word: "urol" ≠ "neurology"
    rows = [e for e in entries if not key or pat.search(f"{e.get('id')} {e.get('journal')} {e.get('category')}")]
    if not rows:
        sys.exit(f"No journal matches '{key}'. Try a shorter keyword, or add it to ./journal-overrides.yaml")
    if a.json:
        print(json.dumps([{k: e.get(k) for k in LIST_KEYS} for e in rows], ensure_ascii=False, indent=2))
    else:
        print(f"# {len(rows)} match(es); data_as_of: {data_as_of}\n# " + " | ".join(LIST_KEYS))
        for e in rows:
            print(" | ".join(str(e.get(k)) for k in LIST_KEYS))


if __name__ == "__main__":
    main()
