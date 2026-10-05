#!/usr/bin/env python3
"""Build site/diagrams/cases.html: the three demo cases on one decision map.

The demo lines come from sentinel-ai-core/eval/demo/replay.md. The handoff
package fields come from HandoffPackage in sentinel-ai-core/app/schemas/chat.py.
The page shows the shape of the package, never an invented record.

    python3 scripts/build_cases.py          # write the files
    python3 scripts/build_cases.py --check  # exit 1 if a file is stale
"""

from __future__ import annotations

import argparse
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_architecture as ba  # noqa: E402
import site_chrome  # noqa: E402
import localize  # noqa: E402

DIR = ba.DIR
REPO = ba.load()["repo"]
W, H = 1110, 400
NW, NH = 130, 60

# id: (title, decider, x, y)
NODES = {
    "msg": ("Message", None, 15, 170),
    "mask": ("Masking", "code", 173, 170),
    "router": ("Intent router", "model", 331, 170),
    "lookup": ("Charge lookup", "code", 489, 170),
    "policy": ("Policy engine", "code", 647, 170),
    "confirm": ("Confirm box", "code", 805, 30),
    "case": ("Case opened", "code", 963, 30),
    "ask": ("Which charge?", "code", 805, 170),
    "wait": ("Nothing opens", "code", 963, 170),
    "handoff": ("Handoff", "code", 805, 310),
    "advisor": ("Advisor view", "person", 963, 310),
}
EDGES = [
    ("msg", "mask"), ("mask", "router"), ("router", "lookup"), ("lookup", "policy"),
    ("policy", "confirm"), ("policy", "ask"), ("policy", "handoff"),
    ("confirm", "case"), ("ask", "wait"), ("handoff", "advisor"),
]

CASES = [
    {
        "id": "normal", "tab": "Normal", "title": "Normal case",
        "setup": "A México account with one matching charge: Cafe Central, 320 MXN.",
        "line": "Vi en mi estado de cuenta un cargo de 320 pesos mexicanos de Cafe Central del 12 de junio y no lo reconozco.",
        "lang": "es-MX line, shown in es-LA",
        "route": ["msg", "mask", "router", "lookup", "policy", "confirm", "case"],
        "steps": [
            ("Masking", "The code masks personal identifiers in the text before any model call."),
            ("Intent router", "The model labels the intent as a charge inquiry. It decides nothing else."),
            ("Charge lookup", "The code reads the charges of the session account and finds one match."),
            ("Policy engine", "The code checks the dispute window, the status and the amount. The policy allows the dispute."),
            ("Confirm box", "The customer confirms the charge. The system opens nothing before that."),
            ("Case opened", "The code opens the case, reads it back and shows the case number."),
        ],
        "end": "A verified case. The system says that the case exists only after it reads it back.",
    },
    {
        "id": "ambiguous", "tab": "Ambiguous", "title": "Ambiguous case",
        "setup": "A Colombia account with several charges that could match.",
        "line": "não reconheço uma cobrança",
        "lang": "pt-BR, then: não reconheço, pode revisar?",
        "route": ["msg", "mask", "router", "lookup", "policy", "ask", "wait"],
        "steps": [
            ("Masking", "The code masks personal identifiers in the text."),
            ("Intent router", "The model labels the intent as a charge inquiry."),
            ("Charge lookup", "The code finds more than one candidate charge."),
            ("Policy engine", "The text does not name one charge. The code does not guess."),
            ("Which charge?", "The page shows the candidate charges as chips. The customer picks one."),
            ("Nothing opens", "No dispute opens and no case exists until the customer picks and confirms."),
        ],
        "end": "A question, not an action. Nothing opens on the second unclear message either.",
    },
    {
        "id": "person", "tab": "A person is needed", "title": "A person is needed",
        "setup": "An Argentina account. The customer asks for an advisor.",
        "line": "Quiero hablar con un asesor.",
        "lang": "es line. In pt-BR: quero falar com um atendente",
        "route": ["msg", "mask", "router", "lookup", "policy", "handoff", "advisor"],
        "steps": [
            ("Masking", "The code masks personal identifiers in the text."),
            ("Intent router", "The model labels the intent as a request for a person."),
            ("Policy engine", "The first request offers help. A second request files a handoff. The code decides, not the model."),
            ("Handoff", "The code builds the package for the advisor from its own records."),
            ("Advisor view", "The advisor reads the package in a read-only view, with the trace of each step."),
        ],
        "end": "A handoff with the verified facts, so the customer does not repeat the story.",
    },
]

