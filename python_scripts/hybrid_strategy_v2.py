#!/usr/bin/env python3
"""
Hybrid Predictive Strategy v2 - Optimized for highest returns
Combines 3 strategies with confidence weighting and better entry/exit logic
"""

import json
import math
import urllib.request
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from math import inf

SYMBOL = "ETHUSDT"
START_DATE = "2024-06-13"
END_DATE = "2025-06-13"
INITIAL_CAPITAL = 10_000.0
POSITION_SIZE_PCT = 0.95
FEE_PCT = 0.001


@dataclass
class Candle:
    ts: int
    o: float
    h: float
    l: float
    c: float
    v: float


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
class State:
    cash: float
    pos: Optional[dict] = None
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)


def fetch_data(symbol: str, start: str, end: str) -> List[Candle]:
    s = int(datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={s}&endTime={e}&limit=1000"
    data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
    return [Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])) for k in data]


def calc_rsi(closes: List[float], period=14) -> List[float]:
    if len(closes) < period + 1:
        return [50.0] * len(closes)
    r = [50.0] * period
    for i in range(period, len(closes)):
        gains = losses = 0.0
        for j in range(i - period + 1, i + 1):
            d = closes[j] - closes[j - 1]
            if d > 0:
                gains += d
            else:
                losses -= d
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            r.append(100.0)
        else:
            rs = avg_gain / avg_loss
            r.append(100.0 - (100.0 / (1.0 + rs)))
    return r


