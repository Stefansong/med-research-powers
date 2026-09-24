import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("pandas")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "data-collection-tools", "scripts"))
import patient_level_split as pls  # noqa: E402
import randomization as rz  # noqa: E402


def _multi_image_dataset(n_patients=120, seed=3):
    rng = np.random.default_rng(seed)
    pids = np.repeat(np.arange(n_patients), rng.integers(1, 6, n_patients))
    return pd.DataFrame({"patient_id": pids,
                         "image": [f"img{i}.png" for i in range(len(pids))],
                         "label": (pids % 3 == 0).astype(int)})


def test_split_has_no_patient_leakage_and_is_reproducible():
    df = _multi_image_dataset()
    out, summary = pls.split_patients(df, "patient_id", "label", seed=42)
    assert summary["leakage_check"]["passed"] is True
    assert pls.check_leakage(out, "patient_id") == []
    assert set(out["split"]) == {"train", "val", "test"}
    assert sum(summary["patients_per_split"].values()) == df["patient_id"].nunique()
    for s in ("train", "val", "test"):
        assert set(summary["class_distribution"][s]) >= {"0", "1", "rows"}
    out2, _ = pls.split_patients(df, "patient_id", "label", seed=42)
    assert out["split"].tolist() == out2["split"].tolist()
    out3, _ = pls.split_patients(df, "patient_id", "label", seed=7)
    assert out["split"].tolist() != out3["split"].tolist()
    json.dumps(summary)


def test_split_is_stratified_by_patient_label():
    df = _multi_image_dataset(n_patients=300)
    out, summary = pls.split_patients(df, "patient_id", "label", fractions=(0.5, 0.25, 0.25), seed=1)
    per_split_pos = out.drop_duplicates("patient_id").groupby("split")["label"].mean()
    assert per_split_pos.max() - per_split_pos.min() < 0.05


def test_kfold_assigns_every_patient_to_one_fold():
    df = _multi_image_dataset()
    out, summary = pls.kfold_patients(df, "patient_id", "label", k=5, seed=42)
    assert summary["k"] == 5
    assert out.groupby("patient_id")["split"].nunique().max() == 1
    assert len(set(out["split"])) == 5


def test_split_bad_inputs():
    df = _multi_image_dataset()
    with pytest.raises(ValueError):
        pls.split_patients(df, "nope")
    with pytest.raises(ValueError):
        pls.split_patients(df, "patient_id", fractions=(0.5, 0.5, 0.5))


def test_split_cli_writes_files(tmp_path):
    df = _multi_image_dataset()
    csv = tmp_path / "labels.csv"
    df.to_csv(csv, index=False)
    pls.main([str(csv), "--patient-col", "patient_id", "--label-col", "label", "--out-dir", str(tmp_path / "splits")])
    summary = json.loads((tmp_path / "splits" / "split_summary.json").read_text(encoding="utf-8"))
    assert summary["leakage_check"]["passed"] is True
    assert (tmp_path / "splits" / "split_assignment.csv").exists()


def test_block_randomization_balances_arms():
    table = rz.block_randomization(48, arms=("Control", "Treatment"), block_sizes=(4, 6), seed=42)
    counts = table["arm"].value_counts()
    assert counts["Control"] == counts["Treatment"] == 24
    assert table["block"].is_monotonic_increasing
    for _, blk in table.groupby("block"):
        assert abs((blk["arm"] == "Control").sum() - (blk["arm"] == "Treatment").sum()) == 0
    again = rz.block_randomization(48, arms=("Control", "Treatment"), block_sizes=(4, 6), seed=42)
    assert table["arm"].tolist() == again["arm"].tolist()


def test_block_randomization_respects_ratio():
    table = rz.block_randomization(60, arms=("A", "B"), ratio=(1, 2), block_sizes=(3, 6), seed=1)
    counts = table["arm"].value_counts()
    assert counts["A"] == 20 and counts["B"] == 40
    with pytest.raises(ValueError):
        rz.block_randomization(60, arms=("A", "B"), ratio=(1, 2), block_sizes=(4,))


def test_stratified_randomization_balances_within_each_stratum():
    table = rz.stratified_randomization(12, {"site": ["A", "B"], "sex": ["M", "F"]}, arms=("A", "B"), seed=42)
    assert table["stratum"].nunique() == 4
    for _, grp in table.groupby("stratum"):
        assert grp["arm"].value_counts().to_dict() == {"A": 6, "B": 6}
    summary = rz.allocation_summary(table)
    assert summary["n_total"] == 48 and summary["per_arm"] == {"A": 24, "B": 24}


def test_simple_randomization_proportions_are_reasonable():
    table = rz.simple_randomization(2000, arms=("A", "B", "C"), ratio=(1, 1, 2), seed=7)
    frac = table["arm"].value_counts(normalize=True)
    assert frac["C"] == pytest.approx(0.5, abs=0.04)
    assert frac["A"] == pytest.approx(0.25, abs=0.04)


def test_randomization_cli(tmp_path):
    out = tmp_path / "alloc.csv"
    rz.main(["--n", "20", "--arms", "A,B", "--method", "block", "--out", str(out)])
    assert out.exists() and (tmp_path / "alloc_summary.json").exists()


# ─── patient split regressions found in the v6.4.0 audit ─────────────────────────

def _one_row_per_patient(labels):
    return pd.DataFrame({"patient_id": np.arange(len(labels)), "label": labels})


def test_split_sizes_match_the_fractions_exactly():
    out, s = pls.split_patients(_one_row_per_patient([0] * 30), "patient_id", None, (0.7, 0.2, 0.1))
    assert s["patients_per_split"] == {"train": 21, "val": 6, "test": 3}   # was 21/5/4 (float floor)


