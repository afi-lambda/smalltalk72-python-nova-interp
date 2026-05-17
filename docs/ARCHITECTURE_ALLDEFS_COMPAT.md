# Architecture: ST72 runtime + ALLDEFS compatibility layer

Date: 2026-05-17
Project: /home/alain/smalltalk72-python-nova-interp

## 1) Purpose

This document explains how the interpreter is structured and how ALLDEFS compatibility is implemented with minimal, readable code.

Design goal:
- keep VM core stable
- add compatibility through thin layers (reader + bootstrap + primitive aliases)
- exclude display/graphics and device/file subsystems

---

## 2) High-level architecture

Three layers:

1. Core VM/runtime (`st72.py`)
- object model, memory, activation records, eval/apply loop, message dispatch
- constants like `NIL` and `EMPTY`
- global dictionary and class-code dispatch table

2. Reader/parser (`st72_reader.py`)
- tokenization and source parsing into runtime vectors
- supports special tokens used by legacy syntax
- executes source snippets through `Reader.run(...)`

3. Primitive + compatibility layer (`st72_prims.py`, `st72_bootstrap.py`)
- native primitive handlers registered by `register_all(st)`
- alias/shim bindings for ALLDEFS names
- optional bootstrap loader for non-CODE `to ... (...)` definitions

Flow:
source text -> Reader tokens/vectors -> VM eval/apply -> primitive/class dispatch -> value

---

## 3) Core VM responsibilities (`st72.py`)

`st72.py` is the execution engine.

Key responsibilities:
- memory/object access helpers
- atom/integer/object representation utilities
- activation-record lifecycle (caller/return/global/message/program counter)
- eval/apply transitions
- truthiness and nil/false behavior

Important semantic facts:
- `NIL` is address `0` (unbound/sentinel)
- `EMPTY` is the `false` object
- many runtime paths treat both as falsy, but identity differs (`nil != false`)

Compatibility implication:
- do not collapse `nil` into `false`
- prefer additive shims over core loop rewrites

---

## 4) Reader capabilities (`st72_reader.py`)

Reader is intentionally separate from runtime semantics.

Implemented/extended capabilities:
- signed integer parsing
- composite operators/tokens (`<= >= ~= <- => :: ~~ &* &+ &- &/`)
- subexpressions in `(...)` as vectorized units (in addition to `[...]`)

Reader does NOT perform bootstrap policy decisions.
It only parses and executes source snippets provided by caller code.

---

## 5) Primitive system and registration (`st72_prims.py`)

`register_all(st)` installs primitive handlers as built-in class entries and global names.

Two categories:
1) Canonical primitives (native runtime behavior)
- Number, Atom, to, eq, null, isnew, mkins, fetch, match, put, get, quot, false, repeat, again, done, apret, mem, rself, qfet, peekr

2) Compatibility aliases/shims (minimal additions)
- examples: `::`, `if`, `ev`, `apply`, `evapply`, `expand`, `getvec`, `addto`, `t`, `core`, `cr`, `is`, `#`, `-`, `nprint`, `class`, `number`, `atom`, `string`, `vector`, `float`, `read`
- these map legacy names to existing behavior with minimal code

Rationale:
- reduce missing/partial ALLDEFS entries without introducing a second execution model
- keep semantics centralized in existing primitives where possible

---

## 6) Optional live bootstrap loader (`st72_bootstrap.py`)

Entry point:
- `load_alldefs_kernel(st, path, strict=False)`
- exposed via `ST72.bootstrap_alldefs(path, strict=False)` in `st72.py`

Loader behavior:
1. parse ALLDEFS file
2. find `to ... (...)` definitions
3. extract balanced body (quote-aware)
4. skip CODE-tagged defs
5. skip unsupported names (display/graphics/device/file/system)
6. execute safe defs via `Reader.run("to ... .")`
7. return stats:
   - `loaded`
   - `skipped_code`
   - `skipped_unsupported`
   - `failed`

Strict mode:
- malformed entries raise immediately
- non-strict mode accumulates failures in stats

---

## 7) Compatibility status model

Audit document:
- `docs/ALLDEFS_COMPAT_AUDIT_2026-05-17.md`

Statuses:
- implemented: direct primitive/global mapping exists
- partial: candidate or semantic gap remains
- missing: intentionally out-of-scope or no mapping

Current shape after recent work:
- implemented increased via alias/shim registration
- missing mostly corresponds to excluded display/graphics + IO/device families

---

## 8) Why `nil` is treated specially

`nil` is core runtime sentinel state, not just syntax sugar.

Implications:
- `nil` must remain identity-distinct from `false`
- binding `nil` to false-class primitive behavior changes observable semantics (`nil .` regression)
- compatibility work should preserve existing `nil` global and VM truth rules

---

## 9) `arec` and `print`: architectural note

`print`:
- can be added as thin behavior wrapper
- low risk if contract is explicit (output target + return value)

`arec`:
- tied to activation-record semantics
- simple name binding is easy; faithful behavior needs a clear frame-model contract
- medium complexity due to coupling with eval/apply and AR layout

---

## 10) Testing and quality gates

Test strategy:
- focused unit tests for reader/primitives/bootstrap
- integration tests for `bootstrap_alldefs`
- audit sanity check for count consistency
- full-suite regression check

Quality gate:
- `python3 -m pytest`
- coverage threshold enforced at 78%

---

## 11) Extension rules (senior/minimal style)

When extending compatibility:
1. prefer alias-to-existing-primitive over new logic
2. if new logic is needed, keep helper small/pure
3. avoid modifying eval/apply core unless mandatory
4. add one focused test per behavior
5. keep unsupported domains explicit (display/graphics, device/file)

This preserves readability, minimizes line count, and keeps risk localized.