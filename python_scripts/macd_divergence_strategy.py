#!/usr/bin/env python3
"""
MACD Divergence Strategy - High Return Trading System
Detects bullish/bearish divergences between price and MACD histogram
for predictive entry signals with optimal risk/reward ratios.
"""

import json
import math
import urllib.request
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional
from math import inf


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


SYMBOL = "ETHUSDT"
START_DATE = "2024-06-13"
END_DATE = "2025-06-13"
INITIAL_CAPITAL = 10_000.0
POSITION_SIZE_PCT = 0.95
FEE_PCT = 0.001


def fetch_data(symbol: str, start: str, end: str) -> List[Candle]:
    """Fetch daily candle data from Binance API."""
    s = int(datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={s}&endTime={e}&limit=1000"
    
    data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
    return [Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])) for k in data]


def ema(prices: List[float], period: int) -> List[float]:
    """Calculate Exponential Moving Average."""
    k = 2.0 / (period + 1)
    res = [sum(prices[:period]) / period]
    for p in prices[period:]:
        res.append(p * k + res[-1] * (1 - k))
    return [res[0]] * (period - 1) + res


def macd(closes: List[float], fast=12, slow=26, signal=9) -> Tuple[List[float], List[float], List[float]]:
    """Calculate MACD line, signal line, and histogram."""
    e_fast = ema(closes, fast)
    e_slow = ema(closes, slow)
    macd_line = [f - s for f, s in zip(e_fast, e_slow)]
    sig_line = ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, sig_line)]
    return macd_line, sig_line, histogram


def find_swings(candles: List[Candle], lookback: int = 5) -> Tuple[List[int], List[int]]:
    """
    Identify swing highs and swing lows.
    Returns indices of swing points.
    """
    swing_highs = []
    swing_lows = []
    
    for i in range(lookback, len(candles) - lookback):
        # Swing high: highest high in lookback window
        is_high = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and candles[j].h >= candles[i].h:
                is_high = False
                break
        if is_high:
            swing_highs.append(i)
        
        # Swing low: lowest low in lookback window
        is_low = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and candles[j].l <= candles[i].l:
                is_low = False
                break
        if is_low:
            swing_lows.append(i)
    
    return swing_highs, swing_lows


def detect_macd_divergence(candles: List[Candle], idx: int, 
                           macd_line: List[float], histogram: List[float]) -> Tuple[str, float]:
    """
    Detect MACD divergences at current index.
    Returns: (divergence_type, strength)
    - 'bullish': price making lower lows, MACD making higher lows
    - 'bearish': price making higher highs, MACD making lower highs
    - 'none': no divergence
    """
    if idx < 30:
        return "none", 0.0
    
    # Look back for recent swing points (last 20-40 candles)
    lookback_start = max(0, idx - 40)
    lookback_end = idx - 5  # Need some separation from current
    
    # Find swing lows for bullish divergence
    bullish_strength = 0.0
    bearish_strength = 0.0
    
    # Check for bullish divergence (price lower lows, MACD higher lows)
    swing_lows = []
    for i in range(lookback_start, lookback_end):
        is_low = True
        for j in range(max(lookback_start, i - 5), min(idx, i + 5) + 1):
            if j != i and candles[j].l <= candles[i].l:
                is_low = False
                break
        if is_low:
            swing_lows.append((i, candles[i].l, histogram[i]))
    
    # Need at least 2 swing lows to compare
    if len(swing_lows) >= 2:
        # Get the two most recent significant lows
        recent_lows = swing_lows[-2:]
        if len(recent_lows) == 2:
            prev_idx, prev_low, prev_hist = recent_lows[0]
            curr_idx, curr_low, curr_hist = recent_lows[1]
            
            # Bullish divergence: price lower, MACD higher
            if curr_low < prev_low * 0.98 and curr_hist > prev_hist * 1.05:
                # Calculate strength based on magnitude
                price_diff = (prev_low - curr_low) / prev_low * 100
                macd_diff = (curr_hist - prev_hist) / abs(prev_hist) * 100 if prev_hist != 0 else 50
                bullish_strength = min((price_diff + macd_diff) / 2, 100)
    
    # Check for bearish divergence (price higher highs, MACD lower highs)
    swing_highs = []
    for i in range(lookback_start, lookback_end):
        is_high = True
        for j in range(max(lookback_start, i - 5), min(idx, i + 5) + 1):
            if j != i and candles[j].h >= candles[i].h:
                is_high = False
                break
        if is_high:
            swing_highs.append((i, candles[i].h, histogram[i]))
    
    if len(swing_highs) >= 2:
        recent_highs = swing_highs[-2:]
        if len(recent_highs) == 2:
            prev_idx, prev_high, prev_hist = recent_highs[0]
            curr_idx, curr_high, curr_hist = recent_highs[1]
            
            # Bearish divergence: price higher, MACD lower
            if curr_high > prev_high * 1.02 and curr_hist < prev_hist * 0.95:
                price_diff = (curr_high - prev_high) / prev_high * 100
                macd_diff = (prev_hist - curr_hist) / abs(prev_hist) * 100 if prev_hist != 0 else 50
                bearish_strength = min((price_diff + macd_diff) / 2, 100)
    
    if bullish_strength > bearish_strength and bullish_strength >= 30:
        return "bullish", bullish_strength
    elif bearish_strength > bullish_strength and bearish_strength >= 30:
        return "bearish", bearish_strength
    else:
        return "none", 0.0


