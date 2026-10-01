# Data assumptions

## Choice

The system assumes accounts belong only to México, Colombia and Argentina, and that currency belongs to the product, so one customer can hold accounts in their local currency and in USD. The canonical country name is `México`.

## Why

The data dictionary states both facts ([reference](../understand/reference/)):

- `customers.country`: "Country (Mexico, Colombia, Argentina)", NOT NULL. There is no other account country.
- `products.currency`: "Currency (MXN, COP, ARS, USD)", NOT NULL. Currency is per product; nothing ties a country to one currency.
- `transactions.transaction_country`: "Country where transaction occurred". It names where a purchase happened, so it includes foreign countries such as Brazil, Spain or the USA. Those are customers of the three countries buying abroad, not foreign accounts.

The dataset is fully synthetic ("no real customer information is included") and its text is Spanish only. The source spells the country both `México` and `Mexico`; we normalize to `México`.

## Consequences

- Any rule with a money value is set per account country **and** currency ([policy thresholds](policy-thresholds.md)).
- Statistics about accounts group by `customers.country`, never by `transaction_country`.
- Portuguese is a language requirement, not a market: there is no Brazilian account and no Portuguese text in the data, yet the system must serve Portuguese ([REQ-0012](../requirements/frontend-backend.md#req-0012)). How it does so is open (decision 15).

## Alternatives rejected

- **One currency per country:** silently skips every USD charge of a Mexican customer.
- **Grouping by `transaction_country`:** mixes foreign purchases into account statistics.

## In production

A real bank has its own country and currency catalog; the assumptions become configuration, and new countries add a policy file (REQ-0049).

## On the slide

"The data covers accounts in three countries, each able to hold local and USD products. Portuguese is served without Portuguese data, and we say so."
