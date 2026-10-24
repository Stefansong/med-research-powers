#!/usr/bin/env python3
"""Fetch ONE journal template instead of reading the whole library YAML (~5,000 lines).

Usage (the YAML is located relative to this script; cwd does not matter):
  get_journal_template.py --id european-urology [--json] [--overrides ./journal-overrides.yaml]
  get_journal_template.py --search urol            # fuzzy match on id / name → candidate list
  get_journal_template.py --list [--specialty urology]
A project-level overrides file (same `templates:` structure) is searched first; the
default ./journal-overrides.yaml is optional, an explicit --overrides path that does not
exist gives a warning. Ids match case-insensitively (an override `Nature` replaces the
library's `nature` in --id, --search and --list). An override entry carries the overrides
file's own `data_as_of` (none when the file has none) and `source: <overrides path>`.
An entry without `guidelines_checked` is unverified: --id prints one warning line on stderr,
--search / --list show it in the `checked` column (— = unverified) and print one warning line.
`special` items starting with "待核实" (values the last check could not confirm) are repeated
by --id in one more warning line on stderr.
The overrides file is untrusted project content: a symlink, anything that is not a regular file
(a FIFO or /dev/zero would hang) or a file over 1 MB is refused, never followed — the rules
mrp_state.py applies when `set target_journal=` reads the same file.
Exit code 0 = found, 1 = no matching journal, 2 = bad usage (one "Error: ..." line), a
missing PyYAML, or a missing / unreadable / unsafe / malformed file (--yaml library not found,
overrides that are not `templates:` + a list of entries with an `id`, invalid YAML, an
impossible date, nesting too deep) — reported as one "Error: ..." line, no traceback.
"""
import argparse, json, os, re, stat, sys

try:
    import yaml
except ImportError:
    print("Error: missing dependency PyYAML — install it with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

DEFAULT_YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "journal-templates.yaml")
LIST_KEYS = ("id", "journal", "IF_approx", "IF_year", "family", "category", "guidelines_checked")
LIST_HEAD = ("id", "journal", "IF_approx", "IF_year", "family", "category", "checked")
UNVERIFIED = ("limits not checked against the journal's current author guidelines; "
              "confirm on the journal site before relying on them")
OVERRIDES_MAX_BYTES = 1_000_000   # a real journal-overrides.yaml is a few KB (mrp_state.py: MAX_FILE_BYTES)
MAX_DEPTH = 20                    # the library nests 6 levels; much deeper data could not be printed (RecursionError)
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_NONBLOCK = getattr(os, "O_NONBLOCK", 0)


class TemplateFileError(Exception):
    """A template file that is missing (when required), unreadable, unsafe or malformed."""


def read_regular(path, limit):
    """Text of `path`, which must be a regular file of at most `limit` bytes. A symlink is never
    followed and nothing blocks (a FIFO or /dev/zero planted as the overrides file would hang)."""
    st = os.lstat(path)
    if stat.S_ISLNK(st.st_mode):
        raise TemplateFileError(f"{path} is a symbolic link; it is not followed (replace it with a regular file)")
    if not stat.S_ISREG(st.st_mode):
        raise TemplateFileError(f"{path} is not a regular file; it is not read")
    fd = os.open(path, os.O_RDONLY | _NOFOLLOW | _NONBLOCK)
    with os.fdopen(fd, "rb") as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise TemplateFileError(f"{path} is not a regular file; it is not read")
        raw = f.read(limit + 1)
    if len(raw) > limit:
        raise TemplateFileError(f"{path} is larger than {limit // 1_000_000} MB; not a journal template file")
    return raw.decode("utf-8-sig")


def too_deep(data, limit=MAX_DEPTH):
    """True if lists / mappings are nested more than `limit` levels (checked without recursion)."""
    stack = [(data, 1)]
    while stack:
        v, depth = stack.pop()
        if isinstance(v, (dict, list)):
            if depth > limit:
                return True
            stack.extend((x, depth + 1) for x in (v.values() if isinstance(v, dict) else v))
    return False


def load(path, required=False, untrusted=False):
    """Return (data_as_of, entries); each entry gets `category` from the '# ═══ / # NAME' banners.

    A missing file gives (None, []) unless required=True. Raises TemplateFileError when the file
    cannot be read, is not valid YAML, or is not `templates:` + a list of mappings with an `id`
    (a bare top-level list of such mappings is also accepted; an empty file means no entries).
    untrusted=True (the project's overrides file): a symlink, a non-regular file or a file over
    OVERRIDES_MAX_BYTES is refused, see read_regular().
    """
    if not path or not (os.path.lexists(path) if untrusted else os.path.exists(path)):
        if required:
            raise TemplateFileError(f"file not found: {path}")
        return None, []
    try:
        if untrusted:
            text = read_regular(path, OVERRIDES_MAX_BYTES)
        else:
            with open(path, encoding="utf-8") as f:
                text = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise TemplateFileError(f"cannot read {path}: {exc}") from None
    too_deep_msg = f"{path} nests lists / mappings more than {MAX_DEPTH} levels deep; not a journal template file"
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
        raise TemplateFileError(f"{path} is not valid YAML{where}: "
                                f"{getattr(exc, 'problem', None) or ' '.join(str(exc).split())}") from None
    except RecursionError:
        raise TemplateFileError(too_deep_msg) from None
    except Exception as exc:              # e.g. ValueError for an impossible date such as 2026-02-30
        raise TemplateFileError(f"{path} cannot be read as YAML: {' '.join(str(exc).split())}") from None
    if too_deep(data):
        raise TemplateFileError(too_deep_msg)
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
    cat, cats, prev = "", {}, ""
    for line in text.splitlines():
        if line.lstrip().startswith("#") and "═" in prev:
            cat = line.lstrip("# ").strip()
        if (m := re.match(r"^\s*- id:\s*(\S+)", line)):
            cats[m.group(1)] = cat
        prev = line
    for e in entries:
        e.setdefault("category", cats.get(e.get("id"), ""))
    return data_as_of, entries


