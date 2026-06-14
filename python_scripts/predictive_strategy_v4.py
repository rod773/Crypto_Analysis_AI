#!/usr/bin/env python3
"""
Predictive Strategy v4 - ULTIMATE High Return
Enhanced version of the original 68% strategy with:
- Adaptive position sizing based on signal strength
- Trailing stop-loss to capture more upside
- Better divergence detection (5-point instead of 2-point)
- Multi-timeframe confirmation
- Dynamic TP/SL based on ATR volatility
"""

import json
import math
import urllib.request
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple
from math import inf


@dataclass
class Candle:
    ts: int
    o: float
    h: float
    l: float
    c: float
    v: float


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
    e_fast = ema(closes, 12)
    e_slow = ema(closes, 26)
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


def calc_atr(candles: List[Candle], idx: int, period=14) -> float:
    """Calculate Average True Range for volatility-based stops"""
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


def detect_divergence_5point(candles: List[Candle], idx: int, rsi_vals: List[float]) -> Tuple[bool, bool, int]:
    """
    Enhanced 5-point divergence detection for stronger signals.
    Returns (bullish, bearish, strength)
    """
    if idx < 15:
        return False, False, 0
    
    # Sample 5 points across last 15 candles
    points = []
    for offset in [0, 3, 6, 9, 12]:
        if idx - offset >= 0:
            points.append((idx - offset, candles[idx - offset].l, rsi_vals[idx - offset]))
    
    if len(points) < 3:
        return False, False, 0
    
    # Check for higher lows in price + lower lows in RSI (bullish)
    bullish_count = 0
    bearish_count = 0
    
    for i in range(len(points) - 1):
        for j in range(i + 1, len(points)):
            p1_low = points[i][1]
            p2_low = points[j][1]
            r1 = points[i][2]
            r2 = points[j][2]
            
            if p1_low > p2_low and r1 < r2:
                bullish_count += 1
            if p1_low < p2_low and r1 > r2:
                bearish_count += 1
    
    # Strong divergence if multiple confirmations
    bullish = bullish_count >= 2
    bearish = bearish_count >= 2
    strength = max(bullish_count, bearish_count)
    
    return bullish, bearish, strength


