#!/usr/bin/env python3
"""Export site/slides/deck.html to a PDF with headless Chromium (1280x720, six pages).

    python3 scripts/export_slides.py [--out site/slides/sentinel-slides.pdf]

The PDF is gitignored (*.pdf). Build it before you submit.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "site" / "slides" / "deck.html"


def chromium() -> str:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("No Chromium or Chrome found in PATH.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "site" / "slides" / "sentinel-slides.pdf"))
    args = parser.parse_args()
    out = Path(args.out).resolve()
    subprocess.run(
        [
            chromium(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={out}", DECK.as_uri(),
        ],
        check=True, capture_output=True,
    )
    pages = out.read_bytes().count(b"/Type /Page\n") or out.read_bytes().count(b"/Type/Page")
    print(f"wrote {out} ({pages or 'unknown'} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
