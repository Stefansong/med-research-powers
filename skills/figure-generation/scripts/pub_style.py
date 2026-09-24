#!/usr/bin/env python3
"""
Publication-quality figure style setup for medical journals.

Usage (run from the user's project directory):
    import os, sys
    sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                    "skills", "figure-generation", "scripts"))
    from pub_style import setup, save_figure, add_significance, journal_figsize, COLORS, COLORBLIND_SAFE

    colors, width = setup(journal='nature', single_column=True)   # rcParams + palette + width (inch)
    fig, ax = plt.subplots(figsize=journal_figsize('nature', n_panels=1))
    ...
    add_significance(ax, x1=0, x2=1, y=y_top, p_value=0.003)      # bracket height = 2% of the axis height (log axes too)
    save_figure(fig, 'figure1')                                    # figure1.tiff (600 dpi, RGB, LZW) + figure1.pdf

Export keeps the figure size: a journal_figsize('nature') figure is saved exactly 89 mm wide
(no bbox_inches='tight' cropping). save_figure() lays the figure out inside that fixed size
(tight_layout, unless the figure already has its own layout, e.g. plt.subplots(layout='constrained'))
and warns if anything would still be cut off at the edge.

Fonts: rcParams use font.family='sans-serif' with the fallback chain
Arial → Helvetica → Liberation Sans → DejaVu Sans. If neither Arial nor Helvetica is
installed, setup() warns ONCE (not 70 times) so the "Arial" checklist item is not
violated silently. Install Arial (e.g. ttf-mscorefonts-installer) for final export.

Command line: `python3 pub_style.py --check` prints the font / journal-width table.
"""

import math
import warnings

try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
except ImportError:  # pragma: no cover - depends on the user's environment
    raise SystemExit("缺少 matplotlib：pip install matplotlib pillow")

# ─── palettes ───────────────────────────────────────────────────────────────

COLORS = {
    'nature':  ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2'],
    'lancet':  ['#00468B', '#ED0000', '#42B540', '#0099B4', '#925E9F', '#FDAF91', '#AD002A'],
    'jama':    ['#374E55', '#DF8F44', '#00A1D5', '#B24745', '#79AF97', '#6A6599', '#80796B'],
    'nejm':    ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1', '#6F99AD', '#FFDC91'],
    'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'],
}

# Colorblind-safe palette (Okabe-Ito)
COLORBLIND_SAFE = ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#000000']

# ─── fonts ──────────────────────────────────────────────────────────────────

PREFERRED_FONTS = ['Arial', 'Helvetica', 'Liberation Sans', 'DejaVu Sans']
_ACCEPTED_FONTS = ('Arial', 'Helvetica')   # what journals ask for (figure-specs.yaml)
_FONT_WARNED = False                        # module-level: warn once per process


def _available_font_names():
    """Set of font family names matplotlib can see (patched in tests)."""
    return {f.name for f in font_manager.fontManager.ttflist}


def check_fonts(warn=True):
    """Return the accepted font that is installed ('Arial'/'Helvetica') or None.

    When none is installed, emit ONE UserWarning per process (if warn=True).
    """
    global _FONT_WARNED
    names = _available_font_names()
    for f in _ACCEPTED_FONTS:
        if f in names:
            return f
    if warn and not _FONT_WARNED:
        _FONT_WARNED = True
        fallback = next((f for f in PREFERRED_FONTS[2:] if f in names), 'matplotlib default')
        warnings.warn(
            f"系统未安装 Arial/Helvetica，图中文字将回退到 {fallback}。"
            "投稿前请在装有 Arial 的机器上重新导出（Ubuntu: sudo apt install ttf-mscorefonts-installer），"
            "或在图注/cover letter 中说明字体。此提示每次运行只出现一次。",
            UserWarning, stacklevel=3)
    return None


# ─── journal widths ─────────────────────────────────────────────────────────

# Column widths in mm. 'verified' = taken from the journal's current figure guide;
# 'approx' = common values for that family, confirm in Instructions for Authors.
JOURNAL_WIDTH_MM = {
    'nature':  {'single': 89, 'oneandahalf': 120, 'double': 183, 'max_height': 247, 'status': 'verified'},
    'lancet':  {'single': 85, 'oneandahalf': 127, 'double': 175, 'max_height': 230, 'status': 'approx'},
    'bmj':     {'single': 85, 'oneandahalf': 127, 'double': 175, 'max_height': 230, 'status': 'approx'},
    'jama':    {'single': 85, 'oneandahalf': 127, 'double': 175, 'max_height': 230, 'status': 'approx'},
    'nejm':    {'single': 85, 'oneandahalf': 127, 'double': 170, 'max_height': 230, 'status': 'approx'},
    'default': {'single': 85, 'oneandahalf': 127, 'double': 170, 'max_height': 230, 'status': 'generic'},
}
MM_PER_INCH = 25.4


