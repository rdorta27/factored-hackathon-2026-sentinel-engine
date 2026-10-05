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

## Judge credentials

The public link has no one-click entry and no documented password. The judges
receive one shared set of logins and passwords in the submission email.

1. Write the users file and the password sheet:

   ```bash
   python3 scripts/make_judge_users.py
   ```

   The users file holds salted hashes only. The plain passwords go to an
   ignored sheet. No password reaches the repository.

2. Copy the users file to the share:

   ```bash
   ./deploy/azure/upload-users.sh
   ```

   Add `--dry-run` to print the commands and stop. `deploy.sh` sets
   `SENTINEL_USERS_PATH` to `/mnt/sentinel/users.json` and
   `SENTINEL_DEMO_PERSONAS=0`. The app reads the file and the one-click entry
   answers 404. `SENTINEL_DEMO_AUTH=1` (Dockerfile) still loads the advisor
   role, so the advisor login keeps its password.

## What it does

1. Stages `sentinel-ai-core/` and `branding/` without tests, `eval/`, local state, data or `.env*`.
2. Creates the resource group and the registry if they do not exist, builds the image and pushes it.
3. Passes the model variables to the container; the API key and the session salt go in as **secrets**, never as plain values.
4. Creates a Standard_LRS storage account and a 1 GiB classic file share, and links the share to the Container Apps environment.
5. **Deletes and recreates the container app**, with `--min-replicas 1` and `--max-replicas 1`, then mounts the share at `/mnt/sentinel` for uid 10001 (the image user).
6. Sets `SENTINEL_VAR_DIR` and `SENTINEL_DB_PATH` on that mount, `SENTINEL_SQLITE_JOURNAL=DELETE` (WAL needs shared memory a share does not have) and `SENTINEL_LOG_STDOUT=1`, so each turn record is one JSON line on standard output and Container Apps sends it to Log Analytics. Sets `SENTINEL_USERS_PATH=/mnt/sentinel/users.json` and `SENTINEL_DEMO_PERSONAS=0` for judge access. Prints the link. The share is not deleted, so the SQLite file and the turn log survive the recreate.

The link is down for a few seconds while the app is recreated. Do not redeploy during the evaluation
unless a fix is critical. If the script prints `deployed: https://` with no host, the
domain lookup came back empty: read it with
`az containerapp show -n sentinel-engine -g rg-sentinel-demo --query properties.configuration.ingress.fqdn -o tsv`.

Names for the share, overridable like the others: `STORAGE_ACCOUNT=stsentinelrdorta`, `SHARE_NAME=sentinelstate`, `MOUNT_NAME=sentinelstate`.

A local `docker run` of the image keeps the Dockerfile defaults (`/tmp/sentinel`, WAL, stdout logging off). The share, `DELETE` and stdout logging are deploy-time settings.

## Services, cost and retention

| Piece | What it is | What it keeps |
|---|---|---|
| Container Apps | One replica, 0.5 vCPU, 1 GiB | The process. Idle time does not drop it until min replicas goes back to 0. |
| Azure Files | Standard_LRS, 1 GiB cap, mounted read-write | The SQLite file and `turns.jsonl`, until the share or the storage account is deleted. |
| Log Analytics | The environment workspace; stdout JSON lines | Turn records (country, outcome, no personal data) for the workspace retention, 30 days unless changed. |

The share is billed on the bytes stored, not on the 1 GiB cap: a SQLite file and a turn log are cents inside the USD 200 trial credit. Log ingestion of the JSON lines is extra and small at demo traffic. Compute for one always-on replica is about USD 1 to 2 per day, as in [019](../../docs/build/decisions/019-azure-container-apps.md); the registry is about USD 0.08 per day. This is a demo, not production: one replica, SMB locking, no alerts. Postgres and OpenTelemetry stay the production path ([specification](../../docs/architecture/specification.md#path-to-production)).

Logout still deletes the conversation. The share does not keep a conversation the app has deleted. After the awards, set min replicas to 0 and delete the storage account if the file should not remain.

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

One replica stays up so the link does not wait for a cold start. After the awards on 10/16, set it back to zero replicas (`--min-replicas 0` in
`deploy.sh`, or `az containerapp update -n sentinel-engine -g rg-sentinel-demo --min-replicas 0`)
so compute stops costing. The file share is separate: delete the storage account if the SQLite file should not remain. Anything that scales the app down on a schedule needs a role on the app,
and that role is lost each time the app is recreated.

## Never commit

The `.env`, the API key, the salt, the registry credentials or any dataset row. The script reads
them from `.env` and from `az`; nothing is written into the repository.
