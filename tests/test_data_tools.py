import json
import os
import shlex
import stat
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


# ─── patient split regressions found in the release-6.4 audit ─────────────────────────

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


def _cli_error(capsys, main, argv):
    """A CLI error is one line on stderr with exit status 2, never a traceback."""
    with pytest.raises(SystemExit) as e:
        main(argv)
    err = capsys.readouterr().err.strip()
    assert e.value.code == 2, err
    assert len(err.splitlines()) == 1 and "Traceback" not in err, err
    return err


def test_kfold_zero_is_an_error_and_existing_split_column_is_not_overwritten(tmp_path, capsys):
    csv = tmp_path / "d.csv"
    _one_row_per_patient([0, 1] * 10).to_csv(csv, index=False)
    err = _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--kfold", "0",
                                        "--out-dir", str(tmp_path / "o")])
    assert "k 必须" in err
    df = _one_row_per_patient([0, 1] * 10).assign(split="old")
    with pytest.raises(ValueError, match="已经有 'split' 列"):
        pls.split_patients(df, "patient_id")


# ─── randomisation regressions found in the release-6.4 audit ─────────────────────────

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
def test_bad_cli_input_gives_a_message_not_a_traceback(tmp_path, capsys, args, msg):
    assert msg in _cli_error(capsys, rz.main, ["--n", "20", "--out", str(tmp_path / "x.csv"), *args])
    assert not (tmp_path / "x.csv").exists()


def test_stratum_input_errors_are_explained():
    with pytest.raises(ValueError, match="缺少这些分层"):
        rz.stratified_randomization({"site=A": 10}, {"site": ["A", "B"]}, seed=1)
    with pytest.raises(ValueError, match="重复"):
        rz.stratified_randomization(10, {"site": ["A", "A"]}, seed=1)


# ─── allocation concealment (shared decision D4) and randomisation CLI, follow-up audit ─

def _rz_summary(csv_path):
    return json.loads((csv_path.parent / (csv_path.stem + "_summary.json")).read_text(encoding="utf-8"))


def test_out_is_required_so_the_list_never_lands_in_the_working_directory(capsys):
    assert "--out" in _cli_error(capsys, rz.main, ["--n", "20"])


@pytest.mark.parametrize("sub", [["tools"], ["deep", "er"], []])
def test_list_inside_a_project_folder_is_refused(tmp_path, capsys, sub):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / ".mrp-state.json").write_text("{}", encoding="utf-8")
    out = proj.joinpath(*sub, "allocation.csv")
    err = _cli_error(capsys, rz.main, ["--n", "20", "--out", str(out)])
    assert "项目文件夹" in err and ".mrp-state.json" in err
    assert not out.exists() and not out.with_name("allocation_summary.json").exists()


