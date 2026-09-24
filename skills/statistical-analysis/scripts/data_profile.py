#!/usr/bin/env python3
"""
data_profile.py -- read-only data check-up ("数据体检") of one table (CSV / TSV / XLSX).

It describes the STRUCTURE and QUALITY of the data and nothing else:
  * it never modifies, cleans, recodes or re-saves the data file;
  * it never computes a relation between two variables, or between any variable and
    the outcome (no cross-tabs, no group comparisons, no correlations, no models).

What it reports
  rows / columns; the inferred type of every column (numeric / categorical / date /
  text / ID-like); disguised missing values ("NA", "/", "未查", "999", ...) per column;
  censored strings ("<0.1", ">1000", "≤5"); numeric columns that would load as text;
  unparseable dates; missing % including disguised missing; numeric range, percentiles,
  Z>3 and IQR×1.5 counts (counted, never removed); categorical levels and spellings that
  differ only in case / spaces; repeated IDs and cluster structure (centre, surgeon ...);
  the outcome's own distribution and event count (--outcome); suspected personal
  information columns (column name and hit count only -- values are never printed).

Command line
  python3 data_profile.py data.csv --id patient_id --outcome recurrence --report data-profile.md
  python3 data_profile.py export.xlsx --sheet Sheet2 --outcome death --time months --json profile.json
  python3 data_profile.py data.csv --missing-tokens 拒查,未做 --range age=0:120

Library use (run from the user's project directory)
  import os, sys
  sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                  "skills", "statistical-analysis", "scripts"))
  from data_profile import load_table, profile_dataframe, render_markdown
  df, meta = load_table("data.csv")            # every value kept exactly as written
  profile = profile_dataframe(df, id_col="patient_id", outcome_col="recurrence", source=meta)
  print(render_markdown(profile))

Give profile_dataframe() a table read by load_table(): pandas' own read_csv() silently
turns "NA", "N/A", "NULL" ... into empty cells, so disguised missing would be under-counted.
"""

import argparse
import codecs
import collections
import csv
import datetime as _dt
import hashlib
import io
import json
import math
import os
import re
import unicodedata

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover - depends on the user's environment
    raise SystemExit("缺少 pandas / numpy：pip install pandas numpy（读 .xlsx 另需 openpyxl）")

STATEMENT = "本报告只描述数据结构与质量，不含变量间或与结局的关系"

# ─── vocabularies ───────────────────────────────────────────────────────────

DEFAULT_MISSING_TOKENS = (
    "", "NA", "N/A", "n/a", "na", "NaN", "nan", "NULL", "null", "None",
    "#N/A", "#NULL!", "#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NUM!",
    ".", "/", "\\", "-", "--", "—", "——", "?", "？",
    "未查", "未测", "未检", "未做", "未知", "不详", "不清", "无", "缺失", "缺", "空",
    "missing", "unknown",
    "999", "9999", "-99", "-999",
)
# These may be real values: "无"/"none" = "no, none" (e.g. 并发症=无); "-" = negative in lab
# results. They count as missing only in numeric / date / ID columns and stay a level elsewhere.
AMBIGUOUS_TOKENS = frozenset({"无", "none", "-"})
# Tokens pandas.read_csv() already turns into NaN by default (they do not force a text column).
PANDAS_DEFAULT_NA = frozenset({"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan",
                               "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None",
                               "n/a", "nan", "null"})

TYPE_LABELS = {"numeric": "数值", "categorical": "分类", "date": "日期", "text": "文本",
               "id": "ID 样式", "empty": "全部缺失"}

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
PLAIN_NUM_RE = re.compile(rf"^{_NUM}$")
CENSORED_RE = re.compile(
    rf"^(?:<=|>=|≤|≥|⩽|⩾|≦|≧|<|>|小于|大于|低于|高于|不足|超过)\s*{_NUM}(?:\s*[^\d\s].*)?$")
CENSORED_WORDS = frozenset({"未检出", "低于检测限", "低于检出限", "高于检测限", "超出检测上限",
                            "<lod", "<loq", "<lloq", ">uloq", "bdl"})
THOUSANDS_RE = re.compile(r"^[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
COMMA_DECIMAL_RE = re.compile(r"^[-+]?\d+,\d{1,2}$")
# number + unit ("130g/L", "45岁", "12%"); at most 10 integer digits so ID numbers ending in X are not read as numbers
UNIT_RE = re.compile(r"^([-+]?(?:\d{1,10}(?:\.\d*)?|\.\d+))\s*([A-Za-z%‰°℃℉μµ×*一-鿿].*)$")
DATE_LIKE_RE = re.compile(
    r"^\d{1,4}[-/.年]\d{1,2}(?:[-/.月]\d{1,4}日?)?(?:[ T]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?$")
DMY_RE = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})")
DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日", "%Y%m%d",
                "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f",
                "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y",
                "%Y-%m", "%Y/%m", "%Y年%m月")

DATE_NAME_RE = re.compile(r"date|日期|生日|出生|dob", re.IGNORECASE)
ID_NAME_RES = (
    re.compile(r"^(?:patient|subject|case|record|study|sample|person|participant)?[\s_\-.]*id$", re.I),
    re.compile(r"^id[\s_\-.]", re.I),
    re.compile(r"[\s_\-.]id$", re.I),
    re.compile(r"^(?:pid|mrn|uid|sid)$", re.I),
    re.compile(r"编号|序号|住院号|病历号|病案号|门诊号|登记号|^id号$|患者id|病人id", re.I),
)
CLUSTER_TOKENS = frozenset({"center", "centre", "site", "hospital", "clinic", "surgeon", "operator",
                            "doctor", "physician", "reader", "rater", "batch",
                            "centerid", "centreid", "siteid", "hospitalid", "surgeonid"})
CLUSTER_SUBSTR = ("中心", "医院", "院区", "科室", "术者", "主刀", "医生", "医师", "读片", "评分者", "批次")
PII_NAME_SUBSTR = ("姓名", "名字", "身份证", "证件号", "手机", "电话", "联系方式", "住址", "地址",
                   "住院号", "病历号", "病案号", "门诊号", "医保号", "邮箱",
                   "name", "phone", "mobile", "address", "email", "idcard", "id_card", "id card", "mrn")
PII_NAME_TOKENS = frozenset({"tel", "addr"})
ID_CARD_RE = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")
MOBILE_RE = re.compile(r"(?:(?<=\+86)|(?<=\+86 )|(?<=\+86-)|(?<!\d))1[3-9]\d{9}(?!\d)")

EVENT_WORDS = frozenset({"1", "是", "yes", "y", "true", "阳性", "positive", "有", "死亡", "dead",
                         "death", "died", "复发", "recurrence", "event", "发生", "事件"})
DATA_EXTS = (".csv", ".tsv", ".tab", ".txt", ".xlsx", ".xlsm", ".xls", ".sav", ".dta", ".rds")


# ─── small helpers ──────────────────────────────────────────────────────────

def _r(x, sig=6):
    """Round to `sig` significant digits and return a plain float (JSON friendly)."""
    return None if x is None else float(f"{float(x):.{sig}g}")


def _fmt_num(v):
    v = float(v)
    return str(int(v)) if v.is_integer() and abs(v) < 1e15 else f"{v:.6g}"


def _nfkc(s):
    return unicodedata.normalize("NFKC", str(s)).strip()


def _as_list(x):
    if x is None:
        return []
    if isinstance(x, str):
        return [p.strip() for p in x.split(",") if p.strip()]
    return [str(p) for p in x]


