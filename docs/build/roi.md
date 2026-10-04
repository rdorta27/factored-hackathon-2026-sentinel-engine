# ROI: break-even projection

**Status:** projection, not a measured saving. REQ-0057 (P1). Every figure below is labelled a projection or a simulation; no saving is claimed.

**Purpose:** the safe-resolution rate at which the monthly cost of the system equals the human cost it replaces. The measured inputs are frozen; the advisor-hour cost is an assumption the reader can replace.

## Inputs, labelled by origin

| Input | Value | Origin | Source |
|---|---|---|---|
| Transactional (*Transaccional*) calls, 2023-06-17 to 2026-06-18 | 240,056 of 686,296 | measured | [call-center aggregates](../evidence/roi/2023-2026-callcenter-v1/summary.json): `transactional_calls.n`, `window` |
| Mean handle time | 3.68 minutes (206,465 calls with a duration; 33,591 without one) | derived | same summary: `transactional.handle_time` |
| Human first-contact resolution | 0.9151 (219,671 of 240,056) | derived | same summary: `transactional.first_contact_resolution` |
| Human escalation share | 0.0993 (23,841 of 240,056) | derived | same summary: `transactional.escalation` |
| Monthly transactional volume | about 6,661 calls (240,056 over 36.0 months) | derived | same summary, same window |
| AI cost per attempted case | USD 0.00016 (per resolution USD 0.000561) | measured, simulated replay | [resolution run 2024Q4-resolution-v2](../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json): `system.router_v2.cost_usd` |
| Infrastructure | USD 20 to 60 a month | estimated (team estimate, not validated pricing) | [cost](cost.md) |
| Advisor hour | USD 5 to 25 an hour | **assumed** — cites no dataset; replaceable by the reader | none |

The call-center data does not separate dispute calls from other transactional calls: *Transaccional* is a superset of disputes, so this projection bounds the dispute flow, it does not price it. Complaint (*Queja*) calls run 7.243 minutes at 0.436 first-contact resolution (same summary, `complaint_calls`) and bound the handle time from above.

## Formula

Break-even safe-resolution rate `r*`:

```
system monthly cost  = infra + V × AI per attempted case
human cost replaced  = r × V × h × w
r*                   = (infra + V × AI per attempted) / (V × h × w)
```

where `V` is the monthly transactional volume, `h` the mean handle time in hours (3.68 min = 0.0613 h) and `w` the assumed advisor hour. The system pays for itself when the safe-resolution share `r` reaches `r*`.

- System monthly cost: USD 21.07 (infra 20) to 61.07 (infra 60), including USD 1.07 of AI at full volume.
- Human monthly cost of all transactional calls: `V × h × w` = 409 hours × `w`.

## Sensitivity over the assumed advisor hour

| Advisor hour (assumed) | Human cost of all transactional calls / month | Break-even safe-resolution rate (infra 20 / 60) |
|---|---|---|
| USD 5 | USD 2,043 | 1.03% / 2.99% |
| USD 10 | USD 4,085 | 0.52% / 1.49% |
| USD 15 | USD 6,128 | 0.34% / 1.00% |
| USD 20 | USD 8,170 | 0.26% / 0.75% |
| USD 25 | USD 10,213 | 0.21% / 0.60% |

Beside it, the measured simulated rate: **16 of 56 = 0.2857** safe resolutions (numerator 16, denominator 56), a **simulation** over a mock store ([resolution run 2024Q4-resolution-v2](../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json), decision 022) — not field behaviour, and above every break-even rate in the table.

## The headroom finding, plainly

The break-even rate is low, and it is tempting to read that as a win. It is low because the monthly fixed cost is tens of USD, not because the system displaces a large human cost: humans already resolve 91.51% of transactional calls at first contact in 3.68 minutes. The saving per displaced call is one 3.7-minute advisor call, and the addressable volume is the minority not resolved at first contact (8.49%), with 9.93% escalated at extra cost this projection does not price. A real saving claim would need the dispute-only volume (not separated in the data), the escalation cost, and a field resolution rate; none of them is measured here.

## What is not claimed

- No measured saving: every figure is a projection (formula over labelled inputs) or a simulation (mock store).
- No price on an unsafe outcome: safety is reported separately (unsafe outcome rate), never converted to money.
- No saving from better handoffs: containment and handoff figures come from the same simulation and are not monetized.
- No field resolution rate: 0.2857 is a simulated rate over 14 situations on a mock store.
- No production volume forecast: `V` is the dataset's 2023–2026 history, not a claim about future call volume.

**Related:** [metrics report](metrics-report.md), [cost](cost.md), [metrics](metrics.md).
