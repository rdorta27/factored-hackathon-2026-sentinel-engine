"""The transcript sample stays on the development side of the 70/30 cut."""

from eval.sample_transcripts import HELD_OUT_CUT, event_date, is_development, sample_size, summary, take_sample


def test_cut_is_the_held_out_date() -> None:
    assert HELD_OUT_CUT == "2025-07-01"
    assert is_development("2025-06-30")
    assert not is_development("2025-07-01")
    assert not is_development("2026-01-01")


def test_event_date_prefers_the_row_over_the_partition() -> None:
    row = {"interaction_date": "2024-11-02T10:00:00"}
    assert event_date(row, "year=2025/month=07/day=01/x.csv") == "2024-11-02"
    assert event_date({}, "data/year=2024/month=12/day=31/a.csv") == "2024-12-31"


def test_one_percent_of_the_development_window_is_deterministic() -> None:
    assert sample_size(14023) == 280
    rows = [{"text": f"plantilla {i}", "date": "2024-10-01"} for i in range(14023)]
    first = take_sample(rows)
    second = take_sample(rows)
    assert len(first) == 280
    assert [row["text"] for row in first] == [row["text"] for row in second]


def test_sample_and_summary_store_no_text() -> None:
    rows = [{"text": f"plantilla {i}", "date": "2024-10-01"} for i in range(60)]
    sample = take_sample(rows, n=50, seed=1)
    assert len(sample) == 50
    payload = summary(rows, 3, sample, {"clarification": 50}, "analysis-working-copy")
    assert payload["n_held_out_excluded"] == 3
    assert payload["text_stored"] is False
    assert "plantilla" not in str(payload)
    assert "customer_id" not in payload
