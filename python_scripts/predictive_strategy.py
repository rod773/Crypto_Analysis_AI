#!/usr/bin/env python3
"""Predictive signal engine — standalone strategy from predictive_backtest.py."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Candle:
    ts: int
    o: float
    h: float
    l: float
    c: float
    v: float


# ─── INDICATORS ─────────────────────────────────────────────────────────────

def ema(prices: List[float], period: int) -> List[float]:
    k = 2.0 / (period + 1)
    res = [sum(prices[:period]) / period]
    for p in prices[period:]:
        res.append(p * k + res[-1] * (1 - k))
    return [res[0]] * (period - 1) + res


def rsi(closes: List[float], period=14) -> List[float]:
    rsis = [50.0] * period
    for i in range(period, len(closes)):
        gains, losses = [], []
        for j in range(i - period + 1, i + 1):
            diff = closes[j] - closes[j - 1]
            gains.append(max(0, diff))
            losses.append(max(0, -diff))
        avg_g, avg_l = sum(gains) / period, sum(losses) / period
        rsis.append(100.0 if avg_l == 0 else 100.0 - (100.0 / (1 + avg_g / avg_l)))
    return rsis


def macd_vals(closes: List[float]):
    e_fast = ema(closes[:len(closes)], 12)
    e_slow = ema(closes[:len(closes)], 26)
    macd_line = [f - s for f, s in zip(e_fast, e_slow)]
    sig = ema(macd_line, 9)
    hist = [m - s for m, s in zip(macd_line, sig)]
    return macd_line, sig, hist


def ma(prices: List[float], period: int) -> List[float]:
    res = []
    for i in range(len(prices)):
        if i < period - 1:
            res.append(sum(prices[:i + 1]) / (i + 1))
        else:
            res.append(sum(prices[i - period + 1:i + 1]) / period)
    return res


# ─── SIGNAL ENGINE ──────────────────────────────────────────────────────────

def generate_signal(candles: List[Candle], idx: int) -> Tuple[str, str, float, float]:
    """
    Returns (direction, reason, stop_loss, take_profit).
    direction: 'buy' | 'sell' | 'hold'
    """
    # Need at least two candles to compute 24‑hour change
    if idx < 1 or idx >= len(candles):
        return "hold", "", 0, 0

    price = candles[idx].c
    prev_price = candles[idx - 1].c
    change24h = ((price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

    # Synthetic RSI based on 24‑hour change
    rsi_raw = 50 + change24h * 1.5
    rsi_val = max(15, min(85, round(rsi_raw)))

    # Synthetic MACD derived from RSI (not used for final signal)
    if rsi_val > 60:
        macd = "bullish crossover"
    elif rsi_val < 40:
        macd = "bearish crossover"
    else:
        macd = "neutral"

    # Synthetic trend
    if change24h > 2:
        trend = "bullish"
    elif change24h < -2:
        trend = "bearish"
    else:
        trend = "neutral"

    # Direction based on trend only (matches EA logic)
    if trend == "bullish":
        direction = "buy"
        sl = price * 0.95  # support level
        tp = price * 1.04  # resistance level
        reason = "heuristic"
    elif trend == "bearish":
        direction = "sell"
        sl = price * 1.04  # resistance level as stop‑loss for short
        tp = price * 0.95  # support level as take‑profit for short
        reason = "heuristic"
    else:
        direction = "hold"
        sl = tp = 0
        reason = ""

    return direction, reason, sl, tp
