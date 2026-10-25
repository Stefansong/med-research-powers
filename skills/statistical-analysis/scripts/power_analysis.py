#!/usr/bin/env python3
"""
Sample size calculation for common medical research designs.

Library use (run from the user's project directory):
    # copy this file into the project once (it reads nothing else from the plugin):
    #   cp "$CLAUDE_PLUGIN_ROOT/skills/statistical-analysis/scripts/power_analysis.py" .
    from power_analysis import two_groups, proportion, survival, diagnostic, correlation

Command line (prints JSON):
    python3 power_analysis.py two-groups --effect-size 0.5 --dropout 0.15
    python3 power_analysis.py two-groups --effect-size 0 --hypothesis non-inferiority --margin 0.3
    python3 power_analysis.py proportion --p1 0.30 --p2 0.50 [--continuity-correction]
    python3 power_analysis.py proportion --p1 0.85 --p2 0.85 --hypothesis non-inferiority --margin 0.10
    python3 power_analysis.py survival --hr 0.7 --event-rate 0.5
    python3 power_analysis.py diagnostic --sensitivity 0.9 --specificity 0.85 --prevalence 0.3
    python3 power_analysis.py correlation --r 0.3

What it covers
    superiority      : two means, two proportions, log-rank (survival), correlation;
                       two-sided (default) or one-sided (sides=1)
    non-inferiority  : two means, two proportions (one-sided test against the margin)
    equivalence      : two means, two proportions (two one-sided tests, TOST)
    precision        : diagnostic accuracy (CI half-width for sensitivity / specificity)
Not covered (use a dedicated tool and cite it): cluster-randomised designs (design effect),
crossover and repeated-measures designs, non-inferiority / equivalence for survival or
correlation, prediction-model development or validation (pmsampsize / pmvalsampsize),
multi-reader multi-case reader studies (MRMC), multi-arm and group-sequential designs.

Groups: group 1 = control / reference, group 2 = treatment / new; ratio = n2 / n1.

Formulas
    two_groups  : t-test power (statsmodels TTestIndPower), effect = Cohen's d; non-inferiority
                  = one-sided t-test of the difference shifted by the margin; equivalence = TOST
                  (Schuirmann 1987) with exact power, integrated over the sample SD (Julious 2004)
    proportion  : two-sample z / chi-square test of proportions, pooled variance under H0
                  (Fleiss, Levin & Paik 2003; the same formula as R's power.prop.test);
                  optional continuity correction (Fleiss, Tytun & Ury 1980). Non-inferiority and
                  equivalence: Farrington & Manning (1990) score test, variance under H0 from the
                  restricted maximum-likelihood estimates (Miettinen & Nurminen 1985)
    survival    : Schoenfeld (1983) number of events for the log-rank test
                  D = (z_{1-α/2} + z_{power})² / (ln(HR)² · p1 · p2),  p1 = 1/(1+r), p2 = r/(1+r)
    diagnostic  : Buderer (1996) precision-based n for sensitivity and specificity (Wald CI);
                  optional Wilson score CI basis for proportions near 0 or 1
    correlation : Fisher z transform,  n = ((z_{1-α/2} + z_{power}) / z_r)² + 3

α: two-sided for a superiority test (default 0.05). For a one-sided test -- sides=1,
non-inferiority, and each of the two one-sided tests of an equivalence design -- α is the
one-sided level and defaults to 0.025, half the two-sided level, as ICH E9 recommends; this
matches a two-sided 95% CI. Pass alpha explicitly for anything else. The one-sided α default
and the dropout default (0.1) are stated in the result's 'warnings' whenever they were used.

These calculations are for the *a priori* sample size written into study-protocol.md.
Do not use them for post hoc ("observed") power after the data are in.
"""

import argparse
import json
import math
import sys
import warnings

try:
    from scipy import integrate, optimize
    from scipy import stats as st
except ImportError:  # pragma: no cover - depends on the user's environment
    print("缺少 scipy：pip install scipy", file=sys.stderr)
    raise SystemExit(2)

HYPOTHESES = ('superiority', 'non-inferiority', 'equivalence')
DEFAULT_DROPOUT = 0.1
N_MAX = 1e9            # beyond this the effect is effectively zero
MIN_PER_GROUP_T = 2    # two_groups: at least 2 per group, so each group has a within-group SD
D_MAX = 1e3            # two_groups: |d| or margin in SD units; far beyond any real separation, and
                       # scipy's noncentral t slows down without bound (d = 1e7: > 8 s per call)
TOST_TAIL = 1e-16      # _tost_power_t: χ² tail mass left out of the integral, on each side


# ─── helpers ────────────────────────────────────────────────────────────────

def _require_statsmodels():
    try:
        from statsmodels.stats import power as smp
    except ImportError:
        print("缺少 statsmodels：pip install statsmodels", file=sys.stderr)
        raise SystemExit(2)
    return smp


def _finite(name, x):
    if x is None or not math.isfinite(x):
        raise ValueError(f"{name} 必须是有限数值，收到 {x}")


