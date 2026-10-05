#!/usr/bin/env python3
"""Export the slides to a PDF with headless Chromium (1280x720, six pages).

    python3 scripts/export_slides.py                 # English, Spanish (es-LA) and Portuguese (pt-BR)
    python3 scripts/export_slides.py --lang es-la    # one language

The PDFs are site/slides/sentinel-slides.pdf, sentinel-slides.es-la.pdf and sentinel-slides.pt-br.pdf.

The PDF is gitignored (*.pdf). Build it before you submit.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
LANGS = {"en": "", "es-la": "es-la", "pt-br": "pt-br"}


def chromium() -> str:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("No Chromium or Chrome found in PATH.")


def export(lang: str, out: Path | None = None) -> Path:
    deck = SITE / LANGS[lang] / "slides" / "deck.html"
    suffix = "" if lang == "en" else f".{lang}"
    out = (out or SITE / "slides" / f"sentinel-slides{suffix}.pdf").resolve()
    subprocess.run(
        [
            chromium(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={out}", deck.as_uri(),
        ],
        check=True, capture_output=True,
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=sorted(LANGS), help="one language; default: all three")
    parser.add_argument("--out", help="output file (needs --lang)")
    args = parser.parse_args()
    if args.out and not args.lang:
        parser.error("--out needs --lang")
    for lang in [args.lang] if args.lang else sorted(LANGS):
        out = export(lang, Path(args.out) if args.out else None)
        data = out.read_bytes()
        pages = data.count(b"/Type /Page\n") or data.count(b"/Type/Page")
        print(f"wrote {out} ({pages or 'unknown'} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
