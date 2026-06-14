#!/usr/bin/env python3
"""Heuristic Strategy based on synthetic technical indicators.

This module provides a lightweight implementation of the "parseTechnicalIndicators"
logic described in the project documentation and a simple buy/hold/sell decision
function that combines the generated MACD and trend signals.

The functions are deliberately minimal: they require only the current price, the
24‑hour percentage change, and a list of historical close prices (used for
compatibility with the existing backtest code, but not for the synthetic
calculations themselves).
"""

from dataclasses import dataclass
from typing import List


@dataclass
class TechnicalIndicators:
    rsi: int
    macd: str
    ma50: float
    ma200: float
    support_levels: List[float]
    resistance_levels: List[float]
    trend: str


def _round_price(value: float) -> float:
    """Round price values – use 4 dp for small numbers, otherwise integer.

    The back‑test code uses a similar helper; keeping the behaviour identical
    ensures the strategy is interchangeable with the existing engine.
    """
    if abs(value) < 10:
        return round(value, 4)
    return round(value)


def parse_technical_indicators(price: float, change_24h: float, closes: List[float]) -> TechnicalIndicators:
    """Generate synthetic technical indicators from a 24 h price change.

    The calculations follow the table provided in the task description:

    * RSI = 50 + (change24h × 1.5)  → clamped to 15‑85
    * MACD = bullish crossover if RSI > 60, bearish if RSI < 40, else neutral
    * MA50 = price × 0.97 when bullish, else × 1.03
    * MA200 = price × 0.92 when bullish, else × 1.08
    * Trend = bullish if change24h > 2 %, bearish if < ‑2 %, else neutral
    * Supports = price × {0.95, 0.90, 0.85}
    * Resistances = price × {1.04, 1.08, 1.15}
    """
    # --- RSI --------------------------------------------------------------
    rsi_raw = 50 + change_24h * 1.5
    rsi = round(rsi_raw)
    rsi = max(15, min(85, rsi))

    # --- MACD -------------------------------------------------------------
    if rsi > 60:
        macd = "bullish crossover"
    elif rsi < 40:
        macd = "bearish crossover"
    else:
        macd = "neutral"

    # --- Moving averages (synthetic) --------------------------------------
    if change_24h > 0:
        ma50 = price * 0.97
        ma200 = price * 0.92
    else:
        ma50 = price * 1.03
        ma200 = price * 1.08

    # --- Support / resistance ---------------------------------------------
    support_levels = [_round_price(price * f) for f in (0.95, 0.90, 0.85)]
    resistance_levels = [_round_price(price * f) for f in (1.04, 1.08, 1.15)]

    # --- Trend ------------------------------------------------------------
    if change_24h > 2:
        trend = "bullish"
    elif change_24h < -2:
        trend = "bearish"
    else:
        trend = "neutral"

    return TechnicalIndicators(
        rsi=rsi,
        macd=macd,
        ma50=ma50,
        ma200=ma200,
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        trend=trend,
    )


def heuristic_signal(price: float, change_24h: float, closes: List[float]) -> str:
    """Return a simple trading signal based on the synthetic indicators.

    Rules (intentionally straightforward):
    * BUY  – MACD bullish **and** trend bullish
    * SELL – MACD bearish **and** trend bearish
    * otherwise HOLD
    """
    tech = parse_technical_indicators(price, change_24h, closes)
    if tech.macd == "bullish crossover" and tech.trend == "bullish":
        return "buy"
    if tech.macd == "bearish crossover" and tech.trend == "bearish":
        return "sell"
    return "hold"


# Optional: simple CLI for quick manual testing
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run the heuristic strategy on a single snapshot.")
    parser.add_argument("price", type=float, help="Current closing price")
    parser.add_argument("change24h", type=float, help="24‑hour percentage change")
    parser.add_argument(
        "--closes",
        type=str,
        default="[]",
        help="JSON list of historical close prices (optional – not used for synthetic calculations)",
    )
    args = parser.parse_args()
    closes = json.loads(args.closes)
    print("Technical indicators:")
    print(parse_technical_indicators(args.price, args.change24h, closes))
    print("Signal:", heuristic_signal(args.price, args.change24h, closes))
