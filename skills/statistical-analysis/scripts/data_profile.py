#!/usr/bin/env python3
"""
data_profile.py -- read-only data check-up ("数据体检") of one table (CSV / TSV / XLSX).

It describes the STRUCTURE and QUALITY of the data and nothing else:
  * it never modifies, cleans, recodes or re-saves the data file;
  * it never computes a relation between two variables, or between any variable and
    the outcome (no cross-tabs, no group comparisons, no correlations, no models).

What it reports
  rows / columns; the inferred type of every column (numeric / categorical / date / text /
  ID-like); disguised missing values ("NA", "/", "未查", "未送检", "未檢", "999", ...) per column -- a
  number added with --missing-tokens counts in every column type where it can be a code (words,
  or away from the range of the column's other numbers); one of the two codes of a 0/1 column, a
  value inside the range (a score of 9 among 0-29) or right next to it (0 next to counts 1-3) is
  reported, not applied, and "col=code" applies it to that one column; censored strings ("<0.1",
  ">1000", "ND" in a lab column -- in a column of ages or counts "ND" is missing), told apart from
  pre-binned groups by their values: groups cover both sides of a cut point ("0 / <20 / ≥20"), come
  with ranges ("2-5cm") or are counts ("0 / 1 / ≥2"), a detection limit is one open end next to
  measured values, however many fall below it, and two limits with results between them are a lab
  censored at both ends; numbers that would load as text -- units are read by their parts (g/L,
  mm Hg, ×10^9 /L, years old, 次/分 ...), spellings of one unit (×10⁹/L, x10^9/L, 10*9/L; IU/ml,
  IU/mL) are one unit, a lab flag after the number or the unit ("5.6↑", "7.8 H", "95 g/L L") is
  counted and stripped (also before the unit or the number: "9.6↑ mmol/L", "H 9.6", "9.6(偏高)"), a
  power of ten that multiplies the number is applied ("5.29×10^5 IU/mL" is 529000 IU/mL; "×10^9/L" is a
  unit), "约12.3" / "~12.3" / "5.2?" / "12 345" are numbers -- so are approximate values ("约500ml", "500ml左右",
  "approx. 5 mL", "12余年", "20多"; counted as written, with a problem line), flag words ("5.6 High", "(Low)",
  "14.8 A", "!H", "(危急值)", "（异常）", "阳性 12") and decimal commas or thousands separators before a unit
  ("5,4 mmol/L", "12.345,67", "12,345.67元"; in a column of decimal commas "1,125" is 1.125) --, and a
  capital L / H is litres / hours only when it is on every value or next to ml / min values ten times
  larger -- two measurements in one
  cell (120/80, 120-80, 3.5×2.1cm, 3.5 cm x 2.1 cm; 20/40 or 4/10 get a "what is it" hint, not a
  blood-pressure one) are named as such, and words that are none of these are listed as tokens
  (digits masked); dates and date-times in common export spellings (also "1/5/2022 0:00", "Jan-22",
  "Wed Jan 16 2019", "2022-01-01T00:00:00Z", yyyymmdd / yyyymm whole numbers, yyyymmddHHMMSS under a
  date-like name, "19-01-16" read year first when the first part takes few values, a few impossible
  ones such as 20230230 counted as unreadable), placeholder dates (1900-01-01), time-of-day columns
  and unreadable date cells; missing % including disguised missing; numeric range (exact min / max), percentiles, Z>3
  and IQR×1.5 counts (counted, never removed); categorical levels and spellings that differ only in
  case / spaces; total rows (合计 / 合计： / Total: / 平均值 / 均值±标准差; a word many rows hold, such as
  thyroidectomy Total / Subtotal, is a category), footer rows (注：…, 制表人：…, 打印时间：…) and a units
  row under the header that would be profiled as patients; repeated IDs and the column the rows are grouped by; cluster structure (centre,
  surgeon ...); the outcome's own distribution and event count (--outcome), counted per patient
  when rows repeat.

What it never prints (privacy)
  * Text values without a patient unit: a category level, a spelling variant, a word in a number
    column or a note typed into a date cell is printed only when patients can be told apart --
    --id names the patient column; or exactly one column is the automatic patient key -- its name
    clearly names the patient (patient_id, pid, subject_id, case_id, 患者编号, 住院号, 病案号, MRN,
    Hospital Number ...; never a per-row number such as 序号, No., visit_id, 检验号) with no visit /
    time / sample word in it (visit, 随访, 第, 次, 天, day, week, POD, FU, sample, 标本, admission, 入院
    ...), its values repeat (some value on 2+ rows) with 10+ different values, and they are no visit /
    ordinal labels (第1次, 随访一, V1, V-1, visit_1, FU1, D1, POD1, wk4, baseline, Roman I-XII, single
    letters, small integer runs 0..k); how many rows each value has is never used. Two or more such
    columns: none is used and one problem line names them for --id. Every value of the key is one
    patient. Or --rows-are-patients says every row is a different patient. Without any
    of these no text value of any column is printed -- only the number of values and the shares
    of the commonest and the rarest -- and one line says to pass --id or --rows-are-patients.
  * Small cells: with a patient unit, a text value is printed only when at least 5 patients hold
    it and it is shaped like no identifier (no strong-shaped personal name; no weaker name written in
    another script than the column's other values, as "Testa Personne" among 死亡 / 存活; no record
    number among values that are none); the others are only counted ("另有 N 个低频取值未显示"). An
    outcome level follows the same rule, and a plain code (0 / 1, 是 / 否, 死亡 / 存活 ...) is printed
    whatever its count; the others are shown as placeholders with their counts (event counts stay right).
  * Numbers and dates are measurements: their distribution is shown and they are never hidden for
    being unique -- but a whole number of 7+ digits, however it is written (13800131005, 13800131005.00,
    1.38001E+10, 13,800,131,005; a phone, ID card or record number typed into a numeric column, the
    outcome or --time), is never printed: the statistics it could show are hidden and the problem list
    says why. A date column whose name names no event (d1, date1, 日期1) shows an end of its range that
    lies 18+ years back as the year only (it may be a date of birth).
  * Privacy columns -- found by column name (also written with spaces or full-width letters,
    and date-of-birth names in other languages: 生辰, bdate, DtNasc, data di nascita, date de naissance,
    fecha_nac, data de nascimento, fødselsdato, 생년월일, дата рождения ... -- not poids / lieu / rang de
    naissance, peso al nacimiento or 出生(kg)), by ID-card / phone / e-mail / messaging-account patterns (also with spaces,
    hyphens, dashes or a country code inside), by values shaped like personal names (Chinese,
    Tibetan, transliterated, Japanese, Korean, pinyin, Western), street addresses or record
    numbers, by dates spanning 40+ years like dates of birth, by a person named inside free text
    ("患者刘洋拒绝随访"), by person-role columns (术者, 主治, surgeon) holding names, or because
    almost every value belongs to a single patient -- are shown by column name and hit counts only.
  * File, sheet and column names: the file name and the chosen sheet name are printed only
    when they are made of ordinary words (data, export, 2023, 随访, 汇总 ...) and hold no digit
    groups of 7+ digits (also joined by – , # + 、 x or spaces: "138 0013 1005", "100,1234"); the names
    of the other sheets are never printed; a column name that holds a person (also inside a longer
    name: "患者张三", "王芳医生", "Dr. Smith", "Testa Personne_hb", "hb(Testa Personne)"; a name of a strong
    shape anywhere in it, whatever stands next to it: "王一二左眼", "3床王一二", "Mary Smith CT", "John_Smith"),
    a record code or 7+ digits is replaced by its position, and the problem list says which 列N and why --
    item, visit and time codes (SF36_01, V01_01, T08_30), date stamps (Hb_20230101) and rsIDs are no codes,
    clinical words and eponyms ("Heart Rate", "Child Pugh", "Kellgren Lawrence", "白细胞", "白天心率", "周平均血压",
    "焦虑评分", a surname + 氏 such as "王氏评分") no persons -- and so are those of a table that looks
    transposed (patients as columns,
    also named by their record numbers); a title row above the header (1-2 cells over wider rows, or
    up to 4 cells with one like "患者：张三" / "住院号：…" / "XX医院" above a row of column names) is never
    printed as column names -- the problem list says how many rows to skip with --skip-rows.
  * Units, flags and example cells: a unit, a lab flag or an example cell (section 4, the mixed-units hint, a
    censored example, a level of a numeric column) is printed when its unit is a known one (mmol/L, g/L, ×10^9/L,
    mg/dL, IU/mL, %, mmHg, °C, 岁, 元 ...) and its flag one of the lab flags; any other string read as a unit
    ("Lin Yu" and "周天元" are made of unit words) is printed only with a patient unit, when 5+ patients have it and
    it is shaped like no name -- otherwise it is counted ("另有 N 种单位写法不显示").
  These are pattern checks: an identifier that fits none of them is not recognised, so the
  report is still reviewed before it is shared. A first row that looks like data (numbers,
  dates, an ID card or phone number, names / record numbers above more of them, or values that
  recur in their columns while no cell reads like a column name) is not used as column names;
  a word over its own yes / no column ("复发" over 复发 / 未复发) stays a header. Quote errors that
  merge lines into one cell are reported with their line numbers. "Rows with no missing value"
  counts only the analysable columns (not all-empty, ID, privacy, remarks or free-text columns).
  Rows are grouped by patient only by the patient ID -- --id, or without it the one column named
  like a patient identifier whose values repeat (_auto_patient_key) -- so a variable that merely looks like an ID
  ("arm_id"), a record number found only by its values, or the outcome never groups the outcome
  or a centre; when a per-row number (序号, 流水号) sits next to the repeating ID, the problem list
  says which was used. All-different whole numbers, and whole numbers of 5+ digits that behave
  like record numbers (also in a table of 3-19 rows; one value per patient; repeating in a long
  table more often than chance ties would), are typed ID -- a type, not a privacy redaction; round
  counts (213000) and yyyymmdd dates are not; a measurement such as a cost or a baseline value is
  kept numeric with --not-id, which the problem list names. Nothing outside the outcome's own
  summary depends on --outcome: every column, the outcome too, is profiled the same way with and
  without it, and the patient key is chosen without it (an --outcome that is the detected patient
  key stays the key; its entry says so). All checks of raw cells run on bounded lengths with linear
  patterns. CSV encodings tried without --encoding: UTF-8 (a few stray bytes are replaced and reported
  with their line numbers), GBK (Big5 when its reading is clearly more of a text), GB18030. Chinese wins:
  bytes that are valid GBK / GB18030 are read as Chinese (a GBK file of 男 / 女 or 是 / 否 is valid EUC-KR
  too); when their Korean / Japanese reading is clearly the text (frequent characters, label words such as
  남 / 여) a warning names EUC-KR / Shift-JIS / EUC-JP and --encoding, and no text value is printed until the
  encoding is given (also when an explicit --encoding reads clearly worse than another one); a value whose
  bytes read as a name in another East-Asian encoding counts as a name; only bytes that are no valid GB18030
  are read as EUC-KR / Shift-JIS / EUC-JP (with a warning).
  Exit status 0 = report written / printed; 2 = invalid arguments or an unreadable file (one
  line on stderr, no traceback).

Command line
  python3 data_profile.py data.csv --id patient_id --outcome recurrence --report data-profile.md
  python3 data_profile.py wide.csv --rows-are-patients --outcome death   # one row per patient, no ID column
  python3 data_profile.py export.xlsx --sheet Sheet2 --outcome death --time months --json profile.json
  python3 data_profile.py data.csv --missing-tokens 拒查,未做 --missing-tokens age=0 --range age=0:120
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
import functools
import hashlib
import io
import json
import math
import os
import re
import sys
import unicodedata

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover - depends on the user's environment
    print("[数据体检] 缺少 pandas / numpy：pip install pandas numpy（读 .xlsx 另需 openpyxl）", file=sys.stderr)
    raise SystemExit(2)

STATEMENT = "本报告只描述数据结构与质量，不含变量间或与结局的关系"
# A text value is printed only when at least this many patients hold it (rows are patients only with
# --rows-are-patients or an --id of one row each); when patients cannot be told apart, never.
SMALL_CELL_K = 5

# ─── vocabularies ───────────────────────────────────────────────────────────

DEFAULT_MISSING_TOKENS = (
    "", "NA", "N/A", "n/a", "na", "NaN", "nan", "NULL", "null", "None",
    "#N/A", "#NULL!", "#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NUM!",
    ".", "/", "\\", "-", "--", "—", "——", "?", "？",
    "未查", "未测", "未检", "未做", "未知", "不详", "不清", "无", "缺失", "缺", "空",
    "未检测", "未检查", "未测定", "未测量", "未化验", "未行", "未记录", "未填", "未填写", "未提供",
    "未送检", "未送", "未采", "未采集", "未采样", "拒查", "拒检",
    "暂无", "暂缺", "待查", "待定", "不明", "不适用", "无记录", "无数据", "失访",
    "missing", "unknown", "unk", "not done", "not available", "not applicable", "n.a.",
    "999", "9999", "-99", "-999",
    # traditional characters (Big5 exports from Taiwan / Hong Kong)
    "未檢", "未測", "未檢測", "未檢查", "未化驗", "不詳", "無", "未記錄", "未填寫", "未送檢", "未採", "未採集",
    "拒檢", "暫無", "暫缺", "不適用", "無記錄", "無數據", "失訪",
    "不清楚", "不知道", "(空)", "<空>", "[空]", "空白", "NK", "NR", "拒绝", "拒絕",
)
# These may be real values: "无"/"none" = "no, none" (并发症=无) or zero (输血量=无); "-" = negative
# in lab results. They count as missing only in date / ID columns; in numeric and categorical
# columns they are kept and listed for the user to confirm (numeric statistics leave them out).
AMBIGUOUS_TOKENS = frozenset({"无", "無", "none", "-"})
# missing in a number / date column, but a real category in a categorical one (随访结局 = 失访)
# ("NR" is also "non-reactive" in serology, "拒绝" a consent answer, "NK" not known / NK cells)
CATEGORY_TOKENS = frozenset({"失访", "失訪", "lost to follow-up", "lost to follow up", "nr", "nk", "拒绝", "拒絕"})
# "ND": not detected in a lab (number) column -- a censored value; not done in any other column
ND_WORDS = frozenset({"nd", "n.d.", "n.d", "n/d"})
# numeric columns that are no lab results: there "ND" is "not done" (missing), not "not detected"
NON_LAB_NAME_RE = re.compile(r"(?:^|[^a-z])(?:age|weight|height|bmi|score|count|days?|duration|months?|years?|los|parity"
                             r"|gravida|visits?|times?)(?:$|[^a-z])|年龄|岁|体重|身高|评分|分数|得分|次数|个数|数量|天数|时长|月数"
                             r"|年限|住院日|孕次|产次|随访")
# Tokens pandas.read_csv() already turns into NaN by default (they do not force a text column).
PANDAS_DEFAULT_NA = frozenset({"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan",
                               "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None",
                               "n/a", "nan", "null"})

TYPE_LABELS = {"numeric": "数值", "categorical": "分类", "date": "日期", "text": "文本",
               "id": "ID 样式", "empty": "全部缺失"}

# ASCII digits only: Python's \d also matches full-width "４５", which pandas reads as text.
# Written so that a run of digits can be split only one way (no slow backtracking on a long cell).
_NUM = r"[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?"
PLAIN_NUM_RE = re.compile(rf"^{_NUM}$")
_CENS_OPS = r"<=|>=|≤|≥|⩽|⩾|≦|≧|<|>|小于|大于|低于|高于|不足|超过"
# (not a titre "<1:40": a ratio after the operator is no detection limit)
CENSORED_RE = re.compile(rf"^(?:{_CENS_OPS})\s*{_NUM}(?:\s*(?!:\s*[0-9])[^\d\s].*)?$")
# "60以上", "5cm以下", "65岁及以上": the bound written after the number. The unit is a group of its own
# (not "\s*X{0,3}?\s*", two space runs around an optional part: quadratic on a cell of spaces).
CENSORED_SUFFIX_RE = re.compile(rf"^(?P<num>{_NUM})(?:\s*(?P<unit>[A-Za-z%一-鿿]{{1,3}}))?\s*(?:及|或)?(?P<side>以上|以下)$")
CENSORED_WORDS = frozenset({"未检出", "低于检测限", "低于检出限", "高于检测限", "超出检测上限", "未检测到", "检测不到",
                            "低于检测下限", "高于检测上限", "低于检出下限", "高于检出上限", "低于定量下限", "高于定量上限",
                            "小于检测下限", "大于检测上限", "超出检测范围", "低于线性范围", "高于线性范围", "超出线性范围",
                            "未檢出", "低於檢測限", "低於檢出限", "高於檢測限", "未檢測到", "檢測不到", "低於檢測下限", "高於檢測上限",
                            "<lod", "<loq", "<lloq", ">uloq", "bdl", "blq", "bql", "bloq", "alq", "aloq", "below lod", "below loq",
                            "below lloq", "above uloq", "below detection limit", "below the detection limit", "above detection limit",
                            "not detected", "undetected", "undetectable"})
# raw cells longer than this are text: no number / date / censored pattern is tried on them
MAX_MEASURE_LEN = 200
# column-name rules (privacy words, ID / date / cluster words) read the first this many characters of a name
MAX_NAME_RULE_LEN = 200
# operator and threshold of a censored string: "<0.5" -> ("<", 0.5); used to tell bins from limits
CENSORED_PARTS_RE = re.compile(rf"^({_CENS_OPS})\s*({_NUM})")
LOWER_OPS = frozenset({"<=", "≤", "⩽", "≦", "<", "小于", "低于", "不足"})
INCLUSIVE_OPS = frozenset({"<=", ">=", "≤", "≥", "⩽", "⩾", "≦", "≧"})
# a bin between two numbers: "2-5cm", "60~69岁", "18.5–24"
RANGE_RE = re.compile(rf"^{_NUM}\s*(?:-|~|～|–|—|至|到)\s*{_NUM}\s*[^\d\s]{{0,6}}$")
# lab-report abnormal flags next to a number: "5.6↑", "3.2 ↓", "7.8H", "1.2 L", "120*", "4.1(H)", "↑5.6"
_CN_FLAGS = r"偏高|偏低|升高|降低|增高|减低|高|低"
_FLAG = rf"(?:↑+|↓+|\*+|HH|LL|H|L|\+|\((?:HH|LL|H|L|↑|↓|{_CN_FLAGS})\)|\[(?:HH|LL|H|L)\]|{_CN_FLAGS})"
# ("H 9.6": a letter flag before the number only with a space after it; "9.6+": "+" only after a decimal, see _classify)
FLAG_RE = re.compile(rf"^(?:(?P<pre>↑+|↓+|\*+|(?:HH|LL|H|L)(?=\s))\s*)?(?P<num>{_NUM})\s*(?P<post>{_FLAG})?$")
# a flag after a unit: "5.6mmol/L↑", "130 g/L(L)"; a letter flag only after a space ("95 g/L L")
SYMBOL_FLAG_TAIL_RE = re.compile(r"^(?P<rest>.*?[^\s↑↓*])\s*(?P<flag>↑+|↓+|\*+|\((?:HH|LL|H|L|↑|↓)\)|\[(?:HH|LL|H|L)\])$")
LETTER_FLAG_TAIL_RE = re.compile(r"^(?P<rest>.*\S)\s+(?P<flag>HH|LL|H|L)$")
THOUSANDS_RE = re.compile(r"^[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
SPACE_THOUSANDS_RE = re.compile(r"^[-+]?[0-9]{1,3}(?: [0-9]{3})+(?:\.[0-9]+)?$")       # "12 345" (also no-break / thin spaces)
# an approximate or doubtful value: "约12.3", "~12.3", "≈12.3", "5.2?"
APPROX_RE = re.compile(rf"^(?:约|大约|~|≈|≒)\s*({_NUM})$")
QMARK_RE = re.compile(rf"^({_NUM})\s*\?$")
COMMA_DECIMAL_RE = re.compile(r"^[-+]?(?:[0-9]+,[0-9]{1,2}|0,[0-9]+)$")         # "5,2", "37,25", "0,125"
EURO_NUM_RE = re.compile(r"^[-+]?[0-9]{1,3}(?:\.[0-9]{3})+,[0-9]+$")               # "12.345,67"
# a number written with a decimal comma / thousands separators and followed by something (a unit): "5,4 mmol/L", "12,345.67元"
LOCALE_TAIL_RE = re.compile(r"^([-+]?(?:[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+,[0-9]{1,2}|[0-9]{1,3}(?:\.[0-9]{3})+,[0-9]+))"
                            r"\s{0,3}(\S.{0,40})$")
APPROX_REASON = "约数（约、~、≈、左右、余、多等）"
# an approximate value written with a word before or after the number: "约500ml", "approx. 5.6 mmol/L", "500ml左右", "12余年"
_APPROX_PREFIX_RE = re.compile(r"(?:约为|大约|大概|约|近|~|≈|≒|approx\.?|approximately|about|around|ca\.|circa)\s{0,3}(?=[-+.0-9])",
                               re.IGNORECASE)
_APPROX_SUFFIX_RE = re.compile(r"(?<=\S)\s{0,3}(?:左右|上下|余|多|许)$")
_APPROX_INFIX_RE = re.compile(r"^([-+]?[0-9]+(?:\.[0-9]+)?)\s{0,2}(?:余|多)\s{0,2}(\S.{0,30})$")             # "12余年", "20多岁"
# a lab flag written as a word, before or after the number (and its unit): "5.6 High", "5.6 (High)", "14.8 A", "14.0 !H",
# "12.3 (危急值)", "5.5（异常）", "阳性 12", "5.6 mmol/L Low"; a letter A / AA / N (abnormal / critical / normal) only after a
# decimal or a number of 3+ digits ("3 A" is a grade)
_WORD_FLAG = r"(?:[Hh]igh|HIGH|[Ll]ow|LOW|[Aa]bnormal|ABNORMAL|[Cc]ritical|CRITICAL|弱阳性|阳性|阴性|偏高|偏低|升高|降低|增高|减低|异常|危急值|危急)"
_LETTER_FLAG = r"[*!]{0,2}(?:HH|LL|H|L|AA|A|N)[*!]{0,2}"
_FLAG_SUFFIX_RE = re.compile(rf"(?<=[0-9A-Za-z%./°μ一-鿿])(?:\s{{0,3}}\(\s{{0,2}}(?P<a>[*!]{{0,2}}{_WORD_FLAG}[*!]{{0,2}}|{_LETTER_FLAG})\s{{0,2}}\)"
                             rf"|\s{{1,3}}(?P<b>[*!]{{0,2}}{_WORD_FLAG}[*!]{{0,2}}|{_LETTER_FLAG})|(?P<c>{_WORD_FLAG}))$")
_FLAG_PREFIX_RE = re.compile(rf"(?P<f>{_WORD_FLAG})\s{{0,3}}:?\s{{0,3}}(?=[-+.0-9])")
# a number followed by something: "130g/L", "45岁", "12 %"; at most 10 integer digits so ID
# numbers ending in X are not read as numbers. The tail is a unit only if it parses as one.
NUM_TAIL_RE = re.compile(r"^([-+]?(?:[0-9]{1,10}(?:\.[0-9]*)?|\.[0-9]+))\s*(\S.{0,40})$")
NUM_E_TAIL_RE = re.compile(r"^([-+]?[0-9]{1,10}(?:\.[0-9]*)?[eE][-+]?[0-9]{1,3})\s*(\S.{0,40})$")     # "1.7E+08 IU/mL"
# a power of ten after the number that multiplies it ("5.29×10^5 IU/mL", "3.2*10^4") -- not one that is part of a
# unit per volume ("6.5×10^9/L")
_MULT_RE = re.compile(r"^[x×*]\s?10(?:\^|\*\*|\*|e|~)?(-?[0-9]{1,2})(?![0-9])\s*(.*)$")
# a flag before the unit: "9.6↑ mmol/L", "9.6* mmol/L"
_FLAG_FIRST_RE = re.compile(r"^(?P<flag>↑+|↓+|\*+)\s*(?P<rest>\S.*)$")

# Units are read by their parts: every character of the tail must belong to a unit word, a power
# of ten, a separator or an exponent -- "Smith", "王芳", "Baker Street", "days later" are no units.
UNIT_WORDS = frozenset("""
kg g mg ug μg mcg ng pg lb lbs oz l dl ml ul μl cl cc fl mol mmol umol μmol nmol pmol meq eq osm mosm
iu miu uiu μiu u mu ku kiu iu iu/l copies copy cells cell cfu pfu m cm mm km um μm nm in inch inches ft
mmhg hg kpa pa cmh2o mmh2o atm bar s sec secs second seconds min mins minute minutes h hr hrs hour hours
d day days wk wks week weeks mo mon month months y yr yrs year years old kcal cal kj hpf hp lp lpf gtt
drops drop units unit points point pts score bpm rpm beats breaths times yo y/o % ‰ °c °f
岁 次 分 分钟 秒 小时 时 天 日 周 星期 个月 月 年 斤 公斤 千克 克 毫克 微克 纳克 毫升 升 毫米 厘米 米 个 片 粒 支
袋 瓶 单位 毫米汞柱 度 毫摩尔 微摩尔 次数 人次 例 包 根 人 名 元 万元 千元 美元 rmb cny usd eur
""".split())
_UNIT_WORD_LIST = sorted(UNIT_WORDS, key=len, reverse=True)
_POW10_RE = re.compile(r"(?:[x×*]\s?)?10(?:\^|\*\*|\*|e|~)?-?[0-9]{1,2}")
_UNIT_EXP_RE = re.compile(r"\^?-?[23]")
_UNIT_FACTOR_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?")
# a unit after which a factor follows a slash ("/1.73m2", "/100ml", "/24h"): "/80mmHg" is no unit
_PER_UNITS = frozenset({"m2", "m^2", "ml", "dl", "l", "ul", "μl", "h", "hr", "hrs", "hours", "min", "kg", "g", "hpf", "lpf",
                        "cells", "cell", "个", "小时", "天", "d", "day", "days"})
# superscript digits ("×10⁹/L", "m²"): written as "^9" before NFKC turns them into plain digits ("×109/L")
_SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SUPERSCRIPT_RE = re.compile("[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+")
# two numbers in one cell: blood pressure "120/80", "120/80 mmHg"; a size "3.5×2.1cm", "2x3x4 cm"
_LEN_UNIT = r"(?:\s*(?:cm|mm|m))?"
COMPOUND_RE = re.compile(r"^(?:[0-9]{1,3}\s*/\s*[0-9]{1,3}(?:\s*(?:mm\s*hg|kpa))?"
                         rf"|{_NUM}{_LEN_UNIT}\s*[×xX*]\s*{_NUM}{_LEN_UNIT}(?:\s*[×xX*]\s*{_NUM}{_LEN_UNIT})?)$", re.IGNORECASE)
# blood pressure written with a dash ("120-80"): two numbers, the first larger -- a range ("60-69") has the smaller first
DASH_PAIR_RE = re.compile(r"^([0-9]{2,3})\s*[-–—]\s*([0-9]{2,3})(?:\s*mm\s*hg)?$", re.IGNORECASE)
_PAIR_RE = re.compile(r"^([0-9]{1,3})\s*[/\-–—]\s*([0-9]{1,3})")

DATE_SHAPE_RE = re.compile(r"^(?:\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.](?:\d{4}|\d{2})"
                           r"|\d{1,2}[-\s/]?[A-Za-z]{3,9}\.?[-\s/]?(?:\d{4}|\d{2}))(?![0-9])")
# a whole cell shaped like a (possibly impossible) date, digits and separators only: shown as written
BROKEN_DATE_RE = re.compile(r"^\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?$"
                            r"|^\d{1,2}[-/.]\d{1,2}[-/.](?:\d{4}|\d{2})$|^\d{8}$")
TIME_OF_DAY_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?$")
DMY_RE = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4}|\d{2})(?![0-9])")
_YMD_RE = re.compile(r"^([0-9]{4})([-/.年])([0-9]{1,2})[-/.月]([0-9]{1,2})日?$")
_YM_RE = re.compile(r"^([0-9]{4})([-/.年])([0-9]{1,2})月?$")
# the same separator twice: "18.5-24" is a range, not 18 May 2024
_DMY_FULL_RE = re.compile(r"^([0-9]{1,2})([-/.])([0-9]{1,2})\2([0-9]{4}|[0-9]{2})$")
_Y8_RE = re.compile(r"^([0-9]{4})([0-9]{2})([0-9]{2})$")
_YY_MM_DD_RE = re.compile(r"^([0-9]{2})([-/.])([0-9]{2})\2([0-9]{2})$")
_DATE_TIME_SPLIT_RE = re.compile(r"^([0-9][^\sT]{3,15}?)(?:(?:T|\s+)(.{1,30}))?$")
_TIME_RE = re.compile(r"^(?:(上午|下午|AM|PM|am|pm|a\.m\.|p\.m\.)\s*)?([0-9]{1,2})"
                      r"(?::([0-9]{2})(?::([0-9]{2})(?:\.[0-9]{1,6})?)?|时(?:([0-9]{1,2})分(?:([0-9]{1,2})秒)?)?|点)"
                      r"\s*(上午|下午|AM|PM|am|pm|a\.m\.|p\.m\.)?\s*(?:Z|[+-][0-9]{2}:?[0-9]{2})?$")
# month written as a word: "25-Mar-2023", "25MAR2023" (SAS), "Mar 25, 2023", "25 March 2023", "Jan-22", "Jan 2022"
MONTH_DATE_RE = re.compile(r"^\d{1,2}[-\s/]?[A-Za-z]{3,9}\.?[-\s/]?\d{2,4}$|^[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}$"
                           r"|^[A-Za-z]{3,9}\.?(?:-\d{2}|[-\s/]\d{4})$"
                           r"|^[A-Za-z]{3,9},?\s+[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}$")      # "Wed Jan 16 2019"
MONTH_DATE_FORMATS = ("%d-%b-%Y", "%d-%b-%y", "%d %b %Y", "%d%b%Y", "%d%b%y", "%d/%b/%Y", "%d-%B-%Y",
                      "%d %B %Y", "%b %d, %Y", "%b %d %Y", "%B %d, %Y", "%B %d %Y",
                      "%b-%y", "%b-%Y", "%b %Y", "%B %Y", "%B-%Y", "%b/%Y",
                      "%a %b %d %Y", "%A %B %d %Y", "%a, %b %d, %Y", "%A, %B %d, %Y", "%a %b %d, %Y", "%a, %b %d %Y")
SENTINEL_DATES = frozenset({(1900, 1, 1), (1899, 12, 30), (1899, 12, 31)})

DATE_NAME_RE = re.compile(r"date|日期|时间|年月|生日|出生|生辰|诞辰|dob|d\.o\.b|birthday|b(?:i?r)?th[\s_\-.]*dt|geburtsdatum"
                          r"|datum|fecha|nascita|naissance|nacimiento|fødsel|dtnasc", re.IGNORECASE)
# date of birth (an identifier) -- but not 出生体重 / 出生(kg) / birth weight / birth order / 出生地 / poids de naissance /
# lieu de naissance / peso al nacimiento: a foreign birth word counts only after a date word or on its own
BIRTH_NAME_RE = re.compile(r"出生(?:日期|年月日?|时间|日|年月|年)?(?:$|[(（\[【](?![^)）\]】]{0,8}(?:kg|克|g\b|周|天|cm|厘米|w\b|wk|分|胎龄|体重|身高)))"
                           r"|生日|生辰|诞辰|生年月日|生年月|^生年$|诞生日|誕生日"
                           r"|b(?:i?r)?th[\s_\-.]*(?:date|day|dt|dte)|geburtsdatum|geburtstag|geboortedatum|f[øo]dselsdato|f[øo]dselsdag"
                           r"|f[öo]delsedatum|date[\s_\-.]*(?:of[\s_\-.]*birth|(?:de[\s_\-.]*)?naissance)"
                           r"|^(?:naissance|nacimiento|nascimento|nascita)$"
                           r"|data[\s_\-.]*(?:(?:de|di|da)[\s_\-.]*)?nasc(?:imento|ita)?(?:$|[^a-z])|dt[\s_\-.]*nasc"
                           r"|fecha[\s_\-.]*(?:de[\s_\-.]*)?nac(?:imiento)?(?:$|[^a-z])"
                           r"|syntymä(?:aika|päivä)|doğum[\s_\-.]*tarihi|dogum[\s_\-.]*tarihi|tanggal[\s_\-.]*lahir|ngày[\s_\-.]*sinh"
                           r"|ngay[\s_\-.]*sinh|data[\s_\-.]*urodzenia|datum[\s_\-.]*narození|datum[\s_\-.]*narozeni|születési"
                           r"|ημερομηνία[\s_\-.]*γέννησης|γέννηση|дата[\s_\-.]*рождения|день[\s_\-.]*рождения|생년월일|생일"
                           r"|(?:^|[^a-z])b[\s_\-.]?date(?:$|[^a-z])"
                           r"|(?:^|[^a-z])dob(?:$|[^a-z])|dob$|bday|(?:^|[^a-z])d\.o\.b\.?(?:$|[^a-z])", re.IGNORECASE)
# the same on the name with spaces / separators removed ("出 生 日 期", "D-O-B", "Geb.-Datum")
BIRTH_COMPACT_RE = re.compile(r"^(?:dob|dateofbirth|birthdate|birthday|bday|bdate|gebdatum|geburtsdatum|fecha(?:de)?nacimiento"
                              r"|nacimiento|naissance|nascimento|nascita|datedenaissance|datenaissance|dtnasc|datanasc|datanascita"
                              r"|datadinascita|datadenascimento|fechanac|生年月日|出生日期|出生年月日?|出生日|"
                              r"诞生日期|生辰|诞辰)"
                              r"(?:yyyymmdd|yyyymm|ddmmyyyy|mmddyyyy|yyyy|ymd|dmy|mdy|date|dt|公历|农历|阳历|阴历|西暦|和暦)?[0-9]?$")
# a DATE column named after birth ("Birth", "出生") is a date of birth
# (also "FNac" / "ddn" -- fecha / date de naissance, but FNAC is also a fine-needle aspiration, so only over dates)
BIRTH_WORD_RE = re.compile(r"birth|born|出生|生日|生辰|诞辰|誕生|dob|nacimiento|nascita|nascimento|naissance|fødsel|födelse|geb"
                           r"|(?:^|[^a-z])f[\s_\-.]?nac(?:$|[^a-z])|(?:^|[^a-z])ddn(?:$|[^a-z])"
                           r"|syntymä|doğum|lahir|sinh|urodzenia|narozen|születés|γέννησ|рождени|생년|생일", re.IGNORECASE)
ID_NAME_RES = (
    re.compile(r"^(?:patient|subject|case|record|study|sample|person|participant)?[\s_\-.]*id$", re.I),
    re.compile(r"^id[\s_\-.]", re.I),
    re.compile(r"[\s_\-.]id$", re.I),
    re.compile(r"^(?:pid|mrn|uid|sid)$", re.I),
    re.compile(r"编号|序号|住院号|病历号|病案号|门诊号|登记号|病例号|就诊卡号|档案号|随机号|入组号|筛选号|^id号码?$|患者id|病人id"
               r"|(?:患者|病人|受试者|病例)(?:编码|唯一号)", re.I),
)
# A column the ID rows can be grouped by (events per patient, patients per centre, one value per
# patient). Without --id only a column named like a patient identifier (or a record number that
# repeats) is trusted with that: "arm_id" or "drug_id" typed ID by name must never relate the
# outcome or a centre to a variable.
PATIENT_ID_NAME_RE = re.compile(
    r"^(?:(?:patient|pt|pat|subject|subj|case|record|person|participant|study|sample|enrol(?:l)?ment|randomi[sz]ation)"
    r"[\s_\-.]*(?:id|no|number|num|code)|[\s_\-.]*(?:id|no))\.?$"
    r"|^(?:pid|mrn|uid|sid|ptid|subjid|usubjid|patid)$"
    r"|住院号|病历号|病案号|门诊号|登记号|入组号|筛选号|研究编号|病例号|就诊卡号|档案号|随机号|^id号码?$|^编号$|^序号$"
    r"|(?:患者|病人|受试者|病例)(?:id|编号|编码|号|序号|唯一号)", re.IGNORECASE)
# names that are an ID only when the column holds codes ("pt" over S001, S002 ...; "PT" over 11.2, 12.5
# is prothrombin time; "subject" over names is a privacy column)
AMBIGUOUS_ID_NAMES = frozenset({"pt", "subject", "subj", "case", "id no"})
CODE_VALUE_RE = re.compile(r"^[A-Za-z]{0,4}[-_]?[0-9]{2,10}[A-Za-z]?$")
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
# columns that hold people who are not patients (surgeons, readers): names there are names,
# however many patients share one
PERSON_ROLE_RE = re.compile(r"术者|主刀|医生|医师|主治|护士|读片|阅片|评分者|评估者|观察者|检查者|操作者|研究者|随访者"
                            r"|(?:^|[^a-z])(?:surgeon|operator|doctor|physician|reader|rater|nurse|investigator|"
                            r"examiner|observer|clinician)s?(?:$|[^a-z])", re.IGNORECASE)
# privacy words in a column name, by kind. A "contact" word next to small numbers is a
# measurement (电话随访次数, phone_use_hours); the others are identifiers whatever the values.
PII_RECORD_SUBSTR = ("身份证", "证件号", "住院号", "病历号", "病案号", "门诊号", "医保号", "病理号", "影像号", "idcard",
                     "id_card", "id card")
PII_PERSON_SUBSTR = ("姓名", "名字", "联系人")
PII_CONTACT_SUBSTR = ("手机", "电话", "联系方式", "住址", "地址", "居住", "现住", "家庭住", "邮箱", "邮编", "邮政编码", "phone",
                      "mobile", "address", "residence", "email", "e-mail", "postcode", "postal code", "zipcode", "zip code")
PII_RECORD_TOKENS = frozenset({"mrn", "nhs", "ssn"})
# "home" names an address / phone ("home", "home_address", "home_cn_dist", "hometown") -- not when a care or
# measurement word follows ("home_bp_control", "home_oxygen", "home_visits")
HOME_CONTACT_RE = re.compile(r"home(?:town|$|[\s_\-.](?![\s_\-.]*(?:bp|blood|pressure|oxygen|o2|care|visits?|monitor|glucose|dialysis"
                             r"|therapy|treatment|infusion|exercise|test|testing|medication|meds|insulin|ventilation|nursing|health"
                             r"|support|rehab|rehabilitation|control|based|setting|death|discharge)))")
PII_PERSON_TOKENS = frozenset({"surname", "forename"})
PII_CONTACT_TOKENS = frozenset({"tel", "addr", "zip"})
# a person's name: "name", "patient name", "pt_name", "full name", "姓名", "患者名", "受检者" ... — but
# not "drug_name", "hospital_name" or pandas' "Unnamed: 3"; a column called just "patient" holds names
# or record numbers, either of them an identifier. Only clear name words count: "PT" (prothrombin
# time), "pT" (pathological T stage), "INR", "Hb" are measurements.
NAME_HEADER_RE = re.compile(r"^(?:patient|pt|subject|full|first|last|given|family|sur)?[\s_\-.]*name$"
                            r"|^(?:patient|client|person)$"
                            r"|^(?:患者|病人|家属|受检者|受检人|受试者|被检者|就诊人|就诊者|病人名|患者名)$", re.IGNORECASE)
RECORD_HEADER_RE = re.compile(r"^hospital[\s_\-.]*(?:number|no\.?)$", re.IGNORECASE)
ID_CARD_RE = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")
# a mobile number, also after a country code ("+86", "0086", "86-" -- the separators are removed first)
MOBILE_RE = re.compile(r"(?:(?<=\+86)|(?<=\+86 )|(?<=\+86-)|(?<=(?<![0-9])86)|(?<=(?<![0-9])0086)|(?<![0-9]))"
                       r"1[3-9][0-9]{9}(?![0-9])")
# a land line once the separators between its digits are removed: "(010) 6234-5678" -> 01062345678
LANDLINE_RE = re.compile(r"(?<![0-9.])0[1-9][0-9]{8,10}(?![0-9])")
# separators between digits ("138-1234-5678", "138–0013–1005", "110101 19900307 1234 X"): removed before the
# checks; also before the X of an ID card
DIGIT_GAP_RE = re.compile(r"(?<=[0-9])[\s\-–—_·•()（）]{1,4}(?=[0-9]|[Xx](?![A-Za-z0-9]))")
# a phone number of 7-8 digits (no area code) or an account named by the word before it ("家里电话 62345678",
# "QQ 4100512", "微信 zw19800101")
CONTEXT_PHONE_RE = re.compile(r"(?:电话|手机|座机|固话|联系方式|tel|phone|mobile|call)[^0-9A-Za-z]{0,6}[0-9]{3,4}[ \-]?[0-9]{4}"
                              r"(?![0-9])", re.IGNORECASE)
CONTEXT_ACCOUNT_RE = re.compile(r"(?:(?<![A-Za-z])qq|微信|wechat|weixin|(?<![A-Za-z])vx|(?<![A-Za-z])wx)[号:：\s]{0,4}"
                                r"[A-Za-z0-9_\-]{5,20}", re.IGNORECASE)
# a raw cell longer than this is free text: privacy checks look at its first MAX_SCAN_LEN characters only
MAX_SCAN_LEN = 5000
# bounded parts (as in the RFCs): no slow backtracking in a long remark
# (the local part may be written in any script: "测试@example.com")
EMAIL_RE = re.compile(r"[^\s@,;，；:：<>()（）\[\]\"']{1,64}@[A-Za-z0-9\-]{1,63}(?:\.[A-Za-z0-9\-]{1,63}){0,4}\.[A-Za-z]{2,24}")
# Values shaped like identifiers, whatever the column is called. Checked per column (at least 5
# different values), so one word that happens to fit does not hide a column.
# Common Chinese surnames (single and compound); a 2-3 character value starting with one, or a
# masked name ("张*", "李某某"), is name-shaped.
CN_SURNAMES = frozenset("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶"
                        "程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付傅方白邹孟熊秦邱江尹薛闫阎段雷侯龙史陶"
                        "黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤"
                        # less frequent surnames (the commonest 300 or so; characters that mostly start
                        # ordinary words -- 文 安 成 和 左 单 关 管 阳 -- are left out)
                        "常温康施洪牛樊葛邢齐易乔伍庞颜倪庄聂章鲁岳翟殷詹申欧耿兰焦俞柳甘祝宁尚舒阮柯纪童凌毕季裴霍"
                        "涂苗谷盛曲翁冉骆蓝路游辛靳柴蒙鲍喻祁蒲房滕屈饶牟尤穆农卓古吉缪简项芦麦褚娄窦戚岑景党"
                        "冷晏席米柏宗瞿桂佟臧闵苟邬卞姬仇栾隋刁荣巫寇桑郎甄丛仲虞敖巩佘池查麻苑迟邝官谈匡鞠惠荆"
                        "冀郁胥班储栗燕楚鄢劳谌奚粟冼蔺楼闻厉伊仝郜阚权帅屠豆朴盖练廉禹祖漆卿狄索宣晋扈晁芮阙浦戈"
                        "伏鹿邸雍辜裘亓邰赫杭逯茹诸慕嵇湛宾戎勾茅揭尉冶檀昝幸衡尧")
CN_COMPOUND_SURNAMES = ("欧阳", "司马", "上官", "诸葛", "东方", "皇甫", "尉迟", "公孙", "慕容", "长孙", "司徒",
                        "令狐", "夏侯", "宇文", "轩辕", "端木", "南宫", "独孤")
CN_NAME_RE = re.compile(r"^[一-鿿]{2,4}$|^[一-鿿][*＊×xX某]{1,2}$|^[一-鿿][*＊×某][一-鿿]$")
CN_MASKED_RE = re.compile(r"^[一-鿿][*＊×xX某]{1,2}$")
# Characters common in Chinese given names. A column is taken for names only when most of its
# name-shaped values have given names made of them: "黄芪 / 白术 / 石斛 / 陈皮" start with a surname
# too, but 芪 / 术 / 斛 / 皮 are no given-name characters.
CN_GIVEN_CHARS = frozenset(
    "一二三四五六七八九十百千万大小东西南北中春夏秋冬天日月星云雨雪霜露风雷电光明亮辉晖煌"
    "伟刚勇毅俊峰强军平保文武斌彬力永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发新利清飞"
    "富顺信子杰涛昌成康安岩茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲"
    "江超浩政谦亨奇固之翰朗伯宏言若鸣朋梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄琛钧冠"
    "策腾楠榕航弘秀娟英华慧巧美娜静淑惠珠翠雅芝玉萍红娥玲芬芳燕彩菊兰凤洁梅琳素莲真环荣爱妹霞香"
    "莺媛艳瑞凡佳嘉琼勤珍贞莉桂娣叶璧璐娅琦晶妍茜秋珊莎锦黛青倩婷姣婉娴瑾颖瑶怡婵雁蓓仪荷丹蓉眉"
    "君琴蕊薇菁梦岚苑婕馨瑗琰韵融园艺咏卿聪澜纯毓悦昭冰爽琬茗羽希欣飘育滢馥筠柔竹凝晓欢霄枫芸菲"
    "寒伊亚宜可舒影荔丽阳妮宝贝初程恒鸿桦骅剑娇纪宽灵琪晴容睿烁唯威韦雯萱彦宇洋忠宗曼紫逸贤蝶菡"
    "儿轩涵梓宸铭昊煜烨鑫锐凯楷坤垚峻嵘川洲淼渊源沛润泓滔潇瀚汉沁远方圆吉喜怀意敏捷笑晗曦昕晟暄"
    "乾诺遥迪佩儒仕仲叔季孟少尚尧舜禹拓扬继延传启迎朴实守定宣宪寅宾宛存孝金银铁钢锋镇钰键柯桐杨"
    "柳樊勋劲励均培增墨石嵩崇峥泉浦长财情雷鹤燕鹰虎豹麟凤莹蕾芙蓝绿彤菲倩卫兵红革跃进超群胜利"
    "根柱栓锁满仓囤田富贵来福运喜财旺发达英雄杰豪斐然书画琪瑛珂瑚珀琨琮璇玮珏蓁菀萌蔓蕴蕙佑"
    # given-name characters that are rarer but used almost only in names (于赟, 王婧, 张珺, 杨帆 ...)
    "立丰碧芹瑜帆熙沐奕赟婧珺旻昶甦晞玥琤珩犇淏水翀霖骁翊岑朗俐昱煊炜焱晔皓琰璟瑄琬瑗珮璠祺禧"
    "钊铮锴镕骞驰骏骐鹍鹏鸾凰姝妤娉婕嫣媛婧嫦姗娟婉妙妍姿娅倩靖竣湘澄淳涛浚渝溪漪潼澍")
# Pinyin surnames: an all-capitals word is a surname in "ZHANG Wei", "Wei ZHANG", "ZHANG WEI"
PINYIN_SURNAMES = frozenset(
    "wang li zhang liu chen yang huang zhao wu zhou xu sun ma zhu hu guo he gao lin luo zheng liang xie song"
    " tang han feng deng cao peng zeng xiao tian dong yuan pan yu jiang cai du ye cheng su wei lu lv ding ren"
    " shen yao cui zhong tan fan jin shi liao jia xia fu fang bai zou meng xiong qin qiu yin xue yan duan lei"
    " hou long tao gu mao hao gong shao wan qian dai mo kong xiang ouyang sima shangguan zhuge".split())
# Latin letters with diacritics ("José García", "Søren Nørgaard", "Łukasz Wójcik")
_LAT_UP = "".join(ch for ch in map(chr, range(0xC0, 0x250)) if ch.isalpha() and ch.isupper())
_LAT_LO = "".join(ch for ch in map(chr, range(0xC0, 0x250)) if ch.isalpha() and ch.islower())
# "Smith, John" / "John Smith" / "J. Smith" / "Mary-Ann O'Neil" / "Leonard H. McCoy" / "Robert Downey Jr."
_WORD = rf"(?:O'|D'|Mc|Mac)?[A-Z{_LAT_UP}][a-z{_LAT_LO}]+(?:['\-][A-Z{_LAT_UP}]?[a-z{_LAT_LO}]+)*"
_CAPS = rf"[A-Z{_LAT_UP}]{{2,}}(?:['\-][A-Z{_LAT_UP}]+)*"
_SUFFIX = r"(?:,?\s+(?:Jr|Sr|II|III|IV)\.?)?"
WESTERN_NAME_RE = re.compile(rf"^{_WORD},\s*{_WORD}(?:\s+[A-Z]\.?)?$|^(?:{_WORD}|[A-Z]\.)(?:\s+[A-Z]\.?)?\s+{_WORD}{_SUFFIX}$"
                             # "Mary Ann Smith", "Peter van Dijk", "Jose de la Cruz", "Kim Jong Su", "Ali ibn Hassan"
                             rf"|^{_WORD}(?:\s+(?:{_WORD}|[A-Z]\.|van|von|de|del|der|den|la|le|da|di|du|dos|das|do|bin|ibn|al|el"
                             rf"|abu|ten|ter)){{1,2}}\s+{_WORD}{_SUFFIX}$")
# "SMITH, John", "ZHANG, WEI": a capitalised surname before a comma
CAPS_COMMA_NAME_RE = re.compile(rf"^{_CAPS},\s*(?:{_WORD}|{_CAPS})$")
# "ZHANG Wei", "ZHANG WEI", "Wei ZHANG": only with a pinyin surname in capitals (not "STABLE DISEASE")
CAPS_NAME_RE = re.compile(rf"^(?P<a>{_CAPS}|{_WORD})\s+(?P<b>{_CAPS}|{_WORD})$")
# pinyin written without a space or in lower case: "ZhangWei", "LiNa", "zhang wei", "wang xiaoming"
_PINYIN_SYL = (r"(?:zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?(?:iang|iong|uang|ang|eng|ing|ong|uai|uan|ian|iao|ai|ei|ao|ou|an|en|in"
               r"|un|ia|ie|iu|ua|uo|ui|ue|er|a|o|e|i|u|v)")
PINYIN_GIVEN_RE = re.compile(rf"^(?:{_PINYIN_SYL}){{1,2}}$")
PINYIN_CAMEL_RE = re.compile(r"^([A-Z][a-z]+)([A-Z][a-z]+)$")
# common Western given names: a word that is one of them makes a single word ("Mary"), a lower-case pair
# ("smith john") or a column header ("John Smith评分") a person. Words that are also months, places or
# ordinary words (May, Grace, Florence, Austin, Will) are left out.
FIRST_NAMES = frozenset("""
james john robert michael william david richard joseph thomas charles christopher daniel matthew anthony donald
steven paul andrew joshua kenneth kevin brian george edward ronald timothy jason jeffrey ryan jacob gary nicholas
eric jonathan stephen larry justin scott brandon benjamin samuel gregory frank alexander raymond patrick jack dennis
jerry tyler aaron jose adam henry nathan douglas zachary peter kyle walter ethan jeremy harold keith 
roger noah gerald carl terry sean arthur lawrence jesse dylan bryan joe albert logan willie alan juan wayne
ralph roy eugene louis philip bobby johnny liam oliver lucas mason elijah aiden sebastian mateo levi
mary patricia jennifer linda elizabeth barbara susan jessica sarah karen nancy lisa betty margaret sandra ashley
kimberly emily donna michelle dorothy carol amanda melissa deborah stephanie rebecca sharon laura cynthia kathleen
amy shirley angela helen anna brenda pamela nicole emma samantha katherine christine debra rachel catherine carolyn
janet maria heather diane julie joyce kelly christina lauren joan evelyn olivia judith megan cheryl martha
andrea frances hannah jacqueline ann gloria jean kathryn alice teresa sara janice doris julia judy abigail
marie denise beverly theresa marilyn danielle diana brittany natalie sophia isabella mia ava amelia
harper ella chloe zoe zoë ellie scarlett
jose josé juan carlos luis miguel javier antonio manuel francisco pedro alejandro ángel angel diego jorge alberto
fernando ricardo sergio raúl raul andrés andres pablo inés ines lucía lucia carmen isabel elena pilar
françois francois pierre jean jacques michel philippe nicolas alain bernard renée renee chloé chloe camille sophie
hans jürgen jurgen klaus wolfgang stefan andreas thomas uwe björn bjorn søren soren lars anders mårten marten nils
erik karl ingrid astrid zoë zoe łukasz lukasz piotr krzysztof tomasz marek ewa agnieszka katarzyna magdalena
mohammed muhammad mohamed ahmed ahmad ali hassan hussein omar mahmoud yusuf ibrahim fatima aisha khadija zainab
mariam leila layla sean ian liam kim
""".split())
# Tibetan names are made of a few dozen syllables ("扎西多吉", "次仁卓玛", "央金")
TIBETAN_SYLLABLES = frozenset("""
扎西 次仁 格桑 拉姆 央金 达瓦 尼玛 平措 德吉 索朗 旦增 拉巴 白玛 卓玛 多吉 措姆 普布 边巴 次旦 洛桑 丹增 益西 曲珍 仁增 群培
巴桑 米玛 顿珠 强巴 嘎玛 欧珠 贡布 桑珠 罗布 次珠 旺堆 旺姆 加措 嘉措 卓嘎 拉珍 央宗 德庆 格勒 次央 白珍 琼达 普琼 曲吉 次多
尼珍 桑姆 达娃 拉宗 群宗 才让 多杰 洛追 贡嘎 晋美 赤列 土登 阿旺 南杰 卓嘎 玉珍 德央 仓决 次曲 边珍 拉吉 益加 色珍 美朵
""".split())
_TIB_RE = re.compile("^(?:" + "|".join(sorted(TIBETAN_SYLLABLES, key=len, reverse=True)) + "){1,3}$")
# a transliterated foreign name with a middle dot ("买买提·艾力", "约翰·史密斯")
DOT_NAME_RE = re.compile(r"^[一-鿿]{1,8}(?:[·•・．.][一-鿿]{1,8}){1,3}$")
# Japanese names: one of the commoner two-character surnames and a one / two character given name
JP_SURNAMES = frozenset("""
佐藤 鈴木 高橋 田中 伊藤 渡辺 渡邊 山本 中村 小林 加藤 吉田 山田 佐々木 山口 松本 井上 木村 林 斎藤 斉藤 清水 山崎 森 池田
橋本 阿部 石川 山下 中島 石井 小川 前田 岡田 長谷川 藤田 後藤 近藤 村上 遠藤 青木 坂本 福田 太田 西村 藤井 金子 岡本
藤原 中野 三浦 原田 中川 松田 竹内 小野 田村 中山 和田 石田 森田 上田 原 内田 柴田 酒井 宮崎 横山 高木 安藤 宮本 大野
小島 谷口 今井 工藤 高田 増田 丸山 杉山 村田 大塚 新井 小山 平野 藤本 河野 上野 野口 武田 松井 千葉 岩崎 菅原 木下 久保
""".split())
# Korean names: three Hangul syllables starting with a common surname ("김민준")
KR_SURNAMES = frozenset("김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구민진나지엄채원천방공현함변염여추도소석선설마길연위표명기반왕금옥육인맹제모탁국어은편용예경봉사부가복태목형피두감호음빈동온시범좌팽승간상갈")
HANGUL_NAME_RE = re.compile(r"^[가-힣]{3,4}$")
# last syllables of Korean clinical words (압 pressure, 병 disease, 증 syndrome, 암 cancer, 염 inflammation ...)
KR_TERM_END = frozenset("압병증암염률율량액종통술제혈균막력법약관낭")
# a title after a name ("张伟先生", "王芳(女)")
CN_TITLE_SUFFIX_RE = re.compile(r"(?:先生|女士|小姐|太太|阿姨|老师|大爷|大妈|奶奶|爷爷|同志|[(（](?:男|女)[)）])$")
# initials, only for a single label such as a sheet name: "J Smith", "Smith J"
INITIAL_NAME_RE = re.compile(rf"^[A-Z]\.?\s+{_WORD}$|^{_WORD}\s+[A-Z]\.?$")
# words that make a two-word value a place, institution or category, not a person ("New Zealand",
# "Mayo Clinic", "Left Lobe", "Stable Disease", "Patient Name", "Hodgkin Lymphoma")
NON_NAME_WORDS = frozenset(
    "united new south north east west saudi costa sri hong kong san santa los las saint mount mt lake port fort"
    " cape great clinic hospital health medical medicine center centre university college institute general"
    " memorial children childrens county city state states kingdom republic island islands zealand africa"
    " arabia rica lanka america group arm grade stage type phase level class lobe upper lower left right"
    " middle positive negative normal abnormal not done none yes no other unknown disease response partial"
    " complete stable progressive primary secondary early late acute chronic male female mild moderate severe"
    " risk dose name patient subject first last full given family surname date number code id street road"
    " avenue lane drive sheet data summary table results result raw baseline follow up visit export list"
    " cohort site figure fig total all lab labs test tests imaging pathology survey notes info main final"
    " clean cleaned original old copy version lymphoma sarcoma syndrome tumor tumour disease palsy esophagus"
    " oesophagus carcinoma cancer leukemia leukaemia myeloma fracture failure arthritis thyroiditis anemia"
    " anaemia sign test scale score index criteria classification procedure operation repair resection".split())
# clinical words and eponyms: two capitalised words that hold one ("Heart Rate", "Child Pugh", "Hunt Hess", "Smoking
# Status") are a variable or a scale, not a person -- unless a common given name makes them one ("Mary Hunt")
MEDICAL_WORDS = frozenset("""
heart rate blood pressure body mass temperature weight height pulse oxygen saturation respiratory breathing white red
cell cells count platelet platelets hemoglobin haemoglobin glucose sugar serum plasma urine urinary protein albumin
creatinine clearance bilirubin enzyme liver kidney renal hepatic cardiac lung pulmonary function vital status smoking
smoker alcohol drinking marital education income occupation history comorbidity comorbidities tumor tumour size node
nodes lymph lymphocyte neutrophil monocyte eosinophil basophil ejection fraction volume capacity flow pain quality
life scale scales questionnaire item items domain physical mental social emotional role cognitive fatigue nausea
vomiting appetite sleep anxiety depression stress mood symptom symptoms sign signs dose doses drug drugs therapy
treatment surgery surgical operative operation time duration length stay hospital admission discharge readmission
mortality survival death recurrence relapse progression response remission toxicity adverse event events side effect
effects infection fever cough wound healing bleeding blood loss transfusion fluid intake output diet nutrition
vitamin mineral iron calcium sodium potassium chloride magnesium phosphate zinc copper factor hormone thyroid insulin
cortisol testosterone estrogen oestrogen progesterone antigen antibody marker markers biomarker gene genes mutation
expression receptor pathway ratio index score scores class category grade stage type subtype status level levels
total mean average median range minimum maximum baseline follow visit visits week weeks month months year years day
days hour hours minute minutes pre post before after during first second third last left right bilateral anterior
posterior upper lower distal proximal central peripheral acute chronic primary secondary family personal medical
clinical laboratory lab imaging scan ultrasound echo ecg ekg eeg emg mri ct pet xray radiograph biopsy pathology
histology cytology margin margins invasion lymphovascular perineural differentiation necrosis fibrosis cirrhosis
child pugh hess spetzler gleason breslow ann arbor charlson killip mayo apgar
karnofsky mallampati borrmann debakey
glasgow coma ranson apache sofa curb barthel rankin nyha ecog kps asa child pugh meld albi tnm figo who
kaposi
gustilo schatzker lauge frankel oswestry womac lysholm tegner kujala mcgill
zung morisky braden caprini khorana timi euroscore syntax cobb angle risser
thickness depth width diameter area circumference cormack lehane aldrete agitation sedation wfns abcd hospital anxiety
vision visual hearing acuity strength grip gait balance walking mobility activity activities daily living
systolic diastolic arterial venous mean central pressure rate rhythm interval segment wave axis
phenomenon fundoplication limb change model lamp maneuver manoeuvre monitoring treadmill angina postnatal arteritis
procedure repair classification criteria injury fracture disease cyst neuroma gangrene palsy reflex triad curve method
equation formula effect approach technique incision flap exact rank correlation kappa alpha rho coefficient regression
""".split())
# places and eponyms made of a given name and another word: no person ("Ann Arbor stage", "Johns Hopkins")
NOT_PERSON_PHRASES = frozenset({"ann arbor", "johns hopkins", "john hopkins", "mary kay", "st john", "st james", "st mary",
                                "st thomas", "st george", "st peter", "mount sinai", "san jose",
                                # eponym scales and classifications (column names such as "Kellgren Lawrence", "Hoehn Yahr")
                                "kellgren lawrence", "stevens johnson", "hoehn yahr", "lund mackay", "salter harris",
                                "gustilo anderson", "spetzler martin", "hunt hess", "child pugh", "cormack lehane",
                                # (two surnames: tests, scores and syndromes)
                                "bloom richardson", "van nuys", "tyrer cuzick", "kaplan meier", "mann whitney", "kruskal wallis",
                                "hosmer lemeshow", "bland altman", "benjamini hochberg", "holm bonferroni", "clavien dindo",
                                "roland morris", "fugl meyer", "dix hallpike", "guillain barre", "henoch schonlein", "peutz jeghers",
                                "budd chiari", "mallory weiss", "osgood schlatter", "hill sachs", "cheyne stokes", "austin flint",
                                "brown sequard", "argyll robertson", "marcus gunn", "kayser fleischer", "prader willi", "li fraumeni",
                                "von willebrand", "lauge hansen", "creutzfeldt jakob", "ehlers danlos", "zollinger ellison",
                                "wernicke korsakoff", "dandy walker", "arnold chiari", "beckwith wiedemann", "sturge weber",
                                "klippel trenaunay", "pierre robin", "michaelis menten", "henderson hasselbalch", "frank starling",
                                "wolff parkinson", "charcot marie", "legg calve", "hippel lindau", "stein leventhal", "le fort",
                                "harris hip"})
# characters of clinical words: a 2-3 character "name" holding one ("白细胞", "高血压", "黄体酮", "华法林") is a variable
CN_TERM_CHARS = frozenset(
    "细胞蛋白血压糖脂酸酶素尿肝肾心肺脑骨肌酐率量度数值级期型性时间龄体温脉搏呼吸钠钾氯钙镁磷铁锌铜碱胆固醇油"
    "检测查验诊断疗术药剂针液浆管瘤癌炎病症征伤痛肿块结节淋巴腺囊胃肠胰脾膀胱宫卵乳房状颈腰腹胸背肢关皮肤眼耳鼻"
    "口牙舌喉咽食道支气氧碳分评指标积容频次周月年岁重径宽厚长短大小高低左右前后内外上下初复首末总均最例法酮酯"
    "苷碱霉唑沙星林汀普利坦洛尔芬因卡铂紫杉醇奥替尼单抗芪术参归苓草根籽果茎菌毒抗原核免疫基化物理科室院所组别"
    "类项目码编号称位置部侧多少再次量否是有无阴阳良恶死活存亡花叶仁皮枝藤壳胶粉丸散汤膏虫冷拉丁")
# words next to a person in a column name: roles, honorifics, kin and contact words ("患者张三", "王芳医生", "家属李娜电话")
HEADER_PERSON_WORDS_CN = tuple(sorted(
    "主治医生 主治医师 主刀医生 主刀医师 手术医生 责任护士 责任医生 管床医生 患者姓名 病人姓名 患者 病人 家属 病友 受检者 受试者 "
    "医生 医师 主治 主刀 术者 护士 主任 大夫 老师 联系人 本人 其子 其女 儿子 女儿 丈夫 妻子 父亲 母亲 爱人 老伴 姓名 签名 签字 "
    "评估者 评分者 读片 阅片 读片者 阅片者 电话 手机 联系电话 联系方式 住址 地址 微信".split(), key=len, reverse=True))
# words that may stand next to a person in a column name without being part of the name ("Testa Personne visit 1")
HEADER_FILLER_EN = frozenset("""visit visits score scores rating ratings reading readings read baseline follow up fu pre post
day days week weeks month months year years time times value values result results test tests lab labs level levels total
mean final initial first second third last left right v t d m w y no number id code group arm site""".split())
FUNCTION_WORDS_EN = frozenset("of the and for in on at to by with per from or vs versus a an no not is are was".split())
HEADER_PERSON_WORDS_EN = frozenset("dr dr. mr mr. mrs mrs. ms ms. miss prof prof. doctor nurse reader rater surgeon patient pt "
                                   "physician examiner observer signed sig sir madam mx".split())
# a person named inside free text: "患者刘洋拒绝随访", "家属李娜代签", "Mr Smith refused"
CN_ROLE_NAME_RE = re.compile(r"(?:患者|病人|家属|病友|受检者|受试者|本人|其子|其女|儿子|女儿|丈夫|妻子|父亲|母亲|爱人|"
                             r"老伴|联系人|医生|医师|护士|主任|大夫)([一-鿿]{2,3})")
HONORIFIC_NAME_RE = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Dr|Prof)\.?\s+[A-Z][a-z]+")
_DOT_IN_TEXT_RE = re.compile(r"[一-鿿]{2,6}[·•・][一-鿿]{2,6}")
_TIB_IN_TEXT_RE = re.compile("(?:" + "|".join(sorted(TIBETAN_SYLLABLES, key=len, reverse=True)) + "){2,3}")
_WEST_IN_TEXT_RE = re.compile(rf"(?<![A-Za-z{_LAT_LO}{_LAT_UP}])({_WORD})\s+{_WORD}")
# street-level addresses: 省/市/区 ... 路/街/号/室; 路/街 + house number ("建国路88号", "88号建国路");
# 小区 / 栋 / 室; or "12 Baker Street". A run of digits is only tried from its first digit.
ADDRESS_RE = re.compile(r"[一-鿿]{1,10}(?:省|市|区|县|旗|镇|乡|街道|村)[一-鿿\w\-—()（）]{0,30}"
                        r"(?:路|街|巷|弄|胡同|大道|小区|村|组|号|栋|幢|单元|室|楼|花园|家园|新村|公寓|大厦|苑|园|城)(?![区县市省])"   # not 鼓楼区
                        r"|[一-鿿](?:路|街|巷|弄|胡同|大道)[0-9]{1,6}(?:号|弄|栋|幢)"
                        r"|^[0-9]{1,6}号[一-鿿]{1,10}(?:路|街|巷|弄|胡同|大道)"
                        r"|(?:小区|花园|公寓|大厦|新村|家园)[0-9]{1,6}(?:号楼|栋|幢|单元|号|室)"
                        r"|(?<![0-9])[0-9]{1,6}(?:栋|幢|号楼)(?:[0-9]{1,4}单元)?[0-9]{1,6}室"
                        r"|^\d{1,6}[A-Za-z]?\s+(?:[A-Za-z.]+\s+){1,4}(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr"
                        r"|boulevard|blvd|way|court|ct|place|pl|close|crescent)\.?(?:[\s,].*)?$", re.IGNORECASE)
# record / specimen numbers: up to 6 letters and a run of 5+ digits in one to five parts ("ZY2023001",
# "S-123456", "ZY-2023-01000", "HN 482910", "MR/23000", "560000-1")
RECORD_PARTS_RE = re.compile(r"^[A-Za-z0-9]{1,12}(?:[\s\-_/.#]{1,2}[A-Za-z0-9]{1,12}){0,4}$")
# ... but not gene / transcript / sequence accessions or reagent lots shared by many patients
NOT_RECORD_RE = re.compile(r"^(?:ENS[A-Z]{0,6}[0-9]|rs[0-9]|[NX][MRP]_|LOT|BATCH|GS[EM][0-9]|[SED]RR[0-9]|SAM[NDE]"
                           r"|PRJ|CHEMBL)", re.IGNORECASE)

EVENT_WORDS = frozenset({"1", "是", "yes", "y", "true", "阳性", "positive", "有", "死亡", "dead",
                         "death", "died", "复发", "recurrence", "event", "发生", "事件"})
# rows that sum up the others ("合计", "Total"): profiled like a patient they distort min / max / counts
TOTAL_WORDS = frozenset({"合计", "总计", "小计", "共计", "总和", "汇总", "平均", "平均值", "均值", "总数", "合計", "總計",
                         "total", "totals", "subtotal", "grandtotal", "sum", "mean", "average", "avg"})
# "均值±标准差", "mean±sd", "mean(sd)", "平均值(标准差)": a row of summary statistics
TOTAL_STAT_RE = re.compile(r"^(?:均值|平均值?|mean|average|中位数|median)(?:±|\+/-|\(|（)?(?:标准差|sd|std|iqr|四分位数间距)?[)）]?$")
DATA_EXTS = (".csv", ".tsv", ".tab", ".txt", ".xlsx", ".xlsm", ".xls", ".sav", ".dta", ".rds")
EXCEL_EXTS = (".xlsx", ".xlsm", ".xls")
# binary formats of statistics packages: reading them as text would give a garbage profile
UNSUPPORTED_EXTS = (".sav", ".zsav", ".por", ".dta", ".rds", ".rdata", ".rda", ".sas7bdat", ".xpt",
                    ".parquet", ".feather", ".pkl", ".pickle", ".mat")
# free-text notes: not an analysis variable, so not part of "complete rows"
REMARK_NAME_RE = re.compile(r"备注|注释|附注|说明|備註|備注|註釋|附註|說明|備考|(?:^|[^a-z])(?:remarks?|notes?|comments?|memo)(?:$|[^a-z])",
                            re.IGNORECASE)

# Words a file or sheet name may be made of and still be printed. A name with any other word
# (a person, a record number, a place) is replaced by its position: there is no list of names
# to miss, only a list of ordinary words.
SAFE_LABEL_WORDS_EN = frozenset("""
data dataset datasets export exported cohort clean cleaned raw final merged merge baseline followup follow up fu
visit visits lab labs test tests sample samples table tables sheet sheets analysis study trial patients patient
subjects subject records record survey registry db database file files v ver version new old copy backup all
total summary deid deidentified anon anonymized anonymised input output example demo template master main page
info readme dictionary codebook notes demographics outcome outcomes events imaging pathology surgery ct mri pet
ecg gbk utf utf8 csv xlsx tsv txt part round wave phase arm group groups control case cases pilot train training
valid validation external internal set center centre site sites multi single day week month year crf ehr emr
redcap spss stata sas long wide format updated latest draft clinical cancer tumor tumour stone kidney bladder
lung liver breast gastric heart blood urine serum plasma cell cells gene genes rna dna seq omics genomics
sheet1 sheet2 sheet3 tab tabs list lists log logs for and of the to by with in on at x y
my our prostate colon colorectal rectal stomach esophageal pancreas pancreatic renal thyroid brain stroke cardiac
diabetes diabetic hypertension sepsis covid icu ward inpatient outpatient admission admissions discharge readmission
mortality survival recurrence relapse response toxicity adverse events complications biopsy tissue specimen specimens
biomarker biomarkers genomic genomics radiology radiomics ultrasound xray endoscopy pathology histology cytology
medication medications drug drugs dose doses therapy treatment treatments chemo radiotherapy operation operations
score scores scale scales questionnaire questionnaires item items wide long merged combined subset sample sampled
""".split())
SAFE_LABEL_WORDS_CN = frozenset("""
数据 资料 导出 随访 基线 原始 清洗 清洁 汇总 合并 最终 终版 版 表 总表 明细 病例 化验 检验 检查 结果 队列 研究 项目
统计 分析 副本 备份 说明 字典 数据字典 实验室 影像 病理 手术 用药 患者 门诊 住院 出院 入院 基本 信息 基本信息 登记 记录
入组 筛选 第 批 次 期 组 中心 多中心 试验 临床 样本 示例 模板 新 旧 去标识 脱敏 年 月 日 工作表 主表 附表 一 二 三 四
五 六 七 八 九 十 上 下 前 后 术前 术后 复查 实验 对照 治疗 干预 问卷 调查 量表 生化 血常规 尿常规 并发症 结局 生存 预后
全部 部分 测试 单中心 单因素 单变量 列表 目录 代码 编码 变量 指标 用 的 和 与 及 数 据 库 数据库 文件 表格 汇总表 总 分 例 名单 清单
""".split())
_SAFE_CN_LIST = sorted(SAFE_LABEL_WORDS_CN, key=len, reverse=True)


# ─── small helpers ──────────────────────────────────────────────────────────

def _r(x, sig=10):
    """Round to `sig` significant digits and return a plain float (JSON friendly)."""
    return None if x is None else float(f"{float(x):.{sig}g}")


def _fmt_num(v):
    v = float(v)
    return str(int(v)) if v.is_integer() and abs(v) < 1e15 else f"{v:.10g}"


def _nfkc(s):
    """NFKC, the minus sign U+2212 read as '-', outer spaces stripped."""
    return _nfkc_str(s if isinstance(s, str) else str(s))


@functools.lru_cache(maxsize=1 << 18)
def _nfkc_str(s):
    if _SUPERSCRIPT_RE.search(s):            # "×10⁹/L" -> "×10^9/L" (NFKC alone gives "×109/L")
        s = _SUPERSCRIPT_RE.sub(lambda m: "^" + m.group().translate(_SUPERSCRIPTS), s)
    return unicodedata.normalize("NFKC", s).replace("\u2212", "-").strip()


@functools.lru_cache(maxsize=1 << 18)
def _fold(s):
    """A value as spellings are compared: NFKC, lower case, runs of spaces as one space."""
    return re.sub(r"\s+", " ", _nfkc(s).lower())


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


def _name_forms(name):
    """(low, compact): the column name in NFKC lower case with runs of spaces as one space, and the
    same without any space or separator ("出 生 日 期" -> 出生日期, "D-O-B" -> dob)."""
    low = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(name)[:MAX_NAME_RULE_LEN]).lower()).strip()
    compact = re.sub(r"[\s_\-.·/()（）:：,，、\[\]【】]+", "", low)
    return low, compact


def _is_cluster_name(name):
    name = str(name)[:MAX_NAME_RULE_LEN]
    if _is_pii_name(name):
        return False
    tokens = set(re.findall(r"[a-z]+", name.lower()))
    if tokens & CLUSTER_TOKENS and not (tokens - CLUSTER_TOKENS - CLUSTER_QUALIFIERS):
        return True
    return bool(CLUSTER_NAME_RE.match(name.strip()))


def _is_person_role_name(name):
    """A column of people who are not patients (术者, 主治, 读片医生, surgeon)."""
    return bool(PERSON_ROLE_RE.search(unicodedata.normalize("NFKC", str(name)[:MAX_NAME_RULE_LEN])))


def _is_patient_id_name(name):
    low, compact = _name_forms(name)
    return bool(PATIENT_ID_NAME_RE.search(low) or PATIENT_ID_NAME_RE.search(compact))


def _is_id_name(name):
    name = str(name)[:MAX_NAME_RULE_LEN]
    low, _ = _name_forms(name)
    return (any(rx.search(name) for rx in ID_NAME_RES) or _is_patient_id_name(name)) and not _is_cluster_name(name) \
        and not low.startswith("unnamed:")


def _pii_name_kind(name):
    """'record' / 'person' / 'birth' / 'contact' when the column name says it holds personal
    information, else None. Checked on the name and on its compact form (no spaces / separators)."""
    low, compact = _name_forms(name)
    tokens = set(re.findall(r"[a-z]+", low))
    if any(s in low or s.replace(" ", "") in compact for s in PII_RECORD_SUBSTR) or tokens & PII_RECORD_TOKENS \
            or RECORD_HEADER_RE.match(low):
        return "record"
    if BIRTH_NAME_RE.search(low) or BIRTH_COMPACT_RE.match(compact):
        return "birth"
    if any(s in compact for s in PII_PERSON_SUBSTR) or tokens & PII_PERSON_TOKENS or NAME_HEADER_RE.match(low) \
            or NAME_HEADER_RE.match(compact):
        return "person"
    if any(s in low or s.replace(" ", "") in compact for s in PII_CONTACT_SUBSTR) or tokens & PII_CONTACT_TOKENS \
            or HOME_CONTACT_RE.match(low):
        return "contact"
    return None


def _pii_name_word(name):
    """The word of a column name that makes it a privacy column ("居住", "联系人", "dob"), for the report."""
    low, compact = _name_forms(name)
    tokens = set(re.findall(r"[a-z]+", low))
    for sub in PII_RECORD_SUBSTR + PII_PERSON_SUBSTR + PII_CONTACT_SUBSTR:
        if sub in low or sub.replace(" ", "") in compact:
            return sub
    hit = tokens & (PII_RECORD_TOKENS | PII_PERSON_TOKENS | PII_CONTACT_TOKENS)
    if hit:
        return sorted(hit)[0]
    m = BIRTH_NAME_RE.search(low)
    return (m.group(0).strip(" _-.") if m else None) or ("home" if HOME_CONTACT_RE.match(low) else None) or _disp(name)[:20]


def _is_pii_name(name):
    return _pii_name_kind(name) is not None


# names do not end in an institution, place or category word ("中山医院", "金华市", "黄山区", "高血压病")
_NOT_NAME_END_RE = re.compile(r"[院学路街市区县省镇乡村站厂所科部楼场馆局处室店司队组班号期型级类性病癌炎症瘤剂片药]$")


# the other East-Asian encodings a CSV's text is also read in by the name rules: ((codec of the file, (alt codec,
# language), ...)) or () -- set by profile_dataframe from the source's codec. A Korean name in a Korean file read
# as GBK is three random Chinese characters, no name shape, but its bytes are still the name.
_CROSS_READINGS = ()


def _cross_readings(codec):
    fam = _EA_FAMILY_OF.get(codec or "")
    alts = {"zh": (("cp949", "ko"), ("cp932", "ja"), ("euc_jp", "ja")), "big5": (("gbk", "zh"), ("cp949", "ko"), ("cp932", "ja")),
            "ko": (("gbk", "zh"), ("cp932", "ja"), ("euc_jp", "ja")), "sjis": (("gbk", "zh"), ("cp949", "ko")),
            "eucjp": (("gbk", "zh"), ("cp949", "ko"))}.get(fam)
    return (codec, alts) if alts else ()


@functools.lru_cache(maxsize=65536)
def _cross_name(s, readings):
    """`s` (a value of a file in readings[0]) read in another of its East-Asian encodings is a personal name of a strong
    shape: a Korean name of a common surname and frequent syllables ("김민수"), a Chinese one (_name_kind), a Japanese
    one of a known surname ("佐藤花子")."""
    codec, alts = readings
    try:
        b = s.encode(codec)
    except UnicodeEncodeError:
        return False
    hangul = _ea_tables()[1]
    for alt, lang in alts:
        try:
            t = b.decode(alt).strip()
        except UnicodeDecodeError:
            continue
        if t == s or not t:
            continue
        if lang == "ko" and HANGUL_NAME_RE.match(t) and t[0] in KR_SURNAMES and all(ch in hangul for ch in t[1:]) and \
                t[-1] not in KR_TERM_END:
            return True
        if lang == "zh" and re.fullmatch(r"[一-鿿]{2,4}", t) and _name_kind_own(t) == "strong":
            return True
        if lang == "ja" and re.fullmatch(r"[一-鿿぀-ヿ]{3,5}", t) and t[:2] in JP_SURNAMES:
            return True
    return False


def _name_kind(s, loose=False):
    """_name_kind_own; and "strong" for a value of a Chinese / Korean / Japanese CSV that is such a name when its bytes
    are read in another of these encodings (_cross_name)."""
    if _CROSS_READINGS and s and not s.isascii() and len(s) <= 12 and _cross_name(s, _CROSS_READINGS):
        return "strong"
    return _name_kind_own(s, loose)


def _name_kind_own(s, loose=False):
    """None, "weak" or "strong": how much one value looks like a personal name.

    strong: a 3-character Chinese name of a common surname and common given-name characters, a compound
    surname, a masked name ("张*", "李某某"), a name with a title ("张伟先生", "王芳(女)"), a dotted
    transliteration ("买买提·艾力"), a Tibetan name of 2+ syllables ("扎西多吉"), a Japanese ("佐藤花子") or
    Korean ("김민준") name, a pinyin name ("ZHANG Wei", "ZhangWei", "zhang wei") or a Western name with a
    common given name ("John Smith", "José García", "mary jones").
    weak: other shapes of a name -- 2 Chinese characters after a surname ("张力" may be a word), two
    capitalised words ("Stevens Johnson" may be an eponym), "Smith J", a lone given name ("Mary").
    Never when a word makes it a place, institution or category ("New Zealand", "Mayo Clinic").
    loose (a single label such as a sheet name): initials count as strong ("J Smith")."""
    s = _nfkc(s)
    if not s or len(s) > 60:
        return None
    if re.search(r"[一-鿿]", s):
        t = CN_TITLE_SUFFIX_RE.sub("", s).strip()
        if t != s:
            return "strong" if t and _name_kind(t, loose) else None
        if " " in s and re.fullmatch(r"[一-鿿]{1,3}(?: +[一-鿿]{1,3})+", s) and len(s.replace(" ", "")) <= 4:
            s = s.replace(" ", "")                     # "张 伟", "王　芳" (NFKC: full-width space -> space)
        if DOT_NAME_RE.match(s):
            return "strong"
        if _TIB_RE.match(s):
            return "strong" if len(s) >= 4 else "weak"
        if not CN_NAME_RE.match(s) or (_NOT_NAME_END_RE.search(s) and not CN_MASKED_RE.match(s)):
            return None
        if CN_MASKED_RE.match(s) or re.search(r"[*＊×某]", s) or s[:2] in CN_COMPOUND_SURNAMES:
            return "strong"
        if s[:2] in JP_SURNAMES and len(s) >= 3:
            return "strong"
        if len(s) <= 3 and s[0] in CN_SURNAMES:
            if len(s) == 3 and _cn_given_common(s):
                return "strong"
            # a character of clinical words that is no given-name character: "高血压", "白细胞", "黄体酮" are no names
            return None if any(ch in CN_TERM_CHARS and ch not in CN_GIVEN_CHARS for ch in s[1:]) else "weak"
        return None
    if HANGUL_NAME_RE.match(s):
        # ("고혈압" hypertension, "당뇨병", "위암": a clinical word ending, not a given name)
        return "strong" if s[0] in KR_SURNAMES and s[-1] not in KR_TERM_END else None
    if CAPS_COMMA_NAME_RE.match(s):
        return "strong"
    words = re.findall(r"[^\W\d_]+", s.lower())
    if any(w in NON_NAME_WORDS for w in words) or " ".join(words) in NOT_PERSON_PHRASES:
        return None
    first = any(w in FIRST_NAMES for w in words)
    if not first and any(w in MEDICAL_WORDS for w in words):
        return None                                     # "Heart Rate", "Child Pugh", "Smoking Status"
    m = CAPS_NAME_RE.match(s)
    if m and any(p.isupper() and p.lower() in PINYIN_SURNAMES for p in (m.group("a"), m.group("b"))):
        return "strong"
    m = PINYIN_CAMEL_RE.match(s)
    if m and ((m.group(1).lower() in PINYIN_SURNAMES and PINYIN_GIVEN_RE.match(m.group(2).lower()))
              or (m.group(2).lower() in PINYIN_SURNAMES and PINYIN_GIVEN_RE.match(m.group(1).lower()))):
        return "strong"
    if re.fullmatch(rf"[a-z{_LAT_LO}]+ [a-z{_LAT_LO}]+", s):     # all lower case: pinyin or a known given name
        a, b = s.split()
        if (a in PINYIN_SURNAMES and PINYIN_GIVEN_RE.match(b)) or (b in PINYIN_SURNAMES and PINYIN_GIVEN_RE.match(a)) or first:
            return "strong"
        return None
    if WESTERN_NAME_RE.match(s):
        return "strong" if first else "weak"
    if INITIAL_NAME_RE.match(s):
        return "strong" if loose else "weak"
    if re.fullmatch(rf"[A-Z{_LAT_UP}][a-z{_LAT_LO}]+", s) and first:
        return "weak"
    return None


def _name_shaped(s, loose=False):
    """One value shaped like a personal name (see _name_kind)."""
    return _name_kind(s, loose) is not None


def _cn_given_common(s):
    """The given name of a Chinese name-shaped value is made of common given-name characters."""
    given = s[2:] if s[:2] in CN_COMPOUND_SURNAMES else s[1:]
    return bool(given) and all(ch in CN_GIVEN_CHARS for ch in given)


def _names_column(values, min_distinct=5):
    """True when (almost) every one of >= 5 different values is shaped like a personal name, they
    do not share a first or last word / character, as categories do ("高血压 / 高血脂 / 高尿酸",
    "Left Lobe / Right Lobe"), and most Chinese ones have a given name of common given-name
    characters (not "黄芪 / 白术 / 陈皮"). Masked names ("张*", "李某某") share only their mask."""
    vals = [v for v in {_nfkc(v) for v in values} if v]
    hits = [v for v in vals if _name_shaped(v)]
    if len(vals) < min_distinct or not hits or len(hits) < 0.8 * len(vals):
        return False
    cn = [v for v in hits if not re.search(r"[A-Za-z]", v) and not re.search(r"[*＊×xX某]", v)]
    personal = lambda v: _cn_given_common(v) or _name_kind(v) == "strong"
    if len(hits) < 3:
        return all(personal(v) for v in cn)
    words = [re.split(r"[\s,]+", v) if re.search(r"[A-Za-z]", v) else [v[0], v if CN_MASKED_RE.match(v) else v[-1]]
             for v in hits]
    firsts = collections.Counter(w[0] for w in words)
    lasts = collections.Counter(w[-1] for w in words)
    return max(firsts.values()) <= 0.5 * len(hits) and max(lasts.values()) <= 0.5 * len(hits) and \
        sum(1 for v in cn if personal(v)) >= 0.5 * len(cn)


def _mentions_person(s, strict=False):
    """A personal name inside free text: after a role word ("患者刘洋拒绝随访", "家属李娜代签") or a title
    ("Mr Smith refused"); unless strict, also a dotted transliteration or a Tibetan name of 2+ syllables
    ("转院 扎西多吉家属陪同"), or a given name and a surname ("死亡 José García")."""
    s = _nfkc(s)[:MAX_SCAN_LEN]
    if HONORIFIC_NAME_RE.search(s):
        return True
    for m in CN_ROLE_NAME_RE.finditer(s):
        g = m.group(1)
        if g[0] == "于":                       # "患者于明日出院": a preposition, not the surname 于
            continue
        if g[:2] in CN_COMPOUND_SURNAMES or (g[0] in CN_SURNAMES and (g[1] in CN_GIVEN_CHARS or g[1] == "某")):
            return True
    if strict:
        return False
    return bool(_DOT_IN_TEXT_RE.search(s) or _TIB_IN_TEXT_RE.search(s)) or \
        any(m.group(1).lower() in FIRST_NAMES for m in _WEST_IN_TEXT_RE.finditer(s))


def _record_code(s):
    """A record / specimen number: one to five parts of letters and digits ("ZY2023001", "S-123456",
    "ZY-2023-01000", "HN 482910", "MR/23000", "560000-1", "B23-12345") with a run of 5+ digits, at
    most 6 letters, not a date or a decimal number."""
    s = _nfkc(s)
    if len(s) > 32 or not RECORD_PARTS_RE.match(s) or not re.search(r"[0-9]{5}", s):
        return False
    if sum(ch.isalpha() for ch in s) > 6 or PLAIN_NUM_RE.match(s) or DATE_SHAPE_RE.match(s):
        return False
    return not NOT_RECORD_RE.match(s)


_DIGIT_RUN_RE = re.compile(r"[0-9]+")
_YEAR_RANGE_RE = re.compile(r"(?:19|20)[0-9]{2}\s*[-_~/–—]\s*(?:19|20)[0-9]{2}")


def _digit_groups_7(s):
    """Digits that, with only separators between them, make 7 or more: a phone, ID card or record
    number written in groups ("138 0013 1005", "ZY-2023-0412", "1980 01 01", "100–1234", "100,1234",
    "100#1234", "100、1234", "100|1234", "100    1234", zero-width characters, "100x1234", "100号1234") --
    any 1-4 characters that are no letter / digit, or one letter / CJK character between groups of 3+
    digits; not a year range ("2019-2020")."""
    t = unicodedata.normalize("NFKC", "".join(ch for ch in str(s)[:1000] if unicodedata.category(ch) != "Cf"))
    runs = [(m.start(), m.end()) for m in _DIGIT_RUN_RE.finditer(t)]
    i = 0
    while i < len(runs):
        j, total = i, runs[i][1] - runs[i][0]
        while j + 1 < len(runs):
            gap = t[runs[j][1]:runs[j + 1][0]]
            plain = 1 <= len(gap) <= 4 and not any(ch.isalnum() for ch in gap)
            letter = len(gap) == 1 and gap.isalpha() and runs[j][1] - runs[j][0] >= 3 and runs[j + 1][1] - runs[j + 1][0] >= 3
            if not (plain or letter):
                break
            j += 1
            total += runs[j][1] - runs[j][0]
        if total >= 7 and not _YEAR_RANGE_RE.fullmatch(t[runs[i][0]:runs[j][1]]):
            return True
        i = j + 1
    return False


def _contact_hits(s):
    """(ID card, phone) patterns in one value, also with spaces / hyphens / dashes between the digits,
    a country code before a mobile number, or a 7-8 digit number after a phone word ("家里电话 62345678")."""
    s = _nfkc(s)[:MAX_SCAN_LEN]
    n_dig = sum(1 for ch in s if "0" <= ch <= "9")
    if n_dig < 7:
        return False, False
    c = DIGIT_GAP_RE.sub("", s)
    idc = n_dig >= 15 and bool(ID_CARD_RE.search(c))
    ph = (n_dig >= 10 and bool(MOBILE_RE.search(c) or LANDLINE_RE.search(c))) or bool(CONTEXT_PHONE_RE.search(s))
    return idc, ph


def _has_identifier(s):
    """A value that must never be printed: an ID card, phone number, e-mail address or messaging account
    in it, a person named in it -- or a cell too long to check."""
    s = str(s)
    if len(s) > MAX_SCAN_LEN:
        return True
    idc, ph = _contact_hits(s)
    return idc or ph or ("@" in s and bool(EMAIL_RE.search(s))) or bool(CONTEXT_ACCOUNT_RE.search(_nfkc(s))) \
        or _mentions_person(s)


# words around a name in a sheet label: "患者张三", "张三术后", "李四资料"
SHEET_AFFIX_RE = re.compile(r"^(?:患者|病人|受试者|受检者|姓名)+|(?:术后|术前|随访|复查|资料|数据|记录|病历|病例|化验|检验|检查|"
                            r"报告|入院|出院|住院|门诊)+$")


# a patient's own number in a label: "patient 0042", "case 12", "患者12", "第3例" -- one sheet per patient
PATIENT_LABEL_RE = re.compile(r"(?:patient|pt|case|subject|subj|患者|病人|病例|受试者|例)[\s_\-#.]*[0-9]{1,6}(?![0-9])"
                              r"|第[0-9一二三四五六七八九十]+例", re.IGNORECASE)


def _identifier_text(s):
    """A single string (a sheet name) that may be someone's name, record number or contact data --
    also inside a longer label ("张三-术后", "001张三", "患者张三", "张三(2023)", "J Smith")."""
    s = _nfkc(s)[:200]
    if ID_CARD_RE.search(s) or MOBILE_RE.search(s) or ("@" in s and EMAIL_RE.search(s)) or _digit_groups_7(s) \
            or ADDRESS_RE.search(s) or re.search(r"[0-9]{5,}", s) or _name_shaped(s, loose=True) or PATIENT_LABEL_RE.search(s):
        return True
    for part in re.findall(r"[一-鿿*＊×某]+", s):
        part = SHEET_AFFIX_RE.sub("", part)
        if 2 <= len(part) <= 3 and _name_shaped(part):
            return True
    latin = [p.strip() for p in re.split(r"[_\-()（）\[\]0-9]+", s) if p.strip()]
    return any(_name_shaped(p, loose=True) for p in latin + [" ".join(latin)])


def _safe_label_text(s):
    """True when a file / sheet name is made only of ordinary words (SAFE_LABEL_WORDS_*), numbers of
    at most 4 digits and single letters, and does not look like an identifier -- then it may be
    printed."""
    if _identifier_text(s):
        return False
    s = unicodedata.normalize("NFKC", str(s)).lower().strip()
    if not s or len(s) > 80:
        return False
    toks = re.findall(r"[a-z]+|[0-9]+|[一-鿿]+|[^\sa-z0-9一-鿿]", s)
    letters = [t for t in toks if re.fullmatch(r"[a-z]+", t)]
    if len(letters) >= 2 and all(len(t) == 1 for t in letters):
        return False                                   # initials ("x y", "J S")
    # "第五一": 第 + numerals without a counter word may be the surname 第五 and a given name
    if re.search(r"第[一二三四五六七八九十]{2,}(?![批次期组轮周月年天日版部阶例])", s):
        return False
    for tok in toks:
        if tok.isdigit():
            if len(tok) > 4:
                return False
        elif re.fullmatch(r"[a-z]+", tok):
            if len(tok) > 1 and tok not in SAFE_LABEL_WORDS_EN:
                return False
        elif re.fullmatch(r"[一-鿿]+", tok):
            i = 0
            while i < len(tok):
                w = next((w for w in _SAFE_CN_LIST if tok.startswith(w, i)), None)
                if w is None:
                    return False
                i += len(w)
        elif tok not in "_-.()（）[]【】#&+,，、 ":
            return False
    return True


def _file_label(path):
    """The data file's name as it may be printed: as written when made of ordinary words."""
    base = os.path.basename(str(path))
    stem, ext = os.path.splitext(base)
    return base if _safe_label_text(stem) else f"（文件名不显示，可能含个人信息）{ext}"


def _fail(msg):
    """CLI error: one line on stderr, exit status 2 (never a traceback)."""
    print("[数据体检] " + str(msg).replace("\r", " ").replace("\n", " "), file=sys.stderr)
    raise SystemExit(2)


class _Vocab:
    """Missing-value vocabulary: text tokens (normalised), numeric codes, ambiguous tokens.
    user_codes: numbers the user added for every column; forced_codes: numbers added for this column."""

    def __init__(self, extra_tokens=(), column_tokens=()):
        self.text, self.codes, self.default_codes = set(), set(), set()
        self.user_codes, self.forced_codes = set(), set()
        user = set()
        for tok in DEFAULT_MISSING_TOKENS:
            t = _nfkc(tok)
            if PLAIN_NUM_RE.match(t):
                self.default_codes.add(float(t))
            else:
                self.text.add(t.lower())
        for tok, forced in [(t, False) for t in extra_tokens] + [(t, True) for t in column_tokens]:
            t = _nfkc(tok)
            user.add(t.lower())
            if PLAIN_NUM_RE.match(t):
                (self.forced_codes if forced else self.user_codes).add(float(t))
            else:
                self.text.add(t.lower())
        self.codes = self.default_codes | self.user_codes | self.forced_codes
        # a token the user added explicitly always means "missing"
        self.ambiguous = {a for a in AMBIGUOUS_TOKENS if a in self.text and a not in user}
        self.extra = [str(t) for t in extra_tokens]


# ─── reading (never writes) ─────────────────────────────────────────────────

def _sniff_sep(text, skip_rows=0):
    """The separator that splits most of the first lines (after --skip-rows) into the same number of
    fields: a title line above tab data, or commas inside tab-separated labels, do not decide it."""
    lines = [ln for ln in text.split("\n")[skip_rows:skip_rows + 80] if ln.strip()][:50]
    best, best_score = ",", (0, 0)
    for s in ("\t", ";", "|", ","):
        counts = [ln.count(s) for ln in lines]
        nonzero = [c for c in counts if c]
        if not nonzero:
            continue
        mode, _ = collections.Counter(nonzero).most_common(1)[0]
        score = (sum(1 for c in counts if c == mode), mode)
        if score > best_score:
            best, best_score = s, score
    return best


def load_table(path, sheet=None, encoding=None, sep=None, header=None, skip_rows=0):
    """Read CSV / TSV / TXT / XLSX keeping every value exactly as written. Never writes.

    Returns (df, meta). CSV cells are str ('' = empty cell); XLSX cells keep Excel's own
    type (int / float / datetime / str), so numbers typed as text can be detected.
    CSV encodings tried in order: utf-8 (with or without BOM), gbk, gb18030 (UTF-16 when the file
    starts with a UTF-16 BOM). A GBK result that looks like a Western file decoded wrongly
    (cp1252 / latin-1: "µmol" -> "祄ol", "Müller") is flagged in meta["encoding_warning"].
    header     None = first row is the header unless it looks like data (numbers, dates, an ID
               card or phone number) -- then columns are named 列1, 列2 ... and the row is kept
               as data; True / False force it.
    skip_rows  rows to skip before the header (e.g. a merged title row in a Chinese export).
    Rows that are completely blank are dropped and counted in meta["n_blank_rows"].
    meta["file"] / meta["sheet"] are printable labels: a name that is not made of ordinary words
    is replaced (see _safe_label_text).
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
    meta = {"file": _file_label(path), "file_shown": _safe_label_text(os.path.splitext(os.path.basename(path))[0]),
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if ext in EXCEL_EXTS:
        return _load_excel(raw, ext, sheet, meta, header, skip_rows)
    return _load_csv(raw, ext, encoding, sep, meta, header, skip_rows)


def _is_blank(v):
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return isinstance(v, str) and not v.strip()


def _measured(v):
    """A body cell that holds a number, a date, a censored value or a number with unit / flag."""
    if isinstance(v, (int, float, _dt.date)) and not isinstance(v, bool):
        return True
    s = _nfkc(v)
    if len(s) > MAX_MEASURE_LEN:
        return False
    return bool(PLAIN_NUM_RE.match(s) or CENSORED_RE.match(s) or CENSORED_SUFFIX_RE.match(s) or _with_unit(s)
                or FLAG_RE.match(s) or THOUSANDS_RE.match(s) or SPACE_THOUSANDS_RE.match(s) or APPROX_RE.match(s)
                or QMARK_RE.match(s) or _parse_date(s) or COMPOUND_RE.match(s) or _qualified_number(s))


MISSING_LOWER = frozenset(_nfkc(t).lower() for t in DEFAULT_MISSING_TOKENS)
# answers that negate the column's own name: "复发" over 复发 / 未复发, "Death" over Death / Alive
NEGATION_WORDS = frozenset({"否", "无", "不", "未", "非", "没有", "no", "n", "none", "non", "not", "negative", "neg",
                            "alive", "absent", "false", "0", "存活", "生存", "健在", "阴性", "正常"})


def _shape_sig(s):
    """The character classes of a value (CJK, upper, lower, digit, space, other)."""
    return (bool(re.search(r"[一-鿿]", s)), bool(re.search(r"[A-Z]", s)), bool(re.search(r"[a-z]", s)),
            bool(re.search(r"[0-9]", s)), " " in s, bool(re.search(r"[^\w\s]", s)))


def _header_word(h):
    """A first-row cell that reads like a column name."""
    h = str(h)[:MAX_NAME_RULE_LEN]
    return _is_pii_name(h) or _is_id_name(h) or _is_cluster_name(h) or bool(DATE_NAME_RE.search(h)) \
        or bool(REMARK_NAME_RE.search(h))


_FIVE_DIGITS_RE = re.compile(r"[0-9]{5}")
_DIGIT_RE = re.compile(r"[0-9]")


def _header_looks_like_data(cells, body=()):
    """True when the first row looks like a data row rather than column names.

    Without rows below it: numbers / dates in most cells (not just years), or an ID card / phone
    number. With rows below (body), each first-row cell is held against its column. Data: a number
    above numbers, a personal name / address / record number above more of them, a value that
    recurs below as one of the column's categories ("男" over 男 / 女, "肺癌" over several
    diagnoses), or a value shaped like the others of a column of (nearly) all-different values.
    A column name: a label above numbers or codes, above a few repeated values it is not one of
    ("性别" over 男 / 女), a known column word (姓名, 住院号 ...), or a word over its own yes / no
    column ("复发" over 复发 / 未复发, "Smoker" over Smoker / Non-smoker, "Death" over Death /
    Alive) -- which is how dummy columns are named. The first row is data when the data evidence
    outweighs the column-name evidence. Rows that repeat the first row (several exports pasted
    together) are left out."""
    vals = [_nfkc(c)[:MAX_SCAN_LEN] for c in cells if not _is_blank(c)]
    if not vals:
        return False
    if any(_contact_hits(v)[0] or MOBILE_RE.search(v) for v in vals):
        return True
    if _transposed_header(cells, body):
        return False                               # patients' record numbers over their columns: column names
    datalike = [v for v in vals if PLAIN_NUM_RE.match(v) or _parse_date(v)]
    years = [v for v in datalike if re.fullmatch(r"(?:19|20)[0-9]{2}", v)]   # "2019, 2020" year columns
    by_cells = len(datalike) >= 2 and len(datalike) >= 0.5 * len(vals) and len(years) < len(datalike)
    norm = lambda row: ["" if _is_blank(c) else _nfkc(c)[:MAX_SCAN_LEN] for c in row]
    first = norm(cells)
    body = [r for r in body if norm(r[:len(first)]) != first]
    if not body:
        return by_cells
    data_ev = header_votes = 0
    for j, h in enumerate(first):
        below = [r[j] for r in body if j < len(r) and not _is_blank(r[j])]
        if not h or not below or h.lower() in MISSING_LOWER:     # "未查" in the first row says nothing
            continue
        measured = sum(1 for v in below if _measured(v)) / len(below)
        texts = collections.Counter(_nfkc(v)[:300] for v in below)
        folded = {t.lower() for t in texts}
        share = lambda rx: sum(1 for v in texts if rx.search(v)) / len(texts)
        if _parse_date(h) and not PLAIN_NUM_RE.match(h):
            # a date over dates is a data row; over numbers it names a time point ("2023-01-01", "2023年1月1日")
            dated = sum(1 for v in below if isinstance(v, _dt.date) or (isinstance(v, str) and _parse_date(_nfkc(v)[:60]))) / len(below)
            if dated >= 0.5:
                data_ev += 1
            elif measured >= 0.8:
                header_votes += 1
            continue
        if PLAIN_NUM_RE.match(h):
            if measured >= 0.5 and len(years) < len(datalike):
                data_ev += 1
            continue
        if measured >= 0.8:
            header_votes += 1                      # a label above a column of numbers
            continue
        if (_name_shaped(h) and _names_column(texts)) or (_record_code(h) and share(_FIVE_DIGITS_RE) >= 0.5) or \
                (ADDRESS_RE.search(h[:300]) and share(ADDRESS_RE) >= 0.5):
            data_ev += 1                           # an identifier above more of them
            continue
        if h.lower() in folded:
            others = [t for t in folded if t != h.lower()]
            dummy = bool(others) and all(h.lower() in t or t in NEGATION_WORDS for t in others)
            if dummy:
                header_votes += 0.5                # a dummy column named after its own "yes" value
            else:
                data_ev += 1                       # one of the column's categories
            continue
        if _header_word(h):
            header_votes += 1
            continue
        if not re.search(r"[0-9]", h) and share(_DIGIT_RE) >= 0.8:
            header_votes += 1                      # "pid" above P001, P002 ...
        elif len(texts) >= 5 and len(texts) >= 0.8 * len(below):
            sigs = collections.Counter(_shape_sig(t) for t in texts)
            sig, n_sig = sigs.most_common(1)[0]
            if _shape_sig(h) == sig and n_sig >= 0.6 * len(texts) and abs(len(h) - np.median([len(t) for t in texts])) <= 3:
                data_ev += 1                       # one more of a column of all-different values
        elif len(texts) <= 20 and len(below) >= 2 * len(texts):
            header_votes += 1                      # "性别" above 男 / 女
    data = data_ev >= 1 and data_ev > header_votes
    return data or (by_cells and header_votes == 0)


def _row_labels_column(values):
    """The first column of a transposed table: 3+ different labels (variable names) -- no numbers or dates,
    no personal names, no patient codes (P001, ZY2023001)."""
    vals = [_nfkc(v)[:100] for v in values if not _is_blank(v)]
    if len(vals) < 3 or len(set(vals)) < 0.9 * len(vals):
        return False
    if sum(1 for v in vals if _measured(v)) > 0.2 * len(vals) or _names_column(vals):
        return False
    return sum(1 for v in vals if CODE_VALUE_RE.match(v) or _record_code(v)) < 0.5 * len(vals)


def _patient_code_header(h):
    """A column name that is a patient's number: a record code, a number of 5+ digits ("100230", "000123")."""
    t = _nfkc(h)
    return _header_code(t) or _record_code(t) or bool(re.fullmatch(r"[0-9]{5,}", t))


def _transposed_header(cells, body):
    """The first row of a transposed table whose columns are patients named by their numbers ("项目, 100230,
    100231 ..."): the first cell a label (or blank), the other cells different record numbers / 5+ digit
    numbers; below it, row labels in the first column and numbers in the others."""
    vals = ["" if _is_blank(c) else _nfkc(c)[:100] for c in cells]
    rest = [v for v in vals[1:] if v]
    if len(rest) < 1 or len(set(rest)) < len(rest) or not body:
        return False
    if vals[0] and (_measured(vals[0]) or _header_person(vals[0]) or _patient_code_header(vals[0])):
        return False
    if not all(_patient_code_header(v) for v in rest) or not _row_labels_column([r[0] for r in body if r]):
        return False
    cells_ = [v for r in body for v in r[1:len(vals)] if not _is_blank(v)]
    return bool(cells_) and sum(1 for v in cells_ if _measured(v)) >= 0.5 * len(cells_)


def _decide_header(first_row, header, meta, body=()):
    """-> True if the first row is the header. Records the decision in meta."""
    if header is None:
        use = not _header_looks_like_data(first_row, body)
        meta["header_mode"] = "first-row" if use else "auto-none"
    else:
        use = bool(header)
        meta["header_mode"] = "first-row" if use else "none"
    return use


# a cell of a title row: "患者：张三", "住院号: 123", "XX医院检验报告", "化验单", "Lab report", "打印时间 ..."
_TITLE_KV_RE = re.compile(r"^[^:]{1,12}:\s*\S")
_TITLE_WORD_RE = re.compile(r"报告|化验单|检验单|检查单|报告单|病历|医院|科室|导出|打印|统计表|一览表|名单|清单|表格|"
                            r"report|hospital|printed|export", re.IGNORECASE)


def _title_cell(v):
    """A first-row cell that reads like (part of) a title, not a column name: 'label: value', a person or a
    record / phone number, a title word ("XX医院", "化验单", "Lab report"), a date, a long text."""
    t = _nfkc(v)[:200]
    return bool(_TITLE_KV_RE.match(t) or _TITLE_WORD_RE.search(t) or len(t) > 30 or re.search(r"[0-9]{5,}", t)) or \
        _header_identifier(t) or bool(_parse_date(t))


def _header_like_row(row, width):
    """A row that reads like column names: most columns named by short labels -- no numbers, dates or
    measurements, no title cell."""
    cells = [v for v in row if not _is_blank(v)]
    return len(cells) >= max(2, 0.5 * width) and all(not _measured(v) and not _title_cell(v) and len(_nfkc(v)) <= 30 for v in cells)


def _title_rows(rows):
    """How many leading rows hold only a title or a merged group header -> the --skip-rows hint. Such a row
    is never printed as column names (a title may name the patient: "患者：张三 住院号：…"). A title row:
    one or two non-empty cells over wider rows -- unless they are short labels over data (a header whose
    last column names are blank: "pid, age, , ") -- or up to four cells of which one reads like a title
    ("患者：张三", "住院号：…", "XX医院") above a row of column names."""
    rows = [list(r) for r in rows[:205]]
    filled = [sum(1 for v in r if not _is_blank(v)) for r in rows]
    if len(filled) < 3:
        return 0
    mode = collections.Counter(filled[1:]).most_common(1)[0][0]
    k = 0
    while k < min(5, len(filled) - 2) and mode >= 2:
        cells = [v for v in rows[k] if not _is_blank(v)]
        titled = any(_title_cell(v) for v in cells)
        above_header = _header_like_row(rows[k + 1], mode)
        if filled[k] <= 2 and filled[k] < mode and (titled or above_header or not _header_like_row(rows[k], filled[k] or 1)):
            k += 1
        elif 1 <= filled[k] <= 4 and titled and above_header:
            k += 1
        else:
            break
    return k


def _mask_title_header(columns, meta):
    """The header row is a title row: the columns are named by position (列1, 列2 ...), never by the
    title's words. -> the new column names."""
    meta["title_header_hidden"] = True
    meta["raw_header"] = [f"列{j + 1}" for j in range(len(columns))]
    return list(meta["raw_header"])


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
    # Some workbooks have one sheet per patient: only the chosen sheet's name may be printed, and
    # only when it is made of ordinary words; the others are counted.
    if sheet is None:
        index = 0
    elif str(sheet) in names:
        index = names.index(str(sheet))
    elif str(sheet).isdigit() and int(sheet) < len(names):
        index = int(sheet)
    else:
        shown = f" {str(sheet)!r}" if _safe_label_text(str(sheet)) else ""
        raise ValueError(f"找不到工作表{shown}；这个文件共 {len(names)} 个工作表（名称不显示），"
                         f"--sheet 写工作表名或从 0 开始的序号（0–{len(names) - 1}）")
    grid = pd.read_excel(book, sheet_name=names[index], header=None, dtype=object, na_filter=False, skiprows=skip_rows)
    keep = [i for i in range(len(grid)) if not all(_is_blank(v) for v in grid.iloc[i].tolist())]
    if not keep:
        if skip_rows:
            total = len(pd.read_excel(book, sheet_name=names[index], header=None, dtype=object, na_filter=False))
            raise ValueError(f"--skip-rows {skip_rows} 跳过了这个工作表的全部内容（共 {total} 行）；请改小 --skip-rows")
        raise ValueError("工作表是空的")
    first = keep[0]
    head = grid.iloc[first].tolist()
    use_header = _decide_header(head, header, meta, [grid.iloc[i].tolist() for i in keep[1:201]])
    raw_header = ["" if _is_blank(v) else str(v) for v in head] if use_header else []
    body_idx = [i for i in keep if i > first] if use_header else keep
    n_blank = (len(grid) - first - (1 if use_header else 0)) - len(body_idx)
    df = grid.iloc[body_idx].reset_index(drop=True)
    df.columns = _unique_names(raw_header) if use_header else [f"列{j + 1}" for j in range(grid.shape[1])]
    norm_head = [_nfkc(v) for v in head]
    label = names[index] if _safe_label_text(names[index]) else f"第 {index + 1} 个工作表（名称不显示）"
    meta.update(format="xlsx", sheet=label, sheet_index=index, n_sheets=len(names), raw_header=raw_header,
                n_blank_rows=n_blank, skip_rows=skip_rows,
                title_rows=_title_rows([grid.iloc[i].tolist() for i in keep[:205]]),
                n_header_copies=sum(1 for i in body_idx
                                    if use_header and [_nfkc(v) for v in grid.iloc[i].tolist()] == norm_head))
    if use_header and meta["title_rows"]:
        df.columns = _mask_title_header(df.columns, meta)
    return df, meta


def _gbk_mojibake(text):
    """-> set of characters that look like a Western (cp1252 / latin-1) file decoded as GBK.

    In such a file an accented byte (µ = B5, ü = FC, ° = B0) pairs with the ASCII byte after it into
    a rare GBK-extension character ("µm" -> 祄, "Mü" -> M黮), which then sits between ASCII
    characters; Chinese text uses the common GB2312 characters next to other Chinese characters.
    Suspicious when rare characters between ASCII ones make up half of the non-ASCII characters."""
    rare_by_latin, n_non_ascii, rare = 0, 0, set()
    for i, ch in enumerate(text):
        if ord(ch) < 0x80:
            continue
        n_non_ascii += 1
        try:
            b = ch.encode("gbk")
        except UnicodeEncodeError:
            continue
        if len(b) != 2 or (0xA1 <= b[0] <= 0xF7 and b[1] >= 0xA1):
            continue
        near = (i == 0 or text[i - 1].isascii()) and (i + 1 == len(text) or text[i + 1].isascii())
        if near:
            rare_by_latin += 1
            rare.add(ch)
    return rare if rare_by_latin >= 2 and rare_by_latin >= 0.5 * n_non_ascii else set()


def _cjk_common_share(text, enc):
    """How Chinese the characters of `text` read in `enc`: for GBK the share that are in GB2312 (a Big5 file
    read as GBK turns every character whose second byte is below 0x7F into a rare GBK-extension one); for
    Big5 the share in its block of frequent characters (A440-C67E)."""
    n = common = 0
    for ch in text[:200000]:
        if "\u4e00" <= ch <= "\u9fff":
            n += 1
            if enc in ("gbk", "gb18030"):
                try:
                    ch.encode("gb2312")
                    common += 1
                except UnicodeEncodeError:
                    pass
            else:
                try:
                    common += 0xA4 <= ch.encode("big5")[0] <= 0xC6
                except UnicodeEncodeError:
                    pass
    return common / n if n >= 20 else 1.0


def _guess_decode(raw):
    """-> (text, encoding, notes) for a file given without --encoding (no UTF-16 BOM). Chinese encodings win:
    UTF-8 (also with a few stray bytes from another encoding, replaced by �); else GBK -- or Big5 when its reading is
    clearly more of a text than GBK's (_better_reading), or GBK reads as rare characters and Big5 as common ones; else
    GB18030. A Korean or Japanese file is valid GBK / GB18030 almost always, and a Chinese file whose Chinese text is a
    few characters (男 / 女, 是 / 否, a few names) is valid EUC-KR / Shift-JIS just as often: such a file is read as
    Chinese, and _load_csv warns (and prints no text value) when the Korean / Japanese reading of the bytes is clearly
    the text. Only bytes that are no valid GB18030 are read as EUC-KR / Shift-JIS / EUC-JP, with a warning.
    (None, None, []) when nothing decodes."""
    try:
        return raw.decode("utf-8-sig"), "utf-8-sig", []
    except UnicodeDecodeError:
        pass
    loose = raw.decode("utf-8", errors="replace")
    n_bad = loose.count("\ufffd")
    n_multi = sum(1 for ch in loose if ord(ch) >= 0x80 and ch != "\ufffd")
    if 0 < n_bad <= 3 and n_multi >= 20 * n_bad:
        lines = []
        for i, ln in enumerate(raw.split(b"\n"), start=1):
            try:
                ln.decode("utf-8")
            except UnicodeDecodeError:
                lines.append(i)
        note = (f"文件按 UTF-8 解码，但第 {'、'.join(map(str, lines[:5]))} 行有 {n_bad} 个不是 UTF-8 的字节（可能是从别的软件"
                "粘贴进来的字符），已替换为 �；请在原文件里核对这几行")
        return loose.lstrip("\ufeff"), "utf-8-replace", [note]
    decoded = {}
    for enc in ("gbk", "big5", "gb18030"):
        try:
            decoded[enc] = raw.decode(enc)
        except UnicodeDecodeError:
            pass
    note = ["按 Big5（繁体中文）解码：按 GBK 解码时多是生僻字或无法解码；如果列名或取值显示不对，请用 --encoding 指定编码"]
    # Big5 text is words of several characters; a Western file read as Big5 / GBK has single characters
    # between Latin letters ("µmol" -> one character + "mol")
    words = lambda t: (lambda runs: sum(len(r) for r in runs if len(r) >= 2) / max(1, sum(len(r) for r in runs)))(
        re.findall(r"[\u4e00-\u9fff]+", t[:200000]))
    big5_ok = lambda th: "big5" in decoded and _cjk_common_share(decoded["big5"], "big5") >= th and words(decoded["big5"]) >= 0.5
    big5_better = lambda zh: "big5" in decoded and _better_reading(_ea_readings(raw), zh) == "big5"
    if "gbk" in decoded:
        if (_cjk_common_share(decoded["gbk"], "gbk") < 0.9 and big5_ok(0.9)) or big5_better("zh"):
            return decoded["big5"], "big5", note
        return decoded["gbk"], "gbk", []
    # not GBK: Big5 if it reads as common characters (a GB18030 file's 4-byte characters are no Big5)
    if big5_ok(0.8) or big5_better("zh"):
        return decoded["big5"], "big5", note
    if "gb18030" in decoded:
        return decoded["gb18030"], "gb18030", []
    return _japanese_korean(raw) or (None, None, [])


def _hangul(ch):
    return "가" <= ch <= "힣"


def _kana(ch):
    return "぀" <= ch <= "ヿ"


def _jis_common(ch):
    """A character common in Japanese text: kana, JIS level-1 kanji, Japanese punctuation."""
    if _kana(ch) or ch in "，。、・（）「」":
        return True
    try:
        return 0x88 <= ch.encode("cp932")[0] <= 0x98
    except UnicodeEncodeError:
        return False


# ── which reading of a file's bytes is text: the frequent characters of each language (simplified and traditional
# Chinese, Japanese kanji forms, Korean syllables) and the label / header words of its tables. Korean and Japanese
# bytes read as GBK give characters that lie anywhere in the character table -- mostly not frequent ones, and no cell
# that is a word; Chinese bytes read as EUC-KR give rare syllables. Only the presence of a character counts (each
# different character once), so a value on many rows weighs no more than one on a single row. ──
_HAN_FREQUENT = (
    "的一是不了人我在有他这中大来上国个到说们为子和你地出道也时年得就那要下以生会自着去之过家学对可她里后小么心多天而能好都然没日于起还发成事只作当想看文无开手十用主行方又如前所本见经头面公同三已老从动两长"
    "知民样现分将外但身些与高意进把法此实回二理美点月明其种声全工己话儿者向情部正名定女问力机给等几很业最间新什打便位因重被走电四第门相次东政海口使教西再平真听世气信北少关并内加化由却代军产入先山五太水万市"
    "眼体别处总才场师书比住员九笑性通目华报立马命张活难神数件安表原车白应路期叫死常提感金何更反合放做系计或司利受光王果亲界及今京务制解各任至清物台象记边共风战干接它许八特觉望直服毛林题建南度统色字请交爱让"
    "认算论百吃义科怎元社术结六功指思非流每青管夫连远资队跟带花快条院变联言权往展该领传近留红治决周保达办运武半候七必城父强步完革深区即求品士转量空甚众技轻程告江语英基派满式李息写呢识极令黄德收脸钱党倒未持"
    "取设始版双历越史商千片容研像找友孩站广改议形委早房音火际则首单据导影失拿网香似斯专石若兵弟谁校读志飞观争究包组造落视济喜离虽坐集编宝谈府拉黑且随格尽剑讲布杀微怕母调局根曾准团段终乐切级克精哪官示冷域类"
    "规确证存具罗击备质需价整况亚约复病线断支消器照须增称企吗乎查易除农装显吧阿标图念引医突费号另较注仅考选列响推势参希古构节土投某案维划敌致陈律足态护兴验责营星够章底严巴例防族供效续施型料答紧绝奇察依批群"
    "项故按河米围织害斗境客纪采举攻苏密低朝诉止细愿值仍男破热助育属帝限船职速刻否刚威状率独球般普弹苦创假久错承印晚兰试股脑预益阳尼继送急血惊伤素药适波夜省初卫源食险待述陆习置居劳财环排福纳欢雷警获模充负云"
    "停木游龙树疑层洲冲射略范竟句室异激汉村哈策演简卡罪判担州静退既衣您宗积余痛检差富灵协角占配征修皮挥胜降阶审沉坚善妈刘啊超免压银买皇养伊怀执副乱抗犯追帮宣佛岁航优怪著田铁控税左右份穿艺背阵草脚概恶块顿敢"
    "守酒岛托央户烈洋哥索胡款靠评座释景顾登货互付伯慢欧换闻危忙核暗姐介坏讨丽良序升监临亮露永呼味野架沙掉括舰鱼杂误湾吉减楚肯测败屋跑梦散温困渐封救贵枪缺楼县尚毫移娘朋画班智亦耳恩短掌恐遗固席松秘谢鲁遇康虑"
    "幸均销钟诗藏赶剧票损忽巨炮旧端探湖录叶春乡附吸予礼港雨呀板庭妇归睛饭额含顺输摇招婚脱补谓督毒油疗旅泽材灭逐莫笔亡鲜词圣择寻厂睡博勒烟授诺伦岸奥唐卖俄炸载洛健堂旁宫喝借君禁阴园谋宋避抓荣姑孙逃牙束跳顶玉"
    "镇雪午练迫爷篇肉嘴馆遍凡础洞卷坦牛宁纸诸训私庄祖丝翻暴森塔默握戏隐熟骨访弱蒙歌店鬼软典欲萨伙遭盘爸扩盖弄雄稳忘亿刺拥徒姆杨齐赛趣曲刀床迎冰虚玩析窗醒妻透购替塞努休虎扬途侵刑绿兄迅套贸毕唯谷轮库迹尤竞街"
    "促延震弃甲伟麻川申缓潜闪售灯针哲络抵朱埃抱鼓植纯夏忍页杰筑折郑贝尊吴秀混臣雅振染盛怒舞圆搞狂措姓残秋培迷诚宽宇猛摆梅毁伸摩盟末乃悲拍丁赵"
)
_HAN_CLINICAL = (
    "癌瘤炎症肺胃肝肾糖尿脂蛋酶胞淋浓诊剂龄饮侧径厚液肿码酐氨胆醇钾钠钙镁磷锌氯碱酸氧碳氮硫肌腺垂泌乳睾雌孕胰髓骼韧腱椎颈腰胸腹盆腔膀胱卵巢肠肛肤黏膜鼻喉咽齿舌唇咳嗽痰喘呕吐泻胀疼晕厥昏抽搐瘫痪乏瘦浮疸贫凝"
    "栓梗阻狭窄殖萎缩硬纤溃疡孔瘘疝囊粒嗜疫胎妊娠娩剖婴幼童壮痊愈疾盲慰瞻镜彩磁扫描秒尔滴瓶袋盒脉雾靶苗彝丧偶硕偏详符零壹贰叁肆伍柒捌玖拾乙丙戊庚辛壬癸丑寅卯辰巳酉戌亥"
)
_HAN_TRADITIONAL = (
    "與這們來為國個說時會對過後還發經種動長現兩實點將麼從當沒樣幾開體學問義讓認論話關門業應見頭進於無變給隊東車電書軍產間處題風飛機場員邊總條強歷氣議區號報導連運傳類質觀親資團術權際決結統選擊斷費確務離嗎轉"
    "戰華歡鐵醫療藥檢診壓腦腎臟腸膽脈癥癱瘓腫細紅鹽鈉鉀鈣鎂氫標記碼齡婦兒歲組驗隨訪復煙飲職狀況輸併態評慮鬱圍餐遊殘餘積別異陽陰輕癒歸縣鎮鄉級師範廣護淚灣側膚頸線縮擴張壞瘍屬樓雙歐廠戶濕燒熱寫瘡灶聲脹鬆癢膿"
    "嘔瀉痺擬廢斂瀕瘻臨誤證稱準數據圖單專編備註訊網設萬樂畫裡視則達許價愛調馬請該辦覺營卻較聯參帶舉陳裝約錢項臺黨眾規聽亞預濟買環製滿試續顯獲創須陸賽協遠習昨興極聞爭險雖藝園銀錄財戲領勢魚爾黃談適農紀係軟語"
    "優讀養銷識館獎維換簡購絕討夠構錯額採億講劇訴賣寶負媽課劃謝羅幫終傷獨牌龍貨擇擔彈練雜勞嚴檔麗顧吳執溫攝責緊繼測補筆僅剛訓漢壯喪碩貼內鋅鹼韌齒暈貧狹纖潰惡穩緩劑鏡層掃鐘昇納靜霧劉楊趙孫郭鄭韓馮鄧曹彭蕭蔣"
    "蔡賈葉閻蘇盧魏薛憂衰顫皰恢"
)
_HAN_JAPANESE = (
    "齢転帰検査薬円気図実圧剤価県駅楽様辺発応変広単続両対険脳軽塩悪歳巣徴験読団営栄衛縁桜渇巻関観歓穏仮偽戯拠挙峡響暁勤駆茎継経渓芸撃倹剣圏権献厳効恒済砕斎雑惨賛姉歯児辞湿釈寿収従渋獣縦粛処緒叙奨焼証乗剰壌"
    "嬢浄畳譲醸触嘱寝慎尋粋酔枢瀬斉窃摂専戦浅践銭禅荘捜挿僧総騒蔵臓堕帯滞滝択沢弾痴遅昼虫鋳庁聴伝盗稲闘徳届縄難弐悩覇拝廃売麦髪抜晩蛮卑浜賓頻敏仏払並塀弁勉歩舗峰萌褒豊坊冒毎満黙訳誉揚謡頼覧竜猟緑涙塁励鈴霊"
    "隷暦歴恋炉労郎録患番喫飽筋膵宮節跡痢倦怠減赤"
)
_HANGUL_FREQUENT = (
    "이그저것수등들및의에를을는은가와과도로으서하다있없되않했한할해고지기게면며나니까요죠네데든던더또만뿐처럼보같위대통따라중부터께테일삼사오육칠팔구십백천억년월시분초주개명번회차세살첫둘셋넷섯곱덟아홉열두"
    "환자호성별연령키신장체몸무혈압축완맥박심온흡산소포화당뇨병질협근경색뇌졸출치매파킨슨간염암폐직유방갑상선전립췌담낭광궁난식피림프종골양악절용재발생존망추적관찰진단급크측앞뒤래술항료약물투량횟효작합증감"
    "침곤란토설변어욕판헤모글빈마트리레티닌알민총빌루콜스롤밀공복후륨칼슘인철페틴젖제능검영음엑씨엠내조결정비계미름타예남녀운동력현금업학혼험거역농촌원외입퇴응실날짜록메참확취행락높낮많좋쁘빠르느길짧넓좁새"
    "젊늙김최강윤임권황안송류홍문손배허노곽우엄채함여석표반왕옥맹탁국편봉태목형범좌팽승갈준혜숙희혁훈순규섭웅찬솔슬린율겸건균애향례덕춘귀말점람교님버머딸족친랑각씀야때막법불련필드러된디바른습려었히접속될특"
    "떤값받몇줄읽찾렇째겠볼므못잘달져써됩집았떻누얻얼끝론갖넣싶곳놓즉올돌격먼답꾸였혹너쪽움맞책청엔엇쉽품풀좀걸쉬붙쓸쳐충긴잡벽즈낸넘활겨왜창군졌견큰떠혀멀슷독략꼭듯씩논뜻왔밖냐즘쓴캡슐액팩튜브카텐펌링겔덱"
)
_ZH_LABEL_WORDS = frozenset("""
男 女 男性 女性 是 否 有 无 未知 不详 不明 阳性 阴性 弱阳性 正常 异常 良性 恶性 左 右 左侧
右侧 双侧 高 中 低 轻 重 轻度 中度 重度 死亡 存活 生存 复发 未复发 转移 无转移 治愈 好转
稳定 进展 缓解 汉族 回族 满族 城市 农村 城镇 已婚 未婚 离异 丧偶 吸烟 不吸烟 饮酒 不饮酒 有效
无效 痊愈 显效 一般 良好 差 优 可 小学 初中 高中 大学 本科 硕士 博士 农民 工人 干部 职员
退休 学生 无业 内科 外科 门诊 住院 無 陽性 陰性 異常 惡性 復發 轉移 痊癒 好轉 穩定 進展 緩解
農村 吸煙 飲酒 不詳 编号 序号 性别 年龄 姓名 诊断 结果 备注 身高 体重 血压 心率 体温 日期
医院 科室 分期 分级 病理 手术 治疗 随访 结局 事件 时间 月数 天数 編號 性別 年齡 診斷 結果
備註 體重 血壓 醫院 手術 治療 隨訪 結局 時間
""".split())
_KO_LABEL_WORDS = frozenset("""
남 여 남자 여자 남성 여성 예 아니오 아니요 네 유 무 있음 없음 양성 음성 정상 비정상 이상
해당없음 모름 미상 기타 생존 사망 재발 무재발 좌 우 좌측 우측 양측 상 중 하 고 저 경증
중등증 중증 흡연 비흡연 금연 과거흡연 현재흡연 음주 비음주 위암 폐암 간암 대장암 유방암 갑상선암
내과 외과 외래 입원 퇴원 응급 완치 호전 악화 불변 안정 진행 관해 부분관해 완전관해 기혼 미혼
이혼 사별 도시 농촌 초졸 중졸 고졸 대졸 환자번호 등록번호 차트번호 성별 나이 연령 이름 성명
환자명 보호자 담당의 진단 진단명 결과 비고 체온 혈압 수축기혈압 이완기혈압 맥박 키 신장 체중
몸무게 병원 날짜 입원일 퇴원일 수술일 수술 치료 병기 등급 당뇨 당뇨병 고혈압 고지혈증 흡연여부
음주여부 검사일 검사결과 혈당 크레아티닌 헤모글로빈 백혈구 혈소판 알부민 콜레스테롤 나트륨 칼륨
추적기간 생존기간 재발여부 사망여부 합병증 부작용 투여량
""".split())
_JA_LABEL_WORDS = frozenset("""
男 女 男性 女性 有 無 あり なし 有り 無し はい いいえ 陽性 陰性 正常 異常 良性 悪性 死亡
生存 再発 転移 軽快 不変 悪化 治癒 寛解 右 左 両側 高 中 低 軽度 中等度 重度 喫煙 禁煙 飲酒
不明 未確認 その他 患者番号 性別 年齢 氏名 診断 診断名 結果 備考 身長 体重 血圧 体温 病院 日付
入院日 退院日 手術日 手術 治療 病期 転帰 喫煙歴 飲酒歴 既往歴 家族歴 高血圧 糖尿病 脂質異常症
肺癌 胃癌 肝癌 大腸癌 乳癌
""".split())
_EA_SYMBOLS = frozenset("，。、；：？！（）【】《》〈〉「」『』“”‘’…—～·•℃℉°±×÷≤≥≈≠‰％μ㎎㎏㎜㎝㎞㎡㎖㎗㎕㏄㎍㎛※○●◎△▲□■◇◆☆★"
                        "→←↑↓①②③④⑤⑥⑦⑧⑨⑩ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩαβγδεκλμπσωΔ・ー々〜￥　")
# the readings compared, by family: (codec that reads it, language of its text)
_EA_FAMILIES = {"zh": (("gbk", "gb18030"), "zh"), "big5": (("big5",), "zh"), "ko": (("cp949",), "ko"),
                "sjis": (("cp932",), "ja"), "eucjp": (("euc_jp",), "ja")}
_EA_FAMILY_OF = {"gbk": "zh", "gb2312": "zh", "gb18030": "zh", "hz": "zh", "big5": "big5", "cp950": "big5", "big5hkscs": "big5",
                 "euc_kr": "ko", "cp949": "ko", "johab": "ko", "shift_jis": "sjis", "cp932": "sjis", "shift_jisx0213": "sjis",
                 "shift_jis_2004": "sjis", "euc_jp": "eucjp", "euc_jisx0213": "eucjp", "euc_jis_2004": "eucjp"}
_EA_NAMES = {"zh": ("GBK（简体中文）", "gbk", "中文"), "big5": ("Big5（繁体中文）", "big5", "繁体中文"), "ko": ("EUC-KR（韩文）", "euc-kr", "韩文"),
             "sjis": ("Shift-JIS / cp932（日文）", "cp932", "日文"), "eucjp": ("EUC-JP（日文）", "euc-jp", "日文")}
_EA_ORDER = ("zh", "big5", "ko", "sjis", "eucjp")
_FIELD_SPLIT_RE = re.compile(r'[,\t;|\n\r"]+')


@functools.lru_cache(maxsize=1)
def _ea_tables():
    """(frequent Han characters, frequent Hangul syllables, label words by language)."""
    han = set(_HAN_FREQUENT + _HAN_CLINICAL + _HAN_TRADITIONAL + _HAN_JAPANESE) | set(CN_SURNAMES) | set(CN_GIVEN_CHARS) | \
        set(CN_TERM_CHARS) | set("".join(CN_COMPOUND_SURNAMES))
    for w in list(CN_CLINICAL_WORDS) + list(CN_FIELD_WORDS) + list(SAFE_LABEL_WORDS_CN) + list(_ZH_LABEL_WORDS):
        han |= set(w)
    han = frozenset(ch for ch in han if "\u4e00" <= ch <= "\u9fff")
    hangul = frozenset(_HANGUL_FREQUENT) | frozenset(KR_SURNAMES)
    return han, hangul, {"zh": _ZH_LABEL_WORDS, "ko": _KO_LABEL_WORDS, "ja": _JA_LABEL_WORDS}


def _reading_evidence(text, lang):
    """How much `text` (one reading of a file) reads as `lang` text -> (frequent characters, different non-ASCII
    characters, cells that are a label word of the language)."""
    han, hangul, words = _ea_tables()
    chars = {ch for ch in text[:200000] if ord(ch) > 0x7F and not ch.isspace()}
    hits = 0
    for ch in chars:
        if ch in _EA_SYMBOLS or "\uff01" <= ch <= "\uff5e":
            hits += 1
        elif "\u4e00" <= ch <= "\u9fff":
            hits += ch in han
        elif "가" <= ch <= "힣":
            hits += lang == "ko" and ch in hangul
        elif "\u3041" <= ch <= "\u30ff":
            hits += lang == "ja"
    cells = {f.strip() for f in _FIELD_SPLIT_RE.split(text[:200000])}
    return hits, len(chars), sum(1 for f in cells if f and not f.isascii() and f in words[lang])


def _ea_readings(raw):
    """{family: (frequent characters, different characters, word cells, codec)} for the East-Asian readings the bytes
    decode in."""
    out = {}
    for fam, (encs, lang) in _EA_FAMILIES.items():
        for enc in encs:
            try:
                text = raw.decode(enc)
            except UnicodeDecodeError:
                continue
            out[fam] = _reading_evidence(text, lang) + (enc,)
            break
    return out


def _better_reading(readings, family):
    """The family of a reading that is clearly more of a text than the reading of `family` -> family or None: 3 in 4 of
    its different characters are frequent ones, and either it has cells that are label words ("남", "아니오", "陽性")
    where `family`'s reading has none, or it has 8+ different characters, 0.3 more of them frequent and 4+ more
    frequent ones (a few characters read as frequent ones by chance)."""
    if family not in readings or not readings[family][1]:
        return None
    k0, n0, w0, _ = readings[family]
    s0, best = k0 / n0, None
    for fam in _EA_ORDER:
        if fam == family or fam not in readings or readings[fam][1] < 2:
            continue
        k, n, w, _ = readings[fam]
        s = k / n
        by_words = w >= 1 and w0 == 0 and s >= s0
        by_chars = n >= 8 and s - s0 >= 0.3 and k - k0 * n / n0 >= 4 and w >= w0
        if s >= 0.75 and (by_words or by_chars) and (best is None or (s, w) > best[1:]):
            best = (fam, s, w)
    return best[0] if best else None


def _encoding_doubt(raw, used, explicit):
    """When the bytes of a file decoded with `used` (a Chinese, Korean or Japanese encoding) read clearly better in
    another one -> (family, warning) or None. The file stays read with `used` (a Chinese reading is never replaced
    by a Korean / Japanese guess), but no text value is printed: a name read in the wrong encoding is still the name
    (its bytes are), and the name rules cannot see it."""
    try:
        fam0 = _EA_FAMILY_OF.get(codecs.lookup(used).name)
    except LookupError:
        return None
    if fam0 is None:
        return None
    rd = _ea_readings(raw)
    if fam0 not in rd:
        return None
    fam = _better_reading(rd, fam0)
    if fam is None:
        return None
    name, flag, lang = _EA_NAMES[fam]
    if fam == "ko" and rd["ko"][3] == "cp949":
        try:
            raw.decode("euc_kr")
        except UnicodeDecodeError:
            flag = "cp949"
    head = f"按 --encoding {used} 解码" if explicit else \
        f"按 {({'gb18030': 'GB18030（简体中文）'}).get(used) or _EA_NAMES[fam0][0]}解码"
    return fam, (f"{head}，但文件的字节按 {name}读才像有意义的文字：列名和取值可能显示为无意义的字符。确认编码之前，报告不显示任何"
                 f"单元格里的文字（分类取值、单元格文字、单位写法都只计数）；如果这是{lang}文件，请加 --encoding {flag} 重新体检")


def _japanese_korean(raw):
    """A file that is no valid GB18030 (nor UTF-8 / GBK / Big5): a Korean (EUC-KR) or Japanese (Shift-JIS / cp932,
    EUC-JP) file -> (text, encoding, notes with a warning) or None."""
    tip = "；如果列名或取值显示不对，请用 --encoding 指定编码"
    for enc, test in (("euc_kr", _hangul), ("cp932", _jis_common), ("euc_jp", _jis_common)):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        chars = [ch for ch in text[:200000] if ord(ch) > 0x7F]
        if chars and sum(1 for ch in chars if test(ch)) >= 0.5 * len(chars):
            fam = {"euc_kr": "ko", "cp932": "sjis", "euc_jp": "eucjp"}[enc]
            return text, enc, [f"文件不能按 UTF-8 / GBK / GB18030 解码，按 {_EA_NAMES[fam][0]} 读入" + tip]
    return None


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
        tried = ["utf-8-sig", "gbk", "big5", "gb18030"]
    text = used = None
    notes = []
    if len(tried) > 1:
        text, used, notes = _guess_decode(raw)
    else:
        try:
            text, used = raw.decode(tried[0]), tried[0]
        except UnicodeDecodeError:
            pass
    if text is None:
        raise ValueError(f"无法按 {' / '.join(tried)} 解码该文件；请用 --encoding 指定编码"
                         "（Windows 西文文件可试 --encoding cp1252）")
    label = used
    if used == "utf-8-sig":
        label = "utf-8（带 BOM）" if raw.startswith(codecs.BOM_UTF8) else "utf-8"
    elif used == "utf-16" and not encoding:
        label = "utf-16（带 BOM）"
    elif used in ("big5", "euc_kr", "cp932", "euc_jp") and not encoding:
        label = f"{used}（自动判断）"
    elif used == "utf-8-replace":
        label, used = "utf-8（有无法识别的字节）", "utf-8"
    # a Chinese / Korean / Japanese reading whose bytes read clearly better in another of these encodings: kept, with
    # a warning, and no text value printed (also with --encoding: following a wrong hint must not print names)
    doubt = _encoding_doubt(raw, used, bool(encoding))
    if doubt:
        notes = list(notes) + [doubt[1]]
    suspect = _gbk_mojibake(text) if used in ("gbk", "gb18030") and not encoding and not doubt else set()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if sep in ("\\t", "tab", "TAB"):
        sep = "\t"
    if sep is None:
        sep = "\t" if ext in (".tsv", ".tab") else _sniff_sep(text, skip_rows)
    if len(sep) != 1:
        raise ValueError("--sep 只能是一个字符，如 , 或 ; 或 \\t")
    # The csv module (not pandas.read_csv) so that no value is converted and a row with extra
    # fields cannot silently turn the first column into the index.
    _raise_csv_limit()                   # a long free-text cell is data, not a parse error
    try:
        reader = csv.reader(io.StringIO(text), delimiter=sep)
        rows, spans, prev = [], [], 0    # spans: (first, last) physical line of every record
        for r in reader:
            rows.append(r)
            spans.append((prev + 1, reader.line_num))
            prev = reader.line_num
    except csv.Error as e:
        raise ValueError(f"CSV 解析失败（常见原因：引号不配对）：{e}")
    # The lenient reader above never complains about quotes. An opening quote that is never closed
    # makes it read the REST OF THE FILE into one cell; a quote closed later, or followed by more
    # characters ("abc"def), silently merges the lines in between into one cell. The strict reader
    # notices both; it goes on after an error, so every place is found.
    strict, bad_quotes, prev = csv.reader(io.StringIO(text), delimiter=sep, strict=True), [], 0
    while True:
        try:
            next(strict)
        except StopIteration:
            break
        except csv.Error as e:
            if "unexpected end of data" in str(e):
                line = spans[-1][0] if spans else 1
                raise ValueError(f"CSV 引号不配对：第 {line} 行附近有一个以 \" 开头、却没有结束引号的单元格，"
                                 "后面的所有内容都会被读进这一格。请在原软件里修正后重新导出（或另存为 .xlsx）")
            bad_quotes.append((prev + 1, strict.line_num))
        prev = strict.line_num
    recs = list(zip(rows, spans))[skip_rows:]
    while recs and not any(x.strip() for x in recs[0][0]):
        recs.pop(0)
    if not recs:
        if skip_rows and any(any(x.strip() for x in r) for r in rows):
            raise ValueError(f"--skip-rows {skip_rows} 跳过了文件的全部内容（文件共 {len(rows)} 行记录）；请改小 --skip-rows")
        raise ValueError("数据文件是空的")
    rows = [r for r, _ in recs]
    use_header = _decide_header(rows[0], header, meta, [r for r in rows[1:201] if any(x.strip() for x in r)])
    raw_header = rows[0] if use_header else []
    rest = recs[1:] if use_header else recs
    body_recs = [(r, s) for r, s in rest if any(x.strip() for x in r)]
    body = [r for r, _ in body_recs]
    # records over several lines: a quoted line break, or lines merged by a stray quote (then every
    # physical line of the record, quotes ignored, has as many fields as a row: it is several rows)
    merged, multiline, lines, width = [], [], text.split("\n"), len(rows[0])
    for r, (a, b) in body_recs:
        if b == a:
            continue
        rows_inside = width >= 2 and all(line.count(sep) + 1 == width for line in lines[a - 1:b])
        strict_error = any(a <= q <= b and q2 > q for q, q2 in bad_quotes)
        (merged if rows_inside or strict_error else multiline).append((a, b))
    meta["quote_issues"] = {"merged_lines": merged, "multiline_cells": multiline,
                            "bad_quote_lines": [a for a, b in bad_quotes if a == b]}
    longer = [r for r in body if len(r) > width]
    counts = {"longer": len(longer), "shorter": sum(1 for r in body if len(r) < width),
              "longer_with_content": sum(1 for r in longer if any(x.strip() for x in r[width:]))}
    data = [r[:width] + [""] * (width - len(r)) for r in body]
    columns = _unique_names(raw_header) if use_header else [f"列{j + 1}" for j in range(width)]
    df = pd.DataFrame(data, columns=columns, dtype=object)
    head = [x.strip() for x in raw_header]
    meta.update(format="csv", encoding=label, codec=codecs.lookup(used).name, sep=sep, raw_header=raw_header, field_counts=counts,
                n_blank_rows=len(rest) - len(body), skip_rows=skip_rows,
                title_rows=_title_rows([r for r in rows[:205] if any(x.strip() for x in r)]),
                n_header_copies=sum(1 for r in body if use_header and [x.strip() for x in r] == head))
    if use_header and meta["title_rows"]:
        df.columns = _mask_title_header(df.columns, meta)
    if notes:
        meta["encoding_warning"] = "；".join(notes)
    if doubt:
        meta["encoding_doubt"] = doubt[0]
    if suspect:
        try:
            raw.decode("cp1252")
            alt = "cp1252"
        except UnicodeDecodeError:
            alt = "latin-1"
        meta["encoding_warning"] = (
            f"按 {used} 解码后，英文字母旁出现了生僻汉字，文件可能是 Windows 西文编码（如 µmol、Müller 被读坏）："
            f"请加 --encoding {alt} 重新体检，确认列名和取值显示正常")
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


# a measure or role written after a person's name in a column name ("张三评分", "John Smith score")
HEADER_NAME_SUFFIX_RE = re.compile(r"(?:的)?(?:评分|打分|评估|测量|判读|读片|阅片|结果|意见|诊断|记录|签名|score|rating|reading|read)$",
                                   re.IGNORECASE)
# where a column name is split to find a person in it ("患者：张三", "王芳(主治)", "Testa Personne_hb", "hb(Testa Personne)")
_HEADER_SPLIT_RE = re.compile(r"[_\-–—./\\()（）\[\]【】{}:：,，、;；|#+*~=<>!?？！\"'‘’“”\n\r↵\t0-9]+")
_HEADER_RUN_RE = re.compile(r"[一-鿿·•・]+|[가-힣]+|[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ' ]*")
# a date stamp in a column name ("Hb_20230101", "Hb 2021-01", "2023-01-01", "2023年1月1日"): no record number
_DATE_STAMP_RE = re.compile(r"(?<![0-9])(?:(?:19|20)[0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])?"
                            r"|(?:19|20)[0-9]{2}[-/.年](?:0?[1-9]|1[0-2])(?:[-/.月](?:0?[1-9]|[12][0-9]|3[01])日?|月)?)(?![0-9])")
_HEADER_GROUPS_RE = re.compile(r"(?<![0-9])[0-9]+(?:[-/\s._][0-9]+)+")      # (from a run's first digit: linear)


# field words a name may run into inside a column name ("王芳出生日期", "张三电话", "李四评分", "王芳随访")
CN_FIELD_WORDS = frozenset("""
出生日期 出生年月 出生年月日 生日 电话 手机 联系电话 联系方式 住址 地址 身份证 身份证号 住院号 病历号 病案号 门诊号 医保号 微信 姓名
评分 打分 评估 随访 复查 复诊 术前 术后 入院 出院 签名 签字 意见 结果 记录 化验 检验 检查 诊断 血压 体重 身高 年龄 性别 病史 日期 时间
编号 备注 资料 数据 信息 情况 病历 报告 影像 用药 费用 治疗 手术 主诉 现病史 既往史 家族史 体检 化验单 检验单 心率 血糖 血脂
""".split())


def _cn_field_word(t):
    """A field word, alone or followed by others ("出生日期", "血压值", "随访记录"): what a name may run into."""
    return t in CN_FIELD_WORDS or t in VARIABLE_WORDS or any(t.startswith(w) for w in CN_FIELD_WORDS if len(w) >= 2)


def _cn_header_name(t):
    """A Chinese part of a column name -> 'strong' / 'weak' (3 characters) / 'weak2' (2 characters) / None. A
    "name" with a character of clinical words in its given name ("白细胞", "高血压", "黄体酮") is a variable."""
    if len(t) == 2 and t[1] == "氏":
        return None                                    # a surname + 氏 is an eponym (王氏评分, 张氏分型), no person
    k = _name_kind(t)
    if k != "weak":
        return k
    given = t[2:] if t[:2] in CN_COMPOUND_SURNAMES else t[1:]
    if any(ch in CN_TERM_CHARS and ch not in CN_GIVEN_CHARS for ch in given):
        return None
    return "weak" if len(t) >= 3 else "weak2"


def _latin_header_name(words):
    """The person in a run of Latin words of a column name -> 'strong' / 'weak' (two or more words) / 'weak2' (a
    lone given name) / None. All-capitals words are read as capitalised ("TESTA PERSONNE"). A part of the run is a
    candidate only when the other words are variable / visit / role words ("Testa Personne visit", "Testa Personne
    hb") and it holds no function word ("Date Of Birth" is no "Of Birth")."""
    rank = {None: 0, "weak2": 1, "weak": 2, "strong": 3}
    best = None
    words = [w.strip("'") for w in words if w.strip("'")]
    n = len(words)
    for i in range(n):
        for j in range(i + 1, min(n, i + 4) + 1):
            span = words[i:j]
            if (i, j) != (0, n) and not all(_fold(w) in HEADER_FILLER_EN or _fold(w) in VARIABLE_WORDS
                                            or re.fullmatch(r"[A-Z]{2,5}[0-9]?", w) for w in words[:i] + words[j:]):
                continue                     # (other words: variable, visit or role words, acronyms such as CT / MRI / OD)
            if any(w.lower() in FUNCTION_WORDS_EN for w in span):
                continue
            forms = {" ".join(span)}
            if all(w.isupper() and len(w) >= 4 for w in span):
                forms.add(" ".join(w.capitalize() for w in span))
            for f in forms:
                k = _name_kind(f)
                if k == "weak" and len(span) == 1:
                    k = "weak2"
                if rank[k] > rank[best]:
                    best = k
    return best


# ordinary words of clinical column names made of characters that also make names ("白天心率", "周平均血压", "焦虑评分",
# "白介素6", "白球比"): a column name is read without them before a person is looked for in it -- whatever they leave
# over is searched (a name that is itself one of these words is read as the word)
CN_CLINICAL_WORDS = frozenset("""
白天 夜间 日间 上午 下午 中午 晚上 凌晨 早晨 清晨 每日 每周 每月 季度 春季 夏季 秋季 冬季 季节 平均 平均值 均值 最大值 最小值
最高值 最低值 比值 变化量 变化率 差值 焦虑 抑郁 睡眠 疼痛 乏力 白介素 白球比 白蛋白 白细胞 红细胞 甘油三酯 甲状腺 甲胎蛋白 叶酸
游离 谷丙 谷草 转氨酶 胆红素 舒张压 收缩压 华法林 黄体酮 前列腺 维生素 文化程度 发病 发病率 发生率 病程 首发 严重程度 程度
时长 天数 间隔 左眼 右眼 双眼 左侧 右侧 双侧 常规 金额 费用 方式 方法 范围 水平 浓度 含量 数量 大小 长度 宽度 厚度 高度 深度
直径 面积 体积 位置 部位 原发 继发 增厚 增生 心电 生存 中心 有无 是否 多少 前后 上下 内外
""".split())


@functools.lru_cache(maxsize=1)
def _header_vocab():
    """Every known word a column name may be made of besides a person: clinical, field, variable and role words."""
    words = set(CN_CLINICAL_WORDS) | set(CN_FIELD_WORDS) | set(HEADER_PERSON_WORDS_CN)
    words |= {w for w in VARIABLE_WORDS if re.fullmatch(r"[一-鿿]+", w)}
    words |= set("评分 打分 评估 测量 判读 读片 阅片 结果 意见 诊断 记录 签名".split())
    # (generic words of named criteria, scores and laws: "柏林定义" is the Berlin definition, no "柏林定")
    words |= set("定义 标准 模型 分型 分级 分类 指数 量表 综合征 现象 公式 系数 效应 试验 曲线 法则 定律 原理 学说 假说".split())
    return frozenset(w for w in words if len(w) >= 2)


def _cut_words(run, words):
    """The pieces of a run of Chinese characters left over when the words of `words` are cut out (longest first,
    left to right)."""
    pieces, buf, i = [], "", 0
    while i < len(run):
        for L in range(min(8, len(run) - i), 1, -1):
            if run[i:i + L] in words:
                if buf:
                    pieces.append(buf)
                    buf = ""
                i += L
                break
        else:
            buf += run[i]
            i += 1
    if buf:
        pieces.append(buf)
    return pieces


_LATIN_JOIN = r"\s_\-./,+&·•・()（）"
_LATIN_SEQ_RE = re.compile(rf"[A-Za-zÀ-ɏ']+(?:[{_LATIN_JOIN}]{{1,3}}[A-Za-zÀ-ɏ']+)*")
_LATIN_SPLIT_RE = re.compile(rf"[{_LATIN_JOIN}]+")
_CN_SPACE_RE = re.compile(r"(?<=[一-鿿])[ \u3000]{1,2}(?=[一-鿿])")
_CAMEL2_RE = re.compile(r"([A-Z][a-z]{1,15})([A-Z][a-z]{1,15})")
_HONORIFICS = frozenset({"dr", "mr", "mrs", "ms", "miss", "prof"})


def _strong_name_anywhere(s):
    """A personal name of a strong shape (_name_kind) anywhere in a column name, whatever stands next to it: in the
    Chinese characters left over when known words are cut out ("王一二左眼", "3床王一二", "患儿王一二", "王一二与李三四";
    3-4 characters, a masked "王某"), a dotted or Tibetan name, or 2-4 Latin words joined by spaces, _ - . or /
    ("Mary Fakename CT", "OD John Testperson", "WANG Yier CT", "John_Testperson", "MARY FAKENAME"), or an honorific
    before a capitalised word ("Dr_Testperson"). A space after the surname is read away ("王 一二左眼"); Latin words may
    also be joined by , + & · or brackets ("Fakename, Mary CT", "Mary+Fakename", "Mary（Fakename）"), a word in
    capitals is also read capitalised ("John TESTPERSON"), and a common given name run into a surname is read as two
    words ("MaryFakename_CT"). An initial and a surname ("J. Testperson") is left out: it is written like a species
    ("H. Pylori", "E. Coli"). All-lower-case Latin words count only with a common given
    name ("mary fakename ct", "john_testperson"): lower-case pinyin is how column names are written (xue_ya, xin_lv)
    and a pinyin name looks the same. A 2-character surname + 氏 is an eponym (王氏评分). Reads the first 200
    characters."""
    s = s[:200]
    if _DOT_IN_TEXT_RE.search(s) or _TIB_IN_TEXT_RE.search(s):
        return True
    vocab = _header_vocab()
    joined = _CN_SPACE_RE.sub("", s)
    for run in re.findall(r"[一-鿿]+", s) + (re.findall(r"[一-鿿]+", joined) if joined != s else []):
        for piece in _cut_words(run, vocab):
            for L in (4, 3):
                if any(_name_kind(piece[i:i + L]) == "strong" for i in range(len(piece) - L + 1)):
                    return True
            if any(piece[i + 1] == "某" and piece[i] in CN_SURNAMES for i in range(len(piece) - 1)):
                return True
    for m in _LATIN_SEQ_RE.finditer(s):
        words = [w.strip("'") for w in _LATIN_SPLIT_RE.split(m.group()) if w.strip("'")]
        for i, w in enumerate(words):
            if w.lower() in _HONORIFICS and i + 1 < len(words) and re.fullmatch(rf"[A-Z{_LAT_UP}][a-z{_LAT_LO}]+", words[i + 1]):
                return True
            c2 = _CAMEL2_RE.fullmatch(w)          # "MaryFakename_CT": a common given name run into a surname
            if c2 and (c2.group(1).lower() in FIRST_NAMES or c2.group(2).lower() in FIRST_NAMES) and \
                    _name_kind(f"{c2.group(1)} {c2.group(2)}") == "strong":
                return True
            for j in range(i + 2, min(len(words), i + 4) + 1):
                span = words[i:j]
                if any(x.lower() in FUNCTION_WORDS_EN for x in span) or \
                        (all(x.islower() for x in span) and not any(x in FIRST_NAMES for x in span)):
                    continue
                forms = [" ".join(span)]
                if all(x.isupper() and len(x) >= 4 for x in span):
                    forms.append(" ".join(x.capitalize() for x in span))
                elif any(x.isupper() and len(x) >= 4 for x in span):
                    forms.append(" ".join(x.capitalize() if x.isupper() and len(x) >= 4 else x for x in span))
                if any(_name_kind(f) == "strong" for f in forms):
                    return True
    return False


def _holds_name(t):
    """A short string typed into cells (a word in a number column, a unit) that holds a personal name: one of a strong
    shape anywhere (_strong_name_anywhere), or two or three Latin words shaped like a name ("#Lin Yu以上", "lin yu",
    "LIN YU")."""
    if _strong_name_anywhere(t):
        return True
    for m in _LATIN_SEQ_RE.finditer(t[:200]):
        words = [w.strip("'") for w in _LATIN_SPLIT_RE.split(m.group()) if w.strip("'")]
        for i in range(len(words)):
            for j in range(i + 2, min(len(words), i + 3) + 1):
                f = " ".join(words[i:j])
                if _name_kind(f):
                    return True
    return False


def _header_person(h):
    """How much a column name holds a person: 'strong' -- a name of a strong shape anywhere in it ("患者张建国",
    "Dr. John Smith"); a weak shape of two words or three Chinese characters that is no clinical word ("Testa Personne",
    "Testa Personne_hb", "hb(Testa Personne)", "王甲乙-随访"); a shorter one next to a role, honorific, kin or contact word
    ("患者王芳", "王芳医生", "家属李娜电话", "Mr Testa") -- is masked on its own; 'weak' (2-character Chinese names, a
    lone given name: "张力", "Mary") counts only when most column names are people (a transposed table); None."""
    s = "".join(ch for ch in _nfkc(h)[:120] if unicodedata.category(ch) != "Cf")[:80]
    if not s:
        return None
    if HONORIFIC_NAME_RE.search(s) or CAPS_COMMA_NAME_RE.match(s) or _name_kind(s) == "strong" or _strong_name_anywhere(s):
        return "strong"
    rank = {None: 0, "weak2rare": 1, "weak2": 2, "weak": 3, "strong": 4}
    best, context = None, False
    for chunk in _HEADER_SPLIT_RE.split(s):
        runs = []
        for run in _HEADER_RUN_RE.findall(chunk):
            # (Chinese runs without the ordinary clinical words: "焦虑评分" is "评分", "白天心率" is "心率")
            runs += _cut_words(run, CN_CLINICAL_WORDS) if re.match(r"[一-鿿]", run) else [run]
        for run in runs:
            run = run.strip()
            if not run:
                continue
            if re.match(r"[一-鿿·•・]", run):
                t, changed, stripped_front = run, True, False
                while changed and t:
                    changed = False
                    for w in HEADER_PERSON_WORDS_CN:
                        if t != w and t.startswith(w):
                            t, context, changed, stripped_front = t[len(w):], True, True, True
                            break
                        if t != w and t.endswith(w):
                            t, context, changed = t[:-len(w)], True, True
                            break
                        if t == w:
                            t, context = "", True
                            break
                    if t and not changed:
                        t2 = HEADER_NAME_SUFFIX_RE.sub("", t)
                        if t2 and t2 != t:
                            t, context, changed = t2, True, True
                # the name may run into a field word ("王芳出生日期", "血压王芳") or follow a role word ("患者王芳出生日期")
                cands = [t] if t else []
                for L in (2, 3, 4):
                    if len(t) > L and (_cn_field_word(t[L:]) or (stripped_front and context)):
                        cands.append(t[:L])
                    if len(t) > L and _cn_field_word(t[:-L]):
                        cands.append(t[-L:])
                k = None
                for t_ in cands:
                    k_ = _cn_header_name(t_)
                    if k_ == "weak2" and not _cn_given_common(t_):
                        k_ = "weak2rare"         # ("金额", "方便", "常规"): a person only next to a role word
                    if t_ != t and k_ in ("weak2", "weak"):
                        context = True           # a name next to a field word: someone's own column ("常规检查" is none)
                    if rank[k_] > rank[k]:
                        k = k_
            elif re.match(r"[가-힣]", run):
                k = _name_kind(run)
            else:
                words = run.split()
                if any(w.lower() in HEADER_PERSON_WORDS_EN or w.lower() in ("score", "rating", "reading") for w in words):
                    context = True
                words = [w for w in words if w.lower() not in HEADER_PERSON_WORDS_EN]
                k = _latin_header_name(words)
            if rank[k] > rank[best]:
                best = k
    if best in ("strong", "weak") or (best in ("weak2", "weak2rare") and context):
        return "strong"
    return "weak" if best == "weak2" else None


def _header_code(s):
    """A column name that is (or holds) a record / specimen number: a run of 5+ digits ("100230", "P100230",
    "#100230", "住院100230", "100230号"), digit groups of 6+ digits with a part of 4+ ("23-1000", "ZY-23-4100",
    "2023/1000"), a record code -- not a date stamp ("Hb_20230101", "Hb 2021-01", "2023年1月1日"), a year range,
    an item / visit / time code ("SF36_01", "V01_01", "T08_30") or an accession ("rs1801133")."""
    t = s.strip()
    if re.fullmatch(r"[A-Za-z0-9_.\-]+", t) and NOT_RECORD_RE.match(t):
        return False
    t = _DATE_STAMP_RE.sub(" ", t)
    if _digit_groups_7(t) or re.search(r"[0-9]{5,}", t):
        return True
    for m in _HEADER_GROUPS_RE.finditer(t):
        g = m.group()
        parts = re.findall(r"[0-9]+", g)
        if sum(map(len, parts)) >= 6 and max(map(len, parts)) >= 4 and not _YEAR_RANGE_RE.fullmatch(g):
            return True
    return False


def _header_identifier(h, strong=False):
    """A column name that is itself someone's name, record number or contact data. strong: only what is
    a person / number on its own (contact data, a record number, a person found by _header_person), as a single
    such column name in an ordinary table is masked; weak name shapes ("张力", "Mary") count only when most
    column names look like people (a transposed table)."""
    s = "".join(ch for ch in _nfkc(h)[:MAX_SCAN_LEN] if unicodedata.category(ch) != "Cf")
    if not s:
        return False
    idc, ph = _contact_hits(s)
    if idc or ph or ("@" in s and EMAIL_RE.search(s[:MAX_SCAN_LEN])) or _header_code(s[:200]):
        return True
    if len(s) > 80:
        return False
    k = _header_person(s)
    return k == "strong" or (not strong and k == "weak")


def _header_reason(h):
    """Why a column name is shown by its position: what it holds."""
    s = "".join(ch for ch in _nfkc(h)[:MAX_SCAN_LEN] if unicodedata.category(ch) != "Cf")
    idc, ph = _contact_hits(s)
    if idc or ph or ("@" in s and EMAIL_RE.search(s)):
        return "含证件号、电话或邮箱"
    if _header_code(s[:200]):
        return "含编号或 7 位以上的数字"
    return "含人名" if _header_person(s) else "转置表的列名"


def _identifier_headers(names):
    """(positions of column names that would print people or record numbers, transposed?). Most column
    names (but the first, the row labels) shaped like people or record numbers: a table with patients
    as columns -- those and the other names of the same shape are masked. Otherwise only the names that
    are a person or a number on their own (see _header_identifier(strong=True))."""
    hits = [j for j, h in enumerate(names) if _header_identifier(h)]
    strong = [j for j in hits if _header_identifier(names[j], strong=True)]
    others = max(1, len(names) - 1)
    # weak shapes alone ("Blood Pressure", "Heart Rate", "张力") never make a table transposed; strong ones do,
    # and so do three or more 2-character Chinese names of common given-name characters ("王芳 / 李娜 / 张伟")
    cn_names = sum(1 for j in hits if CN_NAME_RE.match(_nfkc(names[j])) and _cn_given_common(_nfkc(names[j])))
    people = strong or cn_names >= 3
    if hits and people and (len(hits) >= 0.5 * others or (len(hits) >= 3 and len(hits) >= 0.3 * len(names))):
        # patients as columns: the other column names of the same shape (2-4 Chinese characters, or
        # capitalised words) are patients too -- except the first column, which holds the row labels
        sigs = collections.Counter(_shape_sig(_nfkc(names[j])) for j in hits)
        sig = sigs.most_common(1)[0][0]
        lens = [len(_nfkc(names[j])) for j in hits]
        return sorted(set(hits) | {j for j, h in enumerate(names) if j > 0 and _shape_sig(_nfkc(h)) == sig
                                   and min(lens) <= len(_nfkc(h)) <= max(lens) and not _header_word(h)}), True
    return strong, False


# names of common clinical variables: a first column made of them, next to columns of numbers, is the
# row labels of a transposed table (patients as columns)
VARIABLE_WORDS = frozenset(_fold(w) for w in """
年龄 性别 身高 体重 bmi 血压 收缩压 舒张压 心率 脉搏 体温 呼吸 血红蛋白 白细胞 血小板 中性粒细胞 淋巴细胞 肌酐 尿素 尿素氮 尿酸
白蛋白 总蛋白 胆红素 总胆红素 血糖 空腹血糖 糖化血红蛋白 胆固醇 甘油三酯 钾 钠 氯 钙 诊断 分期 分级 病理 手术 化疗 放疗 复发 死亡
随访 吸烟 饮酒 高血压 糖尿病 民族 职业 婚姻 住院天数 费用 评分 结局 入院日期 出院日期 手术日期
age sex gender height weight sbp dbp hr pulse temperature temp rr hb hgb wbc plt neut lymph alt ast ggt alp crea cr creatinine bun
urea ua albumin alb tp tbil dbil glucose glu hba1c tc tg ldl hdl k na cl ca crp pct esr inr pt aptt fib d-dimer psa cea afp ca125
ca199 diagnosis dx stage grade histology pathology surgery chemo radiotherapy recurrence death outcome smoking alcohol los cost
score ecog kps asa
""".split())


def _transposed_layout(df):
    """A table with patients as columns, told by its layout: the first column holds 3+ different
    names of clinical variables (年龄, Hb, ALT ...), or other row labels while most other column names
    are people or patient numbers ("Ki-67 / LVEF / FEV1" under "Testa Personne / Fakeo Nomen"); and the
    other columns hold mostly numbers."""
    if df.shape[1] < 2 or len(df) < 3 or len(df) > 500:
        return False
    first = [_fold(v) for v in df.iloc[:, 0].tolist() if not _is_blank(v)]
    if len(first) < 3 or len(set(first)) < 0.9 * len(first):
        return False
    if sum(1 for v in first if v in VARIABLE_WORDS) < 0.5 * len(first):
        heads = [str(c) for c in df.columns[1:]]
        if not _row_labels_column(df.iloc[:, 0].tolist()) or \
                sum(1 for h in heads if _header_person(h) or _patient_code_header(h)) < 0.5 * len(heads):
            return False
    cells = [v for j in range(1, df.shape[1]) for v in df.iloc[:, j].tolist() if not _is_blank(v)]
    return bool(cells) and sum(1 for v in cells if _measured(v)) >= 0.5 * len(cells)


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
    if isinstance(v, _dt.time):
        return ("s", v.strftime("%H:%M:%S"))
    return ("s", str(v))


def _year2(y):
    y = int(y)
    return y + (2000 if y < 69 else 1900) if y < 100 else y


def _make_date(y, m, d):
    try:
        return _dt.datetime(y, m, d)
    except ValueError:
        return None


def _parse_time(t):
    """'14:30', '14:30:00.123', '3:05 PM', '下午 3:05', '14时30分', '14时' -> (h, m, s) or None."""
    m = _TIME_RE.match(t.strip())
    if not m:
        return None
    ap = (m.group(1) or m.group(7) or "").lower()
    h = int(m.group(2))
    mi = int(m.group(3) or m.group(5) or 0)
    s = int(m.group(4) or m.group(6) or 0)
    if ap in ("pm", "下午", "p.m.") and h < 12:
        h += 12
    elif ap in ("am", "上午", "a.m.") and h == 12:
        h = 0
    return (h, mi, s) if h < 24 and mi < 60 and s < 60 else None


def _parse_date(s, month_first=False, digits8=False):
    """A date or date-time cell -> (datetime, spelling) or None. Numeric spellings: y-m-d (also / .
    年月日), d/m/y or m/d/y (2- or 4-digit year; month first only when the day decides it or
    month_first), y-m, yyyymmdd (only when digits8), each with an optional time ('14:30', '3:05 PM',
    '下午 3:05', '14时', 'T14:30:00Z', '+08:00'); month words ("25-Mar-2023", "Jan-22")."""
    s = s.strip()
    if not s or len(s) > 48 or not s[0].isalnum():
        return None
    if re.search(r"[A-Za-z]", s) and not re.search(r"[0-9]T[0-9]|AM|PM|am|pm|Z$", s):
        if not MONTH_DATE_RE.match(s):
            return None
        for fmt in MONTH_DATE_FORMATS:
            try:
                return _dt.datetime.strptime(s, fmt), fmt
            except ValueError:
                continue
        return None
    if not s[0].isdigit():
        return None
    if re.fullmatch(r"[0-9]{8}", s):
        m = _Y8_RE.match(s)
        if not digits8:
            return None
        d = _make_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return (d, "%Y%m%d") if d and 1800 <= d.year <= 2200 else None
    m = _DATE_TIME_SPLIT_RE.match(s)
    if not m:
        return None
    dpart, tpart = m.group(1), m.group(2)
    tm = None
    if tpart:
        tm = _parse_time(tpart)
        if tm is None:
            return None
    d = fmt = None
    m = _YMD_RE.match(dpart)
    if m:
        d = _make_date(int(m.group(1)), int(m.group(3)), int(m.group(4)))
        sep = m.group(2)
        fmt = "%Y年%m月%d日" if sep == "年" else f"%Y{sep}%m{sep}%d"
    elif _YM_RE.match(dpart) and not tpart:
        m = _YM_RE.match(dpart)
        d = _make_date(int(m.group(1)), int(m.group(3)), 1)
        fmt = "%Y年%m月" if m.group(2) == "年" else f"%Y{m.group(2)}%m"
    else:
        m = _DMY_FULL_RE.match(dpart)
        if m:
            a, b, y, sep = int(m.group(1)), int(m.group(3)), _year2(m.group(4)), m.group(2)
            yfmt = "%Y" if len(m.group(4)) == 4 else "%y"
            day_first = not month_first and a <= 31 and b <= 12
            if not day_first and not (a <= 12 and b <= 31):
                return None
            d = _make_date(y, b, a) if day_first else _make_date(y, a, b)
            if d is None and day_first:
                d, day_first = _make_date(y, a, b), False
            fmt = f"%d{sep}%m{sep}{yfmt}" if day_first else f"%m{sep}%d{sep}{yfmt}"
    if d is None:
        return None
    if tm:
        d = d.replace(hour=tm[0], minute=tm[1], second=tm[2])
        fmt += " %H:%M"
    return d, fmt


def _is_unit(u):
    """True when every character of `u` belongs to a unit: unit words (mmol, L, kg, mm Hg, years,
    岁, 次/分 ...), a power of ten (×10^9), separators (/ space · *), an exponent (m2) or a factor
    after a slash (/1.73m2). Names, addresses and sentences are no units."""
    s = _nfkc(u).lower()
    if not s or len(s) > 24:
        return False
    i, n, words, after_slash = 0, len(s), 0, False
    while i < n:
        ch = s[i]
        if ch in " /·*":
            after_slash = after_slash or ch == "/"
            i += 1
            continue
        m = _POW10_RE.match(s, i)
        if m:
            i, words, after_slash = m.end(), words + 1, False
            continue
        if after_slash:
            m = _UNIT_FACTOR_RE.match(s, i)
            if m and m.end() < n and not s[m.end()].isspace():
                rest = s[m.end():]                 # "/1.73m2", "/100ml": a factor only before a unit it can divide
                if not any(rest.startswith(u) for u in _PER_UNITS):
                    return False
                i = m.end()
                continue
        w = next((w for w in _UNIT_WORD_LIST if s.startswith(w, i)), None)
        if w is None:
            return False
        i, words, after_slash = i + len(w), words + 1, False
        m = _UNIT_EXP_RE.match(s, i)
        if m and (m.end() == n or not s[m.end()].isdigit()):
            i = m.end()
    return words > 0


def _with_unit(s):
    """A number with a unit ("130g/L", "120 mm Hg", "6.5 ×10^9 /L", "45 years old", "45岁", "1.7E+08 IU/mL") ->
    (number, unit, flag, reason) or None; a lab flag after the unit ("5.6mmol/L↑", "95 g/L L") or between the
    number and the unit ("9.6↑ mmol/L", "9.6* mmol/L") is split off; a power of ten that multiplies the number
    ("5.29×10^5 IU/mL", "3.2*10^4") is applied (unit IU/mL), one that belongs to a unit per volume ("×10^9/L") is not."""
    m = NUM_E_TAIL_RE.match(s) or NUM_TAIL_RE.match(s)
    if not m:
        return None
    num, tail = m.group(1), m.group(2).strip()
    tries = [(num, tail)]
    if len(num) > 2 and num.endswith("10") and tail[:1] in ("^", "*", "e", "E") and num[:-2] not in ("", "-", "+"):
        tries.append((num[:-2], "10" + tail))    # "53.210^9/L": 53.2 ×10^9/L written without a space
    for num, tail in tries:
        mm = _MULT_RE.match(tail)
        if mm and not mm.group(2).startswith("/"):
            rest = mm.group(2).strip()
            val = float(f"{num}e{int(mm.group(1))}")            # (exact: 9.99×10^8 is 999000000, a whole number)
            if not rest:
                return val, None, None, "科学计数（×10^n）"
            u = _unit_flag(rest)
            if u:
                return val, u[0], u[1], "带单位"
        u = _unit_flag(tail)
        if u:
            return float(num), u[0], u[1], "带单位"
    return None


def _unit_flag(tail):
    """A unit, with a lab flag after it or before it -> (unit, flag) or None."""
    f = _FLAG_FIRST_RE.match(tail)
    # ("5.9*10^9/L": a "*" before a power of ten multiplies, it is no flag)
    if f and _is_unit(f.group("rest")) and not (f.group("flag").startswith("*") and re.match(r"10(?:\^|\*|e|~)?-?[0-9]", f.group("rest"))):
        return f.group("rest").strip(), f.group("flag")
    for rx in (SYMBOL_FLAG_TAIL_RE, LETTER_FLAG_TAIL_RE):
        t = rx.match(tail)
        if t and _is_unit(t.group("rest")):
            return t.group("rest").strip(), t.group("flag")
    if _is_unit(tail):
        return tail, None
    return None


def _unit_key(u):
    """A unit as units are compared: case, spaces, μ / u, × / x / * before 10, 10*9 / 10e9 / 10^9 and m2 / m^2
    do not make two units ("×10^9/L" = "x10^9/L" = "10*9/L", "IU/ml" = "IU/mL")."""
    t = _nfkc(u).lower().replace(" ", "").replace("μ", "u").replace("µ", "u")
    t = re.sub(r"(?:[x×*])?10(?:\^|\*\*|\*|e|~)(-?[0-9]{1,2})", r"×10^\1", t)
    t = t.replace("hpf", "hp").replace("lpf", "lp")
    t = t[1:] if t.startswith("个/") else t
    return re.sub(r"(?<=[a-z])\^(?=[23](?![0-9]))", "", t)


# Units printed whatever the patient unit: a fixed list of known units, compared as _unit_key compares them. Any other
# string read as a unit (unit words joined into "Lin Yu", "周天元", "Du Min" ...) is printed only when patients can be
# told apart and at least SMALL_CELL_K of them have it, and it is shaped like no name (see _gate_values).
KNOWN_UNITS = """
g/L|g/dL|mg/L|mg/dL|mg/mL|mg/100mL|μg/L|μg/dL|μg/mL|mcg/mL|ng/L|ng/dL|ng/mL|pg/mL|pg/L|μg/g|mg/g|mg/mmol|g/24h|mg/24h|mg/d|g/d
mmol/L|μmol/L|nmol/L|pmol/L|mol/L|mEq/L|mmol/mol|mmol/24h|mOsm/kg|mOsm/L|IU/L|IU/mL|IU/dL|mIU/mL|mIU/L|μIU/mL|U/L|U/mL|U/dL|kU/L
mU/L|kIU/L|U|IU|mIU|units|unit|单位|万单位|copies/mL|copy/mL|cells/μL|cells/mL|/μL|/mL|/L|/HP|/LP|个/HP|个/μL|cfu/mL|pfu/mL
×10^9/L|×10^12/L|×10^6/L|×10^3/μL|×10^4/μL|×10^6/μL|×10^6/mL|×10^9|×10^12|×10^3|×10^6|10^9/L|10^12/L|%|‰|fL|pg|kg|g|mg|μg|mcg
ng|lb|lbs|oz|斤|公斤|千克|克|毫克|微克|纳克|mL|L|dL|μL|cc|毫升|升|mm|cm|m|km|μm|nm|in|inch|inches|ft|毫米|厘米|米|mm2|cm2|m2|mm3
cm3|m3|kg/m2|g/m2|mg/m2|mL/m2|L/min/m2|mL/min|mL/min/1.73m2|mL/h|mL/kg|mL/kg/h|mg/kg|μg/kg|μg/kg/min|mg/kg/d|mg/kg/h|L/min|mm/h
cm/s|m/s|mmHg|cmH2O|mmH2O|kPa|Pa|atm|bar|毫米汞柱|s|sec|secs|second|seconds|ms|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day
days|wk|wks|week|weeks|mo|month|months|y|yr|yrs|year|years|years old|yo|y/o|岁|秒|分|分钟|小时|时|天|日|周|星期|个月|月|年|次|次/分
次/min|/min|bpm|beats/min|次/分钟|breaths/min|rpm|times|次数|人次|°C|°F|度|kcal|kcal/d|kcal/kg|cal|kJ|HU|points|point|pts|score
元|万元|千元|美元|rmb|cny|usd|eur|个|片|粒|支|袋|瓶|例|人|名|包|根
"""
KNOWN_UNIT_KEYS = frozenset(_unit_key(u) for u in re.split(r"[|\n]", KNOWN_UNITS) if u.strip())
# lab flags as the parsing rules produce them (a closed set; checked once more before they are printed)
KNOWN_FLAG_RE = re.compile(r"[(\[]?(?:↑+|↓+|\*+|\+|[*!]{0,2}(?:HH|LL|H|L|AA|A|N|[Hh]igh|HIGH|[Ll]ow|LOW|[Aa]bnormal|ABNORMAL|[Cc]ritical|CRITICAL"
                           r"|偏高|偏低|升高|降低|增高|减低|高|低|异常|危急值|危急|阳性|阴性|弱阳性|↑|↓)[*!]{0,2})[)\]]?")


def _classify(key, vocab, date_hint):
    """-> (kind, value, extra). kinds: blank token amb nd number censored date loose text."""
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
    n = _nfkc(t)
    low = n.lower()
    if low in vocab.text:
        return ("amb" if low in vocab.ambiguous else "token", t, None)
    if low in ND_WORDS:
        return ("nd", t, None)
    if PLAIN_NUM_RE.match(t):
        if date_hint and re.fullmatch(r"\d{8}", t):
            d = _parse_date(t, digits8=True)
            if d:
                return ("date", d[0], d[1])
        f = float(t)
        return ("number", f, True) if math.isfinite(f) else ("text", t, None)
    if len(n) > 200:
        return ("text", t, None)
    if CENSORED_RE.match(n) or CENSORED_SUFFIX_RE.match(n) or low in CENSORED_WORDS:
        return ("censored", t, None)
    d = _parse_date(n)
    if d:
        return ("date", d[0], d[1])
    # loose numbers: extra = (reason, unit, abnormal flag)
    if PLAIN_NUM_RE.match(n):
        return ("loose", float(n), ("非标准负号" if "\u2212" in t else "全角字符", None, None))
    if THOUSANDS_RE.match(n) and not re.match(r"[-+]?0,", n):
        return ("loose", float(n.replace(",", "")), ("千分位逗号", None, None))
    if SPACE_THOUSANDS_RE.match(n):
        return ("loose", float(n.replace(" ", "")), ("千分位空格", None, None))
    if COMMA_DECIMAL_RE.match(n):
        return ("loose", float(n.replace(",", ".")), ("逗号作小数点", None, None))
    m = FLAG_RE.match(n)
    if m and (m.group("pre") or m.group("post")) and math.isfinite(float(m.group("num"))) and \
            not (m.group("post") == "+" and "." not in m.group("num")):      # "2+" is a grade, "9.6+" a flag
        return ("loose", float(m.group("num")), ("带异常标记", None, m.group("pre") or m.group("post")))
    m = APPROX_RE.match(n) or QMARK_RE.match(n)
    if m and math.isfinite(float(m.group(1))):
        return ("loose", float(m.group(1)), (APPROX_REASON if not n.endswith("?") else "带问号（不确定）", None, None))
    if COMPOUND_RE.match(n):                   # "120/80", "120/80mmHg", "3.5×2.1cm": two numbers, not one with a unit
        return ("text", t, "compound")
    u = _with_unit(n)
    if u and math.isfinite(u[0]):
        return ("loose", u[0], (u[3], u[1], u[2]))
    q = _qualified_number(n)
    if q and math.isfinite(q[0]):
        return ("loose", q[0], (q[1], q[2], q[3]))
    return ("text", t, None)


def _core_number(s):
    """A number, written plainly, with thousands separators or a decimal comma, with a symbol flag ("5.6↑") or with a
    unit ("5.6 mmol/L", "5,4 mmol/L", "12,345.67元") -> (value, unit, flag, reason) or None."""
    if PLAIN_NUM_RE.match(s):
        return float(s), None, None, None
    if THOUSANDS_RE.match(s) and not re.match(r"[-+]?0,", s):
        return float(s.replace(",", "")), None, None, "千分位逗号"
    if SPACE_THOUSANDS_RE.match(s):
        return float(s.replace(" ", "")), None, None, "千分位空格"
    if COMMA_DECIMAL_RE.match(s):
        return float(s.replace(",", ".")), None, None, "逗号作小数点"
    if EURO_NUM_RE.match(s):
        return float(s.replace(".", "").replace(",", ".")), None, None, "千分位点、逗号作小数点"
    m = FLAG_RE.match(s)
    if m and (m.group("pre") or m.group("post")) and not (m.group("post") == "+" and "." not in m.group("num")):
        return float(m.group("num")), None, m.group("pre") or m.group("post"), "带异常标记"
    u = _with_unit(s)
    if u:
        return u[0], u[1], u[2], u[3]
    m = LOCALE_TAIL_RE.match(s)
    if m:
        v, uf = _core_number(m.group(1)), _unit_flag(m.group(2).strip())
        if v and uf:
            return v[0], uf[0], uf[1], v[3]
    return None


def _qualified_number(s):
    """A number with an approximate word ("约500ml", "500ml左右", "~500 mL", "approx. 5.6", "12余年", "20多") or a lab flag
    written as a word ("5.6 High", "12.6 (High)", "14.8 A", "14.0 !H", "12.3 (危急值)", "阳性 12") around it, or one written
    with a decimal comma / thousands separators before a unit ("5,4 mmol/L", "12.345,67", "12,345.67元") -> (value,
    reason, unit, flag) or None. The value is the number as written (an approximate one is counted with a note)."""
    if len(s) > 80:
        return None
    approx, flag = False, None
    m = _APPROX_PREFIX_RE.match(s)
    if m:
        approx, s = True, s[m.end():]
    m = _FLAG_PREFIX_RE.match(s)
    if m:
        flag, s = m.group("f"), s[m.end():]
    m = _APPROX_SUFFIX_RE.search(s)
    if m:
        approx, s = True, s[:m.start()]
    m = None if flag else _FLAG_SUFFIX_RE.search(s)
    if m:
        f, core = m.group("a") or m.group("b") or m.group("c"), s[:m.start()].rstrip()
        if re.fullmatch(_LETTER_FLAG, f) and not re.search(r"[0-9]\.[0-9]|[0-9]{3}", core):
            return None                                    # ("3 A", "2 N": a grade or a stage)
        flag, s = f, core
    m = None if approx else _APPROX_INFIX_RE.match(s)
    if m:
        approx, s = True, m.group(1) + m.group(2)
    v = _core_number(s.strip())
    if v is None:
        return None
    val, unit, flag2, reason = v
    reason = APPROX_REASON if approx else "带异常标记" if (flag or flag2) else (reason or ("带单位" if unit else None))
    return (val, reason, unit, flag or flag2) if reason else None


# units after which a capital L / H is litres / hours, not a lab flag ("1.5L" next to "800ml",
# "3H" next to "120min")
VOLUME_UNITS = frozenset({"ml", "dl", "cl", "μl", "ul", "cc", "毫升"})
TIME_UNITS = frozenset({"min", "mins", "minute", "minutes", "s", "sec", "secs", "分", "分钟", "秒"})


def _letter_flags_as_units(counts, cls):
    """A bare "L" / "H" after a number is a lab flag ("3.1 L", "5.8H", "128 L" on most sodium
    values) unless it is a unit: it is on every number of the column, or other cells carry a
    smaller unit of the same kind (ml for L, min / s for H) and their numbers are at least ten
    times larger (800ml next to 1.5L, 120min next to 2H -- PT "11.5s" next to "17.2 H" is a flag).
    Updates cls."""
    n_nums = sum(c for k, c in counts.items() if cls[k][0] in ("number", "loose"))
    for letter, family in (("L", VOLUME_UNITS), ("H", TIME_UNITS)):
        keys = [k for k in counts if cls[k][0] == "loose" and cls[k][2][2] == letter and not cls[k][2][1]]
        if not keys:
            continue
        on_all = sum(counts[k] for k in keys) == n_nums
        fam = [cls[k][1] for k in counts if cls[k][0] == "loose" and (cls[k][2][1] or "").lower() in family
               for _ in range(min(counts[k], 50))]
        mine = [cls[k][1] for k in keys for _ in range(min(counts[k], 50))]
        larger = bool(fam) and float(np.median(np.abs(fam))) >= 10 * max(float(np.median(np.abs(mine))), 1e-9)
        if on_all or larger:
            for k in keys:
                cls[k] = ("loose", cls[k][1], ("带单位", letter, None))


_FIRST_NUMBER_RE = re.compile(r"[-+]?[0-9][0-9.,]*")


def _comma_decimal_column(counts, cls):
    """A column whose numbers are written with a decimal comma ("5,2", "37,25", "12.345,67") and never with comma
    thousands for sure ("1,234.5", "1,234,567"): its "1,234"-shaped values are decimals too (1.234). Updates cls; True
    when one was re-read."""
    dec = sure_thou = 0
    amb = []
    for k in counts:
        if cls[k][0] != "loose" or k[0] != "s":
            continue
        reason = cls[k][2][0]
        if reason in ("逗号作小数点", "千分位点、逗号作小数点"):
            dec += 1
        elif reason == "千分位逗号":
            m = _FIRST_NUMBER_RE.search(_nfkc(k[1])[:80])
            part = m.group().rstrip(".,") if m else ""
            if re.fullmatch(r"[-+]?[0-9]{1,3},[0-9]{3}", part):
                amb.append((k, part))
            else:
                sure_thou += 1
    if not (dec and amb and not sure_thou):
        return False
    for k, part in amb:
        _, _, (reason, unit, flag) = cls[k]
        cls[k] = ("loose", float(part.replace(",", ".")), ("逗号作小数点", unit, flag))
    return True


_WORD_FLAG_RE = re.compile(rf"[*!(\[（]{{0,2}}{_WORD_FLAG}[*!)\]）]{{0,2}}")


def _number_labels(counts, cls):
    """Category labels made of a flag or approximate word and a small number ("阳性 16 / 阳性 18 / 阴性" HPV types,
    "阴性 0 / 阳性 2", "异常 1 / 异常 2 / 正常", "High 2 / Low 1", "约1次/周 / 从不", "近1月 / 近2周 / 半年"): the numbers
    that were read only with such a word are 12 or fewer different ones, and other numbers are fewer than a fifth of
    them -- labels, not measurements with a note (a lab value "5.6 偏高" among plain numbers takes many values).
    They are read back as text: the column stays categorical with every level (its reference word too) counted.
    Updates cls; True when it did."""
    q = [k for k in counts if cls[k][0] == "loose" and k[0] == "s" and
         (cls[k][2][0] == APPROX_REASON or (cls[k][2][2] and _WORD_FLAG_RE.fullmatch(str(cls[k][2][2]))))]
    if not q:
        return False
    n_q = sum(counts[k] for k in q)
    n_other = sum(c for k, c in counts.items() if k not in q and cls[k][0] in ("number", "loose", "censored"))
    if len({cls[k][1] for k in q}) > 12 or n_other >= 0.2 * n_q:
        return False
    for k in q:
        cls[k] = ("text", k[1].strip(), None)
    return True


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
    out = {"n": int(len(x)), "min": float(x.min()), "p1": _r(q[1]), "p5": _r(q[2]), "p25": _r(q[3]),
           "median": _r(q[4]), "p75": _r(q[5]), "p95": _r(q[6]), "p99": _r(q[7]), "max": float(x.max()),
           "mean": _r(mean, 6), "sd": _r(sd, 6),
           "n_z_gt3": None if binary else (int((np.abs(x - mean) / sd > 3).sum()) if sd > 0 else 0),
           "n_iqr_out": None if binary else int(((x < lo) | (x > hi)).sum()),
           "iqr_bounds": None if binary else [_r(lo), _r(hi)],
           "n_negative": int((x < 0).sum()), "n_zero": int((x == 0).sum()),
           "n_distinct": n_distinct}
    if rng:
        out["range"] = [rng[0], rng[1]]
        out["n_out_of_range"] = int(((x < rng[0]) | (x > rng[1])).sum())
    return out


# a whole number this large (7+ digits) may be a phone, ID card or record number typed into a numeric column
BIG_INT = 1e6
_STAT_KEYS = ("min", "p1", "p5", "p25", "median", "p75", "p95", "p99", "max", "mean", "sd")


def _n_big_ints(info):
    """How many valid cells hold a whole number of 7+ digits, however it is written: an Excel number,
    "13800131005", "13,800,131,005", "13800131005.0", Excel's two-decimal "13800131005.00" or its CSV
    export "1.38001E+10" -- the value decides, not the spelling (a viral load written 9.88E+09 is hidden
    like one written 9880000000)."""
    cls, miss, n = info["cls"], info["missing_by_key"], 0
    for k, c in info["counts"].items():
        kind, val = cls[k][0], cls[k][1]
        if kind in ("number", "loose") and not miss[k] and abs(val) >= BIG_INT and float(val).is_integer():
            n += c
    return n


def _hide_big_numbers(stats, n_big):
    """A whole number of 7+ digits is never printed: when a column holds one, every statistic that
    could show it or be pulled towards it (>= 1e6 in size: the maximum, a high percentile, the mean,
    the SD, the IQR bounds) is hidden; the count is kept for the report. Updates stats."""
    if not n_big:
        return
    hidden = [k for k in _STAT_KEYS if stats.get(k) is not None and abs(stats[k]) >= BIG_INT]
    for k in hidden:
        stats[k] = None
    if stats.get("iqr_bounds") and ({"p25", "p75"} & set(hidden) or any(abs(b) >= BIG_INT for b in stats["iqr_bounds"])):
        stats["iqr_bounds"] = None
    stats["n_big_int"], stats["hidden_stats"] = n_big, hidden


def _round_numbers(labels):
    """Most of these whole numbers are round (213000, 450000): counts, not record numbers."""
    labels = set(labels)
    return bool(labels) and sum(1 for v in labels if v.endswith("00")) >= 0.5 * len(labels)


def _looks_like_int_id(values, counts):
    """All-unique integers that are a 1..n (or 1001..) sequence or all have >= 5 digits (record
    numbers, also of mixed length) and are not mostly round. A run such as ages 40..69 is not taken
    for a sequence number."""
    if len(values) < 20 or any(c > 1 for c in counts) or not all(float(v).is_integer() for v in values):
        return False
    ints = [int(v) for v in values]
    sequence = max(ints) - min(ints) + 1 == len(ints) and (min(ints) <= 1 or min(ints) >= 1000)
    return sequence or (all(abs(i) >= 10000 for i in ints) and not _round_numbers(str(abs(i)) for i in ints))


def _looks_like_code_id(labels, counts):
    """All-unique codes such as P0001 / ZY2024001 (letters + digits)."""
    if len(labels) < 20 or any(c > 1 for c in counts):
        return False
    rx = re.compile(r"^(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9_\-]+$")
    return all(rx.match(s.strip()) for s in labels)


def _int_dates(counts, cls, date_hint):
    """Whole numbers that are all real yyyymmdd dates (or, all of at least 3 different values or under a
    date-like name, yyyymm year-months) -> {key: (datetime, spelling)}, else None. A few impossible
    ones among 10+ real dates (20230230; at most 5%) stay out of the result: unreadable date cells."""
    keys = [k for k in counts if cls[k][0] == "number"]
    if not keys:
        return None
    out, bad = {}, 0
    for k in keys:
        lab = _label(k).strip() if k[0] == "s" else _fmt_num(cls[k][1])
        if not re.fullmatch(r"[0-9]{6}|[0-9]{8}|[0-9]{12}|[0-9]{14}", lab):
            return None
        if len(lab) in (12, 14):
            # yyyymmddHHMM(SS) date-times -- only under a date-like name (a record number may start with a date)
            if not date_hint:
                return None
            try:
                out[k] = (_dt.datetime.strptime(lab, "%Y%m%d%H%M%S" if len(lab) == 14 else "%Y%m%d%H%M"),
                          "%Y%m%d%H%M%S" if len(lab) == 14 else "%Y%m%d%H%M")
            except ValueError:
                return None
            continue
        if len(lab) == 8:
            d = _parse_date(lab, digits8=True)
            if not d or not 1900 <= d[0].year <= 2100:
                # a typo such as 20230230 among real yyyymmdd dates: an unreadable date, not a number
                if re.fullmatch(r"(?:19|20)[0-9]{2}(?:0[1-9]|1[0-2]|[0-9]{2})[0-9]{2}", lab):
                    bad += counts[k]
                    continue
                return None
            out[k] = d
        else:
            y, m = int(lab[:4]), int(lab[4:])
            if not (1900 <= y <= 2100 and 1 <= m <= 12):
                return None
            out[k] = (_dt.datetime(y, m, 1), "%Y%m")
    lens = {len(_label(k).strip()) if k[0] == "s" else len(_fmt_num(cls[k][1])) for k in keys}
    if len(lens) != 1:
        return None
    if lens == {6} and not date_hint and len(keys) < 3:
        return None
    n_ok = sum(counts[k] for k in out)
    if bad and (n_ok < 10 or bad > max(1, 0.05 * (n_ok + bad))):
        return None
    return out


def _censored_bound(v):
    """'<0.5' -> ('<', 0.5, False); '≥8' -> ('>', 8, True); '60以上' -> ('>', 60, True)."""
    v = _nfkc(v)
    m, m2 = CENSORED_PARTS_RE.match(v), CENSORED_SUFFIX_RE.match(v)
    if m:
        return ("<" if m.group(1) in LOWER_OPS else ">"), float(m.group(2)), m.group(1) in INCLUSIVE_OPS
    if m2:
        return ("<" if m2.group("side") == "以下" else ">"), float(m2.group("num")), True
    return None


def _censored_unit(v):
    """The unit written in a censored value ("<0.5 mg/L" -> "mg/L", "60岁以上" -> "岁") or None."""
    s = _nfkc(v)
    m = CENSORED_PARTS_RE.match(s)
    if m:
        return s[m.end():].strip() or None
    m = CENSORED_SUFFIX_RE.match(s)
    return ((m.group("unit") or "").rstrip("及或") or None) if m else None


def _censored_clean(v):
    """A censored value made of an operator, a number and at most a unit ("<0.5", "＞1000 IU/mL",
    "60岁以上", "未检出"): shown as an example. Free text after it ("<0.5 王芳复查") is not."""
    s = _nfkc(v)
    if s.lower() in CENSORED_WORDS or s.lower() in ND_WORDS or CENSORED_SUFFIX_RE.match(s):
        return True
    m = CENSORED_PARTS_RE.match(s)
    if not m:
        return False
    tail = s[m.end():].strip()
    return not tail or _is_unit(tail)


def _grouped_bins(counts, cls):
    """True when a column's censored strings are pre-binned groups, not values beyond a detection
    limit -- decided from the values: ranges ("2-5cm", "1~3年") with at most a few plain numbers; the
    two sides of one cut point, also next to a few other groups ("<60 / ≥60", "0 / <20 / ≥20"); whole
    numbers that fill the gap between two cuts ("≤6 / 7 / ≥8"); or count bins, an upper open end right
    after whole numbers starting at 0 or 1 ("0 / 1 / ≥2", "0 / 1 / 2 / >2", "1 / 2 / >2"). A detection
    limit is one open end next to measured values ("<1 / 1 / 2 / 3", ">90 / 86 ... 90"), however many
    fell beyond it; two different limits with results between them ("<0.01 / 0.15 / 1.2 / >50") are a
    lab censored at both ends."""
    bounds = [b for b in (_censored_bound(cls[k][1]) for k in counts if cls[k][0] == "censored") if b]
    texts = [_nfkc(cls[k][1])[:MAX_MEASURE_LEN] for k in counts if cls[k][0] == "text"]
    # (numbers with a unit or a flag are results too: "<0.010 ng/mL / 0.15 ng/mL / >50.00 ng/mL", "<1% / 35% / >90%")
    nums = sorted({cls[k][1] for k in counts if cls[k][0] in ("number", "loose")})
    measured = bool(nums)
    if not bounds:
        return False
    if any(RANGE_RE.match(t) for t in texts):
        return len(nums) <= 5
    lows = [(t, incl) for side, t, incl in bounds if side == "<"]
    highs = [(t, incl) for side, t, incl in bounds if side == ">"]
    if lows and highs:
        lo, lo_incl = max(lows)
        hi, hi_incl = min(highs)
        if len(nums) > 3:
            return False
        if lo == hi or not nums:          # "<20 / ≥20" (and maybe a "0" group): two sides of one cut point;
            return True                   # "<18.5 / 18.5-24 / ≥24": open ends with nothing measured between
        # "≤6 / 7 / ≥8": whole numbers that fill the gap between the cuts; decimals in between ("<0.01 /
        # 0.15 / 1.2 / >50") are results between two detection limits
        first = lo + 1 if lo_incl else lo
        last = hi - 1 if hi_incl else hi
        return bool(nums) and all(float(x).is_integer() for x in nums) and float(first).is_integer() and \
            [int(x) for x in nums] == list(range(int(first), int(last) + 1))
    if highs and nums and len(nums) <= 5 and all(float(x).is_integer() for x in nums) and nums[0] in (0, 1) \
            and nums[-1] - nums[0] + 1 == len(nums):
        return all(t == nums[-1] + (1 if incl else 0) for side, t, incl in bounds)
    return bool(texts) and not measured


def _token(s):
    """A word from a numeric / date column as it may be shown: digits masked ("#"), at most 20
    characters, so the example shows the spelling ("溶血", "#..#", "见报告") and never a result."""
    return re.sub(r"[0-9]+(?:[.,][0-9]+)*", "#", _nfkc(s)[:1000])[:20]


def _profile_column(name, values, vocab, text_numbers_are_issue, max_levels, rng, forced_id,
                    never_id=False, rule_name=None):
    """One column. never_id (--not-id): never typed ID. Nothing here depends on --outcome: the outcome
    column is profiled like any other. rule_name: the column's own name when the report shows it by its
    position (a name that holds a person or a number): the name rules (date of birth, contact, ID, date words)
    still read it; it is never printed."""
    rn = (name if rule_name is None else rule_name)[:MAX_NAME_RULE_LEN]
    n = len(values)
    keys = [_key(v) for v in values]
    counts = collections.Counter(keys)
    date_hint = bool(DATE_NAME_RE.search(rn))
    cls = {k: _classify(k, vocab, date_hint) for k in counts}
    hints = []
    if _prefer_month_first(counts, cls):
        hints.append("日期按 月/日/年 解读（该列没有日 > 12 的 日/月/年 写法）")
    yy = _prefer_year_first2(counts, cls)
    if yy:
        hints.append(yy)
    _dash_pairs_as_compound(counts, cls)
    _letter_flags_as_units(counts, cls)
    if _comma_decimal_column(counts, cls):
        hints.append("该列用逗号作小数点（如 5,2）：像 1,234 这样的取值也按小数读（1.234），不是千分位")
    _number_labels(counts, cls)
    kc = collections.Counter()
    for k, c in counts.items():
        kc[cls[k][0]] += c
    # whole numbers that are all yyyymmdd / yyyymm dates are dates, not record numbers or measurements
    idates = None if (forced_id or kc["text"] or kc["loose"]) else _int_dates(counts, cls, date_hint)
    if idates and kc["number"] >= 0.8 * (kc["number"] + kc["date"] + kc["censored"]):
        for k, d in idates.items():
            cls[k] = ("date", d[0], d[1])
        kc = collections.Counter()
        for k, c in counts.items():
            kc[cls[k][0]] += c
        if any(d[1] == "%Y%m" for d in idates.values()):
            hints.append("整数取值是年月（yyyymm），按日期（当月 1 日）处理")
    # "ND": not detected (censored) in a lab column; not done (missing) in a column of ages, counts, scores or
    # durations (named so, with whole numbers below 1000 and no other censored value)
    n_measured = kc["number"] + kc["loose"] + kc["censored"]
    num_vals = [(cls[k][1], c) for k, c in counts.items() if cls[k][0] in ("number", "loose")]
    n_vals = sum(c for _, c in num_vals)
    lab_like = bool(kc["censored"]) or not NON_LAB_NAME_RE.search(_name_forms(rn)[0]) or \
        (n_vals and (sum(c for v, c in num_vals if not float(v).is_integer()) >= 0.5 * n_vals
                     or max(abs(v) for v, _ in num_vals) >= 1000))
    nd_censored = bool(kc["nd"]) and lab_like and n_measured >= 0.2 * (n_measured + kc["text"] + kc["date"])
    for k in counts:
        if cls[k][0] == "nd":
            cls[k] = ("censored", cls[k][1], None) if nd_censored else ("token", cls[k][1], None)
    kc = collections.Counter()
    for k, c in counts.items():
        kc[cls[k][0]] += c

    # "<60 / ≥60", "≤2cm / 2-5cm / >5cm", "0 / 1 / ≥2": pre-binned groups, not detection-limit values
    binned = bool(kc["censored"]) and _grouped_bins(counts, cls)
    if binned:
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
    bad_date_shaped = sum(c for k, c in counts.items() if cls[k][0] == "text" and BROKEN_DATE_RE.match(_nfkc(cls[k][1])))
    id_source = None                    # forced (--id) / name / value
    pct_numeric = None                  # set for a column half text, half numbers
    # codes, one per patient: many different ones ("pT1a / pT2 / pT3" stages are few and shared)
    text_keys_ = [k for k in counts if cls[k][0] == "text"]
    code_like = lambda: (len(text_keys_) >= 10 and len(text_keys_) >= 0.2 * max(kc["text"], 1)
                         and sum(1 for k in text_keys_ if CODE_VALUE_RE.match(_nfkc(cls[k][1]))
                                 and re.search(r"[A-Za-z]", cls[k][1])) >= 0.8 * len(text_keys_)
                         and kc["text"] >= 0.8 * n_def)
    if forced_id or (n_def and not never_id and (_is_id_name(rn) or
                                                 (_name_forms(rn)[0] in AMBIGUOUS_ID_NAMES and code_like()))):
        ctype, id_source = "id", ("forced" if forced_id else "name")
    elif n_def == 0:
        ctype = "categorical" if kc["amb"] else "empty"
    elif kc["date"] >= 0.8 * n_def or (date_hint and kc["date"] >= 0.5 * n_def) or \
            (date_hint and kc["date"] + bad_date_shaped >= 0.8 * n_def and bad_date_shaped):
        ctype = "date"
    elif n_num >= 0.5 * n_def and not binned:
        # mostly numbers: a numeric column, whose words ("溶血", "见报告") are listed as a problem
        num_keys = [k for k in counts if cls[k][0] == "number"]
        ctype = "numeric"
        # a column named like a date holding 5-digit numbers is Excel date serials, not an ID
        if not never_id and not date_hint and kc["loose"] == 0 and kc["censored"] == 0 and \
                kc["text"] <= 0.2 * n_def and _looks_like_int_id(
                [cls[k][1] for k in num_keys], [counts[k] for k in num_keys]):
            ctype, id_source = "id", "value"
            # all different whole numbers may also be a measurement (cost, platelets, a date serial)
            serial = all(20000 <= cls[k][1] <= 80000 for k in num_keys)
            hints.append("按取值判为 ID：全部是互不相同的整数（序号，或 5 位以上、像病历号）；这只是类型判断，不是隐私判断。"
                         "如果它是测量值（费用、计数" + ("、Excel 日期序列号" if serial else "") + "），请加 --not-id 重新体检，才有分布统计")
    else:
        text_keys = [k for k in counts if cls[k][0] == "text"]
        if not never_id and kc["text"] == n_def and _looks_like_code_id([cls[k][1] for k in text_keys],
                                                                         [counts[k] for k in text_keys]):
            ctype, id_source = "id", "value"
        else:
            ctype = "categorical"          # may become "text" below (free text / too many levels)
            if 0.2 <= n_num / n_def < 0.5 and not binned:
                pct_numeric = round(100 * n_num / n_def)
                hints.append(f"约 {pct_numeric}% 是数字、其余是文字，内容可能混杂")

    # remarks hold whatever was typed (names, phone calls ...): counted, never listed or summarised
    if ctype in ("numeric", "categorical") and not never_id and REMARK_NAME_RE.search(rn):
        ctype, pct_numeric = "text", None
        hints[:] = [h for h in hints if "是数字、其余是文字" not in h]

    # ── missing: blank + tokens (+ ambiguous tokens / numeric codes where they cannot be values) ──
    amb_is_missing = ctype in ("date", "id", "empty")
    nums_all = {cls[k][1] for k in counts if cls[k][0] == "number"} - vocab.default_codes - vocab.forced_codes
    # A number the user added for all columns (--missing-tokens 0,9) is a missing code only where it can
    # be one: in a column of words, or away from the range of the column's other numbers. One of the two
    # codes of a 0/1 column, a value inside the range (a score of 9 among 0-29) or right next to it (0
    # complications next to 1 / 2 / 3, a score of 0 next to 1-29) is a real value -- reported, not
    # applied ("col=0" applies it to that column). A negative number below numbers that are all >= 0
    # (-1 under 0-29) is a code, however close.
    binary_code = len(nums_all) == 2 and kc["text"] == 0 and kc["loose"] == 0 and kc["censored"] == 0 and ctype != "date"

    def real_value(v):
        others = sorted(nums_all - {v})
        if binary_code:
            return True
        if len(others) < 2:
            return False
        step = min(b - a for a, b in zip(others, others[1:]))
        if v < 0 <= others[0]:
            return False
        return others[0] - step <= v <= others[-1] + step
    missing_by_key = {}
    disguised, codes, kept_amb, skipped = (collections.Counter() for _ in range(4))
    for k, c in counts.items():
        kind, val, _ = cls[k]
        if kind == "token" and ctype == "categorical" and _nfkc(val).lower() in CATEGORY_TOKENS:
            kind = "category"
            cls[k] = ("text", val, None)
        miss = kind in ("blank", "token") or (kind == "amb" and amb_is_missing)
        if kind == "token" or (kind == "amb" and amb_is_missing):
            disguised[val] += c
        elif kind == "amb":
            kept_amb[val] += c
        elif kind == "number" and val in vocab.codes:
            if val in vocab.forced_codes:
                miss = True
            elif val in vocab.user_codes:
                miss = not real_value(val)
            else:
                miss = ctype in ("numeric", "categorical", "date", "id")
            if miss:
                codes[_fmt_num(val)] += c
            elif val in vocab.user_codes:
                skipped[_fmt_num(val)] += c
        missing_by_key[k] = miss
    n_missing = sum(c for k, c in counts.items() if missing_by_key[k])
    n_valid = n - n_missing

    col = {"name": name, "type": ctype, "type_label": TYPE_LABELS[ctype], "id_source": id_source, "n": n,
           "n_valid": n_valid,
           "n_blank": kc["blank"], "disguised_missing": dict(disguised), "missing_codes": dict(codes),
           "n_missing_total": n_missing, "pct_missing_total": round(100 * n_missing / n, 1) if n else 0.0,
           "pct_missing_blank_only": round(100 * kc["blank"] / n, 1) if n else 0.0,
           "possible_missing_kept": dict(kept_amb), "hints": hints}
    if skipped:
        col["missing_tokens_not_applied"] = dict(skipped)
    if pct_numeric is not None:
        col["pct_numeric"] = pct_numeric
    # "120/80", "3.5×2.1cm": two measurements in one cell -- not free text, not an identifier
    comp = [(k, c) for k, c in counts.items() if cls[k][0] == "text" and cls[k][2] == "compound"]
    n_compound = sum(c for _, c in comp)
    if n_compound and ((n_compound >= 0.5 * max(1, kc["text"]) and ctype in ("categorical", "text")) or ctype == "numeric"):
        col["compound"] = n_compound
        hints.append(_compound_hint([_nfkc(cls[k][1]) for k, _ in comp], n_compound, ctype == "numeric"))

    # ── privacy: count hits only, never keep the values ──
    id_hits = phone_hits = email_hits = n_text_vals = 0
    for k, c in counts.items():
        if k[0] in ("s", "n") and not missing_by_key[k]:
            s = _label(k)
            idc, ph = _contact_hits(s) if k[0] == "s" or len(s) >= 11 else (False, False)
            id_hits += c if idc else 0
            phone_hits += c if ph else 0
            email_hits += c if k[0] == "s" and "@" in s and EMAIL_RE.search(s[:MAX_SCAN_LEN]) else 0
            n_text_vals += c
    kind = _pii_name_kind(rn)
    by_name = kind is not None
    # "联系人数", "家属人数": a count of people, not a person
    count_word = re.search(r"人数|次数|个数|数量|数$|count|number[\s_\-.]*of|^n[\s_\-.]|[\s_\-.]n$|_num$", _name_forms(rn)[0])
    if kind == "person" and ctype == "numeric" and count_word:
        kind = "contact"
    if kind == "contact" and ctype == "numeric":
        # "电话随访次数", "phone_use_hours", "address_changes": a measurement, unless the numbers are
        # phone / post-code shaped (5+ digit whole numbers)
        nums = [cls[k][1] for k in counts if cls[k][0] in ("number", "loose") and not missing_by_key[k]]
        by_name = bool(nums) and sum(1 for x in nums if float(x).is_integer() and abs(x) >= 10000) >= 0.5 * len(nums)
    elif kind == "contact" and ctype in ("categorical", "text"):
        # "home_oxygen" 是 / 否: a yes / no answer is no address or phone number
        vals = {_fold(_label(k)) for k in counts if not missing_by_key[k] and k[0] != "blank"}
        by_name = len(vals) > 2
    # a date column named after birth ("Birth", "出生") is a date of birth
    by_name = by_name or (ctype == "date" and bool(BIRTH_WORD_RE.search(rn)))
    # a column full of ID-card / phone / e-mail values is private; a few of them in a reason column
    # are hidden like any small cell and reported (the reasons many patients share stay visible)
    full = lambda h: h and (h >= 0.5 * max(n_text_vals, 1) or by_name)
    pii = bool(by_name or full(id_hits) or full(phone_hits) or full(email_hits))
    col["contact_cells"] = {"id_card": id_hits, "phone": phone_hits, "email": email_hits} \
        if (id_hits or phone_hits or email_hits) and not pii else None
    col["pii"] = ({"by_name": by_name, "id_card_hits": id_hits, "phone_hits": phone_hits, "email_hits": email_hits,
                   "looks_like": [], "unique_per_patient": False} if pii else None)
    if pii and by_name:
        word = _pii_name_word(rn)
        # (of a name shown by its position only a vocabulary word may be printed, never the name itself)
        if rn == name or (word != _disp(rn)[:20] and not _header_identifier(word)):
            col["pii"]["name_word"] = word
    if rn != name:
        col["_rule_name"] = rn

    # ── censored strings ──
    cens = collections.Counter({cls[k][1]: c for k, c in counts.items() if cls[k][0] == "censored"})
    if cens:
        clean = collections.Counter({v: c for v, c in cens.items() if _censored_clean(v) and not _digit_groups_7(v)})
        # (the examples are chosen by _gate_values: a unit in them is printed only as any unit is)
        col["censored"] = {"n": sum(cens.values()), "examples": []}
        if len(clean) < len(cens):
            col["censored"]["n_unshown"] = len(cens) - len(clean)

    # ── numeric column that would load as text ──
    tokens = collections.Counter()
    examples, unit_keys, flags = collections.Counter(), collections.Counter(), collections.Counter()
    spellings, unit_of, flag_of, ex_unit = collections.defaultdict(collections.Counter), {}, {}, {}
    if ctype == "numeric":
        reasons = collections.Counter()
        for k, c in counts.items():
            kind_, val, extra = cls[k]
            if kind_ == "token" and val not in PANDAS_DEFAULT_NA:
                reasons["伪装缺失（非标准写法）"] += c
            elif kind_ == "amb":
                reasons["文字“无/none/-”（是 0、阴性还是缺失需确认）"] += c
            elif kind_ == "censored":
                reasons["截断值"] += c
            elif kind_ == "loose":
                reasons[extra[0]] += c
                uk = _unit_key(extra[1]) if extra[1] else None
                if not extra[2] and not (abs(val) >= BIG_INT and float(val).is_integer()):
                    examples[k[1].strip()] += c    # (flagged results: the flags are listed instead)
                    ex_unit[k[1].strip()] = uk
                if extra[1]:
                    unit_keys[uk] += c
                    spellings[uk][extra[1]] += c
                    unit_of[k] = uk
                if extra[2]:
                    flags[extra[2]] += c
                    flag_of[k] = extra[2]
            elif kind_ in ("text", "date"):
                # neither a number, a missing spelling nor a censored value: shown as a token only
                reasons["其他文字"] += c
                tokens[_token(_label(k).strip())] += c
            elif kind_ == "number" and extra and text_numbers_are_issue:
                reasons["以文本格式存储的数字"] += c
        # a unit spelled several ways (×10^9/L, x10^9/L, 10*9/L; IU/ml, IU/mL) is one unit, shown in its commonest spelling
        if reasons:
            # (units, flags and examples are strings typed into cells: _gate_values decides which may be printed)
            col["numeric_as_text"] = {"reasons": dict(reasons), "examples": [], "units": {}, "flags": {}}
            if tokens:
                col["numeric_as_text"]["unrecognised"] = {"n": sum(tokens.values()), "examples": [], "n_unshown": 0}

    # ── numeric distribution (counted, nothing removed) ──
    if ctype == "numeric":
        vals, wts = [], []
        for k, c in counts.items():
            kind_, val, _ = cls[k]
            if (kind_ == "number" and not missing_by_key[k]) or kind_ == "loose":
                vals.append(val)
                wts.append(c)
        x = np.repeat(np.array(vals, dtype=float), np.array(wts, dtype=int)) if vals else np.array([])
        stats = _numeric_stats(x, rng)
        _hide_big_numbers(stats, _n_big_ints({"cls": cls, "counts": counts, "missing_by_key": missing_by_key}))
        if cens:
            stats["note"] = f"已排除 {sum(cens.values())} 个截断值"
        col["numeric"] = stats
        if 0 < stats.get("n_distinct", 0) <= 10:
            hints.append(f"只有 {stats['n_distinct']} 个不同取值，可能是分类编码")
        if date_hint:
            serial = sum(c for k, c in counts.items() if cls[k][0] == "number" and 20000 <= cls[k][1] <= 80000)
            if serial:
                hints.append(f"列名像日期，但有 {serial} 个数字像 Excel 日期序列号（需要换算成日期）")

    # ── dates ──
    if ctype == "date":
        col["date"] = _date_details(counts, cls, missing_by_key)

    # ── categorical levels (also for numeric columns with <= 10 distinct values) ──
    levels = collections.Counter()
    if ctype in ("categorical", "numeric"):
        for k, c in counts.items():
            # in a numeric column a word written once may be someone's own words: listed as a token count only
            if not missing_by_key[k] and not (ctype == "numeric" and cls[k][0] == "text" and c == 1
                                              and re.search(r"[^\W\d_]", _label(k))):
                levels[_label(k)] += c
        if ctype == "categorical" and _is_free_text(levels, n_valid):
            ctype = "text"
        if ctype != "text" and len(levels) == 1:
            hints.append("所有有效值都相同（常数列）")
    if ctype in ("categorical", "text", "id"):
        defined = [_label(k).strip() for k in counts if not missing_by_key[k] and k[0] == "s"]
        if defined and sum(1 for v in defined if TIME_OF_DAY_RE.match(_nfkc(v))) >= 0.8 * len(defined):
            hints.append("取值是一天中的时刻（时:分），不是日期；需要时间间隔时请与日期列一起换算")
    col["type"], col["type_label"] = ctype, TYPE_LABELS[ctype]
    if ctype in ("text", "id"):
        col["n_distinct"] = len({_label(k).strip() for k in counts if not missing_by_key[k]})
    info = {"keys": keys, "counts": counts, "cls": cls, "missing_by_key": missing_by_key, "levels": levels,
            "tokens": tokens, "max_levels": max_levels,
            # strings typed next to numbers: the unit of each spelling (commonest spelling of each unit), per cell the
            # unit and flag, the example cells and their units, the censored examples that hold no free text
            "unit_counts": unit_keys, "unit_spell": {k: sp.most_common(1)[0][0] for k, sp in spellings.items()},
            "unit_of": unit_of, "flag_of": flag_of, "flag_counts": flags, "examples": examples, "example_unit": ex_unit,
            "cens_clean": clean if cens else collections.Counter()}
    return col, info


def _dash_pairs_as_compound(counts, cls):
    """Text values "120-80" (two numbers, the first larger, sizes of a blood pressure) are compound measurements
    when most such values of the column are: a range ("60-69", "1-5") has the smaller number first. Updates cls."""
    pairs = [(k, DASH_PAIR_RE.match(_nfkc(cls[k][1]))) for k in counts if cls[k][0] == "text" and cls[k][2] is None]
    pairs = [(k, int(m.group(1)), int(m.group(2))) for k, m in pairs if m]
    if len(pairs) >= 5 and sum(1 for _, a, b in pairs if a > b and 60 <= a <= 260 and 20 <= b <= 160) >= 0.8 * len(pairs):
        for k, _, _ in pairs:
            cls[k] = ("text", cls[k][1], "compound")


def _compound_hint(values, n, numeric):
    """The hint for two numbers in one cell: blood pressure (larger first, 60-260 / 20-160), a size (×), or another
    pair (visual acuity 20/40, a score 4/10) whose meaning the data dictionary gives."""
    pairs = [m for m in (_PAIR_RE.match(v) for v in values) if m]
    bp = pairs and sum(1 for m in pairs if int(m.group(1)) > int(m.group(2)) and 60 <= int(m.group(1)) <= 260
                       and 20 <= int(m.group(2)) <= 160) >= 0.8 * len(pairs)
    sizes = sum(1 for v in values if re.search(r"[0-9.]\s*(?:cm|mm|m)?\s*[×xX*]", v))
    tail = "；这些取值没有计入分布统计（只统计单个数值）" if numeric else ""
    if sizes >= 0.5 * len(values):
        return f"{n} 个取值是复合测量（一个单元格里两三个数字，如大小 3.5×2.1cm）：分析前需要拆成几列（如长径 / 短径）" + tail
    if bp:
        return f"{n} 个取值是复合测量（一个单元格里两个数字，如血压 120/80）：分析前需要拆成两列（收缩压 / 舒张压）" + tail
    return (f"{n} 个取值是一个单元格里的两个数字（复合测量，如视力 20/40、评分 4/10、比值）：是分数、比值还是两个测量，"
            "请按数据字典确认，需要时拆分或换算") + tail


def _prefer_year_first2(counts, cls):
    """Dates written with a 2-digit year in the first place ("19-01-16" = 2019-01-16) are read day first (16 Jan
    2019 would be "16-01-19"). When the first part of such a column takes few values while the last takes many
    (years first, days last), its dates are re-read year-month-day -> the hint, or None. Updates cls."""
    keys = []
    for k in counts:
        if k[0] == "s" and cls[k][0] in ("date", "text"):
            m = _YY_MM_DD_RE.match(_nfkc(k[1]))
            if m:
                keys.append((k, m))
    if len(keys) < 10 or sum(counts[k] for k, _ in keys) < 0.5 * sum(c for k, c in counts.items() if cls[k][0] != "blank"):
        return None
    firsts = {m.group(1) for _, m in keys}
    lasts = {m.group(4) for _, m in keys}
    if not (len(lasts) > 12 and len(firsts) * 2 < len(lasts)):
        return None
    new = {}
    for k, m in keys:
        d = _make_date(_year2(m.group(1)), int(m.group(3)), int(m.group(4)))
        if d is None and cls[k][0] == "date":
            return None                         # a valid d-m-y date that is no y-m-d one: keep the column as read
        if d is not None:
            new[k] = d
    sep = keys[0][1].group(2)
    for k, d in new.items():
        cls[k] = ("date", d, f"%y{sep}%m{sep}%d")
    return f"两位年份的日期按 年{sep}月{sep}日 顺序解读（第一段只有 {len(firsts)} 种取值、像年份，最后一段有 {len(lasts)} 种、像日）；请按导出系统核对"


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
        d = _parse_date(_nfkc(k[1]), month_first=True)
        if d:
            cls[k] = ("date", d[0], d[1])
    return True


def _is_free_text(levels, n_valid):
    """Mostly one-off values or long strings -> free text, not categories. Many levels that each
    recur (31 provinces, 60 ICD codes) stay categories."""
    n_levels = len(levels)
    total = sum(levels.values())
    if n_levels > 5 and sum(c for c in levels.values() if c == 1) >= 0.5 * max(n_valid, 1):
        return True
    if n_levels > 1000:
        return True
    return total > 0 and sum(len(str(lab)) * c for lab, c in levels.items()) / total > 30


def _date_details(counts, cls, missing_by_key):
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
           "unparseable_examples": [], "n_unparseable_unshown": 0, "formats": dict(fmts),
           "n_future": sum(c for v, c in stamps if v > tomorrow),
           "n_before_1900": sum(c for v, c in stamps if v.year < 1900), "notes": []}
    out["_bad"] = bad
    if stamps:
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
    sentinel = sum(c for v, c in stamps if (v.year, v.month, v.day) in SENTINEL_DATES)
    if sentinel:
        out["notes"].append(f"{sentinel} 个 1900-01-01（或 1899-12-30/31）：常见的占位/默认日期，可能表示缺失")
    return out


# ─── privacy: who holds a value ─────────────────────────────────────────────

class _Units:
    """Counts how many patients hold each value of a column -- when patients can be told apart.

    mode 'patient':  the patient ID repeats (--id, or the one column that _auto_patient_key accepts: named like a
                     patient identifier, values that repeat, 10+ of them, no visit labels): patients are its values.
    mode 'asserted': one row per patient (--rows-are-patients, or an --id with one row each): rows are patients.
    mode 'none':     nothing says which rows belong to the same patient (also: two or more columns could be the
                     automatic key): no text value is printed at all (counting rows would print any identifier that
                     repeats on a few rows of a long table).
    mode 'encoding': the file's bytes read clearly better in another encoding than the one used (_encoding_doubt):
                     no text value is printed either (a name read in the wrong encoding escapes the name rules)."""

    def __init__(self, n_rows, mode, groupings, source=None):
        self.n, self.mode, self.groupings, self.source = n_rows, mode, groupings, source   # groupings: [(name, labels)]
        self.names = [nm for nm, _ in groupings]
        # (every value of the key counts as one patient, also of the key the tool found itself -- no weighting;
        # there is at most one grouping: --id or the automatic key, see _auto_patient_key)

    @property
    def known(self):
        return self.mode in ("patient", "asserted")

    def per_value(self, keys, key_group, exclude=None):
        """keys: per-row cell keys; key_group: {key: group string or None} -> {group: n patients} (rows when
        patients are rows or unknown)."""
        gs = [(nm, lab) for nm, lab in self.groupings if nm != exclude]
        if not gs:
            rows = collections.Counter(key_group[k] for k in keys if key_group.get(k) is not None)
            if exclude is not None and exclude in self.names:
                return {g: 1 for g in rows}                 # the column is the patient key itself
            return dict(rows)
        best = None
        for nm_, lab in self.groupings:
            if nm_ == exclude:
                continue
            sets = collections.defaultdict(set)
            for k, u in zip(keys, lab):
                g = key_group.get(k)
                if g is not None and u is not None:
                    sets[g].add(u)
            cur = {g: len(s) for g, s in sets.items()}
            best = cur if best is None else {g: min(v, cur.get(g, v)) for g, v in best.items()}
        return best or {}

    @property
    def what(self):
        return "名患者" if self.known else "行"


def _rule_name(col):
    """The name the name rules read: the column's own name, also when the report shows it by its position."""
    return col.get("_rule_name") or col["name"]


def _level_groups(info):
    """{key: folded value} for the cells counted in a column's levels."""
    miss = info["missing_by_key"]
    return {k: (None if miss[k] or k[0] == "blank" else _fold(_label(k))) for k in info["counts"]}


def _script(v):
    """The script a value is written in: 'cjk', 'latin' or 'other'."""
    return "cjk" if re.search(r"[一-鿿가-힣぀-ヿ]", v) else "latin" if re.search(r"[^\W\d_]", v) else "other"


def _level_ctx(info):
    """What a column's text levels look like, for _level_shape_ok: the share of its different values shaped like
    a record number, and the scripts of the values that are no name."""
    by_fold = {}
    for k in info["counts"]:
        if not info["missing_by_key"][k] and k[0] != "blank":
            by_fold.setdefault(_fold(_label(k)), _nfkc(_label(k)))      # (shapes read the value as written, not folded)
    vals = [v for v in by_fold.values() if v][:3000]
    n = max(1, len(vals))
    return {"coded": sum(1 for v in vals if _record_code(v)) / n,
            "scripts": collections.Counter(_script(v) for v in vals if not _name_shaped(v))}


def _level_shape_ok(lab, ctx):
    """A text value that holds no identifier, so that it may be printed when enough patients share it: no
    phone / ID card / e-mail / person in it, no 7+ digits, no street address, no personal name of a strong
    shape -- and no name of a weaker shape written in another script than the column's other values (a name
    typed into an outcome or category column: "死亡 / 存活 / Testa Personne"; eponyms among other Latin
    categories -- "Stevens Johnson / Crohn Disease", "Han Chinese / Hui" -- stay), no record number in a column
    whose other values are none. The same rule for the category levels (section 6) and the outcome levels
    (section 9)."""
    s = _nfkc(lab)
    if _has_identifier(s) or _big_int_text(s) or _digit_groups_7(s) or ADDRESS_RE.search(s[:300]):
        return False
    k = _name_kind(s)
    if k == "strong":
        return False
    if k == "weak":
        others = ctx["scripts"]
        if others and others[_script(s)] < 0.5 * sum(others.values()):
            return False
    return not (_record_code(s) and ctx["coded"] < 0.5)


def _shown_ok(group, u, ctx):
    """A text value may be printed: held by at least SMALL_CELL_K patients and shaped like no identifier
    (_level_shape_ok; a record number shared by a family is still a record number)."""
    return u >= SMALL_CELL_K and _level_shape_ok(group, ctx)


def _shape_flags(col, info, units):
    """What the text values of a column look like when they look like identifiers: 姓名 (personal
    names; in a person-role column also a few shared ones), 地址 (street addresses), 编号 (record
    numbers), 文字里的姓名 (a person named in free text). Names and record numbers that many
    patients (or rows, when patients cannot be told apart) share (herbs, hospitals, lots, eponyms) are
    categories."""
    if col["type"] in ("numeric", "date", "empty") or (col["type"] == "id" and col["id_source"] != "value"):
        return []
    cls, counts, miss = info["cls"], info["counts"], info["missing_by_key"]
    texts = collections.Counter()
    for k, c in counts.items():
        if cls[k][0] == "text" and not miss[k]:
            texts[_nfkc(cls[k][1])] += c
    if len(texts) > 3000:                 # a free-text column: its commonest values decide its shape
        texts = collections.Counter(dict(texts.most_common(3000)))
    n = sum(texts.values())
    if not n:
        return []
    out = []
    # (when patients cannot be told apart rows are counted: nothing is printed then, this only decides
    # whether the column is listed as private)
    kg = {k: (_nfkc(cls[k][1]) if cls[k][0] == "text" and not miss[k] else None) for k in counts}
    per = units.per_value(info["keys"], kg, exclude=col["name"])
    shared = lambda vals: sum(texts[v] for v in vals if per.get(v, 0) >= SMALL_CELL_K) >= 0.5 * sum(texts[v] for v in vals)
    role = _is_person_role_name(_rule_name(col))
    named = [v for v in texts if _name_shaped(v)]
    # Chinese / Tibetan / Japanese / Korean names of a strong shape are people however many share one;
    # two capitalised words may be an eponym or a place ("Stevens Johnson", "Han Chinese")
    people = sum(texts[v] for v in named if _name_kind(v) == "strong" and not re.search(r"[A-Za-z]", v)) \
        >= 0.5 * max(1, sum(texts[v] for v in named))
    if role and named and sum(texts[v] for v in named) >= 0.5 * n and (len(texts) >= 5 or _names_column(texts, 1)):
        out.append("姓名")
    elif _names_column(texts) and (people or not (shared and shared(named))):
        out.append("姓名")
    if sum(c for v, c in texts.items() if ADDRESS_RE.search(v[:300])) >= 0.5 * n:
        out.append("地址")
    coded = [v for v in texts if _record_code(v)]
    if len(texts) >= 3 and n <= 20 * len(texts) and not _is_cluster_name(_rule_name(col)) and not col.get("compound") and \
            sum(texts[v] for v in coded) >= 0.9 * n and not (shared and shared(coded)):
        out.append("编号")
    # a person named in the text: one value after a role word or title, or a few with a name of another shape
    if "姓名" not in out and (any(_mentions_person(v, strict=True) for v in texts)
                             or sum(1 for v in texts if _mentions_person(v)) >= max(2, 0.05 * len(texts))):
        out.append("文字里的姓名")
    return out


def _birth_dates_shaped(col, info):
    """A date column whose values look like dates of birth whatever it is called ("d1", "date1"): they
    span 40+ years and most lie 30+ years back. Its range would print the oldest and the youngest
    patient's birthday."""
    if col["type"] != "date" or col["pii"]:
        return False
    years = []
    for k, c in info["counts"].items():
        if info["cls"][k][0] == "date" and not info["missing_by_key"][k]:
            years += [info["cls"][k][1].year] * min(c, 1000)
    if len(years) < 10:
        return False
    years.sort()
    return years[-1] - years[0] >= 40 and years[len(years) // 2] <= _dt.date.today().year - 30


# a date column named after an event (admission, surgery, diagnosis, visit ...): its range is never a birthday range
EVENT_DATE_NAME_RE = re.compile(
    r"入院|出院|住院|手术|术|诊断|确诊|随访|就诊|门诊|复诊|检查|检验|化验|采样|采血|标本|发病|起病|复发|进展|转移|死亡|去世|治疗|用药|服药"
    r"|化疗|放疗|入组|随机|知情|签署|开始|结束|停止|首次|末次|最后|登记|报告|影像|活检|事件|删失|截止|分娩|妊娠|末次月经|疫苗|接种"
    r"|admi|disch|surg|oper|(?:^|[^a-z])op(?:$|[^a-z])|diag|(?:^|[^a-z])dx(?:$|[^a-z])|visit|follow|(?:^|[^a-z])fu(?:$|[^a-z])"
    r"|exam|test|sampl|collect|specimen|onset|death|died|dod|progress|recur|relapse|metasta|treat|therap|chemo|radio|start|begin"
    r"|(?:^|[^a-z])end|stop|enrol|random|consent|last|first|report|scan|imag|biops|(?:^|[^a-z])lab|event|censor|contact|deliver"
    r"|pregnan|lmp|vaccin|dose|infus|transplant|implant|discharge|icu|ward|transfer", re.IGNORECASE)
BIRTH_LIKE_YEARS = 18


def _old_dates_as_years(col):
    """A date column whose name names no event ("d1", "date1", "日期1", "date_a"): an end of its range lying
    BIRTH_LIKE_YEARS or more years back may be the oldest / youngest patient's date of birth (a few dates of
    birth under a neutral name are not told apart from other dates) -- that end is shown as its year only."""
    d = col.get("date")
    if col["type"] != "date" or col["pii"] or not d or not d.get("min") or EVENT_DATE_NAME_RE.search(_name_forms(_rule_name(col))[0]):
        return
    cutoff = _dt.date.today().year - BIRTH_LIKE_YEARS
    sentinel = {f"{y:04d}-{m:02d}-{dd:02d}" for y, m, dd in SENTINEL_DATES}       # (a placeholder, no birthday)
    hit = [k for k in ("min", "max") if re.match(r"[0-9]{4}", d[k]) and int(d[k][:4]) <= cutoff and d[k] not in sentinel]
    for k in hit:
        d[k] = d[k][:4]
    if hit:
        d["years_only"] = hit
        d["notes"].append(f"日期多在 {BIRTH_LIKE_YEARS} 年以前、列名不像就诊/手术/随访等事件日期，可能是出生日期：范围的"
                          + ("两端" if len(hit) == 2 else "这一端") + "只显示年份")


def _identifying(col, info, units):
    """Almost every value belongs to a single patient (a name, record number or note per patient),
    whatever the column is called. Numbers and dates are measurements: never (a numeric record
    number is typed ID instead, keeping its --not-id hint) -- also dates written in a way this
    tool does not read ("3/25/23 14h", "2023-02-30")."""
    if col["type"] not in ("categorical", "text", "id") or col.get("id_source") == "value" or col.get("compound"):
        return False
    kg = _level_groups(info)
    present = [kg[k] for k in info["keys"] if kg.get(k) is not None]
    if len(present) < 5:
        return False
    distinct = set(present)
    if sum(1 for v in distinct if DATE_SHAPE_RE.match(v) or NOT_RECORD_RE.match(v) or TIME_OF_DAY_RE.match(v)) >= 0.8 * len(distinct):
        return False                      # dates, times of day; gene / sequence accessions and reagent lots
    per = units.per_value(info["keys"], kg, exclude=col["name"])
    single = sum(1 for v in present if per.get(v, 0) <= 1)
    return single >= 0.8 * len(present) and len(distinct) >= 2


def _redact(col):
    """Keep counts, drop every value of a column that turned out to identify patients."""
    col["pii"] = dict(col["pii"] or {"by_name": False, "id_card_hits": 0, "phone_hits": 0, "email_hits": 0,
                                     "looks_like": []}, unique_per_patient=True)
    _drop_values(col)


def _drop_values(col):
    """Keep counts, drop every value (levels, distribution, examples, date range) of a column."""
    col["categorical"] = None
    if col.get("numeric") is not None:
        col["numeric"] = None
    if col.get("censored"):
        col["censored"]["examples"] = []
        col["censored"].pop("n_unshown", None)
    nat = col.get("numeric_as_text")
    if nat:
        nat["examples"], nat["units"], nat["flags"] = [], {}, {}
        u = nat.get("unrecognised")
        if u:
            u["examples"] = []
    if col.get("date"):
        d = col["date"]
        d["unparseable_examples"] = []
        d.pop("min", None)
        d.pop("max", None)
    col["hints"] = [h for h in col["hints"] if not h.startswith(("只有 ", "同一列出现多种单位"))]


_VALUE_ID_WHY = {
    "all_different": "5 位以上的整数、几乎各不相同",
    "per_patient": "5 位以上的整数、同一名患者的各行相同、不同患者各不相同（每名患者一个值）",
    "repeats": "5 位以上的整数、每个取值在少数几行重复（像同一患者的各次记录）",
}


def _as_value_id(col, info, why="all_different"):
    """Type a numeric column that looks like a record number as ID: its values are not shown, and
    -- it may be a measurement (a baseline value, a cost), not an identifier -- the --not-id hint (also
    in the problem list) tells how to get its distribution back. Not a privacy redaction."""
    col["type"], col["type_label"], col["id_source"] = "id", TYPE_LABELS["id"], "value"
    col["n_distinct"] = len({_label(k).strip() for k in info["keys"] if not info["missing_by_key"][k]})
    _drop_values(col)
    col["hints"].append(f"按取值判为 ID：{_VALUE_ID_WHY.get(why, _VALUE_ID_WHY['all_different'])}，像病历号/住院号；"
                        "这只是类型判断，不是隐私判断。如果它是测量值（基线值、费用、计数），请加 --not-id 重新体检，才有分布统计")


def _record_number_like(col, info, id_labels=None):
    """A numeric column of whole numbers that behaves like a record number: 5+ digits and (almost)
    all different (also in a table of 3-19 rows); or, rows repeating per patient (id_labels), one
    value per patient and different between patients; or, without a patient ID, one block of
    consecutive rows per value (a long table sorted by patient) or each value on a few rows in any
    order (shuffled, sorted by date) -- then also of mixed length when most have 5+ digits, and only when
    the values repeat more than chance would make them in a column this long (50 000 step counts of
    1 000-25 000 tie by chance). Never when most of them are round numbers (counts such as platelets
    213000)."""
    if col["type"] != "numeric":
        return ""
    miss = info["missing_by_key"]
    whole = lambda v: v[:-len(m.group(1))] if (m := re.search(r"[0-9](\.0+)$", v)) else v    # "144048.0"
    vals = [None if miss[k] else whole(_label(k).strip()[:40]) for k in info["keys"]]
    present = [v for v in vals if v is not None]
    if len(present) < 3 or not all(len(v) <= 20 and re.fullmatch(r"[0-9]+", v) for v in present):
        return ""
    distinct = set(present)
    if _round_numbers(distinct):
        return ""
    long5 = sum(1 for v in distinct if len(v) >= 5)
    if len(distinct) >= 0.9 * len(present) and (long5 == len(distinct) or (
            long5 >= 0.5 * len(distinct) and max(int(v) for v in distinct) >= 1000 * max(1, min(int(v) for v in distinct)))):
        return "all_different"            # all different: 5+ digits, or mixed length over 3+ orders of magnitude
    if id_labels is not None:
        if long5 < 0.5 * len(distinct):
            return ""
        per, rows = collections.defaultdict(set), collections.Counter()
        for pid, v in zip(id_labels, vals):
            if pid is not None and v is not None:
                per[pid].add(v)
                rows[pid] += 1
        multi = [p for p in per if rows[p] > 1]      # one-row patients say nothing about constancy
        return "per_patient" if len(multi) >= 5 and sum(1 for p in multi if len(per[p]) == 1) >= 0.95 * len(multi) and \
            len({v for vs in per.values() for v in vs}) >= 0.8 * len(per) else ""
    # values drawn at random from a range of R numbers give about R * (1 - exp(-n / R)) different ones: a
    # measurement in a long table ties that often, a record number repeats far more
    lo, hi = min(int(v) for v in distinct), max(int(v) for v in distinct)
    span, n_p = hi - lo + 1, len(present)
    if span >= 1000 and n_p >= 0.2 * span and len(distinct) > 0.7 * span * (1 - math.exp(-n_p / span)):
        return ""
    runs = sum(1 for i, v in enumerate(present) if i == 0 or v != present[i - 1])
    if long5 == len(distinct) and len(distinct) >= 5 and runs == len(distinct) and len(present) >= 1.5 * len(distinct):
        return "repeats"
    reps = collections.Counter(present)
    return "repeats" if len(distinct) >= 3 and long5 >= 0.5 * len(distinct) and len(present) >= 1.5 * len(distinct) and \
        max(reps.values()) <= 20 and sum(c for c in reps.values() if c >= 2) >= 0.8 * len(present) else ""


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


def _numberish(col):
    """The column's values are numbers: a numeric column, or whole numbers typed ID by their values."""
    return col["type"] == "numeric" or (col["type"] == "id" and col.get("id_source") == "value")


def _outcome_levels(col, info):
    """The outcome's own value counts, all of them (not cut by --max-levels): spellings that differ
    only in case / spaces, or numbers written 1 / 1.0, are one value, labelled by the commonest
    spelling. -> ([[label, count], ...] most common first, merged?)"""
    cls, miss = info["cls"], info["missing_by_key"]
    groups, spell = collections.Counter(), collections.defaultdict(collections.Counter)
    for k, c in info["counts"].items():
        if miss[k] or cls[k][0] == "blank":
            continue
        g = ("n", cls[k][1]) if cls[k][0] in ("number", "loose") and _numberish(col) else ("s", _fold(_label(k)))
        groups[g] += c
        spell[g][_label(k)] += c
    out = [[spell[g].most_common(1)[0][0], c] for g, c in sorted(groups.items(), key=lambda kv: (-kv[1], str(kv[0])))]
    return out, any(len(s) > 1 for s in spell.values())


# outcome codes that are words of no one ("0 / 1", "是 / 否", "死亡 / 存活", "CR / PR"): printed whatever their count
PLAIN_OUTCOME_WORDS = frozenset(_fold(w) for w in """
是 否 有 无 無 yes no y n true false t f positive negative pos neg 阳性 阴性 陽性 陰性 + - ± 正常 异常 異常 良性 恶性 惡性
benign malignant 死亡 存活 生存 健在 活 死 alive dead deceased died death survived 失访 失訪 删失 截尾 censored lost
复发 復發 未复发 未復發 无复发 無復發 recurrence relapse no_recurrence 进展 進展 未进展 无进展 progression progressed stable
转移 轉移 无转移 治愈 痊愈 好转 好轉 有效 无效 無效 显效 缓解 緩解 完全缓解 部分缓解 稳定 疾病稳定 疾病进展 未愈 加重 恶化
cr pr sd pd ne orr ncr non-cr response responder non-responder nonresponder cured improved unchanged worse worsened
event no_event events 发生 未发生 事件 无事件 case control cases controls 病例 对照 男 女 male female m
低危 中危 高危 低 中 高 low intermediate medium high mild moderate severe 轻 中 重 轻度 中度 重度 i ii iii iv v
a b c d e g1 g2 g3 g4 1a 1b 2a 2b 3a 3b 4a 4b 合格 不合格 达标 未达标 满意 不满意 成功 失败 success failure fail
""".split())


def _plain_outcome_code(lab):
    s = _fold(lab)
    return bool(re.fullmatch(r"[-+]?[0-9]{1,3}(?:\.[0-9]+)?", s)) or s in PLAIN_OUTCOME_WORDS or \
        s.replace(" ", "_") in PLAIN_OUTCOME_WORDS


def _outcome_label_ok(lab, n_patients, known, ctx):
    """An outcome level may be printed: shaped like no identifier (_level_shape_ok, the rule of the category
    levels), and a plain code (0 / 1, 是 / 否, 死亡 / 存活 ...) or shared by >= SMALL_CELL_K patients (only
    countable when patients can be told apart)."""
    if not _level_shape_ok(lab, ctx):
        return False
    return _plain_outcome_code(_nfkc(lab)) or (known and n_patients >= SMALL_CELL_K)


def _numbers_of(col, info):
    """The column's valid numbers (numbers and numbers with units / flags), one per row."""
    cls, miss = info["cls"], info["missing_by_key"]
    vals, wts = [], []
    for k, c in info["counts"].items():
        if cls[k][0] in ("number", "loose") and not miss[k]:
            vals.append(cls[k][1])
            wts.append(c)
    return np.repeat(np.array(vals, dtype=float), np.array(wts, dtype=int)) if vals else np.array([])


def _number_summary(col, info):
    """n / min / median / max / mean / sd of a column's numbers, with 7+ digit whole numbers hidden."""
    if col.get("numeric"):
        s = dict(col["numeric"])
    else:
        s = _numeric_stats(_numbers_of(col, info))
        _hide_big_numbers(s, _n_big_ints(info))
    return s


def _outcome_summary(col, info, time, units, id_labels=None):
    """Only the outcome's OWN distribution. Nothing here looks at any other variable.

    With a patient ID whose rows repeat, events are also counted per patient: the number of
    patients with at least one event row is what limits the number of predictors, not the
    number of rows (the ID only says which rows belong together; it is not a predictor).
    A level is printed only when it is a plain code or shared by >= SMALL_CELL_K patients and holds no
    identifier; the others are shown as placeholders with their counts (event counts stay right)."""
    out = {"column": col["name"], "n_rows": col["n"], "n_missing": col["n_missing_total"],
           "n_valid": col["n_valid"], "kind": "empty", "levels": None, "event_label": None,
           "events": None, "non_events": None, "minority_count": None, "numeric": None,
           "time": None, "per_patient": None, "notes": []}
    levels, merged = _outcome_levels(col, info)
    # the label each level is printed under
    kg = {k: (None if info["missing_by_key"][k] or k[0] == "blank" else _fold(_label(k))) for k in info["counts"]}
    per = units.per_value(info["keys"], kg, exclude=col["name"]) if units.known else {}
    shown_as, n_masked, ctx = {}, 0, _level_ctx(info)
    for lab, _ in levels:
        if _outcome_label_ok(lab, per.get(_fold(lab), 0), units.known, ctx):
            shown_as[lab] = lab
        else:
            n_masked += 1
            shown_as[lab] = f"〔不显示的取值 {n_masked}〕"
    show = lambda lv: [[shown_as[lab], c] for lab, c in lv]
    numberish = _numberish(col)
    x = col["pii"] or {}
    # a privacy column by its name or its values (names, ID cards, one value per patient) shows nothing; one
    # whose few values name someone ("死亡（家属李娜告知）") shows its counts under placeholders
    if x and (x.get("by_name") or x.get("id_card_hits") or x.get("phone_hits") or x.get("email_hits")
              or x.get("unique_per_patient") or set(x.get("looks_like") or []) - {"文字里的姓名"}):
        out["notes"].append("该列疑似隐私字段，不显示取值")
    elif col["type"] == "date":
        out["kind"] = "date"
        out["notes"].append("结局列是日期（如死亡日期、复发日期）：作为结局需要一个“是否发生”的列和随访时间；"
                            "这里不按取值分类计数")
    elif col["type"] == "id" and not numberish:
        out["kind"] = "id"
        out["notes"].append("结局列被识别为 ID 样式（列名或取值像编号），不显示取值；请确认 --outcome 指定的列")
    elif len(levels) == 2 and col["type"] != "text":
        out.update(kind="binary", levels=show(levels))
        ev = _binary_event(levels)
        counts = dict((str(l), c) for l, c in levels)
        out["minority_count"] = min(counts.values())
        if merged:
            out["notes"].append("取值写法不一致（只差大小写/空格，或 1 与 1.0），已合并计数")
        group_of = _outcome_group_fn(col, info, levels)
        if ev is not None:
            out.update(event_label=shown_as.get(ev, ev), events=counts[ev], non_events=sum(counts.values()) - counts[ev])
            if id_labels is not None:
                out["per_patient"] = _events_per_patient(group_of, id_labels, ev)
        else:
            out["notes"].append("无法从编码判断哪一类是事件，请确认后按那一类的例数计事件数")
            if id_labels is not None:
                pp = _levels_per_patient(group_of, id_labels, [l for l, _ in levels])
                if pp:
                    pp["patients_by_level"] = {shown_as.get(l, l): n for l, n in pp["patients_by_level"].items()}
                out["per_patient"] = pp
    elif len(levels) == 1 and col["type"] != "text":
        out.update(kind="constant", levels=show(levels))
        out["notes"].append("结局只有一个取值")
    elif len(levels) > 2 and not numberish:
        out.update(kind="categorical", levels=show(levels[:30]))
        out["notes"].append(f"多分类结局（{len(levels)} 类）" + ("；只列出最常见的 30 类" if len(levels) > 30 else ""))
    elif numberish:
        s = _number_summary(col, info)
        if s.get("n"):
            out.update(kind="numeric", numeric={k: s.get(k) for k in ("n", "min", "median", "max", "mean", "sd")})
            if s.get("n_big_int"):
                out["notes"].append(f"有 {s['n_big_int']} 个 7 位以上的整数（像电话、证件号或病历号），最小/最大值等不显示")
        if len(levels) <= 10:                 # 3-10 whole values: a count, a score or a coded category
            out["levels"] = show(levels)
            out["notes"].append(f"数值结局只有 {len(levels)} 个不同取值：是计数、评分还是分类编码，请按数据字典确认")
    if col["type"] == "text":
        out["kind"] = "text"
        out["notes"].append("结局列像自由文本，需要先编码")
    key_note = ("的取值在多行重复、列名像患者 ID，报告其余部分用它区分患者（这一点不随 --outcome / --time 改变）；"
                "如果它不是患者 ID，请用 --id 指定真正的患者 ID 列")
    if col["name"] in units.names and units.source == "auto":
        out["notes"].append("结局列" + key_note)
    if n_masked and out["levels"] is not None:
        out["notes"].append(f"{n_masked} 个结局取值不显示（取值像标识符，或"
                            + ("不足 %d 名患者共有）" % SMALL_CELL_K if units.known else "无法区分患者、不是 0/1、是/否 这类编码）")
                            + "，只显示计数")
    if time is not None:
        tcol, tinfo = time
        out["time"] = {"column": tcol["name"], "n_valid": tcol["n_valid"], "n_missing": tcol["n_missing_total"],
                       "min": None, "median": None, "max": None, "n_nonpositive": None}
        if tcol["pii"]:
            out["time"]["note"] = "随访时间列疑似隐私字段，不显示取值"
        else:
            s = _number_summary(tcol, tinfo) if _numberish(tcol) else {}
            out["time"].update(min=s.get("min"), median=s.get("median"), max=s.get("max"),
                               n_nonpositive=(s.get("n_negative", 0) + s.get("n_zero", 0)) if s.get("n") else None)
            notes = []
            if tcol["type"] != "numeric":
                notes.append(f"随访时间列被识别为{tcol['type_label']}，请检查")
            if s.get("n_big_int"):
                notes.append(f"有 {s['n_big_int']} 个 7 位以上的整数（像电话、证件号或病历号），最大值等不显示")
            if tcol["name"] in units.names and units.source == "auto":
                notes.append("随访时间列" + key_note)
            if notes:
                out["time"]["note"] = "；".join(notes)
    return out


def _outcome_group_fn(col, info, levels):
    """Per-row outcome label (the level it was counted under) or None."""
    cls, miss = info["cls"], info["missing_by_key"]
    by_fold = {}
    for lab, _ in levels:
        by_fold[_fold(lab)] = lab
        if PLAIN_NUM_RE.match(str(lab).strip()):
            by_fold[("n", float(lab))] = lab
    out = []
    for k in info["keys"]:
        if miss[k] or cls[k][0] == "blank":
            out.append(None)
        elif cls[k][0] in ("number", "loose") and col["type"] == "numeric":
            out.append(by_fold.get(("n", cls[k][1])))
        else:
            out.append(by_fold.get(_fold(_label(k))))
    return out


def _one_row_each(id_labels):
    ids = [p for p in id_labels if p is not None]
    return len(ids) == len(set(ids))


def _events_per_patient(labels, id_labels, event_label):
    """Patients with >= 1 event row / without; patients whose rows disagree on the outcome."""
    if _one_row_each(id_labels):
        return None                                   # one row per patient: rows = patients
    per = collections.defaultdict(set)
    for pid, lab in zip(id_labels, labels):
        if pid is not None and lab is not None:
            per[pid].add(lab == event_label)
    if not per:
        return None
    with_event = sum(1 for v in per.values() if True in v)
    return {"n_patients": len(per), "patients_with_event": with_event,
            "patients_without_event": len(per) - with_event,
            "n_patients_mixed": sum(1 for v in per.values() if len(v) > 1)}


def _levels_per_patient(labels, id_labels, levels):
    """Two outcome codes, neither known to be the event (1 / 2): patients with each code."""
    if _one_row_each(id_labels):
        return None
    per = collections.defaultdict(set)
    for pid, lab in zip(id_labels, labels):
        if pid is not None and lab is not None:
            per[pid].add(lab)
    if not per:
        return None
    return {"n_patients": len(per), "patients_by_level": {str(l): sum(1 for v in per.values() if l in v) for l in levels},
            "n_patients_mixed": sum(1 for v in per.values() if len(v) > 1)}


def _header_issues(source, names):
    raw_header = source.get("raw_header")
    header = [str(h) for h in (raw_header if raw_header else names)]
    issues = []
    if source.get("encoding_warning"):
        issues.append(source["encoding_warning"])
    if source.get("header_mode") == "auto-none":
        issues.append("第一行看起来是数据（数字、日期、身份证号或手机号样式，或与下面各行的取值同类），不是列名：已按没有表头处理，"
                      "列名记为 列1、列2……；如果第一行确实是表头，请加 --header 重新体检")
    if source.get("title_rows"):
        k = source["title_rows"] + (source.get("skip_rows") or 0)
        issues.append(f"表头前像有 {source['title_rows']} 行标题或合并单元格（只有一两个非空单元格，下面各行字段更多）："
                      f"请加 --skip-rows {k} 重新体检，否则列名和列数可能不对"
                      + ("；标题行的文字可能含患者姓名或病历号，不作列名显示（列名记为 列1、列2……）"
                         if source.get("title_header_hidden") else ""))
    why = source.get("hidden_header_reasons") or []
    which = ("：" + "、".join(f"{nm}（{w}）" for nm, w in why[:10]) + ("等" if len(why) > 10 else "")) if why else ""
    if source.get("hidden_header") and source.get("transposed"):
        issues.append(f"表格看起来是转置的（每列一名患者：列名像人名或编号，或第一列是变量名、其余各列是数值），也可能列名是"
                      f"评分者/医生的姓名：{source['hidden_header']} 个列名用 列1、列2…… 代替，原列名不显示{which}。"
                      "转置的表请先转成每行一名患者（或一次就诊）再体检")
    elif source.get("hidden_header"):
        issues.append(f"{source['hidden_header']} 个列名像人名、编号或联系方式，报告里用 列1、列2…… 代替这些列名，原列名不显示{which}")
    if source.get("n_blank_rows"):
        issues.append(f"{source['n_blank_rows']} 行完全空白（常见于导出时末尾的空行），已忽略")
    q = source.get("quote_issues") or {}
    spans = lambda xs: "、".join(f"第 {a}–{b} 行" for a, b in xs[:5]) + ("等" if len(xs) > 5 else "")
    if q.get("merged_lines"):
        lost = sum(b - a for a, b in q["merged_lines"])
        issues.append(f"引号不配对：{spans(q['merged_lines'])}（每一段都被读成了一行：引号里包住了换行和分隔符，像是几行数据"
                      f"并进了一个单元格），共 {lost} 行数据没有单独体检。请在原软件里修正后重新导出（或另存为 .xlsx）")
    if q.get("multiline_cells"):
        issues.append(f"{len(q['multiline_cells'])} 条记录的单元格里有换行（{spans(q['multiline_cells'])}），已按单元格内换行读入；"
                      "如果原表没有这样的换行，说明引号不配对、几行被并进了一格")
    if q.get("bad_quote_lines"):
        lines = q["bad_quote_lines"]
        issues.append("引号用法不规范（结束引号后面还有字符，如 \"abc\"def）：第 " + "、".join(map(str, lines[:5]))
                      + (" 等" if len(lines) > 5 else "") + " 行；已按宽松规则读入（引号可能被去掉），请核对这些格")
    if source.get("n_header_copies"):
        issues.append(f"{source['n_header_copies']} 行与表头完全相同（可能是几次导出拼在一起），这些行被当成了数据")
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
        issues.append(f"{empty} 个列没有列名（表头可能不在第一行，或有合并单元格；可用 --skip-rows 跳过表头前的行）")
    spaced = [h for h in header if h.strip() and h != h.strip()]
    if spaced:
        issues.append("列名首尾有空格：" + "、".join(repr(h) for h in spaced[:10]))
    return issues


def _complete_row_exclusion(col):
    """Why a column does not count for "rows with no missing value" (None = it counts)."""
    if col["type"] == "empty":
        return "全列缺失"
    if col["type"] == "id":
        return "ID 列"
    if col["pii"]:
        return "疑似隐私字段"
    if REMARK_NAME_RE.search(_rule_name(col)):
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


def _split_tokens(tokens, names):
    """--missing-tokens items: 'tok' for every column, 'col=tok' for one column (unknown columns are
    an error) -> (global tokens, {column: [tokens]})."""
    glob, per = [], collections.defaultdict(list)
    for t in tokens:
        t = str(t)
        if "=" in t:
            c, tok = t.split("=", 1)
            if not c.strip():
                raise ValueError(f"--missing-tokens {t!r} 缺少列名：只用于某一列时写 列名=取值（如 age=0）")
            nm = _resolve_cols("--missing-tokens", [c.strip()], names)[0]
            per[nm].append(tok)
        else:
            glob.append(t)
    return glob, dict(per)


def _total_word(v):
    """A cell that names a summary row: 合计 / 总计 / 小计 / Total / 平均值 / Sum ..., also with a colon
    ("合计：", "Total:" -- NFKC turns "：" into ":") or a statistic after it ("均值±标准差", "Mean (SD)")."""
    if not isinstance(v, str) or not 1 <= len(v) <= 20:
        return False
    t = re.sub(r"\s+", "", _nfkc(v)).lower().rstrip(":")
    return t in TOTAL_WORDS or bool(TOTAL_STAT_RE.match(t))


def _total_rows(df, names):
    """Rows that sum up the others: a cell reading 合计 / 总计 / 小计 / Total / 平均值 ... while the
    row's other cells are empty, numbers or counts ("60人", "60 例") -> [(row number, word)]."""
    hits = {}
    n = len(df)
    for j in range(df.shape[1]):
        vals = df.iloc[:, j].tolist()
        freq = collections.Counter(v for v in vals if isinstance(v, str) and 1 <= len(v) <= 20)
        # a word many rows hold is a category ("Total / Subtotal / Lobectomy" thyroidectomy), not a summary row
        words = {v for v, c in freq.items() if _total_word(v) and c <= max(3, 0.05 * n)}
        if words:
            for i, v in enumerate(vals):
                if isinstance(v, str) and v in words:
                    hits.setdefault(i, _nfkc(v))
    out = []
    for i in sorted(hits):
        row = df.iloc[i].tolist()
        words = [v for v in row if isinstance(v, str) and v.strip() and not PLAIN_NUM_RE.match(_nfkc(v))
                 and not (len(v) <= 40 and _with_unit(_nfkc(v)))]
        if len(words) == 1:
            out.append((i + 1, hits[i]))
    return out


_FOOTER_WORD_RE = re.compile(r"^(?:注|备注|说明|制表|审核|复核|打印|导出|来源|数据来源|填表|签名|签字|核对|"
                             r"note|notes|source|printed|prepared|checked|generated|exported|reviewed|signed)", re.IGNORECASE)


def _footer_rows(df):
    """Rows at the end of the table holding only a note, a signature or a print time ("注：…", "制表人：…",
    "打印时间：…"): one or two non-empty cells while most rows fill three or more -> [row numbers]. Like total
    rows they stay in the statistics (the data are never changed) and are reported."""
    n, w = df.shape
    if n < 5 or w < 3:
        return []
    sample = df.iloc[:: max(1, n // 400)].values.tolist()          # (a typical row's width from a sample of rows)
    filled = sorted(sum(1 for v in r if not _is_blank(v)) for r in sample)
    if filled[len(filled) // 2] < 3:
        return []
    tail = df.iloc[max(0, n - 10):].values.tolist()
    out = []
    for i in range(n - 1, max(-1, n - 11), -1):
        cells = [v for v in tail[i - (n - len(tail))] if not _is_blank(v)]
        if not (1 <= len(cells) <= 2 and all(isinstance(v, str) and (_TITLE_KV_RE.match(_nfkc(v)[:100])
                                                                     or _FOOTER_WORD_RE.match(_nfkc(v)[:100])) for v in cells)):
            break
        out.append(i + 1)
    return sorted(out)


def _unit_row(df):
    """The first data row holds only units ("", "", "岁", "元" right under the header), over columns of numbers:
    it is read as one more patient."""
    if len(df) < 3:
        return False
    cells = [(j, v) for j, v in enumerate(df.iloc[0].tolist()) if not _is_blank(v)]
    if len(cells) < 2 or not all(isinstance(v, str) and not PLAIN_NUM_RE.match(_nfkc(v)) and _is_unit(_nfkc(v)) for _, v in cells):
        return False
    for j, _ in cells:
        below = [v for v in df.iloc[1:51, j].tolist() if not _is_blank(v)]
        if not below or sum(1 for v in below if _measured(v)) < 0.8 * len(below):
            return False
    return True


def profile_dataframe(df, id_col=None, outcome_col=None, time_col=None, cluster_cols=None,
                      missing_tokens=None, ranges=None, max_levels=15, source=None, not_id_cols=None,
                      rows_are_patients=False):
    """Structure / quality profile of one table -> JSON-serialisable dict.

    id_col       patient ID column (None: detect ID-like columns by name / values)
    outcome_col  outcome column(s): ONLY their own distribution and event count are reported
    time_col     follow-up time for a survival outcome (described on its own)
    cluster_cols centre / surgeon / reader columns (None: detect by name)
    missing_tokens extra disguised-missing spellings added to DEFAULT_MISSING_TOKENS; "col=tok"
                 adds one for that column only
    ranges       {'age': (0, 120)} plausible ranges; values outside are only counted
    source       meta dict from load_table() (file name, sha256, encoding, sheet ...)
    not_id_cols  columns that are measurements, never identifiers (all-different whole numbers
                 such as a cost would otherwise be typed ID and lose their distribution)
    rows_are_patients  the user says every row is a different patient (--rows-are-patients): category
                 values are then printed when at least SMALL_CELL_K rows hold them. Without it, and
                 without a patient ID (id_col, or the one automatic key of _auto_patient_key: named like a
                 patient identifier, values that repeat, 10+ of them, no visit labels), no category value
                 of any text column is printed.
    Column names may be given with the line breaks of a header cell typed as spaces.
    Nothing in this function relates one variable to another or to the outcome: rows are grouped
    only by the patient ID (--id, or an auto-detected patient identifier), and what is printed is
    decided without looking at the outcome (every column, the outcome too, is profiled the same way
    with and without outcome_col; only the outcome's own summary is added).
    """
    global _CROSS_READINGS
    prev = _CROSS_READINGS
    _CROSS_READINGS = _cross_readings((source or {}).get("codec"))
    try:
        return _profile_dataframe(df, id_col, outcome_col, time_col, cluster_cols, missing_tokens, ranges, max_levels, source,
                                  not_id_cols, rows_are_patients)
    finally:
        _CROSS_READINGS = prev


def _profile_dataframe(df, id_col, outcome_col, time_col, cluster_cols, missing_tokens, ranges, max_levels, source,
                       not_id_cols, rows_are_patients):
    """profile_dataframe, with the name rules also reading each value in the other East-Asian encodings of the file
    (_CROSS_READINGS)."""
    source = dict(source or {})
    if max_levels < 1:
        raise ValueError("--max-levels 至少为 1（每个分类列最多列出的取值数）")
    raw_names = _unique_names([str(c) for c in df.columns])
    hidden, transposed = _identifier_headers(raw_names)
    hidden = set(hidden)
    if _transposed_layout(df):             # patients as columns, whatever their names look like
        hidden, transposed = hidden | set(range(1, len(raw_names))), True
    names = [f"列{j + 1}" if j in hidden else nm for j, nm in enumerate(raw_names)]
    names = _unique_names(names)
    reasons = {j: _header_reason(raw_names[j]) for j in sorted(hidden)}
    if hidden:
        source["hidden_header"] = len(hidden)
        source["transposed"] = transposed
        source["hidden_header_reasons"] = [[names[j], why] for j, why in reasons.items()]
        if source.get("raw_header"):
            source["raw_header"] = [names[j] if j in hidden else h for j, h in enumerate(source["raw_header"])]
    try:
        ids, outs, times, clus, not_ids = (
            _resolve_cols(label, _split_cols(x, names), names)
            for label, x in (("--id", id_col), ("--outcome", outcome_col), ("--time", time_col),
                             ("--cluster", cluster_cols), ("--not-id", not_id_cols)))
        tok_list = _as_list(missing_tokens) if isinstance(missing_tokens, str) else list(missing_tokens or ())
        glob_tokens, col_tokens = _split_tokens(tok_list, names)
    except ValueError as e:
        if source.get("header_mode") == "auto-none":     # the header was taken for a data row
            raise ValueError(f"{e}——第一行看起来像数据，已按没有表头处理；如果第一行就是列名，请加 --header 重新体检")
        raise
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
    text_numbers_are_issue = source.get("format") != "csv"   # in a CSV every number is text
    vocab = _Vocab(glob_tokens)
    vocabs = {nm: _Vocab(glob_tokens, toks) for nm, toks in col_tokens.items()}

    n_rows = len(df)
    columns, infos = [], {}
    for j, name in enumerate(names):
        col, info = _profile_column(
            name, df.iloc[:, j].tolist(), vocabs.get(name, vocab), text_numbers_are_issue, max_levels,
            ranges.get(name), forced_id=bool(ids) and name == ids[0],
            # a declared measurement is never an ID (the outcome is profiled like any column)
            never_id=name in not_ids, rule_name=raw_names[j] if j in hidden else None)
        if j in hidden and not transposed:
            col["hints"].append(f"原列名{reasons[j]}，报告里用位置（{name}）代替，原列名不显示")
        columns.append(col)
        infos[name] = info
    by_name = {c["name"]: c for c in columns}

    row_tuples = collections.Counter(zip(*[infos[nm]["keys"] for nm in names])) if names else collections.Counter()
    n_dup_rows = sum(c - 1 for c in row_tuples.values() if c > 1)

    # ── the patient ID: --id, or the one column named like a patient identifier whose values repeat (_auto_patient_key) ──
    # (chosen without looking at --outcome / --time: an outcome named like a patient ID that repeats is still
    # the key -- the outcome entry says so -- so that nothing outside the outcome entry depends on --outcome)
    auto = _auto_patient_key(columns, infos, exclude=ids)
    auto_key = auto["key"]
    main_id = ids[0] if ids else auto_key
    main_labels = _row_labels(infos[main_id]["keys"], infos[main_id]["missing_by_key"]) if main_id else None
    informative = bool(main_id) and _id_structure(main_id, main_labels)["n_ids_multi"] > 0

    # ── record-number-like whole numbers are typed ID (judged on their own values; with a patient ID that
    # repeats, a record number is one value per patient, different between patients) ──
    skip_value_id = lambda nm: nm in ids or nm in not_ids or nm in clus
    for c in columns:
        nm = c["name"]
        if c["type"] == "numeric" and not skip_value_id(nm) and not c["pii"] and not _is_cluster_name(_rule_name(c)) and \
                not DATE_NAME_RE.search(_rule_name(c)):
            why = _record_number_like(c, infos[nm], main_labels if informative else None)
            if why:
                _as_value_id(c, infos[nm], why)
    id_names = ids or [c["name"] for c in columns if c["type"] == "id" and not _is_cluster_name(_rule_name(c))][:5]
    if main_id and main_id not in id_names:
        id_names = [main_id] + id_names[:4]
    structs = {nm: _id_structure(nm, _row_labels(infos[nm]["keys"], infos[nm]["missing_by_key"])) for nm in id_names}
    # two or more columns that could be the patient key: none is used -- also not the rows an --id of one value per row or
    # --rows-are-patients would count (a patient's own text on his rows would count as several patients); one line names them
    ambiguous = auto["ambiguous"] if not (informative and ids) else []
    passed_over = None if ambiguous else _id_choice_note(ids, main_id, id_names, by_name, structs, infos)
    id_structure = [dict(structs[nm], as_patient_id=nm == main_id, patient_id_name=_patient_key_named(by_name[nm]),
                         key_status=auto["status"].get(nm)) for nm in id_names]

    # ── who holds each value: patients (a repeating patient ID), rows (one row per patient), or nobody
    # knows -- decides what may be printed ──
    if informative and ids:
        units = _Units(n_rows, "patient", [(main_id, main_labels)], source="--id")
    elif auto_key:                         # --id has one value per row, a patient ID-named column repeats
        units = _Units(n_rows, "patient", [(auto_key, _row_labels(infos[auto_key]["keys"], infos[auto_key]["missing_by_key"]))],
                       source="auto")
    elif (ids or rows_are_patients) and not ambiguous:
        units = _Units(n_rows, "asserted", [], source="--id" if ids else "--rows-are-patients")
    else:
        units = _Units(n_rows, "none", [])
    if source.get("encoding_doubt"):         # the bytes read better in another encoding: no text value at all
        units = _Units(n_rows, "encoding", [], source="encoding")
    for c in columns:
        nm = c["name"]
        looks = _shape_flags(c, infos[nm], units) + (["出生日期"] if _birth_dates_shaped(c, infos[nm]) else [])
        if looks and not c["pii"]:
            c["pii"] = {"by_name": False, "id_card_hits": 0, "phone_hits": 0, "email_hits": 0,
                        "looks_like": looks, "unique_per_patient": False}
        elif looks:
            c["pii"]["looks_like"] = looks
    for c in columns:
        _old_dates_as_years(c)
    for c in columns:
        nm = c["name"]
        if nm in id_names or nm in not_ids or nm in clus or c["pii"] or c["type"] == "id":
            continue                       # (privacy and ID columns print no value)
        if _identifying(c, infos[nm], units):
            _redact(c)
    for c in columns:
        if c["pii"]:
            c["contact_cells"] = None
            _drop_values(c)
        _gate_values(c, infos[c["name"]], units)
    # without a patient unit, the columns that may be the patient ID: record numbers that repeat (typed ID by
    # their values), and columns named like a patient ID (one value per row in a table of one row per patient)
    id_hint = [] if units.mode != "none" else list(dict.fromkeys(
        ambiguous + auto["visit_valued"] +
        [s_["column"] for s_ in id_structure if s_["n_ids_multi"] >= 3 and by_name[s_["column"]].get("id_source") == "value"] +
        [c["name"] for c in columns if c["type"] == "id" and c.get("id_source") == "name" and _is_patient_id_name(_rule_name(c))
         and not PER_ROW_NAME_RE.search(_name_forms(_rule_name(c))[0])]))

    # ── complete rows: over the analysable columns only (see _complete_row_exclusion) ──
    excluded = {c["name"]: why for c in columns for why in [_complete_row_exclusion(c)] if why}
    any_missing = np.zeros(n_rows, dtype=bool)
    for nm in names:
        if nm not in excluded:
            miss = infos[nm]["missing_by_key"]
            any_missing |= np.fromiter((miss[k] for k in infos[nm]["keys"]), dtype=bool, count=n_rows)
    if clus:
        cluster_names = clus
    else:
        cluster_names = []
        for c in columns:
            # a surgeon / batch column holding names / codes is still a cluster (only counts are shown)
            x = c["pii"] or {}
            strong_pii = x and (set(x.get("looks_like", [])) - {"姓名", "编号"} or x["by_name"] or x["id_card_hits"]
                                or x["phone_hits"] or x.get("email_hits") or x.get("unique_per_patient"))
            if c["name"] in id_names or strong_pii or not _is_cluster_name(_rule_name(c)):
                continue
            num = c.get("numeric") or {}
            if c["type"] in ("categorical", "id", "text") or (c["type"] == "numeric" and 0 < num.get("n_distinct", 99) <= 50) \
                    or (c["type"] == "numeric" and x):
                cluster_names.append(c["name"])
    pid_for_groups = main_labels if informative else None
    clusters = [_cluster_structure(nm, _row_labels(infos[nm]["keys"], infos[nm]["missing_by_key"]),
                                   pid_for_groups if nm != main_id else None) for nm in cluster_names]

    # ── outcome: its own distribution only ──
    outcomes = []
    for i, nm in enumerate(outs):
        tcol = (by_name[times[0]], infos[times[0]]) if (times and i == 0) else None
        outcomes.append(_outcome_summary(by_name[nm], infos[nm], tcol, units,
                                         pid_for_groups if nm != main_id else None))

    for c in columns:
        if c.get("date"):
            c["date"].pop("_bad", None)
    type_counts = collections.Counter(c["type"] for c in columns)
    profile = {
        "tool": "data_profile.py", "statement": STATEMENT,
        "generated": _dt.date.today().isoformat(),
        "source": {k: v for k, v in source.items() if k != "raw_header"},
        "n_rows": n_rows, "n_cols": len(names),
        "type_counts": {TYPE_LABELS[t]: type_counts.get(t, 0) for t in TYPE_LABELS},
        "header_issues": _header_issues(source, names),
        "n_duplicate_rows": int(n_dup_rows),
        "n_complete_rows": int(n_rows - any_missing.sum()),
        "complete_rows_basis": {"n_columns": len(names) - len(excluded), "excluded": excluded},
        "range_notes": [f"--range {_disp(nm)} 没有用上：该列识别为{by_name[nm]['type_label']}，不是数值列"
                        for nm in ranges if by_name[nm]["type"] != "numeric"],
        "columns": columns, "id_structure": id_structure, "clusters": clusters, "outcomes": outcomes,
        "privacy": [{"column": c["name"], **c["pii"]} for c in columns if c["pii"]],
        "privacy_units": {"mode": units.mode, "columns": [nm for nm in units.names], "source": units.source,
                          "id_hint": id_hint, "rows_are_patients": bool(rows_are_patients),
                          "conflict": bool(rows_are_patients) and units.mode == "patient",
                          # (the automatic key: 2+ qualifying columns -> none; patient-ID-named columns of visit labels)
                          "ambiguous": ambiguous if units.mode == "none" else [],
                          "visit_valued": auto["visit_valued"] if units.mode == "none" and not ambiguous else [],
                          "id_given": ids[0] if ids else None},
        "missing_tokens": {"default": [t for t in DEFAULT_MISSING_TOKENS if t], "added": vocab.extra,
                           "by_column": {nm: list(t) for nm, t in col_tokens.items()},
                           "ambiguous": sorted(vocab.ambiguous)},
        "total_rows": [{"row": r, "word": w} for r, w in _total_rows(df, names)[:20]],
        "footer_rows": [{"row": r} for r in _footer_rows(df)],
        "unit_row": _unit_row(df),
        "id_choice": passed_over,
    }
    for c in columns:
        c.pop("_rule_name", None)            # (internal: a masked column's own name is never printed)
    profile["problems"] = _problems(profile)
    return _json_safe(profile)


# per-row numbers (a row, visit, sample or test number): never a patient key, however they repeat
PER_ROW_NAME_RE = re.compile(r"序号|行号|流水号|检验号|化验号|标本号|样本号|申请单?号|条码|医嘱号|检查号|报告号|就诊号|随访号|病理号|影像号"
                             r"|^(?:no|nr|#|index|idx|row)\.?$|^row[\s_\-.#]|^unnamed|visit|encounter|admission|specimen|sample"
                             r"|accession|order|report|lab[\s_\-.]*(?:no|id|number)", re.IGNORECASE)


# ── the automatic patient key (no --id): a deterministic rule on a column's NAME and its SET of values, never on how
# many rows each value has (_auto_patient_key) ──
# a visit / time / sample word in the name of a patient-ID-named column ("住院号_第2次", "patient_id_visit", "病案号(入院)",
# "pid_day", "MRN_sample", "住院次数"): it numbers visits, days or samples -- never an automatic key (rule 1)
VISIT_NAME_RE = re.compile(
    r"visit|follow[\s_\-.]*up|cycle|time|week|day|hour|month|year|sample|specimen|encounter|admission|admit|episode|session"
    r"|(?:^|[^a-z])(?:fu|pod|tp|wk|hr|mo|yr|adm)(?:$|[^a-z])"
    r"|随访|访视|复查|复诊|疗程|周期|次|第|天|日|周|月|年|时间|时点|小时|标本|样本|检验|化验|入院|出院", re.IGNORECASE)
AUTO_KEY_MIN_VALUES = 10

# visit / time / ordinal / sample labels (rule 2). A value is read as numbers -- Arabic ("1", "05", "5.1"), Chinese ("一",
# "十二"), Roman ("II", "Ⅳ") -- and words, and every word must be one a visit, a time point, a treatment course or a sample is
# called by:
#   STRONG words, never part of a patient code: "V", "visit", "FU", "follow-up", "POD", "day", "week", "month", "year",
#     "hour", "time", "cycle", "course", "session", "dose", "fraction", "sample", "specimen", "draw", "biopsy", "baseline",
#     "screening", "pre", "post", "repeat", "unscheduled", "end", "first".."twentieth", "lost", "died" ...; 第, 次, 随访,
#     访视, 复查, 复诊, 化疗, 放疗, 疗程, 周期, 住院, 门诊, 入院, 出院, 标本, 样本, 采血, 术前, 术后, 基线, 筛选, 治疗, 用药,
#     首次, 末次, 失访, 死亡 ...;
#   WEAK words a patient code may also start with: one letter "T", "D", "W", "M", "Y", "H" and short units "TP", "wk",
#     "mo", "yr", "hr", "min", "Fx", "Tx", "BL", "st"/"nd"/"rd"/"th", 天, 日, 周, 月, 年, 个月, 小时 ...;
#   fillers that are neither: "of", "to", "no", "number", "study", 前, 后, 补, 加, 号, 份 ...;
#   and, next to a strong word, a single letter ("Visit A", "V3a"). A word that names the patient ("patient", "case",
#   "subject", "pt", "ID", 例, 患者, 病例, 受试者) or any other word makes the value no label.
# So "第1次随访", "随访第3次", "化疗第2周期", "Visit 1 (Week 2)", "First visit", "Visit A", "V1D1", "V1.0", "V3a", "Day 3
# repeat", "第3次(补)", "Session 4", "Dose 2", "Sample 5", "标本5", "Post1", "Fx3" are labels; "P001", "S-01", "C01", "No.12",
# "ZY000123", "Case 3", "Study-001" are not. After weak words only, zero padding wider than the largest number needs makes
# a code ("T001".."T040", "D001").
_VL_STRONG_LATIN = (
    "v vis visit visits fu followup follow pod day days week weeks month months year years hour hours minute minutes time "
    "times timepoint timepoints cycle cycles course courses session sessions dose doses dosing fraction fractions sample "
    "samples specimen specimens aliquot aliquots tube tubes draw draws collection collections biopsy biopsies infusion "
    "infusions injection injections treatment treatments therapy assessment assessments exam exams examination "
    "measurement measurements replicate replicates repeat repeated retest recheck rescreen round rounds wave waves occasion "
    "occasions period periods phase phases interim baseline screening screen enrollment enrolment enrol enroll entry "
    "randomization randomisation randomized randomised pre post preop postop pretreatment posttreatment end final last first "
    "second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth fifteenth sixteenth "
    "seventeenth eighteenth nineteenth twentieth unscheduled unsched unplanned discharge admission admit readmission "
    "encounter episode operation surgery postoperative preoperative termination lost ltfu died death dead deceased "
    "withdrawn withdrawal dropout dropped endoftreatment endofstudy earlytermination blood urine serum plasma tissue saliva "
    "stool swab csf scan scans imaging mri hospitalization hospitalisation stay appointment appointments appt "
    "consultation consult checkup questionnaire questionnaires survey surveys phone telephone call calls").split()
_VL_WEAK_LATIN = "t d w m y h tp wk wks mo mos yr yrs hr hrs min mins st nd rd th fx tx rx op bl scr et eot eos rep rpt".split()
_VL_FILL_LATIN = ("of to at on in the and or after before from since up no nr num number study early next prior extra additional plus "
                  "per am pm morning evening night").split()
_VL_PATIENT_LATIN = "patient patients pt pts pat case cases subject subj sub participant id".split()
_VL_LATIN = {**{w: "fill" for w in _VL_FILL_LATIN}, **{w: "weak" for w in _VL_WEAK_LATIN},
             **{w: "strong" for w in _VL_STRONG_LATIN}, **{w: "patient" for w in _VL_PATIENT_LATIN}, "v": "v"}
_VL_CJK = {**{w: "fill" for w in "前 后 补 加 复 份 个 号 的 之 内 共 约 再 初 首 再次 初次 其 他 早 晚 上午 下午 晚上 夜间".split()},
           **{w: "weak" for w in "天 日 周 月 年 个月 小时 分钟 时 分 周末 星期".split()},
           **{w: "strong" for w in (
               "第 次 随访 访视 回访 复查 复诊 复检 化疗 放疗 疗程 周期 住院 门诊 入院 出院 转院 标本 样本 采血 采样 抽血 留样 术前 术后 "
               "基线 筛选 筛查 治疗 用药 给药 首次 末次 初诊 检查 时点 阶段 期 失访 死亡 退出 脱落 中止 终止 结束 计划外 随机 入组 化验 "
               "检验 检测 疗 剂 访 诊 手术 观察 评估 测量 测定 访问 就诊 复测 重复 加测 补测 补充 管 轮 针 血样 血清 血浆 尿样 活检 穿刺 影像 扫描 问卷 "
               "量表 电话 微信 短信 信函 现场 线上 线下 家访").split()},
           **{w: "patient" for w in "例 患者 病人 病例 受试者 患儿".split()}}
_VL_CJK_MAXLEN = max(len(w) for w in _VL_CJK)
_VL_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")
_VL_TOKEN_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?|[a-z]+|[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+|[^\W\d_]")
_VISIT_WORDS = frozenset(
    "baseline bl screening screen scr enrollment enrolment entry randomization randomisation pre post preop postop pretreatment "
    "posttreatment end eot eos et final last first unscheduled discharge admission followup fu endoftreatment endofstudy "
    "earlytermination 基线 筛选 筛选期 入组 随机 术前 术后 出院 入院 末次 末次随访 首次 初诊 复诊 复查 治疗前 治疗后 随访 计划外 提前终止 "
    "治疗结束 结束 用药前 用药后".split())
_ROMAN_1_12 = {r: i + 1 for i, r in enumerate("i ii iii iv v vi vii viii ix x xi xii".split())}
_CN_NUM_CHARS = "零〇一二两三四五六七八九十百"
_CN_NUM_RE = re.compile(r"(?:([一二两三四五六七八九])百零?)?(?:([一二两三四五六七八九]?)(十))?([零〇一二两三四五六七八九])?")
_CN_DIGITS = dict(zip("零〇一二两三四五六七八九", (0, 0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9)))
_CYCLE_DAY_RE = re.compile(r"(?:c|cycle)[\s_\-.]{0,2}([0-9]{1,3})[\s_\-.]{0,2}(?:d|day)[\s_\-.]{0,2}([0-9]{1,3})", re.IGNORECASE)
_BARE_NUMBER_RE = re.compile(r"[#＃]?\s*(-?)\s*([0-9]{1,15})(?:\.0+)?")


def _cn_int(s):
    """A Chinese numeral below 1000 ("一", "十二", "二十", "一百零五") -> int, else None."""
    m = _CN_NUM_RE.fullmatch(s)
    if not s or not m:
        return None
    return ((_CN_DIGITS[m.group(1)] * 100 if m.group(1) else 0) + ((_CN_DIGITS[m.group(2)] if m.group(2) else 1) * 10 if m.group(3) else 0)
            + (_CN_DIGITS[m.group(4)] if m.group(4) else 0))


@functools.lru_cache(maxsize=4096)
def _latin_words(tok):
    """A run of Latin letters -> the kinds of its words ("strong", "weak", "fill", "patient", "v", "letter", ("num", n) for a
    Roman numeral II-XII), splitting a compound of vocabulary words of 2+ letters ("followup", "firstvisit", "endoftreatment");
    None when some part is no visit vocabulary."""
    if tok in _VL_LATIN:
        return (_VL_LATIN[tok],)
    if len(tok) == 1:
        return ("letter",)
    if tok in _ROMAN_1_12:
        return (("num", _ROMAN_1_12[tok]),)
    if len(tok) > 40:
        return None
    for i in range(len(tok) - 1, 1, -1):
        head, rest = tok[:i], tok[i:]
        if head not in _VL_LATIN:
            continue
        if len(rest) == 1:                 # "visita": a strong word and an ordinal letter
            if _VL_LATIN[head] == "strong":
                return "strong", "letter"
            continue
        tail = _latin_words(rest)
        if tail is not None and "letter" not in tail:
            return (_VL_LATIN[head],) + tail
    return None


def _cjk_words(run):
    """A run of CJK characters -> ([(kind, word) ...], its Chinese numerals), longest vocabulary word first; a character that
    is neither a visit word nor part of a numeral is ("unknown", ch)."""
    words, nums, i = [], [], 0
    while i < len(run):
        for n in range(min(_VL_CJK_MAXLEN, len(run) - i), 0, -1):
            if run[i:i + n] in _VL_CJK:
                words.append((_VL_CJK[run[i:i + n]], run[i:i + n]))
                i += n
                break
        else:
            j = i
            while j < len(run) and run[j] in _CN_NUM_CHARS:
                j += 1
            val = _cn_int(run[i:j]) if j > i else None
            if val is None:
                words.append(("unknown", run[i]))
                i += 1
            else:
                nums.append(val)
                i = j
    return words, nums


def _visit_value(v):
    """One value (NFKC, lower case) read as a visit / time / ordinal / sample label (rule 2):
      ("word", strong)            no number: a visit word ("baseline", "First visit", "术前", "末次随访"; strong) or an ordinal
                                  on its own -- a Roman numeral I-XII, a single letter, a Chinese numeral (not strong);
      ("bare", n, width)          a bare whole number ("12", "#12", "012", "-1", "3.0");
      ("label", n, width, kind, top)  a number with visit words: n its first number (None for "Visit A"), width the widest
                                  Arabic number written, kind "strong" / "v" (only the letter V) / "weak", top its largest number;
      None                        anything else (a patient code, a name, a word that is no visit word)."""
    if len(v) > 80:
        return None                        # (a label is short; keeps long cells linear)
    compact = re.sub(r"[\s_\-.]+", "", v)
    if compact in _VISIT_WORDS:
        return "word", True
    if compact in _ROMAN_1_12 or re.fullmatch(r"[a-z]", compact):
        return "word", False
    m = _BARE_NUMBER_RE.fullmatch(v)
    if m:
        return "bare", int(m.group(2)) * (-1 if m.group(1) else 1), len(m.group(2))
    m = _CYCLE_DAY_RE.fullmatch(v)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return "label", a, max(len(m.group(1)), len(m.group(2))), "strong", max(a, b)
    kinds, nums, widths, anchor, cjk = [], [], [0], False, set()
    for t in _VL_TOKEN_RE.findall(re.sub(r"(?<![a-z])f\s*/\s*u(?![a-z])", "fu", v)):
        if t[0].isdigit():
            whole = t.split(".")[0]
            nums.append(int(whole))
            widths.append(len(whole))
        elif "a" <= t[0] <= "z":
            words = _latin_words(t) or ("unknown",)
            for k in words:
                if isinstance(k, tuple):
                    nums.append(k[1])
                else:
                    kinds.append(k)
            anchor = anchor or ("strong" in words and len(t) >= 3)
        elif _VL_CJK_RE.match(t):
            words, cn = _cjk_words(t)
            kinds += [k for k, _ in words]
            nums += cn
            cjk.update(w for k, w in words if k == "strong")
            anchor = anchor or any(k == "strong" and len(w) >= 2 for k, w in words)
        else:
            kinds.append("unknown")        # a letter of another script
    if "patient" in kinds:
        return None                        # "Case 3", "Patient 12", "第3例": numbers patients, not visits
    if "unknown" in kinds and not (anchor or {"第", "次"} <= cjk):
        return None                        # another word: only next to a visit word of its own ("随访3（电话）", "张三第1次")
    kind = "strong" if "strong" in kinds else "v" if "v" in kinds else "weak" if "weak" in kinds else None
    if kind is None:
        # only numbers (and fillers): a Chinese numeral alone ("十二") is an ordinal; "No.12" / "12号" number patients
        return ("word", False) if nums and not kinds and widths == [0] else None
    if "letter" in kinds and kind == "weak":
        return None                        # "D3a": a letter needs a strong word next to it
    if not nums:
        return "word", kind != "weak"
    return "label", nums[0], max(widths), kind, max(nums)


def _visit_labels(values):
    """Rule 2 of the automatic patient key: the column's different values are visit / time / ordinal / sample labels
    (_visit_value) -- at most one in ten of them being anything else:
      * numbers with visit words: their numbers at most 1000, at most 60 different first numbers or 0/1..k without a gap;
        after weak words only ("T", "D", "M", "wk", 天 ...), zero padding wider than the largest number needs makes a code
        ("T001".."T040", "D001".."D012");
      * visit words, Roman numerals I-XII, single letters, Chinese numerals on their own;
      * bare whole numbers only when they start at 0 or below and go up to 400 (a 0..k index, a schedule 0 / 1 / 3 / 6 /
        12 ..., days -1 / 0 / 1 ...) -- unless padded wider than needed ("000".."039") -- or, up to 1000, next to a visit
        word or label in the same column ("baseline, 1, 2 ...", "1..12, 失访, 死亡"). Bare numbers from 1 on their own (1..N,
        001..0NN, 1 / 4 / 7 ...) are patient numbers: from the set of values a 1..k visit index cannot be told apart from
        patients numbered 1..N, and only a 0..k run names a visit index (a patient is not numbered 0).
    Patient codes are none ("P001", "S-01", "C01", "No.12", "ZY000123", "A2001", "T001".."T040", 1..N, 001..0NN, names).
    Looks at the set of values only (not at how many rows hold each)."""
    vals = {_nfkc(str(v)).strip().lower() for v in values if v is not None}
    vals.discard("")
    if len(vals) < 2:
        return False
    other, bare, labels, marked = 0, {}, {}, False
    for v in vals:
        x = _visit_value(v)
        if x is None:
            other += 1
            if other > len(vals) // 10:
                return False
        elif x[0] == "word":
            marked = marked or x[1]
        elif x[0] == "bare":
            bare[v] = x[1:]
        else:
            labels[v] = x[1:]
    weak = {v: x for v, x in labels.items() if x[2] == "weak"}
    if weak:
        top = max(x[3] for x in weak.values())
        if max(x[1] for x in weak.values()) > len(str(top)):
            for v in weak:                 # "T001".."T040": codes
                labels.pop(v)
            other += len(weak)
    if labels:
        firsts = sorted({x[0] for x in labels.values() if x[0] is not None})
        if max(x[3] for x in labels.values()) > 1000 or (len(firsts) > 60 and not (
                firsts[0] in (0, 1) and firsts == list(range(firsts[0], firsts[-1] + 1)))):
            other += len(labels)
            labels = {}
    marked = marked or bool(labels)
    if bare:
        ints = sorted({n for n, _ in bare.values()})
        padded = max(wd for _, wd in bare.values()) > len(str(max(abs(ints[0]), abs(ints[-1]))))
        if not ((ints[0] <= 0 and ints[-1] <= 400 and not padded) or (marked and ints[-1] <= 1000)):
            other += len(bare)
    return len(vals) - other >= 2 and other <= len(vals) // 10


def _auto_patient_key(columns, infos, exclude=()):
    """The automatic patient key (no --id, or an --id with one value per row): a deterministic rule on each column's name
    and its set of values -- nothing about how many rows each value has is used to accept or reject it.
      1. the name clearly names the patient (_patient_key_named: patient_id, pid, pt_id, subject_id, case_id, 患者编号, 病人ID,
         住院号, 病案号, 病历号, 门诊号, 研究编号, 受试者编号, MRN, Hospital Number ...; never a per-row number such as 序号 /
         No. / visit_id / 检验号, nor a centre / surgeon) and holds no visit / time / sample word (VISIT_NAME_RE), and its values
         repeat (some value on two or more rows) with at least AUTO_KEY_MIN_VALUES (10) different values;
      2. values that look like visit / time / ordinal / sample labels (_visit_labels: "第1次随访", "随访一", "V1", "Visit A",
         "Day 3 repeat", "Sample 5", "baseline", Roman numerals, single letters, bare numbers from 0 ...) disqualify it, whatever
         its name -- bare numbers from 1 (1..N, 001..0NN) are patient numbers;
      3. when two or more columns qualify, none is used (the problem list names them and asks for --id).
    Every value of the key counts as one patient. Never looks at --outcome.
    -> {"key": name or None, "status": {column: why}, "ambiguous": [the qualifying columns when 2+],
    "visit_valued": [patient-ID-named columns that failed rule 2]}; why: "key", "ambiguous", "visit_name", "visit_values",
    "few_values" (fewer than 10 values), "no_repeats" (one row each)."""
    status = {}
    for c in columns:
        nm = c["name"]
        if nm in exclude or not _patient_key_named(c):
            continue
        counts = collections.Counter(v for v in _row_labels(infos[nm]["keys"], infos[nm]["missing_by_key"]) if v is not None)
        low, compact = _name_forms(_rule_name(c))
        if VISIT_NAME_RE.search(low) or VISIT_NAME_RE.search(compact):
            status[nm] = "visit_name"
        elif not counts or max(counts.values()) < 2:
            status[nm] = "no_repeats"
        elif _visit_labels(counts):
            status[nm] = "visit_values"
        elif len(counts) < AUTO_KEY_MIN_VALUES:
            status[nm] = "few_values"
        else:
            status[nm] = "qualifies"
    found = [nm for nm, why in status.items() if why == "qualifies"]
    key = found[0] if len(found) == 1 else None
    for nm in found:
        status[nm] = "key" if key else "ambiguous"
    return {"key": key, "status": status, "ambiguous": found if len(found) > 1 else [],
            "visit_valued": [nm for nm, why in status.items() if why == "visit_values"]}


def _patient_key_named(c):
    """A column named like a patient identifier, typed ID by its name (or a record number by its privacy word);
    never a cluster or a per-row number."""
    rn = _rule_name(c)
    low, compact = _name_forms(rn)
    if _is_cluster_name(rn) or PER_ROW_NAME_RE.search(low) or PER_ROW_NAME_RE.search(compact) or c["type"] in ("empty", "date"):
        return False
    return (c["type"] == "id" and c.get("id_source") in ("name", "forced") and
            (_is_patient_id_name(rn) or low in AMBIGUOUS_ID_NAMES)) or _pii_name_kind(rn) == "record"


def _id_choice_note(ids, main_id, id_names, by_name, structs, infos):
    """A note about the patient ID choice (or None): --id has one value per row while another ID column
    repeats like a patient ID; or rows are grouped by a repeating ID while per-row numbers (序号,
    就诊流水号, 标本号) sit next to it."""
    if ids:
        if structs[main_id]["n_ids_multi"] == 0:
            alt = [nm for nm, c in by_name.items() if nm != main_id and c["type"] == "id" and not _is_cluster_name(_rule_name(c))
                   and (c.get("id_source") == "value" or _is_patient_id_name(_rule_name(c)))]
            rep = [nm for nm in alt
                   if _id_structure(nm, _row_labels(infos[nm]["keys"], infos[nm]["missing_by_key"]))["n_ids_multi"] >= 3]
            if rep:
                return {"used": main_id, "repeating": rep[0], "per_row": [main_id], "given": True}
        return None
    if not main_id:
        return None
    per_row = [nm for nm in id_names if nm != main_id and structs[nm]["n_ids_multi"] == 0
               and structs[nm]["n_ids"] >= 0.9 * structs[nm]["n_rows"]]
    return {"used": main_id, "repeating": main_id, "per_row": per_row, "given": False} if per_row else None


def _big_int_text(s):
    """A label that is a whole number of 7+ digits (a phone, ID card or record number typed into the
    column), also written "1.38E+10", "13800131005.00" or "13,800,131,005": never printed."""
    t = re.sub(r"[,\s]", "", _nfkc(s))[:60]
    if re.fullmatch(r"[-+]?0*[0-9]{7,}(?:\.0*)?", t):
        return True
    if not PLAIN_NUM_RE.match(t):
        return False
    try:
        f = float(t)
    except (ValueError, OverflowError):
        return False
    return math.isfinite(f) and abs(f) >= BIG_INT and f.is_integer()


def _gate_values(col, info, units):
    """Turn the column's raw value lists into what may be printed: category levels and spelling
    variants held by >= SMALL_CELL_K patients, words in number columns and notes in date cells the
    same (digits masked), censored examples without free text. When patients cannot be told apart
    (units.mode 'none') no text value is printed at all -- only the number of levels and the shape of
    their counts. Numbers and dates are measurements and are not gated (but a whole number of 7+
    digits is never printed). Privacy columns print nothing."""
    pii = bool(col["pii"])
    cls, keys, miss = info["cls"], info["keys"], info["missing_by_key"]
    levels = info["levels"]
    known = units.known
    letters = lambda t: re.search(r"[^\W\d_#]", t)
    strings = col.get("numeric_as_text") or col.get("censored") or info["unit_of"] or info["flag_of"]
    gate = _string_gate(col, info, units) if strings and not pii and col["type"] != "id" else None
    if col["type"] in ("categorical", "numeric") and levels and not pii and \
            (col["type"] == "categorical" or len(levels) <= 10):
        kg = _level_groups(info)
        per = units.per_value(keys, kg, exclude=col["name"]) if known else {}
        numeric = col["type"] == "numeric"
        ctx = _level_ctx(info)
        key_of = {_label(k): k for k in info["counts"]}

        def ok(lab):
            if numeric and PLAIN_NUM_RE.match(str(lab).strip()):
                return not _big_int_text(lab)
            if not known:
                return False
            k = key_of.get(lab)
            if numeric and k is not None and gate and ((info["unit_of"].get(k) and not gate[0](info["unit_of"][k]))
                                                     or (info["flag_of"].get(k) and not gate[1](info["flag_of"][k]))):
                return False                 # ("5 Lin Yu": a number with a "unit" that may be printed only as units are)
            g = _fold(lab)
            return _shown_ok(lab, per.get(g, 0), ctx)
        col["categorical"] = _levels_summary(levels, info["max_levels"], ok, units.what)
        if not known and any(not (numeric and PLAIN_NUM_RE.match(str(lab).strip())) for lab in levels):
            col["categorical"]["values_hidden"] = "no_patient_unit"
    elif col["type"] in ("categorical", "numeric"):
        col["categorical"] = None
    nat = col.get("numeric_as_text")
    if nat and gate:
        unit_ok, flag_ok = gate
        # a unit / flag / example cell is printed when its unit and flag are known ones (KNOWN_UNITS, KNOWN_FLAG_RE)
        # or held by SMALL_CELL_K+ patients and shaped like no name; the others are counted
        spell = info["unit_spell"]
        shown_u = {spell[uk]: n for uk, n in info["unit_counts"].most_common() if unit_ok(uk)}
        n_hidden_u = len(info["unit_counts"]) - len(shown_u)
        nat["units"] = shown_u
        nat["flags"] = {f: n for f, n in info["flag_counts"].most_common() if flag_ok(f)}
        if n_hidden_u:
            nat["n_units_unshown"] = n_hidden_u
        if len(info["unit_counts"]) > 1:
            col["hints"].append("同一列出现多种单位：" + "、".join(f"{u}×{n}" for u, n in list(shown_u.items())[:5])
                                + (f"{'；' if shown_u else ''}另有 {n_hidden_u} 种单位写法不显示" if n_hidden_u else ""))
        exs = collections.Counter({e: c for e, c in info["examples"].items()
                                   if not _has_identifier(e) and (info["example_unit"].get(e) is None or unit_ok(info["example_unit"][e]))})
        nat["examples"] = _top(exs)
    if nat and nat.get("unrecognised") is not None:
        tg = {k: (_token(_label(k).strip()) if cls[k][0] in ("text", "date") and not miss[k] else None) for k in info["counts"]}
        per = units.per_value(keys, tg, exclude=col["name"]) if known else {}
        toks = info["tokens"]
        tctx = _level_ctx(info)
        ok = collections.Counter({t: c for t, c in toks.items() if not pii and not _mentions_person(t) and _level_shape_ok(t, tctx)
                                  and not _holds_name(t) and (not letters(t) or per.get(t, 0) >= SMALL_CELL_K)})
        nat["unrecognised"] = {"n": sum(toks.values()), "examples": [[t, ok[t]] for t in _top(ok)],
                               "n_unshown": len(toks) - len(ok), "no_patient_unit": not known}
        nat["examples"] = [] if pii else nat["examples"] + _top(ok)
    cens = col.get("censored")
    if cens and gate:
        unit_ok = gate[0]
        clean = collections.Counter({v: c for v, c in info["cens_clean"].items()
                                     if _censored_unit(v) is None or unit_ok(_unit_key(_censored_unit(v)))})
        cens["examples"] = _top(clean)
        n_unshown = len({cls[k][1] for k in info["counts"] if cls[k][0] == "censored"}) - len(clean)
        if n_unshown:
            cens["n_unshown"] = n_unshown
        else:
            cens.pop("n_unshown", None)
    d = col.get("date")
    if d is not None:
        bad = d.get("_bad") or collections.Counter()
        shown = collections.Counter()
        # how an unreadable date cell may be shown: as written when it is a date of digits and separators
        # ("2024-13-45"), else its digits masked ("#..#", "昨天"); a bare 8-digit number is a number
        shape = lambda lab: lab if BROKEN_DATE_RE.match(_nfkc(lab)) and not _big_int_text(lab) else _token(lab)
        if not pii and bad:
            tg = {}
            for k in info["counts"]:
                if miss[k] or cls[k][0] == "date":
                    tg[k] = None
                    continue
                tg[k] = shape(_label(k).strip())
            per = units.per_value(keys, tg, exclude=col["name"]) if known else {}
            dctx = _level_ctx(info)
            for k, c in info["counts"].items():
                g = tg.get(k)
                if g is None:
                    continue
                if (BROKEN_DATE_RE.match(_nfkc(g)) or not letters(g) or per.get(g, 0) >= SMALL_CELL_K) and not _has_identifier(g) \
                        and (BROKEN_DATE_RE.match(_nfkc(g)) or _level_shape_ok(g, dctx)):
                    shown[g] += c
        d["unparseable_examples"] = _top(shown)
        n_groups = len({shape(_label(k).strip()) for k in info["counts"] if not miss[k] and cls[k][0] != "date"})
        d["n_unparseable_unshown"] = max(0, n_groups - len(shown))


def _string_gate(col, info, units):
    """(unit_ok, flag_ok): which unit keys and flags of a column's cells may be printed -- the known ones always,
    another one only when patients can be told apart, at least SMALL_CELL_K of them have it and it is shaped like no
    name or other identifier (a "unit" made of unit words, "5 Lin Yu", "60周天元以上", is a name)."""
    keys, cls, known = info["keys"], info["cls"], units.known
    ctx = _level_ctx(info)
    per_u = per_f = {}
    if known:
        ug = {k: info["unit_of"].get(k) for k in info["counts"]}
        for k in info["counts"]:
            if cls[k][0] == "censored" and _censored_unit(cls[k][1]):
                ug[k] = _unit_key(_censored_unit(cls[k][1]))
        per_u = units.per_value(keys, ug, exclude=col["name"])
        per_f = units.per_value(keys, {k: info["flag_of"].get(k) for k in info["counts"]}, exclude=col["name"])
    spell = dict(info["unit_spell"])
    for v in info["cens_clean"]:
        u = _censored_unit(v)
        if u:
            spell.setdefault(_unit_key(u), u)
    shape_ok = lambda t: _level_shape_ok(t, ctx) and not _name_shaped(t) and not _holds_name(t)

    def unit_ok(uk):
        return uk in KNOWN_UNIT_KEYS or (per_u.get(uk, 0) >= SMALL_CELL_K and shape_ok(spell.get(uk, uk)))

    def flag_ok(f):
        return bool(KNOWN_FLAG_RE.fullmatch(f)) or (per_f.get(f, 0) >= SMALL_CELL_K and shape_ok(f))
    return unit_ok, flag_ok


def _levels_summary(levels, max_levels, ok, what):
    """Category levels as printed: only those `ok` lets through (small cells are counted, not
    shown), the commonest max_levels of them; spelling variants (case / spaces) of printed values;
    the shares of the commonest and the rarest level (printed also when no level may be)."""
    ordered = sorted(levels.items(), key=lambda kv: (-kv[1], kv[0]))
    shown = [(lab, cnt) for lab, cnt in ordered if ok(lab)]
    hidden = [(lab, cnt) for lab, cnt in ordered if not ok(lab)]
    groups = collections.defaultdict(list)
    for lab, _ in shown:
        groups[_fold(lab)].append(lab)
    total = sum(cnt for _, cnt in ordered)
    folded = collections.Counter(_fold(lab) for lab, _ in ordered)
    return {"n_levels": len(ordered),
            "levels": [[lab, cnt] for lab, cnt in shown[:max_levels]],
            "n_levels_truncated": max(0, len(shown) - max_levels),
            "n_rows_truncated": sum(cnt for _, cnt in shown[max_levels:]),
            "n_levels_suppressed": len(hidden), "n_rows_suppressed": sum(cnt for _, cnt in hidden),
            "suppressed_unit": what,
            "inconsistent": [g for g in groups.values() if len(g) > 1],
            "n_inconsistent": sum(1 for c in folded.values() if c > 1),
            "largest_share": round(100 * ordered[0][1] / total, 1) if total else None,
            "smallest_share": round(100 * ordered[-1][1] / total, 1) if total else None,
            "n_levels_lt5": sum(1 for _, cnt in ordered if cnt < 5)}


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
    if p.get("total_rows"):
        tr = p["total_rows"]
        out.append("像合计/汇总的行：" + "、".join(f"第 {x['row']} 行（{_code(x['word'], 12)}）" for x in tr[:5])
                   + ("等" if len(tr) > 5 else "") + "——这些行会被当成一名患者计入统计（例如数值列的最大值、结局取值），"
                   "清洗时请删除")
    if p.get("footer_rows"):
        fr = [x["row"] for x in p["footer_rows"]]
        out.append(f"表尾像注释 / 签名 / 打印时间的行：第 {fr[0]}" + (f"–{fr[-1]}" if len(fr) > 1 else "") + " 行（只有一两个非空单元格，"
                   "如“注：…”“制表人：…”）——这些行被当成了数据行（患者）计入行数和统计，清洗时请删除")
    if p.get("unit_row"):
        out.append("表头下的第 1 行像单位行（只有单位，如“岁”“元”）：它被当成了一行数据；读入时请跳过这一行（或把单位写进列名）")
    dis = []
    for c in cols:
        parts = [f"{t or '空白'}×{n}" for t, n in c["disguised_missing"].items()]
        parts += [f"{t}×{n}" for t, n in c["missing_codes"].items()]
        if parts:
            dis.append(f"{_disp(c['name'])}（{'、'.join(parts[:6])}）")
    if dis:
        out.append("伪装缺失：" + "；".join(dis))
    added = p["missing_tokens"]["added"]
    num_added = [t for t in added if PLAIN_NUM_RE.match(_nfkc(t))]
    if num_added:
        used = [f"{_disp(c['name'])}（{sum(n for t, n in c['missing_codes'].items() if t in {_fmt_num(float(_nfkc(x))) for x in num_added})}）"
                for c in cols if any(t in {_fmt_num(float(_nfkc(x))) for x in num_added} for t in c["missing_codes"])]
        skipped = [f"{_disp(c['name'])}（{'、'.join(f'{t}×{n}' for t, n in c['missing_tokens_not_applied'].items())}）"
                   for c in cols if c.get("missing_tokens_not_applied")]
        msg = f"--missing-tokens {','.join(num_added)}：按缺失计的列 " + ("、".join(used) if used else "（没有）")
        if skipped:
            msg += ("；没有用于 " + "、".join(skipped) + "——在这些列里它是真实取值（0/1 编码之一，也可能是结局；"
                    "或在该列其他数字的范围之内，如评分 9）；如果它在某列确实表示缺失，请写 --missing-tokens 列名=取值")
        out.append(msg)
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
        out.append("截断值（如 <0.1、>1000、ND）：" + "、".join(cens))
    nat = [_disp(c["name"]) for c in cols if c.get("numeric_as_text")]
    if nat:
        out.append("数值列直接读入会变成文本：" + "、".join(nat))
    flagged, words = [], []
    for c in cols:
        nat_ = c.get("numeric_as_text") or {}
        if nat_.get("flags") or nat_.get("reasons", {}).get("带异常标记"):
            shown = "、".join(f"{f}×{n}" for f, n in nat_["flags"].items())
            flagged.append(f"{_disp(c['name'])}（{shown or str(nat_['reasons'].get('带异常标记', 0)) + ' 个'}）")
        u = nat_.get("unrecognised")
        if u:
            notes = ["如 " + "、".join(f"{_code(t, 20)}×{n}" for t, n in u["examples"])] if u["examples"] else []
            notes += [(f"另有 {u['n_unshown']} 种写法不显示（无法区分患者）" if u.get("no_patient_unit") else
                       f"另有 {u['n_unshown']} 种低频写法不显示（不足 {SMALL_CELL_K} 名患者，或带姓名/电话）")] if u["n_unshown"] else []
            words.append(f"{_disp(c['name'])} {u['n']} 个" + (f"（{'；'.join(notes)}）" if notes else ""))
    if flagged:
        out.append("数值带异常标记（↑ ↓ H L * High / Low / 偏高 / 阳性 等；分布统计已去掉标记、保留数值）：" + "；".join(flagged))
    approx = [f"{_disp(c['name'])}（{n} 个）" for c in cols
              for n in [(c.get("numeric_as_text") or {}).get("reasons", {}).get(APPROX_REASON, 0)] if n]
    if approx:
        out.append("数值带约数写法（约、~、≈、左右、余、多等）：按写出的数值计入分布统计，实际值可能略有出入，分析前请决定怎么处理："
                   + "、".join(approx))
    if words:
        out.append("数值列里有不是数字、缺失写法或截断值的文字（分布统计不含它们；示例里的数字记为 #）：" + "；".join(words))
    mixed = [f"{_disp(c['name'])}（约 {c['pct_numeric']}% 是数字）" for c in cols if c.get("pct_numeric") is not None]
    if mixed:
        out.append("数字与文字混杂、按文字处理（没有分布统计）：" + "、".join(mixed))
    bad_dates = [f"{_disp(c['name'])}（{c['date']['n_unparseable']} 个）" for c in cols
                 if c.get("date") and c["date"]["n_unparseable"]]
    if bad_dates:
        out.append("无法解析的日期：" + "、".join(bad_dates))
    sent = [_disp(c["name"]) for c in cols if c.get("date") and any("1900-01-01" in x for x in c["date"]["notes"])]
    if sent:
        out.append("日期列里有 1900-01-01 这类占位日期（可能表示缺失）：" + "、".join(sent))
    inc = [_disp(c["name"]) for c in cols if (c.get("categorical") or {}).get("inconsistent")
           or ((c.get("categorical") or {}).get("values_hidden") and (c.get("categorical") or {}).get("n_inconsistent"))]
    if inc:
        out.append("分类取值只差大小写/空格：" + "、".join(inc))
    big = [f"{_disp(c['name'])}（{c['numeric']['n_big_int']} 个）" for c in cols if (c.get("numeric") or {}).get("n_big_int")]
    if big:
        out.append("数值列里有 7 位以上的整数（像电话号码、身份证号或病历号，可能是录错的标识符；也可能是很大的测量值，如病毒载量、"
                   "费用）：" + "、".join(big) + "——这些列的最大值等统计量不显示（报告里不出现 7 位以上的整数）；请核对是否有录错的标识符")
    contact = [f"{_disp(c['name'])}（" + "、".join(f"{lab} {c['contact_cells'][k]}" for k, lab in
                                                (("id_card", "身份证号"), ("phone", "电话号码"), ("email", "邮箱"))
                                                if c["contact_cells"][k]) + "）"
               for c in cols if c.get("contact_cells")]
    if contact:
        out.append("单元格里有身份证号/电话号码/邮箱样式的内容（这些取值不显示；分析前请去标识化）：" + "；".join(contact))
    by_value = [_disp(c["name"]) for c in cols if c.get("id_source") == "value" and not c["pii"]
                and any(h.startswith("按取值判为 ID") for h in c["hints"])]
    if by_value:
        out.append("按取值判为 ID 的整数列（只是类型判断，不是隐私判断）：" + "、".join(by_value)
                   + "——如果其中有测量值（基线值、费用、计数、日期序列号），加 --not-id " + ",".join(by_value) + " 重新体检，才会有分布统计")
    ch = p.get("id_choice")
    if ch and ch.get("given"):
        out.append(f"--id {_disp(ch['used'])} 每行一个取值，不能说明哪些行属于同一患者；{_disp(ch['repeating'])} 的取值在多行重复，"
                   f"像患者 ID（病历号/住院号）——如果同一患者有多行，请改用 --id {_disp(ch['repeating'])} 重新体检")
    elif ch:
        out.append(f"按 {_disp(ch['used'])} 汇总患者：它的取值在多行重复；" + "、".join(_disp(x) for x in ch["per_row"])
                   + " 每行一个取值（像序号、就诊流水号或标本号），没有用来按患者汇总——如果患者 ID 是另一列，请用 --id 指定")
    pu = p.get("privacy_units") or {}
    if pu.get("mode") == "encoding":
        out.append("编码未确认（见上面关于编码的说明）：分类取值和单元格里的文字一律不显示（只给取值个数和分布形状）；"
                   "用 --encoding 指定正确的编码重新体检后才显示")
    elif pu.get("mode") == "none":
        hint = pu.get("id_hint") or []
        amb, vis = pu.get("ambiguous") or [], pu.get("visit_valued") or []
        rest = [x for x in hint if x not in vis]
        if amb:
            given = (f"--id {_disp(pu['id_given'])} 每行一个取值，" if pu.get("id_given") else
                     "--rows-are-patients 说每行一名患者，" if pu.get("rows_are_patients") else "")
            out.append(f"无法区分患者：{given}{'、'.join(_disp(x) for x in amb[:4])}{' 等' if len(amb) > 4 else ''} 都可能是患者 ID（列名像"
                       f"患者 ID、取值在多行重复、至少 {AUTO_KEY_MIN_VALUES} 个取值），工具不替你从中选一列，所以分类取值和单元格里的文字一律"
                       f"不显示（只给取值个数和分布形状）。要看分类取值，请用 --id 指定其中真正的患者 ID 列（如 --id {_disp(amb[0])}）重新体检")
        else:
            out.append("无法区分患者：没有 --id，也没有能自动认作患者 ID 的列（列名像患者 ID、取值在多行重复、至少 "
                       f"{AUTO_KEY_MIN_VALUES} 个取值），所以分类取值和单元格里的文字一律不显示（只给取值个数和分布形状）"
                       + (f"；{'、'.join(_disp(x) for x in vis[:3])} 的列名像患者 ID，但取值像就诊/随访序号或序数（如 第1次、随访一、V1、"
                          "baseline、罗马数字、单个字母、从 0 开始的 0/1/2… 这样的小整数），没有自动采用" if vis else "")
                       + (f"；{'、'.join(_disp(x) for x in rest[:3])} 可能就是患者 ID（列名或取值像病历号/住院号）" if rest else "")
                       + "。要看分类取值，请加 --id <患者ID列>（同一患者可有多行）或 --rows-are-patients（每行一名不同的患者）重新体检")
    elif pu.get("conflict"):
        out.append(f"加了 --rows-are-patients，但 {_disp(pu['columns'][0])} 的取值在多行重复、像患者 ID：已按 {_disp(pu['columns'][0])} "
                   "区分患者（少于 5 名患者共有的取值不显示）；如果每行确实是不同的患者，请检查这一列")

    for s in p["id_structure"]:
        unused = not s.get("as_patient_id", True)
        if s["n_ids_multi"] and unused and s["column"] in (pu.get("ambiguous") or []) + (pu.get("visit_valued") or []):
            continue                       # (named in the one "无法区分患者" line above)
        if s["n_ids_multi"] and unused and s.get("patient_id_name"):
            out.append(f"{_disp(s['column'])}：列名像患者 ID（{s['n_ids']} 个取值，每个最多 {s['max_rows_per_id']} 行），{_key_why(s)}，"
                       "没有用它按患者汇总；如果它就是患者 ID，请用 --id 指定")
        elif s["n_ids_multi"] and unused:
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
            _disp(x["column"]) + (f"（列名含“{_disp(x['name_word'])}”；若它只是分类，如 城市/农村，请改用不含这个词的列名）"
                                   if x["by_name"] and x.get("name_word") and not _is_strong_pii_word(x["name_word"])
                                   else "" if x["by_name"] else _privacy_why(x)) for x in p["privacy"]))
    return out


def _key_why(s):
    """Why a patient-ID-named column that repeats is not the automatic patient key (id_structure entry s; with --id
    only the --id column is listed)."""
    return {"visit_values": "但取值像就诊/随访序号或序数（如 第1次、随访一、V1、baseline、罗马数字、单个字母、从 0 开始的 0/1/2… 这样的小整数）",
            "visit_name": "但列名含就诊/随访/时间/标本类的词（visit、day、sample、随访、第、次、天、入院 等），不自动当作患者 ID",
            "few_values": f"但只有 {s['n_ids']} 个取值（自动认作患者 ID 至少要 {AUTO_KEY_MIN_VALUES} 个）",
            "ambiguous": "但还有别的列也像患者 ID，工具不替你从中选一列"}.get(s.get("key_status"), "但不能自动认作患者 ID")


def _is_strong_pii_word(w):
    """A name word that always means an identifier (姓名, 身份证, 住院号, dob ...), as opposed to one that
    may name a category column (居住, home, 联系人)."""
    return w in PII_RECORD_SUBSTR or w in ("姓名", "名字") or w in PII_RECORD_TOKENS or w in PII_PERSON_TOKENS \
        or bool(BIRTH_NAME_RE.search(str(w))) or w in ("手机", "电话", "邮箱", "phone", "mobile", "email", "e-mail", "tel")


def _privacy_why(x):
    """Why a column whose name gives nothing away is a privacy column (for the problem list)."""
    why = ["文字里有姓名" if w == "文字里的姓名" else f"取值像{w}" for w in x.get("looks_like") or []]
    if x.get("id_card_hits"):
        why.append("含身份证号")
    if x.get("phone_hits"):
        why.append("含电话号码")
    if x.get("email_hits"):
        why.append("含邮箱地址")
    if x.get("unique_per_patient"):
        why.append("每名患者一个、几乎各不相同的取值")
    return f"（{'；'.join(why)}）" if why else ""


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


def _source_title(src):
    return _disp(src["file"]) if src.get("file") and src.get("file_shown", True) else ""


def render_markdown(p):
    """Render a profile dict (from profile_dataframe) as the data-profile.md report."""
    src = p.get("source", {})
    cols = p["columns"]
    title = _source_title(src)
    L = [f"# 数据体检报告：{title}" if title else "# 数据体检报告", "", f"> {p['statement']}。", ""]
    info = []
    if src.get("file"):
        extra = [f"{src.get('bytes', 0)} 字节", f"sha256 `{src.get('sha256', '')}`"]
        if src.get("encoding"):
            extra.append(f"编码 {src['encoding']}")
        if src.get("sep"):
            extra.append("分隔符 " + ("制表符" if src["sep"] == "\t" else f"`{src['sep']}`"))
        info.append(f"- 文件：{_disp(src['file'])}（{'；'.join(extra)}）")
    if src.get("sheet"):
        n = src.get("n_sheets", 1)
        info.append(f"- 工作表：{src['sheet']}（第 {src.get('sheet_index', 0) + 1} 个，共 {n} 个"
                    + ("；其他工作表的名称不显示" if n > 1 else "") + "）")
    tc = "、".join(f"{k} {v}" for k, v in p["type_counts"].items() if v)
    info += [f"- 体检日期：{p['generated']}；工具：data_profile.py（只读，没有修改或另存数据）",
             f"- 规模：{p['n_rows']} 行 × {p['n_cols']} 列；列类型：{tc}",
             f"- 完全重复的行：{p['n_duplicate_rows']}；没有任何缺失的行：{p['n_complete_rows']}"
             + (f"（{round(100 * p['n_complete_rows'] / p['n_rows'], 1)}%）" if p["n_rows"] else "")
             + _basis_text(p.get("complete_rows_basis")),
             (f"- 分类取值、单元格里的文字只在至少 {SMALL_CELL_K} 名患者共有时才显示（其余只计数）；"
              if (p.get("privacy_units") or {}).get("mode") not in ("none", "encoding") else
              "- 编码未确认：分类取值、单元格里的文字都不显示（只给取值个数和分布形状，见问题清单）；"
              if (p.get("privacy_units") or {}).get("mode") == "encoding" else
              "- 无法区分患者：分类取值、单元格里的文字都不显示（只给取值个数和分布形状，见问题清单）；")
             + "数值和日期的分布照常显示（7 位以上的整数不显示）"]
    pu = p.get("privacy_units") or {}
    if pu.get("mode") == "patient" and pu.get("source") == "auto" and pu.get("columns"):
        info.append(f"- 患者按 {_code(pu['columns'][0])} 区分（自动采用：列名像患者 ID、取值在多行重复、至少 {AUTO_KEY_MIN_VALUES} 个取值；"
                    "它的每个取值算一名患者）——如果它其实是每次就诊或住院一个的编号，请用 `--id <患者ID列>` 重新体检")
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
          "`999`、`9999`、`-99`、`-999` 在数值列和分类列按缺失码计，如果它在该列是真实取值，请在清洗时不要当缺失。"
          "`ND` 在数值列按\"未检出\"（截断值）计，在其他列按缺失计；`失访` 在分类列（如结局状态）按取值保留，在数值/日期列按缺失计。"]

    cens = [c for c in cols if c.get("censored")]
    nat = [c for c in cols if c.get("numeric_as_text")]
    L += ["", "## 4. 截断值与\"数值存成文本\"", ""]
    if cens:
        L.append(_table(["列", "截断值个数", "示例"], [
            [_code(c["name"]), c["censored"]["n"],
             "、".join([_code(x) for x in c["censored"]["examples"]]
                      + ([f"另 {c['censored']['n_unshown']} 种带文字的写法不显示"] if c["censored"].get("n_unshown") else []))
             or "（不显示）"]
            for c in cens]))
        L.append("")
    if nat:
        L.append(_table(["列", "直接读入会变成文本的原因（个数）", "示例（文字里的数字记为 #）", "单位", "异常标记"], [
            [_code(c["name"]), "、".join(f"{k} {v}" for k, v in c["numeric_as_text"]["reasons"].items()),
             "、".join(_code(x) for x in c["numeric_as_text"]["examples"]),
             "、".join(f"{_code(u)}×{n}" for u, n in c["numeric_as_text"]["units"].items()),
             "、".join(f"{_code(f)}×{n}" for f, n in c["numeric_as_text"].get("flags", {}).items())]
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
            hid = set(s.get("hidden_stats") or [])
            f_ = lambda k, sig=None: "不显示" if k in hid else _fmt(s[k], sig)
            rows.append([_code(c["name"]), s["n"], f_("min"), f_("p25"), f_("median"),
                         f_("p75"), f_("max"), f"{f_('mean', 4)} ± {f_('sd', 4)}",
                         "—" if s["n_z_gt3"] is None else s["n_z_gt3"],
                         "—" if s["n_iqr_out"] is None else s["n_iqr_out"],
                         s.get("n_out_of_range", "") if "range" in s else ""])
        L.append(_table(["列", "n", "最小", "P25", "中位数", "P75", "最大", "均值 ± SD", "Z>3", "IQR×1.5 外",
                         "超出 --range"], rows))
        L += ["", "统计时已排除空值、伪装缺失、缺失码和截断值；只有两个取值的列不计离群（—）；"
              "是否处理离群值由 SAP 预先规定。"]
        big = [c for c in num if (c["numeric"] or {}).get("n_big_int")]
        if big:
            L.append("“不显示”：该列有 7 位以上的整数（像电话号码、身份证号或病历号，可能是录错的标识符），"
                     "可能等于或接近它们的统计量不显示：" + "、".join(f"{_code(c['name'])}（{c['numeric']['n_big_int']} 个）" for c in big))
    else:
        L.append("没有数值列（或数值列均为疑似隐私字段，不显示分布）。")

    cat = [c for c in cols if c.get("categorical")]
    L += ["", "## 6. 分类取值", ""]
    if cat:
        for c in cat:
            k = c["categorical"]
            if k.get("values_hidden"):
                shape = (f"最常见的一个占 {k['largest_share']}%，最少的占 {k['smallest_share']}%"
                         if k.get("largest_share") is not None and k["n_levels"] > 1 else "")
                L.append(f"- {_code(c['name'])}（{k['n_levels']} 个取值）：取值不显示（无法区分患者）"
                         + (f"；{shape}" if shape else "")
                         + (f"；{k['n_levels_lt5']} 个取值不足 5 行" if k["n_levels_lt5"] and c["type"] == "categorical" else ""))
                continue
            levels = "、".join(f"{_code(lab)} {cnt}" for lab, cnt in k["levels"])
            more = f"；其余 {k['n_levels_truncated']} 个取值共 {k['n_rows_truncated']} 行" if k["n_levels_truncated"] else ""
            if k.get("n_levels_suppressed"):
                more += (f"{'；' if levels or more else ''}另有 {k['n_levels_suppressed']} 个低频取值未显示"
                         f"（共 {k['n_rows_suppressed']} 行，每个不足 {SMALL_CELL_K} {k.get('suppressed_unit', '名患者')}）")
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
                         "、".join([_code(x) for x in d["unparseable_examples"]]
                                  + ([f"另 {d['n_unparseable_unshown']} 种不显示"] if d.get("n_unparseable_unshown") else [])),
                         "、".join(f"{k} {v}" for k, v in d["formats"].items()), rng,
                         "；".join(d["notes"] + ([f"晚于体检日 {d['n_future']} 个"] if d["n_future"] else [])
                                  + ([f"早于 1900 年 {d['n_before_1900']} 个"] if d["n_before_1900"] else []))])
        L.append(_table(["列", "可解析", "无法解析", "无法解析的示例（少数患者的文字不显示，数字记为 #）", "写法", "范围", "备注"], rows))
    else:
        L.append("没有识别为日期的列。")

    L += ["", "## 8. 重复 ID 与聚类结构", ""]
    if p["id_structure"]:
        for s in p["id_structure"]:
            L.append(f"- {_code(s['column'])}：{s['n_rows']} 行对应 {s['n_ids']} 个 ID（缺 ID {s['n_missing_id']} 行）；"
                     f"{s['n_ids_multi']} 个 ID 出现多行，共 {s['n_rows_in_multi']} 行，每个 ID 最多 {s['max_rows_per_id']} 行")
            if not s.get("as_patient_id", True) and s["n_ids_multi"]:
                L.append((f"  - 列名像患者 ID，{_key_why(s)}" if s.get("patient_id_name") else "  - 列名不像患者 ID")
                         + "，没有用它按患者汇总（事件数、聚类里的患者数）；如果它就是患者 ID，请用 `--id` 指定后重新体检")
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
            elif pp and pp.get("patients_by_level"):
                L.append("  - 同一患者有多行：按患者计，" + "、".join(f"有 {_code(lab)} 的 {n} 名" for lab, n in pp["patients_by_level"].items())
                         + f"（共 {pp['n_patients']} 名患者）；确认哪一类是事件后，按那一类的患者数计事件数")
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
        L.append(_table(["列", "列名像隐私字段", "18 位身份证号样式", "手机/电话号码样式", "邮箱地址",
                         "取值像姓名/地址/编号/出生日期（或文字里有姓名）", "每名患者一个、几乎各不相同"], [
            [_code(x["column"]), (f"是（含“{_cell(x['name_word'], 20)}”）" if x.get("name_word") else "是") if x["by_name"] else "",
             x["id_card_hits"] or "", x["phone_hits"] or "",
             x.get("email_hits") or "", "、".join(x.get("looks_like") or []),
             "是" if x.get("unique_per_patient") else ""]
            for x in p["privacy"]]))
        L += ["", "分析前请去标识化（删除或替换为研究编号）；这些列不要进入分析数据集和任何对外共享的文件。"]
    else:
        L.append("未发现。")

    mt = p["missing_tokens"]
    by_col = mt.get("by_column") or {}
    L += ["", "## 说明", "",
          "- 伪装缺失默认词表：" + "、".join(_code(t) for t in mt["default"]) + "（外加空白单元格）"
          + ("；本次追加：" + "、".join(_code(t) for t in mt["added"]) if mt["added"] else "")
          + ("；只用于某一列：" + "、".join(f"{_disp(k)}={'/'.join(v)}" for k, v in by_col.items()) if by_col else ""),
          "- 类型是按取值推断的，只作参考；变量的真实含义以数据字典和 SAP 为准。",
          "- 隐私检查是按样式的检查：不符合任何样式的标识符认不出来，共享报告前仍需人工检查。", ""]
    return "\n".join(L)


# ─── terminal summary & CLI ─────────────────────────────────────────────────

def summary_lines(p):
    src = p.get("source", {})
    title = _source_title(src)
    head = f"{title or '数据文件'}：{p['n_rows']} 行 × {p['n_cols']} 列"
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
        pp = o.get("per_patient")
        if o["events"] is not None and pp:
            s += (f"，事件（={_disp(o['event_label'])}）{o['events']} 行 / {pp['patients_with_event']} 名患者"
                  f"（共 {pp['n_patients']} 名）")
        elif pp and pp.get("patients_by_level"):
            s += "，按患者计：" + "、".join(f"={_disp(lab)} {n} 名" for lab, n in pp["patients_by_level"].items()) \
                 + f"（共 {pp['n_patients']} 名；无法从编码判断哪一类是事件）"
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
            head = fh.read(4096).decode("utf-8", "replace").lstrip("﻿")
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
            _fail("报告文件不能与数据文件同名：本工具绝不改写数据")
        if os.path.splitext(out)[1].lower() in DATA_EXTS + UNSUPPORTED_EXTS:
            _fail(f"报告文件 {out} 的扩展名像数据文件；请用 .md / .json，以免覆盖数据")
        if real.lower() in seen:                   # also the same file on a case-insensitive disk
            _fail(f"{flag} 和 {seen[real.lower()]} 是同一个文件；请分别指定")
        seen[real.lower()] = flag
        parent = os.path.dirname(os.path.abspath(out))
        if not os.path.isdir(parent):
            _fail(f"{flag} 的目录不存在：{parent}")
        if os.path.isdir(out):
            _fail(f"{flag} {out} 是一个目录")
        if os.path.exists(out) and not _is_earlier_output(out, kind):
            _fail(f"{out} 已存在，且不是之前的数据体检{'报告' if kind == 'report' else ' JSON'}："
                  "为免覆盖，请换一个文件名或先移走它")


class _Parser(argparse.ArgumentParser):
    def error(self, message):            # one line on stderr, exit 2 (argparse prints a usage block)
        _fail(f"参数错误：{message}（用 --help 查看用法）")


def main(argv=None):
    p = _Parser(
        prog="data_profile.py",
        description="只读数据体检：描述数据结构与质量（类型、伪装缺失、截断值、数值存成文本、日期、"
                    "离群计数、分类取值、重复 ID/聚类、结局事件数、疑似隐私字段）。"
                    "不修改、不清洗、不另存数据；不计算任何变量与结局的关系，也不计算变量之间的关联。",
        epilog="例：python3 data_profile.py data.csv --id patient_id --outcome recurrence --report data-profile.md",
    )
    p.add_argument("data", help="数据文件：.csv / .tsv / .txt / .xlsx（只读，不会被修改）")
    p.add_argument("--sheet", help="xlsx 的工作表名或序号（从 0 开始），默认第一个")
    p.add_argument("--id", dest="id_col", help="患者 ID 列（同一患者可有多行）；不填则只自动认一列：列名像患者 ID（不含就诊/时间/标本类的词）、取值在多行重复、"
                        "至少 10 个取值、不像就诊/随访序号；有两列以上符合时一列也不用")
    p.add_argument("--rows-are-patients", action="store_true",
                   help="每行是一名不同的患者（没有患者 ID 列时用）：分类取值才会显示（不足 5 名患者共有的不显示）；"
                        "不加、也没有 --id 时，分类取值一律不显示")
    p.add_argument("--not-id", dest="not_id",
                   help="这些列是测量值、不是 ID（逗号分隔），如全部互不相同的住院费用、血小板计数")
    p.add_argument("--outcome", help="结局列（多个用逗号分隔）：只报告结局本身的分布与事件数")
    p.add_argument("--time", dest="time_col", help="生存结局的随访时间列（配合 --outcome 的事件列）")
    p.add_argument("--cluster", help="聚类列（中心/术者/读片者），逗号分隔；不填则按列名自动识别")
    p.add_argument("--missing-tokens", action="append", default=[],
                   help="追加伪装缺失写法，逗号（, 或 ，）分隔，可重复：--missing-tokens 拒查,未做；只用于某一列写 列名=取值"
                        "（如 --missing-tokens age=0）；负数可直接写（--missing-tokens -1,-9）；对所有列追加的数字"
                        "只用于它可能是缺失码的列（不是 0/1 编码之一，也不在该列其他数字的范围之内或紧挨着它）")
    p.add_argument("--range", action="append", default=[],
                   help="临床合理范围（只计数）：--range age=0:120 --range bmi=10:60")
    p.add_argument("--max-levels", type=int, default=15, help="每个分类列最多列出的取值数（默认 15，≥1）")
    p.add_argument("--report", help="写 Markdown 报告，如 data-profile.md")
    p.add_argument("--json", dest="json_path", help="另存 JSON 结果")
    p.add_argument("--encoding", help="CSV 编码；默认依次尝试 utf-8（含 BOM）、gbk（或 big5）、gb18030——字节符合中文编码时按中文读，"
                                      "按韩文 / 日文读明显更像文字时提示加 --encoding euc-kr / cp932 / euc-jp，并在确认编码之前不显示任何"
                                      "单元格文字（指定的编码读出来不像文字时也一样）；不符合 gb18030 时才按 euc-kr、cp932（Shift-JIS）、"
                                      "euc-jp 读（并提示）")
    p.add_argument("--sep", help="CSV 分隔符；默认自动识别（, 制表符 ; |）")
    hdr = p.add_mutually_exclusive_group()
    hdr.add_argument("--header", dest="header", action="store_const", const=True, default=None,
                     help="第一行一定是列名（默认自动判断：第一行像数据时按没有表头处理）")
    hdr.add_argument("--no-header", dest="header", action="store_const", const=False,
                     help="文件没有表头：列名记为 列1、列2……")
    p.add_argument("--skip-rows", type=int, default=0,
                   help="表头前要跳过的行数（如导出文件第一行是合并单元格的标题）")
    # "--missing-tokens -1,0": argparse takes a value starting with "-" for an option; join it to its flag
    raw, argv, i = list(sys.argv[1:] if argv is None else argv), [], 0
    while i < len(raw):
        if raw[i] == "--missing-tokens" and i + 1 < len(raw) and raw[i + 1].startswith("-") and not raw[i + 1].startswith("--"):
            argv.append(f"--missing-tokens={raw[i + 1]}")
            i += 2
        else:
            argv.append(raw[i])
            i += 1
    args = p.parse_args(argv)
    if args.max_levels < 1:
        p.error("--max-levels 至少为 1")

    _check_output_paths(args.data, (("--report", "report", args.report), ("--json", "json", args.json_path)))
    tokens = [t for item in args.missing_tokens for t in re.split(r"[,，]", item) if t != ""]
    try:
        ranges = _parse_ranges(args.range)
        df, meta = load_table(args.data, sheet=args.sheet, encoding=args.encoding, sep=args.sep,
                              header=args.header, skip_rows=args.skip_rows)
    except (FileNotFoundError, ValueError) as e:
        _fail(e)
    except Exception as e:                   # an unreadable file is an error message, not a traceback
        _fail(f"读取数据文件失败（{type(e).__name__}: {str(e)[:200]}）")
    try:
        profile = profile_dataframe(df, id_col=args.id_col, outcome_col=args.outcome, time_col=args.time_col,
                                    cluster_cols=args.cluster, missing_tokens=tokens, ranges=ranges,
                                    max_levels=args.max_levels, source=meta, not_id_cols=args.not_id,
                                    rows_are_patients=args.rows_are_patients)
    except ValueError as e:
        _fail(e)
    except Exception as e:                   # data the checks did not foresee: a message, not a traceback
        _fail(f"体检时出错（{type(e).__name__}: {str(e)[:200]}）；请把这一行报告给插件维护者")

    try:
        if args.report:
            with open(args.report, "w", encoding="utf-8") as fh:
                fh.write(render_markdown(profile))
        if args.json_path:
            with open(args.json_path, "w", encoding="utf-8") as fh:
                json.dump(profile, fh, ensure_ascii=False, indent=2, allow_nan=False)
    except OSError as e:
        _fail(f"无法写入报告：{e}")
    for line in summary_lines(profile):
        print(f"[数据体检] {line}")
    written = [x for x in (args.report, args.json_path) if x]
    print("[数据体检] " + (f"报告已写入 {'、'.join(written)}" if written else "加 --report data-profile.md 可保存完整报告"))
    return profile


if __name__ == "__main__":
    main()