def test_many_small_strata_still_give_proportional_splits():
    labels = np.repeat(np.arange(10), 3)                                   # 10 strata of 3 patients
    _, s = pls.split_patients(_one_row_per_patient(labels), "patient_id", "label", (0.6, 0.2, 0.2))
    assert s["patients_per_split"] == {"train": 18, "val": 6, "test": 6}   # was 10/10/10


def test_continuous_label_does_not_send_everyone_to_test():
    psa = np.round(np.random.default_rng(1).lognormal(1.5, 0.7, 200), 2)
    _, s = pls.split_patients(_one_row_per_patient(psa), "patient_id", "label")
    assert s["patients_per_split"] == {"train": 120, "val": 40, "test": 40}  # was {'test': 200}
    assert any("像连续变量" in w for w in s["warnings"])


def test_stratified_split_keeps_the_class_ratio_within_one_patient():
    labels = [1] * 30 + [0] * 70
    _, s = pls.split_patients(_one_row_per_patient(labels), "patient_id", "label")
    for name, n in (("train", 60), ("val", 20), ("test", 20)):
        assert abs(s["class_distribution"][name]["1"] - 0.3 * n) <= 1


@pytest.mark.parametrize("rule", ["majority", "any"])
def test_missing_labels_never_crash_or_leave_rows_unassigned(rule):
    df = pd.DataFrame({"patient_id": np.repeat(np.arange(40), 2),
                       "label": [np.nan, np.nan] + [1.0, 0.0] * 10 + [0.0, np.nan] * 29})
    out, s = pls.split_patients(df, "patient_id", "label", patient_label=rule)
    assert out["split"].notna().all()
    assert s["leakage_check"]["passed"] is True and s["leakage_check"]["rows_without_split"] == 0
    assert any("没有任何非缺失标签" in w for w in s["warnings"])


def test_kfold_spreads_the_remainder():
    _, s = pls.kfold_patients(_one_row_per_patient([0] * 42), "patient_id", None, k=5)
    sizes = sorted(s["patients_per_split"].values())
    assert sum(sizes) == 42 and sizes[-1] - sizes[0] <= 1                  # was 8/8/8/8/10


def test_kfold_zero_is_an_error_and_existing_split_column_is_not_overwritten(tmp_path):
    csv = tmp_path / "d.csv"
    _one_row_per_patient([0, 1] * 10).to_csv(csv, index=False)
    with pytest.raises(SystemExit, match="k 必须"):
        pls.main([str(csv), "--patient-col", "patient_id", "--kfold", "0", "--out-dir", str(tmp_path / "o")])
    df = _one_row_per_patient([0, 1] * 10).assign(split="old")
    with pytest.raises(ValueError, match="已经有 'split' 列"):
        pls.split_patients(df, "patient_id")


# ─── randomisation regressions found in the v6.4.0 audit ─────────────────────────

def test_cli_draws_an_unpredictable_seed_and_the_summary_regenerates_the_list(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    rz.main(["--n", "40", "--arms", "A,B", "--out", str(a)])
    rz.main(["--n", "40", "--arms", "A,B", "--out", str(b)])
    sa = json.loads((tmp_path / "a_summary.json").read_text(encoding="utf-8"))
    sb = json.loads((tmp_path / "b_summary.json").read_text(encoding="utf-8"))
    assert sa["seed"] != sb["seed"] and sa["seed"] > 10 ** 6 and "secrets" in sa["seed_source"]
    again = tmp_path / "again.csv"
    rz.main(["--n", "40", "--arms", "A,B", "--seed", str(sa["seed"]), "--out", str(again)])
    assert pd.read_csv(again)["arm"].tolist() == pd.read_csv(a)["arm"].tolist()
    assert "study-protocol.md" in sa["concealment_note"]


def test_library_calls_need_an_explicit_seed():
    with pytest.raises(ValueError, match="seed"):
        rz.block_randomization(10)


def test_strata_use_independent_streams():
    strata = {"site": ["A", "B"]}
    t42 = rz.stratified_randomization(40, strata, seed=42)
    t43 = rz.stratified_randomization(40, strata, seed=43)
    s2_of_42 = t42[t42["stratum"] == "site=B"]["arm"].tolist()
    s1_of_43 = t43[t43["stratum"] == "site=A"]["arm"].tolist()
    assert s2_of_42 != s1_of_43                                  # was identical with seed + i


@pytest.mark.parametrize("seed", range(20))
def test_block_lists_end_on_a_complete_block_when_n_allows(seed):
    table = rz.block_randomization(50, arms=("A", "B"), block_sizes=(4, 6), seed=seed)
    assert table["arm"].value_counts().to_dict() == {"A": 25, "B": 25}


@pytest.mark.parametrize("args,msg", [
    (["--ratio", "1.5:1"], "--ratio"),
    (["--block-sizes", ","], "区组大小"),
    (["--block-sizes", "4,x"], "--block-sizes"),
])
def test_bad_cli_input_gives_a_message_not_a_traceback(tmp_path, args, msg):
    with pytest.raises(SystemExit, match=msg):
        rz.main(["--n", "20", "--out", str(tmp_path / "x.csv"), *args])


def test_stratum_input_errors_are_explained():
    with pytest.raises(ValueError, match="缺少这些分层"):
        rz.stratified_randomization({"site=A": 10}, {"site": ["A", "B"]}, seed=1)
    with pytest.raises(ValueError, match="重复"):
        rz.stratified_randomization(10, {"site": ["A", "A"]}, seed=1)
