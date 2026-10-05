"""v8 metrics: one test per new metric (eval-v8 task 1.3 and 1.4)."""

from app.ai.port import UnderstandSlots
from eval import metrics
from eval.cases import Case


def _case(case_id, subtype=None, slots=None, locale="es-419", country="MX"):
    return Case(
        id=case_id, locale=locale, country=country, turns=(case_id,),
        expected_intent="missing", expected_category=None,
        expected_outcome="clarification", requires_handoff=False,
        split="development", base_id=None, variant=None,
        expected_subtype=subtype, expected_slots=slots,
    )


def test_subtype_accuracy_counts_only_labelled_cases():
    cases = [
        _case("a", subtype="greeting"),
        _case("b", subtype="thanks"),
        _case("c", subtype=None),
    ]
    result = metrics.subtype_accuracy(cases, ["greeting", "wrong", "greeting"])
    assert (result["n"], result["correct"], result["accuracy"]) == (2, 1, 0.5)


def test_slot_precision_counts_returned_slots_only():
    expected = [{"merchant_words": "oxxo", "amount": 250.0}, None]
    predicted = [
        UnderstandSlots(merchant_words="cargo OXXO centro", amount=250.0),
        UnderstandSlots(merchant_words="oxxo", amount=1.0),
    ]
    result = metrics.slot_precision(expected, predicted)
    assert result["returned"] == 4
    assert result["correct"] == 2
    assert result["precision"] == 0.5


def test_rejected_draft_rate_reports_cases():
    rows = [
        {"id": "a", "draft": "hola {merchant}", "draft_ok": True, "draft_reason": "ok"},
        {"id": "b", "draft": "son 250 pesos", "draft_ok": False, "draft_reason": "digit_outside_placeholder"},
        {"id": "c", "draft": None, "draft_ok": None, "draft_reason": None},
    ]
    result = metrics.rejected_draft_rate(rows)
    assert (result["returned"], result["rejected"], result["rate"]) == (2, 1, 0.5)
    assert result["cases"] == ["b"]


def test_unsafe_wording_counts_amount_not_verified():
    rows = [
        {"id": "a", "draft": "son 250 pesos", "draft_ok": False, "draft_reason": "digit_outside_placeholder"},
        {"id": "b", "draft": "hola {merchant}", "draft_ok": True, "draft_reason": "ok"},
    ]
    result = metrics.unsafe_wording(rows)
    assert result["rate"] == "1/2"
    assert result["cases"] == ["a"]


def test_unnecessary_handoff_rate_uses_attempted_denominator():
    turns = [
        {"id": "a", "outcome": "handoff", "requires_handoff": False, "fault": "none"},
        {"id": "b", "outcome": "clarification", "requires_handoff": False, "fault": "none"},
        {"id": "c", "outcome": "handoff", "requires_handoff": False, "fault": "gold_unavailable"},
    ]
    result = metrics.unnecessary_handoff_rate(turns)
    assert (result["n"], result["unnecessary"], result["rate"]) == (2, 1, 0.5)


def test_system_outcome_match_reads_matched_flag():
    turns = [
        {"id": "a", "outcome": "handoff", "expected_outcome": "handoff", "matched": True},
        {"id": "b", "outcome": "text", "expected_outcome": "handoff", "matched": False},
    ]
    result = metrics.system_outcome_match(turns)
    assert (result["matched"], result["share"]) == (1, 0.5)


def test_resolution_ceiling_names_resolvable_and_gap():
    turns = [
        {"id": "a", "outcome": "case_confirmation", "requires_handoff": False, "must_not_pass": False, "fault": "none"},
        {"id": "b", "outcome": "clarification", "requires_handoff": False, "must_not_pass": False, "fault": "none"},
        {"id": "c", "outcome": "handoff", "requires_handoff": True, "must_not_pass": False, "fault": "none"},
        {"id": "d", "outcome": "text", "requires_handoff": False, "must_not_pass": True, "fault": "none"},
    ]
    result = metrics.resolution_ceiling(turns)
    assert (result["attempted"], result["resolvable"], result["resolved"], result["gap"]) == (4, 2, 1, 1)
    assert result["ceiling_share"] == 0.5


def test_handoff_checklist_scores_seven_items():
    handoffs = [
        {"id": "h1", "request": True, "verified_facts": True, "actions": True,
         "evidence": True, "open_questions": True, "reason": True, "language_country": True},
        {"id": "h2", "request": True, "verified_facts": False, "actions": True,
         "evidence": False, "open_questions": True, "reason": True, "language_country": True},
    ]
    result = metrics.handoff_checklist_score(handoffs)
    assert result["n"] == 2
    assert result["items"][0]["score"] == 1.0
    assert result["items"][1]["score"] == round(5 / 7, 4)
    assert result["mean"] == round((1.0 + round(5 / 7, 4)) / 2, 4)


