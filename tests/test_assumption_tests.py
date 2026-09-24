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


def test_cli_rejects_text_values_and_duplicate_paired_rows(tmp_path):
    import pandas as pd
    csv = tmp_path / "bad.csv"
    pd.DataFrame({"arm": ["A", "B"] * 10, "y": ["1.2", "未查"] + ["3"] * 18}).to_csv(csv, index=False)
    with pytest.raises(SystemExit, match="不是数字"):
        at.main([str(csv), "--value", "y", "--group", "arm"])
    dup = tmp_path / "dup.csv"
    pd.DataFrame({"id": [1, 1, 1, 2, 2], "t": ["pre", "pre", "post", "pre", "post"],
                  "y": [1.0, 2.0, 3.0, 4.0, 5.0]}).to_csv(dup, index=False)
    with pytest.raises(SystemExit, match="重复记录"):
        at.main([str(dup), "--value", "y", "--group", "t", "--paired", "--id", "id"])


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
    assert res["recommended_test"].startswith("Repeated-measures ANOVA")
    assert res["rank_based_alternative"] == "Friedman + Nemenyi"


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
