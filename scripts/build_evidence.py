#!/usr/bin/env python3
"""Build site/diagrams/evidence.html: the evidence explorer.

Every bar comes from a row of the series in site/numbers.json (written by
scripts/site_numbers.py from frozen summary.json runs). No number is typed here.

    python3 scripts/build_evidence.py          # write the files
    python3 scripts/build_evidence.py --check  # exit 1 if a file is stale
"""

from __future__ import annotations

import argparse
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_architecture as ba  # noqa: E402
import site_numbers as sn  # noqa: E402

DIR = ba.DIR
REPO = ba.load()["repo"]
TAG = {"Test suite": "test", "Simulation": "", "Synthetic": "data", "Projection": ""}


def num(value, kind: str, unit: str = "") -> str:
    if kind == "rate":
        return f"{value * 100:.1f}%"
    if kind == "scale":
        if unit == "USD":
            return f"USD {value:.6g}"
        return f"{value:,.2f} {unit}".strip()
    return f"{int(value):,}"


def series_html(s: dict) -> str:
    kind, unit = s["kind"], s.get("unit", "")
    top = max(r["value"] for r in s["rows"]) or 1
    rows = []
    for r in s["rows"]:
        if kind == "rate":
            width = r["value"] * 100
            note = f'on {int(r["n"]):,} turns'
        elif kind == "count":
            width = r["value"] / r["n"] * 100 if r["n"] else 0
            note = f'of {int(r["n"]):,}'
        else:
            width = r["value"] / top * 100
            note = f'{int(r["n"]):,} turns' if unit != "USD" else f'for {int(r["n"]):,} turns'
        rows.append(
            f'<li><span class="lab">{escape(r["label"])}</span>'
            f'<span class="track" role="img" aria-label="{escape(r["label"])}: {num(r["value"], kind, unit)} {note}">'
            f'<span class="fill" style="width:{width:.2f}%"></span></span>'
            f'<span class="val"><strong>{num(r["value"], kind, unit)}</strong> {note} · <code>{escape(r["field"])}</code></span></li>'
        )
    extra = "".join(
        f'<p><strong>{escape(x["label"])}:</strong> {escape(str(x["value"]))} · <code>{escape(x["field"])}</code></p>'
        for x in s.get("extra", [])
    )
    mode = f'<span class="tag data">{escape(s["mode"])}</span>' if s.get("mode") else ""
    return (
        f'<section class="series" id="s-{s["id"]}" data-series="{s["id"]}" role="tabpanel" aria-labelledby="t-{s["id"]}">'
        f'<h2>{escape(s["title"])}</h2>'
        f'<p class="chips"><span class="tag {TAG[s["type"]]}">{escape(s["type"])}</span>{mode}</p>'
        f'<p>{escape(s["about"])}</p><ul class="bars">{"".join(rows)}</ul>{extra}'
        f'<p class="src">{escape(s["source"])}</p></section>'
    )


def page() -> str:
    series = sn.build()["series"]
    tabs = "".join(
        f'<button type="button" role="tab" class="seg{" on" if i == 0 else ""}" id="t-{s["id"]}" data-tab="{s["id"]}" '
        f'aria-selected="{"true" if i == 0 else "false"}" aria-controls="s-{s["id"]}">{escape(s["title"])}</button>'
        for i, s in enumerate(series)
    )
    body = "\n".join(series_html(s) for s in series)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evidence · Sentinel Engine</title>
<meta name="description" content="Explore the measured results: intent accuracy, the resolution ceiling, attacks, latency and cost. Each bar shows its denominator, its type and its summary.json field.">
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
    <nav aria-label="Main"><a href="../">Home</a><a href="architecture.html">Architecture</a><a href="cases.html">Cases</a></nav>
  </header>
  <main id="main">
    <h1>Evidence explorer</h1>
    <p class="lead">Each bar shows its denominator, its type and the field of the frozen run that it reads. No number here is a production measurement.</p>
    <div class="switch" role="tablist" aria-label="Metric">{tabs}</div>
    <div id="detail" aria-live="polite">
{body}
    </div>
    <p class="note">The runs are listed in the <a href="{REPO}/blob/main/evidence/README.md">evidence index</a>. The types follow <a href="{REPO}/blob/main/docs/architecture/what-is-real.md">what is real</a>.</p>
  </main>
</div>
<script src="evidence.js"></script>
</body>
</html>
"""


JS = """(function () {
  document.documentElement.classList.add("js");
  var tabs = Array.prototype.slice.call(document.querySelectorAll("[data-tab]"));
  var panels = document.querySelectorAll(".series");
  function show(id) {
    tabs.forEach(function (t) {
      var on = t.dataset.tab === id;
      t.classList.toggle("on", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
    });
    panels.forEach(function (p) { p.classList.toggle("on", p.dataset.series === id); });
    try { history.replaceState(null, "", "#" + id); } catch (e) {}
  }
  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { show(t.dataset.tab); });
    t.addEventListener("keydown", function (e) {
      var j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : -1;
      if (j >= 0) { j = (j + tabs.length) % tabs.length; tabs[j].focus(); show(tabs[j].dataset.tab); e.preventDefault(); }
    });
  });
  var ids = tabs.map(function (t) { return t.dataset.tab; });
  var start = location.hash.slice(1);
  show(ids.indexOf(start) >= 0 ? start : ids[0]);
})();
"""


def outputs() -> dict[Path, str]:
    return {DIR / "evidence.html": page(), DIR / "evidence.js": JS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = outputs()
    if args.check:
        stale = [p for p, t in files.items() if not p.exists() or p.read_text() != t]
        for p in stale:
            print(f"stale: {p.relative_to(ba.ROOT)}")
        return 1 if stale else 0
    for path, text in files.items():
        path.write_text(text)
    print("wrote " + ", ".join(p.name for p in files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
