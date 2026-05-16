"""
st72_reader.py — Smalltalk-72 source reader / tokenizer.

Based on READ.SR (deduced from SMALL.SYMS exports) and the HOPL paper.

ST72 syntax rules:
  - Tokens are separated by whitespace.
  - Special single-character tokens: . : ? " % ! # _ [ ]
  - Integers: optional sign, digits.
  - Strings: delimited by single quotes '' (doubled ' is escape).
  - Comments: not in ST72 source; we skip nothing special.
  - '[' ... ']' delimit a sub-expression list (compiled into a vector).
  - Atom hashes: in the real system each atom is hashed to an octal number.
    In our Python implementation atoms are interned by name directly.

The reader produces a list of token addresses (ints) suitable for
passing to ST72.run().

Sub-expressions ([ ... ]) are compiled into message vectors recursively.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from st72 import ST72


class Reader:
    """
    ST72 source reader.
    Converts a source string into a list of token addresses.
    """

    # Characters that are always single tokens
    SPECIALS = set('.:?"%!#_')

    def __init__(self, st: 'ST72'):
        self.st  = st
        self.src  = ""
        self.pos  = 0

    # ------------------------------------------------------------------
    # Top-level entry
    # ------------------------------------------------------------------

    def read_str(self, src: str) -> list[int]:
        """
        Tokenize source string.
        Returns list of token addresses (ints).
        Sub-expressions [ ... ] are compiled into vector addresses.
        """
        self.src = src
        self.pos = 0
        tokens = self._read_list(terminator=None)
        return tokens

    def read_expr(self, src: str) -> list[int]:
        """
        Read one top-level expression (terminated by '.').
        Returns token list including the final '.'.
        """
        self.src = src
        self.pos = 0
        tokens = self._read_list(terminator=None)
        if not tokens or tokens[-1] != self.st.A_PER:
            tokens.append(self.st.A_PER)
        return tokens

    # ------------------------------------------------------------------
    # Internal reader
    # ------------------------------------------------------------------

    def _read_list(self, terminator: str | None) -> list[int]:
        """
        Read tokens until terminator (']') or end of input.
        If terminator is ']', stop and consume it.
        Returns list of token addresses.
        Sub-expressions are compiled into inline vectors.
        """
        st     = self.st
        result = []

        while self.pos < len(self.src):
            self._skip_whitespace()
            if self.pos >= len(self.src):
                break

            ch = self.src[self.pos]

            # End of sub-expression
            if ch == ']':
                if terminator == ']':
                    self.pos += 1
                break

            # Start of sub-expression: compile into vector
            if ch == '[':
                self.pos += 1
                sub = self._read_list(terminator=']')
                vec = st.make_vector(sub)
                result.append(vec)
                continue

            # Single-character special tokens
            if ch in self.SPECIALS:
                self.pos += 1
                result.append(self._intern_special(ch))
                continue

            # String literal: 'text'
            if ch == "'":
                s = self._read_string()
                result.append(self._intern_string(s))
                continue

            # Word token (atom or integer)
            word = self._read_word()
            result.append(self._intern_word(word))

        return result

    def _skip_whitespace(self):
        while self.pos < len(self.src) and self.src[self.pos] in ' \t\n\r':
            self.pos += 1

    def _intern_special(self, ch: str) -> int:
        st = self.st
        mapping = {
            '.':  st.A_PER,
            ':':  st.A_COLN,
            '?':  st.A_QUEST,
            '"':  st.A_QUOTE,
            '%':  st.A_MACH,
            '!':  st.A_BANG,
            '#':  st.A_NOEV,
            '_':  st.A_ARROW,
        }
        return mapping.get(ch, st.atoms.intern(ch))

    def _read_word(self) -> str:
        """Read a whitespace/special-delimited word."""
        start = self.pos
        while self.pos < len(self.src):
            ch = self.src[self.pos]
            if ch in ' \t\n\r[]' or ch in self.SPECIALS:
                break
            self.pos += 1
        return self.src[start:self.pos]

    def _read_string(self) -> str:
        """Read a single-quoted string. '' inside is an escaped '."""
        self.pos += 1   # consume opening '
        chars = []
        while self.pos < len(self.src):
            ch = self.src[self.pos]
            if ch == "'":
                self.pos += 1
                if self.pos < len(self.src) and self.src[self.pos] == "'":
                    chars.append("'")
                    self.pos += 1
                else:
                    break   # end of string
            else:
                chars.append(ch)
                self.pos += 1
        return ''.join(chars)

    def _intern_string(self, s: str) -> int:
        """
        Intern a string literal.
        In ST72 strings are atom-like objects; here we intern as an atom.
        """
        return self.st.atoms.intern(s)

    def _intern_word(self, word: str) -> int:
        """Intern a word as an integer or atom."""
        st = self.st
        # Try integer
        try:
            n = int(word)
            return st.intern_int(n)
        except ValueError:
            pass
        # Try negative integer with leading minus
        if word.startswith('-') and len(word) > 1:
            try:
                n = int(word)
                return st.intern_int(n)
            except ValueError:
                pass
        # Atom
        return st.atoms.intern(word)

    # ------------------------------------------------------------------
    # Convenience: tokenize + run
    # ------------------------------------------------------------------

    def run(self, source: str, max_steps: int = 100_000) -> int:
        """Tokenize source and run it on the ST72 machine."""
        tokens = self.read_expr(source)
        return self.st.run(tokens, max_steps)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

