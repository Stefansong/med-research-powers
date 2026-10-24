#!/usr/bin/env python3
"""
Assumption diagnostics for medical research: normality, homogeneity of variance, effect size.

The test itself is prespecified in the SAP; these results DESCRIBE the data (write them into
analysis-log.md next to Q-Q / residual plots) and never switch the test on their p-values.
Picking Student / Welch / Mann-Whitney from a Levene or Shapiro-Wilk result is a two-stage
procedure that distorts the type I error (Zimmerman 2004; Rochon 2012), so `recommended_test`
is the design default -- Welch's t-test for two independent groups, Welch's ANOVA +
Games-Howell for more -- and `rank_based_alternative` names the test to use only when the
SAP prespecified it (skewed, ordinal, bounded or very small samples). For three or more
repeated conditions the default is a linear mixed model or repeated-measures ANOVA with the
Greenhouse-Geisser correction applied whatever Mauchly's test says; Mauchly's test and the
Greenhouse-Geisser epsilon are reported as descriptions only (choosing the correction from
Mauchly's p-value is the same kind of two-stage procedure).

Library use (run from the user's project directory):
    # copy this file into the project once:  cp "$CLAUDE_PLUGIN_ROOT/skills/statistical-analysis/scripts/assumption_tests.py" .
    from assumption_tests import full_check, effect_size_cohens_d
    report = full_check(group_a, group_b, paired=False)   # json.dumps(report) works

Command line (long-format CSV, prints JSON):
    python3 assumption_tests.py data_clean.csv --value outcome --group arm [--paired --id patient_id]
Rows with a missing group (or, with --paired, subject ID) are excluded and counted in
'rows_excluded' and 'warnings'. Invalid arguments, unreadable files and bad data: one line on
stderr, exit status 2.

All results contain plain Python bool/float/int (no numpy scalars) and no NaN / inf, so they
can be written straight into analysis-log.md via json.dumps. Infinite values are rejected
(ValueError) as invalid input; NaN / None are treated as missing.
"""

import argparse
import json
import math
import sys

try:
    import numpy as np
    from scipy import stats
except ImportError:  # pragma: no cover - depends on the user's environment
    print("缺少 scipy / numpy：pip install scipy numpy", file=sys.stderr)
    raise SystemExit(2)


# ─── helpers ────────────────────────────────────────────────────────────────

def _to_array_keep_nan(data):
    """Coerce list/Series/array (may contain None or NaN = missing) to a float array.
    Infinite values are invalid input, not observations: raise instead of testing them."""
    arr = np.asarray(data, dtype=float).ravel()
    n_inf = int(np.isinf(arr).sum())
    if n_inf:
        raise ValueError(f"数据中有 {n_inf} 个无穷值（inf）：多半是除以 0 或对 0 取对数的结果；"
                         "请先在清洗代码里按 SAP 处理，再做前提诊断")
    return arr


def _to_array(data):
    """Coerce list/Series/array (may contain None or NaN) to a float array without NaN."""
    arr = _to_array_keep_nan(data)
    return arr[~np.isnan(arr)]


def _check_alpha(alpha):
    if alpha is None or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError(f"alpha 必须在 (0, 1) 之间，收到 {alpha}")


def _finite_or_none(x, digits=4):
    x = float(x)
    return round(x, digits) if math.isfinite(x) else None


# ─── single tests ───────────────────────────────────────────────────────────

def check_normality(data, alpha=0.05):
    """Test normality. Auto-selects Shapiro-Wilk (n<50) or D'Agostino-Pearson (n>=50).

    A description of the data (with a Q-Q plot), never a switch between tests: the result has
    no 'recommendation' -- the test to use is full_check()['recommended_test'] / the SAP.
    Constant data or n < 8: normality is not testable -> is_normal=None.
    """
    _check_alpha(alpha)
    data = _to_array(data)
    n = int(len(data))
    with np.errstate(over='ignore'):         # finite values near ±1e308: the range overflows to inf
        constant = n >= 2 and float(np.ptp(data)) == 0.0
    if constant:
        return {'method': 'constant_data', 'n': n, 'is_normal': None,
                'note': 'All values identical (zero variance) — normality test not applicable'}
    if n < 8:
        return {'method': 'too_few_samples', 'n': n, 'is_normal': None,
                'note': 'n < 8: normality not testable — use the method prespecified in the SAP'}
    # both tests are scale invariant: rescale so that values near ±1e308 do not overflow and values
    # below ~1e-38 do not vanish (the Shapiro-Wilk routine works in single precision)
    scaled = data / float(np.max(np.abs(data)))
    with np.errstate(all='ignore'):
        if n < 50:
            stat, p = stats.shapiro(scaled)
            method = 'Shapiro-Wilk'
        else:
            stat, p = stats.normaltest(scaled)
            method = "D'Agostino-Pearson"
    stat, p = float(stat), float(p)
    if not (math.isfinite(stat) and math.isfinite(p)):
        return {'method': method, 'statistic': None, 'p_value': None, 'n': n, 'is_normal': None,
                'note': f'{method} test undefined for these data — look at the Q-Q plot'}
    return {
        'method': method, 'statistic': round(stat, 4), 'p_value': round(p, 4),
        'n': n, 'is_normal': bool(p > alpha),
        'note': 'Description only (with a Q-Q plot); it does not choose the test',
    }