def test_a_symlink_into_the_project_folder_is_refused_too(tmp_path, capsys):
    proj = tmp_path / "proj"
    (proj / "tools").mkdir(parents=True)
    (proj / ".mrp-state.json").write_text("{}", encoding="utf-8")
    link = tmp_path / "private"
    try:
        os.symlink(proj / "tools", link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    _cli_error(capsys, rz.main, ["--n", "20", "--out", str(link / "allocation.csv")])
    assert not (proj / "tools" / "allocation.csv").exists()


def test_a_symlinked_output_is_never_followed_even_with_force(tmp_path, capsys):
    target = tmp_path / "elsewhere.txt"
    target.write_text("keep\n", encoding="utf-8")
    try:
        os.symlink(target, tmp_path / "alloc.csv")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    assert "符号链接" in _cli_error(capsys, rz.main, ["--n", "20", "--out", str(tmp_path / "alloc.csv"), "--force"])
    assert target.read_text(encoding="utf-8") == "keep\n"


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
def test_list_and_summary_are_owner_only_also_after_force(tmp_path):
    out = tmp_path / "alloc.csv"
    out.write_text("old\n", encoding="utf-8")
    os.chmod(out, 0o644)
    rz.main(["--n", "20", "--out", str(out), "--force"])
    for p in (out, tmp_path / "alloc_summary.json"):
        assert stat.S_IMODE(os.stat(p).st_mode) == 0o600, p


def test_existing_list_is_not_overwritten_without_force(tmp_path, capsys):
    out = tmp_path / "alloc.csv"
    rz.main(["--n", "20", "--out", str(out)])
    seed = _rz_summary(out)["seed"]
    capsys.readouterr()
    assert "--force" in _cli_error(capsys, rz.main, ["--n", "20", "--out", str(out)])
    assert _rz_summary(out)["seed"] == seed                      # the only record of the seed survives
    (tmp_path / "alloc.csv").unlink()                            # a summary alone also blocks the run
    _cli_error(capsys, rz.main, ["--n", "20", "--out", str(out)])
    rz.main(["--n", "20", "--out", str(out), "--force"])
    assert _rz_summary(out)["seed"] != seed


def test_cli_prints_a_concealment_reminder_and_never_the_seed(tmp_path, capsys):
    out = tmp_path / "alloc.csv"
    rz.main(["--n", "50", "--block-sizes", "4,8", "--out", str(out)])
    printed = capsys.readouterr()
    reminder = [line for line in printed.out.splitlines() if line.startswith("[Randomization] Allocation concealment")]
    assert len(reminder) == 1 and "sealed envelopes" in reminder[0]
    summary = _rz_summary(out)
    assert summary["seed_str"] not in printed.out + printed.err
    assert summary["warnings"] and "截断" in printed.err          # 50 cannot be made of blocks of 4 and 8
    console = printed.out + printed.err
    assert "4,8" not in console and "[4, 8]" not in console and "4, 8" not in console  # block sizes stay out


@pytest.mark.parametrize("argv,msg", [
    (["--n", "20", "--strata", "site=A,B"], "--method stratified"),
    (["--n", "20", "--n-per-stratum", "10"], "--method stratified"),
    (["--method", "stratified", "--n", "20", "--n-per-stratum", "8", "--strata", "site=A,B"], "--n-per-stratum"),
    (["--method", "stratified", "--n-per-stratum", "8", "--strata", "site=A,B", "site=C"], "两次"),
    (["--method", "stratified", "--n-per-stratum", "8", "--strata", "=A,B"], "factor=level"),
    (["--method", "simple", "--n", "20", "--block-sizes", "4"], "--block-sizes"),
    (["--n", "20", "--seed", "-1"], "--seed"),
    (["--n", "abc"], "--n"),
])
def test_ignored_or_conflicting_flags_are_errors(tmp_path, capsys, argv, msg):
    assert msg in _cli_error(capsys, rz.main, [*argv, "--out", str(tmp_path / "x.csv")])
    assert not (tmp_path / "x.csv").exists()


def test_summary_records_the_seed_as_text_versions_and_a_working_regenerate_command(tmp_path):
    a = tmp_path / "a.csv"
    rz.main(["--method", "stratified", "--n-per-stratum", "12", "--strata", "site=A,B", "sex=M,F",
             "--arms", "Drug X,Placebo", "--ratio", "1:2", "--block-sizes", "3,6", "--out", str(a)])
    s = _rz_summary(a)
    assert s["seed_str"] == str(s["seed"]) and s["seed"] > 2 ** 53     # a double would lose digits
    assert s["software"]["numpy"] == np.__version__ and len(s["software"]["script_sha256"]) == 64
    argv = shlex.split(s["regenerate"])
    assert argv[:2] == ["python3", "randomization.py"]
    argv = argv[2:]
    argv[argv.index("--out") + 1] = str(tmp_path / "again.csv")
    rz.main(argv)
    assert pd.read_csv(tmp_path / "again.csv").equals(pd.read_csv(a))
    assert pd.read_csv(a)["arm"].value_counts().to_dict() == {"Placebo": 32, "Drug X": 16}   # the ratio is used


def _arms_by_stratum(table):
    return {frozenset(lab.split("|")): grp["arm"].tolist() for lab, grp in table.groupby("stratum")}


def test_existing_strata_keep_their_lists_when_a_centre_is_added_or_factors_reordered():
    base = _arms_by_stratum(rz.stratified_randomization(20, {"sex": ["M", "F"], "site": ["A", "B"]}, seed=123))
    grown = _arms_by_stratum(rz.stratified_randomization(20, {"site": ["A", "B", "C"], "sex": ["M", "F"]}, seed=123))
    assert len(grown) == 6
    for key, arms in base.items():
        assert grown[key] == arms, key
    other_seed = _arms_by_stratum(rz.stratified_randomization(20, {"sex": ["M", "F"], "site": ["A", "B"]}, seed=124))
    assert other_seed != base


def test_strata_streams_are_independent_and_unbiased():
    firsts = np.array([[grp["arm"].iloc[0] == "A" for _, grp in
                        rz.stratified_randomization(4, {"site": list("ABCD")}, seed=s).groupby("stratum")]
                       for s in range(1500)], dtype=float)
    assert np.allclose(firsts.mean(axis=0), 0.5, atol=0.05)
    corr = np.corrcoef(firsts.T)[~np.eye(4, dtype=bool)]
    assert np.abs(corr).max() < 0.1


@pytest.mark.parametrize("seed", range(10))
def test_every_complete_block_follows_the_ratio(seed):
    table = rz.block_randomization(90, arms=("A", "B", "C"), ratio=(1, 1, 2), block_sizes=(4, 8), seed=seed)
    sizes = table.groupby("block").size()
    for b, blk in table.groupby("block"):
        counts = blk["arm"].value_counts().to_dict()
        if b < sizes.index.max():                                   # the last block may be cut (90 % 4 != 0)
            unit = len(blk) // 4
            assert counts == {"A": unit, "B": unit, "C": 2 * unit} and len(blk) in (4, 8)


def test_cli_arguments_reach_the_list(tmp_path):
    """CLI wiring: method, n, arms, ratio, block sizes and strata end up in the written list."""
    out = tmp_path / "ratio.csv"
    rz.main(["--n", "60", "--arms", "Ctl,Trt", "--ratio", "1:2", "--block-sizes", "6", "--out", str(out)])
    t = pd.read_csv(out)
    assert len(t) == 60 and t["arm"].value_counts().to_dict() == {"Ctl": 20, "Trt": 40}
    assert set(t.groupby("block").size()) == {6}
    s = _rz_summary(out)
    assert s["ratio"] == [1, 2] and s["block_sizes"] == [6] and s["method"] == "block"
    out = tmp_path / "simple.csv"
    rz.main(["--method", "simple", "--n", "30", "--arms", "A,B,C", "--out", str(out)])
    t = pd.read_csv(out)
    assert len(t) == 30 and t["block"].isna().all() and set(t["arm"]) <= {"A", "B", "C"}
    out = tmp_path / "strat.csv"
    rz.main(["--method", "stratified", "--n-per-stratum", "8", "--strata", "site=A,B,C", "--out", str(out)])
    t = pd.read_csv(out)
    assert sorted(t["stratum"].unique()) == ["site=A", "site=B", "site=C"]
    assert (t.groupby("stratum").size() == 8).all()


# ─── patient-level split, follow-up audit ────────────────────────────────────────────

def _partition(out, col="split"):
    return frozenset(frozenset(g["patient_id"]) for _, g in out.groupby(col))


def test_continuous_label_split_still_depends_on_the_seed():
    df = _one_row_per_patient(np.random.default_rng(1).lognormal(1.5, 0.7, 200))   # every value distinct
    holdout = {_partition(pls.split_patients(df, "patient_id", "label", seed=s)[0]) for s in range(20)}
    folds = {_partition(pls.kfold_patients(df, "patient_id", "label", k=5, seed=s)[0]) for s in range(20)}
    assert len(holdout) == 20 and len(folds) == 20              # was 5 hold-out splits and 1 k-fold grouping
    _, s = pls.split_patients(df, "patient_id", "label")
    assert any("不分层" in w for w in s["warnings"])


def test_each_patient_has_the_same_chance_of_each_split():
    df = _one_row_per_patient([0] * 21 + [1] * 9)
    test_share = sum((pls.split_patients(df, "patient_id", "label", seed=s)[0]["split"] == "test").to_numpy()
                     for s in range(400)) / 400
    assert np.all(np.abs(test_share - 0.2) < 0.1), test_share


def test_a_one_patient_stratum_lands_in_each_split_with_its_fraction():
    df = _one_row_per_patient([0] * 20 + [1] * 20 + [2])
    dest = pd.Series([pls.split_patients(df, "patient_id", "label", seed=s)[0]["split"].iloc[-1]
                      for s in range(300)]).value_counts(normalize=True)
    for name, share in (("train", 0.6), ("val", 0.2), ("test", 0.2)):
        assert abs(dest.get(name, 0) - share) < 0.08, dest.to_dict()


@pytest.mark.parametrize("labels", [[0] * 10, None])
def test_patients_of_one_stratum_are_shuffled(labels):
    df = _one_row_per_patient(labels if labels is not None else [0] * 10)
    label_col = "label" if labels is not None else None
    parts = {_partition(pls.split_patients(df, "patient_id", label_col, seed=s)[0]) for s in range(60)}
    assert len(parts) > 40                                       # 1260 possible 6/2/2 partitions of 10


def test_split_does_not_depend_on_the_row_order():
    df = _multi_image_dataset()
    a, _ = pls.split_patients(df, "patient_id", "label", seed=5)
    b, _ = pls.split_patients(df.sample(frac=1, random_state=0), "patient_id", "label", seed=5)
    assert a.drop_duplicates("patient_id").set_index("patient_id")["split"].sort_index().equals(
        b.drop_duplicates("patient_id").set_index("patient_id")["split"].sort_index())


def test_rare_label_values_are_reported():
    _, s = pls.split_patients(_one_row_per_patient([0] * 20 + [1] * 20 + [2]), "patient_id", "label")
    assert any("少于集合数" in w and "'2'" in w for w in s["warnings"])


def test_id_spellings_of_one_patient_always_share_a_split():
    ids = [f"P{i:03d}" for i in range(60)]
    df = pd.DataFrame({"patient_id": ids + ["P001 ", "p002", "　P003", "Ｐ００４"], "label": [0, 1] * 32})
    for seed in range(20):
        out, s = pls.split_patients(df, "patient_id", "label", seed=seed)
        assert out.groupby(out["patient_id"].str.strip().str.upper().str.replace("Ｐ００４", "P004"))[
            "split"].nunique().max() == 1
    assert s["n_patients"] == 60 and s["patient_ids"]["patients_with_several_spellings"] == 4
    assert any("不止一种写法" in w for w in s["warnings"])


def test_check_leakage_catches_a_patient_in_two_splits_also_across_spellings():
    df = pd.DataFrame({"patient_id": ["A", "A", "B", "C", "c "], "split": ["train", "test", "val", "train", "val"]})
    assert sorted(pls.check_leakage(df, "patient_id")) == ["a", "c"]
    assert pls.check_leakage(df.iloc[2:4], "patient_id") == []


def test_cli_keeps_leading_zeros_and_lists_id_variants_without_printing_them(tmp_path, capsys):
    csv = tmp_path / "ids.csv"
    csv.write_text("patient_id,label,accession\n0012,1,000123\n12,0,000124\n0012 ,1,000125\n"
                   + "".join(f"{i:04d},{i % 2},{i:06d}\n" for i in range(20, 32)), encoding="utf-8")
    pls.main([str(csv), "--patient-col", "patient_id", "--label-col", "label", "--out-dir", str(tmp_path / "s")])
    printed = capsys.readouterr()
    a = pd.read_csv(tmp_path / "s" / "split_assignment.csv", dtype=str)
    assert a["patient_id"].tolist()[:3] == ["0012", "12", "0012 "] and a["accession"].iloc[0] == "000123"
    summary = json.loads((tmp_path / "s" / "split_summary.json").read_text(encoding="utf-8"))
    assert summary["n_patients"] == 14                           # 0012 and 12 are two patients
    v = pd.read_csv(tmp_path / "s" / "split_id_variants.csv", dtype=str, keep_default_na=False)
    assert sorted(v["patient_id"]) == ["0012", "0012 "]
    assert "0012" not in printed.out + printed.err and "不止一种写法" in printed.err


def test_cli_reads_bom_and_gb18030_files(tmp_path):
    rows = "患者编号,标签\n" + "".join(f"{i:03d},{'阳性' if i % 3 else '阴性'}\n" for i in range(30))
    for name, enc in (("bom.csv", "utf-8-sig"), ("gbk.csv", "gb18030")):
        (tmp_path / name).write_bytes(rows.encode(enc))
        out, s = pls.main([str(tmp_path / name), "--patient-col", "患者编号", "--label-col", "标签",
                           "--out-dir", str(tmp_path / name.split(".")[0])])
        assert s["n_patients"] == 30 and set(s["class_distribution"]["train"]) == {"阳性", "阴性", "rows"}


def test_patient_label_any_uses_numbers_and_rejects_text_labels():
    df = pd.DataFrame({"patient_id": ["1", "1", "2", "2"], "label": ["10", "9", "9", "9"]})
    pt, _ = pls._patient_table(df, "patient_id", "label", "any")
    assert dict(zip(pt["_pid"], pt["_stratum"])) == {"1": 10, "2": 9}   # '9' > '10' as text
    text = pd.DataFrame({"patient_id": [1, 1, 2, 2], "label": ["阳性", "阴性", "阴性", "阴性"]})
    with pytest.raises(ValueError, match="数值标签"):                   # max('阳性', '阴性') == '阴性'
        pls.split_patients(text, "patient_id", "label", patient_label="any")


def test_majority_tie_forms_its_own_stratum():
    df = pd.DataFrame({"patient_id": [1, 1, 2, 3, 3, 3], "label": [0, 1, 1, 0, 0, 1]})
    pt, _ = pls._patient_table(df, "patient_id", "label", "majority")
    assert dict(zip(pt["_pid"], pt["_stratum"])) == {"1": pls.TIE_STRATUM, "2": 1, "3": 0}
    _, s = pls.split_patients(df, "patient_id", "label")
    assert any("平票" in w for w in s["warnings"])


@pytest.mark.parametrize("content,argv,msg", [
    ("", [], "空文件"),
    ("patient_id,label\n", [], "没有任何行"),
    ("patient_id,label\n1,0\n2,1\n", ["--train", "nan"], "有限"),
    ("patient_id,label\n1,0\n2,1\n", ["--kfold", "5", "--train", "0.8"], "--kfold"),
    ("patient_id,label\n1,0\n2,1\n", ["--seed", "-3"], "seed"),
    ("pid,lab\n1,0\n,1\n", ["--label-col", "nolabel"], "没有标签列"),        # columns are checked before content
    ("patient_id,label\n1,0\n  ,1\n", [], "空的"),
    ("patient_id,label\n1,0\n2,1\n", ["--label-col", "label", "--patient-label", "worst"], "--patient-label"),
])
def test_split_cli_errors_are_one_line(tmp_path, capsys, content, argv, msg):
    csv = tmp_path / "in.csv"
    csv.write_text(content, encoding="utf-8")
    col = "pid" if content.startswith("pid") else "patient_id"
    assert msg in _cli_error(capsys, pls.main, [str(csv), "--patient-col", col, *argv,
                                                "--out-dir", str(tmp_path / "o")])
    assert not (tmp_path / "o").exists()


def test_split_cli_missing_file_and_input_as_output(tmp_path, capsys):
    assert "找不到文件" in _cli_error(capsys, pls.main, [str(tmp_path / "nope.csv"), "--patient-col", "x"])
    csv = tmp_path / "split_assignment.csv"
    _one_row_per_patient([0, 1] * 5).to_csv(csv, index=False)
    assert "同名" in _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--out-dir", str(tmp_path)])


def test_split_cli_arguments_reach_the_output(tmp_path):
    """CLI wiring: fractions, seed, k, split column, label column and patient-label rule are passed through."""
    df = _multi_image_dataset(n_patients=100)
    csv = tmp_path / "labels.csv"
    df.to_csv(csv, index=False)
    common = [str(csv), "--patient-col", "patient_id", "--label-col", "label"]
    out, s = pls.main([*common, "--train", "0.5", "--val", "0.3", "--test", "0.2", "--seed", "9",
                       "--split-col", "fold", "--patient-label", "any", "--out-dir", str(tmp_path / "a")])
    assert s["patients_per_split"] == {"train": 50, "val": 30, "test": 20}
    assert s["seed"] == 9 and s["stratified_by"] == "label" and s["patient_label_rule"] == "any"
    written = pd.read_csv(tmp_path / "a" / "split_assignment.csv")
    assert "fold" in written.columns and "split" not in written.columns
    lib, _ = pls.split_patients(pd.read_csv(csv, dtype=str), "patient_id", "label", (0.5, 0.3, 0.2),
                                seed=9, patient_label="any", split_col="fold")
    assert written["fold"].tolist() == lib["fold"].tolist()
    _, s7 = pls.main([*common, "--kfold", "7", "--out-dir", str(tmp_path / "b")])
    assert s7["k"] == 7 and len(s7["patients_per_split"]) == 7
    patients = pd.read_csv(tmp_path / "b" / "split_patients.csv")
    assert patients["patient_id"].is_unique and len(patients) == 100


# ─── second follow-up audit ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("argv,msg", [
    (["--block-sizes", ""], "区组大小"),                       # was silently 4,6
    (["--ratio", ""], "--ratio"),                              # was silently 1:1
])
def test_empty_ratio_or_block_sizes_is_an_error_not_the_default(tmp_path, capsys, argv, msg):
    assert msg in _cli_error(capsys, rz.main, ["--n", "20", *argv, "--out", str(tmp_path / "x.csv")])
    assert not (tmp_path / "x.csv").exists()


