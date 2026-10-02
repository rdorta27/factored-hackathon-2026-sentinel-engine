"""Customer-facing policy texts claim nothing the policy files do not say."""

import json
import re
from pathlib import Path

import pytest

I18N = Path(__file__).parents[1] / "app" / "static" / "i18n"
LOCALES = sorted(path.stem for path in I18N.glob("*.json"))


def _texts(locale: str) -> dict[str, str]:
    return json.loads((I18N / f"{locale}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("locale", LOCALES)
def test_no_text_cites_an_article_the_repository_does_not_have(locale: str) -> None:
    cited = {key: text for key, text in _texts(locale).items() if re.search(r"\bArt\.?\s*\d", text)}
    assert cited == {}


@pytest.mark.parametrize("locale", LOCALES)
def test_no_text_hard_codes_the_dispute_window(locale: str) -> None:
    """The window is `window_days` in each country file; a text must not repeat it."""
    window = re.compile(r"\b\d+\s*(?:d[ií]as|dias|days)\b", re.IGNORECASE)
    hard_coded = {key: text for key, text in _texts(locale).items() if window.search(text)}
    assert hard_coded == {}


@pytest.mark.parametrize("locale", ["es-419", "pt-BR"])
def test_the_estimated_time_is_labelled_as_a_demonstration_value(locale: str) -> None:
    assert re.search(r"demonstra|demostra", _texts(locale)["field_eta"], re.IGNORECASE)
