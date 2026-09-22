#!/usr/bin/env python3
"""
Statistical assumption tests and method selection for medical research.

Library use (run from the user's project directory):
    import os, sys
    sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                    "skills", "statistical-analysis", "scripts"))
    from assumption_tests import full_check, effect_size_cohens_d
    report = full_check(group_a, group_b, paired=False)   # json.dumps(report) works

Command line (long-format CSV, prints JSON):
    python3 assumption_tests.py data_clean.csv --value outcome --group arm [--paired --id patient_id]

All results contain plain Python bool/float/int (no numpy scalars), so they can be
written straight into analysis-log.md via json.dumps.
"""

import argparse
import json

try:
    import numpy as np
    from scipy import stats
except ImportError:  # pragma: no cover - depends on the user's environment
    raise SystemExit("缺少 scipy / numpy：pip install scipy numpy")


# ─── helpers ────────────────────────────────────────────────────────────────

def _to_array(data):
    """Coerce list/Series/array (may contain None or NaN) to a float array without NaN."""
    arr = np.asarray(data, dtype=float).ravel()
    return arr[~np.isnan(arr)]


def _to_array_keep_nan(data):
    return np.asarray(data, dtype=float).ravel()


# ─── single tests ───────────────────────────────────────────────────────────

def check_normality(data, alpha=0.05):
    """Test normality. Auto-selects Shapiro-Wilk (n<50) or D'Agostino-Pearson (n>=50).

    n < 8: normality is untestable -> is_normal=None, recommendation non-parametric.
    """
    data = _to_array(data)
    n = int(len(data))
    if n < 8:
        return {'method': 'too_few_samples', 'n': n, 'is_normal': None,
                'recommendation': 'Non-parametric (n<8, normality untestable)'}
    if float(np.ptp(data)) == 0.0:
        return {'method': 'constant_data', 'n': n, 'is_normal': None,
                'recommendation': 'All values identical (zero variance) — normality test not applicable'}
    if n < 50:
        stat, p = stats.shapiro(data)
        method = 'Shapiro-Wilk'
    else:
        stat, p = stats.normaltest(data)
        method = "D'Agostino-Pearson"
    p = float(p)
    return {
        'method': method, 'statistic': round(float(stat), 4), 'p_value': round(p, 4),
        'n': n, 'is_normal': bool(p > alpha),
        'recommendation': 'Parametric' if p > alpha else 'Non-parametric',
    }


def check_homogeneity(*groups, alpha=0.05):
    """Test homogeneity of variance across independent groups (Levene, median-centred)."""
    clean = [_to_array(g) for g in groups]
    if len(clean) < 2:
        raise ValueError("方差齐性检验至少需要 2 组")
    if any(len(g) < 2 for g in clean):
        raise ValueError("每组至少需要 2 个非缺失观测才能做 Levene 检验")
    stat, p = stats.levene(*clean)
    p = float(p)
    return {
        'method': 'Levene', 'statistic': round(float(stat), 4), 'p_value': round(p, 4),
        'is_homogeneous': bool(p > alpha),
        'note': 'Equal variances assumed' if p > alpha else 'Use Welch correction or non-parametric',
    }


def choose_test(n_groups, paired=False, all_normal=True, homogeneous=True):
    """Recommend a statistical test from the assumption results."""
    if n_groups < 2:
        return 'One-sample t-test' if all_normal else 'Wilcoxon signed-rank (one-sample)'
    if n_groups == 2:
        if all_normal:
            if paired:
                return 'Paired t-test'
            return 'Independent t-test' if homogeneous else "Welch's t-test"
        return 'Wilcoxon signed-rank' if paired else 'Mann-Whitney U'
    # > 2 groups
    if paired:
        return ('Repeated-measures ANOVA (check sphericity: Mauchly; Greenhouse-Geisser if violated)'
                if all_normal else 'Friedman + Nemenyi')
    if all_normal and homogeneous:
        return 'One-way ANOVA + Tukey HSD'
    if all_normal and not homogeneous:
        return "Welch's ANOVA + Games-Howell"
    return 'Kruskal-Wallis + Dunn'


