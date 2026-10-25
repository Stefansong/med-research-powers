#!/usr/bin/env python3
"""
Publication-quality figure style setup for medical journals.

Usage (run from the user's project directory):
    # copy this file into the project once (it reads nothing else from the plugin):
    #   cp "$CLAUDE_PLUGIN_ROOT/skills/figure-generation/scripts/pub_style.py" .
    from pub_style import setup, save_figure, add_significance, journal_figsize, COLORS, COLORBLIND_SAFE

    colors, width = setup(journal='nature', single_column=True)   # rcParams + palette + width (inch)
    fig, ax = plt.subplots(figsize=journal_figsize('nature', n_panels=1))
    ...
    add_significance(ax, x1=0, x2=1, y=y_top, p_value=0.003)      # bracket height = 2% of the axis height (log axes too)
    save_figure(fig, 'figure1')                                    # figure1.tiff (600 dpi, RGB, LZW) + figure1.pdf

journal: an id from journal-templates.yaml, or that journal's full name as the library writes it
(e.g. 'Nature Medicine', 'Lancet Infectious Diseases'). Journals of
the Nature, Lancet and JAMA families get their family's house widths and palette; any other journal
gets the generic 85/127/170 mm widths and the colour-blind-safe Okabe-Ito palette, with a one-line
notice on stderr (once per journal) — check that journal's figure guide.

Reproducible files: save_figure writes no creation date into PDF / SVG / SVGZ / EPS (and no gzip
timestamp into SVGZ) and uses a fixed SVG id salt, so saving an unchanged figure again gives
byte-identical files (reproduce_check passes).
metadata= is checked for every format before any file is written: each format gets the keys its
writer can store (SVG / SVGZ take Author / Subject as Creator / Description), the rest are skipped
with one warning. PGF typesets its text with LaTeX (rcParams['pgf.texsystem'], xelatex by default):
it is rendered in memory first, so a missing TeX stops save_figure before any file is written.

Export keeps the figure size: a journal_figsize('nature') figure is saved exactly 89 mm wide
(no bbox_inches='tight' cropping). save_figure() lays the figure out inside that fixed size
(tight_layout, unless the figure already has its own layout, e.g. plt.subplots(layout='constrained'))
and warns if anything would still be cut off at the edge.

Fonts: rcParams use font.family='sans-serif' with the fallback chain
Arial → Helvetica → Liberation Sans → DejaVu Sans. If neither Arial nor Helvetica is
installed, setup() warns ONCE (not 70 times) so the "Arial" checklist item is not
violated silently. Install Arial (e.g. ttf-mscorefonts-installer) for final export.

Command line: `python3 pub_style.py --check` prints the font / journal-width table.
Needs matplotlib 3.6 or later (layout engines, draw_without_rendering).
"""

import contextlib
import math
import os
import re
import sys
import warnings

try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
except ImportError:  # pragma: no cover - depends on the user's environment
    print("缺少 matplotlib：pip install 'matplotlib>=3.6' pillow", file=sys.stderr)
    raise SystemExit(2)

MIN_MATPLOTLIB = (3, 6)   # Figure.get_layout_engine() / draw_without_rendering() in save_figure


def _version_tuple(version):
    m = re.match(r'(\d+)\.(\d+)', version)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


if _version_tuple(mpl.__version__) < MIN_MATPLOTLIB:
    print(f"pub_style 需要 matplotlib 3.6 或更新版本（当前 {mpl.__version__}）："
          "pip install -U 'matplotlib>=3.6'", file=sys.stderr)
    raise SystemExit(2)

# ─── palettes ───────────────────────────────────────────────────────────────

# Colorblind-safe palette (Okabe-Ito)
COLORBLIND_SAFE = ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#000000']

COLORS = {
    'nature':  ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2'],
    'lancet':  ['#00468B', '#ED0000', '#42B540', '#0099B4', '#925E9F', '#FDAF91', '#AD002A'],
    'jama':    ['#374E55', '#DF8F44', '#00A1D5', '#B24745', '#79AF97', '#6A6599', '#80796B'],
    'nejm':    ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1', '#6F99AD', '#FFDC91'],
    'default': list(COLORBLIND_SAFE),   # journals without a house palette (bmj, unknown ids)
}

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

