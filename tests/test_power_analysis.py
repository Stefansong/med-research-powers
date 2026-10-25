import json
import math
import os
import sys
import types

import pytest

pytest.importorskip("scipy")
import numpy as np  # noqa: E402  (scipy depends on numpy)
from scipy import optimize, stats  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "statistical-analysis", "scripts"))
import power_analysis as pa  # noqa: E402

try:
    import statsmodels  # noqa: F401
    HAS_SM = True
except ImportError:
    HAS_SM = False
needs_statsmodels = pytest.mark.skipif(not HAS_SM, reason="statsmodels not installed")

Z = stats.norm.ppf


def _t_power(n1, n2, effect, alpha, sides):
    """Power of the two-sample t-test from scipy's noncentral t (independent of statsmodels)."""
    df = n1 + n2 - 2
    ncp = effect / math.sqrt(1 / n1 + 1 / n2)
    crit = stats.t.ppf(1 - alpha / sides, df)
    return stats.nct.sf(crit, df, ncp) + (stats.nct.cdf(-crit, df, ncp) if sides == 2 else 0)


def _mn_rmle(p1, p2, ratio, theta):
    """Restricted MLE with q2 - q1 = theta: root of the Miettinen-Nurminen (1985) cubic in q1."""
    n1, n2 = 1.0, ratio
    x1, x2 = p1 * n1, p2 * n2
    n, m = n1 + n2, x1 + x2
    coef = [n, (n2 + 2 * n1) * theta - n - m, (n1 * theta - n - 2 * x1) * theta + m, x1 * theta * (1 - theta)]
    lo, hi = max(0, -theta), min(1, 1 - theta)
    q1 = [r.real for r in np.roots(coef) if abs(r.imag) < 1e-9 and lo < r.real < hi]
    assert len(q1) == 1
    return q1[0], q1[0] + theta


def _cli(capsys, argv):
    try:
        res = pa.main([str(a) for a in argv])
        code = 0
    except SystemExit as e:
        res, code = None, e.code
    out, err = capsys.readouterr()
    return code, res, out, err


# ─── survival ───────────────────────────────────────────────────────────────

def test_survival_schoenfeld_events_not_double_counted():
    res = pa.survival(hazard_ratio=0.7, alpha=0.05, power=0.80, ratio=1.0, event_rate=0.5, dropout=0.1)
    assert res["events_needed"] == 247                 # ≈247, was 494 before the fix
    assert res["n1"] == res["n2"] == 247 and res["total"] == 494        # before dropout
    assert res["n1_adjusted"] == res["n2_adjusted"] == 275              # ceil(247 / 0.9), per group
    assert res["total_adjusted"] == res["n_total"] == 550
    assert res["warnings"] == []                       # dropout given explicitly


def test_survival_default_dropout_is_stated_in_the_output():
    res = pa.survival(0.7)
    assert res["params"]["dropout"] == 0.1
    assert any("dropout" in w and "默认" in w for w in res["warnings"])
    assert res["total"] == 494 and res["total_adjusted"] == 550
    none = pa.survival(0.7, dropout=0)
    assert none["total"] == none["total_adjusted"] == 494


def test_survival_ratio_two_is_not_tripled_and_puts_twice_as_many_in_group_2():
    r1 = pa.survival(0.7, ratio=1.0, dropout=0)
    r2 = pa.survival(0.7, ratio=2.0, dropout=0)
    assert r1["events_needed"] < r2["events_needed"] < 1.5 * r1["events_needed"]   # 1/(p1 p2): ×1.125, not ×3
    d = (Z(0.975) + Z(0.8)) ** 2 / (math.log(0.7) ** 2 * (1 / 3) * (2 / 3))
    assert r2["events_needed"] == math.ceil(d)
    assert r2["n1"] == math.ceil(r2["events_needed"] / 0.5 / 3)          # group 1 = control = 1/(1+r)
    assert r2["n2"] == math.ceil(r2["events_needed"] / 0.5 * 2 / 3)      # group 2 = treatment = r/(1+r)
    assert r2["n2"] > 1.9 * r2["n1"]


def test_survival_one_sided():
    res = pa.survival(0.7, sides=1, alpha=0.05, dropout=0)
    assert res["events_needed"] == math.ceil((Z(0.95) + Z(0.8)) ** 2 / (math.log(0.7) ** 2 / 4))


# ─── two means ──────────────────────────────────────────────────────────────

@needs_statsmodels
def test_two_groups_cohen_d_half():
    res = pa.two_groups(effect_size=0.5, alpha=0.05, power=0.80, ratio=1.0, dropout=0.0)
    assert res["n_per_group"] == 64
    assert res["n1"] == res["n2"] == 64
    assert res["total"] == 128
    assert res["n1_adjusted"] == 64                    # dropout 0 → no inflation


@needs_statsmodels
def test_two_groups_dropout_inflates():
    res = pa.two_groups(0.5, dropout=0.1)
    assert res["n1_adjusted"] == 72                    # ceil(64 / 0.9)
    assert res["total_adjusted"] == 144


def test_dropout_inflation_is_not_pushed_up_by_float_noise():
    assert pa._inflate(21, 0.3) == 30                  # 21 / 0.7 = 30.000000000000004 in floating point
    assert pa._inflate(64, 0.1) == 72 and pa._inflate(90, 0.1) == 100


@needs_statsmodels
@pytest.mark.parametrize("ratio", [2.0, 0.5, 3.0])
def test_two_groups_allocation_ratio_direction(ratio):
    res = pa.two_groups(0.5, ratio=ratio, dropout=0)
    n1, n2 = res["n1"], res["n2"]
    assert n2 == pytest.approx(ratio * n1, abs=1)      # ratio = n2 / n1, group 2 = treatment
    assert res["n_treatment"] == n2 and res["n_control_adjusted"] == n1
    assert _t_power(n1, n2, 0.5, 0.05, 2) >= 0.80
    assert _t_power(n1 - 1, (n1 - 1) * ratio, 0.5, 0.05, 2) < 0.80   # n1 is the smallest such n1


