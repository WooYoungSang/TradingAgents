import importlib
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]


def load_interface_module():
    """Load the interface module with offline-safe dependency stubs."""
    stockstats_stub = types.ModuleType("stockstats")
    stockstats_stub.wrap = lambda data: data
    sys.modules["stockstats"] = stockstats_stub

    module = importlib.import_module("tradingagents.dataflows.interface")
    return importlib.reload(module)


def load_core_stock_tools_module():
    """Load the core stock tool module without importing the full agents package."""
    spec = importlib.util.spec_from_file_location(
        "core_stock_tools_under_test",
        ROOT / "tradingagents/agents/utils/core_stock_tools.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StockDataOutputContractTests(unittest.TestCase):
    def test_route_to_vendor_returns_csv_string_for_get_stock_data(self):
        interface = load_interface_module()
        csv_payload = "timestamp,open,close\n2024-01-02,100.0,101.0\n"

        config = {
            "data_vendors": {"core_stock_apis": "yfinance"},
            "tool_vendors": {"get_stock_data": "yfinance"},
        }
        vendor_methods = {
            "get_stock_data": {
                "yfinance": mock.Mock(return_value=csv_payload),
                "alpha_vantage": mock.Mock(return_value="unused"),
            }
        }

        with mock.patch.object(interface, "get_config", return_value=config):
            with mock.patch.object(interface, "VENDOR_METHODS", vendor_methods):
                result = interface.route_to_vendor(
                    "get_stock_data",
                    "AAPL",
                    "2024-01-01",
                    "2024-01-31",
                )

        self.assertIsInstance(result, str)
        self.assertEqual(result, csv_payload)
        self.assertIn(",", result.splitlines()[0])

    def test_get_stock_data_tool_preserves_csv_string_contract(self):
        load_interface_module()
        core_stock_tools = load_core_stock_tools_module()
        csv_payload = "timestamp,open,close\n2024-01-02,100.0,101.0\n"

        with mock.patch.object(
            core_stock_tools,
            "route_to_vendor",
            return_value=csv_payload,
        ) as route_to_vendor:
            result = core_stock_tools.get_stock_data.func(
                "AAPL",
                "2024-01-01",
                "2024-01-31",
            )

        self.assertIsInstance(result, str)
        self.assertEqual(result, csv_payload)
        route_to_vendor.assert_called_once_with(
            "get_stock_data",
            "AAPL",
            "2024-01-01",
            "2024-01-31",
        )

    def test_polygon_get_stock_returns_csv_string(self):
        polygon_daily = importlib.import_module("tradingagents.dataflows.polygon_daily")
        response = mock.Mock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "results": [
                {
                    "t": 1704067200000,
                    "o": 100.0,
                    "h": 110.0,
                    "l": 95.0,
                    "c": 108.0,
                    "v": 1234,
                },
                {
                    "t": 1704153600000,
                    "o": 108.0,
                    "h": 112.0,
                    "l": 107.0,
                    "c": 111.0,
                    "v": 2345,
                },
            ]
        }

        with mock.patch.object(
            polygon_daily,
            "get_api_key",
            return_value="test-key",
        ):
            with mock.patch.object(polygon_daily.requests, "get", return_value=response):
                result = polygon_daily.get_stock(
                    "AAPL",
                    "2024-01-01",
                    "2024-01-02",
                )

        self.assertIsInstance(result, str)
        self.assertEqual(
            result,
            (
                "timestamp,open,high,low,close,volume\r\n"
                "2024-01-01,100.0,110.0,95.0,108.0,1234\r\n"
                "2024-01-02,108.0,112.0,107.0,111.0,2345\r\n"
            ),
        )


if __name__ == "__main__":
    unittest.main()
