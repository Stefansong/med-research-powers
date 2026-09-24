import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "statistical-analysis", "scripts"))
import reproduce_check as rc  # noqa: E402

PY = sys.executable

DETERMINISTIC = """
import json, os, random
random.seed(20240101)
os.makedirs("results", exist_ok=True)
with open("results/table.csv", "w") as f:
    f.write("term,estimate\\n")
    for t in ("age", "sex"):
        f.write("%s,%.6f\\n" % (t, random.random()))
json.dump({"n": 60, "auc": 0.81}, open("results/summary.json", "w"))
open("summary.txt", "w").write("N=60\\n")
"""

UNSEEDED = """
import os, random
os.makedirs("results", exist_ok=True)
with open("results/table.csv", "w") as f:
    f.write("term,estimate\\nage,%.12f\\n" % random.random())
open("summary.txt", "w").write("N=60\\n")
"""

FLOAT_NOISE = """
import os, random
os.makedirs("results", exist_ok=True)
x = 0.123456789 + random.random() * 1e-15
with open("results/table.csv", "w") as f:
    f.write("term,estimate\\nage,%r\\n" % x)
"""


def _project(tmp_path, name, body):
    (tmp_path / name).write_text(body, encoding="utf-8")
    return f'"{PY}" {name}'


def _run(tmp_path, *argv):
    """Run the checker inside tmp_path (options go before any `--`) and return (exit code, JSON result)."""
    js = tmp_path / "rc.json"
    if js.exists():
        js.unlink()
    code = rc.main(["--cwd", str(tmp_path), "--json", str(js)] + list(argv))
    return code, json.loads(js.read_text(encoding="utf-8")) if js.exists() else None


def test_deterministic_script_is_consistent_and_outputs_stay_in_place(tmp_path):
    cmd = _project(tmp_path, "analysis_script.py", DETERMINISTIC)
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "old.csv").write_text("from an earlier run\n", encoding="utf-8")
    code, res = _run(tmp_path, "--cmd", cmd, "--outputs", "results/", "summary.txt")
    assert code == 0 and res["exit_code"] == 0
    assert len(res["comparison"]["identical"]) == 3 and not res["comparison"]["different"]
    # last run's outputs are where the script wrote them
    assert (tmp_path / "results" / "table.csv").is_file() and (tmp_path / "summary.txt").is_file()
    assert not (tmp_path / "results" / "old.csv").exists()
    keep = res["keep_dir"]
    # earlier outputs were moved, not deleted; every run has a copy
    assert open(os.path.join(keep, "pre-existing", "results", "old.csv"), encoding="utf-8").read() == "from an earlier run\n"
    for k in (1, 2):
        assert os.path.isfile(os.path.join(keep, f"run{k}", "results", "table.csv"))


def test_unseeded_random_numbers_are_reported(tmp_path):
    cmd = _project(tmp_path, "analysis_script.py", UNSEEDED)
    report = tmp_path / "reproduce-check.md"
    code, res = _run(tmp_path, "--cmd", cmd, "--outputs", "results", "summary.txt", "--report", str(report))
    assert code == 1
    assert [d["file"] for d in res["comparison"]["different"]] == ["results/table.csv"]
    assert res["comparison"]["identical"] == ["summary.txt"]
    text = report.read_text(encoding="utf-8")
    assert "不一致" in text and "results/table.csv" in text and "[estimate]" in text and "随机种子" in text
    assert (tmp_path / "results" / "table.csv").is_file()


def test_float_noise_is_within_tolerance_unless_tolerance_is_zero(tmp_path):
    cmd = _project(tmp_path, "analysis_script.py", FLOAT_NOISE)
    code, res = _run(tmp_path, "--cmd", cmd, "--outputs", "results/")
    assert code == 0 and [d["file"] for d in res["comparison"]["within_tolerance"]] == ["results/table.csv"]
    code, _ = _run(tmp_path, "--cmd", cmd, "--outputs", "results/", "--rtol", "0", "--atol", "0")
    assert code == 1


def test_command_after_double_dash_and_three_runs(tmp_path):
    _project(tmp_path, "analysis_script.py", DETERMINISTIC)
    code, res = _run(tmp_path, "--outputs", "results", "summary.txt", "--runs", "3", "--", PY, "analysis_script.py")
    assert code == 0 and len(res["runs"]) == 3


def test_failed_run_returns_2_and_puts_previous_outputs_back(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "keep.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (tmp_path / "summary.txt").write_text("old summary\n", encoding="utf-8")
    code, res = _run(tmp_path, "--cmd", f'"{PY}" -c "import sys; sys.exit(3)"', "--outputs", "results/", "summary.txt")
    assert code == 2 and res["runs"][0]["returncode"] == 3
    assert (tmp_path / "results" / "keep.csv").read_text(encoding="utf-8") == "a,b\n1,2\n"
    assert (tmp_path / "summary.txt").read_text(encoding="utf-8") == "old summary\n"


def test_timeout_counts_as_failed_run(tmp_path):
    t0 = time.time()
    code, res = _run(tmp_path, "--cmd", f'"{PY}" -c "import time; time.sleep(30)"', "--outputs", "results/",
                     "--timeout", "1")
    assert code == 2 and res["runs"][0]["timed_out"] is True
    assert time.time() - t0 < 20


def test_guards(tmp_path):
    cmd = _project(tmp_path, "analysis_script.py", DETERMINISTIC)
    assert rc.main(["--cmd", cmd, "--outputs", ".", "--cwd", str(tmp_path)]) == 2            # the project itself
    assert rc.main(["--cmd", cmd, "--outputs", "results", "results/table.csv", "--cwd", str(tmp_path)]) == 2
    assert rc.main(["--cmd", cmd, "--outputs", "results", "--cwd", str(tmp_path), "--", PY, "x.py"]) == 2
    assert rc.main(["--cmd", cmd, "--outputs", "results", "--runs", "1", "--cwd", str(tmp_path)]) == 2
    assert rc.main(["--cmd", cmd, "--outputs", "tables/", "--cwd", str(tmp_path)]) == 2       # never produced
    assert (tmp_path / "analysis_script.py").is_file()


def test_outputs_outside_the_project_are_refused(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "a.py").write_text("print(1)\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere.csv"
    elsewhere.write_text("keep me\n", encoding="utf-8")
    code = rc.main(["--cwd", str(proj), "--outputs", str(elsewhere), "--", PY, "a.py"])
    assert code == 2
    assert elsewhere.read_text(encoding="utf-8") == "keep me\n"          # untouched


def test_earlier_files_come_back_when_an_output_is_never_produced(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "a.py").write_text("open('real.txt', 'w').write('1')\n", encoding="utf-8")
    (proj / "typo.csv").write_text("earlier result\n", encoding="utf-8")
    code = rc.main(["--cwd", str(proj), "--outputs", "real.txt", "typo.csv", "--", PY, "a.py"])
    assert code == 2
    assert (proj / "typo.csv").read_text(encoding="utf-8") == "earlier result\n"