def _check_common(alpha, power, ratio=1.0, dropout=0.0):
    for name, x in (('alpha', alpha), ('power', power), ('ratio', ratio), ('dropout', dropout)):
        _finite(name, x)
    if not 0 < alpha < 1:
        raise ValueError(f"alpha 必须在 (0, 1) 之间，收到 {alpha}")
    if 1 - alpha / 2 == 1:                   # the critical value would be infinite
        raise ValueError(f"alpha（{alpha}）太小：浮点数下 1 − α/2 等于 1，临界值为无穷大，无法计算样本量")
    if not 0 < power < 1:
        raise ValueError(f"power 必须在 (0, 1) 之间，收到 {power}")
    if power <= alpha:
        raise ValueError(f"power（{power}）必须大于 alpha（{alpha}）：效能不超过 α 时任何样本量都满足，"
                         "算出的 n 没有意义；power 通常取 0.8 或 0.9")
    if ratio <= 0:
        raise ValueError(f"ratio（n2/n1）必须 > 0，收到 {ratio}")
    if not 0 <= dropout < 1:
        raise ValueError(f"dropout（脱落率）必须在 [0, 1) 之间，收到 {dropout}；"
                         "0.1 表示 10% 脱落")


def _design(hypothesis, sides, alpha, dropout, margin, warn, with_dropout=True):
    """Validate the hypothesis / sides / margin choice and fill in the defaults, saying so in warn."""
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"hypothesis 必须是 {' / '.join(HYPOTHESES)} 之一，收到 {hypothesis!r}")
    if hypothesis == 'superiority':
        if margin is not None:
            raise ValueError("margin 只用于非劣效 / 等效设计（hypothesis='non-inferiority' 或 'equivalence'）")
        sides = 2 if sides is None else sides
        if sides not in (1, 2):
            raise ValueError(f"sides 必须是 1 或 2，收到 {sides}")
    else:
        if sides is not None:
            raise ValueError("sides 只用于优效性检验：非劣效检验本身是单侧检验，等效检验是两个单侧检验（TOST），"
                             "alpha 即单侧水平")
        _finite('margin', margin)
        if margin <= 0:
            raise ValueError(f"margin（界值）必须 > 0，收到 {margin}；方向用 higher_is_better 指定")
        sides = 1
    if alpha is None:
        alpha = 0.05 if sides == 2 else 0.025
        if sides == 1:
            warn.append("alpha 未指定，用默认单侧 0.025（ICH E9：单侧检验取双侧水平的一半，与双侧 95% CI 一致）；"
                        "protocol 用别的水平时请显式给出")
    if with_dropout and dropout is None:
        dropout = DEFAULT_DROPOUT
        warn.append(f"dropout 未指定，按默认 {DEFAULT_DROPOUT}（10% 脱落）放大样本量；请换成 protocol 里的预期脱落率"
                    "（0 表示不考虑脱落）")
    return sides, alpha, dropout


def _z(alpha, power, sides=2):
    return float(st.norm.ppf(1 - alpha / sides)), float(st.norm.ppf(power))


TOO_MANY = "所需样本量超过 10 亿{what}：效应几乎为 0，或 ratio / event_rate / dropout / precision / prevalence 取值过于极端；请核对输入"


def _check_n(*ns, what=""):
    """Refuse a sample size (or event count) that is not finite or exceeds N_MAX, instead of
    printing an absurd number or failing with an OverflowError when it is rounded."""
    if not all(math.isfinite(n) and n <= N_MAX for n in ns):
        raise ValueError(TOO_MANY.format(what=what))


def _inflate(n, dropout):
    """Inflate n for expected dropout (n / (1 - dropout)), rounded up (21 / 0.7 is 30, not 31)."""
    adjusted = n / (1 - dropout)
    _check_n(adjusted, what="（按脱落率放大后）")
    return int(math.ceil(adjusted - 1e-9))


def _solve_n(power_at, target, n_min, too_small, too_large=None):
    """Smallest (continuous) n1 >= n_min with power_at(n1) = target; power_at increases with n1.
    If power_at(n_min) already reaches the target, return n_min (or raise too_large if given).
    Refuses (too_small) only when the power at N_MAX itself is below the target."""
    def checked(n):
        p = power_at(n)
        if math.isnan(p):
            raise ValueError("检验效能无法计算：effect_size / margin 取值过于极端；请核对它们是标准化效应量（以标准差为单位）")
        return p

    p_min = checked(n_min)
    if p_min >= target:
        if too_large is not None:
            raise ValueError(too_large.format(n=n_min, p=p_min))
        return float(n_min)
    lo, hi = n_min, max(2 * n_min, 16.0)
    while checked(hi) < target:
        if hi >= N_MAX:                       # the power at N_MAX itself was checked: refuse only then
            raise ValueError(too_small)
        lo, hi = hi, min(hi * 4, N_MAX)
    return float(optimize.brentq(lambda n: checked(n) - target, lo, hi, xtol=1e-10))


def _per_group(n1, ratio, dropout, eps=0.0, min_n=1):
    """Per-group n before and after dropout inflation, as returned by every two-group design."""
    _check_n(n1, n1 * ratio)
    n1_ceil = max(min_n, int(math.ceil(n1 - eps)))
    n2_ceil = max(min_n, int(math.ceil(n1 * ratio - eps)))
    n1_adj, n2_adj = _inflate(n1_ceil, dropout), _inflate(n2_ceil, dropout)
    return {
        'n1': n1_ceil,
        'n2': n2_ceil,
        'n_per_group': n1_ceil,
        'total': n1_ceil + n2_ceil,
        'n1_adjusted': n1_adj,
        'n2_adjusted': n2_adj,
        'total_adjusted': n1_adj + n2_adj,
    }


