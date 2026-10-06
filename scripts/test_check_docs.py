"""Tests for scripts/check_docs.py.

Run from the repository root: python3 -m pytest scripts/test_check_docs.py -q
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_docs as cd  # noqa: E402


def test_header_detection():
    good = "---\nlanguage: en\nstyle: ASD-STE100\nlast_reviewed: 2026-10-05\n---\n\n# Title\n"
    assert cd.frontmatter(good) == (True, "2026-10-05")
    assert cd.frontmatter("# Title\n") == (False, None)
    assert cd.frontmatter("---\nlanguage: en\n---\n\n# Title\n") == (False, None)


def test_long_sentence():
    lines = [(1, "The router labels the intent " + "word " * 21)]
    found = cd.long_sentences(lines)
    assert found and found[0][2] > cd.MAX_WORDS
    assert cd.long_sentences([(1, "The router labels the intent in one turn.")]) == []


def test_table_rows_are_skipped_for_the_sentence_check():
    lines = [(1, "| " + "word " * 30 + "|")]
    assert cd.long_sentences(lines) == []


def test_likely_passive():
    found = cd.passives([(1, "The intent is labelled by the router.")])
    assert found and found[0][1] == "is labelled"
    assert cd.passives([(1, "The router labels the intent.")]) == []


def test_bare_locale_tags():
    found = cd.bare_locales([(1, "Write ES or PT alone. Use es-419 and pt-BR.")])
    assert [hit[1] for hit in found] == ["ES", "PT"]


def test_synonyms_name_the_agreed_term():
    found = cd.synonyms([(1, "The system makes an escalation.")])
    assert (1, "'escalation' for 'handoff'") in found


def test_code_and_links_are_ignored():
    text = "---\nstyle: ASD-STE100\nlast_reviewed: 2026-10-05\n---\n\n`escalate` and [diagnosis](2024Q4-cutoff-v1/summary.json)\n"
    lines = cd.prose(text)
    assert cd.synonyms(lines) == []


def test_analyze_reads_a_page(tmp_path):
    page = tmp_path / "page.md"
    page.write_text("---\nlanguage: en\nstyle: ASD-STE100\nlast_reviewed: 2026-10-05\n---\n\nThe escalation is done.\n")
    result = cd.analyze(page)
    assert result["header"] is True and result["reviewed"] == "2026-10-05"
    assert result["synonym"] and result["passive"]


def test_repository_report_has_a_summary(capsys):
    pages = cd.pages()
    assert pages
    counts = cd.report([cd.analyze(path) for path in pages])
    out = capsys.readouterr().out
    assert "summary:" in out
    assert counts["pages"] == len(pages)
    assert counts["header"] <= counts["pages"]
