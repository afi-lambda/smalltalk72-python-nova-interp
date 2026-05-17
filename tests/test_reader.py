from conftest import make_machine
from st72_reader import REPL, make_repl


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
    assert st.atoms.name_of(toks[0]) == "it's ok"


def test_reader_whitespace_and_token_boundaries():
    st, r = make_machine()
    toks = r.read_str("\n\t3   <=\t4  .\r")
    assert st.value_repr(toks[0]) == "3"
    assert st.atoms.name_of(toks[1]) == "<="
    assert st.value_repr(toks[2]) == "4"
    assert toks[3] == st.A_PER

    toks = r.read_str('?:"%#!_')
    assert toks == [st.A_QUEST, st.A_COLN, st.A_QUOTE, st.A_MACH, st.A_NOEV, st.A_BANG, st.A_ARROW]


def test_reader_edge_inputs_and_repl_paths(monkeypatch, capsys):
    st, r = make_machine()
    assert r.read_str("   \n\t") == []
    assert r.read_str("]") == []
    assert st.atoms.name_of(r.read_str("'unterminated")[0]) == "unterminated"

    repl = make_repl(st)
    assert isinstance(repl, REPL)
    _, rep = repl.run_line("3 + 4")
    assert rep == "7"

    answers = iter(["3 + 4", "", "q"])
    monkeypatch.setattr("builtins.input", lambda _p: next(answers))
    repl.loop()
    out = capsys.readouterr().out
    assert "Smalltalk-72" in out and "→ 7" in out
