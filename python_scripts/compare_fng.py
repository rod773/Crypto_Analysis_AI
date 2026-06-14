#!/usr/bin/env python3
"""Compare analysis.ts backtest with and without FNG overrides."""

import sys, json, math
from datetime import datetime
from analysis_backtest import *

def run_backtest(candles, fng_data, use_fng=True):
    ph = PriceHistory(maxlen=120)
    state = State(cash=INITIAL_CAPITAL)

    for i in range(len(candles)):
        c = candles[i]
        dt = datetime.fromtimestamp(c.ts / 1000).strftime("%Y-%m-%d")
        change24h = ((c.c - candles[i-1].c) / candles[i-1].c) * 100 if i > 0 else 0
        fng = fng_data.get(dt, 50)

        ph.update(c.c, c.v, c.h, c.l, change24h)
        sig = generate_signal(ph)

        short, long_v, conf, sl, tp_s, tp_l = "hold", "hold", 50, round_price(c.c * 0.93), round_price(c.c * 1.06), round_price(c.c * 1.15)

        if sig["direction"] == "buy":
            short = "buy"; long_v = "buy"; conf = sig["confidence"]
            sl = round_price(c.c * 0.94); tp_s = round_price(c.c * 1.12); tp_l = round_price(c.c * 1.28)
        elif sig["direction"] == "sell":
            short = "sell"; long_v = "hold"; conf = sig["confidence"]
            sl = round_price(c.c * 1.06); tp_s = round_price(c.c * 0.90); tp_l = round_price(c.c * 1.05)

        if use_fng:
            if fng < 20 and short == "sell": short = "hold"
            if fng > 80 and short == "buy": short = "hold"

        # Exit
        if state.pos:
            p = state.pos
            if p["direction"] == "long" and c.l <= p["sl"]:
                pnl = (p["sl"] - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], p["sl"], dt, pnl, "stop_loss"))
                state.pos = None
            elif p["direction"] == "short" and c.h >= p["sl"]:
                pnl = (p["entry"] - p["sl"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], p["sl"], dt, pnl, "stop_loss"))
                state.pos = None
            elif p["direction"] == "long" and c.h >= p["tp"]:
                pnl = (p["tp"] - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], p["tp"], dt, pnl, "take_profit"))
                state.pos = None
            elif p["direction"] == "short" and c.l <= p["tp"]:
                pnl = (p["entry"] - p["tp"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], p["tp"], dt, pnl, "take_profit"))
                state.pos = None
            elif (p["direction"] == "long" and short == "sell") or (p["direction"] == "short" and short == "buy"):
                pnl = ((c.c - p["entry"]) / p["entry"] * p["size"]) if p["direction"] == "long" else ((p["entry"] - c.c) / p["entry"] * p["size"])
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], p["direction"], p["size"], c.c, dt, pnl, "signal_reversal"))
                state.pos = None

        # Entry
        if not state.pos and short in ("buy", "sell"):
            size = state.cash * POSITION_SIZE_PCT
            state.cash -= size
            direction = "long" if short == "buy" else "short"
            state.pos = {"direction": direction, "entry": c.c, "sl": sl, "tp": tp_s, "size": size, "entry_date": dt, "entry_idx": i}

        eq = state.cash
        if state.pos:
            p = state.pos
            val = p["size"]
            if p["direction"] == "long": val *= (c.c / p["entry"])
            else: val *= (p["entry"] / c.c)
            eq += val
        state.equity_curve.append(eq)
        state.dates.append(dt)

    if state.pos:
        p = state.pos; c_last = candles[-1]
        pnl = ((c_last.c - p["entry"]) / p["entry"] * p["size"]) if p["direction"] == "long" else ((p["entry"] - c_last.c) / p["entry"] * p["size"])
        state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
        state.trades.append(Trade(p["entry_date"], p["entry"], p["direction"], p["size"], c_last.c, datetime.fromtimestamp(c_last.ts / 1000).strftime("%Y-%m-%d"), pnl, "end_of_test"))
        state.pos = None

    return state

candles = fetch_binance(SYMBOL, START_DATE, END_DATE)
fng_data = fetch_fng()

for label, use_fng in [("WITH FNG overrides", True), ("WITHOUT FNG overrides", False)]:
    state = run_backtest(candles, fng_data, use_fng)
    ret = ((state.equity_curve[-1] / INITIAL_CAPITAL) - 1) * 100
    wins = len([t for t in state.trades if t.pnl > 0])
    total = len(state.trades)
    print(f"\n{label}:")
    print(f"  Return:    {ret:+.2f}%")
    print(f"  Trades:    {total} (W: {wins}/{total} = {wins/total*100:.1f}%)")
    print(f"  Final:     ${state.equity_curve[-1]:,.2f}")