# ─── full report ────────────────────────────────────────────────────────────

def _complete_pairs(*groups):
    """Row-wise complete cases across equal-length groups. Raises on length mismatch."""
    arrays = [_to_array_keep_nan(g) for g in groups]
    lengths = [len(a) for a in arrays]
    if len(set(lengths)) != 1:
        raise ValueError(
            f"配对数据各组长度不等：{lengths}。配对/重复测量分析要求每组按同一受试者顺序一一对应；"
            "请先按受试者 ID 对齐（合并成宽表）再传入。")
    mask = np.ones(lengths[0], dtype=bool)
    for a in arrays:
        mask &= ~np.isnan(a)
    return [a[mask] for a in arrays], int(mask.sum()), int((~mask).sum())


def full_check(*groups, paired=False, alpha=0.05):
    """Run all assumption tests and recommend a method. Returns a JSON-serialisable dict.

    Independent groups : normality per group (+ Levene when >= 2 groups).
    Paired, 2 groups   : complete pairs only, then normality of the differences.
    Paired, > 2 groups : complete cases only, normality per condition; Levene is skipped
                         (use Mauchly's sphericity test / Greenhouse-Geisser in RM-ANOVA).
    Any group with n < 8 -> all_normal=False and a warning (normality untestable).
    """
    warnings = []
    if len(groups) == 0:
        raise ValueError("至少传入 1 组数据")

    if paired and len(groups) == 2:
        (a, b), n_pairs, n_dropped = _complete_pairs(*groups)
        if n_dropped:
            warnings.append(f"已剔除 {n_dropped} 对含缺失值的配对，保留 {n_pairs} 对完整配对")
        diff_normality = check_normality(a - b, alpha)
        if diff_normality['is_normal'] is None:
            warnings.append(f"完整配对数 {n_pairs} < 8，差值正态性无法检验，按非参数处理")
            all_normal = False
        else:
            all_normal = bool(diff_normality['is_normal'])
        return {
            'design': 'paired_two_groups',
            'n_pairs': n_pairs,
            'n_pairs_dropped': n_dropped,
            'normality_tests': [diff_normality],
            'normality_note': 'Tested on paired differences (not individual groups)',
            'homogeneity_test': None,
            'homogeneity_note': 'Levene test not applicable for paired data',
            'all_normal': all_normal,
            'homogeneous': None,
            'recommended_test': choose_test(2, paired=True, all_normal=all_normal, homogeneous=True),
            'alpha': alpha,
            'warnings': warnings,
        }

    if paired and len(groups) > 2:
        arrays, n_complete, n_dropped = _complete_pairs(*groups)
        if n_dropped:
            warnings.append(f"已剔除 {n_dropped} 个含缺失值的受试者，保留 {n_complete} 个完整病例")
        normality = [check_normality(a, alpha) for a in arrays]
        untestable = [i + 1 for i, r in enumerate(normality) if r['is_normal'] is None]
        if untestable:
            warnings.append(f"条件 {untestable} 的 n < 8，正态性无法检验，按非参数处理")
            all_normal = False
        else:
            all_normal = all(bool(r['is_normal']) for r in normality)
        return {
            'design': 'repeated_measures',
            'n_complete': n_complete,
            'n_dropped': n_dropped,
            'normality_tests': normality,
            'normality_note': 'Tested per condition on complete cases',
            'homogeneity_test': None,
            'homogeneity_note': ('Levene skipped for repeated measures (>2 conditions): '
                                 "test sphericity with Mauchly's test; apply Greenhouse-Geisser "
                                 'correction if violated'),
            'all_normal': all_normal,
            'homogeneous': None,
            'recommended_test': choose_test(len(groups), paired=True, all_normal=all_normal,
                                            homogeneous=True),
            'alpha': alpha,
            'warnings': warnings,
        }

    # independent groups
    normality = [check_normality(g, alpha) for g in groups]
    untestable = [i + 1 for i, r in enumerate(normality) if r['is_normal'] is None]
    if untestable:
        warnings.append(f"组 {untestable} 的 n < 8，正态性无法检验，按非参数处理（all_normal=False）")
        all_normal = False
    else:
        all_normal = all(bool(r['is_normal']) for r in normality)
    homogeneity = None
    homogeneous = True
    if len(groups) > 1:
        try:
            homogeneity = check_homogeneity(*groups, alpha=alpha)
            homogeneous = bool(homogeneity['is_homogeneous'])
        except ValueError as e:
            warnings.append(f"Levene 检验未执行：{e}")
            homogeneous = False
    recommended = choose_test(len(groups), paired=False, all_normal=all_normal, homogeneous=homogeneous)
    return {
        'design': 'independent_groups',
        'normality_tests': normality,
        'homogeneity_test': homogeneity,
        'all_normal': all_normal,
        'homogeneous': homogeneous if homogeneity else None,
        'recommended_test': recommended,
        'alpha': alpha,
        'warnings': warnings,
    }


