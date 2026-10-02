# Deploy to Azure Container Apps

How to publish the app to the public link. Why Azure Container Apps and what the
link runs: [decision 019](../../docs/build/decisions/019-azure-container-apps.md) and
[what the public link runs](../../docs/rationale/public-link.md).

## Before you start

- **Azure CLI**, logged in on the target subscription: `az login`, then `az account show`.
- **Docker**, with the daemon running (the image is built locally and pushed; ACR Tasks is not allowed on this subscription).
- **`rsync`** (the script stages a clean copy of the build context).
- **A `.env` at the repository root**, never committed. Copy [`.env.example`](../../.env.example) and fill in:
  - `SENTINEL_LLM_API_KEY`, `SENTINEL_LLM_BASE_URL` and the three `SENTINEL_LLM_*_MODEL` values. With the base URL and the key set, the app serves router_v2; without them it serves the keyword baseline. Values for router_v2: [016](../../docs/build/decisions/016-router-models.md#served-configuration-added-2026-10-02).
  - `SENTINEL_LLM_PROMPT_VERSION=v2`.
  - `SENTINEL_LLM_TIMEOUT_S=6` and `SENTINEL_LLM_MAX_RETRIES=1` keep a failing model under about 12 s per turn before the baseline answers.
  - `SENTINEL_SESSION_SALT` is optional; a random one is generated per run when it is empty.

## Run it

From the repository root:

```bash
./deploy/azure/deploy.sh
```

Names come from environment variables with these defaults: `RESOURCE_GROUP=rg-sentinel-demo`,
`LOCATION=eastus`, `ACR_NAME`, `APP_ENV`, `APP_NAME=sentinel-engine`, `IMAGE_NAME`. Override
them on the command line to deploy somewhere else.

## What it does

1. Stages `sentinel-ai-core/` and `branding/` without tests, `eval/`, local state, data or `.env*`.
2. Creates the resource group and the registry if they do not exist, builds the image and pushes it.
3. Passes the model variables to the container; the API key and the session salt go in as **secrets**, never as plain values.
4. **Deletes and recreates the container app**, with `--min-replicas 1` and `--max-replicas 1`, and prints the link.

The app is recreated on every run, so the link is down for a few seconds and sessions and open
cases are lost (SQLite lives on the container's disk). Do not redeploy during the evaluation
unless a fix is critical. If the script prints `deployed: https://` with no host, the
domain lookup came back empty: read it with
`az containerapp show -n sentinel-engine -g rg-sentinel-demo --query properties.configuration.ingress.fqdn -o tsv`.

## Check it

```bash
curl -s https://<host>/api/v1/health
az containerapp show -n sentinel-engine -g rg-sentinel-demo \
  --query "{min:properties.template.scale.minReplicas,max:properties.template.scale.maxReplicas}"
az containerapp secret list -n sentinel-engine -g rg-sentinel-demo --query "[].name" -o tsv
```

- `health` shows `status: ok`, the model (`accounts/fireworks/models/glm-5p3-flash`) and `prompt_version: v2`; with no model variables it shows `keyword-baseline`.
- The replicas are `1` and `1`.
- The secrets list has `llm-api-key` and `session-salt`; the key must not appear as a plain environment value.
- Then walk the demo cases on the public link: a normal case in es-419, an ambiguous one in pt-BR, a request for a person twice (the ticket, seen as `ADV-0001`), and a prompt-injection attempt.

## After the awards

One replica stays up so the link does not wait for a cold start and the state survives idle
time. After the awards on 10/16, set it back to zero replicas (`--min-replicas 0` in
`deploy.sh`, or `az containerapp update -n sentinel-engine -g rg-sentinel-demo --min-replicas 0`)
so it stops costing. Anything that scales it down on a schedule needs a role on the app,
and that role is lost each time the app is recreated.

## Never commit

The `.env`, the API key, the salt, the registry credentials or any dataset row. The script reads
them from `.env` and from `az`; nothing is written into the repository.
