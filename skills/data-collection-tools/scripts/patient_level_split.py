#!/usr/bin/env python3
"""
Patient-level train / val / test split (or K-fold) for AI/ML studies.

Why: splitting by image / slice / frame leaks the same patient into both the training
and the test set and inflates performance. This script assigns every row of a patient
to ONE split, optionally stratified by label, with a fixed seed, and verifies that no
patient appears in more than one split.

Command line (from the project directory):
    python3 patient_level_split.py data/annotations/consensus/labels.csv \
        --patient-col patient_id --label-col label --train 0.6 --val 0.2 --test 0.2 \
        --seed 42 --out-dir data/splits
    python3 patient_level_split.py labels.csv --patient-col patient_id --label-col label --kfold 5

Outputs (in --out-dir):
    split_assignment.csv   one row per input row + column `split` (train/val/test or fold_k)
    split_patients.csv     one row per patient + split
    split_summary.json     per-split patient / row counts, class distribution, leakage check, seed

Library use:
    import os, sys
    sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                    "skills", "data-collection-tools", "scripts"))
    from patient_level_split import split_patients, kfold_patients, check_leakage
"""

import argparse
import json
import os

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover - depends on the user's environment
    raise SystemExit("缺少 pandas / numpy：pip install pandas numpy")


# ─── helpers ────────────────────────────────────────────────────────────────

MISSING_STRATUM = '<缺失>'


def _patient_table(df, patient_col, label_col=None, patient_label='majority'):
    """One row per patient with a patient-level label (majority vote or 'any' = the maximum).

    Missing labels are ignored when deriving the patient label; a patient whose labels are all
    missing gets its own stratum '<缺失>' (it is still assigned to a split, never dropped)."""
    if patient_col not in df.columns:
        raise ValueError(f"数据中没有患者 ID 列 {patient_col!r}；可用列：{list(df.columns)}")
    if df[patient_col].isna().any():
        raise ValueError(f"患者 ID 列 {patient_col!r} 含缺失值，无法按患者划分")
    if label_col is None:
        return pd.DataFrame({patient_col: df[patient_col].unique()})
    if label_col not in df.columns:
        raise ValueError(f"数据中没有标签列 {label_col!r}；可用列：{list(df.columns)}")
    if patient_label not in ('majority', 'any'):
        raise ValueError("patient_label 必须是 'majority' 或 'any'")

    def one(s):
        s = s.dropna()
        if s.empty:
            return MISSING_STRATUM
        return s.mode().sort_values().iloc[0] if patient_label == 'majority' else s.max()

    lab = df.groupby(patient_col, sort=False)[label_col].agg(one)
    return lab.rename('_stratum').reset_index()


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


def _assign(pt, patient_col, fractions, names, seed, stratified):
    """Order patients by stratum (shuffled within each stratum), then deal them onto an evenly
    interleaved sequence of splits. Split sizes match the fractions exactly overall, and every
    stratum -- including strata of one or two patients -- is spread proportionally."""
    rng = np.random.default_rng(seed)
    ordered = []
    if stratified:
        for _, grp in pt.groupby('_stratum', sort=True):
            ids = grp[patient_col].to_numpy(copy=True)
            rng.shuffle(ids)
            ordered.extend(ids.tolist())
    else:
        ids = pt[patient_col].to_numpy(copy=True)
        rng.shuffle(ids)
        ordered = ids.tolist()
    seq = _interleaved(_targets(len(ordered), fractions))
    if seq:
        shift = int(rng.integers(len(seq)))            # which split gets a stratum's "extra" varies
        seq = seq[shift:] + seq[:shift]
    return {pid: names[j] for pid, j in zip(ordered, seq)}


def check_leakage(df, patient_col, split_col='split'):
    """Return the list of patient ids appearing in more than one split (empty = no leakage)."""
    counts = df.groupby(patient_col)[split_col].nunique()
    return counts[counts > 1].index.tolist()


def class_distribution(df, split_col, label_col):
    """{split: {label: n_rows}} plus row totals."""
    if label_col is None:
        return {s: {'rows': int(n)} for s, n in df[split_col].value_counts().items()}
    table = pd.crosstab(df[split_col], df[label_col].astype(object).where(df[label_col].notna(), MISSING_STRATUM))
    return {str(s): {str(k): int(v) for k, v in row.items()} | {'rows': int(row.sum())}
            for s, row in table.iterrows()}


# ─── public API ─────────────────────────────────────────────────────────────

