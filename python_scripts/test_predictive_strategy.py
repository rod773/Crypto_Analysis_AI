#!/usr/bin/env python3
"""One-year backtest using predictive_strategy.py — verify ~68% return."""

import json, math, urllib.request
from datetime import datetime
from predictive_strategy import Candle, generate_signal

SYMBOL = "ETHUSDT"
START = "2024-06-13"
END = "2025-06-13"
INITIAL_CAPITAL = 10000.0
FEE_PCT = 0.001

def fetch(symbol, start, end):
    s = int(datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={s}&endTime={e}&limit=1000"
    data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
    return [Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])) for k in data]

def run(candles):
    cash = INITIAL_CAPITAL
    pos = None
    trades = []
    equity, dates = [], []

    for i in range(1, len(candles)):
        day = candles[i]
        dt = datetime.fromtimestamp(day.ts / 1000).strftime("%Y-%m-%d")
        direction, reason, sl, tp = generate_signal(candles, i)

        # Exit
        if pos:
            if pos["side"] == "long" and day.l <= pos["sl"]:
                pnl = ((pos["sl"] - pos["entry"]) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                trades.append({"entry": pos["entry"], "exit": pos["sl"], "pnl": pnl, "reason": "sl", "date": dt})
                pos = None
            elif pos["side"] == "short" and day.h >= pos["sl"]:
                pnl = ((pos["entry"] - pos["sl"]) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                trades.append({"entry": pos["entry"], "exit": pos["sl"], "pnl": pnl, "reason": "sl", "date": dt})
                pos = None
            elif pos["side"] == "long" and day.h >= pos["tp"]:
                pnl = ((pos["tp"] - pos["entry"]) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                trades.append({"entry": pos["entry"], "exit": pos["tp"], "pnl": pnl, "reason": "tp", "date": dt})
                pos = None
            elif pos["side"] == "short" and day.l <= pos["tp"]:
                pnl = ((pos["entry"] - pos["tp"]) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                trades.append({"entry": pos["entry"], "exit": pos["tp"], "pnl": pnl, "reason": "tp", "date": dt})
                pos = None
            elif (pos["side"] == "long" and direction == "sell") or (pos["side"] == "short" and direction == "buy"):
                p = day.c
                if pos["side"] == "long":
                    pnl = ((p - pos["entry"]) / pos["entry"]) * pos["size"]
                else:
                    pnl = ((pos["entry"] - p) / pos["entry"]) * pos["size"]
                cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
                trades.append({"entry": pos["entry"], "exit": p, "pnl": pnl, "reason": "reversal", "date": dt})
                pos = None

        # Entry
        if not pos and direction in ("buy", "sell"):
            size = cash * 0.95
            cash -= size
            side = "long" if direction == "buy" else "short"
            pos = {"side": side, "entry": day.c, "sl": sl, "tp": tp, "size": size, "date": dt}

        # Track equity
        eq = cash
        if pos:
            val = pos["size"]
            if pos["side"] == "long":
                val *= (day.c / pos["entry"])
            else:
                val *= (pos["entry"] / day.c)
            eq += val
        equity.append(eq)
        dates.append(dt)

    # Close open position
    if pos:
        p = candles[-1].c
        if pos["side"] == "long":
            pnl = ((p - pos["entry"]) / pos["entry"]) * pos["size"]
        else:
            pnl = ((pos["entry"] - p) / pos["entry"]) * pos["size"]
        cash += pos["size"] + pnl - (pos["size"] * FEE_PCT)
        trades.append({"entry": pos["entry"], "exit": p, "pnl": pnl, "reason": "end", "date": dates[-1]})

    return equity, trades, dates

def report(equity, trades, dates):
    ret = ((equity[-1] / INITIAL_CAPITAL) - 1) * 100
    ups = [t for t in trades if t["pnl"] > 0]
    downs = [t for t in trades if t["pnl"] <= 0]

    print(f"\n{'='*60}")
    print(f"  PREDICTIVE STRATEGY BACKTEST — {SYMBOL}")
    print(f"  Period: {START} to {END}")
    print(f"{'='*60}")
    print(f"  Final Value:   ${equity[-1]:>8,.2f}")
    print(f"  Total Return:  {ret:>+8.2f}%")
    print(f"  Trades:        {len(trades):>8} (W: {len(ups)} / L: {len(downs)})")
    if trades:
        print(f"  Win Rate:      {len(ups)/len(trades)*100:>7.1f}%")
        print(f"  Avg Win:       ${sum(t['pnl'] for t in ups)/len(ups):>8,.2f}")
        print(f"  Avg Loss:      ${sum(t['pnl'] for t in downs)/len(downs):>8,.2f}")
    print(f"{'='*60}\n")

    # Save
    json.dump({"dates": dates, "equity": equity, "trades": trades},
              open("test_predictive_result.json", "w"), indent=2)
    print("Saved test_predictive_result.json")

def main():
    print("Fetching data...", end=" ", flush=True)
    candles = fetch(SYMBOL, START, END)
    print(f"{len(candles)} candles")
    print("Running backtest...")
    equity, trades, dates = run(candles)
    report(equity, trades, dates)

if __name__ == "__main__":
    main()