PACKAGE = [
    ("request", "The intent that the system understood. A code, not the customer's words."),
    ("summary", "A fixed summary of the conversation, built from the turns."),
    ("conversation", "Each turn as codes and references. No raw transcript."),
    ("verified_facts", "The charge facts that the code read from the data."),
    ("actions_taken", "Every step the system tried, with its turn and outcome. Failed steps too."),
    ("evidence", "References that support the facts."),
    ("open_questions", "What the advisor still needs to ask."),
    ("language, country, phase", "Where the case is and in which language."),
]


def svg() -> str:
    data = {"node": [NW, NH], "nodes": [{"id": k, "x": v[2], "y": v[3]} for k, v in NODES.items()],
            "edges": [{"from": a, "to": b} for a, b in EDGES]}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" class="arch" id="map" viewBox="0 0 {W} {H}" role="group" '
           f'aria-label="Decision map of the three demo cases">', f"<style>\n{ba.STYLE}\n{EXTRA_STYLE}\n</style>",
           '<rect class="bg" width="100%" height="100%" rx="12"/>', ba.svg_edges(data)]
    for key, (title, decider, x, y) in NODES.items():
        cls = "real" if key != "advisor" else "mock"
        out.append(f'<g class="node {cls}" data-node="{key}" transform="translate({x},{y})">')
        out.append(f'<rect class="box" width="{NW}" height="{NH}" rx="12"/>')
        out.append(f'<text class="t1" x="10" y="26" style="font-size:13px">{escape(title)}</text>')
        sub = {"code": "Code decides", "model": "Model labels", "person": "Person decides", None: "Starts the turn"}[decider]
        out.append(f'<text class="t3" x="10" y="46">{sub}</text>')
        if decider:
            letter = ba.DECIDES[decider][0]
            out.append(f'<circle class="chip {decider}" cx="{NW - 15}" cy="15" r="9"/>')
            out.append(f'<text class="chipt" x="{NW - 15}" y="19" text-anchor="middle">{letter}</text>')
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


EXTRA_STYLE = """svg.arch .node,svg.arch .edge,svg.arch .arrow{transition:opacity .2s}
svg.arch.focus .node:not(.lit),svg.arch.focus .edge:not(.lit),svg.arch.focus .arrow:not(.lit){opacity:.25}
svg.arch .node.lit .box{stroke:var(--model);stroke-width:3}
svg.arch .edge.lit{stroke:var(--model);stroke-width:3}
svg.arch .arrow.lit{fill:var(--model)}
svg.arch .node{cursor:default}
@media (prefers-reduced-motion:reduce){svg.arch .node,svg.arch .edge,svg.arch .arrow{transition:none}}"""


def case_panel(c) -> str:
    rows = "".join(f"<li><b>{escape(t)}{'' if t.endswith('?') else '.'}</b> {escape(d)}</li>" for t, d in c["steps"])
    extra = ""
    if c["id"] == "person":
        fields = "".join(f"<dt><code>{escape(k)}</code></dt><dd>{escape(v)}</dd>" for k, v in PACKAGE)
        extra = (
            '<div class="pkg" id="package"><h3>The handoff package</h3>'
            "<p>This is the shape of what the advisor receives. It holds no customer identifier and no raw transcript. "
            "The values come from the conversation, so this page shows the fields only.</p>"
            f"<dl>{fields}</dl>"
            f'<p class="note">Source: <a href="{REPO}/blob/main/sentinel-ai-core/app/schemas/chat.py">HandoffPackage</a> '
            f'and <a href="{REPO}/blob/main/docs/architecture/mocks.md">the advisor mock</a>.</p></div>'
        )
    return (
        f'<article class="detail case" id="c-{c["id"]}" data-case="{c["id"]}" role="tabpanel" aria-labelledby="t-{c["id"]}">'
        f'<h3>{escape(c["title"])}</h3><p>{escape(c["setup"])}</p>'
        f'<blockquote><span lang="{"pt-BR" if "pt-BR" in c["lang"].split(",")[0] else "es"}">&ldquo;{escape(c["line"])}&rdquo;</span>'
        f'<small>{escape(c["lang"])}</small></blockquote>'
        f"<ol>{rows}</ol><p><b>Result.</b> {escape(c['end'])}</p>{extra}</article>"
    )


