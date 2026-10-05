"""Tests for the static site: numbers match the evidence, no secret, no external load.

Run from the repository root: python3 -m pytest scripts/test_site.py -q
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import site_numbers as sn  # noqa: E402

SITE = sn.ROOT / "site"
PAGES = sorted(SITE.rglob("*.html"))


def test_numbers_json_matches_evidence():
    assert sn.OUT.read_text() == sn.render(sn.build()), "run scripts/site_numbers.py"


def test_each_number_slot_matches_numbers_json():
    numbers = json.loads(sn.OUT.read_text())["numbers"]
    slots = 0
    for page in PAGES:
        for m in sn.SLOT.finditer(page.read_text()):
            slots += 1
            key = m.group(4)
            assert key in numbers, f"{page.name}: unknown number {key}"
            expected = sn.slot_text(numbers, m.group(3), key)
            assert m.group(5) == expected, f"{page.name}: {key} shows {m.group(5)!r}, evidence says {expected!r}"
    assert slots > 0


def test_every_number_has_type_source_and_field():
    for key, entry in json.loads(sn.OUT.read_text())["numbers"].items():
        assert entry["type"] in {"Test suite", "Simulation", "Synthetic", "Projection"}, key
        assert entry["source"].startswith("evidence/") and entry["field"], key


def test_no_hand_typed_digits_in_result_cards():
    # Result cards must hold digits only inside number slots.
    html = (SITE / "index.html").read_text()
    proof = html.split('id="proof"')[1].split('id="demo"')[0]
    stripped = sn.SLOT.sub("", proof)
    stripped = re.sub(r'<span class="src">.*?</span>', "", stripped)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    stripped = re.sub(r"summary\.json|numbers\.json|v\d+|\d{4}Q\d", "", stripped)
    assert not re.search(r"\d", stripped), re.findall(r".{20}\d.{20}", stripped)


def test_no_secret_on_the_site():
    banned = re.compile(
        r"password|passwd|testpass|api[_-]?key|secret|bucket|account[_-]?id|CUST-\d|s3://|abfss://|\.blob\.core",
        re.I,
    )
    for path in SITE.rglob("*"):
        if path.is_file() and path.suffix in {".html", ".css", ".js", ".json", ".svg"}:
            hit = banned.search(path.read_text())
            assert not hit, f"{path.name}: {hit.group(0)}"


def test_no_external_request():
    # Links (<a href>) may leave the site. Loaded resources may not.
    load = re.compile(r'<(?:script|img|link|iframe|source|video|audio)\b[^>]*?(?:src|href)="(?:https?:)?//', re.I)
    for page in PAGES:
        assert not load.search(page.read_text()), page.name
    for css in SITE.rglob("*.css"):
        assert "url(http" not in css.read_text() and "@import" not in css.read_text(), css.name


def test_page_details():
    for page in PAGES:
        html = page.read_text()
        assert '<html lang="en">' in html and "<title>" in html, page.name
        assert 'name="viewport"' in html, page.name
    home = (SITE / "index.html").read_text()
    assert 'name="description"' in home and 'rel="icon"' in home
    assert (SITE / "404.html").exists() and (SITE / "favicon.svg").exists()
    assert "prefers-color-scheme: dark" in (SITE / "style.css").read_text()


def test_product_page_numbers_match_the_evidence():
    page = (sn.ROOT / "docs" / "product.md").read_text()
    flows = json.loads((sn.EVIDENCE / "flows/2024Q4-v3/summary.json").read_text())
    problem = json.loads((sn.EVIDENCE / "problem/dev-v1/summary.json").read_text())
    expected = [
        f"{flows['accounts']['reason_transaccional']:,} of {flows['accounts']['n_calls']:,} calls",
        f"{flows['disputes']['unrecognized_claim']} of {flows['disputes']['n']:,}",
        f"{problem['hours']['transaction_dispute']['hours_per_month']}",
        f"{problem['reasons']['Queja']['share_pct']}%",
    ]
    for text in expected:
        assert text in page, f"docs/product.md does not show {text!r}"


# --- architecture drawing (tasks 2.4 and 4.1) ---

import build_architecture as ba  # noqa: E402


def test_architecture_files_are_current():
    for path, text in ba.outputs().items():
        assert path.read_text() == text, f"{path.name} is stale: run scripts/build_architecture.py"


def test_architecture_evidence_paths_exist():
    data = ba.load()
    ids = {n["id"] for n in data["nodes"]}
    assert len(ids) == len(data["nodes"])
    for n in data["nodes"]:
        assert n["status"] in {"real", "mock", "synthetic"} and n["decides"] in ba.DECIDES
        assert n["evidence"], n["id"]
        for rel in n["evidence"]:
            assert (sn.ROOT / rel).exists(), f"{n['id']}: missing {rel}"
        for key in n["metrics"]:
            assert key in sn.METRICS, f"{n['id']}: unknown number {key}"
    for e in data["edges"]:
        assert e["from"] in ids and e["to"] in ids


def test_architecture_nodes_are_keyboard_operable():
    html = (SITE / "diagrams" / "architecture.html").read_text()
    for n in ba.load()["nodes"]:
        assert f'id="n-{n["id"]}"' in html and f'id="d-{n["id"]}"' in html
    assert html.count('role="button" aria-label=') == len(ba.load()["nodes"])
    assert html.count('tabindex="0"') >= len(ba.load()["nodes"])
    # No library, no external request: one local script.
    assert html.count("<script") == 1 and 'src="architecture.js"' in html


def test_every_mock_names_its_production_replacement():
    for n in ba.load()["nodes"]:
        if n["status"] == "mock":
            assert n["prod"] and n["prod_short"] and n["prod"] != n["runs"], n["id"]


def test_architecture_page_in_the_browser():
    pytest = __import__("pytest")
    sync = pytest.importorskip("playwright.sync_api")
    chromium = next((p for p in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome") if Path(p).exists()), None)
    if not chromium:
        pytest.skip("no Chromium found")
    url = (SITE / "diagrams" / "architecture.html").as_uri()
    with sync.sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium, args=["--no-sandbox"])
        errors = []
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        requests = []
        page.on("request", lambda r: requests.append(r.url))
        page.goto(url)
        page.click("#n-gold")
        assert page.inner_text(".detail.on h3") == "Gold store"
        page.click("[data-view=prod]")
        assert "Gold on Databricks" in page.text_content("#n-gold")
        page.click("[data-view=demo]")
        assert "Labelled in-memory mock" in page.text_content("#n-gold")
        page.focus("#n-policy")
        page.keyboard.press("Enter")
        assert page.inner_text(".detail.on h3") == "Policy engine"
        phone = browser.new_page(viewport={"width": 390, "height": 800})
        phone.goto(url)
        assert not phone.evaluate("document.documentElement.scrollWidth > innerWidth")
        browser.close()
    assert not errors
    assert all(u.startswith("file:") for u in requests), requests


# --- slides (task 3.2) ---

DECK = SITE / "slides" / "deck.html"


def test_deck_has_six_slides_with_the_right_order():
    html = DECK.read_text()
    assert html.count('<section class="slide"') == 6
    labels = re.findall(r'<section class="slide" id="s\d" aria-label="([^"]+)"', html)
    assert labels == ["Why", "What", "How", "Proof", "Your brand", "Limits and roadmap"]
    assert "The AI converses." in html and "The rules decide." in html
    assert "architecture-light.svg" in html


def test_deck_numbers_only_in_number_slots():
    html = DECK.read_text()
    outside = sn.SLOT.sub("", html)
    outside = re.sub(r"<style.*?</style>|<script.*?</script>", "", outside, flags=re.S)
    for key, entry in json.loads(sn.OUT.read_text())["numbers"].items():
        text = entry["text"]
        if len(text) >= 3:
            assert text not in outside, f"{key} ({text}) is typed by hand in the deck"


def test_deck_in_the_browser_and_pdf():
    pytest = __import__("pytest")
    sync = pytest.importorskip("playwright.sync_api")
    chromium = next((p for p in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome") if Path(p).exists()), None)
    if not chromium:
        pytest.skip("no Chromium found")
    with sync.sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 784})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(DECK.as_uri())
        assert page.locator(".slide.on").count() == 1
        for _ in range(7):
            page.keyboard.press("ArrowRight")
        assert page.locator(".slide.on").get_attribute("id") == "s6"
        page.keyboard.press("Home")
        assert page.locator(".slide.on").get_attribute("id") == "s1"
        page.emulate_media(media="print")
        assert page.locator(".slide").evaluate_all("els => els.every(e => getComputedStyle(e).display !== 'none')")
        browser.close()
    assert not errors


def test_markdown_number_marks_match_the_evidence():
    assert sn.sync_markdown(json.loads(sn.OUT.read_text())["numbers"], check=True) == []
    assert "<!--n:" in (sn.ROOT / "docs/build/video-script.md").read_text()


# --- all diagrams (task 4.6) ---

import build_cases as bc  # noqa: E402
import build_evidence as be  # noqa: E402

DIAGRAMS = ["architecture", "cases", "evidence"]


def test_cases_and_evidence_files_are_current():
    for mod in (bc, be):
        for path, text in mod.outputs().items():
            assert path.read_text() == text, f"{path.name} is stale: run scripts/{mod.__name__}.py"


def test_evidence_text_holds_no_typed_number():
    # Prose is free of digits. Every digit on a bar comes from numbers.json.
    for s in json.loads(sn.OUT.read_text())["series"]:
        assert not re.search(r"\d", s["about"]), s["id"]
        assert s["type"] in {"Test suite", "Simulation", "Synthetic", "Projection"}
        for row in s["rows"]:
            assert row["field"] and row["n_field"], (s["id"], row["label"])
    html = (SITE / "diagrams" / "evidence.html").read_text()
    assert "<script" in html and html.count("<script") == 1


def test_cases_page_uses_the_real_demo_lines_and_package_fields():
    html = (SITE / "diagrams" / "cases.html").read_text()
    replay = (sn.ROOT / "sentinel-ai-core/eval/demo/replay.md").read_text()
    for c in bc.CASES:
        assert c["line"] in replay, f"demo line of {c['id']} is not in replay.md"
    schema = (sn.ROOT / "sentinel-ai-core/app/schemas/chat.py").read_text()
    package = schema.split("class HandoffPackage")[1].split("class Handoff(")[0]
    for name, _ in bc.PACKAGE:
        for field in name.split(", "):
            assert f"{field}:" in package, f"{field} is not a HandoffPackage field"
    assert 'id="package"' in html


def test_every_diagram_in_the_browser():
    pytest = __import__("pytest")
    sync = pytest.importorskip("playwright.sync_api")
    chromium = next((p for p in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome") if Path(p).exists()), None)
    if not chromium:
        pytest.skip("no Chromium found")
    with sync.sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium, args=["--no-sandbox"])
        for name in DIAGRAMS:
            url = (SITE / "diagrams" / f"{name}.html").as_uri()
            for width in (1280, 390):
                page = browser.new_page(viewport={"width": width, "height": 800})
                errors, requests = [], []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("request", lambda r: requests.append(r.url))
                page.goto(url)
                assert not errors, (name, errors)
                assert all(u.startswith("file:") for u in requests), (name, requests)
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (name, width)
                page.close()
            # Keyboard: every tab or node is reachable and works with the keys.
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url)
            if name == "architecture":
                page.focus("#n-gold")
                page.keyboard.press("Enter")
                assert page.inner_text(".detail.on h3") == "Gold store"
            else:
                tabs = page.locator("[role=tab]")
                assert tabs.count() >= 3
                tabs.nth(0).focus()
                page.keyboard.press("ArrowRight")
                assert page.locator("[role=tab][aria-selected=true]").get_attribute("data-tab") == tabs.nth(1).get_attribute("data-tab")
            # Without JS the content is still on the page.
            nojs = browser.new_context(java_script_enabled=False).new_page()
            nojs.goto(url)
            assert len(nojs.inner_text("main")) > 400, name
            page.close()
        browser.close()


def test_home_page_links_every_diagram_and_the_slides():
    home = (SITE / "index.html").read_text()
    for target in ("diagrams/architecture.html", "diagrams/cases.html", "diagrams/evidence.html", "slides/deck.html"):
        assert f'href="{target}"' in home, target
        assert (SITE / target).exists()
    assert 'property="og:image"' in home and (SITE / "preview.png").exists()
    assert 'id="limits"' in home and "submission email" in home
