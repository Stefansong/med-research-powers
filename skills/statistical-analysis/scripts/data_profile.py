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
  the outcome's own distribution and event count (--outcome), also per patient when rows
  repeat; suspected personal information columns -- found by column name, by ID-card / phone
  number patterns, or because a column holds one value per patient and almost every patient
  has a different one (a name, record number ...) -- shown by column name and hit count only,
  their values are never printed. A first row that looks like data (numbers, dates, an ID
  card or phone number) is not used as column names. "Rows with no missing value" counts only
  the analysable columns (not all-empty, ID, privacy, remarks or free-text columns).
  Rows are grouped only by the patient ID -- --id, or without it a column named like a patient
  identifier -- so a variable that merely looks like an ID ("arm_id") never groups the outcome
  or a centre. All-different whole numbers are typed ID; a measurement such as a cost can be
  kept numeric with --not-id.

Command line
  python3 data_profile.py data.csv --id patient_id --outcome recurrence --report data-profile.md
  python3 data_profile.py export.xlsx --sheet Sheet2 --outcome death --time months --json profile.json
  python3 data_profile.py data.csv --missing-tokens 拒查,未做 --range age=0:120
  python3 data_profile.py export.csv --skip-rows 1          # a merged title row above the header
  python3 data_profile.py data.csv --not-id 住院费用,platelet  # all-different integers that are measurements

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
    "未检测", "未检查", "未测定", "未测量", "未化验", "未行", "未记录", "未填", "未填写", "未提供",
    "暂无", "暂缺", "待查", "待定", "不明", "不适用", "无记录", "无数据", "失访",
    "missing", "unknown", "unk", "not done", "not available", "not applicable", "n.a.",
    "999", "9999", "-99", "-999",
)
# These may be real values: "无"/"none" = "no, none" (并发症=无) or zero (输血量=无); "-" = negative
# in lab results. They count as missing only in date / ID columns; in numeric and categorical
# columns they are kept and listed for the user to confirm (numeric statistics leave them out).
AMBIGUOUS_TOKENS = frozenset({"无", "none", "-"})
# Tokens pandas.read_csv() already turns into NaN by default (they do not force a text column).
PANDAS_DEFAULT_NA = frozenset({"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan",
                               "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None",
                               "n/a", "nan", "null"})

TYPE_LABELS = {"numeric": "数值", "categorical": "分类", "date": "日期", "text": "文本",
               "id": "ID 样式", "empty": "全部缺失"}

# ASCII digits only: Python's \d also matches full-width "４５", which pandas reads as text.
_NUM = r"[-+]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?"
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
# date of birth (an identifier) -- but not 出生体重 / birth weight
BIRTH_NAME_RE = re.compile(r"出生(?:日期|年月日?|时间)?$|生日|birth[\s_\-.]*date|date[\s_\-.]*of[\s_\-.]*birth"
                           r"|(?:^|[^a-z])dob(?:$|[^a-z])", re.IGNORECASE)
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
# A cluster column name is a cluster word plus, at most, these qualifiers ("site_id", "study
# centre", "hospital name"). Anything else ("hospital_stay", "tumor_site", "surgical_site_infection",
# "physician_diagnosis") is an ordinary variable that merely contains the word.
CLUSTER_QUALIFIERS = frozenset({"id", "no", "code", "name", "num", "study", "trial", "recruiting",
                                "enrolling", "treating", "operating", "attending", "of", "the"})
CLUSTER_NAME_RE = re.compile(
    r"^(?:研究|参与|入组|分)?(?:中心|医院|院区|科室)(?:编号|名称|代码|号|id)?$"
    r"|^(?:术者|主刀(?:医生|医师)?|手术(?:医生|医师)|医生|医师|主治(?:医生|医师)?|"
    r"(?:读片|阅片)(?:者|医生|医师)?|评分者|评估者|观察者)(?:编号|姓名|代码|号|id)?$"
    r"|^(?:检测|测序|实验)?批次(?:号|编号)?$", re.IGNORECASE)
PII_NAME_SUBSTR = ("姓名", "名字", "身份证", "证件号", "手机", "电话", "联系方式", "住址", "地址",
                   "住院号", "病历号", "病案号", "门诊号", "医保号", "邮箱", "病理号", "影像号", "联系人",
                   "phone", "mobile", "address", "email", "idcard", "id_card", "id card")
PII_NAME_TOKENS = frozenset({"tel", "addr", "mrn", "nhs", "ssn"})
# a person's name: "name", "patient name", "pt_name", "full name", "姓名" ... — but not "drug_name",
# "hospital_name" or pandas' "Unnamed: 3"
PERSON_NAME_RE = re.compile(r"^(?:patient|pt|subject|full|first|last|given|family|sur)?[\s_\-.]*name$"
                            r"|^(?:患者|病人|家属)$|^hospital[\s_\-.]*(?:number|no)$", re.IGNORECASE)
ID_CARD_RE = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")
MOBILE_RE = re.compile(r"(?:(?<=\+86)|(?<=\+86 )|(?<=\+86-)|(?<!\d))1[3-9]\d{9}(?!\d)")

EVENT_WORDS = frozenset({"1", "是", "yes", "y", "true", "阳性", "positive", "有", "死亡", "dead",
                         "death", "died", "复发", "recurrence", "event", "发生", "事件"})
DATA_EXTS = (".csv", ".tsv", ".tab", ".txt", ".xlsx", ".xlsm", ".xls", ".sav", ".dta", ".rds")
EXCEL_EXTS = (".xlsx", ".xlsm", ".xls")
# binary formats of statistics packages: reading them as text would give a garbage profile
UNSUPPORTED_EXTS = (".sav", ".zsav", ".por", ".dta", ".rds", ".rdata", ".rda", ".sas7bdat", ".xpt",
                    ".parquet", ".feather", ".pkl", ".pickle", ".mat")
# A column the ID rows can be grouped by (events per patient, patients per centre, one value per
# patient). Without --id only a column named like a patient identifier is trusted with that:
# "arm_id" or "drug_id" typed ID by name must never relate the outcome or a centre to a variable.
PATIENT_ID_NAME_RE = re.compile(
    r"^(?:patient|pt|pat|subject|subj|case|record|person|participant|study|sample)?[\s_\-.]*(?:id|no|number|num)$"
    r"|^(?:pid|mrn|uid|sid|ptid|subjid|usubjid|patid)$"
    r"|住院号|病历号|病案号|门诊号|登记号|入组号|筛选号|研究编号|^id号$|^编号$|^序号$"
    r"|(?:患者|病人|受试者|病例)(?:id|编号|号|序号)", re.IGNORECASE)
# free-text notes: not an analysis variable, so not part of "complete rows"
REMARK_NAME_RE = re.compile(r"备注|注释|附注|说明|(?:^|[^a-z])(?:remarks?|notes?|comments?|memo)(?:$|[^a-z])",
                            re.IGNORECASE)


# ─── small helpers ──────────────────────────────────────────────────────────

