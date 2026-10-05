# Analysis of 2024Q4-eval-v8 (post hoc, descriptive)

Cases: main 308. No live call. The case text stays in the sealed set.

## M1 · Failure categories by intent, language and country

### trained_baseline: 30 wrong of 308
- out_of_scope->charge: 3 (v8i-44-es-CO, v8i-44-es-MX, v8i-44-pt-BR)
- out_of_scope->missing: 2 (v8i-41-pt-BR, v8i-44-es-AR)
- status->charge: 15 (v8i-33-pt-BR, v8i-35-es-AR, v8i-35-es-CO, v8i-35-es-MX, v8i-35-pt-BR, v8i-36-es-AR, v8i-36-es-CO, v8i-36-es-MX, v8i-36-pt-BR, v8i-37-es-AR, v8i-37-es-CO, v8i-37-es-MX, v8i-37-pt-BR, v8i-53-es-CO, v8i-53-es-MX)
- status->missing: 1 (v8i-34-pt-BR)
- status->out_of_scope: 8 (v8i-34-es-AR, v8i-34-es-CO, v8i-34-es-MX, v8i-52-es-AR, v8i-52-es-MX, v8i-52-pt-BR, v8i-53-es-AR, v8i-53-pt-BR)
- status->person: 1 (v8i-52-es-CO)

### router_v2: 56 wrong of 308
- missing->out_of_scope: 26 (v8i-23-es-AR, v8i-23-es-CO, v8i-23-es-MX, v8i-23-pt-BR, v8i-24-es-AR, v8i-24-es-CO, v8i-24-es-MX, v8i-24-pt-BR, v8i-25-es-AR, v8i-25-es-CO, v8i-25-es-MX, v8i-25-pt-BR, v8i-26-es-AR, v8i-26-es-CO, v8i-26-es-MX, v8i-26-pt-BR, v8i-27-es-AR, v8i-27-es-CO, v8i-27-es-MX, v8i-27-pt-BR, v8i-28-es-CO, v8i-28-es-MX, v8i-29-es-AR, v8i-29-es-CO, v8i-29-es-MX, v8i-29-pt-BR)
- missing->person: 2 (v8i-28-es-AR, v8i-28-pt-BR)
- status->charge: 12 (v8i-33-es-AR, v8i-33-es-CO, v8i-33-es-MX, v8i-35-pt-BR, v8i-36-es-AR, v8i-36-es-CO, v8i-36-es-MX, v8i-36-pt-BR, v8i-37-es-AR, v8i-37-es-CO, v8i-37-es-MX, v8i-37-pt-BR)
- status->out_of_scope: 16 (v8i-33-pt-BR, v8i-34-es-AR, v8i-34-es-CO, v8i-34-es-MX, v8i-34-pt-BR, v8i-35-es-AR, v8i-35-es-CO, v8i-35-es-MX, v8i-52-es-AR, v8i-52-es-CO, v8i-52-es-MX, v8i-52-pt-BR, v8i-53-es-AR, v8i-53-es-CO, v8i-53-es-MX, v8i-53-pt-BR)

### router_v3: 4 wrong of 308
- status->out_of_scope: 4 (v8i-52-es-AR, v8i-52-es-CO, v8i-52-es-MX, v8i-52-pt-BR)

## M2 · Trained baseline, highest-weight n-grams per intent

- charge: `eco` 0.9073, `·de` 0.843, `·cob` 0.8231, `·cobr` 0.8231, `cob` 0.8231, `cobr` 0.8231, `obr` 0.8128, `rec` 0.7449, `·rec` 0.7358, `·re` 0.7357, `·reco` 0.6945, `econ` 0.6945
- missing: `rob` 0.6637, `uda` 0.6543, `·algo` 0.6441, `algo` 0.6441, `algo·` 0.6441, `lgo` 0.6441, `lgo·` 0.6441, `ema·` 0.57, `ias` 0.5343, `·prob` 0.4948, `blem` 0.4948, `blema` 0.4948
- out_of_scope: `al·` 0.5975, `edi` 0.5819, `·sald` 0.5801, `ald` 0.5801, `aldo` 0.5801, `aldo·` 0.5801, `ldo` 0.5801, `ldo·` 0.5801, `sald` 0.5801, `saldo` 0.5801, `ta·` 0.5796, `pres` 0.5661
- person: `or·` 1.1552, `end` 0.7769, `lar·` 0.6599, `·at` 0.6591, `ende` 0.6089, `ente·` 0.5867, `nte·` 0.5867, `me·` 0.5818, `ente` 0.5766, `·hu` 0.5706, `·hum` 0.5706, `·huma` 0.5706
- status: `·ul` 0.7693, `·ult` 0.7693, `·ulti` 0.7693, `lti` 0.7693, `ltim` 0.7693, `ult` 0.7693, `ulti` 0.7693, `ultim` 0.7693, `·esta` 0.7446, `estad` 0.7354, `stad` 0.7354, `stado` 0.7354

The model reads character n-grams of three to five characters, not words. A dot is a space.
The weights show the substrings that push each intent: `cobr` (cobro) for charge, `algo` and `blema` (problema) for missing,
`sald` (saldo) for out of scope, `ende` (entiende) and `huma` (humano) for person, `ultim` and `estad` (estado) for status.


## M4 · Complementarity (post hoc, descriptive)

- router_v2_vs_trained_baseline: both right 247, both wrong 25, only router 5, only trained 31, net -26 [-0.1591, -0.013] of 308
- router_v3_vs_trained_baseline: both right 274, both wrong 4, only router 26, only trained 4, net 22 [0.0097, 0.1364] of 308

The TF-IDF to LLM cascade is a projection, not a measurement.

## Post hoc sensitivity of router_v3

- candidates: unavailable 4 of 308; kind 0.974 all, 0.9868 without; subtype 0.8971 all, 0.9385 without
- noisy: unavailable 3 of 52; kind 0.9423 all, 1.0 without; subtype not defined all, None without
- attacks: unavailable 6 of 84; kind 0.8095 all, 0.8718 without; subtype not defined all, None without
- topup: unavailable 17 of 92; kind 0.7717 all, 0.9467 without; subtype not defined all, None without

Not the measurement. It changes no gate and no verdict.

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Post hoc and descriptive: the analysis reads the frozen 2024Q4-eval-v8 run and its recordings. It makes no live call and changes no gate.
- The case text stays in the sealed set. This page names cases by id only.
- The replay turns the rows that the frozen summary labels unavailable into predictions. The sensitivity section keeps the frozen view.
