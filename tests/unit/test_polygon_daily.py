from __future__ import annotations

from requests import HTTPError

from tradingagents.dataflows.polygon_daily import PolygonRateLimitError, get_stock


class MockResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPError(f"{self.status_code} error")


def test_get_stock_returns_csv_string(monkeypatch) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")

    def fake_get(*args, **kwargs):
        return MockResponse(
            200,
            {
                "results": [
                    {"t": 1704067200000, "o": 100.0, "h": 110.0, "l": 95.0, "c": 108.0, "v": 1234},
                    {"t": 1704153600000, "o": 108.0, "h": 112.0, "l": 107.0, "c": 111.0, "v": 2345},
                ]
            },
        )

    monkeypatch.setattr("tradingagents.dataflows.polygon_daily.requests.get", fake_get)

    result = get_stock("AAPL", "2024-01-01", "2024-01-02")

    assert result == (
        "timestamp,open,high,low,close,volume\r\n"
        "2024-01-01,100.0,110.0,95.0,108.0,1234\r\n"
        "2024-01-02,108.0,112.0,107.0,111.0,2345\r\n"
    )


def test_get_stock_raises_typed_error_for_429(monkeypatch) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")
    monkeypatch.setattr(
        "tradingagents.dataflows.polygon_daily.requests.get",
        lambda *args, **kwargs: MockResponse(429),
    )

    try:
        get_stock("AAPL", "2024-01-01", "2024-01-02")
    except PolygonRateLimitError:
        pass
    else:
        raise AssertionError("Expected PolygonRateLimitError for HTTP 429")


def test_get_stock_does_not_convert_non_429_errors(monkeypatch) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")
    monkeypatch.setattr(
        "tradingagents.dataflows.polygon_daily.requests.get",
        lambda *args, **kwargs: MockResponse(401),
    )

    try:
        get_stock("AAPL", "2024-01-01", "2024-01-02")
    except HTTPError:
        pass
    else:
        raise AssertionError("Expected HTTPError for non-429 failure")
