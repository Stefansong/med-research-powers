#!/usr/bin/env python3
"""
Sample size calculation for common medical research designs.

Library use (inside a Python session; run from the user's project directory):
    import os, sys
    sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                    "skills", "statistical-analysis", "scripts"))
    from power_analysis import two_groups, proportion, survival, diagnostic, correlation

Command line (prints JSON):
    python3 power_analysis.py two-groups --effect-size 0.5 --dropout 0.15
    python3 power_analysis.py proportion --p1 0.30 --p2 0.50
    python3 power_analysis.py survival --hr 0.7 --event-rate 0.5
    python3 power_analysis.py diagnostic --sensitivity 0.9 --specificity 0.85 --prevalence 0.3
    python3 power_analysis.py correlation --r 0.3

Formulas
    two_groups  : two-sample t-test power (statsmodels TTestIndPower), effect = Cohen's d
    proportion  : two-sample test of proportions using Cohen's h (arcsine transform),
                  normal approximation (statsmodels NormalIndPower)
    survival    : Schoenfeld (1983) number of events for the log-rank test
                  D = (z_{1-α/2} + z_{power})² / (ln(HR)² · p1 · p2),  p1 = 1/(1+r), p2 = r/(1+r)
    diagnostic  : Buderer (1996) precision-based n for sensitivity and specificity
    correlation : Fisher z transform,  n = ((z_{1-α/2} + z_{power}) / z_r)² + 3

These calculations are for the *a priori* sample size written into study-protocol.md.
Do not use them for post hoc ("observed") power after the data are in.
"""

import argparse
import json
import math

try:
    from scipy import stats as st
except ImportError:  # pragma: no cover - depends on the user's environment
    raise SystemExit("缺少 scipy：pip install scipy")


# ─── helpers ────────────────────────────────────────────────────────────────

def _require_statsmodels():
    try:
        from statsmodels.stats import power as smp
    except ImportError:
        raise SystemExit("缺少 statsmodels：pip install statsmodels")
    return smp


def _check_common(alpha, power, ratio=1.0, dropout=0.0):
    if not 0 < alpha < 1:
        raise ValueError(f"alpha 必须在 (0, 1) 之间，收到 {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"power 必须在 (0, 1) 之间，收到 {power}")
    if ratio <= 0:
        raise ValueError(f"ratio（n2/n1）必须 > 0，收到 {ratio}")
    if not 0 <= dropout < 1:
        raise ValueError(f"dropout（脱落率）必须在 [0, 1) 之间，收到 {dropout}；"
                         "0.1 表示 10% 脱落")


def _z(alpha, power):
    return float(st.norm.ppf(1 - alpha / 2)), float(st.norm.ppf(power))


def _inflate(n, dropout):
    """Inflate n for expected dropout (n / (1 - dropout)), rounded up."""
    return int(math.ceil(n / (1 - dropout)))


# ─── designs ────────────────────────────────────────────────────────────────

def two_groups(effect_size, alpha=0.05, power=0.80, ratio=1.0, dropout=0.1):
    """Two-group continuous outcome (independent t-test). effect_size = Cohen's d.

    ratio = n2 / n1 (treatment : control). Returns per-group n before and after
    dropout inflation. Key 'n_per_group' is n1 (kept for backward compatibility).
    """
    _check_common(alpha, power, ratio, dropout)
    if effect_size is None or effect_size == 0:
        raise ValueError("effect_size（Cohen's d）不能为 0：效应为 0 时所需样本量无穷大")
    smp = _require_statsmodels()
    n1 = float(smp.TTestIndPower().solve_power(effect_size=abs(effect_size), alpha=alpha,
                                                power=power, ratio=ratio))
    n1_ceil = int(math.ceil(n1))
    n2_ceil = int(math.ceil(n1 * ratio))
    n1_adj, n2_adj = _inflate(n1_ceil, dropout), _inflate(n2_ceil, dropout)
    return {
        'design': 'two_groups_continuous',
        'n1': n1_ceil,
        'n2': n2_ceil,
        'n_per_group': n1_ceil,
        'n_treatment': n2_ceil,
        'total': n1_ceil + n2_ceil,
        'n1_adjusted': n1_adj,
        'n2_adjusted': n2_adj,
        'n_control_adjusted': n1_adj,
        'n_treatment_adjusted': n2_adj,
        'total_adjusted': n1_adj + n2_adj,
        'params': {'effect_size': effect_size, 'alpha': alpha, 'power': power,
                   'ratio': ratio, 'dropout': dropout},
    }


def proportion(p1, p2, alpha=0.05, power=0.80, ratio=1.0, dropout=0.1):
    """Two-group comparison of proportions.

    Effect size is Cohen's h = 2·asin(√p1) − 2·asin(√p2) (arcsine transform) and
    power is computed with the normal approximation (statsmodels NormalIndPower).
    This is the usual approximation for a chi-square / z test of two proportions;
    for very small expected counts plan on Fisher's exact test and add margin.
    ratio = n2 / n1. Returns n1, n2 and total, before and after dropout inflation.
    """
    _check_common(alpha, power, ratio, dropout)
    for name, p in (('p1', p1), ('p2', p2)):
        if not 0 < p < 1:
            raise ValueError(f"{name} 必须在 (0, 1) 之间（比例，不是百分数），收到 {p}")
    if p1 == p2:
        raise ValueError("p1 == p2：两组比例相同，效应为 0，所需样本量无穷大")
    smp = _require_statsmodels()
    h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))
    n1 = float(smp.NormalIndPower().solve_power(effect_size=abs(h), alpha=alpha,
                                                 power=power, ratio=ratio))
    n1_ceil = int(math.ceil(n1))
    n2_ceil = int(math.ceil(n1 * ratio))
    n1_adj, n2_adj = _inflate(n1_ceil, dropout), _inflate(n2_ceil, dropout)
    return {
        'design': 'two_proportions',
        'n1': n1_ceil,
        'n2': n2_ceil,
        'n_per_group': n1_ceil,
        'total': n1_ceil + n2_ceil,
        'n1_adjusted': n1_adj,
        'n2_adjusted': n2_adj,
        'n_adjusted': n1_adj,
        'total_adjusted': n1_adj + n2_adj,
        'effect_size_h': round(h, 3),
        'params': {'p1': p1, 'p2': p2, 'alpha': alpha, 'power': power,
                   'ratio': ratio, 'dropout': dropout},
    }


