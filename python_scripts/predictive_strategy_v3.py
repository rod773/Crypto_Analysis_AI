#!/usr/bin/env python3
"""
Predictive Strategy v3 - Optimized for HIGHEST RETURNS
Focus: Strong trend following + momentum + strict risk management
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


def calc_ma(prices: List[float], period: int) -> List[float]:
    ma = []
    for i in range(len(prices)):
        if i < period - 1:
            ma.append(sum(prices[:i+1]) / (i+1))
        else:
            ma.append(sum(prices[i-period+1:i+1]) / period)
    return ma


def round_price(v: float) -> float:
    return round(v, 4) if abs(v) < 10 else round(v)


def get_signal(candles: List[Candle], i: int, closes: List[float], rsi_vals: List[float],
               macd_line: List[float], signal_line: List[float], hist: List[float]) -> Tuple[str, float, float, float]:
    """
    High-return predictive signal with momentum and trend following.
    """
    if i < 50:
        return "hold", 0, 0, 0
    
    price = candles[i].c
    prev_c = candles[i-1].c
    change24h = ((price - prev_c) / prev_c) * 100
    
    # Multi-timeframe trend
    ma20 = calc_ma(closes, 20)[i] if i >= 20 else price
    ma50 = calc_ma(closes, 50)[i] if i >= 50 else price
    ma200 = calc_ma(closes, 200)[i] if i >= 200 else price
    
    # MACD signals
    macd_bullish = hist[i] > 0 and hist[i-1] <= 0
    macd_bearish = hist[i] < 0 and hist[i-1] >= 0
    macd_positive = hist[i] > 0
    macd_negative = hist[i] < 0
    
    # RSI signals
    rsi = rsi_vals[i]
    rsi_oversold = rsi < 35
    rsi_overbought = rsi > 65
    rsi_bullish = 40 < rsi < 60
    rsi_bearish = 45 < rsi < 55
    
    # Divergence detection
    bullish_div = False
    bearish_div = False
    if i >= 5:
        for lookback in [5, 7, 10]:
            if i >= lookback:
                if closes[i-lookback] > closes[i] * 1.02 and rsi_vals[i-lookback] < rsi * 0.95:
                    bullish_div = True
                if closes[i-lookback] < closes[i] * 0.98 and rsi_vals[i-lookback] > rsi * 1.05:
                    bearish_div = True
    
    # Trend strength
    uptrend = price > ma20 > ma50 > ma200
    downtrend = price < ma20 < ma50 < ma200
    
    # Momentum
    momentum_strong = change24h > 3
    momentum_weak = change24h < -3
    
    # === SCORING ===
    buy_score = 0
    sell_score = 0
    
    # Trend following (highest weight)
    if uptrend:
        buy_score += 4
    if downtrend:
        sell_score += 4
    
    # MACD
    if macd_bullish:
        buy_score += 3
    if macd_bearish:
        sell_score += 3
    if macd_positive:
        buy_score += 1
    if macd_negative:
        sell_score += 1
    
    # RSI
    if rsi_oversold:
        buy_score += 2
    if rsi_overbought:
        sell_score += 2
    if rsi_bullish:
        buy_score += 1
    if rsi_bearish:
        sell_score += 1
    
    # Divergence (strong signal)
    if bullish_div:
        buy_score += 3
    if bearish_div:
        sell_score += 3
    
    # Momentum
    if momentum_strong:
        buy_score += 2
    if momentum_weak:
        sell_score += 2
    
    # === DECISION ===
    confidence = abs(buy_score - sell_score) * 10
    
    if buy_score >= 6 and buy_score > sell_score:
        # Dynamic TP/SL based on volatility
        atr = sum(abs(closes[j] - closes[j-1]) for j in range(max(0, i-14), i)) / min(14, i)
        sl = price - (atr * 2)
        tp = price + (atr * 4)
        return "buy", sl, tp, min(confidence, 95)
    
    elif sell_score >= 6 and sell_score > buy_score:
        atr = sum(abs(closes[j] - closes[j-1]) for j in range(max(0, i-14), i)) / min(14, i)
        sl = price + (atr * 2)
        tp = price - (atr * 4)
        return "sell", sl, tp, min(confidence, 95)
    
    return "hold", 0, 0, confidence


def run(candles: List[Candle]) -> State:
    state = State(cash=INITIAL_CAPITAL)
    closes = [c.c for c in candles]
    rsi_vals = calc_rsi(closes)
    macd_line, signal_line, hist = calc_macd(closes)
    
    for i in range(50, len(candles)):
        c = candles[i]
        dt = datetime.fromtimestamp(c.ts / 1000).strftime("%Y-%m-%d")
        
        direction, sl, tp, confidence = get_signal(
            candles, i, closes, rsi_vals, macd_line, signal_line, hist
        )
        
        # Exit logic
        if state.pos:
            p = state.pos
            dir = p["direction"]
            
            # Stop loss
            if dir == "long" and c.l <= p["sl"]:
                exit_p = p["sl"]
                pnl = (exit_p - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], exit_p, dt, pnl, "stop_loss"))
                state.pos = None
                continue
            elif dir == "short" and c.h >= p["sl"]:
                exit_p = p["sl"]
                pnl = (p["entry"] - exit_p) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], exit_p, dt, pnl, "stop_loss"))
                state.pos = None
                continue
            
            # Take profit
            if dir == "long" and c.h >= p["tp"]:
                exit_p = p["tp"]
                pnl = (exit_p - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], exit_p, dt, pnl, "take_profit"))
                state.pos = None
                continue
            elif dir == "short" and c.l <= p["tp"]:
                exit_p = p["tp"]
                pnl = (p["entry"] - exit_p) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], exit_p, dt, pnl, "take_profit"))
                state.pos = None
                continue
            
            # Signal reversal
            if (dir == "long" and direction == "sell" and confidence > 40) or \
               (dir == "short" and direction == "buy" and confidence > 40):
                if dir == "long":
                    pnl = (c.c - p["entry"]) / p["entry"] * p["size"]
                else:
                    pnl = (p["entry"] - c.c) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], dir, p["size"], c.c, dt, pnl, "signal_reversal"))
                state.pos = None
        
        # Entry logic
        if not state.pos and direction in ("buy", "sell") and confidence >= 30:
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
    print(f"  PREDICTIVE STRATEGY v3 (HIGH RETURN) — {SYMBOL}")
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
    with open("predictive_v3_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print("  Results saved to predictive_v3_result.json\n")


def main():
    print("Fetching data...", end=" ", flush=True)
    candles = fetch_data(SYMBOL, START_DATE, END_DATE)
    print(f"{len(candles)} candles loaded")
    if len(candles) < 200:
        print("Not enough data")
        return
    print("Running predictive strategy v3 backtest...")
    state = run(candles)
    report(state)


if __name__ == "__main__":
    main()