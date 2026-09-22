"""Shared pytest configuration for MRP script tests.

Run from the repo root:  python3 -m pytest tests -q

Each test module loads the bundled script it exercises by inserting that script's
directory into sys.path (e.g. <repo>/skills/statistical-analysis/scripts). Test code
is exempt from the ${CLAUDE_PLUGIN_ROOT} rule that applies to SKILL.md examples.
"""

try:
    import matplotlib
    matplotlib.use("Agg")  # headless backend for figure tests; set before pyplot is imported anywhere
except ImportError:      # figure tests skip themselves when matplotlib is absent
    pass