def make_repl(st: 'ST72') -> 'REPL':
    return REPL(st)


class REPL:
    """Interactive Smalltalk-72 read-eval-print loop."""

    def __init__(self, st: 'ST72'):
        self.st     = st
        self.reader = Reader(st)
        self._setup_display()

    def _setup_display(self):
        """Register a 'print' primitive for output."""
        def _print(st: 'ST72'):
            inst = st._inst
            print(f"  {st.value_repr(inst)}", end='')
            st._sval(inst)
            st._eret()

        # 'print' outputs to stdout
        print_atom = self.st.atoms.intern("print")
        print_cls  = self.st.def_builtin_class("print", _print)

        # 'cr' outputs a newline
        def _cr(st: 'ST72'):
            print()
            st._sval(st._inst)
            st._eret()
        self.st.def_builtin_class("cr", _cr)

        # 'show' prints and cr
        def _show(st: 'ST72'):
            inst = st._inst
            print(st.value_repr(inst))
            st._sval(inst)
            st._eret()
        self.st.def_builtin_class("show", _show)

    def run_line(self, line: str) -> tuple[int, str]:
        """Run one line. Returns (value_addr, repr_str)."""
        tokens = self.reader.read_expr(line)
        result = self.st.run(tokens)
        return result, self.st.value_repr(result)

    def loop(self):
        """Run an interactive REPL."""
        st = self.st
        print("Smalltalk-72  (quit or q pour sortir)")
        print(f"  mem={st.mem.size} words, atoms={st.atoms._next-1}, "
              f"heap top={oct(st.BHMEM)}")
        print()
        buf = []
        while True:
            prompt = "st72> " if not buf else "  ... "
            try:
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if line.strip() in ("quit", "exit", "q"):
                break
            if not line.strip():
                if buf:
                    line = ' '.join(buf)
                    buf  = []
                else:
                    continue
            else:
                # Accumulate until we see a '.'
                buf.append(line)
                if '.' not in line:
                    continue
                line = ' '.join(buf)
                buf  = []

            try:
                result, rep = self.run_line(line)
                print(f"  → {rep}")
            except NameError as e:
                print(f"  ERROR: {e}")
            except RuntimeError as e:
                print(f"  ERROR: {e}")
            except Exception as e:
                print(f"  ERROR ({type(e).__name__}): {e}")
