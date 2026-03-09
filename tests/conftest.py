from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "stockstats" not in sys.modules:
    stockstats_stub = cast(Any, types.ModuleType("stockstats"))
    stockstats_stub.wrap = lambda data: data
    sys.modules["stockstats"] = stockstats_stub