def _t_power(ttest, effect, n1, n2, alpha, alternative):
    """statsmodels TTestIndPower power for n1, n2. statsmodels returns NaN once the power is
    essentially 1 (its far noncentral-t tail underflows, e.g. d = 3 with 30 per group); the
    near tail alone is then the power."""
    p = float(ttest.power(effect_size=effect, nobs1=n1, alpha=alpha, ratio=n2 / n1, alternative=alternative))
    if math.isnan(p):
        df = n1 + n2 - 2
        crit = st.t.ppf(1 - alpha / (2 if alternative == 'two-sided' else 1), df)
        p = float(st.nct.sf(crit, df, effect / math.sqrt(1 / n1 + 1 / n2)))
    return p


def _tost_power_t(n1, n2, diff, margin, alpha):
    """Exact power of the two one-sided t-tests (equivalence, two means, SD units).

    Equivalence is concluded when -margin + t·S·k < D < margin - t·S·k; D ~ N(diff, k²) and
    S² ~ χ²_df / df independently, so the power is a one-dimensional integral over U = df·S².
    The integral covers only the central part of the χ²_df distribution: outside it the integrand
    holds less than 1e-16 of mass on each side. Over a much wider range (a margin of hundreds of
    SDs, a t quantile of 6.7e-17 instead of 0 at α = 0.5, tens of thousands per group) quad's
    nodes miss the peak of the integrand and it returns 0 instead of the power.
    """
    df = n1 + n2 - 2
    k = math.sqrt(1 / n1 + 1 / n2)
    t_crit = float(st.t.ppf(1 - alpha, df))
    u_lo = float(st.chi2.ppf(TOST_TAIL, df))
    u_hi = float(st.chi2.isf(TOST_TAIL, df))
    if t_crit > 0:                                  # alpha >= 0.5 (t <= 0): no upper limit on S
        s_max = margin / (t_crit * k)               # beyond this S is too large to conclude equivalence
        u_hi = min(u_hi, df * s_max * s_max)
    if u_hi <= u_lo:                                # the power is below 1e-16
        return 0.0

    def integrand(u):
        s = math.sqrt(u / df)
        inside = (st.norm.cdf((margin - diff) / k - t_crit * s)
                  - st.norm.cdf((-margin - diff) / k + t_crit * s))
        return max(inside, 0.0) * st.chi2.pdf(u, df)

    return float(integrate.quad(integrand, u_lo, u_hi, limit=200)[0])


def _rmle_diff(p1, p2, ratio, theta):
    """Restricted MLE (q1, q2) with q2 - q1 = theta given proportions p1, p2 and n2 = ratio·n1
    (Miettinen & Nurminen 1985; Farrington & Manning 1990). The log-likelihood is concave in q1,
    so a bounded one-dimensional maximisation finds it."""
    lo, hi = max(0.0, -theta), min(1.0, 1.0 - theta)

    def neg_loglik(q1):
        q2 = q1 + theta
        return -(p1 * math.log(q1) + (1 - p1) * math.log(1 - q1)
                 + ratio * (p2 * math.log(q2) + (1 - p2) * math.log(1 - q2)))

    span = hi - lo
    res = optimize.minimize_scalar(neg_loglik, bounds=(lo + 1e-12 * span, hi - 1e-12 * span),
                                   method='bounded', options={'xatol': 1e-13})
    return float(res.x), float(res.x) + theta


# ─── designs ────────────────────────────────────────────────────────────────

