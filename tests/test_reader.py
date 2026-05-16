from conftest import make_machine


def test_reader_subexpr_nested_strings_and_terminator():
    st, r = make_machine()

    toks = r.read_expr("3 + 4")
    assert toks[-1] == st.A_PER

    toks = r.read_str("[ 1 [ 2 3 ] ] .")
    outer = toks[0]
    assert st.is_vector(outer) and st.vec_len(outer) == 2
    inner = st.vec_get(outer, 1)
    assert st.is_vector(inner) and st.vec_len(inner) == 2

    toks = r.read_str("'it''s ok' .")
    atom = toks[0]
    assert st.atoms.name_of(atom) == "it's ok"


def test_reader_whitespace_and_token_boundaries():
    st, r = make_machine()
    toks = r.read_str("\n\t3   <=\t4  .\r")
    assert st.value_repr(toks[0]) == "3"
    assert st.atoms.name_of(toks[1]) == "<="
    assert st.value_repr(toks[2]) == "4"
    assert toks[3] == st.A_PER
