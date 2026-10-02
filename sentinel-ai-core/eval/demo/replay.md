# Demo replay

Stage directions for the video. Customer lines are in the variant; everything else is English. The served app is the keyword baseline. After login, set the language selector. The session country starts the chrome in Spanish. Do not open a case on the ambiguous beat. Do not type `R$` on the Mexican charge.

Login password for the three demo customers is the shared test password. These rows are the mock Gold store, not real Gold. The account does not change with the variant: the charge lives on one customer. Twelve scripts are in `pt-br.jsonl`.

The video uses two of them (`docs/build/delivery.md`): normal in es-419 (the es-MX line is the one to type), ambiguous in pt-BR.

## 1. Normal, Mexico account, Cafe Central, 320 MXN, TXN-1006

Log in as `CUST-0001`. Select the variant. Type the line. Expect a confirm box, not a case number. Confirm `TXN-1006`. Expect a verified case. Currency stays MXN.

| Variant | Line |
|---|---|
| es-MX | Vi en mi estado de cuenta un cargo de 320 pesos mexicanos de Cafe Central del 12 de junio y no lo reconozco. |
| es-CO | No reconozco el cobro de 320 pesos mexicanos en Cafe Central, el día 12 de junio. |
| es-AR | En el resumen me figura un cargo de 320 pesos mexicanos de Cafe Central del 12 de junio y no lo reconozco. |
| pt-BR | não reconheço uma cobrança de 320 no Cafe Central em 12 de junho |

## 2. Ambiguous, Colombia account

Log in as `CUST-0002`. Select the variant. Type the first line, then the second. Expect candidate chips both times. Nothing opens.

| Variant | Lines |
|---|---|
| es-MX | No reconozco un cargo. / No lo reconozco, ¿lo pueden revisar? |
| es-CO | No reconozco un cobro. / ¿Lo pueden revisar? |
| es-AR | Me figura un cargo y no lo reconozco. / ¿Lo revisan? |
| pt-BR | não reconheço uma cobrança / não reconheço, pode revisar? |

## 3. Human, Argentina account

Log in as `CUST-0003`. Select the variant. Type the line twice, or press the person button twice after selecting `pt-BR` or `es-419`. The first turn offers help. The second files a handoff. Package country is `AR`. Package language is `es-419` or `pt-BR`.

| Variant | Line |
|---|---|
| es-MX, es-CO, es-AR | Quiero hablar con un asesor. |
| pt-BR | quero falar com um atendente |

## Do not show

A Pix ask hands off. A bare extrato or fatura ask shows the account's charges. Do not treat those two words as out of scope: the sealed set uses them inside charge inquiries.
