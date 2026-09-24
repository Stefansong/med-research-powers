#!/usr/bin/env python3
"""
reproduce_check.py -- run an analysis from scratch several times and check that it
writes the same output files every time (statistical-analysis Step 5, self-check).

Usage
  python3 reproduce_check.py --cmd "python3 analysis_script.py" --outputs results/ tables/results.csv
  python3 reproduce_check.py --outputs results/ --runs 3 --report reproduce-check.md -- Rscript analysis.R

What it does
  1. Files that already exist in the output paths are MOVED (never deleted) to
     <keep-dir>/pre-existing/ so that run 1 really starts from scratch. Directories that
     existed before the check (the output directories and their subdirectories) stay in
     place, emptied, because many scripts expect them to exist.
  2. The command runs in a fresh subprocess (--cwd, --timeout; empty stdin; stdout and stderr
     go to <keep-dir>/logs/). After every run except the last, its outputs are moved to
     <keep-dir>/run<k>/, so every run starts from the same state. The last run's outputs stay
     where the script wrote them; a copy goes to <keep-dir>/run<N>/.
  3. The runs are compared: the set of files and the sha256 of every file; CSV/TSV cell by
     cell; JSON value by value; .txt/.md/.log etc. as text (the first 20 changed lines are
     shown); .xlsx cell values and formulas; .svg as text, ignoring matplotlib's embedded date
     and random element ids; .gz by its decompressed content. Other files (PDF, PNG, RDS ...)
     by sha256 only. Whole numbers must match exactly; other numbers within --rtol / --atol.
     --exclude leaves files out of the comparison.
  4. What the command prints (stdout) is compared with --compare-stdout; without it the report
     still warns when the printed output differs between runs.
  5. If a run fails, or the check is interrupted (Ctrl-C, SIGTERM, SIGHUP), the analysis is
     stopped, its partial outputs go to <keep-dir>/run<k>-failed/ (-interrupted/) and the
     previous outputs are copied back into place.

--outputs, --report, --json and --keep-dir paths are relative to --cwd. <keep-dir> defaults to
<cwd>/.reproduce-check/<time>/; that folder gets its own .gitignore (the copies may hold
patient-level results), and --keep-last N deletes all but the N most recent checks.
Exit code: 0 identical (within tolerance) · 1 outputs differ · 2 a run failed, the check was
interrupted, or there was nothing to compare.
"""

import argparse
import csv
import datetime as _dt
import difflib
import fnmatch
import gzip
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
import threading
import time
from pathlib import Path

TABLE_SEPS = {".csv": ",", ".tsv": "\t", ".tab": "\t"}
TEXT_EXTS = {".txt", ".md", ".log", ".tex", ".html", ".htm", ".xml", ".yaml", ".yml",
             ".rmd", ".qmd", ".out"}
