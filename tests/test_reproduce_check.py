import json
import os
import sys
import time

import pytest

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


# ─── regressions found in the release-6.4.1 audit ───────────────────────────────────

def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _runs(tmp_path, body, *argv, name="a.py"):
    _write(tmp_path / name, body)
    return _run(tmp_path, *argv, "--", PY, name)


# RC-1: naming an output path in the command must not fail the second check
def test_output_paths_named_in_the_command_do_not_block_a_recheck(tmp_path):
    _write(tmp_path / "analysis_script.py", "import sys, os\nprint('[SAP 4.1] n=60')\n"
           "d = sys.argv[1] if len(sys.argv) > 1 else 'results'\nos.makedirs(d, exist_ok=True)\n"
           "open(os.path.join(d, 't.csv'), 'w').write('a\\n1\\n')\n")
    redirect = f'"{PY}" analysis_script.py > results/stdout.txt'     # results/ does not exist yet
    for _ in range(3):                                            # first check and every re-check
        code, res = _run(tmp_path, "--cmd", redirect, "--outputs", "results/")
        assert code == 0, res["messages"]
    for _ in range(2):
        assert _run(tmp_path, "--cmd", f'"{PY}" analysis_script.py results', "--outputs", "results/")[0] == 0
        assert _run(tmp_path, "--outputs", "results/", "--", PY, "analysis_script.py", "results")[0] == 0


def test_a_script_inside_an_output_directory_is_refused_with_a_clear_message(tmp_path, capsys):
    _write(tmp_path / "results" / "a.py", "print(1)\n")
    assert rc.main(["--cwd", str(tmp_path), "--outputs", "results/", "--", PY, "results/a.py"]) == 2
    assert "脚本" in capsys.readouterr().err
    assert (tmp_path / "results" / "a.py").is_file()


def test_an_input_file_inside_an_output_directory_gets_a_hint_when_the_run_fails(tmp_path):
    _write(tmp_path / "results" / "clean.csv", "x\n1\n")
    code, res = _runs(tmp_path, "import sys\nopen(sys.argv[1]).read()\n", "--outputs", "results/")
    assert code == 2                                              # the input was moved aside, so run 1 fails
    code, res = _run(tmp_path, "--outputs", "results/", "--", PY, "a.py", "results/clean.csv")
    assert code == 2 and any("输入文件" in m for m in res["messages"])
    assert (tmp_path / "results" / "clean.csv").read_text(encoding="utf-8") == "x\n1\n"   # put back


def test_long_one_liner_tokens_do_not_crash(tmp_path):
    code = "open('out.txt','w').write('1')  # " + "x" * 400
    res_code, res = _run(tmp_path, "--outputs", "out.txt", "--", PY, "-c", code)
    assert res_code == 0 and res["comparison"]["identical"] == ["out.txt"]