def two_groups(effect_size, alpha=None, power=0.80, ratio=1.0, dropout=None,
               hypothesis='superiority', margin=None, sides=None, higher_is_better=True):
    """Two-group continuous outcome (independent t-test). Effects and margins in SD units.

    ratio = n2 / n1 (treatment : control). Returns per-group n before and after
    dropout inflation. Key 'n_per_group' is n1 (kept for backward compatibility).

    superiority     : effect_size = Cohen's d to detect (its sign is ignored); sides 2 or 1.
    non-inferiority : effect_size = expected true difference treatment − control (often 0),
                      margin = non-inferiority margin (> 0). H0: Δ ≤ −margin (higher_is_better)
                      or Δ ≥ margin (higher_is_better=False); one-sided t-test at alpha.
    equivalence     : H0: |Δ| ≥ margin; two one-sided t-tests at alpha each (TOST).
    d = 0.5, 1:1, two-sided α 0.05, power 0.8: 64 per group.
    Each group gets at least 2. When a group is at that minimum (a very large effect, e.g. d = 3
    with ratio 0.25 gives n1 = 7, n2 = 2) the result says so in 'warnings', with the power reached.
    """
    warn = []
    sides, alpha, dropout = _design(hypothesis, sides, alpha, dropout, margin, warn)
    _check_common(alpha, power, ratio, dropout)
    _finite('effect_size', effect_size)
    for name, x in (('effect_size', effect_size), ('margin', margin)):
        if x is not None and abs(x) > D_MAX:
            raise ValueError(f"{name} = {x} 个标准差，不可能是标准化效应量（|{name}| ≤ {D_MAX:g}）："
                             "请核对是否把均值差（原始单位）当成了 Cohen's d")
    smp = _require_statsmodels()
    ttest = smp.TTestIndPower()
    # smallest n1 searched: n1 >= 1 and n1·ratio >= 1 (so the ratio, not the floor of 2, sets both
    # groups) and df >= 1 (below that the noncentral-t power is numerically unreliable)
    n_min = max(1.0, 1.0 / ratio, 3.0 / (1.0 + ratio))
    _check_n(n_min * (1 + ratio), what="（分配比例 ratio 过于极端）")
    too_small = ("所需样本量超过 10 亿：效应量（或预期差值与界值之差）几乎为 0；请核对 effect_size"
                 + ("" if hypothesis == 'superiority' else " 与 margin"))
    if hypothesis == 'superiority':
        if effect_size == 0:
            raise ValueError("effect_size（Cohen's d）不能为 0：效应为 0 时所需样本量无穷大")
        d = abs(effect_size)
        alternative = 'two-sided' if sides == 2 else 'larger'
        method = f"{'two' if sides == 2 else 'one'}-sided t-test (statsmodels TTestIndPower)"

        def power_of(n1, n2):
            return _t_power(ttest, d, n1, n2, alpha, alternative)
    elif hypothesis == 'non-inferiority':
        shift = (effect_size if higher_is_better else -effect_size) + margin
        if shift <= 0:
            raise ValueError(f"预期差值 {effect_size} 已经比非劣效界值 {margin} 更差（按 higher_is_better="
                             f"{higher_is_better}），非劣效不可能成立；请核对方向和数值")
        method = "one-sided t-test of the difference shifted by the margin (statsmodels TTestIndPower)"

        def power_of(n1, n2):
            return _t_power(ttest, shift, n1, n2, alpha, 'larger')
    else:
        if abs(effect_size) >= margin:
            raise ValueError(f"等效设计要求 |预期差值| < margin，收到 effect_size={effect_size}，margin={margin}")
        method = "two one-sided t-tests (TOST), exact power"

        def power_of(n1, n2):
            return _tost_power_t(n1, n2, effect_size, margin, alpha)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        n1 = _solve_n(lambda n: power_of(n, n * ratio), power, n_min, too_small)
        res = _per_group(n1, ratio, dropout, min_n=MIN_PER_GROUP_T)
        if min(res['n1'], res['n2']) <= MIN_PER_GROUP_T:
            reached = power_of(res['n1'], res['n2'])
            lead = "效应量很大" if hypothesis == 'superiority' else "界值（margin）相对标准差很大"
            warn.append(f"{lead}：n1 = {res['n1']}、n2 = {res['n2']} 例（每组至少 {MIN_PER_GROUP_T} 例）时检验效能"
                        f"已达 {reached:.3f}（目标 {power}）。请核对 effect_size 是标准化效应量（Cohen's d = 均值差 / 标准差），"
                        "而不是均值差本身" + ("" if hypothesis == 'superiority' else "，margin 同样以标准差为单位")
                        + "；例数这么少时结论依赖正态假设，一例脱落或缺失就会改变结果")
    return {
        'design': 'two_groups_continuous',
        'hypothesis': hypothesis,
        'method': method,
        **res,
        'n_treatment': res['n2'],
        'n_control_adjusted': res['n1_adjusted'],
        'n_treatment_adjusted': res['n2_adjusted'],
        'params': {'effect_size': effect_size, 'alpha': alpha, 'sides': sides, 'power': power,
                   'ratio': ratio, 'dropout': dropout, 'margin': margin,
                   'higher_is_better': higher_is_better},
        'warnings': warn,
    }