def effect_size_cohens_d(group1, group2):
    """Cohen's d (pooled SD) with approximate 95% CI for two independent groups."""
    g1, g2 = _to_array(group1), _to_array(group2)
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        raise ValueError("每组至少需要 2 个非缺失观测才能计算 Cohen's d")
    pooled_var = ((n1 - 1) * g1.var(ddof=1) + (n2 - 1) * g2.var(ddof=1)) / (n1 + n2 - 2)
    pooled_std = float(np.sqrt(pooled_var))
    if pooled_std == 0:
        raise ValueError("两组合并标准差为 0，无法计算 Cohen's d")
    d = float((g1.mean() - g2.mean()) / pooled_std)
    se_d = float(np.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2 - 2))))
    ad = abs(d)
    if ad < 0.2:
        magnitude = 'negligible'
    elif ad < 0.5:
        magnitude = 'small'
    elif ad < 0.8:
        magnitude = 'medium'
    else:
        magnitude = 'large'
    return {
        'cohens_d': round(d, 3),
        'ci_95': [round(d - 1.96 * se_d, 3), round(d + 1.96 * se_d, 3)],
        'magnitude': magnitude,
        'n1': int(n1), 'n2': int(n2),
    }


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv=None):
    p = argparse.ArgumentParser(
        description='Assumption checks + test recommendation from a long-format CSV (prints JSON).')
    p.add_argument('csv', help='long-format CSV: one row per observation')
    p.add_argument('--value', required=True, help='numeric outcome column')
    p.add_argument('--group', required=True, help='grouping / condition column')
    p.add_argument('--paired', action='store_true', help='paired / repeated-measures design')
    p.add_argument('--id', default=None, help='subject id column (required with --paired)')
    p.add_argument('--alpha', type=float, default=0.05)
    args = p.parse_args(argv)
    try:
        import pandas as pd
    except ImportError:
        raise SystemExit("缺少 pandas：pip install pandas")
    df = pd.read_csv(args.csv)
    for col in (args.value, args.group):
        if col not in df.columns:
            raise SystemExit(f"CSV 中没有列 {col!r}；可用列：{list(df.columns)}")
    if args.paired:
        if not args.id or args.id not in df.columns:
            raise SystemExit("--paired 需要 --id <受试者ID列>，用于按受试者对齐各条件")
        wide = df.pivot_table(index=args.id, columns=args.group, values=args.value, aggfunc='first')
        groups = [wide[c].to_numpy(dtype=float) for c in wide.columns]
        labels = [str(c) for c in wide.columns]
    else:
        labels, groups = [], []
        for name, sub in df.groupby(args.group, sort=True):
            labels.append(str(name))
            groups.append(sub[args.value].to_numpy(dtype=float))
    try:
        report = full_check(*groups, paired=args.paired, alpha=args.alpha)
    except ValueError as e:
        raise SystemExit(f"输入错误：{e}")
    report['group_labels'] = labels
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    main()
