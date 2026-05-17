from pathlib import Path

from conftest import make_machine
from st72_bootstrap import load_alldefs_kernel


def _w(tmp_path, text: str) -> str:
    p = tmp_path / "defs.txt"
    p.write_text(text, encoding="latin-1")
    return str(p)


def test_loader_loads_safe_and_skips_code(tmp_path):
    st, _ = make_machine()
    p = _w(tmp_path, """
to one (1)
to read (CODE 2)
""")
    s = load_alldefs_kernel(st, p)
    assert s["loaded"] == 1 and s["skipped_code"] == 1
    assert st._globals.get(st.atoms.intern("one")) is not None


def test_loader_skips_unsupported_and_handles_bad(tmp_path):
    st, _ = make_machine()
    p = _w(tmp_path, """
to dmove (x)
to ok x (:x. x)
to broken x (
""")
    s = load_alldefs_kernel(st, p)
    assert s["loaded"] == 1
    assert s["skipped_unsupported"] >= 1
    assert s["failed"] >= 1


def test_loader_strict_raises_on_malformed(tmp_path):
    st, _ = make_machine()
    p = _w(tmp_path, "to broken x (")
    try:
        load_alldefs_kernel(st, p, strict=True)
        assert False, "expected strict mode to raise"
    except ValueError:
        pass
