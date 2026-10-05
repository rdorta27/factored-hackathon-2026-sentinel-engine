#!/usr/bin/env python3
"""Find text that leaves its box, on every page of the site in every language.

    python3 scripts/audit_overflow.py            # print the findings, exit 1 if any
    python3 scripts/audit_overflow.py --lang es-la --page diagrams/architecture.html

It checks HTML boxes (a child wider than its parent, a box with clipped text),
SVG labels (a text wider than its node) and slides (content below or beside the
1280x720 frame). It needs Playwright and Chromium.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import localize as lz  # noqa: E402

SITE = lz.SITE
LANGS = ["en", "es-la", "pt-br"]

JS = r"""
() => {
  const out = [];
  const tol = 1.5;
  const name = (e) => (e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).join('.') : '')).slice(0, 70);
  const txt = (e) => (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60);
  const scroller = (e) => { for (let p = e; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
  // 1. Clipped or overflowing HTML boxes.
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('svg') || e.closest('.hud')) continue;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (e.scrollWidth > e.clientWidth + tol && e.clientWidth > 0 && cs.display !== 'inline' && !scroller(e)) {
      out.push(['wider-than-box', name(e), txt(e), e.scrollWidth + ' > ' + e.clientWidth]);
    }
    const p = e.parentElement;
    if (p && p !== document.body && !scroller(e)) {
      const r = e.getBoundingClientRect(), pr = p.getBoundingClientRect();
      if (r.width > 0 && r.right > pr.right + tol && getComputedStyle(p).display !== 'inline' && !p.closest('.slide')) {
        out.push(['child-past-parent', name(e), txt(e), Math.round(r.right) + ' > ' + Math.round(pr.right)]);
      }
    }
  }
  // 2. SVG labels wider than their node, or over the badge.
  for (const g of document.querySelectorAll('svg g.node')) {
    const box = g.querySelector('rect.box'); if (!box) continue;
    const w = box.getBBox().width;
    const chip = g.querySelector('circle.chip');
    const chipLeft = chip ? parseFloat(chip.getAttribute('cx')) - parseFloat(chip.getAttribute('r')) : w;
    for (const t of g.querySelectorAll('text')) {
      if (t.classList.contains('chipt')) continue;
      const b = t.getBBox();
      const limit = t.classList.contains('t1') ? chipLeft - 3 : w - 6;
      if (b.x + b.width > limit + 0.5) out.push(['svg-text-wide', name(g), (t.textContent || '').slice(0, 50), Math.round(b.x + b.width) + ' > ' + Math.round(limit)]);
    }
  }
  // 2b. Arrow labels that run into a node.
  for (const svg of document.querySelectorAll('svg')) {
    const nodes = [...svg.querySelectorAll('g.node')].map((g) => {
      const m = /translate\(([\d.]+),\s*([\d.]+)\)/.exec(g.getAttribute('transform') || '');
      const b = g.querySelector('rect.box'); if (!m || !b) return null;
      return { x: +m[1], y: +m[2], w: b.getBBox().width, h: b.getBBox().height };
    }).filter(Boolean);
    for (const t of svg.querySelectorAll('text.elabel')) {
      const b = t.getBBox();
      for (const n of nodes) {
        if (b.x < n.x + n.w && b.x + b.width > n.x && b.y < n.y + n.h && b.y + b.height > n.y) {
          out.push(['label-over-node', 'text.elabel', (t.textContent || '').slice(0, 40), Math.round(b.width) + 'px wide']); break;
        }
      }
    }
  }
  // 3. Slides: any line of text past the frame.
  for (const s of document.querySelectorAll('.slide')) {
    const sr = s.getBoundingClientRect();
    const walker = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.textContent.trim()) continue;
      const el = n.parentElement;
      if (getComputedStyle(el).display === 'none') continue;
      const range = document.createRange(); range.selectNodeContents(n);
      const r = range.getBoundingClientRect();
      if (r.height && (r.bottom > sr.bottom - 8 || r.right > sr.right - 8)) {
        out.push(['slide-overflow', s.id + ' ' + name(el), n.textContent.trim().slice(0, 50), Math.round(r.bottom - sr.top) + 'px']);
      }
    }
  }
  return out;
}
"""


def chromium() -> str:
    for n in ("chromium", "chromium-browser", "google-chrome"):
        if shutil.which(n):
            return shutil.which(n)
    raise SystemExit("No Chromium found")


def audit(langs=LANGS, only=None) -> list[str]:
    from playwright.sync_api import sync_playwright

    findings: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium(), args=["--no-sandbox"])
        for lang in langs:
            for page in lz.sources():
                if only and page != only:
                    continue
                path = SITE / page if lang == "en" else SITE / lang / page
                widths = [1280] if page.startswith("slides/") else [1280, 390]
                for width in widths:
                    pg = browser.new_page(viewport={"width": width, "height": 800})
                    pg.goto(path.as_uri())
                    if page.startswith("slides/"):
                        pg.add_style_tag(content=".js .slide{display:flex!important;position:relative!important;left:0!important;top:0!important;transform:none!important;margin:0 0 24px!important}.js html,.js body{overflow:auto!important}.js .deck{position:static!important}")
                    for kind, el, text, detail in pg.evaluate(JS):
                        findings.append(f"{lang:6} {width:4} {page:28} {kind:16} {el} | {text} | {detail}")
                    pg.close()
        browser.close()
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=LANGS)
    parser.add_argument("--page")
    args = parser.parse_args()
    findings = audit([args.lang] if args.lang else LANGS, args.page)
    for f in findings:
        print(f)
    print(f"{len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