def _top(counter, k=5):
    return [v for v, _ in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))[:k]]


def _is_cluster_name(name):
    tokens = set(re.findall(r"[a-z]+", name.lower()))
    return bool(tokens & CLUSTER_TOKENS) or any(s in name for s in CLUSTER_SUBSTR)


def _is_id_name(name):
    return any(rx.search(name) for rx in ID_NAME_RES) and not _is_cluster_name(name)


def _is_pii_name(name):
    low = name.lower()
    tokens = set(re.findall(r"[a-z]+", low))
    return any(s in low for s in PII_NAME_SUBSTR) or bool(tokens & PII_NAME_TOKENS)


class _Vocab:
    """Missing-value vocabulary: text tokens (normalised), numeric codes, ambiguous tokens."""

    def __init__(self, extra_tokens=()):
        self.text, self.codes = set(), set()
        user = set()
        for tok in list(DEFAULT_MISSING_TOKENS) + list(extra_tokens):
            t = _nfkc(tok)
            if PLAIN_NUM_RE.match(t):
                self.codes.add(float(t))
            else:
                self.text.add(t.lower())
        for tok in extra_tokens:
            user.add(_nfkc(tok).lower())
        # a token the user added explicitly always means "missing"
        self.ambiguous = {a for a in AMBIGUOUS_TOKENS if a in self.text and a not in user}
        self.extra = [str(t) for t in extra_tokens]


# ─── reading (never writes) ─────────────────────────────────────────────────