EMBEDDED_TIME_EXTS = {".pdf", ".docx", ".pptx"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
SCRIPT_EXTS = {".py", ".r", ".rmd", ".qmd", ".ipynb", ".jl", ".sh", ".bash", ".bat", ".cmd", ".ps1",
               ".do", ".ado", ".sas", ".sps", ".m", ".js"}
# --report / --json must never overwrite a script or a data file
NOT_A_REPORT_EXTS = SCRIPT_EXTS | {".csv", ".tsv", ".tab", ".xlsx", ".xlsm", ".xls", ".sav", ".dta", ".rds",
                                   ".rdata", ".rda", ".parquet", ".feather", ".sas7bdat"}
_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
NUM_RE = re.compile(_NUM)
PLAIN_NUM_RE = re.compile(rf"^\s*{_NUM}\s*$")
INT_RE = re.compile(r"^\s*[-+]?\d+\s*$")
MAX_LINES = 20
MAX_GZ = 256 << 20                                   # decompressed size limit for .gz outputs
MARKER = ".reproduce-check-run.json"                 # status file inside every check folder
CHECK_DIR_RE = re.compile(r"^\d{8}-\d{6}-")
CHECK_PARTS_RE = re.compile(r"^(?:pre-existing|logs|run\d+(?:-failed|-interrupted)?|\.reproduce-check-run\.json)$")
GITIGNORE = ("# reproduce_check.py: copies of analysis outputs from each check (they may contain\n"
             "# patient-level results). Never commit them; delete a check folder once it is reviewed.\n*\n")

HINTS = (
    "未固定随机种子：Python 的 random.seed / numpy.random.default_rng(seed) / sklearn 的 random_state / "
    "torch.manual_seed，R 的 set.seed()——bootstrap、多重插补、交叉验证、机器学习都用到随机数",
    "输出依赖当前时间：结果里写了运行日期时间、文件名带时间戳；PDF/XLSX/DOCX 会内嵌保存时间"
    "（matplotlib：PDF 用 savefig(..., metadata={'CreationDate': None})，SVG 用 metadata={'Date': None} "
    "并设 plt.rcParams['svg.hashsalt'] = 'fixed'；或设环境变量 SOURCE_DATE_EPOCH）；.gz 文件头里有压缩时间"
    "（pandas 用 compression={'method': 'gzip', 'mtime': 0}）",
    "多线程或 GPU 的非确定性：并行求和的顺序不同会带来末位差异；可设 OMP_NUM_THREADS=1、"
    "OPENBLAS_NUM_THREADS=1 重跑验证，确属浮点末位差异时再适当放宽 --rtol",
    "读取了会变的文件：运行中下载数据、读取上游仍在更新的文件、把上一次的输出当成输入",
    "顺序不固定：遍历集合（set）、os.listdir / glob 的结果没有排序",
    "确认某个文件只是内嵌的时间不同、内容相同后，可以用 --exclude 把它排除在比较之外，并在 analysis-log.md 里写明",
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


def _is_real_dir(p):
    return p.is_dir() and not p.is_symlink()


def _count_files(p):
    return len(_files_at(p)) if _is_real_dir(p) else 1


def _dirs_under(outputs):
    """Every directory (not symlink) that is an output directory or lies inside one."""
    found = set()
    for o in outputs:
        if _is_real_dir(o.path):
            found.add(o.path)
            for root, dirs, _ in os.walk(o.path):
                found.update(Path(root) / d for d in dirs if not (Path(root) / d).is_symlink())
    return found


def _move_out(outputs, dest, keep_dirs=None):
    """Move current outputs into dest/<rel>. Returns the number of files moved.

    Directories in keep_dirs (None = every directory) stay in place, emptied; everything else --
    files, symlinks and directories a run created -- is moved, so the next run starts from the
    same state as run 1."""
    n = 0
    for o in outputs:
        if _is_real_dir(o.path) and (keep_dirs is None or o.path in keep_dirs):
            n += _move_children(o.path, dest / o.rel, keep_dirs)
        elif o.path.exists() or o.path.is_symlink():
            target = dest / o.rel
            target.parent.mkdir(parents=True, exist_ok=True)
            n += _count_files(o.path)
            shutil.move(str(o.path), str(target))
    return n


def _move_children(directory, target, keep_dirs):
    n = 0
    target.mkdir(parents=True, exist_ok=True)
    for child in sorted(directory.iterdir()):
        if _is_real_dir(child) and (keep_dirs is None or child in keep_dirs):
            n += _move_children(child, target / child.name, keep_dirs)
        else:
            n += _count_files(child)
            shutil.move(str(child), str(target / child.name))
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


def _excluded(rel, patterns):
    """True if an output file (path relative to --cwd) matches an --exclude pattern."""
    for pat in patterns or ():
        p = pat.replace("\\", "/")
        if p.startswith("./"):
            p = p[2:]
        if fnmatch.fnmatchcase(rel, p) or fnmatch.fnmatchcase(rel.rsplit("/", 1)[-1], p) \
                or rel.startswith(p.rstrip("/") + "/"):
            return True
    return False


# ─── interruption ───────────────────────────────────────────────────────────

class Interrupted(Exception):
    """Ctrl-C, SIGTERM or SIGHUP arrived while the check was running."""

    def __init__(self, signum):
        super().__init__(signum)
        self.signum = signum


_SIG = {"defer": 0, "pending": None}


def _on_signal(signum, frame):
    if _SIG["defer"]:
        _SIG["pending"] = signum          # acted on as soon as the current file move is complete
        return
    raise Interrupted(signum)


class _Deferred:
    """Signals that arrive while files are being moved are acted on right after the move."""

    def __enter__(self):
        _SIG["defer"] += 1

    def __exit__(self, exc_type, exc, tb):
        _SIG["defer"] -= 1
        if not _SIG["defer"] and _SIG["pending"] is not None and exc_type is None:
            signum, _SIG["pending"] = _SIG["pending"], None
            raise Interrupted(signum)
        return False


def _install_handlers():
    old = {}
    if threading.current_thread() is not threading.main_thread():
        return old
    for name in ("SIGINT", "SIGTERM", "SIGHUP"):
        sig = getattr(signal, name, None)
        if sig is None:
            continue
        try:
            old[sig] = signal.signal(sig, _on_signal)
        except (ValueError, OSError):
            pass
    return old


def _restore_handlers(old):
    for sig, handler in old.items():
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError, TypeError):
            pass


def _signal_name(signum):
    try:
        return signal.Signals(signum).name
    except (ValueError, TypeError):
        return str(signum)


# ─── running ────────────────────────────────────────────────────────────────

def _kill(proc):
    """Stop the command and everything it started (not only the shell)."""
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)       # the whole process group (shell + children)
        else:                                          # Windows: kill the process tree
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        proc.kill()
    except OSError:
        pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def _read_log(path):
    try:
        return Path(path).read_bytes().decode("utf-8", "replace")
    except OSError:
        return ""


