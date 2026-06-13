#!/usr/bin/env python3
"""RSI Divergence (3-Point Heuristic) — standalone Python implementation."""

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


@dataclass
class Signal:
    candle: Candle
    kind: str  # "bullish" | "bearish"
    p2: float
    p3: float
    r2: float
    r3: float


def rsi(closes: List[float], period: int = 14) -> List[float]:
    result = [50.0] * period
    for i in range(period, len(closes)):
        gains, losses = 0.0, 0.0
        for j in range(i - period, i):
            diff = closes[j + 1] - closes[j]
            if diff > 0:
                gains += diff
            else:
                losses -= diff
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100.0 - 100.0 / (1.0 + rs))
    return result


def detect_divergences(
    candles: List[Candle],
    rsi_period: int = 14,
) -> List[Signal]:
    if len(candles) < rsi_period + 20:
        return []

    closes = [c.c for c in candles]
    lows = [c.l for c in candles]
    rsi_vals = rsi(closes, rsi_period)

    signals: List[Signal] = []

    for i in range(20, len(candles)):
        p2 = lows[i - 4]
        p3 = lows[i - 1]
        r2 = rsi_vals[i - 4]
        r3 = rsi_vals[i - 1]

        if p2 > p3 and r2 < r3:
            signals.append(Signal(
                candle=candles[i], kind="bullish",
                p2=p2, p3=p3, r2=r2, r3=r3,
            ))
        elif p2 < p3 and r2 > r3:
            signals.append(Signal(
                candle=candles[i], kind="bearish",
                p2=p2, p3=p3, r2=r2, r3=r3,
            ))

    return signals


def print_signals(signals: List[Signal]) -> None:
    if not signals:
        return
    bull = [s for s in signals if s.kind == "bullish"]
    bear = [s for s in signals if s.kind == "bearish"]
    print(f"Total signals: {len(signals)}  |  Bullish: {len(bull)}  |  Bearish: {len(bear)}")
    for s in signals:
        label = "BULL" if s.kind == "bullish" else "BEAR"
        print(f"  {label:6s}  idx={s.candle.ts}  price ({s.p2:.2f} -> {s.p3:.2f})  RSI ({s.r2:.1f} -> {s.r3:.1f})")


def main():
    import json, urllib.request
    url = "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&limit=500"
    with urllib.request.urlopen(url) as resp:
        raw = json.loads(resp.read())

    candles = [
        Candle(ts=int(k[0]) // 1000, o=float(k[1]), h=float(k[2]),
               l=float(k[3]), c=float(k[4]), v=float(k[5]))
        for k in raw
    ]

    sigs = detect_divergences(candles)
    print_signals(sigs)


if __name__ == "__main__":
    main()
