#!/usr/bin/env bash
set -euo pipefail

# Builds the Sentinel Engine image in Azure Container Registry and deploys
# it to Azure Container Apps. Requires an active Azure login (az login) on
# the target subscription. Reads SENTINEL_SESSION_SALT from the repo .env
# when set; otherwise generates a random one per run. The LLM router variables
# (SENTINEL_LLM_*) are read from the same .env and passed through when set; the
# API key goes in as a secret. With the base URL and the key set, the app serves
# router_v2 (prompt v2 with its examples) and answers a turn with the keyword
# baseline when the model fails; without them it serves the baseline
# (app/ai/serving.py). State is SQLite on an Azure Files share mounted at
# /mnt/sentinel, journal mode DELETE, one replica. A restart keeps the file;
# a second replica would not. Set min replicas back to 0 after the awards
# (see docs/rationale/public-link.md). The storage account key is read at
# deploy time and is never written into the repository.

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

LOCATION="${LOCATION:-eastus}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-sentinel-demo}"
ACR_NAME="${ACR_NAME:-sentinelenginerdorta}"
APP_ENV="${APP_ENV:-sentinel-engine-env}"
APP_NAME="${APP_NAME:-sentinel-engine}"
IMAGE_NAME="${IMAGE_NAME:-sentinel-engine:latest}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-stsentinelrdorta}"
SHARE_NAME="${SHARE_NAME:-sentinelstate}"
MOUNT_NAME="${MOUNT_NAME:-sentinelstate}"
MOUNT_PATH="/mnt/sentinel"
# Matches the uid/gid pinned in the Dockerfile. nobrl: SQLite on SMB cannot
# use byte-range locks; DELETE journal mode is set for the same reason.
MOUNT_OPTIONS="uid=10001,gid=10001,dir_mode=0700,file_mode=0600,nobrl"

