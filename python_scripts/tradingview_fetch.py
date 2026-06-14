"""Utility to fetch historical bar data from TradingView chart history endpoint.

The function `download_tradingview` returns a pandas DataFrame with OHLCV columns indexed by timestamp.
It uses the public TradingView v5 history endpoint which does not require an API key, but it is
subject to rate‑limits and may change without notice.
"""

import datetime
import pandas as pd
import requests

def _resolution_from_interval(interval: str) -> str:
    """Convert a human‑readable interval like '1m', '5m', '1h', 'D' to TradingView resolution.
    TradingView uses numeric minutes for intraday resolutions and letters for daily/weekly/monthly.
    """
    if interval.endswith("m"):
        return interval.rstrip("m")  # e.g., "1m" -> "1"
    if interval.endswith("h"):
        return str(int(interval.rstrip("h")) * 60)  # hours to minutes
    # Daily, weekly, monthly
    mapping = {"D": "D", "W": "W", "M": "M"}
    return mapping.get(interval.upper(), "D")

def download_tradingview(ticker: str, start: str, end: str, interval: str = "1m") -> pd.DataFrame:
    """Fetch historical OHLCV data from TradingView.

    Parameters
    ----------
    ticker: str
        Symbol in TradingView format (e.g., "BINANCE:BTCUSDT" or "FX:AUDUSD").
    start, end: str
        ISO‑format dates (``YYYY-MM-DD``) or datetime strings understood by ``datetime.fromisoformat``.
    interval: str, default "1m"
        Resolution – "1m", "5m", "15m", "1h", "D", "W", "M", etc.

    Returns
    -------
    pandas.DataFrame
        Index is timestamps (UTC), columns are ``open, high, low, close, volume``.
    """
    try:
        start_dt = datetime.datetime.fromisoformat(start)
    except Exception:
        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d")
    try:
        end_dt = datetime.datetime.fromisoformat(end)
    except Exception:
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d")
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    resolution = _resolution_from_interval(interval)
    url = "https://tvc4.tradingview.com/v5/history"
    params = {
        "symbol": ticker,
        "resolution": resolution,
        "from": start_ts,
        "to": end_ts,
        "adjusted": "true",
        "countback": "5000",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("s") != "ok":
        raise ValueError(f"TradingView returned error: {data.get('errmsg', 'unknown')}")
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["t"], unit="s", utc=True),
        "open": data["o"],
        "high": data["h"],
        "low": data["l"],
        "close": data["c"],
        "volume": data["v"],
    })
    df.set_index("timestamp", inplace=True)
    df.columns = [c.lower() for c in df.columns]
    return df
