#!/usr/bin/env python3
"""
Patient-level train / val / test split (or K-fold) for AI/ML studies.

Why: splitting by image / slice / frame leaks the same patient into both the training
and the test set and inflates performance. This script assigns every row of a patient
to ONE split, optionally stratified by label, with a fixed seed, and verifies that no
patient appears in more than one split.

Command line (from the project directory):
    python3 "$CLAUDE_PLUGIN_ROOT/skills/data-collection-tools/scripts/patient_level_split.py" \
        data/annotations/consensus/labels.csv --patient-col patient_id --label-col label \
        --train 0.6 --val 0.2 --test 0.2 --seed 42 --out-dir data/splits
    python3 "$CLAUDE_PLUGIN_ROOT/skills/data-collection-tools/scripts/patient_level_split.py" \
        labels.csv --patient-col patient_id --label-col label --kfold 5

Reading the CSV: every cell is read as text, exactly as written -- leading zeros survive ('0012'
and '12' are two patients) and 'NA' / 'null' stay as they are in the output files. Encoding: UTF-8
(with or without BOM), else GB18030; --encoding sets it (e.g. cp1252 for a Windows Western file).
A file read as GB18030 is checked for being a Western file: a warning names cp1252 only when the
GB18030 reading has characters Chinese text rarely holds (outside GB2312, or one character inside
a Latin word: 'Müller' -> 'M黮ler') AND the cp1252 reading is plausible Western text (each run of
non-ASCII characters is one accented letter or common symbol, or two letters inside a word, as in
'Conceição'; a Chinese word read as cp1252 gives longer runs of symbols and capitals). It
suggests --encoding cp1252 only when both readings group the rows into the same patients; when
they do not (e.g. 'Müller' and 'MÜLLER' are one patient only in cp1252) it gives both patient
counts and asks to confirm the encoding with whoever exported the file.
The CSV outputs are written in the input's encoding, so their IDs are byte-for-byte those of the
source file and join back to it; --output-encoding sets another one (utf-8 when a value -- a
normalised ID in split_id_variants.csv, the --split-col name -- cannot be written in the input's
encoding). Nothing is written unless every output can be written: the files are made in
temporary files and moved into place together.
Patient IDs: an empty ID cell, or one holding a missing-value code (NA, N/A, NaN, null, #N/A,
<NA>), is an error -- such rows cannot be given to a patient. For grouping, IDs are normalised --
Unicode NFKC (full-width "ＰＯ０１" = "PO01"), surrounding spaces removed, case ignored -- so
'P001', 'P001 ' and 'p001' are ONE patient and always land in the same split; check_leakage()
applies the same rule. The output files keep the IDs exactly as written; spellings that were
merged are listed in split_id_variants.csv (the summary and the screen give only counts, never IDs).

Stratification (--label-col): patients are grouped by their patient-level label, the groups
are taken in random order, patients are shuffled within each group and dealt onto an evenly
interleaved sequence of splits. Every group is spread proportionally, split sizes follow the
fractions exactly, and a different seed gives a different partition. A label with very many
distinct values (a continuous measurement) cannot be stratified -- every group holds one or two
patients -- so the split is then an unstratified random split; a warning says so (bin the label
first, e.g. by quartiles). Label values with fewer patients than there are splits are reported:
they cannot appear in every split.
Split sizes: a split (or fold) that gets no patient -- fewer patients than splits -- is reported in
the warnings and shows 0 in patients_per_split; --kfold k needs at least k patients (error).
Patient-level label (--patient-label): 'majority' = the most frequent label among the patient's
rows; a tie forms its own group '<平票>' (reported, spread like any other group). 'any' = the
largest numeric label (with 0/1: positive if any row is positive) and needs numeric labels --
text labels such as 阳性/阴性 must be coded 0/1 first. Labels are compared after removing
surrounding spaces, and as numbers when every label is a number ('1', '1.0' and ' 1' are one
class; class_distribution counts them the same way). A label is missing when it is empty or a
missing-value code (NA, N/A, NaN, null, #N/A, <NA>; 'None' is a value). Rows without a label are
ignored for the patient label; a patient with no label at all forms the group '<缺失>' and is
still assigned.

Outputs (in --out-dir):
    split_assignment.csv   one row per input row (values as read) + column `split` (train/val/test or fold_k)
    split_patients.csv     one row per patient ID spelling + split
    split_summary.json     per-split patient / row counts, class distribution, leakage check, seed,
                           warnings, input encoding, Python / numpy / pandas versions and the sha256
                           of this script
    split_id_variants.csv  only when some patient IDs were written in several ways: each spelling
Warnings are also printed on stderr. Exit status 0 = written; 2 = invalid arguments, an
unreadable / unusable input file, or outputs that cannot be written -- the files already in
--out-dir are then left as they were (one line on stderr, no traceback).

Library use (project code never imports from the plugin install path): copy this file into the
project once -- it reads nothing else from the plugin -- e.g. as the project's tools/data_split.py:
    cp "$CLAUDE_PLUGIN_ROOT/skills/data-collection-tools/scripts/patient_level_split.py" tools/data_split.py
    # in a script in tools/ (Python finds modules next to the script it runs):
    from data_split import split_patients, kfold_patients, check_leakage
    # read the CSV with pd.read_csv(path, dtype=str, keep_default_na=False) so IDs keep their
    # leading zeros and every value stays as written
"""

