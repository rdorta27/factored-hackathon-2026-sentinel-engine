# Hugging Face Space (deployment)

The container that serves the public link (decision
[012](../../../docs/build/decisions/012-public-deployment.md), REQ-0035). The
`Dockerfile` is versioned here; the Space repository holds its copy together
with the two folders it needs (`sentinel-ai-core/` and `branding/`), staged and
pushed by `push.sh`.

## Stage (local build check, no network)

```
./push.sh --stage /tmp/sentinel-space
docker build -t sentinel-space /tmp/sentinel-space
docker run --rm -p 7860:7860 -e SENTINEL_SECURE_COOKIES=false sentinel-space
```

## Push (builds on Hugging Face)

```
HF_TOKEN=hf_... ./push.sh
```

The token needs write access to `rdorta/sentinel-engine` and nothing else. The
Space settings hold `SENTINEL_SECURE_COOKIES=true` (Variable) and
`SENTINEL_SESSION_SALT` (Secret); the image carries the rest of the
configuration as defaults.