def proportion(p1, p2, alpha=None, power=0.80, ratio=1.0, dropout=None, continuity_correction=False,
               hypothesis='superiority', margin=None, sides=None, higher_is_better=True):
    """Two-group comparison of proportions. p1 = group 1 (control), p2 = group 2 (treatment), r = n2/n1.

    Superiority (z / chi-square test):
    n1 = [z_{1-α/2}·√(p̄q̄(1 + 1/r)) + z_{power}·√(p1q1 + p2q2/r)]² / (p1 − p2)²,
    p̄ = (p1 + r·p2)/(1 + r) -- the pooled-variance normal approximation
    (Fleiss, Levin & Paik 2003; R power.prop.test gives the same n). With
    continuity_correction=True: n1' = n1/4 · [1 + √(1 + 2(r + 1)/(r·n1·|p1 − p2|))]²
    (Fleiss, Tytun & Ury 1980), the usual choice when the analysis is a corrected
    chi-square or Fisher's exact test. p1 = 0.30 vs p2 = 0.50: 93 per group (103 corrected).

    Non-inferiority (risk difference Δ = p2 − p1, margin δ > 0; H0: Δ ≤ −δ, or Δ ≥ δ with
    higher_is_better=False) and equivalence (H0: |Δ| ≥ δ, two one-sided tests): Farrington &
    Manning (1990) score test, n1 = [z_{1-α}·√(q̃-variance under H0) + z_{power}·√(p1q1 + p2q2/r)]²
    / (distance from Δ to the margin)², with the H0 variance from the restricted MLEs; for
    equivalence the power of the two one-sided tests is P_lower + P_upper − 1. With fewer than
    30 per group, or fewer than 5 expected events or non-events in a group, 'warnings' says that
    this normal approximation is unreliable (check the power by an exact method or simulation).

    Cohen's h (arcsine) is reported for reference only: sizing with it under-estimates n for
    rare or extreme proportions (0.01 vs 0.05: 250 instead of 285 per group).
    Returns n1, n2 and total, before and after dropout inflation.
    """
    warn = []
    sides, alpha, dropout = _design(hypothesis, sides, alpha, dropout, margin, warn)
    _check_common(alpha, power, ratio, dropout)
    for name, p in (('p1', p1), ('p2', p2)):
        _finite(name, p)
        if not 0 < p < 1:
            raise ValueError(f"{name} 必须在 (0, 1) 之间（比例，不是百分数），收到 {p}")
    r = ratio
    var_alt = p1 * (1 - p1) + p2 * (1 - p2) / r          # n1 · Var(p̂2 − p̂1) under the alternative
    z_alpha, z_beta = _z(alpha, power, sides)
    if hypothesis == 'superiority':
        if p1 == p2:
            raise ValueError("p1 == p2：两组比例相同，效应为 0，所需样本量无穷大")
        p_bar = (p1 + r * p2) / (1 + r)
        delta = abs(p1 - p2)
        root = (z_alpha * math.sqrt(p_bar * (1 - p_bar) * (1 + 1 / r)) + z_beta * math.sqrt(var_alt)) / delta
        n1 = root * root                                  # inf (refused below), not an OverflowError
        _check_n(n1, n1 * r, what="（如两组比例几乎相同）")
        if continuity_correction:
            n1 = n1 / 4 * (1 + math.sqrt(1 + 2 * (r + 1) / (r * n1 * delta))) ** 2
        method = ('pooled-variance normal approximation (Fleiss)'
                  + (' with continuity correction' if continuity_correction else '')
                  + ('' if sides == 2 else ', one-sided'))
    else:
        if continuity_correction:
            raise ValueError("连续性校正只用于优效性检验；非劣效 / 等效设计用 Farrington-Manning 得分检验")
        if not margin < 1:
            raise ValueError(f"margin 是率差（比例单位），必须在 (0, 1) 之间，收到 {margin}")
        diff = p2 - p1

        def var_null(theta):
            q1, q2 = _rmle_diff(p1, p2, r, theta)
            return q1 * (1 - q1) + q2 * (1 - q2) / r

        if hypothesis == 'non-inferiority':
            theta = -margin if higher_is_better else margin
            distance = (diff - theta) if higher_is_better else (theta - diff)
            if distance <= 0:
                raise ValueError(f"预期率差 p2 − p1 = {diff:.4g} 已经越过非劣效界值（higher_is_better="
                                 f"{higher_is_better}），非劣效不可能成立；请核对方向和数值")
            root = (z_alpha * math.sqrt(var_null(theta)) + z_beta * math.sqrt(var_alt)) / distance
            n1 = root * root
            _check_n(n1, n1 * r, what="（如预期率差几乎落在非劣效界值上）")
            method = 'Farrington-Manning score test (restricted-MLE variance under H0), one-sided'
        else:
            if abs(diff) >= margin:
                raise ValueError(f"等效设计要求 |p2 − p1| < margin，收到 p2 − p1 = {diff:.4g}，margin = {margin}")
            sd_lo, sd_hi, sd_alt = (math.sqrt(var_null(-margin)), math.sqrt(var_null(margin)),
                                    math.sqrt(var_alt))

            def power_at(n):
                root = math.sqrt(n)
                return float(st.norm.cdf((root * (diff + margin) - z_alpha * sd_lo) / sd_alt)
                             + st.norm.cdf((root * (margin - diff) - z_alpha * sd_hi) / sd_alt) - 1)

            n1 = _solve_n(power_at, power, 1e-6, "所需样本量超过 10 亿：margin 与预期率差几乎相同",
                          too_large="margin 太宽：n1 = {n:g} 时检验效能已达 {p:.3f}；请核对 margin")
            method = 'two one-sided Farrington-Manning score tests (TOST)'
    h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))
    res = _per_group(n1, r, dropout, eps=1e-9)
    if hypothesis != 'superiority':
        small = _small_sample_note(res['n1'], res['n2'], p1, p2)
        if small:
            warn.append(small)
    return {
        'design': 'two_proportions',
        'hypothesis': hypothesis,
        'method': method,
        **res,
        'n_adjusted': res['n1_adjusted'],
        'effect_size_h': round(h, 3),
        'params': {'p1': p1, 'p2': p2, 'alpha': alpha, 'sides': sides, 'power': power,
                   'ratio': ratio, 'dropout': dropout, 'continuity_correction': continuity_correction,
                   'margin': margin, 'higher_is_better': higher_is_better},
        'warnings': warn,
    }


SMALL_N = 30           # proportion NI / equivalence: fewer per group than this, or
SMALL_COUNT = 5        # fewer expected events (or non-events) in a group: the normal approximation is doubtful


