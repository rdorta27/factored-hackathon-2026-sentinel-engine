#!/usr/bin/env python3
"""Report style findings in the Markdown pages under `docs/` and `team/`.

The script reads the Markdown pages that Git tracks under `docs/` and `team/`.
For each page it reports:

- the header status and the `last_reviewed` date of the ASD-STE100 frontmatter
- each sentence longer than 25 words
- each likely passive verb
- each bare locale tag (`ES`, `PT`)
- each synonym of an agreed term (handoff, cut-off, held-out, baseline,
  simulation, mock)

The script changes nothing. It skips the frontmatter, the fenced code blocks,
the inline code and the target of a link. It skips the table rows for the
sentence check, because a table cell is a fragment, not a sentence.

Run from anywhere in the repository:
    python3 scripts/check_docs.py
Exit code: 0 always. The report is the output.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = "style: ASD-STE100"
MAX_WORDS = 25

# One agreed term, one concept. The value holds the synonyms to report.
# The source is AGENTS.md and docs/glossary/glossary.en-us.md.
AGREED_TERMS: dict[str, tuple[str, ...]] = {
    "handoff": ("hand-off", "handover", "hand-over", "transfer", "escalation", "escalate"),
    "cut-off": ("cutoff", "cut off"),
    "held-out": ("holdout", "hold-out", "hold out"),
    "baseline": ("benchmark", "control group", "reference point"),
    "simulation": ("dry run", "practice run"),
    "mock": ("stub", "dummy", "fake", "stand-in"),
}

IRREGULAR_PARTICIPLES = (
    "written", "made", "given", "shown", "taken", "done", "sent", "read", "kept",
    "held", "built", "set", "run", "led", "found", "known", "seen", "left",
    "brought", "thought", "put", "cut", "chosen", "drawn", "shown",
)
BE_VERB = r"(?:is|are|was|were|be|been|being|am)"
PARTICIPLE = r"(?:\w+ed|" + "|".join(IRREGULAR_PARTICIPLES) + r")"
PASSIVE = re.compile(rf"\b{BE_VERB}\s+(?:\w+\s+)?{PARTICIPLE}\b", re.IGNORECASE)
LOCALE = re.compile(r"(?<![A-Za-z0-9-])(ES|PT)(?![A-Za-z0-9-])")
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
DATE = re.compile(r"^last_reviewed:\s*(\S+)\s*$", re.MULTILINE)


def pages() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "docs", "team"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    names = [n for n in result.stdout.splitlines() if n.endswith(".md")]
    return [ROOT / n for n in sorted(set(names)) if (ROOT / n).is_file()]


def frontmatter(text: str) -> tuple[bool, str | None]:
    match = FRONTMATTER.match(text)
    if not match:
        return False, None
    block = match.group(1)
    if HEADER not in block:
        return False, None
    date = DATE.search(block)
    return True, date.group(1) if date else None


def prose(text: str) -> list[tuple[int, str]]:
    """Return the lines that hold prose, without the code and the link targets."""
    body = FRONTMATTER.sub("", text)
    result: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(body.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        clean = LINK_TARGET.sub("]", INLINE_CODE.sub("", line))
        result.append((number, clean))
    return result


def long_sentences(lines: list[tuple[int, str]]) -> list[tuple[int, str, int]]:
    found: list[tuple[int, str, int]] = []
    for number, line in lines:
        if line.lstrip().startswith(("|", "#", ">", "<!--")):
            continue
        stripped = re.sub(r"^\s*[-*+]\s+", "", line)
        for sentence in SENTENCE_END.split(stripped.strip()):
            words = WORD.findall(sentence)
            if len(words) > MAX_WORDS:
                found.append((number, " ".join(words), len(words)))
    return found


def passives(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for number, line in lines:
        for match in PASSIVE.finditer(line):
            found.append((number, match.group(0)))
    return found


def bare_locales(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for number, line in lines:
        for match in LOCALE.finditer(line):
            found.append((number, match.group(1)))
    return found


def synonyms(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for number, line in lines:
        low = line.lower()
        for term, alternatives in AGREED_TERMS.items():
            for alternative in alternatives:
                if re.search(rf"\b{re.escape(alternative)}\b", low):
                    found.append((number, f"'{alternative}' for '{term}'"))
    return found


def analyze(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    has_header, reviewed = frontmatter(text)
    lines = prose(text)
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        name = path.as_posix()
    return {
        "path": name,
        "header": has_header,
        "reviewed": reviewed,
        "long": long_sentences(lines),
        "passive": passives(lines),
        "locale": bare_locales(lines),
        "synonym": synonyms(lines),
    }


def report(findings: list[dict[str, object]]) -> dict[str, int]:
    counts = {"pages": len(findings), "header": 0, "long": 0, "passive": 0, "locale": 0, "synonym": 0}
    for page in findings:
        if page["header"]:
            counts["header"] += 1
        else:
            print(f"{page['path']}: no ASD-STE100 header")
        for kind in ("long", "passive", "locale", "synonym"):
            hits = page[kind]
            counts[kind] += len(hits)
            for hit in hits:
                print(f"{page['path']}:{hit[0]}: {kind}: {hit[1]}")
    print(
        "summary: {pages} pages, {header} with the header, {long} long sentence(s), "
        "{passive} likely passive(s), {locale} bare locale tag(s), {synonym} synonym(s)".format(**counts)
    )
    return counts


def main() -> int:
    report([analyze(path) for path in pages()])
    return 0


if __name__ == "__main__":
    sys.exit(main())
