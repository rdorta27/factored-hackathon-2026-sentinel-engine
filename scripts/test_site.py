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
