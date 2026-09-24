#!/usr/bin/env python3
"""
reproduce_check.py -- run an analysis from scratch several times and check that it
writes the same output files every time (statistical-analysis Step 5, self-check).

Usage
  python3 reproduce_check.py --cmd "python3 analysis_script.py" --outputs results/ tables/results.csv
  python3 reproduce_check.py --outputs results/ --runs 3 --report reproduce-check.md -- Rscript analysis.R

What it does
  1. Outputs that already exist are MOVED (never deleted) to <keep-dir>/pre-existing/ so that
     run 1 really starts from scratch. Output directories stay in place (emptied), because
     many scripts expect them to exist.
  2. The command runs in a fresh subprocess (--cwd, --timeout). After every run except the
     last, its outputs are moved to <keep-dir>/run<k>/. The last run's outputs stay where the
     script wrote them; a copy goes to <keep-dir>/run<N>/.
  3. The runs are compared: the set of files and the sha256 of every file; CSV/TSV cell by
     cell with a float tolerance (--rtol / --atol); JSON value by value with the same
     tolerance; .txt/.md/.log etc. as text (numbers within tolerance count as equal,
     otherwise the first 20 changed lines are shown); .xlsx cell values. Other files
     (PDF, PNG, RDS ...) are compared by sha256 only.
  4. If a run fails, its partial outputs go to <keep-dir>/run<k>-failed/ and the previous
     outputs are copied back into place.

--outputs paths are relative to --cwd. <keep-dir> defaults to <cwd>/.reproduce-check/<time>/.
Exit code: 0 identical (within tolerance) · 1 outputs differ · 2 a run failed / nothing to compare.
"""

import argparse
import csv
import datetime as _dt
import difflib
import hashlib
import io
import json
import math
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TABLE_SEPS = {".csv": ",", ".tsv": "\t", ".tab": "\t"}
TEXT_EXTS = {".txt", ".md", ".log", ".tex", ".html", ".htm", ".svg", ".xml", ".yaml", ".yml",
             ".rmd", ".qmd", ".out"}
EMBEDDED_TIME_EXTS = {".pdf", ".png", ".xlsx", ".docx", ".pptx", ".svg"}
_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
NUM_RE = re.compile(_NUM)
PLAIN_NUM_RE = re.compile(rf"^\s*{_NUM}\s*$")
MAX_LINES = 20

HINTS = (
    "未固定随机种子：Python 的 random.seed / numpy.random.default_rng(seed) / sklearn 的 random_state / "
    "torch.manual_seed，R 的 set.seed()——bootstrap、多重插补、交叉验证、机器学习都用到随机数",
    "输出依赖当前时间：结果里写了运行日期时间、文件名带时间戳；PDF/PNG/XLSX 会内嵌保存时间"
    "（matplotlib 可用 savefig(..., metadata={'CreationDate': None})，或设环境变量 SOURCE_DATE_EPOCH）",
    "多线程或 GPU 的非确定性：并行求和的顺序不同会带来末位差异；可设 OMP_NUM_THREADS=1、"
    "OPENBLAS_NUM_THREADS=1 重跑验证，确属浮点末位差异时再适当放宽 --rtol",
    "读取了会变的文件：运行中下载数据、读取上游仍在更新的文件、把上一次的输出当成输入",
    "顺序不固定：遍历集合（set）、os.listdir / glob 的结果没有排序",
)


# ─── files ──────────────────────────────────────────────────────────────────

class Output:
    """One --outputs entry: a file or a directory, located relative to --cwd."""

    def __init__(self, raw, cwd):
        p = Path(raw).expanduser()
        self.raw = raw
        self.path = (p if p.is_absolute() else cwd / p).resolve()
        try:
            self.rel = self.path.relative_to(cwd).as_posix()
        except ValueError:
            self.rel = "_outside_cwd/" + "/".join(self.path.parts[1:])


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _files_at(root):
    """{sub_path: Path} for a file ('' key) or every file under a directory."""
    if root.is_file():
        return {"": root}
    if root.is_dir():
        return {p.relative_to(root).as_posix(): p for p in sorted(root.rglob("*")) if p.is_file()}
    return {}


