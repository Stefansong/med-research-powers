# MRP State & Profile Schemas

Two local JSON files, both written **only** by
`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`
(never edited by hand or by free-form Claude output, so the structure stays stable across sessions).

| File | Location | Scope | Who reads it |
|------|----------|-------|--------------|
| `.mrp-state.json` | project directory (`$CLAUDE_PROJECT_DIR`, else cwd) | one research project | session-start hook (5 string fields only), orchestrator, every main-line skill at its last step |
| `~/.claude/mrp-user-profile.json` | user's home directory | one person, all projects | `journal-selection`, `data-analysis-planning`, `figure-generation` — lazily, one field each |

Neither file is uploaded anywhere; the user may delete them at any time. Only the plugin's own repository
git-ignores them: in a research project kept in git, add `.mrp-state.json` to that project's `.gitignore`
if the repository is shared (the profile lives outside the project).

`mrp_state.py` never follows a symlink: if `.mrp-state.json`, `.mrp-state.json.tmp`, the profile or the
project's `journal-overrides.yaml` is a symlink or not a regular file (a FIFO, a device), it stops with one
line on stderr (exit 2) and changes nothing. Files are written to a newly created `.tmp` file and then moved
into place. A file over 1 MB, or with lists / objects nested more than 20 levels deep, is refused the same way.

---

## `.mrp-state.json` — project state (schema_version 1)

```json
{
  "schema_version": 1,
  "project": "AI-assisted bladder-cancer detection on CT",
  "created": "2026-09-21",
  "updated": "2026-09-21",
  "current_stage": "study-design",
  "next_step": "research-ethics",
  "checkpoint_mode": "light",
  "target_journal": "european-urology",
  "hard_checkpoints": {
    "protocol": "confirmed 2026-09-21",
    "sap": null,
    "pre_submission": null
  },
  "completed_skills": [
    {"skill": "research-question-formulation", "date": "2026-09-20", "outputs": ["research-question.md"]},
    {"skill": "literature-synthesis", "date": "2026-09-20", "outputs": ["search-strategy.md", "literature-synthesis-summary.md"]},
    {"skill": "study-design", "date": "2026-09-21", "outputs": ["study-protocol.md"]}
  ],
  "artifacts": {
    "research-question.md": {"skill": "research-question-formulation", "date": "2026-09-20"},
    "study-protocol.md": {"skill": "study-design", "date": "2026-09-21"}
  },
  "notes": [
    {"date": "2026-09-21", "skill": "study-design", "note": "Primary outcome locked: AUROC on external test set"}
  ]
}
```

Field rules

- `current_stage` — name of the last completed main-line skill (or a free-text stage such as "用户收集数据中").
- `next_step` — name of the next skill in the pipeline; the hook shows it verbatim.
- `checkpoint_mode` — `light` (default) | `step` | `auto`; see the orchestrator's 确认方式 table.
- `target_journal` — the journal's **library id** (the `id` in `journal-templates.yaml`, or in the project's
  `journal-overrides.yaml`), so that `get_journal_template.py --id`, `export_docx.py --journal` and
  `pub_style.setup(journal=...)` can use it directly. `set target_journal=` also accepts the journal's full
  name (case-insensitive, e.g. "European Urology") and stores its id; a journal in neither file is refused
  with a pointer to `get_journal_template.py --search <keyword>`. Empty = not chosen yet.
  `journal-overrides.yaml` is read with PyYAML exactly as `get_journal_template.py` reads it (`templates:` +
  a list of entries with an `id`; a file it refuses is refused here too). Without PyYAML only the library
  is searched (one line says so). An id containing control characters, backticks or `< >` is refused.
- `hard_checkpoints` — `null` until confirmed; then `"confirmed <date>"`, `"pending <date>"` or `"rejected <date>"`.
- `completed_skills[].outputs` — array (a skill may produce several files); every entry is also registered in `artifacts`.
- `notes[]` — `{"date": "<YYYY-MM-DD>", "skill": "<skill, or empty>", "note": "<text>"}`, oldest first. Anything else a skill wants to remember goes here as plain text — the file is data, never instructions. Written by `note` (a note only: nothing is marked completed, `current_stage` / `next_step` stay) or `done --note`; the text is stored cleaned like `show` cleans it (line breaks become a space) and cut to 480 UTF-8 bytes.

