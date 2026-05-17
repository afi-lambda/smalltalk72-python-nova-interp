# Hybrid bootstrap (nova core + ALLDEFS live kernel) Implementation Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Reduce Python bootstrap/kernel code (excluding display/graphics) by loading safe ALLDEFS `to` definitions at runtime.

Architecture: Keep `st72.py` and `st72_prims.py` as execution substrate. Upgrade reader/tokenizer only where needed. Add a separate bootstrap loader module that ingests ALLDEFS, filters unsupported definitions, and installs safe high-level defs.

Tech Stack: Python 3, existing ST72 runtime (`st72.py`, `st72_reader.py`, `st72_prims.py`), pytest.

---

## Constraints (must hold)

- Do not rewrite VM/eval/apply core semantics in `st72.py`.
- Do not remove/replace CODE primitives from `st72_prims.py`.
- Exclude display/graphics/file-I/O primitives from bootstrap scope.
- Prefer minimum lines, simple readable code, no extra abstraction layers.

---

### Task 1: Baseline and guardrails

Objective: Lock current behavior before bootstrap changes.

Files:
- Modify: `tests/test_semantic_golden.py`
- Modify: `tests/test_reader.py`

Step 1: Add/confirm golden assertions for core behavior (`if/then/else`, arithmetic, comparisons, quote/fetch paths).

Step 2: Add/confirm reader assertions for composite tokens to preserve current parse contract.

Step 3: Run baseline.

Run:
`python3 -m pytest -q`

Expected:
- All tests pass.
- Coverage gate remains green.

Definition of done:
- Baseline test suite passes before any loader changes.

---

### Task 2: Add bootstrap loader module

Objective: Introduce ALLDEFS loader without touching reader responsibilities.

Files:
- Create: `st72_bootstrap.py`
- Test: `tests/test_bootstrap_loader.py`

Step 1: Implement `load_alldefs_kernel(st, path, *, strict=False) -> dict`.

Required behavior:
- Open ALLDEFS using `latin-1` with replacement.
- Extract line-start `to <name> (...)` definitions.
- Balanced-paren extraction for body.
- Skip any body containing `CODE`.
- Skip unsupported/system defs via explicit skiplist (display/graphics/io/editor/mouse/etc.).
- Compile/install safe defs into runtime globals/classes using existing runtime APIs.
- Return stats dict: `{"loaded": n, "skipped_code": n, "skipped_unsupported": n, "failed": n}`.

Step 2: Add unit tests for:
- loads simple safe defs,
- skips CODE defs,
- skips unsupported names,
- handles malformed entry without crashing (`strict=False`),
- raises on malformed entry in strict mode.

Step 3: Run targeted tests.

Run:
`python3 -m pytest tests/test_bootstrap_loader.py -q`

Expected:
- New loader tests pass.

Definition of done:
- Loader exists and is validated independently of REPL.

---

### Task 3: Wire optional bootstrap into startup flow

Objective: Enable live bootstrap as opt-in with safe fallback.

Files:
- Modify: `st72.py`
- Modify: `README.md`
- Test: `tests/test_bootstrap_integration.py`

Step 1: Add integration entry point (minimal):
- `ST72.bootstrap_alldefs(path, strict=False)` calling `st72_bootstrap.load_alldefs_kernel`.

Step 2: In CLI/REPL startup path, add optional ALLDEFS load:
- default: off,
- enabled via explicit argument or env var.

Step 3: Ensure failure fallback:
- if file missing/parse errors (non-strict), runtime still usable.

Step 4: Add integration tests:
- bootstrap on: selected defs become callable,
- bootstrap off: baseline behavior unchanged.

Run:
`python3 -m pytest tests/test_bootstrap_integration.py -q`

Expected:
- Integration tests pass.

Definition of done:
- Live bootstrap is optional and non-breaking.

---

### Task 4: Reader/token compatibility lift (only needed subset)

Objective: Accept tokens required by safe ALLDEFS defs while keeping reader simple.

Files:
- Modify: `st72_reader.py`
- Test: `tests/test_reader.py`

Step 1: Add only required composite token handling used by loaded defs (e.g. `<= >= ~= <- => :: ~~ &* &+ &- &/`) if currently missing.

Step 2: Keep reader API unchanged (`read_str`, `read_expr`, `run`).

Step 3: Extend tests with precise token boundary checks.

Run:
`python3 -m pytest tests/test_reader.py -q`

Expected:
- Reader tests pass with no regressions.

Definition of done:
- Reader supports required bootstrap syntax, with no expanded scope beyond necessity.

---

### Task 5: Reduce Python kernel duplication

Objective: Replace duplicated hardcoded high-level defs with ALLDEFS-loaded equivalents where safe.

Files:
- Modify: `st72_prims.py` (only if duplicate high-level wrappers can be removed safely)
- Modify: `st72.py` (bootstrap callsite/comments)
- Modify: `README.md`
- Test: `tests/test_semantic_golden.py`

Step 1: Identify high-level defs currently hardcoded in Python but now loaded from ALLDEFS safely.

Step 2: Remove only redundant glue; keep CODE primitives intact.

Step 3: Document exact retained-vs-loaded boundary.

Step 4: Re-run golden semantics.

Run:
`python3 -m pytest tests/test_semantic_golden.py -q`

Expected:
- Golden semantics unchanged for covered cases.

Definition of done:
- Net Python code reduction in bootstrap layer without semantic regression.

---

### Task 6: Compatibility audit refresh and coverage check

Objective: Quantify improvement and verify quality gates.

Files:
- Modify/Create: `docs/ALLDEFS_COMPAT_AUDIT_2026-05-17.md` (or a new dated report)

Step 1: Re-run compatibility audit script/method.

Step 2: Compare counts pre/post:
- implemented / partial / missing.

Step 3: Run full suite + coverage.

Run:
`python3 -m pytest`

Expected:
- Full test pass.
- Coverage gate passes.
- Audit shows improved implemented/partial coverage for non-CODE defs.

Definition of done:
- Measured compatibility delta and green CI quality bar.

---

## Rollout order

1. Task 1 baseline
2. Task 2 loader unit tests
3. Task 3 optional integration
4. Task 4 minimal reader lift
5. Task 5 duplication reduction
6. Task 6 audit + full validation

---

## Non-goals

- Full ALLDEFS parity including CODE/display/graphics/file-editor subsystems.
- Re-architecture of VM or primitive dispatch.
- Broad syntax redesign.

---

## Risks and mitigations

- Risk: Over-loading unsafe ALLDEFS defs.
  - Mitigation: explicit skiplist + strict/non-strict mode + tests.

- Risk: Reader complexity creep.
  - Mitigation: implement only token forms needed by safe defs.

- Risk: Hidden semantic drift.
  - Mitigation: golden tests + integration tests + compatibility diff.

---

## Success criteria

- Optional live bootstrap works from `ALLDEFS.ASCII.txt` for safe non-CODE defs.
- Python bootstrap glue is reduced while core VM/prims remain stable.
- Tests and coverage remain green.
- Compatibility audit shows improved non-CODE coverage.