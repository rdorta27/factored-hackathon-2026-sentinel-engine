# Tasks

## 1. Persistence

- [x] 1.1 Sync engine and extended models (evidence: `tests/test_state_sqlite.py`)
- [x] 1.2 SQLite session, conversation and case stores; memory kept (evidence: `tests/test_state_sqlite.py::test_session_conversation_and_case_survive_a_restart`)
- [x] 1.3 Retention on logout and expiry (evidence: `tests/test_state_sqlite.py::test_logout_deletes_the_conversation`, `::test_expiry_deletes_the_conversation`)

## 2. Disputes

- [x] 2.1 One open dispute per charge across sessions (evidence: `tests/test_disputes_api.py::test_second_session_cannot_dispute_the_same_charge_again`)
- [x] 2.2 Handoff filed as a ticket (evidence: `tests/test_disputes_api.py::test_handoff_is_filed_as_a_ticket`)
- [x] 2.5 Handoff package with conversation summary and every attempted action (evidence: `tests/test_handoff_package.py`)
- [x] 2.6 Replies show only verified amounts and merchants (evidence: `tests/test_facts_grounding.py`)
- [x] 2.3 Two-step API and listing (evidence: `tests/test_disputes_api.py`)
- [x] 2.4 Adversarial B9, B10, C6, D6, D7 (evidence: `evidence/adversarial/20261001T122759Z/summary.json`)