def run_once(cmd, shell, cwd, timeout, log_dir, k):
    """Run the command once. stdout / stderr go straight to files, so a process the command
    leaves behind cannot keep the checker waiting on a pipe."""
    log_dir.mkdir(parents=True, exist_ok=True)
    out_p, err_p = log_dir / f"run{k}.stdout.txt", log_dir / f"run{k}.stderr.txt"
    res = {"run": k, "returncode": None, "timed_out": False, "launch_error": None}
    t0 = time.time()
    with open(out_p, "wb") as fo, open(err_p, "wb") as fe:
        kw = {"cwd": str(cwd), "stdin": subprocess.DEVNULL, "stdout": fo, "stderr": fe, "shell": shell}
        if os.name == "posix":
            kw["start_new_session"] = True
        else:
            kw["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        try:
            proc = subprocess.Popen(cmd, **kw)
        except OSError as e:
            res["launch_error"] = str(e)
            fe.write(str(e).encode("utf-8", "replace"))
        else:
            try:
                proc.wait(timeout=timeout)
                res["returncode"] = proc.returncode
            except subprocess.TimeoutExpired:
                _kill(proc)
                res["timed_out"] = True
            except BaseException:
                _kill(proc)                            # Ctrl-C / SIGTERM: never leave the analysis running
                raise
    res["seconds"] = round(time.time() - t0, 1)
    res["stdout"], res["stderr"] = _read_log(out_p), _read_log(err_p)
    res["ok"] = res["returncode"] == 0
    return res


# ─── comparing ──────────────────────────────────────────────────────────────

def _raise_csv_limit():
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10


def _bytes(src):
    return bytes(src) if isinstance(src, (bytes, bytearray)) else Path(src).read_bytes()


def _read_text(src):
    data = _bytes(src)
    for enc in ("utf-8-sig", "gbk"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def _as_number(v):
    """int for whole numbers ('12', 12), float for other numbers, None for anything else."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, str):
        if INT_RE.match(v):
            return int(v)
        if PLAIN_NUM_RE.match(v):
            return float(v)
    return None


def _num_state(a, b, rtol, atol):
    """-> 'same' | 'tol' | 'diff' for two numbers. Whole numbers (counts, IDs, epoch seconds) must
    match exactly; other numbers may differ within the relative / absolute tolerance."""
    if isinstance(a, int) and isinstance(b, int):
        return "same" if a == b else "diff"
    try:
        fa, fb = float(a), float(b)
    except OverflowError:
        return "same" if a == b else "diff"
    if fa == fb or (math.isnan(fa) and math.isnan(fb)):
        return "same"
    if math.isinf(fa) or math.isinf(fb) or math.isnan(fa) or math.isnan(fb):
        return "diff"
    return "tol" if math.isclose(fa, fb, rel_tol=rtol, abs_tol=atol) else "diff"


class _Formula:
    """An xlsx formula cell: its formula text plus the value Excel cached for it (if any)."""
    __slots__ = ("text", "cached")

    def __init__(self, text, cached):
        self.text, self.cached = text, cached

    def __repr__(self):
        return f"{self.text}（缓存值 {self.cached!r}）"


def _cells_equal(va, vb, rtol, atol):
    """-> 'same' | 'tol' | 'diff' for two cell values (str / number / formula / other)."""
    if isinstance(va, _Formula) or isinstance(vb, _Formula):
        if not (isinstance(va, _Formula) and isinstance(vb, _Formula)) or va.text != vb.text:
            return "diff"
        return _cells_equal(va.cached, vb.cached, rtol, atol)
    if isinstance(va, bool) or isinstance(vb, bool):
        return "same" if type(va) is type(vb) and va == vb else "diff"
    if va == vb:
        return "same"
    fa, fb = _as_number(va), _as_number(vb)
    if fa is not None and fb is not None:
        state = _num_state(fa, fb, rtol, atol)
        return "tol" if state == "same" else state    # the same number written differently ("1" / "1.0")
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
    _raise_csv_limit()                     # a long cell (a JSON blob, a free-text note) is not an error
    ra = list(csv.reader(io.StringIO(_read_text(a)), delimiter=sep))
    rb = list(csv.reader(io.StringIO(_read_text(b)), delimiter=sep))
    details, n_diff, n_tol = _compare_grid(ra, rb, rtol, atol)
    return {"method": "逐单元格比较", "equal": n_diff == 0, "n_diff": n_diff, "n_within_tol": n_tol,
            "details": details}


def _xlsx_sheets(src, openpyxl):
    """{sheet: rows}; a formula cell becomes _Formula(formula text, cached value)."""
    data = _bytes(src)
    wf = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=False)
    wv = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        sheets = {}
        for name in wf.sheetnames:
            f_rows = [list(r) for r in wf[name].iter_rows(values_only=True)]
            v_rows = [list(r) for r in wv[name].iter_rows(values_only=True)]
            grid = []
            for i, row in enumerate(f_rows):
                vrow = v_rows[i] if i < len(v_rows) else []
                grid.append([_Formula(c, vrow[j] if j < len(vrow) else None)
                             if isinstance(c, str) and c.startswith("=") else c for j, c in enumerate(row)])
            sheets[name] = grid
        return list(wf.sheetnames), sheets
    finally:
        wf.close()
        wv.close()


def compare_xlsx(a, b, rtol, atol):
    try:
        import openpyxl
    except ImportError:
        return {"method": "sha256（未安装 openpyxl，无法逐单元格比较）", "equal": False, "n_diff": None,
                "details": ["xlsx 内含保存时间，建议分析脚本另存一份 CSV 供比较"]}
    names_a, sa = _xlsx_sheets(a, openpyxl)
    names_b, sb = _xlsx_sheets(b, openpyxl)
    details, n_diff, n_tol = [], 0, 0
    if names_a != names_b:
        details.append(f"工作表不同：{names_a} → {names_b}")
        n_diff += 1
    for name in names_a:
        if name not in sb:
            continue
        d, nd, nt = _compare_grid(sa[name], sb[name], rtol, atol, f"[{name}] ")
        details += d
        n_diff += nd
        n_tol += nt
    return {"method": "逐单元格比较（xlsx 公式与取值，忽略内嵌保存时间）", "equal": n_diff == 0, "n_diff": n_diff,
            "n_within_tol": n_tol, "details": details[:MAX_LINES]}


def _walk_json(x, y, path, out, rtol, atol):
    if len(out) >= 200:
        return
    if isinstance(x, bool) or isinstance(y, bool) or x is None or y is None:
        if not (type(x) is type(y) and x == y):          # true is not 1, null is not 0
            out.append(f"{path}: {x!r} → {y!r}")
    elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
        if _num_state(x, y, rtol, atol) == "diff":
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


def compare_text(a, b, rtol, atol, normalise=None):
    ta, tb = _read_text(a), _read_text(b)
    if normalise:
        ta, tb = normalise(ta), normalise(tb)
    if ta == tb:
        return {"method": "文本", "equal": True, "details": []}
    if ta.replace("\r\n", "\n") == tb.replace("\r\n", "\n"):
        return {"method": "文本", "equal": False, "n_diff": 1, "details": ["只有换行符不同（\\r\\n 与 \\n）"]}
    na, nb = NUM_RE.findall(ta), NUM_RE.findall(tb)
    if NUM_RE.split(ta) == NUM_RE.split(tb) and len(na) == len(nb) and \
            all(_num_state(_as_number(u), _as_number(v), rtol, atol) != "diff" for u, v in zip(na, nb)):
        return {"method": "文本（数字按容差比较）", "equal": True, "details": ["只有数字的末位不同，在容差内"]}
    changed = [ln for ln in difflib.unified_diff(ta.splitlines(), tb.splitlines(), lineterm="", n=0)
               if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
    if not changed:
        changed = ["差别在看不见的字符上（行尾空白或文件末尾的换行）"]
    return {"method": "文本 diff", "equal": False, "n_diff": len(changed), "details": changed[:MAX_LINES]}


def compare_json(a, b, rtol, atol):
    try:
        ja, jb = json.loads(_read_text(a)), json.loads(_read_text(b))
    except ValueError:
        return compare_text(a, b, rtol, atol)
    diffs = []
    _walk_json(ja, jb, "$", diffs, rtol, atol)
    return {"method": "JSON 逐值比较（整数须完全相同，其他数字按容差）", "equal": not diffs, "n_diff": len(diffs),
            "details": diffs[:MAX_LINES]}


_SVG_DATE = re.compile(r"<dc:date>[^<]*</dc:date>")
# matplotlib names clip paths / markers / hatches with a letter + 10 random hex digits unless
# rcParams['svg.hashsalt'] is set
_SVG_ID = re.compile(r"(id=\"|url\(#|href=\"#)([A-Za-z])[0-9a-f]{10}\b")


def _svg_normalise(text):
    return _SVG_ID.sub(r"\1\2-id", _SVG_DATE.sub("<dc:date/>", text))


def compare_svg(a, b, rtol, atol):
    res = compare_text(a, b, rtol, atol, normalise=_svg_normalise)
    res["method"] = "SVG 文本（忽略内嵌日期与 matplotlib 的随机图元编号）"
    if res["equal"]:
        res["details"] = ["只有内嵌日期或随机编号不同；作图时可固定：savefig(..., metadata={'Date': None})，"
                          "plt.rcParams['svg.hashsalt'] = 'fixed'"]
    return res


def _gunzip(src):
    with gzip.GzipFile(fileobj=io.BytesIO(_bytes(src))) as fh:
        data = fh.read(MAX_GZ + 1)
    if len(data) > MAX_GZ:
        raise ValueError("解压后超过 256 MB，只按 sha256 比较")
    return data


def compare_gzip(a, b, rtol, atol, name):
    ra, rb = _gunzip(a), _gunzip(b)
    if ra == rb:
        return {"method": "gzip 解压后逐字节比较", "equal": True,
                "details": ["解压后的内容完全相同，只有 gzip 文件头（压缩时间）不同；"
                            "pandas 可用 compression={'method': 'gzip', 'mtime': 0} 去掉"]}
    res = compare_file(ra, rb, rtol, atol, name=name[:-3])
    return dict(res, method="gzip 解压后" + res["method"])


def _binary_note(ext):
    note = ["二进制文件内容不同，无法逐项比较"]
    if ext in EMBEDDED_TIME_EXTS:
        note.append("这类文件常内嵌生成时间：确认内容相同后，可让脚本去掉时间戳，或用 --exclude 排除并写明")
    elif ext in IMAGE_EXTS:
        note.append("图片不同多半是作图用的数据不同，或抖动（jitter）/布局用了没固定的随机数")
    return {"method": "sha256", "equal": False, "n_diff": None, "details": note}


def compare_file(a, b, rtol, atol, name=None):
    """Compare two versions of one output (paths or bytes; name gives the file type)."""
    name = str(name if name is not None else a)
    ext = Path(name).suffix.lower()
    if ext in TABLE_SEPS:
        kind, fn = "表格", lambda: compare_table(a, b, TABLE_SEPS[ext], rtol, atol)
    elif ext == ".json":
        kind, fn = "JSON", lambda: compare_json(a, b, rtol, atol)
    elif ext in (".xlsx", ".xlsm"):
        kind, fn = "xlsx", lambda: compare_xlsx(a, b, rtol, atol)
    elif ext == ".svg":
        kind, fn = "SVG 文本", lambda: compare_svg(a, b, rtol, atol)
    elif ext in TEXT_EXTS:
        kind, fn = "文本", lambda: compare_text(a, b, rtol, atol)
    elif ext == ".gz":
        kind, fn = "gzip", lambda: compare_gzip(a, b, rtol, atol, name)
    else:
        return _binary_note(ext)
    try:
        return fn()
    except Exception as e:                  # a damaged or mislabelled file is a difference, not a crash
        return {"method": f"sha256（无法按{kind}读取）", "equal": False, "n_diff": None,
                "details": [f"按{kind}读取时出错：{type(e).__name__}: {str(e)[:200]}",
                            "两次运行的文件内容不同（sha256 不一致）"]}


def compare_runs(snapshots, outputs, rtol, atol, exclude=()):
    maps = [_collect(outputs, base=s) for s in snapshots]
    names = sorted(set().union(*[set(m) for m in maps])) if maps else []
    excluded = [n for n in names if _excluded(n, exclude)]
    names = [n for n in names if n not in excluded]
    res = {"n_files": len(names), "identical": [], "within_tolerance": [], "different": [], "excluded": excluded}
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


def compare_stdout(logs, rtol, atol, compared):
    """What the runs printed. Always checked; it only decides the verdict with --compare-stdout."""
    texts = [_read_log(p) for p in logs]
    res = {"compared": compared, "equal": True, "empty": not any(t.strip() for t in texts),
           "method": "文本", "details": [], "runs": None}
    for k in range(1, len(logs)):
        c = compare_text(logs[0], logs[k], rtol, atol)
        if not c["equal"]:
            res.update(equal=False, method=c["method"], details=c["details"], runs=[1, k + 1])
            break
    return res


def _date_regex(days):
    pats = []
    for d in sorted(days):
        y, m, dd = d.year, d.month, d.day
        pats += [rf"(?<!\d){y}[-/.]0?{m}[-/.]0?{dd}(?!\d)", rf"{y}\s*年\s*0?{m}\s*月\s*0?{dd}\s*日",
                 rf"(?<!\d)0?{dd}[-/.]0?{m}[-/.]{y}(?!\d)", rf"(?<!\d)0?{m}[-/.]0?{dd}[-/.]{y}(?!\d)"]
    return re.compile("|".join(pats))


def files_with_run_date(files, days):
    """Text-like outputs that contain the date the check ran on -- probably a run timestamp, which two
    back-to-back runs can share (same minute / same day) without the comparison noticing."""
    rx, hits = _date_regex(days), []
    for rel, p in files.items():
        ext = Path(rel).suffix.lower()
        if ext not in TEXT_EXTS and ext not in TABLE_SEPS and ext != ".json":
            continue
        try:
            with open(p, "rb") as fh:
                head = fh.read(2 << 20)
        except OSError:
            continue
        if rx.search(_read_text(head)):
            hits.append(rel)
    return hits


# ─── the check folders (.reproduce-check/) ─────────────────────────────────

def _write_marker(keep, status, **extra):
    try:
        data = {"status": status, "pid": os.getpid(), "time": _dt.datetime.now().isoformat(timespec="seconds"),
                "started": _started(keep), **extra}
        (keep / MARKER).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _read_marker(folder):
    try:
        data = json.loads((folder / MARKER).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _started(folder):
    """When a check started: from its status file, else from the folder name (older versions)."""
    t = _read_marker(folder).get("started")
    if isinstance(t, (int, float)):
        return t
    try:
        return _dt.datetime.strptime(folder.name[:15], "%Y%m%d-%H%M%S").timestamp()
    except ValueError:
        return 0.0


def _check_folders(keep_root):
    """[(folder, status)] of earlier checks under keep_root, oldest first. status None = a folder
    written by an older version (no status file) that only holds what a check writes."""
    out = []
    try:
        entries = [p for p in keep_root.iterdir() if _is_real_dir(p) and CHECK_DIR_RE.match(p.name)]
    except OSError:
        return out
    for p in entries:
        if (p / MARKER).is_file():
            out.append((p, _read_marker(p).get("status") or "unknown"))
        else:
            try:
                parts = [c.name for c in p.iterdir()]
            except OSError:
                continue
            if all(CHECK_PARTS_RE.match(n) for n in parts):
                out.append((p, None))
    return sorted(out, key=lambda x: (_started(x[0]), x[0].name))


def _folder_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


def _prune(keep_root, current, keep_last):
    """Delete the check folders older than the keep_last most recent ones (never an unfinished one)."""
    folders = _check_folders(keep_root)
    finished = [p for p, st in folders if st != "running" or p == current]
    removed = []
    for p in finished[:max(0, len(finished) - keep_last)]:
        if p == current:
            continue
        try:
            shutil.rmtree(p)
            removed.append(p.name)
        except OSError:
            pass
    return removed


# ─── report ─────────────────────────────────────────────────────────────────

def _run_text(x):
    if x.get("launch_error"):
        return f"第 {x['run']} 次 无法启动（{x['launch_error']}）"
    state = "超时" if x["timed_out"] else f"退出码 {x['returncode']}"
    return f"第 {x['run']} 次 {state}，{x['seconds']} 秒"


def render(result):
    r = result
    verdict = {0: "一致", 1: "不一致", 2: "未完成（运行失败、被中断或没有可比较的输出）"}[r["exit_code"]]
    lines = ["# 重跑一致性检查", "",
             f"- 结论：**{verdict}**",
             f"- 命令：`{r['command']}`（工作目录 {r['cwd']}；每次都在新的子进程里从头运行）"]
    if r["runs"]:
        lines.append("- 各次运行：" + "；".join(_run_text(x) for x in r["runs"]))
    cmp = r.get("comparison")
    if cmp:
        lines.append(f"- 比较的文件 {cmp['n_files']} 个：完全相同 {len(cmp['identical'])}，"
                     f"在容差内相同 {len(cmp['within_tolerance'])}（rtol={r['rtol']:g}，atol={r['atol']:g}；"
                     f"整数须完全相同），不同 {len(cmp['different'])}")
        if cmp.get("excluded"):
            lines.append(f"- 没有比较（--exclude）：{'、'.join(cmp['excluded'][:20])}"
                         + (f" 等 {len(cmp['excluded'])} 个" if len(cmp["excluded"]) > 20 else ""))
        so = cmp.get("stdout")
        if so:
            if so["empty"]:
                state = "没有打印内容"
            elif so["equal"]:
                state = "各次相同"
            else:
                state = f"第 {so['runs'][0]} 次与第 {so['runs'][1]} 次不同"
            lines.append(f"- 屏幕输出（stdout）：{state}" + ("" if so["compared"] else "（未计入结论；加 --compare-stdout 计入）"))
    for msg in r["messages"]:
        lines.append(f"- {msg}")
    if r.get("warnings"):
        lines += ["", "## 需要留意", ""]
        lines += [f"- {w}" for w in r["warnings"]]
    diff_items = list(cmp["different"]) if cmp else []
    so = (cmp or {}).get("stdout")
    if so and so["compared"] and not so["equal"]:
        diff_items.append({"file": "(屏幕输出 stdout)", **so})
    if diff_items:
        lines += ["", "## 不一致的文件", ""]
        for d in diff_items:
            runs = f"第 {d['runs'][0]} 次 vs 第 {d['runs'][1]} 次，" if d.get("runs") else ""
            lines.append(f"### {d['file']}（{runs}{d['method']}）")
            lines += [f"- {x}" for x in d["details"]] or ["- （无更多细节）"]
            lines.append("")
    if cmp and cmp["within_tolerance"]:
        lines += ["", "## 在容差内相同的文件（数字末位、内嵌时间或随机编号不同）", ""]
        for d in cmp["within_tolerance"]:
            lines.append(f"- {d['file']}（{d['method']}）")
            lines += [f"  - {x}" for x in d.get("details", [])[:2]]
    live = "、".join(r["outputs"])
    lines += ["", "## 文件在哪里", ""]
    if r.get("last_run_in_place"):
        lines.append(f"- 最后一次运行的结果留在原位：{live}")
    elif r.get("restored"):
        lines.append(f"- 没有完成：已把 {r['restored']} 里的输出复制回原位（{live}）")
    else:
        lines.append(f"- 没有完成：原位（{live}）没有保留输出")
    lines.append(f"- 各次运行的副本与日志：{r['keep_dir']}（{'、'.join(r['snapshots'] + ['logs/'])}）")
    if r.get("pre_existing"):
        lines.append(f"- 检查前已有的输出已移到（没有删除）：{r['keep_dir']}/pre-existing/（{r['pre_existing']} 个文件）")
    kr = r.get("keep_root") or {}
    if kr:
        line = f"- {kr['path']} 里现有 {kr['n_checks']} 次检查的副本，共 {kr['mb']:.1f} MB"
        if kr.get("pruned"):
            line += f"（按 --keep-last 删除了较早的 {len(kr['pruned'])} 次）"
        line += ("；副本里可能有患者级结果：看完可以删除，或下次加 --keep-last 1 只保留最近一次"
                 + ("；该目录有自己的 .gitignore，不会被 git 提交" if kr.get("gitignored") else
                    "；请把它加进 .gitignore，不要提交"))
        lines.append(line)
    if r["exit_code"] == 1:
        lines += ["", "## 常见原因（逐条排查后重跑本检查）", ""]
        lines += [f"{i}. {h}" for i, h in enumerate(HINTS, 1)]
    return "\n".join(lines) + "\n"


# ─── CLI ────────────────────────────────────────────────────────────────────

def _parser():
    p = argparse.ArgumentParser(
        prog="reproduce_check.py",
        description="在全新子进程里把分析命令从头运行 N 次，比较输出文件是否一致。"
                    "退出码：0 一致；1 不一致；2 运行失败、被中断或没有可比较的输出。",
        epilog='例：python3 reproduce_check.py --cmd "python3 analysis_script.py" --outputs results/ '
               'tables/results.csv --compare-stdout；或把命令放在 -- 之后：--outputs results/ -- Rscript analysis.R')
    p.add_argument("--cmd", help="要运行的命令（整条字符串，经 shell 执行）；也可以把命令写在 -- 之后")
    p.add_argument("--outputs", nargs="+", required=True, help="要比较的输出文件或目录（相对于 --cwd），可多个")
    p.add_argument("--runs", type=int, default=2, help="运行次数（≥2，默认 2）")
    p.add_argument("--cwd", default=".", help="运行命令的工作目录（默认当前目录）")
    p.add_argument("--timeout", type=float, default=600, help="每次运行的超时秒数（默认 600）")
    p.add_argument("--rtol", type=float, default=1e-12,
                   help="非整数的相对容差（默认 1e-12；整数一律要求完全相同）")
    p.add_argument("--atol", type=float, default=1e-12, help="浮点绝对容差（默认 1e-12，用于接近 0 的数）")
    p.add_argument("--exclude", action="append", default=[], metavar="PATTERN",
                   help="不参与比较的输出文件（glob，相对于 --cwd 或只写文件名），可重复：--exclude '*.pdf'")
    p.add_argument("--keep-dir", help="存放各次运行副本的目录（相对于 --cwd；默认 <cwd>/.reproduce-check/<时间>/）")
    p.add_argument("--keep-last", type=int, metavar="N",
                   help="检查结束后只保留最近 N 次检查的副本，删除更早的（默认全部保留）")
    p.add_argument("--compare-stdout", action="store_true",
                   help="把各次运行打印到屏幕的内容也计入结论（结果只打印在屏幕上时必须加）")
    p.add_argument("--report", help="另存 Markdown 报告（相对于 --cwd），如 reproduce-check.md")
    p.add_argument("--json", dest="json_path", help="另存 JSON 结果（相对于 --cwd）")
    return p


def _fail(msg):
    print(f"[重跑检查] 错误：{msg}", file=sys.stderr)
    return 2


def _under(cwd, raw):
    p = Path(raw).expanduser()
    return (p if p.is_absolute() else cwd / p).resolve()


def _command_tokens(cmd_text, cmd_list, shell):
    """-> [(token, is_output)]: the command's words; redirect and tee targets count as outputs."""
    if not shell:
        return [(t, False) for t in cmd_list]
    try:
        lx = shlex.shlex(cmd_text, posix=os.name == "posix", punctuation_chars=True)
        lx.whitespace_split = True
        words = list(lx)
    except ValueError:                      # unbalanced quotes: let the shell report it
        return []
    out, next_out, tee = [], False, False
    for w in words:
        if os.name != "posix" and len(w) > 1 and w[0] == w[-1] and w[0] in "\"'":
            w = w[1:-1]
        if w and set(w) <= set("<>&|;()"):
            next_out = ">" in w
            tee = tee and not ({"|", "&&", "||", ";", "&"} & {w})
            continue
        if w == "tee":
            tee = True
            continue
        out.append((w, next_out or (tee and not w.startswith("-"))))
        next_out = False
        if w.startswith("-") and "=" in w:              # --out=results/table.csv
            out.append((w.split("=", 1)[1], False))
    return out


def _check_command_paths(tokens, cwd, outputs):
    """-> (error or None, [tokens inside an output path that may be inputs], [dirs to create]).

    A script inside an output path is refused (it would be moved away before run 1). An output
    directory passed as an argument, or a redirect target inside it, is fine -- also on the next
    check, when the previous run's files are there. The directory of a redirect target inside an
    output directory is created, because the shell opens that file before the script runs."""
    named, mkdirs = [], []
    for tok, is_output in tokens:
        if not tok or len(tok) > 1024 or "\n" in tok or "\0" in tok:
            continue
        try:
            p = Path(os.path.realpath(os.path.join(str(cwd), os.path.expanduser(tok))))
        except (OSError, ValueError):
            continue
        hit = next((o for o in outputs if p == o.path or o.path in p.parents), None)
        if hit is None:
            continue
        if is_output:
            if p != hit.path and not p.parent.exists():
                mkdirs.append(p.parent)
            continue
        try:
            is_dir, is_file = p.is_dir(), p.is_file()
        except OSError:
            continue
        if is_dir:
            continue
        if is_file and p.suffix.lower() in SCRIPT_EXTS:
            return (f"命令要运行的脚本 {tok} 在输出路径 {hit.raw} 里：检查开始前输出路径里的文件会被移走，"
                    "脚本就找不到了。请把脚本放到输出目录之外，或把 --outputs 写得更具体"), [], []
        named.append(tok)
    return None, named, mkdirs


def _check_report_paths(paths, cwd, outputs, tokens):
    seen = {}
    for flag, p in paths:
        if p is None:
            continue
        if p.suffix.lower() in NOT_A_REPORT_EXTS:
            return f"{flag} {p.name} 的扩展名像脚本或数据文件；请用 .md / .json，以免覆盖它"
        key = str(p).lower()                       # the same file on a case-insensitive disk
        if key in seen:
            return f"{flag} 和 {seen[key]} 是同一个文件"
        seen[key] = flag
        if any(p == o.path or o.path in p.parents for o in outputs):
            return f"{flag} {p} 在输出路径里：下次检查会把它当成输出移走；请写到输出目录之外"
        if not p.parent.is_dir():
            return f"{flag} 的目录不存在：{p.parent}"
        if p.is_dir():
            return f"{flag} {p} 是一个目录"
        for tok, _ in tokens:
            try:
                if Path(os.path.realpath(os.path.join(str(cwd), tok))) == p:
                    return f"{flag} {p.name} 是命令里用到的文件，不能被报告覆盖"
            except (OSError, ValueError):
                continue
    return None


def _put_back(outputs, keep, st, tag, result):
    """After a failed / interrupted run: move its partial outputs aside and copy the earlier ones back."""
    k = st["k"]
    with _Deferred():
        _move_out(outputs, keep / f"run{k}-{tag}", st["keep_dirs"])
        result["snapshots"].append(f"run{k}-{tag}/")
        source = keep / "pre-existing" if st["pre"] else (st["snapshots"][-1] if st["snapshots"] else None)
        if source is not None:
            _copy_back(outputs, source)
            result["restored"] = str(source)


def _check(args, cmd, shell, cwd, outputs, keep, result, st, named):
    st["phase"] = "pre"
    with _Deferred():
        st["pre"] = result["pre_existing"] = _move_out(outputs, keep / "pre-existing")
        st["keep_dirs"] = _dirs_under(outputs)
    st["phase"] = "run"
    days = {_dt.date.today()}
    for k in range(1, args.runs + 1):
        st["k"] = k
        res = run_once(cmd, shell, cwd, args.timeout, keep / "logs", k)
        result["runs"].append({x: res[x] for x in ("run", "returncode", "timed_out", "seconds", "launch_error")})
        if not res["ok"]:
            _put_back(outputs, keep, st, "failed", result)
            if res["launch_error"]:
                why = f"命令无法启动（{res['launch_error']}）"
            elif res["timed_out"]:
                why = f"超时（>{args.timeout:g} 秒），命令及其子进程已被结束"
            else:
                why = f"退出码 {res['returncode']}"
            tail = res["stderr"].strip().splitlines()[-8:] if not res["launch_error"] else []
            result["messages"].append(f"第 {k} 次运行失败：{why}" + ("；错误输出最后几行见下" if tail else ""))
            result["messages"] += [f"`{ln}`" for ln in tail]
            if named:
                result["messages"].append(
                    f"命令里写到的 {'、'.join(named)} 在 --outputs 路径里：检查前这些路径里原有的文件被移走、"
                    "每次运行前都会清空。如果其中有输入文件（数据、配置），请移到输出目录之外")
            result["exit_code"] = 2
            return
        snap = keep / f"run{k}"
        with _Deferred():
            if k < args.runs:
                _move_out(outputs, snap, st["keep_dirs"])
            else:
                _copy_out(outputs, snap)
        st["snapshots"].append(snap)
        result["snapshots"].append(f"run{k}/")

    st["phase"] = "compare"
    result["last_run_in_place"] = True
    days.add(_dt.date.today())
    cmp = compare_runs(st["snapshots"], outputs, args.rtol, args.atol, args.exclude)
    logs = [keep / "logs" / f"run{k}.stdout.txt" for k in range(1, args.runs + 1)]
    cmp["stdout"] = so = compare_stdout(logs, args.rtol, args.atol, args.compare_stdout)
    result["comparison"] = cmp
    if not so["compared"] and not so["equal"]:
        shown = "；".join(f"`{ln[:120]}`" for ln in so["details"][:4])
        result["warnings"].append(
            "屏幕输出（stdout）各次运行不同，但没有计入结论（没加 --compare-stdout）：如果有结果只打印在屏幕上"
            f"（如 `[SAP 4.1] …` 行），请加 --compare-stdout 重跑。不同的行：{shown}")
    live = {k: v for k, v in _collect(outputs, base=st["snapshots"][-1]).items()
            if not _excluded(k, args.exclude)}
    dated = files_with_run_date(live, days)
    if so["compared"] and _date_regex(days).search(_read_log(logs[-1])):
        dated.append("(屏幕输出 stdout)")
    if dated:
        result["warnings"].append(
            f"输出里出现了运行当天的日期：{'、'.join(dated[:10])}。如果那是运行时间，连续两次运行可能恰好相同"
            "（同一分钟、同一天）而查不出来——请确认；结果文件里不要写运行时间")
    if cmp["never_produced"]:
        result["messages"].append("这些输出路径在各次运行中都没有文件，无法比较（检查 --outputs 是否写对、"
                                  "路径是否相对于 --cwd）：" + "、".join(cmp["never_produced"]))
        missing = [o for o in outputs if o.raw in cmp["never_produced"]]
        if st["pre"] and any(_files_at(keep / "pre-existing" / o.rel) for o in missing):
            # the runs never recreated them: put the earlier files back instead of leaving the path empty
            _copy_back(missing, keep / "pre-existing")
            result["restored"] = str(keep / "pre-existing")
            result["messages"].append("这些路径原有的文件已放回原处（运行前被移到了 pre-existing/）")
        result["exit_code"] = 2
    elif cmp["n_files"] == 0:
        result["messages"].append("没有找到任何可比较的输出文件" + ("（其余都被 --exclude 排除了）" if cmp["excluded"] else ""))
        result["exit_code"] = 2
    else:
        stdout_differs = so["compared"] and not so["equal"]
        result["exit_code"] = 1 if cmp["different"] or stdout_differs else 0


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
    if not args.timeout > 0:
        return _fail("--timeout 必须大于 0")
    if not (args.rtol >= 0 and args.atol >= 0):
        return _fail("--rtol / --atol 不能是负数")
    if args.keep_last is not None and args.keep_last < 1:
        return _fail("--keep-last 至少为 1")
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
    tokens = _command_tokens(cmd_text, cmd_list, shell)
    err, named, mkdirs = _check_command_paths(tokens, cwd, outputs)
    if err:
        return _fail(err)
    report = _under(cwd, args.report) if args.report else None
    json_path = _under(cwd, args.json_path) if args.json_path else None
    err = _check_report_paths((("--report", report), ("--json", json_path)), cwd, outputs, tokens)
    if err:
        return _fail(err)

    keep_root = _under(cwd, args.keep_dir) if args.keep_dir else cwd / ".reproduce-check"
    for o in outputs:
        if keep_root == o.path or o.path in keep_root.parents or keep_root in o.path.parents:
            return _fail("--keep-dir 不能和输出路径重叠")
    new_root = not keep_root.exists()
    try:
        keep_root.mkdir(parents=True, exist_ok=True)
        gitignored = (keep_root / ".gitignore").is_file()
        if not gitignored and (new_root or not args.keep_dir):
            (keep_root / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
            gitignored = True
        keep = Path(tempfile.mkdtemp(prefix=_dt.datetime.now().strftime("%Y%m%d-%H%M%S-"), dir=str(keep_root)))
        (keep / MARKER).write_text(json.dumps({"started": time.time()}), encoding="utf-8")
    except OSError as e:
        return _fail(f"无法创建副本目录 {keep_root}：{e}")
    stale = [p for p, status in _check_folders(keep_root) if status == "running" and p != keep]
    _write_marker(keep, "running", command=cmd_text)

    result = {"command": cmd_text, "cwd": str(cwd), "outputs": [o.raw for o in outputs], "runs": [],
              "n_runs": args.runs, "rtol": args.rtol, "atol": args.atol, "keep_dir": str(keep),
              "snapshots": [], "messages": [], "warnings": [], "pre_existing": 0, "restored": None,
              "interrupted": False, "last_run_in_place": False, "comparison": None, "keep_root": None}
    for p in stale:
        if _files_at(p / "pre-existing"):
            result["warnings"].append(f"较早的一次检查（{p}）没有正常结束（可能被强行终止）：它运行前移走的文件"
                                      f"还在 {p}/pre-existing/，请确认是否需要放回原处")
    for d in mkdirs:                          # "> results/stdout.txt" needs results/ before the shell starts
        d.mkdir(parents=True, exist_ok=True)
    st = {"phase": "start", "k": 0, "pre": 0, "snapshots": [], "keep_dirs": None}
    old = _install_handlers()
    try:
        _check(args, cmd, shell, cwd, outputs, keep, result, st, named)
    except (Interrupted, KeyboardInterrupt) as e:
        name = _signal_name(e.signum) if isinstance(e, Interrupted) else "SIGINT"
        result["interrupted"] = True
        _abort(result, st, outputs, keep, f"检查被中断（{name}）：分析命令已被结束")
    except Exception as e:                    # an unexpected error must not leave the outputs moved away
        _abort(result, st, outputs, keep, f"检查出错（{type(e).__name__}: {e}）")
    finally:
        _restore_handlers(old)
    status = "interrupted" if result["interrupted"] else ("finished" if result["exit_code"] in (0, 1) else "failed")
    _write_marker(keep, status, command=cmd_text, exit_code=result["exit_code"])
    pruned = _prune(keep_root, keep, args.keep_last) if args.keep_last else []
    result["keep_root"] = {"path": str(keep_root), "n_checks": len(_check_folders(keep_root)),
                           "mb": _folder_size(keep_root) / 1e6, "pruned": pruned, "gitignored": gitignored}
    return _finish(result, report, json_path)


def _abort(result, st, outputs, keep, message):
    _SIG["defer"] += 1                        # a second Ctrl-C must not stop the files going back
    try:
        if st["phase"] == "pre":
            if (keep / "pre-existing").exists():
                _copy_back(outputs, keep / "pre-existing")
                result["restored"] = str(keep / "pre-existing")
        elif st["phase"] == "run":
            _put_back(outputs, keep, st, "interrupted" if result["interrupted"] else "failed", result)
        result["messages"].append(message)
    except Exception as e:
        result["messages"].append(message)
        result["messages"].append(f"放回原有输出时出错（{type(e).__name__}: {e}）：原有输出在 {keep}/pre-existing/，"
                                  "请手动放回")
    finally:
        _SIG["defer"] -= 1
        _SIG["pending"] = None
    result["exit_code"] = 2


def _finish(result, report, json_path):
    text = render(result)
    for path, content in ((report, text), (json_path, json.dumps(result, ensure_ascii=False, indent=2))):
        if path is None:
            continue
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as e:
            print(f"[重跑检查] 错误：无法写入 {path}：{e}", file=sys.stderr)
            result["exit_code"] = 2
    print(text.rstrip())
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