def _sniff_sep(text):
    first = text.split("\n", 1)[0]
    counts = {s: first.count(s) for s in (",", "\t", ";", "|")}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def load_table(path, sheet=None, encoding=None, sep=None):
    """Read CSV / TSV / TXT / XLSX keeping every value exactly as written. Never writes.

    Returns (df, meta). CSV cells are str ('' = empty cell); XLSX cells keep Excel's own
    type (int / float / datetime / str), so numbers typed as text can be detected.
    CSV encodings tried in order: utf-8 (with or without BOM), gbk, gb18030.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"找不到数据文件 {path}（当前目录 {os.getcwd()}）")
    with open(path, "rb") as fh:          # read-only; the file is never opened for writing
        raw = fh.read()
    meta = {"file": os.path.basename(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        return _load_excel(raw, ext, sheet, meta)
    return _load_csv(raw, ext, encoding, sep, meta)


def _load_excel(raw, ext, sheet, meta):
    try:
        book = pd.ExcelFile(io.BytesIO(raw), engine=None if ext == ".xls" else "openpyxl")
    except ImportError:
        if ext == ".xls":
            raise SystemExit("读取 .xls 需要 xlrd：pip install xlrd（或在 Excel 里另存为 .xlsx / .csv）")
        raise SystemExit("读取 .xlsx 需要 openpyxl：pip install openpyxl")
    names = [str(n) for n in book.sheet_names]
    if sheet is None:
        target = names[0]
    elif str(sheet) in names:
        target = str(sheet)
    elif str(sheet).isdigit() and int(sheet) < len(names):
        target = names[int(sheet)]
    else:
        raise ValueError(f"找不到工作表 {sheet!r}；可用工作表：{names}")
    df = book.parse(target, dtype=object, na_filter=False)
    head = book.parse(target, header=None, nrows=1, dtype=object, na_filter=False)
    raw_header = ["" if v is None else str(v) for v in head.iloc[0].tolist()] if len(head) else []
    meta.update(format="xlsx", sheet=target, sheets=names, raw_header=raw_header)
    return df, meta


def _load_csv(raw, ext, encoding, sep, meta):
    tried = [encoding] if encoding else ["utf-8-sig", "gbk", "gb18030"]
    text = used = None
    for enc in tried:
        try:
            text, used = raw.decode(enc), enc
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if text is None:
        raise ValueError(f"无法按 {' / '.join(tried)} 解码该文件；请用 --encoding 指定编码")
    label = used
    if used == "utf-8-sig":
        label = "utf-8（带 BOM）" if raw.startswith(codecs.BOM_UTF8) else "utf-8"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if sep in ("\\t", "tab", "TAB"):
        sep = "\t"
    if sep is None:
        sep = "\t" if ext in (".tsv", ".tab") else _sniff_sep(text)
    if len(sep) != 1:
        raise ValueError("--sep 只能是一个字符，如 , 或 ; 或 \\t")
    # The csv module (not pandas.read_csv) so that no value is converted and a row with extra
    # fields cannot silently turn the first column into the index.
    try:
        rows = [r for r in csv.reader(io.StringIO(text), delimiter=sep) if r]
    except csv.Error as e:
        raise ValueError(f"CSV 解析失败（常见原因：引号不配对）：{e}")
    if not rows:
        raise ValueError("数据文件是空的")
    raw_header, body = rows[0], rows[1:]
    width = len(raw_header)
    longer = [r for r in body if len(r) > width]
    counts = {"longer": len(longer), "shorter": sum(1 for r in body if len(r) < width),
              "longer_with_content": sum(1 for r in longer if any(x.strip() for x in r[width:]))}
    data = [r[:width] + [""] * (width - len(r)) for r in body]
    df = pd.DataFrame(data, columns=_unique_names(raw_header), dtype=object)
    meta.update(format="csv", encoding=label, sep=sep, raw_header=raw_header, field_counts=counts)
    return df, meta


def _unique_names(header):
    """Column names as pandas would make them: empty -> 'Unnamed: j', repeats -> name.1, name.2."""
    out, used = [], set()
    for j, h in enumerate(header):
        base = h if h.strip() else f"Unnamed: {j}"
        name, k = base, 0
        while name in used:
            k += 1
            name = f"{base}.{k}"
        used.add(name)
        out.append(name)
    return out


# ─── cell classification ────────────────────────────────────────────────────

def _key(v):
    """Hashable key for one cell. Empty / NaN / None -> ('blank', '')."""
    if v is None:
        return ("blank", "")
    if isinstance(v, str):
        return ("s", v)
    if isinstance(v, (bool, np.bool_)):
        return ("s", str(bool(v)))
    if isinstance(v, (int, np.integer)):
        return ("n", int(v))
    if isinstance(v, (float, np.floating)):
        return ("blank", "") if math.isnan(v) else ("n", float(v))
    try:
        if pd.isna(v):
            return ("blank", "")
    except (TypeError, ValueError):
        pass
    if isinstance(v, _dt.datetime):          # includes pandas.Timestamp
        return ("d", v)
    if isinstance(v, _dt.date):
        return ("d", _dt.datetime(v.year, v.month, v.day))
    return ("s", str(v))


def _parse_date(s):
    if not (DATE_LIKE_RE.match(s) or re.fullmatch(r"\d{8}", s)):
        return None
    for fmt in DATE_FORMATS:
        if fmt == "%Y%m%d" and not re.fullmatch(r"\d{8}", s):
            continue
        try:
            return _dt.datetime.strptime(s, fmt), fmt
        except ValueError:
            continue
    return None


def _classify(key, vocab, date_hint):
    """-> (kind, value, extra). kinds: blank token amb number censored date loose text."""
    tag, v = key
    if tag == "blank":
        return ("blank", None, None)
    if tag == "n":
        return ("number", float(v), False)
    if tag == "d":
        return ("date", v, "日期格式单元格")
    t = v.strip()
    if t == "":
        return ("blank", None, None)
    n = unicodedata.normalize("NFKC", t)
    low = n.lower()
    if low in vocab.text:
        return ("amb" if low in vocab.ambiguous else "token", t, None)
    if PLAIN_NUM_RE.match(t):
        if date_hint and re.fullmatch(r"\d{8}", t):
            d = _parse_date(t)
            if d:
                return ("date", d[0], d[1])
        return ("number", float(t), True)
    if CENSORED_RE.match(n) or low in CENSORED_WORDS:
        return ("censored", t, None)
    d = _parse_date(n)
    if d:
        return ("date", d[0], d[1])
    if PLAIN_NUM_RE.match(n):
        return ("loose", float(n), ("全角字符", None))
    if THOUSANDS_RE.match(n):
        return ("loose", float(n.replace(",", "")), ("千分位逗号", None))
    if COMMA_DECIMAL_RE.match(n):
        return ("loose", float(n.replace(",", ".")), ("逗号作小数点", None))
    m = UNIT_RE.match(n)
    if m:
        return ("loose", float(m.group(1)), ("带单位", m.group(2).strip()))
    return ("text", t, None)


def _label(key):
    tag, v = key
    if tag == "n":
        return _fmt_num(v)
    if tag == "d":
        return v.strftime("%Y-%m-%d") if (v.hour, v.minute, v.second) == (0, 0, 0) else v.isoformat()
    return "" if tag == "blank" else v


# ─── one column ─────────────────────────────────────────────────────────────

def _numeric_stats(x, rng=None):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return {"n": 0}
    q = np.percentile(x, [0, 1, 5, 25, 50, 75, 95, 99, 100])
    mean = float(x.mean())
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    iqr = q[5] - q[3]
    lo, hi = q[3] - 1.5 * iqr, q[5] + 1.5 * iqr
    n_distinct = int(len(np.unique(x)))
    binary = n_distinct <= 2                      # outlier rules mean nothing for 0/1 codes
    out = {"n": int(len(x)), "min": _r(q[0]), "p1": _r(q[1]), "p5": _r(q[2]), "p25": _r(q[3]),
           "median": _r(q[4]), "p75": _r(q[5]), "p95": _r(q[6]), "p99": _r(q[7]), "max": _r(q[8]),
           "mean": _r(mean), "sd": _r(sd),
           "n_z_gt3": None if binary else (int((np.abs(x - mean) / sd > 3).sum()) if sd > 0 else 0),
           "n_iqr_out": None if binary else int(((x < lo) | (x > hi)).sum()),
           "iqr_bounds": None if binary else [_r(lo), _r(hi)],
           "n_negative": int((x < 0).sum()), "n_zero": int((x == 0).sum()),
           "n_distinct": n_distinct}
    if rng:
        out["range"] = [rng[0], rng[1]]
        out["n_out_of_range"] = int(((x < rng[0]) | (x > rng[1])).sum())
    return out


def _looks_like_int_id(values, counts):
    """All-unique integers that are a 1..n style sequence or share one length of >= 5 digits."""
    if len(values) < 20 or any(c > 1 for c in counts) or not all(float(v).is_integer() for v in values):
        return False
    ints = [int(v) for v in values]
    lengths = {len(str(abs(i))) for i in ints}
    return (max(ints) - min(ints) + 1 == len(ints)) or (len(lengths) == 1 and lengths.pop() >= 5)


def _looks_like_code_id(labels, counts):
    """All-unique codes such as P0001 / ZY2024001 (letters + digits)."""
    if len(labels) < 20 or any(c > 1 for c in counts):
        return False
    rx = re.compile(r"^(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9_\-]+$")
    return all(rx.match(s.strip()) for s in labels)


def _profile_column(name, values, vocab, text_numbers_are_issue, max_levels, rng, forced_id):
    n = len(values)
    keys = [_key(v) for v in values]
    counts = collections.Counter(keys)
    date_hint = bool(DATE_NAME_RE.search(name))
    cls = {k: _classify(k, vocab, date_hint) for k in counts}
    kc = collections.Counter()
    for k, c in counts.items():
        kc[cls[k][0]] += c

    # ── type ──
    n_num = kc["number"] + kc["loose"] + kc["censored"]
    n_def = n_num + kc["date"] + kc["text"]
    hints = []
    if forced_id or (n_def and _is_id_name(name)):
        ctype = "id"
    elif n_def == 0:
        ctype = "categorical" if kc["amb"] else "empty"
    elif kc["date"] >= 0.8 * n_def or (date_hint and kc["date"] >= 0.5 * n_def):
        ctype = "date"
    elif n_num >= 0.8 * n_def:
        num_keys = [k for k in counts if cls[k][0] == "number"]
        ctype = "numeric"
        if kc["loose"] == 0 and kc["censored"] == 0 and _looks_like_int_id(
                [cls[k][1] for k in num_keys], [counts[k] for k in num_keys]):
            ctype = "id"
    else:
        text_keys = [k for k in counts if cls[k][0] == "text"]
        if kc["text"] == n_def and _looks_like_code_id([cls[k][1] for k in text_keys],
                                                      [counts[k] for k in text_keys]):
            ctype = "id"
        else:
            ctype = "categorical"          # may become "text" below (free text / too many levels)
            if 0.2 <= n_num / n_def < 0.8:
                hints.append(f"约 {round(100 * n_num / n_def)}% 是数字、其余是文字，内容可能混杂")

    # ── missing: blank + tokens (+ ambiguous tokens / numeric codes where they cannot be values) ──
    amb_is_missing = ctype in ("numeric", "date", "id", "empty")
    missing_by_key = {}
    disguised, codes, kept_amb = collections.Counter(), collections.Counter(), collections.Counter()
    for k, c in counts.items():
        kind, val, _ = cls[k]
        miss = kind in ("blank", "token") or (kind == "amb" and amb_is_missing)
        if kind == "token" or (kind == "amb" and amb_is_missing):
            disguised[val] += c
        elif kind == "amb":
            kept_amb[val] += c
        elif kind == "number" and ctype == "numeric" and val in vocab.codes:
            miss = True
            codes[_fmt_num(val)] += c
        missing_by_key[k] = miss
    n_missing = sum(c for k, c in counts.items() if missing_by_key[k])
    n_valid = n - n_missing

    col = {"name": name, "type": ctype, "type_label": TYPE_LABELS[ctype], "n": n, "n_valid": n_valid,
           "n_blank": kc["blank"], "disguised_missing": dict(disguised), "missing_codes": dict(codes),
           "n_missing_total": n_missing, "pct_missing_total": round(100 * n_missing / n, 1) if n else 0.0,
           "pct_missing_blank_only": round(100 * kc["blank"] / n, 1) if n else 0.0,
           "possible_missing_kept": dict(kept_amb), "hints": hints}

    # ── privacy: count hits only, never keep the values ──
    id_hits = phone_hits = 0
    for k, c in counts.items():
        if k[0] in ("s", "n"):
            s = _label(k)
            id_hits += c if ID_CARD_RE.search(s) else 0
            phone_hits += c if MOBILE_RE.search(s) else 0
    by_name = _is_pii_name(name)
    pii = by_name or id_hits > 0 or phone_hits > 0
    col["pii"] = {"by_name": by_name, "id_card_hits": id_hits, "phone_hits": phone_hits} if pii else None

    # ── censored strings ──
    cens = collections.Counter({cls[k][1]: c for k, c in counts.items() if cls[k][0] == "censored"})
    if cens:
        col["censored"] = {"n": sum(cens.values()), "examples": [] if pii else _top(cens)}

    # ── numeric column that would load as text ──
    if ctype == "numeric":
        reasons, examples, units = collections.Counter(), collections.Counter(), collections.Counter()
        for k, c in counts.items():
            kind, val, extra = cls[k]
            if kind in ("token", "amb") and val not in PANDAS_DEFAULT_NA:
                reasons["伪装缺失（非标准写法）"] += c
            elif kind == "censored":
                reasons["截断值"] += c
            elif kind == "loose":
                reasons[extra[0]] += c
                examples[k[1].strip()] += c
                if extra[1]:
                    units[extra[1]] += c
            elif kind in ("text", "date"):
                reasons["其他文字"] += c
                examples[_label(k).strip()] += c
            elif kind == "number" and extra and text_numbers_are_issue:
                reasons["以文本格式存储的数字"] += c
        if reasons:
            col["numeric_as_text"] = {"reasons": dict(reasons), "examples": [] if pii else _top(examples),
                                      "units": {} if pii else dict(units)}
            if len(units) > 1:
                hints.append("同一列出现多种单位：" + "、".join(f"{u}×{units[u]}" for u in _top(units)))

    # ── numeric distribution (counted, nothing removed) ──
    if ctype == "numeric":
        vals, wts = [], []
        for k, c in counts.items():
            kind, val, _ = cls[k]
            if (kind == "number" and not missing_by_key[k]) or kind == "loose":
                vals.append(val)
                wts.append(c)
        x = np.repeat(np.array(vals, dtype=float), np.array(wts, dtype=int)) if vals else np.array([])
        stats = _numeric_stats(x, rng)
        if cens:
            stats["note"] = f"已排除 {sum(cens.values())} 个截断值"
        col["numeric"] = None if pii else stats
        if not pii and 0 < stats.get("n_distinct", 0) <= 10:
            hints.append(f"只有 {stats['n_distinct']} 个不同取值，可能是分类编码")
        if date_hint:
            serial = sum(c for k, c in counts.items() if cls[k][0] == "number" and 20000 <= cls[k][1] <= 80000)
            if serial:
                hints.append(f"列名像日期，但有 {serial} 个数字像 Excel 日期序列号（需要换算成日期）")

    # ── dates ──
    if ctype == "date":
        col["date"] = _date_details(counts, cls, missing_by_key, pii)

    # ── categorical levels (also for numeric columns with <= 10 distinct values) ──
    if ctype in ("categorical", "numeric"):
        levels = collections.Counter()
        for k, c in counts.items():
            if not missing_by_key[k]:
                levels[_label(k)] += c
        if ctype == "categorical" and _is_free_text(levels, n_valid):
            ctype = "text"
        elif not pii and (ctype == "categorical" or len(levels) <= 10):
            col["categorical"] = _levels_summary(levels, max_levels)
        if ctype != "text" and len(levels) == 1:
            hints.append("所有有效值都相同（常数列）")
    col["type"], col["type_label"] = ctype, TYPE_LABELS[ctype]
    if ctype in ("text", "id"):
        col["n_distinct"] = len({_label(k).strip() for k in counts if not missing_by_key[k]})
    return col, keys, missing_by_key


def _is_free_text(levels, n_valid):
    """Too many distinct values, mostly unique values or long strings -> free text, not categories."""
    n_levels = len(levels)
    if n_levels > 20 and not (n_levels <= 100 and n_levels <= 0.05 * n_valid):
        return True
    if n_levels > 5 and n_levels > 0.5 * n_valid:
        return True
    total = sum(levels.values())
    return total > 0 and sum(len(str(lab)) * c for lab, c in levels.items()) / total > 30


def _levels_summary(levels, max_levels):
    ordered = sorted(levels.items(), key=lambda kv: (-kv[1], kv[0]))
    groups = collections.defaultdict(list)
    for lab, _ in ordered:
        groups[re.sub(r"\s+", " ", _nfkc(lab).lower())].append(lab)
    return {"n_levels": len(ordered),
            "levels": [[lab, cnt] for lab, cnt in ordered[:max_levels]],
            "n_levels_truncated": max(0, len(ordered) - max_levels),
            "n_rows_truncated": sum(cnt for _, cnt in ordered[max_levels:]),
            "inconsistent": [g for g in groups.values() if len(g) > 1],
            "n_levels_lt5": sum(1 for _, cnt in ordered if cnt < 5)}


def _date_details(counts, cls, missing_by_key, pii):
    fmts, bad, dmy = collections.Counter(), collections.Counter(), [0, 0, 0]   # d/m, m/d, undecidable
    stamps, serial = [], 0
    for k, c in counts.items():
        kind, val, extra = cls[k]
        if missing_by_key[k]:
            continue
        if kind == "date":
            fmts[extra] += c
            stamps.append((val, c))
            m = DMY_RE.match(k[1].strip()) if k[0] == "s" else None
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                dmy[0 if a > 12 else 1 if b > 12 else 2] += c
        else:
            bad[_label(k).strip()] += c
            if kind == "number" and 20000 <= val <= 80000:
                serial += c
    tomorrow = _dt.datetime.combine(_dt.date.today(), _dt.time()) + _dt.timedelta(days=1)
    out = {"n_parsed": sum(c for _, c in stamps), "n_unparseable": sum(bad.values()),
           "unparseable_examples": [] if pii else _top(bad), "formats": dict(fmts),
           "n_future": sum(c for v, c in stamps if v > tomorrow),
           "n_before_1900": sum(c for v, c in stamps if v.year < 1900), "notes": []}
    if stamps and not pii:
        out["min"] = min(v for v, _ in stamps).strftime("%Y-%m-%d")
        out["max"] = max(v for v, _ in stamps).strftime("%Y-%m-%d")
    if len(fmts) > 1:
        out["notes"].append("同一列混用多种日期写法")
    if dmy[0] and dmy[1]:
        out["notes"].append("同一列里既有 日/月/年 又有 月/日/年 写法")
    elif dmy[2] and not (dmy[0] or dmy[1]):
        out["notes"].append("日/月顺序无法从数据判断（如 03/04/2024），需按导出系统确认")
    if serial:
        out["notes"].append(f"{serial} 个数字像 Excel 日期序列号（需要换算成日期）")
    return out


# ─── whole table ────────────────────────────────────────────────────────────

def _rows_summary(sizes):
    arr = np.array(sorted(sizes), dtype=float)
    return {"min": int(arr.min()), "median": _r(np.median(arr)), "max": int(arr.max())} if len(arr) else {}


def _row_labels(keys, missing_by_key):
    return [None if missing_by_key[k] else _label(k).strip() for k in keys]


def _id_structure(name, labels):
    n_rows = len(labels)
    counts = collections.Counter(v for v in labels if v is not None)
    multi = {k: c for k, c in counts.items() if c > 1}
    dist = collections.Counter(counts.values())
    return {"column": name, "n_rows": n_rows, "n_missing_id": n_rows - sum(counts.values()),
            "n_ids": len(counts), "n_ids_multi": len(multi), "n_rows_in_multi": sum(multi.values()),
            "max_rows_per_id": max(counts.values()) if counts else 0,
            "rows_per_id_distribution": {str(k): v for k, v in sorted(dist.items())[:10]}}


def _cluster_structure(name, labels, id_labels):
    groups = collections.Counter(v for v in labels if v is not None)
    out = {"column": name, "n_clusters": len(groups), "rows_per_cluster": _rows_summary(groups.values())}
    if id_labels is not None:
        ids_per = collections.defaultdict(set)
        clusters_per_id = collections.defaultdict(set)
        for cl, pid in zip(labels, id_labels):
            if cl is not None and pid is not None:
                ids_per[cl].add(pid)
                clusters_per_id[pid].add(cl)
        out["ids_per_cluster"] = _rows_summary([len(s) for s in ids_per.values()])
        out["n_ids_in_several_clusters"] = sum(1 for s in clusters_per_id.values() if len(s) > 1)
    return out


def _binary_event(levels):
    """levels: [[label, count], [label, count]] -> (event_label or None)."""
    labs = [str(l) for l, _ in levels]
    if all(PLAIN_NUM_RE.match(x) for x in labs):
        return "1" if {float(x) for x in labs} == {0.0, 1.0} else None
    hits = [x for x in labs if _nfkc(x).lower() in EVENT_WORDS]
    return hits[0] if len(hits) == 1 else None


def _outcome_summary(col, time_col):
    """Only the outcome's OWN distribution. Nothing here looks at any other variable."""
    out = {"column": col["name"], "n_rows": col["n"], "n_missing": col["n_missing_total"],
           "n_valid": col["n_valid"], "kind": "empty", "levels": None, "event_label": None,
           "events": None, "non_events": None, "minority_count": None, "numeric": None,
           "time": None, "notes": []}
    cat = col.get("categorical")
    if col["pii"]:
        out["notes"].append("该列疑似隐私字段，不显示取值")
    elif cat and cat["n_levels"] == 2:
        out.update(kind="binary", levels=cat["levels"])
        ev = _binary_event(cat["levels"])
        counts = dict((str(l), c) for l, c in cat["levels"])
        out["minority_count"] = min(counts.values())
        if ev is not None:
            out.update(event_label=ev, events=counts[ev], non_events=sum(counts.values()) - counts[ev])
        else:
            out["notes"].append("无法从编码判断哪一类是事件，请确认后按那一类的例数计事件数")
    elif cat and cat["n_levels"] > 2:
        out.update(kind="categorical", levels=cat["levels"])
        out["notes"].append(f"多分类结局（{cat['n_levels']} 类）")
    elif cat and cat["n_levels"] == 1:
        out.update(kind="constant", levels=cat["levels"])
        out["notes"].append("结局只有一个取值")
    elif col.get("numeric"):
        s = col["numeric"]
        out.update(kind="numeric", numeric={k: s.get(k) for k in ("n", "min", "median", "max", "mean", "sd")})
    if col["type"] == "text":
        out["notes"].append("结局列像自由文本，需要先编码")
    if time_col is not None:
        s = time_col.get("numeric") or {}
        out["time"] = {"column": time_col["name"], "n_valid": time_col["n_valid"],
                       "n_missing": time_col["n_missing_total"],
                       "min": s.get("min"), "median": s.get("median"), "max": s.get("max"),
                       "n_nonpositive": (s.get("n_negative", 0) + s.get("n_zero", 0)) if s else None}
        if time_col["type"] != "numeric":
            out["time"]["note"] = f"随访时间列被识别为{time_col['type_label']}，请检查"
    return out


