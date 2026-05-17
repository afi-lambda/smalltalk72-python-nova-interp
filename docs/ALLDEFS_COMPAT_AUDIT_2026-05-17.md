# ALLDEFS.ASCII compatibility audit

Date: 2026-05-17 (restored + recomputed)
Project: /home/alain/smalltalk72-python-nova-interp

## Scope and method
- Parsed `ALLDEFS.ASCII.txt` for `to ... (...)` headers (first occurrence per `to` name).
- Parsed `st72_prims.py` for names registered in `register_all(st)`.
- Applied explicit symbol/name mapping: `@->quot`, `^->apret`, `:->fetch`, `?->match`, `PUT->put`, `GET->get`, `falseclass->false`.
- Classified each ALLDEFS `to` as `implemented`, `partial`, or `missing`.
- `partial` includes entries loadable through non-CODE bootstrap path (where applicable).

## Summary
- Total unique `to` definitions parsed: 61
- Implemented: 14
- Partial: 24
- Missing: 23

## Registered primitives detected
Atom, Number, again, apret, done, eq, false, fetch, get, isnew, match, mem, mkins, null, peekr, put, qfet, quot, repeat, rself, to

## CODE-tagged entries
| to name | CODE | status | mapped primitive |
|---|---|---|---|
| `read` | 2 | partial | `read` |
| `isnew` | 5 | implemented | `isnew` |
| `again` | 6 | implemented | `again` |
| `@` | 9 | implemented | `quot` |
| `^` | 13 | implemented | `apret` |
| `eq` | 15 | implemented | `eq` |
| `?` | 17 | implemented | `match` |
| `:` | 18 | implemented | `fetch` |
| `atom` | 29 | partial | `atom` |
| `::` | 36 | missing | `::` |
| `dclear` | 52 | missing | `dclear` |
| `dcomp` | 53 | missing | `dcomp` |
| `dmove` | 54 | missing | `dmove` |
| `dmovec` | 55 | missing | `dmovec` |

## Full audit table
| to name | raw header | CODE | status | mapped | note |
|---|---|---|---|---|---|
| `#` | `#` |  | partial | `#` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `-` | `- x` |  | partial | `-` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `:` | `:` | 18 | implemented | `fetch` | mapped to primitive 'fetch' |
| `::` | `::` | 36 | missing | `::` | no direct runtime primitive registration found |
| `?` | `?` | 17 | implemented | `match` | mapped to primitive 'match' |
| `@` | `@` | 9 | implemented | `quot` | mapped to primitive 'quot' |
| `^` | `^` | 13 | implemented | `apret` | mapped to primitive 'apret' |
| `addto` | `addto func v w` |  | partial | `addto` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `again` | `again` | 6 | implemented | `again` | mapped to primitive 'again' |
| `apply` | `apply x y` |  | partial | `apply` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `arec` | `arec x y` |  | partial | `arec` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `atom` | `atom x y` | 29 | partial | `atom` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `button` | `button n` |  | missing | `button` | no direct runtime primitive registration found |
| `class` | `class x y` |  | partial | `class` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `core` | `core` |  | partial | `core` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `cr` | `cr` |  | partial | `cr` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `dclear` | `dclear` | 52 | missing | `dclear` | no direct runtime primitive registration found |
| `dcomp` | `dcomp` | 53 | missing | `dcomp` | no direct runtime primitive registration found |
| `dmove` | `dmove` | 54 | missing | `dmove` | no direct runtime primitive registration found |
| `dmovec` | `dmovec` | 55 | missing | `dmovec` | no direct runtime primitive registration found |
| `done` | `done x` |  | implemented | `done` | mapped to primitive 'done' |
| `dsoff` | `dsoff` |  | missing | `dsoff` | no direct runtime primitive registration found |
| `dson` | `dson` |  | missing | `dson` | no direct runtime primitive registration found |
| `edtarget` | `edtarget` |  | missing | `edtarget` | no direct runtime primitive registration found |
| `eq` | `eq x` | 15 | implemented | `eq` | mapped to primitive 'eq' |
| `ev` | `ev` |  | partial | `ev` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `evapply` | `evapply x y` |  | partial | `evapply` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `expand` | `expand x` |  | partial | `expand` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `falseclass` | `falseclass x y` |  | implemented | `false` | mapped to primitive 'false' |
| `filin` | `filin fi :: ev` |  | missing | `filin` | no direct runtime primitive registration found |
| `float` | `float x y :: fprint` |  | partial | `float` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `GET` | `GET x y` |  | implemented | `get` | mapped to primitive 'get' |
| `getvec` | `getvec` |  | partial | `getvec` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `if` | `if exp` |  | partial | `if` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `indisp` | `indisp disp` |  | missing | `indisp` | no direct runtime primitive registration found |
| `is` | `is` |  | partial | `is` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `isnew` | `isnew` | 5 | implemented | `isnew` | mapped to primitive 'isnew' |
| `junta` | `junta` |  | missing | `junta` | no direct runtime primitive registration found |
| `kbck` | `kbck` |  | missing | `kbck` | no direct runtime primitive registration found |
| `kbd` | `kbd` |  | missing | `kbd` | no direct runtime primitive registration found |
| `mem` | `mem x y` |  | implemented | `mem` | mapped to primitive 'mem' |
| `mouse` | `mouse x` |  | missing | `mouse` | no direct runtime primitive registration found |
| `mx` | `mx` |  | missing | `mx` | no direct runtime primitive registration found |
| `my` | `my` |  | missing | `my` | no direct runtime primitive registration found |
| `newchars` | `newchars fil i j new old str` |  | missing | `newchars` | no direct runtime primitive registration found |
| `nil` | `nil x` |  | partial | `nil` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `nprint` | `nprint digit n` |  | partial | `nprint` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `null` | `null x` |  | implemented | `null` | mapped to primitive 'null' |
| `number` | `number x y :: nprint` |  | partial | `number` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `print` | `print` |  | partial | `print` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `PUT` | `PUT x y z` |  | implemented | `put` | mapped to primitive 'put' |
| `read` | `read` | 2 | partial | `read` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `redo` | `redo` |  | missing | `redo` | no direct runtime primitive registration found |
| `repeat` | `repeat token` |  | implemented | `repeat` | mapped to primitive 'repeat' |
| `reread` | `reread n i p reader` |  | missing | `reread` | no direct runtime primitive registration found |
| `show` | `show showpretty` |  | missing | `show` | no direct runtime primitive registration found |
| `string` | `string x y :: substr` |  | partial | `string` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `sub` | `sub disp` |  | missing | `sub` | no direct runtime primitive registration found |
| `t` | `t tabin index` |  | partial | `t` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |
| `TTY` | `TTY` |  | missing | `TTY` | no direct runtime primitive registration found |
| `vector` | `vector x y :: substr` |  | partial | `vector` | no direct primitive mapping; candidate for non-CODE runtime loading via bootstrap loader |

## README limitations relevant to parity
- `String` class not fully implemented (literals interned as atoms)
- Display/graphics primitives not implemented
- `repeat`/`again` uses a Python loop (no proper GOTO restart)
- No file I/O (Alto sector-based storage)

## Verdict
Partial compatibility with ALLDEFS: key core primitives are present; additional non-CODE definitions can now be live-loaded via optional bootstrap, but many system/display/file entries remain unavailable.
