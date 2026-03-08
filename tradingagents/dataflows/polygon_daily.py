from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from io import StringIO

import requests


API_BASE_URL = "https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"


class PolygonRateLimitError(Exception):
    """Raised when Polygon returns a retryable rate-limit response."""


def get_api_key() -> str:
    """Retrieve the Polygon API key from the environment."""
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        raise ValueError("POLYGON_API_KEY environment variable is not set.")
    return api_key


def _validate_date(date_input: str) -> str:
    """Validate and normalize a date input to YYYY-MM-DD."""
    return datetime.strptime(date_input, "%Y-%m-%d").strftime("%Y-%m-%d")


def _format_csv(results: list[dict]) -> str:
    """Convert Polygon aggregate rows to a CSV-compatible string."""
    output = StringIO()
    fieldnames = ["timestamp", "open", "high", "low", "close", "volume"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in results:
        timestamp_ms = row.get("t")
        if timestamp_ms is None:
            continue

        trading_day = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        writer.writerow(
            {
                "timestamp": trading_day,
                "open": row.get("o"),
                "high": row.get("h"),
                "low": row.get("l"),
                "close": row.get("c"),
                "volume": row.get("v"),
            }
        )

    return output.getvalue()


def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """Fetch daily OHLCV data from Polygon and return it as a CSV-compatible string."""
    normalized_start = _validate_date(start_date)
    normalized_end = _validate_date(end_date)
    url = API_BASE_URL.format(
        symbol=symbol.upper(),
        start_date=normalized_start,
        end_date=normalized_end,
    )
    response = requests.get(
        url,
        params={
            "adjusted": "true",
            "sort": "asc",
            "limit": "50000",
            "apiKey": get_api_key(),
        },
        timeout=30,
    )

    if response.status_code == 429:
        raise PolygonRateLimitError("Polygon API rate limit exceeded.")

    response.raise_for_status()
    payload = response.json()
    return _format_csv(payload.get("results", []))
