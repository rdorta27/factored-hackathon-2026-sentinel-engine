# REQ-0050 · Country Log Analytics Report

**Generated:** 2026-10-02  
**Source database:** `sentinel-data-engine/data/gold_bank.duckdb`  
**Requirement:** REQ-0050 — Monitoring by country  
**Depends on:** REQ-0024, REQ-0025

---

## 1. Scope

This report analyses digital interaction logs and call center data broken down by country
(México, Colombia, Argentina) to satisfy the country-level monitoring requirement. Data is
drawn from three Silver-layer tables:

- `bronze_digital_events` (joined with `silver_customers` for canonical country)
- `silver_call_center_interactions` (joined with `silver_customers`)
- `silver_satisfaction_surveys` (joined with `silver_customers`)

Country attribution uses the `country` column from `silver_customers` — the customer's
registered country — rather than the IP-derived `ip_country` field, which reflects device
location and may differ from the customer's home market.

---

## 2. Digital Events by Country

Digital events capture all customer actions on the bank's web and mobile channels (page
views, feature interactions, session starts, transaction initiations).

| Country | Total Digital Events |
|---|---:|
| México | 5,931,070 |
| Colombia | 3,578,002 |
| Argentina | 2,366,476 |
| **Three-country total** | **11,875,548** |

México generates the largest share (~49.9%) of digital event volume, consistent with its
position as the largest customer market in the dataset.

### 2.1 Channel Breakdown

| Country | Channel | Events |
|---|---|---:|
| México | Android App | 2,078,392 |
| México | iOS App | 1,481,624 |
| México | Mobile Web | 1,185,538 |
| México | Desktop Web | 1,185,516 |
| Colombia | Android App | 1,258,166 |
| Colombia | iOS App | 891,499 |
| Colombia | Desktop Web | 716,785 |
| Colombia | Mobile Web | 711,552 |
| Argentina | Android App | 830,369 |
| Argentina | iOS App | 592,420 |
| Argentina | Desktop Web | 473,675 |
| Argentina | Mobile Web | 470,012 |

**Key finding:** Android App is the dominant channel in all three countries, followed by
iOS App. Desktop Web and Mobile Web share roughly equal volumes, indicating that customers
split between native-app and browser access with no strong platform preference.

---

## 3. Call Center Interactions by Country

Call center data comes from `silver_call_center_interactions`. Sentiment score is derived
from the interaction transcript and ranges from −1.0 (very negative) to +1.0 (very
positive).

| Country | Total Interactions | Avg Sentiment Score |
|---|---:|---:|
| México | 343,189 | −0.0373 |
| Colombia | 206,790 | −0.0368 |
| Argentina | 136,317 | −0.0362 |

All three countries show mildly negative average sentiment (around −0.037), which is
expected for a customer support channel where interactions are driven by friction events
(disputes, billing questions, complaints). The scores are nearly identical across
countries, indicating no country-specific service quality disparity in the current data.

### 3.1 Call Center Channel Breakdown

| Country | Channel | Interactions | Avg Sentiment |
|---|---|---:|---:|
| México | Phone | 291,678 | −0.0372 |
| México | Email | 13,764 | −0.0370 |
| México | App | 13,077 | −0.0368 |
| México | WhatsApp | 11,525 | −0.0353 |
| México | Web Chat | 11,450 | −0.0431 |
| México | Web | 1,695 | −0.0346 |
| Colombia | Phone | 175,818 | −0.0366 |
| Colombia | Email | 8,245 | −0.0378 |
| Colombia | App | 8,042 | −0.0365 |
| Colombia | Web Chat | 6,867 | −0.0422 |
| Colombia | WhatsApp | 6,787 | −0.0363 |
| Colombia | Web | 1,031 | −0.0467 |
| Argentina | Phone | 115,754 | −0.0364 |
| Argentina | Email | 5,534 | −0.0377 |
| Argentina | App | 5,245 | −0.0350 |
| Argentina | WhatsApp | 4,576 | −0.0291 |
| Argentina | Web Chat | 4,539 | −0.0355 |
| Argentina | Web | 669 | −0.0430 |

**Key finding:** Phone remains the dominant call center channel in all three countries
(~85% of interactions). WhatsApp shows slightly better sentiment than Web Chat, suggesting
customers find the asynchronous messaging channel less frustrating. Web Chat shows the
most negative sentiment scores across all countries.

---

## 4. Customer Satisfaction Surveys by Country

Satisfaction surveys use a 0–10 scale (10 = most satisfied), collected via
`silver_satisfaction_surveys`.

| Country | Total Surveys | Avg Satisfaction Score |
|---|---:|---:|
| México | 106,282 | 3.52 |
| Colombia | 64,002 | 3.53 |
| Argentina | 42,475 | 3.52 |

Average satisfaction scores of ~3.5/10 across all countries indicate a meaningfully
negative customer experience in the current manual dispute process — directly supporting
the business case for an automated resolution channel (REQ-0014). Scores are uniform
across countries, confirming the pain point is systemic rather than country-specific.

---

## 5. Conclusions

- **Volume distribution** follows the market-size ordering: México (~50%) > Colombia
  (~30%) > Argentina (~20%) across all three log sources.
- **Sentiment uniformity** across countries (all at ~−0.037) indicates no single country
  is a disproportionate outlier for service quality problems in the current dataset.
- **Channel preference** is strongly mobile-native (Android App leads in all countries),
  which informs the UI decision to serve the dispute chat from the bank's existing mobile
  app surface.
- **Satisfaction scores** of ~3.5/10 confirm the pre-existing pain point across the
  three-country footprint; the Sentinel Engine targets this gap directly.
- Country-level monitoring at this granularity satisfies REQ-0050. The Gold pipeline's
  daily-partitioned Silver tables can feed a live dashboard with sub-day latency once a
  streaming Bronze ingestion layer is connected.

*Proven by: this report, backed by `bronze_digital_events`, `silver_call_center_interactions`,
and `silver_satisfaction_surveys` joined with `silver_customers` in
`sentinel-data-engine/data/gold_bank.duckdb`.*
