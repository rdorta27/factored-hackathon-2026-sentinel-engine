# Flow measurements

What the measurement script returned for each candidate flow. **This page is generated** by [`scripts/render_flow_measurements.py`](../../../scripts/render_flow_measurements.py) from the latest frozen `summary.json`; do not edit it by hand. It holds results only. What they mean for the choice is in [flow selection](03-flow-selection.md); where the four flows come from is in [candidate flows](01-flow-candidates.md).

**Window:** 2024-10-01 to 2025-01-01 exclusive (92 days, by event date). Data from 2025-07-01 on is reserved for the final evaluation and was not read (`disputes.rows_in_heldout`).

## Source

Values come from run `2024Q4-v3` (script version `2026-09-28+q4-7030-v3`), stored in [`evidence/flows/2024Q4-v3/`](../../../evidence/flows/2024Q4-v3/README.md) with its method and data manifest. Earlier runs in `evidence/flows/` are subsets of it: every field they share has the same value (checked each time this page is generated). The raw data never enters the repository.

## Reading guide

- **Count** is a number of rows. **%** is a share or a spread, in percent.
- **Spread** = highest minus lowest rate among the values of one field. It is a one-field-at-a-time screen: it does not rule out a model that combines fields.
- Fields ending in `_learnable` are **fixed in code** (`false`), not computed. Read them together with the spreads.
- Field names ending in `_pp` keep the script's name; their values are in %.

## 1. Accounts and payments

| Field | Value | What it is |
|---|---|---|
| `accounts.decline_learnable` | false | Fixed in code: `false` when every spread is small. Not a proof |
| `accounts.decline_spread_pp.channel` | 0.71% | Spread of the non-approved rate (Declined, Pending or Reversed) across values of `channel` |
| `accounts.decline_spread_pp.merchant_category` | 0.53% | Spread of the non-approved rate (Declined, Pending or Reversed) across values of `merchant_category` |
| `accounts.decline_spread_pp.txn_category` | 0.5% | Spread of the non-approved rate (Declined, Pending or Reversed) across values of `txn_category` |
| `accounts.fraud_true` | 366 | Transactions with `is_fraud = True` |
| `accounts.n_calls` | 56,045 | Calls in the window (`call_center_interactions`) |
| `accounts.n_transactions` | 370,659 | Transactions in the window (event date) |
| `accounts.reason_category_degenerate` | true | `reason_category` mirrors `contact_reason`: calls carry no subcategory |
| `accounts.reason_transaccional` | 19,630 | Calls whose `contact_reason` is *Transaccional* (transactional) |
| `accounts.status_Approved` | 340,929 | Transactions with status Approved |
| `accounts.status_Declined` | 18,652 | Transactions with status Declined |
| `accounts.status_Pending` | 7,316 | Transactions with status Pending |
| `accounts.status_Reversed` | 3,762 | Transactions with status Reversed |
| `accounts.transaccional_products_blank` | 11,776 | *Transaccional* calls with a blank product field |
| `accounts.transaccional_products_blank_pct` | 59.99% | Same, as a share of *Transaccional* calls |

**Derived figures** (formula over the fields above; 92 days in the window):

| Figure | Formula | Value |
|---|---|---|
| Transactional share of calls | reason_transaccional ÷ n_calls | 35.03% |
| Transactional calls per day | reason_transaccional ÷ days | 213.4 |
| Approved share of transactions | status_Approved ÷ n_transactions | 91.98% |
| Declined share of transactions | status_Declined ÷ n_transactions | 5.03% |
| Pending share of transactions | status_Pending ÷ n_transactions | 1.97% |
| Reversed share of transactions | status_Reversed ÷ n_transactions | 1.01% |

## 2. Cards

| Field | Value | What it is |
|---|---|---|
| `cards.actionable` | 29,730 | Transactions Declined, Pending or Reversed |
| `cards.blocked` | 16,233 | Products with status Blocked, **all product types**, filtered snapshot |
| `cards.blocked_learnable` | false | Fixed in code, same caveat |
| `cards.blocked_spread_pp` | 0.98% | Spread of the Blocked rate across product types (all products) |
| `cards.credit_cards` | 81,895 | Products of type *Tarjeta Crédito* (credit card) in the filtered snapshot |
| `cards.fraud_true` | 366 | Transactions with `is_fraud = True` (same count as `accounts.fraud_true`) |

