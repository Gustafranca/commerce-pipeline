"""Make `staged_promote` and shared `commerce_models` importable when running pytest from repo root."""

from __future__ import annotations

import sys
from pathlib import Path

_backend = Path(__file__).resolve().parents[1]
_etl_etl = _backend.parent / "etl" / "etl"
sys.path.insert(0, str(_backend))
sys.path.insert(0, str(_etl_etl))
