# Figure Generation

Invoke the `figure-generation` skill to create publication-quality figures.

## Workflow

1. Review `results-summary.md` to identify which results need visualization
2. Select figure type per result (bar / box / scatter / survival curve / forest plot / heatmap / ROC)
3. Apply journal style using `pub_style.py` (Nature / Lancet / JAMA / NEJM palettes)
4. Ensure: Arial font, ≥300 DPI (≥600 for line art), colorblind-safe palette, axis labels with units
5. Generate figure legends
6. Export as TIFF/EPS/PDF per journal requirements

## Output
- `figures/*.tiff` — publication-ready figure files
- Figure legends in manuscript draft

## Mandatory next step
After completion → `manuscript-writing` (embed figures in Results).
