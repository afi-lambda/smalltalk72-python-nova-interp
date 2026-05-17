from conftest import make_machine
from st72_bootstrap import load_alldefs_kernel


def test_aliases_registered_in_globals():
    st, _ = make_machine()
    for name in (
        "is", "core", "cr", "::", "if", "ev", "apply", "evapply", "expand",
        "getvec", "addto", "t", "#", "-", "nprint", "class", "number", "atom",
        "string", "vector", "float", "read",
    ):
        assert st._globals.get(st.atoms.intern(name)) is not None, name


def test_loader_allows_single_char_and_partial_defs(tmp_path):
    st, _ = make_machine()
    p = tmp_path / "defs.txt"
    p.write_text("""
to one (1)
to - x (x)
to # x (x)
to t x (x)
""", encoding="latin-1")
    stats = load_alldefs_kernel(st, str(p))
    assert stats["loaded"] == 4
