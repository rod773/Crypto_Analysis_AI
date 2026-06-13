#!/usr/bin/env python3
"""
Backtest for the updated analysis.ts strategy (predictive signals).
Faithfully reproduces the generatePredictiveSignal + buildVerdict logic.
"""

import json, math, urllib.request, sys
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

# ─── FETCHER ─────────────────────────────────────────────────────────────────

def fetch_binance(symbol: str, start: str, end: str) -> List[Candle]:
    s = int(datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&startTime={s}&endTime={e}&limit=1000"
    data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
    return [Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])) for k in data]

def fetch_fng(limit: int = 365) -> dict:
    """Fetch Fear & Greed Index history. Returns dict mapping date_str -> value."""
    try:
        url = f"https://api.alternative.me/fng/?limit={limit}"
        data = json.loads(urllib.request.urlopen(url, timeout=15).read().decode())
        result = {}
        for item in data.get("data", []):
            ts = int(item["timestamp"])
            dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            result[dt] = int(item["value"])
        return result
    except Exception:
        return {}

# ─── INDICATORS (mirrors analysis.ts) ───────────────────────────────────────

def calc_ema(values: List[float], period: int) -> List[float]:
    if len(values) < period:
        avg = sum(values) / len(values) if values else 0
        return [avg] * len(values)
    k = 2.0 / (period + 1)
    result = [sum(values[:period]) / period]
    for v in values[period:]:
        result.append(v * k + result[-1] * (1 - k))
    pad = result[0]
    while len(result) < len(values):
        result.insert(0, pad)
    return result

def calc_sma(values: List[float], period: int) -> List[float]:
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(sum(values[:i+1]) / (i + 1))
        else:
            result.append(sum(values[i-period+1:i+1]) / period)
    return result

def calc_rsi(closes: List[float], period: int = 14) -> List[float]:
    if len(closes) < period + 1:
        return [50.0] * len(closes)
    rsis = [50.0] * period
    for i in range(period, len(closes)):
        gains = losses = 0.0
        for j in range(i - period + 1, i + 1):
            d = closes[j] - closes[j - 1]
            if d > 0: gains += d
            else: losses -= d
        avg_g = gains / period
        avg_l = losses / period
        rsis.append(100.0 if avg_l == 0 else 100.0 - 100.0 / (1 + avg_g / avg_l))
    return rsis

def calc_macd(closes: List[float]):
    fast = calc_ema(closes, 12)
    slow = calc_ema(closes, 26)
    macd = [f - s for f, s in zip(fast, slow)]
    signal = calc_ema(macd, 9)
    hist = [m - s for m, s in zip(macd, signal)]
    return macd, signal, hist

# ─── PRICE HISTORY (mirrors analysis.ts) ─────────────────────────────────────

class PriceHistory:
    def __init__(self, maxlen: int = 120):
        self._data: List[dict] = []
        self._maxlen = maxlen

    def update(self, close: float, volume: float, high: float, low: float, change24h: float):
        self._data.append({"close": close, "volume": volume, "high": high, "low": low, "change24h": change24h})
        if len(self._data) > self._maxlen:
            self._data = self._data[-self._maxlen:]

    @property
    def closes(self) -> List[float]: return [d["close"] for d in self._data]

    @property
    def volumes(self) -> List[float]: return [d["volume"] for d in self._data]

    @property
    def lows(self) -> List[float]: return [d["low"] for d in self._data]

    @property
    def length(self) -> int: return len(self._data)

    def low_at(self, idx: int) -> float:
        if 0 <= idx < len(self._data): return self._data[idx]["low"]
        return 0.0

# ─── SIGNAL ENGINE (mirrors generatePredictiveSignal) ────────────────────────

def round_price(v: float) -> float:
    return round(v, 4) if abs(v) < 10 else round(v)

