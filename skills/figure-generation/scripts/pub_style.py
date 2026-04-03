"""
Publication-quality figure style setup for medical journals.
Usage: from pub_style import setup, save_figure, COLORS
"""

import matplotlib.pyplot as plt
import matplotlib as mpl

COLORS = {
    'nature':  ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2'],
    'lancet':  ['#00468B', '#ED0000', '#42B540', '#0099B4', '#925E9F', '#FDAF91', '#AD002A'],
    'jama':    ['#374E55', '#DF8F44', '#00A1D5', '#B24745', '#79AF97', '#6A6599', '#80796B'],
    'nejm':    ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1', '#6F99AD', '#FFDC91'],
    'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'],
}

# Colorblind-safe palette (Okabe-Ito)
COLORBLIND_SAFE = ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#000000']

def setup(journal='nature', single_column=True, font='Arial'):
    """Set publication-quality matplotlib defaults. Returns (colors, fig_width_inches)."""
    width = 3.35 if single_column else 6.7  # 85mm / 170mm
    plt.rcParams.update({
        'font.family': font,
        'font.size': 8,
        'axes.titlesize': 10,
        'axes.labelsize': 9,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.transparent': False,
        'axes.linewidth': 0.8,
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,
        'lines.linewidth': 1.2,
        'axes.spines.top': False,
        'axes.spines.right': False,
    })
    colors = COLORS.get(journal, COLORS['default'])
    return colors, width

def save_figure(fig, filename, formats=('tiff', 'pdf'), dpi=300):
    """Save figure in multiple formats meeting journal requirements."""
    for fmt in formats:
        kwargs = {}
        if fmt == 'tiff':
            kwargs['pil_kwargs'] = {'compression': 'tiff_lzw'}
        fig.savefig(f'{filename}.{fmt}', dpi=dpi, format=fmt, bbox_inches='tight', **kwargs)
    print(f"Saved: {', '.join(f'{filename}.{f}' for f in formats)}")

def add_significance(ax, x1, x2, y, p_value, height=0.02):
    """Add significance bracket between two groups."""
    if p_value < 0.001:
        sig = '***'
    elif p_value < 0.01:
        sig = '**'
    elif p_value < 0.05:
        sig = '*'
    else:
        sig = 'ns'
    ax.plot([x1, x1, x2, x2], [y, y+height, y+height, y], 'k-', linewidth=0.8)
    ax.text((x1+x2)/2, y+height, sig, ha='center', va='bottom', fontsize=8)

def journal_figsize(journal='default', n_panels=1):
    """Return appropriate figure size for journal and panel count."""
    widths = {
        'single': 3.35,   # 85mm single column
        'oneandahalf': 5.0, # 127mm 1.5 column
        'double': 6.7,    # 170mm double column
    }
    if n_panels <= 2:
        w = widths['single'] if n_panels == 1 else widths['double']
    else:
        w = widths['double']
    h = w * 0.75
    return (w, h)