def journal_widths(journal='default'):
    """Width spec (mm) for a journal; unknown journals fall back to the generic 85/170 mm."""
    key = (journal or 'default').lower()
    if key not in JOURNAL_WIDTH_MM:
        spec = dict(JOURNAL_WIDTH_MM['default'])
        spec['status'] = f"unknown journal '{journal}' — generic 85/170 mm used; check its author guide"
        return spec
    return dict(JOURNAL_WIDTH_MM[key])


def journal_figsize(journal='default', n_panels=1, columns=None, aspect=0.75):
    """(width, height) in inches for a journal / panel count.

    columns: 'single' | 'oneandahalf' | 'double' — overrides the panel-count rule
             (1 panel → single column, ≥2 panels → double column).
    aspect : height / width (0.75 default). Height is capped at the journal's max height.
    """
    spec = journal_widths(journal)
    if columns is None:
        columns = 'single' if n_panels <= 1 else 'double'
    if columns not in ('single', 'oneandahalf', 'double'):
        raise ValueError("columns 必须是 'single' / 'oneandahalf' / 'double'")
    w_mm = spec[columns]
    h_mm = min(w_mm * aspect, spec['max_height'])
    return (round(w_mm / MM_PER_INCH, 3), round(h_mm / MM_PER_INCH, 3))


# ─── setup ──────────────────────────────────────────────────────────────────

def setup(journal='nature', single_column=True, font=None, colorblind_safe=False):
    """Set publication-quality matplotlib defaults. Returns (colors, fig_width_inches).

    font: optional extra family put in front of the fallback chain.
    colorblind_safe: return the Okabe-Ito palette instead of the journal palette.
    """
    chain = ([font] if font and font not in PREFERRED_FONTS else []) + PREFERRED_FONTS
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': chain,
        'font.size': 8,
        'axes.titlesize': 10,
        'axes.labelsize': 9,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'figure.dpi': 150,          # screen preview only; export dpi is set in save_figure
        'savefig.dpi': 600,
        'savefig.bbox': 'standard',  # never crop: the saved width must stay the journal column width
        'savefig.transparent': False,
        'axes.linewidth': 0.8,
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,
        'lines.linewidth': 1.2,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'pdf.fonttype': 42,         # embed TrueType so text stays editable in PDF
        'ps.fonttype': 42,
        'svg.fonttype': 'none',
    })
    check_fonts(warn=True)
    spec = journal_widths(journal)
    width = round(spec['single' if single_column else 'double'] / MM_PER_INCH, 3)
    colors = COLORBLIND_SAFE if colorblind_safe else COLORS.get((journal or 'default').lower(), COLORS['default'])
    return colors, width


apply_style = setup   # alias used in some docs


# ─── export ─────────────────────────────────────────────────────────────────

DPI_BY_KIND = {'line_art': 600, 'combination': 500, 'halftone': 300}   # figure-specs.yaml


_SUBPLOT_KEYS = ('left', 'right', 'bottom', 'top', 'wspace', 'hspace')


def _fit_layout(fig):
    """Fit labels inside the FIXED figure size, unless the figure already has its own layout.

    Own layout = a layout engine (layout='constrained' / 'compressed', an earlier
    tight_layout()) or subplots_adjust() values that differ from the rcParams defaults.
    """
    if fig.get_layout_engine() is not None:
        return
    if any(getattr(fig.subplotpars, k) != mpl.rcParams[f'figure.subplot.{k}'] for k in _SUBPLOT_KEYS):
        return
    fig.tight_layout()


def _warn_if_clipped(fig, tol_in=0.02):
    """Warn when drawn content extends past the figure edge (it would be cut off on export)."""
    fig.draw_without_rendering()
    tb = fig.get_tightbbox()
    w, h = fig.get_size_inches()
    if tb.x0 < -tol_in or tb.y0 < -tol_in or tb.x1 > w + tol_in or tb.y1 > h + tol_in:
        warnings.warn(
            "图中内容超出了图幅边界，导出时会被裁掉（图幅固定为期刊栏宽，不再用 bbox_inches='tight' 自动扩边）。"
            "请用 plt.subplots(..., layout='constrained')、缩短标签/图例，或把图例放进坐标轴内。",
            UserWarning, stacklevel=3)


def _save_tiff_rgb(fig, out, dpi):
    """TIFF as RGB (no alpha channel) with LZW compression — matplotlib alone writes RGBA."""
    import io
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi)
    buf.seek(0)
    with Image.open(buf) as im:
        im = im.convert('RGBA')
        rgb = Image.new('RGB', im.size, (255, 255, 255))   # transparent areas → white
        rgb.paste(im, mask=im.getchannel('A'))
    rgb.save(out, format='TIFF', compression='tiff_lzw', dpi=(dpi, dpi))