def split_patients(df, patient_col, label_col=None, fractions=(0.6, 0.2, 0.2),
                   names=('train', 'val', 'test'), seed=42, patient_label='majority', split_col='split'):
    """Assign each patient (hence every row) to one of `names` with the given fractions.

    Stratified by the patient-level label when label_col is given.
    Returns (df_with_split, summary_dict). Raises if a patient lands in two splits or a row is
    left without a split (neither should ever happen).
    """
    if len(fractions) != len(names):
        raise ValueError("fractions 与 names 长度必须一致")
    if any(f < 0 for f in fractions) or abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError(f"fractions 必须为非负且总和为 1，收到 {fractions}")
    if split_col in df.columns:
        raise ValueError(f"数据里已经有 {split_col!r} 列；为免覆盖，请先改名或指定另一个输出列名")
    pt = _patient_table(df, patient_col, label_col, patient_label)
    warnings = []
    if label_col is not None:
        n_strata = pt['_stratum'].nunique()
        n_missing = int((pt['_stratum'] == MISSING_STRATUM).sum())
        if n_missing:
            warnings.append(f"{n_missing} 名患者没有任何非缺失标签：归入单独一层 '{MISSING_STRATUM}'，仍被分配")
        if n_strata > max(10, len(pt) // 10):
            warnings.append(f"标签有 {n_strata} 个不同取值，像连续变量：已按取值排序后均匀分配（各集合分布相近）；"
                            "如需按类别分层，请先把标签分组")
    assignment = _assign(pt, patient_col, fractions, names, seed, stratified=label_col is not None)
    out = df.copy()
    out[split_col] = out[patient_col].map(assignment)
    unassigned = int(out[split_col].isna().sum())
    if unassigned:
        raise RuntimeError(f"内部错误：{unassigned} 行没有分到任何集合")
    leaked = check_leakage(out, patient_col, split_col)
    if leaked:
        raise RuntimeError(f"内部错误：患者 {leaked[:5]} 出现在多个集合中")
    summary = {
        'method': 'patient-level hold-out',
        'seed': seed,
        'fractions': dict(zip(names, fractions)),
        'stratified_by': label_col,
        'patient_label_rule': patient_label if label_col else None,
        'n_patients': int(pt.shape[0]),
        'n_rows': int(len(out)),
        'patients_per_split': {str(k): int(v) for k, v in out.groupby(split_col)[patient_col].nunique().items()},
        'rows_per_split': {str(k): int(v) for k, v in out[split_col].value_counts().items()},
        'class_distribution': class_distribution(out, split_col, label_col),
        'leakage_check': {'patients_in_multiple_splits': leaked, 'rows_without_split': unassigned,
                          'passed': not leaked and not unassigned},
        'warnings': warnings,
    }
    return out, summary


def kfold_patients(df, patient_col, label_col=None, k=5, seed=42, patient_label='majority', split_col='split'):
    """Assign each patient to one of k folds (stratified when label_col given)."""
    if k < 2:
        raise ValueError("k 必须 >= 2")
    names = [f'fold_{i + 1}' for i in range(k)]
    fractions = [1.0 / k] * k
    out, summary = split_patients(df, patient_col, label_col, fractions, names, seed, patient_label, split_col)
    summary['method'] = f'patient-level {k}-fold cross-validation'
    summary['k'] = k
    return out, summary


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv=None):
    p = argparse.ArgumentParser(description='Patient-level, stratified, seeded data split with leakage check.')
    p.add_argument('csv', help='one row per sample (image/slice/record) with a patient id column')
    p.add_argument('--patient-col', required=True)
    p.add_argument('--label-col', default=None, help='label used for stratification (optional)')
    p.add_argument('--patient-label', choices=['majority', 'any'], default='majority',
                   help="how to derive one label per patient from its rows")
    p.add_argument('--train', type=float, default=0.6)
    p.add_argument('--val', type=float, default=0.2)
    p.add_argument('--test', type=float, default=0.2)
    p.add_argument('--kfold', type=int, default=None, help='use K-fold instead of hold-out')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--split-col', default='split', help='name of the new column (must not exist yet)')
    p.add_argument('--out-dir', default='data/splits')
    args = p.parse_args(argv)

    if not os.path.exists(args.csv):
        raise SystemExit(f"找不到文件 {args.csv}（当前目录 {os.getcwd()}）")
    df = pd.read_csv(args.csv)
    try:
        if args.kfold is not None:                     # --kfold 0 / 1 is an error, not a hold-out
            out, summary = kfold_patients(df, args.patient_col, args.label_col, args.kfold,
                                          args.seed, args.patient_label, args.split_col)
        else:
            out, summary = split_patients(df, args.patient_col, args.label_col,
                                          (args.train, args.val, args.test),
                                          ('train', 'val', 'test'), args.seed, args.patient_label,
                                          args.split_col)
    except ValueError as e:
        raise SystemExit(f"参数错误：{e}")

    os.makedirs(args.out_dir, exist_ok=True)
    out.to_csv(os.path.join(args.out_dir, 'split_assignment.csv'), index=False)
    out[[args.patient_col, args.split_col]].drop_duplicates().to_csv(
        os.path.join(args.out_dir, 'split_patients.csv'), index=False)
    with open(os.path.join(args.out_dir, 'split_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[Split] wrote {args.out_dir}/split_assignment.csv, split_patients.csv, split_summary.json")
    return out, summary


if __name__ == '__main__':
    main()
