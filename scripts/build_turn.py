#!/usr/bin/env python3
"""Build site/diagrams/turn.html: one chat turn, step by step.

Each step says who decides (model or code), what goes in and out, and what can
stop the turn (clarify, refuse or hand off). The sample messages are demo lines
from sentinel-ai-core/eval/demo/replay.md. The values are demo data.

    python3 scripts/build_turn.py          # write the files
    python3 scripts/build_turn.py --check  # exit 1 if a file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_architecture as ba  # noqa: E402

DIR = ba.DIR
REPO = ba.load()["repo"]

SAMPLES = [
    {"id": "es", "label": "Spanish (es-MX)", "lang": "es",
     "text": "Vi en mi estado de cuenta un cargo de 320 pesos mexicanos de Cafe Central del 12 de junio y no lo reconozco."},
    {"id": "pt", "label": "Portuguese (pt-BR)", "lang": "pt-BR",
     "text": "não reconheço uma cobrança de 320 no Cafe Central em 12 de junho"},
]

# decides: model | code. stops: (kind, text). Kinds: clarify, refuse, handoff.
STEPS = [
    {
        "id": "mask", "title": "Masking", "decides": "code",
        "in": "The text of the customer.",
        "out": "The same text, with personal identifiers masked. The model never sees the customer id.",
        "what": "Code masks personal identifiers by pattern. It also refuses a request to reveal the prompt, before any model call.",
        "stops": [("refuse", "A request to reveal the prompt gets a refusal. The code records the attempt.")],
        "evidence": ["sentinel-ai-core/app/privacy", "docs/build/decisions/004-pii-lifecycle.md"],
    },
    {
        "id": "router", "title": "Intent router", "decides": "model",
        "in": "The masked text.",
        "out": "One intent label: charge, missing, out of scope or person. For this sample: charge.",
        "what": "A prompted LLM labels the intent. It decides nothing else. If the model fails, the keyword baseline answers the turn.",
        "stops": [
            ("clarify", "Label missing: not enough information. The system asks."),
            ("refuse", "Label out of scope: the system does not act."),
            ("handoff", "Label person: the customer asks for an advisor."),
        ],
        "evidence": ["docs/build/decisions/016-router-models.md", "evidence/evaluation-runs/2024Q4-eval-v7/summary.json"],
    },
    {
        "id": "lookup", "title": "Charge lookup", "decides": "code",
        "in": "The session account and the words of the customer: amount, merchant, date.",
        "out": "The candidate charges of this account. For this sample: one match, Cafe Central, 320 MXN (demo data).",
        "what": "A session-bound tool reads the charges. The code narrows the list with the words of the customer.",
        "stops": [
            ("clarify", "Several candidates, or none for the date: the system shows the charges and asks which one."),
            ("handoff", "Three failed lookups hand off without an action."),
        ],
        "evidence": ["sentinel-ai-core/app/tools", "docs/build/conversation.md"],
    },
    {
        "id": "policy", "title": "Policy engine", "decides": "code",
        "in": "The facts of the charge and the policy of the country.",
        "out": "A decision with a rule id: allow, refuse or hand off. For this sample: allow.",
        "what": "Code checks the window, the status, the amount and the fraud rule. A later question of why gets this stored decision.",
        "stops": [
            ("refuse", "Outside the window, or a status that cannot be disputed."),
            ("handoff", "A high amount, or a fraud signal. A person decides."),
        ],
        "evidence": ["docs/build/decisions/021-dispute-policy-sources.md", "docs/rationale/policy-sources.md"],
    },
    {
        "id": "confirm", "title": "Confirmation", "decides": "code",
        "in": "The allowed charge.",
        "out": "A confirm box with the verified facts. The customer confirms or not.",
        "what": "The system opens nothing before the customer confirms. A confirm opens only the charge of the box that the customer saw.",
        "stops": [("clarify", "The customer does not confirm, or names another charge. The box closes and nothing opens.")],
        "evidence": ["docs/build/conversation.md"],
    },
    {
        "id": "open", "title": "Case opening", "decides": "code",
        "in": "The confirmed charge.",
        "out": "A case record in the case store.",
        "what": "A tool writes the case. The system counts only an action that the tool confirms. A timeout is not a success.",
        "stops": [("handoff", "A step that fails is not reported as done. The package for the advisor lists it.")],
        "evidence": ["sentinel-ai-core/app/models/dispute_case.py", "docs/architecture/mocks.md"],
    },
    {
        "id": "readback", "title": "Read-back", "decides": "code",
        "in": "The case reference.",
        "out": "The case number, shown to the customer.",
        "what": "The code reads the case back from the store. The system says that the case exists only after this read.",
        "stops": [],
        "evidence": ["docs/architecture/specification.md"],
    },
]

STOP = {"clarify": "Clarify", "refuse": "Refuse", "handoff": "Hand off"}
WHO = {"model": "Model labels", "code": "Code decides"}


def step_html(i: int, s: dict) -> str:
    stops = "".join(
        f'<li><span class="stop {k}">{STOP[k]}</span> {escape(t)}</li>' for k, t in s["stops"]
    ) or "<li>Nothing stops this step. It is the end of the turn.</li>"
    ev = " · ".join(
        f'<a href="{REPO}/{"tree" if (ba.ROOT / p).is_dir() else "blob"}/main/{p}">{escape(p)}</a>' for p in s["evidence"]
    )
    chip = "model" if s["decides"] == "model" else "code"
    return (
        f'<article class="detail tstep" id="p-{s["id"]}" data-step="{s["id"]}">'
        f'<h3>{i + 1}. {escape(s["title"])}</h3>'
        f'<p class="chips"><span class="tag {"" if chip == "model" else "data"}">{WHO[s["decides"]]}</span></p>'
        f'<p>{escape(s["what"])}</p>'
        f'<dl><dt>In</dt><dd>{escape(s["in"])}</dd><dt>Out</dt><dd>{escape(s["out"])}</dd></dl>'
        f'<h4>What can stop the turn</h4><ul class="stops">{stops}</ul>'
        f"<p>Evidence: {ev}</p></article>"
    )


def page() -> str:
    chips = "".join(
        f'<li><button type="button" class="chipbtn{" on" if i == 0 else ""}" data-go="{s["id"]}">'
        f'<span class="n">{i + 1}</span>{escape(s["title"])}'
        f'<span class="who {s["decides"]}">{"M" if s["decides"] == "model" else "C"}</span></button></li>'
        for i, s in enumerate(STEPS)
    )
    radios = "".join(
        f'<label class="radio"><input type="radio" name="sample" value="{x["id"]}"{" checked" if i == 0 else ""}> {escape(x["label"])}</label>'
        for i, x in enumerate(SAMPLES)
    )
    quotes = "".join(
        f'<blockquote class="sample" data-sample="{x["id"]}" lang="{x["lang"]}">&ldquo;{escape(x["text"])}&rdquo;</blockquote>'
        for x in SAMPLES
    )
    steps = "\n".join(step_html(i, s) for i, s in enumerate(STEPS))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>One chat turn · Sentinel Engine</title>
<meta name="description" content="Follow one chat turn step by step. See who decides, what goes in and out, and what can stop the turn.">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../style.css">
<link rel="stylesheet" href="diagram.css">
<link rel="stylesheet" href="turn.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
  <header class="top">
    <a class="logo" href="../"><img src="../favicon.svg" width="34" height="34" alt="">Sentinel</a>
    <nav aria-label="Main"><a href="../">Home</a><a href="architecture.html">Architecture</a><a href="cases.html">Cases</a><a href="evidence.html">Evidence</a></nav>
  </header>
  <main id="main">
    <h1>One chat turn</h1>
    <p class="lead">The customer writes one message. Seven steps follow. The model decides one of them. The code decides the rest.</p>
    <div class="switch" role="radiogroup" aria-label="Sample message">{radios}</div>
    {quotes}
    <ol class="steps" aria-label="Steps of the turn">
{chips}
    </ol>
    <div class="switch">
      <button type="button" class="seg" id="prev">Previous step</button>
      <button type="button" class="seg on" id="next">Next step</button>
      <span class="note">Demo data: Cafe Central, 320 MXN. The values are team-generated.</span>
    </div>
    <section id="detail" aria-live="polite" aria-label="Step details">
{steps}
    </section>
    <p class="note">Each stop is a kind of reply: <span class="stop clarify">Clarify</span> asks the customer, <span class="stop refuse">Refuse</span> declines, <span class="stop handoff">Hand off</span> files a ticket for an advisor. See <a href="{REPO}/blob/main/docs/build/conversation.md">the conversation page</a>.</p>
  </main>
</div>
<script src="turn.js"></script>
</body>
</html>
"""


