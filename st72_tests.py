"""
st72_tests.py — Integration tests for Smalltalk-72 interpreter.

Tests structured by primitive groups, reader behavior, and end-to-end flows.
"""

from st72 import ST72
from st72_prims import register_all
from st72_reader import Reader


def make_machine() -> tuple[ST72, Reader]:
    st = ST72()
    register_all(st)
    r = Reader(st)
    return st, r


def eval_repr(source: str, st: ST72, r: Reader) -> str:
    return st.value_repr(r.run(source))


def assert_eval(source: str, expected_repr: str, st: ST72, r: Reader):
    got = eval_repr(source, st, r)
    assert got == expected_repr, (
        f"source={source!r} expected={expected_repr!r} got={got!r}"
    )


def test_arithmetic():
    st, r = make_machine()
    assert_eval("3 + 4 .", "7", st, r)
    assert_eval("10 - 3 .", "7", st, r)
    assert_eval("3 * 4 .", "12", st, r)
    assert_eval("12 / 4 .", "3", st, r)
    assert_eval("10 mod 3 .", "1", st, r)
    assert_eval("-5 + 2 .", "-3", st, r)
    assert_eval("0 + 0 .", "0", st, r)
    assert_eval("100 * 3 .", "300", st, r)


def test_comparisons():
    st, r = make_machine()
    # True cases return self (the number), false returns 'false'.
    assert_eval("3 = 3 .", "3", st, r)
    assert_eval("3 = 4 .", "false", st, r)
    assert_eval("3 < 4 .", "3", st, r)
    assert_eval("4 < 3 .", "false", st, r)
    assert_eval("4 > 3 .", "4", st, r)
    assert_eval("3 > 4 .", "false", st, r)
    assert_eval("3 <= 3 .", "3", st, r)
    assert_eval("3 >= 3 .", "3", st, r)
    assert_eval("3 # 4 .", "3", st, r)
    assert_eval("3 # 3 .", "false", st, r)


def test_bitwise():
    st, r = make_machine()
    assert_eval("6 &* 3 .", "2", st, r)  # AND
    assert_eval("5 &+ 3 .", "7", st, r)  # OR
    assert_eval("6 &- 3 .", "5", st, r)  # XOR


def test_quote():
    st, r = make_machine()
    assert_eval('" hello .', "'hello'", st, r)
    assert_eval("42 .", "42", st, r)
    assert_eval("-7 .", "-7", st, r)
    assert_eval("nil .", "nil", st, r)
    assert_eval("false .", "false", st, r)


def test_globals():
    st, r = make_machine()
    st.defglobal("x", st.intern_int(0))
    assert_eval("x .", "0", st, r)

    st.defglobal("y", st.intern_int(99))
    assert_eval("y .", "99", st, r)
    assert_eval("y + 1 .", "100", st, r)


def test_conditional():
    st, r = make_machine()
    assert_eval("3 < 4 ? [ 99 ] .", "99", st, r)
    assert_eval("4 < 3 ? [ 99 ] .", "false", st, r)


def test_false_ops():
    st, r = make_machine()
    assert_eval("false or 42 .", "42", st, r)
    assert_eval("false and 42 .", "false", st, r)
    assert_eval("false = false .", "false", st, r)


def test_reader_subexpr():
    st, r = make_machine()
    tokens = r.read_str("[ 1 2 3 ] .")
    vec = tokens[0]

    assert st.is_vector(vec), "[ 1 2 3 ] should produce a vector"
    assert st.vec_len(vec) == 3
    assert st.obj_int_value(st.vec_get(vec, 0)) == 1


def test_null():
    st, r = make_machine()
    assert_eval("nil null .", "false", st, r)


def test_eq():
    st, r = make_machine()
    hello = st.atoms.intern("hello")
    st.defglobal("hello", hello)
    st.defglobal("world", st.atoms.intern("world"))
    assert_eval('" hello eq " hello " hello .', "'hello'", st, r)


def test_to_define():
    st, r = make_machine()
    r.run("to Double : x [ x + x ] .")

    double_atom = st.atoms.intern("Double")
    double_cls = st._globals.get(double_atom)
    assert double_cls is not None, "'to Double' should define class"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main(["-q", __file__]))
