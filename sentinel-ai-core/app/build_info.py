"""One hash over the files that decide behavior (REQ-0025, REQ-0029).

``bundle_hash`` covers the country policies, the served prompt examples
and the calibrated cut-offs. When any of them changes, the hash in
``/health`` changes with it, so a run can name exactly what it measured.
A missing file raises: without it the service cannot serve what was
measured, and health must not say otherwise.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def bundle_files() -> list[Path]:
    from app.ai import serving
    from app.policy.load import CONFIG_DIR

    return [
        CONFIG_DIR / "mx.yaml",
        CONFIG_DIR / "co.yaml",
        CONFIG_DIR / "ar.yaml",
        serving.EXAMPLES_PATH,
        serving.EXAMPLES_V3_PATH,
        serving.CUTOFFS_PATH,
    ]


def bundle_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(bundle_files()):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