**Derived figures** (formula over the fields above; 92 days in the window):

| Figure | Formula | Value |
|---|---|---|
| Non-approved share of transactions | actionable ÷ accounts.n_transactions | 8.02% |
| Fraud share of transactions | fraud_true ÷ accounts.n_transactions | 0.10% |
| Blocked share of all products | blocked ÷ credit.n_products | 4.96% |

## 3. Disputes

| Field | Value | What it is |
|---|---|---|
| `disputes.claims` | 1,383 | Complaints with `case_type = Claim` (claims) |
| `disputes.cnr_learnable` | false | Fixed in code, same caveat |
| `disputes.cnr_spread_pp.priority` | 0.96% | Spread of the unrecognized-charge claim rate across values of `priority` (all complaints) |
| `disputes.cnr_spread_pp.reception_channel` | 4.72% | Spread of the unrecognized-charge claim rate across values of `reception_channel` (all complaints) |
| `disputes.description_leak` | 5,611 | Complaints whose `description` contains their `category` |
| `disputes.dispute_share_ci95pp` | 0.54% | 95% interval half-width of that share (normal approximation) |
| `disputes.dispute_share_pct` | 4.47% | `unrecognized_claim` as a share of `disputes.n` |
| `disputes.dup_extra_rows` | 0 | Extra rows repeating a `complaint_id` |
| `disputes.esc_agent_spread_pp` | 0% – 26.7% | Lowest and highest escalation rate across agents with at least 20 calls |
| `disputes.esc_learnable` | false | Fixed in code, same caveat |
| `disputes.esc_spread_pp.accent` | 0.65% | Spread of the call escalation rate across values of `accent` |
| `disputes.esc_spread_pp.channel` | 1.59% | Spread of the call escalation rate across values of `channel` |
| `disputes.esc_spread_pp.contact_reason` | 0.84% | Spread of the call escalation rate across values of `contact_reason` |
| `disputes.esc_spread_pp.interaction_type` | 0.97% | Spread of the call escalation rate across values of `interaction_type` |
| `disputes.esc_spread_pp.wait_bucket` | 1.09% | Spread of the call escalation rate across values of `wait_bucket` |
| `disputes.escalated_by_reason.Comercial` | 456 | Escalated calls with `contact_reason = Comercial` |
| `disputes.escalated_by_reason.Producto` | 1,239 | Escalated calls with `contact_reason = Producto` |
| `disputes.escalated_by_reason.Queja` | 988 | Escalated calls with `contact_reason = Queja` |
| `disputes.escalated_by_reason.Retención` | 164 | Escalated calls with `contact_reason = Retención` |
| `disputes.escalated_by_reason.Transaccional` | 1,970 | Escalated calls with `contact_reason = Transaccional` |
| `disputes.escalated_by_reason.Técnico` | 818 | Escalated calls with `contact_reason = Técnico` |
| `disputes.escalated_calls` | 5,635 | Calls with `was_escalated = True` |
| `disputes.escalated_calls_n` | 56,045 | Calls in the window (denominator) |
| `disputes.join_hit` | 14,023 | Transcripts whose `interaction_id` matches a call in the window |
| `disputes.leak_fill_open_pct.assigned_agent_id` | 56.82% | Share of **open** complaints with `assigned_agent_id` filled |
| `disputes.leak_fill_open_pct.assignment_date` | 56.67% | Share of **open** complaints with `assignment_date` filled |
| `disputes.leak_fill_open_pct.closing_date` | 0% | Share of **open** complaints with `closing_date` filled |
| `disputes.leak_fill_open_pct.compensation_granted` | 0% | Share of **open** complaints with `compensation_granted` filled |
| `disputes.leak_fill_open_pct.first_response_date` | 50.44% | Share of **open** complaints with `first_response_date` filled |
| `disputes.leak_fill_open_pct.resolution` | 0% | Share of **open** complaints with `resolution` filled |
| `disputes.leak_fill_open_pct.resolution_date` | 0% | Share of **open** complaints with `resolution_date` filled |
| `disputes.leak_fill_open_pct.resolution_days` | 0% | Share of **open** complaints with `resolution_days` filled |
| `disputes.leak_fill_open_pct.resolution_satisfaction` | 0% | Share of **open** complaints with `resolution_satisfaction` filled |
| `disputes.leak_fill_open_pct.sla_breached` | 100% | Share of **open** complaints with `sla_breached` filled |
| `disputes.leak_fill_terminal_pct.assigned_agent_id` | 91.34% | Share of **closed** complaints with `assigned_agent_id` filled |
| `disputes.leak_fill_terminal_pct.assignment_date` | 90.84% | Share of **closed** complaints with `assignment_date` filled |
| `disputes.leak_fill_terminal_pct.closing_date` | 15.84% | Share of **closed** complaints with `closing_date` filled |
| `disputes.leak_fill_terminal_pct.compensation_granted` | 27.2% | Share of **closed** complaints with `compensation_granted` filled |
| `disputes.leak_fill_terminal_pct.first_response_date` | 92.26% | Share of **closed** complaints with `first_response_date` filled |
| `disputes.leak_fill_terminal_pct.resolution` | 90.48% | Share of **closed** complaints with `resolution` filled |
| `disputes.leak_fill_terminal_pct.resolution_date` | 90.34% | Share of **closed** complaints with `resolution_date` filled |
| `disputes.leak_fill_terminal_pct.resolution_days` | 91.48% | Share of **closed** complaints with `resolution_days` filled |
| `disputes.leak_fill_terminal_pct.resolution_satisfaction` | 14.56% | Share of **closed** complaints with `resolution_satisfaction` filled |
| `disputes.leak_fill_terminal_pct.sla_breached` | 100% | Share of **closed** complaints with `sla_breached` filled |
| `disputes.linkage_filled` | 0 | Complaints with `origin_interaction_id` filled |
| `disputes.n` | 5,611 | Complaints created in the window |
| `disputes.regulator_cnr_n` | 10 | Of those, unrecognized-charge claims |
| `disputes.regulator_n` | 46 | Complaints received through the Regulator channel (filed via the financial regulator) |
| `disputes.rows_in_heldout` | 0 | Rows dated inside the held-out zone (must be 0) |
| `disputes.text_prefixes` | 2 | Distinct 60-character prefixes of `customer_text` across all transcripts |
| `disputes.transcripts` | 14,023 | Transcripts in the window |
| `disputes.unrecognized_claim` | 251 | Claims whose `subcategory` is *Cargo no reconocido* (unrecognized charge) |
| `disputes.unrecognized_complaint` | 611 | Complaints (`case_type = Complaint`) with the same subcategory |