def diagnostic(sensitivity, prevalence, precision=0.05, confidence=0.95, specificity=None):
    """Diagnostic accuracy study: precision-based sample size (Buderer 1996).

    n_diseased      = z² · Se · (1 − Se) / precision²            (from sensitivity)
    n_non_diseased  = z² · Sp · (1 − Sp) / precision²            (from specificity)
    total_by_sens   = n_diseased / prevalence
    total_by_spec   = n_non_diseased / (1 − prevalence)
    n_total         = max(total_by_sens, total_by_spec)

    precision = half-width of the two-sided CI (0.05 means ±5 percentage points).
    If specificity is None only the sensitivity requirement is computed.
    """
    if not 0 < sensitivity < 1:
        raise ValueError(f"sensitivity 必须在 (0, 1) 之间，收到 {sensitivity}")
    if specificity is not None and not 0 < specificity < 1:
        raise ValueError(f"specificity 必须在 (0, 1) 之间，收到 {specificity}")
    if not 0 < prevalence < 1:
        raise ValueError(f"prevalence（患病率）必须在 (0, 1) 之间，收到 {prevalence}")
    if not 0 < precision < 1:
        raise ValueError(f"precision（CI 半宽）必须在 (0, 1) 之间，收到 {precision}")
    if not 0 < confidence < 1:
        raise ValueError(f"confidence 必须在 (0, 1) 之间，收到 {confidence}")

    z = float(st.norm.ppf(1 - (1 - confidence) / 2))
    n_dis = int(math.ceil((z ** 2 * sensitivity * (1 - sensitivity)) / precision ** 2))
    total_by_sens = int(math.ceil(n_dis / prevalence))
    result = {
        'design': 'diagnostic_accuracy',
        'by_sensitivity': {'n_diseased': n_dis, 'n_total': total_by_sens},
        'by_specificity': None,
        'n_diseased': n_dis,
        'n_total': total_by_sens,
        'binding_constraint': 'sensitivity',
        'params': {'sensitivity': sensitivity, 'specificity': specificity,
                   'prevalence': prevalence, 'precision': precision,
                   'confidence': confidence},
    }
    if specificity is not None:
        n_non = int(math.ceil((z ** 2 * specificity * (1 - specificity)) / precision ** 2))
        total_by_spec = int(math.ceil(n_non / (1 - prevalence)))
        result['by_specificity'] = {'n_non_diseased': n_non, 'n_total': total_by_spec}
        result['n_non_diseased'] = n_non
        if total_by_spec > total_by_sens:
            result['n_total'] = total_by_spec
            result['binding_constraint'] = 'specificity'
    return result


