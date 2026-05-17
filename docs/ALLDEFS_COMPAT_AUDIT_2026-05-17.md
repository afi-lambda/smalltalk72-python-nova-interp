# ALLDEFS.ASCII compatibility audit

Date: 2026-05-17
Project: /home/alain/smalltalk72-python-nova-interp

## Scope and method
- Parsed `ALLDEFS.ASCII.txt` for `to ... (...)` headers (first occurrence per `to` name).
- Parsed `st72_prims.py` for names registered in `register_all(st)`.
- Applied explicit symbol/name mapping: `@->quot`, `^->apret`, `:->fetch`, `?->match`, `PUT->put`, `GET->get`.
- Classified each ALLDEFS `to` as `implemented`, `partial`, or `missing`.

## Summary
- Total unique `to` definitions parsed: 61
- Implemented: 14
- Partial: 9
- Missing: 38

## Registered primitives detected
Atom, Number, again, apret, done, eq, false, fetch, get, isnew, match, mem, mkins, null, peekr, put, qfet, quot, repeat, rself, to

## CODE-tagged entries
| to name | CODE | status | mapped primitive |
|---|---:|---|---|
| `repeat` | 1 | implemented | `repeat` |
| `read` | 2 | partial | `read` |
| `isnew` | 5 | implemented | `isnew` |
| `again` | 6 | implemented | `again` |
| `@` | 9 | implemented | `quot` |
| `apply` | 10 | missing | `apply` |
| `evapply` | 10 | missing | `evapply` |
| `PUT` | 12 | implemented | `put` |
| `^` | 13 | implemented | `apret` |
| `eq` | 15 | implemented | `eq` |
| `?` | 17 | implemented | `match` |
| `:` | 18 | implemented | `fetch` |
| `TTY` | 20 | missing | `TTY` |
| `kbck` | 20 | missing | `kbck` |
| `kbd` | 20 | missing | `kbd` |
| `done` | 25 | implemented | `done` |
| `mem` | 26 | implemented | `mem` |
| `GET` | 28 | implemented | `get` |
| `atom` | 29 | partial | `atom` |
| `junta` | 31 | missing | `junta` |
| `mouse` | 35 | missing | `mouse` |
| `::` | 36 | missing | `::` |
| `null` | 37 | implemented | `null` |
| `dclear` | 52 | missing | `dclear` |
| `dcomp` | 53 | missing | `dcomp` |
| `dmove` | 54 | missing | `dmove` |
| `dmovec` | 55 | missing | `dmovec` |