def generate_signal_v4(candles: List[Candle], idx: int, rsi_func, macd_func, ma_func) -> Tuple[str, str, float, float, float]:
    """
    Enhanced predictive signal with adaptive stops and confidence scoring.
    Returns (direction, reason, stop_loss, take_profit, confidence)
    """
    if idx < 30:
        return "hold", "", 0, 0, 0
    
    closes = [c.c for c in candles[:idx + 1]]
    volumes = [c.v for c in candles[:idx + 1]]
    
    rsi_vals = rsi_func(closes)
    macd_l, macd_sig, hist = macd_func(closes)
    ma50 = ma_func(closes, 50)
    ma20 = ma_func(closes, 20)
    
    cur = idx
    price = candles[cur].c
    atr = calc_atr(candles, idx, 14)
    
    # Enhanced 5-point divergence
    bullish_div, bearish_div, div_strength = detect_divergence_5point(candles, idx, rsi_vals)
    
    # MACD Signal - enhanced timing
    macd_buy = False
    macd_sell = False
    
    # Histogram crossing zero with momentum
    if hist[cur] > 0 and hist[cur-1] <= 0:
        macd_buy = True
    if hist[cur] < 0 and hist[cur-1] >= 0:
        macd_sell = True
    
    # Histogram acceleration
    if cur >= 3:
        hist_accel = hist[cur] - hist[cur-2]
        if hist_accel > 0 and macd_l[cur] < macd_sig[cur]:
            macd_buy = True
        if hist_accel < 0 and macd_l[cur] > macd_sig[cur]:
            macd_sell = True
    
    # Volume confirmation
    avg_vol = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
    vol = volumes[-1]
    vol_confirmed = vol > avg_vol * 1.3
    
    # Multi-timeframe trend
    ma50_val = ma50[cur] if ma50[cur] else price
    ma20_val = ma20[cur] if ma20[cur] else price
    
    uptrend = price > ma20_val > ma50_val
    downtrend = price < ma20_val < ma50_val
    
    # RSI momentum
    rsi = rsi_vals[cur]
    rsi_oversold = rsi < 30
    rsi_overbought = rsi > 70
    rsi_neutral_bull = 35 <= rsi < 50
    rsi_neutral_bear = 50 < rsi <= 65
    
    # === ENHANCED SCORING ===
    buy_score = 0
    sell_score = 0
    
    # Divergence (highest weight - most reliable signal)
    if bullish_div:
        buy_score += 4 + div_strength
    if bearish_div:
        sell_score += 4 + div_strength
    
    # MACD
    if macd_buy:
        buy_score += 3
    if macd_sell:
        sell_score += 3
    
    # Trend alignment
    if uptrend:
        buy_score += 2
    if downtrend:
        sell_score += 2
    
    # RSI
    if rsi_oversold:
        buy_score += 2
    if rsi_overbought:
        sell_score += 2
    if rsi_neutral_bull:
        buy_score += 1
    if rsi_neutral_bear:
        sell_score += 1
    
    # Volume confirmation (boosts signal)
    if vol_confirmed:
        if buy_score > sell_score:
            buy_score += 1
        elif sell_score > buy_score:
            sell_score += 1
    
    # === DECISION WITH CONFIDENCE ===
    confidence = abs(buy_score - sell_score) * 10
    
    # Dynamic TP/SL based on ATR and confidence
    atr_mult_sl = 2.5 - (min(confidence, 80) / 80) * 0.5  # 2.0 to 2.5
    atr_mult_tp = 4.0 + (min(confidence, 80) / 80) * 2.0  # 4.0 to 6.0
    
    if buy_score > sell_score and buy_score >= 4:
        sl = price - (atr * atr_mult_sl)
        tp = price + (atr * atr_mult_tp)
        reason = "div" if bullish_div else ("macd" if macd_buy else "trend")
        return "buy", reason, sl, tp, min(confidence, 95)
    
    if sell_score > buy_score and sell_score >= 4:
        sl = price + (atr * atr_mult_sl)
        tp = price - (atr * atr_mult_tp)
        reason = "div" if bearish_div else ("macd" if macd_sell else "trend")
        return "sell", reason, sl, tp, min(confidence, 95)
    
    return "hold", "", 0, 0, confidence


