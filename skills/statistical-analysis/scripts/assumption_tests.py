#!/usr/bin/env python3
"""
Assumption diagnostics for medical research: normality, homogeneity of variance, effect size.

The test itself is prespecified in the SAP; these results DESCRIBE the data (write them into
analysis-log.md next to Q-Q / residual plots) and never switch the test on their p-values.
Picking Student / Welch / Mann-Whitney from a Levene or Shapiro-Wilk result is a two-stage
procedure that distorts the type I error (Zimmerman 2004; Rochon 2012), so `recommended_test`
is the design default -- Welch's t-test for two independent groups, Welch's ANOVA +
Games-Howell for more -- and `rank_based_alternative` names the test to use only when the
SAP prespecified it (skewed, ordinal, bounded or very small samples).

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
    """Levene test (median-centred) across independent groups -- a description, not a gate."""
    clean = [_to_array(g) for g in groups]
    if len(clean) < 2:
        raise ValueError("方差齐性检验至少需要 2 组")
    if any(len(g) < 2 for g in clean):
        raise ValueError("每组至少需要 2 个非缺失观测才能做 Levene 检验")
    if all(float(np.ptp(g)) == 0.0 for g in clean):
        return {'method': 'Levene', 'statistic': None, 'p_value': None, 'is_homogeneous': None,
                'note': 'All groups are constant (zero variance) — Levene test not applicable'}
    stat, p = stats.levene(*clean)
    if not np.isfinite(p):
        return {'method': 'Levene', 'statistic': None, 'p_value': None, 'is_homogeneous': None,
                'note': 'Levene test undefined for these data'}
    p = float(p)
    return {
        'method': 'Levene', 'statistic': round(float(stat), 4), 'p_value': round(p, 4),
        'is_homogeneous': bool(p > alpha),
        'note': 'Description only: the default Welch test does not assume equal variances',
    }


def choose_test(n_groups, paired=False, **_ignored):
    """The design default to prespecify in the SAP. Assumption-test results are deliberately
    ignored (extra keyword arguments such as all_normal / homogeneous are accepted and unused)."""
    if n_groups < 2:
        return 'One-sample t-test'
    if n_groups == 2:
        return 'Paired t-test' if paired else "Welch's t-test"
    if paired:
        return ('Repeated-measures ANOVA or linear mixed model '
                '(check sphericity: Mauchly; Greenhouse-Geisser if violated)')
    return "Welch's ANOVA + Games-Howell"


def rank_alternative(n_groups, paired=False):
    """The rank-based test to use ONLY if the SAP prespecified it for this variable."""
    if n_groups < 2:
        return 'Wilcoxon signed-rank (one-sample)'
    if n_groups == 2:
        return 'Wilcoxon signed-rank' if paired else 'Mann-Whitney U'
    return 'Friedman + Nemenyi' if paired else 'Kruskal-Wallis + Dunn'


HOW_TO_USE = ('方法按 SAP 预先规定执行；这里的正态性/方差齐性检验只描述数据（与 Q-Q 图、残差图一起记入 '
              'analysis-log.md），不按它们的 p 值临时切换检验。SAP 预先规定了偏态/小样本时用秩检验或对数变换的，'
              '按预定备选执行；没有预定而认为方法不合适的，按"偏离 SAP"写明理由。')


def _flags(normality, labels):
    out = []
    for lab, r in zip(labels, normality):
        if r['method'] == 'constant_data':
            out.append(f"{lab}：所有取值相同（方差为 0）")
        elif r['is_normal'] is None:
            out.append(f"{lab}：n = {r['n']} < 8，正态性无法检验；样本很小时结论对分布假设敏感，"
                       "按 SAP 预定的方法（或预定的秩检验备选）执行")
        elif not r['is_normal']:
            out.append(f"{lab}：{r['method']} p = {r['p_value']}，分布可能偏离正态——看 Q-Q 图；"
                       "样本较大时 t 检验对此稳健")
    return out


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
    Any group with n < 8 or constant -> all_normal=None and a warning (normality untestable).
    recommended_test is the design default whatever the diagnostics say (see module docstring).
    """
    warnings = []
    if len(groups) == 0:
        raise ValueError("至少传入 1 组数据")

    if paired and len(groups) == 2:
        (a, b), n_pairs, n_dropped = _complete_pairs(*groups)
        if n_dropped:
            warnings.append(f"已剔除 {n_dropped} 对含缺失值的配对，保留 {n_pairs} 对完整配对")
        diff_normality = check_normality(a - b, alpha)
        warnings += _flags([diff_normality], ['配对差值'])
        all_normal = None if diff_normality['is_normal'] is None else bool(diff_normality['is_normal'])
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
            'recommended_test': choose_test(2, paired=True),
            'rank_based_alternative': rank_alternative(2, paired=True),
            'how_to_use': HOW_TO_USE,
            'alpha': alpha,
            'warnings': warnings,
        }

    if paired and len(groups) > 2:
        arrays, n_complete, n_dropped = _complete_pairs(*groups)
        if n_dropped:
            warnings.append(f"已剔除 {n_dropped} 个含缺失值的受试者，保留 {n_complete} 个完整病例")
        normality = [check_normality(a, alpha) for a in arrays]
        warnings += _flags(normality, [f"条件 {i + 1}" for i in range(len(arrays))])
        all_normal = (None if any(r['is_normal'] is None for r in normality)
                      else all(bool(r['is_normal']) for r in normality))
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
            'recommended_test': choose_test(len(groups), paired=True),
            'rank_based_alternative': rank_alternative(len(groups), paired=True),
            'how_to_use': HOW_TO_USE,
            'alpha': alpha,
            'warnings': warnings,
        }

    # independent groups
    normality = [check_normality(g, alpha) for g in groups]
    warnings += _flags(normality, [f"组 {i + 1}" for i in range(len(groups))])
    all_normal = (None if any(r['is_normal'] is None for r in normality)
                  else all(bool(r['is_normal']) for r in normality))
    homogeneity = None
    if len(groups) > 1:
        try:
            homogeneity = check_homogeneity(*groups, alpha=alpha)
        except ValueError as e:
            warnings.append(f"Levene 检验未执行：{e}")
    return {
        'design': 'independent_groups',
        'normality_tests': normality,
        'homogeneity_test': homogeneity,
        'all_normal': all_normal,
        'homogeneous': homogeneity['is_homogeneous'] if homogeneity else None,
        'recommended_test': choose_test(len(groups), paired=False),
        'rank_based_alternative': rank_alternative(len(groups), paired=False),
        'how_to_use': HOW_TO_USE,
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
    numeric = pd.to_numeric(df[args.value], errors='coerce')
    bad = df[args.value][numeric.isna() & df[args.value].notna()]
    if len(bad):
        raise SystemExit(f"列 {args.value!r} 有 {len(bad)} 个不是数字的取值（如 {bad.astype(str).unique()[:3].tolist()}）；"
                         "请先在清洗代码里按 SAP 处理（伪装缺失、截断值、带单位的数字）")
    df[args.value] = numeric
    if args.paired:
        if not args.id or args.id not in df.columns:
            raise SystemExit("--paired 需要 --id <受试者ID列>，用于按受试者对齐各条件")
        dup = int(df.duplicated([args.id, args.group]).sum())
        if dup:
            raise SystemExit(f"有 {dup} 行是同一受试者在同一条件下的重复记录；配对分析要求每人每条件一行，"
                             "请先按 SAP 规定汇总（如取均值）或去重")
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
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return report


if __name__ == '__main__':
    main()
