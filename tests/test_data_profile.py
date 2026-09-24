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
    assert "12..5" in hb["numeric_as_text"]["examples"]

    d = cols["surgery_date"]                                     # dates
    assert d["type"] == "date" and d["date"]["n_unparseable"] == 2
    assert set(d["date"]["unparseable_examples"]) == {"2024-13-45", "昨天"}

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
    assert profile["source"]["sheet"] == "2023" and profile["source"]["sheets"] == ["说明", "2023"]
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
    ("出生日期", True), ("DOB", True), ("date_of_birth", True), ("病理号", True),
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


def test_unclosed_quote_is_an_error_not_a_silently_short_file(tmp_path):
    path = _csv(tmp_path, "d.csv", 'a,b\n1,"x\n2,y\n3,z\n')
    with pytest.raises(SystemExit, match="引号不配对"):
        _run(path)


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


def test_an_outcome_is_never_typed_as_an_id(tmp_path):
    rows = ["cost"] + [str(10000 + 37 * i) for i in range(30)]
    profile = _run(_csv(tmp_path, "d.csv", "\n".join(rows) + "\n"), "--outcome", "cost")
    assert _cols(profile)["cost"]["type"] == "numeric"
    assert profile["outcomes"][0]["kind"] == "numeric"


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