def run_backtest(candles: List[Candle], symbol: str = "ETHUSDT", 
                 start_date: str = "2024-06-13", end_date: str = "2025-06-13",
                 initial_capital: float = 10_000.0, position_size_pct: float = 0.95,
                 fee_pct: float = 0.001, use_trailing_stop: bool = True):
    """Run the v4 strategy backtest with trailing stop option."""
    
    cash = initial_capital
    pos = None
    trades = []
    equity_curve = []
    dates = []
    
    for i in range(1, len(candles)):
        day = candles[i]
        dt = datetime.fromtimestamp(day.ts / 1000).strftime("%Y-%m-%d")
        direction, reason, sl, tp, confidence = generate_signal_v4(candles, i, rsi, macd_vals, ma)
        
        # Update trailing stop if enabled
        if pos and use_trailing_stop:
            if pos["direction"] == "long":
                # Trail stop below price
                new_sl = day.c - (pos["entry"] - pos["initial_sl"]) * 0.5
                if new_sl > pos["sl"]:
                    pos["sl"] = new_sl
            elif pos["direction"] == "short":
                # Trail stop above price
                new_sl = day.c + (pos["initial_sl"] - pos["entry"]) * 0.5
                if new_sl < pos["sl"]:
                    pos["sl"] = new_sl
        
        # Exit logic
        if pos:
            exited = False
            
            # Stop loss
            if pos["direction"] == "long" and day.l <= pos["sl"]:
                exit_price = pos["sl"]
                pnl = ((exit_price - pos["entry"]) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * fee_pct)
                trades.append({"entry": pos["entry"], "exit": exit_price, "pnl": pnl, 
                              "reason": "stop_loss", "date": dt, "direction": "long"})
                pos = None
                exited = True
                
            elif pos["direction"] == "short" and day.h >= pos["sl"]:
                exit_price = pos["sl"]
                pnl = ((pos["entry"] - exit_price) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * fee_pct)
                trades.append({"entry": pos["entry"], "exit": exit_price, "pnl": pnl, 
                              "reason": "stop_loss", "date": dt, "direction": "short"})
                pos = None
                exited = True
            
            # Take profit
            if not exited and pos:
                if pos["direction"] == "long" and day.h >= pos["tp"]:
                    exit_price = pos["tp"]
                    pnl = ((exit_price - pos["entry"]) / pos["entry"]) * pos["size"]
                    cash += pos["size"] + pnl - (pos["size"] * fee_pct)
                    trades.append({"entry": pos["entry"], "exit": exit_price, "pnl": pnl, 
                                  "reason": "take_profit", "date": dt, "direction": "long"})
                    pos = None
                    exited = True
                    
                elif pos["direction"] == "short" and day.l <= pos["tp"]:
                    exit_price = pos["tp"]
                    pnl = ((pos["entry"] - exit_price) / pos["entry"]) * pos["size"]
                    cash += pos["size"] + pnl - (pos["size"] * fee_pct)
                    trades.append({"entry": pos["entry"], "exit": exit_price, "pnl": pnl, 
                                  "reason": "take_profit", "date": dt, "direction": "short"})
                    pos = None
                    exited = True
            
            # Signal reversal (only on high confidence)
            if not exited and pos and confidence > 50:
                if (pos["direction"] == "long" and direction == "sell") or \
                   (pos["direction"] == "short" and direction == "buy"):
                    exit_price = day.c
                    if pos["direction"] == "long":
                        pnl = ((exit_price - pos["entry"]) / pos["entry"]) * pos["size"]
                    else:
                        pnl = ((pos["entry"] - exit_price) / pos["entry"]) * pos["size"]
                    cash += pos["size"] + pnl - (pos["size"] * fee_pct)
                    trades.append({"entry": pos["entry"], "exit": exit_price, "pnl": pnl, 
                                  "reason": "reversal", "date": dt, "direction": pos["direction"]})
                    pos = None
        
        # Entry logic - scale position by confidence
        if not pos and direction in ("buy", "sell") and confidence >= 30:
            # Dynamic position sizing based on confidence
            size_mult = 0.7 + (confidence / 100) * 0.3  # 0.7 to 1.0
            size = cash * position_size_pct * size_mult
            cash -= size
            
            side = "long" if direction == "buy" else "short"
            pos = {
                "side": side,
                "direction": side,
                "entry": day.c,
                "sl": sl,
                "tp": tp,
                "initial_sl": sl,
                "size": size,
                "date": dt,
                "confidence": confidence,
            }
        
        # Track equity
        eq = cash
        if pos:
            val = pos["size"]
            if pos["side"] == "long":
                val *= (day.c / pos["entry"])
            else:
                val *= (pos["entry"] / day.c)
            eq += val
        equity_curve.append(eq)
        dates.append(dt)
    
    # Close open position
    if pos:
        p = pos
        final_price = candles[-1].c
        if p["side"] == "long":
            pnl = ((final_price - p["entry"]) / p["entry"]) * p["size"]
        else:
            pnl = ((p["entry"] - final_price) / p["entry"]) * p["size"]
        cash += p["size"] + pnl - (p["size"] * fee_pct)
        trades.append({"entry": p["entry"], "exit": final_price, "pnl": pnl, 
                      "reason": "end", "date": dates[-1], "direction": p["side"]})
    
    return equity_curve, trades, dates