def _small_sample_note(n1, n2, p1, p2):
    """One-line warning when the Farrington-Manning (normal approximation) sample size is so small that
    its power is unreliable: fewer than SMALL_N per group, or fewer than SMALL_COUNT expected events or
    non-events in a group (the usual n·p ≥ 5 condition). Simulated at such sizes the power of the two
    one-sided score tests ranges from about 0.68 to 0.93 against a target of 0.80 (p1 = p2 = 0.02,
    margin 0.4: 10 per group, simulated power 0.70)."""
    counts = {'n1·p1': n1 * p1, 'n1·(1−p1)': n1 * (1 - p1), 'n2·p2': n2 * p2, 'n2·(1−p2)': n2 * (1 - p2)}
    name, low = min(counts.items(), key=lambda kv: kv[1])
    if min(n1, n2) >= SMALL_N and low >= SMALL_COUNT:
        return None
    return (f"样本量很小（n1 = {n1}、n2 = {n2}，预期例数最少的是 {name} = {low:.3g}）：每组不足 {SMALL_N} 例或预期事件数"
            f"（或非事件数）不足 {SMALL_COUNT} 时，Farrington-Manning 得分检验的正态近似不可靠，实际检验效能可能明显低于"
            "（或高于）目标；请用精确检验或模拟核对检验效能后再定样本量")


def _wilson_half_width(n, p, z):
    return z / (1 + z ** 2 / n) * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))


def _precision_n(p, precision, z, ci_method):
    """n (unrounded) for which the expected CI around p has half-width `precision`."""
    if ci_method == 'wald':
        root = z * math.sqrt(p * (1 - p)) / precision
        return root * root                     # a tiny precision gives inf (refused by the caller)
    if _wilson_half_width(1.0, p, z) <= precision:
        return 1.0
    hi = 2.0
    while _wilson_half_width(hi, p, z) > precision:
        hi *= 2
        if hi > N_MAX:
            return math.inf
    return float(optimize.brentq(lambda n: _wilson_half_width(n, p, z) - precision, 1.0, hi, xtol=1e-10))


def diagnostic(sensitivity, prevalence, precision=0.05, confidence=0.95, specificity=None, ci_method='wald'):
    """Diagnostic accuracy study: precision-based sample size (Buderer 1996).

    n_diseased      = z² · Se · (1 − Se) / precision²            (from sensitivity)
    n_non_diseased  = z² · Sp · (1 − Sp) / precision²            (from specificity)
    total_by_sens   = z² · Se · (1 − Se) / precision² / prevalence        (rounded up once)
    total_by_spec   = z² · Sp · (1 − Sp) / precision² / (1 − prevalence)  (rounded up once)
    n_total         = max(total_by_sens, total_by_spec)

    precision = half-width of the two-sided CI (0.05 means ±5 percentage points).
    If specificity is None only the sensitivity requirement is computed.
    ci_method='wald' is Buderer's formula. Near 0 or 1 (Se ± precision outside [0, 1]) the Wald
    interval is not usable and the formula under-sizes the study: a warning is added; use
    ci_method='wilson' to size for the Wilson score interval instead.
    """
    for name, x in (('sensitivity', sensitivity), ('specificity', specificity)):
        if x is not None and not 0 < x < 1:
            raise ValueError(f"{name} 必须在 (0, 1) 之间，收到 {x}")
    if not 0 < prevalence < 1:
        raise ValueError(f"prevalence（患病率）必须在 (0, 1) 之间，收到 {prevalence}")
    if not 0 < precision < 1:
        raise ValueError(f"precision（CI 半宽）必须在 (0, 1) 之间，收到 {precision}")
    if not 0 < confidence < 1:
        raise ValueError(f"confidence 必须在 (0, 1) 之间，收到 {confidence}")
    if ci_method not in ('wald', 'wilson'):
        raise ValueError(f"ci_method 必须是 'wald' 或 'wilson'，收到 {ci_method!r}")

    z = float(st.norm.ppf(1 - (1 - confidence) / 2))
    warn = []

    def need(name, p, share):
        raw = _precision_n(p, precision, z, ci_method)
        _check_n(raw, raw / share, what="（如 precision 太小，或患病率接近 0 或 1）")
        if ci_method == 'wald' and (p + precision >= 1 or p - precision <= 0):
            wilson = _precision_n(p, precision, z, 'wilson')
            _check_n(wilson, what="（按 Wilson 区间；如 precision 太小）")
            wilson = int(math.ceil(wilson - 1e-9))
            warn.append(f"{name} {p} ± {precision} 达到或超出 [0, 1] 的边界：Wald（Buderer）公式在比例接近 0 或 1 时不可用，"
                        f"会低估所需例数；按 Wilson 区间需 {wilson} 例（ci_method='wilson'，命令行 --ci-method wilson）")
        return max(1, int(math.ceil(raw - 1e-9))), max(1, int(math.ceil(raw / share - 1e-9)))

    n_dis, total_by_sens = need('sensitivity', sensitivity, prevalence)
    result = {
        'design': 'diagnostic_accuracy',
        'ci_method': ci_method,
        'by_sensitivity': {'n_diseased': n_dis, 'n_total': total_by_sens},
        'by_specificity': None,
        'n_diseased': n_dis,
        'n_total': total_by_sens,
        'binding_constraint': 'sensitivity',
        'params': {'sensitivity': sensitivity, 'specificity': specificity,
                   'prevalence': prevalence, 'precision': precision,
                   'confidence': confidence, 'ci_method': ci_method},
        'warnings': warn,
    }
    if specificity is not None:
        n_non, total_by_spec = need('specificity', specificity, 1 - prevalence)
        result['by_specificity'] = {'n_non_diseased': n_non, 'n_total': total_by_spec}
        result['n_non_diseased'] = n_non
        if total_by_spec > total_by_sens:
            result['n_total'] = total_by_spec
            result['binding_constraint'] = 'specificity'
    return result


