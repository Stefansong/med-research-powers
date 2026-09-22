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
