#!/usr/bin/env python3
"""Compare the cited requirement status in the specs with the requirements index.

Each spec cites a requirement as `REQ-0001 (P0, Done)`. The source of truth is
the status table in `docs/requirements/requirements.md`. The script prints each
citation that differs and exits with 1. With `--fix` it rewrites the citations.

Run from the repository root:
    python3 scripts/check_spec_citations.py [--fix] [--specs openspec/specs]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "requirements" / "requirements.md"

ROW = re.compile(
    r"^\|\s*\[(REQ-\d{4})\]\([^)]*\)\s*\|[^|]*\|\s*(P\d)\s*\|[^|]*\|[^|]*\|\s*([A-Za-z][A-Za-z ]*?)\s*\|\s*$"
)
# A citation can wrap across two lines, so the gaps allow any whitespace.
CITATION = re.compile(r"(REQ-\d{4})(\s*\()(P\d)(,\s*)([A-Za-z][A-Za-z\s]*?)(\))")


def read_index() -> dict[str, tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if match:
            index[match.group(1)] = (match.group(2), match.group(3))
    return index


def check(spec_dir: Path, index: dict[str, tuple[str, str]], fix: bool) -> list[str]:
    problems: list[str] = []
    for path in sorted(spec_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            req, open_, priority, comma, status, close = match.groups()
            if req not in index:
                problems.append(f"{path.relative_to(ROOT)}: {req} is not in the index")
                return match.group(0)
            want_priority, want_status = index[req]
            if (priority, " ".join(status.split())) == (want_priority, want_status):
                return match.group(0)
            line = text.count("\n", 0, match.start()) + 1
            problems.append(
                f"{path.relative_to(ROOT)}:{line}: {req} cites ({priority}, {' '.join(status.split())}), "
                f"the index says ({want_priority}, {want_status})"
            )
            return f"{req}{open_}{want_priority}{comma}{want_status}{close}"

        updated = CITATION.sub(replace, text)
        if fix and updated != text:
            path.write_text(updated, encoding="utf-8")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--specs", type=Path, default=ROOT / "openspec" / "specs")
    parser.add_argument("--fix", action="store_true", help="rewrite the citations that differ")
    args = parser.parse_args()

    index = read_index()
    if not index:
        print(f"no requirement rows found in {INDEX.relative_to(ROOT)}", file=sys.stderr)
        return 2
    problems = check(args.specs, index, args.fix)
    for problem in problems:
        print(problem)
    if problems:
        verb = "fixed" if args.fix else "differ"
        print(f"{len(problems)} citation(s) {verb}")
        return 0 if args.fix else 1
    print("no difference")
    return 0


if __name__ == "__main__":
    sys.exit(main())
