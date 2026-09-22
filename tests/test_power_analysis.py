import json
import os
import sys

import pytest

pytest.importorskip("scipy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "statistical-analysis", "scripts"))
import power_analysis as pa  # noqa: E402

try:
    import statsmodels  # noqa: F401
    HAS_SM = True
except ImportError:
    HAS_SM = False
needs_statsmodels = pytest.mark.skipif(not HAS_SM, reason="statsmodels not installed")


def test_survival_schoenfeld_events_not_double_counted():
    res = pa.survival(hazard_ratio=0.7, alpha=0.05, power=0.80, ratio=1.0, event_rate=0.5, dropout=0.1)
    assert 240 <= res["events_needed"] <= 255          # ≈247, was 494 before the fix
    assert res["n_total"] == 549
    assert res["n1"] + res["n2"] == res["n_total"]


def test_survival_ratio_two_is_not_tripled():
    r1 = pa.survival(0.7, ratio=1.0)["events_needed"]
    r2 = pa.survival(0.7, ratio=2.0)["events_needed"]
    assert r1 < r2 < 1.5 * r1                          # p1*p2 = 2/9 vs 1/4 → ×1.125, not ×3


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


def test_correlation_r_03():
    assert pa.correlation(0.3)["n"] == 85


@needs_statsmodels
def test_proportion_returns_both_groups_and_total():
    res = pa.proportion(0.30, 0.50, ratio=2.0, dropout=0.0)
    assert res["n1"] == 70 and res["n2"] == 140
    assert res["total"] == 210
    assert res["effect_size_h"] == pytest.approx(-0.412, abs=1e-3)
    assert "Cohen's h" in pa.proportion.__doc__


def test_diagnostic_with_specificity_takes_max():
    res = pa.diagnostic(sensitivity=0.9, prevalence=0.3, precision=0.05, specificity=0.85)
    assert res["by_sensitivity"]["n_diseased"] == 139
    assert res["by_sensitivity"]["n_total"] == 464
    assert res["by_specificity"]["n_non_diseased"] == 196
    assert res["by_specificity"]["n_total"] == 280
    assert res["n_total"] == max(464, 280)
    assert res["binding_constraint"] == "sensitivity"
    low_prev = pa.diagnostic(0.9, prevalence=0.9, specificity=0.85)
    assert low_prev["binding_constraint"] == "specificity"
    assert low_prev["n_total"] == low_prev["by_specificity"]["n_total"]


def test_diagnostic_without_specificity_is_backward_compatible():
    res = pa.diagnostic(0.9, 0.3)
    assert res["by_specificity"] is None
    assert res["n_diseased"] == 139 and res["n_total"] == 464


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
])
def test_boundary_inputs_raise_value_error(call):
    with pytest.raises(ValueError):
        call()


@needs_statsmodels
def test_results_are_json_serialisable():
    for res in (pa.two_groups(0.5), pa.proportion(0.3, 0.5), pa.survival(0.7),
                pa.diagnostic(0.9, 0.3, specificity=0.8), pa.correlation(0.3)):
        json.dumps(res)


def test_cli_survival(capsys):
    pa.main(["survival", "--hr", "0.7", "--event-rate", "0.5"])
    out = json.loads(capsys.readouterr().out)
    assert out["events_needed"] == 247


def test_cli_bad_input_exits_cleanly():
    with pytest.raises(SystemExit):
        pa.main(["survival", "--hr", "1"])
