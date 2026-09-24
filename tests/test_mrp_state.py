"""Behaviour tests for skills/using-med-research-powers/scripts/mrp_state.py (the only writer of
.mrp-state.json and the user profile)."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "using-med-research-powers" / "scripts" / "mrp_state.py"


def run(tmp_path, *args, config=None):
    env = dict(os.environ, HOME=str(tmp_path / "home"))
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("CLAUDE_CONFIG_DIR", None)
    if config:
        env["CLAUDE_CONFIG_DIR"] = str(config)
    return subprocess.run([sys.executable, str(SCRIPT), "--dir", str(tmp_path / "proj"), *args],
                          capture_output=True, text=True, env=env)


def test_init_done_checkpoint_roundtrip(tmp_path):
    (tmp_path / "proj").mkdir()
    assert run(tmp_path, "init", "--project", "膀胱癌 CT").returncode == 0
    assert run(tmp_path, "done", "study-design", "--output", "study-protocol.md", "--next", "research-ethics").returncode == 0
    assert run(tmp_path, "checkpoint", "protocol", "confirmed").returncode == 0
    st = json.loads((tmp_path / "proj" / ".mrp-state.json").read_text(encoding="utf-8"))
    assert st["project"] == "膀胱癌 CT"
    assert (st["current_stage"], st["next_step"]) == ("study-design", "research-ethics")
    assert st["hard_checkpoints"]["protocol"].startswith("confirmed")
    assert "study-protocol.md" in st["artifacts"]


def test_a_state_file_that_is_not_an_object_gives_a_message_not_a_traceback(tmp_path):
    (tmp_path / "proj").mkdir()
    (tmp_path / "proj" / ".mrp-state.json").write_text("[1, 2, 3]", encoding="utf-8")
    proc = run(tmp_path, "show")
    assert proc.returncode != 0
    assert "Traceback" not in proc.stderr and "不是一个 JSON 对象" in proc.stderr


def test_profile_list_values_are_stripped_and_follow_claude_config_dir(tmp_path):
    (tmp_path / "proj").mkdir()
    config = tmp_path / "cfg"
    assert run(tmp_path, "profile", "set", "research_domains", "urology, radiology", config=config).returncode == 0
    prof = json.loads((config / "mrp-user-profile.json").read_text(encoding="utf-8"))
    values = [v for section in prof.values() if isinstance(section, dict) for v in section.get("research_domains", [])]
    assert values == ["urology", "radiology"]
    assert not (tmp_path / "home" / ".claude" / "mrp-user-profile.json").exists()
