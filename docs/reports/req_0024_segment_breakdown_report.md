# REQ-0024 · Customer Segment & Multi-Currency Dispute Breakdown

**Generated:** 2026-10-02  
**Source database:** `sentinel-data-engine/data/gold_bank.duckdb`  
**Requirement:** REQ-0024 — Breakdown by language, country and segment  
**Dispute source view:** `v_service_dispute_eligible_transactions`

---

## 1. Scope

This report provides the segment-level and multi-currency breakdown of transaction volume
and dispute eligibility required by REQ-0024. It uses the PII-free service view
`v_service_dispute_eligible_transactions`, which already carries the `customer_segment`
column pre-joined from `gold_dispute_customer_360`.

**Eligibility window:** 2026-03-19 to 2026-06-17 (90 days)  
**Excluded statuses:** `Reversed`, `Refunded`  
**Total transactions in view:** 4,425,008  
**Total eligible:** 373,443 (8.4%)

> **Currency note:** All `amount` figures are in the original transaction currency
> (MXN, COP, ARS, or USD). No exchange-rate conversion is applied. Amounts expressed in
> ARS and COP are significantly larger in nominal terms than USD equivalents.

---

## 2. Transaction Volume & Dispute Eligibility by Segment

| Segment | Total Transactions | Eligible Count | Eligibility Rate | Total Amount (native currency) | Eligible Amount (native currency) |
|---|---:|---:|---:|---:|---:|
| Basic | 2,650,179 | 223,084 | 8.42% | 5,080,105,800,631.58 | 424,751,206,800.46 |
| Plus | 1,110,263 | 94,319 | 8.50% | 2,114,932,971,051.21 | 182,526,126,596.93 |
| Premium | 443,830 | 37,451 | 8.44% | 847,179,625,041.45 | 72,265,237,237.99 |
| Student | 220,736 | 18,589 | 8.42% | 425,790,656,576.17 | 35,497,835,461.70 |
| **Total** | **4,425,008** | **373,443** | **8.44%** | **8,468,009,053,300.41** | **715,040,406,097.08** |

**Observations:**

- Eligibility rate is remarkably uniform across all four segments (8.42–8.50%), confirming
  that dispute exposure probability does not vary significantly by customer tier in the
  synthetic dataset.
- **Basic** customers account for 59.9% of total transactions and 59.7% of eligible
  disputes — their dominance reflects the largest customer base.
- **Student** customers have the smallest absolute eligible count (18,589) and the lowest
  total amount, consistent with lower-value, higher-frequency spending patterns.

---

## 3. Multi-Currency Dispute Exposure by Country

The three core markets each transact in their domestic currency (MXN for México, COP for
Colombia, ARS for Argentina) plus some cross-border USD exposure.

| Country | Currency | Transactions | Total Amount | Eligible Amount |
|---|---|---:|---:|---:|
| México | USD | 2,126,409 | 3,564,080,968.12 | 300,712,548.21 |
| México | ARS | 7,995 | 4,558,078,275.90 | 435,379,031.05 |
| México | COP | 11,905 | 79,613,656,020.34 | 6,646,039,886.61 |
| Colombia | COP | 1,134,801 | 7,597,980,559,948.35 | 642,533,589,951.43 |
| Colombia | ARS | 7,983 | 4,658,453,920.23 | 419,277,426.81 |
| Colombia | USD | 146,719 | 246,730,249.12 | 20,834,229.17 |
| Argentina | ARS | 752,794 | 441,537,542,671.64 | 37,054,135,573.86 |
| Argentina | COP | 12,059 | 80,318,690,311.28 | 7,266,440,952.18 |
| Argentina | USD | 102,708 | 170,519,488.47 | 14,515,196.49 |

**Observations:**

- **México** is predominantly a USD-denominated market in this dataset (2.1M transactions
  in USD vs. ~20K in other currencies), suggesting international or cross-border card
  usage is the primary transaction type in the Mexican cohort.
- **Colombia** is the largest COP exposure pool (7.6T COP total; 642B COP eligible),
  making it the country with the highest nominal eligible dispute exposure.
- **Argentina** transacts primarily in ARS (752K transactions, 441B ARS total).
- Cross-currency transactions exist in all three countries (small volumes of ARS and COP
  transactions in non-home markets), indicating international customer card usage.

---

## 4. High-Value Segment Monetary Exposure

Premium and Plus customers represent the highest revenue tier. The table below shows their
share of total and eligible transaction amounts.

| Metric | Value |
|---|---:|
| Premium + Plus share of total transaction amount | 34.98% |
| Premium + Plus share of eligible dispute amount | 35.63% |

High-value segments (Premium + Plus) represent approximately **35% of total monetary
exposure** despite constituting only ~35% of transactions, confirming near-proportional
monetary representation. Their slightly elevated share of eligible dispute exposure
(35.63% vs. 34.98%) is consistent with a modestly higher eligibility rate for the Plus
segment (8.50% vs. 8.42%).

**Business implication:** Prioritising Premium and Plus customers in the automated dispute
intake flow — through reduced wait times or proactive outreach — captures 35.6% of the
total dispute monetary exposure while serving only ~35% of the customer base, maximising
business ROI of the Sentinel Engine.

---

## 5. Conclusions

- **Eligibility rate is uniform (~8.4%)** across all four customer segments, indicating
  the 90-day eligibility window and status exclusion rules apply consistently regardless
  of customer tier.
- **Country-currency mapping** shows México as primarily USD-transacting, Colombia as
  the largest COP exposure, and Argentina as primarily ARS. Any multi-currency dispute
  handling must respect these native-currency contexts when presenting amounts to the
  customer (REQ-0041).
- **High-value segment priority:** Premium + Plus account for 35.6% of eligible dispute
  monetary exposure; targeted handling of this cohort delivers the highest financial
  impact per dispute resolved.
- The segment and currency breakdowns, combined with the language-accuracy breakdown in
  `evidence/evaluation-runs/2024Q4-eval-v7/summary.json` (`component.versions.<version>.breakdown`),
  fully satisfy REQ-0024.

*Proven by: this report, backed by `v_service_dispute_eligible_transactions` in
`sentinel-data-engine/data/gold_bank.duckdb`.*
