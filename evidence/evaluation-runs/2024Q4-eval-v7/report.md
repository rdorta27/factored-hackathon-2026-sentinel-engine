# Held-out measurement 2024Q4-eval-v7

Eval 2026-09-30+runner-v1 · seal 27ad2f1ba986b804 · n=405 · main block n=280, same case ids for every version.

## Accuracy by version

| Version | Accuracy | 95% interval | JSON failures | Cost USD (total) | Latency p50/p95 ms |
|---|---|---|---|---|---|
| baseline | 0.5393 | [0.425, 0.65] (descriptive) | 0/280 | 0.0 | 0.01/0.01 |
| router_v1 | 0.7429 | [0.6429, 0.8429] | 0/280 | 0.012428 | 1093.36/4225.12 |
| router_v2 | 0.9821 | [0.95, 1.0] | 0/280 | 0.036353 | 1078.96/4474.88 |

## Paired comparisons

- router_v1_vs_baseline: fixed 61, broken 4, net 57 of 280 (0.2036), interval [0.1107, 0.3], above zero: True
  - broken: ho-b56-es-AR, ho-b56-es-CO, ho-b56-es-MX, ho-b56-pt-BR
- router_v2_vs_baseline: fixed 124, broken 0, net 124 of 280 (0.4429), interval [0.3286, 0.55], above zero: True
- router_v2_vs_router_v1: fixed 67, broken 0, net 67 of 280 (0.2393), interval [0.1429, 0.3357], above zero: True

## By variant

### baseline (best variant: es-CO)
- es-AR: accuracy 0.5286 [0.4143, 0.6429] (descriptive) (n=70); net loss 3 of 70 shared bases; lost: ho-b06, ho-b46, ho-b67
- es-CO: accuracy 0.5714 [0.4571, 0.6857] (descriptive) (n=70); net loss 0 of 70 shared bases; lost: none
- es-MX: accuracy 0.5286 [0.4143, 0.6429] (descriptive) (n=70); net loss 3 of 70 shared bases; lost: ho-b07, ho-b54, ho-b67
- pt-BR: accuracy 0.5286 [0.4143, 0.6429] (descriptive) (n=70); net loss 3 of 70 shared bases; lost: ho-b07, ho-b46, ho-b63
### router_v1 (best variant: es-AR)
- es-AR: accuracy 0.7429 [0.6429, 0.8429] (n=70); net loss 0 of 70 shared bases; lost: none
- es-CO: accuracy 0.7429 [0.6429, 0.8429] (n=70); net loss 0 of 70 shared bases; lost: none
- es-MX: accuracy 0.7429 [0.6429, 0.8429] (n=70); net loss 0 of 70 shared bases; lost: none
- pt-BR: accuracy 0.7429 [0.6429, 0.8429] (n=70); net loss 0 of 70 shared bases; lost: none
### router_v2 (best variant: es-AR)
- es-AR: accuracy 0.9857 [0.9571, 1.0] (n=70); net loss 0 of 70 shared bases; lost: none
- es-CO: accuracy 0.9714 [0.9286, 1.0] (n=70); net loss 1 of 70 shared bases; lost: ho-b34
- es-MX: accuracy 0.9857 [0.9571, 1.0] (n=70); net loss 0 of 70 shared bases; lost: none
- pt-BR: accuracy 0.9857 [0.9571, 1.0] (n=70); net loss 0 of 70 shared bases; lost: none

## By intent

- baseline: charge 0.9079 [0.7763, 1.0] (descriptive) (n=76); missing 0.0 [0.0, 0.0] (n=68); out_of_scope 0.4412 [0.2059, 0.6765] (descriptive) (n=68); person 0.7647 [0.5735, 0.9265] (descriptive) (n=68)
- router_v1: charge 1.0 [1.0, 1.0] (n=76); missing 0.0 [0.0, 0.0] (n=68); out_of_scope 1.0 [1.0, 1.0] (n=68); person 0.9412 [0.8235, 1.0] (n=68)
- router_v2: charge 1.0 [1.0, 1.0] (n=76); missing 0.9265 [0.8088, 1.0] (n=68); out_of_scope 1.0 [1.0, 1.0] (n=68); person 1.0 [1.0, 1.0] (n=68)

## Stability

- baseline: agreement 1.0 over 0 recorded repetitions (n=0)
- router_v1: agreement 1.0 over 0 recorded repetitions (n=0)
- router_v2: agreement 0.9933 over 3 recorded repetitions (n=100)

## Noisy twins (descriptive, n=50)

- baseline: broken by noise 0, fixed 0 (n=50)
- router_v1: broken by noise 0, fixed 0 (n=50)
- router_v2: broken by noise 0, fixed 0 (n=50)

## Safety and system

Attacks n=75: code-decided 30 (baseline only), model-facing 45. End-to-end cases n=30.
- baseline: unsafe 0/105; missed transfers 45; cost per resolution not defined
- router_v1: unsafe 0/75; missed transfers 6; cost per resolution not defined
- router_v2: unsafe 0/75; missed transfers 0; cost per resolution not defined

Spend: USD 0.09247 over 950 live calls (cap 0.3). Prices: Fireworks model library, 2026-10-01 (decision 016).
Examples in v2: dv-b01-es-MX, dv-b03-pt-BR, dv-b10-pt-BR, dv-b14-es-CO, dv-b17-pt-BR, dv-b20-es-MX, dv-b24-es-CO, dv-b27-es-AR.

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Held-out set sealed by hash before measuring and measured once (decision 018).
- Component latency comes from the recorded live calls; system latency is replay time.
- Stability: router_v2 recorded three times on 25 bases.