## Full audit table
| to name | raw header | CODE | status | mapped | note |
|---|---|---:|---|---|---|
| `#` | `#` |  | missing | `#` | no direct runtime primitive registration found |
| `-` | `- x` |  | missing | `-` | no direct runtime primitive registration found |
| `:` | `:` | 18 | implemented | `fetch` | mapped to primitive 'fetch' |
| `::` | `::` | 36 | missing | `::` | no direct runtime primitive registration found |
| `?` | `?` | 17 | implemented | `match` | mapped to primitive 'match' |
| `@` | `@` | 9 | implemented | `quot` | mapped to primitive 'quot' |
| `^` | `^` | 13 | implemented | `apret` | mapped to primitive 'apret' |
| `addto` | `addto func v w` |  | missing | `addto` | no direct runtime primitive registration found |
| `again` | `again` | 6 | implemented | `again` | mapped to primitive 'again' |
| `apply` | `apply x y` | 10 | missing | `apply` | no direct runtime primitive registration found |
| `arec` | `arec x y` |  | missing | `arec` | no direct runtime primitive registration found |
| `atom` | `atom x y` | 29 | partial | `atom` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `button` | `button n` |  | missing | `button` | no direct runtime primitive registration found |
| `class` | `class x y` |  | partial | `class` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `core` | `core` |  | missing | `core` | no direct runtime primitive registration found |
| `cr` | `cr` |  | missing | `cr` | no direct runtime primitive registration found |
| `dclear` | `dclear` | 52 | missing | `dclear` | no direct runtime primitive registration found |
| `dcomp` | `dcomp` | 53 | missing | `dcomp` | no direct runtime primitive registration found |
| `dmove` | `dmove` | 54 | missing | `dmove` | no direct runtime primitive registration found |
| `dmovec` | `dmovec` | 55 | missing | `dmovec` | no direct runtime primitive registration found |
| `done` | `done x` | 25 | implemented | `done` | mapped to primitive 'done' |
| `dsoff` | `dsoff` |  | missing | `dsoff` | no direct runtime primitive registration found |
| `dson` | `dson` |  | missing | `dson` | no direct runtime primitive registration found |
| `edtarget` | `edtarget` |  | missing | `edtarget` | no direct runtime primitive registration found |
| `eq` | `eq x` | 15 | implemented | `eq` | mapped to primitive 'eq' |
| `ev` | `ev` |  | missing | `ev` | no direct runtime primitive registration found |
| `evapply` | `evapply x y` | 10 | missing | `evapply` | no direct runtime primitive registration found |
| `expand` | `expand x` |  | missing | `expand` | no direct runtime primitive registration found |
| `falseclass` | `falseclass x y` |  | implemented | `false` | mapped to primitive 'false' |
| `filin` | `filin fi :: ev` |  | missing | `filin` | no direct runtime primitive registration found |
| `float` | `float x y :: fprint` |  | partial | `float` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `GET` | `GET x y` | 28 | implemented | `get` | mapped to primitive 'get' |
| `getvec` | `getvec` |  | missing | `getvec` | no direct runtime primitive registration found |
| `if` | `if exp` |  | partial | `if` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `indisp` | `indisp disp` |  | missing | `indisp` | no direct runtime primitive registration found |
| `is` | `is` |  | missing | `is` | no direct runtime primitive registration found |
| `isnew` | `isnew` | 5 | implemented | `isnew` | mapped to primitive 'isnew' |
| `junta` | `junta` | 31 | missing | `junta` | no direct runtime primitive registration found |
| `kbck` | `kbck` | 20 | missing | `kbck` | no direct runtime primitive registration found |
| `kbd` | `kbd` | 20 | missing | `kbd` | no direct runtime primitive registration found |
| `mem` | `mem x y` | 26 | implemented | `mem` | mapped to primitive 'mem' |
| `mouse` | `mouse x` | 35 | missing | `mouse` | no direct runtime primitive registration found |
| `mx` | `mx` |  | missing | `mx` | no direct runtime primitive registration found |
| `my` | `my` |  | missing | `my` | no direct runtime primitive registration found |
| `newchars` | `newchars fil i j new old str` |  | missing | `newchars` | no direct runtime primitive registration found |
| `nil` | `nil x` |  | missing | `nil` | no direct runtime primitive registration found |
| `nprint` | `nprint digit n` |  | missing | `nprint` | no direct runtime primitive registration found |
| `null` | `null x` | 37 | implemented | `null` | mapped to primitive 'null' |
| `number` | `number x y :: nprint` |  | partial | `number` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `print` | `print` |  | partial | `print` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `PUT` | `PUT x y z` | 12 | implemented | `put` | mapped to primitive 'put' |
| `read` | `read` | 2 | partial | `read` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `redo` | `redo` |  | missing | `redo` | no direct runtime primitive registration found |
| `repeat` | `repeat token` | 1 | implemented | `repeat` | mapped to primitive 'repeat' |
| `reread` | `reread n i p reader` |  | missing | `reread` | no direct runtime primitive registration found |
| `show` | `show showpretty` |  | missing | `show` | no direct runtime primitive registration found |
| `string` | `string x y :: substr` |  | partial | `string` | language/runtime concept exists but not directly registered as this ALLDEFS name |
| `sub` | `sub disp` |  | missing | `sub` | no direct runtime primitive registration found |
| `t` | `t nprint substr` |  | missing | `t` | no direct runtime primitive registration found |
| `TTY` | `TTY` | 20 | missing | `TTY` | no direct runtime primitive registration found |
| `vector` | `vector x y :: substr` |  | partial | `vector` | language/runtime concept exists but not directly registered as this ALLDEFS name |

## README limitations relevant to parity
- `String` class not fully implemented (literals interned as atoms)
- Display/graphics primitives not implemented
- `repeat`/`again` uses a Python loop (no proper GOTO restart)
- No file I/O (Alto sector-based storage)

## Verdict
Partial compatibility with ALLDEFS: key core primitives are present, but many ALLDEFS `to` definitions are not directly implemented/registered as runtime primitives.