def calc_macd(closes: List[float], fast=12, slow=26, signal=9) -> Tuple[List[float], List[float], List[float]]:
    ema_fast = calc_ema(closes, fast)
    ema_slow = calc_ema(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = calc_ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, hist


def calc_ema(prices: List[float], period: int) -> List[float]:
    if len(prices) < period:
        return [sum(prices) / len(prices)] * len(prices)
    ema = [sum(prices[:period]) / period]
    multiplier = 2 / (period + 1)
    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return [ema[0]] * (period - 1) + ema


def round_price(v: float) -> float:
    return round(v, 4) if abs(v) < 10 else round(v)


def calc_ma(prices: List[float], period: int) -> List[float]:
    ma = []
    for i in range(len(prices)):
        if i < period - 1:
            ma.append(sum(prices[:i+1]) / (i+1))
        else:
            ma.append(sum(prices[i-period+1:i+1]) / period)
    return ma


def get_hybrid_signal(candles: List[Candle], i: int, closes: List[float], rsi_vals: List[float], 
                      macd_line: List[float], signal_line: List[float], hist: List[float], 
                      lows: List[float]) -> Tuple[str, float, float, float]:
    """
    Combined hybrid signal with confidence scoring.
    Returns: (direction, stop_loss, take_profit, confidence)
    """
    if i < 50:
        return "hold", 0, 0, 0
    
    price = candles[i].c
    prev_c = candles[i-1].c
    change24h = ((price - prev_c) / prev_c) * 100
    
    buy_signals = 0
    sell_signals = 0
    confidence = 0.0
    
    # === STRATEGY 1: RSI + MACD + Divergence ===
    bullish_div = False
    bearish_div = False
    
    if i >= 4:
        for lookback in [4, 6, 8]:
            if i >= lookback:
                if closes[i-lookback] > closes[i] and rsi_vals[i-lookback] < rsi_vals[i]:
                    bullish_div = True
                if closes[i-lookback] < closes[i] and rsi_vals[i-lookback] > rsi_vals[i]:
                    bearish_div = True
    
    macd_bullish = hist[i] > 0 and (i < 2 or hist[i-1] <= 0)
    macd_bearish = hist[i] < 0 and (i < 2 or hist[i-1] >= 0)
    
    rsi_oversold = rsi_vals[i] < 30
    rsi_overbought = rsi_vals[i] > 70
    rsi_neutral_buy = 30 <= rsi_vals[i] < 45
    rsi_neutral_sell = 55 < rsi_vals[i] <= 70
    
    if bullish_div:
        buy_signals += 3
        confidence += 15
    if bearish_div:
        sell_signals += 3
        confidence += 15
    
    if macd_bullish:
        buy_signals += 2
        confidence += 10
    if macd_bearish:
        sell_signals += 2
        confidence += 10
    
    if rsi_oversold:
        buy_signals += 2
        confidence += 10
    if rsi_overbought:
        sell_signals += 2
        confidence += 10
    
    # === STRATEGY 2: Trend Following ===
    ma50 = calc_ma(closes, 50)[i] if i >= 50 else price
    ma200 = calc_ma(closes, 200)[i] if i >= 200 else price
    
    if price > ma50 and ma50 > ma200:
        buy_signals += 2
        confidence += 10
    elif price < ma50 and ma50 < ma200:
        sell_signals += 2
        confidence += 10
    
    if change24h > 2:
        buy_signals += 1
        confidence += 5
    elif change24h < -2:
        sell_signals += 1
        confidence += 5
    
    # === STRATEGY 3: Mean Reversion ===
    if rsi_neutral_buy and price > ma50:
        buy_signals += 1
        confidence += 5
    elif rsi_neutral_sell and price < ma50:
        sell_signals += 1
        confidence += 5
    
    # === DECISION ===
    if buy_signals >= 4 and buy_signals > sell_signals:
        sl = price * 0.94
        tp = price * 1.15
        return "buy", sl, tp, min(confidence, 95)
    elif sell_signals >= 4 and sell_signals > buy_signals:
        sl = price * 1.06
        tp = price * 0.88
        return "sell", sl, tp, min(confidence, 95)
    else:
        return "hold", 0, 0, confidence


def run(candles: List[Candle]) -> State:
    state = State(cash=INITIAL_CAPITAL)
    closes = [c.c for c in candles]
    lows = [c.l for c in candles]
    rsi_vals = calc_rsi(closes)
    macd_line, signal_line, hist = calc_macd(closes)
    
    for i in range(50, len(candles)):
        c = candles[i]
        dt = datetime.fromtimestamp(c.ts / 1000).strftime("%Y-%m-%d")
        
        direction, sl, tp, confidence = get_hybrid_signal(
            candles, i, closes, rsi_vals, macd_line, signal_line, hist, lows
        )
        
        # Exit logic
        if state.pos:
            p = state.pos
            dir = p["direction"]
            
            if dir == "long" and c.l <= p["sl"]:
                exit_p = p["sl"]
                pnl = (exit_p - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], exit_p, dt, pnl, "stop_loss"))
                state.pos = None
            elif dir == "short" and c.h >= p["sl"]:
                exit_p = p["sl"]
                pnl = (p["entry"] - exit_p) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], exit_p, dt, pnl, "stop_loss"))
                state.pos = None
            elif dir == "long" and c.h >= p["tp"]:
                exit_p = p["tp"]
                pnl = (exit_p - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], exit_p, dt, pnl, "take_profit"))
                state.pos = None
            elif dir == "short" and c.l <= p["tp"]:
                exit_p = p["tp"]
                pnl = (p["entry"] - exit_p) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], exit_p, dt, pnl, "take_profit"))
                state.pos = None
            elif (dir == "long" and direction == "sell" and confidence > 50) or \
                 (dir == "short" and direction == "buy" and confidence > 50):
                if dir == "long":
                    pnl = (c.c - p["entry"]) / p["entry"] * p["size"]
                else:
                    pnl = (p["entry"] - c.c) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], dir, p["size"], c.c, dt, pnl, "signal_reversal"))
                state.pos = None
        
        # Entry logic - only enter on high confidence
        if not state.pos and direction in ("buy", "sell") and confidence >= 40:
            size = state.cash * POSITION_SIZE_PCT
            state.cash -= size
            dir = "long" if direction == "buy" else "short"
            state.pos = {
                "direction": dir,
                "entry": c.c,
                "sl": sl,
                "tp": tp,
                "size": size,
                "entry_date": dt,
                "entry_idx": i,
                "confidence": confidence,
            }
        
        # Track equity
        eq = state.cash
        if state.pos:
            p = state.pos
            val = p["size"]
            if p["direction"] == "long":
                val *= (c.c / p["entry"])
            else:
                val *= (p["entry"] / c.c)
            eq += val
        state.equity_curve.append(eq)
        state.dates.append(dt)
    
    # Close open position
    if state.pos:
        p = state.pos
        c_last = candles[-1]
        if p["direction"] == "long":
            pnl = (c_last.c - p["entry"]) / p["entry"] * p["size"]
        else:
            pnl = (p["entry"] - c_last.c) / p["entry"] * p["size"]
        state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
        last_dt = datetime.fromtimestamp(c_last.ts / 1000).strftime("%Y-%m-%d")
        state.trades.append(Trade(p["entry_date"], p["entry"], p["direction"], p["size"], c_last.c, last_dt, pnl, "end_of_test"))
        state.pos = None
    
    return state


