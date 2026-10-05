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