@needs_statsmodels
@pytest.mark.parametrize("d,ratio,expected", [
    (3.0, 0.25, (7, 2)),       # preclinical-size effects with unequal allocation are sized, not refused
    (3.5, 0.5, (4, 2)),
    (6.0, 1.0, (2, 2)),
    (6.0, 4.0, (2, 4)),
    (6.0, 0.25, (4, 2)),
    (2.5, 0.25, (9, 3)),
])
def test_two_groups_large_effects_keep_the_ratio_and_at_least_two_per_group(d, ratio, expected):
    res = pa.two_groups(d, ratio=ratio, dropout=0)
    n1, n2 = res["n1"], res["n2"]
    assert (n1, n2) == expected
    assert min(n1, n2) >= 2
    assert n2 <= ratio * n1 + 1 and n1 <= n2 / ratio + 1     # the ratio, not the floor, sets the group sizes
    reached = _t_power(n1, n2, d, 0.05, 2)
    assert reached >= 0.80
    floor_warnings = [w for w in res["warnings"] if "效应量很大" in w]
    if min(n1, n2) == 2:
        assert len(floor_warnings) == 1 and f"n1 = {n1}、n2 = {n2}" in floor_warnings[0]
        assert f"{reached:.3f}" in floor_warnings[0] and "每组 8 例" not in floor_warnings[0]
    else:
        assert floor_warnings == []


class _NanPower:
    """Stands in for TTestIndPower where its power is NaN, whatever the installed release returns."""
    def power(self, **kwargs):
        return float("nan")


@needs_statsmodels
@pytest.mark.parametrize("d,n,alternative,sides", [(3, 30, "two-sided", 2), (10, 10, "two-sided", 2),
                                                   (10, 30, "larger", 1)])
def test_two_groups_power_where_statsmodels_returns_nan(d, n, alternative, sides):
    # Once the power is essentially 1, TTestIndPower returns NaN with newer scipy (its far noncentral-t
    # tail underflows) but the right value with older releases (statsmodels 0.14.0 / scipy 1.11: 1.0).
    # Either way _t_power must give the exact power; the stub below runs its NaN branch on every release.
    from statsmodels.stats.power import TTestIndPower
    ttest = TTestIndPower()
    exact = _t_power(n, n, d, 0.05, sides)
    with np.errstate(all="ignore"):
        raw = float(ttest.power(effect_size=d, nobs1=n, alpha=0.05, ratio=1, alternative=alternative))
    assert math.isnan(raw) or raw == pytest.approx(exact, abs=1e-12)
    assert pa._t_power(ttest, d, n, n, 0.05, alternative) == pytest.approx(exact, abs=1e-12)
    assert pa._t_power(_NanPower(), d, n, n, 0.05, alternative) == pytest.approx(exact, abs=1e-12)


def test_t_power_nan_fallback_is_the_noncentral_t_power_not_a_constant():
    # the fallback at a power well below 1 and unequal groups, so df, ncp and the critical value are all
    # checked; two-sided it is the near tail alone (the far tail, P(T < −t), is 2e-5 here)
    assert pa._t_power(_NanPower(), 0.6, 20, 40, 0.05, "larger") == pytest.approx(_t_power(20, 40, 0.6, 0.05, 1),
                                                                                   abs=1e-12)
    two_sided = pa._t_power(_NanPower(), 0.6, 20, 40, 0.05, "two-sided")
    near_tail = stats.nct.sf(stats.t.ppf(0.975, 58), 58, 0.6 / math.sqrt(1 / 20 + 1 / 40))
    assert two_sided == pytest.approx(near_tail, abs=1e-12) and 0.5 < two_sided < 0.7
    assert two_sided == pytest.approx(_t_power(20, 40, 0.6, 0.05, 2), abs=1e-4)


@needs_statsmodels
def test_two_groups_large_effects_where_statsmodels_returns_nan():
    assert pa.two_groups(5.5, dropout=0)["n1"] == 3 and pa.two_groups(3, dropout=0)["n1"] == 4


@needs_statsmodels
def test_two_groups_one_sided():
    two = pa.two_groups(0.5, dropout=0)
    one_default = pa.two_groups(0.5, sides=1, dropout=0)   # default one-sided α 0.025 = two-sided 0.05
    assert one_default["params"]["alpha"] == 0.025 and abs(one_default["n1"] - two["n1"]) <= 1
    assert any("0.025" in w for w in one_default["warnings"])
    one = pa.two_groups(0.5, sides=1, alpha=0.05, dropout=0)
    assert one["n1"] == 51
    assert _t_power(51, 51, 0.5, 0.05, 1) >= 0.80 > _t_power(50, 50, 0.5, 0.05, 1)


@needs_statsmodels
@pytest.mark.parametrize("d,margin,ratio", [(0.0, 0.3, 1.0), (0.1, 0.5, 1.0), (0.0, 0.5, 2.0), (0.2, 0.6, 0.5)])
def test_two_groups_non_inferiority_against_noncentral_t(d, margin, ratio):
    res = pa.two_groups(d, hypothesis="non-inferiority", margin=margin, ratio=ratio, dropout=0)
    n1, n2 = res["n1"], res["n2"]
    assert res["params"]["alpha"] == 0.025              # one-sided default
    assert _t_power(n1, n2, d + margin, 0.025, 1) >= 0.80
    assert _t_power(n1 - 1, (n1 - 1) * ratio, d + margin, 0.025, 1) < 0.80
    normal = (Z(0.975) + Z(0.8)) ** 2 * (1 + 1 / ratio) / (d + margin) ** 2
    assert normal <= n1 <= normal + 3                    # t-based n is a little above the z-based n


@needs_statsmodels
def test_two_groups_non_inferiority_direction():
    better = pa.two_groups(0.1, hypothesis="non-inferiority", margin=0.3, dropout=0)
    worse = pa.two_groups(0.1, hypothesis="non-inferiority", margin=0.3, dropout=0, higher_is_better=False)
    assert better["n1"] < worse["n1"]                   # d+m = 0.4 vs m-d = 0.2
    with pytest.raises(ValueError, match="非劣效不可能成立"):
        pa.two_groups(-0.4, hypothesis="non-inferiority", margin=0.3)


def _sim_tost(n1, n2, d, margin, alpha, reps, seed):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((reps, n1))
    y = rng.standard_normal((reps, n2)) + d
    df = n1 + n2 - 2
    se = np.sqrt(((n1 - 1) * x.var(1, ddof=1) + (n2 - 1) * y.var(1, ddof=1)) / df * (1 / n1 + 1 / n2))
    diff = y.mean(1) - x.mean(1)
    t = stats.t.ppf(1 - alpha, df)
    return float(np.mean((diff - t * se > -margin) & (diff + t * se < margin)))