import argparse
import codecs
import errno
import hashlib
import io
import json
import math
import os
import platform
import re
import secrets
import sys
import unicodedata

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover - depends on the user's environment
    print("缺少 pandas / numpy：pip install pandas numpy", file=sys.stderr)
    raise SystemExit(2)


# ─── helpers ────────────────────────────────────────────────────────────────

MISSING_STRATUM = '<缺失>'
TIE_STRATUM = '<平票>'
OUTPUT_FILES = ('split_assignment.csv', 'split_patients.csv', 'split_summary.json', 'split_id_variants.csv')
# Missing-value codes of a label or an ID cell, compared after strip + casefold. The CSV is read with
# keep_default_na=False (so the output repeats every value as written); 'None' is not a code here,
# it is a common category ("None / Mild / Severe").
MISSING_CODES = frozenset({'na', 'n/a', 'nan', 'null', '#n/a', '<na>'})


def patient_key(value):
    """Normalised patient ID used for grouping: Unicode NFKC, surrounding whitespace removed, case
    ignored. A whole-number float (12.0, from a column pandas read as numbers) counts as 12."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return unicodedata.normalize('NFKC', str(value)).strip().casefold()


def _keys(series):
    """patient_key of every row (missing stays missing), computed once per distinct value."""
    return series.map({v: patient_key(v) for v in pd.unique(series.dropna())})


def _clean_labels(s):
    """Labels as used for the patient-level label: text stripped ('' = missing); when every label is a
    number they are compared as numbers ('1' and '1.0' are one class, '10' > '9')."""
    def clean(v):
        if not isinstance(v, str):
            return v
        v = v.strip()
        return None if not v or v.casefold() in MISSING_CODES else v
    s = s.map({v: clean(v) for v in pd.unique(s.dropna())})
    num = pd.to_numeric(s, errors='coerce')
    if num[s.notna()].notna().all():
        return num, True
    return s, False


def _label_name(v):
    """A label as shown in the summary: whole numbers without '.0' (1.0 -> '1')."""
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return str(int(v))
    return str(v)


def _patient_table(df, patient_col, label_col=None, patient_label='majority'):
    """One row per patient: '_pid' (normalised ID, see patient_key) and, with label_col, the patient-level
    label '_stratum'. Returns (table, normalised ID of every row).

    'majority' = most frequent label, a tie gives '<平票>'; 'any' = the largest numeric label. Missing
    labels are ignored when deriving the patient label; a patient whose labels are all missing gets its
    own stratum '<缺失>' (it is still assigned to a split, never dropped)."""
    if patient_label not in ('majority', 'any'):
        raise ValueError("patient_label 必须是 'majority' 或 'any'")
    if patient_col not in df.columns:
        raise ValueError(f"数据中没有患者 ID 列 {patient_col!r}；可用列：{list(df.columns)}")
    if label_col is not None and label_col not in df.columns:
        raise ValueError(f"数据中没有标签列 {label_col!r}；可用列：{list(df.columns)}")
    if len(df) == 0:
        raise ValueError("数据没有任何行")
    keys = _keys(df[patient_col])
    blank = keys.isna() | (keys == '')
    if blank.any():
        raise ValueError(f"患者 ID 列 {patient_col!r} 有 {int(blank.sum())} 行是空的（缺失或只有空格），无法按患者划分")
    coded = keys.isin(MISSING_CODES)
    if coded.any():
        codes = sorted({str(v).strip() for v in df[patient_col][coded]})[:3]
        raise ValueError(f"患者 ID 列 {patient_col!r} 有 {int(coded.sum())} 行写的是缺失值代码（{', '.join(codes)}），"
                         "这些行不知道属于哪名患者，无法按患者划分；请补全 ID 或删去这些行")
    if label_col is None:
        return pd.DataFrame({'_pid': keys.unique()}), keys
    labels, numeric = _clean_labels(df[label_col])
    if patient_label == 'any' and not numeric:
        examples = [str(v) for v in pd.unique(labels.dropna()) if pd.isna(pd.to_numeric(v, errors='coerce'))][:3]
        raise ValueError(f"--patient-label any 取每名患者标签的最大值（0/1 标签里任一行为 1 即为 1），只适用于数值标签；"
                         f"标签列 {label_col!r} 有文字取值（如 {examples}），请先编码为 0/1，或用 majority")

    rows = pd.DataFrame({'_pid': keys, '_lab': labels}).dropna(subset=['_lab'])
    if patient_label == 'any':
        per_patient = rows.groupby('_pid', sort=False)['_lab'].max()
    else:
        counts = rows.groupby(['_pid', '_lab'], sort=False).size().rename('n').reset_index()
        top = counts[counts['n'] == counts.groupby('_pid', sort=False)['n'].transform('max')]
        tied = top.groupby('_pid', sort=False)['_lab'].transform('size') > 1
        per_patient = (top.assign(_lab=top['_lab'].astype(object).where(~tied, TIE_STRATUM))
                       .drop_duplicates('_pid').set_index('_pid')['_lab'])
    pids = pd.Series(pd.unique(keys))
    stratum = pids.map(per_patient).astype(object)
    return pd.DataFrame({'_pid': pids, '_stratum': stratum.where(stratum.notna(), MISSING_STRATUM)}), keys


def _check_fractions(fractions, names):
    if len(fractions) != len(names):
        raise ValueError("fractions 与 names 长度必须一致")
    try:
        values = [float(f) for f in fractions]
    except (TypeError, ValueError):
        raise ValueError(f"fractions 必须是数字，收到 {fractions}")
    if not all(math.isfinite(f) and f >= 0 for f in values) or abs(sum(values) - 1.0) > 1e-6:
        raise ValueError(f"fractions 必须是有限的非负数且总和为 1，收到 {tuple(fractions)}")


def _check_seed(seed):
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError(f"seed 必须是非负整数（划分要能重现），收到 {seed!r}")


def _targets(n, fractions):
    """Split sizes that add up to n: floor of each share, the rest by largest remainder.
    (Cutting at floor(cumsum(fractions) * n) gave 21/5/4 for 0.7/0.2/0.1 of 30 through float error.)"""
    raw = [f * n for f in fractions]
    base = [int(np.floor(x + 1e-9)) for x in raw]
    rest = n - sum(base)
    order = sorted(range(len(raw)), key=lambda j: (-(raw[j] - base[j]), j))
    for j in order[:rest]:
        base[j] += 1
    return base


def _interleaved(targets):
    """A sequence with split j appearing targets[j] times, spread evenly (at every prefix each split
    is within one of its share), so any contiguous run of patients is split proportionally."""
    n = sum(targets)
    got = [0] * len(targets)
    seq = []
    for i in range(n):
        j = max(range(len(targets)), key=lambda j: (targets[j] * (i + 1) / n - got[j], -j))
        got[j] += 1
        seq.append(j)
    return seq


def _assign(pt, fractions, names, seed, stratified):
    """Take the strata in random order (patients shuffled within each stratum), then deal the patients
    onto an evenly interleaved sequence of splits. Split sizes match the fractions exactly overall,
    every stratum -- including strata of one or two patients -- is spread proportionally, and the seed
    changes the partition even when every stratum is a single patient (a continuous label: taking the
    strata in sorted order made the split almost the same for every seed). The input row order does
    not matter: patients and strata are sorted before they are shuffled."""
    rng = np.random.default_rng(seed)
    if stratified:
        groups = {}
        for pid, st in zip(pt['_pid'], pt['_stratum']):
            groups.setdefault(st, []).append(pid)
        strata = sorted(groups, key=lambda k: (type(k).__name__, str(k)))
        ordered = []
        for i in rng.permutation(len(strata)):
            ids = sorted(groups[strata[i]])
            rng.shuffle(ids)
            ordered.extend(ids)
    else:
        ordered = sorted(pt['_pid'])
        rng.shuffle(ordered)
    seq = _interleaved(_targets(len(ordered), fractions))
    if seq:
        shift = int(rng.integers(len(seq)))            # which split gets a stratum's "extra" varies
        seq = seq[shift:] + seq[:shift]
    return {pid: names[j] for pid, j in zip(ordered, seq)}


def _script_sha256():
    with open(os.path.abspath(__file__), 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_leakage(df, patient_col, split_col='split'):
    """Return the patients (normalised IDs, see patient_key) that appear in more than one split
    (empty = no leakage). 'P001', 'P001 ' and 'p001' count as the same patient."""
    counts = df[split_col].groupby(_keys(df[patient_col])).nunique()
    return counts[counts > 1].index.tolist()


def id_variants(df, patient_col):
    """Patient IDs written in more than one way that count as one patient (see patient_key): a table
    with columns patient_key, <patient_col> (each spelling, as written) and rows."""
    col = df[patient_col].dropna()
    t = (pd.DataFrame({'patient_key': col.map(patient_key), patient_col: col})
         .groupby(['patient_key', patient_col], sort=False).size().rename('rows').reset_index())
    t = t[t.groupby('patient_key')[patient_col].transform('size') > 1]
    order = sorted(range(len(t)), key=lambda i: (t['patient_key'].iloc[i], str(t[patient_col].iloc[i])))
    return t.iloc[order].reset_index(drop=True)


def class_distribution(df, split_col, label_col, names=None):
    """{split: {label: n_rows}} plus row totals. Labels are counted as the split uses them (see
    _clean_labels: '1', '1.0' and ' 1' are one class; empty / NA = '<缺失>'). With names, every
    split is listed, also one without rows."""
    names = list(names) if names is not None else sorted(df[split_col].dropna().unique(), key=str)
    if label_col is None:
        counts = df[split_col].value_counts()
        return {str(s): {'rows': int(counts.get(s, 0))} for s in names}
    labels, _ = _clean_labels(df[label_col])
    shown = labels.map(lambda v: MISSING_STRATUM if pd.isna(v) else _label_name(v))
    table = pd.crosstab(df[split_col], shown).reindex(names, fill_value=0)
    return {str(s): {str(k): int(v) for k, v in row.items()} | {'rows': int(row.sum())}
            for s, row in table.iterrows()}


# ─── public API ─────────────────────────────────────────────────────────────

def split_patients(df, patient_col, label_col=None, fractions=(0.6, 0.2, 0.2),
                   names=('train', 'val', 'test'), seed=42, patient_label='majority', split_col='split'):
    """Assign each patient (hence every row) to one of `names` with the given fractions.

    Stratified by the patient-level label when label_col is given. Patients are grouped by their
    normalised ID (patient_key), so ID spellings that differ only in spaces / case / full-width
    characters stay together. Returns (df_with_split, summary_dict). Raises if a patient lands in two
    splits or a row is left without a split (neither should ever happen).
    """
    _check_fractions(fractions, names)
    _check_seed(seed)
    if split_col in df.columns:
        raise ValueError(f"数据里已经有 {split_col!r} 列；为免覆盖，请先改名或指定另一个输出列名")
    pt, keys = _patient_table(df, patient_col, label_col, patient_label)
    warnings = []
    n_spellings = int(df[patient_col].nunique())
    n_variant_patients = int(id_variants(df, patient_col)['patient_key'].nunique()) if n_spellings > len(pt) else 0
    if n_variant_patients:
        warnings.append(f"{n_variant_patients} 名患者的 ID 有不止一种写法（首尾空格 / 大小写 / 全角字符）：已按同一患者处理，"
                        "放在同一集合；各写法见 split_id_variants.csv（命令行）或 id_variants()，请在原始数据里统一")
    if label_col is not None:
        counts = pt['_stratum'].value_counts()
        n_strata = len(counts)
        n_missing = int(counts.get(MISSING_STRATUM, 0))
        n_tie = int(counts.get(TIE_STRATUM, 0))
        n_splits = sum(1 for f in fractions if float(f) > 0)
        if n_missing:
            warnings.append(f"{n_missing} 名患者没有任何非缺失标签：归入单独一层 '{MISSING_STRATUM}'，仍被分配")
        if n_tie:
            warnings.append(f"{n_tie} 名患者各标签的行数相同（majority 平票）：归入单独一层 '{TIE_STRATUM}'，"
                            "在各集合中均匀分配")
        if n_strata > max(10, len(pt) // 10):
            warnings.append(f"标签有 {n_strata} 个不同取值，像连续变量：每层只有一两名患者，分层不起作用，实际是不分层的"
                            "随机划分（各集合的标签分布不保证相近）；如需分层，请先把标签分组（如按四分位）")
        else:
            small = [k for k, v in counts.items() if v < n_splits and k not in (MISSING_STRATUM, TIE_STRATUM)]
            if small:
                warnings.append(f"{len(small)} 个标签取值的患者数少于集合数 {n_splits}（如 {[_label_name(k) for k in small[:5]]}）："
                                "这些类别不可能出现在每个集合里，落在哪个集合是随机的；可考虑合并稀有类别")
    assignment = _assign(pt, fractions, names, seed, stratified=label_col is not None)
    out = df.copy()
    out[split_col] = keys.map(assignment)
    unassigned = int(out[split_col].isna().sum())
    if unassigned:
        raise RuntimeError(f"内部错误：{unassigned} 行没有分到任何集合")
    leaked = check_leakage(out, patient_col, split_col)
    if leaked:
        raise RuntimeError(f"内部错误：{len(leaked)} 名患者出现在多个集合中")
    per_split = keys.groupby(out[split_col]).nunique()
    empty = [nm for nm, f in zip(names, fractions) if float(f) > 0 and nm not in per_split.index]
    if empty:
        warnings.append(f"只有 {len(pt)} 名患者，{len(empty)} 个集合没有分到任何患者（{', '.join(map(str, empty))}）："
                        "这样的划分不能用来评估模型；请增加患者，或减少集合 / 调整比例")
    row_counts = out[split_col].value_counts()
    summary = {
        'method': 'patient-level hold-out',
        'seed': int(seed),
        'fractions': dict(zip(names, fractions)),
        'stratified_by': label_col,
        'patient_label_rule': patient_label if label_col else None,
        'n_patients': int(pt.shape[0]),
        'n_rows': int(len(out)),
        'patient_ids': {'grouping': 'NFKC, surrounding spaces removed, case ignored',
                        'n_spellings': n_spellings, 'patients_with_several_spellings': n_variant_patients},
        'patients_per_split': {str(nm): int(per_split.get(nm, 0)) for nm in names},
        'rows_per_split': {str(nm): int(row_counts.get(nm, 0)) for nm in names},
        'class_distribution': class_distribution(out, split_col, label_col, names),
        'leakage_check': {'patients_in_multiple_splits': leaked, 'rows_without_split': unassigned,
                          'passed': not leaked and not unassigned},
        'warnings': warnings,
        'software': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
                     'script_sha256': _script_sha256()},
    }
    return out, summary


def kfold_patients(df, patient_col, label_col=None, k=5, seed=42, patient_label='majority', split_col='split'):
    """Assign each patient to one of k folds (stratified when label_col given)."""
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)) or k < 2:
        raise ValueError(f"k 必须是 >= 2 的整数，收到 {k!r}")
    names = [f'fold_{i + 1}' for i in range(k)]
    fractions = [1.0 / k] * k
    out, summary = split_patients(df, patient_col, label_col, fractions, names, seed, patient_label, split_col)
    if summary['n_patients'] < k:
        raise ValueError(f"{k} 折交叉验证需要至少 {k} 名患者，数据里只有 {summary['n_patients']} 名（有的折会是空的）；"
                         "请减小 --kfold")
    summary['method'] = f'patient-level {k}-fold cross-validation'
    summary['k'] = int(k)
    return out, summary


# ─── CLI ────────────────────────────────────────────────────────────────────

def _fail(msg):
    """CLI error: one line on stderr, exit status 2 (never a traceback)."""
    print(str(msg).replace('\r', ' ').replace('\n', ' '), file=sys.stderr)
    raise SystemExit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):            # one line on stderr, exit 2 (argparse prints a usage block)
        _fail(f"参数错误：{message}（用 --help 查看用法）")


def _check_encoding(encoding, flag):
    try:
        codecs.lookup(encoding)
    except LookupError:
        raise ValueError(f"未知的编码名 {flag} {encoding!r}；常用：utf-8、gb18030、cp1252（Windows 西文）、latin-1")


# A Western (cp1252) file read as GB18030, and a GBK / GB18030 file read as cp1252: see _western_warning.
_NON_ASCII_RUN = re.compile(r'[^\x00-\x7f]+')
_WEDGED = re.compile(r'[A-Za-z][^\x00-\x7f][A-Za-z]')        # one non-ASCII character inside a Latin word
_LATIN_SYMBOLS = frozenset('°±²³µ·×÷€£¢¥§©®™«»‘’‚“”„–—…•¼½¾¹¿¡\xa0')


def _in_gb2312(ch):
    try:
        return len(ch.encode('gb2312')) == 2
    except UnicodeEncodeError:
        return False


def _gb_improbable(text):
    """True when a GB18030 reading holds characters that Chinese text rarely holds but a Western file
    read as GB18030 is full of: characters outside GB2312 (an accented byte followed by an ASCII letter
    pairs into a rare GBK character: 'Müller' -> 'M黮ler') or one character inside a Latin word (two
    accented letters pair into one GB2312 character: 'Conceição' -> 'Concei' + one character + 'o').
    Not enough on its own: Chinese names use characters outside GB2312 too (张喆), and GB18030 writes
    'µ' in four bytes -- _latin_plausible must agree."""
    return (any(ord(ch) >= 0x80 and not _in_gb2312(ch) for ch in set(text))
            or _WEDGED.search(text) is not None)


def _latin_plausible(text):
    """True when a cp1252 reading looks like Western text: every run of non-ASCII characters is one
    letter or common symbol, or two letters of the same case inside a word ('çã' in 'Conceição'), and
    at least one run touches an ASCII letter ('ü' in 'Müller', 'µ' in 'µmol'). Every Chinese character
    read as cp1252 gives two characters, mostly symbols or mixed-case letters, so a Chinese word gives a
    run of four or more ('王伟' -> 'Íõΰ', '张喆' -> 'ÕÅ†´') and fails."""
    in_word = False
    for m in _NON_ASCII_RUN.finditer(text):
        run = m.group()
        letters = all(unicodedata.category(c).startswith('L') for c in run)
        near = text[max(m.start() - 1, 0):m.start()] + text[m.end():m.end() + 1]
        touches = any(c.isascii() and c.isalpha() for c in near)
        if len(run) == 1:
            if not (letters or run in _LATIN_SYMBOLS):
                return False
        elif not (len(run) == 2 and letters and touches and (run.islower() or run.isupper())):
            return False
        in_word = in_word or touches
    return in_word


def _parse_csv(text, path):
    if text.startswith('\ufeff'):               # a BOM kept by --encoding utf-8 (or inside a GB18030 file)
        text = text[1:]
    try:
        return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        raise ValueError(f"{path} 是空文件（没有表头）")
    except pd.errors.ParserError as e:
        raise ValueError(f"{path} 不是可读的 CSV：{str(e).strip().splitlines()[0][:200]}")


def _same_patients(ids_a, ids_b):
    """Two readings of one ID column (row by row): (patients in a, patients in b, True when every pair
    of rows is one patient in both readings or in neither). Equal counts are not enough: one reading
    can merge two IDs and split two others."""
    a, b = _keys(ids_a).to_numpy(), _keys(ids_b).to_numpy()
    n_a, n_b = len(pd.unique(a)), len(pd.unique(b))
    return n_a, n_b, n_a == n_b == len(pd.DataFrame({'a': a, 'b': b}).drop_duplicates())


def _western_warning(raw, text, df, patient_col, path):
    """The warning for a file read as GB18030 that may be a Western (cp1252) file, or None.

    Warns only when the GB18030 reading is improbable Chinese AND the cp1252 reading is plausible
    Western text, and suggests --encoding cp1252 only when both readings group the rows into the same
    patients: another reading can merge IDs (two Chinese IDs one byte apart can read 'À…' and 'à…' in
    cp1252, one patient after case folding). Otherwise it gives both patient counts and names no
    encoding to switch to."""
    if patient_col not in df.columns or not _gb_improbable(text):
        return None
    try:
        western = raw.decode('cp1252')
    except UnicodeDecodeError:                    # bytes cp1252 does not use: not a cp1252 file
        return None
    if not _latin_plausible(western):
        return None
    head = ("文件不是 UTF-8，按 GB18030 读出了中文里少见的字符，而按 Windows 西文编码（cp1252）读是通顺的西文："
            "文件可能是 cp1252")
    tail = "；本次输出的 CSV 按 GB18030 写，与原文件逐字节一致"
    try:
        alt = _parse_csv(western, path)
    except ValueError:
        alt = None
    if alt is None or alt.shape != df.shape:
        return (head + "，但按 cp1252 读出的表格行列与按 GB18030 读出的不同：请先向导出数据的人确认文件编码，"
                "再用 --encoding 指定" + tail)
    col = list(df.columns).index(patient_col)
    n_a, n_b, same = _same_patients(df.iloc[:, col], alt.iloc[:, col])
    if same:
        return head + f"，请加 --encoding cp1252 重跑（两种读法下各行属于的患者完全相同，都是 {n_a} 名）" + tail
    return (head + f"，但两种读法下各行属于的患者不同（按 GB18030 是 {n_a} 名患者，按 cp1252 是 {n_b} 名：只差大小写 / "
            "全角 / 首尾空格的 ID 只在一种读法里算同一患者），换编码会改变谁算同一患者：请先向导出数据的人确认文件"
            "编码，再用 --encoding 指定" + tail)


def _read_csv(path, encoding=None, patient_col=None):
    """Every cell as text, exactly as written (no NA conversion): IDs keep their leading zeros and the
    output repeats the values as read. Returns (df, encoding the file was read with, warnings).
    patient_col: the ID column, used to check an encoding before the warning suggests it."""
    try:
        with open(path, 'rb') as f:
            raw = f.read()
    except OSError as e:
        raise ValueError(f"无法读取 {path}：{e.strerror or e}")
    warnings = []
    if encoding is not None:
        _check_encoding(encoding, '--encoding')
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError as e:
            raise ValueError(f"{path} 不能按 {encoding} 解码（第 {e.start + 1} 个字节 0x{raw[e.start]:02X}）；"
                             "请换一个 --encoding，或去掉 --encoding 让脚本自动识别 UTF-8 / GB18030")
        used = encoding
    else:
        try:
            text = raw.decode('utf-8-sig')
            used = 'utf-8-sig' if raw.startswith(codecs.BOM_UTF8) else 'utf-8'
        except UnicodeDecodeError:
            try:
                text = raw.decode('gb18030')
            except UnicodeDecodeError:
                raise ValueError(f"{path} 既不是 UTF-8 也不是 GB18030 编码；请用 --encoding 指定"
                                 "（Windows 西文文件用 --encoding cp1252）")
            used = 'gb18030'
    df = _parse_csv(text, path)
    if used == 'gb18030' and encoding is None and patient_col is not None:
        warning = _western_warning(raw, text, df, patient_col, path)
        if warning:
            warnings.append(warning)
    return df, used, warnings


class _Unwritable(Exception):
    """An output file holds a character its encoding cannot write (nothing was written)."""
    def __init__(self, name, char):
        super().__init__(name)
        self.name, self.char = name, char


class _PartialWrite(Exception):
    """Moving the finished files into place failed after `done` were replaced (e.g. on Windows, an
    output file open in Excel cannot be replaced)."""
    def __init__(self, done, error):
        super().__init__(error)
        self.done, self.error = done, error


def _write_outputs(out_dir, tables, encoding, summary):
    """Write every output or none. Each file is encoded in memory first (a character the encoding
    cannot write fails before anything is touched), then written to a temporary file in out_dir; the
    files are moved into place only when all of them were written, the summary last. A
    split_id_variants.csv left over from an earlier run is removed after that. Raises _Unwritable or
    OSError when nothing in out_dir was changed, _PartialWrite when a move failed after others had
    succeeded; temporary files never stay behind."""
    contents = {}
    for name, table in tables.items():
        text = table.to_csv(index=False)
        try:
            contents[name] = text.encode(encoding)
        except UnicodeEncodeError as e:
            raise _Unwritable(name, e.object[e.start])
    contents['split_summary.json'] = json.dumps(summary, ensure_ascii=False, indent=2).encode('utf-8')
    for name in contents:                         # a folder in the way would fail halfway through the moves
        if os.path.isdir(os.path.join(out_dir, name)):
            raise IsADirectoryError(errno.EISDIR, f"{name} 是一个文件夹", os.path.join(out_dir, name))
    os.makedirs(out_dir, exist_ok=True)
    temps, done = {}, []
    try:
        for name, data in contents.items():
            temps[name] = os.path.join(out_dir, f'.{name}.{secrets.token_hex(4)}.tmp')
            with open(temps[name], 'xb') as f:
                f.write(data)
        try:
            for name, tmp in list(temps.items()):
                os.replace(tmp, os.path.join(out_dir, name))
                del temps[name]
                done.append(name)
            variants_path = os.path.join(out_dir, 'split_id_variants.csv')
            if 'split_id_variants.csv' not in contents and os.path.isfile(variants_path):
                os.remove(variants_path)
        except OSError as e:
            if done:
                raise _PartialWrite(done, e) from e
            raise
    finally:
        for tmp in temps.values():
            try:
                os.remove(tmp)
            except OSError:
                pass


def main(argv=None):
    p = _Parser(description='Patient-level, stratified, seeded data split with leakage check.')
    p.add_argument('csv', help='one row per sample (image/slice/record) with a patient id column')
    p.add_argument('--patient-col', required=True)
    p.add_argument('--label-col', default=None, help='label used for stratification (optional)')
    p.add_argument('--patient-label', choices=['majority', 'any'], default='majority',
                   help="how to derive one label per patient from its rows: majority (a tie forms its own "
                        "stratum) or any (largest numeric label, e.g. 1 if any row is 1)")
    p.add_argument('--train', type=float, default=None,
                   help='training fraction as the SAP specifies (default 0.6; the defaults are placeholders, '
                        'not a recommendation -- the SAP chooses the validation design by model type and '
                        'events, D3)')
    p.add_argument('--val', type=float, default=None, help='validation fraction as the SAP specifies (default 0.2)')
    p.add_argument('--test', type=float, default=None, help='test fraction as the SAP specifies (default 0.2)')
    p.add_argument('--kfold', type=int, default=None, help='use K-fold instead of hold-out')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--split-col', default='split', help='name of the new column (must not exist yet)')
    p.add_argument('--encoding', default=None,
                   help='CSV encoding (default: UTF-8 with or without BOM, else GB18030; e.g. cp1252); '
                        'the CSV outputs are written in the same encoding unless --output-encoding is given')
    p.add_argument('--output-encoding', default=None,
                   help="encoding of the CSV outputs (default: the input's, so IDs stay byte-for-byte those "
                        "of the source file); e.g. utf-8 when a value cannot be written in the input's encoding")
    p.add_argument('--out-dir', default='data/splits')
    args = p.parse_args(argv)

    names = ('train', 'val', 'test')
    fractions = tuple(d if x is None else x for x, d in zip((args.train, args.val, args.test), (0.6, 0.2, 0.2)))
    try:                                               # argument checks first, before reading the data
        if args.kfold is not None:                     # --kfold 0 / 1 is an error, not a hold-out
            if any(x is not None for x in (args.train, args.val, args.test)):
                raise ValueError("--kfold 不能与 --train / --val / --test 同时用（K 折时每折各占 1/K）")
            if args.kfold < 2:
                raise ValueError(f"k 必须是 >= 2 的整数，收到 --kfold {args.kfold}")
        else:
            _check_fractions(fractions, names)
        _check_seed(args.seed)
        for value, flag in ((args.encoding, '--encoding'), (args.output_encoding, '--output-encoding')):
            if value is not None:
                _check_encoding(value, flag)
    except ValueError as e:
        _fail(f"参数错误：{e}")
    if not os.path.isfile(args.csv):
        _fail(f"找不到文件 {args.csv}（当前目录 {os.getcwd()}）" if not os.path.exists(args.csv)
              else f"{args.csv} 不是文件")
    if any(os.path.realpath(os.path.join(args.out_dir, f)) == os.path.realpath(args.csv) for f in OUTPUT_FILES):
        _fail(f"输入文件 {args.csv} 和 --out-dir 里的输出文件同名：会被覆盖，请换一个 --out-dir")
    try:
        df, encoding, read_warnings = _read_csv(args.csv, args.encoding, args.patient_col)
        if args.kfold is not None:
            out, summary = kfold_patients(df, args.patient_col, args.label_col, args.kfold,
                                          args.seed, args.patient_label, args.split_col)
        else:
            out, summary = split_patients(df, args.patient_col, args.label_col, fractions, names,
                                          args.seed, args.patient_label, args.split_col)
    except (ValueError, OSError) as e:
        _fail(f"参数错误：{e}")

    variants = id_variants(df, args.patient_col)
    summary['patient_ids']['variants_file'] = 'split_id_variants.csv' if len(variants) else None
    out_encoding = args.output_encoding or encoding
    summary['input'] = {'encoding': encoding, 'csv_outputs_encoding': out_encoding}
    summary['warnings'] = read_warnings + summary['warnings']
    tables = {'split_assignment.csv': out,
              'split_patients.csv': out[[args.patient_col, args.split_col]].drop_duplicates()}
    if len(variants):
        tables['split_id_variants.csv'] = variants
    try:
        _write_outputs(args.out_dir, tables, out_encoding, summary)
    except OSError as e:
        _fail(f"无法写入 {args.out_dir}：{e.strerror or e}；没有写入任何输出文件（目录里原有的文件未改动）")
    except _PartialWrite as e:
        rest = [n for n in [*tables, 'split_summary.json'] if n not in e.done]
        _fail(f"无法写入 {args.out_dir}：{e.error.strerror or e.error}。已替换 {', '.join(e.done)}，"
              + (f"未替换 {', '.join(rest)}：这些输出来自不同的运行，不要使用；" if rest else
                 "但上次运行留下的 split_id_variants.csv 没能删除（它不属于这次划分）；")
              + "关闭占用这些文件的程序（如 Excel）后重跑")
    except _Unwritable as e:
        where = (f"（--split-col 的列名；也可以给 --split-col 换一个 {out_encoding} 能写的名字）"
                 if e.char in str(args.split_col) else
                 "（patient_key 列是统一写法后的 ID）" if e.name == 'split_id_variants.csv' else "")
        _fail(f"{e.name} 里有 {out_encoding} 写不出的字符 U+{ord(e.char):04X}{where}：没有写入任何输出文件"
              f"（{args.out_dir} 里原有的文件未改动）。请加 --output-encoding utf-8 重跑：输入仍按 {encoding} 读，"
              "只是输出的 CSV 改用 UTF-8（读回时按 UTF-8 读）")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for w in summary['warnings']:
        print(f"[Split] 警告：{w}", file=sys.stderr)
    written = ', '.join(f for f in OUTPUT_FILES if f != 'split_id_variants.csv' or len(variants))
    print(f"[Split] wrote {args.out_dir}/: {written}")
    return out, summary


if __name__ == '__main__':
    main()
