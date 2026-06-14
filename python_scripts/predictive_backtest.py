#!/usr/bin/env python3
"""
Predictive Backtest Engine for Crypto Analysis AI.
Replaces reactive 'change24h' logic with predictive signals based on
RSI Divergence, MACD Crossover, S/R levels, and Volume.
"""

import json
import math
import urllib.request
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

# ─── CONFIG ─────────────────────────────────────────────────────────────────
SYMBOL = "ETHUSDT"; INTERVAL = "1m"
START = "2024-06-13"; END = "2024-06-14"
INITIAL_CAPITAL = 10000.0; FEE_PCT = 0.001

@dataclass 
class Candle:
    ts: int; o: float; h: float; l: float; c: float; v: float

@dataclass
class State:
    cash: float
    position: Optional[Dict] = None
    trades: List[Dict] = field(default_factory=list)
    equity_log: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)

# ─── FETCHER ────────────────────────────────────────────────────────────────

def fetch(symbol: str, start: str, end: str) -> List[Candle]:
    s = int(datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = (f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={INTERVAL}"
           f"&startTime={s}&endTime={e}&limit=1000")
    data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
    return [Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])) for k in data]

# ─── INDICATORS ────────────────────────────────────────────────────────────

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
            gains.append(max(0, diff)); losses.append(max(0, -diff))
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
        if i < period - 1: res.append(sum(prices[:i+1]) / (i + 1))
        else: res.append(sum(prices[i - period + 1:i + 1]) / period)
    return res

# ─── SIGNAL ENGINE ──────────────────────────────────────────────────────────

def generate_signal(candles: List[Candle], idx: int) -> Tuple[str, str, float, float]:
    if idx < 30: return "hold", "", 0, 0
    closes = [c.c for c in candles[:idx + 1]]
    volumes = [c.v for c in candles[:idx + 1]]
    
    rsi_vals = rsi(closes)
    macd_l, macd_sig, hist = macd_vals(closes)
    ma50 = ma(closes, 50)
    
    cur, prev = idx, idx - 1
    price = candles[cur].c
    
    # Divergence check (last ~10 candles)
    bullish, bearish = False, False
    if idx > 20:
        recent_lows = [(i, candles[i].l) for i in range(idx-10, idx+1, 3)]
        if len(recent_lows) >= 2:
            p_lows = recent_lows[-2:]; r_lows = [(i, rsi_vals[i]) for i, _ in recent_lows[-2:]]
            if p_lows[0][1] > p_lows[1][1] and r_lows[0][1] < r_lows[1][1]: bullish = True
            if p_lows[0][1] < p_lows[1][1] and r_lows[0][1] > r_lows[1][1]: bearish = True

    # MACD Signal Prediction
    hist_growing = hist[cur] > hist[cur - 2]
    hist_declining = hist[cur] < hist[cur - 2]
    macd_buy = hist_growing and macd_l[cur] < macd_sig[cur]
    macd_sell = hist_declining and macd_l[cur] > macd_sig[cur]
    
    # Volume
    avg_vol = sum(volumes[-20:]) / 20; vol = volumes[-1]
    
    # Scoring
    buy_score, sell_score = 0, 0
    if bullish: buy_score += 3
    if macd_buy: buy_score += 2
    if ma50[cur] and price > ma50[cur]: buy_score += 1
    if rsi_vals[cur] < 35: buy_score += 1
    if vol > avg_vol * 1.5: buy_score += 1
    
    if bearish: sell_score += 3
    if macd_sell: sell_score += 2
    if ma50[cur] and price < ma50[cur]: sell_score += 1
    if rsi_vals[cur] > 65: sell_score += 1
    if vol > avg_vol * 1.5: sell_score += 1

    # Entry Thresholds
    if buy_score > sell_score and buy_score >= 3:
        return "buy", "div" if bullish else "macd", price * 0.94, price * 1.12
    if sell_score > buy_score and sell_score >= 3:
        return "sell", "div" if bearish else "macd", price * 1.06, price * 0.9
    return "hold", "", 0, 0

# ─── BACKTEST ───────────────────────────────────────────────────────────────

