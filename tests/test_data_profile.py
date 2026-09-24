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
                      "non_events", "minority_count", "numeric", "time", "notes"}
    assert o["time"]["column"] == "months" and o["time"]["n_valid"] == N

    text = dp.render_markdown(with_outcome)
    section = text.split("## 9.")[1].split("## 10.")[0]
    assert "事件（`1`）12 例" in section
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
