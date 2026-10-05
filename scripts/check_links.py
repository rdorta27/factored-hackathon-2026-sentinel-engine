#!/usr/bin/env python3
"""Check that each relative link in the Markdown files points to a file or folder.

The script reads the Markdown files that Git tracks (and the new files that Git
does not ignore). It skips `openspec/changes/archive/`, because archived
changes are history. It skips links inside code blocks and inline code, web
links, `mailto:` links and links to an anchor on the same page. It checks the
path only, not the anchor.

Run from anywhere in the repository:
    python3 scripts/check_links.py
Exit code: 0 when no link is broken, 1 otherwise.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP_PREFIX = "openspec/changes/archive/"

LINK = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
REFERENCE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
EXTERNAL = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")


def markdown_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    names = [n for n in result.stdout.splitlines() if n and not n.startswith(SKIP_PREFIX)]
    return [ROOT / n for n in sorted(set(names)) if (ROOT / n).is_file()]


def targets(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        plain = INLINE_CODE.sub("", line)
        for match in LINK.finditer(plain):
            found.append((number, match.group(1)))
        reference = REFERENCE.match(plain)
        if reference:
            found.append((number, reference.group(1)))
    return found


def broken_links(path: Path) -> list[str]:
    problems: list[str] = []
    for number, raw in targets(path.read_text(encoding="utf-8")):
        target = raw.strip("<>")
        if not target or target.startswith("#") or EXTERNAL.match(target):
            continue
        location = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not location:
            continue
        base = ROOT if location.startswith("/") else path.parent
        resolved = (base / location.lstrip("/")).resolve()
        if not resolved.exists():
            problems.append(f"{path.relative_to(ROOT)}:{number}: broken link {raw}")
    return problems


def main() -> int:
    problems: list[str] = []
    for path in markdown_files():
        problems.extend(broken_links(path))
    for problem in problems:
        print(problem)
    if problems:
        print(f"{len(problems)} broken link(s)")
        return 1
    print("no broken link")
    return 0


if __name__ == "__main__":
    sys.exit(main())
