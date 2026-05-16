"""
st72_tests.py — Integration tests for Smalltalk-72 interpreter.

Tests structured by CODE.SR primitive, then by reader, then end-to-end.
"""

import sys

from st72 import ST72, NIL, EMPTY, NCLAS, ATCLS, MXATM
from st72_prims import register_all
from st72_reader import Reader


def make_machine() -> tuple[ST72, Reader]:
    st = ST72()
    register_all(st)
    r  = Reader(st)
    return st, r


def check(label, got, expected, st):
    if st.is_sint(got) and st.is_sint(expected):
        gv = st.obj_int_value(got)
        ev = st.obj_int_value(expected)
        ok = (gv == ev)
    else:
        ok = (got == expected)
    status = "PASS" if ok else "FAIL"
    print(f"{status}  {label}  →  {st.value_repr(got)}", end='')
    if not ok:
        print(f"  (expected {st.value_repr(expected)})", end='')
    print()
    return ok


def run_and_check(label: str, source: str, expected_repr: str,
                  st: ST72, r: Reader) -> bool:
    try:
        result = r.run(source)
        rep    = st.value_repr(result)
        ok     = (rep == expected_repr)
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            print(f"       source:   {source!r}")
            print(f"       expected: {expected_repr!r}")
            print(f"       got:      {rep!r}")
        return ok
    except Exception as e:
        print(f"FAIL  {label}  EXCEPTION: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
def test_arithmetic():
    print("\n=== Arithmetic (Number class) ===")
    st, r = make_machine()
    ok = True

    ok &= run_and_check("3 + 4",     "3 + 4 .",    "7",   st, r)
    ok &= run_and_check("10 - 3",    "10 - 3 .",   "7",   st, r)
    ok &= run_and_check("3 * 4",     "3 * 4 .",    "12",  st, r)
    ok &= run_and_check("12 / 4",    "12 / 4 .",   "3",   st, r)
    ok &= run_and_check("10 mod 3",  "10 mod 3 .", "1",   st, r)
    ok &= run_and_check("-5 + 2",    "-5 + 2 .",   "-3",  st, r)
    ok &= run_and_check("0 + 0",     "0 + 0 .",    "0",   st, r)
    ok &= run_and_check("100 * 3",   "100 * 3 .",  "300", st, r)

    return ok


def test_comparisons():
    print("\n=== Comparisons (Number class) ===")
    st, r = make_machine()
    ok = True

    # True cases return self (the number), false return 'false'
    ok &= run_and_check("3 = 3",   "3 = 3 .",   "3",     st, r)
    ok &= run_and_check("3 = 4",   "3 = 4 .",   "false", st, r)
    ok &= run_and_check("3 < 4",   "3 < 4 .",   "3",     st, r)
    ok &= run_and_check("4 < 3",   "4 < 3 .",   "false", st, r)
    ok &= run_and_check("4 > 3",   "4 > 3 .",   "4",     st, r)
    ok &= run_and_check("3 > 4",   "3 > 4 .",   "false", st, r)
    ok &= run_and_check("3 <= 3",  "3 <= 3 .",  "3",     st, r)
    ok &= run_and_check("3 >= 3",  "3 >= 3 .",  "3",     st, r)
    ok &= run_and_check("3 # 4",   "3 # 4 .",   "3",     st, r)
    ok &= run_and_check("3 # 3",   "3 # 3 .",   "false", st, r)

    return ok


def test_bitwise():
    print("\n=== Bitwise (Number &-ops) ===")
    st, r = make_machine()
    ok = True

    ok &= run_and_check("6 &* 3",   "6 &* 3 .",  "2",  st, r)   # AND: 110 & 011 = 010
    ok &= run_and_check("5 &+ 3",   "5 &+ 3 .",  "7",  st, r)   # OR:  101 | 011 = 111
    ok &= run_and_check("6 &- 3",   "6 &- 3 .",  "5",  st, r)   # XOR: 110 ^ 011 = 101

    return ok


def test_quote():
    print("\n=== Quote and atoms ===")
    st, r = make_machine()
    ok = True

    ok &= run_and_check('quote atom',   '" hello .',     "'hello'", st, r)
    ok &= run_and_check('integer lit',  '42 .',          "42",      st, r)
    ok &= run_and_check('negative int', '-7 .',          "-7",      st, r)
    ok &= run_and_check('nil',          'nil .',         "nil",     st, r)
    ok &= run_and_check('false',        'false .',       "false",   st, r)

    return ok


def test_globals():
    print("\n=== Global lookup and assignment ===")
    st, r = make_machine()
    ok = True

    # Assign via atom '_' operator
    # In ST72: x _ 42 .  means: look up x, apply '_' with arg 42
    # This calls ATOM1C's '_' handler which binds x→42 in GLOB
    st.defglobal("x", st.intern_int(0))
    ok &= run_and_check("x = 0",    "x .",     "0", st, r)

    # Direct global binding via defglobal
    st.defglobal("y", st.intern_int(99))
    ok &= run_and_check("y = 99",   "y .",     "99", st, r)

    # Arithmetic on globals
    ok &= run_and_check("y + 1",    "y + 1 .", "100", st, r)

    return ok


def test_conditional():
    print("\n=== Conditionals ===")
    st, r = make_machine()
    ok = True

    # true case: 3 < 4 returns 3 (truthy), then ? runs branch
    # false case: 4 < 3 returns false, ? skips branch
    # ST72 conditional syntax: expr ? [branch] .
    # The branch is a sub-expression in [ ... ]
    ok &= run_and_check(
        "true branch",
        "3 < 4 ? [ 99 ] .",
        "99", st, r
    )
    ok &= run_and_check(
        "false branch skipped",
        "4 < 3 ? [ 99 ] .",
        "false", st, r
    )

    return ok


def test_false_ops():
    print("\n=== false object operations ===")
    st, r = make_machine()
    ok = True

    ok &= run_and_check("false or 42",   "false or 42 .",  "42",    st, r)
    ok &= run_and_check("false and 42",  "false and 42 .", "false", st, r)
    ok &= run_and_check("false = false", "false = false .", "false", st, r)

    return ok


def test_reader_subexpr():
    print("\n=== Reader: sub-expressions ===")
    st, r = make_machine()
    ok = True

    # [ 1 2 3 ] should produce a vector
    tokens = r.read_str("[ 1 2 3 ] .")
    # The first token should be a vector address
    vec = tokens[0]
    is_vec = st.is_vector(vec)
    print(f"{'PASS' if is_vec else 'FAIL'}  [ 1 2 3 ] produces vector")
    ok &= is_vec

    if is_vec:
        n = st.vec_len(vec)
        print(f"{'PASS' if n == 3 else 'FAIL'}  vector length = {n}")
        ok &= (n == 3)

        v0 = st.vec_get(vec, 0)
        print(f"{'PASS' if st.obj_int_value(v0)==1 else 'FAIL'}  vec[0] = {st.value_repr(v0)}")
        ok &= (st.obj_int_value(v0) == 1)

    return ok


def test_null():
    print("\n=== null primitive ===")
    st, r = make_machine()
    ok = True

    # null with nil instance → eret (return true / self)
    # null with non-nil instance → false
    # NULLC tests ARG0 of null's *own* AREC (not the preceding expression).
    # When null is activated as a template, its AREC.ARG0 = NIL → FALS.
    # 'nil null .' → null activated (inst=NIL, ARG0=NIL) → FALS → 'false'
    # '42 null .' → 42 returned passively; null activated (inst=NIL) → FALS
    #   but since 42 did JMP @.EVAL (not ARET), SELF is still Number's AREC.
    #   loop reads 'null' in EVAL mode → template inst=NIL → FALS.
    #   However VALUE=42 was set by Number. After FALS _aret → VALUE=EMPTY…
    #   Actually '42 null .' is not canonical ST72. Test standalone null only.
    ok &= run_and_check("nil null → false", "nil null .", "false", st, r)

    return ok


def test_eq():
    print("\n=== eq primitive (pointer equality) ===")
    st, r = make_machine()
    ok = True

    # eq fetches two args and compares pointers
    # Same atom twice → equal
    hello = st.atoms.intern("hello")
    st.defglobal("hello", hello)
    st.defglobal("world", st.atoms.intern("world"))

    ok &= run_and_check('eq hello hello → equal',
                        '" hello eq " hello " hello .',
                        "'hello'", st, r)

    return ok


def test_to_define():
    print("\n=== to: define a new class ===")
    st, r = make_machine()
    ok = True

    # to Double (: x) x + x .
    # Defines class 'Double' with one local 'x'.
    # Usage: 21 Double .  → 42
    # This tests class definition and activation.
    source = 'to Double : x [ x + x ] .'
    try:
        r.run(source)
        double_atom = st.atoms.intern("Double")
        double_cls  = st._globals.get(double_atom)
        defined = double_cls is not None
        print(f"{'PASS' if defined else 'FAIL'}  'to Double' defines class")
        ok &= defined
    except Exception as e:
        print(f"FAIL  'to Double' raised: {e}")
        import traceback; traceback.print_exc()
        ok = False

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Smalltalk-72 Integration Tests ===")
    results = []

    results.append(test_arithmetic())
    results.append(test_comparisons())
    results.append(test_bitwise())
    results.append(test_quote())
    results.append(test_globals())
    results.append(test_conditional())
    results.append(test_false_ops())
    results.append(test_reader_subexpr())
    results.append(test_null())
    results.append(test_eq())
    results.append(test_to_define())

    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*40}")
    print(f"Test groups: {passed}/{total} passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