def save_figure(fig, filename, formats=('tiff', 'pdf'), dpi=None, line_art=True, kind=None, layout='auto'):
    """Save in journal formats. TIFF (RGB, LZW) + PDF by default, at the figure's exact size.

    The figure size is NOT changed on export (no bbox_inches='tight'), so a figure made with
    journal_figsize() is saved at exactly the journal column width.
    layout: 'auto' (default) → if the figure has no layout of its own, run tight_layout() so the
            labels fit inside the fixed size; None → leave the figure untouched.
    A UserWarning is issued if content still extends beyond the figure edge.
    dpi resolution: explicit `dpi` > `kind` ('line_art' 600 / 'combination' 500 / 'halftone' 300)
    > `line_art` flag (True → 600, False → 300). Line art (plots with thin lines/text) needs 600.
    """
    if dpi is None:
        if kind is not None:
            if kind not in DPI_BY_KIND:
                raise ValueError(f"kind 必须是 {list(DPI_BY_KIND)}")
            dpi = DPI_BY_KIND[kind]
        else:
            dpi = DPI_BY_KIND['line_art'] if line_art else DPI_BY_KIND['halftone']
    if layout not in ('auto', None):
        raise ValueError("layout 必须是 'auto' 或 None")
    if layout == 'auto':
        _fit_layout(fig)
    saved = []
    with mpl.rc_context({'savefig.bbox': 'standard'}):   # no cropping, whatever the rcParams say
        _warn_if_clipped(fig)
        for fmt in formats:
            out = f'{filename}.{fmt}'
            if fmt in ('tiff', 'tif'):
                try:
                    import PIL  # noqa: F401  (TIFF is written through Pillow)
                except ImportError:
                    raise SystemExit("保存 TIFF 需要 Pillow：pip install pillow")
                _save_tiff_rgb(fig, out, dpi)
            else:
                fig.savefig(out, dpi=dpi, format=fmt)
            saved.append(out)
    w_in, h_in = fig.get_size_inches()
    print(f"Saved ({dpi} dpi, {w_in * MM_PER_INCH:.1f} × {h_in * MM_PER_INCH:.1f} mm): {', '.join(saved)}")
    return saved


# ─── annotations ────────────────────────────────────────────────────────────

def p_to_stars(p_value):
    """'***' (p<0.001) / '**' (p<0.01) / '*' (p<0.05) / 'ns'.

    A missing or invalid p-value (None, NaN, non-numeric, outside [0, 1]) raises ValueError —
    it is never shown as 'ns'. Pass text=... to add_significance() to label such a bracket yourself.
    """
    try:
        p = float(p_value)
    except (TypeError, ValueError):
        raise ValueError(f"p_value 必须是 0–1 之间的数，收到 {p_value!r}；缺失的 p 值不能标成 'ns'") from None
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError(f"p_value 必须是 0–1 之间的数，收到 {p_value!r}；缺失的 p 值不能标成 'ns'")
    if p < 0.001:
        return '***'
    if p < 0.01:
        return '**'
    if p < 0.05:
        return '*'
    return 'ns'


def add_significance(ax, x1, x2, y, p_value, height=0.02, text=None, fontsize=8):
    """Draw a significance bracket between x1 and x2 starting at data-y `y`.

    height is a FRACTION OF THE Y-AXIS HEIGHT (0.02 = 2%), measured in the axis' scaled
    space, so the bracket looks the same on linear, log and symlog axes. text defaults to
    ***/**/*/ns from p_value (p_to_stars; a missing p-value raises ValueError).
    """
    label = text if text is not None else p_to_stars(p_value)
    scale = ax.yaxis.get_transform()          # data → scaled (identity / log10 / symlog …)
    inv = scale.inverted()
    y0, y1 = ax.get_ylim()
    s0, s1 = (float(v) for v in scale.transform([y0, y1]))
    ys = float(scale.transform(y))
    if (ax.get_yscale() == 'log' and y <= 0) or not all(math.isfinite(v) for v in (s0, s1, ys)):
        raise ValueError(f"y={y!r} 不在该坐标轴的有效范围内（对数轴要求 y > 0）")
    hs = height * (s1 - s0)
    top = float(inv.transform(ys + hs))
    ax.plot([x1, x1, x2, x2], [y, top, top, y], 'k-', linewidth=0.8, clip_on=False)
    ax.text((x1 + x2) / 2, top, label, ha='center', va='bottom', fontsize=fontsize)
    if (ys + 2 * hs - s1) * (1 if s1 >= s0 else -1) > 0:   # make room for the label
        ax.set_ylim(y0, float(inv.transform(ys + 3 * hs)))
    return label


# ─── CLI ────────────────────────────────────────────────────────────────────

def _main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description='pub_style environment check: fonts + journal widths')
    p.add_argument('--check', action='store_true', help='(default action) print font availability and journal widths')
    p.parse_args(argv)
    found = check_fonts(warn=False)
    print(f"matplotlib {mpl.__version__}; accepted font installed: "
          f"{found or 'NONE (fallback to Liberation Sans / DejaVu Sans)'}")
    print("journal  single  1.5col  double  status")
    for j, s in JOURNAL_WIDTH_MM.items():
        print(f"{j:<8} {s['single']:>5}mm {s['oneandahalf']:>5}mm {s['double']:>5}mm  {s['status']}")


if __name__ == '__main__':
    _main()
