from conftest import make_machine, assert_eval


def test_print_builtin_outputs_and_returns_value(capsys):
    st, r = make_machine()
    assert_eval(st, r, "print 3 .", "3")
    out = capsys.readouterr().out
    assert "3" in out


def test_print_name_is_bound():
    st, _ = make_machine()
    assert st._globals.get(st.atoms.intern("print")) is not None
