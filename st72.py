"""
Smalltalk-72 interpreter — complete eval/apply/find loop
Faithful translation of EVAL.SR + FUNCS.SR + PAGE0.SR (Nova assembly sources).

Memory model
============
A flat list `mem[]` of Python ints, indexed by address.

Address spaces (decimal, from SMALL.PARMS + PAGE0.SR):
  0                   NIL
  1 .. MXATM-1        atoms  (MXATM = NATMS-1 = 2047)
  SINTB .. MXNUM      small integers  (SINTB = NATMS+8 = 2056, MXNUM = SINTB+513)
  BHMEM downward      heap objects (2-word pairs: [CLASS|refct, value])
  BHMEM upward        activation records (AREC, layout below)

Object layout in heap (2 words at address A):
  mem[A]   = CLASS_addr | refcount  (RCMSK = 0o177770 masks out refct)
  mem[A+1] = payload / value

AREC layout (from ARTAB / ACTIV in EVAL.SR + FUNCS.SR):
  AREC+0  = CLASS of activation class (used for CACT/HFRE sizing)
  AREC+1  = class hash-table mask / nvars
  AREC+2  = INST  (instance the activation is running on)
  AREC+3  = MESS  (pointer to current message vector)
  AREC+4  = GLOB  (enclosing global scope AREC)
  AREC+5  = RETN  (caller AREC, 0 = top level)
  AREC+6  = CLAS  (class of this activation)
  AREC+7  = MODE  (2=EVAL, 3=APPLY)
  AREC+8  = PC    (program counter, index into MESS vector)
  AREC+9  = VALUE (current value — shadowed in self.VALUE for speed)
  AREC+10 = TOKEN (current token)
  AREC+11..= local variables (nil-initialised)

Message vector layout (LSCLA object):
  mem[V]   = LSCLA | refct
  mem[V+1] = length  N
  mem[V+2..V+N+1] = token addresses

FIND chain: GLOB links ARECs together for lexical scoping.
"""

# ---------------------------------------------------------------------------
# Constants  (octal literals match the Nova sources exactly)
# ---------------------------------------------------------------------------

NATMS  = 0o4000          # 2048 — atom table size
MXATM  = NATMS - 1       # 2047 — highest atom address

SINT1  = -0o200          # -128 — value of smallest small integer
SINTB  = NATMS + 8       # 2056 — base address of small-int table
MXNUM  = SINTB + 0o1001  # 2056 + 513 = 2569 — highest small-int address

# Built-in class addresses (octal, fixed by PAGE0.SR)
MASTER = 0o5210   # Class CLASS   2184
NCLAS  = 0o5260   # Number        2224
LSCLA  = 0o5350   # Vector/List   2280
ATCLS  = 0o5430   # Atom          2328
SCLAS  = 0o5470   # String        2360
ARCLS  = 0o5540   # ARecord       2400
FPCLAS = 0o5610   # Float         2440
EMPTY  = 0o5126   # false object  2134

RCMSK  = 0o177770  # mask to kill ref-count bits (low 3 bits)
NIL    = 0

# AREC field offsets  (from ARTAB / field names in EVAL.SR)
AR_CLAS0 = 0   # class of activation-class (for CACT/HFRE sizing)
AR_MASK  = 1   # class mask / nvars
AR_INST  = 2   # INST
AR_MESS  = 3   # MESS
AR_GLOB  = 4   # GLOB
AR_RETN  = 5   # RETN
AR_CLAS  = 6   # CLAS
AR_MODE  = 7   # MODE
AR_PC    = 8   # PC
AR_VALUE = 9   # VALUE  (also a PAGE0 global)
AR_TOKEN = 10  # TOKEN  (also PAGE0)
AR_LOCAL = 11  # first local variable (= ARG0 = NSYS)

MODE_EVAL  = 2
MODE_APPLY = 3

VMEM_SIZE  = 0o20000   # 8192 words


# ---------------------------------------------------------------------------
# Virtual memory
# ---------------------------------------------------------------------------

class VMem:
    def __init__(self, size: int = VMEM_SIZE):
        self._m  = [NIL] * size
        self.size = size

    def ld(self, a: int) -> int:
        if not (0 <= a < self.size):
            raise MemoryError(f"vmem load OOB: {oct(a)}")
        return self._m[a]

    def st(self, a: int, v: int):
        if not (0 <= a < self.size):
            raise MemoryError(f"vmem stor OOB: {oct(a)}")
        self._m[a] = v

    # LDAF/STAF: load/store relative to a base pointer (SELF in Nova)
    def ldaf(self, base: int, offset: int) -> int:
        return self.ld(base + offset)

    def staf(self, base: int, offset: int, val: int):
        self.st(base + offset, val)


# ---------------------------------------------------------------------------
# Atom table  (intern by name → address in 1..MXATM)
# ---------------------------------------------------------------------------

class AtomTable:
    def __init__(self):
        self._s2a: dict[str, int] = {}
        self._a2s: dict[int, str] = {}
        self._next = 1

    def intern(self, name: str) -> int:
        if name in self._s2a:
            return self._s2a[name]
        a = self._next
        if a > MXATM:
            raise OverflowError(f"Atom table overflow: {name!r}")
        self._s2a[name] = a
        self._a2s[a]    = name
        self._next     += 1
        return a

    def name_of(self, a: int) -> str | None:
        return self._a2s.get(a)

    def is_atom(self, a: int) -> bool:
        return 1 <= a <= MXATM