def _header_issues(source, names):
    raw_header = source.get("raw_header")
    header = [str(h) for h in (raw_header if raw_header else names)]
    issues = []
    fc = source.get("field_counts") or {}
    if fc.get("longer_with_content"):
        issues.append(f"{fc['longer_with_content']} 行的字段数多于表头，多出的内容没有体检"
                      "（常见原因：取值里有没加引号的逗号）")
    elif fc.get("longer"):
        issues.append(f"{fc['longer']} 行末尾有多余的分隔符（多出的格是空的，已忽略）")
    if fc.get("shorter"):
        issues.append(f"{fc['shorter']} 行的字段数少于表头（缺的格按空值计）")
    dups = sorted(h for h, c in collections.Counter(header).items() if c > 1 and h.strip())
    if dups:
        issues.append("列名重复：" + "、".join(dups))
    empty = sum(1 for h in header if not h.strip() or h.startswith("Unnamed:"))
    if empty:
        issues.append(f"{empty} 个列没有列名（表头可能不在第一行，或有合并单元格）")
    spaced = [h for h in header if h.strip() and h != h.strip()]
    if spaced:
        issues.append("列名首尾有空格：" + "、".join(repr(h) for h in spaced[:10]))
    return issues


def profile_dataframe(df, id_col=None, outcome_col=None, time_col=None, cluster_cols=None,
                      missing_tokens=None, ranges=None, max_levels=15, source=None):
    """Structure / quality profile of one table -> JSON-serialisable dict.

    id_col       patient ID column (None: detect ID-like columns by name / values)
    outcome_col  outcome column(s): ONLY their own distribution and event count are reported
    time_col     follow-up time for a survival outcome (described on its own)
    cluster_cols centre / surgeon / reader columns (None: detect by name)
    missing_tokens extra disguised-missing spellings added to DEFAULT_MISSING_TOKENS
    ranges       {'age': (0, 120)} plausible ranges; values outside are only counted
    source       meta dict from load_table() (file name, sha256, encoding, sheet ...)
    Nothing in this function relates one variable to another or to the outcome.
    """
    source = dict(source or {})
    vocab = _Vocab(_as_list(missing_tokens) if isinstance(missing_tokens, str) else (missing_tokens or ()))
    ranges = ranges or {}
    names = _unique_names([str(c) for c in df.columns])
    ids, outs, times, clus = (_as_list(id_col), _as_list(outcome_col), _as_list(time_col),
                              _as_list(cluster_cols))
    for label, cols in (("--id", ids), ("--outcome", outs), ("--time", times), ("--cluster", clus)):
        for c in cols:
            if c not in names:
                raise ValueError(f"{label} 指定的列 {c!r} 不在数据中；可用列：{names}")
    if len(ids) > 1:
        raise ValueError("--id 只能指定一个列")
    if times and not outs:
        raise ValueError("--time 需要与 --outcome（事件列）一起使用")
    text_numbers_are_issue = source.get("format") != "csv"   # in a CSV every number is text

    n_rows = len(df)
    columns, keys_by, miss_by = [], {}, {}
    any_missing = np.zeros(n_rows, dtype=bool)
    for j, name in enumerate(names):
        col, keys, missing_by_key = _profile_column(
            name, df.iloc[:, j].tolist(), vocab, text_numbers_are_issue, max_levels,
            ranges.get(name), forced_id=bool(ids) and name == ids[0])
        columns.append(col)
        keys_by[name], miss_by[name] = keys, missing_by_key
        any_missing |= np.fromiter((missing_by_key[k] for k in keys), dtype=bool, count=n_rows)
    by_name = {c["name"]: c for c in columns}

    row_tuples = collections.Counter(zip(*[keys_by[nm] for nm in names])) if names else collections.Counter()
    n_dup_rows = sum(c - 1 for c in row_tuples.values() if c > 1)

    # ── repeated IDs and clusters (structure only) ──
    id_names = ids or [c["name"] for c in columns if c["type"] == "id" and not _is_cluster_name(c["name"])][:5]
    id_structure = [_id_structure(nm, _row_labels(keys_by[nm], miss_by[nm])) for nm in id_names]
    main_id = id_names[0] if id_names else None
    main_id_labels = _row_labels(keys_by[main_id], miss_by[main_id]) if main_id else None
    if clus:
        cluster_names = clus
    else:
        cluster_names = []
        for c in columns:
            if c["name"] in id_names or c["name"] in outs or not _is_cluster_name(c["name"]):
                continue
            num = c.get("numeric") or {}
            if c["type"] in ("categorical", "id", "text") or (c["type"] == "numeric" and 0 < num.get("n_distinct", 99) <= 50):
                cluster_names.append(c["name"])
    clusters = [_cluster_structure(nm, _row_labels(keys_by[nm], miss_by[nm]),
                                   main_id_labels if nm != main_id else None) for nm in cluster_names]

    # ── outcome: its own distribution only ──
    outcomes = []
    for i, nm in enumerate(outs):
        tcol = by_name[times[0]] if (times and i == 0) else None
        outcomes.append(_outcome_summary(by_name[nm], tcol))

    type_counts = collections.Counter(c["type"] for c in columns)
    profile = {
        "tool": "data_profile.py", "statement": STATEMENT,
        "generated": _dt.date.today().isoformat(),
        "source": {k: v for k, v in source.items() if k != "raw_header"},
        "n_rows": n_rows, "n_cols": len(names),
        "type_counts": {TYPE_LABELS[t]: type_counts.get(t, 0) for t in TYPE_LABELS},
        "header_issues": _header_issues(source, [str(c) for c in df.columns]),
        "n_duplicate_rows": int(n_dup_rows),
        "n_complete_rows": int(n_rows - any_missing.sum()),
        "columns": columns, "id_structure": id_structure, "clusters": clusters, "outcomes": outcomes,
        "privacy": [{"column": c["name"], **c["pii"]} for c in columns if c["pii"]],
        "missing_tokens": {"default": [t for t in DEFAULT_MISSING_TOKENS if t], "added": vocab.extra,
                           "ambiguous": sorted(vocab.ambiguous)},
    }
    profile["problems"] = _problems(profile)
    return profile


