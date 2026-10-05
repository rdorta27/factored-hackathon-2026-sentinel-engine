#!/usr/bin/env bash
set -euo pipefail

# Copies the judge users file to the Azure Files share. The app reads the copy
# with SENTINEL_USERS_PATH (deploy.sh sets it to /mnt/sentinel/users.json). The
# file holds salted password hashes only, never a plain password.
#
# Requires an active Azure login (az login) on the target subscription, unless
# you pass --dry-run. The storage account key is read at run time and is never
# printed.
#
#   ./deploy/azure/upload-users.sh
#   ./deploy/azure/upload-users.sh --dry-run
#
# Create the file first: python3 scripts/make_judge_users.py

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

LOCAL_FILE="${JUDGE_USERS_FILE:-$REPO_DIR/deploy/judge-users/users.json}"
REMOTE_NAME="${JUDGE_USERS_REMOTE:-users.json}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-sentinel-demo}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-stsentinelrdorta}"
SHARE_NAME="${SHARE_NAME:-sentinelstate}"
DRY_RUN="${DRY_RUN:-0}"

if [[ "${1:-}" == "--dry-run" ]]; then
	DRY_RUN=1
fi

if [[ "$DRY_RUN" == "1" ]]; then
	echo "[dry-run] az storage account keys list --resource-group $RESOURCE_GROUP --account-name $STORAGE_ACCOUNT --query [0].value -o tsv"
	echo "[dry-run] az storage file upload --account-name $STORAGE_ACCOUNT --share-name $SHARE_NAME --source $LOCAL_FILE --path $REMOTE_NAME --account-key <storage-key> --output none"
	exit 0
fi

if [[ ! -f "$LOCAL_FILE" ]]; then
	echo "users file not found: $LOCAL_FILE" >&2
	echo "run: python3 scripts/make_judge_users.py" >&2
	exit 1
fi

storage_key="$(az storage account keys list \
	--resource-group "$RESOURCE_GROUP" \
	--account-name "$STORAGE_ACCOUNT" \
	--query '[0].value' -o tsv)"

az storage file upload \
	--account-name "$STORAGE_ACCOUNT" \
	--share-name "$SHARE_NAME" \
	--source "$LOCAL_FILE" \
	--path "$REMOTE_NAME" \
	--account-key "$storage_key" \
	--output none
unset storage_key

echo "uploaded $REMOTE_NAME to $STORAGE_ACCOUNT/$SHARE_NAME"
