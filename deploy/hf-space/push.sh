#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Usage:
  push.sh --stage <dir>   stage the Space files into <dir> (local build check)
  push.sh                 stage, clone the Space, copy, commit and push

Requires HF_TOKEN with write access to the Space.
EOF
}

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SPACE_REPO="https://huggingface.co/spaces/rdorta/sentinel-engine"

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
	cp "$REPO_DIR/deploy/hf-space/Dockerfile" "$dst/Dockerfile"
}

push_to_space() {
	if [[ -z "${HF_TOKEN:-}" ]]; then
		echo "push.sh: HF_TOKEN is required (write access to the Space)" >&2
		exit 1
	fi
	local tmp credential
	tmp="$(mktemp -d)"
	trap 'rm -rf "$tmp"' EXIT
	credential='!f() { echo "username=rdorta"; echo "password=$HF_TOKEN"; }; f'
	git -c credential.helper="$credential" clone --depth 1 "$SPACE_REPO" "$tmp/space"
	stage "$tmp/staged"
	rsync -a --delete --exclude '.git/' "$tmp/staged/" "$tmp/space/"
	sed -i 's/^sdk: static/sdk: docker/' "$tmp/space/README.md"
	rm -f "$tmp/space/index.html" "$tmp/space/style.css"
	git -C "$tmp/space" add -A
	git -C "$tmp/space" -c user.name="rdorta" -c user.email="rdorta@users.noreply.huggingface.co" \
		commit -m "deploy: serve the sentinel engine container"
	git -C "$tmp/space" -c credential.helper="$credential" push origin main
	echo "pushed: $SPACE_REPO"
}

case "${1:-}" in
--stage)
	[[ -n "${2:-}" ]] || { usage; exit 1; }
	stage "$2"
	echo "staged: $2"
	;;
"")
	push_to_space
	;;
*)
	usage
	exit 1
	;;
esac