# journal-templates.yaml ids whose `family:` has a house width above (tests keep this in sync with
# the library). Kept in this file, not read from the library, so a copy of pub_style.py works alone.
_FAMILY_MEMBERS = {
    'nature': ('nature-communications', 'nature-medicine', 'nature-reviews-cancer', 'nature-reviews-cardiology',
               'nature-reviews-clinical-oncology', 'nature-reviews-disease-primers', 'nature-reviews-endocrinology',
               'nature-reviews-gastro-hepatol', 'nature-reviews-nephrology', 'nature-reviews-neurology',
               'nature-reviews-rheumatology', 'npj-digital-medicine', 'scientific-reports'),
    'lancet': ('eclinical-medicine', 'lancet-child', 'lancet-diabetes', 'lancet-digital-health',
               'lancet-gastro-hepatol', 'lancet-global-health', 'lancet-haematology', 'lancet-id', 'lancet-microbe',
               'lancet-neurology', 'lancet-oncology', 'lancet-psychiatry', 'lancet-public-health',
               'lancet-respiratory'),
    'jama':   ('jama-cardiology', 'jama-dermatology', 'jama-internal-medicine', 'jama-network-open',
               'jama-neurology', 'jama-oncology', 'jama-ophthalmology', 'jama-otolaryngology', 'jama-pediatrics',
               'jama-psychiatry', 'jama-surgery'),
}
JOURNAL_FAMILY = {j: family for family, ids in _FAMILY_MEMBERS.items() for j in ids}
# Full names (journal-templates.yaml `journal:`) of those journals whose name, written as a slug, is not
# their id ('Lancet Infectious Diseases' → lancet-infectious-diseases, id lancet-id). Tests check that every
# family journal's library name resolves.
_NAME_TO_ID = {
    'new-england-journal-of-medicine': 'nejm',
    'eclinicalmedicine': 'eclinical-medicine',
    'lancet-child-adolescent-health': 'lancet-child',
    'lancet-diabetes-endocrinology': 'lancet-diabetes',
    'lancet-gastroenterology-hepatology': 'lancet-gastro-hepatol',
    'lancet-infectious-diseases': 'lancet-id',
    'lancet-respiratory-medicine': 'lancet-respiratory',
    'nature-reviews-gastroenterology-hepatology': 'nature-reviews-gastro-hepatol',
    'jama-otolaryngology-head-neck-surgery': 'jama-otolaryngology',
}
_NOTICED = set()                            # unknown journals already reported in this process


def _journal_key(journal):
    """('nature', 'own' | 'family') for a known journal id / name, ('default', 'unknown') otherwise."""
    key = re.sub(r'[^a-z0-9]+', '-', str(journal or 'default').lower()).strip('-') or 'default'
    for k in (key, key[4:] if key.startswith('the-') else None):     # 'The Lancet' → lancet
        k = _NAME_TO_ID.get(k, k)
        if k in JOURNAL_WIDTH_MM:
            return k, 'own'
        if k in JOURNAL_FAMILY:
            return JOURNAL_FAMILY[k], 'family'
    if key not in _NOTICED:
        _NOTICED.add(key)
        print(f"pub_style: 期刊 '{journal}' 没有记录的栏宽和配色 → 用通用栏宽 85/127/170 mm 和色盲友好的 "
              "Okabe-Ito 配色；最终尺寸以该刊作者须知为准", file=sys.stderr)
    return 'default', 'unknown'


def journal_widths(journal='default'):
    """Width spec (mm) for a journal id or name.

    Nature / Lancet / JAMA family members get their family's widths (status 'approx …'); unknown
    journals the generic 85/127/170 mm, with a one-line notice on stderr.
    """
    key, how = _journal_key(journal)
    spec = dict(JOURNAL_WIDTH_MM[key])
    if how == 'family':
        spec['status'] = f"approx — {key}-family house width for '{journal}'; confirm in its author guide"
    elif how == 'unknown':
        spec['status'] = f"unknown journal '{journal}' — generic 85/170 mm used; check its author guide"
    return spec


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
    colorblind_safe: return the Okabe-Ito palette instead of the journal palette
                     (journals without a house palette get Okabe-Ito anyway).
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
    colors = COLORBLIND_SAFE if colorblind_safe else COLORS.get(_journal_key(journal)[0], COLORS['default'])
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