def test_latency_per_conversation_groups_by_trace():
    turns = [
        {"id": "a-1", "trace_id": "t1", "latency_ms": 10.0},
        {"id": "a-2", "trace_id": "t1", "latency_ms": 20.0},
        {"id": "b", "trace_id": "t2", "latency_ms": 5.0},
    ]
    result = metrics.latency_per_conversation(turns)
    assert result["n"] == 2
    assert result["mean"] == round((30.0 + 5.0) / 2, 4)


def test_system_metrics_report_bases_next_to_n():
    turns = [
        {"id": "a-1", "situation": "b1", "outcome": "text", "requires_handoff": False,
         "must_not_pass": False, "fault": "none", "latency_ms": 1.0, "cost_usd": 0.0},
        {"id": "a-2", "situation": "b1", "outcome": "text", "requires_handoff": False,
         "must_not_pass": False, "fault": "none", "latency_ms": 1.0, "cost_usd": 0.0},
        {"id": "b-1", "situation": "b2", "outcome": "text", "requires_handoff": False,
         "must_not_pass": False, "fault": "none", "latency_ms": 1.0, "cost_usd": 0.0},
    ]
    result = metrics.system_metrics(turns)
    assert result["n"] == 3
    assert result["bases"] == 2


def test_timing_metrics_report_per_call_and_per_conversation():
    turns = [
        {"id": "a", "model_latency_ms": 100.0, "conversation_latency_ms": 200.0},
        {"id": "b", "model_latency_ms": 300.0, "conversation_latency_ms": 500.0},
        {"id": "c", "model_latency_ms": None, "conversation_latency_ms": 50.0},
    ]
    result = metrics.timing_metrics(turns)
    assert result["per_call"] == {"n": 2, "p50": 200.0, "p95": 290.0}
    assert result["per_conversation"]["n"] == 3
    assert result["per_conversation"]["p50"] == 200.0


def test_high_risk_ids_cover_attacks_and_handoffs():
    cases = [
        _case("adv", slots=None),
        _case("hand", slots=None),
        _case("plain", slots=None),
    ]
    object.__setattr__(cases[0], "tags", ("adversarial",))
    object.__setattr__(cases[1], "requires_handoff", True)
    result = metrics.high_risk_ids(cases)
    assert result == frozenset({"adv", "hand"})


def test_breakdown_has_language_and_country_groups():
    from eval.intervals import breakdown

    cases = [
        _case("mx-1", locale="es-419", country="MX"),
        _case("br-1", locale="pt-BR", country="MX"),
    ]
    result = breakdown(cases, ["missing", "missing"])
    assert set(result["by_locale"]) == {"es-419", "pt-BR"}
    assert set(result["by_country"]) == {"MX"}
    assert result["by_locale"]["es-419"]["n"] == 1


def test_run_version_reports_v8_fields():
    from eval.versions import Version, run_version
    from app.ai.demo import DemoModel

    cases = [_case("a", subtype="greeting", slots={"merchant_words": "oxxo"})]
    block = run_version(cases, Version(DemoModel()))
    assert block["subtype"]["n"] == 1
    assert block["slots"]["n"] >= 0
    assert block["drafts"]["n"] >= 0
    assert block["unsafe_wording"]["rate"] == f"{block['unsafe_wording']['count']}/{block['unsafe_wording']['n']}"


def test_high_risk_repeats_cover_attacks_three_times():
    from eval.versions import Version, with_high_risk_repeats
    from app.ai.demo import DemoModel

    cases = [_case("adv"), _case("plain")]
    object.__setattr__(cases[0], "tags", ("adversarial",))
    versions = {"baseline": Version(DemoModel()), "router": Version(DemoModel())}
    out = with_high_risk_repeats(versions, cases)
    assert out["baseline"].repetitions == 1
    assert out["router"].repetitions == 3
    assert out["router"].repeat_ids == frozenset({"adv"})


def test_system_metrics_carry_v8_reports():
    from eval.metrics import system_metrics

    turns = [
        {"id": "a", "outcome": "case_confirmation", "expected_outcome": "case_confirmation",
         "matched": True, "requires_handoff": False, "must_not_pass": False,
         "fault": "none", "latency_ms": 10.0, "cost_usd": 0.001,
         "variant": "es-MX", "country": "MX", "situation": "s1", "trace_id": "t1"},
        {"id": "b", "outcome": "handoff", "expected_outcome": "handoff",
         "matched": True, "requires_handoff": False, "must_not_pass": False,
         "fault": "none", "latency_ms": 20.0, "cost_usd": 0.002,
         "variant": "es-MX", "country": "MX", "situation": "s2", "trace_id": "t2"},
    ]
    result = system_metrics(turns)
    assert result["unnecessary_handoff_rate"]["unnecessary"] == 1
    assert result["system_outcome_match"]["matched"] == 2
    assert result["resolution_ceiling"]["resolvable"] == 2
    assert result["latency_per_conversation"]["n"] == 2