def survival(hazard_ratio, alpha=0.05, power=0.80, ratio=1.0, event_rate=0.5, dropout=0.1):
    """Survival outcome (log-rank test): Schoenfeld number of events, then total n.

    D       = (z_{1-α/2} + z_{power})² / (ln(HR)² · p1 · p2),  p1 = 1/(1+ratio), p2 = ratio/(1+ratio)
    n_total = D / event_rate / (1 − dropout)

    ratio = n2 / n1 (1.0 for 1:1). event_rate = overall proportion of participants
    expected to have the event by end of follow-up. HR = 0.7, 1:1, α = 0.05,
    power = 0.80 gives ≈ 247 events (not 494 — the old version double-counted).
    """
    _check_common(alpha, power, ratio, dropout)
    if hazard_ratio is None or hazard_ratio <= 0:
        raise ValueError(f"hazard_ratio 必须 > 0，收到 {hazard_ratio}")
    if hazard_ratio == 1:
        raise ValueError("hazard_ratio == 1：无效应，所需事件数无穷大")
    if not 0 < event_rate <= 1:
        raise ValueError(f"event_rate（随访期内事件发生比例）必须在 (0, 1] 之间，收到 {event_rate}")
    z_alpha, z_beta = _z(alpha, power)
    p1, p2 = 1 / (1 + ratio), ratio / (1 + ratio)
    d = (z_alpha + z_beta) ** 2 / (math.log(hazard_ratio) ** 2 * p1 * p2)
    events = int(math.ceil(d))
    n_total = int(math.ceil(events / event_rate / (1 - dropout)))
    n1 = int(math.ceil(n_total * p1))
    return {
        'design': 'survival_logrank',
        'events_needed': events,
        'n_total': n_total,
        'n1': n1,
        'n2': n_total - n1,
        'params': {'hazard_ratio': hazard_ratio, 'event_rate': event_rate, 'alpha': alpha,
                   'power': power, 'ratio': ratio, 'dropout': dropout},
    }


def correlation(r_expected, alpha=0.05, power=0.80):
    """Sample size to detect a (Pearson) correlation r ≠ 0 via Fisher's z transform."""
    _check_common(alpha, power)
    if r_expected is None or not -1 < r_expected < 1:
        raise ValueError(f"r_expected 必须在 (-1, 1) 之间，收到 {r_expected}")
    if r_expected == 0:
        raise ValueError("r_expected == 0：无效应，所需样本量无穷大")
    z_alpha, z_beta = _z(alpha, power)
    z_r = 0.5 * math.log((1 + r_expected) / (1 - r_expected))
    n = int(math.ceil(((z_alpha + z_beta) / z_r) ** 2 + 3))
    return {'design': 'correlation', 'n': n,
            'params': {'r_expected': r_expected, 'alpha': alpha, 'power': power}}


# ─── CLI ────────────────────────────────────────────────────────────────────

def _build_parser():
    p = argparse.ArgumentParser(
        description="A priori sample size for common medical study designs (prints JSON).")
    sub = p.add_subparsers(dest='design', required=True)

    def common(sp, dropout=True, ratio=True):
        sp.add_argument('--alpha', type=float, default=0.05)
        sp.add_argument('--power', type=float, default=0.80)
        if ratio:
            sp.add_argument('--ratio', type=float, default=1.0, help='n2/n1 allocation ratio')
        if dropout:
            sp.add_argument('--dropout', type=float, default=0.1, help='expected dropout, 0.1 = 10%%')

    sp = sub.add_parser('two-groups', help="continuous outcome, Cohen's d")
    sp.add_argument('--effect-size', type=float, required=True, help="Cohen's d")
    common(sp)

    sp = sub.add_parser('proportion', help="two proportions (Cohen's h)")
    sp.add_argument('--p1', type=float, required=True)
    sp.add_argument('--p2', type=float, required=True)
    common(sp)

    sp = sub.add_parser('survival', help='log-rank / Cox (Schoenfeld events)')
    sp.add_argument('--hr', type=float, required=True, help='hazard ratio')
    sp.add_argument('--event-rate', type=float, default=0.5)
    common(sp)

    sp = sub.add_parser('diagnostic', help='sensitivity/specificity precision')
    sp.add_argument('--sensitivity', type=float, required=True)
    sp.add_argument('--specificity', type=float, default=None)
    sp.add_argument('--prevalence', type=float, required=True)
    sp.add_argument('--precision', type=float, default=0.05, help='CI half-width')
    sp.add_argument('--confidence', type=float, default=0.95)

    sp = sub.add_parser('correlation', help='Pearson correlation')
    sp.add_argument('--r', type=float, required=True, help='expected correlation')
    common(sp, dropout=False, ratio=False)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.design == 'two-groups':
            res = two_groups(args.effect_size, args.alpha, args.power, args.ratio, args.dropout)
        elif args.design == 'proportion':
            res = proportion(args.p1, args.p2, args.alpha, args.power, args.ratio, args.dropout)
        elif args.design == 'survival':
            res = survival(args.hr, args.alpha, args.power, args.ratio, args.event_rate, args.dropout)
        elif args.design == 'diagnostic':
            res = diagnostic(args.sensitivity, args.prevalence, args.precision,
                             args.confidence, args.specificity)
        else:
            res = correlation(args.r, args.alpha, args.power)
    except ValueError as e:
        raise SystemExit(f"参数错误：{e}")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res


if __name__ == '__main__':
    main()
