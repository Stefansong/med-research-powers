import os
import sys
import warnings

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
pytest.importorskip("PIL")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "skills", "figure-generation", "scripts"))
import pub_style  # noqa: E402


@pytest.fixture
def no_arial(monkeypatch):
    """Simulate a machine without Arial/Helvetica regardless of the real font set."""
    monkeypatch.setattr(pub_style, "_available_font_names", lambda: {"DejaVu Sans", "Liberation Sans"})
    monkeypatch.setattr(pub_style, "_FONT_WARNED", False)
    yield


def test_setup_without_arial_warns_exactly_once(no_arial):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pub_style.setup(journal="nature")
        pub_style.setup(journal="lancet")
        pub_style.setup(journal="jama", single_column=False)
    font_warnings = [w for w in caught if "Arial" in str(w.message)]
    assert len(font_warnings) == 1
    assert plt.rcParams["font.family"] == ["sans-serif"]
    assert plt.rcParams["font.sans-serif"][:2] == ["Arial", "Helvetica"]
    assert "DejaVu Sans" in plt.rcParams["font.sans-serif"]


def test_save_figure_produces_tiff_and_pdf_without_arial(no_arial, tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        colors, width = pub_style.setup(journal="nature")
    fig, ax = plt.subplots(figsize=pub_style.journal_figsize("nature"))
    ax.bar([0, 1], [50, 80], color=colors[:2])
    ax.set_ylim(0, 100)
    label = pub_style.add_significance(ax, 0, 1, 85, 0.003)
    assert label == "**"
    out = pub_style.save_figure(fig, str(tmp_path / "fig1"))
    plt.close(fig)
    assert sorted(os.path.basename(p) for p in out) == ["fig1.pdf", "fig1.tiff"]
    assert (tmp_path / "fig1.tiff").stat().st_size > 0
    assert (tmp_path / "fig1.pdf").stat().st_size > 0
    from PIL import Image
    with Image.open(tmp_path / "fig1.tiff") as im:
        dpi = im.info.get("dpi")
        assert dpi and round(dpi[0]) == 600           # line art default


def test_save_figure_dpi_rules(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    from PIL import Image
    pub_style.save_figure(fig, str(tmp_path / "half"), formats=("tiff",), line_art=False)
    with Image.open(tmp_path / "half.tiff") as im:
        assert round(im.info["dpi"][0]) == 300
    pub_style.save_figure(fig, str(tmp_path / "combo"), formats=("tiff",), kind="combination")
    with Image.open(tmp_path / "combo.tiff") as im:
        assert round(im.info["dpi"][0]) == 500
    plt.close(fig)


def test_journal_figsize_differs_by_journal():
    nature = pub_style.journal_figsize("nature", n_panels=1)
    generic = pub_style.journal_figsize("default", n_panels=1)
    unknown = pub_style.journal_figsize("some-unknown-journal", n_panels=1)
    assert nature[0] == pytest.approx(89 / 25.4, abs=0.01)
    assert generic[0] == pytest.approx(85 / 25.4, abs=0.01)
    assert nature[0] != generic[0]
    assert unknown == generic                          # unknown journal → generic 85 mm
    assert pub_style.journal_figsize("nature", n_panels=4)[0] == pytest.approx(183 / 25.4, abs=0.01)
    assert pub_style.journal_figsize("lancet", columns="double")[0] == pytest.approx(175 / 25.4, abs=0.01)
    assert "unknown" in pub_style.journal_widths("xyz")["status"]


def test_add_significance_height_is_fraction_of_axis_range():
    fig, ax = plt.subplots()
    ax.set_ylim(0, 1000)
    pub_style.add_significance(ax, 0, 1, 900, 0.5, height=0.05)
    bracket = ax.lines[-1].get_ydata()
    assert max(bracket) - min(bracket) == pytest.approx(50)   # 5% of a 1000-unit range
    assert ax.texts[-1].get_text() == "ns"
    plt.close(fig)


# ─── v6.4.1: exact export width, RGB TIFF, log-axis brackets, invalid p-values ───

def _tiff_width_mm(path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size[0] / im.info["dpi"][0] * 25.4, im.mode, im.info.get("compression")


def _pdf_width_mm(path):
    import re
    m = re.search(rb"/MediaBox \[\s*0 0 ([\d.]+) ([\d.]+)\s*\]", path.read_bytes())
    assert m, "no MediaBox in PDF"
    return float(m.group(1)) / 72 * 25.4


@pytest.mark.parametrize("journal,n_panels,expected_mm", [("nature", 1, 89), ("nature", 2, 183), ("lancet", 1, 85)])
def test_saved_figure_has_exact_journal_width(tmp_path, journal, n_panels, expected_mm):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pub_style.setup(journal=journal)
    fig, ax = plt.subplots(figsize=pub_style.journal_figsize(journal, n_panels=n_panels))
    ax.bar([0, 1], [50, 80])
    ax.set_ylabel("A fairly long y-axis label (units)")
    ax.set_xlabel("Group")
    pub_style.save_figure(fig, str(tmp_path / "w"))
    plt.close(fig)
    width_mm, mode, compression = _tiff_width_mm(tmp_path / "w.tiff")
    assert width_mm == pytest.approx(expected_mm, abs=0.5)      # bbox_inches='tight' gave 82-85 mm
    assert _pdf_width_mm(tmp_path / "w.pdf") == pytest.approx(expected_mm, abs=0.5)
    assert mode == "RGB" and compression == "tiff_lzw"


def test_export_ignores_tight_bbox_rcparam_and_setup_does_not_set_it(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pub_style.setup(journal="nature")
    assert plt.rcParams["savefig.bbox"] in (None, "standard")
    with matplotlib.rc_context({"savefig.bbox": "tight"}):
        fig, ax = plt.subplots(figsize=pub_style.journal_figsize("nature"))
        ax.plot([0, 1], [0, 1])
        pub_style.save_figure(fig, str(tmp_path / "rc"), formats=("tiff",))
        plt.close(fig)
    assert _tiff_width_mm(tmp_path / "rc.tiff")[0] == pytest.approx(89, abs=0.5)


def test_tiff_has_no_alpha_even_with_transparent_background(tmp_path):
    from PIL import Image
    fig, ax = plt.subplots(figsize=(2, 1.5))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.plot([0, 1], [0, 1])
    pub_style.save_figure(fig, str(tmp_path / "t"), formats=("tiff",), dpi=100)
    plt.close(fig)
    with Image.open(tmp_path / "t.tiff") as im:
        assert im.mode == "RGB"
        assert im.getpixel((1, 1)) == (255, 255, 255)           # transparent corner → white, not black


def test_save_figure_keeps_user_layout(tmp_path):
    fig, ax = plt.subplots(figsize=(3, 2))
    fig.subplots_adjust(left=0.3)
    pub_style.save_figure(fig, str(tmp_path / "adj"), formats=("pdf",))
    assert fig.subplotpars.left == pytest.approx(0.3)             # subplots_adjust not overridden
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(3, 2), layout="constrained")
    pub_style.save_figure(fig, str(tmp_path / "con"), formats=("pdf",))
    assert type(fig.get_layout_engine()).__name__ == "ConstrainedLayoutEngine"
    plt.close(fig)
    with pytest.raises(ValueError):
        pub_style.save_figure(fig, str(tmp_path / "x"), layout="bogus")


def test_save_figure_warns_when_content_would_be_clipped(tmp_path):
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1], [0, 1])
    fig.text(1.05, 0.5, "outside the canvas")
    with pytest.warns(UserWarning, match="超出了图幅边界"):
        pub_style.save_figure(fig, str(tmp_path / "clip"), formats=("pdf",))
    plt.close(fig)
    fig, ax = plt.subplots(figsize=pub_style.journal_figsize("nature"))
    ax.plot([0, 1], [0, 1], label="series")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    with warnings.catch_warnings():
        warnings.simplefilter("error")                           # a normal figure: no clip warning
        pub_style.save_figure(fig, str(tmp_path / "ok"), formats=("pdf",))
    plt.close(fig)


def test_add_significance_on_log_axis_uses_fraction_of_decades():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.set_ylim(1, 1e4)                                           # 4 decades
    pub_style.add_significance(ax, 0, 1, 100, 0.003)
    bracket = ax.lines[-1].get_ydata()
    assert min(bracket) == pytest.approx(100)
    assert max(bracket) == pytest.approx(10 ** (2 + 0.02 * 4))    # ≈120, not 300 (linear 2% of 1e4)
    assert ax.texts[-1].get_position()[1] == pytest.approx(max(bracket))
    assert ax.get_ylim() == pytest.approx((1, 1e4))              # plenty of room → limits untouched
    pub_style.add_significance(ax, 0, 1, 9000, 0.2)               # near the top → room made for label
    assert ax.get_ylim()[1] > 9000 * 10 ** (2 * 0.02 * 4)
    with pytest.raises(ValueError, match="y > 0"):
        pub_style.add_significance(ax, 0, 1, 0, 0.2)
    plt.close(fig)


@pytest.mark.parametrize("bad", [float("nan"), None, -0.01, 1.5, "n/a"])
def test_p_to_stars_rejects_missing_or_invalid_p(bad):
    with pytest.raises(ValueError, match="ns"):
        pub_style.p_to_stars(bad)


def test_p_to_stars_thresholds_and_explicit_text_bypass():
    assert [pub_style.p_to_stars(p) for p in (0.0005, 0.005, 0.03, 0.05, 1)] == ["***", "**", "*", "ns", "ns"]
    fig, ax = plt.subplots()
    ax.set_ylim(0, 10)
    with pytest.raises(ValueError):
        pub_style.add_significance(ax, 0, 1, 8, float("nan"))
    assert pub_style.add_significance(ax, 0, 1, 8, None, text="n/a") == "n/a"
    plt.close(fig)


# ─── v6.4.3: reproducible files, journal families, colour-blind-safe fallback, matplotlib ≥ 3.6 ───

FORMATS = ("tiff", "pdf", "svg", "eps", "png")


def _save_bar_figure(path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        colors, _ = pub_style.setup(journal="nature")
        fig, ax = plt.subplots(figsize=pub_style.journal_figsize("nature"))
        ax.bar([0, 1], [3, 4], color=colors[:2])
        ax.set_xlabel("Group")
        ax.set_ylabel("Value (mg)")
        pub_style.save_figure(fig, str(path), formats=FORMATS)
    plt.close(fig)


def test_saving_an_unchanged_figure_twice_gives_identical_files(tmp_path, monkeypatch):
    import time
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    (tmp_path / "run1").mkdir()
    (tmp_path / "run2").mkdir()
    _save_bar_figure(tmp_path / "run1" / "figure1")
    time.sleep(1.1)                                   # the old PDF / EPS dates had 1-second resolution
    _save_bar_figure(tmp_path / "run2" / "figure1")
    for fmt in FORMATS:
        a = (tmp_path / "run1" / f"figure1.{fmt}").read_bytes()
        b = (tmp_path / "run2" / f"figure1.{fmt}").read_bytes()
        assert a == b, fmt
    assert b"CreationDate" not in (tmp_path / "run1" / "figure1.pdf").read_bytes()
    assert b"<dc:date>" not in (tmp_path / "run1" / "figure1.svg").read_bytes()
    assert "SOURCE_DATE_EPOCH" not in os.environ      # only set while saving


def test_save_figure_keeps_user_svg_salt_and_passes_metadata(tmp_path):
    fig, ax = plt.subplots(figsize=(2, 1.5))
    ax.plot([0, 1], [0, 1])
    with matplotlib.rc_context({"svg.hashsalt": "my-salt"}):
        pub_style.save_figure(fig, str(tmp_path / "m"), formats=("pdf", "svg"), metadata={"Title": "Figure 1"})
        assert plt.rcParams["svg.hashsalt"] == "my-salt"
    plt.close(fig)
    assert b"Figure 1" in (tmp_path / "m.pdf").read_bytes()
    assert b"Figure 1" in (tmp_path / "m.svg").read_bytes()
    assert plt.rcParams["svg.hashsalt"] is None       # pub_style's own salt is not left behind


@pytest.mark.parametrize("journal,family", [
    ("nature-medicine", "nature"), ("nature-communications", "nature"), ("npj-digital-medicine", "nature"),
    ("Nature Medicine", "nature"), ("lancet-oncology", "lancet"), ("eclinical-medicine", "lancet"),
    ("The Lancet", "lancet"), ("jama-network-open", "jama"), ("jama-oncology", "jama"),
])
def test_family_journals_get_their_family_widths_and_palette(journal, family, capsys):
    spec = pub_style.journal_widths(journal)
    house = pub_style.JOURNAL_WIDTH_MM[family]
    assert (spec["single"], spec["double"]) == (house["single"], house["double"])
    assert pub_style.journal_figsize(journal) == pub_style.journal_figsize(family)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        colors, _ = pub_style.setup(journal=journal)
    assert colors == pub_style.COLORS[family]
    assert capsys.readouterr().err == ""              # no "unknown journal" notice


def test_family_table_matches_the_journal_library():
    yaml = pytest.importorskip("yaml")
    lib = os.path.join(os.path.dirname(__file__), os.pardir, "skills", "manuscript-writing", "references",
                       "journal-templates.yaml")
    with open(lib, encoding="utf-8") as f:
        entries = yaml.safe_load(f)["templates"]
    expected = {e["id"]: e["family"] for e in entries
                if e.get("family") in pub_style.JOURNAL_WIDTH_MM and e["id"] not in pub_style.JOURNAL_WIDTH_MM}
    assert pub_style.JOURNAL_FAMILY == expected
    assert sum(1 for f in pub_style.JOURNAL_FAMILY.values() if f == "nature") == 13


def test_unknown_journal_gets_one_notice_and_the_okabe_ito_palette(capsys, monkeypatch):
    monkeypatch.setattr(pub_style, "_NOTICED", set())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        colors, width = pub_style.setup(journal="european-urology")
    pub_style.journal_figsize("european-urology", n_panels=2)
    err = capsys.readouterr().err
    assert err.count("european-urology") == 1 and len(err.strip().splitlines()) == 1
    assert "Okabe-Ito" in err
    assert colors == pub_style.COLORBLIND_SAFE
    assert width == pytest.approx(85 / 25.4, abs=0.01)
    assert pub_style.COLORS["default"] == pub_style.COLORBLIND_SAFE
    pub_style.journal_widths("default")
    assert capsys.readouterr().err == ""              # the generic default itself is not "unknown"


def test_old_matplotlib_is_refused_with_one_line(tmp_path):
    import subprocess
    scripts = os.path.join(os.path.dirname(__file__), os.pardir, "skills", "figure-generation", "scripts")
    code = ("import sys, matplotlib; matplotlib.use('Agg'); matplotlib.__version__ = '3.5.3'; "
            f"sys.path.insert(0, {scripts!r}); import pub_style")
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(tmp_path))
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr and "3.6" in proc.stderr and len(proc.stderr.strip().splitlines()) == 1


def test_figure_specs_yaml_mirrors_the_width_table():
    yaml = pytest.importorskip("yaml")
    specs = os.path.join(os.path.dirname(__file__), os.pardir, "skills", "figure-generation", "references",
                         "figure-specs.yaml")
    with open(specs, encoding="utf-8") as f:
        width = yaml.safe_load(f)["figure_specs"]["width"]
    for j, w in width["by_journal"].items():
        t = pub_style.JOURNAL_WIDTH_MM[j]
        assert (w["single_mm"], w["one_and_half_mm"], w["double_mm"], w["max_height_mm"], w["status"]) == \
            (t["single"], t["oneandahalf"], t["double"], t["max_height"], t["status"])
    assert set(width["by_family"]) - {"other"} == set(pub_style._FAMILY_MEMBERS)


# ─── v6.4.3 round 2: journal full names, metadata matched to each format ───

def _library_entries():
    yaml = pytest.importorskip("yaml")
    lib = os.path.join(os.path.dirname(__file__), os.pardir, "skills", "manuscript-writing", "references",
                       "journal-templates.yaml")
    with open(lib, encoding="utf-8") as f:
        return yaml.safe_load(f)["templates"]


def test_every_journal_resolves_by_its_library_name_like_by_its_id(capsys, monkeypatch):
    monkeypatch.setattr(pub_style, "_NOTICED", set())
    checked = 0
    for e in _library_entries():
        expected = e["id"] if e["id"] in pub_style.JOURNAL_WIDTH_MM else e.get("family")
        if expected not in pub_style.JOURNAL_WIDTH_MM:
            expected = "default"
        for given in (e["id"], e["journal"]):
            assert pub_style._journal_key(given)[0] == expected, (given, expected)
        checked += expected != "default"
    own = set(pub_style.JOURNAL_WIDTH_MM) - {"default"}  # nature, lancet, bmj, jama, nejm
    assert checked == len(own) + len(pub_style.JOURNAL_FAMILY)
    capsys.readouterr()
    for name in ("Lancet Infectious Diseases", "The Lancet Respiratory Medicine", "eClinicalMedicine",
                 "Nature Reviews Gastroenterology & Hepatology", "JAMA Otolaryngology - Head & Neck Surgery",
                 "New England Journal of Medicine"):
        pub_style.journal_widths(name)
    assert capsys.readouterr().err == ""                 # no "unknown journal" notice for a library name


def test_metadata_goes_to_each_format_in_the_keys_its_writer_takes(tmp_path):
    fig, ax = plt.subplots(figsize=(2, 1.5))
    ax.plot([0, 1], [0, 1])
    pub_style.save_figure(fig, str(tmp_path / "s"), formats=("svg",), metadata={"Author": "Dr X", "Title": "T1"})
    svg = (tmp_path / "s.svg").read_text(encoding="utf-8")
    assert "<dc:title>Dr X</dc:title>" in svg and "<dc:title>T1</dc:title>" in svg   # Author → dc:creator
    with pytest.warns(UserWarning, match="已跳过") as caught:
        pub_style.save_figure(fig, str(tmp_path / "m"), formats=("tiff", "pdf", "svg", "eps", "png"),
                              metadata={"Author": "Dr X", "Title": "T1", "Subject": "S1"})
    skipped = [str(w.message) for w in caught if "已跳过" in str(w.message)]
    assert len(skipped) == 1 and "eps: Author" in skipped[0] and "svg" not in skipped[0]
    plt.close(fig)
    assert b"Dr X" in (tmp_path / "m.pdf").read_bytes() and b"Dr X" in (tmp_path / "m.png").read_bytes()
    assert "<dc:description>S1</dc:description>" in (tmp_path / "m.svg").read_text(encoding="utf-8")


def test_metadata_a_writer_refuses_stops_before_any_file_is_written(tmp_path):
    fig, ax = plt.subplots(figsize=(2, 1.5))
    ax.plot([0, 1], [0, 1])
    with pytest.raises(ValueError, match="SVG"):
        pub_style.save_figure(fig, str(tmp_path / "bad"), formats=("tiff", "pdf", "svg"), metadata={"Title": 5})
    plt.close(fig)
    assert list(tmp_path.iterdir()) == []


def test_saving_twice_with_metadata_gives_identical_files(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    formats = ("pdf", "svg", "eps", "png")
    for run in ("a", "b"):
        (tmp_path / run).mkdir()
        fig, ax = plt.subplots(figsize=(2, 1.5))
        ax.plot([0, 1], [0, 1])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pub_style.save_figure(fig, str(tmp_path / run / "f"), formats=formats,
                                  metadata={"Title": "Figure 2", "Author": "Dr X"})
        plt.close(fig)
    for fmt in formats:
        assert (tmp_path / "a" / f"f.{fmt}").read_bytes() == (tmp_path / "b" / f"f.{fmt}").read_bytes(), fmt


# ─── v6.4.3 cleanup: format names in any case ───

def test_format_names_are_case_insensitive(tmp_path, monkeypatch):
    from PIL import Image
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    fig, ax = plt.subplots(figsize=(2, 1.5))
    ax.plot([0, 1], [0, 1])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = pub_style.save_figure(fig, str(tmp_path / "f"), formats=("TIFF", "PDF", "SVG", ".Png"), dpi=100,
                                    metadata={"Author": "Dr X"})
    plt.close(fig)
    assert [os.path.basename(p) for p in out] == ["f.tiff", "f.pdf", "f.svg", "f.png"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["f.pdf", "f.png", "f.svg", "f.tiff"]
    with Image.open(tmp_path / "f.tiff") as im:                         # the RGB / LZW writer, not matplotlib's
        assert im.mode == "RGB" and im.info.get("compression") == "tiff_lzw"
    svg = (tmp_path / "f.svg").read_text(encoding="utf-8")
    assert "<dc:title>Dr X</dc:title>" in svg and "<dc:date>" not in svg  # metadata + no date for 'SVG' too
    pdf = (tmp_path / "f.pdf").read_bytes()
    assert b"Dr X" in pdf and b"CreationDate" not in pdf
    assert not [w for w in caught if "已跳过" in str(w.message)]


def test_format_aliases_duplicates_and_unknown_formats(tmp_path):
    fig, ax = plt.subplots(figsize=(2, 1.5))
    ax.plot([0, 1], [0, 1])
    out = pub_style.save_figure(fig, str(tmp_path / "a"), formats=("tiff", "TIFF", "TIF", "JPEG"), dpi=72)
    assert [os.path.basename(p) for p in out] == ["a.tiff", "a.tif", "a.jpeg"]
    from PIL import Image
    with Image.open(tmp_path / "a.tif") as im:
        assert im.mode == "RGB" and im.info.get("compression") == "tiff_lzw"
    assert [os.path.basename(p) for p in pub_style.save_figure(fig, str(tmp_path / "b"), formats="PDF")] == ["b.pdf"]
    (tmp_path / "c").mkdir()
    with pytest.raises(ValueError, match="docx"):
        pub_style.save_figure(fig, str(tmp_path / "c" / "c"), formats=("pdf", "docx"))
    plt.close(fig)
    assert list((tmp_path / "c").iterdir()) == []                         # checked before any file is written
