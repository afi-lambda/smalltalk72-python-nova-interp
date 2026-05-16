# Smalltalk-72 Nova Interpreter — Development Account

Faithful Python translation of the Smalltalk-72 Nova assembly sources:
`EVAL.SR`, `FUNCS.SR`, `PAGE0.SR`, `CODE.SR`, `READ.SR` (deduced from `SMALL.SYMS`).

Original sources from [pablomarx/Smalltalk72](https://github.com/pablomarx/Smalltalk72).

---

## What was built

A Python interpreter that mirrors the architecture of the original Nova assembly
implementation as closely as possible, rather than being a clean-room redesign.
The starting point was the HOPL one-pager by Alan Kay; the actual source files
(`EVAL.SR`, `FUNCS.SR`, `CODE.SR`, etc.) were then used to drive a faithful
translation.

Four files, zero external dependencies:

| File | Mirrors | Contents |
|---|---|---|
| `st72.py` | EVAL.SR + FUNCS.SR + PAGE0.SR | VMem, AtomTable, ST72 machine, eval/apply loop |
| `st72_prims.py` | CODE.SR | All primitive class handlers |
| `st72_reader.py` | READ.SR (deduced) | Tokenizer, sub-expression compiler, REPL |
| `st72_tests.py` | — | Integration tests (11 groups) |

---

## Memory model (`st72.py`)

Mirrors Nova vmem exactly: a flat Python list `mem[]` of ints indexed by address.

**Address spaces** (from `SMALL.PARMS` + `PAGE0.SR`):

| Range | Contents |
|---|---|
| `0` | NIL |
| `1 .. MXATM-1` (1..2047) | Atom table |
| `SINTB .. MXNUM` (2056..2569) | Small integer table |
| `BHMEM` downward | Heap objects (2-word pairs) |
| `BHMEM` upward | Activation records |

**Heap objects** (2 words at address A):
```
mem[A]   = CLASS_addr | refcount  (RCMSK = 0o177770 kills low 3 bits)
mem[A+1] = payload / value
```

**Built-in class addresses** (octal, fixed by `PAGE0.SR`):

| Name | Address | Decimal |
|---|---|---|
| MASTER (Class) | 0o5210 | 2184 |
| NCLAS (Number) | 0o5260 | 2224 |
| LSCLA (Vector) | 0o5350 | 2280 |
| ATCLS (Atom)   | 0o5430 | 2328 |
| SCLAS (String) | 0o5470 | 2360 |
| ARCLS (ARecord)| 0o5540 | 2400 |
| EMPTY (false)  | 0o5126 | 2134 |

---

## AREC layout (from `ARTAB` / `ACTIV` in `EVAL.SR`)

Each activation record is 11+ words in vmem:

| Offset | Field | Description |
|---|---|---|
| 0 | CLASS0 | Class of activation-class (for CACT/HFRE sizing) |
| 1 | MASK | Class hash-table mask / nvars |
| 2 | INST | Instance the activation is running on |
| 3 | MESS | Pointer to current message vector |
| 4 | GLOB | Enclosing global scope AREC |
| 5 | RETN | Caller AREC (0 = top level) |
| 6 | CLAS | Class of this activation |
| 7 | MODE | 2=EVAL, 3=APPLY |
| 8 | PC | Program counter (index into MESS) |
| 9 | VALUE | Current value (shadowed in `st.VALUE`) |
| 10 | TOKEN | Current token (shadowed in `st.TOKEN`) |
| 11+ | locals | Local variables (NIL-initialised) |

Message vectors (LSCLA objects): `[LSCLA, len, tok0, …, tokN-1]`.

**FIND chain**: `GLOB` links ARECs for lexical scoping (mirrors FIND/FND3A in `FUNCS.SR`).

---

## Eval/apply loop (`_eval_loop`, `_emode`, `_amode`)

Mirrors `EL1` in `EVAL.SR`:

```
MODE < 3  →  EMODE: advance PC, dispatch on token type
MODE == 3 →  AMODE: re-activate current VALUE against remaining message
```

Key dispatch functions:

| Method | Nova label | Description |
|---|---|---|
| `_emode` | EM1/EMODE | One eval-mode step: advance PC, dispatch |
| `_amode` | AMODE | Apply VALUE to message |
| `_efind` | EFIND | Look up TOKEN in GLOBX; dispatch `?`/`"` |
| `_tori` | TORI | Template-or-instance dispatch |
| `_atorn` | ATORN | Atom/small-int dispatch |
| `_activ` | ACTIV | Allocate AREC, switch SELF |
| `_eret` | ERET | Passive return |
| `_aret` | ARET | Active return (peek '.' or → APPLY mode) |
| `_sretn` | SRETN | Pop activation, sync caller PC |
| `_fmode` | FMODE | `:` fetch-and-bind (FM3/FM6/FM7 variants) |
| `_conds` | CONDS | `?` conditional — redirect MESS into branch |
| `_quot` | QUOT | `"` quote next token |
| `_mach` | MACH/MACHLP | `%` pattern match |
| `_faret` | FARET | `!` active return without activating |
| `_find` | FIND/FND3A | Chase GLOB chain for token lookup |

**PC propagation in `_sretn`**: when a primitive's AREC shares the same message
vector as its caller (set by `_activ`), `_sretn` syncs the caller's PC before
popping. This is the mechanism by which `NUM1C`/`ATOM1C` consume tokens from the
caller's stream.

---

## Primitives (`st72_prims.py`, from `CODE.SR`)

Registered via `register_all(st)`. Each is a Python callable `fn(st: ST72) → None`.

| Name | Nova primitive | Notes |
|---|---|---|
| Number | NUM1C | `+` `-` `*` `/` `mod` `=` `#` `<` `<=` `>` `>=` `&*` `&+` `&-` `&/` |
| Atom | ATOM1C | `_` (assign) `chars` `eval` `=` |
| to | TO1C | Define new template/class |
| eq | EQ1C | Pointer equality |
| null | NULLC | NIL test |
| isnew | ISNEWC | Allocate instance if nil |
| mkins | MKINSC | Make instance |
| fetch | FET1C | Nested fetch from GLOB |
| match | MAT1C | Peek-match in GLOB's message |
| put | PUT1C | Store into binding table |
| get | GET1C | Load from binding table |
| quot | QUOT1C | Quote next token, active return |
| false | EMPT1C | `?` (skip) `or` `and` `>` `=` `<` |
| repeat | RPT1C | Repeat loop (Python for-loop impl) |
| again | AGAINC | Loop restart (simplified: eret) |
| done | DONE1C | Exit repeat with value |
| apret | APRETC | Apply-return to GLOB scope |
| mem | MEM1C | Raw vmem read/write |
| rself | RSELFC | Return self (instance) |
| qfet | QFETC | Quoted fetch from GLOB message |
| peekr | PEEKC | Peek at GLOB message without advancing |

**Comparison return convention** (mirrors CODE.SR):
- True: `_rself` → returns INST via `_eret`
- False: `_rfalse` → if next token is `?`, skip the clause and `_eret`; otherwise `_aret` (active, enables `or`-style chaining)

---

## Reader (`st72_reader.py`)

Based on `READ.SR` (deduced from `SMALL.SYMS` exports) and the HOPL paper.

- Single-char specials: `. : ? " % ! # _`
- `[ ... ]` compile to inline message vectors (LSCLA objects) — sub-expressions
- `'text'` string literals (doubled `''` = escape)
- Word tokens: integers (decimal, with leading `-`) or atoms
- `run_str` in `st72.py` delegates here; `REPL` class for interactive use

---

## Test status

| Suite | Tests | Status |
|---|---|---|
| `python3 st72.py` (internal eval) | 10 | 11/11 ✓ |
| `python3 st72_tests.py` (integration) | 11 groups | 11/11 ✓ |

Test groups in `st72_tests.py`: arithmetic, comparisons, bitwise, quote/atoms,
globals, conditionals, false-ops, reader sub-expressions, null, eq, `to` define.

---

## Known limitations / open work

| Area | Status |
|---|---|
| `repeat`/`again` | Simplified: Python for-loop; `again` just erets (no proper GOTO restart) |
| String class (SCLAS) | Not implemented — string literals are interned as atoms |
| Display primitives | `dmove`, `turtle`, `dclear` etc. not implemented |
| File I/O | Alto sector-based `file` not implemented |
| `to` class locals | Declaration metadata stored but AREC local slot wiring incomplete |
| Ref-counting | RCMSK extracted but ref-counting not enforced (no GC pressure in tests) |
| REPL `read` | `read` would need CODE 2 (keyboard) — not implemented |