def _problems(p):
    """Plain-language list of the issues that need a decision in the SAP / cleaning code."""
    out = list(p["header_issues"])
    pii_cols = {x["column"] for x in p["privacy"]}
    cols = [c for c in p["columns"] if c["name"] not in pii_cols]   # privacy columns are listed once, at the end
    if p["n_duplicate_rows"]:
        out.append(f"完全重复的行 {p['n_duplicate_rows']} 行（可能是导出重复）")
    dis = []
    for c in cols:
        parts = [f"{t or '空白'}×{n}" for t, n in c["disguised_missing"].items()]
        parts += [f"{t}×{n}" for t, n in c["missing_codes"].items()]
        if parts:
            dis.append(f"{c['name']}（{'、'.join(parts[:6])}）")
    if dis:
        out.append("伪装缺失：" + "；".join(dis))
    kept = [f"{c['name']}（{'、'.join(f'{t}×{n}' for t, n in c['possible_missing_kept'].items())}）"
            for c in cols if c["possible_missing_kept"]]
    if kept:
        out.append("可能表示缺失、也可能是真实取值（按取值保留，请确认）：" + "；".join(kept))
    high = [f"{c['name']} {c['pct_missing_total']}%" for c in cols if c["pct_missing_total"] >= 20 and c["type"] != "empty"]
    if high:
        out.append("缺失 ≥20%（含伪装缺失）：" + "、".join(high))
    empty = [c["name"] for c in cols if c["type"] == "empty"]
    if empty:
        out.append("整列缺失：" + "、".join(empty))
    cens = [f"{c['name']}（{c['censored']['n']} 个）" for c in cols if c.get("censored")]
    if cens:
        out.append("截断值（如 <0.1、>1000）：" + "、".join(cens))
    nat = [c["name"] for c in cols if c.get("numeric_as_text")]
    if nat:
        out.append("数值列直接读入会变成文本：" + "、".join(nat))
    bad_dates = [f"{c['name']}（{c['date']['n_unparseable']} 个）" for c in cols
                 if c.get("date") and c["date"]["n_unparseable"]]
    if bad_dates:
        out.append("无法解析的日期：" + "、".join(bad_dates))
    inc = [c["name"] for c in cols if (c.get("categorical") or {}).get("inconsistent")]
    if inc:
        out.append("分类取值只差大小写/空格：" + "、".join(inc))
    for s in p["id_structure"]:
        if s["n_ids_multi"]:
            out.append(f"{s['column']}：{s['n_ids_multi']} 个 ID 出现多行（每个 ID 最多 {s['max_rows_per_id']} 行）"
                       "——这些行不是相互独立的观测")
    for s in p["clusters"]:
        if s["n_clusters"] > 1:
            out.append(f"{s['column']}：{s['n_clusters']} 个聚类单位，每个 {s['rows_per_cluster'].get('min')}–"
                       f"{s['rows_per_cluster'].get('max')} 行")
    if p["privacy"]:
        out.append("疑似隐私字段：" + "、".join(x["column"] for x in p["privacy"]))
    return out


