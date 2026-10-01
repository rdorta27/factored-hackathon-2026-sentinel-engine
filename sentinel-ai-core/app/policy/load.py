from datetime import date
from pathlib import Path

from app.policy.engine import CountryPolicy, Threshold

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config" / "policy"


def load_country(country: str, directory: Path = CONFIG_DIR) -> CountryPolicy | None:
    path = directory / f"{country.lower()}.yaml"
    if not path.is_file():
        return None
    data = _parse(path.read_text(encoding="utf-8"))
    thresholds = data["thresholds"]
    return CountryPolicy(
        country=data["country"],
        currency=data["currency"],
        demo_today=date.fromisoformat(data["demo_today"]),
        window_days=int(data["window_days"]),
        disputable={
            name: item["disputable"] == "true"
            for name, item in data["statuses"].items()
        },
        fraud_score=_threshold(thresholds["fraud_score"]),
        high_amount=_threshold(thresholds["high_amount"]),
        staleness_days=_threshold(thresholds["staleness_days"]),
        mandatory_fields=tuple(data.get("mandatory_fields", [])),
        synthetic=data.get("synthetic") == "true",
    )


def _threshold(item: dict) -> Threshold:
    raw = item.get("value")
    value = None if raw in (None, "null", "") else raw
    per_currency = item.get("values") or {}
    if not isinstance(per_currency, dict):
        raise ValueError("threshold values must be a currency map")
    values = tuple(
        sorted((code, limit) for code, limit in per_currency.items() if limit not in (None, "null", ""))
    )
    source = item.get("source")
    return Threshold(
        value=value,
        provisional=item.get("provisional") == "true",
        decision=int(item["decision"]) if item.get("decision") else None,
        values=values,
        source=None if source in (None, "null", "") else source,
    )


def _parse(text: str) -> dict:
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        key, _, value = raw.strip().partition(":")
        value = value.strip().strip('"')
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        elif value == "[]":
            parent[key] = []
        else:
            parent[key] = value
    return root
