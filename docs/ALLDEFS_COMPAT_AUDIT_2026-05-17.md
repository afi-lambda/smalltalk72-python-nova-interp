# ALLDEFS.ASCII compatibility audit

Date: 2026-05-17 (restored + recomputed)
Project: /home/alain/smalltalk72-python-nova-interp

## Scope and method
- Parsed `ALLDEFS.ASCII.txt` for `to ... (...)` headers (first occurrence per `to` name).
- Parsed `st72_prims.py` for names registered in `register_all(st)`.
- Applied explicit symbol/name mapping: `@->quot`, `^->apret`, `:->fetch`, `?->match`, `PUT->put`, `GET->get`, `falseclass->false`.
- Classified each ALLDEFS `to` as `implemented`, `partial`, or `missing`.
- `nil` is classified `implemented` via VM core global binding (not a primitive alias).

## Summary
- Total unique `to` definitions parsed: 61
- Implemented: 39
- Partial: 0
- Missing: 22

## Registered primitives detected
#, -, ::, Atom, Number, addto, again, apply, apret, arec, atom, class, core, cr, done, eq, ev, evapply, expand, false, fetch, float, get, getvec, if, is, isnew, match, mem, mkins, nprint, null, number, peekr, print, put, qfet, quot, read, repeat, rself, string, t, to, vector

## CODE-tagged entries
| to name | CODE | status | mapped primitive |
|---|---|---|---|
| `read` | 2 | implemented | `read` |
| `isnew` | 5 | implemented | `isnew` |
| `again` | 6 | implemented | `again` |
| `@` | 9 | implemented | `quot` |
| `^` | 13 | implemented | `apret` |
| `eq` | 15 | implemented | `eq` |
| `?` | 17 | implemented | `match` |
| `:` | 18 | implemented | `fetch` |
| `atom` | 29 | implemented | `atom` |
| `::` | 36 | implemented | `::` |
| `dclear` | 52 | missing | `dclear` |
| `dcomp` | 53 | missing | `dcomp` |
| `dmove` | 54 | missing | `dmove` |
| `dmovec` | 55 | missing | `dmovec` |