def generate_signal(candles: List[Candle], idx: int, 
                    macd_line: List[float], histogram: List[float]) -> Tuple[str, float, float, float]:
    """
    Generate trading signal based on MACD divergence.
    Returns: (direction, stop_loss, take_profit, confidence)
    """
    if idx < 30:
        return "hold", 0, 0, 0
    
    price = candles[idx].c
    
    # Detect divergence
    div_type, strength = detect_macd_divergence(candles, idx, macd_line, histogram)
    
    # Additional confirmation: MACD histogram momentum
    hist_momentum = histogram[idx] - histogram[idx - 2] if idx >= 2 else 0
    
    # Calculate ATR for dynamic stops
    atr = 0
    if idx >= 14:
        tr_values = []
        for i in range(idx - 13, idx + 1):
            high = candles[i].h
            low = candles[i].l
            prev_close = candles[i-1].c
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)
        atr = sum(tr_values) / len(tr_values)
    else:
        atr = price * 0.03
    
    if div_type == "bullish":
        # Bullish divergence + positive histogram momentum = strong buy
        if hist_momentum > 0:
            sl = price - (atr * 2.0)
            tp = price + (atr * 4.5)
            return "buy", sl, tp, min(strength + 20, 95)
    
    elif div_type == "bearish":
        # Bearish divergence + negative histogram momentum = strong sell
        if hist_momentum < 0:
            sl = price + (atr * 2.0)
            tp = price - (atr * 4.5)
            return "sell", sl, tp, min(strength + 20, 95)
    
    return "hold", 0, 0, 0


