import pytest

from st72 import ST72, NIL, EMPTY, AR_PC
from st72_prims import register_all, prim_get, prim_mem, prim_null, prim_number, prim_peekr, prim_qfet
from st72_reader import Reader


def make_st() -> tuple[ST72, Reader]:
    st = ST72()
    register_all(st)
    return st, Reader(st)


def test_run_tests_smoke():
    import st72
    st72.run_tests()


def test_number_div_zero_and_mod_zero_raise():
    st, r = make_st()
    with pytest.raises(ZeroDivisionError):
        r.run("1 / 0 .")
    with pytest.raises(ZeroDivisionError):
        r.run("1 mod 0 .")


def test_number_bitshift_paths():
    st, r = make_st()
    assert st.value_repr(r.run("8 &/ 1 .")) == "16"
    assert st.value_repr(r.run("8 &/ -1 .")) == "4"


def test_prim_null_non_nil_returns_inst():
    st, _ = make_st()
    ar = st.make_top_arec(st.make_vector([st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = ar
    st._inst = st.intern_int(9)
    prim_null(st)
    assert st.value_repr(st.VALUE) == "9"


def test_prim_get_non_master_returns_nil():
    st, _ = make_st()
    ar = st.make_top_arec(st.make_vector([st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = ar
    st._inst = st.intern_int(1)
    prim_get(st)
    assert st.VALUE == NIL


def test_prim_get_master_table_success_path():
    st, _ = make_st()
    table = st.defclass("TableX", [])
    key = st.atoms.intern("k")
    st._put(key, st.intern_int(11), table)

    ar = st.make_top_arec(st.make_vector([st.A_QUOTE, key, st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = ar
    st._inst = table
    prim_get(st)
    assert st.value_repr(st.VALUE) == "11"


def test_prim_mem_write_then_read():
    st, _ = make_st()

    wr = st.make_top_arec(st.make_vector([st.A_ARROW, st.A_QUOTE, st.intern_int(77), st.A_QUOTE, st.intern_int(200), st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = wr
    st._inst = NIL
    prim_mem(st)

    rd = st.make_top_arec(st.make_vector([st.intern_int(200), st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = rd
    st._inst = NIL
    prim_mem(st)
    assert st.value_repr(st.VALUE) == "77"


def test_prim_number_nil_inst_and_bad_ampersand_op():
    st, _ = make_st()
    ar = st.make_top_arec(st.make_vector([st.atoms.intern("foo"), st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = ar
    st._inst = NIL
    prim_number(st)

    ar2 = st.make_top_arec(st.make_vector([st.atoms.intern("&"), st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = ar2
    st._inst = st.intern_int(3)
    with pytest.raises(RuntimeError, match="needs second operator"):
        prim_number(st)


def test_prim_number_non_numeric_compare_paths():
    st, _ = make_st()
    atom_x = st.atoms.intern("x")

    eq_msg = st.make_top_arec(st.make_vector([st.atoms.intern("="), st.A_QUOTE, atom_x, st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = eq_msg
    st._inst = st.intern_int(3)
    prim_number(st)
    assert st.VALUE == EMPTY

    ne_msg = st.make_top_arec(st.make_vector([st.atoms.intern("#"), st.A_QUOTE, atom_x, st.A_PER]))
    st.VALUE = NIL
    st.SELF = st.MESSX = st.GLOBX = ne_msg
    st._inst = st.intern_int(3)
    prim_number(st)
    assert st.value_repr(st.VALUE) == "3"


def test_qfet_and_peekr_paths():
    st, _ = make_st()
    tok = st.intern_int(42)
    glob = st.make_top_arec(st.make_vector([tok, st.A_PER]))
    ar = st.make_top_arec(st.make_vector([st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = ar
    st._glob = glob

    prim_peekr(st)
    assert st.VALUE == tok
    assert st.mem.ld(glob + AR_PC) == 0

    prim_qfet(st)
    assert st.VALUE == tok
    assert st.mem.ld(glob + AR_PC) == 1


def test_qfet_and_peekr_no_glob_return_nil():
    st, _ = make_st()
    ar = st.make_top_arec(st.make_vector([st.A_PER]))
    st.SELF = st.MESSX = st.GLOBX = ar
    st._glob = NIL

    prim_peekr(st)
    assert st.VALUE == NIL
    prim_qfet(st)
    assert st.VALUE == NIL
