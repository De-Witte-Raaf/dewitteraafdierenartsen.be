"""Minify the CSS inside <style> tags of every built HTML page in _site/.

Runs after `jekyll build`. Only whitespace/comment collapsing is performed
(removes comments and collapses runs of whitespace to a single space), which
is safe for any valid CSS and nearly as compact as full token-based minifying.

Usage: python3 scripts/minify-inline-css.py [site_root]
"""

import re
import sys
from pathlib import Path

STYLE_RE = re.compile(r"(<style(?:\s[^>]*)?>)(.*?)(</style>)", re.DOTALL)
COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
WS_RE = re.compile(r"\s+")

def minify_css(css: str) -> str:
    """Collapse CSS to a single line: drop comments and squeeze whitespace."""
    out = COMMENT_RE.sub(" ", css)
    out = WS_RE.sub(" ", out)
    return out.strip()

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