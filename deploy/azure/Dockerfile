FROM python:3.12-slim

WORKDIR /srv

COPY sentinel-ai-core ./sentinel-ai-core
COPY branding ./branding

WORKDIR /srv/sentinel-ai-core
RUN pip install --no-cache-dir .

ENV SENTINEL_GOLD_SOURCE=mock \
    SENTINEL_STATE_BACKEND=sqlite \
    SENTINEL_REFERENCE_DATE=2026-06-17 \
    SENTINEL_DEMO_AUTH=1

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