def run_backtest(candles: List[Candle]) -> Tuple[List[float], List[Trade], List[str]]:
    """Run the MACD divergence strategy backtest."""
    
    closes = [c.c for c in candles]
    macd_line, signal_line, histogram = macd(closes)
    
    cash = INITIAL_CAPITAL
    pos = None
    trades = []
    equity_curve = []
    dates = []
    
    for i in range(1, len(candles)):
        candle = candles[i]
        dt = datetime.fromtimestamp(candle.ts / 1000).strftime("%Y-%m-%d")
        
        # Generate signal
        direction, sl, tp, confidence = generate_signal(candles, i, macd_line, histogram)
        
        # Exit logic
        if pos:
            exited = False
            
            # Stop loss
            if pos["direction"] == "long" and candle.l <= pos["sl"]:
                exit_price = pos["sl"]
                pnl = ((exit_price - pos["entry"]) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                trades.append(Trade(pos["entry_date"], pos["entry"], "long", pos["size"], 
                                   exit_price, dt, pnl, "stop_loss"))
                pos = None
                exited = True
                
            elif pos["direction"] == "short" and candle.h >= pos["sl"]:
                exit_price = pos["sl"]
                pnl = ((pos["entry"] - exit_price) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                trades.append(Trade(pos["entry_date"], pos["entry"], "short", pos["size"], 
                                   exit_price, dt, pnl, "stop_loss"))
                pos = None
                exited = True
            
            # Take profit
            if not exited and pos:
                if pos["direction"] == "long" and candle.h >= pos["tp"]:
                    exit_price = pos["tp"]
                    pnl = ((exit_price - pos["entry"]) / pos["entry"]) * pos["size"]
                    cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                    trades.append(Trade(pos["entry_date"], pos["entry"], "long", pos["size"], 
                                       exit_price, dt, pnl, "take_profit"))
                    pos = None
                    exited = True
                    
                elif pos["direction"] == "short" and candle.l <= pos["tp"]:
                    exit_price = pos["tp"]
                    pnl = ((pos["entry"] - exit_price) / pos["entry"]) * pos["size"]
                    cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                    trades.append(Trade(pos["entry_date"], pos["entry"], "short", pos["size"], 
                                       exit_price, dt, pnl, "take_profit"))
                    pos = None
                    exited = True
            
            # Signal reversal
            if not exited and pos and confidence > 50:
                if (pos["direction"] == "long" and direction == "sell") or \
                   (pos["direction"] == "short" and direction == "buy"):
                    exit_price = candle.c
                    if pos["direction"] == "long":
                        pnl = ((exit_price - pos["entry"]) / pos["entry"]) * pos["size"]
                    else:
                        pnl = ((pos["entry"] - exit_price) / pos["entry"]) * pos["size"]
                    cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                    trades.append(Trade(pos["entry_date"], pos["entry"], pos["direction"], 
                                       pos["size"], exit_price, dt, pnl, "reversal"))
                    pos = None
        
        # Entry logic
        if not pos and direction in ("buy", "sell") and confidence >= 40:
            size = cash * POSITION_SIZE_PCT
            cash -= size
            
            side = "long" if direction == "buy" else "short"
            pos = {
                "direction": side,
                "entry": candle.c,
                "sl": sl,
                "tp": tp,
                "size": size,
                "entry_date": dt,
                "confidence": confidence,
            }
        
        # Track equity
        eq = cash
        if pos:
            val = pos["size"]
            if pos["direction"] == "long":
                val *= (candle.c / pos["entry"])
            else:
                val *= (pos["entry"] / candle.c)
            eq += val
        equity_curve.append(eq)
        dates.append(dt)
    
    # Close open position
    if pos:
        p = pos
        final_price = candles[-1].c
        if p["direction"] == "long":
            pnl = ((final_price - p["entry"]) / p["entry"]) * p["size"]
        else:
            pnl = ((p["entry"] - final_price) / p["entry"]) * p["size"]
        cash += p["size"] + pnl - (p["size"] * FEE_PCT)
        trades.append(Trade(p["entry_date"], p["entry"], p["direction"], 
                           p["size"], final_price, dates[-1], pnl, "end"))
    
    return equity_curve, trades, dates


def compute_stats(equity: List[float], trades: List[Trade]) -> dict:
    """Calculate performance statistics."""
    
    final_value = equity[-1]
    total_return = ((final_value / INITIAL_CAPITAL) - 1) * 100
    
    # Drawdown
    peak = equity[0]
    max_dd = 0
    max_dd_pct = 0
    for v in equity:
        if v > peak:
            peak = v
        dd = peak - v
        dd_pct = (dd / peak) * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = dd_pct
    
    # Sharpe ratio
    returns = []
    for i in range(1, len(equity)):
        if equity[i-1] > 0:
            returns.append((equity[i] - equity[i-1]) / equity[i-1])
    
    sharpe = 0.0
    if returns:
        avg_r = sum(returns) / len(returns)
        std = math.sqrt(sum((r - avg_r)**2 for r in returns) / len(returns))
        if std > 0:
            sharpe = (avg_r / std) * math.sqrt(365)
    
    # Trade statistics
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    total_trades = len(trades)
    win_rate = len(wins) / total_trades * 100 if total_trades else 0
    avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0
    profit_factor = sum(t.pnl for t in wins) / abs(sum(t.pnl for t in losses)) if losses and sum(t.pnl for t in losses) != 0 else inf
    
    return {
        "final_value": final_value,
        "total_return": total_return,
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd_pct,
        "sharpe_ratio": sharpe,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "wins": len(wins),
        "losses": len(losses),
    }


def report(equity: List[float], trades: List[Trade], dates: List[str]):
    """Print and save backtest results."""
    
    stats = compute_stats(equity, trades)
    
    print("=" * 70)
    print(f"  MACD DIVERGENCE STRATEGY — {SYMBOL}")
    print(f"  Period: {START_DATE} to {END_DATE}")
    print("=" * 70)
    print(f"  Initial Capital:    ${INITIAL_CAPITAL:>12,.2f}")
    print(f"  Final Value:        ${stats['final_value']:>12,.2f}")
    print(f"  Total Return:       {stats['total_return']:>12.2f}%")
    print(f"  Max Drawdown:       ${stats['max_drawdown']:>12,.2f}  ({stats['max_drawdown_pct']:.1f}%)")
    print(f"  Sharpe Ratio:       {stats['sharpe_ratio']:>12.3f}")
    print(f"  Total Trades:       {stats['total_trades']:>12}")
    print(f"  Win Rate:           {stats['win_rate']:>11.1f}%")
    print(f"  Avg Win:            ${stats['avg_win']:>12,.2f}  ({stats['wins']} trades)")
    print(f"  Avg Loss:           ${stats['avg_loss']:>12,.2f}  ({stats['losses']} trades)")
    if isinstance(stats['profit_factor'], float):
        print(f"  Profit Factor:      {stats['profit_factor']:>12.3f}")
    print("=" * 70)
    
    print("  Recent Trades:")
    for t in trades[-5:]:
        dir_sym = "LONG" if t.direction == "long" else "SHORT"
        pnl_sym = "+" if t.pnl > 0 else ""
        print(f"  {t.exit_date} | {dir_sym:>5} | Entry: ${t.entry_price:>8,.2f} | "
              f"Exit: ${t.exit_price:>8,.2f} | P&L: {pnl_sym}${t.pnl:>8,.2f} | {t.exit_reason}")
    print("=" * 70)
    
    # Save results
    output = {
        "symbol": SYMBOL,
        "period": {"start": START_DATE, "end": END_DATE},
        "initial_capital": INITIAL_CAPITAL,
        "statistics": {
            "final_value": stats["final_value"],
            "total_return_pct": stats["total_return"],
            "max_drawdown": stats["max_drawdown"],
            "max_drawdown_pct": stats["max_drawdown_pct"],
            "sharpe_ratio": stats["sharpe_ratio"],
            "total_trades": stats["total_trades"],
            "win_rate": stats["win_rate"],
            "avg_win": stats["avg_win"],
            "avg_loss": stats["avg_loss"],
            "profit_factor": stats["profit_factor"] if isinstance(stats["profit_factor"], float) else "inf",
        },
        "dates": dates,
        "equity_curve": equity,
        "trades": [
            {
                "entry_date": t.entry_date,
                "entry_price": t.entry_price,
                "direction": t.direction,
                "exit_price": t.exit_price,
                "exit_date": t.exit_date,
                "pnl": t.pnl,
                "exit_reason": t.exit_reason,
            }
            for t in trades
        ],
    }
    
    with open("macd_divergence_result.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n  Results saved to macd_divergence_result.json")


def main():
    print("Fetching data...", end=" ", flush=True)
    candles = fetch_data(SYMBOL, START_DATE, END_DATE)
    
    if not candles:
        print("Failed to fetch data")
        return
    
    print(f"{len(candles)} candles loaded")
    print("Running MACD Divergence Strategy backtest...\n")
    
    equity, trades, dates = run_backtest(candles)
    report(equity, trades, dates)


if __name__ == "__main__":
    main()