**Derived figures** (formula over the fields above; 92 days in the window):

| Figure | Formula | Value |
|---|---|---|
| Unrecognized-charge claims per day | unrecognized_claim ÷ days | 2.7 |
| Unrecognized-charge claims and complaints | unrecognized_claim + unrecognized_complaint | 862 |
| Claims share of complaints | claims ÷ n | 24.65% |
| Description leak share | description_leak ÷ n | 100.00% |
| Linkage share | linkage_filled ÷ n | 0.00% |
| Transcript join share | join_hit ÷ transcripts | 100.00% |
| Regulator share of complaints | regulator_n ÷ n | 0.82% |
| Call escalation share | escalated_calls ÷ escalated_calls_n | 10.05% |

## 4. Credit

| Field | Value | What it is |
|---|---|---|
| `credit.delinq_learnable` | false | Fixed in code, same caveat |
| `credit.delinq_spread_pp` | 0.48% | Spread of the share above 30 days past due across the three loan types (*Préstamo Personal*, *Préstamo Hipotecario*, *Tarjeta Crédito*) |
| `credit.delinquent` | 15,321 | Products with `days_past_due` above 0 |
| `credit.n_products` | 327,035 | Products in the snapshot after the `last_updated` filter (all types) |

**Derived figures** (formula over the fields above; 92 days in the window):

| Figure | Formula | Value |
|---|---|---|
| Delinquent share of products | delinquent ÷ n_products | 4.68% |

## Reproduce

```bash
python3 scripts/render_flow_measurements.py            # rewrite this page
python3 scripts/render_flow_measurements.py --verify   # fresh run in a subprocess, compared with this data
```

`--verify` needs the raw data (gitignored) in `evidence/flows/data/`, or the folder in `$FLOW_DATA_DIR` or `--data`. A new run goes in a new folder under `evidence/flows/`; add it to `RUNS` in the script.
