---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# ADR 023 – PII Handling in the Gold Layer

| Field       | Value                               |
|-------------|-------------------------------------|
| Status      | Accepted                            |
| Date        | 2026-09-30                          |
| Author      | Natalia Restrepo                    |
| Linked REQs | REQ-0027 (access and retention), REQ-0047 (no personal data to the LLM). The first version listed REQ-0021 and REQ-0051 by mistake. |

This decision had the number 008 until 2026-10-04. Two decisions had that number, so this one became 023.

---

## Context

The Gold layer (`gold_dispute_customer_360`, `gold_dispute_eligible_transactions`, `gold_dispute_cases_summary`) is the boundary between the data platform and the live FastAPI service (`sentinel-ai-core`). These tables are denormalized serving tables for point lookups under 50 ms.

A dispute needs the full customer context. So the Gold tables contain personally identifiable information (PII): `customer_id`, `document_number`, `first_name`, `last_name`, `date_of_birth`. Plain-text PII in the Gold layer is a compliance risk if someone reads the layer without the correct controls.

---

## Decision for Prototype / MVP

**Keep `customer_id` and the related PII columns in the Gold layer in plain text for the hackathon prototype.**

Reasons:

- The prototype runs on one developer machine, with local DuckDB and gitignored data files. The files never leave the workstation.
- Without `customer_id` in Gold, each FastAPI handler needs a token-resolution call at runtime. This adds latency against the 50 ms target.
- The hackathon dataset is synthetic. No committed or deployed artifact contains real customer data.
- The global `.gitignore` rule for `data/` covers all raw data files.

The service does not read these columns directly. It reads the PII-free view `v_service_dispute_eligible_transactions`, which drops `customer_first_name`, `customer_last_name` and `customer_credit_score` ([data engine README](../../../sentinel-data-engine/README.md)). The public link reads no Gold at all. It uses the labelled mock ([what is real](../../architecture/what-is-real.md)).

---

## Production Mitigation Strategy

Apply these controls before any production deployment:

### 1 · Static PII masking in Silver (before Gold promotion)

Apply deterministic tokenization in the Silver layer. Then `customer_id` in Gold is an opaque token, not a real document number or identity key.

- Use **Azure Purview Data Map** to classify PII columns automatically.
- Apply **Azure Databricks column-level masking** (Delta Lake Column Masking, GA since DBR 12.2). A role without the `PII_READ` privilege then sees `MASKED` values at query time, also when it reads the Gold Delta tables.

### 2 · Dynamic tokenization via Azure Key Vault

For fields that the service must resolve in real time (for example, a masked account number for the agent):

- Keep the map between opaque tokens and real identifiers as a secret in **Azure Key Vault**.
- The FastAPI service calls Key Vault at runtime with a Managed Identity. The raw identifier never goes into application logs or response caches.
- Token TTL: 24 h. A customer erasure request (GDPR) revokes the tokens of that customer.

### 3 · RBAC access controls in Azure Databricks (Unity Catalog)

- The `sentinel-data` service principal owns the `gold` schema.
- Human analysts get `SELECT` on Silver only. Only the `sentinel-api` Managed Identity and the `sentinel-data` job principal can read Gold.
- **Unity Catalog audit logs** record all access and go to Azure Monitor and Log Analytics.

### 4 · Network isolation

- The Gold Delta tables are in an ADLS Gen 2 account behind a **Private Endpoint** in the Sentinel VNet.
- The FastAPI service reaches ADLS through the private endpoint only. Public network access is off.

---

## Consequences

| Scope       | Impact                                                                 |
|-------------|------------------------------------------------------------------------|
| Prototype   | No extra engineering work. The PII risk stays in local development.     |
| Production  | About 2 sprints to implement Key Vault tokenization and column masks.   |
| Compliance  | With the mitigations, it meets GDPR Art. 25 (data protection by design). |
| Latency     | Token resolution adds about 5 ms per request, inside the 50 ms budget.  |
