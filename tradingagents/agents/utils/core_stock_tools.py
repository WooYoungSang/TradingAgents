from typing import Annotated, Any

from langchain_core.tools import tool
from tradingagents.dataflows.interface import route_to_vendor


def _normalize_stock_payload_to_csv_string(payload: Any) -> str:
    """Normalize vendor stock payloads to a CSV-compatible string contract."""
    if isinstance(payload, str):
        return payload

    if isinstance(payload, bytes):
        return payload.decode("utf-8")

    to_csv = getattr(payload, "to_csv", None)
    if callable(to_csv):
        return to_csv()

    raise TypeError(
        f"Unsupported stock payload type for CSV contract: {type(payload).__name__}"
    )


@tool
def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve stock price data (OHLCV) for a given ticker symbol as a CSV string.

    Uses the configured core_stock_apis vendor and normalizes the response to the
    shared CSV-string contract expected by downstream prompts.

    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: CSV-compatible stock price data for the specified ticker symbol and date range.
    """
    payload = route_to_vendor("get_stock_data", symbol, start_date, end_date)
    return _normalize_stock_payload_to_csv_string(payload)