def check_homogeneity(*groups, alpha=0.05):
    """Levene test (median-centred) across independent groups -- a description, not a gate."""
    _check_alpha(alpha)
    clean = [_to_array(g) for g in groups]
    if len(clean) < 2:
        raise ValueError("方差齐性检验至少需要 2 组")
    if any(len(g) < 2 for g in clean):
        raise ValueError("每组至少需要 2 个非缺失观测才能做 Levene 检验")
    with np.errstate(over='ignore'):
        constant = all(float(np.ptp(g)) == 0.0 for g in clean)
    if constant:
        return {'method': 'Levene', 'statistic': None, 'p_value': None, 'is_homogeneous': None,
                'note': 'All groups are constant (zero variance) — Levene test not applicable'}
    with np.errstate(all='ignore'):          # a degenerate case is reported below, not printed as a warning
        stat, p = stats.levene(*clean)
    stat, p = float(stat), float(p)
    if not (math.isfinite(stat) and math.isfinite(p)):   # e.g. no spread of the deviations within every group
        return {'method': 'Levene', 'statistic': None, 'p_value': None, 'is_homogeneous': None,
                'note': 'Levene test undefined for these data'}
    return {
        'method': 'Levene', 'statistic': round(stat, 4), 'p_value': round(p, 4),
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
        return ('Linear mixed model, or repeated-measures ANOVA with the Greenhouse-Geisser '
                "correction (prespecified; applied whatever Mauchly's test says)")
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
        elif r['is_normal'] is None and r['method'] != 'too_few_samples':
            out.append(f"{lab}：{r['method']} 检验对这些数据无定义，只看 Q-Q 图")
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


def check_sphericity(*conditions):
    """Mauchly's test and the Greenhouse-Geisser epsilon for >= 3 repeated conditions (complete
    cases of equal-length arrays). A description only: the Greenhouse-Geisser correction (or a
    mixed model) is prespecified, not switched on Mauchly's p-value.

    S = covariance of orthonormal contrasts (k − 1 = p of them), n subjects, m = n − 1,
    W = det(S) / (tr(S) / p)^p, ρ = 1 − (2p² + p + 2) / (6pm), χ² = −m·ρ·ln W on
    f = p(p + 1)/2 − 1 df; p-value with the second-order term as in R's mauchly.test (and
    pingouin): P = P(χ²_f > χ²) + ω₂·[P(χ²_{f+4} > χ²) − P(χ²_f > χ²)],
    ω₂ = (p + 2)(p − 1)(p − 2)(2p³ + 6p² + 3k + 2) / (288·(m·p·ρ)²), capped at 1 (ω₂ = 0 for k = 3).
    ε_GG = tr(S)² / (p · tr(S²)), between 1/p and 1.
    """
    if len(conditions) < 3:
        raise ValueError("球形性只在 3 个及以上重复测量条件时有意义")
    arrays, n, _ = _complete_pairs(*conditions)
    X = np.column_stack(arrays)
    k = X.shape[1]
    p = k - 1
    df = int(p * (p + 1) // 2 - 1)
    out = {'method': ("Mauchly's test (chi-square approximation with the second-order term, as R "
                      "mauchly.test) + Greenhouse-Geisser epsilon"),
           'n': int(n), 'W': None, 'chi2': None, 'df': df, 'p_value': None,
           'greenhouse_geisser_epsilon': None,
           'note': ('Description only: apply the prespecified Greenhouse-Geisser correction '
                    '(or use a mixed model) whatever these values are')}
    if n <= p:
        out['note'] = f'n = {n} subjects is too few for {k} conditions — sphericity not estimable'
        return out
    contrasts = np.linalg.qr(np.column_stack([np.ones(k), np.eye(k)[:, :p]]))[0][:, 1:]
    scale = float(np.max(np.abs(X)))             # W, χ² and ε do not depend on the scale: rescaling
    cov = np.cov(X / scale if scale > 0 else X, rowvar=False, ddof=1)   # keeps 1e±300 data finite
    s = contrasts.T @ cov @ contrasts
    eig = np.linalg.eigvalsh(s)                  # ascending; rounding noise counts as zero below
    tol = 1e-10
    if not eig[-1] > tol * float(np.trace(cov)):
        out['note'] = ('The differences between conditions are the same for every subject (no subject × '
                       'condition variation; the condition means may still differ, e.g. values x, x + 1, '
                       'x + 2) — sphericity not estimable')
        return out
    tr = float(np.trace(s))
    out['greenhouse_geisser_epsilon'] = _finite_or_none(tr ** 2 / (p * float(np.trace(s @ s))))
    if not eig[0] > tol * eig[-1]:
        out['note'] = ('Contrast covariance is singular: some difference between conditions (or a '
                       'combination of differences) is the same for every subject, e.g. condition 3 = '
                       "condition 2 + a constant — Mauchly's test not estimable; epsilon is still reported")
        return out
    m = n - 1
    log_w = float(np.sum(np.log(eig))) - p * math.log(tr / p)
    rho = 1 - (2 * p ** 2 + p + 2) / (6 * p * m)
    chi2 = -m * rho * log_w
    w2 = ((p + 2) * (p - 1) * (p - 2) * (2 * p ** 3 + 6 * p ** 2 + 3 * k + 2)
          / (288 * (m * p * rho) ** 2))
    pr1, pr2 = float(stats.chi2.sf(chi2, df)), float(stats.chi2.sf(chi2, df + 4))
    out.update(W=_finite_or_none(math.exp(log_w)), chi2=_finite_or_none(chi2),
               p_value=_finite_or_none(min(1.0, pr1 + w2 * (pr2 - pr1))))
    return out


def full_check(*groups, paired=False, alpha=0.05):
    """Run all assumption tests and recommend a method. Returns a JSON-serialisable dict.

    Independent groups : normality per group (+ Levene when >= 2 groups).
    Paired, 2 groups   : complete pairs only, then normality of the differences.
    Paired, > 2 groups : complete cases only, normality per condition; Levene is skipped;
                         Mauchly's test and the Greenhouse-Geisser epsilon are reported as a
                         description (the correction is prespecified, not chosen from them).
    Any group with n < 8 or constant -> all_normal=None and a warning (normality untestable).
    recommended_test is the design default whatever the diagnostics say (see module docstring).
    Missing values (None / NaN) are dropped and counted in the warnings; inf raises ValueError.
    """
    _check_alpha(alpha)
    warnings = []
    if len(groups) == 0:
        raise ValueError("至少传入 1 组数据")
    if paired and len(groups) < 2:
        raise ValueError(f"配对 / 重复测量设计至少需要 2 个条件，收到 {len(groups)} 个")

    if paired and len(groups) == 2:
        (a, b), n_pairs, n_dropped = _complete_pairs(*groups)
        if n_dropped:
            warnings.append(f"已剔除 {n_dropped} 对含缺失值的配对，保留 {n_pairs} 对完整配对")
        with np.errstate(over='ignore', invalid='ignore'):
            differences = a - b
        if not np.isfinite(differences).all():
            raise ValueError("配对差值超出浮点数范围（取值接近 ±1e308）：请检查数据的单位和数量级")
        diff_normality = check_normality(differences, alpha)
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
            'homogeneity_note': ('Levene does not apply to repeated measures. Sphericity: the '
                                 'Greenhouse-Geisser correction (or a mixed model) is the prespecified '
                                 "default; Mauchly's test and the epsilon under 'sphericity' are "
                                 'descriptions only, not a gate'),
            'sphericity': check_sphericity(*arrays),
            'all_normal': all_normal,
            'homogeneous': None,
            'recommended_test': choose_test(len(groups), paired=True),
            'rank_based_alternative': rank_alternative(len(groups), paired=True),
            'how_to_use': HOW_TO_USE,
            'alpha': alpha,
            'warnings': warnings,
        }

    # independent groups
    labels = [f"组 {i + 1}" for i in range(len(groups))]
    for lab, g in zip(labels, groups):
        n_missing = int(np.isnan(_to_array_keep_nan(g)).sum())
        if n_missing:
            warnings.append(f"{lab}：剔除 {n_missing} 个缺失值")
    normality = [check_normality(g, alpha) for g in groups]
    warnings += _flags(normality, labels)
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

def _fail(msg):
    """CLI error: one line on stderr, exit status 2 (never a traceback)."""
    print("[前提诊断] " + str(msg).replace("\r", " ").replace("\n", " "), file=sys.stderr)
    raise SystemExit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):            # one line on stderr, exit 2 (argparse prints a usage block)
        _fail(f"参数错误：{message}（用 --help 查看用法）")