def page() -> str:
    tabs = "".join(
        f'<button type="button" role="tab" class="seg{" on" if i == 0 else ""}" id="t-{c["id"]}" data-tab="{c["id"]}" '
        f'aria-selected="{"true" if i == 0 else "false"}" aria-controls="c-{c["id"]}">{escape(c["tab"])}</button>'
        for i, c in enumerate(CASES)
    )
    panels = "\n".join(case_panel(c) for c in CASES)
    routes = {c["id"]: c["route"] for c in CASES}
    import json
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demo cases · Sentinel Engine</title>
<meta name="description" content="The three demo cases on one decision map: normal, ambiguous and a person is needed. Select a case to light its route.">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../style.css">
<link rel="stylesheet" href="diagram.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
  <!--site:header-->
  <main id="main">
    <h1>Three cases, one decision map</h1>
    <p class="lead">The same steps run each time. The code decides where the turn goes. Select a case to light its route.</p>
    <div class="switch" role="tablist" aria-label="Demo cases">{tabs}</div>
    <div class="scroller" tabindex="0" aria-label="Decision map, scrolls sideways on a narrow screen">
{svg()}
    </div>
    <section id="detail" aria-live="polite" aria-label="Case details">
{panels}
    </section>
    <p class="note">The lines are the demo lines of the <a href="{REPO}/blob/main/sentinel-ai-core/eval/demo/replay.md">demo replay</a>. The data behind the demo is synthetic and the Gold store is a labelled mock. See <a href="{REPO}/blob/main/docs/architecture/what-is-real.md">what is real</a>.</p>
  </main>
  <!--site:footer-->
</div>
<script type="application/json" id="routes">{json.dumps(routes)}</script>
<script src="cases.js"></script>
</body>
</html>
"""


JS = """(function () {
  document.documentElement.classList.add("js");
  var routes = JSON.parse(document.getElementById("routes").textContent);
  var svg = document.getElementById("map");
  var tabs = Array.prototype.slice.call(document.querySelectorAll("[data-tab]"));
  var panels = document.querySelectorAll(".case");

  function show(id) {
    var lit = routes[id];
    svg.classList.add("focus");
    svg.querySelectorAll(".node").forEach(function (n) { n.classList.toggle("lit", lit.indexOf(n.dataset.node) >= 0); });
    svg.querySelectorAll("[data-e]").forEach(function (e) {
      var p = e.dataset.e.split(":");
      e.classList.toggle("lit", lit.indexOf(p[0]) >= 0 && lit.indexOf(p[1]) >= 0 && lit.indexOf(p[1]) === lit.indexOf(p[0]) + 1);
    });
    tabs.forEach(function (t) {
      var on = t.dataset.tab === id;
      t.classList.toggle("on", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
    });
    panels.forEach(function (p) { p.classList.toggle("on", p.dataset["case"] === id); });
    try { history.replaceState(null, "", "#" + id); } catch (e) {}
  }

  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { show(t.dataset.tab); });
    t.addEventListener("keydown", function (e) {
      var j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : -1;
      if (j >= 0) { j = (j + tabs.length) % tabs.length; tabs[j].focus(); show(tabs[j].dataset.tab); e.preventDefault(); }
    });
  });
  var start = location.hash.slice(1);
  show(routes[start] ? start : tabs[0].dataset.tab);
})();
"""




def outputs() -> dict[Path, str]:
    return {DIR / "cases.html": localize.en_page(page(), "diagrams/cases.html"), DIR / "cases.js": JS}


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