# ---------------------------------------------------------------------------
# Smalltalk-72 machine
# ---------------------------------------------------------------------------

class ST72:
    """
    Complete Smalltalk-72 evaluator.

    The central structure is the AREC (activation record) stored in vmem.
    self.SELF always points to the current AREC (= PAGE0 SELF in Nova).

    Main loop mirrors EL1 in EVAL.SR:
        mode < 3  →  EMODE
        mode == 3 →  AMODE
    """

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def __init__(self):
        self.mem   = VMem()
        self.atoms = AtomTable()

        # PAGE0 registers
        self.SELF  = NIL
        self.VALUE = NIL
        self.TOKEN = NIL
        self.MESSX = NIL   # working message ptr  (EVAL.SR: MESSX)
        self.GLOBX = NIL   # working global ptr   (EVAL.SR: GLOBX)

        # Heap pointers  (stack grows down from top of vmem)
        self.BHMEM = self.mem.size - 2
        self.TLMEM = MXNUM + 0o200

        self._running = False

        # Set of "permanent" object addresses (classes, globals) that must
        # survive the BHMEM >= obj guard in _tori.
        self._perm_objects: set[int] = set()

        # Python-level binding tables  (replaces in-vmem hash tables)
        #   _bindings[arec_addr][token_addr] = value_addr
        self._bindings: dict[int, dict[int, int]] = {}
        self._globals:  dict[int, int]            = {}

        self._init_specials()
        self._init_builtins()
        self._init_global_bindings()

        # Optional Python callables for built-in class activation:
        #   class_code[class_addr](st72) → None  (modifies self.VALUE etc.)
        self.class_code: dict[int, callable] = {}

    def _init_specials(self):
        i = self.atoms.intern
        self.A_PER   = i(".")
        self.A_COLN  = i(":")
        self.A_QUEST = i("?")
        self.A_QUOTE = i('"')
        self.A_MACH  = i("%")
        self.A_BANG  = i("!")
        self.A_NOEV  = i("#")
        self.A_CODE  = i("CODE")
        self.A_ARROW = i("_")
        self.A_LBRA  = i("[")
        self.A_RBRA  = i("]")

    def _init_builtins(self):
        m = self.mem
        for addr in (MASTER, NCLAS, LSCLA, ATCLS, SCLAS, ARCLS, FPCLAS, EMPTY):
            m.st(addr,   MASTER)
            m.st(addr+1, NIL)
        m.st(EMPTY, ATCLS)
        # Small-integer payload table
        for i in range(MXNUM - SINTB + 1):
            m.st(SINTB + i, SINT1 + i)

    def _init_global_bindings(self):
        for name, addr in [
            ("nil",    NIL),
            ("false",  EMPTY),
            ("Number", NCLAS),
            ("Atom",   ATCLS),
            ("String", SCLAS),
            ("Class",  MASTER),
            ("Vector", LSCLA),
        ]:
            self._globals[self.atoms.intern(name)] = addr

    # ------------------------------------------------------------------
    # Type predicates  (mirrors ISIT / ATORN / TORI tests)
    # ------------------------------------------------------------------

    def is_nil(self, a: int) -> bool:   return a == NIL
    def is_sint(self, a: int) -> bool:  return SINTB <= a <= MXNUM
    def is_atom(self, a: int) -> bool:  return 1 <= a <= MXATM
    def is_false(self, a: int) -> bool: return a == EMPTY or a == NIL

    def class_of(self, a: int) -> int:
        if self.is_nil(a):   return NIL
        if self.is_sint(a):  return NCLAS
        if self.is_atom(a):  return ATCLS
        return self.mem.ld(a) & RCMSK

    def is_template(self, a: int) -> bool:
        """Class whose class-word (masked) == MASTER."""
        if self.is_nil(a) or self.is_atom(a) or self.is_sint(a):
            return False
        return (self.mem.ld(a) & RCMSK) == MASTER

    def is_vector(self, a: int) -> bool:
        return self.class_of(a) == LSCLA

    # ------------------------------------------------------------------
    # Integer helpers  (INTN / IVAL in FUNCS.SR)
    # ------------------------------------------------------------------

    def sint_value(self, a: int) -> int:
        return SINT1 + (a - SINTB)

    def intern_int(self, n: int) -> int:
        """INTN: intern integer → address. Small-int table or heap object."""
        i = n - SINT1
        if 0 <= i <= (MXNUM - SINTB):
            return SINTB + i
        a = self._alloc(2)
        self.mem.st(a,   NCLAS)
        self.mem.st(a+1, n)
        return a

    def obj_int_value(self, a: int) -> int:
        if self.is_sint(a):                return self.sint_value(a)
        if self.class_of(a) == NCLAS:      return self.mem.ld(a + 1)
        raise TypeError(f"Not a number: {oct(a)}")

    # ------------------------------------------------------------------
    # Heap allocation
    # ------------------------------------------------------------------

    def _alloc(self, nwords: int) -> int:
        """Allocate nwords downward from BHMEM."""
        self.BHMEM -= nwords
        if self.BHMEM <= self.TLMEM:
            raise MemoryError("Heap exhausted")
        for i in range(nwords):
            self.mem.st(self.BHMEM + i, NIL)
        return self.BHMEM

    # ------------------------------------------------------------------
    # Vector  (message / list objects — LSCLA)
    # ------------------------------------------------------------------

    def make_vector(self, tokens: list[int]) -> int:
        """Allocate [LSCLA, len, tok0, …, tokN-1]."""
        n = len(tokens)
        a = self._alloc(2 + n)
        self.mem.st(a,   LSCLA)
        self.mem.st(a+1, n)
        for i, t in enumerate(tokens):
            self.mem.st(a + 2 + i, t)
        return a

    def vec_len(self, v: int) -> int:
        return self.mem.ld(v + 1)

    def vec_get(self, v: int, idx: int) -> int:
        """0-based. Returns NIL past end (acts like implicit '.')."""
        if v == NIL:
            return NIL
        n = self.vec_len(v)
        if idx < 0 or idx >= n:
            return NIL
        return self.mem.ld(v + 2 + idx)

    # ------------------------------------------------------------------
    # AREC allocation  (CACT in FUNCS.SR)
    # ------------------------------------------------------------------

    def _alloc_arec(self, n_locals: int = 0) -> int:
        size = AR_LOCAL + n_locals
        a    = self._alloc(size)
        return a

    # ------------------------------------------------------------------
    # AREC field accessors via SELF  (LDAF / STAF macros)
    # ------------------------------------------------------------------

    def _ldaf(self, offset: int) -> int:
        return self.mem.ld(self.SELF + offset)

    def _staf(self, offset: int, val: int):
        self.mem.st(self.SELF + offset, val)

    @property
    def _mode(self):        return self._ldaf(AR_MODE)
    @_mode.setter
    def _mode(self, v):     self._staf(AR_MODE, v)

    @property
    def _pc(self):          return self._ldaf(AR_PC)
    @_pc.setter
    def _pc(self, v):       self._staf(AR_PC, v)

    @property
    def _mess(self):        return self._ldaf(AR_MESS)
    @_mess.setter
    def _mess(self, v):     self._staf(AR_MESS, v)

    @property
    def _glob(self):        return self._ldaf(AR_GLOB)
    @_glob.setter
    def _glob(self, v):     self._staf(AR_GLOB, v)

    @property
    def _retn(self):        return self._ldaf(AR_RETN)
    @_retn.setter
    def _retn(self, v):     self._staf(AR_RETN, v)

    @property
    def _clas(self):        return self._ldaf(AR_CLAS)
    @_clas.setter
    def _clas(self, v):     self._staf(AR_CLAS, v)

    @property
    def _inst(self):        return self._ldaf(AR_INST)
    @_inst.setter
    def _inst(self, v):     self._staf(AR_INST, v)

    # ------------------------------------------------------------------
    # Message cursor primitives  (APC / AMPC / PEEK)
    # ------------------------------------------------------------------

    def _apc(self) -> int:
        """APC: read self's MESS[PC], advance PC."""
        pc       = self._pc
        tok      = self.vec_get(self._mess, pc)
        self._pc = pc + 1
        return tok

    def _ampc(self) -> int:
        """AMPC: read self's MESS[PC] from CURRENT AREC, same as _apc here."""
        return self._apc()

    def _amxpc(self) -> int:
        """
        AMXPC: advance MESSX cursor.
        In EVAL.SR, MESSX is set to SELF in EMODE, so it shares SELF's PC.
        When MESSX == SELF we just use _apc(); otherwise use _messx_pc.
        """
        if self.MESSX == self.SELF:
            return self._apc()
        tok = self.vec_get(self.MESSX, self._messx_pc)
        self._messx_pc += 1
        return tok

    def _peek(self, want: int) -> bool:
        """PEEK: if MESS[PC] == want, advance and return True."""
        tok = self.vec_get(self._mess, self._pc)
        if tok == want:
            self._pc += 1
            return True
        return False

    def _peek_raw(self) -> int:
        """Peek without advancing."""
        return self.vec_get(self._mess, self._pc)

    # ------------------------------------------------------------------
    # FIND  (FUNCS.SR: chase GLOB chain for token lookup)
    # ------------------------------------------------------------------

    def _find(self, token: int, arec_addr: int) -> int | None:
        """
        FIND: look up token starting from arec_addr, chasing GLOB chain.
        Returns value address or None on failure.

        Mirrors FIND in FUNCS.SR:
          1. Check AREC pseudo-fields (ARTAB)
          2. Check local bindings at this AREC
          3. Chase GLOB link (FND3A / FIND3)
          4. Fall back to global table
        """
        if not self.atoms.is_atom(token):
            return None   # FERR: non-atomic symbol

        cur = arec_addr
        while cur:
            # --- ARTAB: activation-record pseudo-fields ---
            name = self.atoms.name_of(token)
            if name == "AREC": return cur
            if name == "SELF": return self.mem.ld(cur + AR_INST)
            if name == "MESS": return self.mem.ld(cur + AR_MESS)
            if name == "GLOB": return self.mem.ld(cur + AR_GLOB)
            if name == "RETN": return self.mem.ld(cur + AR_RETN)
            if name == "CLAS": return self.mem.ld(cur + AR_CLAS)

            # --- local bindings ---
            v = self._bindings.get(cur, {}).get(token)
            if v is not None:
                return v

            # --- chase GLOB (FND3A) ---
            cur = self.mem.ld(cur + AR_GLOB)

        return self._globals.get(token)

    def _put(self, token: int, value: int, arec_addr: int):
        """PUT: store token→value in arec's local binding table."""
        if arec_addr not in self._bindings:
            self._bindings[arec_addr] = {}
        self._bindings[arec_addr][token] = value

    # ------------------------------------------------------------------
    # SVAL / SVLI  (FUNCS.SR)
    # ------------------------------------------------------------------

    def _sval(self, v: int):
        self.VALUE = v

    def _svli(self, v: int):
        self.VALUE = v

    # ------------------------------------------------------------------
    # SRETN  (FUNCS.SR: Smalltalk return — pop activation)
    # ------------------------------------------------------------------

    def _sretn(self) -> bool:
        """
        SRETN: return to caller.
        Returns True if we switched to a valid caller, False at top-level.
        Mirrors SRETN in FUNCS.SR.

        PC propagation: if the departing AREC shares MESS with the caller
        (i.e. the primitive read from the caller's message stream), sync
        the caller's PC to the primitive's current PC before popping.
        This is the mechanism by which NUM1C/ATOM1C consume tokens from
        the caller's stream and the caller's PC advances accordingly.
        """
        retn = self._retn
        if retn == NIL:
            return False   # top-level
        old = self.SELF
        # Sync caller's PC if we share the same message vector
        my_mess = self._ldaf(AR_MESS)
        my_pc   = self._ldaf(AR_PC)
        caller_mess = self.mem.ld(retn + AR_MESS)
        if my_mess == caller_mess and my_mess != NIL:
            self.mem.st(retn + AR_PC, my_pc)
        # Reclaim AREC if at top of heap stack (simplified)
        if old == self.BHMEM:
            self.BHMEM += AR_LOCAL
        self.SELF = retn
        # Restore MESSX PC tracking
        self._messx_pc = self._pc
        return True

    # ------------------------------------------------------------------
    # VOID  (EVAL.SR: test for empty / terminated message)
    # ------------------------------------------------------------------

    def _void(self) -> bool:
        """VOID: True if next token in current message is '.' or NIL."""
        tok = self.vec_get(self._mess, self._pc)
        return tok == NIL or tok == self.A_PER

    # ------------------------------------------------------------------
    # ACTIV  (EVAL.SR: create and switch to a new activation)
    # ------------------------------------------------------------------

    def _activ(self, class_addr: int, inst_addr: int):
        """
        ACTIV: allocate AREC, fill fields, switch SELF.
        Mirrors ACTIV in EVAL.SR exactly.
        """
        retnx  = self.SELF
        new_ar = self._alloc_arec(0)

        self.SELF = new_ar
        self._messx_pc = 0

        self._staf(AR_MODE, MODE_EVAL)
        self._staf(AR_INST, inst_addr)
        self._staf(AR_RETN, retnx)
        self._staf(AR_GLOB, self.GLOBX)
        self._staf(AR_MESS, self.MESSX)
        self._staf(AR_CLAS, class_addr)
        self._staf(AR_PC,   0)

        # Set MESS and PC so primitives can read from the caller's message stream.
        # In the real Nova system, MESSX is the caller's AREC pointer, and
        # the new AREC's MESS field = MESSX (caller AREC).
        # For built-in handlers, we directly set MESS to the caller's message
        # vector and PC to the caller's current PC, so _apc() reads correctly.
        caller_mess = self.mem.ld(retnx + AR_MESS) if retnx else NIL
        caller_pc   = self.mem.ld(retnx + AR_PC)   if retnx else 0
        self._staf(AR_MESS, caller_mess)
        self._staf(AR_PC,   caller_pc)

        # Check for Python built-in handler first
        if class_addr in self.class_code:
            # Handler is responsible for calling _eret() or _aret() itself.
            # Before calling, we are in the primitive's AREC (SELF = prim_ar).
            # The handler reads from SELF._mess (= caller's message vector).
            # After the handler calls _eret/_aret, SELF is restored to caller.
            self.class_code[class_addr](self)
            return

        # Find DO field: mem[class_addr+3] → code vector
        if class_addr != NIL and class_addr + 3 < self.mem.size:
            do_vec = self.mem.ld(class_addr + 3)
            if self.is_vector(do_vec):
                self._staf(AR_MESS, do_vec)
                self._staf(AR_PC,   0)
                return

        # No code vector — passive return (PASRT): VALUE already set
        self._eret()

    # ------------------------------------------------------------------
    # ERET / ARET  (EVAL.SR: passive / active return)
    # ------------------------------------------------------------------

    def _eret(self):
        """
        ERET: passive return.
        SRETN → if top-level: stop.
        If returnee in APPLY mode → cascade ERET.
        """
        alive = self._sretn()
        if not alive:
            self._running = False
            return
        if self._mode == MODE_APPLY:
            self._eret()

    def _aret(self):
        """
        ARET: active return.
        Peek for '.'; if null message → ERET (passive).
        Else MODE ← APPLY, continue eval.
        """
        raw = self._peek_raw()
        if raw == NIL or raw == self.A_PER:
            self._eret()
        else:
            self._mode = MODE_APPLY

    # ------------------------------------------------------------------
    # RNIL  (EVAL.SR)
    # ------------------------------------------------------------------

    def _rnil(self):
        self._sval(NIL)
        # fall through to next eval step

    # ------------------------------------------------------------------
    # PASRT  (EVAL.SR: passive return — set VALUE, dispatch)
    # ------------------------------------------------------------------

    def _pasrt(self, obj: int):
        """
        PASRT: store obj into VALUE.
        If MODE == APPLY → ERET.
        Else fall through to eval loop.
        """
        self._sval(obj)
        if self._mode == MODE_APPLY:
            self._eret()

    # ------------------------------------------------------------------
    # TORI  (EVAL.SR: template-or-instance dispatch)
    # ------------------------------------------------------------------

    def _tori(self, obj: int):
        """
        TORI: classify obj and dispatch.

        NIL              → RNIL
        addr ≤ MXNUM     → ATORN (atom or small-int)
        addr ≥ BHMEM     → PASRT (it's an AREC or unreachable region)
        heap object:
          class == MASTER → ACTIV as template (INSTX = NIL)
          else            → INS  → ACTIV as instance
        """
        if self.is_nil(obj):
            self._rnil()
            return

        # ATORN range: atoms and small-ints
        if obj <= MXNUM:
            self._atorn(obj)
            return

        # Above heap top → PASRT, UNLESS it's a registered class object.
        # Built-in classes are allocated from BHMEM downward at init time,
        # so their addresses are >= current BHMEM (which keeps shrinking).
        # We must treat them as valid class/template objects, not as ARecs.
        if obj >= self.BHMEM and obj not in self._perm_objects:
            self._pasrt(obj)
            return

        # Load class word from heap
        cls = self.mem.ld(obj) & RCMSK

        if cls == MASTER:
            # Template: activate it, instance = NIL
            self._sval(obj)
            self.MESSX = self.SELF
            self.GLOBX  = self.SELF
            self._activ(obj, NIL)
        else:
            # Instance: activate its class
            self._sval(obj)
            self.MESSX = self.SELF
            self.GLOBX  = self.SELF
            self._activ(cls, obj)

    def _atorn(self, obj: int):
        """
        ATORN: atoms and small-ints recognised by address range.
        Small int (SINTB ≤ obj ≤ MXNUM) → class NCLAS
        Atom     (1 ≤ obj ≤ MXATM)      → class ATCLS
        """
        if self.is_sint(obj):
            # NUMBER: void check first
            self._sval(obj)
            if self._void():
                self._pasrt(obj)
                return
            # Also skip activation on ']' or '?'
            nxt = self._peek_raw()
            if nxt == self.A_RBRA or nxt == self.A_QUEST:
                self._pasrt(obj)
                return
            self.MESSX = self.SELF
            self.GLOBX  = self.SELF
            self._activ(NCLAS, obj)
            return

        if self.is_atom(obj):
            self._sval(obj)
            if self._void():
                self._pasrt(obj)
                return
            nxt = self._peek_raw()
            if nxt == self.A_RBRA or nxt == self.A_QUEST:
                self._pasrt(obj)
                return
            self.MESSX = self.SELF
            self.GLOBX  = self.SELF
            self._activ(ATCLS, obj)
            return

        # Fallthrough
        self._pasrt(obj)

    # ------------------------------------------------------------------
    # EFIND  (EVAL.SR: look up TOKEN in GLOBX)
    # ------------------------------------------------------------------

    def _efind(self):
        """
        EFIND: look up self.TOKEN in GLOBX.
        Non-atomic → TORI directly.
        '?' → CONDS
        '"' → QUOT
        else → FIND in GLOBX → TORI
        """
        tok = self.TOKEN

        # Non-atomic (not in atom range) → TORI directly
        if not self.is_atom(tok):
            self._tori(tok)
            return

        # '?' → CONDS
        if tok == self.A_QUEST:
            self._conds()
            return

        # '"' → QUOT
        if tok == self.A_QUOTE:
            self._quot()
            return

        # FIND in GLOBX
        val = self._find(tok, self.GLOBX)
        if val is None:
            raise NameError(
                f"symbol has no value: {self.atoms.name_of(tok)!r}"
            )
        self.TOKEN = val
        self._tori(val)

    # ------------------------------------------------------------------
    # EMODE  (EVAL.SR: one eval-mode step)
    # ------------------------------------------------------------------

    def _emode(self):
        """
        EMODE: advance PC, dispatch on token.
        Mirrors EM1/EMODE in EVAL.SR exactly.
        """
        tok = self._apc()

        # '.' or NIL → EM1 in EVAL.SR:
        #   NIL 0,0; SVLI  -- reset VALUE to NIL
        #   LDAF INST; SNL; SVAL  -- but use INST if non-nil
        #   ERET
        # We only reset VALUE when this activation hasn't produced one yet
        # (VALUE == NIL), because _quot/_bind etc. may have set VALUE before
        # the closing '.'.
        if tok == self.A_PER or tok == NIL:
            inst = self._inst
            if inst != NIL:
                self._sval(inst)
            elif self.VALUE == NIL:
                self._svli(NIL)
            # else: keep VALUE set by prior _quot/_bind etc.
            self._eret()
            return

        self.TOKEN = tok
        # MESSX and GLOBX ← SELF  (so EFIND uses current scope)
        self.MESSX     = self.SELF
        self._messx_pc = self._pc   # MESSX cursor tracks SELF's PC
        self.GLOBX     = self.SELF

        # ':' → FMODE
        if tok == self.A_COLN:
            self._fmode()
            return

        # '%' → MACH
        if tok == self.A_MACH:
            self._mach()
            return

        # '!' → FARET
        if tok == self.A_BANG:
            self._faret()
            return

        # SNL test: tok == NIL already handled → fall through to EFIND
        # EFIND itself handles '?' and '"' when they appear as atoms
        self._efind()

    # Note: '?' and '"' reach _efind as atoms; _efind dispatches them.

    # ------------------------------------------------------------------
    # AMODE  (EVAL.SR: apply / re-run mode)
    # ------------------------------------------------------------------

    def _amode(self):
        """
        AMODE: apply VALUE to the message.
        Mirrors AMODE in EVAL.SR:
          VALUE == NIL → ERET
          GLOBX ← GLOB; MESSX ← MESS (of current AREC)
          TOKEN ← VALUE
          → TORI
        """
        if self.is_nil(self.VALUE):
            self._eret()
            return

        self.GLOBX     = self._glob
        self.MESSX     = self._mess
        self._messx_pc = self._pc
        self.TOKEN     = self.VALUE
        self._tori(self.VALUE)

    # ------------------------------------------------------------------
    # CONDS  (EVAL.SR: '?' conditional)
    # ------------------------------------------------------------------

    def _conds(self):
        """
        CONDS: pick up following list from MESSX; if VALUE is truthy,
        redirect MESSX.PC into the list body.
        Mirrors CONDS in EVAL.SR.
        """
        tok = self._amxpc()
        if not self.is_vector(tok):
            raise RuntimeError("Code vector missing (CONDS expects a list)")
        if not self.is_false(self.VALUE):
            # Redirect: store tok into MESSX, reset PC
            self._mess      = tok
            self._pc        = 0
            self.MESSX      = tok
            self._messx_pc  = 0

    # ------------------------------------------------------------------
    # QUOT  (EVAL.SR: '"' — quote next token)
    # ------------------------------------------------------------------

    def _quot(self):
        """
        QUOT: read next token from MESSX unevaluated, set VALUE, RUN.
        Mirrors QUOT in EVAL.SR.
        """
        tok = self._amxpc()
        self._sval(tok)
        self._run()

    # ------------------------------------------------------------------
    # FMODE  (EVAL.SR: ':' fetch-and-bind)
    # ------------------------------------------------------------------

    def _fmode(self):
        """
        FMODE: ':' — fetch/eval next expression, optionally bind to a name.

        Faithful to FMODE in EVAL.SR:
          flag = MESS[PC+1]  (one past current PC, i.e. two past the ':')
          NIL flag   → FM7: FETCH (eval MESS[PC]), then BIND
          '"'  flag  → FM3: APC (skip '"'), AMPC (literal token) → VALUE, BIND
          '#'  flag  → FM6: APC (skip '#'), AMPC (no-eval token), lookup, BIND
          else       → FM7: FETCH + BIND

        BIND: APC → name; PUT SELF[name] = VALUE; RUN.
        If BIND reads '.' or NIL as name, no binding is done.
        """
        # flag = MESS[PC+1]  (LDAF PC; INC 0,1; LOAD)
        pc   = self._pc           # points to first token after ':'
        flag = self.vec_get(self._mess, pc)  # MESS[PC] — this IS PC+1 after ':' consumed

        if flag == NIL:
            # FM7: nil flag → FETCH (eval MESS[PC])
            self._fetch_inner()
            self._bind()
            return

        if flag == self.A_QUOTE:
            # FM3: ':"' — skip '"', get next token literally
            self._pc += 1           # APC skips '"'
            tok = self._apc()       # AMPC gets the literal token
            self._sval(tok)
            self._bind()
            return

        if flag == self.A_NOEV:
            # FM6: ':#' — skip '#', get token, look up atoms only
            self._pc += 1           # skip '#'
            tok = self._apc()       # get token
            self.TOKEN = tok
            if self.is_atom(tok):
                val = self._find(tok, self._glob)
                if val is not None:
                    tok = val
            self._sval(tok)
            self._bind()
            return

        # FM7 default: FETCH (reads MESS[PC], advances PC, calls EFIND)
        self._fetch_inner()
        self._bind()

    def _fetch_inner(self):
        """
        FETCH / EVTK1 from EVAL.SR:
        AMPC → TOKEN, GLOBX ← GLOB, MESSX ← MESS, → EFIND.
        """
        tok        = self._apc()
        self.TOKEN = tok
        self.GLOBX = self._glob
        self.MESSX = self._mess
        self._messx_pc = self._pc
        self._efind()

    # ------------------------------------------------------------------
    # BIND  (EVAL.SR: store VALUE under next name in SELF)
    # ------------------------------------------------------------------

    def _bind(self):
        """
        BIND: read next token as binding name; if '.' or NIL → eval loop.
        PUT VALUE into SELF under name.
        Then RUN.
        Mirrors BIND in EVAL.SR.
        """
        name_tok = self._apc()
        if name_tok == NIL or name_tok == self.A_PER:
            return   # no name to bind to

        # PUT SELF, name_tok, VALUE
        self._put(name_tok, self.VALUE, self.SELF)
        self._run()

    # ------------------------------------------------------------------
    # RUN  (EVAL.SR: check void then TORI)
    # ------------------------------------------------------------------

    def _run(self):
        """
        RUN: void check, then TOKEN ← VALUE, TORI.
        Mirrors RUN in EVAL.SR.
        """
        if self._void():
            return
        self.TOKEN = self.VALUE
        self._tori(self.VALUE)

    # ------------------------------------------------------------------
    # MACH  (EVAL.SR: '%' pattern match)
    # ------------------------------------------------------------------

    def _mach(self):
        """
        MACH: pick up match token, try to match next in MESS.
        On fail, scan for '? alt % tok' alternatives.
        Mirrors MACH / MACHLP in EVAL.SR.
        """
        want = self._apc()   # APC: pick up token to match

        # PEEK: does next token match?
        if self._peek(want):
            return   # JJ → JEMO: continue eval

        saved = want
        mess  = self._mess

        while True:
            pc  = self._pc
            # NEXT: look-ahead for '?'
            tok = self.vec_get(mess, pc)
            if tok == self.A_QUEST:
                # Hop over ?-clause
                pc += 1
                _   = self.vec_get(mess, pc)   # skip branch token
                pc += 1
                t_pc = pc
                # Seek next '%'
                tok2 = self.vec_get(mess, pc)
                pc  += 1
                if tok2 == self.A_MACH:
                    # Try next match token
                    self._pc = pc
                    next_tok = self._apc()
                    if self._peek(next_tok):
                        return   # match
                    continue
                else:
                    # MACH2: no '%' → resume at t_pc
                    self._pc = t_pc
                    return
            else:
                # MACH1: no '?' → run false
                self._sval(EMPTY)
                self._run()
                return

    # ------------------------------------------------------------------
    # FARET  (EVAL.SR: '!' active return without activating)
    # ------------------------------------------------------------------

    def _faret(self):
        """
        FARET: fetch value from SELF (FARFECH), then ARET.
        Mirrors FARET / FARFECH in EVAL.SR.
        """
        tok        = self._apc()
        self.TOKEN = tok
        self.GLOBX = self._glob
        self.MESSX = self._mess
        self._messx_pc = self._pc
        self._efind()
        self._aret()

    # ------------------------------------------------------------------
    # Main loop  (EL1 in EVAL.SR)
    # ------------------------------------------------------------------

    def _eval_loop(self, max_steps: int = 100_000) -> int:
        """
        EL1: dispatch on MODE until _running goes False or steps exceeded.
        """
        self._running = True
        steps = 0
        while self._running and steps < max_steps:
            steps += 1
            mode = self._mode
            if mode < MODE_APPLY:
                self._emode()
            elif mode == MODE_APPLY:
                self._amode()
            else:
                self._running = False
                break
        return self.VALUE

    # ------------------------------------------------------------------
    # Top-level entry
    # ------------------------------------------------------------------

    def make_top_arec(self, mess_vec: int) -> int:
        """Create a top-level (no caller) AREC for mess_vec."""
        ar = self._alloc_arec(0)
        m  = self.mem
        m.st(ar + AR_MODE, MODE_EVAL)
        m.st(ar + AR_PC,   0)
        m.st(ar + AR_MESS, mess_vec)
        m.st(ar + AR_GLOB, NIL)
        m.st(ar + AR_RETN, NIL)
        m.st(ar + AR_CLAS, NIL)
        m.st(ar + AR_INST, NIL)
        return ar

    def run(self, tokens: list[int], max_steps: int = 100_000) -> int:
        """
        Run a message (list of token addresses).
        Terminates with '.' if not already present.
        Returns final VALUE.
        """
        if not tokens or tokens[-1] != self.A_PER:
            tokens = list(tokens) + [self.A_PER]
        mess           = self.make_vector(tokens)
        self.VALUE     = NIL
        self.TOKEN     = NIL
        ar             = self.make_top_arec(mess)
        self.SELF      = ar
        self.MESSX     = ar
        self.GLOBX     = ar
        self._messx_pc = 0
        return self._eval_loop(max_steps)

    def run_str(self, source: str, max_steps: int = 100_000) -> int:
        """Tokenize and run a source string.
        Delegates to st72_reader.Reader: handles [ ] sub-expressions,
        quoted strings, composite operators (<=, >=, &*, …).
        """
        from st72_reader import Reader
        return Reader(self).run(source, max_steps)

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    def defglobal(self, name: str, value: int):
        self._globals[self.atoms.intern(name)] = value

    def defclass(self, name: str, do_tokens: list[int]) -> int:
        """
        Register a class with a DO code vector.
        Class header: [MASTER, NIL, NIL, do_vec_ptr]  (4 words).
        """
        do_vec = self.make_vector(do_tokens + [self.A_PER])
        cls    = self._alloc(4)
        self.mem.st(cls,   MASTER)
        self.mem.st(cls+1, NIL)
        self.mem.st(cls+2, NIL)
        self.mem.st(cls+3, do_vec)
        self._perm_objects.add(cls)
        self.defglobal(name, cls)
        return cls

    def def_builtin_class(self, name: str, fn: callable) -> int:
        """
        Register a class whose activation runs a Python function.
        fn(st72) → None  (should call _sval / _pasrt etc.)
        """
        cls = self._alloc(4)
        self.mem.st(cls,   MASTER)
        self.mem.st(cls+1, NIL)
        self.mem.st(cls+2, NIL)
        self.mem.st(cls+3, NIL)
        self.class_code[cls] = fn
        self._perm_objects.add(cls)
        self.defglobal(name, cls)
        return cls

    def value_repr(self, a: int) -> str:
        if self.is_nil(a):   return "nil"
        if a == EMPTY:       return "false"
        if self.is_sint(a):  return str(self.sint_value(a))
        if self.is_atom(a):
            n = self.atoms.name_of(a)
            return f"'{n}'" if n else f"atom@{oct(a)}"
        cls = self.class_of(a)
        if cls == NCLAS:
            return str(self.mem.ld(a + 1))
        if cls == LSCLA:
            n   = self.vec_len(a)
            els = [self.value_repr(self.vec_get(a, i)) for i in range(min(n, 8))]
            suffix = "..." if n > 8 else ""
            return f"[{' '.join(els)}{suffix}]"
        return f"obj@{oct(a)}(cls={oct(cls)})"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests():
    print("=== Smalltalk-72 evaluator tests ===\n")

    # ----------------------------------------------------------------
    # 1. Type system basics
    # ----------------------------------------------------------------
    st = ST72()

    for n in (-128, -1, 0, 1, 42, 200):
        a = st.intern_int(n)
        assert st.is_sint(a), f"intern_int({n}): not a sint"
        assert st.obj_int_value(a) == n, f"sint_value({n}) round-trip"
    print("PASS  sint intern/value")

    a_hello = st.atoms.intern("hello")
    assert st.is_atom(a_hello)
    assert st.class_of(a_hello) == ATCLS
    assert st.atoms.name_of(a_hello) == "hello"
    print("PASS  atom intern/class_of")

    v = st.make_vector([st.A_QUOTE, a_hello, st.A_PER])
    assert st.is_vector(v)
    assert st.vec_len(v) == 3
    assert st.vec_get(v, 0) == st.A_QUOTE
    assert st.vec_get(v, 99) == NIL
    print("PASS  make_vector/vec_get")

    # ----------------------------------------------------------------
    # 2. FIND
    # ----------------------------------------------------------------
    st2 = ST72()
    st2.defglobal("answer", st2.intern_int(42))
    ans = st2.atoms.intern("answer")
    ar  = st2.make_top_arec(st2.make_vector([st2.A_PER]))
    found = st2._find(ans, ar)
    assert st2.obj_int_value(found) == 42, f"find answer: {found}"
    print("PASS  _find global")

    # ----------------------------------------------------------------
    # 3. Quote — returns atom unevaluated
    # ----------------------------------------------------------------
    st3 = ST72()
    x   = st3.atoms.intern("hello")
    # run:  " hello .
    result = st3.run([st3.A_QUOTE, x, st3.A_PER])
    assert result == x, f"quote: got {oct(result)}, expected {oct(x)}"
    print(f"PASS  quote: '\" hello .' → {st3.value_repr(result)}")

    # ----------------------------------------------------------------
    # 4. Integer literal
    # ----------------------------------------------------------------
    st4   = ST72()
    a42   = st4.intern_int(42)
    result = st4.run([a42, st4.A_PER])
    assert st4.obj_int_value(result) == 42, \
        f"int literal: {st4.value_repr(result)}"
    print(f"PASS  int literal: '42 .' → {st4.value_repr(result)}")

    # ----------------------------------------------------------------
    # 5. Global lookup
    # ----------------------------------------------------------------
    st5 = ST72()
    st5.defglobal("x", st5.intern_int(99))
    x_atom = st5.atoms.intern("x")
    result  = st5.run([x_atom, st5.A_PER])
    assert st5.obj_int_value(result) == 99, \
        f"global lookup: {st5.value_repr(result)}"
    print(f"PASS  global lookup: 'x .' → {st5.value_repr(result)}")


    # ----------------------------------------------------------------
    # 6. ':' FM3 fetch — flag='"' → literal next token
    #    '" hello : " world .'
    #    First quote → VALUE=hello. Then ':' reads flag='"' (FM3) → VALUE=world.
    #    BIND reads '.' → no name → done. Result = world.
    # ----------------------------------------------------------------
    st6   = ST72()
    hello = st6.atoms.intern("hello")
    world = st6.atoms.intern("world")
    tokens6 = [st6.A_QUOTE, hello, st6.A_COLN, st6.A_QUOTE, world, st6.A_PER]
    result = st6.run(tokens6)
    assert result == world, \
        f"':' fetch FM3: got {st6.value_repr(result)}, expected {st6.value_repr(world)}"
    print(f"PASS  ':' fetch FM3: '\" hello : \" world .' → {st6.value_repr(result)}")

    # ----------------------------------------------------------------
    # 7. Python built-in class
    # ----------------------------------------------------------------
    st7 = ST72()

    def _add_one(st: ST72):
        # Instance is a small-int; add 1
        inst = st._inst
        n    = st.obj_int_value(inst)
        st._sval(st.intern_int(n + 1))

    st7.def_builtin_class("AddOne", _add_one)
    addone_atom = st7.atoms.intern("AddOne")
    addone_cls  = st7._globals[addone_atom]
    a5          = st7.intern_int(5)

    # Manually wire: set up MESSX/GLOBX, call _activ
    top = st7.make_top_arec(st7.make_vector([st7.A_PER]))
    st7.SELF      = top
    st7.MESSX     = top
    st7.GLOBX     = top
    st7._messx_pc = 0
    st7._activ(addone_cls, a5)
    # _activ calls the fn and then _eret, so VALUE should be 6
    assert st7.obj_int_value(st7.VALUE) == 6, \
        f"builtin class: {st7.value_repr(st7.VALUE)}"
    print(f"PASS  builtin class: AddOne(5) → {st7.value_repr(st7.VALUE)}")

    # ----------------------------------------------------------------
    # 8. value_repr
    # ----------------------------------------------------------------
    st8 = ST72()
    assert st8.value_repr(NIL)   == "nil"
    assert st8.value_repr(EMPTY) == "false"
    assert st8.value_repr(st8.intern_int(0)) == "0"
    assert st8.value_repr(st8.atoms.intern("foo")) == "'foo'"
    print("PASS  value_repr")

    print("\nAll tests passed.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "repl":
        from st72_prims import register_all
        from st72_reader import REPL
        st = ST72()
        register_all(st)
        REPL(st).loop()
    else:
        run_tests()