def _collect(outputs, base=None):
    """All output files, keyed by their path relative to --cwd (base=None: the live location)."""
    found = {}
    for o in outputs:
        loc = o.path if base is None else base / o.rel
        for sub, p in _files_at(loc).items():
            found[o.rel + ("/" + sub if sub else "")] = p
    return found


def _move_out(outputs, dest):
    """Move current outputs into dest/<rel>. Directories stay in place, emptied. Returns #files."""
    n = 0
    for o in outputs:
        target = dest / o.rel
        if o.path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            for child in sorted(o.path.iterdir()):
                n += len(_files_at(child)) if child.is_dir() else 1
                shutil.move(str(child), str(target / child.name))
        elif o.path.exists() or o.path.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(o.path), str(target))
            n += 1
    return n


def _copy_out(outputs, dest):
    for o in outputs:
        target = dest / o.rel
        if o.path.is_dir():
            shutil.copytree(o.path, target, dirs_exist_ok=True)
        elif o.path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(o.path, target)


def _copy_back(outputs, src):
    """Copy a snapshot (src/<rel>) back to the live locations."""
    for o in outputs:
        snap = src / o.rel
        if snap.is_dir():
            o.path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(snap, o.path, dirs_exist_ok=True)
        elif snap.is_file():
            o.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snap, o.path)


# ─── running ────────────────────────────────────────────────────────────────

def _kill(proc):
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)       # the whole process group (shell + children)
        else:
            proc.kill()
    except OSError:
        proc.kill()


