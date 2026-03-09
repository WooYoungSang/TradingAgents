import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _wrap_stockstats_payload(data: object) -> object:
    return data


def _install_stockstats_stub() -> None:
    stockstats_module = ModuleType("stockstats")
    setattr(stockstats_module, "wrap", _wrap_stockstats_payload)
    sys.modules["stockstats"] = stockstats_module


def _import_module(module_name: str) -> Any:
    _install_stockstats_stub()
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def _load_module_from_path(module_name: str, relative_path: str) -> Any:
    _install_stockstats_stub()
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_normalize_stock_payload_to_csv_string_handles_dataframe_payload() -> None:
    core_stock_tools = _load_module_from_path(
        "test_core_stock_tools_module",
        "tradingagents/agents/utils/core_stock_tools.py",
    )
    payload = pd.DataFrame(
        [{"Open": 1.0, "Close": 2.0}],
        index=pd.DatetimeIndex(["2024-01-02"], name="Date"),
    )

    result = core_stock_tools._normalize_stock_payload_to_csv_string(payload)

    assert result.startswith("Date,Open,Close")
    assert "2024-01-02,1.0,2.0" in result


def test_get_stock_data_tool_returns_csv_string_from_dataframe_payload(
    monkeypatch,
) -> None:
    core_stock_tools = _load_module_from_path(
        "test_core_stock_tools_module_for_tool",
        "tradingagents/agents/utils/core_stock_tools.py",
    )
    payload = pd.DataFrame(
        [{"Open": 1.0, "Close": 2.0}],
        index=pd.DatetimeIndex(["2024-01-02"], name="Date"),
    )
    monkeypatch.setattr(core_stock_tools, "route_to_vendor", lambda *args: payload)

    result = core_stock_tools.get_stock_data.func("AAPL", "2024-01-01", "2024-01-03")

    assert result.startswith("Date,Open,Close")
    assert "2024-01-02,1.0,2.0" in result


def test_get_yfin_data_online_returns_plain_csv_without_comment_headers(
    monkeypatch,
) -> None:
    y_finance = _import_module("tradingagents.dataflows.y_finance")
    payload = pd.DataFrame(
        [
            {
                "Open": 1.234,
                "High": 1.678,
                "Low": 1.111,
                "Close": 1.555,
                "Adj Close": 1.555,
                "Volume": 100,
            }
        ],
        index=pd.DatetimeIndex(["2024-01-02"], name="Date"),
    )

    class DummyTicker:
        def history(self, start: str, end: str):
            return payload.copy()

    monkeypatch.setattr(y_finance.yf, "Ticker", lambda symbol: DummyTicker())

    result = y_finance.get_YFin_data_online("AAPL", "2024-01-01", "2024-01-03")

    assert result.startswith("Date,Open,High,Low,Close,Adj Close,Volume")
    assert not result.startswith("#")
    assert "2024-01-02,1.23,1.68,1.11,1.56,1.56,100" in result
