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
    if idx < 30:
        return "hold", "", 0, 0

    closes = [c.c for c in candles[:idx + 1]]
    volumes = [c.v for c in candles[:idx + 1]]

    rsi_vals = rsi(closes)
    macd_l, macd_sig, hist = macd_vals(closes)
    ma50 = ma(closes, 50)

    cur = idx
    price = candles[cur].c

    # Divergence check (last ~10 candles, 3 sample points)
    bullish, bearish = False, False
    if idx > 20:
        recent_lows = [(i, candles[i].l) for i in range(idx - 10, idx + 1, 3)]
        if len(recent_lows) >= 2:
            p_lows = recent_lows[-2:]
            r_lows = [(i, rsi_vals[i]) for i, _ in recent_lows[-2:]]
            if p_lows[0][1] > p_lows[1][1] and r_lows[0][1] < r_lows[1][1]:
                bullish = True
            if p_lows[0][1] < p_lows[1][1] and r_lows[0][1] > r_lows[1][1]:
                bearish = True

    # MACD Signal Prediction
    hist_growing = hist[cur] > hist[cur - 2]
    hist_declining = hist[cur] < hist[cur - 2]
    macd_buy = hist_growing and macd_l[cur] < macd_sig[cur]
    macd_sell = hist_declining and macd_l[cur] > macd_sig[cur]

    # Volume
    avg_vol = sum(volumes[-20:]) / 20
    vol = volumes[-1]

    # Scoring
    buy_score, sell_score = 0, 0
    if bullish:
        buy_score += 3
    if macd_buy:
        buy_score += 2
    if ma50[cur] and price > ma50[cur]:
        buy_score += 1
    if rsi_vals[cur] < 35:
        buy_score += 1
    if vol > avg_vol * 1.5:
        buy_score += 1

    if bearish:
        sell_score += 3
    if macd_sell:
        sell_score += 2
    if ma50[cur] and price < ma50[cur]:
        sell_score += 1
    if rsi_vals[cur] > 65:
        sell_score += 1
    if vol > avg_vol * 1.5:
        sell_score += 1

    # Entry thresholds
    if buy_score > sell_score and buy_score >= 3:
        return "buy", "div" if bullish else "macd", price * 0.94, price * 1.12
    if sell_score > buy_score and sell_score >= 3:
        return "sell", "div" if bearish else "macd", price * 1.06, price * 0.9

    return "hold", "", 0, 0
