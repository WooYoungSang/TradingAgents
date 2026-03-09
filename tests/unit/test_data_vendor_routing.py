from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from tradingagents.dataflows import alpha_vantage_common
from tradingagents.dataflows.alpha_vantage_common import AlphaVantageRateLimitError
from tradingagents.dataflows.interface import (
    VENDOR_METHODS,
    get_vendor,
    route_to_vendor,
)
from tradingagents.dataflows.polygon_daily import get_stock as get_polygon_stock


def test_get_stock_data_includes_polygon_only_for_stock_data() -> None:
    assert "polygon" in VENDOR_METHODS["get_stock_data"]
    assert "polygon" not in VENDOR_METHODS["get_indicators"]
    assert "polygon" not in VENDOR_METHODS["get_fundamentals"]
    assert "polygon" not in VENDOR_METHODS["get_news"]


def test_tool_vendor_precedence_over_category() -> None:
    config = {
        "data_vendors": {"core_stock_apis": "yfinance"},
        "tool_vendors": {"get_stock_data": "polygon"},
    }

    with patch("tradingagents.dataflows.interface.get_config", return_value=config):
        assert get_vendor("core_stock_apis", "get_stock_data") == "polygon"


def test_route_to_vendor_falls_back_only_on_alpha_vantage_rate_limit() -> None:
    calls: list[str] = []

    def alpha_vantage_impl(*args: object, **kwargs: object) -> str:
        calls.append("alpha_vantage")
        raise AlphaVantageRateLimitError("rate limit")

    def yfinance_impl(*args: object, **kwargs: object) -> str:
        calls.append("yfinance")
        return "yfinance-data"

    def polygon_impl(*args: object, **kwargs: object) -> str:
        calls.append("polygon")
        return "polygon-data"

    config = {
        "data_vendors": {"core_stock_apis": "yfinance"},
        "tool_vendors": {"get_stock_data": "alpha_vantage"},
    }

    with patch("tradingagents.dataflows.interface.get_config", return_value=config):
        with patch.dict(
            VENDOR_METHODS["get_stock_data"],
            {
                "alpha_vantage": alpha_vantage_impl,
                "yfinance": yfinance_impl,
                "polygon": polygon_impl,
            },
            clear=True,
        ):
            assert route_to_vendor("get_stock_data", "AAPL", "2024-01-01", "2024-01-05") == "yfinance-data"

    assert calls == ["alpha_vantage", "yfinance"]


def test_route_to_vendor_does_not_fallback_on_non_typed_error() -> None:
    calls: list[str] = []

    def alpha_vantage_impl(*args: object, **kwargs: object) -> str:
        calls.append("alpha_vantage")
        raise ValueError("invalid api key")

    def yfinance_impl(*args: object, **kwargs: object) -> str:
        calls.append("yfinance")
        return "yfinance-data"

    config = {
        "data_vendors": {"core_stock_apis": "yfinance"},
        "tool_vendors": {"get_stock_data": "alpha_vantage"},
    }

    with patch("tradingagents.dataflows.interface.get_config", return_value=config):
        with patch.dict(
            VENDOR_METHODS["get_stock_data"],
            {
                "alpha_vantage": alpha_vantage_impl,
                "yfinance": yfinance_impl,
            },
            clear=True,
        ):
            with pytest.raises(ValueError, match="invalid api key"):
                route_to_vendor("get_stock_data", "AAPL", "2024-01-01", "2024-01-05")

    assert calls == ["alpha_vantage"]


def test_alpha_vantage_invalid_api_key_message_is_not_retryable() -> None:
    assert not alpha_vantage_common._is_rate_limit_information_message(
        "The api key provided is invalid."
    )
    assert alpha_vantage_common._is_rate_limit_information_message(
        "Thank you for using Alpha Vantage! Our standard API call frequency is 25 requests per day."
    )


def test_polygon_stock_returns_csv_string() -> None:
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "results": [
            {
                "t": 1704067200000,
                "o": 100.123,
                "h": 101.234,
                "l": 99.345,
                "c": 100.789,
                "v": 123456,
                "vw": 100.55,
                "n": 789,
            }
        ]
    }
    response.raise_for_status.return_value = None

    with patch("tradingagents.dataflows.polygon_daily.get_api_key", return_value="test-key"):
        with patch("tradingagents.dataflows.polygon_daily.requests.get", return_value=response):
            csv_output = get_polygon_stock("AAPL", "2024-01-01", "2024-01-02")

    assert "Date,Open,High,Low,Close,Volume,VWAP,Transactions" in csv_output
    assert "2024-01-01,100.12,101.23,99.34,100.79,123456,100.55,789" in csv_output
