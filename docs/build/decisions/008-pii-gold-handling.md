# ADR 008 – PII Handling in the Gold Layer

| Field       | Value                               |
|-------------|-------------------------------------|
| Status      | Accepted                            |
| Date        | 2026-09-30                          |
| Author      | natalia.restrepo@globant.com        |
| Linked REQs | REQ-0021 (data privacy), REQ-0051   |

---

## Context

The Gold layer (`gold_dispute_customer_360`, `gold_dispute_eligible_transactions`,
`gold_dispute_cases_summary`) is the boundary between the data platform and the
live FastAPI service layer (`sentinel-ai-core`).  These tables are denormalized
serving tables optimised for sub-50 ms point-lookups.

Because disputes require full customer context, the Gold tables necessarily
include personally identifiable information (PII): `customer_id`,
`document_number`, `first_name`, `last_name`, `date_of_birth`.  Retaining
these fields in plain text inside the Gold layer introduces a compliance risk
if the layer is accessed without appropriate controls.

---

## Decision for Prototype / MVP

**Retain `customer_id` and associated PII columns in the Gold layer in plain
text for the hackathon prototype.**

Rationale:
- The prototype runs entirely on a single developer machine with local DuckDB
  and gitignored data files that never leave the workstation.
- Removing `customer_id` from Gold would require a runtime token-resolution
  call in every FastAPI handler, adding latency that conflicts with the sub-50 ms
  SLA target (REQ-0030).
- The hackathon dataset is synthetic; no real customer data is present in any
  committed or deployed artifact.
- All raw data files are covered by the global `.gitignore` rule for `data/`.

---

## Production Mitigation Strategy

Before any production deployment the following controls **must** be applied:

### 1 · Static PII masking in Silver (before Gold promotion)

Apply deterministic tokenization at the Silver layer so that `customer_id` in
Gold resolves to an opaque token, not a real document number or identity key:

- Use **Azure Purview Data Map** to classify PII columns automatically.
- Apply **Azure Databricks column-level masking** (Delta Lake Column Masking,
  GA since DBR 12.2) so that roles without the `PII_READ` privilege see
  `MASKED` values at query time, even when reading the Gold Delta tables.

### 2 · Dynamic tokenization via Azure Key Vault

For fields that must be resolved in real time (e.g. when the FastAPI layer
needs to display a masked account number to the agent):

- Store the mapping between opaque tokens and real identifiers as a secret in
  **Azure Key Vault**.
- The FastAPI service uses a Managed Identity to call Key Vault at runtime;
  the raw identifier is never persisted in application logs or response caches.
- Token TTL: 24 h; revocable per customer on GDPR erasure request.

### 3 · RBAC access controls in Azure Databricks (Unity Catalog)

- The `gold` schema is owned by the `sentinel-data` service principal.
- Human analysts are granted `SELECT` on Silver only; Gold is accessible only
  to the `sentinel-api` Managed Identity and the `sentinel-data` job principal.
- All access is audited via **Unity Catalog audit logs** forwarded to Azure
  Monitor / Log Analytics.

### 4 · Network isolation

- The Gold Delta tables reside in an ADLS Gen 2 account protected by a
  **Private Endpoint** inside the Sentinel VNet.
- The FastAPI service communicates with ADLS over the private endpoint only;
  public network access is disabled.

---

## Consequences

| Scope       | Impact                                                                 |
|-------------|------------------------------------------------------------------------|
| Prototype   | No additional engineering effort; PII risk is contained to local dev.  |
| Production  | ~2 sprint effort to implement Key Vault tokenization and column masks.  |
| Compliance  | Satisfies GDPR Art. 25 (data protection by design) when mitigations applied. |
| Latency     | Token resolution adds ~5 ms per request; within the 50 ms SLA budget.  |
