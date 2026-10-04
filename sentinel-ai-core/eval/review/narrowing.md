# Narrowing report (MT-06, offline)

Development cases in `eval/cases/narrowing/mt06.jsonl`: the five MT-06 messages
that name a merchant, a date, an amount or a repeated charge, each in es-MX,
es-CO, es-AR and pt-BR, plus the accented-merchant line without the contradicting
date (`me cobraron en la cafetería` → TXN-1006). The mock is CUST-0001, reference
date 2026-06-17. No model call.

Right-charge-shown: the shown ids equal the expected ids. A not-found case
expects the newest four. Not-found-said: the reply carries `charge.not_found`
exactly when the case expects it.

| | right-charge-shown | not-found-said |
|---|---|---|
| Before (newest four, never the key) | 20/24 | 4/24 |
| After | 24/24 | 24/24 |

The four misses before are the cafetería cases: the old list included TXN-1006
among the newest four, so the right charge was present but not alone. The twenty
not-found cases already showed the newest four, and none of them said that
nothing matched (0/20). After, those twenty say `charge.not_found` and the four
cafetería cases show only TXN-1006.
