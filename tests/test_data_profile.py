import hashlib
import json
import os
import sys

import numpy as np
import pytest

pd = pytest.importorskip("pandas")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "statistical-analysis", "scripts"))
import data_profile as dp  # noqa: E402

N = 60
NAMES = [f"测试者{i:02d}" for i in range(N)]
ID_CARDS = [f"11010119800101{i:03d}X" for i in range(N)]      # 18-digit ID-card pattern
PHONES = [f"138001380{i:02d}" for i in range(N)]               # 11-digit mobile pattern
OTHER_COLS = ("patient_id", "age", "psa", "hb", "sex", "surgery_date", "center", "group", "complication")


def _messy_frame():
    rng = np.random.default_rng(7)
    age = [str(int(a)) for a in rng.integers(30, 80, N)]
    age[1] = age[2] = "未查"
    age[3] = "/"
    age[4] = age[5] = "999"
    psa = [f"{x:.2f}" for x in rng.lognormal(1, 0.6, N)]
    psa[6] = psa[7] = "<0.1"
    psa[8] = ">1000"
    psa[9] = "≤5"
    hb = [str(int(x)) for x in rng.normal(130, 12, N)]
    hb[10] = "130g/L"
    hb[11] = "12..5"
    sex = list(rng.choice(["男", "女"], N))
    sex[12] = sex[13] = "男 "
    dates = [f"2024-{i % 12 + 1:02d}-{i % 27 + 1:02d}" for i in range(N)]
    dates[14] = "2024-13-45"
    dates[15] = "昨天"
    return pd.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(40)] + [f"P{i:03d}" for i in range(20)],  # 20 patients twice
        "姓名": NAMES, "身份证号": ID_CARDS, "contact": PHONES,
        "age": age, "psa": psa, "hb": hb, "sex": sex, "surgery_date": dates,
        "center": list(rng.choice(["A院", "B院", "C院"], N)),
        "group": list(rng.choice(["robot", "lap"], N)),
        "recurrence": [1 if i < 12 else 0 for i in range(N)],
        "complication": ["有" if i % 5 == 0 else "无" for i in range(N)],
    })


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gbk_csv(tmp_path):
    path = tmp_path / "data_gbk.csv"
    _messy_frame().to_csv(path, index=False, encoding="gbk")
    return path


def _cols(profile):
    return {c["name"]: c for c in profile["columns"]}


def test_gbk_csv_every_problem_is_found_and_file_untouched(tmp_path):
    path = _gbk_csv(tmp_path)
    before = _sha(path)
    md, js = tmp_path / "data-profile.md", tmp_path / "data-profile.json"
    profile = dp.main([str(path), "--id", "patient_id", "--report", str(md), "--json", str(js)])
    assert _sha(path) == before                                  # data file never modified
    assert sorted(os.listdir(tmp_path)) == sorted(["data_gbk.csv", "data-profile.md", "data-profile.json"])
    assert profile["source"]["encoding"] == "gbk"
    cols = _cols(profile)
    assert "姓名" in cols and profile["n_rows"] == N

    age = cols["age"]                                            # disguised missing
    assert age["type"] == "numeric"
    assert age["disguised_missing"] == {"未查": 2, "/": 1}
    assert age["missing_codes"] == {"999": 2}
    assert age["n_missing_total"] == 5 and age["pct_missing_total"] == round(500 / N, 1)
    assert age["numeric"]["n"] == N - 5

    psa = cols["psa"]                                            # censored strings
    assert psa["censored"]["n"] == 4
    assert {"<0.1", ">1000", "≤5"} <= set(psa["censored"]["examples"])
    assert psa["numeric"]["n"] == N - 4 and "截断值" in psa["numeric_as_text"]["reasons"]

    hb = cols["hb"]                                              # numbers stored as text
    assert hb["numeric_as_text"]["reasons"] == {"带单位": 1, "其他文字": 1}
    assert hb["numeric_as_text"]["units"] == {"g/L": 1}
    assert "#..#" in hb["numeric_as_text"]["examples"]           # the spelling, digits masked
    assert "12..5" not in hb["numeric_as_text"]["examples"]

    d = cols["surgery_date"]                                     # dates
    assert d["type"] == "date" and d["date"]["n_unparseable"] == 2
    assert d["date"]["unparseable_examples"] == ["2024-13-45"]   # a one-off word is only counted
    assert d["date"]["n_unparseable_unshown"] == 1

    assert sorted(map(sorted, cols["sex"]["categorical"]["inconsistent"])) == [sorted(["男", "男 "])]
    assert cols["complication"]["possible_missing_kept"] == {"无": 48}    # "无" kept as a level
    assert cols["complication"]["n_missing_total"] == 0

    ids = profile["id_structure"][0]                             # repeated IDs
    assert (ids["column"], ids["n_ids"], ids["n_ids_multi"], ids["max_rows_per_id"]) == ("patient_id", 40, 20, 2)
    assert [c["column"] for c in profile["clusters"]] == ["center"]

    text = md.read_text(encoding="utf-8")
    assert text.splitlines()[2] == f"> {dp.STATEMENT}。"          # the statement opens the report
    assert "GEE" in text and "混合模型" in text
    assert json.loads(js.read_text(encoding="utf-8"))["columns"][0]["name"] == "patient_id"


def test_privacy_columns_show_name_and_count_but_never_values(tmp_path, capsys):
    path = _gbk_csv(tmp_path)
    md, js = tmp_path / "p.md", tmp_path / "p.json"
    profile = dp.main([str(path), "--report", str(md), "--json", str(js)])
    priv = {x["column"]: x for x in profile["privacy"]}
    assert priv["姓名"]["by_name"] is True
    assert priv["身份证号"]["id_card_hits"] == N
    assert priv["contact"]["phone_hits"] == N and priv["contact"]["by_name"] is False
    outputs = [md.read_text(encoding="utf-8"), js.read_text(encoding="utf-8"), capsys.readouterr().out]
    for text in outputs:
        assert "11010119800101" not in text and "1380013" not in text and "测试者" not in text
        for value in NAMES + ID_CARDS + PHONES:
            assert value not in text
    assert "`身份证号`" in outputs[0] and "18 位身份证号样式" in outputs[0]


def test_outcome_adds_only_its_own_distribution(tmp_path):
    df = _messy_frame()
    df["months"] = [float(i % 30) + 0.5 for i in range(N)]
    plain = dp.profile_dataframe(df)
    with_outcome = dp.profile_dataframe(df, outcome_col="recurrence", time_col="months")
    # nothing outside the outcome section depends on the outcome
    strip = lambda p: json.dumps({k: v for k, v in p.items() if k != "outcomes"}, sort_keys=True, ensure_ascii=False)
    assert strip(plain) == strip(with_outcome)
    assert plain["outcomes"] == []

    o = with_outcome["outcomes"][0]
    assert (o["kind"], o["event_label"], o["events"], o["non_events"], o["minority_count"]) == ("binary", "1", 12, 48, 12)
    assert set(o) == {"column", "n_rows", "n_missing", "n_valid", "kind", "levels", "event_label", "events",
                      "non_events", "minority_count", "numeric", "time", "per_patient", "notes"}
    # 20 patients have two rows: events are also counted per patient (the unit that limits predictors)
    assert o["per_patient"] == {"n_patients": 40, "patients_with_event": 12, "patients_without_event": 28,
                                "n_patients_mixed": 12}
    assert o["time"]["column"] == "months" and o["time"]["n_valid"] == N

    text = dp.render_markdown(with_outcome)
    section = text.split("## 9.")[1].split("## 10.")[0]
    assert "事件（`1`）12 行" in section and "40 名患者中 12 名" in section
    for other in OTHER_COLS:                                     # no other variable next to the outcome
        assert f"`{other}`" not in section
    for forbidden in ("p=", "p 值", "P值", "相关系数", "按结局分组的统计：", "OR="):
        assert forbidden not in text

    yes_no = dp.profile_dataframe(df, outcome_col="complication")["outcomes"][0]
    assert (yes_no["event_label"], yes_no["events"]) == ("有", 12)


