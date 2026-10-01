"""
Pytest configuration for sentinel-data-engine tests.

Adds the src/ directory to sys.path so that `sentinel_data` can be imported
without the package being installed in editable mode.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
