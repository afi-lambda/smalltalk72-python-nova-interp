# ALLDEFS missing/partial implementation plan (excluding display/graphics)

> For Hermes: execute in small commits, simplest-first, minimal lines, readability-first.

Goal: Reduce missing/partial ALLDEFS coverage for non-display/non-graphics features with the smallest clean code changes.

Style constraints:
- smallest correct change first
- no new abstraction layers unless reused >=2 times
- short pure helpers over classes
- behavior tests first, compact and explicit

Out of scope:
- display/graphics/input stack: dclear, dcomp, dmove, dmovec, dson, dsoff, indisp, sub, button, mouse, mx, my, show
- file/device stack: filin, TTY, kbck, kbd, newchars, reread, redo, edtarget

---

## Ordered worklist (simplest first)

1) Alias-only builtins for already-supported semantics
- Targets: nil, is, core, cr
- Idea: map names to existing behavior with tiny wrappers or alias registration only.
- Files:
  - modify: st72_prims.py (register_all aliases + tiny handlers if needed)
  - add tests: tests/test_bootstrap_aliases.py
- Est. LOC: 18-30

2) Make `::` available as callable builtin alias to fetch chain primitive
- Targets: ::
- Idea: route `::` to existing fetch-like behavior (same runtime path as current nested fetch semantics).
- Files:
  - modify: st72_prims.py
  - tests: tests/test_bootstrap_aliases.py
- Est. LOC: 10-18

3) Add minimal control helpers from partial set
- Targets: if, ev
- Idea: implement strict minimal semantics used in ALLDEFS forms only:
  - `if`: evaluate conditional branch token protocol already used by runtime
  - `ev`: explicit evaluate-next helper
- Files:
  - modify: st72_prims.py
  - tests: tests/test_control_helpers.py
- Est. LOC: 28-45

4) Add message/application helpers
- Targets: apply, evapply, expand
- Idea: thin wrappers over existing eval/apply machinery; no new execution model.
- Files:
  - modify: st72_prims.py
  - tests: tests/test_apply_helpers.py
- Est. LOC: 35-60

5) Add collection/string helpers with narrow scope
- Targets: getvec, t, addto
- Idea: implement only forms required by ALLDEFS non-IO flow; keep argument protocol strict and documented.
- Files:
  - modify: st72_prims.py
  - tests: tests/test_collection_helpers.py
- Est. LOC: 45-80

6) Decide and implement arithmetic/hash legacy entries that are still partial
- Targets: #, -, nprint
- Idea:
  - if already handled by Number dispatch in message form, register aliases only
  - if not callable directly in ALLDEFS paths, add tiny shim builtins
- Files:
  - modify: st72_prims.py
  - tests: tests/test_numeric_legacy_entries.py
- Est. LOC: 20-40

7) Close class-level partials with minimal compatibility shims
- Targets: class, number, atom, string, vector, float, read
- Idea: prefer registration/dispatch shims over reimplementation; use current class handlers.
- Files:
  - modify: st72_prims.py, st72_bootstrap.py (only if loader mapping needed)
  - tests: tests/test_class_shims.py
- Est. LOC: 35-70

8) Bootstrap loader compatibility pass
- Targets: ensure non-CODE definitions above are actually loadable and bound
- Idea: one compact loader pass update + strict diagnostics for skipped reasons.
- Files:
  - modify: st72_bootstrap.py
  - tests: tests/test_bootstrap_loader.py, tests/test_bootstrap_integration.py
- Est. LOC: 20-35

9) Recompute audit from script and lock regression checks
- Targets: docs/audit consistency
- Idea: keep full-table audit generation and add one test that sanity-checks summary counts shape.
- Files:
  - modify: docs/ALLDEFS_COMPAT_AUDIT_2026-05-17.md
  - add test: tests/test_audit_sanity.py
- Est. LOC: 15-30

---

## Execution protocol per item

For each item above:
1. write focused failing tests
2. implement minimal code to pass
3. run targeted tests
4. run full suite with coverage gate
5. commit one item per commit

Commands:
- targeted: python3 -m pytest -q tests/<new_test_file>.py
- full: python3 -m pytest

Commit style:
- feat(prims): add alias builtins for nil/is/core/cr
- feat(prims): add minimal if/ev helpers
- feat(bootstrap): improve non-CODE binding diagnostics
- test: add ALLDEFS helper coverage
- docs: refresh ALLDEFS compatibility audit

---

## Rough total estimate

- Total incremental LOC: 226-408
- Highest risk items: 4, 5, 7
- Lowest risk items: 1, 2, 9

## Definition of done

- Missing/partial reduced for all non-display/non-graphics targets listed above.
- Full test suite passes.
- Coverage stays >= 78%.
- Audit regenerated in full-table format, counts consistent with implementation state.