@needs_statsmodels
@pytest.mark.parametrize("d,margin,ratio", [(0.0, 0.5, 1.0), (0.1, 0.5, 1.0), (0.0, 0.5, 2.0)])
def test_two_groups_equivalence_tost(d, margin, ratio):
    res = pa.two_groups(d, hypothesis="equivalence", margin=margin, ratio=ratio, dropout=0)
    n1, n2 = res["n1"], res["n2"]
    zb = Z(0.9) if d == 0 else Z(0.8)                    # d = 0: both one-sided tests share β
    normal = (Z(0.975) + zb) ** 2 * (1 + 1 / ratio) / (margin - abs(d)) ** 2
    assert normal <= n1 <= normal + 5
    assert pa._tost_power_t(n1, n1 * ratio, d, margin, 0.025) >= 0.80
    assert pa._tost_power_t(n1 - 1, (n1 - 1) * ratio, d, margin, 0.025) < 0.80
    exact = pa._tost_power_t(n1, n2, d, margin, 0.025)
    assert _sim_tost(n1, n2, d, margin, 0.025, 40000, seed=11) == pytest.approx(exact, abs=0.01)


def test_tost_power_with_alpha_half_has_no_upper_limit_on_the_sd():
    # alpha 0.5: t = 0, equivalence whenever |D| < margin, so the power is P(|N(d, k²)| < margin)
    k = math.sqrt(2 / 10)
    exact = stats.norm.cdf((3 - 0.5) / k) - stats.norm.cdf((-3 - 0.5) / k)
    assert pa._tost_power_t(10, 10, 0.5, 3, 0.5) == pytest.approx(exact, abs=1e-8)     # was ZeroDivisionError


@pytest.mark.parametrize("t_half", [0.0, 6.730779349409391e-17, -6.730779349409391e-17])
def test_tost_power_does_not_depend_on_the_rounding_of_t_at_alpha_half(monkeypatch, t_half):
    # scipy 1.11 gives t.ppf(0.5, 18) = 6.7e-17, not 0: the upper limit on S became ~1e17 SDs, quad
    # integrated up to 1.8e35 and returned 0.0. Every rounding of t_0.5 must give P(|N(d, k²)| < margin).
    fake_t = types.SimpleNamespace(ppf=lambda q, df: t_half)
    monkeypatch.setattr(pa, "st", types.SimpleNamespace(t=fake_t, norm=stats.norm, chi2=stats.chi2))
    k = math.sqrt(2 / 10)
    exact = stats.norm.cdf((3 - 0.5) / k) - stats.norm.cdf((-3 - 0.5) / k)
    assert pa._tost_power_t(10, 10, 0.5, 3, 0.5) == pytest.approx(exact, abs=1e-8)


def _sim_tost_stats(n1, n2, d, margin, alpha, reps, seed):
    """TOST power simulated from the sufficient statistics, D ~ N(d, k²) and S² ~ χ²_df / df, so that
    tens of thousands per group need no raw data; independent of the integration in the package."""
    rng = np.random.default_rng(seed)
    df, k = n1 + n2 - 2, math.sqrt(1 / n1 + 1 / n2)
    diff = rng.normal(d, k, reps)
    se = np.sqrt(rng.chisquare(df, reps) / df) * k
    t = stats.t.ppf(1 - alpha, df)
    return float(np.mean((diff - t * se > -margin) & (diff + t * se < margin)))


@pytest.mark.parametrize("n1,n2,d,margin", [
    (16384, 16384, 0.0, 0.05),       # was 6.9e-13: quad's nodes on [0, df·S_max²] missed the χ² peak at df
    (100000, 100000, 0.0, 0.016),    # was 7e-41
    (100000, 200000, 0.002, 0.016),  # was 2e-100
    (1000000, 1000000, 0.0, 0.005),  # was 0.0
    (30000, 60000, 0.01, 0.03),
    (5, 5, 0.2, 2.0),
])
def test_tost_power_against_simulation_from_small_to_large_samples(n1, n2, d, margin):
    exact = pa._tost_power_t(n1, n2, d, margin, 0.025)
    assert 0.5 < exact < 0.999                                    # a power at which a miss would show
    assert exact == pytest.approx(_sim_tost_stats(n1, n2, d, margin, 0.025, 400000, seed=7), abs=0.004)


@needs_statsmodels
@pytest.mark.parametrize("margin", [0.05, 0.02])
def test_two_groups_equivalence_with_a_narrow_margin_is_sized_not_refused(margin):
    res = pa.two_groups(0, hypothesis="equivalence", margin=margin, dropout=0)   # was "所需样本量超过 10 亿"
    n1 = res["n1"]
    normal = (Z(0.975) + Z(0.9)) ** 2 * 2 / margin ** 2                       # z-based: 8 406 and 52 538 per group
    assert normal <= n1 <= normal + 5
    assert pa._tost_power_t(n1, n1, 0, margin, 0.025) >= 0.80 > pa._tost_power_t(n1 - 1, n1 - 1, 0, margin, 0.025)


@needs_statsmodels
def test_two_groups_equivalence_needing_hundreds_of_millions_per_group_is_sized_not_refused():
    # the search bound went 2.7e8 -> 1.07e9 and refused at once, without the power at 1e9 being looked at:
    # every design needing ~2.7e8 to 1e9 per group was "所需样本量超过 10 亿"
    margin = 0.00025
    res = pa.two_groups(0, hypothesis="equivalence", margin=margin, dropout=0)
    normal = (Z(0.975) + Z(0.9)) ** 2 * 2 / margin ** 2                       # 3.36e8 per group
    assert res["n1"] == res["n2"] > 2.7e8
    assert res["n1"] == pytest.approx(normal, rel=1e-5)    # t = z here; the χ² integral is good to ~1e-7 in power
    assert pa._tost_power_t(res["n1"], res["n2"], 0, margin, 0.025) == pytest.approx(0.80, abs=1e-5)
    with pytest.raises(ValueError, match="10 亿"):
        pa.two_groups(0, hypothesis="equivalence", margin=0.0001, dropout=0)  # 2.1e9: still refused