def _r(x, sig=6):
    """Round to `sig` significant digits and return a plain float (JSON friendly)."""
    return None if x is None else float(f"{float(x):.{sig}g}")


def _fmt_num(v):
    v = float(v)
    return str(int(v)) if v.is_integer() and abs(v) < 1e15 else f"{v:.6g}"


def _nfkc(s):
    return unicodedata.normalize("NFKC", str(s)).strip()


def _disp(s):
    """A column name as shown on one report / terminal line: a line break (Excel Alt+Enter in a
    header cell) becomes ↵, any other control character a space. The data keep the real name."""
    s = str(s).replace("\r\n", "↵").replace("\n", "↵").replace("\r", "↵")
    return "".join(" " if unicodedata.category(ch) == "Cc" else ch for ch in s)


def _norm_name(s):
    """Name as it can be typed on the command line: ↵ / line breaks / runs of spaces -> one space."""
    return re.sub(r"\s+", " ", str(s).replace("↵", " ")).strip()


def _resolve_cols(label, cols, names):
    """Match --id / --outcome / --range ... names to the real column names (exactly, or with the
    line breaks in a header typed as spaces). Unknown names are an error, never ignored."""
    out = []
    for c in cols:
        if c in names:
            out.append(c)
            continue
        hits = [n for n in names if _norm_name(n) == _norm_name(c)]
        if len(hits) != 1:
            raise ValueError(f"{label} 指定的列 {_disp(c)!r} 不在数据中；可用列：{[_disp(n) for n in names]}")
        out.append(hits[0])
    return list(dict.fromkeys(out))


def _split_cols(x, names):
    """'a,b' -> ['a', 'b'], unless the whole string is itself a column name (it contains a comma)."""
    if isinstance(x, str) and (x in names or any(_norm_name(n) == _norm_name(x) for n in names if "," in n)):
        return [x]
    return _as_list(x)


def _as_list(x):
    if x is None:
        return []
    if isinstance(x, str):
        return [p.strip() for p in x.split(",") if p.strip()]
    return [str(p) for p in x]


def _top(counter, k=5):
    return [v for v, _ in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))[:k]]


def _is_cluster_name(name):
    if _is_pii_name(name):
        return False
    tokens = set(re.findall(r"[a-z]+", name.lower()))
    if tokens & CLUSTER_TOKENS and not (tokens - CLUSTER_TOKENS - CLUSTER_QUALIFIERS):
        return True
    return bool(CLUSTER_NAME_RE.match(name.strip()))


def _is_id_name(name):
    return any(rx.search(name) for rx in ID_NAME_RES) and not _is_cluster_name(name)


def _is_pii_name(name):
    low = name.lower().strip()
    tokens = set(re.findall(r"[a-z]+", low))
    return (any(s in low for s in PII_NAME_SUBSTR) or bool(tokens & PII_NAME_TOKENS)
            or bool(PERSON_NAME_RE.match(low)) or bool(BIRTH_NAME_RE.search(low)))


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