def test_xlsx_sheet_choice_and_numbers_typed_as_text(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    import datetime as dt
    wb = openpyxl.Workbook()
    wb.active.title = "说明"
    wb.active.append(["导出说明"])
    ws = wb.create_sheet("2023")
    ws.append(["住院号", "年龄", "手术日期", "死亡"])
    for i in range(30):
        age = "46" if i == 3 else ("不详" if i == 4 else 40 + i)
        ws.append([f"ZY{2023000 + i}", age, dt.datetime(2023, 1 + i % 12, 1 + i % 28), 1 if i % 4 == 0 else 0])
    path = tmp_path / "export.xlsx"
    wb.save(path)
    before = _sha(path)
    profile = dp.main([str(path), "--sheet", "2023", "--outcome", "死亡", "--report", str(tmp_path / "x.md")])
    assert _sha(path) == before
    # the chosen sheet's name (ordinary words / a year) is printed; the other sheets are only counted
    assert (profile["source"]["sheet"], profile["source"]["sheet_index"], profile["source"]["n_sheets"]) == ("2023", 1, 2)
    assert "说明" not in json.dumps(profile["source"], ensure_ascii=False)
    cols = _cols(profile)
    assert cols["年龄"]["numeric_as_text"]["reasons"] == {"以文本格式存储的数字": 1, "伪装缺失（非标准写法）": 1}
    assert cols["年龄"]["disguised_missing"] == {"不详": 1}
    assert cols["手术日期"]["type"] == "date" and cols["手术日期"]["date"]["n_unparseable"] == 0
    assert cols["住院号"]["type"] == "id" and cols["住院号"]["pii"]["by_name"] is True
    assert profile["outcomes"][0]["events"] == 8
    first = dp.main([str(path)])                                 # default = first sheet
    assert first["source"]["sheet"] == "说明"


def test_added_tokens_ranges_and_header_issues(tmp_path):
    path = tmp_path / "bom.csv"
    rows = ["id,creat,creat,"] + [f"{i},{'拒查' if i == 2 else ('待补' if i == 3 else 40 + i * 5)},{i},"
                                  for i in range(1, 31)]
    path.write_text("﻿" + "\n".join(rows) + "\n", encoding="utf-8")
    profile = dp.main([str(path), "--missing-tokens", "拒查,待补", "--range", "creat=30:150"])
    assert profile["source"]["encoding"] == "utf-8（带 BOM）"
    creat = _cols(profile)["creat"]
    assert creat["disguised_missing"] == {"拒查": 1, "待补": 1}
    assert creat["numeric"]["n_out_of_range"] == sum(1 for i in range(1, 31) if i not in (2, 3) and 40 + i * 5 > 150)
    assert any(x.startswith("列名重复：creat") for x in profile["header_issues"])
    assert any("没有列名" in x for x in profile["header_issues"])
    assert profile["missing_tokens"]["added"] == ["拒查", "待补"]


def test_rows_with_extra_or_missing_fields_do_not_shift_columns(tmp_path):
    path = tmp_path / "ragged.csv"
    path.write_text('a,b\n1,2,3\n4,5\n6\n"x,y",7\n', encoding="utf-8")
    profile = dp.main([str(path)])
    assert [c["name"] for c in profile["columns"]] == ["a", "b"]      # pandas would move `a` into the index
    assert _cols(profile)["a"]["n_valid"] == 4 and _cols(profile)["b"]["n_blank"] == 1
    assert any("多于表头" in x for x in profile["header_issues"])
    assert any("少于表头" in x for x in profile["header_issues"])


def test_cli_guards_never_touch_the_data(tmp_path):
    path = _gbk_csv(tmp_path)
    before = _sha(path)
    for argv in ([str(path), "--report", str(path)],               # report over the data file
                 [str(path), "--json", str(tmp_path / "out.csv")],   # data-like extension
                 [str(tmp_path / "missing.csv")],
                 [str(path), "--outcome", "no_such_column"],
                 [str(path), "--time", "age"]):                      # --time without --outcome
        with pytest.raises(SystemExit):
            dp.main(argv)
    with pytest.raises(SystemExit) as exc:
        dp.main(["--help"])
    assert exc.value.code == 0
    assert _sha(path) == before


def test_library_call_on_a_plain_dataframe_is_json_serialisable():
    df = pd.DataFrame({"pid": range(1, 26), "x": [1.5] * 24 + [np.nan], "grp": ["a", "b"] * 12 + [None]})
    profile = dp.profile_dataframe(df)
    json.dumps(profile, ensure_ascii=False)
    cols = _cols(profile)
    assert cols["pid"]["type"] == "id"
    assert cols["x"]["n_missing_total"] == 1 and "常数列" in "".join(cols["x"]["hints"])
    assert cols["grp"]["categorical"]["n_levels"] == 2


# ─── regressions found in the release-6.4 audit ─────────────────────────────────────

def _csv(tmp_path, name, text, encoding="utf-8"):
    path = tmp_path / name
    path.write_bytes(text.encode(encoding))
    return path


def _run(path, *args):
    return dp.main([str(path), *args])


def _error(capsys, *argv):
    """Run the CLI expecting an error: exit status 2 and exactly one line on stderr -> that line."""
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        dp.main([str(a) for a in argv])
    err = capsys.readouterr().err
    assert exc.value.code == 2, exc.value.code
    assert len(err.strip().splitlines()) == 1 and err.startswith("[数据体检]") and "Traceback" not in err, err
    return err


@pytest.mark.parametrize("one,zero", [("1.0", "0.0"), ("1.00", "0.00"), ("01", "00")])
def test_float_coded_binary_outcome_does_not_crash(tmp_path, one, zero):
    rows = ["pid,age,death"] + [f"{i},{50 + i},{one if i < 6 else zero}" for i in range(30)] + ["30,70,"]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid", "--outcome", "death")
    o = profile["outcomes"][0]
    assert (o["event_label"], o["events"], o["non_events"]) == (one, 6, 24)


def test_events_are_also_counted_per_patient(tmp_path):
    rows = ["pid,visit,death"] + [f"{i},{v},{1 if i < 6 else 0}" for i in range(30) for v in range(3)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    md = tmp_path / "p.md"
    profile = _run(path, "--id", "pid", "--outcome", "death", "--report", str(md))
    o = profile["outcomes"][0]
    assert o["events"] == 18                                      # rows
    assert o["per_patient"] == {"n_patients": 30, "patients_with_event": 6, "patients_without_event": 24,
                                "n_patients_mixed": 0}
    section = md.read_text(encoding="utf-8").split("## 9.")[1].split("## 10.")[0]
    assert "按患者计的较少一类（6 名患者）" in section


def test_identifier_values_are_not_printed_even_when_the_name_gives_nothing_away(tmp_path, capsys):
    names = ["刘洋", "吴刚", "王芳", "李娜", "张伟", "陈静", "杨磊", "赵敏", "黄勇", "周杰", "徐丽", "孙强"]
    rows = ["pid,患者,病理号,出生日期,age,复发"]
    for i, n in enumerate(names):
        for v in range(4):
            rows.append(f"{i},{n},{413900 + i},19{50 + i}-03-12,{50 + i},{v % 2}")
    md, js = tmp_path / "p.md", tmp_path / "p.json"
    _run(_csv(tmp_path, "phi.csv", "\n".join(rows) + "\n"), "--id", "pid", "--outcome", "复发",
         "--report", str(md), "--json", str(js))
    outputs = [md.read_text(encoding="utf-8"), js.read_text(encoding="utf-8"), capsys.readouterr().out]
    for text in outputs:
        for value in names + ["413900", "413911", "1950-03-12", "1961-03-12"]:
            assert value not in text, value
    profile = json.loads(outputs[1])
    priv = {x["column"] for x in profile["privacy"]}
    assert {"患者", "病理号", "出生日期"} <= priv and "pid" not in priv and "age" not in priv


def test_patient_level_unique_check_does_not_hide_ordinary_categories(tmp_path):
    rows = ["pid,sex,stage"] + [f"{i},{'男' if i % 2 else '女'},T{i % 4 + 1}" for i in range(40)]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    assert profile["privacy"] == []
    assert _cols(profile)["stage"]["categorical"]["n_levels"] == 4


def test_headerless_csv_is_detected_and_its_first_row_never_becomes_column_names(tmp_path, capsys):
    rows = [f"张{i}明,11010519800101{i:03d}X,139000000{i:02d},{40 + i},{i % 2}" for i in range(30)]
    md = tmp_path / "p.md"
    profile = _run(_csv(tmp_path, "nohdr.csv", "\n".join(rows) + "\n"), "--report", str(md))
    assert profile["n_rows"] == 30
    assert [c["name"] for c in profile["columns"]] == ["列1", "列2", "列3", "列4", "列5"]
    assert any("第一行看起来是数据" in x for x in profile["problems"])
    for text in (md.read_text(encoding="utf-8"), capsys.readouterr().out):
        assert "11010519800101000X" not in text and "13900000000" not in text and "张0明" not in text
    forced = _run(_csv(tmp_path, "years.csv", "id,2019,2020\n1,3,4\n2,5,6\n"))
    assert [c["name"] for c in forced["columns"]] == ["id", "2019", "2020"]      # year columns stay a header


def test_more_disguised_missing_spellings(tmp_path):
    alb = ["未检测", "暂无", "不适用", "待查", "未测定"] * 4 + [f"{35 + i * 0.5:.1f}" for i in range(40)]
    rows = ["alb"] + alb
    col = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n")))["alb"]
    assert col["type"] == "numeric"
    assert sum(col["disguised_missing"].values()) == 20 and col["pct_missing_total"] == 33.3


def test_none_in_a_numeric_column_is_kept_for_confirmation_not_counted_as_missing(tmp_path):
    vals = ["无"] * 40 + [str(200 + 15 * i) for i in range(20)]
    profile = _run(_csv(tmp_path, "d.csv", "输血量ml\n" + "\n".join(vals) + "\n"))
    col = _cols(profile)["输血量ml"]
    assert col["type"] == "numeric"
    assert col["possible_missing_kept"] == {"无": 40} and col["n_missing_total"] == 0
    assert any("可能表示缺失、也可能是真实取值" in x and "输血量ml" in x for x in profile["problems"])
    assert not any(x.startswith("缺失 ≥20%") and "输血量ml" in x for x in profile["problems"])


def test_grouped_ranges_are_categories_not_censored_values(tmp_path):
    rows = ["年龄分组,肿瘤大小,crp"]
    for i in range(60):
        crp = "<0.5" if i % 10 == 0 else f"{1 + i * 0.3:.1f}"
        rows.append(f"{'<60' if i % 2 else '≥60'},{['≤2cm', '2-5cm', '>5cm'][i % 3]},{crp}")
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    cols = _cols(profile)
    for name in ("年龄分组", "肿瘤大小"):
        assert cols[name]["type"] == "categorical" and "censored" not in cols[name]
        assert any("分组区间" in h for h in cols[name]["hints"])
    assert cols["crp"]["censored"]["n"] == 6                       # a real detection limit is still censored


@pytest.mark.parametrize("name,is_cluster", [
    ("center", True), ("site_id", True), ("Study Site", True), ("hospital_name", True), ("中心编号", True),
    ("医院名称", True), ("术者", True), ("读片医生", True), ("批次", True),
    ("hospital_stay", False), ("tumor_site", False), ("surgical_site_infection", False),
    ("中心静脉置管", False), ("中心型肺癌", False), ("医院感染", False), ("读片结果", False),
    ("医师诊断", False), ("physician_diagnosis", False), ("Hospital Number", False),
])
def test_cluster_names(name, is_cluster):
    assert dp._is_cluster_name(name) is is_cluster


@pytest.mark.parametrize("name,is_pii", [
    ("姓名", True), ("name", True), ("patient_name", True), ("Hospital Number", True), ("MRN", True),
    ("出生日期", True), ("DOB", True), ("date_of_birth", True), ("病理号", True), ("受检人", True), ("受试者", True),
    ("brth_dt", True), ("Geburtsdatum", True),
    ("drug_name", False), ("hospital_name", False), ("Unnamed: 2", False), ("PD-L1 mRNA", False),
    ("mRNA_expr", False), ("出生体重", False), ("birth_weight", False), ("tumor_name", False),
])
def test_privacy_names(name, is_pii):
    assert dp._is_pii_name(name) is is_pii


def test_privacy_columns_keep_their_quality_checks(tmp_path):
    rows = ["pid,姓名,x"] + [f"{i},{'未查' if i < 14 else f'某{i}'},{i}" for i in range(40)]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    assert any(x.startswith("伪装缺失") and "姓名" in x for x in profile["problems"])
    assert any(x.startswith("缺失 ≥20%") and "姓名" in x for x in profile["problems"])


def test_full_width_digits_are_flagged(tmp_path):
    vals = ["４５", "５０"] + [str(40 + i) for i in range(30)]
    col = _cols(_run(_csv(tmp_path, "d.csv", "age\n" + "\n".join(vals) + "\n")))["age"]
    assert col["numeric_as_text"]["reasons"].get("全角字符") == 2


def test_unclosed_quote_is_an_error_not_a_silently_short_file(tmp_path, capsys):
    path = _csv(tmp_path, "d.csv", 'a,b\n1,"x\n2,y\n3,z\n')
    assert "引号不配对" in _error(capsys, path)


def test_trailing_blank_rows_are_ignored_and_counted(tmp_path):
    rows = ["a,b"] + [f"{i},{i * 2}" for i in range(10)] + [",", ",", ""]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert profile["n_rows"] == 10 and profile["n_duplicate_rows"] == 0
    assert any("3 行完全空白" in x for x in profile["problems"])


def test_month_first_column_is_read_month_first(tmp_path):
    vals = ["03/25/2024", "04/02/2024", "12/01/2024", "01/15/2024"] * 5
    col = _cols(_run(_csv(tmp_path, "d.csv", "visit_date\n" + "\n".join(vals) + "\n")))["visit_date"]
    assert (col["date"]["min"], col["date"]["max"]) == ("2024-01-15", "2024-12-01")
    assert "同一列混用多种日期写法" not in col["date"]["notes"]


def test_the_outcome_column_is_profiled_like_any_other(tmp_path):
    # round 4: the outcome's own column entry no longer changes with --outcome (all-different 5-digit integers
    # are typed ID by their values either way); its own summary still gives the numeric distribution
    rows = ["cost"] + [str(10000 + 37 * i) for i in range(30)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    plain, profile = _run(path), _run(path, "--outcome", "cost")
    assert _cols(profile)["cost"] == _cols(plain)["cost"] and _cols(profile)["cost"]["type"] == "id"
    o = profile["outcomes"][0]
    assert o["kind"] == "numeric" and o["numeric"]["n"] == 30 and o["numeric"]["min"] == 10000


def test_json_output_is_strict_json(tmp_path):
    rows = ["x"] + ["1e999", "2", "3", "4", "5"]
    js = tmp_path / "p.json"
    _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--json", str(js))
    json.loads(js.read_text(encoding="utf-8"), parse_constant=lambda c: pytest.fail(f"non-JSON constant {c}"))


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="no symlinks")
def test_a_symlinked_report_path_cannot_overwrite_the_data(tmp_path):
    path = _csv(tmp_path, "d.csv", "a\n1\n2\n")
    link = tmp_path / "report.md"
    os.symlink(path, link)
    before = _sha(path)
    with pytest.raises(SystemExit):
        _run(path, "--report", str(link))
    assert _sha(path) == before


def test_skip_rows_for_a_title_row(tmp_path):
    text = "某医院 2024 年数据导出,,\nid,age,sex\n1,50,男\n2,60,女\n"
    profile = _run(_csv(tmp_path, "d.csv", text), "--skip-rows", "1")
    assert [c["name"] for c in profile["columns"]] == ["id", "age", "sex"] and profile["n_rows"] == 2


# ─── regressions found in the release-6.4.1 audit ───────────────────────────────────

# DP-13: all-different whole numbers may be measurements
def test_all_different_whole_numbers_get_a_not_id_hint_and_not_id_restores_the_distribution(tmp_path):
    import random
    rnd = random.Random(1)
    cost, plt_ = rnd.sample(range(10000, 99999), 60), rnd.sample(range(100000, 450000), 60)
    rows = ["pid,住院费用,platelet,age,手术日期"] + [
        f"{i + 1},{cost[i]},{plt_[i]},{40 + i % 30},{40000 + 3 * i}" for i in range(60)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    profile = _run(path)
    cols = _cols(profile)
    for name in ("住院费用", "platelet"):
        assert cols[name]["type"] == "id" and cols[name]["id_source"] == "value"
        assert any("--not-id" in h for h in cols[name]["hints"])
    assert any("--not-id 住院费用,platelet" in x for x in profile["problems"])
    assert cols["age"]["type"] == "numeric"                     # a run of ages is not a sequence number
    assert cols["手术日期"]["type"] == "numeric"                  # a date name: Excel serials, not an ID
    assert any("Excel 日期序列号" in h for h in cols["手术日期"]["hints"])
    fixed = _run(path, "--not-id", "住院费用,platelet")
    cols = _cols(fixed)
    for name in ("住院费用", "platelet"):
        assert cols[name]["type"] == "numeric" and cols[name]["numeric"]["n"] == 60 and cols[name]["pii"] is None
    assert [s["column"] for s in fixed["id_structure"]] == ["pid"]
    assert not any("--not-id" in x for x in fixed["problems"])


def test_a_phone_column_gets_no_not_id_hint(tmp_path):
    rows = ["pid,contact"] + [f"{i + 1},138001380{i:02d}" for i in range(30)]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert _cols(profile)["contact"]["pii"]["phone_hits"] == 30
    assert not any("--not-id" in x for x in profile["problems"])


# DP-14: a variable that merely looks like an ID never groups the outcome or a centre
def _arm_frame():
    return pd.DataFrame({
        "arm_id": [str(1 + i % 2) for i in range(60)],
        "center": ["ABC"[i % 3] for i in range(60)],
        "ssi": ["1" if i % 2 == 0 and i % 4 == 0 else "0" for i in range(60)],    # events only in arm 1
        "age": [str(40 + i % 30) for i in range(60)],
    })


def test_an_id_like_variable_never_groups_the_outcome_or_a_cluster():
    df = _arm_frame()
    plain = dp.profile_dataframe(df)
    with_outcome = dp.profile_dataframe(df, outcome_col="ssi")
    strip = lambda p: json.dumps({k: v for k, v in p.items() if k != "outcomes"}, sort_keys=True, ensure_ascii=False)
    assert strip(plain) == strip(with_outcome)
    assert plain["id_structure"][0]["column"] == "arm_id" and plain["id_structure"][0]["as_patient_id"] is False
    assert [c["column"] for c in plain["clusters"]] == ["center"]
    assert "ids_per_cluster" not in plain["clusters"][0]           # no centre x arm table
    assert with_outcome["outcomes"][0]["per_patient"] is None       # no arm x outcome table
    text = dp.render_markdown(with_outcome)
    assert "个 ID 出现在多个单位" not in text and "每个单位 1–2 个 ID" not in text
    assert "不像患者 ID" in text
    # the same data with a real patient ID: grouping by patient is fine
    df["patient_id"] = [f"P{i // 2:03d}" for i in range(60)]
    grouped = dp.profile_dataframe(df, outcome_col="ssi")
    assert {s["column"]: s["as_patient_id"] for s in grouped["id_structure"]} == {"arm_id": False, "patient_id": True}
    assert "ids_per_cluster" in grouped["clusters"][0] and grouped["outcomes"][0]["per_patient"] is not None


def test_one_column_cannot_take_two_roles(tmp_path, capsys):
    path = _csv(tmp_path, "d.csv", "pid,y,t\n" + "\n".join(f"{i},{i % 2},{i}" for i in range(30)) + "\n")
    for argv in (["--id", "pid", "--outcome", "pid"], ["--outcome", "y", "--cluster", "y"],
                 ["--id", "pid", "--not-id", "pid"], ["--outcome", "y", "--time", "y"]):
        assert "不能同时用于" in _error(capsys, path, *argv)


# DP-16: CLI errors are messages with the tool prefix, never tracebacks or silent no-ops
@pytest.mark.parametrize("make,argv,message", [
    (lambda d: (d.parent / "fake.xlsx").write_text("a,b\n1,2\n", encoding="utf-8"),     # a CSV renamed .xlsx
     ["{tmp}/fake.xlsx"], "不是 Excel 格式"),
    (None, ["{csv}", "--report", "{tmp}/nodir/r.md"], "目录不存在"),
    (None, ["{csv}", "--range", "Age=0:120"], "不在数据中"),
    (None, ["{csv}", "--range", "age=120:0"], "下限大于上限"),
    (None, ["{csv}", "--sheet", "1"], "--sheet 只用于"),
    (None, ["{csv}", "--encoding", "nosuch"], "未知的编码名"),
    (None, ["{csv}", "--report", "{tmp}/x.md", "--json", "{tmp}/x.md"], "同一个文件"),
    (None, ["{csv}", "--report", "{tmp}/notes.md"], "已存在"),
    (lambda d: (d.parent / "s.dta").write_bytes(b"\x00\x01stata"), ["{tmp}/s.dta"], "暂不支持 .dta"),
    (lambda d: (d.parent / "bin.csv").write_bytes(b"\x00\x01\x02abc"), ["{tmp}/bin.csv"], "NUL"),
    (lambda d: (d.parent / "e.csv").write_bytes(b""), ["{tmp}/e.csv"], "空的"),
    (lambda d: (d.parent / "w.csv").write_bytes("a\ncafé\n".encode("latin-1")),
     ["{tmp}/w.csv", "--encoding", "ascii"], "--encoding"),
])
def test_cli_errors_are_clear_messages(tmp_path, capsys, make, argv, message):
    data = _csv(tmp_path, "d.csv", "pid,age\n" + "\n".join(f"{i},{40 + i % 7}" for i in range(30)) + "\n")
    (tmp_path / "notes.md").write_text("my own notes\n", encoding="utf-8")
    if make is not None:
        make(data)
    args = [a.format(csv=data, tmp=tmp_path) for a in argv]
    before = _sha(data)
    assert message in _error(capsys, *args)                      # CLI-1: exit 2, one line on stderr
    assert _sha(data) == before and (tmp_path / "notes.md").read_text(encoding="utf-8") == "my own notes\n"


def test_encoding_or_sep_on_an_xlsx_and_negative_max_levels_are_refused(tmp_path, capsys):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.append(["a"])
    path = tmp_path / "d.xlsx"
    wb.save(path)
    assert "只用于 CSV" in _error(capsys, path, "--encoding", "gbk")
    assert "--max-levels" in _error(capsys, path, "--max-levels", "-1")      # usage errors: one line too
    assert "参数错误" in _error(capsys, path, "--no-such-option")


def test_an_old_excel_file_without_its_reader_is_a_clear_message(tmp_path, capsys):
    path = tmp_path / "old.xls"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 504)
    err = _error(capsys, path)
    assert "xlrd" in err or "损坏" in err


@pytest.mark.skipif(not hasattr(os, "link"), reason="no hard links")
def test_a_hard_linked_report_path_cannot_overwrite_the_data(tmp_path, capsys):
    path = _csv(tmp_path, "d.csv", "a\n1\n2\n")
    link = tmp_path / "report.md"
    os.link(path, link)
    before = _sha(path)
    assert "不能与数据文件同名" in _error(capsys, path, "--report", link)
    assert _sha(path) == before


def test_an_earlier_report_may_be_overwritten_and_unused_ranges_are_reported(tmp_path):
    path = _csv(tmp_path, "d.csv", "pid,sex\n" + "\n".join(f"{i},{'男女'[i % 2]}" for i in range(30)) + "\n")
    md, js = tmp_path / "p.md", tmp_path / "p.json"
    _run(path, "--report", str(md), "--json", str(js))
    profile = _run(path, "--report", str(md), "--json", str(js), "--range", "sex=0:1")   # rerun: allowed
    assert any("--range sex 没有用上" in x for x in profile["problems"])


# DP-17: a Western file decoded as GBK is flagged
def test_cp1252_file_decoded_as_gbk_is_flagged(tmp_path):
    text = "pid,Crea (µmol/L),Temp (°C)\n" + "\n".join(f"{i},{60 + i},36.{i % 10}" for i in range(30)) + "\n"
    path = _csv(tmp_path, "w.csv", text, encoding="cp1252")
    profile = _run(path)
    assert profile["source"]["encoding"] == "gbk"
    assert any("--encoding cp1252" in x for x in profile["problems"])
    fixed = _run(path, "--encoding", "cp1252")
    assert [c["name"] for c in fixed["columns"]] == ["pid", "Crea (µmol/L)", "Temp (°C)"]
    assert "encoding_warning" not in fixed["source"]


def test_real_gbk_gb18030_and_utf16_files_are_read_without_a_warning(tmp_path):
    gbk = _run(_gbk_csv(tmp_path))
    assert gbk["source"]["encoding"] == "gbk" and "encoding_warning" not in gbk["source"]
    rows = "姓名缩写,诊断\n" + "\n".join(f"A{i},𠀀病{i}" for i in range(10)) + "\n"   # 𠀀 is not in GBK
    assert _run(_csv(tmp_path, "g.csv", rows, encoding="gb18030"))["source"]["encoding"] == "gb18030"
    utf16 = _csv(tmp_path, "u.txt", "﻿pid\t肌酐\n1\t80\n2\t95\n", encoding="utf-16-le")
    profile = _run(utf16)
    assert profile["source"]["encoding"] == "utf-16（带 BOM）" and [c["name"] for c in profile["columns"]] == ["pid", "肌酐"]


# DP-19: line breaks in column names never break a report line
def test_line_breaks_in_column_names_are_shown_safely(tmp_path, capsys):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.append(["pid", "肌酐\n(μmol/L)", "结局\r\n(1=死亡)"])
    for i in range(30):
        wb.active.append([i + 1, "未查" if i < 3 else 60 + 2 * i, 1 if i % 5 == 0 else 0])
    path = tmp_path / "nl.xlsx"
    wb.save(path)
    md, js = tmp_path / "p.md", tmp_path / "p.json"
    profile = _run(path, "--outcome", "结局 (1=死亡)", "--range", "肌酐 (μmol/L)=30:150",
                   "--report", str(md), "--json", str(js))
    assert profile["outcomes"][0]["events"] == 6
    assert all("\n" not in x and "\r" not in x for x in profile["problems"])
    assert any("列名里有换行" in x for x in profile["problems"])
    for line in capsys.readouterr().out.splitlines():
        assert line.startswith("[数据体检]")
    text = md.read_text(encoding="utf-8")
    assert "- 伪装缺失：肌酐↵(μmol/L)（未查×3）" in text.splitlines()
    assert json.loads(js.read_text(encoding="utf-8"))["columns"][1]["name"] == "肌酐\n(μmol/L)"   # the real name
    assert _run(path, "--outcome", "结局\r\n(1=死亡)")["outcomes"][0]["column"] == "结局\r\n(1=死亡)"


# DP-20: complete rows count only the analysable columns
def test_complete_rows_ignore_empty_id_privacy_and_remarks_columns(tmp_path):
    rows = ["pid,姓名,age,sex,备注,空列"] + [
        f"{i},某{i},{'' if i == 5 else 40 + i},{'男女'[i % 2]},{'复查' if i == 3 else ''}," for i in range(30)]
    md = tmp_path / "p.md"
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--report", str(md))
    assert profile["n_complete_rows"] == 29
    basis = profile["complete_rows_basis"]
    assert basis["n_columns"] == 2 and set(basis["excluded"]) == {"pid", "姓名", "备注", "空列"}
    assert "只看 2 个可分析列" in md.read_text(encoding="utf-8")


# DP-22: branches the earlier tests never reached
def _edge_frame():
    n = 40
    return pd.DataFrame({
        "pid": [str(i) for i in range(n)],
        "income": ["1,234", "12,345.5"] + [str(100 + i) for i in range(n - 2)],
        "eu": ["3,5", "4,25"] + [str(i) for i in range(n - 2)],
        "hb": ["130g/L", "13g/dL"] + [str(120 + i % 20) for i in range(n - 2)],
        "surg_date": ["2024-01-05", "2024/01/06", "05/03/2024", "03/25/2024"] + ["2024-02-01"] * (n - 4),
        "amb_date": ["03/04/2024", "05/06/2024"] * (n // 2),
        "visit_date": ["2024-01-01"] * (n - 3) + ["45000", "45001", "abc"],
        "grade": ["G1", "G2", "G3"] * 13 + ["G1"],
        "const": ["A"] * n,
        "los": [str(3 + i % 10) for i in range(n)],
        "comment": [f"患者术后恢复良好但是需要长期随访观察第{i}次复查结果无明显异常" for i in range(n)],
        "months": ["x"] * n,
    })


def test_loose_numbers_units_and_date_notes():
    cols = _cols(dp.profile_dataframe(_edge_frame()))
    assert cols["income"]["numeric_as_text"]["reasons"]["千分位逗号"] == 2
    assert cols["eu"]["numeric_as_text"]["reasons"]["逗号作小数点"] == 2
    assert any(h.startswith("同一列出现多种单位") for h in cols["hb"]["hints"])
    assert "同一列混用多种日期写法" in cols["surg_date"]["date"]["notes"]
    assert any("日/月顺序无法从数据判断" in x for x in cols["amb_date"]["date"]["notes"])
    assert any("Excel 日期序列号" in x for x in cols["visit_date"]["date"]["notes"])
    assert cols["visit_date"]["date"]["n_unparseable"] == 3
    assert any("常数列" in h for h in cols["const"]["hints"])
    both = dp.profile_dataframe(pd.DataFrame({"d": ["13/01/2024", "01/13/2024"] * 10}))
    assert "同一列里既有 日/月/年 又有 月/日/年 写法" in _cols(both)["d"]["date"]["notes"]


@pytest.mark.parametrize("outcome,kind,note", [
    ("grade", "categorical", "多分类结局（3 类）"), ("const", "constant", "结局只有一个取值"),
    ("los", "numeric", "只有 10 个不同取值"), ("comment", "text", "自由文本"),
])
def test_outcome_kinds(outcome, kind, note):
    o = dp.profile_dataframe(_edge_frame(), outcome_col=outcome)["outcomes"][0]
    assert o["kind"] == kind and any(note in x for x in o["notes"])
    if kind == "numeric":
        assert o["numeric"]["n"] == 40


def test_time_duplicates_explicit_cluster_and_separators(tmp_path, capsys):
    df = _edge_frame()
    o = dp.profile_dataframe(df, outcome_col="grade", time_col="months")["outcomes"][0]
    assert "随访时间列被识别为分类" in o["time"]["note"]
    p = dp.profile_dataframe(pd.concat([df, df.iloc[:2]]), cluster_cols="grade", id_col="pid")
    assert "完全重复的行 2 行（可能是导出重复）" in p["problems"]
    assert p["clusters"][0]["column"] == "grade" and p["clusters"][0]["ids_per_cluster"]["max"] == 14
    tab = _csv(tmp_path, "t.txt", "a\tb\n1\t2\n3\t4\n")
    assert [c["name"] for c in _run(tab, "--sep", "tab")["columns"]] == ["a", "b"]
    assert "只能是一个字符" in _error(capsys, tab, "--sep", ";;")


def test_a_very_long_cell_is_data_not_a_parse_error(tmp_path):
    path = _csv(tmp_path, "d.csv", "pid,note\n1," + "x" * 200000 + "\n2,short\n")
    profile = _run(path)
    assert profile["n_rows"] == 2


# ─── regressions: detection limits, lab flags, identifiers, headers, quotes, CLI ─────────────

def _outputs(tmp_path, capsys, path, *args):
    """Profile with --report and --json -> (profile, [report, json, terminal])."""
    md, js = tmp_path / "out.md", tmp_path / "out.json"
    for f in (md, js):
        if f.exists():
            f.unlink()
    capsys.readouterr()
    profile = _run(path, *args, "--report", str(md), "--json", str(js))
    return profile, [md.read_text(encoding="utf-8"), js.read_text(encoding="utf-8"), capsys.readouterr().out]


def _assert_hidden(outputs, values):
    for text in outputs:
        for value in values:
            assert str(value) not in text, value


# DPN-1: a lab result mostly below the detection limit is censored, not a grouped variable
def test_values_below_a_detection_limit_stay_censored_however_many_there_are(tmp_path):
    rows = ["pid,crp,il6,年龄组,体重组"]
    for i in range(60):
        crp = "<0.5" if i % 10 else f"{0.6 + i * 0.01:.2f}"                  # 54 of 60 below the limit
        il6 = "<0.1" if i < 40 else (">1000" if i < 45 else f"{2 + i:.1f}")     # lower and upper limit
        rows.append(f"{i},{crp},{il6},{'<60' if i % 2 else '60及以上'},{['<18.5', '18.5-24', '≥24'][i % 3]}")
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n")))
    for name, n_cens in (("crp", 54), ("il6", 45)):
        assert cols[name]["type"] == "numeric" and cols[name]["censored"]["n"] == n_cens
        assert not any("分组区间" in h for h in cols[name]["hints"])
    assert cols["crp"]["numeric"]["n"] == 6
    for name in ("年龄组", "体重组"):                                          # bins: categories
        assert cols[name]["type"] == "categorical" and "censored" not in cols[name]


# DPN-2: abnormal flags are stripped and counted; the number stays a number
def test_lab_abnormal_flags_keep_the_column_numeric(tmp_path, capsys):
    flags = ["↑", " ↓", "H", " L", "*", "(H)", "", "", "", ""]
    vals = [f"{3 + i * 0.02:.2f}{flags[i % 10]}" for i in range(60)]
    path = _csv(tmp_path, "d.csv", "pid,k\n" + "\n".join(f"{i},{v}" for i, v in enumerate(vals)) + "\n")
    profile, outputs = _outputs(tmp_path, capsys, path)
    k = _cols(profile)["k"]
    assert k["type"] == "numeric" and k["numeric"]["n"] == 60 and k["numeric"]["max"] == 4.18
    assert k["numeric_as_text"]["flags"] == {"↑": 6, "↓": 6, "H": 6, "L": 6, "*": 6, "(H)": 6}
    assert not any("多种单位" in h for h in k["hints"])                      # flags are not units
    assert any(x.startswith("数值带异常标记") and "↑×6" in x for x in profile["problems"])
    _assert_hidden(outputs, ["3.00↑", "3.02 ↓"])                             # flags listed, not results


# DPN-2: words in a mostly numeric column are a problem, shown as tokens only
def test_words_in_a_numeric_column_are_listed_as_tokens(tmp_path, capsys):
    vals = ["溶血"] * 15 + ["张三家属拒绝抽血", "12..5"] + [f"{3 + i * 0.02:.2f}" for i in range(43)]
    path = _csv(tmp_path, "d.csv", "pid,k\n" + "\n".join(f"{i},{v}" for i, v in enumerate(vals)) + "\n")
    profile, outputs = _outputs(tmp_path, capsys, path, "--id", "pid")
    k = _cols(profile)["k"]
    assert k["type"] == "numeric" and k["numeric"]["n"] == 43                 # 28% words: still numeric
    assert k["numeric_as_text"]["unrecognised"] == {"n": 17, "examples": [["溶血", 15], ["#..#", 1]], "n_unshown": 1,
                                                    "no_patient_unit": False}
    line = next(x for x in profile["problems"] if x.startswith("数值列里有不是数字"))
    assert "`溶血`×15" in line and "另有 1 种低频写法不显示" in line
    _assert_hidden(outputs, ["张三", "12..5"])
    mixed = ["阴性"] * 35 + [str(i) for i in range(25)]
    p = _run(_csv(tmp_path, "m.csv", "pid,ab\n" + "\n".join(f"{i},{v}" for i, v in enumerate(mixed)) + "\n"))
    assert any(x.startswith("数字与文字混杂") and "ab（约 42% 是数字）" in x for x in p["problems"])


# DPN-3: one row per patient: measurements are never redacted for being all different
def test_measurements_in_one_row_per_patient_data_keep_values_or_their_not_id_hint(tmp_path):
    import random
    rnd = random.Random(5)
    cost = rnd.sample(range(10000, 99999), 60)
    plt_ = [str(rnd.randrange(100000, 450000, 1000)) for _ in range(60)]
    plt_[7] = plt_[8]                                                       # one repeat
    plt2 = rnd.sample(range(100000, 450000), 60)                            # not round
    rows = ["pid,cost,platelet,plt2,crea,weight"] + [
        f"{i},{cost[i]},{plt_[i]},{plt2[i]},{60 + i}{'↑' if i % 3 == 0 else ''},{50 + i * 0.37:.2f}" for i in range(60)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    profile = _run(path, "--id", "pid")
    cols = _cols(profile)
    assert profile["privacy"] == []
    for name in ("crea", "weight", "platelet"):                            # round counts (213000) are counts
        assert cols[name]["type"] == "numeric" and cols[name]["numeric"]["n"] == 60
    for name in ("cost", "plt2"):                                          # record-number-like: ID + hint
        assert cols[name]["type"] == "id" and cols[name]["id_source"] == "value" and cols[name]["pii"] is None
    hint = next(x for x in profile["problems"] if x.startswith("按取值判为 ID"))
    assert "--not-id cost,plt2" in hint
    fixed = _cols(_run(path, "--id", "pid", "--not-id", "cost,plt2"))
    assert fixed["cost"]["numeric"]["n"] == 60 and fixed["plt2"]["numeric"]["n"] == 60


# DP-7: record numbers of mixed length, in one-row and in long tables, are never printed
def test_mixed_length_record_numbers_are_never_printed(tmp_path, capsys):
    import random
    rnd = random.Random(9)
    mrn = [rnd.randrange(10 ** (5 + i % 3), 10 ** (6 + i % 3)) for i in range(40)]
    wide = ["pid,hosp,age"] + [f"{i},{mrn[i]},{40 + i % 30}" for i in range(40)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "w.csv", "\n".join(wide) + "\n"))
    assert _cols(profile)["hosp"]["type"] == "id"
    _assert_hidden(outputs, [min(mrn), max(mrn)])
    long_rows = ["pid,hosp,visit,crea"] + [f"P{i:02d},{mrn[i]},{v},{60 + v}" for i in range(12) for v in range(4)]
    long_path = _csv(tmp_path, "l.csv", "\n".join(long_rows) + "\n")
    for args in (["--id", "pid"], []):                                      # with and without the ID
        profile, outputs = _outputs(tmp_path, capsys, long_path, *args)
        assert _cols(profile)["hosp"]["type"] == "id"
        _assert_hidden(outputs, mrn[:12])
    no_id = ["hosp,visit,crea"] + [f"{mrn[i]},{v},{60 + v}" for i in range(12) for v in range(4)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "n.csv", "\n".join(no_id) + "\n"))
    _assert_hidden(outputs, mrn[:12])


# SEC: a date of birth under other names
@pytest.mark.parametrize("name", ["birthday", "birth_dt", "BirthDay", "PatientDOB", "Birth", "出生年月日", "born"])
def test_date_of_birth_under_other_names_is_hidden(tmp_path, capsys, name):
    rows = [f"pid,{name},x"] + [f"{i},19{50 + i}-03-1{i % 10},{i}" for i in range(30)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert {x["column"] for x in profile["privacy"]} == {name}
    _assert_hidden(outputs, ["1950-03-10", "1979-03-19"])


# SEC: names, addresses, record numbers and e-mail addresses under headers that give nothing away,
# also in a long table without any ID column
def test_identifier_shaped_values_are_hidden_whatever_the_header(tmp_path, capsys):
    cn = ["刘洋", "吴刚", "王芳", "李娜", "张伟", "陈静", "杨磊", "赵敏", "黄勇", "周杰", "徐丽", "孙强"]
    en = ["Smith, John", "Doe, Jane", "Brown, Bob", "Lee, Ann", "Wong, Kim", "Hall, Tom", "King, Amy",
          "Ford, Ian", "Gray, Liz", "Hunt, Max", "Cole, Eve", "Webb, Sam"]
    addr = ["北京市朝阳区建国路88号", "上海市徐汇区漕溪北路12号", "广州市天河区体育西路3号", "南京市鼓楼区中山路1号"]
    rows = ["who,Patient,lives,code,mail,visit,crea"] + [
        f'{cn[i]},"{en[i]}",{addr[i % 4]},ZY{2023000 + i},p{i}@example.org,{v},{60 + v}' for i in range(12) for v in range(4)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    priv = {x["column"]: x for x in profile["privacy"]}
    assert priv["who"]["looks_like"] == ["姓名"] and priv["lives"]["looks_like"] == ["地址"]
    assert priv["code"]["looks_like"] == ["编号"] and priv["mail"]["email_hits"] == 48
    assert priv["Patient"]["by_name"] is True
    assert "visit" not in priv and "crea" not in priv
    _assert_hidden(outputs, cn + en + addr + ["ZY2023000", "p0@example.org"])
    assert any("who（取值像姓名）" in x for x in profile["problems"])


@pytest.mark.parametrize("values", [
    ["高血压", "高血脂", "高尿酸", "黄疸", "白内障"],                       # share a first character
    ["Left Upper", "Left Lower", "Right Upper", "Right Lower", "Right Middle"],
    ["胸外科", "心内科", "骨科", "妇科", "儿科"],
    ["江苏省南京市", "浙江省杭州市", "南京市鼓楼区", "上海市", "广州市"],      # no street: not an address
])
def test_ordinary_categories_are_not_taken_for_names_or_addresses(values):
    df = pd.DataFrame({"pid": [str(i) for i in range(50)], "v": [values[i % 5] for i in range(50)]})
    col = _cols(dp.profile_dataframe(df, id_col="pid"))["v"]
    assert col["pii"] is None and col["categorical"]["n_levels"] == 5


def test_a_surgeon_or_batch_column_with_names_or_codes_is_still_a_cluster():
    df = pd.DataFrame({"pid": [str(i) for i in range(60)],
                       "术者": [["王建国", "李志强", "张明", "刘洋", "陈伟"][i % 5] for i in range(60)],
                       "batch": [f"B20230{i % 5 + 1}" for i in range(60)]})
    p = dp.profile_dataframe(df, id_col="pid")
    assert [c["column"] for c in p["clusters"]] == ["术者", "batch"]
    assert _cols(p)["术者"].get("categorical") is None and _cols(p)["batch"]["pii"] is None


# SEC: remarks are counted, never listed
def test_remarks_are_never_listed(tmp_path, capsys):
    notes = ["家属王芳签字", "复查", "张伟来电", "1", "2"]
    rows = ["pid,备注,comment,x"] + [f"{i},{notes[i % 5]},{['1', '2', '3', '拒绝随访李娜'][i % 4]},{i}" for i in range(40)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert _cols(profile)["备注"]["type"] == "text" and _cols(profile)["comment"]["type"] == "text"
    _assert_hidden(outputs, ["王芳", "张伟", "李娜", "复查"])


# SEC: sheet names that look like a person's name are not printed
def test_sheet_names_that_look_like_names_are_not_printed(tmp_path, capsys):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.title = "张三"
    for name in ("李四", "汇总"):
        wb.create_sheet(name)
    for ws in wb.worksheets:
        ws.append(["pid", "x"])
        for i in range(10):
            ws.append([i, i])
    path = tmp_path / "s.xlsx"
    wb.save(path)
    profile, outputs = _outputs(tmp_path, capsys, path)
    assert profile["source"]["sheet_index"] == 0 and profile["source"]["n_sheets"] == 3
    _assert_hidden(outputs, ["张三", "李四", "汇总"])                         # other sheets: never named
    assert _run(path, "--sheet", "1")["source"]["sheet_index"] == 1
    assert _run(path, "--sheet", "2")["source"]["sheet"] == "汇总"          # the chosen one, ordinary words
    err = _error(capsys, path, "--sheet", "王五")
    assert "共 3 个工作表" in err and "汇总" not in err and "张三" not in err and "王五" not in err


# DP-8: a headerless file whose first row is mostly words
def test_a_headerless_file_of_words_is_detected(tmp_path, capsys):
    cn = ["刘洋", "吴刚", "王芳", "李娜", "张伟", "陈静", "杨磊", "赵敏", "黄勇", "周杰"]
    rows = [f"{cn[i % 10]},{'男女'[i % 2]},{['高血压', '糖尿病'][i % 2]},{40 + i}" for i in range(30)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert profile["n_rows"] == 30 and [c["name"] for c in profile["columns"]] == ["列1", "列2", "列3", "列4"]
    _assert_hidden(outputs, cn)
    headed = ["性别,诊断,年龄"] + rows[:0] + [f"{'男女'[i % 2]},{['高血压', '糖尿病'][i % 2]},{40 + i}" for i in range(30)]
    assert [c["name"] for c in _run(_csv(tmp_path, "h.csv", "\n".join(headed) + "\n"))["columns"]] == ["性别", "诊断", "年龄"]
    pasted = ["pid,sex"] + [f"{i},{'男女'[i % 2]}" for i in range(10)] + ["pid,sex"] + [f"{i},男" for i in range(10)]
    p = _run(_csv(tmp_path, "p.csv", "\n".join(pasted) + "\n"))
    assert [c["name"] for c in p["columns"]] == ["pid", "sex"]
    assert any("1 行与表头完全相同" in x for x in p["problems"])


# DP-10: lines merged into one cell by a stray quote are reported, never silently dropped
def test_lines_merged_by_a_stray_quote_are_reported(tmp_path):
    text = 'a,b,c\n1,"x,3\n2,y,4\n3,z",5\n4,w,6\n5,"line1\nline2",7\n6,"abc"def,8\n'
    profile = _run(_csv(tmp_path, "d.csv", text))
    assert profile["n_rows"] == 4
    assert any(x.startswith("引号不配对：第 2–4 行") and "共 2 行数据没有单独体检" in x for x in profile["problems"])
    assert any("1 条记录的单元格里有换行（第 6–7 行）" in x for x in profile["problems"])
    assert any(x.startswith("引号用法不规范") and "第 8 行" in x for x in profile["problems"])
    clean = _run(_csv(tmp_path, "c.csv", 'a,b\n1,"x, y"\n2,z\n'))
    assert not any("引号" in x or "换行" in x for x in clean["problems"])


# TQ-1: the value-uniqueness fallback is the only thing between these values and the report
TAGS = [f"q{i}k{i * 7 % 10}#x" for i in range(12)]           # no name / code / address shape


def _tag_table(tmp_path):
    rows = ["pid,tag,visit"] + [f"P{i:02d},{TAGS[i]},{v}" for i in range(12) for v in range(4)]
    return _csv(tmp_path, "tags.csv", "\n".join(rows) + "\n")


def test_one_value_per_patient_is_redacted(tmp_path, capsys):
    profile, outputs = _outputs(tmp_path, capsys, _tag_table(tmp_path), "--id", "pid")
    assert [x["column"] for x in profile["privacy"]] == ["tag"]
    assert profile["privacy"][0]["unique_per_patient"] is True
    _assert_hidden(outputs, TAGS)


def test_the_redaction_test_fails_when_redaction_is_disabled(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(dp, "_redact", lambda col: None)       # mutation: no redaction
    monkeypatch.setattr(dp, "SMALL_CELL_K", 0)                 # ... and no small-cell suppression
    _, outputs = _outputs(tmp_path, capsys, _tag_table(tmp_path), "--id", "pid")
    with pytest.raises(AssertionError):
        _assert_hidden(outputs, TAGS)


# CLI-1: the real process: exit status 2 and one line on stderr, no traceback
@pytest.mark.parametrize("argv", [["{tmp}/missing.csv"], ["{csv}", "--max-levels", "x"], ["{csv}", "--outcome", "nope"]])
def test_cli_errors_exit_2_with_one_line(tmp_path, argv):
    import subprocess
    data = _csv(tmp_path, "d.csv", "pid,age\n1,40\n2,50\n")
    script = os.path.join(os.path.dirname(dp.__file__), "data_profile.py")
    r = subprocess.run([sys.executable, script, *[a.format(tmp=tmp_path, csv=data) for a in argv]],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2 and r.stdout == ""
    assert len(r.stderr.strip().splitlines()) == 1 and r.stderr.startswith("[数据体检]") and "Traceback" not in r.stderr


def test_long_cells_with_digits_or_an_at_sign_are_fast(tmp_path):
    import time
    path = _csv(tmp_path, "d.csv", "pid,note,n\n1," + "x" * 200000 + "@,1\n2," + "9" * 30000 + "x,2\n3,ok,3\n")
    start = time.time()
    assert _run(path)["n_rows"] == 3
    assert time.time() - start < 10


# ─── second-round regressions ────────────────────────────────────────────────────────

# DP-8: a header whose words recur as values ("复发" over 复发 / 未复发) is still a header
@pytest.mark.parametrize("header,make", [
    (["pid", "性别", "吸烟", "复发", "死亡"], lambda i: [f"P{i}", "男女"[i % 2], ["吸烟", "不吸烟"][i % 3 == 0],
                                                    ["复发", "未复发"][i % 4 == 0], ["死亡", "存活"][i % 5 == 0]]),
    (["吸烟", "复发", "死亡", "age", "crea"], lambda i: [["吸烟", "不吸烟"][i % 3 == 0], ["复发", "未复发"][i % 4 == 0],
                                                     ["死亡", "存活"][i % 5 == 0], str(40 + i % 30), f"{60 + i * 0.7:.1f}"]),
    (["Smoker", "Recurrence", "Death"], lambda i: [["Smoker", "Non-smoker"][i % 3 == 0],
                                                   ["Recurrence", "No recurrence"][i % 4 == 0], ["Death", "Alive"][i % 5 == 0]]),
    (["pid", "开放", "腹腔镜", "机器人"], lambda i: [f"P{i}", ["开放", "否"][i % 2], ["腹腔镜", "否"][i % 3 == 0],
                                                 ["机器人", "否"][i % 4 == 0]]),
])
def test_header_words_that_recur_as_values_keep_the_header(tmp_path, header, make):
    rows = [",".join(header)] + [",".join(make(i)) for i in range(60)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    profile = _run(path, "--outcome", header[2])
    assert profile["n_rows"] == 60 and [c["name"] for c in profile["columns"]] == header
    assert profile["outcomes"][0]["column"] == header[2]


def test_a_headerless_file_of_answers_is_still_detected(tmp_path):
    rows = [f"{'男女'[i % 2]},{['冠心病', '糖尿病', '高血压'][i % 3]},{'是否'[i % 4 == 0]}" for i in range(40)]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert profile["n_rows"] == 40 and [c["name"] for c in profile["columns"]] == ["列1", "列2", "列3"]
    headed = ["吸烟,饮酒,高血压"] + [f"{'是否'[i % 2]},{'是否'[i % 3 == 0]},{['高血压', '否'][i % 4 == 0]}" for i in range(40)]
    assert [c["name"] for c in _run(_csv(tmp_path, "h.csv", "\n".join(headed) + "\n"))["columns"]] == ["吸烟", "饮酒", "高血压"]


def test_a_missing_column_after_a_headerless_guess_points_to_header(tmp_path, capsys):
    cn = ["刘洋", "吴刚", "王芳", "李娜", "张伟", "陈静", "杨磊", "赵敏", "黄勇", "周杰"]
    rows = [f"{cn[i % 10]},{'男女'[i % 2]},{40 + i}" for i in range(30)]
    err = _error(capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--outcome", "death")
    assert "不在数据中" in err and "--header" in err and "刘洋" not in err


# DPN-2: a capital L / H next to litres / hours is a unit, so mixed units are still reported
def test_litres_and_hours_are_units_not_lab_flags(tmp_path):
    rows = ["pid,尿量,手术时长,k,vol"] + [
        f"{i},{f'{1 + i % 5 * 0.1:.1f}L' if i % 2 else f'{700 + i}ml'},{f'{2 + i % 3}H' if i % 2 else f'{100 + i}min'},"
        f"{'5.8 H' if i % 5 == 0 else ('3.1 L' if i % 5 == 1 else f'{4 + i % 9 * 0.1:.1f}')},{1 + i % 9 * 0.1:.1f}L"
        for i in range(60)]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    cols = _cols(profile)
    assert cols["尿量"]["numeric_as_text"]["units"] == {"L": 30, "ml": 30} and not cols["尿量"]["numeric_as_text"]["flags"]
    assert cols["手术时长"]["numeric_as_text"]["units"] == {"H": 30, "min": 30}
    for name in ("尿量", "手术时长"):
        assert any(h.startswith("同一列出现多种单位") for h in cols[name]["hints"])
    assert cols["vol"]["numeric_as_text"]["units"] == {"L": 60}        # on every value: a unit
    assert cols["k"]["numeric_as_text"]["flags"] == {"H": 12, "L": 12}  # on some values: flags
    line = next(x for x in profile["problems"] if x.startswith("数值带异常标记"))
    assert "k（" in line and "尿量" not in line and "手术时长" not in line and "vol" not in line


# DPN-3: dates in other spellings are dates, never privacy columns
def test_dates_in_other_spellings_are_dates_not_privacy_columns(tmp_path):
    import datetime as dt
    days = [dt.date(2021, 1, 1) + dt.timedelta(days=13 * i) for i in range(60)]
    rows = ["pid,d1,d2,d3,d4,d5"] + [
        f"{i},{d.month}/{d.day}/{d.year % 100:02d},{d.strftime('%d-%b-%Y')},{d.strftime('%d%b%Y').upper()},"
        f"\"{d.strftime('%b %d, %Y')}\",{d.isoformat()} 上午" for i, d in enumerate(days)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    for args in (["--id", "pid"], []):
        profile = _run(path, *args)
        cols = _cols(profile)
        for name in ("d1", "d2", "d3", "d4"):
            assert cols[name]["type"] == "date" and cols[name]["date"]["n_unparseable"] == 0, name
            assert (cols[name]["date"]["min"], cols[name]["date"]["max"]) == (days[0].isoformat(), days[-1].isoformat())
        assert profile["privacy"] == []          # d5: all different, not read as dates, still no identifier


# DPN-3 / DP-7: record numbers in a small table are typed ID, never printed
@pytest.mark.parametrize("n", [5, 8, 15, 19])
def test_record_numbers_in_a_small_table_are_never_printed(tmp_path, capsys, n):
    import random
    rnd = random.Random(n)
    mrn = [str(rnd.randint(100000, 999999)) for _ in range(n)]
    rows = ["pid,hosp,age"] + [f"P{i:02d},{mrn[i]},{40 + i}" for i in range(n)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    for args in (["--id", "pid"], []):
        profile, outputs = _outputs(tmp_path, capsys, path, *args)
        assert _cols(profile)["hosp"]["type"] == "id"
        assert any("--not-id hosp" in x for x in profile["problems"])
        _assert_hidden(outputs, mrn)


# DP-7: a long table without an ID column, rows not grouped by patient
@pytest.mark.parametrize("order", ["shuffled", "by_date"])
def test_record_numbers_in_an_unsorted_long_table_are_never_printed(tmp_path, capsys, order):
    import random
    rnd = random.Random(8)
    mrns = [str(rnd.randint(100000, 999999)) for _ in range(25)]
    cards = [str(rnd.randint(10 ** 9, 10 ** 10 - 1)) for _ in range(25)]
    recs = [[str(v + 1), m, c, f"2023-0{1 + v}-1{rnd.randint(0, 9)}", f"{rnd.uniform(40, 130):.1f}"]
            for m, c in zip(mrns, cards) for v in range(4)]
    rnd.shuffle(recs)
    if order == "by_date":
        recs.sort(key=lambda r: r[3])
    rows = ["住院次序,hosp,card,visit_date,crea"] + [",".join(r) for r in recs]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert _cols(profile)["hosp"]["type"] == "id" and _cols(profile)["card"]["type"] == "id"
    _assert_hidden(outputs, mrns + [c[:6] for c in cards])
    assert _cols(profile)["crea"]["type"] == "numeric"


def test_round_counts_in_a_long_table_stay_numeric(tmp_path):
    import random
    rnd = random.Random(3)
    rows = ["visit,plt"] + [f"{i % 4},{rnd.randrange(100000, 400000, 1000)}" for i in range(200)]
    assert _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n")))["plt"]["type"] == "numeric"


# SEC-3: masked names, pinyin with the surname in capitals, the header 受检人
def test_masked_and_pinyin_names_are_hidden(tmp_path, capsys):
    cn = ["刘洋", "吴刚", "王芳", "李娜", "张伟", "陈静", "杨磊", "赵敏", "黄勇", "周杰", "徐丽", "孙强", "马超", "朱琳", "胡军"]
    py = ["LIU Yang", "WU Gang", "WANG Fang", "LI Na", "ZHANG Wei", "CHEN Jing", "YANG Lei", "ZHAO Min", "HUANG Yong",
          "ZHOU Jie", "XU Li", "SUN Qiang", "MA Chao", "ZHU Lin", "HU Jun"]
    rows = ["受检人,m1,m2,m3,py,py2,visit,crea"]
    for i in range(15):
        for v in range(3):
            rows.append(f"{cn[i]},{cn[i][0]}*,{cn[i][0]}某某,{cn[i][0]}*{cn[i][-1]},{py[i]},{py[i].upper()},{v},{60 + v}")
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert {x["column"] for x in profile["privacy"]} == {"受检人", "m1", "m2", "m3", "py", "py2"}
    _assert_hidden(outputs, cn + py + [p.upper() for p in py] + [f"{n[0]}*{n[-1]}" for n in cn] + ["`张*`", "张某某"])


# SEC-5: addresses that start with the house number, without city or district; units hint of a privacy column
def test_number_first_and_short_addresses_are_hidden(tmp_path, capsys):
    import random
    rnd = random.Random(11)
    streets_en = ["Baker Street", "Oak Road", "Elm Avenue", "Maple Lane", "High Street", "Park Road"]
    streets_cn = ["建国路", "漕溪北路", "体育西路", "中山路", "人民路", "长江路"]
    en = [f"{rnd.randint(1, 300)} {streets_en[i % 6]}" for i in range(30)]
    cnn = [f"{rnd.randint(1, 300)}号{streets_cn[i % 6]}" for i in range(30)]
    cn3 = [f"{streets_cn[i % 6]}{rnd.randint(1, 300)}号" for i in range(30)]
    rows = ["pid,home,居住地,住址,x"] + [f"{i},{en[i]},{cnn[i]},{cn3[i]},{i % 3}" for i in range(30)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    priv = {x["column"]: x for x in profile["privacy"]}
    assert set(priv) == {"home", "居住地", "住址"} and priv["home"]["looks_like"] == ["地址"]
    _assert_hidden(outputs, en + cnn + cn3 + streets_en + streets_cn)
    long_rows = ["home,visit,crea"] + [f"{cn3[i]},{v},{60 + v}" for i in range(15) for v in range(4)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "l.csv", "\n".join(long_rows) + "\n"))
    assert profile["privacy"][0]["looks_like"] == ["地址"]
    _assert_hidden(outputs, cn3[:15])


def test_a_privacy_column_never_shows_its_units():
    df = pd.DataFrame({"pid": [str(i) for i in range(30)],
                       "住址": [f"{i}号{['甲', '乙', '丙'][i % 3]}" for i in range(30)]})   # number + "unit"
    col = _cols(dp.profile_dataframe(df, id_col="pid"))["住址"]
    assert col["pii"] and not any("单位" in h for h in col["hints"])
    assert "甲" not in dp.render_markdown(dp.profile_dataframe(df, id_col="pid"))


# SEC-6: notes in a date column, names inside free text, names inside sheet names
def test_names_in_date_cells_and_free_text_are_not_printed(tmp_path, capsys):
    rows = ["pid,随访日期,失访原因,reason,x"] + [
        f"{i},{['家属王芳说已去世', '患者张伟未接电话'][i % 2] if i % 10 == 0 else f'2023-{1 + i % 12:02d}-0{1 + i % 9}'},"
        f"{['电话无人接听', '患者刘洋拒绝随访', '搬家', '电话无人接听'][i % 4]},{['moved', 'Mr Smith refused', 'moved', 'died'][i % 4]},{i % 3}"
        for i in range(40)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    _assert_hidden(outputs, ["王芳", "张伟", "刘洋", "Smith"])
    cols = _cols(profile)
    assert cols["随访日期"]["date"]["n_unparseable"] == 4 and cols["随访日期"]["pii"] is None
    assert cols["失访原因"]["pii"]["looks_like"] == ["文字里的姓名"] and cols["reason"]["pii"]
    assert any("失访原因（文字里有姓名）" in x for x in profile["problems"])


@pytest.mark.parametrize("sheet", ["张三-术后", "001张三", "患者张三", "张三(2023)", "J Smith", "Smith J", "ZHANG Wei"])
def test_sheet_names_with_a_name_inside_are_not_printed(tmp_path, capsys, sheet):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.title = "汇总"
    wb.create_sheet(sheet)
    for ws in wb.worksheets:
        ws.append(["pid", "x"])
        for i in range(8):
            ws.append([i, i])
    path = tmp_path / "s.xlsx"
    wb.save(path)
    profile, outputs = _outputs(tmp_path, capsys, path, "--sheet", "1")
    assert profile["source"]["sheet_index"] == 1 and profile["source"]["n_sheets"] == 2
    err = _error(capsys, path, "--sheet", "nosuch")
    _assert_hidden(outputs + [err], [sheet])


# value shapes: categories many patients share are not names or record numbers
def test_categories_shaped_like_names_or_codes_keep_their_levels():
    import random
    rnd = random.Random(5)
    vals = {"herb": ["黄芪", "白术", "金银花", "石斛", "丁香", "陈皮", "杜仲", "龙骨"],
            "country": ["United States", "New Zealand", "South Africa", "Saudi Arabia", "United Kingdom", "Costa Rica",
                        "Sri Lanka", "Hong Kong"],
            "centre": ["Mayo Clinic", "Johns Hopkins", "Cleveland Clinic", "Mass General", "Mount Sinai",
                       "Stanford Health", "Duke Health", "Yale Medicine"],
            "gene": [f"ENSG00000{rnd.randint(100000, 299999)}" for _ in range(8)],
            "lot": [f"LOT2023{rnd.randint(1000, 9999)}" for _ in range(8)],
            "code": [f"K{rnd.randint(10000, 99999)}" for _ in range(8)]}       # code-shaped, shared by many patients
    df = pd.DataFrame({"pid": [str(i) for i in range(60)], **{k: [v[i % 8] for i in range(60)] for k, v in vals.items()}})
    two_rows = pd.concat([df, df]).reset_index(drop=True)                      # each patient on two rows
    for frame, id_col in ((two_rows, "pid"), (df, "pid"), (df.drop(columns="pid"), None)):
        cols = _cols(dp.profile_dataframe(frame, id_col=id_col))
        for name in vals:
            if name == "code" and frame is not two_rows:
                continue          # unless the patient ID groups rows, an all-coded value may be a record number
            assert cols[name]["pii"] is None and cols[name]["categorical"]["n_levels"] == 8, (name, id_col)


def test_names_repeating_over_a_visit_level_id_stay_hidden(tmp_path, capsys):
    cn = ["刘洋", "吴刚", "王芳", "李娜", "张伟", "陈静", "杨磊", "赵敏", "黄勇", "周杰", "徐丽", "孙强", "马超", "朱琳", "胡军"]
    rows = ["visit_id,patient_name_x,crea"] + [f"V{4 * i + v:03d},{cn[i]},{60 + v}" for i in range(15) for v in range(4)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "visit_id")
    assert [x["column"] for x in profile["privacy"]] == ["patient_name_x"]
    _assert_hidden(outputs, cn)


def test_code_shaped_record_numbers_one_row_per_patient_are_privacy_columns(tmp_path, capsys):
    import random
    rnd = random.Random(4)
    hosp = [f"ZY2023{rnd.randint(10000, 99999)}" for _ in range(60)]
    card = [f"S-{rnd.randint(100000, 999999)}" for _ in range(60)]
    rows = ["pid,hosp,card,age"] + [f"P{i:03d},{hosp[i]},{card[i]},{30 + i % 50}" for i in range(60)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    priv = {x["column"]: x for x in profile["privacy"]}
    assert priv["hosp"]["looks_like"] == ["编号"] and priv["card"]["looks_like"] == ["编号"]
    _assert_hidden(outputs, hosp + card)


# DPN-1: whole-number bins ("≤6 / 7 / ≥8", "0 / 1 / ≥2", "0 / 1 / 2 / >2") are categories
def test_whole_number_bins_are_categories(tmp_path):
    rows = ["pid,gleason,ecog,nodes,vl"] + [
        f"{i},{['≤6', '7', '≥8'][0 if i % 10 < 5 else (1 if i % 10 == 5 else 2)]},{['0', '1', '≥2'][i % 3]},"
        f"{['0', '1', '2', '>2'][i % 4]},{'<20' if i % 3 else 20 + i * 7}" for i in range(60)]
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n")))
    for name, n_levels in (("gleason", 3), ("ecog", 3), ("nodes", 4)):
        assert cols[name]["type"] == "categorical" and "censored" not in cols[name], name
        assert cols[name]["categorical"]["n_levels"] == n_levels
    assert cols["vl"]["type"] == "numeric" and cols["vl"]["censored"]["n"] == 40       # a detection limit


# DP-10: a valid cell with a line break and a comma is not reported as merged rows
def test_a_valid_multiline_cell_is_not_reported_as_merged_rows(tmp_path):
    text = 'pid,note,age\n1,"Headache\nnausea, vomiting",30\n2,ok,40\n3,ok,50\n'
    profile = _run(_csv(tmp_path, "d.csv", text))
    assert profile["n_rows"] == 3
    assert not any(x.startswith("引号不配对") for x in profile["problems"])
    assert any("1 条记录的单元格里有换行（第 2–3 行）" in x for x in profile["problems"])


# TQ-1 (M14): the examples of a privacy column that would load as text are never printed
def test_examples_of_a_privacy_column_that_loads_as_text_are_hidden(tmp_path, capsys):
    full = "１３８００１３８０９９"                                  # a phone number in full-width digits
    rows = ["pid,mobile"] + [f"{i},138001380{i:02d}" for i in range(29)] + [f"29,{full}"]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    col = _cols(profile)["mobile"]
    assert col["pii"] and col["numeric_as_text"]["reasons"]["全角字符"] == 1
    _assert_hidden(outputs, [full, "13800138099", "13800138000"])


# ─── third-round regressions: printing is decided by who holds a value, not by its shape ─────

UNCOMMON = ["常建国", "康敏", "洪涛", "温静", "易峰", "岳鹏", "庞丽", "齐磊", "祝红", "倪伟", "鲁军", "葛平"]
WESTERN = ["Mary Ann Smith", "JOHN SMITH", "john smith", "McDonald, Ian", "Jose de la Cruz", "Anne-Marie O'Neil",
           "Lee Ann Kim", "Thomas Lane", "Grace Young", "Peter van Dijk", "OBRIEN SEAN", "Kim Jong Su"]


def _long_table(names, visits, seed, with_id=True, second=None, header="col_a"):
    import random
    rnd = random.Random(seed)
    recs = [[f"P{i:03d}", second[i] if (second and i in second and v % 2) else n, str(v + 1), f"{rnd.uniform(40, 130):.1f}",
             rnd.choice("男女")] for i, n in enumerate(names) for v in range(visits)]
    rnd.shuffle(recs)
    return [(["pid"] if with_id else []) + [header, "visit", "crea", "sex"]] + [r if with_id else r[1:] for r in recs]


@pytest.mark.parametrize("names", [UNCOMMON, WESTERN], ids=["uncommon", "western"])
@pytest.mark.parametrize("with_id", [True, False])
def test_names_no_list_knows_are_still_never_printed(tmp_path, capsys, names, with_id):
    """12 patients x 4 shuffled visits; with --id two patients have a second spelling: a name is held
    by one patient, so it is a small cell (and the column is private) whatever its shape."""
    second = {1: names[1] + "（曾用名）", 5: names[5][0] + "某某"}
    rows = _long_table(names, 4, 7, with_id, second)
    path = _csv(tmp_path, "d.csv", "\n".join(",".join(f'"{x}"' if "," in x else x for x in r) for r in rows) + "\n")
    profile, outputs = _outputs(tmp_path, capsys, path, *(["--id", "pid"] if with_id else []))
    _assert_hidden(outputs, names + list(second.values()))
    assert _cols(profile)["col_a"]["pii"]                               # one value per patient / visit
    sex = _cols(profile)["sex"]["categorical"]
    if with_id:
        assert sex["levels"]                                            # shared values stay visible
    else:                                                               # round 4: no patient unit, no value
        assert not sex["levels"] and sex["values_hidden"] and sex["n_levels"] == 2


def test_tiny_tables_never_show_a_name(tmp_path, capsys):
    for n, with_id in ((4, False), (4, True), (5, False)):
        rows = [["pid", "col_a", "age"] if with_id else ["col_a", "age"]] + \
            [([f"P{i}"] if with_id else []) + [nm, str(40 + i)] for i, nm in enumerate(UNCOMMON[:n])]
        _, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "t.csv", "\n".join(",".join(r) for r in rows) + "\n"),
                              *(["--id", "pid"] if with_id else []))
        _assert_hidden(outputs, UNCOMMON[:n])
    rows = _long_table(UNCOMMON[:4], 3, 3, with_id=False)                 # 4 patients x 3 visits
    _, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "t3.csv", "\n".join(",".join(r) for r in rows) + "\n"))
    _assert_hidden(outputs, UNCOMMON[:4])


@pytest.mark.parametrize("make", [lambda i: f"ZY-2023-{1000 + i * 37:05d}", lambda i: f"HN {482910 + i * 13}",
                                  lambda i: f"{560000 + i * 977}-1", lambda i: f"MR/{23000 + i * 59}",
                                  lambda i: str([872, 10234, 5567801, 4410, 99812, 312, 7788123, 65021, 1203, 880412,
                                                 4567, 23011][i])],
                         ids=["hyphens", "space", "suffix", "slash", "mixed-length"])
def test_record_numbers_of_any_spelling_are_never_printed(tmp_path, capsys, make):
    import random
    rnd = random.Random(2)
    for visits in (1, 4):
        recs = [[make(i), f"{rnd.uniform(40, 130):.1f}"] for i in range(12) for _ in range(visits)]
        rnd.shuffle(recs)
        path = _csv(tmp_path, "r.csv", "ref,crea\n" + "\n".join(",".join(r) for r in recs) + "\n")
        profile, outputs = _outputs(tmp_path, capsys, path)
        _assert_hidden(outputs, [make(i) for i in range(12)])
        assert not (_cols(profile)["ref"].get("numeric") or {}).get("n")      # no min / max of record numbers


def test_phone_and_id_card_numbers_with_separators_are_never_printed(tmp_path, capsys):
    import random
    rnd = random.Random(4)
    phones = ["138-1234-5678", "139 8765 4321", "(010) 6234-5678", "+86 186 1234 5678", "110101 19900307 1234"]
    base = ["失访", "死亡", "拒绝随访", "搬家"]
    rows = ["pid,随访情况,随访日期"] + [
        f"P{i:03d},{f'家属电话{phones[i]}无人接' if i < 5 else rnd.choice(base)},"
        f"{phones[i - 5] if 5 <= i < 10 else f'2023-0{1 + i % 9}-1{i % 9}'}" for i in range(200)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    _assert_hidden(outputs, phones + [p.replace(" ", "") for p in phones])
    cols = _cols(profile)
    assert {lab for lab, _ in cols["随访情况"]["categorical"]["levels"]} == set(base)   # 失访 is a category here
    assert cols["随访情况"]["contact_cells"]["phone"] == 4 and cols["随访情况"]["contact_cells"]["id_card"] == 1
    assert any(x.startswith("单元格里有身份证号/电话号码") and "随访情况" in x for x in profile["problems"])
    assert cols["随访日期"]["type"] == "date" and cols["随访日期"]["date"]["n_unparseable"] == 5


def test_file_sheet_and_column_names_that_name_people_are_not_printed(tmp_path, capsys):
    openpyxl = pytest.importorskip("openpyxl")
    for fn in ("张伟.csv", "常建国_化验单.csv", "John Smith labs.csv", "13812345678.csv"):
        _, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, fn, "age,sex\n40,男\n50,女\n"))
        _assert_hidden(outputs, [fn.split("_")[0].split(" labs")[0].replace(".csv", "")])
    _, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "cohort_2023_clean.csv", "age,sex\n40,男\n50,女\n"))
    assert "cohort_2023_clean.csv" in outputs[0]                           # ordinary words are shown
    wb = openpyxl.Workbook()
    wb.active.title = "常建国"
    for name in ("Mary Ann Smith", "温静复查"):
        wb.create_sheet(name)
    for ws in wb.worksheets:
        ws.append(["pid", "x"])
        for i in range(6):
            ws.append([i, i])
    path = tmp_path / "s.xlsx"
    wb.save(path)
    for args in ([], ["--sheet", "1"], ["--sheet", "温静复查"]):
        _, outputs = _outputs(tmp_path, capsys, path, *args)
        _assert_hidden(outputs, ["常建国", "Mary Ann Smith", "温静"])
    # patients as columns (a transposed lab table); a headerless file whose first row is a patient
    pts = UNCOMMON[:6]
    rows = ["指标," + ",".join(pts)] + [f"{lab}," + ",".join(f"{2 + j * 0.3:.1f}" for j in range(6)) for lab in
                                       ("WBC", "Hb", "PLT", "ALT", "AST", "Cr", "BUN", "K")]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "tr.csv", "\n".join(rows) + "\n"))
    _assert_hidden(outputs, pts)
    assert any("列名像人名" in x for x in profile["problems"])
    rows = ["常建国,肺癌,II期,左,协和医院"] + [f"{n},{['肺癌', '胃癌', '肝癌'][i % 3]},{['I期', 'II期'][i % 2]},{'左右'[i % 2]},"
                                         f"{['协和医院', '人民医院'][i % 2]}" for i, n in enumerate(UNCOMMON[1:] * 3)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "nh.csv", "\n".join(rows) + "\n"))
    assert profile["source"]["header_mode"] == "auto-none"
    _assert_hidden(outputs, UNCOMMON)


def test_text_after_a_censored_value_or_a_number_never_shows(tmp_path, capsys):
    rows = ["pid,crp,weight"] + [f"P{i},{1 + i * 0.3:.1f},{50 + i * 0.5:.1f}" for i in range(50)] + \
        ["P50,<0.5 王芳复查,65王芳", "P51,<0.5,70kg张伟", "P52,>200 见张伟医生意见,72Smith", "P53,小于0.5 患者刘洋拒绝复测,60"]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    _assert_hidden(outputs, ["王芳", "张伟", "刘洋", "Smith"])
    cols = _cols(profile)
    assert cols["crp"]["censored"]["n"] == 4 and cols["crp"]["censored"]["examples"] == ["<0.5"]
    assert cols["weight"]["type"] == "numeric" and not cols["weight"]["numeric_as_text"]["units"]


def test_spelling_variants_and_tokens_obey_small_cells(tmp_path, capsys):
    import random
    rnd = random.Random(6)
    rows = ["pid,reason"] + [f"P{i},{rnd.choice(['Lost', 'Died', 'Moved'])}" for i in range(150)] + \
        ["P150,Mary Ann Smith called", "P151,mary ann smith called", "P152,lost ", "P153,LOST"]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    _assert_hidden(outputs, ["Mary Ann Smith", "mary ann smith"])
    cat = _cols(profile)["reason"]["categorical"]
    assert any({"Lost", "LOST"} <= set(g) for g in cat["inconsistent"])     # variants of a shared value
    assert cat["n_levels_suppressed"] == 2 and "另有 2 个低频取值未显示" in outputs[0]


def test_doctors_are_people_however_many_patients_they_treat(tmp_path, capsys):
    import random
    rnd = random.Random(8)
    rows = ["pid,主治,age"] + [f"P{i:03d},{rnd.choice(['张伟', '李娜', '王芳'])},{30 + i % 50}" for i in range(200)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid")
    _assert_hidden(outputs, ["张伟", "李娜", "王芳"])
    assert [c["column"] for c in profile["clusters"]] == ["主治"]


@pytest.mark.parametrize("name", ["出 生 日 期", "ＤＯＢ", "Ｂｉｒｔｈｄａｙ", "D-O-B", "生年月日", "fecha_nacimiento", "Geb.-Datum",
                                  "Hospital Number"])
def test_identifier_headers_in_other_spellings(tmp_path, capsys, name):
    rows = [f"pid,{name},x"] + [f"{i},19{50 + i}-03-1{i % 10},{i}" for i in range(30)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "d.csv", "\n".join(rows) + "\n"))
    assert _cols(profile)[name]["pii"]
    _assert_hidden(outputs, ["1950-03-10", "1979-03-19"])


def test_measurements_named_after_contact_data_and_eponyms_keep_their_values(tmp_path):
    import random
    rnd = random.Random(9)
    eponyms = ["Hodgkin Lymphoma", "Ewing Sarcoma", "Wilms Tumor", "Down Syndrome", "Bell Palsy"]
    rows = ["pid,电话随访次数,phone_use_hours,address_changes,eponym_dx,phone,住址"] + [
        f"P{i:03d},{rnd.randint(0, 6)},{rnd.uniform(0, 9):.1f},{rnd.randint(0, 3)},{rnd.choice(eponyms)},"
        f"1380013{i:04d},北京市朝阳区建国路{i}号" for i in range(200)]
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid"))
    for name in ("电话随访次数", "phone_use_hours", "address_changes"):
        assert cols[name]["pii"] is None and cols[name]["numeric"]["n"] == 200, name
    assert cols["eponym_dx"]["pii"] is None and len(cols["eponym_dx"]["categorical"]["levels"]) == 5
    assert cols["phone"]["pii"] and cols["住址"]["pii"]


def test_numeric_missing_tokens_apply_where_they_can_be_codes(tmp_path, capsys):
    rows = ["pid,marital,outcome,score,y,alb"] + [
        f"P{i:03d},{'88' if i % 10 == 0 else ['已婚', '未婚', '离异'][i % 3]},{'9' if i % 8 == 0 else ['是', '否'][i % 2]},"
        f"{'-1' if i % 9 == 0 else i % 30},{1 if i % 4 == 0 else 0},{0 if i % 10 == 0 else 30 + i % 9}" for i in range(80)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    profile = _run(path, "--id", "pid", "--missing-tokens", "88,9,-1,0", "--outcome", "outcome")
    cols = _cols(profile)
    assert cols["marital"]["n_missing_total"] == 8 and cols["alb"]["n_missing_total"] == 8
    assert cols["score"]["n_missing_total"] == 9                          # -1; the score 9 is a real value
    assert cols["y"]["n_missing_total"] == 0                               # 0 is one of the 0/1 codes
    o = profile["outcomes"][0]
    assert (o["kind"], o["n_missing"], o["events"]) == ("binary", 10, 30)
    line = next(x for x in profile["problems"] if x.startswith("--missing-tokens"))
    assert "没有用于" in line and "y（0×60）" in line and "score（0×2、9×2）" in line   # scores 0 and 9 are real
    assert _cols(_run(path, "--id", "pid", "--missing-tokens", "y=0"))["y"]["n_missing_total"] == 60
    assert "nosuch" in _error(capsys, path, "--missing-tokens", "nosuch=1")


def test_the_separator_is_found_after_skip_rows_and_title_rows_get_a_hint(tmp_path):
    body = "\n".join("\t".join([f"P{i}", str(40 + i), "男女"[i % 2]]) for i in range(30))
    for title in ("某医院住院患者导出,2023年\n", "a,b,c,d,e\n"):
        profile = _run(_csv(tmp_path, "t.txt", title + "pid\tage\tsex\n" + body + "\n"), "--skip-rows", "1", "--id", "pid")
        assert [c["name"] for c in profile["columns"]] == ["pid", "age", "sex"] and profile["n_rows"] == 30
    profile = _run(_csv(tmp_path, "t.txt", "某医院住院患者导出\npid\tage\tsex\n" + body + "\n"))
    assert any("--skip-rows 1" in x for x in profile["problems"])
    tie = "pid\tAge, years\tWeight, kg\n" + "\n".join(f"P{i}\t{40 + i}\t{60 + i}" for i in range(30)) + "\n"
    assert [c["name"] for c in _run(_csv(tmp_path, "tie.txt", tie))["columns"]] == ["pid", "Age, years", "Weight, kg"]


def test_units_are_read_by_their_parts_and_a_flag_may_follow_them(tmp_path):
    rows = ["pid,hb,sbp,wbc,glu"] + [
        f"P{i},{100 + i}{' g/L L' if i % 5 == 0 else ' g/L'},{100 + i} mm Hg,{3 + i * 0.1:.1f} ×10^9 /L,"
        f"{4 + i * 0.1:.1f}{' mmol/L H' if i % 4 == 0 else ' mmol/L'}" for i in range(40)]
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid"))
    for name, unit in (("hb", "g/L"), ("sbp", "mm Hg"), ("wbc", "×10^9 /L"), ("glu", "mmol/L")):
        assert cols[name]["numeric"]["n"] == 40 and list(cols[name]["numeric_as_text"]["units"]) == [unit], name
    assert cols["hb"]["numeric_as_text"]["flags"] == {"L": 8} and cols["glu"]["numeric_as_text"]["flags"] == {"H": 10}
    assert dp._is_unit("次/分") and dp._is_unit("kg/m2") and not dp._is_unit("Baker Street") and not dp._is_unit("王芳")


def test_total_rows_are_reported(tmp_path):
    for word, where in (("合计", 0), ("合 计", 0), ("Total", 1), ("平均值", 0)):
        rows = [["序号", "姓名", "费用"]] + [[str(i + 1), "", str(1000 + i)] for i in range(30)]
        tr = ["", "", "30435"]
        tr[where] = word
        profile = _run(_csv(tmp_path, "d.csv", "\n".join(",".join(r) for r in rows + [tr]) + "\n"))
        assert profile["total_rows"] == [{"row": 31, "word": word}]
        assert any(x.startswith("像合计/汇总的行：第 31 行") for x in profile["problems"])


def test_many_recurring_levels_stay_categorical(tmp_path):
    prov = ("北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 海南 "
            "重庆 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆").split()
    rows = ["pid,province,icd"] + [f"P{i:04d},{prov[(i * 7) % 31]},C{15 + (i * 11) % 60}" for i in range(300)]
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid"))
    assert cols["province"]["type"] == "categorical" and cols["province"]["categorical"]["n_levels"] == 31
    assert cols["icd"]["type"] == "categorical" and cols["icd"]["categorical"]["n_levels"] == 60


def test_date_time_spellings_and_whole_number_dates(tmp_path):
    import datetime as dt
    days = [dt.date(2022, 1, 1) + dt.timedelta(days=13 * i) for i in range(60)]
    rows = ["pid,d_us,d_iso,d_mon,d_cn,op_day,visit_ym"] + [
        f"P{i},{d.month}/{d.day}/{d.year} 0:00,{d.strftime('%Y-%m-%dT%H:%M:%SZ')},{d.strftime('%b-%y')},"
        f"{d.year}/{d.month}/{d.day} 下午 3:05,{d.strftime('%Y%m%d')},{d.strftime('%Y%m')}" for i, d in enumerate(days)]
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid"))
    for name in ("d_us", "d_iso", "d_cn", "op_day"):
        assert cols[name]["type"] == "date" and (cols[name]["date"]["min"], cols[name]["date"]["max"]) == \
            (days[0].isoformat(), days[-1].isoformat()), name
    assert cols["d_mon"]["type"] == "date" and cols["d_mon"]["date"]["min"] == "2022-01-01"
    assert cols["visit_ym"]["type"] == "date" and any("年月" in h for h in cols["visit_ym"]["hints"])
    sent = ["pid,手术日期"] + [f"P{i},{'1900-01-01' if i % 10 == 0 else days[i].isoformat()}" for i in range(60)]
    d = _cols(_run(_csv(tmp_path, "s.csv", "\n".join(sent) + "\n")))["手术日期"]["date"]
    assert any("1900-01-01" in x for x in d["notes"])


def test_outcome_spellings_and_codes_are_counted_right(tmp_path, capsys):
    import random
    for values, events in ((["是", "否", "否", "否", " 是", "否 "], 20), (["1", "0", "0", "1.0", "0.0", "0"], 20)):
        rows = ["pid,y"] + [f"P{i},{values[i % 6]}" for i in range(60)]
        o = _run(_csv(tmp_path, "o.csv", "\n".join(rows) + "\n"), "--outcome", "y")["outcomes"][0]
        assert (o["kind"], o["events"]) == ("binary", events)
    rows = ["pid,y"] + [f"P{i:03d},{'' if i % 6 == 0 else ('1' if i % 5 == 0 else '0')}" for i in range(30)]
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "one.csv", "\n".join(rows) + "\n"), "--id", "pid", "--outcome", "y")
    assert profile["outcomes"][0]["per_patient"] is None and "同一患者有多行" not in outputs[0]
    rnd = random.Random(3)
    rows = ["pid,visit,y"] + [f"P{p:03d},{v + 1},{'1' if (p % 3 == 0 and v == p % 4) else '2'}" for p in range(45) for v in range(1 + p % 4)]
    rows = [rows[0]] + rnd.sample(rows[1:], len(rows) - 1)
    profile, outputs = _outputs(tmp_path, capsys, _csv(tmp_path, "y12.csv", "\n".join(rows) + "\n"), "--id", "pid", "--outcome", "y")
    pp = profile["outcomes"][0]["per_patient"]
    assert pp["patients_by_level"] == {"2": 41, "1": 15}                 # 4 patients have one row, an event
    term = [x for x in outputs[2].splitlines() if x.startswith("[数据体检] 结局 ")][0]
    assert "15 名" in term and "较少一类" not in term


def test_max_levels_one_keeps_the_outcome_and_zero_is_refused(tmp_path, capsys):
    rows = ["pid,y,grade"] + [f"P{p:03d},{1 if p % 10 == 0 else 0},{['I', 'II', 'III', 'IV'][p % 4]}" for p in range(60) for _ in range(2)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    o = _run(path, "--id", "pid", "--outcome", "y", "--max-levels", "1")["outcomes"][0]
    assert (o["events"], o["non_events"], o["per_patient"]["patients_with_event"]) == (12, 108, 6)
    assert "--max-levels" in _error(capsys, path, "--max-levels", "0")


@pytest.mark.parametrize("name", ["case_no", "Patient Number", "入组号", "病例号", "就诊卡号", "档案号", "患者编码", "随机号",
                                  "ID号码", "Pt No.", "pt", "subject", "No."])
def test_patient_id_headers_group_the_rows(tmp_path, name):
    rows = [f"{name},visit,y"] + [f"S{p:03d},{v + 1},{1 if (p % 5 == 0 and v == 0) else 0}" for p in range(30) for v in range(1 + p % 3)]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--outcome", "y")
    if name == "No.":       # round 4: a row-number name (No., 序号, visit, encounter ...) never tells patients apart
        assert not any(s["as_patient_id"] for s in profile["id_structure"]) and profile["privacy_units"]["mode"] == "none"
        return
    assert [s["column"] for s in profile["id_structure"] if s["as_patient_id"]] == [name]
    assert profile["outcomes"][0]["per_patient"]["n_patients"] == 30


def test_the_outcome_changes_nothing_about_the_other_columns(tmp_path):
    import random
    rr = random.Random(5)
    notes = [f"术后第{d}天出院" for d in range(1, 35)]
    rows = ["center,cost,age,dx_note"] + [f"{'ABC'[i % 3]},{20000 + i * 731 + rr.randint(0, 50)},{40 + i % 30},{notes[i % 34]}"
                                         for i in range(40)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    a, b = _run(path), _run(path, "--outcome", "cost")
    assert a["clusters"] == b["clusters"] and a["privacy"] == b["privacy"] and a["privacy_units"] == b["privacy_units"]
    assert [c for c in a["columns"] if c["name"] != "cost"] == [c for c in b["columns"] if c["name"] != "cost"]
    assert "ids_per_cluster" not in a["clusters"][0]                    # no patient ID: no centre x ID table


def test_detection_limits_and_wide_bins_are_told_apart_by_their_values(tmp_path):
    bins = ["<20"] + [f"{a}-{a + 4}" for a in range(20, 85, 5)] + ["≥85"]
    rows = ["pid,crp_int,trop,egfr,age5,nodes"] + [
        f"P{i},{'<1' if i % 8 else 1 + (i // 8) % 3},{'<3' if i % 2 else 3 + i % 3},{'>90' if i % 3 == 0 else 86 + i % 5},"
        f"{bins[i % 15]},{['0', '1', '2', '≥3'][i % 4]}" for i in range(200)]
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid"))
    for name, n in (("crp_int", 175), ("trop", 100), ("egfr", 67)):
        assert cols[name]["type"] == "numeric" and cols[name]["censored"]["n"] == n, name
    for name, n in (("age5", 15), ("nodes", 4)):
        assert cols[name]["type"] == "categorical" and "censored" not in cols[name] and cols[name]["categorical"]["n_levels"] == n


def test_minus_sign_nd_and_more_missing_spellings(tmp_path):
    rows = ["pid,be,alb,smoke,nd_lab"] + [
        f"P{i},{f'−{i % 5}.{i % 10}' if i % 2 else f'{i % 5}.{i % 10}'},"
        f"{['未送检', '未采', '拒查', 'ND'][i % 4] if i < 8 else 30 + i % 9},"
        f"{['999', '9999', 'ND', '未送检'][i % 4] if i < 8 else '是否'[i % 2]},{'ND' if i % 3 else 1 + i % 30}" for i in range(60)]
    cols = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid"))
    assert cols["be"]["numeric"]["n"] == 60 and cols["be"]["numeric"]["min"] == -4.9
    assert cols["alb"]["n_missing_total"] == 6 and cols["alb"]["censored"]["n"] == 2
    assert "unrecognised" not in cols["alb"]["numeric_as_text"]
    assert cols["smoke"]["n_missing_total"] == 8 and {lab for lab, _ in cols["smoke"]["categorical"]["levels"]} == {"是", "否"}
    assert cols["nd_lab"]["type"] == "numeric" and cols["nd_lab"]["numeric"]["n"] == 20


def test_a_cp1252_mu_only_in_the_values_is_flagged(tmp_path):
    path = _csv(tmp_path, "w.csv", "pid,crea,unit\n" + "\n".join(f"P{i},{60 + i},µmol/L" for i in range(40)) + "\n",
                encoding="cp1252")
    assert any("--encoding cp1252" in x for x in _run(path)["problems"])


def test_min_max_are_exact_and_time_of_day_is_named(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    import datetime as dt
    import warnings
    # (costs that are never whole: a whole number of 7+ digits such as 1245568.00 hides the column's large statistics)
    rows = ["pid,cost"] + [f"P{i},{1234567.89 + i * 1000.02:.2f}" for i in range(40)]
    num = _cols(_run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--id", "pid"))["cost"]["numeric"]
    assert num["min"] == 1234567.89 and num["max"] == round(1234567.89 + 39 * 1000.02, 2)
    wb = openpyxl.Workbook()
    wb.active.append(["pid", "开始时间"])
    for i in range(30):
        wb.active.append([f"P{i}", dt.time(8 + i % 10, 30)])
    path = tmp_path / "t.xlsx"
    wb.save(path)
    with warnings.catch_warnings():
        warnings.simplefilter("error")                                  # no pandas deprecation warning
        col = _cols(_run(path, "--id", "pid"))["开始时间"]
    assert any("时刻" in h for h in col["hints"])


def test_a_repeating_record_number_groups_the_rows_next_to_a_row_number(tmp_path, capsys):
    import random
    rnd = random.Random(45)
    mrn = [str(rnd.randint(100000, 999999)) for _ in UNCOMMON]
    recs = [[UNCOMMON[i], mrn[i], f"{rnd.uniform(40, 130):.1f}"] for i in range(12) for _ in range(rnd.choice([3, 5, 7, 9]))]
    rnd.shuffle(recs)
    rows = ["序号,who,hosp,crea"] + [",".join([str(i + 1)] + r) for i, r in enumerate(recs)]
    path = _csv(tmp_path, "d.csv", "\n".join(rows) + "\n")
    profile, outputs = _outputs(tmp_path, capsys, path)
    _assert_hidden(outputs, UNCOMMON + mrn)
    # round 4: a record number found only by its values is never used as the patient key (it could as well be a
    # per-patient measurement, or the outcome); the no-unit line names it as the probable --id
    assert not any(s["as_patient_id"] for s in profile["id_structure"]) and profile["privacy_units"]["mode"] == "none"
    assert any("hosp" in x and "--id" in x and "--rows-are-patients" in x for x in profile["problems"])
    profile, outputs = _outputs(tmp_path, capsys, path, "--id", "hosp")
    _assert_hidden(outputs, UNCOMMON + mrn)
    assert [s["column"] for s in profile["id_structure"] if s["as_patient_id"]] == ["hosp"]


# ─── fourth-round regressions: no text value without a patient unit; 7+ digits; outcome levels; names ───

INVENTED = ["测甲乙", "试丙丁", "验戊己", "样庚辛", "例壬癸", "模子丑", "拟寅卯", "仿辰巳", "虚午未", "构申酉", "设戌亥", "例天地"]


def _rows_csv(tmp_path, name, rows):
    import csv
    path = tmp_path / name
    with open(path, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    return path


def _long_invented(seed, lead=None, visits=6):
    import random
    rnd = random.Random(seed)
    recs = [[nm, rnd.choice(["男", "女"]), rnd.choice(["肺癌", "胃癌", "肝癌"]), f"{rnd.uniform(40, 130):.1f}"]
            for nm in INVENTED for _ in range(visits)]
    rnd.shuffle(recs)
    head = ([lead] if lead is not None else []) + ["col_a", "sex", "dx", "crea"]
    gen = {None: None, "序号": lambda k: str(k + 1), "No.": lambda k: str(k + 1), "Unnamed: 0": lambda k: str(k),
           "visit_id": lambda k: f"V-{500000 + 7 * k}", "encounter": lambda k: f"E{k + 1:05d}",
           "检验号": lambda k: str(20230500000 + 13 * k)}[lead]
    return [head] + [([gen(k)] if gen else []) + r for k, r in enumerate(recs)]


@pytest.mark.parametrize("lead", [None, "序号", "No.", "Unnamed: 0", "visit_id", "encounter", "检验号"])
def test_without_a_patient_unit_no_category_value_is_printed(tmp_path, capsys, lead):
    """12 invented names (no surname, no shape a check knows) x 6 shuffled visits, no patient ID -- a
    row number next to them (序号 / No. / visit / encounter / 检验号) does not make rows patients: no
    level of any text column is printed, only how many there are; one line says what to pass."""
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", _long_invented(401, lead)))
    _assert_hidden(outputs, INVENTED)
    assert profile["privacy_units"]["mode"] == "none"
    cols = _cols(profile)
    for name in ("col_a", "sex", "dx"):
        cat = cols[name].get("categorical")
        assert not (cat or {}).get("levels")
    sex = cols["sex"]["categorical"]
    assert sex["n_levels"] == 2 and sex["values_hidden"] and sex["largest_share"] >= sex["smallest_share"] > 0
    lines = [x for x in profile["problems"] if "--rows-are-patients" in x and "--id" in x]
    assert len(lines) == 1 and "`sex`（2 个取值）：取值不显示" in outputs[0]
    assert cols["crea"]["numeric"]["n"] == 72                               # numbers keep their distribution


def test_rows_are_patients_restores_levels_with_small_cells(tmp_path, capsys):
    import random
    rnd = random.Random(402)
    rows = [["sex", "dx", "rare", "age"]] + [[rnd.choice("男女"), rnd.choice(["肺癌", "胃癌", "肝癌"]),
                                            "稀有甲" if i < 3 else "常见乙", str(rnd.randint(30, 80))] for i in range(60)]
    path = _rows_csv(tmp_path, "d.csv", rows)
    profile, outputs = _outputs(tmp_path, capsys, path, "--rows-are-patients")
    cols = _cols(profile)
    assert profile["privacy_units"]["mode"] == "asserted"
    assert sorted(lab for lab, _ in cols["sex"]["categorical"]["levels"]) == ["女", "男"]
    assert [lab for lab, _ in cols["rare"]["categorical"]["levels"]] == ["常见乙"]       # 3 rows: a small cell
    assert cols["rare"]["categorical"]["n_levels_suppressed"] == 1
    _assert_hidden(outputs, ["稀有甲"])
    assert not any("--rows-are-patients" in x for x in profile["problems"])


def test_a_name_like_category_is_never_the_patient_key(tmp_path):
    """Wide table with city names (常德 / 黄山 / 金华 look like 2-character names) and --rows-are-patients:
    the ordinary categories stay visible -- no column of names or cities ever decides who the patients are."""
    import random
    rnd = random.Random(72)
    base = {"diagnosis": ["肺腺癌", "肺鳞癌", "小细胞肺癌", "间皮瘤"], "hospital": ["华山医院", "瑞金医院", "中山医院"],
            "stage": ["I", "II", "III", "IV"]}
    cols_ = dict(base, city=["武汉", "宁波", "常德", "黄山", "邵阳", "许昌", "金华", "龙岩"])
    pat = [{k: rnd.choice(v) for k, v in cols_.items()} for _ in range(150)]
    rows = [list(cols_)] + [[p[k] for k in cols_] for p in pat]
    profile = _run(_rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients")
    assert profile["privacy_units"] == dict(profile["privacy_units"], mode="asserted", columns=[])
    for k in base:
        assert len(_cols(profile)[k]["categorical"]["levels"]) == len(base[k])


def _inv_table(seed):
    """final-accuracy p10_invariance.py generator: patients with 1-5 visits, several ID styles, a per-row
    and a per-patient 5-digit integer (cost_row / cost_pat), outcomes of every kind."""
    import collections
    import random
    rnd = random.Random(seed)
    surn, giv = "王李张刘陈杨黄赵吴周", "伟芳娜敏静丽强磊军洋勇艳杰涛明超秀霞平刚"
    n_pat, long = rnd.randint(15, 120), rnd.random() < 0.6
    pats = []
    for p in range(n_pat):
        k = rnd.randint(1, 5) if long else 1
        name = rnd.choice(surn) + rnd.choice(giv) + (rnd.choice(giv) if rnd.random() < 0.5 else "")
        base_cost, ev = rnd.randint(10000, 99999), rnd.random() < rnd.uniform(0.05, 0.5)
        pats += [(p, v, name, base_cost, ev) for v in range(k)]
    rnd.shuffle(pats) if rnd.random() < 0.5 else None
    cols = collections.OrderedDict()
    id_style = rnd.choice(["pid", "none", "seq+mrn", "name_only"])
    if id_style == "pid":
        cols["patient_id"] = [f"P{p:04d}" for p, *_ in pats]
    elif id_style == "seq+mrn":
        cols["序号"] = [str(i + 1) for i in range(len(pats))]
        cols["住院号"] = [str(200000 + p * 7) for p, *_ in pats]
    if id_style in ("name_only", "pid") and rnd.random() < 0.7:
        cols["姓名"] = [nm for _, _, nm, _, _ in pats]
    if rnd.random() < 0.5:
        cols["who"] = [nm for _, _, nm, _, _ in pats]
    cols["visit"] = [str(v + 1) for _, v, *_ in pats]
    cols["sex"] = [rnd.choice(["男", "女", "女 ", "未知"]) for _ in pats]
    cols["age"] = [rnd.choice([str(rnd.randint(18, 90))] * 9 + ["999", "未查"]) for _ in pats]
    cols["crea"] = [rnd.choice([f"{rnd.uniform(40, 300):.1f}", f"{rnd.randint(40, 300)} μmol/L", f"{rnd.randint(40, 300)}↑", "/"]) for _ in pats]
    cols["crp"] = [rnd.choice(["<0.5"] * 3 + [f"{rnd.uniform(0.5, 90):.1f}"]) for _ in pats]
    cols["agegrp"] = [rnd.choice(["<60", "≥60"]) for _ in pats]
    cols["dx"] = [rnd.choice([f"dx{rnd.randint(1, 40)}", "dx1", "dx2"]) for _ in pats]
    cols["op_date"] = [rnd.choice([f"2022-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}", f"{rnd.randint(1, 12)}/{rnd.randint(13, 28)}/2022", "未做"]) for _ in pats]
    cols["center"] = [rnd.choice(["A", "B", "C"]) for _ in pats]
    cols["surgeon"] = [rnd.choice(["张伟", "李娜", "王芳", "刘洋"]) for _ in pats]
    cols["备注"] = [rnd.choice(["", "", "患者刘洋拒绝随访", "复查", f"note {rnd.randint(1, 999)}"]) for _ in pats]
    cols["cost_row"] = [str(rnd.randint(10000, 99999)) for _ in pats]
    cols["cost_pat"] = [str(c) for _, _, _, c, _ in pats]
    cols["y01"] = [("1" if ev else "0") if rnd.random() > 0.1 else "" for *_, ev in pats]
    cols["y_yes"] = [("是" if ev else "否") if rnd.random() > 0.1 else "NA" for *_, ev in pats]
    cols["y12"] = [("2" if ev else "1") for *_, ev in pats]
    cols["y3"] = [rnd.choice(["CR", "PR", "SD", "PD", "失访"]) for _ in pats]
    cols["los"] = [str(rnd.randint(1, 40)) for _ in pats]
    cols["months"] = [f"{rnd.uniform(0, 60):.1f}" for _ in pats]
    cols["empty"] = ["" for _ in pats]
    cols["ytext"] = [rnd.choice(["", f"随访记录 {rnd.randint(1, 10 ** 6)} 正常"]) for _ in pats]
    names = list(cols)
    return [names] + [[cols[c][i] for c in names] for i in range(len(pats))]


@pytest.mark.parametrize("seed", [1, 4])
def test_outcome_invariance_on_generated_tables(tmp_path, seed):
    """inv_1 / inv_4 of the round-3 accuracy check: with a per-patient constant 5-digit integer and no
    patient ID, or all-different 5-digit integers, as the outcome, every section but the outcome's own
    summary is identical with and without --outcome -- the outcome column's entry too."""
    import copy
    df, meta = dp.load_table(_rows_csv(tmp_path, f"inv_{seed}.csv", _inv_table(seed)))
    base = dp.profile_dataframe(df, source=meta)
    no9 = lambda md: "\n## ".join(x for x in md.split("\n## ") if not x.startswith("9."))

    def strip(p):
        q = copy.deepcopy(p)
        q.pop("outcomes")
        return json.dumps(q, sort_keys=True, ensure_ascii=False)
    for oc in ("cost_pat", "cost_row", "y01", "y_yes", "y12", "y3", "los", "months", "sex", "dx", "agegrp", "crp"):
        for extra in ({}, {"time_col": "months"} if oc in ("y01", "y_yes") else {}):
            prof = dp.profile_dataframe(df, outcome_col=oc, source=meta, **extra)
            assert strip(prof) == strip(base), (oc, extra)
            assert no9(dp.render_markdown(prof)) == no9(dp.render_markdown(base)), (oc, extra)


def test_the_detected_patient_key_given_as_the_outcome_stays_the_key(tmp_path, capsys):
    """--outcome naming the auto-detected patient key used to stop with exit 2. Now it is profiled: the key stays
    the key (nothing outside the outcome entry changes) and the outcome entry says so and names --id."""
    path = _rows_csv(tmp_path, "d.csv", [["patient_id", "y"]] + [[f"P{i // 2}", str(i % 2)] for i in range(40)])
    with_key, plain = _run(path, "--outcome", "patient_id"), _run(path)
    strip = lambda p: json.dumps({k: v for k, v in p.items() if k != "outcomes"}, sort_keys=True, ensure_ascii=False)
    assert strip(with_key) == strip(plain)
    assert any("--id" in x and "区分患者" in x for x in with_key["outcomes"][0]["notes"])
    assert _run(path, "--outcome", "y")["outcomes"][0]["per_patient"]["n_patients"] == 20


@pytest.mark.parametrize("cell", ["5" + " " * 40000 + "mg", "1" + " " * 40000 + "x"])
def test_a_40k_space_cell_profiles_fast(tmp_path, cell):
    """A cell of 40 000 spaces between a number and a word took 21 s (a quadratic pattern in the header
    check, 200 000 spaces > 600 s): every pattern on raw cells is linear and length-capped."""
    import time
    for where in ("body", "header"):
        rows = ([["pid", "x", "y"]] + [[f"P{i:03d}", cell if i == 0 else str(i), "ab"[i % 2]] for i in range(30)]
                if where == "body" else [["pid", cell, "y"]] + [[f"P{i:03d}", str(i), "a"] for i in range(30)])
        path = _rows_csv(tmp_path, "d.csv", rows)
        t0 = time.time()
        dp.main([str(path)])
        assert time.time() - t0 < 2, where


def test_whole_numbers_of_7_or_more_digits_are_never_printed(tmp_path, capsys):
    phone, idc, local = "13800131005", "110101195001011008", "62345678"
    rows = [["pid", "age", "os_months", "dead", "visit_date"]] + [[f"P{i:03d}", str(30 + i % 50), str(5 + i % 40), str(i % 2),
                                                                  f"2022-{1 + i % 12:02d}-{1 + i % 28:02d}"] for i in range(80)]
    rows[5][1], rows[9][1], rows[11][2], rows[17][4] = phone, idc, phone, local
    path = _rows_csv(tmp_path, "d.csv", rows)
    profile, outputs = _outputs(tmp_path, capsys, path, "--id", "pid", "--outcome", "dead", "--time", "os_months")
    _assert_hidden(outputs, [phone, idc, idc[:15], local, "1.38e+10"])
    age = _cols(profile)["age"]
    assert age["type"] == "numeric" and age["numeric"]["n"] == 80 and age["numeric"]["max"] is None
    assert age["numeric"]["n_big_int"] == 2 and age["numeric"]["min"] == 30
    assert any("7 位以上的整数" in x and "age" in x for x in profile["problems"])
    assert "7 位以上" in profile["outcomes"][0]["time"]["note"] and profile["outcomes"][0]["time"]["max"] is None
    assert _cols(profile)["visit_date"]["date"]["n_unparseable"] == 1
    out = _run(path, "--id", "pid", "--outcome", "age")["outcomes"][0]
    assert out["numeric"]["max"] is None and any("7 位以上" in x for x in out["notes"])


@pytest.mark.parametrize("with_id", [False, True])
def test_an_outcome_level_that_identifies_is_masked(tmp_path, capsys, with_id):
    for rare in ("死亡（家属李娜电话告知）", "失访：电话13800131005停机", "转院至扎西多吉家中", "死亡 José García", "测甲乙"):
        rows = [["pid", "转归", "age"]] + [[f"P{i:03d}", "存活", str(30 + i % 40)] for i in range(59)] + [["P059", rare, "50"]]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows), "--outcome", "转归",
                                    *(["--id", "pid"] if with_id else []))
        _assert_hidden(outputs, [rare, "13800131005", "李娜", "扎西多吉", "José García"])
        o = profile["outcomes"][0]
        assert o["kind"] == "binary" and sorted(n for _, n in o["levels"]) == [1, 59] and "存活" in dict(o["levels"])
    rows = [["pid", "y"]] + [[f"P{i:03d}", "1" if i % 3 == 0 else "0"] for i in range(60)]
    o = _run(_rows_csv(tmp_path, "y.csv", rows), "--outcome", "y")["outcomes"][0]
    assert (o["event_label"], o["events"]) == ("1", 20) and sorted(lab for lab, _ in o["levels"]) == ["0", "1"]


def test_title_rows_and_transposed_tables_never_print_their_names(tmp_path, capsys):
    openpyxl = pytest.importorskip("openpyxl")
    for title in ("患者：张建国  住院号：ZY2023000151", "Patient: 测甲乙", "测甲乙 化验单"):
        body = [[title, "", ""], ["日期", "项目", "结果"]] + [[f"2023-01-{1 + k:02d}", ["ALT", "AST", "Cr"][k % 3], str(20 + k)]
                                                         for k in range(28)]
        wb = openpyxl.Workbook()
        for r in body:
            wb.active.append(r)
        wb.save(tmp_path / "t.xlsx")
        for path in (_rows_csv(tmp_path, "t.csv", body), tmp_path / "t.xlsx"):
            profile, outputs = _outputs(tmp_path, capsys, path)
            _assert_hidden(outputs, ["张建国", "ZY2023000151", "测甲乙"])
            assert any("--skip-rows 1" in x for x in profile["problems"])
    for patients in (["张建国"], ["扎西多吉", "次仁卓玛"], ["测甲乙"], ["ZY-23-4100", "ZY-23-4101"]):
        rows = [["项目"] + patients] + [[v] + ["12.5"] * len(patients) for v in ("年龄", "Hb", "ALT", "Cr", "BMI")]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "tr.csv", rows))
        _assert_hidden(outputs, patients)
        assert any("转置" in x for x in profile["problems"])
    rows = [["pid", "王芳评分", "张建国", "gold"]] + [[f"P{i:03d}", str(i % 5), str(i % 4), str(i % 3)] for i in range(40)]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "r.csv", rows), "--id", "pid")
    _assert_hidden(outputs, ["王芳", "张建国"])
    ok = [["pid", "Blood Pressure", "Heart Rate", "张力", "Total Score"]] + [[f"P{i}", "120", "80", "3", "9"] for i in range(30)]
    assert [c["name"] for c in _run(_rows_csv(tmp_path, "ok.csv", ok), "--id", "pid")["columns"]] == ok[0]


def test_file_and_sheet_names_with_digit_groups_or_initials_are_hidden(tmp_path, capsys):
    openpyxl = pytest.importorskip("openpyxl")
    rows = [["pid", "age"]] + [[f"P{i}", str(40 + i)] for i in range(20)]
    for label in ("138 0013 1005", "1101 0119 5001 0110 0X", "ZY-2023-0412", "1980-01-01", "1980.01.01", "patient 0042",
                  "case 12", "x y", "单一", "第五一"):
        d = tmp_path / f"d{abs(hash(label)) % 10 ** 6}"
        d.mkdir()
        _, outputs = _outputs(tmp_path, capsys, _rows_csv(d, f"{label}.csv", rows))
        _assert_hidden(outputs, [label, label.replace(" ", "")])
        wb = openpyxl.Workbook()
        wb.active.title = label
        for r in rows:
            wb.active.append(r)
        wb.save(d / "b.xlsx")
        _, outputs = _outputs(tmp_path, capsys, d / "b.xlsx")
        _assert_hidden(outputs, [label])
    for label in ("data_2023", "随访数据", "baseline v2", "export 2019-2020", "单中心研究"):
        assert dp._safe_label_text(label), label


@pytest.mark.parametrize("header", ["生辰", "诞辰", "bdate", "b_date", "DtNasc", "data di nascita", "data_nascita", "naissance",
                                    "date de naissance", "fødselsdato", "生年月日(西暦)", "d1"])
def test_dates_of_birth_under_more_headers_are_hidden(tmp_path, capsys, header):
    import datetime as dt
    import random
    rnd = random.Random(31)
    lo, hi = dt.date(1931, 7, 19), dt.date(2003, 11, 27)
    ds = [lo, hi] + [dt.date(1935, 1, 1) + dt.timedelta(days=rnd.randint(0, 24000)) for _ in range(58)]
    rows = [["pid", header, "visit_date"]] + [[f"P{i:03d}", d.isoformat(), f"2023-0{1 + i % 9}-1{i % 9}"] for i, d in enumerate(ds)]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows), "--id", "pid")
    _assert_hidden(outputs, [lo.isoformat(), hi.isoformat()])
    assert _cols(profile)[header]["pii"]
    assert _cols(profile)["visit_date"]["date"]["min"] == "2023-01-10"            # visit dates keep their range


def test_phones_with_dashes_or_country_codes_in_shared_text_are_hidden(tmp_path, capsys):
    import random
    rnd = random.Random(24)
    texts = ["联系人电话138–0013–1005", "tel 138—0013—1006", "联系 0086 13800131007", "家里电话 62345678", "微信 zw19800101"]
    for t in texts:
        rows = [["pid", "随访情况", "crea"]] + [[f"P{i:03d}", rnd.choice(["电话随访", "门诊复查", t]), f"{70 + i * .5:.1f}"] for i in range(60)]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows), "--id", "pid")
        _assert_hidden(outputs, [t, "13800131005", "13800131006", "13800131007", "62345678", "zw19800101"])
        assert {"电话随访", "门诊复查"} <= {lab for lab, _ in _cols(profile)["随访情况"]["categorical"]["levels"]}