def run_once(cmd, shell, cwd, timeout, log_dir, k):
    t0 = time.time()
    kw = {"cwd": str(cwd), "stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "shell": shell}
    if os.name == "posix":
        kw["start_new_session"] = True
    try:
        proc = subprocess.Popen(cmd, **kw)
    except OSError as e:
        res = {"run": k, "returncode": None, "timed_out": False, "seconds": 0.0, "stdout": "", "stderr": str(e)}
    else:
        try:
            out, err = proc.communicate(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            _kill(proc)
            out, err = proc.communicate()
            timed_out = True
        res = {"run": k, "returncode": None if timed_out else proc.returncode, "timed_out": timed_out,
               "seconds": round(time.time() - t0, 1),
               "stdout": out.decode("utf-8", "replace"), "stderr": err.decode("utf-8", "replace")}
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"run{k}.stdout.txt").write_text(res["stdout"], encoding="utf-8")
    (log_dir / f"run{k}.stderr.txt").write_text(res["stderr"], encoding="utf-8")
    res["ok"] = res["returncode"] == 0
    return res


# ─── comparing ──────────────────────────────────────────────────────────────

def _close(a, b, rtol, atol):
    if math.isnan(a) and math.isnan(b):
        return True
    return math.isclose(a, b, rel_tol=rtol, abs_tol=atol)


def _as_float(s):
    return float(s) if isinstance(s, str) and PLAIN_NUM_RE.match(s) else None


def _read_text(path):
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "gbk"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def _cells_equal(va, vb, rtol, atol):
    """-> 'same' | 'tol' | 'diff' for two cell values (str / number / other)."""
    if va == vb:
        return "same"
    fa = float(va) if isinstance(va, (int, float)) and not isinstance(va, bool) else _as_float(va)
    fb = float(vb) if isinstance(vb, (int, float)) and not isinstance(vb, bool) else _as_float(vb)
    if fa is not None and fb is not None and _close(fa, fb, rtol, atol):
        return "tol"
    return "diff"


def _compare_grid(ra, rb, rtol, atol, where=""):
    details, n_diff, n_tol = [], 0, 0
    if len(ra) != len(rb):
        details.append(f"{where}行数不同：{len(ra)} → {len(rb)}")
        n_diff += abs(len(ra) - len(rb))
    header = [str(h) for h in ra[0]] if ra else []
    for i, (row_a, row_b) in enumerate(zip(ra, rb)):
        row_a, row_b = list(row_a), list(row_b)
        if len(row_a) != len(row_b):
            details.append(f"{where}第 {i + 1} 行列数不同：{len(row_a)} → {len(row_b)}")
            n_diff += 1
        for j, (va, vb) in enumerate(zip(row_a, row_b)):
            state = _cells_equal(va, vb, rtol, atol)
            if state == "tol":
                n_tol += 1
            elif state == "diff":
                n_diff += 1
                if len(details) < MAX_LINES:
                    col = header[j] if i > 0 and j < len(header) else f"第 {j + 1} 列"
                    details.append(f"{where}第 {i + 1} 行 [{col}]：{va!r} → {vb!r}")
    return details, n_diff, n_tol


def compare_table(a, b, sep, rtol, atol):
    ra = list(csv.reader(io.StringIO(_read_text(a)), delimiter=sep))
    rb = list(csv.reader(io.StringIO(_read_text(b)), delimiter=sep))
    details, n_diff, n_tol = _compare_grid(ra, rb, rtol, atol)
    return {"method": "逐单元格比较", "equal": n_diff == 0, "n_diff": n_diff, "n_within_tol": n_tol,
            "details": details}


def compare_xlsx(a, b, rtol, atol):
    try:
        import openpyxl
    except ImportError:
        return {"method": "sha256（未安装 openpyxl，无法逐单元格比较）", "equal": False, "n_diff": None,
                "details": ["xlsx 内含保存时间，建议分析脚本另存一份 CSV 供比较"]}
    wa = openpyxl.load_workbook(a, read_only=True, data_only=True)
    wb = openpyxl.load_workbook(b, read_only=True, data_only=True)
    try:
        details, n_diff, n_tol = [], 0, 0
        if wa.sheetnames != wb.sheetnames:
            details.append(f"工作表不同：{wa.sheetnames} → {wb.sheetnames}")
            n_diff += 1
        for name in wa.sheetnames:
            if name not in wb.sheetnames:
                continue
            d, nd, nt = _compare_grid(list(wa[name].iter_rows(values_only=True)),
                                      list(wb[name].iter_rows(values_only=True)), rtol, atol, f"[{name}] ")
            details += d
            n_diff += nd
            n_tol += nt
    finally:
        wa.close()
        wb.close()
    return {"method": "逐单元格比较（xlsx 取值，忽略内嵌保存时间）", "equal": n_diff == 0, "n_diff": n_diff,
            "n_within_tol": n_tol, "details": details[:MAX_LINES]}


def _walk_json(x, y, path, out, rtol, atol):
    if len(out) >= 200:
        return
    if isinstance(x, bool) or isinstance(y, bool) or x is None or y is None:
        if x != y:
            out.append(f"{path}: {x!r} → {y!r}")
    elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
        if not _close(float(x), float(y), rtol, atol):
            out.append(f"{path}: {x!r} → {y!r}")
    elif isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y), key=str):
            if k not in x or k not in y:
                out.append(f"{path}.{k}: 只在其中一次运行中出现")
            else:
                _walk_json(x[k], y[k], f"{path}.{k}", out, rtol, atol)
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            out.append(f"{path}: 列表长度 {len(x)} → {len(y)}")
        for i, (u, v) in enumerate(zip(x, y)):
            _walk_json(u, v, f"{path}[{i}]", out, rtol, atol)
    elif x != y:
        out.append(f"{path}: {x!r} → {y!r}")


