# Data assumptions

## Choice

The system assumes that each account belongs to México, Colombia or Argentina. Currency belongs to the product, not to the country. One customer can have products in the local currency and in USD. The canonical country name is `México`.

## Why

The data dictionary states these facts ([reference](../understand/reference/)):

- `customers.country` is "Country (Mexico, Colombia, Argentina)" and NOT NULL. No other account country exists.
- `products.currency` is "Currency (MXN, COP, ARS, USD)" and NOT NULL. Currency is per product.
- `transactions.transaction_country` is the country of the purchase. It includes Brazil, Spain and the USA. These are purchases abroad by customers of the three countries. They are not foreign accounts.

The measured data confirms them and shows one more fact:

| Fact | Evidence |
|---|---|
| México has no MXN product. Every Mexican product is in USD. | [`customer-360/dev-v1`](../../evidence/customer-360/dev-v1/summary.json): `products.by_country.México.currency` |
| `customers.country` has three levels and needs no normalization. | [`customer-360/dev-signals-v1`](../../evidence/customer-360/dev-signals-v1/summary.json): `labels.country_normalization.customer_country_levels`, `customer_rows_normalized` |
| `transaction_country` spells the country `Mexico` and `México`. The pipeline normalizes it. | `labels.country_normalization.transaction_rows_normalized` |
| A product never has transactions in another currency. | `customer-360/dev-v1`: `balance.currency_mismatch_product_vs_txn_pct` |

The dataset is synthetic ("no real customer information is included"). Its text is Spanish only ([what is real](../architecture/what-is-real.md)).

## Alternatives rejected

- **One currency per country.** This skips every USD charge of a Mexican customer. In this data, that is every Mexican charge.
- **Group by `transaction_country`.** This mixes purchases abroad into account statistics.

## Consequences

- A rule with a money value has one value per account country **and** currency ([policy thresholds](policy-thresholds.md)).
- Account statistics group by `customers.country`, not by `transaction_country`.
- The MXN group has no data, so it has no threshold. The demo Mexican MXN account is team-generated.
- Portuguese is a language requirement, not a market. No Brazilian account and no Portuguese text exist in the data. The system must still serve Portuguese ([REQ-0012](../requirements/frontend-backend.md#req-0012), [017](../build/decisions/017-portuguese.md)).

## In production

A bank has its own catalog of countries and currencies. The assumptions become configuration. A new country adds a policy file (REQ-0049).

## On the slide

"The data has accounts in three countries. Each account can have local and USD products. México has USD products only. We serve Portuguese without Portuguese data, and we say so."
