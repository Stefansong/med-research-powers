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

# TQ-3 / RC2-12: the noise must differ in every run (random * 1e-15 gave only ~73 distinct floats,
# so about 1 check in 70 saw two identical runs); a run counter kept outside --outputs makes it certain
FLOAT_NOISE = """
import os
n = int(open("count").read()) if os.path.exists("count") else 0
open("count", "w").write(str(n + 1))
os.makedirs("results", exist_ok=True)
x = 0.123456789 + (n + 1) * 1e-15
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
    # RC2-1: an earlier file the runs did not write again goes back to its place after the check
    assert (tmp_path / "results" / "old.csv").read_text(encoding="utf-8") == "from an earlier run\n"
    assert res["put_back"] == ["results/old.csv"]
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


def test_float_noise_recipe_differs_in_every_run(tmp_path):
    _write(tmp_path / "a.py", FLOAT_NOISE)
    import subprocess
    seen = set()
    for _ in range(5):
        subprocess.run([PY, "a.py"], cwd=str(tmp_path), check=True)
        seen.add((tmp_path / "results" / "table.csv").read_text(encoding="utf-8"))
    assert len(seen) == 5


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


# ─── regressions found in the first release audit ───────────────────────────────────

def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# a different value in every run, for certain (random.random() rounded to 2 decimals repeats 1 time in 100)
COUNTER = "import os\nn = int(open('count').read()) if os.path.exists('count') else 0\nopen('count', 'w').write(str(n + 1))\n"


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
    code, res = _runs(tmp_path, COUNTER + body.replace("LABEL", "'HR %.2f' % (1 + n / 100)"), "--outputs", "fig.svg")
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


# ─── regressions found in the follow-up audit (RC2-*, SEC-2, SEC-13, P:RC-5/6, CLI-1) ──────

WRITES_TABLE2 = "import os\nos.makedirs('results', exist_ok=True)\nopen('results/table2.csv', 'w').write('a\\n1\\n')\n"


# RC2-1 / SEC-2: --keep-last must never delete a file that only an earlier check folder still holds
def test_keep_last_never_deletes_a_file_the_runs_did_not_write_again(tmp_path):
    _write(tmp_path / "results" / "table2_v1.csv", "hand made\n")
    report = tmp_path / "r.md"
    for _ in range(3):
        code, res = _runs(tmp_path, WRITES_TABLE2, "--outputs", "results/", "--keep-last", "1", "--report", str(report))
        assert code == 0
        assert (tmp_path / "results" / "table2_v1.csv").read_text(encoding="utf-8") == "hand made\n"
        assert res["put_back"] == ["results/table2_v1.csv"]
    assert len(res["keep_root"]["pruned"]) == 1 and not res["keep_root"]["kept"]
    assert "已复制回原处" in report.read_text(encoding="utf-8")


def test_older_check_folders_with_files_not_in_place_are_kept(tmp_path):
    root = tmp_path / ".reproduce-check"
    legacy = {"status": "finished", "pid": 1, "started": 1.0}          # status file of an earlier version
    _write(root / "20240101-000000-only" / "pre-existing" / "results" / "only_copy.csv", "the only copy\n")
    _write(root / "20240101-000000-only" / rc.MARKER, json.dumps(legacy))
    _write(root / "20240102-000000-done" / "pre-existing" / "results" / "table2.csv", "a\n1\n")
    _write(root / "20240102-000000-done" / rc.MARKER, json.dumps(dict(legacy, started=2.0)))
    _write(root / "20240102-100000-edit" / "pre-existing" / "results" / "table2.csv", "a\n1 (corrected by hand)\n")
    _write(root / "20240102-100000-edit" / rc.MARKER, json.dumps(dict(legacy, started=2.5)))
    _write(root / "20240103-000000-busy" / rc.MARKER, json.dumps(dict(legacy, status="running", started=3.0)))
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, WRITES_TABLE2, "--outputs", "results/", "--keep-last", "1", "--report", str(report))
    assert code == 0
    assert res["keep_root"]["pruned"] == ["20240102-000000-done"]     # written again with the same content
    kept = {k["folder"]: k["why"] for k in res["keep_root"]["kept"]}
    assert set(kept) == {"20240101-000000-only", "20240102-100000-edit"}
    assert "内容不同" in kept["20240102-100000-edit"]                   # same name in place is not enough
    assert all("没有记录" in why for why in kept.values())              # the true reason: an earlier version's folders
    assert (root / "20240101-000000-only" / "pre-existing" / "results" / "only_copy.csv").is_file()
    assert (root / "20240102-100000-edit" / "pre-existing" / "results" / "table2.csv").is_file()
    assert (root / "20240103-000000-busy").is_dir()                   # an unfinished check is never touched
    text = report.read_text(encoding="utf-8")
    assert "没有按 --keep-last 删除" in text and "only_copy.csv" in text and "内容相同" in text


def test_a_file_that_cannot_go_back_keeps_its_check_folder(tmp_path):
    _write(tmp_path / "results" / "fit", "an earlier file called fit\n")
    body = "import os\nos.makedirs('results/fit', exist_ok=True)\nopen('results/fit/m.txt', 'w').write('1')\n"
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    assert code == 0 and res["not_put_back"] == [{"file": "results/fit", "why": "dir", "only_copy": True}]
    first = res["keep_dir"]
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--keep-last", "1")
    assert code == 0 and os.path.isfile(os.path.join(first, "pre-existing", "results", "fit"))
    assert [k["folder"] for k in res["keep_root"]["kept"]] == [os.path.basename(first)]


# SEC-13: --keep-dir pointing at an existing folder: folders that only look like checks are not deleted
def test_keep_last_only_deletes_folders_this_tool_made(tmp_path):
    backups = tmp_path / "backups"
    _write(backups / "20240101-120000-final" / "logs" / "notes.txt", "my notes\n")
    _write(backups / "20240101-120000-final" / "run1" / "x.csv", "mine\n")
    _write(backups / "20240101-130000-other" / "summary.docx", "mine too\n")
    _write(backups / "20240101-140000-odd" / "logs" / "a.txt", "mine as well\n")
    _write(backups / "20240101-140000-odd" / rc.MARKER, "{}")           # a status file this tool did not write
    for _ in range(2):
        code, res = _runs(tmp_path, "open('out.txt', 'w').write('1')\n", "--outputs", "out.txt",
                          "--keep-dir", "backups", "--keep-last", "1")
        assert code == 0
    assert (backups / "20240101-120000-final" / "logs" / "notes.txt").is_file()
    assert (backups / "20240101-130000-other" / "summary.docx").is_file()
    assert (backups / "20240101-140000-odd" / "logs" / "a.txt").is_file()
    assert res["keep_root"]["unmarked"] == ["20240101-120000-final"]
    assert [k["folder"] for k in res["keep_root"]["kept"]] == ["20240101-140000-odd"]
    assert not (backups / ".gitignore").exists()                      # an existing --keep-dir is not changed
    # a real check folder the user added a file to is not deleted either
    _write(tmp_path / "backups" / os.path.basename(res["keep_dir"]) / "my-review.md", "notes\n")
    code, res2 = _runs(tmp_path, "open('out.txt', 'w').write('1')\n", "--outputs", "out.txt",
                       "--keep-dir", "backups", "--keep-last", "1")
    kept = {k["folder"]: k["why"] for k in res2["keep_root"]["kept"]}
    assert set(kept) == {"20240101-140000-odd", os.path.basename(res["keep_dir"])}
    assert "my-review.md" in kept[os.path.basename(res["keep_dir"])]


# RC2-2: state the runs leave outside --outputs (a cache) is reported
def test_files_written_outside_the_outputs_are_reported(tmp_path):
    body = ("import os, random, pickle\nos.makedirs('cache', exist_ok=True)\n"
            "if os.path.exists('cache/fit.pkl'):\n    v = pickle.load(open('cache/fit.pkl', 'rb'))\n"
            "else:\n    v = random.random()\n    pickle.dump(v, open('cache/fit.pkl', 'wb'))\n"
            "os.makedirs('results', exist_ok=True)\nopen('results/t.csv', 'w').write('est\\n%r\\n' % v)\n")
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--report", str(report))
    assert code == 0 and res["changed_outside_outputs"] == ["cache/fit.pkl"]
    text = report.read_text(encoding="utf-8")
    assert "cache/fit.pkl" in text and "缓存" in text and "从头运行" not in text


# RC2-3: whatever a successful run leaves running is stopped before the next run
@pytest.mark.skipif(os.name != "posix", reason="POSIX process groups")
def test_background_processes_are_stopped_after_each_run(tmp_path):
    body = ("import os, subprocess, sys\nos.makedirs('results', exist_ok=True)\n"
            "subprocess.Popen([sys.executable, '-c', 'import os, time; time.sleep(1); "
            "os.makedirs(\"results\", exist_ok=True); open(\"results/late.csv\", \"w\").write(\"x\")'])\n"
            "open('results/t.csv', 'w').write('1')\n")
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    time.sleep(2)
    assert code == 0 and not (tmp_path / "results" / "late.csv").exists()
    assert res["runs"][0]["background_killed"] is True and any("后台进程" in w for w in res["warnings"])


# RC2-4: DOCX / PPTX are compared by their content, not by the time they were saved
def _office(path, part, xml, saved, zip_time):
    import zipfile
    core = ('<cp:coreProperties><dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified></cp:coreProperties>' % (saved, saved))
    with zipfile.ZipFile(path, "w") as z:
        for name, data in (("[Content_Types].xml", "<Types/>"), ("docProps/core.xml", core), (part, xml)):
            z.writestr(zipfile.ZipInfo(name, date_time=zip_time), data)
    return path


def test_docx_and_pptx_are_compared_by_content(tmp_path):
    doc = '<w:document><w:body><w:p><w:r><w:t>HR %s (95%% CI 1.1-2.0)</w:t></w:r></w:p></w:body></w:document>'
    a = _office(tmp_path / "a.docx", "word/document.xml", doc % "1.52", "2026-01-01T00:00:00Z", (2026, 1, 1, 0, 0, 0))
    b = _office(tmp_path / "b.docx", "word/document.xml", doc % "1.52", "2026-01-01T00:00:07Z", (2026, 1, 1, 0, 0, 8))
    r = rc.compare_file(a, b, 1e-12, 1e-12)
    assert r["equal"] is True and "按内容比较" in r["method"]
    c = _office(tmp_path / "c.docx", "word/document.xml", doc % "1.87", "2026-01-01T00:00:00Z", (2026, 1, 1, 0, 0, 0))
    r = rc.compare_file(a, c, 1e-12, 1e-12)
    assert r["equal"] is False and any("HR 1.87" in x for x in r["details"])
    sl = '<p:sld><a:p><a:r><a:t>%s</a:t></a:r></a:p></p:sld>'
    a = _office(tmp_path / "a.pptx", "ppt/slides/slide1.xml", sl % "n = 60", "2026-01-01T00:00:00Z", (2026, 1, 1, 0, 0, 0))
    b = _office(tmp_path / "b.pptx", "ppt/slides/slide1.xml", sl % "n = 60", "2026-02-01T00:00:00Z", (2026, 2, 1, 0, 0, 0))
    assert rc.compare_file(a, b, 1e-12, 1e-12)["equal"] is True
    assert ".docx" not in rc.EMBEDDED_TIME_EXTS


# RC2-5: a symlink inside an output is compared by where it points and never followed
@pytest.mark.skipif(not hasattr(os, "symlink") or os.name != "posix", reason="symlinks")
def test_symlinks_inside_outputs_are_not_followed(tmp_path):
    _write(tmp_path / "ext" / "patients.csv", "id,name\n1,secret\n")
    body = ("import os\nos.makedirs('results', exist_ok=True)\nopen('results/t.csv', 'w').write('1')\n"
            "os.symlink(os.path.abspath(TARGET), 'results/raw')\n")
    code, res = _runs(tmp_path, body.replace("TARGET", "'ext'"), "--outputs", "results/")
    assert code == 0 and res["comparison"]["identical"] == ["results/raw", "results/t.csv"]
    assert not [p for p in (tmp_path / ".reproduce-check").rglob("patients.csv")]     # outside data not copied
    assert os.path.islink(tmp_path / "results" / "raw")
    moving = COUNTER + body.replace("TARGET", "'ext%d' % n")
    code, res = _runs(tmp_path, moving, "--outputs", "results/")
    d = res["comparison"]["different"][0]
    assert code == 1 and d["file"] == "results/raw" and "符号链接" in d["method"]


# RC2-6: directories a run creates around a file output are removed before the next run
def test_directories_created_for_a_file_output_do_not_survive_into_the_next_run(tmp_path):
    body = "import os\nos.mkdir('out')\nos.mkdir('out/tables')\nopen('out/tables/t.csv', 'w').write('1')\n"
    code, res = _runs(tmp_path, body, "--outputs", "out/tables/t.csv")
    assert code == 0, res["messages"]
    assert (tmp_path / "out" / "tables" / "t.csv").is_file()


# RC2-7: --exclude is a shell glob: * does not cross directories, ** does
def test_exclude_patterns_follow_shell_glob_rules(tmp_path):
    ex = rc._excluded
    assert ex("results/x.pdf", ["results/*.pdf"]) and not ex("results/sub/y.pdf", ["results/*.pdf"])
    assert ex("results/sub/y.pdf", ["results/**/*.pdf"]) and ex("results/x.pdf", ["results/**/*.pdf"])
    assert ex("a/b/c.pdf", ["*.pdf"]) and not ex("a/b/x.csv", ["*/x.csv"]) and ex("a/x.csv", ["*/x.csv"])
    assert ex("results/figs/a.png", ["results/figs/"]) and ex("results/figs/a.png", ["./results/figs"])
    assert not ex("results/figs.png", ["results/figs/"]) and not ex("results/figsx/a.png", ["results/figs"])
    body = ("import os, time\nos.makedirs('results/sub', exist_ok=True)\nopen('results/t.csv', 'w').write('1')\n"
            "open('results/x.pdf', 'w').write(str(time.time()))\nopen('results/sub/y.pdf', 'w').write(str(time.time()))\n")
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--exclude", "results/*.pdf",
                      "--exclude", str(tmp_path / "results" / "sub" / "*.pdf"), "--exclude", "*.png")
    assert code == 0 and res["comparison"]["excluded"] == ["results/sub/y.pdf", "results/x.pdf"]
    assert any("'*.png'" in w and "没有匹配" in w for w in res["warnings"])


# RC2-8: results written to stderr (R message(), Python logging) can be compared
def test_compare_stderr(tmp_path):
    body = COUNTER + ("import logging\nlogging.basicConfig(format='%(message)s')\n"
                      "logging.warning('[SAP 4.1] HR %.4f', 1 + n / 100)\nopen('out.txt', 'w').write('1')\n")
    code, res = _runs(tmp_path, body, "--outputs", "out.txt")
    assert code == 0 and any("--compare-stderr" in w for w in res["warnings"])
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, body, "--outputs", "out.txt", "--compare-stderr", "--report", str(report))
    assert code == 1 and res["comparison"]["stderr"]["equal"] is False
    assert "(错误输出 stderr)" in report.read_text(encoding="utf-8")


# RC2-9: a run that fails because an input lived inside --outputs is explained
def test_a_failed_run_names_the_input_that_was_moved_out_of_the_outputs(tmp_path):
    _write(tmp_path / "results" / "clean.csv", "x\n1\n")
    body = "open('results/clean.csv').read()\nopen('results/t.csv', 'w').write('1')\n"
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    assert code == 2
    assert any("results/clean.csv" in m and "pre-existing" in m and "输入文件" in m for m in res["messages"])
    assert (tmp_path / "results" / "clean.csv").read_text(encoding="utf-8") == "x\n1\n"


# RC2-10: text outputs with other extensions are compared as text
def test_unlisted_text_extensions_are_compared_as_text(tmp_path):
    for name in ("fit.Rout", "est.smcl", "notes", "model.summary"):
        a, b = _write(tmp_path / "a" / name, "Call: lm\nHR = 0.511285\n"), _write(tmp_path / "b" / name, "Call: lm\nHR = 0.784403\n")
        r = rc.compare_file(a, b, 1e-12, 1e-12)
        assert r["equal"] is False and "+HR = 0.784403" in r["details"], name
    a, b = _write(tmp_path / "a.jsonl", '{"n": 60, "p": 0.1}\n{"n": 61}\n'), _write(tmp_path / "b.jsonl", '{"n": 60, "p": 0.1}\n{"n": 62}\n')
    r = rc.compare_file(a, b, 1e-12, 1e-12)
    assert r["equal"] is False and "JSON Lines" in r["method"] and r["details"] == ["第 2 行 $.n: 61 → 62"]
    a, b = tmp_path / "a.bin", tmp_path / "b.bin"
    a.write_bytes(b"\x00\x01text")
    b.write_bytes(b"\x00\x02text")
    assert rc.compare_file(a, b, 1e-12, 1e-12)["method"] == "sha256"


# RC2-11: zero-padded codes are text, not numbers
def test_zero_padded_codes_must_match_exactly(tmp_path):
    assert rc._cells_equal("007", "07", 1e-12, 1e-12) == "diff"
    assert rc._cells_equal("007", 7, 1e-12, 1e-12) == "diff"
    assert rc._cells_equal("1", "1.0", 1e-12, 1e-12) == "tol" and rc._cells_equal("0.5", "0.50", 1e-12, 1e-12) == "tol"
    a, b = _write(tmp_path / "a.csv", "id,v\n007,1\n"), _write(tmp_path / "b.csv", "id,v\n07,1\n")
    assert rc.compare_file(a, b, 1e-12, 1e-12)["equal"] is False
    a, b = _write(tmp_path / "a.txt", "patient 007: HR 1.2\n"), _write(tmp_path / "b.txt", "patient 07: HR 1.2\n")
    assert rc.compare_file(a, b, 1e-12, 1e-12)["equal"] is False


# P:RC-5: problems of the checker itself exit 2 (never 1, "differ") and leave a report
def test_checker_errors_exit_2_with_a_report_and_no_traceback(tmp_path, capsys, monkeypatch):
    _write(tmp_path / "a.py", "print(1)\n")
    _write(tmp_path / "results", "a file where the command expects a directory\n")
    code, res = _run(tmp_path, "--cmd", f'"{PY}" a.py > results/sub/out.txt', "--outputs", "results")
    assert code == 2 and any("results/sub" in m or "results" in m for m in res["messages"])
    if hasattr(os, "symlink") and os.name == "posix":
        os.symlink("loop_b", tmp_path / "loop_a")
        os.symlink("loop_a", tmp_path / "loop_b")
        capsys.readouterr()
        assert rc.main(["--cwd", str(tmp_path), "--outputs", "loop_a", "--", PY, "a.py"]) == 2
        err = capsys.readouterr().err                                 # Python < 3.13: resolve() raises on a loop
        assert "Traceback" not in err and len(err.strip().splitlines()) <= 1
    monkeypatch.setattr(rc, "_folder_size", lambda p: 1 / 0)          # housekeeping fails after a good check
    code, res = _runs(tmp_path, "open('out.txt', 'w').write('1')\n", "--outputs", "out.txt")
    assert code == 0 and any("整理副本目录" in m for m in res["messages"])


@pytest.mark.skipif(os.name != "posix", reason="POSIX signals")
def test_an_analysis_killed_by_a_signal_is_reported_as_such(tmp_path):
    body = "import os, signal\nopen('out.txt', 'w').write('1')\nos.kill(os.getpid(), signal.SIGSEGV)\n"
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, body, "--outputs", "out.txt", "--report", str(report))
    assert code == 2 and res["runs"][0]["signal"] == "SIGSEGV"
    assert "被信号 SIGSEGV 结束" in report.read_text(encoding="utf-8")


# P:RC-6: timestamps of the runs are differences whatever the tolerance; dates are spotted in more spellings
def test_run_timestamps_are_never_within_tolerance(tmp_path):
    body = ("import json, time\njson.dump({'n': 60, 'created': time.time(), 'ms': time.time() * 1000}, open('r.json', 'w'))\n"
            "time.sleep(0.2)\n")
    code, res = _runs(tmp_path, body, "--outputs", "r.json", "--rtol", "1e-6")
    assert code == 1 and any("时间戳" in x for x in res["comparison"]["different"][0]["details"])
    body = ("import datetime, os\nnow = datetime.datetime.now()\nos.makedirs('results', exist_ok=True)\n"
            "open('results/log.txt', 'w').write('run ' + now.strftime('%Y%m%d') + '\\n')\n"
            "open('results/when.txt', 'w').write('at ' + now.strftime('%H:%M') + '\\n')\n"
            "open('results/out_%s.csv' % now.strftime('%Y-%m-%d'), 'w').write('a\\n1\\n')\n")
    code, res = _runs(tmp_path, body, "--outputs", "results/")
    w = [x for x in res["warnings"] if "运行当天的日期" in x]
    assert code in (0, 1) and w and all(n in w[0] for n in ("log.txt", "when.txt", "results/out_"))   # 1: a new minute
    import datetime as dt
    rx = rc._date_regex({dt.date(2026, 10, 24)})
    for text in ("Sat Oct 24 03:21:00 2026", "October 24, 2026", "24 Oct 2026", "24OCT2026", "20261024_0321"):
        assert rx.search(text), text
    assert not rx.search("20261025") and not rx.search("Oct 25, 2026")


# CLI-1: invalid arguments are one line on stderr and exit 2
def test_invalid_arguments_are_one_line_and_exit_2(tmp_path, capsys):
    assert rc.main(["--cwd", str(tmp_path), "--outputs", "x", "--runs", "abc", "--", PY, "a.py"]) == 2
    err = capsys.readouterr().err.strip().splitlines()
    assert len(err) == 1 and "--runs" in err[0] and err[0].startswith("[重跑检查]")
    assert rc.main(["--cwd", str(tmp_path), "--", PY, "a.py"]) == 2                 # --outputs missing
    assert len(capsys.readouterr().err.strip().splitlines()) == 1


# RC2-13: code paths added in the previous round that no test reached
def test_signals_during_a_file_move_are_acted_on_after_it():
    with pytest.raises(rc.Interrupted) as e:
        with rc._Deferred():
            rc._on_signal(15, None)                                   # arrives mid-move: only noted
            assert rc._SIG["pending"] == 15
    assert e.value.signum == 15 and rc._SIG["pending"] is None and rc._SIG["defer"] == 0


@pytest.mark.skipif(os.name != "posix", reason="POSIX shell and tee")
def test_new_keep_dir_gets_a_gitignore_and_tee_targets_get_their_directory(tmp_path):
    _write(tmp_path / "a.py", "print('[SAP 1] n=60')\n")
    code, res = _run(tmp_path, "--cmd", f'"{PY}" a.py | tee results/log/out.txt', "--outputs", "results/",
                     "--keep-dir", "checks/new")
    assert code == 0 and res["comparison"]["identical"] == ["results/log/out.txt"]
    assert (tmp_path / "checks" / "new" / ".gitignore").is_file() and res["keep_root"]["gitignored"] is True
    assert rc._signal_of(-11, False) == "SIGSEGV" and rc._signal_of(139, True) == "SIGSEGV"
    assert rc._signal_of(139, False) is None and rc._signal_of(3, True) is None


# ─── regressions found when the follow-up fixes were verified ─────────────────────────

# a file that run 1 wrote but the last run did not: the pre-check version is not put back among the new outputs
def test_a_file_only_an_earlier_run_wrote_is_not_put_back(tmp_path, monkeypatch):
    _write(tmp_path / "results" / "extra.csv", "stale pre-check version\n")
    body = COUNTER + ("os.makedirs('results', exist_ok=True)\nopen('results/t.csv', 'w').write('a\\n1\\n')\n"
                      "if n == 0:\n    open('results/extra.csv', 'w').write('fresh from run 1\\n')\n")
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--report", str(report))
    assert code == 1 and res["put_back"] == [] and not (tmp_path / "results" / "extra.csv").exists()
    assert res["not_put_back"] == [{"file": "results/extra.csv", "why": "earlier_run", "only_copy": True}]
    text = report.read_text(encoding="utf-8")
    assert "较早的运行生成过" in text and "没有哪次运行重新生成" not in text and "目录" not in text.split("较早的运行")[1][:40]
    assert "文件集合的差异见上" in text and "## 不一致的文件" in text.split("较早的运行生成过")[0]
    first = os.path.basename(res["keep_dir"])
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--keep-last", "1")
    assert [k["folder"] for k in res["keep_root"]["kept"]] == [first]          # the stale version's only copy
    # a copy that fails is reported with its error, not as "a directory is there now"
    _write(tmp_path / "results" / "hand.csv", "made by hand\n")
    real = rc._copy_entry

    def failing(src, dst, stop):
        if "pre-existing" in str(src):
            raise OSError("disk full")
        return real(src, dst, stop)

    monkeypatch.setattr(rc, "_copy_entry", failing)
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--report", str(report))
    assert {"file": "results/hand.csv", "why": "OSError: disk full", "only_copy": True} in res["not_put_back"]
    text = report.read_text(encoding="utf-8")
    assert "disk full" in text and "那里现在是这次运行生成的目录" not in text


# --keep-last compares content, not only names: a hand-corrected table the analysis regenerates is kept
def test_keep_last_keeps_a_hand_edited_version_of_a_regenerated_file(tmp_path):
    _write(tmp_path / "results" / "table1.md", "| a | 1 | hand-corrected |\n")
    body = "import os\nos.makedirs('results', exist_ok=True)\nopen('results/table1.md', 'w').write('| a | 1 |\\n')\n"
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--report", str(report))
    assert code == 0 and res["pre_existing_replaced"] == ["results/table1.md"]
    assert "内容不同" in report.read_text(encoding="utf-8")
    first = os.path.basename(res["keep_dir"])
    for _ in range(2):
        code, res = _runs(tmp_path, body, "--outputs", "results/", "--keep-last", "1")
        assert code == 0 and [k["folder"] for k in res["keep_root"]["kept"]] == [first]
    assert len(res["keep_root"]["pruned"]) == 1                     # the second check: same content in place
    hits = [p for p in (tmp_path / ".reproduce-check").rglob("table1.md") if "hand-corrected" in p.read_text("utf-8")]
    assert len(hits) == 1


# every version that was in place when a check started survives --keep-last somewhere -- unless it was an
# earlier check's result: check 2's pre-check version (v1) is check 1's output and keeps no folder
@pytest.mark.parametrize("outside_run", [True, False])
def test_keep_last_never_deletes_the_only_copy_of_a_version(tmp_path, outside_run):
    if outside_run:
        _write(tmp_path / "results" / "t.csv", "from a run outside any check\n")
    body = ("import os\nos.makedirs('results', exist_ok=True)\n"
            "open('results/t.csv', 'w').write(open('version.txt').read())\n")
    names = []
    for v in ("v1", "v2", "v3"):                                     # the analysis changes between checks
        _write(tmp_path / "version.txt", v + "\n")
        code, res = _runs(tmp_path, body, "--outputs", "results/", *(["--keep-last", "1"] if v == "v3" else []))
        assert code == 0
        names.append(os.path.basename(res["keep_dir"]))
    kept = res["keep_root"]["kept"]
    contents = {p.read_text("utf-8") for p in tmp_path.rglob("t.csv")}
    if outside_run:      # check 1 holds the outside-run version (and v1 in its runs); check 2 only check 1's v1
        assert [k["folder"] for k in kept] == names[:1] and res["keep_root"]["pruned"] == names[1:2]
        assert "results/t.csv" in kept[0]["why"] and "在检查之外运行" in kept[0]["why"]
        assert {"from a run outside any check\n", "v1\n", "v2\n", "v3\n"} <= contents
    else:                # check 1 has nothing to keep, check 2 only check 1's result
        assert kept == [] and res["keep_root"]["pruned"] == names[:2]
        assert contents == {"v2\n", "v3\n"}                          # check 3: pre-existing/ and its runs


# RC2-2: a cache that already existed before the check (the analysis was run once) is reported too
def test_a_cache_that_existed_before_the_check_is_reported(tmp_path, monkeypatch):
    import subprocess
    body = ("import os, random, pickle\nos.makedirs('cache', exist_ok=True)\n"
            "if os.path.exists('cache/fit.pkl'):\n    v = pickle.load(open('cache/fit.pkl', 'rb'))\n"
            "else:\n    v = random.random()\n    pickle.dump(v, open('cache/fit.pkl', 'wb'))\n"
            "os.makedirs('results', exist_ok=True)\nopen('results/t.csv', 'w').write('est\\n%r\\n' % v)\n")
    _write(tmp_path / "a.py", body)
    _write(tmp_path / "data" / "raw.csv", "id,x\n1,2\n")
    _write(tmp_path / "src" / "cache.py", "# code, not a cache\n")
    _write(tmp_path / "env" / "pyvenv.cfg", "home = /usr/bin\n")      # a virtual environment with another name
    _write(tmp_path / "env" / "lib" / "requests_cache" / "x.sqlite", "")
    subprocess.run([PY, "a.py"], cwd=str(tmp_path), check=True)        # the user ran the analysis once
    code, res = _run(tmp_path, "--outputs", "results/", "--", PY, "a.py")
    assert code == 0 and res["changed_outside_outputs"] == [] and res["cache_like_outside_outputs"] == ["cache/fit.pkl"]
    assert any("cache/fit.pkl" in w and "名字像缓存" in w for w in res["warnings"])
    assert not any("raw.csv" in w for w in res["warnings"])
    # too many files to compare: said so, and caches are still found by name
    monkeypatch.setattr(rc, "TREE_MAX", 2)
    for i in range(3):
        _write(tmp_path / "data" / f"img{i}.dcm", "x")
    code, res = _run(tmp_path, "--outputs", "results/", "--", PY, "a.py")
    assert code == 0 and res["changed_outside_outputs"] is None and res["cache_like_outside_outputs"] == ["cache/fit.pkl"]
    assert any("文件太多" in w for w in res["warnings"])
    (tmp_path / "cache" / "fit.pkl").unlink()
    code, res = _run(tmp_path, "--outputs", "results/", "--", PY, "a.py")
    assert any("新建了 1 个名字像缓存的文件" in w and "cache/fit.pkl" in w for w in res["warnings"])
    assert rc._cache_like("report_cache/html/x.rdb") and rc._cache_like("_targets/objects/fit")
    assert rc._cache_like("data/model.joblib") and not rc._cache_like("data/raw.csv")
    assert not rc._cache_like("results_prev/a.csv")
    # the help and the docstring no longer say the runs start from scratch
    assert "从头" not in rc._parser().format_help() and "from scratch" not in rc.__doc__.split("\n\n")[0]


# Ctrl-C / SIGTERM while old check folders are pruned or measured: the report is still written
def test_an_interruption_during_housekeeping_still_writes_the_report(tmp_path, monkeypatch, capsys):
    def interrupted(path):
        raise KeyboardInterrupt

    monkeypatch.setattr(rc, "_folder_size", interrupted)
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, "open('out.txt', 'w').write('1')\n", "--outputs", "out.txt", "--report", str(report))
    assert code == 0 and report.is_file() and any("被中断（SIGINT）" in m for m in res["messages"])
    assert "检查还没有开始移动任何文件" not in capsys.readouterr().err
    assert rc._SIG == {"defer": 0, "pending": None, "keep": None}
    marker = json.loads((tmp_path / res["keep_dir"] / rc.MARKER).read_text(encoding="utf-8"))
    assert marker["status"] == "finished" and marker["exit_code"] == 0


@pytest.mark.skipif(os.name != "posix", reason="POSIX signals")
def test_a_signal_during_pruning_is_handled_by_the_checker(tmp_path):
    import subprocess
    _write(tmp_path / "a.py", "open('out.txt', 'w').write('1')\n")
    _write(tmp_path / "wrap.py", "import os, signal, sys\nsys.path.insert(0, sys.argv[1])\nimport reproduce_check as rc\n"
           "real = rc._prune\ndef prune(*a):\n    os.kill(os.getpid(), signal.SIGTERM)\n    return real(*a)\n"
           "rc._prune = prune\nsys.exit(rc.main(sys.argv[2:]))\n")
    args = [PY, "wrap.py", os.path.dirname(rc.__file__), "--outputs", "out.txt", "--keep-last", "1",
            "--report", "r.md", "--", PY, "a.py"]
    proc = subprocess.run(args, cwd=str(tmp_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    assert proc.returncode == 0, proc.stderr                          # not killed: the checker's handler ran
    text = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "被中断（SIGTERM）" in text and "只删了一部分" in text


# RC2-11: a zero-padded code is never the same as a number written another way
def test_zero_padded_codes_never_match_other_spellings(tmp_path):
    assert rc._cells_equal("007", "7.0", 1e-12, 1e-12) == "diff"
    assert rc._cells_equal("0123.5", "123.5", 1e-12, 1e-12) == "diff"
    assert rc._str_num_state("007", "7.0", 1e-12, 1e-12) == "diff"
    a, b = _write(tmp_path / "a.csv", "id,v\n007,1\n"), _write(tmp_path / "b.csv", "id,v\n7.0,1\n")
    assert rc.compare_file(a, b, 1e-12, 1e-12)["equal"] is False
    a, b = _write(tmp_path / "a.txt", "ward 0123.5\n"), _write(tmp_path / "b.txt", "ward 123.5\n")
    assert rc.compare_file(a, b, 1e-12, 1e-12)["equal"] is False


# ─── regressions found when the --keep-last fixes were verified (round 2) ─────────────

VERSIONED = ("import os, sys\nv = open('version.txt').read()\nif v == 'fail\\n':\n    sys.exit(3)\n"
             "os.makedirs('results', exist_ok=True)\nopen('results/t.csv', 'w').write(v)\n")


def _folders(tmp_path):
    return sorted(p.name for p in (tmp_path / ".reproduce-check").iterdir() if p.is_dir())


# --keep-last 1 keeps one check folder when the output changes between checks: the previous check's result,
# now in pre-existing/, is recorded as such and keeps no folder (before: 8 checks left 4 folders, each one
# reported as holding a possibly hand-edited only copy)
def test_keep_last_1_keeps_one_folder_when_the_output_changes_between_checks(tmp_path):
    report = tmp_path / "r.md"
    for v in ("v1", "v2", "fail", "v3", "v4"):          # a failed check copies its pre-existing/ back into place
        _write(tmp_path / "version.txt", v + "\n")
        code, res = _runs(tmp_path, VERSIONED, "--outputs", "results/", "--keep-last", "1", "--report", str(report))
        assert code == (2 if v == "fail" else 0), v
        assert _folders(tmp_path) == [os.path.basename(res["keep_dir"])], v
        assert res["keep_root"]["kept"] == [] and "没有按 --keep-last 删除" not in report.read_text(encoding="utf-8")
    keep = tmp_path / res["keep_dir"]
    pre = keep / "pre-existing" / "results" / "t.csv"
    marker = json.loads((keep / rc.MARKER).read_text(encoding="utf-8"))
    assert pre.read_text(encoding="utf-8") == "v3\n" and marker[rc.FROM_CHECKS] == {"results/t.csv": rc._sha256(pre)}
    assert res["pre_existing_from_checks"] == 1 and "其中 1 个是较早一次检查运行生成的结果" in report.read_text("utf-8")
    # a recorded copy that was changed afterwards is protected again, and the report says why
    pre.write_text("v3, corrected by hand in the copy\n", encoding="utf-8")
    _write(tmp_path / "version.txt", "v5\n")
    code, res2 = _runs(tmp_path, VERSIONED, "--outputs", "results/", "--keep-last", "1")
    kept = res2["keep_root"]["kept"]
    assert code == 0 and [k["folder"] for k in kept] == [keep.name] and "被改过" in kept[0]["why"]


# the same with a figure that embeds its save time (left out with --exclude) after the user ran the analysis once
# outside a check: only check 1, which holds that outside-run figure, is kept, and for that reason
def test_keep_last_1_with_an_excluded_timestamped_figure_keeps_only_the_outside_run_version(tmp_path):
    import subprocess
    _write(tmp_path / "a.py", "import os, time\nos.makedirs('results', exist_ok=True)\n"
           "open('results/t.csv', 'w').write('est\\n0.5\\n')\n"
           "open('results/fig.pdf', 'wb').write(b'%PDF-1.4 CreationDate ' + str(time.time_ns()).encode())\n")
    subprocess.run([PY, "a.py"], cwd=str(tmp_path), check=True)
    names = []
    for i in range(4):
        code, res = _run(tmp_path, "--outputs", "results/", "--exclude", "*.pdf", "--keep-last", "1", "--", PY, "a.py")
        assert code == 0
        names.append(os.path.basename(res["keep_dir"]))
        assert _folders(tmp_path) == sorted({names[0], names[-1]}), i
    kept = res["keep_root"]["kept"]
    assert [k["folder"] for k in kept] == names[:1]
    assert "results/fig.pdf" in kept[0]["why"] and "在检查之外运行" in kept[0]["why"] and "t.csv" not in kept[0]["why"]


CACHED_FIT = ("import os, random, pickle\nos.makedirs('cache', exist_ok=True)\n"
              "if os.path.exists('cache/fit.pkl'):\n    v = pickle.load(open('cache/fit.pkl', 'rb'))\n"
              "else:\n    v = random.random()\n    pickle.dump(v, open('cache/fit.pkl', 'wb'))\n"
              "os.makedirs('results', exist_ok=True)\nopen('results/t.csv', 'w').write('est\\n%r\\n' % v)\n")


# a project that is itself a Python / conda environment (`python -m venv .`) still has its cache found;
# an environment inside it is still skipped
@pytest.mark.parametrize("env", ["pyvenv.cfg", "conda-meta/history"])
def test_the_cache_scan_runs_when_the_project_itself_is_an_environment(tmp_path, env):
    _write(tmp_path / env, "")
    _write(tmp_path / "sub_env" / "pyvenv.cfg", "home = /usr/bin\n")
    _write(tmp_path / "sub_env" / "lib" / "cache" / "x.pkl", "")
    code, res = _runs(tmp_path, CACHED_FIT, "--outputs", "results/")
    assert code == 0 and res["changed_outside_outputs"] == ["cache/fit.pkl"]
    code, res = _run(tmp_path, "--outputs", "results/", "--", PY, "a.py")
    assert code == 0 and res["cache_like_outside_outputs"] == ["cache/fit.pkl"]
    assert any("cache/fit.pkl" in w and "名字像缓存" in w for w in res["warnings"])


# a file not put back because only an earlier run wrote it: when --exclude leaves it out of the comparison,
# the report does not point to a file-set difference "above" that is not there
def test_a_file_not_put_back_that_is_excluded_is_explained(tmp_path):
    _write(tmp_path / "results" / "extra.csv", "stale\n")
    body = COUNTER + ("os.makedirs('results', exist_ok=True)\nopen('results/t.csv', 'w').write('a\\n1\\n')\n"
                      "if n == 0:\n    open('results/extra.csv', 'w').write('fresh from run 1\\n')\n")
    report = tmp_path / "r.md"
    code, res = _runs(tmp_path, body, "--outputs", "results/", "--exclude", "results/extra.csv", "--report", str(report))
    assert code == 0 and [x["file"] for x in res["not_put_back"]] == ["results/extra.csv"]
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "没有放回原处" in ln)
    assert "见上" not in line and "--exclude 排除在比较之外" in line and "## 不一致的文件" not in text