def compare_text(a, b, rtol, atol):
    ta, tb = _read_text(a), _read_text(b)
    if ta == tb:
        return {"method": "文本", "equal": True, "details": []}
    na, nb = NUM_RE.findall(ta), NUM_RE.findall(tb)
    if NUM_RE.split(ta) == NUM_RE.split(tb) and len(na) == len(nb) and \
            all(_close(float(u), float(v), rtol, atol) for u, v in zip(na, nb)):
        return {"method": "文本（数字按容差比较）", "equal": True, "details": ["只有数字的末位不同，在容差内"]}
    changed = [ln for ln in difflib.unified_diff(ta.splitlines(), tb.splitlines(), lineterm="", n=0)
               if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
    return {"method": "文本 diff", "equal": False, "n_diff": len(changed), "details": changed[:MAX_LINES]}


def compare_json(a, b, rtol, atol):
    try:
        ja, jb = json.loads(_read_text(a)), json.loads(_read_text(b))
    except ValueError:
        return compare_text(a, b, rtol, atol)
    diffs = []
    _walk_json(ja, jb, "$", diffs, rtol, atol)
    return {"method": "JSON 逐值比较（数字按容差）", "equal": not diffs, "n_diff": len(diffs),
            "details": diffs[:MAX_LINES]}


def compare_file(a, b, rtol, atol):
    ext = Path(a).suffix.lower()
    if ext in TABLE_SEPS:
        return compare_table(a, b, TABLE_SEPS[ext], rtol, atol)
    if ext == ".json":
        return compare_json(a, b, rtol, atol)
    if ext in (".xlsx", ".xlsm"):
        return compare_xlsx(a, b, rtol, atol)
    if ext in TEXT_EXTS:
        return compare_text(a, b, rtol, atol)
    note = ["二进制文件内容不同，无法逐项比较"]
    if ext in EMBEDDED_TIME_EXTS:
        note.append("这类文件常内嵌生成时间：确认内容相同后，可让脚本去掉时间戳再比较")
    return {"method": "sha256", "equal": False, "n_diff": None, "details": note}


def compare_runs(snapshots, outputs, rtol, atol):
    maps = [_collect(outputs, base=s) for s in snapshots]
    names = sorted(set().union(*[set(m) for m in maps])) if maps else []
    res = {"n_files": len(names), "identical": [], "within_tolerance": [], "different": []}
    for rel in names:
        missing = [i + 1 for i, m in enumerate(maps) if rel not in m]
        if missing:
            res["different"].append({"file": rel, "method": "文件集合", "equal": False,
                                     "details": [f"第 {'、'.join(map(str, missing))} 次运行没有生成这个文件"]})
            continue
        hashes = [_sha256(m[rel]) for m in maps]
        if len(set(hashes)) == 1:
            res["identical"].append(rel)
            continue
        verdict = None
        for k in range(1, len(maps)):
            if hashes[k] == hashes[0]:
                continue
            cmp = dict(compare_file(maps[0][rel], maps[k][rel], rtol, atol), runs=[1, k + 1])
            if verdict is None or not cmp["equal"]:
                verdict = cmp
            if not cmp["equal"]:
                break
        (res["within_tolerance"] if verdict["equal"] else res["different"]).append({"file": rel, **verdict})
    empty = [o.raw for o in outputs if not any(_files_at(s / o.rel) for s in snapshots)]
    res["never_produced"] = empty
    return res


# ─── report ─────────────────────────────────────────────────────────────────

def render(result):
    r = result
    verdict = {0: "一致", 1: "不一致", 2: "未完成（运行失败或没有可比较的输出）"}[r["exit_code"]]
    lines = ["# 重跑一致性检查", "",
             f"- 结论：**{verdict}**",
             f"- 命令：`{r['command']}`（工作目录 {r['cwd']}；每次都在新的子进程里从头运行）",
             "- 各次运行：" + "；".join(
                 f"第 {x['run']} 次 " + ("超时" if x["timed_out"] else f"退出码 {x['returncode']}") + f"，{x['seconds']} 秒"
                 for x in r["runs"])]
    cmp = r.get("comparison")
    if cmp:
        lines.append(f"- 比较的文件 {cmp['n_files']} 个：完全相同 {len(cmp['identical'])}，"
                     f"数值在容差内相同 {len(cmp['within_tolerance'])}（rtol={r['rtol']:g}，atol={r['atol']:g}），"
                     f"不同 {len(cmp['different'])}")
    for msg in r["messages"]:
        lines.append(f"- {msg}")
    if cmp and cmp["different"]:
        lines += ["", "## 不一致的文件", ""]
        for d in cmp["different"]:
            runs = f"第 {d['runs'][0]} 次 vs 第 {d['runs'][1]} 次，" if d.get("runs") else ""
            lines.append(f"### {d['file']}（{runs}{d['method']}）")
            lines += [f"- {x}" for x in d["details"]] or ["- （无更多细节）"]
            lines.append("")
    if cmp and cmp["within_tolerance"]:
        lines += ["", "## 数值在容差内相同的文件", ""]
        lines += [f"- {d['file']}（{d['method']}）" for d in cmp["within_tolerance"]]
    live = "、".join(r["outputs"])
    lines += ["", "## 文件在哪里", ""]
    if r["runs"] and all(x["returncode"] == 0 for x in r["runs"]):
        lines.append(f"- 最后一次运行的结果留在原位：{live}")
    elif r.get("restored"):
        lines.append(f"- 运行失败：已把 {r['restored']} 里的输出复制回原位（{live}）")
    else:
        lines.append(f"- 运行失败：原位（{live}）没有保留输出")
    lines.append(f"- 各次运行的副本与日志：{r['keep_dir']}（{'、'.join(r['snapshots'] + ['logs/'])}；看完可以删除）")
    if r.get("pre_existing"):
        lines.append(f"- 检查前已有的输出已移到（没有删除）：{r['keep_dir']}/pre-existing/（{r['pre_existing']} 个文件）")
    if r["exit_code"] == 1:
        lines += ["", "## 常见原因（逐条排查后重跑本检查）", ""]
        lines += [f"{i}. {h}" for i, h in enumerate(HINTS, 1)]
    return "\n".join(lines) + "\n"


# ─── CLI ────────────────────────────────────────────────────────────────────

def _parser():
    p = argparse.ArgumentParser(
        prog="reproduce_check.py",
        description="在全新子进程里把分析命令从头运行 N 次，比较输出文件是否一致。"
                    "退出码：0 一致；1 不一致；2 运行失败或没有可比较的输出。",
        epilog='例：python3 reproduce_check.py --cmd "python3 analysis_script.py" --outputs results/ '
               'tables/results.csv；或把命令放在 -- 之后：--outputs results/ -- Rscript analysis.R')
    p.add_argument("--cmd", help="要运行的命令（整条字符串，经 shell 执行）；也可以把命令写在 -- 之后")
    p.add_argument("--outputs", nargs="+", required=True, help="要比较的输出文件或目录（相对于 --cwd），可多个")
    p.add_argument("--runs", type=int, default=2, help="运行次数（≥2，默认 2）")
    p.add_argument("--cwd", default=".", help="运行命令的工作目录（默认当前目录）")
    p.add_argument("--timeout", type=float, default=600, help="每次运行的超时秒数（默认 600）")
    p.add_argument("--rtol", type=float, default=1e-9, help="浮点相对容差（默认 1e-9）")
    p.add_argument("--atol", type=float, default=1e-12, help="浮点绝对容差（默认 1e-12，用于接近 0 的数）")
    p.add_argument("--keep-dir", help="存放各次运行副本的目录（默认 <cwd>/.reproduce-check/<时间>/）")
    p.add_argument("--compare-stdout", action="store_true", help="同时比较各次运行打印到屏幕的内容")
    p.add_argument("--report", help="另存 Markdown 报告，如 reproduce-check.md")
    p.add_argument("--json", dest="json_path", help="另存 JSON 结果")
    return p


def _fail(msg):
    print(f"[重跑检查] 错误：{msg}", file=sys.stderr)
    return 2


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd_list = None
    if "--" in argv:
        i = argv.index("--")
        argv, cmd_list = argv[:i], argv[i + 1:]
    args = _parser().parse_args(argv)
    if bool(args.cmd) == bool(cmd_list):
        return _fail("请用 --cmd \"<命令>\" 或在 -- 之后写命令（二选一）")
    if args.runs < 2:
        return _fail("--runs 至少为 2")
    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        return _fail(f"工作目录不存在：{cwd}")
    shell = bool(args.cmd)
    cmd = args.cmd if shell else cmd_list
    cmd_text = args.cmd if shell else " ".join(shlex.quote(c) for c in cmd_list)

    outputs = [Output(o, cwd) for o in args.outputs]
    for o in outputs:
        if o.path == cwd or o.path in cwd.parents:
            return _fail(f"--outputs {o.raw} 是工作目录本身或它的上级目录；只能列出分析生成的文件或目录")
        if cwd not in o.path.parents:
            # outside the project the checker would move files it has no business touching
            return _fail(f"--outputs {o.raw} 不在工作目录 {cwd} 里；只能列出这次分析在项目里生成的文件或目录")
    for a in outputs:
        for b in outputs:
            if a is not b and (a.path == b.path or b.path in a.path.parents):
                return _fail(f"--outputs 有重叠：{a.raw} 在 {b.raw} 里面")
    try:
        tokens = shlex.split(cmd_text) if shell else cmd_list
    except ValueError:                      # unbalanced quotes: let the shell report it
        tokens = []
    for tok in tokens:
        p = (cwd / tok).resolve() if not os.path.isabs(tok) else Path(tok).resolve()
        if p.exists() and any(p == o.path or o.path in p.parents for o in outputs):
            return _fail(f"命令用到的 {tok} 在输出路径里；输出目录里只能放分析生成的文件")

    keep_root = Path(args.keep_dir).expanduser().resolve() if args.keep_dir else cwd / ".reproduce-check"
    for o in outputs:
        if keep_root == o.path or o.path in keep_root.parents or keep_root in o.path.parents:
            return _fail("--keep-dir 不能和输出路径重叠")
    keep_root.mkdir(parents=True, exist_ok=True)
    keep = Path(tempfile.mkdtemp(prefix=_dt.datetime.now().strftime("%Y%m%d-%H%M%S-"), dir=str(keep_root)))

    result = {"command": cmd_text, "cwd": str(cwd), "outputs": [o.raw for o in outputs], "runs": [],
              "rtol": args.rtol, "atol": args.atol, "keep_dir": str(keep), "snapshots": [], "messages": [],
              "pre_existing": 0, "restored": None, "comparison": None}
    pre = _move_out(outputs, keep / "pre-existing")
    result["pre_existing"] = pre
    snapshots = []
    for k in range(1, args.runs + 1):
        res = run_once(cmd, shell, cwd, args.timeout, keep / "logs", k)
        result["runs"].append({x: res[x] for x in ("run", "returncode", "timed_out", "seconds")})
        if not res["ok"]:
            _move_out(outputs, keep / f"run{k}-failed")
            result["snapshots"].append(f"run{k}-failed/")
            source = keep / "pre-existing" if pre else (snapshots[-1] if snapshots else None)
            if source is not None:
                _copy_back(outputs, source)
                result["restored"] = str(source)
            why = f"超时（>{args.timeout:g} 秒）" if res["timed_out"] else f"退出码 {res['returncode']}"
            result["messages"].append(f"第 {k} 次运行失败：{why}；错误输出最后几行见下")
            tail = [ln for ln in res["stderr"].strip().splitlines()[-8:]]
            result["messages"] += [f"`{ln}`" for ln in tail]
            result["exit_code"] = 2
            return _finish(result, args)
        snap = keep / f"run{k}"
        if k < args.runs:
            _move_out(outputs, snap)
        else:
            _copy_out(outputs, snap)
        snapshots.append(snap)
        result["snapshots"].append(f"run{k}/")

    cmp = compare_runs(snapshots, outputs, args.rtol, args.atol)
    if args.compare_stdout:
        logs = [keep / "logs" / f"run{k}.stdout.txt" for k in range(1, args.runs + 1)]
        for k in range(1, len(logs)):
            c = compare_text(logs[0], logs[k], args.rtol, args.atol)
            if not c["equal"]:
                cmp["different"].append({"file": "(屏幕输出 stdout)", "runs": [1, k + 1], **c})
                break
    result["comparison"] = cmp
    if cmp["never_produced"]:
        result["messages"].append("这些输出路径在各次运行中都没有文件，无法比较（检查 --outputs 是否写对、"
                                  "路径是否相对于 --cwd）：" + "、".join(cmp["never_produced"]))
        missing = [o for o in outputs if o.raw in cmp["never_produced"]]
        if pre and any(_files_at(keep / "pre-existing" / o.rel) for o in missing):
            # the runs never recreated them: put the earlier files back instead of leaving the path empty
            _copy_back(missing, keep / "pre-existing")
            result["restored"] = str(keep / "pre-existing")
            result["messages"].append("这些路径原有的文件已放回原处（运行前被移到了 pre-existing/）")
        result["exit_code"] = 2
    elif cmp["n_files"] == 0:
        result["messages"].append("没有找到任何输出文件")
        result["exit_code"] = 2
    else:
        result["exit_code"] = 1 if cmp["different"] else 0
    return _finish(result, args)


def _finish(result, args):
    text = render(result)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(text.rstrip())
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
