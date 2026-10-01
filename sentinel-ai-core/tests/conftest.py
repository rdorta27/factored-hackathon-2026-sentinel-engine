"""Suite-wide defaults: tests run on the labeled mock Gold, never on local data."""

import os

os.environ.setdefault("SENTINEL_GOLD_SOURCE", "mock")