# Saving the same figure twice must give identical files (reproduce_check): no creation date in
# PDF / SVG / SVGZ (removed via metadata) or EPS / PS (SOURCE_DATE_EPOCH), a fixed salt for SVG ids and
# no timestamp in the SVGZ gzip header (_save_svgz).
_NO_DATE = {'pdf': {'CreationDate': None}, 'svg': {'Date': None}, 'svgz': {'Date': None}}
_SVG_HASHSALT = 'mrp-pub-style'
# metadata keys each savefig writer stores: SVG's Dublin Core set (any other key raises ValueError), the
# PostScript Creator comment (other keys are ignored); PDF and PNG take any key. savefig(metadata=...)
# is refused for jpg / tiff etc., so those formats get none.
_SVG_METADATA_KEYS = ('Title', 'Coverage', 'Date', 'Description', 'Format', 'Identifier', 'Language', 'Relation',
                      'Source', 'Type', 'Creator', 'Contributor', 'Publisher', 'Rights', 'Keywords')
_METADATA_KEYS = {
    'pdf': None, 'png': None, 'svg': _SVG_METADATA_KEYS, 'svgz': _SVG_METADATA_KEYS,
    'eps': ('Creator',), 'ps': ('Creator',),
}
_SVG_KEY_FOR = {'Author': 'Creator', 'Subject': 'Description'}     # the PDF names of two SVG fields


def _metadata_by_format(formats, metadata):
    """{format: savefig metadata}, worked out before anything is written. Keys a format's writer cannot
    store are left out of that format, with one warning for the whole call."""
    result, skipped = {}, []
    for fmt in formats:
        if fmt not in _METADATA_KEYS:
            continue
        allowed = _METADATA_KEYS[fmt]
        md = dict(_NO_DATE.get(fmt, {}))
        for k, v in (metadata or {}).items():
            key = k
            if fmt in ('svg', 'svgz') and k in _SVG_KEY_FOR and _SVG_KEY_FOR[k] not in metadata:
                key = _SVG_KEY_FOR[k]                   # an explicit Creator / Description wins
            if allowed is None or key in allowed:
                md[key] = v
            else:
                skipped.append(f"{fmt}: {k}")
        result[fmt] = md
    if skipped:
        warnings.warn(f"这些 metadata 该格式存不了，已跳过：{'; '.join(skipped)}", UserWarning, stacklevel=3)
    return result


def _check_metadata(fig, metadata_by_format):
    """Write each format with metadata into memory first, so a value its writer refuses (e.g. a number
    as an SVG Title) stops save_figure before any file exists."""
    import io
    for fmt, md in metadata_by_format.items():
        if set(md) - set(_NO_DATE.get(fmt, {})):
            try:
                with warnings.catch_warnings():        # matplotlib's own warnings come with the real save
                    warnings.simplefilter('ignore')
                    fig.savefig(io.BytesIO(), format=fmt, dpi=72, metadata=md)
            except Exception as e:
                raise ValueError(f"metadata 不能写入 {fmt.upper()}：{e}（没有保存任何文件）") from None


def _check_pgf(fig):
    """PGF typesets its text through LaTeX (rcParams['pgf.texsystem']): check that the TeX program is there
    and render the figure into memory first, so a missing or failing TeX stops save_figure before any file
    exists."""
    import io
    import shutil
    tex = mpl.rcParams['pgf.texsystem']
    if shutil.which(tex) is None:
        raise ValueError(f"PGF 要用 {tex} 排版文字，但找不到 {tex}（没有保存任何文件；装好 TeX，或从 formats 去掉 'pgf'）")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            fig.savefig(io.BytesIO(), format='pgf')
    except Exception as e:
        raise ValueError(f"PGF 要用 {tex} 排版文字，试排时出错：{e}（没有保存任何文件；或从 formats 去掉 'pgf'）") from None


def _save_svgz(fig, out, dpi, metadata):
    """SVGZ = the SVG (with its metadata, no date) gzipped with mtime 0: matplotlib's own svgz writer stores
    the current time in the gzip header, so two saves always differed."""
    import gzip
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format='svg', dpi=dpi, metadata=metadata)
    with open(out, 'wb') as f, gzip.GzipFile(filename='', mode='wb', fileobj=f, mtime=0) as gz:
        gz.write(buf.getvalue())


