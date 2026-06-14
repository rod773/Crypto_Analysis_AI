#!/usr/bin/env python3
"""
Backtest for the exact scoring strategy from src/lib/analysis.ts.
Faithfully reproduces calcWeightedScore and buildVerdict logic.
"""

import json, math, urllib.request, sys
from datetime import datetime, timedelta
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
    ts: int; o: float; h: float; l: float; c: float; v: float

@dataclass
class Trade:
    entry_date: str; entry_price: float; direction: str; size_usd: float
    exit_price: Optional[float] = None; exit_date: Optional[str] = None
    pnl: float = 0.0; exit_reason: str = ""

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
            if d > 0: gains += d
            else: losses -= d
        rsi = 100.0 if losses == 0 else 100.0 - (100.0 / (1 + gains / period / (losses / period)))
        r.append(rsi)
    return r

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

def simulate_data(closes: List[float], rsi_vals: List[float], i: int, price: float, change24h: float):
    """Simulate all data sources from price action."""
    idx = i
    trend = "bullish" if change24h > 1.5 else "bearish" if change24h < -1.5 else "neutral"
    
    # Timeframe data — derive multi-trend from recent price behavior
    short_trend = "bullish" if price > (closes[idx-3] if idx >= 3 else price) else "bearish" if price < (closes[idx-3] if idx >= 3 else price) else "neutral"
    mid_trend = "bullish" if price > (closes[idx-7] if idx >= 7 else price) else "bearish" if price < (closes[idx-7] if idx >= 7 else price) else "neutral"
    
    # Alignment: check if 3 + 1h (short), 4h (mid), daily (all from closes) agree
    daily_t = trend
    fourh_t = mid_trend
    oneh_t = short_trend
    aligned = daily_t == fourh_t == oneh_t and daily_t != "neutral"
    partial = (daily_t == fourh_t or daily_t == oneh_t or fourh_t == oneh_t) and not aligned
    alignment = "aligned" if aligned else "partial" if partial else "conflicting"
    
    # MA50/MA200 status
    ma50 = calc_ma(closes, 50)[idx] if idx >= 50 else price
    ma200 = calc_ma(closes, 200)[idx] if idx >= 200 else price
    ma_status = ""
    if ma200 and price > ma200:
        if price > ma50: ma_status = "above 200 MA"
        else: ma_status = "above 50 MA"
    else:
        ma_status = "below 200 MA"
    
    timeframe_data = {
        "daily": {"trend": daily_t, "rsi": rsi_vals[idx], "maStatus": ma_status},
        "fourHour": {"trend": fourh_t, "rsi": rsi_vals[idx] + 2, "maStatus": ma_status},
        "oneHour": {"trend": oneh_t, "rsi": rsi_vals[idx] + 1, "maStatus": ma_status},
        "alignment": alignment,
        "dominantTrend": daily_t,
    }
    
    # Elliott Wave (simplified from price structure)
    ew_trend = "impulse" if abs(change24h) > 3 else "corrective" if abs(change24h) > 1 else "neutral"
    if ew_trend == "impulse":
        # Detect which wave based on recent momentum
        if change24h > 0 and change24h > 4:
            cur_wave = 3
        elif change24h > 0:
            cur_wave = 1
        else:
            cur_wave = 5
    elif ew_trend == "corrective":
        cur_wave = -1 if abs(change24h) < 3 else -3
    else:
        cur_wave = 0
    
    # SMC (Smart Money Concepts)
    smc_struct = "uptrend" if price > (closes[idx-5] if idx >= 5 else price) + price * 0.02 else \
                 "downtrend" if price < (closes[idx-5] if idx >= 5 else price) - price * 0.02 else "ranging"
    last_bos = "bullish" if change24h > 2 else "bearish" if change24h < -2 else None
    
    # On-chain (use change24h to seed pseudo-random but deterministic values)
    seed = hash((idx, price)) % 1000
    funding_rate = 0.001 + (seed % 100) / 100_000 * (1 if change24h > 0 else -1 * 0.5)
    exchange_net_flow = "outflows (-)" if change24h > 0 else "inflows (+)"
    
    # Sentiment / Fear & Greed (derive from RSI + trend)
    fng = max(10, min(90, int(50 + rsi_vals[idx] - 50 + (10 if change24h > 3 else -10 if change24h < -3 else 0))))
    
    # Order book (simulate)
    bid_ask = 1.0 + (seed % 200 - 100) / 500
    if bid_ask < 0.5: bid_ask = 0.5
    
    # Whale activity
    accum = "accumulating" if change24h > 2 else "distributing" if change24h < -2 else "neutral"
    
    # Macro risk
    risk_on = change24h > -2
    
    return {
        "rsi": max(15, min(85, round(rsi_vals[idx]))),
        "trend": trend,
        "ma50": ma50,
        "ma200": ma200,
        "fng": fng,
        "funding_rate": funding_rate,
        "exchange_net_flow": exchange_net_flow,
        "bid_ask_ratio": round(bid_ask, 2),
        "accumulation": accum,
        "timeframe": timeframe_data,
        "alignment": alignment,
        "dominantTrend": daily_t,
        "elliott_wave_trend": ew_trend,
        "elliott_wave_current": cur_wave,
        "smc_structure": smc_struct,
        "smc_last_bos": last_bos,
        "risk_on": risk_on,
    }