def run(candles: List[Candle]):
    state = State(cash=INITIAL_CAPITAL)
    for i in range(1, len(candles)):
        day = candles[i]; dt = datetime.fromtimestamp(day.ts / 1000).strftime("%Y-%m-%d")
        direction, reason, sl, tp = generate_signal(candles, i)
        
        # Exit management
        if state.position:
            pos = state.position
            if pos["side"] == "long" and day.l <= pos["sl"]:
                pnl = ((pos["sl"] - pos["entry"]) / pos["entry"]) * pos["size"]
                state.cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                state.trades.append({"entry": pos["entry"], "exit": pos["sl"], "pnl": pnl, "reason": "sl", "date": dt})
                state.position = None
            elif pos["side"] == "short" and day.h >= pos["sl"]:
                pnl = ((pos["entry"] - pos["sl"]) / pos["entry"]) * pos["size"]
                state.cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                state.trades.append({"entry": pos["entry"], "exit": pos["sl"], "pnl": pnl, "reason": "sl", "date": dt})
                state.position = None
            elif pos["side"] == "long" and day.h >= pos["tp"]:
                pnl = ((pos["tp"] - pos["entry"]) / pos["entry"]) * pos["size"]
                state.cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                state.trades.append({"entry": pos["entry"], "exit": pos["tp"], "pnl": pnl, "reason": "tp", "date": dt})
                state.position = None
            elif pos["side"] == "short" and day.l <= pos["tp"]:
                pnl = ((pos["entry"] - pos["tp"]) / pos["entry"]) * pos["size"]
                state.cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                state.trades.append({"entry": pos["entry"], "exit": pos["tp"], "pnl": pnl, "reason": "tp", "date": dt})
                state.position = None
            elif (pos["side"] == "long" and direction == "sell") or (pos["side"] == "short" and direction == "buy"):
                p = day.c; pnl = ((p - pos["entry"]) / pos["entry"]) * pos["size"] if pos["side"] == "long" else ((pos["entry"] - p) / pos["entry"]) * pos["size"]
                state.cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                state.trades.append({"entry": pos["entry"], "exit": p, "pnl": pnl, "reason": "reversal", "date": dt})
                state.position = None
        
        # Entry Logic
        if not state.position and direction in ["buy", "sell"]:
            size = state.cash * 0.95; state.cash -= size
            side = "long" if direction == "buy" else "short"
            state.position = {"side": side, "entry": day.c, "sl": sl, "tp": tp, "size": size, "date": dt, "idx": i}
        
        # Equity tracking
        eq = state.cash
        if state.position:
            pos = state.position
            val = pos["size"]
            if pos["side"] == "long": val *= (day.c / pos["entry"])
            else: val *= (pos["entry"] / day.c)
            eq += val
        state.equity_log.append(eq); state.dates.append(dt)
    
    # Close open position
    if state.position:
        pos = state.position; p = candles[-1].c
        pnl = ((p - pos["entry"]) / pos["entry"]) * pos["size"] if pos["side"] == "long" else ((pos["entry"] - p) / pos["entry"]) * pos["size"]
        state.cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
        state.trades.append({"entry": pos["entry"], "exit": p, "pnl": pnl, "reason": "end", "date": datetime.fromtimestamp(candles[-1].ts / 1000).strftime("%Y-%m-%d")})
        state.position = None
    
    return state

def main():
    print("Fetching data..."); candles = fetch(SYMBOL, START, END)
    print(f"Loaded {len(candles)} candles")
    print("Running PREDICTIVE backtest...")
    state = run(candles)
    
    ups = [t for t in state.trades if t["pnl"] > 0]; downs = [t for t in state.trades if t["pnl"] <= 0]
    ret = ((state.equity_log[-1] / INITIAL_CAPITAL) - 1) * 100
    
    print(f"\n{'='*60}\\n PREDICTIVE BACKTEST RESULTS\\n{'='*60}")
    print(f"Final Value:  ${state.equity_log[-1]:,.2f}")
    print(f"Total Return: {ret:.2f}%")
    print(f"Trades: {len(state.trades)} (W: {len(ups)} / L: {len(downs)})")
    if state.trades:
        print(f"Win Rate:     {len(ups)/len(state.trades)*100:.1f}%")
        print(f"Avg Win:      ${sum(t['pnl'] for t in ups)/len(ups):,.2f} (n={len(ups)})")
        print(f"Avg Loss:     ${sum(t['pnl'] for t in downs)/len(downs):,.2f} (n={len(downs)})")
    
    # Save
    out = {"dates": state.dates, "equity": state.equity_log, "trades": state.trades,
           "candles": [{"date": datetime.fromtimestamp(c.ts/1000).strftime("%Y-%m-%d"),"close":c.c} for c in candles[1:]]}
    with open("predictive_backtest.json","w") as f: json.dump(out, f, indent=2)
    print("Saved to predictive_backtest.json")

if __name__ == "__main__": main()