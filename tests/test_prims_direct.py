import pytest

from st72 import ST72, NIL, EMPTY, AR_PC, AR_INST
from st72_prims import (
    register_all, prim_arec, prim_get, prim_mem, prim_null, prim_number, prim_peekr, prim_qfet,
    prim_put, prim_match, prim_mkins, prim_isnew, prim_fetch,
)
from st72_reader import Reader


def make_st() -> tuple[ST72, Reader]:
    st = ST72()
    register_all(st)
    return st, Reader(st)


def ctx(st: ST72, tokens: list[int], inst=NIL, glob=NIL):
    ar = st.make_top_arec(st.make_vector(tokens))
    st.SELF = st.MESSX = st.GLOBX = ar
    st._inst = inst
    st._glob = glob
    return ar


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
    ctx(st, [st.A_PER], inst=st.intern_int(9))
    prim_null(st)
    assert st.value_repr(st.VALUE) == "9"


def test_prim_get_non_master_returns_nil():
    st, _ = make_st()
    ctx(st, [st.A_PER], inst=st.intern_int(1))
    prim_get(st)
    assert st.VALUE == NIL


def test_prim_get_master_table_success_path():
    st, _ = make_st()
    table = st.defclass("TableX", [])
    key = st.atoms.intern("k")
    st._put(key, st.intern_int(11), table)
    ctx(st, [st.A_QUOTE, key, st.A_PER], inst=table)
    prim_get(st)
    assert st.value_repr(st.VALUE) == "11"


def test_prim_put_and_match_paths():
    st, _ = make_st()
    table = st.defclass("TableY", [])
    key, val = st.atoms.intern("k"), st.intern_int(33)
    st.defglobal("k", key)

    ctx(st, [key, st.A_QUOTE, val, st.A_PER], inst=table)
    prim_put(st)
    assert st._find(key, table) is not None

    glob = st.make_top_arec(st.make_vector([key, st.A_PER]))
    ctx(st, [key, st.A_PER], glob=glob)
    prim_match(st)
    assert st.mem.ld(glob + AR_PC) == 1

    glob2 = st.make_top_arec(st.make_vector([st.atoms.intern("z"), st.A_PER]))
    ctx(st, [key, st.A_PER], glob=glob2)
    prim_match(st)
    assert st.VALUE == EMPTY


def test_prim_mkins_isnew_and_fetch_paths():
    st, _ = make_st()
    table = st.defclass("Obj", [])

    ctx(st, [st.A_QUOTE, st.intern_int(2), st.A_QUOTE, table, st.A_PER])
    prim_mkins(st)
    obj = st.VALUE
    assert st.mem.ld(obj) == table
    assert st.mem.ld(obj + 1) == NIL and st.mem.ld(obj + 2) == NIL

    glob = st.make_top_arec(st.make_vector([st.A_QUOTE, st.intern_int(7), st.A_PER]))
    st.mem.st(glob + AR_INST, NIL)
    ctx(st, [st.A_PER], glob=glob)
    prim_isnew(st)
    assert st.mem.ld(glob + AR_INST) != NIL

    glob3 = st.make_top_arec(st.make_vector([st.A_QUOTE, st.intern_int(5), st.A_PER]))
    ctx(st, [st.A_PER], glob=glob3)
    prim_fetch(st)
    assert st.mem.ld(glob3 + AR_PC) >= 1


def test_prim_mem_write_then_read():
    st, _ = make_st()
    ctx(st, [st.A_ARROW, st.A_QUOTE, st.intern_int(77), st.A_QUOTE, st.intern_int(200), st.A_PER])
    prim_mem(st)
    ctx(st, [st.intern_int(200), st.A_PER])
    prim_mem(st)
    assert st.value_repr(st.VALUE) == "77"


def test_prim_number_nil_inst_and_bad_ampersand_op():
    st, _ = make_st()
    ctx(st, [st.atoms.intern("foo"), st.A_PER], inst=NIL)
    prim_number(st)

    ctx(st, [st.atoms.intern("&"), st.A_PER], inst=st.intern_int(3))
    with pytest.raises(RuntimeError, match="needs second operator"):
        prim_number(st)


def test_prim_number_non_numeric_compare_paths():
    st, _ = make_st()
    atom_x = st.atoms.intern("x")

    ctx(st, [st.atoms.intern("="), st.A_QUOTE, atom_x, st.A_PER], inst=st.intern_int(3))
    prim_number(st)
    assert st.VALUE == EMPTY

    st.VALUE = NIL
    ctx(st, [st.atoms.intern("#"), st.A_QUOTE, atom_x, st.A_PER], inst=st.intern_int(3))
    prim_number(st)
    assert st.value_repr(st.VALUE) == "3"


def test_qfet_and_peekr_paths():
    st, _ = make_st()
    tok = st.intern_int(42)
    glob = st.make_top_arec(st.make_vector([tok, st.A_PER]))
    ctx(st, [st.A_PER], glob=glob)

    prim_peekr(st)
    assert st.VALUE == tok
    assert st.mem.ld(glob + AR_PC) == 0

    prim_qfet(st)
    assert st.VALUE == tok
    assert st.mem.ld(glob + AR_PC) == 1


def test_qfet_and_peekr_no_glob_return_nil():
    st, _ = make_st()
    ctx(st, [st.A_PER], glob=NIL)
    prim_peekr(st)
    assert st.VALUE == NIL
    prim_qfet(st)
    assert st.VALUE == NIL


def test_prim_arec_lookup_set_and_missing():
    st, _ = make_st()
    key, key2 = st.atoms.intern("k"), st.atoms.intern("k2")
    val = st.intern_int(21)

    ar = ctx(st, [key, val, st.A_PER])
    prim_arec(st)
    assert st.VALUE == val
    assert st._find(key, ar) == val

    ctx(st, [key, st.A_PER])
    prim_arec(st)
    assert st.VALUE == NIL

    ctx(st, [key2, st.A_PER])
    prim_arec(st)
    assert st.VALUE == NIL