def _normalised_formats(fig, formats):
    """Format names as the writers below compare them: lower case ('TIFF' → 'tiff', so it still gets the
    RGB / LZW writer and 'SVG' / 'PDF' still get their metadata), no leading dot, each format once, a
    single name accepted as well as a list. The file extension is the normalised name ('tif' / 'jpeg'
    stay as given). An unknown format stops save_figure before any file is written."""
    if isinstance(formats, str):
        formats = (formats,)
    out = []
    for fmt in formats:
        f = str(fmt).strip().lstrip('.').lower()
        if f not in out:
            out.append(f)
    supported = fig.canvas.get_supported_filetypes()
    unknown = [f for f in out if f not in supported]
    if unknown or not out:
        raise ValueError(f"{'不支持的图片格式 ' + str(unknown) if unknown else 'formats 是空的'}"
                         f"（可用：{', '.join(sorted(supported))}；没有保存任何文件）")
    return out


@contextlib.contextmanager
def _fixed_source_date():
    """SOURCE_DATE_EPOCH=0 while saving (EPS / PS take their date from it), unless the user set it."""
    if 'SOURCE_DATE_EPOCH' in os.environ:
        yield
        return
    os.environ['SOURCE_DATE_EPOCH'] = '0'
    try:
        yield
    finally:
        os.environ.pop('SOURCE_DATE_EPOCH', None)


def save_figure(fig, filename, formats=('tiff', 'pdf'), dpi=None, line_art=True, kind=None, layout='auto',
                metadata=None):
    """Save in journal formats. TIFF (RGB, LZW) + PDF by default, at the figure's exact size.

    The figure size is NOT changed on export (no bbox_inches='tight'), so a figure made with
    journal_figsize() is saved at exactly the journal column width.
    layout: 'auto' (default) → if the figure has no layout of its own, run tight_layout() so the
            labels fit inside the fixed size; None → leave the figure untouched.
    A UserWarning is issued if content still extends beyond the figure edge.
    dpi resolution: explicit `dpi` > `kind` ('line_art' 600 / 'combination' 500 / 'halftone' 300)
    > `line_art` flag (True → 600, False → 300). Line art (plots with thin lines/text) needs 600.
    The files are reproducible: no creation date in PDF / SVG / SVGZ / EPS, no gzip timestamp in SVGZ and
    a fixed SVG id salt (an svg.hashsalt the user set is kept). metadata: extra savefig metadata (e.g.
    {'Title': ..., 'Author': ...}) for PDF / SVG / SVGZ / PNG / EPS, each format getting the keys its writer
    stores (SVG / SVGZ: Author → Creator, Subject → Description; EPS: Creator only); other keys are skipped
    for that format with one warning. It is checked before any file is written. TIFF and other formats get
    no metadata. 'pgf' needs a TeX installation; it is rendered in memory first, before any file is written.
    formats: names in any case ('TIFF' is 'tiff', '.pdf' is 'pdf'); each file gets the lower-case name as
    its extension (figure1.tiff); a format matplotlib cannot write is refused before any file is written.
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
    formats = _normalised_formats(fig, formats)
    saved = []
    rc = {'savefig.bbox': 'standard'}                    # no cropping, whatever the rcParams say
    if mpl.rcParams['svg.hashsalt'] is None:
        rc['svg.hashsalt'] = _SVG_HASHSALT
    if any(fmt in ('tiff', 'tif') for fmt in formats):      # checked before any file is written
        try:
            import PIL  # noqa: F401  (TIFF is written through Pillow)
        except ImportError:
            print("保存 TIFF 需要 Pillow：pip install pillow", file=sys.stderr)
            raise SystemExit(2)
    md_by_format = _metadata_by_format(formats, metadata)
    with mpl.rc_context(rc), _fixed_source_date():
        if metadata:
            _check_metadata(fig, md_by_format)
        if 'pgf' in formats:
            _check_pgf(fig)
        _warn_if_clipped(fig)
        for fmt in formats:
            out = f'{filename}.{fmt}'
            if fmt in ('tiff', 'tif'):
                _save_tiff_rgb(fig, out, dpi)
            elif fmt == 'svgz':
                _save_svgz(fig, out, dpi, md_by_format['svgz'])
            else:
                md = md_by_format.get(fmt)
                fig.savefig(out, dpi=dpi, format=fmt, **({'metadata': md} if md else {}))
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
    print("family members (journal-templates.yaml ids) use their family's widths and palette: " +
          ", ".join(f"{f} {len(ids)}" for f, ids in _FAMILY_MEMBERS.items()) +
          "; any other journal: generic widths + Okabe-Ito palette, with a one-line notice")


if __name__ == '__main__':
    _main()
