FROM python:3.12-slim

WORKDIR /srv

COPY sentinel-ai-core ./sentinel-ai-core
COPY branding ./branding

WORKDIR /srv/sentinel-ai-core
RUN pip install --no-cache-dir .

# Local defaults: state under /tmp/sentinel, lost when this container stops.
# deploy.sh overrides the paths, journal mode and stdout logging and mounts an
# Azure Files share at /mnt/sentinel. The uid is pinned so that mount can be
# owned by this user. Postgres remains the production path.
RUN groupadd --system --gid 10001 sentinel \
    && useradd --system --uid 10001 --gid 10001 --no-create-home sentinel \
    && install -d -m 700 -o sentinel -g sentinel /tmp/sentinel
USER sentinel

ENV SENTINEL_GOLD_SOURCE=mock \
    SENTINEL_STATE_BACKEND=sqlite \
    SENTINEL_DB_PATH=/tmp/sentinel/sentinel.db \
    SENTINEL_VAR_DIR=/tmp/sentinel \
    SENTINEL_REFERENCE_DATE=2026-06-17 \
    SENTINEL_DEMO_AUTH=1

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/v1/health', timeout=2)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
