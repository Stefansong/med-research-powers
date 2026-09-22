"""Behaviour tests for hooks/session-start.sh.

The hook prints plain text into Claude's context and reads only the whitelisted
string fields of .mrp-state.json (see SECURITY.md). These tests pin both halves of
that contract, and in particular that the whitelisted fields are found whatever
indentation the state file happens to use.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "session-start.sh"

WHITELIST = ("project", "current_stage", "next_step", "target_journal", "checkpoint_mode")

pytestmark = pytest.mark.skipif(shutil.which("sh") is None, reason="POSIX sh not available")


def run_hook(project_dir):
    proc = subprocess.run(
        ["sh", str(HOOK)],
        cwd=str(project_dir),
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "CLAUDE_PROJECT_DIR": str(project_dir)},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


STATE = {
    "project": "PROJECT_MARKER",
    "current_stage": "study-design",
    "next_step": "research-ethics",
    "target_journal": "European Urology",
    "checkpoint_mode": "light",
    "not_a_field": "SECRET_MARKER",
    "artifacts": {"study-protocol.md": {"note": "SECRET_MARKER"}},
}


def test_no_state_file_prints_plain_text(tmp_path):
    out = run_hook(tmp_path)
    assert out.strip(), "hook printed nothing"
    # SessionStart hooks must print plain text, never a JSON object.
    assert not out.lstrip().startswith("{")
    assert "MRP project state found" not in out


@pytest.mark.parametrize(
    "dump",
    [
        pytest.param(lambda s: json.dumps(s, indent=2), id="indented"),
        pytest.param(lambda s: json.dumps(s), id="single-line"),
        pytest.param(lambda s: json.dumps(s, indent=2).replace("\n", "\r\n"), id="crlf"),
    ],
)
def test_whitelisted_fields_are_reported_for_any_formatting(tmp_path, dump):
    (tmp_path / ".mrp-state.json").write_text(dump(STATE), encoding="utf-8")
    out = run_hook(tmp_path)
    assert "MRP project state found" in out
    for name in WHITELIST:
        assert f"{name}:" in out
        assert STATE[name] in out, f"{name} not read from the state file"


@pytest.mark.parametrize(
    "dump",
    [
        pytest.param(lambda s: json.dumps(s, indent=2), id="indented"),
        pytest.param(lambda s: json.dumps(s), id="single-line"),
    ],
)
def test_non_whitelisted_fields_never_reach_the_context(tmp_path, dump):
    (tmp_path / ".mrp-state.json").write_text(dump(STATE), encoding="utf-8")
    out = run_hook(tmp_path)
    assert "SECRET_MARKER" not in out
    assert "not_a_field" not in out
    assert "artifacts" not in out


def test_values_are_truncated(tmp_path):
    state = dict(STATE, project="P" * 500)
    (tmp_path / ".mrp-state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    out = run_hook(tmp_path)
    assert "P" * 500 not in out
    longest = max(len(line) for line in out.splitlines())
    assert longest < 300, f"a state value was printed untruncated ({longest} chars)"


def test_bundled_example_state_is_readable(tmp_path):
    """The shipped example must render through the same code path."""
    example = ROOT / "examples" / "ai-bladder-ct" / ".mrp-state.json"
    if not example.exists():
        pytest.skip("example project not present")
    shutil.copy(example, tmp_path / ".mrp-state.json")
    out = run_hook(tmp_path)
    expected = json.loads(example.read_text(encoding="utf-8"))["project"][:80]
    assert expected in out
