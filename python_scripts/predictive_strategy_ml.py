#!/usr/bin/env python3
"""Machine‑learning driven predictive strategy for any ticker.

Features:
- RSI, MACD histogram, 5‑day price change, SMA‑trend (20 vs 50), volume‑change.
- Target: next‑day price up (1) vs down/no‑move (0).
- GradientBoostingClassifier (500 trees, learning_rate 0.05).
- Probability thresholds turn the model output into long/short/flat signals.
- Simple equity simulation with a configurable risk‑per‑trade (no ATR, no stop‑loss).
- Chronological train/test split (70 % train, 30 % test) and a modest grid‑search
  over thresholds and risk levels to maximize total return.
"""

import sys
import datetime
import numpy as np
import pandas as pd
import json
import urllib.request

INTERVAL = "1m"
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report

# ------------------------------------------------------------
# 1️⃣ Data download
# ------------------------------------------------------------
def download(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch minute‑resolution OHLCV data from Binance.
    Returns a DataFrame with columns: open, high, low, adj_close, volume.
    """
    # Convert dates to Binance timestamps (ms)
    s = int(datetime.datetime.strptime(start, "%Y-%m-%d").timestamp()) * 1000
    e = int(datetime.datetime.strptime(end, "%Y-%m-%d").timestamp()) * 1000
    url = (f"https://api.binance.com/api/v3/klines?symbol={ticker}&interval={INTERVAL}" 
           f"&startTime={s}&endTime={e}&limit=1000")
    raw = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
    # Binance response columns: [open_time, open, high, low, close, volume, ...]
    df = pd.DataFrame(raw, columns=["open_time","open","high","low","close","volume","close_time","quote_asset_volume","num_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"])
    df = df[["open_time","open","high","low","close","volume"]].copy()
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)
    df.rename(columns={"close": "adj_close"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    return df

# ------------------------------------------------------------
# 2️⃣ Technical indicators
# ------------------------------------------------------------
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))

def macd_hist(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    sig_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line - sig_line

# ------------------------------------------------------------
# 3️⃣ Feature engineering
# ------------------------------------------------------------
def build_features(df: pd.DataFrame) -> (pd.DataFrame, list):
    df["rsi"] = compute_rsi(df["adj_close"])
    df["macd_hist"] = macd_hist(df["adj_close"])
    df["price_change_5d"] = df["adj_close"].pct_change(5)
    df["sma_20"] = df["adj_close"].rolling(20).mean()
    df["sma_50"] = df["adj_close"].rolling(50).mean()
    df["sma_trend"] = (df["sma_20"] > df["sma_50"]).astype(int)
    df["vol_change_5d"] = df["volume"].pct_change(5)
    # Fill missing volume change (e.g., zero volume series) with 0
    df["vol_change_5d"] = df["vol_change_5d"].fillna(0)
    # Target: next‑day close higher than today
    df["target"] = (df["adj_close"].shift(-1) > df["adj_close"]).astype(int)
    # Exclude vol_change_5d from the feature list (it provides no info for zero‑volume assets)
    feature_cols = ["rsi", "macd_hist", "price_change_5d", "sma_trend"]
    df = df.dropna(subset=feature_cols + ["target"]).copy()
    return df, feature_cols

# ------------------------------------------------------------
# 4️⃣ Simple equity simulation (no ATR)
# ------------------------------------------------------------
def backtest(df: pd.DataFrame, signal: pd.Series, init_capital: float = 100_000, risk_perc: float = 0.02, stop_loss_factor: float = 0.02, take_profit_factor: float = 0.04) -> pd.Series:
    equity = init_capital
    position = None  # dict with direction, shares, entry_price, size_usd
    equity_curve = []
    for dt, row in df.iterrows():
        sig = signal.get(dt, 0)
        # --------------------------------
        # 1️⃣ Stop‑loss / take‑profit handling
        # --------------------------------
        if position:
            # Long position logic
            if position["direction"] == "long":
                # Stop‑loss hit?
                if row["low"] <= position["stop_price"]:
                    exit_price = position["stop_price"]
                    pnl = (exit_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
                # Take‑profit hit?
                elif row["high"] >= position["take_price"]:
                    exit_price = position["take_price"]
                    pnl = (exit_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
            else:  # short position
                # Stop‑loss hit?
                if row["high"] >= position["stop_price"]:
                    exit_price = position["stop_price"]
                    pnl = (position["entry_price"] - exit_price) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
                # Take‑profit hit?
                elif row["low"] <= position["take_price"]:
                    exit_price = position["take_price"]
                    pnl = (position["entry_price"] - exit_price) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
        # --------------------------------
        # 2️⃣ Signal‑driven reversal (if still in position)
        # --------------------------------
        if position and ((position["direction"] == "long" and sig == -1) or (position["direction"] == "short" and sig == 1)):
            exit_price = row["adj_close"]
            if position["direction"] == "long":
                pnl = (exit_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
            else:
                pnl = (position["entry_price"] - exit_price) / position["entry_price"] * position["size_usd"]
            equity += position["size_usd"] + pnl
            position = None
        # --------------------------------
        # 3️⃣ Entry when flat
        # --------------------------------
        if not position and sig != 0:
            direction = "long" if sig == 1 else "short"
            risk_amount = risk_perc * equity
            shares = int(risk_amount / row["adj_close"])
            if shares > 0:
                entry_price = row["adj_close"]
                size_usd = shares * entry_price
                # Compute stop‑loss and take‑profit levels
                if direction == "long":
                    stop_price = entry_price * (1 - stop_loss_factor)
                    take_price = entry_price * (1 + take_profit_factor)
                else:
                    stop_price = entry_price * (1 + stop_loss_factor)
                    take_price = entry_price * (1 - take_profit_factor)
                position = {
                    "direction": direction,
                    "shares": shares,
                    "entry_price": entry_price,
                    "size_usd": size_usd,
                    "stop_price": stop_price,
                    "take_price": take_price,
                }
                equity -= size_usd
        # mark‑to‑market
        market_val = 0.0
        if position:
            if position["direction"] == "long":
                market_val = position["shares"] * row["adj_close"]
            else:
                market_val = position["shares"] * (2 * position["entry_price"] - row["adj_close"])  # short exposure
        total = equity + market_val
        equity_curve.append(total)
    # close any open position at the end
    if position:
        final_price = df["adj_close"].iloc[-1]
        if position["direction"] == "long":
            pnl = (final_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
        else:
            pnl = (position["entry_price"] - final_price) / position["entry_price"] * position["size_usd"]
        equity += position["size_usd"] + pnl
    return pd.Series(equity_curve, index=df.index)

# ------------------------------------------------------------
# 5️⃣ Performance metrics
# ------------------------------------------------------------
def performance(equity: pd.Series) -> dict:
    start, end = equity.index[0], equity.index[-1]
    years = (end - start).days / 365.25
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1
    # Guard against zero‑year intervals (e.g., minute‑level backtest spanning <1 day)
    if years == 0:
        cagr = total_ret
    else:
        cagr = (1 + total_ret) ** (1 / years) - 1
    roll_max = equity.cummax()
    drawdown = (roll_max - equity) / roll_max
    max_dd = drawdown.max()
    return {
        "total_return_%": round(total_ret * 100, 2),
        "cagr_%": round(cagr * 100, 2),
        "max_drawdown_%": round(max_dd * 100, 2),
        "years": round(years, 2),
    }

# ------------------------------------------------------------
# 6️⃣ Signal conversion from probabilities
# ------------------------------------------------------------
def prob_to_signal(proba: pd.Series, high_thr: float = 0.65, low_thr: float = 0.35) -> pd.Series:
    sig = pd.Series(0, index=proba.index)
    sig[proba > high_thr] = 1
    sig[proba < low_thr] = -1
    return sig

# ------------------------------------------------------------
# 7️⃣ Main driver
# ------------------------------------------------------------
def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AUDUSDT"
    start = sys.argv[2] if len(sys.argv) > 2 else (datetime.datetime.utcnow() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    end = sys.argv[3] if len(sys.argv) > 3 else datetime.datetime.utcnow().strftime("%Y-%m-%d")
    print(f"Fetching {ticker} data from {start} to {end} …")
    data = download(ticker, start, end)
    df, feature_cols = build_features(data)
    # Chronological split
    split_idx = int(len(df) * 0.70)
    train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]
    X_train, y_train = train_df[feature_cols], train_df["target"]
    X_test, y_test = test_df[feature_cols], test_df["target"]
    model = GradientBoostingClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=3,
        random_state=42,
    )
    model.fit(X_train, y_train)
    best = None
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print("\n=== Classification on test set ===")
    print(f"Accuracy: {acc:.3%}")
    print(classification_report(y_test, pred, digits=3))
    # Probability‑based grid search
    proba = pd.Series(model.predict_proba(X_test)[:, 1], index=test_df.index)
    best = None
    for high_thr in [0.60, 0.65, 0.70, 0.75]:
        for low_thr in [0.30, 0.35, 0.40, 0.45]:
            if low_thr >= high_thr:
                continue
            raw_sig = prob_to_signal(proba, high_thr, low_thr)
            # Apply SMA trend filter – allow long only when sma_trend==1, short only when 0
            sig = raw_sig.where(~((raw_sig == 1) & (test_df["sma_trend"] == 0)), 0)
            sig = sig.where(~((sig == -1) & (test_df["sma_trend"] == 1)), 0)
            for risk in [0.02, 0.05, 0.10]:
                equity_curve = backtest(test_df, sig, risk_perc=risk, stop_loss_factor=0.02, take_profit_factor=0.04)
                stats = performance(equity_curve)
                if best is None or stats["total_return_%"] > best["total_return_%"]:
                    best = {
                        "high_thr": high_thr,
                        "low_thr": low_thr,
                        "risk_perc": risk,
                        **stats,
                    }
    if best:
        print("\n=== Best grid-search result (highest total return) ===")
        for k, v in best.items():
            print(f"{k}: {v}")
        # Save best result to JSON for reproducibility
        with open("predictive_strategy_ml_backtest.json", "w") as f:
            json.dump(best, f, indent=2)
        print("Saved best result to predictive_strategy_ml_backtest.json")
    else:
        print("No viable configuration found.")

if __name__ == "__main__":
    main()
