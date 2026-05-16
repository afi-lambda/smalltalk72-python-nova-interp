# Smalltalk-72 Interpreter Quality Plan (Value-First)

Goal
Raise confidence and maintainability quickly by improving tests first, then increasing semantic coverage in the riskiest areas, while keeping code simple, readable, and elegant.

Guiding style
- Small functions, explicit names, no cleverness.
- Behavior-driven tests over print-driven tests.
- Keep architecture as-is unless tests prove a refactor is needed.
- Prefer deletion/simplification over adding abstraction.

---

## Phase 1 — Stabilize test foundation (highest ROI)

### Task 1: Convert test functions to proper pytest assertions
- File: `st72_tests.py`
- Replace bool-return patterns with plain asserts.
- Remove `ok &= ...` accumulation; each check should assert directly.

Why
- Removes pytest warnings that will become future failures.
- Gives precise, readable failure output.
- Makes tests CI-grade immediately.

Definition of done
- `python3 -m pytest -q st72_tests.py` passes with zero PytestReturnNotNone warnings.

### Task 2: Split test helpers into assertion helpers
- File: `st72_tests.py`
- Keep one helper that executes source and returns repr.
- Add `assert_eval(source, expected)` helper that raises clean assertion messages.

Why
- Keeps tests concise and readable.
- Standardizes failure messages.

Definition of done
- Tests read like spec lines:
  - `assert_eval("3 + 4 .", "7")`
  - `assert_eval("4 < 3 ? [ 99 ] .", "false")`

### Task 3: Add pytest config for explicit discovery
- File: `pytest.ini` (new)
- Configure discovery to include `st72_tests.py`.

Why
- Removes ambiguity ("no tests ran" by default).
- Standard command works for everyone.

Definition of done
- `python3 -m pytest -q` runs the suite without extra args.

---

## Phase 2 — Coverage where bugs are most expensive

### Task 4: Add branch-focused tests for `st72_prims.py`
- File: `st72_tests.py` (or split into `tests/test_prims_*.py`)
- Prioritize currently low-coverage primitives:
  - `fetch`, `match`, `put`, `get`
  - `isnew`, `mkins`
  - `repeat`, `again`, `done`
  - `qfet`, `peekr`, `mem`, `apret`

Why
- This module is semantic core and currently weakest (45%).
- Branch bugs here are subtle and high impact.

Definition of done
- Primitive module coverage increases meaningfully (target: 45% -> 60%+ first pass).

### Task 5: Add negative/edge-case tests
Examples:
- malformed token sequences
- empty vectors/messages
- missing globals
- unexpected operand types

Why
- Defensive confidence without changing runtime logic.
- Documents current interpreter behavior clearly.

Definition of done
- Failing paths are intentionally covered and assertions are explicit.

---

## Phase 3 — Reader and eval loop confidence

### Task 6: Add focused reader tests
- File: tests for `st72_reader.py` behavior:
  - nested `[ ... ]`
  - quoting edge cases
  - terminator handling (`.`)
  - whitespace and token boundaries

Why
- Reader is front door; parser ambiguity creates hard-to-debug failures later.

Definition of done
- Reader coverage moves from 49% toward 65%+.

### Task 7: Add eval/apply transition tests
- Target AMODE/EMODE and caller-stream-dependent ops (`:`, `?`, RETN interactions).

Why
- Core control flow deserves explicit executable specs.

Definition of done
- Critical state transitions are validated by tests, not comments.

---

## Phase 4 — Maintainability and CI guardrails

### Task 8: Organize tests by intent
Suggested structure:
- `tests/test_arithmetic.py`
- `tests/test_primitives.py`
- `tests/test_reader.py`
- `tests/test_control_flow.py`

Why
- Easier navigation and ownership.
- Faster debugging.

### Task 9: Add coverage and quality gates in CI
Run:
- `pytest -q`
- `pytest --cov=st72 --cov=st72_prims --cov=st72_reader --cov-report=term-missing`

Start with realistic threshold, then ratchet up incrementally.

Why
- Prevents silent regressions.

Definition of done
- PR fails on test failure or coverage drop below agreed baseline.

---

## Target outcomes (first milestone)
- Default pytest run works.
- Zero pytest return-value warnings.
- Coverage:
  - `st72_prims.py`: 45% -> >=60%
  - `st72_reader.py`: 49% -> >=65%
  - total core modules: 58% -> >=68%
- Test suite reads as a concise behavioral spec.

## Execution order (recommended)
1) Phase 1 completely
2) Phase 2 Task 4
3) Re-measure coverage
4) Phase 2 Task 5 + Phase 3 Task 6
5) Phase 3 Task 7
6) Phase 4
