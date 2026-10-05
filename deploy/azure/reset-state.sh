#!/usr/bin/env bash
set -euo pipefail

# Removes the runtime state of the public link. The app keeps its SQLite file
# and its turn log on the Azure Files share, and a redeploy keeps the share.
# Tests on the link leave sessions, disputes and tickets behind, so this script
# clears the state before the judges open the link.
#
# It scales the app to zero replicas, deletes the state files from the share,
# scales it back to one replica, and waits for GET /api/v1/health to answer.
# The users file (SENTINEL_USERS_PATH) stays on the share: only the state goes.
# The storage account key is read at run time and is never written down.
#
# Usage:
#   ./deploy/azure/reset-state.sh --dry-run   print the commands and stop
#   ./deploy/azure/reset-state.sh             reset the state on the link

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-sentinel-demo}"
APP_NAME="${APP_NAME:-sentinel-engine}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-stsentinelrdorta}"
SHARE_NAME="${SHARE_NAME:-sentinelstate}"
# The state files. The users file is not in this list and stays.
STATE_FILES=(sentinel.db sentinel.db-journal sentinel.db-wal sentinel.db-shm turns.jsonl)

DRY_RUN=0
for arg in "$@"; do
	case "$arg" in
	--dry-run) DRY_RUN=1 ;;
	-h | --help)
		sed -n '3,17p' "$0"
		exit 0
		;;
	*)
		echo "unknown argument: $arg" >&2
		exit 2
		;;
	esac
done

run() {
	if [[ "$DRY_RUN" -eq 1 ]]; then
		printf '+'
		printf ' %q' "$@"
		printf '\n'
		return 0
	fi
	"$@"
}

# Scale to zero first: SQLite on the share must not hold an open handle.
run az containerapp update --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	--min-replicas 0 --max-replicas 0 --output none

if [[ "$DRY_RUN" -eq 0 ]]; then
	storage_key="$(az storage account keys list \
		--resource-group "$RESOURCE_GROUP" \
		--account-name "$STORAGE_ACCOUNT" \
		--query '[0].value' -o tsv)"
	for name in "${STATE_FILES[@]}"; do
		az storage file delete \
			--account-name "$STORAGE_ACCOUNT" \
			--account-key "$storage_key" \
			--share-name "$SHARE_NAME" \
			--path "$name" \
			--output none 2>/dev/null || true
	done
	unset storage_key
else
	for name in "${STATE_FILES[@]}"; do
		run az storage file delete \
			--account-name "$STORAGE_ACCOUNT" \
			--account-key "$(printf 'secretref')" \
			--share-name "$SHARE_NAME" \
			--path "$name" \
			--output none
	done
fi

# One replica keeps the link warm; see decision 019.
run az containerapp update --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	--min-replicas 1 --max-replicas 1 --output none

if [[ "$DRY_RUN" -eq 1 ]]; then
	echo "dry run: no Azure call made, no file deleted"
	exit 0
fi

fqdn="$(az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
	--query properties.configuration.ingress.fqdn -o tsv)"
url="https://$fqdn/api/v1/health"

for _ in $(seq 1 30); do
	code="$(curl -s -o /dev/null -w '%{http_code}' "$url" || true)"
	if [[ "$code" == "200" ]]; then
		echo "reset: $url answers 200"
		exit 0
	fi
	sleep 2
done

echo "error: $url did not answer 200 after the reset" >&2
exit 1
