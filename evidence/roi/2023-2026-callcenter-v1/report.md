# Call-center aggregates 2023-2026-callcenter-v1

Source: bronze_call_center_interactions (silver drops duration_seconds, bronze has it), 2023-06-17 08:03:26 to 2026-06-18 07:58:13, n=686296 calls (96234 without duration).

- Transaccional (transactional) calls: 240056 (0.3498 of all calls), origin measured.
- Mean handle time: 3.68 minutes over 206465 calls with a duration; 33591 without one (origin derived).
- First-contact resolution: 219671/240056 = 0.9151 (origin derived, field was_resolved).
- Escalation share: 23841/240056 = 0.0993 (origin derived, field was_escalated).
- Bound: Queja (complaint) calls handle time 7.243 minutes, first-contact resolution 0.436 (n=117021).

## Notes
- The data does not separate dispute calls from other transactional calls: Transaccional is a superset of disputes, so the projection bounds them.
- Mean handle time is over calls with a duration; the calls without one are counted beside it, not imputed.
- The advisor-hour cost is assumed, not from any dataset; the projection labels it assumed and cites no dataset.
- Aggregates only: no row, identifier or text is written.