def load_table(path, sheet=None, encoding=None, sep=None, header=None, skip_rows=0):
    """Read CSV / TSV / TXT / XLSX keeping every value exactly as written. Never writes.

    Returns (df, meta). CSV cells are str ('' = empty cell); XLSX cells keep Excel's own
    type (int / float / datetime / str), so numbers typed as text can be detected.
    CSV encodings tried in order: utf-8 (with or without BOM), gbk, gb18030 (UTF-16 when the file
    starts with a UTF-16 BOM). A GBK result that looks like a Western file decoded wrongly
    (cp1252 / latin-1: "µmol" -> "祄ol") is flagged in meta["encoding_warning"].
    header     None = first row is the header unless it looks like data (numbers, dates, an ID
               card or phone number) -- then columns are named 列1, 列2 ... and the row is kept
               as data; True / False force it.
    skip_rows  rows to skip before the header (e.g. a merged title row in a Chinese export).
    Rows that are completely blank are dropped and counted in meta["n_blank_rows"].
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"找不到数据文件 {path}（当前目录 {os.getcwd()}）")
    if skip_rows < 0:
        raise ValueError("--skip-rows 不能是负数")
    ext = os.path.splitext(path)[1].lower()
    if ext in UNSUPPORTED_EXTS:
        raise ValueError(f"暂不支持 {ext} 文件：请在原软件里导出为 .csv 或 .xlsx 再体检"
                         "（导出时保留原始取值，不要让软件替换缺失值或标签）")
    if ext in EXCEL_EXTS and (encoding or sep):
        raise ValueError("--encoding / --sep 只用于 CSV / TSV / TXT 文件；Excel 文件不需要")
    if ext not in EXCEL_EXTS and sheet is not None:
        raise ValueError("--sheet 只用于 .xlsx / .xls 文件；这是文本表格，没有工作表")
    with open(path, "rb") as fh:          # read-only; the file is never opened for writing
        raw = fh.read()
    meta = {"file": os.path.basename(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if ext in EXCEL_EXTS:
        return _load_excel(raw, ext, sheet, meta, header, skip_rows)
    return _load_csv(raw, ext, encoding, sep, meta, header, skip_rows)


def _is_blank(v):
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return isinstance(v, str) and not v.strip()


def _header_looks_like_data(cells):
    """True when the first row looks like a data row rather than column names."""
    vals = [_nfkc(c) for c in cells if not _is_blank(c)]
    if not vals:
        return False
    if any(ID_CARD_RE.search(v) or MOBILE_RE.search(v) for v in vals):
        return True
    datalike = [v for v in vals if PLAIN_NUM_RE.match(v) or _parse_date(v)]
    years = [v for v in datalike if re.fullmatch(r"(?:19|20)[0-9]{2}", v)]   # "2019, 2020" year columns
    return len(datalike) >= 2 and len(datalike) >= 0.5 * len(vals) and len(years) < len(datalike)


def _decide_header(first_row, header, meta):
    """-> True if the first row is the header. Records the decision in meta."""
    if header is None:
        use = not _header_looks_like_data(first_row)
        meta["header_mode"] = "first-row" if use else "auto-none"
    else:
        use = bool(header)
        meta["header_mode"] = "first-row" if use else "none"
    return use


def _load_excel(raw, ext, sheet, meta, header=None, skip_rows=0):
    try:
        book = pd.ExcelFile(io.BytesIO(raw), engine=None if ext == ".xls" else "openpyxl")
    except ImportError:
        if ext == ".xls":
            raise ValueError("读取 .xls 需要 xlrd：pip install xlrd（或在 Excel 里另存为 .xlsx / .csv）")
        raise ValueError("读取 .xlsx 需要 openpyxl：pip install openpyxl")
    except Exception as e:                # openpyxl / xlrd raise many types for a file that is not Excel
        looks = ("文件内容不是 Excel 格式（例如 CSV 改了扩展名）" if not raw.startswith((b"PK", b"\xd0\xcf\x11\xe0"))
                 else "文件可能已损坏或加了密码")
        raise ValueError(f"无法按 {ext} 读取：{looks}。请确认文件格式，或在 Excel 里另存为 .xlsx / .csv"
                         f"（{type(e).__name__}: {str(e)[:120]}）")
    names = [str(n) for n in book.sheet_names]
    if sheet is None:
        target = names[0]
    elif str(sheet) in names:
        target = str(sheet)
    elif str(sheet).isdigit() and int(sheet) < len(names):
        target = names[int(sheet)]
    else:
        raise ValueError(f"找不到工作表 {sheet!r}；可用工作表：{names}")
    grid = book.parse(target, header=None, dtype=object, na_filter=False, skiprows=skip_rows)
    keep = [i for i in range(len(grid)) if not all(_is_blank(v) for v in grid.iloc[i].tolist())]
    if not keep:
        raise ValueError("工作表是空的")
    first = keep[0]
    head = grid.iloc[first].tolist()
    use_header = _decide_header(head, header, meta)
    raw_header = ["" if _is_blank(v) else str(v) for v in head] if use_header else []
    body_idx = [i for i in keep if i > first] if use_header else keep
    n_blank = (len(grid) - first - (1 if use_header else 0)) - len(body_idx)
    df = grid.iloc[body_idx].reset_index(drop=True)
    df.columns = _unique_names(raw_header) if use_header else [f"列{j + 1}" for j in range(grid.shape[1])]
    meta.update(format="xlsx", sheet=target, sheets=names, raw_header=raw_header, n_blank_rows=n_blank,
                skip_rows=skip_rows)
    return df, meta


def _gbk_mojibake(text):
    """-> set of characters that look like a Western (cp1252 / latin-1) file decoded as GBK.

    In such a file an accented byte (µ = B5, ° = B0) pairs with the ASCII letter after it into a
    rare GBK-extension character ("µm" -> 祄, "°C" -> 癈); Chinese text uses the common GB2312
    characters. Suspicious only when the rare ones dominate."""
    rare, common = set(), 0
    for ch in set(text):
        if ord(ch) < 0x80:
            continue
        try:
            b = ch.encode("gbk")
        except UnicodeEncodeError:
            continue
        if len(b) != 2:
            continue
        if 0xA1 <= b[0] <= 0xF7 and b[1] >= 0xA1:
            common += 1
        else:
            rare.add(ch)
    return rare if len(rare) >= 2 and len(rare) > common else set()


def _load_csv(raw, ext, encoding, sep, meta, header=None, skip_rows=0):
    if encoding:
        try:
            codecs.lookup(encoding)
        except LookupError:
            raise ValueError(f"未知的编码名 {encoding!r}；常用：utf-8、gbk、gb18030、utf-16、cp1252（Windows 西文）、latin-1")
        tried = [encoding]
    elif raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        tried = ["utf-16"]                # Excel "Unicode text" export
    else:
        if b"\x00" in raw[:65536]:
            raise ValueError("文件里有二进制内容（NUL 字节），不像文本表格：可能是 Stata / SPSS / Excel 文件改了扩展名；"
                             "如果是 UTF-16 文本，请加 --encoding utf-16")
        tried = ["utf-8-sig", "gbk", "gb18030"]
    text = used = None
    for enc in tried:
        try:
            text, used = raw.decode(enc), enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError(f"无法按 {' / '.join(tried)} 解码该文件；请用 --encoding 指定编码"
                         "（Windows 西文文件可试 --encoding cp1252）")
    label = used
    if used == "utf-8-sig":
        label = "utf-8（带 BOM）" if raw.startswith(codecs.BOM_UTF8) else "utf-8"
    elif used == "utf-16" and not encoding:
        label = "utf-16（带 BOM）"
    suspect = _gbk_mojibake(text) if used in ("gbk", "gb18030") and not encoding else set()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if sep in ("\\t", "tab", "TAB"):
        sep = "\t"
    if sep is None:
        sep = "\t" if ext in (".tsv", ".tab") else _sniff_sep(text)
    if len(sep) != 1:
        raise ValueError("--sep 只能是一个字符，如 , 或 ; 或 \\t")
    # The csv module (not pandas.read_csv) so that no value is converted and a row with extra
    # fields cannot silently turn the first column into the index.
    _raise_csv_limit()                   # a long free-text cell is data, not a parse error
    try:
        reader = csv.reader(io.StringIO(text), delimiter=sep)
        rows, starts, prev = [], [], 0
        for r in reader:
            rows.append(r)
            starts.append(prev + 1)
            prev = reader.line_num
    except csv.Error as e:
        raise ValueError(f"CSV 解析失败（常见原因：引号不配对）：{e}")
    # An opening quote that is never closed makes the csv module read the REST OF THE FILE into
    # one cell without any error; the strict reader notices.
    try:
        for _ in csv.reader(io.StringIO(text), delimiter=sep, strict=True):
            pass
    except csv.Error as e:
        if "unexpected end of data" in str(e):
            line = starts[-1] if starts else 1
            raise ValueError(f"CSV 引号不配对：第 {line} 行附近有一个以 \" 开头、却没有结束引号的单元格，"
                             "后面的所有内容都会被读进这一格。请在原软件里修正后重新导出（或另存为 .xlsx）")
    rows = rows[skip_rows:]
    while rows and not any(x.strip() for x in rows[0]):
        rows.pop(0)
    if not rows:
        raise ValueError("数据文件是空的")
    use_header = _decide_header(rows[0], header, meta)
    raw_header = rows[0] if use_header else []
    rest = rows[1:] if use_header else rows
    body = [r for r in rest if any(x.strip() for x in r)]
    width = len(rows[0])
    longer = [r for r in body if len(r) > width]
    counts = {"longer": len(longer), "shorter": sum(1 for r in body if len(r) < width),
              "longer_with_content": sum(1 for r in longer if any(x.strip() for x in r[width:]))}
    data = [r[:width] + [""] * (width - len(r)) for r in body]
    columns = _unique_names(raw_header) if use_header else [f"列{j + 1}" for j in range(width)]
    df = pd.DataFrame(data, columns=columns, dtype=object)
    meta.update(format="csv", encoding=label, sep=sep, raw_header=raw_header, field_counts=counts,
                n_blank_rows=len(rest) - len(body), skip_rows=skip_rows)
    if suspect:
        try:
            raw.decode("cp1252")
            alt = "cp1252"
        except UnicodeDecodeError:
            alt = "latin-1"
        shown = [_disp(h) for h in raw_header if any(ch in suspect for ch in h)][:3]
        meta["encoding_warning"] = (
            f"按 {used} 解码后出现很多生僻汉字{'（如列名 ' + '、'.join(shown) + '）' if shown else ''}，"
            f"文件可能是 Windows 西文编码：请加 --encoding {alt} 重新体检，确认列名和取值显示正常")
    return df, meta


def _raise_csv_limit():
    limit = 1 << 31
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 2


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
        return ("number", float(v), False) if math.isfinite(float(v)) else ("text", str(v), None)
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
        f = float(t)
        return ("number", f, True) if math.isfinite(f) else ("text", t, None)
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
    """All-unique integers that are a 1..n (or 1001..) sequence or share one length of >= 5 digits.
    A run such as ages 40..69 is not taken for a sequence number."""
    if len(values) < 20 or any(c > 1 for c in counts) or not all(float(v).is_integer() for v in values):
        return False
    ints = [int(v) for v in values]
    lengths = {len(str(abs(i))) for i in ints}
    sequence = max(ints) - min(ints) + 1 == len(ints) and (min(ints) <= 1 or min(ints) >= 1000)
    return sequence or (len(lengths) == 1 and lengths.pop() >= 5)


def _looks_like_code_id(labels, counts):
    """All-unique codes such as P0001 / ZY2024001 (letters + digits)."""
    if len(labels) < 20 or any(c > 1 for c in counts):
        return False
    rx = re.compile(r"^(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9_\-]+$")
    return all(rx.match(s.strip()) for s in labels)


def _profile_column(name, values, vocab, text_numbers_are_issue, max_levels, rng, forced_id,
                    never_id=False):
    n = len(values)
    keys = [_key(v) for v in values]
    counts = collections.Counter(keys)
    date_hint = bool(DATE_NAME_RE.search(name))
    cls = {k: _classify(k, vocab, date_hint) for k in counts}
    hints = []
    if _prefer_month_first(counts, cls):
        hints.append("日期按 月/日/年 解读（该列没有日 > 12 的 日/月/年 写法）")
    kc = collections.Counter()
    for k, c in counts.items():
        kc[cls[k][0]] += c

    # "<60 / ≥60", "≤2cm / 2-5cm / >5cm": pre-binned groups, not detection-limit values. Real
    # censored lab values are a minority next to plain numbers; grouped columns have (almost) none.
    n_plain = kc["number"] + kc["loose"]
    if kc["censored"] and n_plain < 0.2 * (n_plain + kc["censored"]) and \
            sum(1 for k in counts if cls[k][0] in ("censored", "text", "number", "loose")) <= 12:
        for k in counts:
            if cls[k][0] == "censored":
                cls[k] = ("text", cls[k][1], None)
        kc = collections.Counter()
        for k, c in counts.items():
            kc[cls[k][0]] += c
        hints.append("取值像分组区间（如 <60 / ≥60），按分类变量处理，不是检测限截断值")

    # ── type ──
    n_num = kc["number"] + kc["loose"] + kc["censored"]
    n_def = n_num + kc["date"] + kc["text"]
    id_source = None                    # forced (--id) / name / value
    if forced_id or (n_def and not never_id and _is_id_name(name)):
        ctype, id_source = "id", ("forced" if forced_id else "name")
    elif n_def == 0:
        ctype = "categorical" if kc["amb"] else "empty"
    elif kc["date"] >= 0.8 * n_def or (date_hint and kc["date"] >= 0.5 * n_def):
        ctype = "date"
    elif n_num >= 0.8 * n_def:
        num_keys = [k for k in counts if cls[k][0] == "number"]
        ctype = "numeric"
        # a column named like a date holding 5-digit numbers is Excel date serials, not an ID
        if not never_id and not date_hint and kc["loose"] == 0 and kc["censored"] == 0 and _looks_like_int_id(
                [cls[k][1] for k in num_keys], [counts[k] for k in num_keys]):
            ctype, id_source = "id", "value"
            # all different whole numbers may also be a measurement (cost, platelets, a date serial)
            serial = all(20000 <= cls[k][1] <= 80000 for k in num_keys)
            hints.append("按取值判为 ID（全部是互不相同的整数）；如果它是测量值（费用、计数"
                         + ("、Excel 日期序列号" if serial else "") + "），请加 --not-id 重新体检")
    else:
        text_keys = [k for k in counts if cls[k][0] == "text"]
        if not never_id and kc["text"] == n_def and _looks_like_code_id([cls[k][1] for k in text_keys],
                                                      [counts[k] for k in text_keys]):
            ctype, id_source = "id", "value"
        else:
            ctype = "categorical"          # may become "text" below (free text / too many levels)
            if 0.2 <= n_num / n_def < 0.8:
                hints.append(f"约 {round(100 * n_num / n_def)}% 是数字、其余是文字，内容可能混杂")

    # ── missing: blank + tokens (+ ambiguous tokens / numeric codes where they cannot be values) ──
    amb_is_missing = ctype in ("date", "id", "empty")
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

    col = {"name": name, "type": ctype, "type_label": TYPE_LABELS[ctype], "id_source": id_source, "n": n,
           "n_valid": n_valid,
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
    if pii:                                # a phone / ID-card column is no measurement: no --not-id hint
        hints[:] = [h for h in hints if not h.startswith("按取值判为 ID")]
    col["pii"] = ({"by_name": by_name, "id_card_hits": id_hits, "phone_hits": phone_hits,
                   "unique_per_patient": False} if pii else None)

    # ── censored strings ──
    cens = collections.Counter({cls[k][1]: c for k, c in counts.items() if cls[k][0] == "censored"})
    if cens:
        col["censored"] = {"n": sum(cens.values()), "examples": [] if pii else _top(cens)}

    # ── numeric column that would load as text ──
    if ctype == "numeric":
        reasons, examples, units = collections.Counter(), collections.Counter(), collections.Counter()
        for k, c in counts.items():
            kind, val, extra = cls[k]
            if kind == "token" and val not in PANDAS_DEFAULT_NA:
                reasons["伪装缺失（非标准写法）"] += c
            elif kind == "amb":
                reasons["文字“无/none/-”（是 0、阴性还是缺失需确认）"] += c
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


MDY_FORMATS = ("%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y")


def _prefer_month_first(counts, cls):
    """A column written m/d/Y throughout (some day > 12 in the 2nd place, never in the 1st) has its
    ambiguous dates (03/04/2024) re-read as m/d/Y. Updates cls in place; True if it did."""
    dm = md = 0
    ambiguous = []
    for k in counts:
        if k[0] != "s" or cls[k][0] != "date":
            continue
        m = DMY_RE.match(_nfkc(k[1]))
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2))
        if a > 12:
            dm += 1
        elif b > 12:
            md += 1
        else:
            ambiguous.append(k)
    if not (md and not dm and ambiguous):
        return False
    for k in ambiguous:
        t = _nfkc(k[1])
        for fmt in MDY_FORMATS:
            try:
                cls[k] = ("date", _dt.datetime.strptime(t, fmt), fmt)
                break
            except ValueError:
                continue
    return True


def _unique_per_patient(col, keys, missing_by_key, id_labels):
    """True when a column holds one value per patient and (almost) every patient has a different
    value -- a name, record number or similar, even when its column name gives nothing away."""
    ctype = col["type"]
    vals = [None if missing_by_key[k] else _label(k).strip() for k in keys]
    if ctype == "numeric":
        present = {v for v in vals if v is not None}
        if not present or not all(re.fullmatch(r"[0-9]+", v) for v in present) \
                or len({len(v) for v in present}) != 1 or len(next(iter(present))) < 5:
            return False                      # only same-length whole numbers of 5+ digits
    elif ctype not in ("categorical", "text", "id"):
        return False
    if id_labels is None:
        present = [v for v in vals if v is not None]
        return len(present) >= 5 and len(set(present)) >= 0.9 * len(present)
    per = collections.defaultdict(set)
    for pid, v in zip(id_labels, vals):
        if pid is not None and v is not None:
            per[pid].add(v)
    if len(per) < 5:
        return False
    constant = sum(1 for vs in per.values() if len(vs) == 1)
    distinct = len({v for vs in per.values() for v in vs})
    return constant >= 0.95 * len(per) and distinct >= 0.8 * len(per)


def _redact(col):
    """Keep counts, drop every value of a column that turned out to identify patients."""
    col["pii"] = dict(col["pii"] or {"by_name": False, "id_card_hits": 0, "phone_hits": 0},
                      unique_per_patient=True)
    col["categorical"] = None
    if col.get("numeric") is not None:
        col["numeric"] = None
    if col.get("censored"):
        col["censored"]["examples"] = []
    if col.get("numeric_as_text"):
        col["numeric_as_text"]["examples"], col["numeric_as_text"]["units"] = [], {}
    if col.get("date"):
        col["date"]["unparseable_examples"] = []
        col["date"].pop("min", None)
        col["date"].pop("max", None)
    col["hints"] = [h for h in col["hints"] if not h.startswith("只有 ")]


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
    if all(PLAIN_NUM_RE.match(x.strip()) for x in labs):
        # the label as written ("1", "1.0", "01"), so it can index the level counts
        ones = [x for x in labs if float(x) == 1.0]
        return ones[0] if {float(x) for x in labs} == {0.0, 1.0} and len(ones) == 1 else None
    hits = [x for x in labs if _nfkc(x).lower() in EVENT_WORDS]
    return hits[0] if len(hits) == 1 else None


def _outcome_summary(col, time_col, labels=None, id_labels=None):
    """Only the outcome's OWN distribution. Nothing here looks at any other variable.

    With a patient ID whose rows repeat, events are also counted per patient: the number of
    patients with at least one event row is what limits the number of predictors, not the
    number of rows (the ID only says which rows belong together; it is not a predictor)."""
    out = {"column": col["name"], "n_rows": col["n"], "n_missing": col["n_missing_total"],
           "n_valid": col["n_valid"], "kind": "empty", "levels": None, "event_label": None,
           "events": None, "non_events": None, "minority_count": None, "numeric": None,
           "time": None, "per_patient": None, "notes": []}
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
            if labels is not None and id_labels is not None:
                out["per_patient"] = _events_per_patient(labels, id_labels, ev)
        else:
            out["notes"].append("无法从编码判断哪一类是事件，请确认后按那一类的例数计事件数")
    elif cat and cat["n_levels"] == 1:
        out.update(kind="constant", levels=cat["levels"])
        out["notes"].append("结局只有一个取值")
    elif cat and cat["n_levels"] > 2 and col["type"] != "numeric":
        out.update(kind="categorical", levels=cat["levels"])
        out["notes"].append(f"多分类结局（{cat['n_levels']} 类）")
    elif col.get("numeric"):
        s = col["numeric"]
        out.update(kind="numeric", numeric={k: s.get(k) for k in ("n", "min", "median", "max", "mean", "sd")})
        if cat:                               # 3-10 whole values: a count, a score or a coded category
            out["levels"] = cat["levels"]
            out["notes"].append(f"数值结局只有 {cat['n_levels']} 个不同取值：是计数、评分还是分类编码，请按数据字典确认")
    if col["type"] == "text":
        out["kind"] = "text"
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


def _events_per_patient(labels, id_labels, event_label):
    """Patients with >= 1 event row / without; patients whose rows disagree on the outcome."""
    per = collections.defaultdict(set)
    for pid, lab in zip(id_labels, labels):
        if pid is not None and lab is not None:
            per[pid].add(lab == str(event_label).strip())
    if not per or all(len(v) == 1 for v in per.values()) and len(per) == sum(1 for p in id_labels if p is not None):
        return None                                   # one row per patient: rows = patients
    with_event = sum(1 for v in per.values() if True in v)
    return {"n_patients": len(per), "patients_with_event": with_event,
            "patients_without_event": len(per) - with_event,
            "n_patients_mixed": sum(1 for v in per.values() if len(v) > 1)}


def _header_issues(source, names):
    raw_header = source.get("raw_header")
    header = [str(h) for h in (raw_header if raw_header else names)]
    issues = []
    if source.get("encoding_warning"):
        issues.append(source["encoding_warning"])
    if source.get("header_mode") == "auto-none":
        issues.append("第一行看起来是数据（数字、日期、身份证号或手机号样式），不是列名：已按没有表头处理，"
                      "列名记为 列1、列2……；如果第一行确实是表头，请加 --header 重新体检")
    if source.get("n_blank_rows"):
        issues.append(f"{source['n_blank_rows']} 行完全空白（常见于导出时末尾的空行），已忽略")
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
        issues.append("列名重复：" + "、".join(_disp(h) for h in dups))
    broken = [h for h in header if "\n" in h or "\r" in h]
    if broken:
        issues.append("列名里有换行（Excel 单元格内换行）：" + "、".join(_disp(h) for h in broken[:10])
                      + "——报告里显示为 ↵；在 --id / --outcome 等参数里用空格代替换行即可")
    empty = sum(1 for h in header if not h.strip() or h.startswith("Unnamed:")) if raw_header or \
        source.get("header_mode") in (None, "first-row") else 0
    if empty:
        issues.append(f"{empty} 个列没有列名（表头可能不在第一行，或有合并单元格）")
    spaced = [h for h in header if h.strip() and h != h.strip()]
    if spaced:
        issues.append("列名首尾有空格：" + "、".join(repr(h) for h in spaced[:10]))
    return issues


def _is_patient_id(col):
    """Can an auto-detected ID column be trusted to group rows by patient? Only when it is named
    like a patient identifier (and has at least 5 values), or when every value is different
    (then no grouping can reveal anything)."""
    if col.get("id_source") == "value":
        return True
    return bool(PATIENT_ID_NAME_RE.search(col["name"].strip())) and col.get("n_distinct", 0) >= 5


def _complete_row_exclusion(col):
    """Why a column does not count for "rows with no missing value" (None = it counts)."""
    if col["type"] == "empty":
        return "全列缺失"
    if col["type"] == "id":
        return "ID 列"
    if col["pii"]:
        return "疑似隐私字段"
    if REMARK_NAME_RE.search(col["name"]):
        return "备注列"
    if col["type"] == "text":
        return "自由文本"
    return None


def _check_ranges(ranges, names):
    out = {}
    for c, bounds in ranges.items():
        nm = _resolve_cols("--range", [c], names)[0]
        lo, hi = (float(b) for b in bounds)
        if not (math.isfinite(lo) and math.isfinite(hi)):
            raise ValueError(f"--range {_disp(c)} 的上下限必须是有限的数字")
        if lo > hi:
            raise ValueError(f"--range {_disp(c)}={_fmt_num(lo)}:{_fmt_num(hi)} 下限大于上限")
        out[nm] = (lo, hi)
    return out


def profile_dataframe(df, id_col=None, outcome_col=None, time_col=None, cluster_cols=None,
                      missing_tokens=None, ranges=None, max_levels=15, source=None, not_id_cols=None):
    """Structure / quality profile of one table -> JSON-serialisable dict.

    id_col       patient ID column (None: detect ID-like columns by name / values)
    outcome_col  outcome column(s): ONLY their own distribution and event count are reported
    time_col     follow-up time for a survival outcome (described on its own)
    cluster_cols centre / surgeon / reader columns (None: detect by name)
    missing_tokens extra disguised-missing spellings added to DEFAULT_MISSING_TOKENS
    ranges       {'age': (0, 120)} plausible ranges; values outside are only counted
    source       meta dict from load_table() (file name, sha256, encoding, sheet ...)
    not_id_cols  columns that are measurements, never identifiers (all-different whole numbers
                 such as a cost would otherwise be typed ID and lose their distribution)
    Column names may be given with the line breaks of a header cell typed as spaces.
    Nothing in this function relates one variable to another or to the outcome: rows are grouped
    only by the patient ID (--id, or an auto-detected column named like a patient identifier).
    """
    source = dict(source or {})
    vocab = _Vocab(_as_list(missing_tokens) if isinstance(missing_tokens, str) else (missing_tokens or ()))
    names = _unique_names([str(c) for c in df.columns])
    ids, outs, times, clus, not_ids = (
        _resolve_cols(label, _split_cols(x, names), names)
        for label, x in (("--id", id_col), ("--outcome", outcome_col), ("--time", time_col),
                         ("--cluster", cluster_cols), ("--not-id", not_id_cols)))
    ranges = _check_ranges(ranges or {}, names)
    if len(ids) > 1:
        raise ValueError("--id 只能指定一个列")
    if times and not outs:
        raise ValueError("--time 需要与 --outcome（事件列）一起使用")
    roles = {}
    for label, cols in (("--id", ids), ("--outcome", outs), ("--time", times), ("--cluster", clus)):
        for c in cols:
            if c in roles:
                raise ValueError(f"列 {_disp(c)!r} 不能同时用于 {roles[c]} 和 {label}")
            roles[c] = label
    if set(ids) & set(not_ids):
        raise ValueError(f"列 {_disp(ids[0])!r} 不能同时用于 --id 和 --not-id")
    if max_levels < 0:
        raise ValueError("--max-levels 不能是负数")
    text_numbers_are_issue = source.get("format") != "csv"   # in a CSV every number is text

    n_rows = len(df)
    columns, keys_by, miss_by = [], {}, {}
    for j, name in enumerate(names):
        col, keys, missing_by_key = _profile_column(
            name, df.iloc[:, j].tolist(), vocab, text_numbers_are_issue, max_levels,
            ranges.get(name), forced_id=bool(ids) and name == ids[0],
            # an outcome / follow-up time / declared measurement is never an ID
            never_id=name in outs or name in times or name in not_ids)
        columns.append(col)
        keys_by[name], miss_by[name] = keys, missing_by_key
    by_name = {c["name"]: c for c in columns}

    row_tuples = collections.Counter(zip(*[keys_by[nm] for nm in names])) if names else collections.Counter()
    n_dup_rows = sum(c - 1 for c in row_tuples.values() if c > 1)

    # ── repeated IDs and clusters (structure only) ──
    id_names = ids or [c["name"] for c in columns if c["type"] == "id" and not _is_cluster_name(c["name"])][:5]
    # the one column rows may be grouped by: --id, or an auto-detected column that is a patient ID
    main_id = ids[0] if ids else next((nm for nm in id_names if _is_patient_id(by_name[nm])), None)
    id_structure = [dict(_id_structure(nm, _row_labels(keys_by[nm], miss_by[nm])), as_patient_id=nm == main_id)
                    for nm in id_names]
    main_id_labels = _row_labels(keys_by[main_id], miss_by[main_id]) if main_id else None

    # ── identifiers the column name does not give away: one value per patient, all different ──
    for c in columns:
        if c["name"] not in id_names and c["name"] not in outs and c["name"] not in times and \
                c["name"] not in not_ids and \
                _unique_per_patient(c, keys_by[c["name"]], miss_by[c["name"]], main_id_labels):
            _redact(c)

    # ── complete rows: over the analysable columns only (see _complete_row_exclusion) ──
    excluded = {c["name"]: why for c in columns for why in [_complete_row_exclusion(c)] if why}
    any_missing = np.zeros(n_rows, dtype=bool)
    for nm in names:
        if nm not in excluded:
            any_missing |= np.fromiter((miss_by[nm][k] for k in keys_by[nm]), dtype=bool, count=n_rows)
    if clus:
        cluster_names = clus
    else:
        cluster_names = []
        for c in columns:
            if c["name"] in id_names or c["name"] in outs or c["name"] in times or c["pii"] \
                    or not _is_cluster_name(c["name"]):
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
        outcomes.append(_outcome_summary(by_name[nm], tcol, _row_labels(keys_by[nm], miss_by[nm]),
                                         main_id_labels if nm != main_id else None))

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
        "complete_rows_basis": {"n_columns": len(names) - len(excluded), "excluded": excluded},
        "range_notes": [f"--range {_disp(nm)} 没有用上：该列识别为{by_name[nm]['type_label']}，不是数值列"
                        for nm in ranges if by_name[nm]["type"] != "numeric"],
        "columns": columns, "id_structure": id_structure, "clusters": clusters, "outcomes": outcomes,
        "privacy": [{"column": c["name"], **c["pii"]} for c in columns if c["pii"]],
        "missing_tokens": {"default": [t for t in DEFAULT_MISSING_TOKENS if t], "added": vocab.extra,
                           "ambiguous": sorted(vocab.ambiguous)},
    }
    profile["problems"] = _problems(profile)
    return _json_safe(profile)


def _json_safe(x):
    """NaN / Infinity are not valid JSON: turn them into null."""
    if isinstance(x, dict):
        return {k: _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _problems(p):
    """Plain-language list of the issues that need a decision in the SAP / cleaning code."""
    out = list(p["header_issues"])
    # Privacy columns keep their quality checks: every message below shows counts, vocabulary
    # tokens or column names only, never a value (their levels / ranges / examples were dropped).
    cols = p["columns"]
    if p["n_duplicate_rows"]:
        out.append(f"完全重复的行 {p['n_duplicate_rows']} 行（可能是导出重复）")
    dis = []
    for c in cols:
        parts = [f"{t or '空白'}×{n}" for t, n in c["disguised_missing"].items()]
        parts += [f"{t}×{n}" for t, n in c["missing_codes"].items()]
        if parts:
            dis.append(f"{_disp(c['name'])}（{'、'.join(parts[:6])}）")
    if dis:
        out.append("伪装缺失：" + "；".join(dis))
    kept = [f"{_disp(c['name'])}（{'、'.join(f'{t}×{n}' for t, n in c['possible_missing_kept'].items())}）"
            for c in cols if c["possible_missing_kept"]]
    if kept:
        out.append("可能表示缺失、也可能是真实取值（按取值保留，请确认）：" + "；".join(kept))
    high = [f"{_disp(c['name'])} {c['pct_missing_total']}%" for c in cols
            if c["pct_missing_total"] >= 20 and c["type"] != "empty"]
    if high:
        out.append("缺失 ≥20%（含伪装缺失）：" + "、".join(high))
    empty = [_disp(c["name"]) for c in cols if c["type"] == "empty"]
    if empty:
        out.append("整列缺失：" + "、".join(empty))
    cens = [f"{_disp(c['name'])}（{c['censored']['n']} 个）" for c in cols if c.get("censored")]
    if cens:
        out.append("截断值（如 <0.1、>1000）：" + "、".join(cens))
    nat = [_disp(c["name"]) for c in cols if c.get("numeric_as_text")]
    if nat:
        out.append("数值列直接读入会变成文本：" + "、".join(nat))
    bad_dates = [f"{_disp(c['name'])}（{c['date']['n_unparseable']} 个）" for c in cols
                 if c.get("date") and c["date"]["n_unparseable"]]
    if bad_dates:
        out.append("无法解析的日期：" + "、".join(bad_dates))
    inc = [_disp(c["name"]) for c in cols if (c.get("categorical") or {}).get("inconsistent")]
    if inc:
        out.append("分类取值只差大小写/空格：" + "、".join(inc))
    by_value = [_disp(c["name"]) for c in cols if c.get("id_source") == "value" and not c["pii"]
                and any(h.startswith("按取值判为 ID") for h in c["hints"])]
    if by_value:
        out.append("按取值判为 ID 的整数列：" + "、".join(by_value) + "——如果其中有测量值（费用、计数、日期序列号），"
                   "加 --not-id " + ",".join(by_value) + " 重新体检，才会有分布统计")
    for s in p["id_structure"]:
        if s["n_ids_multi"] and not s.get("as_patient_id", True):
            out.append(f"{_disp(s['column'])}：列名像 ID、但不像患者 ID（{s['n_ids']} 个取值，每个最多 {s['max_rows_per_id']} 行），"
                       "没有用它按患者汇总；如果它就是患者 ID，请用 --id 指定")
        elif s["n_ids_multi"]:
            out.append(f"{_disp(s['column'])}：{s['n_ids_multi']} 个 ID 出现多行（每个 ID 最多 {s['max_rows_per_id']} 行）"
                       "——这些行不是相互独立的观测")
    for s in p["clusters"]:
        if s["n_clusters"] > 1:
            out.append(f"{_disp(s['column'])}：{s['n_clusters']} 个聚类单位，每个 {s['rows_per_cluster'].get('min')}–"
                       f"{s['rows_per_cluster'].get('max')} 行")
    out += p.get("range_notes", [])
    if p["privacy"]:
        out.append("疑似隐私字段（不显示取值）：" + "、".join(
            _disp(x["column"]) + ("（每名患者一个、几乎各不相同的取值）" if x.get("unique_per_patient") and not x["by_name"] else "")
            for x in p["privacy"]))
    return out


# ─── Markdown report ────────────────────────────────────────────────────────

def _cell(s, limit=40):
    s = _disp(s).replace("`", "'").replace("|", "¦")
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


def _basis_text(basis):
    if not basis or not basis.get("excluded"):
        return ""
    names = "、".join(_disp(n) for n in list(basis["excluded"])[:8]) + ("等" if len(basis["excluded"]) > 8 else "")
    return (f"——只看 {basis['n_columns']} 个可分析列，不计全列缺失、ID、疑似隐私、备注和自由文本列"
            f"（{names}）")


def render_markdown(p):
    """Render a profile dict (from profile_dataframe) as the data-profile.md report."""
    src = p.get("source", {})
    cols = p["columns"]
    title = _disp(src.get("file") or "数据")
    L = [f"# 数据体检报告：{title}", "", f"> {p['statement']}。", ""]
    info = []
    if src.get("file"):
        extra = [f"{src.get('bytes', 0)} 字节", f"sha256 `{src.get('sha256', '')}`"]
        if src.get("encoding"):
            extra.append(f"编码 {src['encoding']}")
        if src.get("sep"):
            extra.append("分隔符 " + ("制表符" if src["sep"] == "\t" else f"`{src['sep']}`"))
        info.append(f"- 文件：{title}（{'；'.join(extra)}）")
    if src.get("sheet"):
        info.append(f"- 工作表：{src['sheet']}（共 {len(src.get('sheets', []))} 个：{'、'.join(src.get('sheets', []))}）")
    tc = "、".join(f"{k} {v}" for k, v in p["type_counts"].items() if v)
    info += [f"- 体检日期：{p['generated']}；工具：data_profile.py（只读，没有修改或另存数据）",
             f"- 规模：{p['n_rows']} 行 × {p['n_cols']} 列；列类型：{tc}",
             f"- 完全重复的行：{p['n_duplicate_rows']}；没有任何缺失的行：{p['n_complete_rows']}"
             + (f"（{round(100 * p['n_complete_rows'] / p['n_rows'], 1)}%）" if p["n_rows"] else "")
             + _basis_text(p.get("complete_rows_basis"))]
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
    L += ["", "说明：`无`、`none`、`-` 在日期/ID 列按缺失计；在数值列和分类列可能表示\"没有\"、0 或\"阴性\"，"
          "按取值保留并列在最后一列（数值列的分布统计不含它们）——是 0、阴性还是缺失，请按数据字典确认。"
          "`999`、`9999`、`-99`、`-999` 只在数值列按缺失码计，如果它在该列是真实数值，请在清洗时不要当缺失。"]

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
            if not s.get("as_patient_id", True) and s["n_ids_multi"]:
                L.append("  - 列名不像患者 ID，没有用它按患者汇总（事件数、聚类里的患者数）；"
                         "如果它就是患者 ID，请用 `--id` 指定后重新体检")
            elif s["n_ids_multi"]:
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
            pp = o.get("per_patient")
            if o["events"] is not None and pp:
                L.append(f"  - 事件（{_code(o['event_label'])}）{o['events']} 行、非事件 {o['non_events']} 行——"
                         f"同一患者有多行：按患者计，{pp['n_patients']} 名患者中 {pp['patients_with_event']} 名"
                         f"至少有一个事件行，{pp['patients_without_event']} 名没有")
                if pp["n_patients_mixed"]:
                    L.append(f"  - {pp['n_patients_mixed']} 名患者的多行结局不一致：结局是按行（随访/病灶）记录的，"
                             "分析单位（患者还是行）要在 SAP 里写明")
                L.append(f"  - 可纳入多少个预测变量取决于按患者计的较少一类（"
                         f"{min(pp['patients_with_event'], pp['patients_without_event'])} 名患者），不是行数")
            elif o["events"] is not None:
                L.append(f"  - 事件（{_code(o['event_label'])}）{o['events']} 例，非事件 {o['non_events']} 例")
            if o["minority_count"] is not None and not pp:
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
        L.append(_table(["列", "列名像隐私字段", "18 位身份证号样式", "11 位手机号样式", "每名患者一个、几乎各不相同"], [
            [_code(x["column"]), "是" if x["by_name"] else "", x["id_card_hits"] or "", x["phone_hits"] or "",
             "是" if x.get("unique_per_patient") else ""]
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
    head = f"{_disp(src.get('file', '数据'))}：{p['n_rows']} 行 × {p['n_cols']} 列"
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
        s = f"结局 {_disp(o['column'])}：有效 {o['n_valid']}/{o['n_rows']}"
        if o["events"] is not None and o.get("per_patient"):
            pp = o["per_patient"]
            s += (f"，事件（={_disp(o['event_label'])}）{o['events']} 行 / {pp['patients_with_event']} 名患者"
                  f"（共 {pp['n_patients']} 名）")
        elif o["events"] is not None:
            s += f"，事件（={_disp(o['event_label'])}）{o['events']} 例"
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
            if not col.strip():
                raise ValueError(f"--range 缺少列名：{part!r}")
    return out


def _is_earlier_output(path, kind):
    """True for an empty file or one this tool wrote before (so it may be overwritten)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(4096).decode("utf-8", "replace").lstrip("\ufeff")
    except OSError:
        return False
    if not head.strip():
        return True
    return head.startswith("# 数据体检报告") if kind == "report" else '"tool": "data_profile.py"' in head


