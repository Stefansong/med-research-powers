# MRP State & Profile Schemas

Two local JSON files, both written **only** by
`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`
(never edited by hand or by free-form Claude output, so the structure stays stable across sessions).

| File | Location | Scope | Who reads it |
|------|----------|-------|--------------|
| `.mrp-state.json` | project directory (`$CLAUDE_PROJECT_DIR`, else cwd) | one research project | session-start hook (5 string fields only), orchestrator, every main-line skill at its last step |
| `~/.claude/mrp-user-profile.json` | user's home directory | one person, all projects | `journal-selection`, `data-analysis-planning`, `figure-generation` — lazily, one field each |

Neither file is uploaded anywhere; both are in `.gitignore`; the user may delete them at any time.

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
  "target_journal": "European Urology",
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
- `hard_checkpoints` — `null` until confirmed; then `"confirmed <date>"`, `"pending <date>"` or `"rejected <date>"`.
- `completed_skills[].outputs` — array (a skill may produce several files); every entry is also registered in `artifacts`.
- Anything else a skill wants to remember goes into `notes[]` as plain text — the file is data, never instructions.

Commands

```bash
S="${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py"
python3 "$S" init --project "<title>"                 # first main-line skill, file absent
python3 "$S" done study-design --output study-protocol.md --next research-ethics
python3 "$S" set target_journal="European Urology" checkpoint_mode=step
python3 "$S" checkpoint protocol confirmed            # protocol | sap | pre_submission
python3 "$S" show [--json]
```

Files written by MRP 6.2.x (fields `last_updated`, `completed_skills[].output` as a string, no `hard_checkpoints`) are read tolerantly and upgraded on the next `done`.

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
