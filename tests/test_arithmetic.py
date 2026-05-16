from conftest import make_machine, assert_eval


def test_arithmetic_and_comparisons():
    st, r = make_machine()
    for src, want in [
        ("3 + 4 .", "7"), ("10 - 3 .", "7"), ("3 * 4 .", "12"), ("12 / 4 .", "3"),
        ("10 mod 3 .", "1"), ("-5 + 2 .", "-3"), ("3 = 3 .", "3"), ("3 = 4 .", "false"),
        ("3 < 4 .", "3"), ("4 < 3 .", "false"), ("3 <= 3 .", "3"), ("3 >= 3 .", "3"),
        ("3 # 4 .", "3"), ("3 # 3 .", "false"), ("6 &* 3 .", "2"), ("5 &+ 3 .", "7"),
        ("6 &- 3 .", "5"),
    ]:
        assert_eval(st, r, src, want)
