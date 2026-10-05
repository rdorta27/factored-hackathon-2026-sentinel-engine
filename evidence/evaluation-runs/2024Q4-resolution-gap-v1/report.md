# Resolution gap 2024Q4-resolution-gap-v1

Replay of 2024Q4-resolution-v2 · simulation over a mock store · n=56 · commit 0fd3bfce0184.

## Case labels

- both resolve: 16 of 56
- both fail: 40 of 56
- different: 0 of 56

## Ceiling of safe resolution

| Version | Attempted | Resolvable | Resolved | Ceiling share | Achieved share | Gap |
|---|---|---|---|---|---|---|
| baseline | 56 | 16 | 16 | 0.2857 | 1.0 | 0 |
| router_v2 | 56 | 16 | 16 | 0.2857 | 1.0 | 0 |

## Where the systems differ

- outcome differs: 0 of 56
- intent label differs: 0 of 56
- intent correct: baseline 4 of 56, router 4 of 56
- expected intent mix: {'charge': 4, 'missing': 52}

## Cause: ceiling

## Cases

| Case | May resolve | Baseline | Router | Label |
|---|---|---|---|---|
| res-eligible-mx-1001-1 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-mx-1001-2 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-mx-1001-3 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-mx-1001-4 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-mx-1006-1 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-mx-1006-2 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-mx-1006-3 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-mx-1006-4 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-co-2001-1 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-co-2001-2 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-co-2001-3 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-co-2001-4 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-ar-3001-1 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-ar-3001-2 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-ar-3001-3 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-eligible-ar-3001-4 | True | case_confirmation (charge) | case_confirmation (charge) | both_resolve |
| res-window-mx-1002-1 | False | text (charge) | text (charge) | both_fail |
| res-window-mx-1002-2 | False | text (charge) | text (charge) | both_fail |
| res-window-mx-1002-3 | False | text (charge) | text (charge) | both_fail |
| res-window-mx-1002-4 | False | text (charge) | text (charge) | both_fail |
| res-reversed-mx-1003-1 | False | text (charge) | text (charge) | both_fail |
| res-reversed-mx-1003-2 | False | text (charge) | text (charge) | both_fail |
| res-reversed-mx-1003-3 | False | text (charge) | text (charge) | both_fail |
| res-reversed-mx-1003-4 | False | text (charge) | text (charge) | both_fail |
| res-disputed-mx-1004-1 | False | text (charge) | text (charge) | both_fail |
| res-disputed-mx-1004-2 | False | text (charge) | text (charge) | both_fail |
| res-disputed-mx-1004-3 | False | text (charge) | text (charge) | both_fail |
| res-disputed-mx-1004-4 | False | text (charge) | text (charge) | both_fail |
| res-amount-mx-1101-1 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-mx-1101-2 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-mx-1101-3 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-mx-1101-4 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-mx-1102-1 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-mx-1102-2 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-mx-1102-3 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-mx-1102-4 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-co-2002-1 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-co-2002-2 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-co-2002-3 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-co-2002-4 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-co-2003-1 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-co-2003-2 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-co-2003-3 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-co-2003-4 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-ar-3002-1 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-ar-3002-2 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-ar-3002-3 | False | handoff (charge) | handoff (charge) | both_fail |
| res-amount-ar-3002-4 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-ar-3003-1 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-ar-3003-2 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-ar-3003-3 | False | handoff (charge) | handoff (charge) | both_fail |
| res-fraud-ar-3003-4 | False | handoff (charge) | handoff (charge) | both_fail |
| res-notmine-mx-1001-1 | False | handoff (charge) | handoff (charge) | both_fail |
| res-notmine-mx-1001-2 | False | handoff (charge) | handoff (charge) | both_fail |
| res-notmine-mx-1001-3 | False | handoff (charge) | handoff (charge) | both_fail |
| res-notmine-mx-1001-4 | False | handoff (charge) | handoff (charge) | both_fail |

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Simulation over a mock store, replay of committed recordings: no live call (decision 022).
- Resolvable means no handoff is required and the case may pass; policy sets this, not the router.
- Cause ceiling: both systems resolve every resolvable case, so no system can resolve more on this set.