def test_proportion_equivalence_needing_hundreds_of_millions_per_group_is_sized_not_refused():
    for margin in (1e-4, 7.3e-5):                                           # 5.3e8 and 9.9e8 per group
        res = pa.proportion(0.5, 0.5, hypothesis="equivalence", margin=margin, dropout=0)
        q1, q2 = _mn_rmle(0.5, 0.5, 1.0, margin)
        n1 = (Z(0.975) * math.sqrt(q1 * (1 - q1) + q2 * (1 - q2)) + Z(0.9) * math.sqrt(0.5)) ** 2 / margin ** 2
        assert 2.7e8 < res["n1"] == res["n2"] <= 1e9
        assert res["n1"] == pytest.approx(n1, abs=1)
    with pytest.raises(ValueError, match="10 亿"):
        pa.proportion(0.5, 0.5, hypothesis="equivalence", margin=7.2e-5, dropout=0)   # 1.02e9


@needs_statsmodels
@pytest.mark.parametrize("margin,ratio,expected", [
    (999, 1.0, (2, 2)),          # was 2 / 2 with "检验效能已达 0.000"
    (1000, 1.0, (2, 2)),
    (150, 0.1, (10, 2)),         # was "已达 0.000"
    (200, 0.1, (10, 2)),         # was "所需样本量超过 10 亿"
    (200, 10.0, (2, 10)),
    (999, 10.0, (2, 10)),
])
def test_two_groups_equivalence_margin_of_hundreds_of_sds_gives_the_minimum_design(margin, ratio, expected):
    res = pa.two_groups(0, hypothesis="equivalence", margin=margin, ratio=ratio, dropout=0)
    n1, n2 = res["n1"], res["n2"]
    assert (n1, n2) == expected
    reached = pa._tost_power_t(n1, n2, 0, margin, 0.025)
    assert reached == pytest.approx(1.0, abs=1e-6)
    assert _sim_tost(n1, n2, 0, margin, 0.025, 20000, seed=3) == 1.0
    floor = [w for w in res["warnings"] if "界值（margin）相对标准差很大" in w]
    assert len(floor) == 1 and f"n1 = {n1}、n2 = {n2}" in floor[0] and "已达 1.000" in floor[0]


@needs_statsmodels
def test_two_groups_equivalence_needs_the_expected_difference_inside_the_margin():
    with pytest.raises(ValueError, match="等效设计要求"):
        pa.two_groups(0.5, hypothesis="equivalence", margin=0.5)


@needs_statsmodels
def test_two_groups_extreme_effect_sizes_give_clear_messages():
    res = pa.two_groups(10)                              # the minimum design, with a warning, not an error
    assert (res["n1"], res["n2"]) == (2, 2)
    assert any("效应量很大" in w and "标准化效应量" in w for w in res["warnings"])
    with pytest.raises(ValueError, match="10 亿"):
        pa.two_groups(1e-12)
    for call in (lambda: pa.two_groups(1e300), lambda: pa.two_groups(1e7, alpha=1e-10),   # NaN power / scipy stalls
                 lambda: pa.two_groups(0, hypothesis="equivalence", margin=1e300),
                 lambda: pa.two_groups(0, hypothesis="non-inferiority", margin=5e3)):
        with pytest.raises(ValueError, match="不可能是标准化效应量"):
            call()
    with pytest.raises(ValueError, match="alpha"):
        pa.two_groups(0.5, alpha=1e-160)                 # 1 − α/2 == 1: infinite critical value


# ─── two proportions ────────────────────────────────────────────────────────

def test_proportion_returns_both_groups_and_total():
    res = pa.proportion(0.30, 0.50, ratio=2.0, dropout=0.0)
    assert res["n1"] == 71 and res["n2"] == 141                 # Fleiss, r = 2 (70.28 → 71)
    assert res["total"] == 212
    assert res["effect_size_h"] == pytest.approx(-0.412, abs=1e-3)


def test_proportion_allocation_ratio_direction():
    # n1 = [z√(p̄q̄(1+1/r)) + zβ√(p1q1 + p2q2/r)]² / Δ², p̄ = (p1 + r p2)/(1 + r), r = n2/n1
    for r in (2.0, 0.5):
        p1, p2 = 0.30, 0.50
        p_bar = (p1 + r * p2) / (1 + r)
        n1 = (Z(0.975) * math.sqrt(p_bar * (1 - p_bar) * (1 + 1 / r))
              + Z(0.8) * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / r)) ** 2 / 0.2 ** 2
        res = pa.proportion(p1, p2, ratio=r, dropout=0)
        assert (res["n1"], res["n2"]) == (math.ceil(n1), math.ceil(n1 * r))
    assert pa.proportion(0.30, 0.50, ratio=0.5, dropout=0)["n1"] > pa.proportion(0.30, 0.50, ratio=2, dropout=0)["n1"]


@pytest.mark.parametrize("p1,p2,n", [
    (0.30, 0.50, 93),      # R: power.prop.test(p1=.3, p2=.5, power=.8) → n = 92.99
    (0.01, 0.05, 285),     # rare outcome: Cohen's h gave 250 (−12 %)
    (0.90, 0.99, 100),     # extreme proportions: Cohen's h gave 80 (−20 %)
    (0.05, 0.15, 141),     # Cohen's h gave 133
])
def test_proportion_matches_the_pooled_variance_formula(p1, p2, n):
    assert pa.proportion(p1, p2, dropout=0.0)["n1"] == n


def test_proportion_continuity_correction():
    res = pa.proportion(0.30, 0.50, dropout=0.0, continuity_correction=True)
    assert res["n1"] == 103 and "continuity" in res["method"]


def test_proportion_one_sided_uses_one_tail():
    p_bar, delta = 0.4, 0.2
    n1 = (Z(0.95) * math.sqrt(p_bar * (1 - p_bar) * 2) + Z(0.8) * math.sqrt(0.21 + 0.25)) ** 2 / delta ** 2
    assert pa.proportion(0.30, 0.50, sides=1, alpha=0.05, dropout=0)["n1"] == math.ceil(n1)


@needs_statsmodels
@pytest.mark.parametrize("p1,p2,ratio,margin,higher_is_better", [
    (0.85, 0.85, 1.0, 0.10, True),     # cure rate, equal expected
    (0.70, 0.75, 2.0, 0.10, True),
    (0.10, 0.10, 1.0, 0.05, False),    # complication rate: lower is better
    (0.30, 0.25, 0.5, 0.10, False),
])
def test_proportion_non_inferiority_farrington_manning(p1, p2, ratio, margin, higher_is_better):
    from statsmodels.stats.power import normal_sample_size_one_tail
    res = pa.proportion(p1, p2, hypothesis="non-inferiority", margin=margin, ratio=ratio, dropout=0,
                        higher_is_better=higher_is_better)
    theta = -margin if higher_is_better else margin
    q1, q2 = _mn_rmle(p1, p2, ratio, theta)
    assert pa._rmle_diff(p1, p2, ratio, theta) == pytest.approx((q1, q2), abs=1e-8)
    n1 = normal_sample_size_one_tail(abs(p2 - p1 - theta), 0.80, 0.025,
                                     std_null=math.sqrt(q1 * (1 - q1) + q2 * (1 - q2) / ratio),
                                     std_alternative=math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio))
    assert (res["n1"], res["n2"]) == (math.ceil(n1 - 1e-9), math.ceil(n1 * ratio - 1e-9))
    assert "Farrington-Manning" in res["method"] and res["params"]["alpha"] == 0.025