def survival(hazard_ratio, alpha=None, power=0.80, ratio=1.0, event_rate=0.5, dropout=None, sides=None):
    """Survival outcome (log-rank test): Schoenfeld number of events, then n per group.

    D     = (z_{1-α/2} + z_{power})² / (ln(HR)² · p1 · p2),  p1 = 1/(1+ratio), p2 = ratio/(1+ratio)
    total = D / event_rate, split p1 : p2, each group then inflated by 1 / (1 − dropout)

    ratio = n2 / n1 (1.0 for 1:1). event_rate = overall proportion of participants
    expected to have the event by end of follow-up. HR = 0.7, 1:1, α = 0.05,
    power = 0.80 gives ≈ 247 events (not 494 — the old version double-counted),
    494 patients, 550 after 10% dropout.
    Keys as in two_groups (n1/n2/total before dropout, *_adjusted after); 'n_total' is
    total_adjusted, kept for backward compatibility.
    """
    warn = []
    sides, alpha, dropout = _design('superiority', sides, alpha, dropout, None, warn)
    _check_common(alpha, power, ratio, dropout)
    _finite('hazard_ratio', hazard_ratio)
    _finite('event_rate', event_rate)
    if hazard_ratio <= 0:
        raise ValueError(f"hazard_ratio 必须 > 0，收到 {hazard_ratio}")
    if hazard_ratio == 1:
        raise ValueError("hazard_ratio == 1：无效应，所需事件数无穷大")
    if not 0 < event_rate <= 1:
        raise ValueError(f"event_rate（随访期内事件发生比例）必须在 (0, 1] 之间，收到 {event_rate}")
    z_alpha, z_beta = _z(alpha, power, sides)
    p1, p2 = 1 / (1 + ratio), ratio / (1 + ratio)
    denominator = math.log(hazard_ratio) ** 2 * p1 * p2
    d = (z_alpha + z_beta) ** 2 / denominator if denominator > 0 else math.inf
    _check_n(d, what="（事件数；如 HR 几乎为 1）")
    events = int(math.ceil(d - 1e-9))
    res = _per_group(events / event_rate * p1, ratio, dropout, eps=1e-9)
    return {
        'design': 'survival_logrank',
        'events_needed': events,
        **res,
        'n_total': res['total_adjusted'],
        'params': {'hazard_ratio': hazard_ratio, 'event_rate': event_rate, 'alpha': alpha,
                   'sides': sides, 'power': power, 'ratio': ratio, 'dropout': dropout},
        'warnings': warn,
    }


def correlation(r_expected, alpha=None, power=0.80, sides=None):
    """Sample size to detect a (Pearson) correlation r ≠ 0 via Fisher's z transform."""
    warn = []
    sides, alpha, _ = _design('superiority', sides, alpha, None, None, warn, with_dropout=False)
    _check_common(alpha, power)
    if r_expected is None or not -1 < r_expected < 1:
        raise ValueError(f"r_expected 必须在 (-1, 1) 之间，收到 {r_expected}")
    if r_expected == 0:
        raise ValueError("r_expected == 0：无效应，所需样本量无穷大")
    z_alpha, z_beta = _z(alpha, power, sides)
    z_r = math.atanh(r_expected)            # = 0.5·ln((1 + r)/(1 − r)), exact also for tiny r
    root = (z_alpha + z_beta) / z_r
    n = root * root + 3
    _check_n(n, what="（如 r_expected 几乎为 0）")
    n = int(math.ceil(n))
    return {'design': 'correlation', 'n': n,
            'params': {'r_expected': r_expected, 'alpha': alpha, 'sides': sides, 'power': power},
            'warnings': warn}


# ─── CLI ────────────────────────────────────────────────────────────────────

def _fail(msg):
    """CLI error: one line on stderr, exit status 2 (never a traceback)."""
    print(str(msg).replace("\r", " ").replace("\n", " "), file=sys.stderr)
    raise SystemExit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):            # one line on stderr, exit 2 (argparse prints a usage block)
        _fail(f"参数错误：{message}（用 --help 查看用法）")


SCOPE = """\
covers: superiority (two- or one-sided) for two means, two proportions, log-rank and
correlation; non-inferiority and equivalence for two means and two proportions; precision
of sensitivity / specificity (diagnostic). Group 1 = control, group 2 = treatment, ratio = n2/n1.
alpha: two-sided for superiority (default 0.05); one-sided for --sides 1, non-inferiority and
each test of an equivalence design (default 0.025, ICH E9).
not covered: cluster-randomised, crossover and repeated-measures designs, non-inferiority /
equivalence for survival, prediction models (pmsampsize / pmvalsampsize), MRMC reader studies,
multi-arm and group-sequential designs -- use a dedicated tool."""


