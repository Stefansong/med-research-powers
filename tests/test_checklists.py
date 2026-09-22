"""Structural tests for the reporting-standards index and the per-item checklist YAMLs."""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST_DIR = ROOT / "skills" / "reporting-standards" / "references" / "checklists"
INDEX = CHECKLIST_DIR / "standards-index.yaml"
NUMBER = re.compile(r"^(\d+|[IVX]+)")  # DECIDE-AI uses roman numerals for its generic items


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def checklist_files():
    return sorted(p for p in CHECKLIST_DIR.glob("*.yaml") if p.name != "standards-index.yaml")


def test_index_counts_and_files():
    idx = load(INDEX)["standards"]
    assert len(idx) == 47
    ids = [s["id"] for s in idx]
    assert len(ids) == len(set(ids)), "duplicate standard ids"
    with_file = [s for s in idx if s.get("file")]
    assert len(with_file) == 21
    for s in with_file:
        assert (CHECKLIST_DIR / s["file"]).exists(), f"{s['id']}: {s['file']} missing"
    # every checklist file is referenced from the index exactly once
    referenced = {s["file"] for s in with_file}
    on_disk = {p.name for p in checklist_files()}
    assert referenced == on_disk, f"unreferenced or missing: {referenced ^ on_disk}"


def test_consort_2025_is_30_items_42_rows():
    d = load(CHECKLIST_DIR / "consort-2025.yaml")
    rows = [i for s in d["sections"] for i in s["items"]]
    assert d["total_items"] == 30 and len(rows) == 42
    idx = load(INDEX)["standards"]
    consort = next(s for s in idx if s["id"] == "consort-2025")
    assert str(consort["items"]).startswith("30")


@pytest.mark.parametrize("path", checklist_files(), ids=lambda p: p.stem)
def test_checklist_structure(path):
    d = load(path)
    for key in ("name", "total_items", "total_rows", "reference", "sections"):
        assert key in d, f"{path.name}: missing {key}"
    rows = [i for s in d["sections"] for i in s["items"]]
    assert len(rows) == d["total_rows"], f"{path.name}: rows {len(rows)} != total_rows {d['total_rows']}"
    ids = [str(i["id"]) for i in rows]
    assert len(ids) == len(set(ids)), f"{path.name}: duplicate item ids"
    if d["total_items"] != d["total_rows"]:
        # sub-items share a number (1a/1b, 21a-d, roman numerals in DECIDE-AI); extension checklists
        # (CONSORT-AI, SPIRIT-AI, RECORD) count one item per row and are covered by the row check above
        numbered = {NUMBER.match(i).group(1) for i in ids if NUMBER.match(i)}
        assert len(numbered) == d["total_items"], (
            f"{path.name}: {len(numbered)} numbered items != total_items {d['total_items']}")
    for i in rows:
        assert isinstance(i["id"], str), f"{path.name}: id {i['id']!r} must be a string"
        assert i.get("text") and len(i["text"]) >= 5, f"{path.name}: item {i['id']} has no text"
    assert any(i.get("critical") for i in rows), f"{path.name}: no critical items marked (Gate 1 needs them)"
    assert "doi" in str(d["reference"]).lower() or "10." in str(d["reference"]), f"{path.name}: reference lacks a DOI"
