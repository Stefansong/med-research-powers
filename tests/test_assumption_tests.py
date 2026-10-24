import json
import os
import sys

import numpy as np
import pytest

pytest.importorskip("pandas")
pytest.importorskip("scipy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "statistical-analysis", "scripts"))
import assumption_tests as at  # noqa: E402

RNG = np.random.default_rng(0)
NORMAL_A = RNG.normal(0, 1, 30)
NORMAL_B = RNG.normal(0.5, 1, 30)

# 10 subjects x 4 repeated conditions; reference values from pingouin 0.7.0 sphericity() / epsilon()
RM = np.array([[45, 50, 55, 70], [42, 42, 45, 60], [36, 41, 43, 62], [39, 35, 40, 55], [51, 55, 59, 72],
               [44, 49, 56, 66], [40, 44, 47, 61], [47, 50, 52, 70], [38, 39, 45, 52], [43, 49, 53, 67]], float)
# 7 subjects x 6 conditions: small n, where the second-order term of Mauchly's p-value matters
K6 = np.array([[12, 15, 11, 18, 14, 20], [10, 14, 13, 15, 12, 17], [14, 13, 15, 21, 16, 19], [11, 16, 12, 14, 15, 22],
               [13, 12, 14, 19, 13, 18], [9, 15, 10, 16, 14, 21], [12, 17, 13, 17, 17, 16]], float)


def _cli(capsys, argv):
    """Run the CLI; return (exit code, stdout, stderr). Exit code 0 when main returns."""
    try:
        at.main([str(a) for a in argv])
        code = 0
    except SystemExit as e:
        code = e.code
    out, err = capsys.readouterr()
    return code, out, err


def _csv(tmp_path, name, **cols):
    import pandas as pd
    path = tmp_path / name
    pd.DataFrame(cols).to_csv(path, index=False)
    return path


def test_small_groups_are_flagged_but_do_not_switch_the_test():
    res = at.full_check([1, 2, 3, 4, 5], [2, 3, 4, 5, 7])
    assert res["all_normal"] is None
    assert res["recommended_test"] == "Welch's t-test"
    assert res["rank_based_alternative"] == "Mann-Whitney U"
    assert res["warnings"] and "< 8" in res["warnings"][0]
    assert all(t["is_normal"] is None for t in res["normality_tests"])


def test_welch_is_the_default_whatever_levene_says():
    rng = np.random.default_rng(1)
    equal = at.full_check(rng.normal(0, 1, 40), rng.normal(0, 1, 40))
    unequal = at.full_check(rng.normal(0, 1, 40), rng.normal(0, 5, 40))
    assert equal["recommended_test"] == unequal["recommended_test"] == "Welch's t-test"
    assert unequal["homogeneous"] is False                      # still reported, as a description
    three = at.full_check(NORMAL_A, NORMAL_B, NORMAL_A + 1)
    assert three["recommended_test"] == "Welch's ANOVA + Games-Howell"
    assert "SAP" in three["how_to_use"]


def test_normal_groups_get_t_test_and_python_bools():
    res = at.full_check(NORMAL_A, NORMAL_B)
    assert res["recommended_test"] == "Welch's t-test"
    assert type(res["all_normal"]) is bool
    assert type(res["homogeneous"]) is bool
    assert type(res["normality_tests"][0]["is_normal"]) is bool
    json.dumps(res)


def test_constant_groups_give_valid_json_and_the_right_warning():
    res = at.full_check([5.0] * 30, [5.0] * 30)
    json.dumps(res, allow_nan=False)
    assert res["homogeneity_test"]["is_homogeneous"] is None
    assert "方差为 0" in res["warnings"][0] and "< 8" not in res["warnings"][0]


def test_small_constant_group_is_reported_as_constant_not_as_n_below_8():
    res = at.check_normality([5.0, 5.0, 5.0])
    assert res["method"] == "constant_data"
    flags = at.full_check([5.0, 5.0, 5.0], [1.0, 2.0, 4.0])["warnings"]
    assert "方差为 0" in flags[0] and "< 8" not in flags[0]


def test_per_group_results_carry_no_parametric_gating_label():
    rng = np.random.default_rng(2)
    reports = [at.full_check(rng.exponential(1, 40), rng.normal(0, 1, 40)),   # one group clearly non-normal
               at.full_check([1, 2, 3, 4, 5], [2, 3, 4, 5, 7]),               # n < 8
               at.full_check(NORMAL_A, NORMAL_B, NORMAL_A + 0.2, paired=True)]
    for res in reports:
        for t in res["normality_tests"]:
            assert "recommendation" not in t
        text = json.dumps(res)
        assert "Parametric" not in text and "Non-parametric" not in text and "Non-param" not in text
    assert reports[0]["normality_tests"][0]["is_normal"] is False          # still described
    assert reports[0]["recommended_test"] == "Welch's t-test"


def test_inf_is_invalid_input_not_a_normal_observation():
    with pytest.raises(ValueError, match="无穷值"):
        at.check_normality([1, 2, 3, 4, 5, 6, 7, 8, 9, float("inf")])
    with pytest.raises(ValueError, match="无穷值"):
        at.full_check([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, float("-inf")])
    with pytest.raises(ValueError, match="无穷值"):
        at.effect_size_cohens_d([1.0, 2.0, float("inf")], [1.0, 2.0, 3.0])


@pytest.mark.parametrize("n", [20, 60])                      # Shapiro-Wilk and D'Agostino-Pearson
@pytest.mark.parametrize("factor", [1e300, 1e-300])
def test_normality_does_not_depend_on_the_scale_of_the_data(n, factor):
    x = np.random.default_rng(n).exponential(1, n)
    ref, res = at.check_normality(x), at.check_normality(x * factor)   # was undefined / "range zero"
    assert res["statistic"] is not None and res["is_normal"] is False
    assert (res["statistic"], res["p_value"], res["method"]) == (ref["statistic"], ref["p_value"], ref["method"])
    two_point = at.check_normality([1e308] * 4 + [-1e308] * 4)   # the range itself overflows
    assert two_point["statistic"] == at.check_normality([1.0] * 4 + [-1.0] * 4)["statistic"]


@pytest.mark.parametrize("name,n,method", [("shapiro", 20, "Shapiro-Wilk"), ("normaltest", 60, "D'Agostino-Pearson")])
@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_non_finite_normality_statistic_is_reported_as_undefined(monkeypatch, name, n, method, value):
    monkeypatch.setattr(at.stats, name, lambda x: (value, value))
    res = at.check_normality(np.arange(n, dtype=float))
    assert res["method"] == method
    assert res["statistic"] is None and res["p_value"] is None and res["is_normal"] is None
    json.dumps(res, allow_nan=False)
    flags = at.full_check(np.arange(n, dtype=float), np.arange(n, dtype=float) ** 2)["warnings"]
    assert any("无定义" in w for w in flags)


def test_paired_differences_that_overflow_are_invalid_input_not_called_inf_in_the_data():
    with pytest.raises(ValueError, match="配对差值超出浮点数范围"):
        at.full_check([1e308, -1e308] * 5, [-1e308, 1e308] * 5, paired=True)


def test_non_finite_levene_statistic_is_reported_as_undefined():
    # every within-group absolute deviation from the median is equal -> Levene's W = inf, p = 0
    res = at.full_check([0, 2] * 4, [5] * 8)
    assert res["homogeneity_test"]["statistic"] is None
    assert res["homogeneity_test"]["is_homogeneous"] is None
    json.dumps(res, allow_nan=False)


def test_independent_missing_values_are_counted_in_the_warnings():
    res = at.full_check([1, 2, 3, None, 5, 6, 7, 8, 9], [2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert res["normality_tests"][0]["n"] == 8
    assert "剔除 1 个缺失值" in res["warnings"][0]


@pytest.mark.parametrize("alpha", [0, 1, 1.5, -0.1, float("nan"), None])
def test_alpha_outside_unit_interval_is_rejected(alpha):
    with pytest.raises(ValueError, match="alpha"):
        at.full_check(NORMAL_A, NORMAL_B, alpha=alpha)


def test_cli_rejects_text_values_and_duplicate_paired_rows(tmp_path, capsys):
    csv = _csv(tmp_path, "bad.csv", arm=["A", "B"] * 10, y=["1.2", "未查"] + ["3"] * 18)
    code, out, err = _cli(capsys, [csv, "--value", "y", "--group", "arm"])
    assert code == 2 and "不是数字" in err and out == ""
    dup = _csv(tmp_path, "dup.csv", id=[1, 1, 1, 2, 2], t=["pre", "pre", "post", "pre", "post"],
               y=[1.0, 2.0, 3.0, 4.0, 5.0])
    code, _, err = _cli(capsys, [dup, "--value", "y", "--group", "t", "--paired", "--id", "id"])
    assert code == 2 and "重复记录" in err


def test_paired_length_mismatch_raises():
    with pytest.raises(ValueError, match="长度不等"):
        at.full_check([1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3], paired=True)


def test_paired_with_a_single_condition_is_rejected(tmp_path, capsys):
    with pytest.raises(ValueError, match="至少需要 2 个条件"):
        at.full_check([1, 2, 3, 4, 5, 6, 7, 8, 9], paired=True)
    csv = _csv(tmp_path, "one.csv", id=list(range(10)), t=["pre"] * 10, y=[1, 3, 2, 5, 4, 6, 8, 7, 9, 12])
    code, out, err = _cli(capsys, [csv, "--value", "y", "--group", "t", "--paired", "--id", "id"])
    assert code == 2 and out == ""
    assert "至少 2 个条件" in err and len(err.strip().splitlines()) == 1


def test_paired_filters_incomplete_pairs_before_differencing():
    a = list(NORMAL_A) + [None]
    b = [None] + list(NORMAL_B)
    res = at.full_check(a, b, paired=True)
    assert res["n_pairs"] == 29
    assert res["n_pairs_dropped"] == 2
    assert res["normality_tests"][0]["n"] == 29
    assert res["homogeneity_test"] is None
    json.dumps(res)


def test_repeated_measures_default_is_greenhouse_geisser_not_a_mauchly_gate():
    res = at.full_check(*RM.T, paired=True)
    assert res["homogeneity_test"] is None
    assert res["recommended_test"] == at.choose_test(4, paired=True)
    assert "Greenhouse-Geisser" in res["recommended_test"] and "mixed model" in res["recommended_test"]
    assert "whatever Mauchly" in res["recommended_test"]
    text = json.dumps(res)
    assert "if violated" not in text
    assert "description" in res["sphericity"]["note"].lower()
    assert res["rank_based_alternative"] == "Friedman + Nemenyi"
    json.dumps(res, allow_nan=False)


def test_sphericity_matches_pingouin_reference_values():
    sph = at.check_sphericity(*RM.T)    # pingouin: W 0.24789, chi2 10.77073, dof 5, p 0.05798, eps 0.70094
    assert sph["W"] == pytest.approx(0.24789, abs=1e-4)
    assert sph["chi2"] == pytest.approx(10.7707, abs=1e-3)
    assert sph["df"] == 5
    assert sph["p_value"] == pytest.approx(0.05798, abs=1e-4)
    assert sph["greenhouse_geisser_epsilon"] == pytest.approx(0.70094, abs=1e-4)
    three = at.check_sphericity(*RM[:, :3].T)           # 3 conditions: first-order p equals pingouin / R
    assert three["W"] == pytest.approx(0.56979, abs=1e-4)
    assert three["p_value"] == pytest.approx(0.10541, abs=1e-4)
    assert three["greenhouse_geisser_epsilon"] == pytest.approx(0.69920, abs=1e-4)
    too_few = at.check_sphericity([1.0, 2.0], [2.0, 4.0], [3.0, 7.0])   # n <= k - 1
    assert too_few["W"] is None and too_few["greenhouse_geisser_epsilon"] is None


def test_mauchly_p_value_has_the_second_order_term_like_r_and_pingouin():
    # pingouin 0.7.0 (same formula as R mauchly.test) for K6: W 0.028653, chi2 14.56521, dof 14, p 0.49102, eps 0.46653;
    # the first-order chi-square p-value alone would be P(chi2_14 > 14.565) = 0.409
    sph = at.check_sphericity(*K6.T)
    assert sph["W"] == pytest.approx(0.028653, abs=1e-4) and sph["chi2"] == pytest.approx(14.5652, abs=1e-3)
    assert sph["df"] == 14 and sph["greenhouse_geisser_epsilon"] == pytest.approx(0.46653, abs=1e-4)
    assert sph["p_value"] == pytest.approx(0.49102, abs=1e-4)
    assert "second-order" in sph["method"]


@pytest.mark.parametrize("seed", range(5))
def test_sphericity_degenerate_cases_are_detected_despite_rounding(seed):
    rng = np.random.default_rng(seed)
    x, y = rng.normal(50, 10, 12), rng.normal(50, 10, 12)
    # condition 3 = condition 2 + a constant: that difference is the same for every subject
    singular = at.check_sphericity(x, y, y + 0.7)
    assert singular["W"] is None and singular["chi2"] is None and singular["p_value"] is None
    assert singular["greenhouse_geisser_epsilon"] == pytest.approx(0.5)      # lower bound 1/(k − 1)
    assert "same for every subject" in singular["note"]
    # condition means differ, but every subject has the same profile: no subject x condition variation
    shifted = at.check_sphericity(x, x + 1.3, x + 2.7)
    assert shifted["W"] is None and shifted["greenhouse_geisser_epsilon"] is None
    assert "subject × condition" in shifted["note"] and "means may still differ" in shifted["note"]
    # a condition that is the sum of two others is not degenerate in contrast space
    summed = at.check_sphericity(x, y, x + y)
    assert summed["W"] is not None and 0 < summed["p_value"] <= 1
    json.dumps([singular, shifted, summed], allow_nan=False)


@pytest.mark.parametrize("factor", [1e306, 1e-300])
def test_sphericity_does_not_depend_on_the_scale_of_the_data(factor):
    ref = at.check_sphericity(*RM.T)
    res = at.check_sphericity(*(RM * factor).T)        # covariance would overflow / underflow unscaled
    for key in ("W", "chi2", "p_value", "greenhouse_geisser_epsilon", "note"):
        assert res[key] == ref[key]


def test_lists_with_none_are_handled():
    res = at.check_normality([1, None, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    assert res["n"] == 10
    assert type(res["is_normal"]) is bool


def test_cohens_d_negligible_band():
    res = at.effect_size_cohens_d(NORMAL_A, NORMAL_A + 0.05)
    assert res["magnitude"] == "negligible"
    assert abs(res["cohens_d"]) < 0.2
    big = at.effect_size_cohens_d(NORMAL_A, NORMAL_A + 2.0)
    assert big["magnitude"] == "large"
    json.dumps(res)


def test_cli_roundtrip(tmp_path, capsys):
    csv = _csv(tmp_path, "long.csv", arm=["A"] * 30 + ["B"] * 30, y=np.r_[NORMAL_A, NORMAL_B])
    code, out, _ = _cli(capsys, [csv, "--value", "y", "--group", "arm", "--alpha", "0.01"])
    out = json.loads(out)
    assert code == 0
    assert out["group_labels"] == ["A", "B"]
    assert out["design"] == "independent_groups"
    assert out["alpha"] == 0.01                                   # --alpha reaches full_check
    assert out["rows_excluded"] == {"missing_group": 0}
    assert out == json.loads(json.dumps(at.full_check(NORMAL_A, NORMAL_B, alpha=0.01) | {
        "group_labels": ["A", "B"], "rows_excluded": {"missing_group": 0}}))


def test_cli_paired_wiring_matches_the_library(tmp_path, capsys):
    pre, post = NORMAL_A, NORMAL_B
    csv = _csv(tmp_path, "paired.csv", pid=list(range(30)) * 2, t=["1pre"] * 30 + ["2post"] * 30, y=np.r_[pre, post])
    code, out, _ = _cli(capsys, [csv, "--value", "y", "--group", "t", "--paired", "--id", "pid"])
    out = json.loads(out)
    lib = at.full_check(pre, post, paired=True)
    assert code == 0 and out["design"] == "paired_two_groups" and out["group_labels"] == ["1pre", "2post"]
    assert out["normality_tests"] == json.loads(json.dumps(lib["normality_tests"]))


def test_cli_reports_rows_dropped_for_missing_group_or_subject(tmp_path, capsys):
    csv = _csv(tmp_path, "mg.csv", arm=["A"] * 10 + ["B"] * 10 + [None] * 3, y=list(range(10)) * 2 + [1, 2, 3])
    code, out, _ = _cli(capsys, [csv, "--value", "y", "--group", "arm"])
    out = json.loads(out)
    assert code == 0 and out["rows_excluded"]["missing_group"] == 3
    assert any("剔除 3 行" in w for w in out["warnings"])
    assert [t["n"] for t in out["normality_tests"]] == [10, 10]
    ids = [float(i) for i in range(10)] * 2 + [None, None]
    rng = np.random.default_rng(4)
    pid = _csv(tmp_path, "mid.csv", id=ids, t=["pre"] * 10 + ["post"] * 10 + ["pre", "post"],
               y=list(rng.normal(size=20)) + [1.0, 2.0])
    code, out, _ = _cli(capsys, [pid, "--value", "y", "--group", "t", "--paired", "--id", "id"])
    out = json.loads(out)
    assert code == 0 and out["rows_excluded"] == {"missing_group": 0, "missing_id": 2}
    assert out["n_pairs"] == 10 and any("受试者ID列" in w for w in out["warnings"])


def test_cli_subject_with_all_values_missing_is_counted_not_silently_dropped(tmp_path, capsys):
    rng = np.random.default_rng(5)
    y = list(rng.normal(size=20))
    y[0] = y[10] = None                      # subject 0 has no value in either condition
    csv = _csv(tmp_path, "allmiss.csv", id=list(range(10)) * 2, t=["pre"] * 10 + ["post"] * 10, y=y)
    code, out, _ = _cli(capsys, [csv, "--value", "y", "--group", "t", "--paired", "--id", "id"])
    out = json.loads(out)
    assert code == 0 and out["n_pairs"] == 9 and out["n_pairs_dropped"] == 1


@pytest.mark.parametrize("make,argv,needle", [
    (None, ["--alpha", "5"], "参数错误：--alpha"),           # checked before the file is read
    (None, ["--alpha", "nan"], "参数错误：--alpha"),
    ("missing", [], "找不到文件"),
    ("empty", [], "空文件"),
    ("latin1", [], "UTF-8"),
    ("inf", [], "列 'y' 有 1 个无穷值"),                   # names the column, not just the data
    (None, ["--paired"], "--id"),
])
def test_cli_errors_are_one_line_with_exit_2(tmp_path, capsys, make, argv, needle):
    good = _csv(tmp_path, "good.csv", arm=["A"] * 10 + ["B"] * 10, y=list(range(20)))
    path = good
    if make == "missing":
        path = tmp_path / "nope.csv"
    elif make == "empty":
        path = tmp_path / "empty.csv"
        path.write_text("")
    elif make == "latin1":
        path = tmp_path / "latin1.csv"
        path.write_bytes("arm,y\nA\xe9,1\n".encode("latin-1"))
    elif make == "inf":
        path = _csv(tmp_path, "inf.csv", arm=["A"] * 10 + ["B"] * 10, y=list(range(19)) + [float("inf")])
    code, out, err = _cli(capsys, [path, "--value", "y", "--group", "arm"] + argv)
    assert code == 2 and out == ""
    assert needle in err and len(err.strip().splitlines()) == 1 and "Traceback" not in err


def test_cli_non_finite_levene_does_not_crash(tmp_path, capsys):
    csv = _csv(tmp_path, "lev.csv", arm=["A"] * 8 + ["B"] * 8, y=[0, 2] * 4 + [5] * 8)
    code, out, err = _cli(capsys, [csv, "--value", "y", "--group", "arm"])
    assert code == 0 and err == ""
    assert json.loads(out)["homogeneity_test"]["statistic"] is None
