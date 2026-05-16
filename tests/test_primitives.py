from conftest import make_machine, assert_eval


def test_quote_globals_false_and_to():
    st, r = make_machine()
    for src, want in [
        ('" hello .', "'hello'"), ("42 .", "42"), ("-7 .", "-7"), ("nil .", "nil"),
        ("false .", "false"), ("false or 42 .", "42"), ("false and 42 .", "false"),
        ("false = false .", "false"), ("nil null .", "false"),
    ]:
        assert_eval(st, r, src, want)

    st.defglobal("x", st.intern_int(0))
    st.defglobal("y", st.intern_int(99))
    assert_eval(st, r, "x .", "0")
    assert_eval(st, r, "y + 1 .", "100")

    hello = st.atoms.intern("hello")
    st.defglobal("hello", hello)
    assert_eval(st, r, '" hello eq " hello " hello .', "'hello'")
    r.run("to Double : x [ x + x ] .")
    assert st._globals.get(st.atoms.intern("Double")) is not None