stage() {
	local dst="$1"
	rm -rf "$dst"
	mkdir -p "$dst"
	rsync -a \
		--exclude '/tests/' \
		--exclude '/eval/' \
		--exclude '/var/' \
		--exclude '/data/' \
		--exclude '*.egg-info/' \
		--exclude '__pycache__/' \
		--exclude '.pytest_cache/' \
		--exclude '.env*' \
		--exclude '.gitignore' \
		"$REPO_DIR/sentinel-ai-core/" "$dst/sentinel-ai-core/"
	rsync -a "$REPO_DIR/branding/" "$dst/branding/"
	cp "$REPO_DIR/deploy/azure/Dockerfile" "$dst/Dockerfile"
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

stage "$tmp/staged"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --output none 2>/dev/null ||
	az acr create --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" \
		--sku Basic --admin-enabled true --output none

# Built locally: ACR Tasks (az acr build) is not permitted on this
# subscription, so the image is built by the local Docker daemon and pushed.
az acr login --name "$ACR_NAME" --output none
docker build -t "$ACR_NAME.azurecr.io/$IMAGE_NAME" "$tmp/staged"
docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME"

az containerapp env create --name "$APP_ENV" --resource-group "$RESOURCE_GROUP" \
	--location "$LOCATION" --output none 2>/dev/null || true

az storage account create \
	--name "$STORAGE_ACCOUNT" \
	--resource-group "$RESOURCE_GROUP" \
	--location "$LOCATION" \
	--sku Standard_LRS \
	--kind StorageV2 \
	--output none

az storage share-rm show \
	--resource-group "$RESOURCE_GROUP" \
	--storage-account "$STORAGE_ACCOUNT" \
	--name "$SHARE_NAME" \
	--output none 2>/dev/null ||
	az storage share-rm create \
		--resource-group "$RESOURCE_GROUP" \
		--storage-account "$STORAGE_ACCOUNT" \
		--name "$SHARE_NAME" \
		--quota 1 \
		--enabled-protocols SMB \
		--output none

storage_key="$(az storage account keys list \
	--resource-group "$RESOURCE_GROUP" \
	--account-name "$STORAGE_ACCOUNT" \
	--query '[0].value' -o tsv)"

az containerapp env storage set \
	--name "$APP_ENV" \
	--resource-group "$RESOURCE_GROUP" \
	--storage-name "$MOUNT_NAME" \
	--azure-file-account-name "$STORAGE_ACCOUNT" \
	--azure-file-account-key "$storage_key" \
	--azure-file-share-name "$SHARE_NAME" \
	--access-mode ReadWrite \
	--output none
unset storage_key

salt="$(sed -n 's/^SENTINEL_SESSION_SALT=//p' "$REPO_DIR/.env" | tail -n 1)"
if [[ -z "$salt" ]]; then
	salt="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
fi

env_value() {
	sed -n "s/^$1=//p" "$REPO_DIR/.env" | tail -n 1
}

env_vars=(
	SENTINEL_SECURE_COOKIES=true
	SENTINEL_SESSION_SALT=secretref:session-salt
	SENTINEL_VAR_DIR="$MOUNT_PATH"
	SENTINEL_DB_PATH="$MOUNT_PATH/sentinel.db"
	SENTINEL_SQLITE_JOURNAL=DELETE
	SENTINEL_LOG_STDOUT=1
)
secrets=("session-salt=$salt")
llm_key="$(env_value SENTINEL_LLM_API_KEY)"
if [[ -n "$llm_key" ]]; then
	secrets+=("llm-api-key=$llm_key")
	env_vars+=(SENTINEL_LLM_API_KEY=secretref:llm-api-key)
fi
for name in SENTINEL_LLM_BASE_URL SENTINEL_LLM_CHEAP_MODEL SENTINEL_LLM_STRONG_MODEL \
	SENTINEL_LLM_DEFAULT_MODEL SENTINEL_LLM_PROMPT_VERSION SENTINEL_LLM_ROUTE_RULE \
	SENTINEL_LLM_REASONING_EFFORT SENTINEL_LLM_MAX_TOKENS SENTINEL_LLM_TIMEOUT_S SENTINEL_LLM_MAX_RETRIES; do
	value="$(env_value "$name")"
	[[ -n "$value" ]] && env_vars+=("$name=$value")
done

acr_user="$(az acr credential show --name "$ACR_NAME" --query username -o tsv)"
acr_pass="$(az acr credential show --name "$ACR_NAME" --query 'passwords[0].value' -o tsv)"

az containerapp delete --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	--yes --output none 2>/dev/null || true

az containerapp create \
	--name "$APP_NAME" \
	--resource-group "$RESOURCE_GROUP" \
	--environment "$APP_ENV" \
	--image "$ACR_NAME.azurecr.io/$IMAGE_NAME" \
	--target-port 7860 \
	--ingress external \
	--transport auto \
	--min-replicas 1 \
	--max-replicas 1 \
	--registry-server "$ACR_NAME.azurecr.io" \
	--registry-username "$acr_user" \
	--registry-password "$acr_pass" \
	--secrets "${secrets[@]}" \
	--env-vars "${env_vars[@]}" \
	--output none

# The CLI create flags cannot attach an Azure Files volume. Patch the
# exported spec, drop the secrets block so their values stay, and update.
az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	-o json >"$tmp/app.json"
python3 - "$tmp/app.json" "$tmp/app.yaml" "$MOUNT_NAME" "$MOUNT_PATH" "$MOUNT_OPTIONS" <<'PY'
import json
import sys

src, dst, mount_name, mount_path, mount_options = sys.argv[1:6]
doc = json.load(open(src, encoding="utf-8"))
template = doc["properties"]["template"]
for container in template["containers"]:
    mounts = [m for m in (container.get("volumeMounts") or []) if m.get("volumeName") != mount_name]
    mounts.append({"volumeName": mount_name, "mountPath": mount_path})
    container["volumeMounts"] = mounts
volumes = [v for v in (template.get("volumes") or []) if v.get("name") != mount_name]
volumes.append(
    {
        "name": mount_name,
        "storageName": mount_name,
        "storageType": "AzureFile",
        "mountOptions": mount_options,
    }
)
template["volumes"] = volumes
doc["properties"].get("configuration", {}).pop("secrets", None)


def scalar(node):
    if node is None:
        return "null"
    if isinstance(node, bool):
        return "true" if node else "false"
    if isinstance(node, (int, float)):
        return str(node)
    if isinstance(node, str):
        return json.dumps(node)
    raise TypeError(type(node))


def emit(node, indent=0):
    pad = "  " * indent
    if isinstance(node, list):
        if not node:
            return "[]"
        lines = []
        for item in node:
            if isinstance(item, dict):
                first = True
                for key, value in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    first = False
                    if isinstance(value, (dict, list)) and value:
                        lines.append(f"{prefix}{key}:")
                        lines.append(emit(value, indent + 2))
                    else:
                        lines.append(f"{prefix}{key}: {scalar(value) if not isinstance(value, (dict, list)) else emit(value)}")
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                lines.append(emit(item, indent + 1))
            else:
                lines.append(f"{pad}- {scalar(item)}")
        return "\n".join(lines)
    if isinstance(node, dict):
        if not node:
            return "{}"
        lines = []
        for key, value in node.items():
            if isinstance(value, (dict, list)) and value:
                lines.append(f"{pad}{key}:")
                lines.append(emit(value, indent + 1))
            else:
                lines.append(f"{pad}{key}: {scalar(value) if not isinstance(value, (dict, list)) else emit(value)}")
        return "\n".join(lines)
    return scalar(node)


with open(dst, "w", encoding="utf-8") as handle:
    handle.write(emit(doc) + "\n")
PY
az containerapp update --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	--yaml "$tmp/app.yaml" --output none
rm -f "$tmp/app.json" "$tmp/app.yaml"

fqdn="$(az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	--query properties.configuration.ingress.fqdn -o tsv)"
echo "deployed: https://$fqdn"