# ─── EXACT STRATEGY FROM analysis.ts ──────────────────────────────────────────

def calc_weighted_score(ctx: dict) -> dict:
    rsi = ctx["rsi"]
    tech_trend = ctx["trend"]
    timeframe = ctx["timeframe"]
    smc_structure = ctx["smc_structure"]
    smc_last_bos = ctx["smc_last_bos"]
    ew_trend = ctx["elliott_wave_trend"]
    ew_cur = ctx["elliott_wave_current"]
    fng = ctx["fng"]
    bid_ask = ctx["bid_ask_ratio"]
    accum = ctx["accumulation"]
    funding = ctx["funding_rate"]
    risk_on = ctx["risk_on"]

    buy_score = 0
    sell_score = 0
    buy_weight = 0
    sell_weight = 0

    # 1. RSI Momentum (weight: 15%)
    if rsi < 30: buy_score += 3; buy_weight += 15
    elif rsi < 40: buy_score += 2; buy_weight += 10
    elif rsi > 70: sell_score += 3; sell_weight += 15
    elif rsi > 60: sell_score += 2; sell_weight += 10

    # 2. Trend Direction (weight: 20%)
    if tech_trend == 'bullish': buy_score += 3; buy_weight += 20
    elif tech_trend == 'bearish': sell_score += 3; sell_weight += 20

    # 3. Multi-Timeframe Alignment (weight: 20%)
    alignment = timeframe["alignment"]
    dominant_trend = timeframe["dominantTrend"]
    if alignment == 'aligned':
        if dominant_trend == 'bullish': buy_score += 3; buy_weight += 20
        elif dominant_trend == 'bearish': sell_score += 3; sell_weight += 20
    elif alignment == 'partial':
        if dominant_trend == 'bullish': buy_score += 1; buy_weight += 8
        elif dominant_trend == 'bearish': sell_score += 1; sell_weight += 8

    # 4. SMC Market Structure (weight: 15%)
    if smc_structure == 'uptrend' and smc_last_bos == 'bullish': buy_score += 3; buy_weight += 15
    elif smc_structure == 'downtrend' and smc_last_bos == 'bearish': sell_score += 3; sell_weight += 15
    elif smc_structure == 'uptrend': buy_score += 2; buy_weight += 10
    elif smc_structure == 'downtrend': sell_score += 2; sell_weight += 10

    # 5. Elliott Wave Position (weight: 10%)
    if ew_trend == 'impulse':
        if ew_cur <= 3: buy_score += 2; buy_weight += 10
        elif ew_cur == 4: buy_score += 1; buy_weight += 5
    elif ew_trend == 'corrective':
        if ew_cur >= 3: sell_score += 2; sell_weight += 10
        else: sell_score += 1; sell_weight += 5

    # 6. Fear & Greed — Contrarian (weight: 10%)
    if fng < 20: buy_score += 2; buy_weight += 10
    elif fng < 30: buy_score += 1; buy_weight += 5
    elif fng > 80: sell_score += 2; sell_weight += 10
    elif fng > 70: sell_score += 1; sell_weight += 5

    # 7. Order Book Flow (weight: 5%)
    if bid_ask > 1.2: buy_score += 2; buy_weight += 5
    elif bid_ask > 1.05: buy_score += 1; buy_weight += 3
    elif bid_ask < 0.8: sell_score += 2; sell_weight += 5
    elif bid_ask < 0.95: sell_score += 1; sell_weight += 3

    # 8. Whale Activity (weight: 5%)
    if accum == 'accumulating': buy_score += 2; buy_weight += 5
    elif accum == 'distributing': sell_score += 2; sell_weight += 5

    # 9. On-Chain Funding (weight: 5%)
    if funding > 0.05: sell_score += 1; sell_weight += 5
    elif funding < -0.02: buy_score += 1; buy_weight += 5

    # 10. Macro Risk Environment (weight: 5%)
    if risk_on: buy_score += 1; buy_weight += 5
    else: sell_score += 1; sell_weight += 5

    total_buy = buy_score * (buy_weight / 100)
    total_sell = sell_score * (sell_weight / 100)
    max_possible = max(buy_weight, sell_weight) / 100 * 3
    net_score = (total_buy - total_sell) / max_possible * 50 if max_possible > 0 else 0

    return {
        "netScore": net_score,
        "buyScore": buy_score, "sellScore": sell_score,
        "buyWeight": buy_weight, "sellWeight": sell_weight,
    }