def fail(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):            # one line on stderr, exit 2 (argparse prints a usage block)
        fail(f"{message} (see --help)")


def is_verified(entry):
    """D2: an entry counts as checked against the journal's guidelines only with guidelines_checked."""
    return bool(entry.get("guidelines_checked"))


def pending_items(entry):
    """`special` items marked 待核实 (values the last check could not confirm), without the marker."""
    special = entry.get("special") or []
    if not isinstance(special, list):
        special = [special]
    return [re.sub(r"^待核实\s*[:：]?\s*", "", str(s).strip()) for s in special if str(s).strip().startswith("待核实")]


def main(argv=None):
    ap = _Parser(description="Look up a journal template by id / keyword")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--id"), g.add_argument("--search"), g.add_argument("--list", action="store_true")
    ap.add_argument("--specialty", help="with --list: filter by category / id / name keyword")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--overrides", help="project overrides YAML (default: ./journal-overrides.yaml, optional)")
    ap.add_argument("--yaml", default=DEFAULT_YAML, help="library file (default: bundled)")
    a = ap.parse_args(argv)
    if a.specialty and not a.list:
        fail("--specialty only works with --list (use --search <keyword> on its own)")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ov_path = a.overrides or "journal-overrides.yaml"
    if a.overrides and not os.path.lexists(a.overrides):
        print(f"Warning: overrides file not found: {a.overrides}; using the library only", file=sys.stderr)
    try:
        ov_as_of, overrides = load(ov_path, untrusted=True)
    except TemplateFileError as exc:
        fail(f"overrides file: {exc}")
    try:
        data_as_of, library = load(a.yaml, required=True)
    except TemplateFileError as exc:
        fail(f"journal library (--yaml): {exc}")
    seen, entries = set(), []
    for e in [{"data_as_of": ov_as_of, **o, "source": ov_path} for o in overrides] + library:
        eid = str(e.get("id", "")).lower()   # overrides win on duplicate id, compared like --id
        if eid and eid not in seen:
            seen.add(eid), entries.append(e)
    if a.id:
        hit = next((e for e in entries if str(e.get("id", "")).lower() == a.id.lower()), None)
        if not hit:
            sys.exit(f"No template with id '{a.id}'. Try: --search {a.id.split('-')[0]}")
        if "source" not in hit:
            hit = {**hit, "data_as_of": data_as_of}
        print(json.dumps(hit, ensure_ascii=False, indent=2, default=str) if a.json
              else yaml.safe_dump(hit, allow_unicode=True, sort_keys=False, width=200), end="")
        if not is_verified(hit):
            print(f"Warning: '{hit['id']}' is unverified (no guidelines_checked) — {UNVERIFIED}", file=sys.stderr)
        if (pending := pending_items(hit)):
            print(f"Warning: '{hit['id']}' has {len(pending)} 待核实 item(s) — values the last check could not "
                  f"confirm; tell the user and confirm them on the journal site: {' | '.join(pending)}", file=sys.stderr)
        return
    key = (a.search or a.specialty or "").lower()
    pat = re.compile(r"(?<![a-z0-9])" + re.escape(key), re.I)  # keyword must start a word: "urol" ≠ "neurology"
    rows = [e for e in entries if not key or pat.search(f"{e.get('id')} {e.get('journal')} {e.get('category')}")]
    if not rows:
        sys.exit(f"No journal matches '{key}'. Try a shorter keyword, or add it to ./journal-overrides.yaml")
    if a.json:
        print(json.dumps([{k: e.get(k) for k in LIST_KEYS} for e in rows], ensure_ascii=False, indent=2, default=str))
    else:
        head = f"# {len(rows)} match(es); data_as_of: {data_as_of}"
        if any("source" in e for e in rows):
            head += f"\n# project overrides ({ov_path}): data_as_of: {ov_as_of or 'not given'}"
        print(head + "\n# IF_year None = a JCR 2022 value (library entries); checked = guidelines_checked (— = unverified)\n# "
              + " | ".join(LIST_HEAD))
        for e in rows:
            cells = [e.get(k) for k in LIST_KEYS]
            cells[-1] = cells[-1] or "—"
            print(" | ".join(str(c) for c in cells))
    unverified = sum(not is_verified(e) for e in rows)
    if unverified:
        print(f"Warning: {unverified} of {len(rows)} listed entries are unverified (checked —): {UNVERIFIED}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
