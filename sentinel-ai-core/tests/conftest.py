"""Suite-wide defaults: mock Gold and in-memory state, never local data or the dev database."""

import os

os.environ.setdefault("SENTINEL_GOLD_SOURCE", "mock")
os.environ.setdefault("SENTINEL_STATE_BACKEND", "memory")
# Tests speak plain HTTP to TestClient, which (correctly) never returns a
# Secure cookie over http; production defaults to Secure (see _secure()).
os.environ.setdefault("SENTINEL_SECURE_COOKIES", "false")