def build_verdict(price: float, ctx: dict) -> dict:
    score = calc_weighted_score(ctx)
    ns = score["netScore"]
    fng = ctx["fng"]

    if ns >= 30:
        short, long_v = "buy", "buy"
        confidence = min(92, 65 + ns * 0.6)
        sl = round_price(price * 0.935)
        tp_s = round_price(price * 1.14)
        tp_l = round_price(price * 1.32)
    elif ns >= 10:
        short, long_v = "hold", "buy"
        confidence = min(78, 50 + ns * 0.7)
        sl = round_price(price * 0.925)
        tp_s = round_price(price * 1.10)
        tp_l = round_price(price * 1.28)
    elif ns >= 0:
        short, long_v = "hold", "hold"
        confidence = min(60, 45 + ns * 1.5)
        sl = round_price(price * 0.91)
        tp_s = round_price(price * 1.06)
        tp_l = round_price(price * 1.18)
    elif ns > -20:
        short, long_v = "hold", "hold"
        confidence = min(60, 45 + abs(ns) * 1.5)
        sl = round_price(price * 1.04)
        tp_s = round_price(price * 0.95)
        tp_l = round_price(price * 1.08)
    elif ns >= -50:
        short, long_v = "sell", "hold"
        confidence = min(78, 50 + abs(ns) * 0.5)
        sl = round_price(price * 1.065)
        tp_s = round_price(price * 0.90)
        tp_l = round_price(price * 1.05)
    else:
        short, long_v = "sell", "sell"
        confidence = min(92, 65 + abs(ns) * 0.4)
        sl = round_price(price * 1.08)
        tp_s = round_price(price * 0.86)
        tp_l = round_price(price * 0.78)

    # Contrarian overrides
    if fng < 20 and short == "sell":
        short = "hold"
    if fng > 80 and short == "buy":
        short = "hold"

    return {
        "shortTerm": short, "longTerm": long_v,
        "confidence": confidence, "stopLoss": sl,
        "takeProfitShort": tp_s, "takeProfitLong": tp_l,
        "netScore": ns,
    }

# ─── BACKTEST LOOP ────────────────────────────────────────────────────────────