@pytest.mark.parametrize("marker", ["study-protocol.md", "analysis-plan.md"])
def test_project_folder_without_state_file_is_still_refused(tmp_path, capsys, marker):
    proj = tmp_path / "fresh"
    proj.mkdir()
    (proj / marker).write_text("# draft\n", encoding="utf-8")
    out = proj / "tools" / "allocation.csv"
    assert marker in _cli_error(capsys, rz.main, ["--n", "20", "--out", str(out)])
    assert not out.exists()


def test_failed_summary_write_leaves_no_list_behind(tmp_path, capsys, monkeypatch):
    real = rz._write_private

    def fail_on_summary(path, text, force):
        if str(path).endswith("_summary.json"):
            raise OSError(28, "No space left on device")
        real(path, text, force)

    monkeypatch.setattr(rz, "_write_private", fail_on_summary)
    out = tmp_path / "alloc.csv"
    assert "没有保留" in _cli_error(capsys, rz.main, ["--n", "20", "--out", str(out)])
    assert not out.exists()                                        # a list without its seed record is removed


def test_stratum_labels_and_ids_do_not_depend_on_the_factor_order():
    a = rz.stratified_randomization(20, {"site": ["A", "B"], "sex": ["M", "F"]}, seed=5)
    b = rz.stratified_randomization(20, {"sex": ["M", "F"], "site": ["A", "B"]}, seed=5)
    assert a.equals(b) and a["stratum"].iloc[0] == "sex=M|site=A"   # was 'site=A|sex=M' vs 'sex=M|site=A'
    c = rz.stratified_randomization(20, {"site": ["B", "A", "C"], "sex": ["F", "M"]}, seed=5)
    m = a.merge(c, on=["stratum", "sequence"], suffixes=("_a", "_c"))  # the documented comparison
    assert len(m) == len(a) and (m["arm_a"] == m["arm_c"]).all()
    n = {"site=A|sex=M": 4, "sex=F|site=A": 6, "site=B|sex=M": 8, "sex=F|site=B": 10}  # labels in any order
    sizes = rz.stratified_randomization(n, {"site": ["A", "B"], "sex": ["M", "F"]}, seed=5).groupby("stratum").size()
    assert sizes.to_dict() == {"sex=F|site=A": 6, "sex=F|site=B": 10, "sex=M|site=A": 4, "sex=M|site=B": 8}
    with pytest.raises(ValueError, match="'\\|'"):
        rz.stratified_randomization(4, {"site": ["A|B", "C"]}, seed=5)


