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
