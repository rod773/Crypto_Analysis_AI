#!/usr/bin/env python3
"""Backtest for RSI Divergence (3-Point Heuristic) strategy over 1 year."""

import json
import math
import urllib.request
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import List, Optional, Dict

SYMBOL = "ETHUSDT"
INTERVAL = "1d"
START_DATE = "2025-06-13"
END_DATE = "2026-06-13"
INITIAL_CAPITAL = 10_000.0
POSITION_SIZE_PCT = 0.95
FEE_PCT = 0.001


@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Trade:
    entry_date: str
    entry_price: float
    direction: str
    size_usd: float
    exit_price: Optional[float] = None
    exit_date: Optional[str] = None
    pnl: float = 0.0
    exit_reason: str = ""


@dataclass
class BacktestState:
    cash: float
    position: Optional[Dict] = None
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)


def fetch_binance_klines(symbol: str, interval: str, start_ms: int, end_ms: int) -> List[Candle]:
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start_ms}&endTime={end_ms}&limit=1000"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    candles = []
    for k in data:
        candles.append(Candle(
            timestamp=int(k[0]),
            open=float(k[1]), high=float(k[2]),
            low=float(k[3]), close=float(k[4]),
            volume=float(k[5]),
        ))
    return candles


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


def detect_divergence(i: int, lows: List[float], rsi_vals: List[float]):
    p2 = lows[i - 4]
    p3 = lows[i - 1]
    r2 = rsi_vals[i - 4]
    r3 = rsi_vals[i - 1]
    if p2 > p3 and r2 < r3:
        return "long"
    if p2 < p3 and r2 > r3:
        return "short"
    return None


