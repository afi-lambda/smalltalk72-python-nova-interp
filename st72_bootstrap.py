from __future__ import annotations

from pathlib import Path

from st72_reader import Reader

_SKIP_NAMES = {
    "substr", "leech", "mouse", "kbd", "TTY",
    "disp", "stream", "dispframe", "newchars", "type", "fix", "shocode",
    "junta", "index", "tablscan", "kbck",
    "dclear", "dcomp", "dmove", "dmovec", "go", "goto", "turn",
}

def _iter_to_heads(text: str):
    """Yield (head, paren_index) for lines starting with `to ...(`."""
    i, n = 0, len(text)
    while i < n:
        j = text.find("\n", i)
        if j < 0:
            j = n
        line = text[i:j]
        stripped = line.lstrip()
        if stripped.startswith("to "):
            rel = line.find("to")
            to_start = i + rel
            head_start = to_start + 3
            paren = text.find("(", head_start, j)
            if paren != -1:
                head = " ".join(text[head_start:paren].split())
                if head:
                    yield head, paren
        i = j + 1


def _extract_balanced(text: str, start: int) -> tuple[str | None, int]:
    if start >= len(text) or text[start] != "(":
        return None, start
    i, depth, in_quote = start, 0, False
    while i < len(text):
        c = text[i]
        if in_quote:
            if c == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    i += 2
                    continue
                in_quote = False
        else:
            if c == "'":
                in_quote = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1], i + 1
        i += 1
    return None, start


def load_alldefs_kernel(st, path: str, *, strict: bool = False) -> dict:
    text = Path(path).read_text(encoding="latin-1", errors="replace")
    r = Reader(st)
    stats = {"loaded": 0, "skipped_code": 0, "skipped_unsupported": 0, "failed": 0}

    for head, paren_idx in _iter_to_heads(text):
        if not head:
            continue
        name = head.split()[0]
        body, _ = _extract_balanced(text, paren_idx)
        if not body:
            stats["failed"] += 1
            if strict:
                raise ValueError(f"Malformed to-definition for {name}")
            continue
        if "CODE" in body.upper():
            stats["skipped_code"] += 1
            continue
        if name in _SKIP_NAMES:
            stats["skipped_unsupported"] += 1
            continue

        src = f"to {head} {body} ."
        try:
            r.run(src)
            stats["loaded"] += 1
        except Exception:
            stats["failed"] += 1
            if strict:
                raise
    return stats