def test_large_tables_do_not_type_measurements_as_ids_by_chance_ties(tmp_path):
    import random
    rnd = random.Random(99)
    rows = [["patient_id", "steps", "ldh"]] + [[f"P{i // 3:05d}", str(rnd.randint(10000, 14999)), str(rnd.randint(100, 900))]
                                              for i in range(10000)]
    path = _rows_csv(tmp_path, "d.csv", rows)
    for args in ((), ("--id", "patient_id")):
        assert _cols(_run(path, *args))["steps"]["type"] == "numeric"
    rows = [["mrn", "crea"]] + [[str(4100230 + 37 * i), f"{50 + v:.1f}"] for i in range(12) for v in range(6)]
    assert _cols(_run(_rows_csv(tmp_path, "m.csv", rows)))["mrn"]["type"] == "id"     # a record number still is one


def test_grouped_bins_with_a_zero_group_and_labs_censored_at_both_ends(tmp_path):
    import random
    rnd = random.Random(23)
    rows = [["pid", "smoke_py", "trop"]] + [[f"P{i:03d}", rnd.choice(["0", "<20", "≥20"]),
                                            "<0.01" if i % 10 else rnd.choice([">50", "0.15", "1.2", "3.4"])] for i in range(200)]
    cols = _cols(_run(_rows_csv(tmp_path, "d.csv", rows), "--id", "pid"))
    assert cols["smoke_py"]["type"] == "categorical" and "censored" not in cols["smoke_py"]
    assert cols["trop"]["type"] == "numeric" and cols["trop"]["censored"]["n"] == sum(1 for r in rows[1:] if r[2][0] in "<>")