CSS = """.steps { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: row; flex-wrap: wrap; gap: 8px; counter-reset: s; }
@media (max-width: 520px) { .steps li { flex: 1 1 calc(50% - 8px); } .steps .chipbtn { width: 100%; padding: 0 10px; font-size: 14px; } }
.steps .chipbtn { display: inline-flex; align-items: center; gap: 8px; }
.steps .n { width: 24px; height: 24px; border-radius: 12px; background: var(--tint); color: var(--brand-ink); display: inline-flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; }
.steps .on { border-color: var(--brand); background: var(--tint); }
.who { font-size: 11px; font-weight: 700; color: #fff; width: 20px; height: 20px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; }
.who.model { background: var(--accent); }
.who.code { background: var(--brand); }
.stop { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; padding: 2px 9px; border-radius: 8px; }
.stop.clarify { background: var(--tint); color: var(--brand-ink); }
.stop.refuse { background: var(--warn-bg); color: var(--warn); }
.stop.handoff { background: var(--ok-bg); color: var(--ok); }
.stops { margin: 0; padding-left: 0; list-style: none; display: flex; flex-direction: column; gap: 6px; }
.detail h4 { margin: 4px 0 0; font: 700 15px var(--sans); }
.js .sample { display: none; }
.js .sample.on { display: block; }
.radio { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 12px; border: 1px solid var(--line); border-radius: 22px; background: var(--card); font-weight: 600; cursor: pointer; }
.radio input { width: 18px; height: 18px; }
"""