def report(equity, trades, dates, initial_capital=10_000.0, symbol="ETHUSDT"):
    """Generate detailed performance report."""
    
    final_value = equity[-1]
    ret = ((final_value / initial_capital) - 1) * 100
    
    ups = [t for t in trades if t["pnl"] > 0]
    downs = [t for t in trades if t["pnl"] <= 0]
    
    # Calculate max drawdown
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
    
    # Trade stats
    total_trades = len(trades)
    win_rate = len(ups) / total_trades * 100 if total_trades else 0
    avg_win = sum(t["pnl"] for t in ups) / len(ups) if ups else 0
    avg_loss = sum(t["pnl"] for t in downs) / len(downs) if downs else 0
    profit_factor = sum(t["pnl"] for t in ups) / abs(sum(t["pnl"] for t in downs)) if downs and sum(t["pnl"] for t in downs) != 0 else inf
    
    # Print report
    print("=" * 70)
    print(f"  PREDICTIVE STRATEGY v4 (ULTIMATE) — {symbol}")
    print(f"  Period: 2024-06-13 to 2025-06-13")
    print("=" * 70)
    print(f"  Initial Capital:    ${initial_capital:>12,.2f}")
    print(f"  Final Value:        ${final_value:>12,.2f}")
    print(f"  Total Return:       {ret:>12.2f}%")
    print(f"  Max Drawdown:       ${max_dd:>12,.2f}  ({max_dd_pct:.1f}%)")
    print(f"  Sharpe Ratio:       {sharpe:>12.3f}")
    print(f"  Total Trades:       {total_trades:>12}")
    print(f"  Win Rate:           {win_rate:>11.1f}%")
    print(f"  Avg Win:            ${avg_win:>12,.2f}  ({len(ups)} trades)")
    print(f"  Avg Loss:           ${avg_loss:>12,.2f}  ({len(downs)} trades)")
    if isinstance(profit_factor, float):
        print(f"  Profit Factor:      {profit_factor:>12.3f}")
    print("=" * 70)
    
    # Recent trades
    print("  Recent Trades:")
    for t in trades[-5:]:
        dir_sym = "LONG" if t["direction"] == "long" else "SHORT"
        pnl_sym = "+" if t["pnl"] > 0 else ""
        print(f"  {t['date']} | {dir_sym:>5} | Entry: ${t['entry']:>8,.2f} | "
              f"Exit: ${t['exit']:>8,.2f} | P&L: {pnl_sym}${t['pnl']:>8,.2f} | {t['reason']}")
    print("=" * 70)
    
    # Save results
    output = {
        "symbol": symbol,
        "initial_capital": initial_capital,
        "final_value": final_value,
        "total_return_pct": ret,
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd_pct,
        "sharpe_ratio": sharpe,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor if isinstance(profit_factor, float) else "inf",
        "dates": dates,
        "equity_curve": equity,
        "trades": trades,
    }
    
    with open("predictive_v4_ultimate_result.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n  Results saved to predictive_v4_ultimate_result.json")
    
    return ret


def fetch_data(symbol: str, start: str, end: str) -> List[Candle]:
    """Fetch candle data from Binance."""
    s = int(datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={s}&endTime={e}&limit=1000"
    
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
        return [Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])) for k in data]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def main():
    print("Fetching data...", end=" ", flush=True)
    candles = fetch_data("ETHUSDT", "2024-06-13", "2025-06-13")
    
    if not candles:
        print("Failed to fetch data")
        return
    
    print(f"{len(candles)} candles loaded")
    print("Running Predictive Strategy v4 (ULTIMATE)...\n")
    
    equity, trades, dates = run_backtest(candles)
    ret = report(equity, trades, dates)
    
    print(f"\n  >> TARGET: Beat 68% return from original strategy")
    print(f"  >> v4 RETURN: {ret:.2f}%")
    
    if ret > 68:
        print(f"  >> SUCCESS! v4 outperforms original by {ret - 68:.2f}%")
    else:
        print(f"  >> Original still better by {68 - ret:.2f}%")


if __name__ == "__main__":
    main()