def run(candles: List[Candle]) -> State:
    state = State(cash=INITIAL_CAPITAL)
    closes = [c.c for c in candles]
    rsi_vals = calc_rsi(closes)

    for i in range(50, len(candles)):
        c = candles[i]
        dt = datetime.fromtimestamp(c.ts / 1000).strftime("%Y-%m-%d")
        prev_c = candles[i-1].c
        change24h = ((c.c - prev_c) / prev_c) * 100

        sim = simulate_data(closes, rsi_vals, i, c.c, change24h)
        verdict = build_verdict(c.c, sim)

        # ── EXIT ──
        if state.pos:
            p = state.pos
            days = i - p["entry_idx"]
            direction = p["direction"]

            if direction == "long" and c.l <= p["sl"]:
                exit_p = p["sl"]
                pnl = (exit_p - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], exit_p, dt, pnl, "stop_loss"))
                state.pos = None
            elif direction == "short" and c.h >= p["sl"]:
                exit_p = p["sl"]
                pnl = (p["entry"] - exit_p) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], exit_p, dt, pnl, "stop_loss"))
                state.pos = None
            elif direction == "long" and c.h >= p["tp"]:
                exit_p = p["tp"]
                pnl = (exit_p - p["entry"]) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "long", p["size"], exit_p, dt, pnl, "take_profit"))
                state.pos = None
            elif direction == "short" and c.l <= p["tp"]:
                exit_p = p["tp"]
                pnl = (p["entry"] - exit_p) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], "short", p["size"], exit_p, dt, pnl, "take_profit"))
                state.pos = None
            elif (direction == "long" and verdict["shortTerm"] == "sell") or \
                 (direction == "short" and verdict["shortTerm"] == "buy"):
                if direction == "long":
                    pnl = (c.c - p["entry"]) / p["entry"] * p["size"]
                else:
                    pnl = (p["entry"] - c.c) / p["entry"] * p["size"]
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], direction, p["size"], c.c, dt, pnl, "signal_reversal"))
                state.pos = None

        # ── ENTRY ──
        if not state.pos and verdict["shortTerm"] in ("buy", "sell"):
            size = state.cash * POSITION_SIZE_PCT
            state.cash -= size
            direction = "long" if verdict["shortTerm"] == "buy" else "short"
            sl = verdict["stopLoss"]
            tp = verdict["takeProfitShort"]
            state.pos = {
                "direction": direction, "entry": c.c, "sl": sl, "tp": tp,
                "size": size, "entry_date": dt, "entry_idx": i,
            }

        # Track equity
        eq = state.cash
        if state.pos:
            p = state.pos
            val = p["size"]
            if p["direction"] == "long": val *= (c.c / p["entry"])
            else: val *= (p["entry"] / c.c)
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
        if v > peak: peak = v
        dd = peak - v
        dd_pct = (dd / peak) * 100 if peak > 0 else 0
        if dd > max_dd: max_dd = dd
        if dd_pct > max_dd_pct: max_dd_pct = dd_pct
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

    # Sharpe
    returns = []
    for i in range(1, len(eq)):
        if eq[i-1] > 0: returns.append((eq[i] - eq[i-1]) / eq[i-1])
    sharpe = 0.0
    if returns:
        avg_r = sum(returns) / len(returns)
        std = math.sqrt(sum((r - avg_r)**2 for r in returns) / len(returns))
        if std > 0: sharpe = (avg_r / std) * math.sqrt(365)

    print("="*60)
    print(f"  STRATEGY BACKTEST — {SYMBOL}")
    print(f"  Period: {START_DATE} to {END_DATE}")
    print("="*60)
    print(f"  Initial Capital:    ${INITIAL_CAPITAL:>8,.2f}")
    print(f"  Final Value:        ${eq[-1]:>8,.2f}")
    print(f"  Total Return:       {ret:>8.2f}%")
    print(f"  Max Drawdown:       ${max_dd:>8,.2f}  ({max_dd_pct:.1f}%)")
    print(f"  Sharpe Ratio:       {sharpe:>8.3f}")
    print(f"  Total Trades:       {total_trades:>8}")
    print(f"  Win Rate:           {win_rate:>7.1f}%")
    print(f"  Avg Win:            ${avg_win:>8,.2f}  ({len(wins)} trades)")
    print(f"  Avg Loss:           ${avg_loss:>8,.2f}  ({len(losses)} trades)")
    print(f"  Profit Factor:      {profit_factor:>8.3f}" if isinstance(profit_factor, float) else f"  Profit Factor:      {profit_factor:>8}")
    print("="*60)
    print("  Recent Trades:")
    for t in state.trades[-5:]:
        print(f"  {t.entry_date} | {t.direction.upper():>4} | "
              f"Entry: ${t.entry_price:>8,.2f} | Exit: ${t.exit_price:>8,.2f} | "
              f"P&L: ${t.pnl:>+8,.2f} | {t.exit_reason}")
    print("="*60)

    # Store results
    out = {
        "dates": state.dates, "equity": eq,
        "trades": [{"entry_date": t.entry_date, "entry_price": t.entry_price,
                    "direction": t.direction, "size_usd": t.size_usd,
                    "exit_price": t.exit_price, "exit_date": t.exit_date,
                    "pnl": t.pnl, "exit_reason": t.exit_reason} for t in state.trades],
    }
    with open("strategy_backtest_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print("  Results saved to strategy_backtest_result.json\n")

def main():
    print("Fetching data...", end=" ", flush=True)
    candles = fetch_data(SYMBOL, START_DATE, END_DATE)
    print(f"{len(candles)} candles loaded")
    if len(candles) < 200:
        print("Not enough data"); return
    print("Running backtest...")
    state = run(candles)
    report(state)

if __name__ == "__main__":
    main()
