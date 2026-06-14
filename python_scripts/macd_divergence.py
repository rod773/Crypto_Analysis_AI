"""
MACD Divergences - Python Conversion
Original Pine Script: "MACD Divergences by @DaviddTech"
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
import urllib.request
import json
from datetime import datetime, timedelta
import sys
from typing import List, Tuple

def fetch_data(symbol: str, start: str, end: str) -> List[Tuple[int, float, float, float, float, float]]:
    """Fetch daily candle data from Binance API."""
    s = int(datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={s}&endTime={e}&limit=1000"
    data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
    return [(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])) for k in data]

def ema(data: np.ndarray, period: int) -> np.ndarray:
    n = len(data)
    result = np.full(n, np.nan)
    if n < period:
        return result
    first_valid = np.where(~np.isnan(data))[0]
    if len(first_valid) == 0:
        return result
    start = first_valid[0] + period - 1
    if start >= n:
        return result
    alpha = 2.0 / (period + 1.0)
    result[start] = np.nanmean(data[start - period + 1 : start + 1])
    for i in range(start + 1, n):
        if np.isnan(data[i]):
            continue
        result[i] = alpha * data[i] + (1.0 - alpha) * result[i - 1]
    return result


def sma(data: np.ndarray, period: int) -> np.ndarray:
    n = len(data)
    result = np.full(n, np.nan)
    if n < period:
        return result
    first_valid = np.where(~np.isnan(data))[0]
    if len(first_valid) == 0:
        return result
    start = first_valid[0] + period - 1
    if start >= n:
        return result
    result[start] = np.nanmean(data[start - period + 1 : start + 1])
    for i in range(start + 1, n):
        prev = data[i - period]
        curr = data[i]
        if np.isnan(curr):
            continue
        if np.isnan(prev):
            result[i] = np.nanmean(data[i - period + 1 : i + 1])
        else:
            result[i] = result[i - 1] + (curr - prev) / period
    return result


def pivot_low(series: np.ndarray, lb_l: int, lb_r: int) -> np.ndarray:
    n = len(series)
    result = np.full(n, np.nan)
    for i in range(lb_l, n - lb_r):
        left = series[i - lb_l : i]
        right = series[i + 1 : i + 1 + lb_r]
        if np.all(left > series[i]) and np.all(right > series[i]):
            result[i] = series[i]
    return result


def pivot_high(series: np.ndarray, lb_l: int, lb_r: int) -> np.ndarray:
    n = len(series)
    result = np.full(n, np.nan)
    for i in range(lb_l, n - lb_r):
        left = series[i - lb_l : i]
        right = series[i + 1 : i + 1 + lb_r]
        if np.all(left < series[i]) and np.all(right < series[i]):
            result[i] = series[i]
    return result


@dataclass
class MACDDivergenceResult:
    macd: np.ndarray
    signal: np.ndarray
    histogram: np.ndarray
    pl_vals: np.ndarray
    ph_vals: np.ndarray
    osc_higher_low: np.ndarray
    price_lower_low: np.ndarray
    bull_div: np.ndarray
    osc_lower_high: np.ndarray
    price_higher_high: np.ndarray
    bear_div: np.ndarray
    hidden_bull_div: np.ndarray
    hidden_bear_div: np.ndarray


class MACDDivergence:
    """
    MACD Divergence Detector

    Detects regular and hidden divergences between price and MACD oscillator.
    """

    def __init__(
        self,
        fast_length: int = 12,
        slow_length: int = 26,
        signal_length: int = 9,
        oscillator_ma_type: str = "EMA",
        signal_ma_type: str = "EMA",
        lb_l: int = 5,
        lb_r: int = 5,
        range_upper: int = 60,
        range_lower: int = 5,
        dont_touch_zero: bool = True,
    ):
        self.fast_length = fast_length
        self.slow_length = slow_length
        self.signal_length = signal_length
        self.oscillator_ma_type = oscillator_ma_type
        self.signal_ma_type = signal_ma_type
        self.lb_l = lb_l
        self.lb_r = lb_r
        self.range_upper = range_upper
        self.range_lower = range_lower
        self.dont_touch_zero = dont_touch_zero

    def _ma(self, data: np.ndarray, period: int, ma_type: str) -> np.ndarray:
        if ma_type == "SMA":
            return sma(data, period)
        return ema(data, period)

    def compute(self, close: np.ndarray, high: np.ndarray, low: np.ndarray) -> MACDDivergenceResult:
        n = len(close)

        fast_ma = self._ma(close, self.fast_length, self.oscillator_ma_type)
        slow_ma = self._ma(close, self.slow_length, self.oscillator_ma_type)
        macd = fast_ma - slow_ma
        signal = self._ma(macd, self.signal_length, self.signal_ma_type)
        hist = macd - signal

        osc = macd

        pl_vals = pivot_low(osc, self.lb_l, self.lb_r)
        ph_vals = pivot_high(osc, self.lb_l, self.lb_r)

        pl_indices = np.where(~np.isnan(pl_vals))[0]
        ph_indices = np.where(~np.isnan(ph_vals))[0]

        bull_div = np.zeros(n, dtype=bool)
        bear_div = np.zeros(n, dtype=bool)
        hidden_bull_div = np.zeros(n, dtype=bool)
        hidden_bear_div = np.zeros(n, dtype=bool)

        osc_higher_low = np.full(n, np.nan)
        price_lower_low = np.full(n, np.nan)
        osc_lower_high = np.full(n, np.nan)
        price_higher_high = np.full(n, np.nan)

        # Regular Bullish: MACD higher low, price lower low, both below zero
        for j in range(1, len(pl_indices)):
            i_curr = pl_indices[j]
            i_prev = pl_indices[j - 1]
            bar_distance = i_curr - i_prev
            if self.range_lower <= bar_distance <= self.range_upper:
                osc_curr = osc[i_curr]
                osc_prev = osc[i_prev]
                low_curr = low[i_curr]
                low_prev = low[i_prev]
                if osc_curr > osc_prev and low_curr < low_prev and osc_curr < 0:
                    osc_higher_low[i_curr] = osc_curr
                    price_lower_low[i_curr] = low_curr
                    bull_div[i_curr] = True
                # Hidden Bullish: MACD higher low, price higher low, above zero
                if osc_curr > osc_prev and low_curr > low_prev and osc_curr > 0:
                    hidden_bull_div[i_curr] = True

        # Regular Bearish: MACD lower high, price higher high, both above zero
        for j in range(1, len(ph_indices)):
            i_curr = ph_indices[j]
            i_prev = ph_indices[j - 1]
            bar_distance = i_curr - i_prev
            if self.range_lower <= bar_distance <= self.range_upper:
                osc_curr = osc[i_curr]
                osc_prev = osc[i_prev]
                high_curr = high[i_curr]
                high_prev = high[i_prev]
                if osc_curr < osc_prev and high_curr > high_prev and osc_curr > 0:
                    osc_lower_high[i_curr] = osc_curr
                    price_higher_high[i_curr] = high_curr
                    bear_div[i_curr] = True
                # Hidden Bearish: MACD lower high, price lower high, below zero
                if osc_curr < osc_prev and high_curr < high_prev and osc_curr < 0:
                    hidden_bear_div[i_curr] = True

        return MACDDivergenceResult(
            macd=macd,
            signal=signal,
            histogram=hist,
            pl_vals=pl_vals,
            ph_vals=ph_vals,
            osc_higher_low=osc_higher_low,
            price_lower_low=price_lower_low,
            bull_div=bull_div.astype(float),
            osc_lower_high=osc_lower_high,
            price_higher_high=price_higher_high,
            bear_div=bear_div.astype(float),
            hidden_bull_div=hidden_bull_div.astype(float),
            hidden_bear_div=hidden_bear_div.astype(float),
        )

    def compute_to_df(
        self, close: np.ndarray, high: np.ndarray, low: np.ndarray, index=None
    ) -> pd.DataFrame:
        result = self.compute(close, high, low)
        return pd.DataFrame({
            "macd": result.macd,
            "signal": result.signal,
            "histogram": result.histogram,
            "pl_vals": result.pl_vals,
            "ph_vals": result.ph_vals,
            "osc_higher_low": result.osc_higher_low,
            "price_lower_low": result.price_lower_low,
            "bull_div": result.bull_div,
            "osc_lower_high": result.osc_lower_high,
            "price_higher_high": result.price_higher_high,
            "bear_div": result.bear_div,
            "hidden_bull_div": result.hidden_bull_div,
            "hidden_bear_div": result.hidden_bear_div,
        }, index=index)


if __name__ == "__main__":
    # One-year backtest using Binance daily data
    symbol = "ETHUSDT"
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=365)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    print(f"Fetching data for {symbol} from {start_str} to {end_str}...", end=" ", flush=True)
    candles = fetch_data(symbol, start_str, end_str)
    if not candles:
        print("No data fetched")
        sys.exit(1)
    print(f"{len(candles)} candles loaded")
    # Extract OHLC arrays
    close = np.array([c[4] for c in candles])
    high = np.array([c[2] for c in candles])
    low = np.array([c[3] for c in candles])
    detector = MACDDivergence()
    result = detector.compute(close, high, low)
    print(f"MACD computed for {len(close)} bars")
    print(f"Regular Bullish divergences: {int(np.nansum(result.bull_div))}")
    print(f"Regular Bearish divergences: {int(np.nansum(result.bear_div))}")
    print(f"Hidden Bullish divergences:  {int(np.nansum(result.hidden_bull_div))}")
    print(f"Hidden Bearish divergences:  {int(np.nansum(result.hidden_bear_div))}")
    print(f"Current MACD: {result.macd[-1]:.4f}")
    print(f"Current Signal: {result.signal[-1]:.4f}")