def _read_csv(pd, path):
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        _fail(f"找不到文件 {path}")
    except IsADirectoryError:
        _fail(f"{path} 是一个目录，不是 CSV 文件")
    except PermissionError:
        _fail(f"没有权限读取 {path}")
    except UnicodeDecodeError:
        _fail(f"{path} 不是 UTF-8 编码：请另存为 UTF-8 的 CSV 再运行")
    except pd.errors.EmptyDataError:
        _fail(f"{path} 是空文件（没有列名）")
    except (pd.errors.ParserError, ValueError, OSError) as e:
        _fail(f"无法读取 {path}（{type(e).__name__}: {str(e)[:200]}）")


def main(argv=None):
    p = _Parser(
        prog='assumption_tests.py',
        description='Assumption checks + test recommendation from a long-format CSV (prints JSON).')
    p.add_argument('csv', help='long-format CSV: one row per observation')
    p.add_argument('--value', required=True, help='numeric outcome column')
    p.add_argument('--group', required=True, help='grouping / condition column')
    p.add_argument('--paired', action='store_true', help='paired / repeated-measures design')
    p.add_argument('--id', default=None, help='subject id column (required with --paired)')
    p.add_argument('--alpha', type=float, default=0.05)
    args = p.parse_args(argv)
    try:
        _check_alpha(args.alpha)
    except ValueError as e:
        _fail(f"参数错误：--{e}")
    try:
        import pandas as pd
    except ImportError:
        _fail("缺少 pandas：pip install pandas")
    df = _read_csv(pd, args.csv)
    if args.paired and not args.id:
        _fail("--paired 需要 --id <受试者ID列>，用于按受试者对齐各条件")
    for col in (args.value, args.group) + ((args.id,) if args.paired else ()):
        if col not in df.columns:
            _fail(f"CSV 中没有列 {col!r}；可用列：{list(df.columns)}")
    numeric = pd.to_numeric(df[args.value], errors='coerce')
    bad = df[args.value][numeric.isna() & df[args.value].notna()]
    if len(bad):
        _fail(f"列 {args.value!r} 有 {len(bad)} 个不是数字的取值（如 {bad.astype(str).unique()[:3].tolist()}）；"
              "请先在清洗代码里按 SAP 处理（伪装缺失、截断值、带单位的数字）")
    n_inf = int(np.isinf(numeric.to_numpy(dtype=float)).sum())
    if n_inf:
        _fail(f"列 {args.value!r} 有 {n_inf} 个无穷值（inf）；请先在清洗代码里按 SAP 处理")
    df[args.value] = numeric
    excluded, row_warnings = {}, []
    keys = [('missing_group', args.group, '分组列')] + ([('missing_id', args.id, '受试者ID列')] if args.paired else [])
    for key, col, what in keys:
        miss = df[col].isna()
        excluded[key] = int(miss.sum())
        if excluded[key]:
            row_warnings.append(f"已剔除 {excluded[key]} 行：{what} {col!r} 缺失")
            df = df[~miss]
    if args.paired:
        dup = int(df.duplicated([args.id, args.group]).sum())
        if dup:
            _fail(f"有 {dup} 行是同一受试者在同一条件下的重复记录；配对分析要求每人每条件一行，"
                  "请先按 SAP 规定汇总（如取均值）或去重")
        levels = sorted(df[args.group].unique().tolist(), key=str)
        if len(levels) < 2:
            _fail(f"--paired 需要至少 2 个条件，但列 {args.group!r} 只有 {len(levels)} 个取值（{levels}）；"
                  "请检查分组列，或去掉 --paired")
        wide = df.pivot(index=args.id, columns=args.group, values=args.value)
        groups = [wide[c].to_numpy(dtype=float) for c in wide.columns]
        labels = [str(c) for c in wide.columns]
    else:
        labels, groups = [], []
        for name, sub in df.groupby(args.group, sort=True):
            labels.append(str(name))
            groups.append(sub[args.value].to_numpy(dtype=float))
        if not groups:
            _fail(f"没有可分析的行：列 {args.group!r} 全部缺失或文件没有数据行")
    try:
        report = full_check(*groups, paired=args.paired, alpha=args.alpha)
    except ValueError as e:
        _fail(f"输入错误：{e}")
    except Exception as e:                   # data the checks did not foresee: a message, not a traceback
        _fail(f"检验时出错（{type(e).__name__}: {str(e)[:200]}）；请把这一行报告给插件维护者")
    report['group_labels'] = labels
    report['rows_excluded'] = excluded
    report['warnings'] = row_warnings + report['warnings']
    try:
        out = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    except ValueError as e:
        _fail(f"结果含非有限数值，无法写成 JSON（{e}）；请把这一行报告给插件维护者")
    print(out)
    return report


if __name__ == '__main__':
    main()
