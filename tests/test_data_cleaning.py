import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("pandas")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "statistical-analysis", "scripts"))
import data_cleaning as dc  # noqa: E402


def _messy():
    rng = np.random.default_rng(2)
    n = 60
    df = pd.DataFrame({
        "pid": range(n),
        "age": np.r_[rng.integers(30, 80, n - 2), [150, 45]].astype(float),
        "bmi": rng.normal(25, 4, n),
        "sex": rng.choice(["Male", "Female", "male "], n),
        "visit_date": ["2024-01-%02d" % (i % 28 + 1) for i in range(n)],
        "psa": np.r_[rng.lognormal(1, 0.5, n - 1), [400.0]],
    })
    df.loc[5, "bmi"] = np.nan
    df.loc[[7, 8, 9], "psa"] = np.nan
    df.loc[4, "visit_date"] = "not a date"
    df["age"] = df["age"].astype(object)
    df.loc[3, "age"] = "unknown"
    return df


def test_missing_summary_strategies():
    df = _messy()
    ms = dc.missing_summary(df).set_index("variable")
    assert ms.loc["psa", "n_missing"] == 3
    assert ms.loc["psa", "pct_missing"] == 5.0
    assert ms.loc["psa", "suggested_strategy"].startswith("multiple imputation")
    assert ms.loc["bmi", "suggested_strategy"].startswith("complete case")
    assert ms.loc["pid", "suggested_strategy"] == "none"
    assert dc.suggest_missing_strategy(45).startswith("discuss")


def test_detect_outliers_counts_z_iqr_and_range():
    df = _messy()
    out = dc.detect_outliers(df, cols=["psa", "age"], clinical_ranges={"age": (0, 120)}).set_index("variable")
    assert out.loc["psa", "n_iqr"] >= 1 and out.loc["psa", "n_z"] >= 1
    assert out.loc["age", "n_out_of_range"] == 1
    assert out.loc["age", "n"] == 59               # 'unknown' coerced to NaN and ignored


def test_check_types_flags_problems():
    issues = dc.check_types(_messy(), continuous=["age", "bmi"], categorical=["sex"], dates=["visit_date"])
    kinds = {(i["variable"], i["issue"]) for i in issues}
    assert ("age", "non-numeric continuous") in kinds
    assert ("sex", "inconsistent coding") in kinds
    assert ("visit_date", "unparseable dates") in kinds
    assert not any(i["variable"] == "bmi" for i in issues)


def test_apply_cleaning_is_non_destructive_by_default():
    df = _messy()
    clean, actions = dc.apply_cleaning(df)
    assert len(clean) == len(df) and actions == []
    assert list(clean.columns) == list(df.columns)


def test_apply_cleaning_actions_are_logged():
    df = _messy()
    clean, actions = dc.apply_cleaning(
        df, complete_case=["bmi"], winsorize=["psa"], recode={"sex": {"Male": "0", "Female": "1"}},
        continuous=["age"], clinical_ranges={"age": (0, 120)}, drop_out_of_range=True)
    steps = [a["step"] for a in actions]
    assert steps == ["type", "recode", "drop_rows", "winsorize", "complete_case"]
    assert len(clean) == 58                        # 1 out-of-range age + 1 missing bmi removed
    assert clean["psa"].max() < 400
    assert set(clean["sex"].dropna().unique()) <= {"0", "1"}
    assert pd.api.types.is_numeric_dtype(clean["age"])


def test_cli_writes_clean_csv_and_log(tmp_path):
    df = _messy()
    raw = tmp_path / "data.csv"
    df.to_csv(raw, index=False)
    out, log = tmp_path / "data_clean.csv", tmp_path / "data-cleaning-log.md"
    dc.main([str(raw), "--out", str(out), "--log", str(log), "--continuous", "age,bmi,psa",
             "--categorical", "sex", "--dates", "visit_date", "--range", "age=0:120", "--complete-case", "bmi"])
    assert out.exists()
    text = log.read_text(encoding="utf-8")
    for heading in ("# Data Cleaning Log", "## Missing Data", "## Outliers", "## Data Type Corrections",
                    "## Recoding", "## Before vs After Summary"):
        assert heading in text
    assert "complete_case" in text
    assert len(pd.read_csv(out)) == 59
    assert len(pd.read_csv(raw)) == 60             # raw file untouched


def test_cli_refuses_to_overwrite_raw(tmp_path):
    raw = tmp_path / "data.csv"
    _messy().to_csv(raw, index=False)
    with pytest.raises(SystemExit):
        dc.main([str(raw), "--out", str(raw)])
    with pytest.raises(SystemExit):
        dc.main([str(tmp_path / "missing.csv")])
