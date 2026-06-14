#!/usr/bin/env python3
"""
SMA 300 + RSI Divergence Strategy
Combines long-term trend filtering (SMA 300) with RSI divergence entries
for high-probability trend continuation trades.
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


def sma(prices: List[float], period: int) -> List[float]:
    """Calculate Simple Moving Average."""
    result = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(sum(prices[:i+1]) / (i+1))
        else:
            result.append(sum(prices[i-period+1:i+1]) / period)
    return result


def rsi(closes: List[float], period=14) -> List[float]:
    """Calculate RSI momentum indicator."""
    rsis = [50.0] * period
    for i in range(period, len(closes)):
        gains, losses = [], []
        for j in range(i - period + 1, i + 1):
            diff = closes[j] - closes[j - 1]
            gains.append(max(0, diff))
            losses.append(max(0, -diff))
        avg_g = sum(gains) / period
        avg_l = sum(losses) / period
        if avg_l == 0:
            rsis.append(100.0)
        else:
            rs = avg_g / avg_l
            rsis.append(100.0 - (100.0 / (1.0 + rs)))
    return rsis


def calc_atr(candles: List[Candle], idx: int, period=14) -> float:
    """Calculate Average True Range for volatility-based stops."""
    if idx < period:
        return candles[idx].c * 0.05
    
    tr_values = []
    for i in range(idx - period + 1, idx + 1):
        high = candles[i].h
        low = candles[i].l
        prev_close = candles[i-1].c if i > 0 else candles[i].c
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_values.append(tr)
    
    return sum(tr_values) / len(tr_values)


def detect_rsi_divergence(candles: List[Candle], idx: int, rsi_vals: List[float], 
                          lookback: int = 15) -> Tuple[str, float]:
    """
    Detect RSI divergences using swing points.
    Returns: (divergence_type, strength)
    - 'bullish': price making lower lows, RSI making higher lows
    - 'bearish': price making higher highs, RSI making lower highs
    - 'none': no divergence
    """
    if idx < lookback + 5:
        return "none", 0.0
    
    bullish_strength = 0.0
    bearish_strength = 0.0
    
    # Find swing lows for bullish divergence
    swing_lows = []
    for i in range(idx - lookback, idx - 2):
        is_low = True
        for j in range(max(idx - lookback - 3, i - 3), min(idx, i + 3) + 1):
            if j != i and candles[j].l <= candles[i].l:
                is_low = False
                break
        if is_low:
            swing_lows.append((i, candles[i].l, rsi_vals[i]))
    
    # Need at least 2 swing lows
    if len(swing_lows) >= 2:
        recent_lows = swing_lows[-2:]
        prev_idx, prev_low, prev_rsi = recent_lows[0]
        curr_idx, curr_low, curr_rsi = recent_lows[1]
        
        # Bullish divergence: price lower low, RSI higher low
        if curr_low < prev_low * 0.985 and curr_rsi > prev_rsi * 1.03:
            price_diff = (prev_low - curr_low) / prev_low * 100
            rsi_diff = (curr_rsi - prev_rsi) / prev_rsi * 100
            bullish_strength = min((price_diff + rsi_diff) * 3, 100)
    
    # Find swing highs for bearish divergence
    swing_highs = []
    for i in range(idx - lookback, idx - 2):
        is_high = True
        for j in range(max(idx - lookback - 3, i - 3), min(idx, i + 3) + 1):
            if j != i and candles[j].h >= candles[i].h:
                is_high = False
                break
        if is_high:
            swing_highs.append((i, candles[i].h, rsi_vals[i]))
    
    if len(swing_highs) >= 2:
        recent_highs = swing_highs[-2:]
        prev_idx, prev_high, prev_rsi = recent_highs[0]
        curr_idx, curr_high, curr_rsi = recent_highs[1]
        
        # Bearish divergence: price higher high, RSI lower high
        if curr_high > prev_high * 1.015 and curr_rsi < prev_rsi * 0.97:
            price_diff = (curr_high - prev_high) / prev_high * 100
            rsi_diff = (prev_rsi - curr_rsi) / prev_rsi * 100
            bearish_strength = min((price_diff + rsi_diff) * 3, 100)
    
    if bullish_strength > bearish_strength and bullish_strength >= 25:
        return "bullish", bullish_strength
    elif bearish_strength > bullish_strength and bearish_strength >= 25:
        return "bearish", bearish_strength
    else:
        return "none", 0.0


def generate_signal(candles: List[Candle], idx: int, 
                    sma300: List[float], rsi_vals: List[float]) -> Tuple[str, float, float, float]:
    """
    Generate trading signal based on SMA 300 trend + RSI divergence.
    
    Rules:
    - BUY: Price above SMA 300 (uptrend) + Bullish RSI divergence
    - SELL: Price below SMA 300 (downtrend) + Bearish RSI divergence
    
    Returns: (direction, stop_loss, take_profit, confidence)
    """
    if idx < 300:
        return "hold", 0, 0, 0
    
    price = candles[idx].c
    sma300_val = sma300[idx]
    
    # Calculate ATR for dynamic stops
    atr = calc_atr(candles, idx, 14)
    
    # Detect RSI divergence
    div_type, div_strength = detect_rsi_divergence(candles, idx, rsi_vals, lookback=15)
    
    # Trend filter: SMA 300
    price_above_sma300 = price > sma300_val
    price_below_sma300 = price < sma300_val
    
    # Distance from SMA 300 (trend strength)
    distance_from_sma = abs(price - sma300_val) / sma300_val * 100
    strong_uptrend = price_above_sma300 and distance_from_sma > 2
    strong_downtrend = price_below_sma300 and distance_from_sma > 2
    
    # RSI momentum confirmation
    rsi = rsi_vals[idx]
    rsi_oversold = rsi < 35
    rsi_overbought = rsi > 65
    rsi_neutral_bull = 40 <= rsi < 55
    rsi_neutral_bear = 45 < rsi <= 60
    
    # === SIGNAL GENERATION ===
    buy_score = 0
    sell_score = 0
    confidence = 0.0
    
    # Primary signal: RSI divergence
    if div_type == "bullish":
        buy_score += 5
        confidence += div_strength * 0.4
    elif div_type == "bearish":
        sell_score += 5
        confidence += div_strength * 0.4
    
    # Trend filter: SMA 300 alignment (critical)
    if price_above_sma300 and div_type == "bullish":
        buy_score += 4
        confidence += 20
        if strong_uptrend:
            buy_score += 2
            confidence += 10
    
    if price_below_sma300 and div_type == "bearish":
        sell_score += 4
        confidence += 20
        if strong_downtrend:
            sell_score += 2
            confidence += 10
    
    # RSI momentum confirmation
    if rsi_oversold and div_type == "bullish":
        buy_score += 2
        confidence += 15
    if rsi_overbought and div_type == "bearish":
        sell_score += 2
        confidence += 15
    if rsi_neutral_bull and div_type == "bullish":
        buy_score += 1
        confidence += 8
    if rsi_neutral_bear and div_type == "bearish":
        sell_score += 1
        confidence += 8
    
    # Volume confirmation (optional boost)
    if idx >= 20:
        avg_vol = sum(c.v for c in candles[idx-20:idx]) / 20
        current_vol = candles[idx].v
        if current_vol > avg_vol * 1.3:
            confidence += 5
    
    # === DECISION ===
    # Dynamic TP/SL based on ATR and confidence
    atr_mult_sl = 2.5 - (min(confidence, 80) / 80) * 0.5  # 2.0 to 2.5
    atr_mult_tp = 4.5 + (min(confidence, 80) / 80) * 2.5  # 4.5 to 7.0
    
    if buy_score >= 7 and buy_score > sell_score:
        sl = price - (atr * atr_mult_sl)
        tp = price + (atr * atr_mult_tp)
        return "buy", sl, tp, min(confidence, 95)
    
    if sell_score >= 7 and sell_score > buy_score:
        sl = price + (atr * atr_mult_sl)
        tp = price - (atr * atr_mult_tp)
        return "sell", sl, tp, min(confidence, 95)
    
    return "hold", 0, 0, confidence


def run_backtest(candles: List[Candle]) -> Tuple[List[float], List[Trade], List[str]]:
    """Run the SMA 300 + RSI Divergence strategy backtest."""
    
    closes = [c.c for c in candles]
    sma300 = sma(closes, 300)
    rsi_vals = rsi(closes, 14)
    
    cash = INITIAL_CAPITAL
    pos = None
    trades = []
    equity_curve = []
    dates = []
    
    for i in range(1, len(candles)):
        candle = candles[i]
        dt = datetime.fromtimestamp(candle.ts / 1000).strftime("%Y-%m-%d")
        
        # Generate signal
        direction, sl, tp, confidence = generate_signal(
            candles, i, sma300, rsi_vals
        )
        
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
            
            # Signal reversal (exit on strong opposite signal)
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
        
        # Entry logic - only enter on high confidence
        if not pos and direction in ("buy", "sell") and confidence >= 45:
            # Dynamic position sizing based on confidence
            size_mult = 0.85 + (confidence / 100) * 0.15  # 0.85 to 1.0
            size = cash * POSITION_SIZE_PCT * size_mult
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
    
    # Close open position at end
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
    print(f"  SMA 300 + RSI DIVERGENCE STRATEGY — {SYMBOL}")
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
    
    with open("sma300_rsi_divergence_result.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n  Results saved to sma300_rsi_divergence_result.json")


def main():
    print("Fetching data...", end=" ", flush=True)
    candles = fetch_data(SYMBOL, START_DATE, END_DATE)
    
    if not candles:
        print("Failed to fetch data")
        return
    
    print(f"{len(candles)} candles loaded")
    print("Running SMA 300 + RSI Divergence Strategy backtest...\n")
    
    equity, trades, dates = run_backtest(candles)
    report(equity, trades, dates)


if __name__ == "__main__":
    main()