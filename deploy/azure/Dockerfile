FROM python:3.12-slim

WORKDIR /srv

COPY sentinel-ai-core ./sentinel-ai-core
COPY branding ./branding

WORKDIR /srv/sentinel-ai-core
RUN pip install --no-cache-dir .

# State is ephemeral on purpose: the SQLite file and the turn log live under
# /tmp/sentinel inside the container and are lost on restart. Sessions and
# open disputes do not survive a redeploy or a scale-to-zero. A durable
# deployment needs Postgres (docs/architecture/specification.md#path-to-production).
RUN useradd --system --no-create-home sentinel \
    && install -d -m 700 -o sentinel /tmp/sentinel
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
