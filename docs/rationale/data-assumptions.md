# Data assumptions

## Choice

The system assumes accounts belong only to México, Colombia and Argentina, and that currency belongs to the product, so one customer can hold accounts in their local currency and in USD. The canonical country name is `México`.

## Why

The data dictionary states both facts ([reference](../understand/reference/)):

- `customers.country`: "Country (Mexico, Colombia, Argentina)", NOT NULL. There is no other account country.
- `products.currency`: "Currency (MXN, COP, ARS, USD)", NOT NULL. Currency is per product; nothing ties a country to one currency.
- `transactions.transaction_country`: "Country where transaction occurred". It names where a purchase happened, so it includes foreign countries such as Brazil, Spain or the USA. Those are customers of the three countries buying abroad, not foreign accounts.

The dataset is fully synthetic ("no real customer information is included") and its text is Spanish only. The source spells the country both `México` and `Mexico`; the pipeline's Silver layer normalizes to `México`. The `Mexico` variant appears in `transaction_country` for purchases made in Mexico, not in the account country.

Checked on the 2024Q4 transactions: Colombian and Argentine charges come in local currency and in USD, while every Mexican charge is in USD and none in MXN, so the MXN group has no data to set a threshold from ([dataset assumptions](../understand/dataset.md#assumptions)).

## Consequences

- Any rule with a money value is set per account country **and** currency ([policy thresholds](policy-thresholds.md)).
- Statistics about accounts group by `customers.country`, never by `transaction_country`.
- Portuguese is a language requirement, not a market: there is no Brazilian account and no Portuguese text in the data, yet the system must serve Portuguese ([REQ-0012](../requirements/frontend-backend.md#req-0012)). A Portuguese-speaking customer holds an MX, CO or AR account, and the Portuguese cases are checked through Spanish back-translation ([017](../build/decisions/017-portuguese.md)).

## Alternatives rejected

- **One currency per country:** silently skips every USD charge of a Mexican customer.
- **Grouping by `transaction_country`:** mixes foreign purchases into account statistics.

## In production

A real bank has its own country and currency catalog; the assumptions become configuration, and new countries add a policy file (REQ-0049).

## On the slide

"The data covers accounts in three countries, each able to hold local and USD products. Portuguese is served without Portuguese data, and we say so."