JS = """(function () {
  document.documentElement.classList.add("js");
  var chips = Array.prototype.slice.call(document.querySelectorAll("[data-go]"));
  var steps = document.querySelectorAll(".tstep");
  var ids = chips.map(function (c) { return c.dataset.go; });
  var cur = 0;
  function go(i) {
    cur = Math.max(0, Math.min(ids.length - 1, i));
    chips.forEach(function (c, k) { c.classList.toggle("on", k === cur); c.setAttribute("aria-current", k === cur ? "step" : "false"); });
    steps.forEach(function (s) { s.classList.toggle("on", s.dataset.step === ids[cur]); });
    document.getElementById("prev").disabled = cur === 0;
    document.getElementById("next").disabled = cur === ids.length - 1;
    try { history.replaceState(null, "", "#" + ids[cur]); } catch (e) {}
  }
  chips.forEach(function (c, k) { c.addEventListener("click", function () { go(k); }); });
  document.getElementById("prev").addEventListener("click", function () { go(cur - 1); });
  document.getElementById("next").addEventListener("click", function () { go(cur + 1); });
  var quotes = document.querySelectorAll(".sample");
  function sample(id) { quotes.forEach(function (q) { q.classList.toggle("on", q.dataset.sample === id); }); }
  document.querySelectorAll("input[name=sample]").forEach(function (r) { r.addEventListener("change", function () { sample(r.value); }); });
  sample(document.querySelector("input[name=sample]:checked").value);
  var start = ids.indexOf(location.hash.slice(1));
  go(start >= 0 ? start : 0);
})();
"""


def outputs() -> dict[Path, str]:
    return {DIR / "turn.html": page(), DIR / "turn.js": JS, DIR / "turn.css": CSS}


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