def test_proportion_non_inferiority_restricted_mle_reduces_to_pooled_at_zero_margin():
    # with a zero margin the restricted MLE is the pooled proportion of the superiority formula
    q1, q2 = pa._rmle_diff(0.3, 0.5, 2.0, 0.0)
    assert q1 == pytest.approx((0.3 + 2 * 0.5) / 3, abs=1e-8) and q2 == pytest.approx(q1, abs=1e-12)


def test_proportion_equivalence_closed_form_at_symmetric_point():
    # p1 = p2 = 0.5, 1:1: both one-sided tests have the same variances, so
    # n1 = (z_{1-α}·σ0 + z_{1-β/2}·σ1)² / δ²  (σ0 from the restricted MLE 0.55 / 0.45)
    res = pa.proportion(0.5, 0.5, hypothesis="equivalence", margin=0.1, dropout=0)
    q1, q2 = _mn_rmle(0.5, 0.5, 1.0, 0.1)
    n1 = (Z(0.975) * math.sqrt(q1 * (1 - q1) + q2 * (1 - q2)) + Z(0.9) * math.sqrt(0.5)) ** 2 / 0.1 ** 2
    assert res["n1"] == res["n2"] == math.ceil(n1) == 523


def _fm_rmle_vec(x1, n1, x2, n2, d0):
    """Farrington-Manning restricted MLE under H0: p1 − p2 = d0, closed-form (trigonometric) root
    of the cubic, vectorised for simulation; independent of the package and of _mn_rmle."""
    p1, p2, th = x1 / n1, x2 / n2, n2 / n1
    a = 1 + th
    b = -(1 + th + p1 + th * p2 + d0 * (th + 2))
    c = d0 ** 2 + d0 * (2 * p1 + th + 1) + p1 + th * p2
    d = -p1 * d0 * (1 + d0)
    v = b ** 3 / (3 * a) ** 3 - b * c / (6 * a ** 2) + d / (2 * a)
    u = np.sign(v) * np.sqrt(np.maximum(b ** 2 / (3 * a) ** 2 - c / (3 * a), 0))
    u = np.where(u == 0, 1e-300, u)
    w = (np.pi + np.arccos(np.clip(v / u ** 3, -1, 1))) / 3
    q1 = 2 * u * np.cos(w) - b / (3 * a)
    return np.clip(q1, 1e-12, 1 - 1e-12), np.clip(q1 - d0, 1e-12, 1 - 1e-12)


def _fm_equivalence_power_sim(p1, p2, n1, n2, margin, alpha, reps, seed):
    rng = np.random.default_rng(seed)
    x1, x2 = rng.binomial(n1, p1, reps), rng.binomial(n2, p2, reps)
    diff = x2 / n2 - x1 / n1                                   # p2 − p1
    za = Z(1 - alpha)
    q1, q2 = _fm_rmle_vec(x1, n1, x2, n2, margin)              # H0 lower: p2 − p1 = −margin
    z_lower = (diff + margin) / np.sqrt(q1 * (1 - q1) / n1 + q2 * (1 - q2) / n2)
    q1, q2 = _fm_rmle_vec(x1, n1, x2, n2, -margin)             # H0 upper: p2 − p1 = +margin
    z_upper = (margin - diff) / np.sqrt(q1 * (1 - q1) / n1 + q2 * (1 - q2) / n2)
    return float(np.mean((z_lower > za) & (z_upper > za)))


@pytest.mark.parametrize("p1,p2,ratio,margin", [(0.80, 0.85, 2.0, 0.10), (0.30, 0.25, 0.5, 0.12), (0.10, 0.13, 1.0, 0.08)])
def test_proportion_equivalence_asymmetric_against_independent_formula_and_simulation(p1, p2, ratio, margin):
    # each one-sided test uses the restricted-MLE variance at ITS OWN margin (−δ for the lower, +δ for the upper)
    res = pa.proportion(p1, p2, hypothesis="equivalence", margin=margin, ratio=ratio, dropout=0)
    diff, sd_alt = p2 - p1, math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)
    sd = {}
    for theta in (-margin, margin):
        q1, q2 = _mn_rmle(p1, p2, ratio, theta)
        sd[theta] = math.sqrt(q1 * (1 - q1) + q2 * (1 - q2) / ratio)

    def power(n):
        return (stats.norm.cdf((math.sqrt(n) * (diff + margin) - Z(0.975) * sd[-margin]) / sd_alt)
                + stats.norm.cdf((math.sqrt(n) * (margin - diff) - Z(0.975) * sd[margin]) / sd_alt) - 1)
    n1 = optimize.brentq(lambda n: power(n) - 0.80, 1, 1e6)                 # continuous n1, then each group up
    assert (res["n1"], res["n2"]) == (math.ceil(n1 - 1e-9), math.ceil(n1 * ratio - 1e-9))
    assert sd[-margin] != pytest.approx(sd[margin], rel=1e-3)          # the case really is asymmetric
    sim = _fm_equivalence_power_sim(p1, p2, res["n1"], res["n2"], margin, 0.025, 200000, seed=5)
    assert sim == pytest.approx(0.80, abs=0.015)


def _ni_power_sim(p1, p2, n1, n2, margin, alpha, reps, seed):
    """Farrington-Manning non-inferiority (higher is better, H0: p2 − p1 ≤ −margin), simulated."""
    rng = np.random.default_rng(seed)
    x1, x2 = rng.binomial(n1, p1, reps), rng.binomial(n2, p2, reps)
    q1, q2 = _fm_rmle_vec(x1, n1, x2, n2, margin)
    z = (x2 / n2 - x1 / n1 + margin) / np.sqrt(q1 * (1 - q1) / n1 + q2 * (1 - q2) / n2)
    return float(np.mean(z > Z(1 - alpha)))


