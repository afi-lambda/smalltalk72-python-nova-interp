from st72 import ST72
from st72_prims import register_all
from st72_reader import Reader


def make_machine() -> tuple[ST72, Reader]:
    st = ST72()
    register_all(st)
    return st, Reader(st)


def assert_eval(st: ST72, r: Reader, src: str, expected: str):
    got = st.value_repr(r.run(src))
    assert got == expected, f"source={src!r} expected={expected!r} got={got!r}"