def test_fewer_patients_than_folds_is_an_error_and_an_empty_split_is_reported(tmp_path, capsys):
    three = pd.DataFrame({"patient_id": ["a", "b", "c"], "label": [0, 1, 0]})
    with pytest.raises(ValueError, match="至少 5 名患者"):              # was k=5 with 3 one-patient folds
        pls.kfold_patients(three, "patient_id", None, k=5)
    out, s = pls.split_patients(three.iloc[:2], "patient_id", "label")
    assert s["patients_per_split"] == {"train": 1, "val": 1, "test": 0}  # 'test' was missing
    assert s["rows_per_split"]["test"] == 0 and s["class_distribution"]["test"]["rows"] == 0
    assert any("没有分到任何患者" in w and "test" in w for w in s["warnings"])
    _, ok = pls.split_patients(_one_row_per_patient([0, 1] * 10), "patient_id", "label")
    assert not any("没有分到任何患者" in w for w in ok["warnings"])
    csv = tmp_path / "d.csv"
    three.to_csv(csv, index=False)
    assert "--kfold" in _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--kfold", "5",
                                                      "--out-dir", str(tmp_path / "o")])


def test_cli_keeps_missing_value_codes_as_written_and_counts_them_as_missing(tmp_path, capsys):
    csv = tmp_path / "na.csv"
    csv.write_text("pid,label,note\n" + "".join(f"{i},{i % 2},x\n" for i in range(10))
                   + "11,0,null\n12,NA,n/a\n13,None,\n", encoding="utf-8")
    _, s = pls.main([str(csv), "--patient-col", "pid", "--label-col", "label", "--out-dir", str(tmp_path / "o")])
    lines = (tmp_path / "o" / "split_assignment.csv").read_text(encoding="utf-8").splitlines()
    assert lines[-3].startswith("11,0,null,") and lines[-2].startswith("12,NA,n/a,")   # were '11,0,,' / '12,,,'
    assert lines[-1].startswith("13,None,,")
    labels = set().union(*s["class_distribution"].values()) - {"rows"}
    assert labels == {"0", "1", "None", pls.MISSING_STRATUM}         # NA is missing, 'None' is a category
    ids = tmp_path / "ids.csv"
    ids.write_text("pid,label\n1,0\n2,1\nNA,0\n", encoding="utf-8")
    capsys.readouterr()
    err = _cli_error(capsys, pls.main, [str(ids), "--patient-col", "pid", "--out-dir", str(tmp_path / "o2")])
    assert "缺失值代码" in err and "空的" not in err                   # was '有 1 行是空的'