@pytest.mark.parametrize("hypothesis,p,margin,n,simulated", [
    ("equivalence", 0.02, 0.4, 10, (0.65, 0.75)),        # expected events 0.2: simulated power 0.70, not 0.80
    ("equivalence", 0.5, 0.5, 18, (0.63, 0.72)),         # 9 events, but 18 per group: 0.68
    ("non-inferiority", 0.5, 0.4, 22, (0.72, 0.79)),     # 0.76
    ("equivalence", 0.02, 0.1, 81, (0.81, 0.88)),        # 81 per group, but 1.6 expected events: 0.84
])
def test_proportion_small_samples_carry_a_one_line_warning(hypothesis, p, margin, n, simulated):
    res = pa.proportion(p, p, hypothesis=hypothesis, margin=margin, dropout=0)
    assert res["n1"] == res["n2"] == n
    small = [w for w in res["warnings"] if "正态近似不可靠" in w]
    assert len(small) == 1 and "\n" not in small[0] and f"n1 = {n}、n2 = {n}" in small[0]
    assert "Farrington-Manning" in small[0] and "模拟" in small[0]
    sim = (_fm_equivalence_power_sim if hypothesis == "equivalence" else _ni_power_sim)(
        p, p, n, n, margin, 0.025, 100000, seed=3)
    assert simulated[0] < sim < simulated[1]                 # the approximation is off at this size, as the warning says


@pytest.mark.parametrize("call", [
    lambda: pa.proportion(0.5, 0.5, hypothesis="equivalence", margin=0.1, dropout=0),     # 523 per group
    lambda: pa.proportion(0.85, 0.85, hypothesis="non-inferiority", margin=0.10, dropout=0),
    lambda: pa.proportion(0.05, 0.05, hypothesis="equivalence", margin=0.1, dropout=0),   # 129, 6.5 events
    lambda: pa.proportion(0.30, 0.50, dropout=0),                                          # superiority: not affected
])
def test_proportion_no_small_sample_warning_for_ordinary_sizes(call):
    assert not any("正态近似不可靠" in w for w in call()["warnings"])
    assert pa._small_sample_note(30, 30, 0.5, 0.5) is None and pa._small_sample_note(29, 30, 0.5, 0.5)
    assert pa._small_sample_note(100, 100, 0.05, 0.05) is None and pa._small_sample_note(99, 100, 0.05, 0.05)
    assert "n2·(1−p2) = 4" in pa._small_sample_note(100, 200, 0.5, 0.98)


@pytest.mark.parametrize("call,needle", [
    (lambda: pa.proportion(0.85, 0.70, hypothesis="non-inferiority", margin=0.1), "非劣效不可能成立"),
    (lambda: pa.proportion(0.5, 0.7, hypothesis="equivalence", margin=0.1), "等效"),
    (lambda: pa.proportion(0.5, 0.5, hypothesis="non-inferiority"), "margin"),
    (lambda: pa.proportion(0.5, 0.5, hypothesis="non-inferiority", margin=0.1, sides=1), "sides"),
    (lambda: pa.proportion(0.3, 0.5, margin=0.1), "margin"),
    (lambda: pa.proportion(0.5, 0.5, hypothesis="non-inferiority", margin=0.1, continuity_correction=True), "连续性"),
    (lambda: pa.proportion(0.3, 0.5, hypothesis="noninferiority"), "hypothesis"),
])
def test_design_choices_are_validated(call, needle):
    with pytest.raises(ValueError, match=needle):
        call()


# ─── diagnostic / correlation ───────────────────────────────────────────────

def test_correlation_r_03():
    assert pa.correlation(0.3)["n"] == 85
    assert pa.correlation(0.3, sides=1, alpha=0.05)["n"] == math.ceil(((Z(0.95) + Z(0.8)) / math.atanh(0.3)) ** 2 + 3)


def test_diagnostic_with_specificity_takes_max():
    res = pa.diagnostic(sensitivity=0.9, prevalence=0.3, precision=0.05, specificity=0.85)
    assert res["by_sensitivity"]["n_diseased"] == 139
    assert res["by_sensitivity"]["n_total"] == 461     # 138.29 / 0.3 rounded up once (not ceil(139 / 0.3) = 464)
    assert res["by_specificity"]["n_non_diseased"] == 196
    assert res["by_specificity"]["n_total"] == 280
    assert res["n_total"] == max(461, 280)
    assert res["binding_constraint"] == "sensitivity"
    low_prev = pa.diagnostic(0.9, prevalence=0.9, specificity=0.85)
    assert low_prev["binding_constraint"] == "specificity"
    assert low_prev["n_total"] == low_prev["by_specificity"]["n_total"]


@pytest.mark.parametrize("se,sp,prev,prec", [(0.9, 0.85, 0.3, 0.05), (0.85, 0.80, 0.24, 0.075), (0.7, 0.95, 0.1, 0.04)])
def test_diagnostic_single_ceiling_matches_buderer(se, sp, prev, prec):
    z2 = Z(0.975) ** 2
    res = pa.diagnostic(se, prev, precision=prec, specificity=sp)
    assert res["by_sensitivity"]["n_total"] == math.ceil(z2 * se * (1 - se) / prec ** 2 / prev)
    assert res["by_specificity"]["n_total"] == math.ceil(z2 * sp * (1 - sp) / prec ** 2 / (1 - prev))


def test_diagnostic_never_returns_zero_participants():
    res = pa.diagnostic(1e-320, 0.5)                    # z²·Se(1 − Se)/L² is ~1e-317: was rounded to 0
    assert res["n_diseased"] == 1 and res["n_total"] >= 1
    assert res["warnings"] and "Wilson" in res["warnings"][0]


def test_diagnostic_without_specificity_is_backward_compatible():
    res = pa.diagnostic(0.9, 0.3)
    assert res["by_specificity"] is None
    assert res["n_diseased"] == 139 and res["n_total"] == 461