# RC-2: an interrupted check stops the analysis and puts the earlier outputs back
@pytest.mark.skipif(os.name != "posix", reason="POSIX signals")
@pytest.mark.parametrize("sig", ["SIGINT", "SIGTERM"])
def test_interrupting_the_check_stops_the_analysis_and_restores_outputs(tmp_path, sig):
    import signal
    import subprocess
    _write(tmp_path / "results" / "final_table.csv", "earlier\n")
    _write(tmp_path / "a.py", "import os, time\nos.makedirs('results', exist_ok=True)\n"
           "open('results/partial.csv', 'w').write('x')\ntime.sleep(3)\n"
           "open('results/late.csv', 'w').write('late')\n")
    script = os.path.join(os.path.dirname(rc.__file__), "reproduce_check.py")
    proc = subprocess.Popen([PY, script, "--cwd", str(tmp_path), "--outputs", "results/", "--json", "rc.json",
                             "--", PY, "a.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline = time.time() + 20
    while not (tmp_path / "results" / "partial.csv").exists() and time.time() < deadline:
        time.sleep(0.05)
    proc.send_signal(getattr(signal, sig))
    proc.communicate(timeout=30)
    assert proc.returncode == 2
    time.sleep(4)                                                  # the analysis would have finished by now
    assert not (tmp_path / "results" / "late.csv").exists()        # it was stopped, not orphaned
    assert (tmp_path / "results" / "final_table.csv").read_text(encoding="utf-8") == "earlier\n"
    res = json.loads((tmp_path / "rc.json").read_text(encoding="utf-8"))
    assert res["interrupted"] is True and res["exit_code"] == 2
    assert os.path.isfile(os.path.join(res["keep_dir"], "run1-interrupted", "results", "partial.csv"))


def test_a_check_that_never_finished_is_reported_next_time(tmp_path):
    _write(tmp_path / "out.txt", "x")
    stale = tmp_path / ".reproduce-check" / "20240101-000000-abc"
    _write(stale / "pre-existing" / "out.txt", "moved aside long ago")
    _write(stale / rc.MARKER, json.dumps({"status": "running"}))
    code, res = _runs(tmp_path, "open('out.txt', 'w').write('1')\n", "--outputs", "out.txt")
    assert code == 0 and any("没有正常结束" in w and "20240101-000000-abc" in w for w in res["warnings"])


# RC-4: numbers printed to the screen are not silently ignored
PRINTS_RANDOM = """
import os, random
os.makedirs("results", exist_ok=True)
open("results/table.csv", "w").write("term,estimate\\nage,0.50\\n")
print("[SAP 4.1] 95%% CI %.6f" % random.random())
"""


def test_differing_stdout_is_a_warning_without_compare_stdout_and_a_failure_with_it(tmp_path):
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, PRINTS_RANDOM, "--outputs", "results/", "--report", str(report))
    assert code == 0
    assert any("--compare-stdout" in w and "[SAP 4.1]" in w for w in res["warnings"])
    text = report.read_text(encoding="utf-8")
    assert "需要留意" in text and "未计入结论" in text
    code, res = _runs(tmp_path, PRINTS_RANDOM, "--outputs", "results/", "--compare-stdout", "--report", str(report))
    assert code == 1
    cmp = res["comparison"]
    # RC-10: the stdout difference does not distort the file counts
    assert cmp["n_files"] == 1 and cmp["identical"] == ["results/table.csv"] and cmp["different"] == []
    assert cmp["stdout"]["equal"] is False and cmp["stdout"]["compared"] is True
    assert "(屏幕输出 stdout)" in report.read_text(encoding="utf-8")


# RC-5: unreadable outputs are reported as differences, not tracebacks
def test_mislabelled_and_huge_files_are_differences_not_crashes(tmp_path):
    body = ("import os, random\nos.makedirs('results', exist_ok=True)\n"
            "open('results/t.xlsx', 'w').write('a,b\\n%f\\n' % random.random())\n"
            "open('results/big.csv', 'w').write('note\\n' + 'x' * 200000 + '%f\\n' % random.random())\n")
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--report", str(report))
    assert code == 1 and report.is_file()
    diff = {d["file"]: d for d in res["comparison"]["different"]}
    assert "无法按xlsx读取" in diff["results/t.xlsx"]["method"]
    assert diff["results/big.csv"]["method"] == "逐单元格比较"


# RC-6: whole numbers and epoch timestamps are not hidden by the tolerance
def test_integers_must_match_exactly_and_timestamps_are_caught():
    assert rc._cells_equal("1000000000", "1000000001", 1e-9, 1e-12) == "diff"
    assert rc._cells_equal("1790000000.25", "1790000001.75", rc._parser().get_default("rtol"), 1e-12) == "diff"
    assert rc._cells_equal("0.1234567890123", "0.1234567890124", 1e-12, 1e-12) == "tol"
    assert rc._cells_equal("1", "1.0", 1e-12, 1e-12) == "tol"
    diffs = []
    rc._walk_json({"n": 60, "t": 1790000000.5}, {"n": 61, "t": 1790000002.0}, "$", diffs, 1e-12, 1e-12)
    assert len(diffs) == 2


def test_a_run_date_in_the_outputs_is_flagged(tmp_path):
    body = ("import datetime\nopen('log.txt', 'w').write('run at ' + "
            "datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + '\\n')\n")
    code, res = _runs(tmp_path, body, "--outputs", "log.txt")
    assert code == 0 and any("运行当天的日期" in w and "log.txt" in w for w in res["warnings"])


# RC-7: xlsx formulas are compared, not only cached values
def test_xlsx_formulas_that_differ_are_caught(tmp_path):
    pytest.importorskip("openpyxl")
    body = ("import os, random, openpyxl\nos.makedirs('results', exist_ok=True)\nwb = openpyxl.Workbook()\n"
            "ws = wb.active\nws.append(['term', 'est'])\nws.append(['age', '=ROUND(%r,4)' % random.random()])\n"
            "ws.append(['n', 60])\nwb.save('results/formula.xlsx')\n")
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    assert code == 1
    d = res["comparison"]["different"][0]
    assert d["file"] == "results/formula.xlsx" and "公式" in d["method"] and "=ROUND(" in d["details"][0]


def test_xlsx_with_identical_values_is_consistent(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.append(["a", 1.5, "=B1*2"])
    a, b = tmp_path / "a.xlsx", tmp_path / "b.xlsx"
    wb.save(a)
    wb.save(b)
    assert rc.compare_file(a, b, 1e-12, 1e-12)["equal"] is True


# RC-8: SVG ids / dates and gzip headers are not differences; hints are right
def test_svg_with_random_clip_ids_and_dates_is_consistent(tmp_path):
    body = ("import random, time\nr = '%010x' % random.getrandbits(40)\nlabel = LABEL\n"
            "open('fig.svg', 'w').write('<svg><metadata><dc:date>%s</dc:date></metadata>'\n"
            "  '<clipPath id=\"p%s\"/><g clip-path=\"url(#p%s)\"><text>%s</text></g></svg>\\n'\n"
            "  % (time.time(), r, r, label))\n")
    code, res = _runs(tmp_path, body.replace("LABEL", "'HR 1.52'"), "--outputs", "fig.svg")
    assert code == 0 and res["comparison"]["within_tolerance"][0]["file"] == "fig.svg"
    code, res = _runs(tmp_path, body.replace("LABEL", "'HR %.2f' % random.random()"), "--outputs", "fig.svg")
    assert code == 1 and "HR" in "".join(res["comparison"]["different"][0]["details"])


def test_gzip_outputs_are_compared_by_content(tmp_path):
    body = ("import gzip, os, random\nos.makedirs('results', exist_ok=True)\nvalue = VALUE\n"
            "with open('results/pred.csv.gz', 'wb') as f:\n"
            "    f.write(gzip.compress(('id,p\\n1,%s\\n' % value).encode(), mtime=random.randint(1, 2**31)))\n")
    code, res = _runs(tmp_path, body.replace("VALUE", "0.25"), "--outputs", "results/")
    assert code == 0 and "gzip" in res["comparison"]["within_tolerance"][0]["method"]
    code, res = _runs(tmp_path, body.replace("VALUE", "random.random()"), "--outputs", "results/")
    assert code == 1 and "逐单元格" in res["comparison"]["different"][0]["method"]


def test_exclude_leaves_files_out_and_hints_do_not_blame_png(tmp_path):
    body = ("import os, time\nos.makedirs('results', exist_ok=True)\n"
            "open('results/t.csv', 'w').write('a\\n1\\n')\nopen('results/fig.pdf', 'w').write(str(time.time()))\n")
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    assert code == 1 and "内嵌生成时间" in res["comparison"]["different"][0]["details"][1]
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--exclude", "*.pdf")
    assert code == 0 and res["comparison"]["excluded"] == ["results/fig.pdf"]
    assert "PNG" not in rc.HINTS[1] and "SOURCE_DATE_EPOCH" in rc.HINTS[1]
    assert ".svg" not in rc.EMBEDDED_TIME_EXTS


# RC-9: subdirectories that existed before stay in place; runs start from the same state
def test_existing_empty_subdirectories_stay_in_place(tmp_path):
    (tmp_path / "results" / "figs").mkdir(parents=True)
    code, res = _runs(tmp_path, "open('results/figs/f.txt', 'w').write('1')\n", "--outputs", "results/")
    assert code == 0 and (tmp_path / "results" / "figs" / "f.txt").is_file()
    body = "import os\nos.mkdir('results/new')\nopen('results/new/f.txt', 'w').write('1')\n"
    code, res = _runs(tmp_path, body, "--outputs", "results/")    # os.mkdir would fail if run 2 saw run 1's dir
    assert code == 0


def test_failure_in_run_2_puts_the_earlier_files_back(tmp_path):
    _write(tmp_path / "results" / "keep.csv", "earlier\n")
    body = ("import os, sys\nos.makedirs('results', exist_ok=True)\n"
            "open('results/t.csv', 'w').write('1')\nif os.path.exists('flag'):\n    sys.exit(4)\n"
            "open('flag', 'w').write('1')\n")
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    assert code == 2 and res["runs"][1]["returncode"] == 4
    assert sorted(os.listdir(tmp_path / "results")) == ["keep.csv"]
    assert (tmp_path / "results" / "keep.csv").read_text(encoding="utf-8") == "earlier\n"


# RC-10: report details
def test_launch_failure_json_types_crlf_and_paths_relative_to_cwd(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    code = rc.main(["--cwd", str(proj), "--outputs", "out.txt", "--report", "r.md", "--json", "r.json",
                    "--", "no_such_program_xyz_123"])
    assert code == 2
    res = json.loads((proj / "r.json").read_text(encoding="utf-8"))      # written under --cwd
    assert res["runs"][0]["launch_error"] and "无法启动" in (proj / "r.md").read_text(encoding="utf-8")
    assert "退出码 None" not in (proj / "r.md").read_text(encoding="utf-8")
    a, b = _write(tmp_path / "a.json", '{"a": true, "b": null}'), _write(tmp_path / "b.json", '{"a": 1, "b": 0}')
    assert len(rc.compare_file(a, b, 1e-12, 1e-12)["details"]) == 2
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_bytes(b"a\nb\n")
    b.write_bytes(b"a\r\nb\r\n")
    assert rc.compare_file(a, b, 1e-12, 1e-12)["details"] == ["只有换行符不同（\\r\\n 与 \\n）"]


def test_report_paths_are_guarded(tmp_path):
    _write(tmp_path / "a.py", "open('out.txt', 'w').write('1')\n")
    base = ["--cwd", str(tmp_path), "--outputs", "out.txt"]
    assert rc.main(base + ["--report", "x.md", "--json", "X.MD", "--", PY, "a.py"]) == 2      # same file
    assert rc.main(base + ["--report", "a.py", "--", PY, "a.py"]) == 2                        # the script
    assert rc.main(base + ["--report", "nodir/r.md", "--", PY, "a.py"]) == 2
    assert rc.main(["--cwd", str(tmp_path), "--outputs", "res/", "--report", "res/r.md", "--", PY, "a.py"]) == 2
    assert rc.main(base + ["--keep-dir", "out.txt", "--", PY, "a.py"]) == 2                   # keep-dir overlap
    assert rc.main(base + ["--timeout", "0", "--", PY, "a.py"]) == 2
    assert (tmp_path / "a.py").read_text(encoding="utf-8") == "open('out.txt', 'w').write('1')\n"


# RC-11: a process left behind by the command cannot keep the checker waiting
@pytest.mark.skipif(os.name != "posix", reason="POSIX sessions")
def test_a_detached_background_process_does_not_block_the_check(tmp_path):
    body = ("import subprocess, sys\nsubprocess.Popen([sys.executable, '-c', 'import time; time.sleep(15)'], "
            "start_new_session=True)\nopen('out.txt', 'w').write('1')\nprint('done')\n")
    t0 = time.time()
    code, res = _runs(tmp_path, body, "--outputs", "out.txt")
    assert code == 0 and time.time() - t0 < 12


# RC-12: the copies are git-ignored and can be pruned
def test_check_folders_are_gitignored_and_keep_last_prunes(tmp_path):
    for _ in range(3):
        code, res = _runs(tmp_path, "open('out.txt', 'w').write('1')\n", "--outputs", "out.txt")
    root = tmp_path / ".reproduce-check"
    assert (root / ".gitignore").read_text(encoding="utf-8").strip().endswith("*")
    assert len([p for p in root.iterdir() if p.is_dir()]) == 3 and res["keep_root"]["n_checks"] == 3
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, "open('out.txt', 'w').write('1')\n", "--outputs", "out.txt", "--keep-last", "1",
                      "--report", str(report))
    assert code == 0 and len(res["keep_root"]["pruned"]) == 3
    assert [p.name for p in root.iterdir() if p.is_dir()] == [os.path.basename(res["keep_dir"])]
    assert "--keep-last" in report.read_text(encoding="utf-8")


# TEST-1: comparison paths the earlier tests never reached
def test_json_text_numbers_file_sets_and_binary(tmp_path):
    a, b = _write(tmp_path / "a.json", '{"auc": 0.8100000000001, "n": 60, "l": [1, 2]}'), \
        _write(tmp_path / "b.json", '{"auc": 0.8100000000002, "n": 60, "l": [1, 2]}')
    r = rc.compare_file(a, b, 1e-9, 1e-12)
    assert r["equal"] is True and "JSON" in r["method"]
    b.write_text('{"auc": 0.9, "n": 60, "l": [1, 2, 3], "x": 1}', encoding="utf-8")
    assert len(rc.compare_file(a, b, 1e-9, 1e-12)["details"]) == 3
    a, b = _write(tmp_path / "a.txt", "HR=1.2345678901\nN=60\n"), _write(tmp_path / "b.txt", "HR=1.2345678902\nN=60\n")
    assert rc.compare_file(a, b, 1e-9, 1e-12)["equal"] is True
    b.write_text("HR=1.3\nN=61\n", encoding="utf-8")
    r = rc.compare_file(a, b, 1e-9, 1e-12)
    assert r["equal"] is False and "+HR=1.3" in r["details"]
    a, b = tmp_path / "a.rds", tmp_path / "b.rds"
    a.write_bytes(b"\x00\x01")
    b.write_bytes(b"\x00\x02")
    assert rc.compare_file(a, b, 1e-9, 1e-12)["method"] == "sha256"
    body = ("import os\nn = int(open('count').read()) if os.path.exists('count') else 0\n"
            "open('count', 'w').write(str(n + 1))\nos.makedirs('results', exist_ok=True)\n"
            "open('results/r%d.csv' % n, 'w').write('1')\n")
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    assert code == 1 and {d["method"] for d in res["comparison"]["different"]} == {"文件集合"}
    assert [d["file"] for d in res["comparison"]["different"]] == ["results/r0.csv", "results/r1.csv"]