def compute_drawdown(equity: List[float]) -> Tuple[float, float]:
    peak = equity[0]
    max_dd = 0.0
    max_dd_pct = 0.0
    for v in equity:
        if v > peak:
            peak = v
        dd = peak - v
        dd_pct = (dd / peak) * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct
    return max_dd, max_dd_pct


def report(state: State):
    eq = state.equity_curve
    ret = ((eq[-1] / INITIAL_CAPITAL) - 1) * 100
    wins = [t for t in state.trades if t.pnl > 0]
    losses = [t for t in state.trades if t.pnl <= 0]
    total_trades = len(state.trades)
    win_rate = len(wins) / total_trades * 100 if total_trades else 0
    
    avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0
    profit_factor = sum(t.pnl for t in wins) / abs(sum(t.pnl for t in losses)) if losses and sum(t.pnl for t in losses) != 0 else inf
    
    max_dd, max_dd_pct = compute_drawdown(eq)
    
    returns = []
    for i in range(1, len(eq)):
        if eq[i-1] > 0:
            returns.append((eq[i] - eq[i-1]) / eq[i-1])
    sharpe = 0.0
    if returns:
        avg_r = sum(returns) / len(returns)
        std = math.sqrt(sum((r - avg_r)**2 for r in returns) / len(returns))
        if std > 0:
            sharpe = (avg_r / std) * math.sqrt(365)
    
    print("=" * 60)
    print(f"  HYBRID STRATEGY v2 BACKTEST — {SYMBOL}")
    print(f"  Period: {START_DATE} to {END_DATE}")
    print("=" * 60)
    print(f"  Initial Capital:    ${INITIAL_CAPITAL:>8,.2f}")
    print(f"  Final Value:        ${eq[-1]:>8,.2f}")
    print(f"  Total Return:       {ret:>8.2f}%")
    print(f"  Max Drawdown:       ${max_dd:>8,.2f}  ({max_dd_pct:.1f}%)")
    print(f"  Sharpe Ratio:       {sharpe:>8.3f}")
    print(f"  Total Trades:       {total_trades:>8}")
    print(f"  Win Rate:           {win_rate:>7.1f}%")
    print(f"  Avg Win:            ${avg_win:>8,.2f}  ({len(wins)} trades)")
    print(f"  Avg Loss:           ${avg_loss:>8,.2f}  ({len(losses)} trades)")
    if isinstance(profit_factor, float):
        print(f"  Profit Factor:      {profit_factor:>8.3f}")
    print("=" * 60)
    print("  Recent Trades:")
    for t in state.trades[-5:]:
        print(f"  {t.entry_date} | {t.direction.upper():>4} | "
              f"Entry: ${t.entry_price:>8,.2f} | Exit: ${t.exit_price:>8,.2f} | "
              f"P&L: ${t.pnl:>+8,.2f} | {t.exit_reason}")
    print("=" * 60)
    
    out = {
        "dates": state.dates,
        "equity": eq,
        "trades": [{
            "entry_date": t.entry_date,
            "entry_price": t.entry_price,
            "direction": t.direction,
            "size_usd": t.size_usd,
            "exit_price": t.exit_price,
            "exit_date": t.exit_date,
            "pnl": t.pnl,
            "exit_reason": t.exit_reason
        } for t in state.trades],
    }
    with open("hybrid_strategy_v2_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print("  Results saved to hybrid_strategy_v2_result.json\n")


def main():
    print("Fetching data...", end=" ", flush=True)
    candles = fetch_data(SYMBOL, START_DATE, END_DATE)
    print(f"{len(candles)} candles loaded")
    if len(candles) < 200:
        print("Not enough data")
        return
    print("Running hybrid strategy v2 backtest...")
    state = run(candles)
    report(state)


if __name__ == "__main__":
    main()