def test_class_distribution_counts_labels_the_way_the_split_uses_them():
    df = pd.DataFrame({"patient_id": [str(i) for i in range(30)], "label": ["1", "1.0", " 1", "0", "0.0"] * 6})
    _, s = pls.split_patients(df, "patient_id", "label")
    assert set().union(*s["class_distribution"].values()) == {"0", "1", "rows"}   # was 5 classes
    assert sum(d["1"] for d in s["class_distribution"].values()) == 18


def test_western_file_is_flagged_and_written_back_byte_for_byte(tmp_path, capsys):
    rows = "pid,label\n" + "".join(f"{name},{i % 2}\n" for i, name in
                                    enumerate(["Müller", "Zolar", "Abel", "Böhm", "Carl", "Dürr", "Egon", "Fürst"]))
    src = tmp_path / "west.csv"
    src.write_bytes(rows.encode("cp1252"))
    _, s = pls.main([str(src), "--patient-col", "pid", "--out-dir", str(tmp_path / "auto")])
    assert any("cp1252" in w for w in s["warnings"]) and "cp1252" in capsys.readouterr().err
    assert s["input"]["encoding"] == "gb18030"
    written = (tmp_path / "auto" / "split_assignment.csv").read_bytes()
    assert "Müller".encode("cp1252") in written and "Dürr".encode("cp1252") in written   # was UTF-8 'M黮ler'
    _, s = pls.main([str(src), "--patient-col", "pid", "--encoding", "cp1252", "--out-dir", str(tmp_path / "cp")])
    assert not s["warnings"] and s["input"]["encoding"] == "cp1252"
    back = pd.read_csv(tmp_path / "cp" / "split_patients.csv", encoding="cp1252")
    assert sorted(back["pid"]) == sorted(pd.read_csv(src, encoding="cp1252")["pid"])
    assert "--encoding" in _cli_error(capsys, pls.main, [str(src), "--patient-col", "pid", "--encoding", "nope",
                                                         "--out-dir", str(tmp_path / "x")])


def test_utf8_outputs_keep_the_input_bom(tmp_path):
    rows = "患者编号,标签\n" + "".join(f"{i:03d},{i % 2}\n" for i in range(12))
    for name, enc, bom in (("bom.csv", "utf-8-sig", True), ("plain.csv", "utf-8", False)):
        (tmp_path / name).write_bytes(rows.encode(enc))
        pls.main([str(tmp_path / name), "--patient-col", "患者编号", "--out-dir", str(tmp_path / name[:-4])])
        head = (tmp_path / name[:-4] / "split_assignment.csv").read_bytes()[:3]
        assert (head == b"\xef\xbb\xbf") is bom


def test_kfold_cli_uses_the_split_column_name(tmp_path):
    csv = tmp_path / "labels.csv"
    _multi_image_dataset(n_patients=40).to_csv(csv, index=False)
    pls.main([str(csv), "--patient-col", "patient_id", "--kfold", "4", "--split-col", "cv_fold",
              "--out-dir", str(tmp_path / "o")])
    written = pd.read_csv(tmp_path / "o" / "split_assignment.csv")
    assert "cv_fold" in written.columns and "split" not in written.columns
    assert set(written["cv_fold"]) == {"fold_1", "fold_2", "fold_3", "fold_4"}
    assert list(pd.read_csv(tmp_path / "o" / "split_patients.csv").columns) == ["patient_id", "cv_fold"]