def _check_output_paths(data, outputs):
    """Refuse any --report / --json path that could overwrite the data or some other file."""
    data_real = os.path.realpath(data)
    seen = {}
    for flag, kind, out in outputs:
        if not out:
            continue
        real = os.path.realpath(out)
        # realpath: a report path that is a symlink to the data file must not overwrite it
        same = real == data_real or real.lower() == data_real.lower()
        try:
            same = same or (os.path.exists(out) and os.path.exists(data) and os.path.samefile(out, data))
        except OSError:
            pass
        if same:
            raise SystemExit("[数据体检] 报告文件不能与数据文件同名：本工具绝不改写数据")
        if os.path.splitext(out)[1].lower() in DATA_EXTS + UNSUPPORTED_EXTS:
            raise SystemExit(f"[数据体检] 报告文件 {out} 的扩展名像数据文件；请用 .md / .json，以免覆盖数据")
        if real.lower() in seen:                   # also the same file on a case-insensitive disk
            raise SystemExit(f"[数据体检] {flag} 和 {seen[real.lower()]} 是同一个文件；请分别指定")
        seen[real.lower()] = flag
        parent = os.path.dirname(os.path.abspath(out))
        if not os.path.isdir(parent):
            raise SystemExit(f"[数据体检] {flag} 的目录不存在：{parent}")
        if os.path.isdir(out):
            raise SystemExit(f"[数据体检] {flag} {out} 是一个目录")
        if os.path.exists(out) and not _is_earlier_output(out, kind):
            raise SystemExit(f"[数据体检] {out} 已存在，且不是之前的数据体检{'报告' if kind == 'report' else ' JSON'}："
                             "为免覆盖，请换一个文件名或先移走它")


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
    p.add_argument("--not-id", dest="not_id",
                   help="这些列是测量值、不是 ID（逗号分隔），如全部互不相同的住院费用、血小板计数")
    p.add_argument("--outcome", help="结局列（多个用逗号分隔）：只报告结局本身的分布与事件数")
    p.add_argument("--time", dest="time_col", help="生存结局的随访时间列（配合 --outcome 的事件列）")
    p.add_argument("--cluster", help="聚类列（中心/术者/读片者），逗号分隔；不填则按列名自动识别")
    p.add_argument("--missing-tokens", action="append", default=[],
                   help="追加伪装缺失写法，逗号分隔，可重复：--missing-tokens 拒查,未做")
    p.add_argument("--range", action="append", default=[],
                   help="临床合理范围（只计数）：--range age=0:120 --range bmi=10:60")
    p.add_argument("--max-levels", type=int, default=15, help="每个分类列最多列出的取值数（默认 15，≥0）")
    p.add_argument("--report", help="写 Markdown 报告，如 data-profile.md")
    p.add_argument("--json", dest="json_path", help="另存 JSON 结果")
    p.add_argument("--encoding", help="CSV 编码；默认依次尝试 utf-8（含 BOM）、gbk、gb18030")
    p.add_argument("--sep", help="CSV 分隔符；默认自动识别（, 制表符 ; |）")
    hdr = p.add_mutually_exclusive_group()
    hdr.add_argument("--header", dest="header", action="store_const", const=True, default=None,
                     help="第一行一定是列名（默认自动判断：第一行像数据时按没有表头处理）")
    hdr.add_argument("--no-header", dest="header", action="store_const", const=False,
                     help="文件没有表头：列名记为 列1、列2……")
    p.add_argument("--skip-rows", type=int, default=0,
                   help="表头前要跳过的行数（如导出文件第一行是合并单元格的标题）")
    args = p.parse_args(argv)
    if args.max_levels < 0:
        p.error("--max-levels 不能是负数")

    _check_output_paths(args.data, (("--report", "report", args.report), ("--json", "json", args.json_path)))
    tokens = [t for item in args.missing_tokens for t in item.split(",") if t != ""]
    try:
        ranges = _parse_ranges(args.range)
        df, meta = load_table(args.data, sheet=args.sheet, encoding=args.encoding, sep=args.sep,
                              header=args.header, skip_rows=args.skip_rows)
    except (FileNotFoundError, ValueError) as e:
        raise SystemExit(f"[数据体检] {e}")
    except Exception as e:                   # an unreadable file is an error message, not a traceback
        raise SystemExit(f"[数据体检] 读取 {args.data} 失败（{type(e).__name__}: {e}）")
    try:
        profile = profile_dataframe(df, id_col=args.id_col, outcome_col=args.outcome, time_col=args.time_col,
                                    cluster_cols=args.cluster, missing_tokens=tokens, ranges=ranges,
                                    max_levels=args.max_levels, source=meta, not_id_cols=args.not_id)
    except ValueError as e:
        raise SystemExit(f"[数据体检] {e}")

    try:
        if args.report:
            with open(args.report, "w", encoding="utf-8") as fh:
                fh.write(render_markdown(profile))
        if args.json_path:
            with open(args.json_path, "w", encoding="utf-8") as fh:
                json.dump(profile, fh, ensure_ascii=False, indent=2, allow_nan=False)
    except OSError as e:
        raise SystemExit(f"[数据体检] 无法写入报告：{e}")
    for line in summary_lines(profile):
        print(f"[数据体检] {line}")
    written = [x for x in (args.report, args.json_path) if x]
    print("[数据体检] " + (f"报告已写入 {'、'.join(written)}" if written else "加 --report data-profile.md 可保存完整报告"))
    return profile


if __name__ == "__main__":
    main()
