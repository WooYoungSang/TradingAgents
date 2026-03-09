import importlib
import sys
import types
import unittest
from unittest import mock


def load_interface_module():
    """Load the interface module with offline-safe dependency stubs."""
    stockstats_stub = types.ModuleType("stockstats")
    stockstats_stub.wrap = lambda data: data
    sys.modules["stockstats"] = stockstats_stub

    module = importlib.import_module("tradingagents.dataflows.interface")
    return importlib.reload(module)


class DataVendorRoutingTests(unittest.TestCase):
    def test_get_stock_data_includes_polygon_only_for_stock_data(self):
        interface = load_interface_module()

        self.assertIn("polygon", interface.VENDOR_METHODS["get_stock_data"])
        self.assertNotIn("polygon", interface.VENDOR_METHODS["get_indicators"])
        self.assertNotIn("polygon", interface.VENDOR_METHODS["get_fundamentals"])
        self.assertNotIn("polygon", interface.VENDOR_METHODS["get_news"])

    def test_tool_vendor_overrides_category_vendor(self):
        interface = load_interface_module()

        config = {
            "data_vendors": {"core_stock_apis": "alpha_vantage"},
            "tool_vendors": {"get_stock_data": "yfinance"},
        }

        with mock.patch.object(interface, "get_config", return_value=config):
            self.assertEqual(
                interface.get_vendor("core_stock_apis", "get_stock_data"),
                "yfinance",
            )

    def test_route_to_vendor_uses_configured_vendor_before_remaining_vendors(self):
        interface = load_interface_module()
        alpha_vantage = mock.Mock(
            side_effect=interface.AlphaVantageRateLimitError("rate limit")
        )
        yfinance = mock.Mock(return_value="date,open\n2024-01-02,100.0\n")

        config = {
            "data_vendors": {"core_stock_apis": "alpha_vantage"},
            "tool_vendors": {"get_stock_data": "alpha_vantage"},
        }
        vendor_methods = {
            "get_stock_data": {
                "yfinance": yfinance,
                "alpha_vantage": alpha_vantage,
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

        self.assertEqual(result, "date,open\n2024-01-02,100.0\n")
        alpha_vantage.assert_called_once_with("AAPL", "2024-01-01", "2024-01-31")
        yfinance.assert_called_once_with("AAPL", "2024-01-01", "2024-01-31")

    def test_route_to_vendor_does_not_fallback_on_non_typed_exceptions(self):
        interface = load_interface_module()
        primary_error = RuntimeError("invalid credentials")
        alpha_vantage = mock.Mock(side_effect=primary_error)
        yfinance = mock.Mock(return_value="date,open\n2024-01-02,100.0\n")

        config = {
            "data_vendors": {"core_stock_apis": "alpha_vantage"},
            "tool_vendors": {"get_stock_data": "alpha_vantage"},
        }
        vendor_methods = {
            "get_stock_data": {
                "alpha_vantage": alpha_vantage,
                "yfinance": yfinance,
            }
        }

        with mock.patch.object(interface, "get_config", return_value=config):
            with mock.patch.object(interface, "VENDOR_METHODS", vendor_methods):
                with self.assertRaisesRegex(RuntimeError, "invalid credentials"):
                    interface.route_to_vendor(
                        "get_stock_data",
                        "AAPL",
                        "2024-01-01",
                        "2024-01-31",
                    )

        alpha_vantage.assert_called_once_with("AAPL", "2024-01-01", "2024-01-31")
        yfinance.assert_not_called()

    def test_invalid_api_key_message_is_not_retryable(self):
        alpha_vantage_common = importlib.import_module(
            "tradingagents.dataflows.alpha_vantage_common"
        )

        self.assertFalse(
            alpha_vantage_common._is_rate_limit_information_message(
                "The api key provided is invalid."
            )
        )
        self.assertTrue(
            alpha_vantage_common._is_rate_limit_information_message(
                "Thank you for using Alpha Vantage! Our standard API call frequency is 25 requests per day."
            )
        )


if __name__ == "__main__":
    unittest.main()