def test_stale_id_variants_file_is_removed(tmp_path):
    out_dir = tmp_path / "s"
    with_variants = tmp_path / "a.csv"
    with_variants.write_text("pid,label\nP1,0\np1 ,0\nP2,1\nP3,0\nP4,1\n", encoding="utf-8")
    pls.main([str(with_variants), "--patient-col", "pid", "--out-dir", str(out_dir)])
    assert (out_dir / "split_id_variants.csv").exists()
    clean = tmp_path / "b.csv"
    clean.write_text("pid,label\nP1,0\nP2,1\nP3,0\nP4,1\n", encoding="utf-8")
    _, s = pls.main([str(clean), "--patient-col", "pid", "--out-dir", str(out_dir)])
    assert not (out_dir / "split_id_variants.csv").exists() and s["patient_ids"]["variants_file"] is None


def test_split_fraction_help_says_the_defaults_are_not_a_recommendation(capsys):
    # D3 (MA-1): the validation design comes from the SAP; 0.6 / 0.2 / 0.2 is only a placeholder.
    with pytest.raises(SystemExit) as exc:
        pls.main(["--help"])
    assert exc.value.code == 0
    out = " ".join(capsys.readouterr().out.split())
    assert "not a recommendation" in out and "as the SAP specifies" in out and "hold-out fraction" not in out


# ─── encoding and output writing, third follow-up audit ─────────────────────────────

def _split_cli(tmp_path, name, data, *argv):
    """Run the split CLI on bytes `data`; returns (summary, warnings) of a successful run."""
    src = tmp_path / f"{name}.csv"
    src.write_bytes(data)
    _, s = pls.main([str(src), "--patient-col", "pid", "--out-dir", str(tmp_path / name), *argv])
    return s, s["warnings"]


def _encoding_warnings(warnings):
    return [w for w in warnings if "cp1252" in w or "latin-1" in w or "西文" in w]


def test_chinese_files_with_rare_name_characters_or_a_micro_sign_are_not_flagged(tmp_path):
    names = "pid,lab,姓名,诊断\n" + "".join(f"{1000 + i},{i % 2},{'张喆' if i == 3 else '王伟'},膀胱癌\n" for i in range(30))
    units = "pid,lab,单位\n" + "".join(f"{1000 + i},{i % 2},µmol/L\n" for i in range(30))
    # single-character cells (男 = 'ÄÐ', 女 = 'Å®' in cp1252) beside a rare character
    cells = "pid,lab,sex,exam,note\n" + "".join(f"P{i},{i % 2},{'男女'[i % 2]},B超,{'喆' if i == 2 else 'x'}\n"
                                                for i in range(12))
    blood = "pid,lab,blood\n" + "".join(f"P{i},{i % 2},{t}型\n" for i, t in enumerate(["A", "B", "O", "AB"] * 3))
    for name, data in (("gbk_names", names.encode("gbk")), ("gb_micro", units.encode("gb18030")),
                       ("gbk_cells", cells.encode("gbk")), ("gbk_blood", blood.encode("gbk"))):
        s, w = _split_cli(tmp_path, name, data)
        assert s["input"]["encoding"] == "gb18030" and not _encoding_warnings(w), (name, w)   # was a cp1252 warning
    assert pls._latin_plausible(blood.encode("gbk").decode("cp1252"))   # 'AÐÍ': only the GB18030 reading decides


@pytest.mark.parametrize("text,plausible", [
    ("Müller", True), ("Conceição", True), ("CONCEIÇÃO", True), ("µmol/L 37°C", True),
    ("AÇøB", False),                  # 区 = C7 F8: two letters of mixed case
    ("Müller,ÄÐ,", False),            # 男 alone in a cell: a two-letter run touching no letter
    ("Q·ñ", False),                   # 否 = B7 F1: a symbol in a two-character run
    ("Müller x†", False),             # a lone character that is neither a letter nor a common symbol
    ("5 ± 2", False),                 # no accented letter or symbol inside a word
    ("ÕÅ†´", False),                  # 张喆
])
def test_what_counts_as_plausible_western_text(text, plausible):
    assert pls._latin_plausible(text) is plausible


def test_two_readings_are_the_same_patients_only_when_they_group_the_rows_alike():
    assert pls._same_patients(pd.Series(["a", "A ", "b"]), pd.Series(["x", "X", "y"])) == (2, 2, True)
    assert pls._same_patients(pd.Series(["a", "a", "b", "c"]), pd.Series(["x", "y", "z", "z"]))[2] is False   # 3 and 3
    assert pls._same_patients(pd.Series(["a", "b"]), pd.Series(["x", "X"])) == (2, 1, False)


def _suggested_encodings(warnings):
    import re
    return {m for w in warnings for m in re.findall(r"--encoding ([A-Za-z0-9_-]+)", w)} | \
           {"latin-1" for w in warnings if "latin-1" in w}


def _patients(tmp_path, name):
    rows = pd.read_csv(tmp_path / name / "split_assignment.csv", dtype=str, keep_default_na=False,
                       encoding=json.loads((tmp_path / name / "split_summary.json").read_text(encoding="utf-8"))
                       ["input"]["csv_outputs_encoding"])
    return rows["pid"].map(pls.patient_key)


