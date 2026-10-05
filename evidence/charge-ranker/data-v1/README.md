---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# charge-ranker / data-v1

This run freezes the examples and the splits of the charge selector ([025](../../../docs/build/decisions/025-charge-selector.md)).

- **Data type:** simulation. The descriptions are team-generated. The transactions are real Gold rows. The label of each example is the id of the transaction that the description came from.
- **Rebuild:** `SENTINEL_GOLD_DUCKDB=<path> python -m eval.build_charge_splits`, from `sentinel-ai-core/`. The same Gold file and seed give `examples_hash`.
- **Content:** counts, hashes, the seed and the family list. It holds no rows and no customer ids.

## Cite these fields

| Question | Field |
|---|---|
| How many examples per split? | `splits.<split>.examples` |
| Are customers shared between splits? | `checks.customers_in_two_splits` |
| Do test-only families appear elsewhere? | `checks.test_only_families_outside_test` |
| Which dates does each split cover? | `splits.<split>.target_date_first`, `target_date_last` |
| How hard is the list of charges? | `splits.<split>.candidates_median`, `candidates_max` |

## Limits

- Train examples have shorter lists of charges than test examples. The list holds only the charges up to the day of the example, and train dates are earlier. The test is harder.
- About 80% of the examples name no merchant. The dataset has no merchant name for 77% of the charges.
- The pt-BR lines are twins of the es-419 lines (same pieces, same order). The test suite checks this. Back-translation of the five pt-BR lines, as in [017](../../../docs/build/decisions/017-portuguese.md): "Não reconheço a cobrança" is "I do not recognize the charge". "O que é a cobrança" is "What is the charge". "Revisando meu extrato vi um lançamento" is "Reviewing my statement I saw an entry". "ei me cobraram" is "hey, they charged me". "e eu não fiz isso" is "and I did not do that". The team wrote these. No native speaker reviewed them.
