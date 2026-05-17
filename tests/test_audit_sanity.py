import re
from pathlib import Path


def test_audit_summary_shape_and_total_consistency():
    p = Path(__file__).resolve().parents[1] / "docs" / "ALLDEFS_COMPAT_AUDIT_2026-05-17.md"
    t = p.read_text(encoding="utf-8")
    total = int(re.search(r"Total unique `to` definitions parsed: (\d+)", t).group(1))
    implemented = int(re.search(r"Implemented: (\d+)", t).group(1))
    partial = int(re.search(r"Partial: (\d+)", t).group(1))
    missing = int(re.search(r"Missing: (\d+)", t).group(1))
    assert total == implemented + partial + missing
    assert total >= 50
