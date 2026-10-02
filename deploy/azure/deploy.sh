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
# (app/ai/serving.py). State is SQLite inside the container, so the app runs a
# single replica and loses sessions and cases on restart; one replica stays up
# (--min-replicas 1) so the state survives idle time and the first visit does not
# wait for a cold start. Set it back to 0 after the awards (see docs/rationale/public-link.md).

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

LOCATION="${LOCATION:-eastus}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-sentinel-demo}"
ACR_NAME="${ACR_NAME:-sentinelenginerdorta}"
APP_ENV="${APP_ENV:-sentinel-engine-env}"
APP_NAME="${APP_NAME:-sentinel-engine}"
IMAGE_NAME="${IMAGE_NAME:-sentinel-engine:latest}"

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

salt="$(sed -n 's/^SENTINEL_SESSION_SALT=//p' "$REPO_DIR/.env" | tail -n 1)"
if [[ -z "$salt" ]]; then
	salt="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
fi

env_value() {
	sed -n "s/^$1=//p" "$REPO_DIR/.env" | tail -n 1
}

env_vars=(SENTINEL_SECURE_COOKIES=true SENTINEL_SESSION_SALT=secretref:session-salt)
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

fqdn="$(az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	--query properties.configuration.ingress.fqdn -o tsv)"
echo "deployed: https://$fqdn"