def run_backtest(candles: List[Candle]) -> BacktestState:
    closes = [c.close for c in candles]
    lows = [c.low for c in candles]
    rsi_vals = rsi(closes, 14)

    state = BacktestState(cash=INITIAL_CAPITAL)

    for i in range(20, len(candles)):
        c = candles[i]
        date_str = datetime.fromtimestamp(c.timestamp / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        state.dates.append(date_str)

        pos = state.position

        if pos:
            if pos["direction"] == "long":
                if c.close <= pos["stop_loss"]:
                    exit_pnl = (pos["stop_loss"] - pos["entry_price"]) / pos["entry_price"] * pos["size_usd"]
                    state.cash += pos["size_usd"] + exit_pnl - (pos["size_usd"] * FEE_PCT)
                    state.trades.append(Trade(entry_date=pos["entry_date"], entry_price=pos["entry_price"],
                                              direction="long", size_usd=pos["size_usd"],
                                              exit_price=pos["stop_loss"], exit_date=date_str,
                                              pnl=exit_pnl, exit_reason="stop_loss"))
                    state.position = None
                elif c.close >= pos["take_profit"]:
                    exit_pnl = (pos["take_profit"] - pos["entry_price"]) / pos["entry_price"] * pos["size_usd"]
                    state.cash += pos["size_usd"] + exit_pnl - (pos["size_usd"] * FEE_PCT)
                    state.trades.append(Trade(entry_date=pos["entry_date"], entry_price=pos["entry_price"],
                                              direction="long", size_usd=pos["size_usd"],
                                              exit_price=pos["take_profit"], exit_date=date_str,
                                              pnl=exit_pnl, exit_reason="take_profit"))
                    state.position = None
            else:  # short
                if c.close >= pos["stop_loss"]:
                    exit_pnl = (pos["entry_price"] - pos["stop_loss"]) / pos["entry_price"] * pos["size_usd"]
                    state.cash += pos["size_usd"] + exit_pnl - (pos["size_usd"] * FEE_PCT)
                    state.trades.append(Trade(entry_date=pos["entry_date"], entry_price=pos["entry_price"],
                                              direction="short", size_usd=pos["size_usd"],
                                              exit_price=pos["stop_loss"], exit_date=date_str,
                                              pnl=exit_pnl, exit_reason="stop_loss"))
                    state.position = None
                elif c.close <= pos["take_profit"]:
                    exit_pnl = (pos["entry_price"] - pos["take_profit"]) / pos["entry_price"] * pos["size_usd"]
                    state.cash += pos["size_usd"] + exit_pnl - (pos["size_usd"] * FEE_PCT)
                    state.trades.append(Trade(entry_date=pos["entry_date"], entry_price=pos["entry_price"],
                                              direction="short", size_usd=pos["size_usd"],
                                              exit_price=pos["take_profit"], exit_date=date_str,
                                              pnl=exit_pnl, exit_reason="take_profit"))
                    state.position = None

        if not state.position:
            sig = detect_divergence(i, lows, rsi_vals)
            if sig:
                size = state.cash * POSITION_SIZE_PCT
                entry_price = c.close
                if sig == "long":
                    sl = entry_price * 0.97
                    tp = entry_price * 1.09
                else:
                    sl = entry_price * 1.03
                    tp = entry_price * 0.91
                state.position = {
                    "direction": sig, "size_usd": size,
                    "entry_price": entry_price, "entry_date": date_str,
                    "stop_loss": sl, "take_profit": tp,
                }
                state.cash -= size

        equity = state.cash
        pos = state.position
        if pos:
            if pos["direction"] == "long":
                current_val = pos["size_usd"] * (c.close / pos["entry_price"])
            else:
                current_val = pos["size_usd"] * (pos["entry_price"] / c.close)
            equity += current_val
        state.equity_curve.append(equity)

    return state


def print_stats(state: BacktestState):
    final = state.equity_curve[-1] if state.equity_curve else state.cash
    ret = ((final / INITIAL_CAPITAL) - 1) * 100
    winning = [t for t in state.trades if t.pnl > 0]
    losing = [t for t in state.trades if t.pnl <= 0]
    total_pnl = sum(t.pnl for t in state.trades)
    avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0
    avg_loss = sum(t.pnl for t in losing) / len(losing) if losing else 0

    print(f"{'='*55}")
    print(f"  RSI Divergence (3-Point) — 1-Year Backtest")
    print(f"  {SYMBOL} | {INTERVAL}")
    print(f"{'='*55}")
    print(f"  Initial Capital:  ${INITIAL_CAPITAL:>8,.2f}")
    print(f"  Final Value:      ${final:>8,.2f}")
    print(f"  Total Return:      {ret:>7.2f}%")
    print(f"  Total Trades:      {len(state.trades):>4}")
    print(f"  Win Rate:          {len(winning) / max(len(state.trades), 1) * 100:>6.1f}%")
    print(f"  Avg Win:          ${avg_win:>8,.2f}")
    print(f"  Avg Loss:         ${avg_loss:>8,.2f}")
    print(f"  Best Trade:       ${max((t.pnl for t in state.trades), default=0):>8,.2f}")
    print(f"  Worst Trade:      ${min((t.pnl for t in state.trades), default=0):>8,.2f}")
    print(f"{'='*55}")

    longs = [t for t in state.trades if t.direction == "long"]
    shorts = [t for t in state.trades if t.direction == "short"]
    print(f"\n  Long trades:  {len(longs)}  (win: {len([t for t in longs if t.pnl > 0])})")
    print(f"  Short trades: {len(shorts)}  (win: {len([t for t in shorts if t.pnl > 0])})")

    print(f"\n  Recent trades:")
    for t in state.trades[-10:]:
        sign = "+" if t.pnl > 0 else ""
        print(f"    {t.entry_date} {t.direction:5s}  ${t.entry_price:>7.2f} -> ${t.exit_price:>7.2f}  "
              f"{sign}${t.pnl:>7.2f}  ({t.exit_reason})")

    import json
    with open("rsi_div_backtest_result.json", "w") as f:
        json.dump({
            "initial_capital": INITIAL_CAPITAL,
            "final_value": final,
            "total_return_pct": ret,
            "total_trades": len(state.trades),
            "win_rate": len(winning) / max(len(state.trades), 1) * 100,
            "trades": [
                {"entry_date": t.entry_date, "entry_price": t.entry_price,
                 "direction": t.direction, "exit_price": t.exit_price,
                 "exit_date": t.exit_date, "pnl": t.pnl, "exit_reason": t.exit_reason}
                for t in state.trades
            ],
            "equity_curve": state.equity_curve,
            "dates": state.dates,
        }, f, indent=2)


def main():
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    print("Fetching Binance data...")
    candles = fetch_binance_klines(SYMBOL, INTERVAL, start_ms, end_ms)
    print(f"Got {len(candles)} candles")

    state = run_backtest(candles)
    print_stats(state)


if __name__ == "__main__":
    main()
