#!/usr/bin/env python3
"""Build the architecture drawing from one source, site/diagrams/architecture.json.

Outputs:
  site/diagrams/architecture.svg   static drawing (demo view), for slides, README and video
  site/diagrams/architecture.html  interactive page (inline SVG + architecture.js)

    python3 scripts/build_architecture.py          # write both files
    python3 scripts/build_architecture.py --check  # exit 1 if a file is stale
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import site_numbers as sn  # noqa: E402

ROOT = sn.ROOT
DIR = ROOT / "site" / "diagrams"
SRC = DIR / "architecture.json"
SVG = DIR / "architecture.svg"
PAGE = DIR / "architecture.html"

STATUS = {"real": "Real", "mock": "Mock", "synthetic": "Synthetic"}
DECIDES = {"model": ("M", "Model labels"), "code": ("C", "Code decides"), "person": ("P", "Person decides")}

STYLE = """
svg.arch{--bg:#faf8f5;--t:#1c1830;--mu:#4a4460;--card:#fff;--line:#cfc8de;--real:#1b6a49;--real-bg:#e5f4ec;--mock:#8a4a0b;--mock-bg:#fdeedd;--prod:#3a1fb8;--prod-bg:#f1edff;--model:#e23e78;--code:#4f2fe0}
@media (prefers-color-scheme:dark){svg.arch{--bg:#14112a;--t:#f1eefb;--mu:#b9b3d0;--card:#1e1a38;--line:#4a4378;--real:#7fd9ae;--real-bg:#173a2c;--mock:#f3b46e;--mock-bg:#3d2a10;--prod:#c4b8ff;--prod-bg:#2a2350;--model:#ff7aa6;--code:#8e78ff}}
svg.arch .bg{fill:var(--bg)}
svg.arch text{font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;fill:var(--t)}
svg.arch .box{fill:var(--card);stroke:var(--line);stroke-width:1.5}
svg.arch .node.real .box{stroke:var(--real)}
svg.arch .node.mock .box{stroke:var(--mock);stroke-dasharray:6 3}
svg.arch .node.prod .box{stroke:var(--prod);stroke-dasharray:none}
svg.arch .node.changed .box{stroke-width:3}
svg.arch .node{cursor:pointer}
svg.arch .node:focus{outline:none}
svg.arch .node:focus-visible .box,svg.arch .node.sel .box{stroke:var(--model);stroke-width:3.5}
svg.arch .t1{font-size:15px;font-weight:700}
svg.arch .t2{font-size:12px;font-weight:700}
svg.arch .real .t2{fill:var(--real)}
svg.arch .mock .t2{fill:var(--mock)}
svg.arch .prod .t2{fill:var(--prod)}
svg.arch .t3{font-size:12px;fill:var(--mu)}
svg.arch .chip.model{fill:var(--model)}
svg.arch .chip.code{fill:var(--code)}
svg.arch .chip.person{fill:var(--mock)}
svg.arch .chipt{font-size:11px;font-weight:700;fill:#fff}
svg.arch .edge{stroke:var(--mu);stroke-width:1.6;fill:none}
svg.arch .edge.dashed{stroke-dasharray:5 4}
svg.arch .arrow{fill:var(--mu)}
svg.arch .elabel{font-size:11px;fill:var(--mu)}
svg.arch .lg{font-size:12px;fill:var(--mu)}
svg.arch .swatch{stroke-width:1.5;fill:var(--card)}
""".strip()


def load() -> dict:
    return json.loads(SRC.read_text())


def clip(cx, cy, w, h, tx, ty, gap=5):
    """Point where the line from the centre (cx,cy) toward (tx,ty) leaves the box."""
    dx, dy = tx - cx, ty - cy
    sx = (w / 2 + gap) / abs(dx) if dx else math.inf
    sy = (h / 2 + gap) / abs(dy) if dy else math.inf
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def svg_edges(data) -> str:
    w, h = data["node"]
    by = {n["id"]: n for n in data["nodes"]}
    out = []
    for e in data["edges"]:
        a, b = by[e["from"]], by[e["to"]]
        ac, bc = (a["x"] + w / 2, a["y"] + h / 2), (b["x"] + w / 2, b["y"] + h / 2)
        x1, y1 = clip(*ac, w, h, *bc)
        x2, y2 = clip(*bc, w, h, *ac)
        ang = math.atan2(y2 - y1, x2 - x1)
        ax, ay = x2 - 9 * math.cos(ang), y2 - 9 * math.sin(ang)
        px, py = -math.sin(ang) * 4.5, math.cos(ang) * 4.5
        cls = "edge dashed" if e.get("dashed") else "edge"
        out.append(f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{ax:.1f}" y2="{ay:.1f}"/>')
        out.append(
            f'<polygon class="arrow" points="{x2:.1f},{y2:.1f} {ax + px:.1f},{ay + py:.1f} {ax - px:.1f},{ay - py:.1f}"/>'
        )
        if e.get("label"):
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
            if abs(x2 - x1) > abs(y2 - y1):
                out.append(
                    f'<text class="elabel" x="{lx:.1f}" y="{ly - 6:.1f}" text-anchor="middle">{escape(e["label"])}</text>'
                )
            else:
                out.append(f'<text class="elabel" x="{lx + 7:.1f}" y="{ly + 4:.1f}">{escape(e["label"])}</text>')
    return "\n".join(out)


def svg_nodes(data, interactive: bool) -> str:
    w, h = data["node"]
    out = []
    for n in data["nodes"]:
        letter, words = DECIDES[n["decides"]]
        label = f'{n["title"]}. {STATUS[n["status"]]}. {words}.'
        attrs = (
            f' id="n-{n["id"]}" data-node="{n["id"]}" data-status="{n["status"]}"'
            f' tabindex="0" role="button" aria-label="{escape(label)}"'
            if interactive
            else ""
        )
        changed = " changed" if n["status"] == "mock" else ""
        out.append(f'<g class="node {n["status"]}{changed}" transform="translate({n["x"]},{n["y"]})"{attrs}>')
        out.append(f'<rect class="box" width="{w}" height="{h}" rx="12"/>')
        out.append(f'<text class="t1" x="14" y="27">{escape(n["title"])}</text>')
        out.append(
            f'<text class="t2" x="14" y="48" data-demo="{STATUS[n["status"]]}" data-prod="Production">'
            f'{STATUS[n["status"]]}</text>'
        )
        out.append(
            f'<text class="t3" x="14" y="65" data-demo="{escape(n["run_short"])}" data-prod="{escape(n["prod_short"])}">'
            f'{escape(n["run_short"])}</text>'
        )
        out.append(f'<circle class="chip {n["decides"]}" cx="{w - 18}" cy="18" r="10"/>')
        out.append(f'<text class="chipt" x="{w - 18}" y="22" text-anchor="middle">{letter}</text>')
        out.append("</g>")
    return "\n".join(out)


def legend(data) -> str:
    _, H = data["viewBox"]
    y = H - 40
    items = [
        (30, "real", "Real: production code or weights"),
        (300, "mock", "Mock: same contract, replaced in production"),
    ]
    out = []
    for x, cls, text in items:
        dash = ' stroke-dasharray="6 3"' if cls == "mock" else ""
        color = f"var(--{cls})"
        out.append(f'<rect class="swatch" x="{x}" y="{y}" width="26" height="16" rx="4" stroke="{color}"{dash}/>')
        out.append(f'<text class="lg" x="{x + 34}" y="{y + 13}">{text}</text>')
    for i, (key, (letter, words)) in enumerate(DECIDES.items()):
        x = 640 + i * 130
        out.append(f'<circle class="chip {key}" cx="{x}" cy="{y + 8}" r="10"/>')
        out.append(f'<text class="chipt" x="{x}" y="{y + 12}" text-anchor="middle">{letter}</text>')
        out.append(f'<text class="lg" x="{x + 16}" y="{y + 13}">{words}</text>')
    return "\n".join(out)


def svg_body(data, interactive: bool) -> str:
    return "\n".join(['<rect class="bg" width="100%" height="100%" rx="12"/>', svg_edges(data), svg_nodes(data, interactive), legend(data)])


def build_svg(data) -> str:
    W, H = data["viewBox"]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="arch" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Sentinel architecture. Demo view. Each part is marked real or mock, and as model, code or person.">\n'
        f"<style>\n{STYLE}\n</style>\n{svg_body(data, False)}\n</svg>\n"
    )


def link(path: str, repo: str) -> str:
    kind = "tree" if (ROOT / path).is_dir() else "blob"
    return f'<a href="{repo}/{kind}/main/{path}">{escape(path)}</a>'


def detail(n, repo, numbers) -> str:
    letter, words = DECIDES[n["decides"]]
    parts = [f'<article class="detail" id="d-{n["id"]}" data-for="{n["id"]}">']
    parts.append(f'<h3>{escape(n["title"])}</h3>')
    parts.append(
        f'<p class="chips"><span class="tag {"test" if n["status"] == "real" else ""}">{STATUS[n["status"]]}</span> '
        f'<span class="tag data">{words}</span></p>'
    )
    parts.append(f'<p>{escape(n["does"])}</p>')
    parts.append(
        '<dl><dt>In the demo</dt><dd>' + escape(n["runs"]) + "</dd><dt>In production</dt><dd>" + escape(n["prod"]) + "</dd></dl>"
    )
    for key in n["metrics"]:
        entry = numbers[key]
        den = ""
        if "denominator" in entry:
            den = f' of <span data-num-den="{key}">{sn.slot_text(numbers, "num-den", key)}</span>'
        parts.append(
            f'<p class="metric"><span class="tag" data-num-type="{key}">{sn.slot_text(numbers, "num-type", key)}</span> '
            f'<strong data-num="{key}">{sn.slot_text(numbers, "num", key)}</strong>{den} {escape(entry["label"])}. '
            f'<span class="src">{escape(entry["source"])} · {escape(entry["field"])}</span></p>'
        )
    parts.append("<p>Evidence: " + " · ".join(link(p, repo) for p in n["evidence"]) + "</p>")
    parts.append("</article>")
    return "\n".join(parts)


def build_page(data) -> str:
    repo = data["repo"]
    numbers = sn.build()["numbers"]
    W, H = data["viewBox"]
    nodes_nav = "\n".join(
        f'<li><button type="button" class="chipbtn" data-pick="{n["id"]}">{escape(n["title"])}</button></li>'
        for n in data["nodes"]
    )
    details = "\n".join(detail(n, repo, numbers) for n in data["nodes"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Architecture · Sentinel Engine</title>
<meta name="description" content="Interactive architecture of Sentinel. Switch between the demo and production views. Select a part to see its label, what replaces it and its evidence.">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../style.css">
<link rel="stylesheet" href="diagram.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
  <header class="top">
    <a class="logo" href="../"><img src="../favicon.svg" width="34" height="34" alt="">Sentinel</a>
    <nav aria-label="Main"><a href="../">Home</a><a href="architecture.svg">Static drawing (SVG)</a></nav>
  </header>
  <main id="main">
    <h1>How the parts fit</h1>
    <p class="lead">The model labels the intent. The code decides, acts and verifies. Select a part. Switch to the production view to see what replaces each mock.</p>

    <div class="switch" role="group" aria-label="View">
      <button type="button" class="seg on" data-view="demo" aria-pressed="true">Demo</button>
      <button type="button" class="seg" data-view="prod" aria-pressed="false">Production</button>
      <span class="note" id="view-note">The demo view shows what runs on the public link.</span>
    </div>

    <div class="scroller" tabindex="0" aria-label="Architecture drawing, scrolls sideways on a narrow screen">
<svg xmlns="http://www.w3.org/2000/svg" class="arch" id="arch" viewBox="0 0 {W} {H}" role="group" aria-label="Sentinel architecture">
<style>
{STYLE}
</style>
{svg_body(data, True)}
</svg>
    </div>

    <h2>Parts</h2>
    <ul class="picks">
{nodes_nav}
    </ul>

    <section id="detail" aria-live="polite" aria-label="Part details">
      <p class="note pick-hint">Select a part of the drawing or a button above.</p>
{details}
    </section>
    <p class="note">Labels follow <a href="{repo}/blob/main/docs/architecture/what-is-real.md">what is real</a> and <a href="{repo}/blob/main/docs/architecture/mocks.md">mocks</a>. No number in this page is a production measurement.</p>
  </main>
</div>
<script src="architecture.js"></script>
</body>
</html>
"""


CSS = """main { display: flex; flex-direction: column; gap: 18px; padding-bottom: 24px; }
.scroller { overflow-x: auto; border: 1px solid var(--line); border-radius: 16px; background: var(--card); padding: 8px; }
.scroller svg { display: block; min-width: 760px; width: 100%; height: auto; }
.switch { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 4px 0; }
.seg, .chipbtn { min-height: 44px; padding: 0 18px; border-radius: 22px; border: 1px solid var(--line); background: var(--card); color: var(--ink); font: 600 15px var(--sans); cursor: pointer; }
.seg.on { background: var(--brand); border-color: var(--brand); color: #fff; }
.chipbtn[aria-pressed="true"] { border-color: var(--brand); background: var(--tint); }
.picks { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 8px; }
.detail { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.detail + .detail { margin-top: 0; }
.detail h3 { font-size: 24px; }
.detail p, .detail dd { margin: 0; }
.detail dl { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; }
.detail dt { font-weight: 700; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.metric { padding: 10px 12px; border-radius: 10px; background: var(--bg); border: 1px solid var(--line); }
@media (max-width: 520px) { .detail dl { grid-template-columns: 1fr; } }
.js .detail { display: none; }
.js .detail.on { display: flex; }
.pick-hint { display: none; }
.js .pick-hint { display: block; }
.js .pick-hint.off { display: none; }
"""

JS = """(function () {
  var root = document.documentElement;
  root.classList.add("js");
  var svg = document.getElementById("arch");
  var nodes = svg.querySelectorAll(".node");
  var picks = document.querySelectorAll("[data-pick]");
  var details = document.querySelectorAll(".detail");
  var hint = document.querySelector(".pick-hint");
  var segs = document.querySelectorAll("[data-view]");
  var note = document.getElementById("view-note");
  var notes = {
    demo: "The demo view shows what runs on the public link.",
    prod: "The production view shows what replaces each part. A thick border marks a part that changes."
  };

  function select(id, focus) {
    nodes.forEach(function (n) { n.classList.toggle("sel", n.dataset.node === id); });
    picks.forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.pick === id ? "true" : "false"); });
    details.forEach(function (d) { d.classList.toggle("on", d.dataset["for"] === id); });
    hint.classList.add("off");
    if (focus) { document.getElementById("d-" + id).scrollIntoView({ block: "nearest" }); }
    try { history.replaceState(null, "", "#" + id); } catch (e) {}
  }

  function view(name) {
    var prod = name === "prod";
    segs.forEach(function (s) {
      var on = s.dataset.view === name;
      s.classList.toggle("on", on);
      s.setAttribute("aria-pressed", on ? "true" : "false");
    });
    nodes.forEach(function (n) {
      n.classList.toggle("prod", prod);
      n.classList.toggle("real", !prod && n.dataset.status === "real");
      n.classList.toggle("mock", !prod && n.dataset.status === "mock");
      var key = prod ? "prod" : "demo";
      n.querySelectorAll("text[data-demo]").forEach(function (t) { t.textContent = t.dataset[key]; });
    });
    note.textContent = notes[name];
  }

  nodes.forEach(function (n) {
    n.addEventListener("click", function () { select(n.dataset.node, true); });
    n.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(n.dataset.node, true); }
    });
  });
  picks.forEach(function (b) { b.addEventListener("click", function () { select(b.dataset.pick, true); }); });
  segs.forEach(function (s) { s.addEventListener("click", function () { view(s.dataset.view); }); });

  var start = location.hash.slice(1);
  if (start && document.getElementById("d-" + start)) { select(start, false); }
})();
"""


def outputs() -> dict[Path, str]:
    data = load()
    return {
        SVG: build_svg(data),
        PAGE: build_page(data),
        DIR / "diagram.css": CSS,
        DIR / "architecture.js": JS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = outputs()
    if args.check:
        stale = [p for p, t in files.items() if not p.exists() or p.read_text() != t]
        for p in stale:
            print(f"stale: {p.relative_to(ROOT)}")
        if stale:
            print("Run scripts/build_architecture.py.")
            return 1
        print("The architecture files are current.")
        return 0
    for path, text in files.items():
        path.write_text(text)
    print("wrote " + ", ".join(p.name for p in files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
