from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import requests

POLYGON_BASE_URL = "https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"


class PolygonRateLimitError(Exception):
    """Exception raised when Polygon API rate limit is exceeded."""


def get_api_key() -> str:
    """Retrieve the API key for Polygon from environment variables."""
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        raise ValueError("POLYGON_API_KEY environment variable is not set.")
    return api_key


def _is_rate_limit_response(status_code: int, payload: dict) -> bool:
    """Return True when the response clearly indicates a retryable rate limit."""
    if status_code == 429:
        return True

    message_parts = [
        str(payload.get("error", "")),
        str(payload.get("message", "")),
        str(payload.get("status", "")),
    ]
    normalized = " ".join(message_parts).lower()
    return "rate limit" in normalized or "too many requests" in normalized


def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """Return Polygon daily OHLCV data as a CSV-compatible string."""
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    response = requests.get(
        POLYGON_BASE_URL.format(
            ticker=symbol.upper(),
            start=start_date,
            end=end_date,
        ),
        params={
            "adjusted": "true",
            "sort": "asc",
            "limit": "50000",
            "apiKey": get_api_key(),
        },
        timeout=30,
    )

    payload = response.json()

    if _is_rate_limit_response(response.status_code, payload):
        raise PolygonRateLimitError(f"Polygon rate limit exceeded: {payload}")

    response.raise_for_status()

    results = payload.get("results", [])
    if not results:
        return (
            f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
        )

    data = pd.DataFrame(results).rename(
        columns={
            "t": "Date",
            "o": "Open",
            "h": "High",
            "l": "Low",
            "c": "Close",
            "v": "Volume",
            "vw": "VWAP",
            "n": "Transactions",
        }
    )
    data["Date"] = pd.to_datetime(data["Date"], unit="ms").dt.strftime("%Y-%m-%d")

    for column in ("Open", "High", "Low", "Close", "VWAP"):
        if column in data.columns:
            data[column] = data[column].round(2)

    ordered_columns = [
        column
        for column in ["Date", "Open", "High", "Low", "Close", "Volume", "VWAP", "Transactions"]
        if column in data.columns
    ]
    return data.loc[:, ordered_columns].to_csv(index=False)
