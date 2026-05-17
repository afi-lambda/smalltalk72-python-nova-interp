from conftest import make_machine, assert_eval


def test_semantic_golden_snippets():
    st, r = make_machine()
    for src, want in [
        ("3 + 4 .", "7"), ("10 - 3 .", "7"), ("3 * 4 .", "12"), ("12 / 4 .", "3"),
        ("10 mod 3 .", "1"), ("6 &* 3 .", "2"), ("5 &+ 3 .", "7"), ("6 &- 3 .", "5"),
        ("8 &/ 1 .", "16"), ("8 &/ -1 .", "4"),
        ("3 = 3 .", "3"), ("3 = 4 .", "false"), ("3 # 4 .", "3"), ("3 < 4 .", "3"),
        ("4 < 3 .", "false"), ("3 <= 3 .", "3"), ("3 >= 3 .", "3"),
        ('" hello .', "'hello'"), ("nil .", "nil"), ("false .", "false"),
        ("false or 42 .", "42"), ("false and 42 .", "false"), ("nil null .", "false"),
        ("3 < 4 ? [ 99 ] .", "99"), ("4 < 3 ? [ 99 ] .", "false"),
    ]:
        assert_eval(st, r, src, want)