def test_compound_measurements_are_named_not_private(tmp_path):
    import random
    rnd = random.Random(8)
    rows = [["pid", "bp", "bp_unit", "size2d"]] + [[f"P{i:03d}", f"{rnd.randint(90, 190)}/{rnd.randint(50, 110)}",
                                                  f"{rnd.randint(90, 190)}/{rnd.randint(50, 110)}mmHg",
                                                  f"{rnd.uniform(0.5, 9):.1f}×{rnd.uniform(0.5, 9):.1f}cm"] for i in range(150)]
    profile = _run(_rows_csv(tmp_path, "d.csv", rows), "--id", "pid")
    for k in ("bp", "bp_unit", "size2d"):
        c = _cols(profile)[k]
        assert not c["pii"] and c.get("compound") == 150 and any("复合测量" in h for h in c["hints"])
        assert not (c.get("numeric_as_text") or {}).get("units")
    assert not profile["privacy"]


def test_total_rows_with_colons_statistics_or_counts_are_found(tmp_path):
    body = [[f"P{i:03d}", "男女"[i % 2], str(30 + i)] for i in range(40)]
    for word, other in (("合计：", ""), ("总计:", ""), ("Total:", ""), ("均值±标准差", ""), ("合计", "40人")):
        rows = [["pid", "sex", "age"]] + body + [[word, other, "1990"]]
        assert [x["row"] for x in _run(_rows_csv(tmp_path, "d.csv", rows))["total_rows"]] == [41], word


