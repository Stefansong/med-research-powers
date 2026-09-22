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


def test_small_groups_force_non_parametric():
    res = at.full_check([1, 2, 3, 4, 5], [2, 3, 4, 5, 7])
    assert res["all_normal"] is False
    assert res["recommended_test"] == "Mann-Whitney U"
    assert res["warnings"] and "n < 8" in res["warnings"][0]
    assert all(t["is_normal"] is None for t in res["normality_tests"])


def test_normal_groups_get_t_test_and_python_bools():
    res = at.full_check(NORMAL_A, NORMAL_B)
    assert res["recommended_test"] in ("Independent t-test", "Welch's t-test")
    assert type(res["all_normal"]) is bool
    assert type(res["homogeneous"]) is bool
    assert type(res["normality_tests"][0]["is_normal"]) is bool
    json.dumps(res)


def test_paired_length_mismatch_raises():
    with pytest.raises(ValueError, match="长度不等"):
        at.full_check([1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3], paired=True)


def test_paired_filters_incomplete_pairs_before_differencing():
    a = list(NORMAL_A) + [None]
    b = [None] + list(NORMAL_B)
    res = at.full_check(a, b, paired=True)
    assert res["n_pairs"] == 29
    assert res["n_pairs_dropped"] == 2
    assert res["normality_tests"][0]["n"] == 29
    assert res["homogeneity_test"] is None
    json.dumps(res)


def test_paired_more_than_two_groups_skips_levene():
    res = at.full_check(NORMAL_A, NORMAL_B, NORMAL_A + 0.2, paired=True)
    assert res["homogeneity_test"] is None
    assert "Mauchly" in res["homogeneity_note"]
    assert "Greenhouse-Geisser" in res["homogeneity_note"]
    assert res["recommended_test"].startswith("Repeated-measures ANOVA") or res["recommended_test"] == "Friedman + Nemenyi"


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
    import pandas as pd
    df = pd.DataFrame({"arm": ["A"] * 30 + ["B"] * 30, "y": np.r_[NORMAL_A, NORMAL_B]})
    csv = tmp_path / "long.csv"
    df.to_csv(csv, index=False)
    at.main([str(csv), "--value", "y", "--group", "arm"])
    out = json.loads(capsys.readouterr().out)
    assert out["group_labels"] == ["A", "B"]
    assert out["design"] == "independent_groups"