def test_a_suggested_encoding_never_changes_who_is_one_patient(tmp_path):
    # 李 = C0 EE and 囝 = E0 EE in GBK; read as cp1252 / latin-1 they are 'Àî' and 'àî': one patient.
    gbk = ("pid,lab,姓名\n" + "".join(f"P{i},{i % 2},王伟\n" for i in range(20))
           + "李1,0,张喆\n囝1,1,王伟\n").encode("gbk")
    west = ("pid,lab\n" + "".join(f"{n},{i % 2}\n" for i, n in
                                  enumerate(["Müller", "MÜLLER", "Abel", "Böhm", "Carl", "Dürr"]))).encode("cp1252")
    for name, data in (("gbk", gbk), ("west", west)):
        s, w = _split_cli(tmp_path, name, data)
        groups = _patients(tmp_path, name)
        for enc in _suggested_encodings(w):                     # was: cp1252 (or latin-1) -> 21 instead of 22
            s2, _ = _split_cli(tmp_path, f"{name}_{enc}", data, "--encoding", enc)
            assert s2["n_patients"] == s["n_patients"], (name, enc)
            again = _patients(tmp_path, f"{name}_{enc}")
            assert groups.nunique() == again.nunique() == pd.DataFrame({"a": groups, "b": again}).drop_duplicates().shape[0]
    (warning,) = _encoding_warnings(w)                          # 'west': flagged, but no encoding is suggested
    assert "cp1252" in warning and "6 名" in warning and "5 名" in warning and "--encoding cp1252" not in warning


def test_western_text_with_two_accented_letters_in_a_row_is_flagged(tmp_path):
    rows = "pid,lab\n" + "".join(f"{n},{i % 2}\n" for i, n in enumerate(["Conceição", "Abel", "Carl", "Egon"]))
    s, w = _split_cli(tmp_path, "pt", rows.encode("cp1252"))
    assert s["input"]["encoding"] == "gb18030"
    assert any("--encoding cp1252" in x for x in w), w          # 'çã' read as one GB2312 character: was missed
    s, w = _split_cli(tmp_path, "pt_cp", rows.encode("cp1252"), "--encoding", "cp1252")
    assert not w and s["n_patients"] == 4


def _snapshot(folder):
    return {p.name: p.read_bytes() for p in folder.iterdir()} if folder.exists() else None


def test_an_output_that_cannot_be_written_leaves_the_folder_as_it_was(tmp_path, capsys):
    src = tmp_path / "mu.csv"                       # NFKC('µ') = Greek 'μ', which cp1252 cannot write
    src.write_bytes(("pid,lab\n" + "".join(f"P{i},{i % 2}\n" for i in range(10)) + "µ7,0\nµ7 ,0\n").encode("cp1252"))
    out = tmp_path / "o"
    out.mkdir()
    (out / "split_summary.json").write_text('{"stale": true}', encoding="utf-8")
    (out / "split_assignment.csv").write_text("old\n", encoding="utf-8")
    before = _snapshot(out)
    err = _cli_error(capsys, pls.main, [str(src), "--patient-col", "pid", "--encoding", "cp1252", "--out-dir", str(out)])
    assert _snapshot(out) == before                              # was: new CSVs beside the stale summary
    assert "--output-encoding utf-8" in err and "--encoding（如 utf-8）" not in err
    err = _cli_error(capsys, pls.main, [str(src), "--patient-col", "pid", "--encoding", "cp1252", "--split-col", "划分",
                                        "--out-dir", str(tmp_path / "o2")])
    assert not (tmp_path / "o2").exists() and "--output-encoding utf-8" in err and "--split-col" in err
    _, s = pls.main([str(src), "--patient-col", "pid", "--encoding", "cp1252", "--output-encoding", "utf-8",
                     "--out-dir", str(out)])                     # the suggested fix works
    assert s["input"] == {"encoding": "cp1252", "csv_outputs_encoding": "utf-8"}
    variants = pd.read_csv(out / "split_id_variants.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    assert sorted(variants["pid"]) == ["µ7", "µ7 "] and set(variants["patient_key"]) == {"μ7"}
    assert sorted(p.name for p in out.iterdir()) == sorted(pls.OUTPUT_FILES)
    capsys.readouterr()
    assert "--output-encoding" in _cli_error(capsys, pls.main, [str(src), "--patient-col", "pid",
                                                                "--output-encoding", "nope", "--out-dir", str(out)])


def test_a_failed_write_changes_no_output_file_or_says_which_it_replaced(tmp_path, capsys, monkeypatch):
    import builtins
    csv = tmp_path / "d.csv"
    _one_row_per_patient([0, 1] * 10).to_csv(csv, index=False)
    out = tmp_path / "o"
    pls.main([str(csv), "--patient-col", "patient_id", "--seed", "1", "--out-dir", str(out)])
    before = _snapshot(out)
    capsys.readouterr()

    def disk_full(path, *a, **k):
        if "split_patients" in str(path) or "split_summary" in str(path):
            raise OSError(28, "No space left on device")
        return builtins.open(path, *a, **k)

    monkeypatch.setattr(pls, "open", disk_full, raising=False)
    _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--seed", "2", "--out-dir", str(out)])
    assert _snapshot(out) == before                              # no new assignment beside the old summary, no temp file
    monkeypatch.undo()
    (out / "split_patients.csv").unlink()
    (out / "split_patients.csv").mkdir()                         # a folder where an output goes
    before = _snapshot_files(out)
    assert "split_patients.csv" in _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--seed", "2",
                                                                 "--out-dir", str(out)])
    assert _snapshot_files(out) == before
    (out / "split_patients.csv").rmdir()
    real_replace = os.replace

    def locked(src, dst):                                        # e.g. split_patients.csv open in Excel on Windows
        if str(dst).endswith("split_patients.csv"):
            raise PermissionError(13, "Permission denied")
        real_replace(src, dst)

    monkeypatch.setattr(pls.os, "replace", locked)
    err = _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--out-dir", str(out)])
    assert "已替换 split_assignment.csv" in err and "未替换 split_patients.csv, split_summary.json" in err
    assert not [p.name for p in out.iterdir() if p.name.startswith(".")]   # no temporary file left


def _snapshot_files(folder):
    return {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()} | \
           {p.name: None for p in folder.iterdir() if p.is_dir()}


