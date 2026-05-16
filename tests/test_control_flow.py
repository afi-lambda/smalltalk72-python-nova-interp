from conftest import make_machine, assert_eval


def test_conditionals_and_fetch_style_transitions():
    st, r = make_machine()
    assert_eval(st, r, "3 < 4 ? [ 99 ] .", "99")
    assert_eval(st, r, "4 < 3 ? [ 99 ] .", "false")
    # ':' fetch from caller stream (RETN-dependent behavior)
    assert_eval(st, r, '" hello : " world .', "'world'")


def test_eval_apply_mixed_flow_smoke():
    st, r = make_machine()
    # exercise eval->apply transitions across Number, false, and quoted vectors
    assert_eval(st, r, "42 .", "42")
    assert_eval(st, r, "false ? [ 7 ] .", "false")
    assert_eval(st, r, "3 < 4 ? [ 1 + 2 ] .", "3")
