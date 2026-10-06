---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# ROI: break-even projection

**Status:** projection, not a measured saving. REQ-0057 (P1). Each figure on this page is a projection or a simulation. The page claims no saving.

**Purpose:** find the safe-resolution rate at which the monthly cost of the system equals the human cost that it replaces. The measured inputs are frozen. The advisor-hour cost is an assumption. The reader can replace it.

## Inputs, labelled by origin

| Input | Value | Origin | Source |
|---|---|---|---|
| Transactional (*Transaccional*) calls, 2023-06-17 to 2026-06-18 | 240,056 of 686,296 | measured | [call-center aggregates](../../evidence/roi/2023-2026-callcenter-v1/summary.json): `transactional_calls.n`, `window` |
| Mean handle time | 3.68 minutes (206,465 calls with a duration, 33,591 without one) | derived | same summary: `transactional.handle_time` |
| Human first-contact resolution | 0.9151 (219,671 of 240,056) | derived | same summary: `transactional.first_contact_resolution` |
| Human escalation share | 0.0993 (23,841 of 240,056) | derived | same summary: `transactional.escalation` |
| Monthly transactional volume | about 6,661 calls (240,056 over 36.0 months) | derived | same summary, same window |
| AI cost per attempted case | USD 0.00016 (per resolution USD 0.000561) | measured, simulated replay | [resolution run 2024Q4-resolution-v2](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json): `system.router_v2.cost_usd` |
| Infrastructure | USD 20 to 60 a month | estimated (team estimate, not validated pricing) | [cost](cost.md) |
| Advisor hour | USD 5 to 25 an hour | **assumed.** It cites no dataset. The reader can replace it | none |

The call-center data does not separate dispute calls from other transactional calls. *Transaccional* is a superset of disputes. This projection sets a bound for the dispute flow. It does not give a price for it.

Complaint (*Queja*) calls last 7.243 minutes and have a first-contact resolution of 0.436 (same summary, `complaint_calls`). They set an upper bound for the handle time.

## Formula

The break-even safe-resolution rate is `r*`:

```
system monthly cost  = infra + V × AI per attempted case
human cost replaced  = r × V × h × w
r*                   = (infra + V × AI per attempted) / (V × h × w)
```

Where:

- `V` is the monthly transactional volume.
- `h` is the mean handle time in hours (3.68 min = 0.0613 h).
- `w` is the assumed advisor hour.

The system pays for itself when the safe-resolution share `r` reaches `r*`.

- System monthly cost: USD 21.07 (infra 20) to 61.07 (infra 60). It includes USD 1.07 of AI at full volume.
- Human monthly cost of all transactional calls: `V × h × w` = 409 hours × `w`.

## Sensitivity over the assumed advisor hour

| Advisor hour (assumed) | Human cost of all transactional calls / month | Break-even safe-resolution rate (infra 20 / 60) |
|---|---|---|
| USD 5 | USD 2,043 | 1.03% / 2.99% |
| USD 10 | USD 4,085 | 0.52% / 1.49% |
| USD 15 | USD 6,128 | 0.34% / 1.00% |
| USD 20 | USD 8,170 | 0.26% / 0.75% |
| USD 25 | USD 10,213 | 0.21% / 0.60% |

The measured simulated rate is **16 of 56 = 0.2857** safe resolutions (numerator 16, denominator 56). It is a **simulation** over a mock store ([resolution run 2024Q4-resolution-v2](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json), decision 022). It is not field behavior. It is above each break-even rate in the table.

## The headroom finding, plainly

The break-even rate is low. Do not read this as a win. The rate is low because the monthly fixed cost is tens of USD. It is not low because the system displaces a large human cost.

- Humans already resolve 91.51% of transactional calls at first contact, in 3.68 minutes.
- The saving for each displaced call is one advisor call of 3.7 minutes.
- The addressable volume is the minority that humans do not resolve at first contact (8.49%).
- 9.93% of calls are escalated at an extra cost that this projection does not price.

A real saving claim needs three inputs: the dispute-only volume (the data does not separate it), the escalation cost and a field resolution rate. This page measures none of them.

## What is not claimed

- No measured saving. Each figure is a projection (a formula over labelled inputs) or a simulation (a mock store).
- No price on an unsafe outcome. The report gives safety apart (unsafe outcome rate). It never converts safety to money.
- No saving from better handoffs. The containment and handoff figures come from the same simulation. This page does not convert them to money.
- No field resolution rate. 0.2857 is a simulated rate over 14 situations on a mock store.
- No production volume forecast. `V` is the dataset history of 2023–2026. It is not a claim about future call volume.

**Related:** [metrics report](metrics-report.md), [cost](cost.md) and [metrics](metrics.md).
