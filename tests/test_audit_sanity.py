from pathlib import Path


def _extract_count(text: str, prefix: str) -> int:
    for line in text.splitlines():
        if prefix in line:
            return int(line.rsplit(":", 1)[1].strip())
    raise AssertionError(f"missing summary line: {prefix}")


def test_audit_summary_shape_and_total_consistency():
    p = Path(__file__).resolve().parents[1] / "docs" / "ALLDEFS_COMPAT_AUDIT_2026-05-17.md"
    t = p.read_text(encoding="utf-8")
    total = _extract_count(t, "Total unique `to` definitions parsed")
    implemented = _extract_count(t, "Implemented")
    partial = _extract_count(t, "Partial")
    missing = _extract_count(t, "Missing")
    assert total == implemented + partial + missing
    assert total >= 50