@needs_statsmodels
def test_diagnostic_warns_near_one_and_offers_the_wilson_basis():
    from statsmodels.stats.proportion import proportion_confint
    wald = pa.diagnostic(0.98, 0.3, precision=0.05)
    assert wald["n_diseased"] == 31 and wald["ci_method"] == "wald"
    assert wald["warnings"] and "Wilson" in wald["warnings"][0]
    assert pa.diagnostic(0.9, 0.3, precision=0.05)["warnings"] == []         # 0.9 ± 0.05 stays inside [0, 1]
    assert pa.diagnostic(0.95, 0.3, precision=0.05)["warnings"]               # 0.95 + 0.05 reaches the bound
    assert pa.diagnostic(0.9, 0.3, precision=0.05, specificity=0.05)["warnings"]   # 0.05 − 0.05 reaches 0
    wilson = pa.diagnostic(0.98, 0.3, precision=0.05, ci_method="wilson", specificity=0.97)
    assert wilson["warnings"] == []
    for p, n in ((0.98, wilson["n_diseased"]), (0.97, wilson["n_non_diseased"])):
        lo, hi = proportion_confint(p * n, n, alpha=0.05, method="wilson")
        lo1, hi1 = proportion_confint(p * (n - 1), n - 1, alpha=0.05, method="wilson")
        assert (hi - lo) / 2 <= 0.05 < (hi1 - lo1) / 2
    assert str(wilson["n_diseased"]) in wald["warnings"][0]
    assert wilson["n_total"] == math.ceil(pa._precision_n(0.98, 0.05, Z(0.975), "wilson") / 0.3)


# ─── validation ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("call", [
    lambda: pa.survival(1.0),
    lambda: pa.survival(0.0),
    lambda: pa.survival(0.7, dropout=1.0),
    lambda: pa.survival(0.7, event_rate=0.0),
    lambda: pa.two_groups(0.0),
    lambda: pa.two_groups(0.5, dropout=1.2),
    lambda: pa.proportion(0.3, 0.3),
    lambda: pa.proportion(1.5, 0.3),
    lambda: pa.correlation(0.0),
    lambda: pa.correlation(1.0),
    lambda: pa.diagnostic(0.9, prevalence=0.0),
    lambda: pa.diagnostic(0.9, 0.3, ci_method="exact"),
    lambda: pa.survival(float("inf")),
    lambda: pa.survival(0.7, ratio=float("nan")),
    lambda: pa.two_groups(float("inf")),
    lambda: pa.two_groups(0.5, ratio=float("nan")),
    lambda: pa.proportion(0.3, float("nan")),
    lambda: pa.survival(0.7, sides=3),
])
def test_boundary_inputs_raise_value_error(call):
    with pytest.raises(ValueError):
        call()


@pytest.mark.parametrize("call,needle", [
    (lambda: pa.correlation(1e-160), "10 亿"),                     # was ZeroDivisionError
    (lambda: pa.survival(0.7, event_rate=1e-308), "10 亿"),        # was OverflowError
    (lambda: pa.survival(0.9999999999), "10 亿"),                  # was 3.1e21 events
    (lambda: pa.survival(0.7, ratio=5e-324), "10 亿"),
    (lambda: pa.proportion(0.3, 0.5, ratio=1e-320), "10 亿"),      # was OverflowError
    (lambda: pa.proportion(0.3, 0.3000000001), "10 亿"),           # was n1 = 3.3e20
    (lambda: pa.proportion(1e-300, 2e-300), "10 亿"),
    (lambda: pa.proportion(0.5, 0.4, hypothesis="non-inferiority", margin=0.1), "10 亿"),   # Δ − (−δ) is rounding noise
    pytest.param(lambda: pa.two_groups(0.5, ratio=1e-320), "ratio", marks=needs_statsmodels),   # ZeroDivisionError
    pytest.param(lambda: pa.two_groups(0.5, ratio=1e300), "ratio", marks=needs_statsmodels),    # n2 had 300 digits
    pytest.param(lambda: pa.two_groups(0.5, dropout=0.9999999999999999), "脱落", marks=needs_statsmodels),
    (lambda: pa.diagnostic(0.9, 0.3, precision=1e-200), "precision"),
    (lambda: pa.diagnostic(0.9, 0.3, precision=1e-200, ci_method="wilson"), "precision"),
    (lambda: pa.diagnostic(0.9, 1e-300), "患病率"),
    (lambda: pa.diagnostic(1e-320, 0.3, precision=1e-12), "Wilson"),   # Wald warning branch: Wilson n is inf
])
def test_extreme_finite_inputs_raise_value_error_not_overflow(call, needle):
    with pytest.raises(ValueError, match=needle):
        call()


@pytest.mark.parametrize("call", [
    lambda: pa.proportion(0.3, 0.5, power=0.03),
    lambda: pa.proportion(0.3, 0.5, power=0.05),
    lambda: pa.survival(0.7, power=0.04),
    lambda: pa.correlation(0.3, power=0.05),
    lambda: pa.two_groups(0.5, power=0.02),
    lambda: pa.correlation(0.3, power=0.02, sides=1),     # one-sided default α 0.025
])
def test_power_not_above_alpha_is_rejected(call):
    with pytest.raises(ValueError, match="必须大于 alpha"):
        call()


@needs_statsmodels
def test_results_are_json_serialisable():
    for res in (pa.two_groups(0.5), pa.proportion(0.3, 0.5), pa.survival(0.7),
                pa.diagnostic(0.9, 0.3, specificity=0.8), pa.correlation(0.3),
                pa.two_groups(0, hypothesis="equivalence", margin=0.5),
                pa.proportion(0.8, 0.8, hypothesis="non-inferiority", margin=0.1)):
        json.dumps(res, allow_nan=False)


@needs_statsmodels
def test_default_dropout_is_stated_for_every_two_group_design():
    for res in (pa.two_groups(0.5), pa.proportion(0.3, 0.5), pa.survival(0.7)):
        assert res["params"]["dropout"] == 0.1 and any("dropout" in w for w in res["warnings"])
    for res in (pa.two_groups(0.5, dropout=0.15), pa.proportion(0.3, 0.5, dropout=0.15)):
        assert res["warnings"] == []


# ─── CLI ────────────────────────────────────────────────────────────────────

def test_cli_survival(capsys):
    code, _, out, _ = _cli(capsys, ["survival", "--hr", "0.7", "--event-rate", "0.5"])
    out = json.loads(out)
    assert code == 0 and out["events_needed"] == 247 and out["total"] == 494 and out["total_adjusted"] == 550


