"""
st72_prims.py — Primitive class implementations for Smalltalk-72.
Faithful translation of CODE.SR (Nova assembly source).

Each primitive is a Python callable registered via st.def_builtin_class().
The callable receives the ST72 machine (st) and must:
  - read its instance from st._inst
  - read arguments via st._fech() / st._ampc() etc.
  - set the result via st._sval() / st._svli()
  - trigger return via st._eret() or st._aret()

Primitives implemented (from CODE.SR exports in SMALL.SYMS):
  Number class:   +  -  *  /  mod  =  #  <  <=  >  >=  &+  &*  &-  &/
  Atom class:     _  chars  eval  =
  to              define a new template/class
  eq              pointer equality
  null            nil test
  isnew           instance allocate-if-nil
  mkins           make instance
  fetch (fet)     nested fetch from GLOB
  match (mat)     peek-match in GLOB message
  put             store into table
  get             load from table
  quot            quote next token, apply
  repeat / again / done   control flow
  apret           apply-return up to enclosing scope
  mem             raw memory read/write
  rself           return self (instance)
  qfet / peekr    quoted fetch / peek-return
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from st72 import ST72

# Operator index table (mirrors TAB1 in CODE.SR, 0-based)
# Order must match exactly: & + * - / = # < <= >= > mod &/ &+ &* &-
from st72 import (NIL, EMPTY, MASTER, NCLAS, LSCLA, ATCLS, SCLAS,
                  MXATM, RCMSK, SINTB, MXNUM, SINT1,
                  AR_INST, AR_GLOB, AR_MESS, AR_PC, AR_LOCAL, AR_MODE,
                  MODE_EVAL, MODE_APPLY)

# ---------------------------------------------------------------------------
# Helpers shared across primitives
# ---------------------------------------------------------------------------

def _ival(st: 'ST72', addr: int) -> int:
    """IVAL: extract integer value from any numeric object."""
    return st.obj_int_value(addr)

def _intnr(st: 'ST72', result: int):
    """INTNR: intern result, store in VALUE, ERET."""
    st._sval(st.intern_int(result))
    st._eret()

def _rself(st: 'ST72'):
    """RSELFC: return INST as VALUE, ERET."""
    inst = st._inst
    st._sval(inst)
    st._eret()

def _rfalse(st: 'ST72'):
    """
    RFALSE in CODE.SR (lines 266-274):
      PEEK for '?':
        found → AMPC (skip ?-clause token), SVAL(EMPTY), ERET (passive)
        not found → SVAL(EMPTY), ARET (active — lets 'or' / empty ops run)
    
    PEEK reads SELF.MESS[PC] — which in a primitive activation is the
    caller's message vector (set in _activ fix).
    """
    if st._peek(st.A_QUEST):
        # Found '?': consume the clause token (skip branch), return passively
        st._ampc()
        st._sval(EMPTY)
        st._eret()
    else:
        st._sval(EMPTY)
        st._aret()


# ---------------------------------------------------------------------------
# NUM1C — Number class
# ---------------------------------------------------------------------------
#
# Operator table (TAB1) in CODE.SR, 1-based dispatch:
#   index 0  → & (bitwise ops prefix — handled separately)
#   index 1  → +
#   index 2  → *
#   index 3  → -
#   index 4  → /
#   index 5  → =    (CMA start)
#   index 6  → #  (≠)
#   index 7  → <
#   index 8  → <=
#   index 9  → >=
#   index 10 → >    (CMB end)
#   index 11 → mod
# Second-level (&-ops, offset by 12):
#   index 12 → &/  (shift)
#   index 13 → &+  (or)
#   index 14 → &*  (and)
#   index 15 → &-  (xor)
#
# Comparison operators (CMA..CMB = indices 5..10) return false if
# VALUE==EMPTY (chained comparisons like 4<x<7).

# Operator hash → (index, second-level?)  matching TAB1 order
_NUM_OPS: dict[str, int] = {
    "&":  0,   # bitwise prefix
    "+":  1,
    "*":  2,
    "-":  3,
    "/":  4,
    "=":  5,
    "#":  6,
    "<":  7,
    "<=": 8,
    ">=": 9,
    ">":  10,
    "mod":11,
}
_NUM_BIT_OPS: dict[str, int] = {
    "&/": 12,
    "&+": 13,
    "&*": 14,
    "&-": 15,
}
_CMA = 5   # first comparison op index
_CMB = 10  # last  comparison op index

def _num_dispatch(st: 'ST72', self_val: int, arg_val: int, opix: int):
    """Arithmetic/comparison dispatch (mirrors dispatch table in CODE.SR)."""
    if opix == 1:  result = self_val + arg_val;              _intnr(st, result); return
    if opix == 2:  result = self_val * arg_val;              _intnr(st, result); return
    if opix == 3:  result = self_val - arg_val;              _intnr(st, result); return
    if opix == 4:                                            # division
        if arg_val == 0:
            raise ZeroDivisionError("division by zero")
        result = int(self_val / arg_val)  # truncate toward zero
        _intnr(st, result); return
    if opix == 5:  # =
        if self_val == arg_val: _rself(st)
        else:                   _rfalse(st)
        return
    if opix == 6:  # # (≠)
        if self_val != arg_val: _rself(st)
        else:                   _rfalse(st)
        return
    if opix == 7:  # <
        if self_val < arg_val:  _rself(st)
        else:                   _rfalse(st)
        return
    if opix == 8:  # <=
        if self_val <= arg_val: _rself(st)
        else:                   _rfalse(st)
        return
    if opix == 9:  # >=
        if self_val >= arg_val: _rself(st)
        else:                   _rfalse(st)
        return
    if opix == 10: # >
        if self_val > arg_val:  _rself(st)
        else:                   _rfalse(st)
        return
    if opix == 11: # mod
        if arg_val == 0:
            raise ZeroDivisionError("mod by zero")
        result = self_val % arg_val
        _intnr(st, result); return
    # Bitwise ops (second level, offsets 12-15)
    if opix == 12: # &/ shift: arg>0 → left, arg<0 → right
        if arg_val >= 0: result = (self_val << arg_val) & 0xFFFF
        else:            result = (self_val >> (-arg_val)) & 0xFFFF
        _intnr(st, result); return
    if opix == 13: result = self_val | arg_val;  _intnr(st, result); return  # &+ or
    if opix == 14: result = self_val & arg_val;  _intnr(st, result); return  # &* and
    if opix == 15: result = self_val ^ arg_val;  _intnr(st, result); return  # &- xor
    raise RuntimeError(f"Unknown number opix: {opix}")

def prim_number(st: 'ST72'):
    """
    NUM1C: Number class handler.
    Mirrors NUM1C in CODE.SR exactly:
      - INST == NIL → back to eval (no-op)
      - peek '.' → RSELF
      - INDX in TAB1 → dispatch
      - not found → back to eval (Smalltalk fallback)
    """
    inst = st._inst
    if inst == NIL:
        # INST==NIL: CODE.SR does JMP @.EVAL. Just return to let loop continue.
        return

    # Peek for '.' — return self
    if st._peek(st.A_PER):
        _rself(st)
        return

    # Read next token as operator
    op_tok = st._apc()
    op_name = st.atoms.name_of(op_tok) if st.is_atom(op_tok) else None

    # Check for '&' prefix (bitwise ops) or composite '&op' token
    second_level = False
    if op_name in _NUM_BIT_OPS:
        # composite token like '&*', '&+', '&-', '&/'
        opix = _NUM_BIT_OPS[op_name]
        second_level = True
    elif op_name == "&":
        # two-token form: '&' followed by op
        if st._peek(st.A_PER):
            raise RuntimeError("Number & needs second operator")
        op2_tok  = st._apc()
        op2_name = st.atoms.name_of(op2_tok) if st.is_atom(op2_tok) else None
        full_op  = "&" + (op2_name or "")
        opix     = _NUM_BIT_OPS.get(full_op)
        if opix is None:
            st._eret(); return
        second_level = True
    else:
        opix = _NUM_OPS.get(op_name) if op_name else None
        if opix is None:
            # Unknown operator: CODE.SR does JMP @.EVAL (not ERET).
            # Just return; the eval loop continues reading from our MESS.
            return

    # Chained comparison shortcut: if VALUE == EMPTY and op is a comparison,
    # return false immediately (mirrors CKCMP in CODE.SR)
    if _CMA <= opix <= _CMB:
        if st.VALUE == EMPTY:
            _rfalse(st); return

    # Fetch operand via FECH (evaluates next expression)
    st._fetch_inner()   # → sets st.VALUE to the operand
    arg_addr = st.VALUE

    # IVAL: extract integer values
    try:
        self_val = _ival(st, inst)
        arg_val  = _ival(st, arg_addr)
    except TypeError:
        # EQT: non-numeric comparee
        if opix == 5:   # =
            _rfalse(st); return
        if opix == 6:   # #
            _rself(st); return
        raise

    _num_dispatch(st, self_val, arg_val, opix)


# ---------------------------------------------------------------------------
# ATOM1C — Atom class
# ---------------------------------------------------------------------------

def prim_atom(st: 'ST72'):
    """
    ATOM1C: Atom class handler.
    Operations (mirrors ATOM1C in CODE.SR):
      INST==NIL (isnew) → fetch string, make atom (MKATOM)
      '_'  → fetch value, bind atom in GLOB
      'chars' → return print-name (atom address itself is name)
      'eval'  → look up binding of INST in GLOB
      '='     → fetch expr, compare pointer equality
      else    → RSELF (return self)
    """
    inst = st._inst

    if inst == NIL:
        # NEWAT: fetch the string arg, intern as atom
        st._fetch_inner()
        name = st.value_repr(st.VALUE)   # best effort string form
        new_atom = st.atoms.intern(name)
        st._svli(new_atom)
        st._aret()
        return

    # Peek for '_' (assignment arrow)
    if st._peek(st.A_ARROW):
        # ATM2: fetch value, bind atom (INST) in GLOB
        st._fetch_inner()
        val = st.VALUE
        # PUT GLOB[INST] = val
        glob = st._glob
        st._put(inst, val, glob)
        st._eret()
        return

    # Peek for 'chars'
    chars_atom = st.atoms.intern("chars")
    if st._peek(chars_atom):
        # ATM3: return print-name of atom
        # In real ST72 the print-name is stored as a string object;
        # here we return the atom itself (its name is accessible via atoms.name_of)
        name = st.atoms.name_of(inst) or ""
        # Intern the name as a string atom
        name_atom = st.atoms.intern(name)
        st._sval(name_atom)
        st._aret()
        return

    # Peek for 'eval'
    eval_atom = st.atoms.intern("eval")
    if st._peek(eval_atom):
        # ATM4: look up binding of INST in GLOB
        st._apc()   # consume 'eval' (already peeked)... actually peek consumed it
        glob = st._glob
        val  = st._find(inst, glob)
        st._sval(val if val is not None else NIL)
        st._aret()
        return

    # Peek for '='
    eq_atom = st.atoms.intern("=")
    if st._peek(eq_atom):
        # ATM5: fetch expr, compare pointer equality
        st._fetch_inner()
        other = st.VALUE
        if inst == other:
            _rself(st)
        else:
            _rfalse(st)
        return

    # RS1: peek for '.', if end-of-message → return self, else EVAL
    if st._void():
        _rself(st)
    else:
        # return self and continue
        _rself(st)


# ---------------------------------------------------------------------------
# TO1C — define a new template
# ---------------------------------------------------------------------------

def prim_to(st: 'ST72'):
    """
    TO1C: 'to' — define a new class/template.
    Syntax:  to Name (:local1 :local2 ... | :inst1 ...) code...

    Mirrors TO1C in CODE.SR:
      1. AMPC → name atom
      2. Count atomic args (locals, instance vars, class vars) separated by ':'
      3. Allocate hash table of size 2^(ceil_log2(N+3)) + 4 words
      4. Install MASTER, mask, arg-count, DO-field
      5. Install each declared atom into the table
      6. Bind the name to the table in SELF's scope
      7. Return the name atom, apply

    Simplified: we build a Python dict-based class object rather than
    a vmem hash table, then register it via defclass machinery.
    """
    # Read name
    name_tok = st._apc()
    name_str  = st.atoms.name_of(name_tok) or f"anon_{oct(name_tok)}"

    # Read argument declarations until we hit a non-atom (the DO body start)
    # Declarations are grouped by ':' separators:
    #   local vars | instance vars | class vars
    # We collect them in order.
    groups: list[list[int]] = [[]]   # groups[0] = locals, [1] = inst, [2] = class
    group_idx = 0

    while True:
        tok = st._peek_raw()
        if tok == NIL or tok == st.A_PER:
            break
        if not st.is_atom(tok):
            break   # non-atom → start of DO code
        st._apc()   # consume

        if tok == st.A_COLN:
            group_idx = min(group_idx + 1, 2)
            groups.append([])
        else:
            while len(groups) <= group_idx:
                groups.append([])
            groups[group_idx].append(tok)

    # Remaining tokens (up to next '.') form the DO code vector
    do_tokens = []
    while True:
        tok = st._peek_raw()
        if tok == NIL or tok == st.A_PER:
            st._apc()   # consume '.'
            break
        do_tokens.append(st._apc())

    # Build class object
    locals_decl = groups[0] if len(groups) > 0 else []
    inst_decl   = groups[1] if len(groups) > 1 else []

    cls_addr = st.defclass(name_str, do_tokens)

    # Store declaration metadata on the class (for CACT sizing)
    if cls_addr not in st._bindings:
        st._bindings[cls_addr] = {}
    # Record local and instance var names as offsets
    for i, var_tok in enumerate(locals_decl):
        offset = AR_LOCAL + i
        st._bindings[cls_addr][var_tok] = offset

    # Bind name in current scope
    st._put(name_tok, cls_addr, st.SELF)
    st._globals[name_tok] = cls_addr

    # Return name atom, active return
    st._sval(name_tok)
    st._aret()


# ---------------------------------------------------------------------------
# EQ1C — pointer equality
# ---------------------------------------------------------------------------

def prim_eq(st: 'ST72'):
    """
    EQ1C: pointer equality test.
    Fetches two args, compares addresses.
    If equal → ERET (return self).
    If not   → FALS (return false).
    """
    st._fetch_inner()
    a = st.VALUE
    st._fetch_inner()
    b = st.VALUE
    if a == b:
        st._eret()   # RSELF path (caller has VALUE=self set already)
    else:
        _rfalse(st)


# ---------------------------------------------------------------------------
# NULLC — nil test
# ---------------------------------------------------------------------------

def prim_null(st: 'ST72'):
    """
    NULLC: "tests if local variable undefined" (CODE.SR comment).
    CODE.SR: LDAF ARG0; SNL 0,0 → skip if negative; JMP @.FALS; JMP @.ERET
    SNL skips if AC0 < 0 (has bit15). NIL=0 → SNL doesn't skip → FALS.
    Non-nil → SNL skips → ERET (return self = truthy).
    
    Semantics: null returns FALSE if arg is NIL (undefined),
               ERET (truthy, the value itself) if arg is non-NIL.
    ARG0 = the calling context's INST = the object being tested.
    """
    inst = st._inst
    if inst == NIL:
        _rfalse(st)   # NIL → false (it IS undefined)
    else:
        st._sval(inst)
        st._eret()    # non-NIL → ERET (truthy)


# ---------------------------------------------------------------------------
# ISNEWC — allocate instance if nil
# ---------------------------------------------------------------------------

def prim_isnew(st: 'ST72'):
    """
    ISNEWC: check if GLOB.INST is nil; if so, allocate a new instance.
    Mirrors ISNEWC in CODE.SR.
    """
    glob = st._glob
    glob_inst = st.mem.ld(glob + AR_INST) if glob else NIL

    if glob_inst != NIL:
        # not nil → return false
        _rfalse(st)
        return

    # Get class definition from GLOB
    cls_addr = st.mem.ld(glob) & RCMSK if glob else NIL

    # Allocate instance (simplified: 2-word object [cls, NIL])
    inst_addr = st._alloc(2)
    st.mem.st(inst_addr,   cls_addr)
    st.mem.st(inst_addr+1, NIL)

    # Install in GLOB.INST
    if glob:
        st.mem.st(glob + AR_INST, inst_addr)

    st._eret()


# ---------------------------------------------------------------------------
# MKINSC — make instance
# ---------------------------------------------------------------------------

def prim_mkins(st: 'ST72'):
    """
    MKINSC: allocate a new instance of a given class with given size.
    Args (from GLOB.ARG0): size (int), class (addr).
    Returns pointer to new object.
    Mirrors MKINSC in CODE.SR.
    """
    # Fetch size and class from message
    st._fetch_inner()
    size_addr = st.VALUE
    size = st.obj_int_value(size_addr) if st.is_sint(size_addr) or st.class_of(size_addr) == NCLAS else 1

    st._fetch_inner()
    cls = st.VALUE

    # Allocate: [CLASS, NIL × size]
    addr = st._alloc(1 + size)
    st.mem.st(addr, cls)
    for i in range(1, 1 + size):
        st.mem.st(addr + i, NIL)

    st._sval(addr)
    st._aret()


# ---------------------------------------------------------------------------
# FET1C — nested fetch from GLOB
# ---------------------------------------------------------------------------

def prim_fetch(st: 'ST72'):
    """
    FET1C: fetch a token from GLOB's message, evaluate it, optionally bind.
    Mirrors FET1C in CODE.SR.

    Syntax (in the GLOB's message stream):
      fetch "name      → literal (quoted) fetch
      fetch #name      → no-eval fetch (look up atoms only)
      fetch expr name  → eval expr, bind result to name in GLOB

    This is the mechanism by which class methods can read and bind their
    message arguments.
    """
    # Temporarily switch SELF to GLOB
    glob = st._glob
    old_self = st.SELF

    # AMPC from GLOB's message
    glob_mess = st.mem.ld(glob + AR_MESS) if glob else NIL
    glob_pc   = st.mem.ld(glob + AR_PC)   if glob else 0
    tok = st.vec_get(glob_mess, glob_pc)
    if glob:
        st.mem.st(glob + AR_PC, glob_pc + 1)

    st.TOKEN = tok

    # Check for quote
    if st._peek(st.A_QUOTE):
        # :" literal fetch
        st._sval(tok)
    elif st.is_atom(tok) and tok > MXATM:
        # :'# no-eval for non-atoms
        st._sval(tok)
    else:
        # Full eval: TOKEN already set, MESSX/GLOBX from GLOB
        st.MESSX     = glob if glob else old_self
        st._messx_pc = glob_pc + 1
        st.GLOBX     = glob if glob else old_self
        st._efind()

    # Now check next token in GLOB's message as binding name
    glob_pc2 = st.mem.ld(glob + AR_PC) if glob else 0
    name_tok = st.vec_get(glob_mess, glob_pc2)
    if glob:
        st.mem.st(glob + AR_PC, glob_pc2 + 1)

    if name_tok == NIL or name_tok == st.A_PER:
        st._eret()
        return

    # PUT: bind name_tok → VALUE in GLOB
    st._put(name_tok, st.VALUE, glob if glob else old_self)
    st._aret()


# ---------------------------------------------------------------------------
# MAT1C — match in GLOB's message
# ---------------------------------------------------------------------------

def prim_match(st: 'ST72'):
    """
    MAT1C: pick up token, peek at GLOB's message for a match.
    Mirrors MAT1C in CODE.SR.
    If matches → ERET (return self/true).
    If not     → FALS.
    """
    tok = st._apc()   # pick up match token

    glob = st._glob
    if not glob:
        _rfalse(st)
        return

    glob_mess = st.mem.ld(glob + AR_MESS)
    glob_pc   = st.mem.ld(glob + AR_PC)
    next_tok  = st.vec_get(glob_mess, glob_pc)

    if next_tok == tok:
        st.mem.st(glob + AR_PC, glob_pc + 1)   # consume
        st._eret()
    else:
        _rfalse(st)


# ---------------------------------------------------------------------------
# PUT1C — store into table
# ---------------------------------------------------------------------------

def prim_put(st: 'ST72'):
    """
    PUT1C: put name→value into table.
    Args: table (INST/ARG0), name (arg1), value (arg2).
    Mirrors PUT1C in CODE.SR.
    """
    # GET name (first arg)
    st._fetch_inner()
    name = st.VALUE

    # GET value (second arg)
    st._fetch_inner()
    val = st.VALUE

    # Table = INST
    table = st._inst
    if table == NIL:
        table = st._glob

    st._put(name, val, table)
    st._eret()


# ---------------------------------------------------------------------------
# GET1C — load from table
# ---------------------------------------------------------------------------

def prim_get(st: 'ST72'):
    """
    GET1C: get value of name from table.
    INST must be a table (class = MASTER).
    Mirrors GET1C in CODE.SR.
    """
    table = st._inst
    if st.class_of(table) != MASTER:
        st._sval(NIL)
        st._eret()
        return

    # Fetch name
    st._fetch_inner()
    name = st.VALUE

    val = st._find(name, table) if st.is_atom(name) else None
    st._sval(val if val is not None else NIL)
    st._aret()


# ---------------------------------------------------------------------------
# QUOT1C — quote next token, apply
# ---------------------------------------------------------------------------

def prim_quot(st: 'ST72'):
    """
    QUOT1C: pick up next token from message, set VALUE, active return.
    Mirrors QUOT1C in CODE.SR.
    """
    tok = st._apc()
    st._sval(tok)
    st._aret()


# ---------------------------------------------------------------------------
# EMPT1C — false/empty class
# ---------------------------------------------------------------------------

def prim_empty(st: 'ST72'):
    """
    EMPT1C: false object operations.
    Mirrors EMPT1C in CODE.SR:
      void message → RSELF
      '?' → skip clause, return self
      'or'  → eval next, return that value
      'and' → return false (short-circuit)
      '>'   → false > x is false
      '='   → false = x is false (unless x is false)
      '<'   → false < x is false
      else  → back to eval
    """
    inst = st._inst
    # Ensure INST is EMPTY
    if inst == NIL:
        st._staf(AR_INST, EMPTY)
        inst = EMPTY

    # Void message → RSELF
    if st._void():
        _rself(st)
        return

    # Peek and dispatch
    peek = st._peek_raw()
    peek_name = st.atoms.name_of(peek) if st.is_atom(peek) else None

    if peek == st.A_QUEST:
        # '?' → skip the branch clause entirely, return self
        st._apc()   # consume '?'
        st._apc()   # consume the clause token
        _rself(st)
        return

    or_atom  = st.atoms.intern("or")
    and_atom = st.atoms.intern("and")
    gt_atom  = st.atoms.intern(">")
    eq_atom  = st.atoms.intern("=")
    lt_atom  = st.atoms.intern("<")

    if peek == or_atom:
        # 'or' → eval next, return its value (false or x = x)
        st._apc()
        st._fetch_inner()
        st._aret()
        return

    if peek == and_atom:
        # 'and' → return false (false and x = false)
        st._apc()
        st._fetch_inner()   # consume but discard
        _rself(st)
        return

    if peek in (gt_atom, eq_atom, lt_atom):
        # comparisons with false → false
        st._apc()
        st._fetch_inner()
        _rfalse(st)
        return

    # Unknown → back to eval
    st._eret()


# ---------------------------------------------------------------------------
# RPT1C / AGAINC / DONE1C — repeat / again / done
# ---------------------------------------------------------------------------

def prim_repeat(st: 'ST72'):
    """
    RPT1C: repeat — evaluate ARG0 (first local) indefinitely.
    In CODE.SR: LDAF ARG0; EVTK → loop back to RPT1C.
    We implement this as a Python loop to avoid recursion depth.
    """
    MAX_ITER = 100_000
    for _ in range(MAX_ITER):
        # Evaluate the body token (ARG0)
        body_tok = st.mem.ld(st.SELF + AR_LOCAL) if st.SELF else NIL
        if body_tok == NIL:
            break
        # Run one eval step on body_tok
        st.TOKEN  = body_tok
        st.MESSX  = st.SELF
        st._messx_pc = 0
        st.GLOBX  = st.SELF
        st._efind()
        # Check for 'again' / 'done' signals via st._running
        if not st._running:
            break
    st._eret()


def prim_again(st: 'ST72'):
    """
    AGAINC: break out of repeat and go back to its start.
    Sets a flag; prim_repeat checks it.
    """
    # Signal repeat to restart (pop up to enclosing repeat)
    # In our simplified model: just eret
    st._eret()


def prim_done(st: 'ST72'):
    """
    DONE1C: exit repeat with a value.
    """
    st._fetch_inner()   # LDAF ARG0 → eval first local
    st._eret()


# ---------------------------------------------------------------------------
# APRETC — apply-return up to global scope
# ---------------------------------------------------------------------------

def prim_apret(st: 'ST72'):
    """
    APRETC: fetch value, pop up to GLOB, active return.
    Mirrors APRETC in CODE.SR.
    """
    st._fetch_inner()
    target_glob = st._glob

    # Pop up to the activation whose address == target_glob
    for _ in range(1000):
        if st.SELF == target_glob:
            break
        alive = st._sretn()
        if not alive:
            break

    st._aret()


# ---------------------------------------------------------------------------
# MEM1C — raw memory access
# ---------------------------------------------------------------------------

def prim_mem(st: 'ST72'):
    """
    MEM1C: raw vmem read or write.
    'mem addr'       → read mem[addr]
    'mem addr _ val' → write mem[addr] = val
    Mirrors MEM1C in CODE.SR.
    """
    # Peek for '_'
    if st._peek(st.A_ARROW):
        # write: fetch value first, then address
        st._fetch_inner()
        val_addr = st.VALUE
        # fetch address
        st._fetch_inner()
        addr = st.obj_int_value(st.VALUE)
        # store
        if st.is_sint(val_addr):
            val = st.sint_value(val_addr)
        else:
            val = val_addr
        st.mem.st(addr, val)
        st._eret()
    else:
        # read: fetch address
        st._fetch_inner()
        addr = st.obj_int_value(st.VALUE)
        raw  = st.mem.ld(addr)
        st._sval(st.intern_int(raw))
        st._eret()


# ---------------------------------------------------------------------------
# RSELFC — return self (instance)
# ---------------------------------------------------------------------------

def prim_rself(st: 'ST72'):
    _rself(st)


# ---------------------------------------------------------------------------
# QFETC / PEEKC — quoted fetch / peek-return
# ---------------------------------------------------------------------------

def prim_qfet(st: 'ST72'):
    """
    QFETC: quoted fetch — read GLOB.MESS.PC token, set VALUE, active return.
    Mirrors QFETC in CODE.SR (uses LGMPC1).
    """
    glob = st._glob
    if not glob:
        st._sval(NIL)
        st._aret()
        return

    glob_mess = st.mem.ld(glob + AR_MESS)
    glob_pc   = st.mem.ld(glob + AR_PC)
    tok       = st.vec_get(glob_mess, glob_pc)
    if tok != NIL:
        # advance PC and store value
        st.mem.st(glob + AR_PC, glob_pc + 1)
    st._sval(tok)
    st._aret()


def prim_peekr(st: 'ST72'):
    """
    PEEKC: peek at GLOB.MESS.PC token, return it (without advancing).
    Mirrors PEEKC in CODE.SR (also uses LGMPC1).
    """
    glob = st._glob
    if not glob:
        st._sval(NIL)
        st._aret()
        return

    glob_mess = st.mem.ld(glob + AR_MESS)
    glob_pc   = st.mem.ld(glob + AR_PC)
    tok       = st.vec_get(glob_mess, glob_pc)
    st._sval(tok)
    st._aret()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_all(st: 'ST72'):
    """
    Register all CODE.SR primitives with the ST72 machine.
    Each primitive is installed as a built-in class handler AND as a
    global name binding, matching how the real system boots.
    """
    prims = [
        # Name          handler           register as class?
        ("Number",      prim_number,      False),  # overrides NCLAS handler
        ("Atom",        prim_atom,        False),  # overrides ATCLS handler
        ("to",          prim_to,          True),
        ("eq",          prim_eq,          True),
        ("null",        prim_null,        True),
        ("isnew",       prim_isnew,       True),
        ("mkins",       prim_mkins,       True),
        ("fetch",       prim_fetch,       True),
        ("match",       prim_match,       True),
        ("put",         prim_put,         True),
        ("get",         prim_get,         True),
        ("quot",        prim_quot,        True),
        ("false",       prim_empty,       False),  # overrides EMPTY handler
        ("repeat",      prim_repeat,      True),
        ("again",       prim_again,       True),
        ("done",        prim_done,        True),
        ("apret",       prim_apret,       True),
        ("mem",         prim_mem,         True),
        ("rself",       prim_rself,       True),
        ("qfet",        prim_qfet,        True),
        ("peekr",       prim_peekr,       True),
    ]

    from st72 import NCLAS, ATCLS, EMPTY

    # Allocate a dedicated class address for the 'false' (EMPTY) class.
    # In the real system EMPT1C handles a special class; we register it
    # under whatever class address the EMPTY object currently reports.
    from st72 import RCMSK
    empty_cls = st.mem.ld(EMPTY) & RCMSK

    for name, fn, make_cls in prims:
        if name == "Number":
            st.class_code[NCLAS] = fn
        elif name == "Atom":
            st.class_code[ATCLS] = fn
        elif name == "false":
            # Register under the actual class of the EMPTY object
            st.class_code[empty_cls] = fn
            # Also keep EMPTY itself as a key in case class lookup uses addr
            st.class_code[EMPTY] = fn
        elif make_cls:
            st.def_builtin_class(name, fn)
        else:
            atom = st.atoms.intern(name)
            st._globals[atom] = st._globals.get(atom, NIL)