def test_spellings_of_one_unit_are_one_unit(tmp_path):
    import random
    rnd = random.Random(101)
    rows = [["pid", "wbc", "plt", "iu", "ten9"]]
    for i in range(120):
        v = round(rnd.uniform(2, 15), 1)
        rows.append([f"P{i:03d}", rnd.choice([f"{v} ×10^9/L", f"{v} x10^9/L", f"{v}*10^9/L"]),
                     rnd.choice([f"{v * 30:.0f} ×10⁹/L", f"{v * 30:.0f}×10^9/L"]), rnd.choice([f"{v} IU/mL", f"{v}IU/ml"]),
                     rnd.choice([f"{v} 10*9/L", f"{v}10^9/L", f"{v} 10E9/L"])])
    path = _rows_csv(tmp_path, "d.csv", rows)
    profile = _run(path, "--id", "pid")
    for k in ("wbc", "plt", "iu", "ten9"):
        c = _cols(profile)[k]
        assert len(c["numeric_as_text"]["units"]) == 1 and c["numeric"]["n"] == 120, (k, c["numeric_as_text"]["units"])
        assert not any("多种单位" in h for h in c["hints"])
    assert "×109" not in json.dumps(profile, ensure_ascii=False)


def test_nd_is_missing_in_ages_and_a_shown_censored_value_in_labs(tmp_path):
    import random
    rnd = random.Random(5)
    rows = [["pid", "age", "psa"]] + [[f"P{i:03d}", "ND" if i % 7 == 0 else str(rnd.randint(18, 90)),
                                      "ND" if i % 5 == 0 else f"{rnd.uniform(0.1, 9):.2f}"] for i in range(200)]
    cols = _cols(_run(_rows_csv(tmp_path, "d.csv", rows), "--id", "pid"))
    assert "censored" not in cols["age"] and cols["age"]["disguised_missing"] == {"ND": 29}
    assert cols["psa"]["censored"] == {"n": 40, "examples": ["ND"]}