def test_explicit_utf8_reads_a_file_with_bom(tmp_path):
    src = tmp_path / "bom.csv"
    src.write_bytes(("患者编号,标签\n" + "".join(f"{i:03d},{i % 2}\n" for i in range(12))).encode("utf-8-sig"))
    _, s = pls.main([str(src), "--patient-col", "患者编号", "--encoding", "utf-8", "--out-dir", str(tmp_path / "o")])
    assert s["n_patients"] == 12 and s["input"]["encoding"] == "utf-8"
    assert (tmp_path / "o" / "split_assignment.csv").read_text(encoding="utf-8").startswith("患者编号,标签,split")


@pytest.mark.parametrize("data,enc", [("患者编号\n张三\n".encode("gb18030"), "utf-8"),
                                      (b"pid\nP\x81\n", "cp1252")])
def test_a_file_the_given_encoding_cannot_decode_is_a_one_line_error(tmp_path, capsys, data, enc):
    src = tmp_path / "in.csv"
    src.write_bytes(data)
    err = _cli_error(capsys, pls.main, [str(src), "--patient-col", "pid", "--encoding", enc,
                                        "--out-dir", str(tmp_path / "o")])
    assert f"不能按 {enc} 解码" in err and "--encoding" in err
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize("script,names", [
    ("patient_level_split.py", "split_patients, kfold_patients, check_leakage"),
    ("randomization.py", "simple_randomization, block_randomization, stratified_randomization"),
])
def test_library_example_copies_the_script_instead_of_importing_from_the_plugin(tmp_path, script, names):
    # CG-6: project code never imports from the plugin install path; the docstring's import example
    # copies the file first, and the copy works without the plugin.
    import ast
    import re
    import shutil
    import subprocess
    src = os.path.join(os.path.dirname(__file__), os.pardir, "skills", "data-collection-tools", "scripts", script)
    with open(src, encoding="utf-8") as f:
        doc = ast.get_docstring(ast.parse(f.read()))
    assert "sys.path.insert" not in doc and "CLAUDE_PLUGIN_ROOT\", \".\"" not in doc
    cp = re.search(rf'cp "\$CLAUDE_PLUGIN_ROOT/skills/data-collection-tools/scripts/{re.escape(script)}" (\S+)', doc)
    assert cp, f"{script}: the library example must copy the file first"
    dest = cp.group(1).replace("~/", "")
    target = tmp_path / dest / script if dest in (".", "./") or dest.endswith("/") else tmp_path / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, target)
    imp = re.search(r"^\s*(from (\w+) import .+)$", doc, re.M)
    assert imp and imp.group(2) == target.stem and names in imp.group(1)
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PLUGIN_ROOT", "PYTHONPATH")}
    (target.parent / "run.py").write_text(imp.group(1) + "\nprint('ok')\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "run.py"], cwd=target.parent, env=env, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr


# ─── final round: consoles that cannot show Chinese, a new --out-dir, a stale variants file ───

@pytest.mark.parametrize("console", [{"PYTHONIOENCODING": "cp1252"}, {"PYTHONIOENCODING": "ascii:surrogateescape"},
                                     {"PYTHONUTF8": "0", "LC_ALL": "C", "LANG": "C"}])
def test_a_console_that_cannot_show_chinese_does_not_fail_a_written_split(tmp_path, console):
    import subprocess
    src = tmp_path / "cn.csv"
    src.write_text("pid,lab\n" + "".join(f"P{i},{'阳性' if i % 2 else '阴性'}\n" for i in range(12)) + "p1 ,阳性\n",
                   encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    env.update(console)
    r = subprocess.run([sys.executable, os.path.abspath(pls.__file__), str(src), "--patient-col", "pid",
                        "--label-col", "lab", "--out-dir", str(tmp_path / "o")], capture_output=True, env=env,
                       timeout=120)
    assert r.returncode == 0 and b"Traceback" not in r.stderr, r.stderr     # was: exit 1 after the files were written
    assert b"[Split] wrote" in r.stdout
    assert b"\\u9633\\u6027" in r.stdout or "PYTHONIOENCODING" not in console     # 阳性 as an escape
    assert sorted(p.name for p in (tmp_path / "o").iterdir()) == sorted(pls.OUTPUT_FILES)


def test_a_failed_write_removes_the_out_dir_it_created(tmp_path, capsys, monkeypatch):
    import builtins
    csv = tmp_path / "d.csv"
    _one_row_per_patient([0, 1] * 10).to_csv(csv, index=False)

    def disk_full(path, *a, **k):
        if "split_summary" in str(path):
            raise OSError(28, "No space left on device")
        return builtins.open(path, *a, **k)

    monkeypatch.setattr(pls, "open", disk_full, raising=False)
    new = tmp_path / "new" / "splits"
    _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--out-dir", str(new)])
    assert sorted(p.name for p in tmp_path.iterdir()) == ["d.csv"]          # was: an empty new/splits left behind
    (tmp_path / "kept").mkdir()
    _cli_error(capsys, pls.main, [str(csv), "--patient-col", "patient_id", "--out-dir", str(tmp_path / "kept")])
    assert (tmp_path / "kept").is_dir() and list((tmp_path / "kept").iterdir()) == []   # an existing folder stays


def test_a_partial_move_names_a_stale_id_variants_file(tmp_path, capsys, monkeypatch):
    out = tmp_path / "o"
    with_variants = tmp_path / "a.csv"
    with_variants.write_text("pid,label\nP1,0\np1 ,0\nP2,1\nP3,0\nP4,1\n", encoding="utf-8")
    pls.main([str(with_variants), "--patient-col", "pid", "--out-dir", str(out)])
    clean = tmp_path / "b.csv"
    clean.write_text("pid,label\nP1,0\nP2,1\nP3,0\nP4,1\n", encoding="utf-8")
    capsys.readouterr()
    real_replace = os.replace

    def locked(src, dst):
        if str(dst).endswith("split_patients.csv"):
            raise PermissionError(13, "Permission denied")
        real_replace(src, dst)

    monkeypatch.setattr(pls.os, "replace", locked)
    err = _cli_error(capsys, pls.main, [str(clean), "--patient-col", "pid", "--out-dir", str(out)])
    assert "未替换 split_patients.csv, split_summary.json" in err
    assert "split_id_variants.csv 也还在" in err and (out / "split_id_variants.csv").exists()
