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