## Full audit table
| to name | raw header | CODE | status | mapped | note |
|---|---|---|---|---|---|
| `#` | `#` |  | implemented | `#` | mapped to primitive '#' |
| `-` | `- x` |  | implemented | `-` | mapped to primitive '-' |
| `:` | `:` | 18 | implemented | `fetch` | mapped to primitive 'fetch' |
| `::` | `::` | 36 | implemented | `::` | mapped to primitive '::' |
| `?` | `?` | 17 | implemented | `match` | mapped to primitive 'match' |
| `@` | `@` | 9 | implemented | `quot` | mapped to primitive 'quot' |
| `^` | `^` | 13 | implemented | `apret` | mapped to primitive 'apret' |
| `addto` | `addto func v w` |  | implemented | `addto` | mapped to primitive 'addto' |
| `again` | `again` | 6 | implemented | `again` | mapped to primitive 'again' |
| `apply` | `apply x y` |  | implemented | `apply` | mapped to primitive 'apply' |
| `arec` | `arec x y` |  | implemented | `arec` | mapped to primitive 'arec' (minimal local lookup/bind) |
| `atom` | `atom x y` | 29 | implemented | `atom` | mapped to primitive 'atom' |
| `button` | `button n` |  | missing | `button` | no direct runtime primitive registration found |
| `class` | `class x y` |  | implemented | `class` | mapped to primitive 'class' |
| `core` | `core` |  | implemented | `core` | mapped to primitive 'core' |
| `cr` | `cr` |  | implemented | `cr` | mapped to primitive 'cr' |
| `dclear` | `dclear` | 52 | missing | `dclear` | no direct runtime primitive registration found |
| `dcomp` | `dcomp` | 53 | missing | `dcomp` | no direct runtime primitive registration found |
| `dmove` | `dmove` | 54 | missing | `dmove` | no direct runtime primitive registration found |
| `dmovec` | `dmovec` | 55 | missing | `dmovec` | no direct runtime primitive registration found |
| `done` | `done x` |  | implemented | `done` | mapped to primitive 'done' |
| `dsoff` | `dsoff` |  | missing | `dsoff` | no direct runtime primitive registration found |
| `dson` | `dson` |  | missing | `dson` | no direct runtime primitive registration found |
| `edtarget` | `edtarget` |  | missing | `edtarget` | no direct runtime primitive registration found |
| `eq` | `eq x` | 15 | implemented | `eq` | mapped to primitive 'eq' |
| `ev` | `ev` |  | implemented | `ev` | mapped to primitive 'ev' |
| `evapply` | `evapply x y` |  | implemented | `evapply` | mapped to primitive 'evapply' |
| `expand` | `expand x` |  | implemented | `expand` | mapped to primitive 'expand' |
| `falseclass` | `falseclass x y` |  | implemented | `false` | mapped to primitive 'false' |
| `filin` | `filin fi :: ev` |  | missing | `filin` | no direct runtime primitive registration found |
| `float` | `float x y :: fprint` |  | implemented | `float` | mapped to primitive 'float' |
| `GET` | `GET x y` |  | implemented | `get` | mapped to primitive 'get' |
| `getvec` | `getvec` |  | implemented | `getvec` | mapped to primitive 'getvec' |
| `if` | `if exp` |  | implemented | `if` | mapped to primitive 'if' |
| `indisp` | `indisp disp` |  | missing | `indisp` | no direct runtime primitive registration found |
| `is` | `is` |  | implemented | `is` | mapped to primitive 'is' |
| `isnew` | `isnew` | 5 | implemented | `isnew` | mapped to primitive 'isnew' |
| `junta` | `junta` |  | missing | `junta` | no direct runtime primitive registration found |
| `kbck` | `kbck` |  | missing | `kbck` | no direct runtime primitive registration found |
| `kbd` | `kbd` |  | missing | `kbd` | no direct runtime primitive registration found |
| `mem` | `mem x y` |  | implemented | `mem` | mapped to primitive 'mem' |
| `mouse` | `mouse x` |  | missing | `mouse` | no direct runtime primitive registration found |
| `mx` | `mx` |  | missing | `mx` | no direct runtime primitive registration found |
| `my` | `my` |  | missing | `my` | no direct runtime primitive registration found |
| `newchars` | `newchars fil i j new old str` |  | missing | `newchars` | no direct runtime primitive registration found |
| `nil` | `nil x` |  | implemented | `nil` | core global 'nil' is pre-bound in VM init (identity-distinct from false) |
| `nprint` | `nprint digit n` |  | implemented | `nprint` | mapped to primitive 'nprint' |
| `null` | `null x` |  | implemented | `null` | mapped to primitive 'null' |
| `number` | `number x y :: nprint` |  | implemented | `number` | mapped to primitive 'number' |
| `print` | `print` |  | implemented | `print` | mapped to primitive 'print' |
| `PUT` | `PUT x y z` |  | implemented | `put` | mapped to primitive 'put' |
| `read` | `read` | 2 | implemented | `read` | mapped to primitive 'read' |
| `redo` | `redo` |  | missing | `redo` | no direct runtime primitive registration found |
| `repeat` | `repeat token` |  | implemented | `repeat` | mapped to primitive 'repeat' |
| `reread` | `reread n i p reader` |  | missing | `reread` | no direct runtime primitive registration found |
| `show` | `show showpretty` |  | missing | `show` | no direct runtime primitive registration found |
| `string` | `string x y :: substr` |  | implemented | `string` | mapped to primitive 'string' |
| `sub` | `sub disp` |  | missing | `sub` | no direct runtime primitive registration found |
| `t` | `t tabin index` |  | implemented | `t` | mapped to primitive 't' |
| `TTY` | `TTY` |  | missing | `TTY` | no direct runtime primitive registration found |
| `vector` | `vector x y :: substr` |  | implemented | `vector` | mapped to primitive 'vector' |

## Missing 22 (canonical list)
`TTY`, `button`, `dclear`, `dcomp`, `dmove`, `dmovec`, `dsoff`, `dson`, `edtarget`, `filin`, `indisp`, `junta`, `kbck`, `kbd`, `mouse`, `mx`, `my`, `newchars`, `redo`, `reread`, `show`, `sub`

## README limitations relevant to parity
- `String` class not fully implemented (literals interned as atoms)
- Display/graphics primitives not implemented
- `repeat`/`again` uses a Python loop (no proper GOTO restart)
- No file I/O (Alto sector-based storage)

## Verdict
Partial compatibility with ALLDEFS: key core primitives are present; additional non-CODE definitions can now be live-loaded via optional bootstrap, while display/graphics and device/file entries remain out of scope.