def test_one_impossible_yyyymmdd_keeps_a_date_column(tmp_path, capsys):
    import random
    rnd = random.Random(99)
    rows = [["patient_id", "op", "手术日期"]]
    for i in range(100):
        d = f"2023{rnd.randint(1, 12):02d}{rnd.randint(1, 28):02d}"
        rows.append([f"P{i:03d}", d, d])
    rows[5][1] = rows[5][2] = "20230230"
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows), "--id", "patient_id")
    for k in ("op", "手术日期"):
        assert _cols(profile)[k]["type"] == "date" and _cols(profile)[k]["date"]["n_unparseable"] == 1
    _assert_hidden(outputs, ["20230230"])


def test_count_and_care_columns_are_not_private_and_value_ids_say_why(tmp_path):
    import random
    rnd = random.Random(55)
    rows = [["patient_id", "visit", "baseline_plt", "居住地", "联系人数", "home_bp_control", "home_address"]]
    for p in range(80):
        plt_, reg, cn = rnd.randint(100000, 450000), rnd.choice(["城市", "城镇", "农村"]), rnd.randint(0, 12)
        rows += [[f"P{p:03d}", str(v + 1), str(plt_), reg, str(cn), rnd.choice(["good", "fair", "poor"]), f"幸福路{p}号"]
                 for v in range(rnd.randint(2, 4))]
    profile = _run(_rows_csv(tmp_path, "d.csv", rows), "--id", "patient_id")
    cols = _cols(profile)
    assert not cols["联系人数"]["pii"] and cols["联系人数"]["numeric"]["n"] == len(rows) - 1
    assert not cols["home_bp_control"]["pii"] and cols["home_bp_control"]["categorical"]["levels"]
    assert cols["home_address"]["pii"]
    assert cols["baseline_plt"]["type"] == "id" and any("每名患者" in h and "不是隐私判断" in h for h in cols["baseline_plt"]["hints"])
    assert any(x.startswith("疑似隐私字段") and "居住地（列名含“居住”" in x for x in profile["problems"])


def test_missing_tokens_full_width_comma_negative_values_and_a_global_zero(tmp_path, capsys):
    import random
    rnd = random.Random(31)
    rows = [["pid", "score", "ncomp", "note", "age", "lab"]] + [
        [f"P{i:03d}", str(rnd.randint(0, 29)), str(rnd.choice([0, 0, 1, 2, 3])), rnd.choice(["拒做", "做了", "待补", "做了"]),
         rnd.choice([str(rnd.randint(20, 90)), "0"]), rnd.choice([f"{rnd.uniform(0.5, 9):.1f}", "-1"])] for i in range(120)]
    path = _rows_csv(tmp_path, "d.csv", rows)
    assert set(_cols(_run(path, "--id", "pid", "--missing-tokens", "拒做，待补"))["note"]["disguised_missing"]) == {"拒做", "待补"}
    cols = _cols(_run(path, "--id", "pid", "--missing-tokens", "-1,0"))
    assert cols["lab"]["missing_codes"].get("-1") and cols["age"]["missing_codes"].get("0")
    assert not cols["ncomp"]["missing_codes"] and not cols["score"]["missing_codes"]        # 0 next to 1..n is real
    assert cols["ncomp"]["missing_tokens_not_applied"].get("0")
    assert _cols(_run(path, "--id", "pid", "--missing-tokens", "ncomp=0"))["ncomp"]["missing_codes"].get("0")
    assert "缺少列名" in _error(capsys, path, "--missing-tokens", "=9")


def test_big5_files_are_read_as_big5(tmp_path):
    text = "病例號,性別,年齡,高血壓,地區,備註\n" + "\n".join(
        f"P{i},{'男女'[i % 2]},{40 + i},{['是', '否', '未檢', '不詳'][i % 4]},{['台北', '高雄', '臺中'][i % 3]},門診隨訪" for i in range(40)) + "\n"
    profile = _run(_csv(tmp_path, "d.csv", text, encoding="big5"), "--id", "病例號")
    assert profile["source"]["encoding"].startswith("big5") and [c["name"] for c in profile["columns"]][:3] == ["病例號", "性別", "年齡"]
    assert _cols(profile)["高血壓"]["disguised_missing"] == {"未檢": 10, "不詳": 10}
    assert any("Big5" in x for x in profile["problems"])
    gbk = text.replace("號", "号").replace("別", "别").replace("齡", "龄").replace("壓", "压").replace("區", "区")
    gbk = gbk.replace("備註", "备注").replace("檢", "检").replace("詳", "详").replace("門診隨訪", "门诊随访").replace("臺", "台")
    assert _run(_csv(tmp_path, "g.csv", gbk, encoding="gbk"), "--id", "病例号")["source"]["encoding"] == "gbk"


def test_a_date_outcome_is_reported_as_a_date(tmp_path):
    rows = [["pid", "death_date"]] + [[f"P{i:03d}", f"2023-{1 + i % 12:02d}-{1 + i % 28:02d}"] for i in range(100)]
    o = _run(_rows_csv(tmp_path, "d.csv", rows), "--id", "pid", "--outcome", "death_date")["outcomes"][0]
    assert o["kind"] == "date" and o["levels"] is None and not any("多分类" in x for x in o["notes"])


def test_skip_rows_beyond_the_file_names_skip_rows(tmp_path, capsys):
    path = _csv(tmp_path, "d.csv", "Export\npid;a\n" + "\n".join(f"P{i};{i}" for i in range(60)) + "\n")
    line = _error(capsys, path, "--skip-rows", "500")
    assert "--skip-rows 500" in line and "数据文件是空的" not in line


def test_a_utf8_file_with_one_stray_byte_stays_utf8(tmp_path):
    rows = ["病例号,性别,年龄,备注"] + [f"BL{10000 + i},{'男女'[i % 2]},{30 + i},{'门诊随访' if i % 3 else '复查'}" for i in range(80)]
    raw = "\n".join(rows).encode("utf-8").replace("门诊随访".encode("utf-8"), "门诊随访".encode("utf-8") + b" caf\xe9", 1)
    path = tmp_path / "d.csv"
    path.write_bytes(raw)
    profile = _run(path, "--id", "病例号")
    assert [c["name"] for c in profile["columns"]] == ["病例号", "性别", "年龄", "备注"]
    line = next(x for x in profile["problems"] if "UTF-8" in x)
    assert "第 3 行" in line and "cp1252" not in json.dumps(profile, ensure_ascii=False)


def test_dead_code_is_gone_and_the_address_header_check_ignores_case():
    for name in ("CODE_RE", "PII_NAME_SUBSTR", "MDY_FORMATS"):
        assert not hasattr(dp, name)
    body = [[f"{20 + i} {s} STREET", str(40 + i)] for i, s in enumerate(["OAK", "ELM", "PINE", "MAPLE", "BIRCH", "CEDAR"] * 3)]
    assert dp._header_looks_like_data(["12 BAKER STREET", "40"], body)


# ─── round 4b: the round-4 verifiers' findings (synthetic names; numbers start with 100) ─────────

_WEAK = ["Testa Personne", "Fakeo Nomen", "Probo Exempla", "Dummo Ficta", "Mocka Sampla", "Synthia Fakerly",
         "Quasi Personna", "Nemo Nullus", "Fictus Rexa", "Imagina Tora", "Pseudo Nyma", "Exempli Gratia"]
_CNW = ["王甲乙", "李丙丁", "张戊己", "刘庚辛", "陈壬癸", "杨甲丙", "赵乙丁", "黄丙戊", "周丁己", "吴戊庚", "徐己辛", "孙庚壬"]


def test_an_admission_number_named_like_a_patient_id_is_the_key_and_two_such_columns_are_none(tmp_path, capsys):
    """Round 5c (deterministic key rule): a 住院号 that repeats on a few rows is the automatic key -- its name names the
    patient and how many rows each value has is not used -- and every value of it counts as one patient (a value is
    printed only when 5+ of its values hold it; the header says so and names --id). Next to a real patient_id (both
    repeating, 10+ values) neither is used: no text value, one line naming both and --id. (Before round 5c the 住院号
    was refused by the share of its values that repeat, and the patient_id won.)"""
    import collections
    rows = [["住院号", "col_a", "hb"]]
    for p in range(12):
        for v in range(6):
            rows.append([f"ZY{1001 + 6 * p + v:05d}", _WEAK[p], str(90 + v)])
    for i in range(1, 10):
        rows[i * 2][0] = rows[i * 2 - 1][0]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows))
    assert profile["privacy_units"]["mode"] == "patient" and profile["privacy_units"]["columns"] == ["住院号"]
    held = collections.defaultdict(set)
    for r in rows[1:]:
        held[r[1]].add(r[0])
    _assert_hidden(outputs, [x for x in _WEAK if len(held[x]) < 5])
    assert "患者按 `住院号` 区分" in outputs[0] and "每个取值算一名患者" in outputs[0]
    rows = [["patient_id", "住院号", "info", "hb"]]
    for p in range(12):
        for v in range(8):
            rows.append([f"P{p:03d}", f"A{2000 + 8 * p + v}", _WEAK[p], str(90 + v)])
    for i in range(1, 27, 2):
        rows[i + 1][1] = rows[i][1]                       # 13 admission numbers on two rows each
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d2.csv", rows))
    _assert_hidden(outputs, _WEAK)
    assert profile["privacy_units"]["mode"] == "none" and profile["privacy_units"]["ambiguous"] == ["patient_id", "住院号"]
    lines = [x for x in profile["problems"] if "patient_id" in x and "住院号" in x]
    assert len(lines) == 1 and lines[0].startswith("无法区分患者") and "--id patient_id" in lines[0], profile["problems"]
    assert not any(x.startswith("patient_id：") or x.startswith("住院号：") for x in profile["problems"])
    profile = _run(_rows_csv(tmp_path, "d2.csv", rows), "--id", "patient_id")
    assert profile["privacy_units"]["columns"] == ["patient_id"] and profile["privacy_units"]["ambiguous"] == []


@pytest.mark.parametrize("spell", ["{}.00", "{}.0", "{0}.{1}E+{2}", "{0}.{1}e{2}"])
def test_whole_numbers_of_7_digits_are_hidden_however_written(tmp_path, capsys, spell):
    """'10012345678.00' (Excel's 2-decimal Number format) and '1.0012345678E+10' (its CSV export) were printed in full as
    a maximum, a --time maximum, a numeric outcome and a level of a <=10-level column."""
    for secret in ("10012345678", "1001234", "100123456789012345"):
        cell = spell.format(secret) if "{}" in spell else spell.format(secret[0], secret[1:], len(secret) - 1)
        rows = [["pid", "age", "crea", "fu_days", "score", "y"]] + [
            [f"P{i:03d}", str(30 + i % 50), f"{40 + i * 0.7:.1f}", str(10 + 13 * i), str(1 + i % 5), f"{1 + i * 0.1:.2f}"] for i in range(60)]
        rows[5][2] = rows[7][3] = rows[9][4] = rows[11][5] = cell
        path = _rows_csv(tmp_path, "d.csv", rows)
        for args in (("--id", "pid", "--outcome", "y", "--time", "fu_days"), ("--rows-are-patients", "--not-id", "crea")):
            profile, outputs = _outputs(tmp_path, capsys, path, *args)
            _assert_hidden([t.replace(profile["source"]["sha256"], "") for t in outputs], [secret])
    rows = [["pid", "vl"]] + [[f"P{i:03d}", f"{1 + (i % 9) * 0.97:.2f}E+0{6 + i % 4}" if i % 2 else "<500"] for i in range(80)]
    assert _cols(_run(_rows_csv(tmp_path, "v.csv", rows), "--rows-are-patients"))["vl"]["numeric"]["n_big_int"] == 40


def test_weak_shaped_names_in_column_names_are_hidden(tmp_path, capsys):
    """Weak name shapes (two capitalised words, a surname with uncommon given characters) as column names were printed:
    transposed tables over uncommon variables, one-patient lab sheets, and names inside a longer column name."""
    rows = [["Variable"] + _WEAK[:3]] + [[v] + ["12.5", "13.1", "9.8"] for v in ("Ki-67", "LVEF", "FEV1", "NIHSS", "MMSE", "eGFR")]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "t.csv", rows))
    _assert_hidden(outputs, _WEAK[:3])
    assert any("转置" in x for x in profile["problems"])
    rows = [["项目", "王" + sorted(dp.CN_GIVEN_CHARS)[2] + "甲"]] + [[v, "4.5"] for v in ("红细胞", "中性粒细胞%", "淋巴细胞%", "单核细胞", "血细胞比容")]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "one.csv", rows))
    _assert_hidden(outputs, [rows[0][1]])
    for h, secret in (("患者王甲乙", "王甲乙"), ("Dr. Testa Personne", "Testa Personne"), ("Testa Personne_hb", "Testa Personne"),
                      ("hb(Testa Personne)", "Testa Personne"), ("家属王甲乙电话", "王甲乙"), ("Mr Testa", "Testa"),
                      ("TESTA PERSONNE", "TESTA PERSONNE"), ("王甲乙 ", "王甲乙"), ("王甲乙（1001）", "王甲乙"), ("Testa Personne visit 1", "Testa Personne"),
                      ("患者王芳出生日期", "王芳"), ("王甲乙电话", "王甲乙"), ("王甲乙随访记录", "王甲乙")):
        rows = [["pid", "age", h, "sex"]] + [[f"P{i:03d}", str(20 + i), str(i % 9), "男女"[i % 2]] for i in range(30)]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "h.csv", rows), "--rows-are-patients")
        _assert_hidden(outputs, [secret])
    ok = ["pid", "Blood Pressure", "Child Pugh", "Hunt Hess", "Ann Arbor stage", "Date Of Birth (dd/mm/yyyy)", "白细胞", "高血压",
          "杜冷丁", "SF36_01", "V01_01", "T08_30", "Hb 2021-01", "Hb_20230101", "Hb_202301", "rs1801133", "金额", "方式", "常规检查", "患者年龄"]
    rows = [ok] + [[f"P{i:03d}"] + [str(i % 5)] * (len(ok) - 1) for i in range(60)]
    profile = _run(_rows_csv(tmp_path, "ok.csv", rows), "--rows-are-patients")
    assert [c["name"] for c in profile["columns"]] == ok and not profile["source"].get("transposed")
    rows = [["pid", "age"] + [f"2023-{m:02d}-01" for m in range(1, 5)]] + [[f"P{i:03d}", str(30 + i)] + ["5"] * 4 for i in range(40)]
    profile = _run(_rows_csv(tmp_path, "dh.csv", rows), "--rows-are-patients")
    assert profile["source"]["header_mode"] == "first-row" and [c["name"] for c in profile["columns"]] == rows[0]


def test_title_rows_of_two_to_four_cells_are_never_column_names(tmp_path, capsys):
    """min(2, mode // 2) made a 2-cell title over 3 columns, and every 3-4 cell title, the header."""
    body = [["pid", "age", "sex"]] + [[f"P{i:03d}", str(30 + i), "男女"[i % 2]] for i in range(30)]
    for title in (["患者：王甲乙", "住院号：1001234567", ""], ["王甲乙", "1001234567", ""], ["患者：王甲乙", "住院号：1001234567", "性别：男"],
                  ["姓名", "王甲乙", "住院号", "1001234567"], ["王甲乙 化验单", "", "2023-01-05"]):
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "t.csv", [title] + body), "--rows-are-patients")
        _assert_hidden(outputs, ["王甲乙", "1001234567"])
        assert any("--skip-rows 1" in x for x in profile["problems"])
    rows = [["pid", "age", "", ""]] + [[f"P{i:03d}", str(30 + i), "男女"[i % 2], f"{100 + i}.5"] for i in range(30)]
    profile = _run(_rows_csv(tmp_path, "b.csv", rows))
    assert [c["name"] for c in profile["columns"]][:2] == ["pid", "age"] and not profile["source"].get("title_rows")


def test_transposed_tables_headed_by_record_numbers(tmp_path, capsys):
    """'项目' over 5-6 digit numbers was read as a data row: each patient's number became his column's maximum."""
    for codes in ([str(100230 + i) for i in range(3)], [f"#{100230 + i}" for i in range(3)], [f"23-{1000 + i}" for i in range(3)],
                  [f"住院{100230 + i}" for i in range(3)]):
        rows = [["项目"] + codes] + [[v, "12.5", "7.25", "33.1"] for v in ("Ki-67", "LVEF", "FEV1", "NIHSS", "eGFR")]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "t.csv", rows))
        _assert_hidden(outputs, codes)
        assert any("转置" in x for x in profile["problems"])


def test_dates_of_birth_under_more_names_and_under_neutral_names(tmp_path, capsys):
    import datetime as dt
    import random
    rnd = random.Random(4)
    dobs = [dt.date(rnd.randint(1950, 1980), rnd.randint(1, 12), rnd.randint(1, 28)).isoformat() for _ in range(40)]
    for h in ("생년월일", "data_nasc", "data de nascimento", "fecha_nac", "FNac", "ημερομηνία γέννησης", "дата рождения", "生年月", "d1", "date_a"):
        rows = [["pid", h, "age"]] + [[f"P{i:03d}", d, str(40 + i)] for i, d in enumerate(dobs)]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients")
        _assert_hidden(outputs, [min(dobs), max(dobs)])
    rows = [["pid", "d1", "admit_date"]] + [[f"P{i:03d}", d, "2023-03-1" + str(i % 9)] for i, d in enumerate(dobs[:6])]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "n.csv", rows), "--rows-are-patients")
    _assert_hidden(outputs, [min(dobs[:6]), max(dobs[:6])])
    hdr = ["pid", "poids de naissance", "peso al nacimiento", "lieu de naissance", "出生(kg)", "出生（周）", "FNAC"]
    rows = [hdr] + [[f"P{i:03d}", str(1500 + 29 * i), str(1600 + 31 * i), ["Paris", "Lyon"][i % 2], f"{1.5 + i * 0.03:.2f}", str(28 + i % 14),
                     ["benign", "malignant"][i % 2]] for i in range(60)]
    cols = _cols(_run(_rows_csv(tmp_path, "w.csv", rows), "--rows-are-patients"))
    assert all(not cols[h]["pii"] for h in hdr[1:])


def test_digit_groups_with_unusual_separators_are_hidden(tmp_path, capsys):
    rows = [["pid", "age", "x", "sex"]] + [[f"P{i:03d}", str(20 + i), str(i % 9), "男女"[i % 2]] for i in range(30)]
    for v in ("100–1234", "100,1234", "100#1234", "100、1234", "100​1234", "100x1234", "100    1234"):
        hdr = [["pid", "age", f"病历号{v}", "sex"]] + rows[1:]
        _, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "h.csv", hdr), "--rows-are-patients")
        _assert_hidden(outputs, [v])
        sub = tmp_path / f"f{abs(hash(v))}"
        sub.mkdir()
        _, outputs = _outputs(tmp_path, capsys, _rows_csv(sub, f"化验{v}.csv", rows))
        _assert_hidden(outputs, [v])
    for sep in ("|", "+", "#", "、", "~", "    "):
        val = sep.join(["100", "1234", "5678"])
        body = [["pid", "info", "age"]] + [[f"P{i:03d}", val if i < 8 else ["本人", "家属"][i % 2], str(20 + i)] for i in range(60)]
        _, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "s.csv", body), "--rows-are-patients")
        _assert_hidden(outputs, [val])


def test_an_outcome_level_hidden_in_the_outcome_entry_is_hidden_in_section_6(tmp_path, capsys):
    rows = [["pid", "age", "y"]] + [[f"P{i:03d}", str(20 + i), y] for i, y in enumerate(["死亡"] * 10 + ["存活"] * 44 + ["Testa Personne"] * 6)]
    for args in (("--id", "pid"), ("--rows-are-patients",)):
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows), "--outcome", "y", *args)
        _assert_hidden(outputs, ["Testa Personne"])
        assert dict(profile["outcomes"][0]["levels"])["死亡"] == 10
    rows = [["pid", "eponym"]] + [[f"P{i:03d}", ["Stevens Johnson", "Crohn Disease", "Graves Disease"][i % 3]] for i in range(60)]
    assert len(_cols(_run(_rows_csv(tmp_path, "e.csv", rows), "--id", "pid"))["eponym"]["categorical"]["levels"]) == 3