# ─── Markdown report ────────────────────────────────────────────────────────

def _cell(s, limit=40):
    s = str(s).replace("`", "'").replace("|", "¦").replace("\n", " ").replace("\r", " ")
    if len(s) > limit:
        s = s[:limit] + "…"
    return f"'{s}'" if (s != s.strip() or s == "") else s


def _code(s, limit=40):
    return f"`{_cell(s, limit)}`"


def _table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    return "\n".join(lines)


def _fmt(v, sig=None):
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return f"{float(v):.{sig}g}" if sig else _fmt_num(v)
    return str(v)


def render_markdown(p):
    """Render a profile dict (from profile_dataframe) as the data-profile.md report."""
    src = p.get("source", {})
    cols = p["columns"]
    title = src.get("file") or "数据"
    L = [f"# 数据体检报告：{title}", "", f"> {p['statement']}。", ""]
    info = []
    if src.get("file"):
        extra = [f"{src.get('bytes', 0)} 字节", f"sha256 `{src.get('sha256', '')}`"]
        if src.get("encoding"):
            extra.append(f"编码 {src['encoding']}")
        if src.get("sep"):
            extra.append("分隔符 " + ("制表符" if src["sep"] == "\t" else f"`{src['sep']}`"))
        info.append(f"- 文件：{src['file']}（{'；'.join(extra)}）")
    if src.get("sheet"):
        info.append(f"- 工作表：{src['sheet']}（共 {len(src.get('sheets', []))} 个：{'、'.join(src.get('sheets', []))}）")
    tc = "、".join(f"{k} {v}" for k, v in p["type_counts"].items() if v)
    info += [f"- 体检日期：{p['generated']}；工具：data_profile.py（只读，没有修改或另存数据）",
             f"- 规模：{p['n_rows']} 行 × {p['n_cols']} 列；列类型：{tc}",
             f"- 完全重复的行：{p['n_duplicate_rows']}；没有任何缺失的行：{p['n_complete_rows']}"
             + (f"（{round(100 * p['n_complete_rows'] / p['n_rows'], 1)}%）" if p["n_rows"] else "")]
    L += info + ["", "## 1. 需要在计划和清洗代码里处理的问题", ""]
    L += [f"- {x}" for x in p["problems"]] if p["problems"] else ["- 未发现需要特别处理的结构或质量问题。"]

    L += ["", "## 2. 各列概览", ""]
    rows = []
    for c in cols:
        dis = sum(c["disguised_missing"].values()) + sum(c["missing_codes"].values())
        note = list(c["hints"])
        if c.get("numeric_as_text"):
            note.append("读入会变文本")
        if c.get("censored"):
            note.append(f"截断值 {c['censored']['n']}")
        if c["pii"]:
            note.append("疑似隐私字段")
        rows.append([_code(c["name"]), c["type_label"], c["n_valid"],
                     f"{c['n_missing_total']}（{c['pct_missing_total']}%）", dis or "", "；".join(note)])
    L.append(_table(["列", "类型", "有效值", "缺失（含伪装）", "其中伪装缺失", "备注"], rows))

    L += ["", "## 3. 缺失与伪装缺失", ""]
    rows = []
    for c in cols:
        if not c["n_missing_total"] and not c["possible_missing_kept"]:
            continue
        dis = "、".join(f"{_code(t) if t else '空白'}×{n}" for t, n in c["disguised_missing"].items())
        cod = "、".join(f"{_code(t)}×{n}" for t, n in c["missing_codes"].items())
        kept = "、".join(f"{_code(t)}×{n}" for t, n in c["possible_missing_kept"].items())
        rows.append([_code(c["name"]), c["n_blank"], dis, cod, f"{c['n_missing_total']}（{c['pct_missing_total']}%）", kept])
    if rows:
        L.append(_table(["列", "空值", "文字型伪装缺失", "数字缺失码", "合计（比例）", "未计入缺失、可能是真实取值"], rows))
    else:
        L.append("没有空值或伪装缺失。")
    L += ["", "说明：`无`、`none`、`-` 在数值/日期/ID 列按缺失计；在分类列可能表示\"没有\"或\"阴性\"，"
          "按取值保留并列在最后一列。`999`、`9999`、`-99`、`-999` 只在数值列按缺失码计，"
          "如果它在该列是真实数值，请在清洗时不要当缺失。"]

    cens = [c for c in cols if c.get("censored")]
    nat = [c for c in cols if c.get("numeric_as_text")]
    L += ["", "## 4. 截断值与\"数值存成文本\"", ""]
    if cens:
        L.append(_table(["列", "截断值个数", "示例"], [
            [_code(c["name"]), c["censored"]["n"], "、".join(_code(x) for x in c["censored"]["examples"]) or "（不显示）"]
            for c in cens]))
        L.append("")
    if nat:
        L.append(_table(["列", "直接读入会变成文本的原因（个数）", "示例", "单位"], [
            [_code(c["name"]), "、".join(f"{k} {v}" for k, v in c["numeric_as_text"]["reasons"].items()),
             "、".join(_code(x) for x in c["numeric_as_text"]["examples"]),
             "、".join(f"{_code(u)}×{n}" for u, n in c["numeric_as_text"]["units"].items())]
            for c in nat]))
    if not cens and not nat:
        L.append("没有截断值；数值列都能直接按数字读入。")

    num = [c for c in cols if c.get("numeric")]
    L += ["", "## 5. 数值列分布（离群值只计数，不删除）", ""]
    if num:
        rows = []
        for c in num:
            s = c["numeric"]
            if not s.get("n"):
                rows.append([_code(c["name"]), 0] + [""] * 9)
                continue
            rows.append([_code(c["name"]), s["n"], _fmt(s["min"]), _fmt(s["p25"]), _fmt(s["median"]),
                         _fmt(s["p75"]), _fmt(s["max"]), f"{_fmt(s['mean'], 4)} ± {_fmt(s['sd'], 4)}",
                         "—" if s["n_z_gt3"] is None else s["n_z_gt3"],
                         "—" if s["n_iqr_out"] is None else s["n_iqr_out"],
                         s.get("n_out_of_range", "") if "range" in s else ""])
        L.append(_table(["列", "n", "最小", "P25", "中位数", "P75", "最大", "均值 ± SD", "Z>3", "IQR×1.5 外",
                         "超出 --range"], rows))
        L += ["", "统计时已排除空值、伪装缺失、缺失码和截断值；只有两个取值的列不计离群（—）；"
              "是否处理离群值由 SAP 预先规定。"]
    else:
        L.append("没有数值列（或数值列均为疑似隐私字段，不显示分布）。")

    cat = [c for c in cols if c.get("categorical")]
    L += ["", "## 6. 分类取值", ""]
    if cat:
        for c in cat:
            k = c["categorical"]
            levels = "、".join(f"{_code(lab)} {cnt}" for lab, cnt in k["levels"])
            more = f"；其余 {k['n_levels_truncated']} 个取值共 {k['n_rows_truncated']} 行" if k["n_levels_truncated"] else ""
            L.append(f"- {_code(c['name'])}（{k['n_levels']} 个取值）：{levels}{more}")
            if k["inconsistent"]:
                L.append("  - 只差大小写/空格的写法：" + "；".join(" / ".join(_code(x) for x in g) for g in k["inconsistent"]))
            if k["n_levels_lt5"] and c["type"] == "categorical":
                L.append(f"  - {k['n_levels_lt5']} 个取值不足 5 例（建模时可能需要合并）")
    else:
        L.append("没有分类列。")

    dates = [c for c in cols if c.get("date")]
    L += ["", "## 7. 日期列", ""]
    if dates:
        rows = []
        for c in dates:
            d = c["date"]
            rng = f"{d['min']} ~ {d['max']}" if d.get("min") else ""
            rows.append([_code(c["name"]), d["n_parsed"], d["n_unparseable"],
                         "、".join(_code(x) for x in d["unparseable_examples"]),
                         "、".join(f"{k} {v}" for k, v in d["formats"].items()), rng,
                         "；".join(d["notes"] + ([f"晚于体检日 {d['n_future']} 个"] if d["n_future"] else [])
                                  + ([f"早于 1900 年 {d['n_before_1900']} 个"] if d["n_before_1900"] else []))])
        L.append(_table(["列", "可解析", "无法解析", "无法解析的示例", "写法", "范围", "备注"], rows))
    else:
        L.append("没有识别为日期的列。")

    L += ["", "## 8. 重复 ID 与聚类结构", ""]
    if p["id_structure"]:
        for s in p["id_structure"]:
            L.append(f"- {_code(s['column'])}：{s['n_rows']} 行对应 {s['n_ids']} 个 ID（缺 ID {s['n_missing_id']} 行）；"
                     f"{s['n_ids_multi']} 个 ID 出现多行，共 {s['n_rows_in_multi']} 行，每个 ID 最多 {s['max_rows_per_id']} 行")
            if s["n_ids_multi"]:
                dist = "、".join(f"{k} 行的 ID {v} 个" for k, v in s["rows_per_id_distribution"].items())
                L.append(f"  - 每个 ID 的行数：{dist}")
                L.append("  - 同一 ID 的多行不是相互独立的观测：分析时需要按患者汇总、用 GEE / 混合模型，"
                         "或（建模时）按患者划分训练/测试集——在 SAP 里预先写明")
    else:
        L.append("- 未识别到 ID 列；若同一患者可能有多行，请用 `--id <患者ID列>` 重新体检。")
    for s in p["clusters"]:
        line = (f"- 聚类 {_code(s['column'])}：{s['n_clusters']} 个单位，每个单位 "
                f"{s['rows_per_cluster'].get('min')}–{s['rows_per_cluster'].get('max')} 行"
                f"（中位数 {_fmt(s['rows_per_cluster'].get('median'))}）")
        if "ids_per_cluster" in s and s["ids_per_cluster"]:
            line += f"；每个单位 {s['ids_per_cluster']['min']}–{s['ids_per_cluster']['max']} 个 ID"
            if s["n_ids_in_several_clusters"]:
                line += f"；{s['n_ids_in_several_clusters']} 个 ID 出现在多个单位"
        L.append(line)
    if any(s["n_clusters"] > 1 for s in p["clusters"]):
        L.append("  - 数据来自多个中心/术者/读片者时，SAP 需要写明怎么处理（分层、随机效应或 GEE）")

    L += ["", "## 9. 结局（只报告结局本身的分布）", ""]
    if p["outcomes"]:
        for o in p["outcomes"]:
            L.append(f"- {_code(o['column'])}：有效 {o['n_valid']} / {o['n_rows']}，缺失 {o['n_missing']}")
            if o["levels"]:
                L.append("  - 取值：" + "、".join(f"{_code(lab)} {cnt}" for lab, cnt in o["levels"]))
            if o["events"] is not None:
                L.append(f"  - 事件（{_code(o['event_label'])}）{o['events']} 例，非事件 {o['non_events']} 例")
            if o["minority_count"] is not None:
                L.append(f"  - 较少一类 {o['minority_count']} 例（可纳入多少个预测变量取决于这个数）")
            if o["numeric"]:
                s = o["numeric"]
                L.append(f"  - 数值结局：n={s['n']}，最小 {_fmt(s['min'])}，中位数 {_fmt(s['median'])}，"
                         f"最大 {_fmt(s['max'])}，均值 {_fmt(s['mean'])} ± {_fmt(s['sd'])}")
            if o["time"]:
                t = o["time"]
                L.append(f"  - 随访时间 {_code(t['column'])}：有效 {t['n_valid']}，缺失 {t['n_missing']}，"
                         f"最小 {_fmt(t['min'])}，中位数 {_fmt(t['median'])}，最大 {_fmt(t['max'])}，"
                         f"≤0 的 {_fmt(t['n_nonpositive'])} 个" + (f"（{t['note']}）" if t.get("note") else ""))
            for note in o["notes"]:
                L.append(f"  - {note}")
        L.append("- 这里没有、也不应该有按结局分组的任何统计（计划确认前只看结构和质量）。")
    else:
        L.append("- 未指定结局（`--outcome`）。")

    L += ["", "## 10. 疑似隐私字段（只列列名与命中数，不显示取值）", ""]
    if p["privacy"]:
        L.append(_table(["列", "列名像隐私字段", "18 位身份证号样式", "11 位手机号样式"], [
            [_code(x["column"]), "是" if x["by_name"] else "", x["id_card_hits"] or "", x["phone_hits"] or ""]
            for x in p["privacy"]]))
        L += ["", "分析前请去标识化（删除或替换为研究编号）；这些列不要进入分析数据集和任何对外共享的文件。"]
    else:
        L.append("未发现。")

    mt = p["missing_tokens"]
    L += ["", "## 说明", "",
          "- 伪装缺失默认词表：" + "、".join(_code(t) for t in mt["default"]) + "（外加空白单元格）"
          + ("；本次追加：" + "、".join(_code(t) for t in mt["added"]) if mt["added"] else ""),
          "- 类型是按取值推断的，只作参考；变量的真实含义以数据字典和 SAP 为准。", ""]
    return "\n".join(L)