@needs_statsmodels
@pytest.mark.parametrize("argv,lib", [
    (["two-groups", "--effect-size", "0.4", "--alpha", "0.04", "--power", "0.85", "--ratio", "1.5",
      "--dropout", "0.2"],
     lambda: pa.two_groups(0.4, alpha=0.04, power=0.85, ratio=1.5, dropout=0.2)),
    (["two-groups", "--effect-size", "0.05", "--hypothesis", "non-inferiority", "--margin", "0.35",
      "--lower-is-better", "--ratio", "2", "--dropout", "0.05", "--power", "0.9", "--alpha", "0.02"],
     lambda: pa.two_groups(0.05, alpha=0.02, power=0.9, ratio=2, dropout=0.05, hypothesis="non-inferiority",
                           margin=0.35, higher_is_better=False)),
    (["two-groups", "--effect-size", "0.1", "--hypothesis", "equivalence", "--margin", "0.6", "--ratio", "0.5"],
     lambda: pa.two_groups(0.1, ratio=0.5, hypothesis="equivalence", margin=0.6)),
    (["two-groups", "--effect-size", "0.5", "--sides", "1", "--dropout", "0"],
     lambda: pa.two_groups(0.5, sides=1, dropout=0)),
    (["proportion", "--p1", "0.2", "--p2", "0.35", "--alpha", "0.01", "--power", "0.9", "--ratio", "0.5",
      "--dropout", "0.3", "--continuity-correction"],
     lambda: pa.proportion(0.2, 0.35, alpha=0.01, power=0.9, ratio=0.5, dropout=0.3, continuity_correction=True)),
    (["proportion", "--p1", "0.12", "--p2", "0.10", "--hypothesis", "non-inferiority", "--margin", "0.05",
      "--lower-is-better", "--ratio", "3"],
     lambda: pa.proportion(0.12, 0.10, ratio=3, hypothesis="non-inferiority", margin=0.05, higher_is_better=False)),
    (["proportion", "--p1", "0.6", "--p2", "0.62", "--hypothesis", "equivalence", "--margin", "0.12",
      "--dropout", "0"],
     lambda: pa.proportion(0.6, 0.62, hypothesis="equivalence", margin=0.12, dropout=0)),
    (["survival", "--hr", "0.75", "--event-rate", "0.6", "--alpha", "0.01", "--power", "0.9", "--ratio", "2",
      "--dropout", "0.2", "--sides", "1"],
     lambda: pa.survival(0.75, alpha=0.01, power=0.9, ratio=2, event_rate=0.6, dropout=0.2, sides=1)),
    (["diagnostic", "--sensitivity", "0.97", "--specificity", "0.8", "--prevalence", "0.2", "--precision", "0.04",
      "--confidence", "0.9", "--ci-method", "wilson"],
     lambda: pa.diagnostic(0.97, 0.2, precision=0.04, confidence=0.9, specificity=0.8, ci_method="wilson")),
    (["correlation", "--r", "0.25", "--alpha", "0.01", "--power", "0.9", "--sides", "1"],
     lambda: pa.correlation(0.25, alpha=0.01, power=0.9, sides=1)),
])
def test_cli_passes_every_flag_to_the_right_parameter(capsys, argv, lib):
    code, res, out, err = _cli(capsys, argv)
    assert code == 0 and err == ""
    assert json.loads(out) == json.loads(json.dumps(lib()))


@pytest.mark.parametrize("argv,needle", [
    (["survival", "--hr", "1"], "hazard_ratio"),
    (["survival", "--hr", "abc"], "参数错误"),
    (["survival", "--hr", "0.7", "--power", "0.04"], "必须大于 alpha"),
    (["two-groups", "--effect-size", "0.5", "--margin", "0.2"], "margin"),
    (["two-groups", "--effect-size", "0.5", "--lower-is-better"], "--lower-is-better"),
    (["proportion", "--p1", "0.3", "--p2", "0.5", "--hypothesis", "equivalence", "--margin", "0.1"], "等效"),
    (["diagnostic", "--sensitivity", "0.9", "--prevalence", "0.3", "--ci-method", "exact"], "参数错误"),
    ([], "参数错误"),
    (["correlation", "--r", "1e-160"], "10 亿"),
    (["survival", "--hr", "0.7", "--event-rate", "1e-308"], "10 亿"),
    (["survival", "--hr", "0.9999999999"], "10 亿"),
    (["proportion", "--p1", "0.3", "--p2", "0.5", "--ratio", "1e-320"], "10 亿"),
    (["proportion", "--p1", "0.3", "--p2", "0.3000000001"], "10 亿"),
    (["diagnostic", "--sensitivity", "0.9", "--prevalence", "0.3", "--precision", "1e-200"], "10 亿"),
])
def test_cli_errors_are_one_line_with_exit_2(capsys, argv, needle):
    code, _, out, err = _cli(capsys, argv)
    assert code == 2 and out == ""
    assert needle in err and len(err.strip().splitlines()) == 1 and "Traceback" not in err


@needs_statsmodels
@pytest.mark.parametrize("argv", [["two-groups", "--effect-size", "0.5", "--ratio", "1e-320"],
                                  ["two-groups", "--effect-size", "0.5", "--ratio", "1e300"]])
def test_cli_extreme_ratio_is_one_line_with_exit_2(capsys, argv):
    code, _, out, err = _cli(capsys, argv)
    assert code == 2 and out == "" and "ratio" in err and len(err.strip().splitlines()) == 1


@pytest.mark.parametrize("exc,needle", [(OverflowError("math range error"), "溢出"),
                                        (ZeroDivisionError("float division by zero"), "溢出"),
                                        (RuntimeError("unexpected"), "维护者")])
def test_cli_unforeseen_errors_are_one_line_with_exit_2(capsys, monkeypatch, exc, needle):
    def boom(*a, **k):
        raise exc
    monkeypatch.setattr(pa, "correlation", boom)
    code, _, out, err = _cli(capsys, ["correlation", "--r", "0.3"])
    assert code == 2 and out == "" and needle in err
    assert len(err.strip().splitlines()) == 1 and "Traceback" not in err


@needs_statsmodels
def test_cli_large_effect_is_sized_with_a_warning(capsys):
    code, _, out, err = _cli(capsys, ["two-groups", "--effect-size", "3", "--ratio", "0.25", "--dropout", "0"])
    out = json.loads(out)
    assert code == 0 and err == "" and (out["n1"], out["n2"]) == (7, 2)
    assert any("n1 = 7、n2 = 2" in w for w in out["warnings"])


def test_cli_help_states_what_is_and_is_not_covered(capsys):
    code, _, out, _ = _cli(capsys, ["--help"])
    assert code == 0
    for needle in ("non-inferiority", "equivalence", "not covered", "cluster", "pmsampsize", "MRMC"):
        assert needle in out
