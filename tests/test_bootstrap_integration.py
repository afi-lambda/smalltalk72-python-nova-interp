from conftest import make_machine


def test_bootstrap_alldefs_integration(tmp_path):
    st, r = make_machine()
    p = tmp_path / "defs.txt"
    p.write_text("to one (1)\n", encoding="latin-1")
    stats = st.bootstrap_alldefs(str(p))
    assert stats["loaded"] == 1
    assert st._globals.get(st.atoms.intern("one")) is not None
    assert st.value_repr(r.run("one .")) == "[1]"


def test_bootstrap_optional_no_file_breakage():
    st, r = make_machine()
    try:
        st.bootstrap_alldefs("/tmp/no-such-file-xyz.txt")
        assert False, "expected file error"
    except FileNotFoundError:
        pass
    assert st.value_repr(r.run("3 + 4 .")) == "7"
