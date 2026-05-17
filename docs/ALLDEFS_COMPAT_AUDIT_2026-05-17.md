# ALLDEFS.ASCII compatibility audit

Date: 2026-05-17 (refreshed)

- loader module: present (`st72_bootstrap.py`)
- unique `to` defs parsed: 61
- implemented (direct primitive mapping): 14
- partial (non-CODE now loadable via bootstrap path): 33
- missing: 14

Notes:
- Direct primitive mapping comes from `st72_prims.register_all`.
- `partial` means no direct primitive mapping but candidate for non-CODE runtime loading via bootstrap loader.
