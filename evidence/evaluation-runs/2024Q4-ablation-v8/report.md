# Ablation 2024Q4-ablation-v8 (prompt v3 examples on development)

Cases: 198 development, same cases for every config. No sealed case read.

- v3_no_examples (0 examples): kind 0.9848; subtype 1.0; cost USD 0.023847 (n=198); latency p50/p95 ms 0.46/0.72.
- v3_4_examples (4 examples): kind 0.9747; subtype 1.0; cost USD 0.034982 (n=198); latency p50/p95 ms 2401.05/5619.01.
- v3_8_examples (8 examples): kind 0.9798; subtype 0.975; cost USD 0.046462 (n=198); latency p50/p95 ms 2304.05/5209.83.
- v3_32_examples (32 examples): kind 0.9899; subtype 1.0; cost USD 0.119385 (n=198); latency p50/p95 ms 2119.98/4996.81.

Spend: USD 0.197 over 581 live calls (cap 1.0). Time 1647.1 s.