def _build_parser():
    p = _Parser(
        prog='power_analysis.py',
        description="A priori sample size for common medical study designs (prints JSON).",
        epilog=SCOPE, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='design', required=True, parser_class=_Parser)

    def common(sp, dropout=True, ratio=True):
        sp.add_argument('--alpha', type=float, default=None,
                        help='default 0.05 two-sided; 0.025 one-sided (--sides 1, non-inferiority, equivalence)')
        sp.add_argument('--power', type=float, default=0.80)
        if ratio:
            sp.add_argument('--ratio', type=float, default=1.0, help='n2/n1 allocation ratio (treatment : control)')
        if dropout:
            sp.add_argument('--dropout', type=float, default=None,
                            help=f'expected dropout, 0.1 = 10%% (default {DEFAULT_DROPOUT}, stated in the output)')

    def hypothesis(sp):
        sp.add_argument('--hypothesis', choices=HYPOTHESES, default='superiority')
        sp.add_argument('--margin', type=float, default=None,
                        help='non-inferiority / equivalence margin (> 0, same units as the effect)')
        sp.add_argument('--lower-is-better', action='store_true',
                        help='non-inferiority: a lower outcome is better (e.g. complication rate)')

    def sides(sp):
        sp.add_argument('--sides', type=int, choices=(1, 2), default=None,
                        help='superiority only: 2 (default) or 1-sided test')

    sp = sub.add_parser('two-groups', help="continuous outcome, Cohen's d", epilog=SCOPE,
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    sp.add_argument('--effect-size', type=float, required=True,
                    help="Cohen's d to detect; non-inferiority / equivalence: expected true difference "
                         "treatment − control in SD units (often 0)")
    hypothesis(sp)
    sides(sp)
    common(sp)

    sp = sub.add_parser('proportion', help="two proportions (Fleiss; Farrington-Manning for NI / equivalence)",
                        epilog=SCOPE, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp.add_argument('--p1', type=float, required=True, help='group 1 (control / reference) proportion')
    sp.add_argument('--p2', type=float, required=True, help='group 2 (treatment / new) proportion')
    sp.add_argument('--continuity-correction', action='store_true',
                    help='Fleiss-Tytun-Ury continuity correction (corrected chi-square / Fisher analysis)')
    hypothesis(sp)
    sides(sp)
    common(sp)

    sp = sub.add_parser('survival', help='log-rank / Cox (Schoenfeld events)')
    sp.add_argument('--hr', type=float, required=True, help='hazard ratio')
    sp.add_argument('--event-rate', type=float, default=0.5)
    sides(sp)
    common(sp)

    sp = sub.add_parser('diagnostic', help='sensitivity/specificity precision')
    sp.add_argument('--sensitivity', type=float, required=True)
    sp.add_argument('--specificity', type=float, default=None)
    sp.add_argument('--prevalence', type=float, required=True)
    sp.add_argument('--precision', type=float, default=0.05, help='CI half-width')
    sp.add_argument('--confidence', type=float, default=0.95)
    sp.add_argument('--ci-method', choices=('wald', 'wilson'), default='wald',
                    help='wald = Buderer (default); wilson for sensitivity / specificity near 0 or 1')

    sp = sub.add_parser('correlation', help='Pearson correlation')
    sp.add_argument('--r', type=float, required=True, help='expected correlation')
    sides(sp)
    common(sp, dropout=False, ratio=False)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if getattr(args, 'lower_is_better', False) and args.hypothesis != 'non-inferiority':
        _fail("参数错误：--lower-is-better 只用于 --hypothesis non-inferiority（优效性按双侧或 |d| 计算，等效不分方向）")
    try:
        if args.design == 'two-groups':
            res = two_groups(args.effect_size, alpha=args.alpha, power=args.power, ratio=args.ratio,
                             dropout=args.dropout, hypothesis=args.hypothesis, margin=args.margin,
                             sides=args.sides, higher_is_better=not args.lower_is_better)
        elif args.design == 'proportion':
            res = proportion(args.p1, args.p2, alpha=args.alpha, power=args.power, ratio=args.ratio,
                             dropout=args.dropout, continuity_correction=args.continuity_correction,
                             hypothesis=args.hypothesis, margin=args.margin, sides=args.sides,
                             higher_is_better=not args.lower_is_better)
        elif args.design == 'survival':
            res = survival(args.hr, alpha=args.alpha, power=args.power, ratio=args.ratio,
                           event_rate=args.event_rate, dropout=args.dropout, sides=args.sides)
        elif args.design == 'diagnostic':
            res = diagnostic(args.sensitivity, args.prevalence, precision=args.precision,
                             confidence=args.confidence, specificity=args.specificity,
                             ci_method=args.ci_method)
        else:
            res = correlation(args.r, alpha=args.alpha, power=args.power, sides=args.sides)
    except ValueError as e:
        _fail(f"参数错误：{e}")
    except ArithmeticError as e:             # overflow / underflow the guards above did not foresee
        _fail(f"参数错误：输入取值过于极端，计算溢出（{type(e).__name__}: {e}）；请核对各参数的数量级")
    except Exception as e:                   # a message, not a traceback
        _fail(f"计算时出错（{type(e).__name__}: {str(e)[:200]}）；请把这一行报告给插件维护者")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res


if __name__ == '__main__':
    main()