def test_labs_censored_at_both_ends_with_a_unit_or_flag_on_every_value(tmp_path):
    import random
    rnd = random.Random(22)
    gens = {"pct": lambda: rnd.choices(["<0.010 ng/mL", ">50.00 ng/mL", f"{rnd.uniform(0.01, 50):.3f} ng/mL"], [3, 1, 6])[0],
            "ki67": lambda: rnd.choices(["<1%", ">90%", f"{rnd.randint(1, 90)}%"], [2, 1, 6])[0],
            "trop": lambda: rnd.choices(["<0.01", ">50", f"{rnd.uniform(0.01, 50):.2f}↑"], [3, 1, 6])[0]}
    rows = [["pid"] + list(gens)] + [[f"P{i:03d}"] + [g() for g in gens.values()] for i in range(200)]
    cols = _cols(_run(_rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients"))
    for j, k in enumerate(gens, start=1):
        assert cols[k]["type"] == "numeric" and cols[k]["censored"]["n"] == sum(1 for r in rows[1:] if r[j][0] in "<>")
        assert not any("分组区间" in h for h in cols[k]["hints"])


def test_total_and_subtotal_category_values_are_no_total_rows(tmp_path):
    rows = [["住院号", "age", "thyroidectomy"]] + [[str(100000 + i), str(20 + i % 60), ["Total", "Subtotal", "Lobectomy"][i % 3]] for i in range(80)]
    assert _run(_rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients")["total_rows"] == []
    rows = [["pid", "cost"]] + [[str(1000 + i), str(1000 + 7 * i)] for i in range(60)] + [["Total", "123456"]]
    assert [x["row"] for x in _run(_rows_csv(tmp_path, "t.csv", rows))["total_rows"]] == [61]


def test_powers_of_ten_flags_and_approximate_values_are_read_as_numbers(tmp_path):
    import random
    rnd = random.Random(12)
    v = lambda: f"{rnd.uniform(3, 15):.1f}"
    gens = {"hbv": lambda: f"{rnd.uniform(1, 9.9):.2f}×10^{rnd.randint(2, 5)} IU/mL", "sci": lambda: f"{rnd.uniform(1, 9):.1f}*10^{rnd.randint(3, 5)}",
            "wbc": lambda: rnd.choice([f"{v()}×10~9/L", f"{v()}*10^9/L"]), "glu": lambda: rnd.choice([f"{v()}↑ mmol/L", f"{v()} mmol/L"]),
            "na": lambda: rnd.choice([f"H {v()}", v()]), "k": lambda: rnd.choice([f"{v()}(偏高)", f"{v()}低", f"{v()}+", v()]),
            "cl": lambda: rnd.choice([f"{v()}* mmol/L", f"{v()} mmol/L"]), "ca": lambda: rnd.choice([f"约{v()}", f"~{v()}", f"≈{v()}", f"{v()}?"]),
            "cnt": lambda: f"{rnd.randint(1, 99)} {rnd.randint(100, 999)}"}
    rows = [["pid"] + list(gens)] + [[f"P{i:03d}"] + [g() for g in gens.values()] for i in range(120)]
    cols = _cols(_run(_rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients"))
    for k in gens:
        assert cols[k]["type"] == "numeric" and cols[k]["numeric"]["n"] == 120 and not cols[k]["pii"], k
    assert cols["hbv"]["numeric"]["min"] >= 100 and list(cols["hbv"]["numeric_as_text"]["units"]) == ["IU/mL"]
    assert cols["sci"]["numeric"]["min"] >= 1000
    assert list(cols["cl"]["numeric_as_text"]["units"]) == ["mmol/L"] and len(cols["wbc"]["numeric_as_text"]["units"]) == 1   # (×10~9/L = *10^9/L)
    assert not cols["wbc"]["numeric_as_text"]["flags"]


def test_footer_rows_and_a_units_row_are_reported(tmp_path):
    body = [[f"P{i:03d}", "男女"[i % 2], str(30 + i % 50), f"{500 + i * 3.5:.2f}"] for i in range(60)]
    hdr = ["pid", "sex", "age", "cost"]
    profile = _run(_rows_csv(tmp_path, "f.csv", [hdr] + body + [["注：↑表示偏高"], ["制表人：测甲乙", "", "审核：试丙丁"], ["打印时间：2023-01-01 10:00"]]))
    assert [x["row"] for x in profile["footer_rows"]] == [61, 62, 63] and any("表尾" in x for x in profile["problems"])
    profile = _run(_rows_csv(tmp_path, "u.csv", [hdr, ["", "", "岁", "元"]] + body))
    assert profile["unit_row"] and any("单位" in x and "第 1 行" in x for x in profile["problems"])
    profile = _run(_rows_csv(tmp_path, "t.csv", [["XX医院", "2023年", "数据"], hdr] + body))
    assert any("--skip-rows 1" in x for x in profile["problems"])


def test_year_first_two_digit_dates_stamps_and_weekday_dates(tmp_path):
    import datetime as dt
    ds = [dt.date(2019, 1, 1) + dt.timedelta(days=11 * i) for i in range(150)]
    rows = [["pid", "a_date", "stamp_date", "c_date"]] + [[f"P{i:03d}", d.strftime("%y-%m-%d"), d.strftime("%Y%m%d") + "083000", d.strftime("%a %b %d %Y")]
                                                     for i, d in enumerate(ds)]
    cols = _cols(_run(_rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients"))
    for k in ("a_date", "stamp_date", "c_date"):
        assert cols[k]["type"] == "date" and (cols[k]["date"]["min"], cols[k]["date"]["max"]) == (str(ds[0]), str(ds[-1])), k


def test_compound_measurements_with_a_dash_or_units_on_each_number(tmp_path):
    rows = [["pid", "bp", "size", "mixed", "visual", "titer"]] + [
        [f"P{i:03d}", f"{100 + i % 80}-{60 + i % 40}", f"{1 + i % 8}.5 cm x {1 + i % 5}.1 cm", f"{1 + i % 8}.5×2.1cm" if i % 2 else f"{1 + i % 8}.5cm",
         ["20/20", "20/40", "6/12"][i % 3], ["1:80", "1:160", "<1:40"][i % 3]] for i in range(150)]
    cols = _cols(_run(_rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients"))
    assert cols["bp"].get("compound") and not cols["bp"]["pii"] and any("收缩压" in h for h in cols["bp"]["hints"])
    assert cols["size"].get("compound") and not cols["size"]["pii"]
    assert any("复合测量" in h for h in cols["mixed"]["hints"])
    assert not any("收缩压" in h for h in cols["visual"]["hints"]) and not any("分组区间" in h for h in cols["titer"]["hints"])


def test_more_censored_and_missing_spellings(tmp_path):
    rows = [["pid", "lod", "x", "備註"]] + [[f"P{i:03d}", ["低于检测下限", "高于检测上限", "BLQ", "below LLOQ", f"{10 + i}.5"][i % 5],
                                            ["不清楚", "NK", "NR", "（空）", "<空>", "拒绝", f"{10 + i}.5", f"{20 + i}.5"][i % 8], ["", "複查", "轉院"][i % 3]]
                                           for i in range(80)]
    cols = _cols(_run(_rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients"))
    assert cols["lod"]["type"] == "numeric" and cols["lod"]["censored"]["n"] == 64
    assert sum(cols["x"]["disguised_missing"].values()) == 60 and cols["備註"]["type"] == "text"
    rows = [["pid", "hbsag"]] + [[f"P{i:03d}", ["R", "NR"][i % 2]] for i in range(60)]
    assert not _cols(_run(_rows_csv(tmp_path, "c.csv", rows), "--rows-are-patients"))["hbsag"]["disguised_missing"]   # "non-reactive"


@pytest.mark.parametrize("enc,rows", [
    ("cp932", [["患者番号", "性別", "年齢", "クレアチニン", "高血圧", "診断"]] + [[f"{100000 + i // 2}", "男女"[i % 2], str(30 + i % 50), "0.9", "有無"[i % 2], "肺癌"] for i in range(80)]),
    ("euc_jp", [["患者番号", "性別", "年齢", "クレアチニン", "高血圧", "診断"]] + [[f"{100000 + i // 2}", "男女"[i % 2], str(30 + i % 50), "0.9", "有無"[i % 2], "肺癌"] for i in range(80)]),
    ("euc_kr", [["환자번호", "성별", "나이", "크레아티닌", "고혈압"]] + [[f"{100000 + i // 2}", "남여"[i % 2], str(30 + i % 50), "0.9", ["예", "아니오"][i % 2]] for i in range(80)]),
    ("utf-8", [["환자번호", "성별", "나이", "크레아티닌", "고혈압"]] + [[f"{100000 + i // 2}", "남여"[i % 2], str(30 + i % 50), "0.9", ["예", "아니오"][i % 2]] for i in range(80)]),
])
def test_japanese_and_korean_files_are_decoded(tmp_path, enc, rows):
    # (round 5: bytes that are valid GBK / GB18030 are read as Chinese -- a Korean / Japanese file then gets a warning
    # that names its encoding and --encoding, never silent garbage; with --encoding it reads right)
    import csv
    path = tmp_path / "d.csv"
    with open(path, "w", encoding=enc, newline="") as fh:
        csv.writer(fh).writerows(rows)
    profile = _run(path)
    names = [c["name"] for c in profile["columns"]]
    flag = {"cp932": "cp932", "euc_jp": "euc-jp", "euc_kr": "euc-kr"}.get(enc)
    if flag:
        assert names == rows[0] or any(f"--encoding {flag}" in x for x in profile["header_issues"]), (names, profile["header_issues"])
        assert [c["name"] for c in _run(path, "--encoding", enc)["columns"]] == rows[0]
    else:
        assert names == rows[0]


def test_name_shaped_words_in_number_or_date_columns_are_no_examples(tmp_path, capsys):
    rows = [["pid", "hb", "visit_date"]] + [[f"P{i:03d}", "Testa Personne" if i < 6 else ("溶血" if i < 12 else str(90 + i)),
                                             "Testa Personne" if i < 6 else f"2023-01-{1 + i % 28:02d}"] for i in range(60)]
    _, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "d.csv", rows), "--rows-are-patients")
    _assert_hidden(outputs, ["Testa Personne"])
    assert "溶血" in outputs[0]


# ─── round 5 ─────────────────────────────────────────────────────────────────

def _gbk_rows_csv(tmp_path, name, rows, enc="gbk"):
    import csv
    path = tmp_path / name
    with open(path, "w", encoding=enc, newline="") as fh:
        csv.writer(fh).writerows(rows)
    return path


def test_gbk_files_with_few_chinese_characters_stay_gbk(tmp_path, capsys):
    # I1: GB2312 rows B0-C8 are EUC-KR's Hangul rows -- a GBK file of 男 / 女, 是 / 否 or a few names must not be read as Korean
    import random
    rnd = random.Random(59)
    names = ["鲁晨瑞", "齐龙会", "荆昌光", "宾厚福", "荣日竣", "邓千昌"]       # (strong-shaped; GBK bytes that also decode as Hangul)
    assert all("\uac00" <= ch <= "\ud7a3" for n in names for ch in n.encode("gbk").decode("euc_kr"))
    tables = {
        "sex": [["pid", "sex", "age"]] + [[f"P{i:03d}", rnd.choice("男女"), str(rnd.randint(20, 80))] for i in range(300)],
        "cn_sex": [["编号", "性别", "年龄", "血红蛋白"]] + [[f"P{i:03d}", rnd.choice("男女"), str(rnd.randint(20, 80)), str(rnd.randint(90, 160))]
                                                     for i in range(300)],
        "yesno": [["pid", "smoke", "drink"]] + [[f"P{i:03d}", rnd.choice(["是", "否"]), rnd.choice(["是", "否"])] for i in range(200)],
        "names": [["pid", "who", "sex"]] + [[f"P{i:03d}", names[i % 6], rnd.choice("男女")] for i in range(120)],
    }
    for tag, rows in tables.items():
        profile, outputs = _outputs(tmp_path, capsys, _gbk_rows_csv(tmp_path, f"{tag}.csv", rows), "--rows-are-patients")
        assert profile["source"]["encoding"] == "gbk", tag
        assert [c["name"] for c in profile["columns"]] == rows[0], tag
        assert not any("\uac00" <= ch <= "\ud7a3" for text in outputs for ch in text), tag
        _assert_hidden(outputs, names)
    # a real Korean / Japanese file: a warning naming its encoding (and it reads right with --encoding)
    kr = [["환자번호", "성별", "결과"]] + [[f"P{i}", ["남", "여"][i % 2], ["양성", "음성"][i % 3 % 2]] for i in range(12)]
    jp = [["pid", "ステータス"]] + [[f"P{i}", ["ガン", "なし"][i % 2]] for i in range(12)]
    for rows, enc, flag in ((kr, "euc_kr", "euc-kr"), (jp, "shift_jis", "cp932")):
        profile = _run(_gbk_rows_csv(tmp_path, f"{enc}.csv", rows, enc))
        assert any(f"--encoding {flag}" in x for x in profile["header_issues"]), profile["header_issues"]


def test_a_visit_index_is_no_patient_key_and_auto_keys_count_exactly(tmp_path, capsys):
    # I2: a column named like an ID holding a visit index per patient splits every patient into k "patients" (round 5d: an
    # index from 0 or a labelled one; bare 1..k cannot be told from patients numbered 1..N and is read as patient numbers)
    fam = ["王一", "李三", "张五", "刘七", "陈九", "杨八", "赵六", "黄四", "周十", "吴二", "徐一", "孙三", "马五", "朱七", "胡九", "郭八",
           "何六", "高四", "林十", "罗二"]
    for key, fmt in (("ID", "{v0}"), ("编号", "第{v}次"), ("record_id", "V{v}"), ("study_id", "{v0:02d}")):
        rows = [[key, "家属", "sex", "hb"]] + [[fmt.format(v=v + 1, v0=v), fam[i], "男女"[i % 2], str(100 + i + v)] for i in range(20)
                                              for v in range(12)]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "v.csv", rows))
        assert key not in profile["privacy_units"]["columns"], key
        _assert_hidden(outputs, fam)
    # pre / post design under the auto key: a level held by 6 different patients (2 with both rows, 4 baseline only) is shown
    import random
    rnd = random.Random(524)
    rows = [["patient_id", "visit", "histology"]]
    for p in range(120):
        h, k = ("腺鳞癌", 2 if p < 2 else 1) if p < 6 else (rnd.choice(["腺癌", "鳞癌"]), 2 if rnd.random() < 0.75 else 1)
        rows += [[f"P{p:04d}", ["baseline", "fu"][v], h] for v in range(k)]
    profile = _run(_rows_csv(tmp_path, "pairs.csv", rows))
    assert profile["privacy_units"]["mode"] == "patient" and profile["privacy_units"]["source"] == "auto"
    assert dict(_cols(profile)["histology"]["categorical"]["levels"]).get("腺鳞癌") == 8


def test_strong_names_anywhere_in_a_column_name_are_masked(tmp_path, capsys):
    # I3: the name is masked wherever it stands; ordinary clinical names (also eponyms) are kept
    heads = ["王一二左眼", "3床王一二", "患儿王一二", "王一二与李三四", "Mary Fakename CT", "OD John Testperson", "WANG Yier CT",
             "John_Testperson", "Dr_Testperson", "Testa Personne CT"]
    for h in heads:
        rows = [["pid", "age", h]] + [[f"P{i:03d}", str(30 + i % 40), f"{1 + i % 9}.5"] for i in range(40)]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "h.csv", rows), "--rows-are-patients")
        _assert_hidden(outputs, [x for x in ("王一二", "李三四", "Mary Fakename", "John Testperson", "WANG Yier", "Testperson", "Testa Personne")
                                 if x.replace(" ", "") in h.replace(" ", "").replace("_", "")])
        assert any("列3（含人名）" in x for x in profile["problems"]), (h, profile["problems"][:3])
    ok = ["张力", "Blood Pressure", "王氏评分", "张氏分型", "白天心率", "周平均血压", "焦虑评分", "白介素6", "高中文化程度", "结石大小",
          "Kellgren Lawrence", "Cobb Angle", "Heart Rate", "Child Pugh"]
    rows = [["pid"] + ok] + [[f"P{i:03d}"] + [str(1 + i % 9) for _ in ok] for i in range(40)]
    assert [c["name"] for c in _run(_rows_csv(tmp_path, "ok.csv", rows), "--rows-are-patients")["columns"]] == ["pid"] + ok


def test_unit_flag_and_example_strings_are_gated(tmp_path, capsys):
    # I4: a "unit" made of unit words ("Lin Yu", "周天元") is never printed; known units always are; another unit only
    # with a patient unit and 5+ patients
    for nm in ("Lin Yu", "Du Min", "周天元", "Hu Ling"):
        for form in ("5.6 {}", "5.6{}", "<0.5 {}", "5.6↑ {}", "5.6 {} H", "60{}以上"):
            for reps in (1, 6):
                rows = [["pid", "crp"]] + [[f"P{i:03d}", form.format(nm) if i < reps else f"{1 + i % 30}.5"] for i in range(80)]
                for args in ((), ("--rows-are-patients",)):
                    _, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "u.csv", rows), *args)
                    _assert_hidden(outputs, [nm])
    rows = [["pid", "glu", "hb", "gain"]] + [[f"P{i:03d}", f"{4 + i % 5}.{i % 9} mmol/L" + ("↑" if i % 7 == 0 else ""), f"{100 + i} g/L",
                                              f"{i % 3}.{i % 7}" + (" kg/wk" if i < 8 else "")] for i in range(60)]
    path = _rows_csv(tmp_path, "k.csv", rows)
    for args, rare in (((), False), (("--rows-are-patients",), True)):
        cols = _cols(_run(path, *args))
        assert list(cols["glu"]["numeric_as_text"]["units"]) == ["mmol/L"] and cols["glu"]["numeric_as_text"]["flags"] == {"↑": 9}
        assert list(cols["hb"]["numeric_as_text"]["units"]) == ["g/L"] and cols["hb"]["numeric_as_text"]["examples"]
        assert ("kg/wk" in cols["gain"]["numeric_as_text"]["units"]) == rare and cols["gain"]["numeric"]["n"] == 60
    rows[1:4] = [[r[0], r[1], r[2], r[3].replace(" kg/wk", "")] for r in rows[1:4]]       # kg/wk on 5 rows -> 3 rows
    rows[1:6] = [[r[0], r[1], r[2], r[3].split(" ")[0]] for r in rows[1:6]]
    assert "kg/wk" not in _cols(_run(_rows_csv(tmp_path, "k3.csv", rows), "--rows-are-patients"))["gain"]["numeric_as_text"]["units"]


def test_flag_words_approximate_and_locale_numbers_are_counted(tmp_path):
    # I5: the abnormal / approximate values carry the words -- they are numbers in the statistics, with a note
    import random
    rnd = random.Random(503)
    forms = {"high": lambda x: f"{x} High", "paren": lambda x: f"{x} (High)", "a": lambda x: f"{x} A", "crit": lambda x: f"{x} (危急值)",
             "abn": lambda x: f"{x}（异常）", "yang": lambda x: f"阳性 {x}", "yue": lambda x: f"约{x}mmol/L", "zuoyou": lambda x: f"{x}左右",
             "en": lambda x: f"approx. {x} mL", "tilde": lambda x: f"~{x}"}
    truth, rows = {k: [] for k in forms}, [["pid"] + list(forms)]
    for i in range(150):
        row = [f"P{i:03d}"]
        for k, f in forms.items():
            x = round(rnd.uniform(2.0, 15.0), 1)
            truth[k].append(x)
            row.append(f(x) if x > 6.1 else f"{x}")
        rows.append(row)
    profile = _run(_rows_csv(tmp_path, "q.csv", rows))
    for k in forms:
        s = _cols(profile)[k]["numeric"]
        assert _cols(profile)[k]["type"] == "numeric" and s["n"] == 150 and (s["min"], s["max"]) == (min(truth[k]), max(truth[k])), k
    assert any("约数" in x and "yue" in x and "zuoyou" in x for x in profile["problems"])
    assert any("异常标记" in x and "high" in x for x in profile["problems"])
    path = tmp_path / "eu.csv"
    path.write_text("pid;k;kosten;cost;crea;thou\n" + "".join(
        f"P{i};{3 + i % 3},{i % 10} mmol/L;{10 + i}.{345 + i},{i % 90 + 10};{10 + i},{345 + i}.{i % 90 + 10}元;{['0,925', '1,125', '0,87'][i % 3]};"
        f"{'1,' + str(200 + i) if i % 2 else 1200 + i}\n" for i in range(60)), encoding="utf-8")
    cols = _cols(_run(path, "--rows-are-patients"))
    assert (cols["k"]["numeric"]["min"], cols["k"]["numeric"]["max"]) == (3.0, 5.9)
    assert cols["kosten"]["numeric"]["min"] == 10345.1 and cols["cost"]["numeric"]["max"] == 69404.69
    assert (cols["crea"]["numeric"]["min"], cols["crea"]["numeric"]["max"]) == (0.87, 1.125)
    assert (cols["thou"]["numeric"]["min"], cols["thou"]["numeric"]["max"]) == (1200, 1259)
    for k in ("k", "kosten", "cost", "crea", "thou"):
        assert cols[k]["type"] == "numeric" and cols[k]["numeric"]["n"] == 60, k


# ─── round 5b (the r5 verifier's open items and regressions) ─────────────────

def _bytes_readings(names, enc):
    """Every East-Asian reading of the bytes of `names` written in `enc` (a name printed as mojibake is still the name)."""
    out = set(names)
    for nm in names:
        for e in ("gbk", "gb18030", "big5", "euc_kr", "cp932", "euc_jp"):
            try:
                out.add(nm.encode(enc).decode(e))
            except UnicodeDecodeError:
                pass
    return out


def test_korean_japanese_and_big5_files_warn_with_their_encoding_and_print_no_misread_text(tmp_path, capsys):
    # I1: Korean lab symbols (℃ ※ ○ ·), Hanja headers, an ASCII header with only 남/여: a warning naming euc-kr and no text
    # value of the wrong reading; kanji-only Shift-JIS / EUC-JP: the right encoding named (never latin-1 / euc-kr); small Big5
    kr = {"symbols": [["환자번호", "성별", "체온(℃)", "비고"]] + [[f"{1000 + i}", "남여"[i % 2], "36.5", ["정상", "※재검", "○"][i % 3]] for i in range(60)],
          "middot": [["환자번호", "성별", "진단"]] + [[f"{1000 + i}", "남여"[i % 2], ["고혈압·당뇨", "폐암", "위암"][i % 3]] for i in range(60)],
          "hanja": [["患者番號", "性別", "診斷"]] + [[f"{1000 + i}", "男女"[i % 2], ["高血壓", "糖尿病"][i % 2]] for i in range(60)],
          "ascii_sex": [["pid", "sex", "age"]] + [[f"P{i}", ["남", "여"][i % 2], str(30 + i)] for i in range(60)]}
    for tag, rows in kr.items():
        profile = _run(_gbk_rows_csv(tmp_path, f"kr_{tag}.csv", rows, "euc_kr"), "--rows-are-patients")
        assert any("--encoding euc-kr" in x for x in profile["header_issues"]), (tag, profile["header_issues"])
        assert profile["privacy_units"]["mode"] == "encoding", tag
        assert not [lab for c in profile["columns"] for lab, _ in ((c.get("categorical") or {}).get("levels") or []) if not lab.isascii()], tag
    jp = {"kanji": [["患者番号", "性別", "年齢", "診断"]] + [[f"{1000 + i}", "男女"[i % 2], str(30 + i % 50), ["肺癌", "胃癌", "肝癌"][i % 3]] for i in range(80)],
          "small": [["pid", "性別", "喫煙"]] + [[f"P{i}", "男女"[i % 2], ["有", "無"][i % 2]] for i in range(20)]}
    for tag, rows in jp.items():
        for enc, flag in (("shift_jis", "cp932"), ("euc_jp", "euc-jp")):
            issues = _run(_gbk_rows_csv(tmp_path, f"jp_{tag}_{enc}.csv", rows, enc))["header_issues"]
            assert any(f"--encoding {flag}" in x for x in issues), (tag, enc, issues)
            assert not any(w in x for x in issues for w in ("--encoding latin-1", "--encoding cp1252", "--encoding euc-kr")), (tag, enc)
    for rows in ([["pid", "sex", "age"]] + [[f"P{i}", "男女"[i % 2], str(30 + i)] for i in range(40)],
                 [["pid", "性別", "年齡"]] + [[f"P{i}", "男女"[i % 2], str(30 + i)] for i in range(40)]):
        profile = _run(_gbk_rows_csv(tmp_path, "b5.csv", rows, "big5"), "--rows-are-patients")
        assert profile["source"]["encoding"].startswith("big5") and [c["name"] for c in profile["columns"]] == rows[0]
        assert sorted(dict(_cols(profile)[rows[0][1]]["categorical"]["levels"])) == ["女", "男"]
    # a Korean name column (header 이름 or neutral, also only two names) is never printed, in any reading of its bytes
    names = ["김민수", "이영희", "박지현", "최성호", "정은진"]
    for hdr, nn in (("이름", 5), ("who", 5), ("who", 2)):
        rows = [["pid", hdr, "age"]] + [[f"P{i:03d}", names[i % nn], str(30 + i % 40)] for i in range(100)]
        _, outputs = _outputs(tmp_path, capsys, _gbk_rows_csv(tmp_path, "kn.csv", rows, "euc_kr"), "--rows-are-patients")
        _assert_hidden(outputs, _bytes_readings(names[:nn], "euc_kr"))
    # a GBK file of names in rows B0-C8 (EUC-KR's Hangul rows): no hint; following a wrong --encoding euc-kr prints no name
    cn = ["鲁晨瑞", "齐龙会", "荆昌光", "宾厚福", "荣日竣", "邓千昌"]
    rows = [["pid", "who", "sex"]] + [[f"P{i:03d}", cn[i % 6], "男女"[i % 2]] for i in range(120)]
    path = _gbk_rows_csv(tmp_path, "cn.csv", rows)
    profile, outputs = _outputs(tmp_path, capsys, path, "--rows-are-patients")
    assert not any("--encoding" in x for x in profile["header_issues"]) and profile["privacy_units"]["mode"] == "asserted"
    _assert_hidden(outputs, _bytes_readings(cn, "gbk"))
    profile, outputs = _outputs(tmp_path, capsys, path, "--rows-are-patients", "--encoding", "euc-kr")
    _assert_hidden(outputs, _bytes_readings(cn, "gbk"))


def test_more_visit_labels_are_no_patient_key_and_a_crossed_patient_id_is(tmp_path, capsys):
    # I2: 第k次 / V-k / visit_k / kh / FUk / C{k}D1 / V001 / M0, M1, M3 ... / bare 0..23 sorted by visit: never the key
    fam = ["王一", "李三", "张五", "刘七", "陈九", "杨八", "赵六", "黄四", "周十", "吴二", "徐一", "孙三"]
    gaps = [0, 1, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60, 72, 84, 96, 108, 120, 132, 144, 156, 168, 180]
    for fmt, k, n_pat, by_visit in (("第{v}次", 12, 8, False), ("V-{v}", 15, 12, False), ("visit_{v}", 10, 3, True), ("{v}h", 24, 12, False),
                                    ("FU{v}", 12, 12, True), ("C{v}D1", 12, 6, False), ("V{v:03d}", 12, 12, False), ("M{g}", 24, 10, False),
                                    ("{v0}", 24, 12, True), ("{g}", 24, 12, False)):
        recs = sorted(((p, v) for p in range(n_pat) for v in range(k)), key=(lambda t: (t[1], t[0])) if by_visit else None)
        rows = [["ID", "家属", "sex", "hb"]] + [[fmt.format(v=v + 1, v0=v, g=gaps[v]), fam[p], "男女"[p % 2], str(100 + v)] for p, v in recs]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "v.csv", rows))
        assert "ID" not in profile["privacy_units"]["columns"], fmt
        _assert_hidden(outputs, fam[:n_pat])
    # a real patient_id next to an ID-named visit column in a long table (12 patients x 15 visits): patient_id is the key
    emp = [f"测{ch}科技有限公司" for ch in "甲乙丙丁戊己庚辛壬癸子丑"]
    for fmt in ("V-{v}", "第{v}次", "{v0}", "{v}"):
        rows = [["patient_id", "编号", "工作单位", "histology"]] + [[f"P{p:03d}", fmt.format(v=v + 1, v0=v), emp[p], "罕见型" if p == 0 else "腺癌"]
                                                                  for p in range(12) for v in range(15)]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "long.csv", rows))
        _assert_hidden(outputs, emp + ["罕见型"])
        if fmt == "{v}":
            # round 5d: a bare 1..15 cannot be told from patients numbered 1..15 -- both columns qualify, so neither is used
            assert profile["privacy_units"]["mode"] == "none" and profile["privacy_units"]["ambiguous"] == ["patient_id", "编号"]
            continue
        assert profile["privacy_units"]["columns"] == ["patient_id"], fmt
        assert dict(_cols(profile)["histology"]["categorical"]["levels"]) == {"腺癌": 165}