def generate_signal(ph: PriceHistory) -> dict:
    if ph.length < 30:
        return {"direction": "hold", "reason": "insufficient_data", "score": 0, "confidence": 50}

    closes = ph.closes
    volumes = ph.volumes
    idx = ph.length - 1
    cur = idx

    rsi_vals = calc_rsi(closes)
    macd_line, sig_line, hist = calc_macd(closes)
    ma50 = calc_sma(closes, 50)

    # RSI Divergence over last ~10 candles (3 sample points)
    bullish_div = False
    bearish_div = False
    if idx > 20:
        step = 3
        samples = list(range(idx - 10, idx + 1, step))
        if len(samples) >= 2:
            p_low1 = ph.low_at(samples[-2])
            p_low2 = ph.low_at(samples[-1])
            r_low1 = rsi_vals[samples[-2]] if samples[-2] < len(rsi_vals) else 50
            r_low2 = rsi_vals[samples[-1]] if samples[-1] < len(rsi_vals) else 50
            if p_low1 > p_low2 and r_low1 < r_low2:
                bullish_div = True
            if p_low1 < p_low2 and r_low1 > r_low2:
                bearish_div = True

    # MACD signal prediction
    hist_growing = hist[cur] > (hist[cur - 2] if cur >= 2 else hist[cur])
    hist_declining = hist[cur] < (hist[cur - 2] if cur >= 2 else hist[cur])
    macd_buy = hist_growing and macd_line[cur] < sig_line[cur]
    macd_sell = hist_declining and macd_line[cur] > sig_line[cur]

    # Volume spike
    avg_vol = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else (sum(volumes) / len(volumes) if volumes else 1)
    vol_spike = volumes[cur] > avg_vol * 1.5

    # Scoring
    buy_score = 0
    sell_score = 0

    if bullish_div: buy_score += 3
    if macd_buy: buy_score += 2
    if ma50[cur] and closes[cur] > ma50[cur]: buy_score += 1
    if rsi_vals[cur] < 35: buy_score += 1
    if vol_spike: buy_score += 1

    if bearish_div: sell_score += 3
    if macd_sell: sell_score += 2
    if ma50[cur] and closes[cur] < ma50[cur]: sell_score += 1
    if rsi_vals[cur] > 65: sell_score += 1
    if vol_spike: sell_score += 1

    direction = "hold"
    reason = ""
    confidence = 50

    if buy_score > sell_score and buy_score >= 3:
        direction = "buy"
        reason = "divergence" if bullish_div else "momentum"
        confidence = min(92, 55 + buy_score * 8)
    elif sell_score > buy_score and sell_score >= 3:
        direction = "sell"
        reason = "divergence" if bearish_div else "momentum"
        confidence = min(92, 55 + sell_score * 8)

    return {"direction": direction, "reason": reason, "score": max(buy_score, sell_score), "confidence": confidence}

# ─── BUILD VERDICT (mirrors buildVerdict in analysis.ts) ─────────────────────

def build_verdict(price: float, change24h: float, high: float, low: float, volume: float,
                  ph: PriceHistory, fng: int) -> dict:
    ph.update(price, volume, high, low, change24h)
    sig = generate_signal(ph)

    short, long_v, conf, sl, tp_s, tp_l = "hold", "hold", 50, round_price(price * 0.93), round_price(price * 1.06), round_price(price * 1.15)

    if sig["direction"] == "buy":
        short = "buy"
        long_v = "buy"
        conf = sig["confidence"]
        sl = round_price(price * 0.94)
        tp_s = round_price(price * 1.12)
        tp_l = round_price(price * 1.28)
    elif sig["direction"] == "sell":
        short = "sell"
        long_v = "hold"
        conf = sig["confidence"]
        sl = round_price(price * 1.06)
        tp_s = round_price(price * 0.90)
        tp_l = round_price(price * 1.05)

    # Contrarian overrides (mirrors analysis.ts)
    if fng < 20 and short == "sell":
        short = "hold"
    if fng > 80 and short == "buy":
        short = "hold"

    return {"shortTerm": short, "longTerm": long_v, "confidence": conf,
            "stopLoss": sl, "takeProfitShort": tp_s, "takeProfitLong": tp_l,
            "score": sig["score"], "reason": sig["reason"]}

# ─── BACKTEST LOOP ────────────────────────────────────────────────────────────

