# Smalltalk-72 Nova Interpreter (Python)

Faithful Python translation of the original Smalltalk-72 Nova assembly sources.
Zero external dependencies.

## What it is

The original Smalltalk-72 ran on a Data General Nova minicomputer. Its evaluator
was written in Nova assembly across five source files: `EVAL.SR`, `FUNCS.SR`,
`PAGE0.SR`, `CODE.SR`, and `READ.SR`. This project translates those sources to
Python as faithfully as possible — including the flat virtual memory model, the
activation-record layout, and the eval/apply loop structure.

This is distinct from the
[arec interpreter](https://github.com/afi-lambda/smalltalk72-python-arec-interpreter),
which is a clean-room Python redesign focused on the token-stream semantics.

## Files

| File | Mirrors | Contents |
|---|---|---|
| `st72.py` | EVAL.SR + FUNCS.SR + PAGE0.SR | VMem, ST72 machine, eval/apply loop |
| `st72_prims.py` | CODE.SR | Primitive class handlers (Number, Atom, to, …) |
| `st72_reader.py` | READ.SR | Tokenizer, `[ ]` sub-expressions, REPL |
| `st72_tests.py` | — | Integration tests |
| `ALLDEFS.ASCII.txt` | ALLDEFS | Original Smalltalk-72 class definitions (reference) |
| `smalltalk72_nova_interp.md` | — | Full development account and architecture reference |

## Usage

```bash
# Run internal eval tests
python3 st72.py

# Run integration tests
python3 st72_tests.py

# Interactive REPL
python3 st72.py repl
```

### REPL example

```
st72> 3 + 4 .
  → 7
st72> 3 < 4 ? [ 99 ] .
  → 99
st72> false or 42 .
  → 42
st72> " hello .
  → 'hello'
```

## Architecture

The central structure is the **AREC** (activation record): a 11-word struct in
flat vmem. `st.SELF` always points to the current AREC, mirroring the Nova `SELF`
page-zero register.

The main eval loop (`_eval_loop`) mirrors `EL1` in `EVAL.SR`:
- `MODE < 3` → EMODE: advance PC, dispatch on token
- `MODE == 3` → AMODE: apply current VALUE against remaining message

`RETN` (caller AREC pointer) enables the `:` fetch and `?` match operators to
reach back into the caller's live message stream — the core mechanism of
Smalltalk-72 method activation.

## Test status

```
python3 st72.py        → 10/10 eval unit tests
python3 st72_tests.py  → 11/11 integration test groups
```

## Limitations

- `String` class not fully implemented (literals interned as atoms)
- Display/graphics primitives not implemented
- `repeat`/`again` uses a Python loop (no proper GOTO restart)
- No file I/O (Alto sector-based storage)

## References

- [pablomarx/Smalltalk72](https://github.com/pablomarx/Smalltalk72) — original Nova sources
- Alan Kay, HOPL paper — the one-pager that started this project