def test_more_name_shapes_in_column_names_are_masked_and_eponyms_are_not(tmp_path, capsys):
    # I3: a space after the surname, 'Surname, Given', + & · （） joiners, lower case with a common given name, a surname in
    # capitals, a given name run into a surname: the column name is masked; eponyms / clinical names stay
    heads = ["王 一二左眼", "Fakename, Mary CT", "Mary+Fakename", "Mary·Fakename", "Mary（Fakename）", "mary fakename ct", "john_testperson",
             "John TESTPERSON", "TESTPERSON John", "MaryFakename_CT"]
    for h in heads:
        rows = [["patient_id", "sex", h]] + [[f"P{k // 2:03d}", "男女"[k % 2], f"{5 + k % 20}.5"] for k in range(120)]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "h.csv", rows))
        assert [c["name"] for c in profile["columns"]][2] == "列3", h
        _assert_hidden(outputs, [h, "一二", "Fakename", "FAKENAME", "fakename", "testperson", "TESTPERSON", "Testperson"])
    for h in ("柏林定义", "Nissen Fundoplication", "Roux Limb", "Modic Change", "Bloom Richardson", "Van Nuys", "Gail Model", "Kaplan Meier",
              "王氏评分", "白天血压", "张力", "Blood Pressure", "xue_ya", "xin_lv", "H. Pylori IgG"):
        rows = [["pid", "sex", h]] + [[f"P{k:03d}", "男女"[k % 2], str(k % 9)] for k in range(60)]
        assert [c["name"] for c in _run(_rows_csv(tmp_path, "ok.csv", rows), "--rows-are-patients")["columns"]][2] == h, h


def test_labels_with_a_flag_word_and_a_small_number_stay_categorical(tmp_path):
    # I5 regression: HPV types, IHC codes, frequency / duration labels are categories -- not numbers with their reference
    # category ("阴性", "正常", "从不") dropped from n
    import random
    rnd = random.Random(2)
    cats = {"hpv": ["阳性 16", "阳性 18", "阳性 52", "阴性"], "her2": ["阴性 0", "阴性 1", "阳性 2", "阳性 3"], "freq": ["约1次/周", "约3次/月", "从不"],
            "dur": ["近1月", "近2周", "半年"], "grade": ["High 3", "Low 1", "High 2"], "abn": ["异常 1", "异常 2", "正常"]}
    rows = [["pid"] + list(cats)] + [[f"P{i:03d}"] + [rnd.choice(v) for v in cats.values()] for i in range(200)]
    cols = _cols(_run(_rows_csv(tmp_path, "lab.csv", rows), "--rows-are-patients"))
    for k, vals in cats.items():
        lv = dict(cols[k]["categorical"]["levels"])
        assert cols[k]["type"] == "categorical" and set(lv) == set(vals) and sum(lv.values()) == 200, k
    # a lab value with a flag word on its abnormal values (many different numbers) is still numeric
    rows = [["pid", "glu"]] + [[f"P{i:03d}", f"{x} 偏高" if x > 6.1 else str(x)] for i, x in enumerate(round(rnd.uniform(3, 15), 1) for _ in range(100))]
    assert _cols(_run(_rows_csv(tmp_path, "glu.csv", rows)))["glu"]["numeric"]["n"] == 100


# ─── round 5c: the deterministic automatic-patient-key rule ───────────────────

_FAM12 = ["王一", "李三", "张五", "刘七", "陈九", "杨八", "赵六", "黄四", "周十", "吴二", "徐一", "孙三", "马五", "朱七", "胡九", "郭八",
          "何六", "高四", "林十", "罗二", "宋一", "郑三", "谢五", "韩七", "唐九", "冯八", "于六", "董四", "萧十", "程二"]
_EMP30 = [f"测{ch}科技有限公司" for ch in "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥天地玄黄宇宙洪荒"]


@pytest.mark.parametrize("n_pat,k", [(12, 15), (16, 20), (20, 30)])
@pytest.mark.parametrize("by_visit", [False, True])
def test_a_real_patient_id_in_a_long_table_is_the_automatic_key(tmp_path, capsys, n_pat, k, by_visit):
    # rule 4: no "at least as many values as the median rows per value" any more -- 12 x 15, 16 x 20, 20 x 30 are accepted
    recs = sorted(((p, v) for p in range(n_pat) for v in range(k)), key=(lambda t: (t[1], t[0])) if by_visit else None)
    rows = [["patient_id", "工作单位", "histology", "sex", "hb"]] + [
        [f"P{p + 1:03d}", _EMP30[p], "罕见型" if p == 0 else ["腺癌", "鳞癌"][p % 2], "男女"[p % 2], str(100 + v)] for p, v in recs]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "long.csv", rows))
    assert profile["privacy_units"]["mode"] == "patient" and profile["privacy_units"]["columns"] == ["patient_id"]
    lv = dict(_cols(profile)["histology"]["categorical"]["levels"])
    assert lv == {"腺癌": k * ((n_pat - 1) // 2), "鳞癌": k * (n_pat // 2)}
    _assert_hidden(outputs, _EMP30[:n_pat] + ["罕见型"])


_ROMAN12 = "I II III IV V VI VII VIII IX X XI XII".split()
_CN12 = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
_VISIT_FORMATS = {"第一次": lambda v: f"第{_CN12[v]}次", "随访一": lambda v: f"随访{_CN12[v]}", "letters": lambda v: "ABCDEFGHIJKL"[v],
                  "roman": lambda v: _ROMAN12[v], "baseline_wk": lambda v: "baseline" if v == 0 else f"wk{4 * v}",
                  "baseline_week": lambda v: "Baseline" if v == 0 else f"Week {v}", "V-k": lambda v: f"V-{v + 1}", "FUk": lambda v: f"FU{v + 1}",
                  "PODk": lambda v: f"POD{v}", "第k次": lambda v: f"第{v + 1}次", "Dk": lambda v: f"D{v + 1}", "0..k": lambda v: str(v)}


@pytest.mark.parametrize("fmt", list(_VISIT_FORMATS))
@pytest.mark.parametrize("key", ["patient_id", "编号", "住院号", "subject_id"])
def test_an_id_named_column_of_visit_labels_is_never_the_key(tmp_path, capsys, fmt, key):
    # rule 2: visit / ordinal values disqualify the column whatever its name; no other key -> no text value, and the one
    # no-unit line names the column and --id
    rows = [[key, "家属", "工作单位", "sex"]] + [[_VISIT_FORMATS[fmt](v), _FAM12[p], _EMP30[p], "男女"[p % 2]] for p in range(12) for v in range(12)]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "v.csv", rows))
    pu = profile["privacy_units"]
    assert pu["mode"] == "none" and pu["columns"] == [] and pu["visit_valued"] == [key]
    _assert_hidden(outputs, _FAM12 + _EMP30[:12])
    lines = [x for x in profile["problems"] if x.startswith("无法区分患者")]
    assert len(lines) == 1 and key in lines[0] and "就诊/随访序号" in lines[0] and "--id" in lines[0]
    # next to a real patient_id it is no competitor: patient_id is the key, the visit column gets its own line
    rows2 = [["patient_no"] + rows[0]] + [[f"P{i // 12 + 1:03d}"] + r for i, r in enumerate(rows[1:])]
    profile = _run(_rows_csv(tmp_path, "v2.csv", rows2))
    assert profile["privacy_units"]["columns"] == ["patient_no"]
    assert any(x.startswith(f"{key}：") and "就诊/随访序号" in x for x in profile["problems"]), profile["problems"]


@pytest.mark.parametrize("a,b", [("patient_id", "subject_id"), ("MRN", "病案号"), ("pid", "case_id")])
def test_two_qualifying_columns_give_no_key_and_one_line(tmp_path, capsys, a, b):
    # rule 3: two columns qualify -> none is used (also not --rows-are-patients' rows); one line names both and --id
    rows = [[a, b, "家属", "sex"]] + [[f"P{p + 1:03d}", f"Z{9000 + 2 * p + v % 2}", _FAM12[p], "男女"[p % 2]] for p in range(12) for v in range(4)]
    path = _rows_csv(tmp_path, "two.csv", rows)
    for args in ((), ("--rows-are-patients",)):
        profile, outputs = _outputs(tmp_path, capsys, path, *args)
        assert profile["privacy_units"]["mode"] == "none" and profile["privacy_units"]["ambiguous"] == [a, b], args
        _assert_hidden(outputs, _FAM12)
        lines = [x for x in profile["problems"] if x.startswith("无法区分患者")]
        assert len(lines) == 1 and a in lines[0] and b in lines[0] and f"--id {a}" in lines[0], (args, profile["problems"])
        assert not any(x.startswith(f"{a}：") or x.startswith(f"{b}：") for x in profile["problems"])
    profile = _run(path, "--id", b)
    assert profile["privacy_units"]["columns"] == [b] and sorted(dict(_cols(profile)["sex"]["categorical"]["levels"])) == ["女", "男"]


@pytest.mark.parametrize("name", ["住院号_第2次", "病案号(入院)", "患者编号_随访", "patient_id_visit", "MRN_sample"])
def test_a_patient_id_name_with_a_visit_word_is_never_the_key(tmp_path, capsys, name):
    # rule 1: a visit / time / sample word in the name disqualifies it, whatever its values
    rows = [[name, "家属", "sex"]] + [[f"P{p + 1:03d}", _FAM12[p], "男女"[p % 2]] for p in range(20) for _ in range(4)]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "n.csv", rows))
    assert profile["privacy_units"]["mode"] == "none"
    _assert_hidden(outputs, _FAM12)


def test_visit_label_value_sets_and_patient_codes():
    yes = [[f"第{c}次" for c in _CN12], [f"随访{c}" for c in _CN12[:11]], list("ABCDEFGHIJKL"), _ROMAN12,
           ["baseline"] + [f"wk{2 * v}" for v in range(1, 12)], ["baseline"] + [f"week {v}" for v in range(1, 12)], [f"V-{v}" for v in range(1, 13)],
           [f"FU{v}" for v in range(1, 13)], [f"POD{v}" for v in range(14)], [f"visit_{v}" for v in range(1, 13)], [str(v) for v in range(15)],
           ["0", "1", "3", "6", "9", "12", "18", "24", "36", "48", "60"], [f"C{v}D1" for v in range(1, 13)]]
    no = [[f"P{v:03d}" for v in range(1, 40)], [f"ZY{v:06d}" for v in range(1, 40)], [f"T{v:03d}" for v in range(1, 41)],
          [str(v) for v in range(1, 151)], [f"{v:03d}" for v in range(1, 151)], [f"A{2000 + v}" for v in range(40)], _FAM12,
          [str(v) for v in range(1, 13)], [str(v) for v in range(1, 101)]]
    assert all(dp._visit_labels(v) for v in yes)
    assert not any(dp._visit_labels(v) for v in no)


# ─── round 5d: more visit / sample label shapes; patients numbered 1..N ───────

_CN_ORD12 = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
_ORD_WORDS = "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split()
_CITY30 = [f"测试{ch}市" for ch in "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥天地玄黄宇宙洪荒"]
_MORE_VISIT_FORMATS = {
    "第k次随访": lambda v: f"第{v + 1}次随访", "第一次随访": lambda v: f"第{_CN_ORD12[v]}次随访", "随访第k次": lambda v: f"随访第{v + 1}次",
    "第k次复查": lambda v: f"第{v + 1}次复查", "第k次化疗": lambda v: f"第{v + 1}次化疗", "第k次住院": lambda v: f"第{v + 1}次住院",
    "第k次访视": lambda v: f"第{v + 1}次访视", "第k次门诊": lambda v: f"第{v + 1}次门诊", "化疗第k周期": lambda v: f"化疗第{v + 1}周期",
    "Visit k (Week 2k)": lambda v: f"Visit {v + 1} (Week {2 * v + 2})", "First visit": lambda v: f"{_ORD_WORDS[v].capitalize()} visit",
    "ordinal words": lambda v: _ORD_WORDS[v], "Visit A": lambda v: f"Visit {'ABCDEFGHIJKL'[v]}", "Session k": lambda v: f"Session {v + 1}",
    "Dose k": lambda v: f"Dose {v + 1}", "Sample k": lambda v: f"Sample {v + 1}", "标本k": lambda v: f"标本{v + 1}",
    "Pre / Postk": lambda v: "Pre" if v == 0 else f"Post{v}", "VkD1": lambda v: f"V{v + 1}D1", "Vk.0": lambda v: f"V{v + 1}.0",
    "Fxk": lambda v: f"Fx{v + 1}", "随访k（电话）": lambda v: f"随访{v + 1}（电话）", "Blood sample k": lambda v: f"Blood sample {v + 1}",
    "0..k": lambda v: str(v), "0, 1, 3, 6 ..": lambda v: str([0, 1, 3, 6, 9, 12, 18, 24, 30, 36, 48, 60][v]),
}


@pytest.mark.parametrize("fmt", list(_MORE_VISIT_FORMATS))
@pytest.mark.parametrize("by_visit", [False, True])
def test_more_visit_and_sample_label_shapes_are_never_the_key(tmp_path, capsys, fmt, by_visit):
    # rule 2 (round 5d): a value is read as numbers and visit / time / sample words -- 第1次随访, 随访第3次, 化疗第2周期, Visit 1
    # (Week 2), First visit, Visit A, Session / Dose / Sample k, 标本k, Pre / Post1, V1D1, V1.0, Fx1 -- never the key; the family
    # names, employers and cities copied down a patient's rows are never printed
    key = ["patient_id", "pid", "subject_id", "患者编号", "住院号", "MRN", "ID", "case_id", "病案号", "研究编号"][len(fmt) % 10]
    recs = sorted(((p, v) for p in range(12) for v in range(12)), key=(lambda t: (t[1], t[0])) if by_visit else None)
    rows = [[key, "家属", "工作单位", "city", "sex"]] + [[_MORE_VISIT_FORMATS[fmt](v), _FAM12[p], _EMP30[p], _CITY30[p], "男女"[p % 2]]
                                                       for p, v in recs]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "v.csv", rows))
    pu = profile["privacy_units"]
    assert pu["mode"] == "none" and pu["visit_valued"] == [key], (fmt, pu)
    _assert_hidden(outputs, _FAM12 + _EMP30[:12] + _CITY30[:12])
    lines = [x for x in profile["problems"] if x.startswith("无法区分患者")]
    assert len(lines) == 1 and key in lines[0] and "--id" in lines[0]
    rows2 = [["patient_no"] + rows[0]] + [[f"P{p + 1:03d}"] + r for (p, _), r in zip(recs, rows[1:])]
    assert _run(_rows_csv(tmp_path, "v2.csv", rows2))["privacy_units"]["columns"] == ["patient_no"]


def test_visit_label_mixes_with_a_few_variant_values_are_still_visit_labels(tmp_path, capsys):
    # tolerance (round 5d): V1..V10 + V3a / V5b, 第1..10次 + 第k次(补), Day 1..14 + Day k repeat, V1..V20 + V5.1 / V9.1 / V12.1,
    # 1..12 + 失访 / 死亡 -- still visit labels, so the column is no key and no per-patient text prints
    mixes = [[f"V{i}" for i in range(1, 11)] + ["V3a", "V5b"], [f"第{i}次" for i in range(1, 11)] + ["第3次(补)", "第5次(补)"],
             [f"Day {i}" for i in range(1, 15)] + ["Day 3 repeat", "Day 7 repeat"], [f"V{i}" for i in range(1, 21)] + ["V5.1", "V9.1", "V12.1"],
             [str(i) for i in range(1, 13)] + ["失访", "死亡"]]
    for vals in mixes:
        assert dp._visit_labels(vals), vals[-1]
        rows = [["patient_id", "工作单位", "sex"]] + [[v, _EMP30[p], "男女"[p % 2]] for p in range(12) for v in vals]
        profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "mix.csv", rows))
        assert profile["privacy_units"]["mode"] == "none", vals[-1]
        _assert_hidden(outputs, _EMP30[:12])


_NUMBERED = {"1..N": lambda p: str(p + 1), "001..": lambda p: f"{p + 1:03d}", "0001..": lambda p: f"{p + 1:04d}",
             "1, 4, 7 ..": lambda p: str(1 + 3 * p), "2..N+1": lambda p: str(p + 2), "#1..": lambda p: f"#{p + 1}", "No.1..": lambda p: f"No.{p + 1}",
             "S1..": lambda p: f"S{p + 1}", "C01..": lambda p: f"C{p + 1:02d}"}


@pytest.mark.parametrize("style", list(_NUMBERED))
@pytest.mark.parametrize("n_pat,k", [(12, 15), (16, 20), (20, 30), (30, 3), (11, 25)])
def test_patients_numbered_from_one_are_the_automatic_key(tmp_path, capsys, style, n_pat, k):
    # rule 2 names only a 0..k run: patients numbered 1..N, 001..0NN, 1 / 4 / 7 ..., #1, No.1, S1, C01 in long tables are the
    # key (rule 4), every value one patient: a level held by 5+ patients is printed with its row count, a one-patient text never
    name = ["patient_id", "住院号", "MRN", "患者编号", "ID"][(n_pat + k) % 5]
    rows = [[name, "visit", "工作单位", "histology", "sex"]] + [
        [_NUMBERED[style](p), f"V{v + 1}", _EMP30[p], "罕见型" if p == 0 else ["腺癌", "鳞癌"][p % 2], "男女"[p % 2]]
        for p in range(n_pat) for v in range(k)]
    profile, outputs = _outputs(tmp_path, capsys, _rows_csv(tmp_path, "num.csv", rows))
    pu = profile["privacy_units"]
    assert pu["mode"] == "patient" and pu["columns"] == [name], (style, pu)
    want = {lab: k * n for lab, n in (("腺癌", (n_pat - 1) // 2), ("鳞癌", n_pat // 2)) if n >= 5}
    assert dict(_cols(profile)["histology"]["categorical"]["levels"]) == want
    _assert_hidden(outputs, _EMP30[:n_pat] + ["罕见型"])


def test_patients_numbered_from_zero_are_a_visit_index_and_padded_codes_are_not():
    # rule 2: a 0..k run (or a schedule from 0, days -1 / 0 / 1 ...) is a visit index -- "000".."039" are codes; the probe's
    # code-like shapes C1, S1, Q1, E1, R1, No.1, #1, T001, D001 are patient codes (only "T" / "D" with no zero padding wider
    # than needed, "Fx" and the visit words are labels)
    assert dp._visit_labels([str(p) for p in range(12)]) and dp._visit_labels([str(p) for p in range(-1, 14)])
    assert not dp._visit_labels([f"{p:03d}" for p in range(40)])
    for fmt in ("C{}", "S{}", "Q{}", "E{}", "R{}", "No.{}", "#{}", "T{:03d}", "D{:03d}", "Case {}", "第{}例", "Study-{:03d}", "PT{:02d}"):
        assert not dp._visit_labels([fmt.format(p) for p in range(1, 13)]), fmt
    for fmt in ("T{}", "D{:02d}", "Fx{}", "Tx{}", "{}st", "Wk {}", "{}个月", "第{}天", "第{}周期", "术后{}周"):
        assert dp._visit_labels([fmt.format(p) for p in range(1, 13)]), fmt