def run(candles: List[Candle], fng_data: dict) -> State:
    state = State(cash=INITIAL_CAPITAL)
    ph = PriceHistory(maxlen=120)

    for i in range(len(candles)):
        c = candles[i]
        dt = datetime.fromtimestamp(c.ts / 1000).strftime("%Y-%m-%d")
        change24h = ((c.c - candles[i-1].c) / candles[i-1].c) * 100 if i > 0 else 0

        # First call: seed with 30 candles (matches analysis.ts seedPriceHistory)
        if i == 30:
            for j in range(0, 30):
                prev = candles[j-1].c if j > 0 else candles[j].c
                chg = ((candles[j].c - prev) / prev) * 100
                ph.update(candles[j].c, candles[j].v, candles[j].h, candles[j].l, chg)

        # Skip signal generation before history is seeded
        if i < 30:
            state.dates.append(dt)
            state.equity_curve.append(state.cash + (state.pos["size"] if state.pos else 0))
            continue

        # Build verdict with real HL (matches analysis.ts)
        verdict = build_verdict(c.c, change24h, c.h, c.l,
                                c.v, ph, fng_data.get(dt, 50))

        # ── EXIT ──
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
            elif (p["direction"] == "long" and verdict["shortTerm"] == "sell") or \
                 (p["direction"] == "short" and verdict["shortTerm"] == "buy"):
                pnl = ((c.c - p["entry"]) / p["entry"] * p["size"]) if p["direction"] == "long" else \
                      ((p["entry"] - c.c) / p["entry"] * p["size"])
                state.cash += p["size"] + pnl - (p["size"] * FEE_PCT)
                state.trades.append(Trade(p["entry_date"], p["entry"], p["direction"], p["size"], c.c, dt, pnl, "signal_reversal"))
                state.pos = None

        # ── ENTRY ──
        if not state.pos and verdict["shortTerm"] in ("buy", "sell"):
            size = state.cash * POSITION_SIZE_PCT
            state.cash -= size
            direction = "long" if verdict["shortTerm"] == "buy" else "short"
            state.pos = {
                "direction": direction, "entry": c.c,
                "sl": verdict["stopLoss"], "tp": verdict["takeProfitShort"],
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
    total = len(state.trades)
    win_rate = len(wins) / total * 100 if total else 0

    avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0
    total_wins = sum(t.pnl for t in wins)
    total_losses = abs(sum(t.pnl for t in losses))
    profit_factor = total_wins / total_losses if total_losses > 0 else inf

    max_dd, max_dd_pct = compute_drawdown(eq)

    returns = []
    for i in range(1, len(eq)):
        if eq[i-1] > 0:
            returns.append((eq[i] - eq[i-1]) / eq[i-1])
    sharpe = 0.0
    if returns:
        avg_r = sum(returns) / len(returns)
        std = math.sqrt(sum((r - avg_r)**2 for r in returns) / len(returns))
        if std > 0: sharpe = (avg_r / std) * math.sqrt(365)

    print("="*60)
    print(f"  ANALYSIS.TS BACKTEST — {SYMBOL}")
    print(f"  Period: {START_DATE} to {END_DATE}")
    print("="*60)
    print(f"  Initial Capital:    ${INITIAL_CAPITAL:>8,.2f}")
    print(f"  Final Value:        ${eq[-1]:>8,.2f}")
    print(f"  Total Return:       {ret:>+8.2f}%")
    print(f"  Max Drawdown:       ${max_dd:>8,.2f}  ({max_dd_pct:.1f}%)")
    print(f"  Sharpe Ratio:       {sharpe:>8.3f}")
    print(f"  Total Trades:       {total:>8}")
    print(f"  Win Rate:           {win_rate:>7.1f}%")
    print(f"  Avg Win:            ${avg_win:>8,.2f}  ({len(wins)} trades)")
    print(f"  Avg Loss:           ${avg_loss:>8,.2f}  ({len(losses)} trades)")
    print(f"  Profit Factor:      {profit_factor:>8.3f}")
    print("="*60)
    print("  Recent Trades:")
    for t in state.trades[-5:]:
        print(f"  {t.entry_date} | {t.direction.upper():>4} | "
              f"Entry: ${t.entry_price:>8,.2f} | Exit: ${t.exit_price:>8,.2f} | "
              f"P&L: ${t.pnl:>+8,.2f} | {t.exit_reason}")
    print("="*60)

    out = {
        "dates": state.dates, "equity": eq,
        "trades": [{"entry_date": t.entry_date, "entry_price": t.entry_price,
                    "direction": t.direction, "size_usd": t.size_usd,
                    "exit_price": t.exit_price, "exit_date": t.exit_date,
                    "pnl": t.pnl, "exit_reason": t.exit_reason} for t in state.trades],
    }
    with open("analysis_backtest_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print("  Results saved to analysis_backtest_result.json\n")

def main():
    print("Fetching Binance data...", end=" ", flush=True)
    candles = fetch_binance(SYMBOL, START_DATE, END_DATE)
    print(f"{len(candles)} candles")

    print("Fetching Fear & Greed Index...", end=" ", flush=True)
    fng_data = fetch_fng()
    print(f"{len(fng_data)} days")

    if len(candles) < 50:
        print("Not enough data!"); return

    print("Running analysis.ts backtest...")
    state = run(candles, fng_data)
    report(state)

if __name__ == "__main__":
    main()
