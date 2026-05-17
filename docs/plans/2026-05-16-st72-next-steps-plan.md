# Smalltalk-72 Next Steps Plan (Value-First, Minimal-Line Style)

Goal
Increase confidence and semantic correctness with the fewest new lines possible, while keeping tests and code simple, readable, and elegant.

Style constraints
- Prefer short tests and tiny helpers.
- Avoid new abstractions unless they remove repetition immediately.
- Add only lines that improve correctness, clarity, or verification.

Current baseline
- st72.py: 82%
- st72_prims.py: 60%
- st72_reader.py: 61%
- total: 72%

---

## Phase A — Highest-value coverage with minimal code

### Task A1: Raise reader coverage to >=75%
Objective
Cover remaining parser/tokenizer behavior that can silently misparse user input.

Files
- Modify: tests/test_reader.py

Steps
1) Add compact tests for malformed/edge input:
- unmatched quote
- unmatched ] and nested [] boundaries
- empty input and whitespace-only input

2) Add compact tests for token boundaries:
- consecutive specials
- mixed operators and numbers with tight spacing

3) Run:
- python3 -m pytest tests/test_reader.py

Definition of done
- reader coverage >=75%
- tests remain concise and behavior-first

### Task A2: Raise primitive coverage to >=70%
Objective
Cover remaining low-cost, high-value semantic branches in st72_prims.

Files
- Modify: tests/test_prims_direct.py

Steps
1) Add branch tests with direct primitive invocation for:
- fetch/match/put success/failure branches
- isnew/mkins allocation and nil/non-nil paths
- apret and repeat/again/done control flow smoke paths

2) Keep setup minimal by reusing existing make_st helper and small inline ARECs.

3) Run:
- python3 -m pytest tests/test_prims_direct.py

Definition of done
- st72_prims coverage >=70%
- no production-code changes unless a test reveals a real bug

---

## Phase B — Semantic regression lock (small, high leverage)

### Task B1: Add golden semantic snippets
Objective
Create a tiny contract suite that catches subtle evaluator regressions.

Files
- Create: tests/test_semantic_golden.py

Steps
1) Add 20-30 one-line source→expected cases (table-driven).
2) Include arithmetic, comparisons, conditionals, quote/fetch, false ops.
3) Run:
- python3 -m pytest tests/test_semantic_golden.py

Definition of done
- golden suite is small, readable, and stable
- failures clearly show source, expected, got

---

## Phase C — CI ratchet and hygiene

### Task C1: Ratchet coverage gate upward
Objective
Keep CI strict but achievable.

Files
- Modify: pytest.ini

Steps
1) After A/B complete, measure real total coverage.
2) Set cov-fail-under to the verified new floor (no speculative target).
3) Run:
- python3 -m pytest

Definition of done
- gate blocks regressions without failing healthy PRs

### Task C2: Keep tests lean
Objective
Preserve minimal-line style as suite grows.

Files
- Modify: tests/*.py (only if needed)

Steps
1) Remove duplicated setup/assertions when trivial helper extraction reduces lines.
2) Avoid deep fixture trees; keep explicit local setup.

Definition of done
- tests stay easy to read in one pass

---

## Execution order
1) A1
2) A2
3) B1
4) C1
5) C2

## Verification commands
- python3 -m pytest
- python3 -m pytest --cov=st72 --cov=st72_prims --cov=st72_reader --cov-report=term-missing

## Success criteria
- st72_reader >=75%
- st72_prims >=70%
- total coverage increased from current 72%
- no unnecessary production complexity added
- tests remain short, readable, and elegant
