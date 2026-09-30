# Tasks

## 1. Measurement harness

- [x] 1.1 Add `@pytest.mark.attack(id, group)` to every attack and register the `attack` marker in `sentinel-ai-core/pyproject.toml`; verify `python -m pytest tests/adversarial -q` collects 29 marked attacks. Evidence: `sentinel-ai-core/tests/adversarial/test_a_injection.py` … `test_e_ambiguity.py`, `sentinel-ai-core/pyproject.toml`; owner area `docs/build/areas/ml.md`.
- [x] 1.2 Record the real outcome of each attack in `conftest.py` and derive the report in `summary.py`; verify a deliberately failing attack moves `unsafe_outcomes`. Evidence: `sentinel-ai-core/tests/adversarial/summary.py`, `conftest.py`.
- [x] 1.3 Fail collection on an unmarked attack and run `test_summary.py` after every attack; verify `test_every_attack_ran_and_was_classified` passes. Evidence: `sentinel-ai-core/tests/adversarial/conftest.py`, `test_summary.py`.

## 2. Attack repairs

- [x] 2.1 Capture the model input in A9 with `monkeypatch` and use the session memory in A4a and D5; verify both reach their intended assertion instead of erroring early. Evidence: `test_a_injection.py::test_national_id_in_the_message_never_reaches_the_model`, `test_d_tools.py::test_failed_read_back_never_becomes_a_case_number`.
- [x] 2.2 Stop the D4 xfail from sleeping 30 seconds; verify it xfails in about 0.2 s. Evidence: `test_d_tools.py::test_slow_gold_does_not_hang_the_request`.
- [x] 2.3 Correct the stand-in attribution and group rationale (`app/ai/demo.py:DemoModel`, E2/E3 confirmation gate, B7/B8/C1b ids); verify docstrings match the code. Evidence: docstrings under `sentinel-ai-core/tests/adversarial/`.

## 3. Evidence

- [x] 3.1 Write one immutable run under `evidence/adversarial/<run-id>/summary.json` only with `SENTINEL_WRITE_EVIDENCE=1`; verify a normal run writes nothing. Evidence: `evidence/adversarial/20260930T214744Z/summary.json` and its `README.md`; see `docs/build/decisions/004-pii-lifecycle.md`.
- [x] 3.2 Document the flag and the write-once rule; verify the command in the docs reproduces the run. Evidence: `AGENTS.md`, `sentinel-ai-core/tests/adversarial/README.md`.

## 4. Traceability

- [x] 4.1 Point REQ-0021 and REQ-0047 at the frozen run and mark the adversarial task done; verify the requirement table and `team/tasks.md` name the run. Evidence: `docs/requirements/requirements.md`, `team/tasks.md`; owner area `docs/build/areas/ml.md`.

## 5. Integration checks

- [x] 5.1 Run the full suite on `main` and lint the set; verify `python -m pytest -q` reports 114 passed, 4 xfailed and `flake8 --max-line-length=100 tests/adversarial` is clean. Evidence: `sentinel-ai-core/tests/adversarial/README.md`.
