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

def _patient_table(df, patient_col, label_col=None, patient_label='majority'):
    """One row per patient with a patient-level label (majority vote or 'any' positive)."""
    if patient_col not in df.columns:
        raise ValueError(f"数据中没有患者 ID 列 {patient_col!r}；可用列：{list(df.columns)}")
    if df[patient_col].isna().any():
        raise ValueError(f"患者 ID 列 {patient_col!r} 含缺失值，无法按患者划分")
    if label_col is None:
        return pd.DataFrame({patient_col: df[patient_col].unique()})
    if label_col not in df.columns:
        raise ValueError(f"数据中没有标签列 {label_col!r}；可用列：{list(df.columns)}")
    if patient_label == 'majority':
        lab = df.groupby(patient_col)[label_col].agg(lambda s: s.mode().iloc[0])
    elif patient_label == 'any':
        lab = df.groupby(patient_col)[label_col].agg(lambda s: s.max())
    else:
        raise ValueError("patient_label 必须是 'majority' 或 'any'")
    return lab.rename('_stratum').reset_index()


def _assign_by_fraction(patients, fractions, names, seed):
    """Shuffle patient ids (within a stratum) and cut by cumulative fractions."""
    rng = np.random.default_rng(seed)
    ids = np.array(patients)
    rng.shuffle(ids)
    n = len(ids)
    cuts = np.floor(np.cumsum(fractions) * n).astype(int)
    cuts[-1] = n
    out = {}
    start = 0
    for name, end in zip(names, cuts):
        for pid in ids[start:end]:
            out[pid] = name
        start = end
    return out


def check_leakage(df, patient_col, split_col='split'):
    """Return the list of patient ids appearing in more than one split (empty = no leakage)."""
    counts = df.groupby(patient_col)[split_col].nunique()
    return counts[counts > 1].index.tolist()


def class_distribution(df, split_col, label_col):
    """{split: {label: n_rows}} plus row totals."""
    if label_col is None:
        return {s: {'rows': int(n)} for s, n in df[split_col].value_counts().items()}
    table = pd.crosstab(df[split_col], df[label_col])
    return {str(s): {str(k): int(v) for k, v in row.items()} | {'rows': int(row.sum())}
            for s, row in table.iterrows()}


# ─── public API ─────────────────────────────────────────────────────────────

def split_patients(df, patient_col, label_col=None, fractions=(0.6, 0.2, 0.2),
                   names=('train', 'val', 'test'), seed=42, patient_label='majority'):
    """Assign each patient (hence every row) to one of `names` with the given fractions.

    Stratified by the patient-level label when label_col is given.
    Returns (df_with_split, summary_dict). Raises if leakage is detected (should never happen).
    """
    if len(fractions) != len(names):
        raise ValueError("fractions 与 names 长度必须一致")
    if any(f < 0 for f in fractions) or abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError(f"fractions 必须为非负且总和为 1，收到 {fractions}")
    pt = _patient_table(df, patient_col, label_col, patient_label)
    assignment = {}
    if label_col is None:
        assignment.update(_assign_by_fraction(pt[patient_col].tolist(), fractions, names, seed))
    else:
        for i, (_, grp) in enumerate(pt.groupby('_stratum', sort=True)):
            assignment.update(_assign_by_fraction(grp[patient_col].tolist(), fractions, names, seed + i))
    out = df.copy()
    out['split'] = out[patient_col].map(assignment)
    leaked = check_leakage(out, patient_col)
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
        'patients_per_split': {str(k): int(v) for k, v in out.groupby('split')[patient_col].nunique().items()},
        'rows_per_split': {str(k): int(v) for k, v in out['split'].value_counts().items()},
        'class_distribution': class_distribution(out, 'split', label_col),
        'leakage_check': {'patients_in_multiple_splits': leaked, 'passed': not leaked},
    }
    return out, summary


def kfold_patients(df, patient_col, label_col=None, k=5, seed=42, patient_label='majority'):
    """Assign each patient to one of k folds (stratified when label_col given)."""
    if k < 2:
        raise ValueError("k 必须 >= 2")
    names = [f'fold_{i + 1}' for i in range(k)]
    fractions = [1.0 / k] * k
    out, summary = split_patients(df, patient_col, label_col, fractions, names, seed, patient_label)
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
    p.add_argument('--out-dir', default='data/splits')
    args = p.parse_args(argv)

    if not os.path.exists(args.csv):
        raise SystemExit(f"找不到文件 {args.csv}（当前目录 {os.getcwd()}）")
    df = pd.read_csv(args.csv)
    try:
        if args.kfold:
            out, summary = kfold_patients(df, args.patient_col, args.label_col, args.kfold,
                                          args.seed, args.patient_label)
        else:
            out, summary = split_patients(df, args.patient_col, args.label_col,
                                          (args.train, args.val, args.test),
                                          ('train', 'val', 'test'), args.seed, args.patient_label)
    except ValueError as e:
        raise SystemExit(f"参数错误：{e}")

    os.makedirs(args.out_dir, exist_ok=True)
    out.to_csv(os.path.join(args.out_dir, 'split_assignment.csv'), index=False)
    out[[args.patient_col, 'split']].drop_duplicates().to_csv(
        os.path.join(args.out_dir, 'split_patients.csv'), index=False)
    with open(os.path.join(args.out_dir, 'split_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[Split] wrote {args.out_dir}/split_assignment.csv, split_patients.csv, split_summary.json")
    return out, summary


if __name__ == '__main__':
    main()
