import random

from eval import charge_examples as gen
from eval.charge_examples import Row

MERCHANTS = ["Super Ahorro", "Restaurante El Buen Sabor", gen.UNNAMED, "Uber"]
KINDS = ["Purchase", "Transfer", "Payment", "Withdrawal"]


def _customers(count: int) -> dict[str, list[Row]]:
    rng = random.Random(7)
    out = {}
    for number in range(count):
        cid = f"CLI-{number:04d}"
        rows = []
        for index in range(30):
            day = f"{rng.choice((2023, 2024, 2025, 2026))}-{rng.randint(1, 6):02d}-{rng.randint(1, 28):02d}"
            rows.append(Row(f"TRX-{cid}-{index}", cid, day, round(rng.uniform(5, 90000), 2), "USD",
                            rng.choice(MERCHANTS), rng.choice(KINDS), "Approved"))
        out[cid] = sorted(rows, key=lambda row: row.date, reverse=True)
    return out


def _build(rows):
    return gen.build_examples(rows, {"train": 3, "validation": 3, "test": 6})


def test_same_rows_and_seed_give_the_same_examples() -> None:
    rows = _customers(300)
    assert gen.digest_of(_build(rows)) == gen.digest_of(_build(rows))


def test_no_customer_is_in_two_splits() -> None:
    seen: dict[str, str] = {}
    for item in _build(_customers(300)):
        assert seen.setdefault(item.customer_id, item.split) == item.split


def test_the_target_date_matches_the_split_and_the_target_exists() -> None:
    rows = _customers(300)
    by_id = {row.transaction_id: row for items in rows.values() for row in items}
    examples = _build(rows)
    assert examples
    for item in examples:
        target = by_id[item.target_id]
        assert gen.split_of_date(target.date) == item.split
        assert target.date <= item.today
        assert target.customer_id == item.customer_id


def test_new_families_appear_only_in_the_test_split() -> None:
    examples = _build(_customers(600))
    for item in examples:
        if item.split != "test":
            assert item.family in gen.TRAIN_FAMILIES
    assert {item.family for item in examples if item.split == "test"} >= set(gen.TEST_ONLY_FAMILIES)


def test_every_family_has_an_es_419_and_a_pt_br_line_with_the_same_pieces() -> None:
    for family in gen.FAMILIES:
        es, pt = gen._FAMILY[family]["es"], gen._FAMILY[family]["pt"]
        slots = lambda order: [piece.partition(":")[0] for piece in order]
        assert slots(es[1]) == slots(pt[1])
        assert bool(es[0]) == bool(pt[0]) and bool(es[2]) == bool(pt[2])


def test_both_locales_and_amounts_in_words_are_present() -> None:
    examples = _build(_customers(600))
    assert {item.locale for item in examples} == {"es-419", "pt-BR"}
    assert any(item.amount_in_words for item in examples)
    assert any(not item.has_merchant for item in examples)


def test_no_description_is_empty() -> None:
    assert all(item.text.strip() for item in _build(_customers(300)))