# ─── terminal summary & CLI ─────────────────────────────────────────────────

def summary_lines(p):
    src = p.get("source", {})
    head = f"{src.get('file', '数据')}：{p['n_rows']} 行 × {p['n_cols']} 列"
    if src.get("encoding"):
        head += f"（编码 {src['encoding']}）"
    if src.get("sheet"):
        head += f"（工作表 {src['sheet']}）"
    lines = [head, p["statement"],
             "列类型：" + "、".join(f"{k} {v}" for k, v in p["type_counts"].items() if v)]
    if p["problems"]:
        lines.append("需要处理的问题：")
        lines += [f"  - {x}" for x in p["problems"]]
    for o in p["outcomes"]:
        s = f"结局 {o['column']}：有效 {o['n_valid']}/{o['n_rows']}"
        if o["events"] is not None:
            s += f"，事件（={o['event_label']}）{o['events']} 例"
        elif o["minority_count"] is not None:
            s += f"，较少一类 {o['minority_count']} 例"
        lines.append(s)
    return lines


def _parse_ranges(items):
    out = {}
    for item in items:
        for part in [x for x in item.split(",") if x.strip()]:
            try:
                col, bounds = part.rsplit("=", 1)
                lo, hi = bounds.split(":")
                out[col.strip()] = (float(lo), float(hi))
            except ValueError:
                raise ValueError(f"--range 格式应为 列名=下限:上限（如 age=0:120），收到 {part!r}")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="data_profile.py",
        description="只读数据体检：描述数据结构与质量（类型、伪装缺失、截断值、数值存成文本、日期、"
                    "离群计数、分类取值、重复 ID/聚类、结局事件数、疑似隐私字段）。"
                    "不修改、不清洗、不另存数据；不计算任何变量与结局的关系，也不计算变量之间的关联。",
        epilog="例：python3 data_profile.py data.csv --id patient_id --outcome recurrence --report data-profile.md",
    )
    p.add_argument("data", help="数据文件：.csv / .tsv / .txt / .xlsx（只读，不会被修改）")
    p.add_argument("--sheet", help="xlsx 的工作表名或序号（从 0 开始），默认第一个")
    p.add_argument("--id", dest="id_col", help="患者 ID 列；不填则按列名/取值自动识别疑似 ID 列")
    p.add_argument("--outcome", help="结局列（多个用逗号分隔）：只报告结局本身的分布与事件数")
    p.add_argument("--time", dest="time_col", help="生存结局的随访时间列（配合 --outcome 的事件列）")
    p.add_argument("--cluster", help="聚类列（中心/术者/读片者），逗号分隔；不填则按列名自动识别")
    p.add_argument("--missing-tokens", action="append", default=[],
                   help="追加伪装缺失写法，逗号分隔，可重复：--missing-tokens 拒查,未做")
    p.add_argument("--range", action="append", default=[],
                   help="临床合理范围（只计数）：--range age=0:120 --range bmi=10:60")
    p.add_argument("--max-levels", type=int, default=15, help="每个分类列最多列出的取值数（默认 15）")
    p.add_argument("--report", help="写 Markdown 报告，如 data-profile.md")
    p.add_argument("--json", dest="json_path", help="另存 JSON 结果")
    p.add_argument("--encoding", help="CSV 编码；默认依次尝试 utf-8（含 BOM）、gbk、gb18030")
    p.add_argument("--sep", help="CSV 分隔符；默认自动识别（, 制表符 ; |）")
    args = p.parse_args(argv)

    data_abs = os.path.abspath(args.data)
    for out in (args.report, args.json_path):
        if not out:
            continue
        if os.path.abspath(out) == data_abs:
            raise SystemExit("报告文件不能与数据文件同名：本工具绝不改写数据")
        if os.path.splitext(out)[1].lower() in DATA_EXTS:
            raise SystemExit(f"报告文件 {out} 的扩展名像数据文件；请用 .md / .json，以免覆盖数据")
    tokens = [t for item in args.missing_tokens for t in item.split(",") if t != ""]
    try:
        ranges = _parse_ranges(args.range)
        df, meta = load_table(args.data, sheet=args.sheet, encoding=args.encoding, sep=args.sep)
        profile = profile_dataframe(df, id_col=args.id_col, outcome_col=args.outcome, time_col=args.time_col,
                                    cluster_cols=args.cluster, missing_tokens=tokens, ranges=ranges,
                                    max_levels=args.max_levels, source=meta)
    except (FileNotFoundError, ValueError) as e:
        raise SystemExit(f"[数据体检] {e}")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(render_markdown(profile))
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as fh:
            json.dump(profile, fh, ensure_ascii=False, indent=2)
    for line in summary_lines(profile):
        print(f"[数据体检] {line}")
    written = [x for x in (args.report, args.json_path) if x]
    print("[数据体检] " + (f"报告已写入 {'、'.join(written)}" if written else "加 --report data-profile.md 可保存完整报告"))
    return profile


if __name__ == "__main__":
    main()
