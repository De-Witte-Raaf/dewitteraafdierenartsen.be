"""Minify the CSS inside <style> tags of every built HTML page in _site/.

Runs after `jekyll build`. A small tokenizing minifier (no external deps):

- strips comments
- collapses runs of whitespace to a single space
- removes structural whitespace (after `{ ( ; ,`, before `} ) ; ,`, between a
  selector and its `{`, between sibling rules)
- drops the final `;` before a closing `}`

Deliberately conservative: it never removes whitespace around `:` (which is
meaningful in selectors like `.a :hover`), around descendant/combinator
spaces, or around `+`/`-` inside calc() expressions, and it never touches
string literals or url() payloads.

Usage: python3 scripts/minify-inline-css.py [site_root]
"""

import re
import sys
from pathlib import Path

STYLE_RE = re.compile(r"(<style(?:\s[^>]*)?>)(.*?)(</style>)", re.DOTALL)

_WS = " \t\r\n\f"


def minify_css(css: str) -> str:
    out = []
    i, n = 0, len(css)
    prev = None  # last emitted significant char
    pending_space = False
    while i < n:
        c = css[i]
        # comment -> acts as whitespace between tokens
        if c == "/" and i + 1 < n and css[i + 1] == "*":
            end = css.find("*/", i + 2)
            i = (end + 2) if end != -1 else n
            if prev is not None:
                pending_space = True
            continue
        # string literal -> copy verbatim, no minification inside
        if c in ('"', "'"):
            if pending_space and should_emit_space(prev, c):
                out.append(" ")
            j = i + 1
            while j < n:
                if css[j] == "\\":
                    j += 2
                    continue
                if css[j] == c:
                    j += 1
                    break
                j += 1
            out.append(css[i:j])
            prev = css[j - 1]
            i = j
            pending_space = False
            continue
        if c in _WS:
            if prev is not None:
                pending_space = True
            i += 1
            continue
        if pending_space and prev is not None and should_emit_space(prev, c):
            out.append(" ")
        # drop a ';' that is the last declaration in its block
        if c == ";" and decl_tail(css, i + 1):
            pending_space = False
            i += 1
            continue
        out.append(c)
        prev = c
        i += 1
        pending_space = False
    return "".join(out)


def should_emit_space(prev: str, cur: str) -> bool:
    """Structural whitespace is removable; semantic whitespace is kept."""
    # after an opening { or ( or after ; or , between declarations/selectors
    if prev in "{(;,":
        return False
    # before a closing } or ) or before ; or , or before the { that opens a block
    if cur in "{});,":
        return False
    return True


def decl_tail(css: str, i: int) -> bool:
    """True if the ';' at i-1 is followed only by space/comment before '}'."""
    n = len(css)
    while i < n:
        c = css[i]
        if c in _WS:
            i += 1
            continue
        if c == "/" and i + 1 < n and css[i + 1] == "*":
            end = css.find("*/", i + 2)
            i = (end + 2) if end != -1 else n
            continue
        if c in ('"', "'"):  # skip string literals (may contain } or ;)
            i += 1
            while i < n:
                if css[i] == "\\":
                    i += 2
                    continue
                if css[i] == c:
                    i += 1
                    break
                i += 1
            continue
        return c == "}"
    return False

def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    changed = STYLE_RE.sub(
        lambda m: m.group(1) + minify_css(m.group(2)) + m.group(3),
        original,
    )
    if changed != original:
        path.write_text(changed, encoding="utf-8")
        return True
    return False

def main() -> int:
    site_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_site")
    files = list(site_root.rglob("*.html"))
    changed = [f for f in files if process_file(f)]
    print(f"minify-inline-css: {len(files)} HTML files scanned, {len(changed)} updated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())