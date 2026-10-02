# Selection run 2024Q4-select-v2

Development split, n=164.

| Model | Accuracy | 95% interval | JSON failures | pt-BR net loss | Cost USD |
|---|---|---|---|---|---|
| `accounts/fireworks/models/gpt-oss-120b` | 0.4878 | [0.3742, 0.6076] | 37/164 | 1 of 30 | 0.010556 |
| `accounts/fireworks/models/glm-5p3-flash` | 0.7805 | [0.6702, 0.8882] | 0/164 | -1 of 30 | 0.007083 |
| `accounts/fireworks/models/deepseek-v4p1-flash` | 0.7317 | [0.6228, 0.8412] | 9/164 | -3 of 30 | 0.040459 |
| `accounts/fireworks/models/glm-5p3` | 0.6829 | [0.5642, 0.8026] | 0/164 | 1 of 30 | 0.064504 |

Keyword baseline: accuracy 0.6829 (n=164).

## Route rules

### heuristic: 0.2012 of turns to strong
- accounts/fireworks/models/gpt-oss-120b + accounts/fireworks/models/deepseek-v4p1-flash: accuracy 0.5671 [0.4573, 0.6788] (n=164)
- accounts/fireworks/models/gpt-oss-120b + accounts/fireworks/models/glm-5p3: accuracy 0.5366 [0.4194, 0.6529] (n=164)
- accounts/fireworks/models/glm-5p3-flash + accounts/fireworks/models/deepseek-v4p1-flash: accuracy 0.7805 [0.6703, 0.8882] (n=164)
- accounts/fireworks/models/glm-5p3-flash + accounts/fireworks/models/glm-5p3: accuracy 0.75 [0.6429, 0.8581] (n=164)
### keyword_miss: 0.7866 of turns to strong
- accounts/fireworks/models/gpt-oss-120b + accounts/fireworks/models/deepseek-v4p1-flash: accuracy 0.6463 [0.5353, 0.7578] (n=164)
- accounts/fireworks/models/gpt-oss-120b + accounts/fireworks/models/glm-5p3: accuracy 0.628 [0.5063, 0.7429] (n=164)
- accounts/fireworks/models/glm-5p3-flash + accounts/fireworks/models/deepseek-v4p1-flash: accuracy 0.7317 [0.6228, 0.8412] (n=164)
- accounts/fireworks/models/glm-5p3-flash + accounts/fireworks/models/glm-5p3: accuracy 0.7134 [0.5978, 0.8323] (n=164)
### strong: 1.0 of turns to strong
- accounts/fireworks/models/gpt-oss-120b + accounts/fireworks/models/deepseek-v4p1-flash: accuracy 0.7317 [0.6228, 0.8412] (n=164)
- accounts/fireworks/models/gpt-oss-120b + accounts/fireworks/models/glm-5p3: accuracy 0.6829 [0.5642, 0.8026] (n=164)
- accounts/fireworks/models/glm-5p3-flash + accounts/fireworks/models/deepseek-v4p1-flash: accuracy 0.7317 [0.6228, 0.8412] (n=164)
- accounts/fireworks/models/glm-5p3-flash + accounts/fireworks/models/glm-5p3: accuracy 0.6829 [0.5642, 0.8026] (n=164)

Spend: USD 0.063074 over 157 live calls (cap 0.15).

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Selection run on the development split only (016 amendment).