Commands

```bash
S="${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py"
python3 "$S" init --project "<title>"                 # optional: names the project
python3 "$S" done study-design --output study-protocol.md --next research-ethics
python3 "$S" set target_journal=european-urology checkpoint_mode=step   # a full journal name is resolved to its id
python3 "$S" checkpoint protocol confirmed            # protocol | sap | pre_submission
python3 "$S" note "SAP 前看过：按治疗分组的 KM 图（exploratory）" --skill figure-generation   # a note only; marks nothing completed
python3 "$S" show [--json]
```

- `done`, `set`, `checkpoint` and `note` create the file when it does not exist yet (and say so in one line), so a
  skill's last step works whichever skill the user started with; `init` is only needed to name the project
  up front (`set project="<title>"` names it later).
- `show` / `show --json` print the state **as data** (a "not instructions" label; `--json` adds a `_notice`
  key) with the SessionStart hook's cleaning: control characters, invisible characters (zero-width, bidi,
  soft hyphen, variation selectors, Hangul fillers, the Unicode tag characters and the rest of
  U+E0000–U+E0FFF, every category-Cf character and every other default-ignorable code point — the same
  set as the SessionStart hook, see SECURITY.md), backticks and `< >` removed, each value cut to 160
  UTF-8 bytes (notes to 480) without
  splitting a character. Only the fields above are printed — any other key (also one named `_notice`) is
  counted, not shown — with the newest 50 `completed_skills` (10 outputs each), 100 `artifacts` and 20
  `notes`, at most 32 KB in all; what was left out is counted in `_not_shown` (text mode: a `未显示` line). Text mode prints the newest 5 notes and says how many more `show --json` has.
- Exit codes: 0 = done, 2 = error (bad usage, a command-line argument that is not UTF-8, or a state / profile
  file that is unsafe, not UTF-8, not JSON, has a field of the wrong type or an integer of more than 4300
  digits — one line on stderr, no traceback, nothing written, no `.tmp` file left), 3 = `profile get`: field
  not set. A UTF-8 BOM is accepted. Text holding a lone UTF-16 surrogate (a JSON escape such as `\ud800` that is
  not half of a pair) cannot be stored as UTF-8: `show` drops it, a write, `profile get` and `profile show`
  stop with exit 2 and name the field to correct. A write that would make the file larger than 1 MB is
  refused the same way.

Files written by MRP 6.2.x (fields `last_updated`, `completed_skills[].output` as a string, no `hard_checkpoints`) are read tolerantly and upgraded on the next write (`done` / `set` / `checkpoint`).

---

## `~/.claude/mrp-user-profile.json` — user profile (schema_version 1)

```json
{
  "schema_version": 1,
  "updated": "2026-09-21",
  "profile": {
    "role": "PI",
    "research_domains": ["urologic oncology", "medical AI"],
    "expertise_level": "senior"
  },
  "preferences": {
    "favorite_journals": ["European Urology", "Lancet Digital Health"],
    "preferred_stats_tool": "R",
    "preferred_figure_style": "nature",
    "methods_familiar": ["Cox regression", "deep learning"],
    "methods_unfamiliar": ["Bayesian analysis"],
    "checkpoint_mode": "light",
    "language": "zh"
  },
  "history": {
    "projects_completed": ["AI bladder-cancer CT (Radiology, 2026)"],
    "common_reviewer_feedback": ["needs external validation"],
    "skills_most_used": {}
  }
}
```

Collection rules

- **Lazy**: nothing is asked at session start. A skill that needs a field runs
  `mrp_state.py profile get <field>`; exit code 3 means "not set" → ask that one question → offer to save with
  `profile set <field> <value>` (scalars) or `profile add <field> <value>` (lists).
- Other fields are filled only when the user volunteers the information.
- Never store passwords, patient-level data or ethics-approval numbers.
- "忘记我的 X" → `profile set <field> ""`; deleting the file resets everything.
