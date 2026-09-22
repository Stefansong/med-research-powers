#!/usr/bin/env python3
"""
mrp_state.py — the only writer of MRP's two state files.

  Project state   ./.mrp-state.json            (one per research project; in the project directory)
  User profile    ~/.claude/mrp-user-profile.json   (one per person; shared by all projects)

Usage (run from the project directory, or pass --dir):

  # project state
  mrp_state.py init --project "AI bladder-cancer CT study"
  mrp_state.py done study-design --output study-protocol.md --next research-ethics
  mrp_state.py done statistical-analysis --output results-summary.md --output analysis-log.md \
                    --next figure-generation
  mrp_state.py set target_journal="European Urology" checkpoint_mode=light
  mrp_state.py checkpoint protocol confirmed        # protocol | sap | pre_submission
  mrp_state.py show [--json]

  # user profile (global, lazy — ask the user before writing)
  mrp_state.py profile get favorite_journals
  mrp_state.py profile set preferred_stats_tool R
  mrp_state.py profile add favorite_journals "European Urology"
  mrp_state.py profile show

Values are written verbatim as JSON strings; nothing in these files is ever executed.
Only Python's standard library is used.
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

STATE_NAME = ".mrp-state.json"
PROFILE_PATH = Path.home() / ".claude" / "mrp-user-profile.json"

STATE_SCALARS = {"project", "current_stage", "next_step", "checkpoint_mode", "target_journal"}
CHECKPOINTS = ("protocol", "sap", "pre_submission")
CHECKPOINT_MODES = ("light", "step", "auto")

PROFILE_LISTS = {
    ("profile", "research_domains"),
    ("preferences", "favorite_journals"),
    ("preferences", "methods_familiar"),
    ("preferences", "methods_unfamiliar"),
    ("history", "projects_completed"),
    ("history", "common_reviewer_feedback"),
}
PROFILE_SECTIONS = {
    "profile": ["role", "research_domains", "expertise_level"],
    "preferences": ["favorite_journals", "preferred_stats_tool", "preferred_figure_style",
                    "methods_familiar", "methods_unfamiliar", "checkpoint_mode", "language"],
    "history": ["projects_completed", "common_reviewer_feedback", "skills_most_used"],
}


# ── helpers ────────────────────────────────────────────────────────────────────
def today() -> str:
    return date.today().isoformat()


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"无法读取 {path}: {e}")


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def state_path(args) -> Path:
    base = args.dir or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(base) / STATE_NAME


def empty_state(project: str) -> dict:
    return {
        "schema_version": 1,
        "project": project,
        "created": today(),
        "updated": today(),
        "current_stage": "",
        "next_step": "research-question-formulation",
        "checkpoint_mode": "light",
        "target_journal": "",
        "hard_checkpoints": {k: None for k in CHECKPOINTS},
        "completed_skills": [],
        "artifacts": {},
        "notes": [],
    }


def load_state(args, must_exist=True) -> dict:
    p = state_path(args)
    if not p.exists():
        if must_exist:
            sys.exit(f"{p} 不存在——先运行: mrp_state.py init --project \"<项目名>\"")
        return empty_state("")
    st = load_json(p, None)
    # tolerate files written by hand or by 6.2.x
    st.setdefault("schema_version", 1)
    st.setdefault("hard_checkpoints", {k: None for k in CHECKPOINTS})
    st.setdefault("completed_skills", [])
    st.setdefault("artifacts", {})
    st.setdefault("notes", [])
    st.setdefault("checkpoint_mode", "light")
    st.setdefault("target_journal", "")
    st.setdefault("next_step", "")
    st.setdefault("current_stage", "")
    return st


def write_state(args, st: dict) -> None:
    st["updated"] = today()
    save_json(state_path(args), st)


def empty_profile() -> dict:
    return {
        "schema_version": 1,
        "updated": today(),
        "profile": {"role": "", "research_domains": [], "expertise_level": ""},
        "preferences": {"favorite_journals": [], "preferred_stats_tool": "",
                        "preferred_figure_style": "", "methods_familiar": [],
                        "methods_unfamiliar": [], "checkpoint_mode": "light", "language": "zh"},
        "history": {"projects_completed": [], "common_reviewer_feedback": [], "skills_most_used": {}},
    }


def find_section(field: str):
    for section, fields in PROFILE_SECTIONS.items():
        if field in fields:
            return section
    return None


# ── project-state commands ─────────────────────────────────────────────────────
def cmd_init(args):
    p = state_path(args)
    if p.exists() and not args.force:
        sys.exit(f"{p} 已存在（用 --force 覆盖，或用 show 查看）")
    st = empty_state(args.project)
    if args.checkpoint_mode:
        st["checkpoint_mode"] = args.checkpoint_mode
    write_state(args, st)
    print(f"已创建 {p}")


def cmd_done(args):
    st = load_state(args)
    entry = {"skill": args.skill, "date": today(), "outputs": list(args.output or [])}
    st["completed_skills"].append(entry)
    for out in entry["outputs"]:
        st["artifacts"][out] = {"skill": args.skill, "date": today()}
    st["current_stage"] = args.stage or args.skill
    if args.next is not None:
        st["next_step"] = args.next
    if args.note:
        st["notes"].append({"date": today(), "skill": args.skill, "note": args.note})
    write_state(args, st)
    print(f"已记录 {args.skill} 完成；current_stage={st['current_stage']}; next_step={st['next_step']}")


def cmd_set(args):
    st = load_state(args)
    for kv in args.pairs:
        if "=" not in kv:
            sys.exit(f"格式应为 key=value，收到: {kv}")
        k, v = kv.split("=", 1)
        if k not in STATE_SCALARS:
            sys.exit(f"不允许直接设置的字段: {k}（允许: {', '.join(sorted(STATE_SCALARS))}）")
        if k == "checkpoint_mode" and v not in CHECKPOINT_MODES:
            sys.exit(f"checkpoint_mode 只能是 {CHECKPOINT_MODES}")
        st[k] = v
    write_state(args, st)
    print("已更新: " + ", ".join(args.pairs))


def cmd_checkpoint(args):
    st = load_state(args)
    st["hard_checkpoints"][args.name] = f"{args.status} {today()}"
    write_state(args, st)
    print(f"硬确认 {args.name}: {st['hard_checkpoints'][args.name]}")


def cmd_show(args):
    p = state_path(args)
    if not p.exists():
        print(f"没有 {p}（新项目）")
        return
    st = load_state(args)
    if args.json:
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return
    print(f"项目: {st.get('project') or '(未命名)'}")
    print(f"当前阶段: {st.get('current_stage') or '(尚未开始)'}")
    print(f"下一步: {st.get('next_step') or '(未设置)'}")
    print(f"确认方式: {st.get('checkpoint_mode')}    目标期刊: {st.get('target_journal') or '(未定)'}")
    hc = st.get("hard_checkpoints", {})
    print("硬确认: " + ", ".join(f"{k}={v or '未确认'}" for k, v in hc.items()))
    done = st.get("completed_skills", [])
    if done:
        print("已完成:")
        for e in done:
            outs = ", ".join(e.get("outputs", [])) or "-"
            print(f"  {e.get('date','')}  {e.get('skill','')}  → {outs}")
    if st.get("notes"):
        print(f"备注 {len(st['notes'])} 条（show --json 查看）")


# ── profile commands ───────────────────────────────────────────────────────────
def cmd_profile(args):
    prof = load_json(PROFILE_PATH, None) or empty_profile()
    if args.pcmd == "show":
        print(json.dumps(prof, ensure_ascii=False, indent=2))
        return
    if args.pcmd == "path":
        print(PROFILE_PATH)
        return
    section = find_section(args.field)
    if section is None:
        sys.exit(f"未知字段: {args.field}（可用: " +
                 ", ".join(f for fs in PROFILE_SECTIONS.values() for f in fs) + ")")
    prof.setdefault(section, {})
    if args.pcmd == "get":
        val = prof[section].get(args.field)
        if val in (None, "", [], {}):
            print("")          # empty → the skill should ask the user
            sys.exit(3)        # exit 3 = missing, distinguishable from errors
        print(json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val)
        return
    if args.pcmd == "set":
        if (section, args.field) in PROFILE_LISTS:
            prof[section][args.field] = [v for v in args.value.split(",") if v.strip()]
        else:
            prof[section][args.field] = args.value
    elif args.pcmd == "add":
        if (section, args.field) not in PROFILE_LISTS:
            sys.exit(f"{args.field} 不是列表字段，请用 set")
        lst = prof[section].setdefault(args.field, [])
        if args.value not in lst:
            lst.append(args.value)
    prof["updated"] = today()
    save_json(PROFILE_PATH, prof)
    print(f"已写入 {PROFILE_PATH}: {args.field}")


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser():
    ap = argparse.ArgumentParser(description="MRP project state / user profile helper")
    ap.add_argument("--dir", help="项目目录（默认 $CLAUDE_PROJECT_DIR 或当前目录）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="创建 .mrp-state.json")
    s.add_argument("--project", required=True)
    s.add_argument("--checkpoint-mode", choices=CHECKPOINT_MODES)
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("done", help="记录某个 skill 完成")
    s.add_argument("skill")
    s.add_argument("--output", action="append", help="产物文件，可重复")
    s.add_argument("--next", help="下一步 skill")
    s.add_argument("--stage", help="current_stage（默认 = skill 名）")
    s.add_argument("--note")
    s.set_defaults(func=cmd_done)

    s = sub.add_parser("set", help="设置标量字段 key=value")
    s.add_argument("pairs", nargs="+")
    s.set_defaults(func=cmd_set)

    s = sub.add_parser("checkpoint", help="记录硬确认")
    s.add_argument("name", choices=CHECKPOINTS)
    s.add_argument("status", choices=["confirmed", "pending", "rejected"])
    s.set_defaults(func=cmd_checkpoint)

    s = sub.add_parser("show", help="显示状态")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("profile", help="全局用户画像 ~/.claude/mrp-user-profile.json")
    s.add_argument("pcmd", choices=["get", "set", "add", "show", "path"])
    s.add_argument("field", nargs="?")
    s.add_argument("value", nargs="?")
    s.set_defaults(func=cmd_profile)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "profile" and args.pcmd in ("get", "set", "add"):
        if not args.field or (args.pcmd in ("set", "add") and args.value is None):
            sys.exit("用法: profile get <field> | profile set <field> <value> | profile add <field> <value>")
    args.func(args)


if __name__ == "__main__":
    main()
