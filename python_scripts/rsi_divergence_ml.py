# rsi_divergence_ml.py
"""
RSI‑divergence + Machine‑Learning predictor with a simple back‑test.

Features
- Download daily OHLCV data (default: BTC‑USD)
- Compute RSI, SMA trend, and two divergence flags (bullish / bearish)
- Build a feature matrix and a binary target (next‑day up = 1)
- Train a RandomForest on a chronological train / test split
- Evaluate classification performance
- Run a **very simple back‑test** that goes long when the model predicts an up‑move
  and exits when it predicts a down‑move. Position size = risk_perc of current equity.

The script is intentionally lightweight for quick experimentation.
"""

import sys
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

# ------------------------------------------------------------
# 1️⃣ Data download
# ------------------------------------------------------------
def download(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch daily OHLCV data from Yahoo Finance."""
    df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.rename(columns={"Close": "adj_close"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index)
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

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (ATR) – same as in the dual‑MA script."""
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def detect_rsi_divergence(df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    price = df["adj_close"]
    rsi = df["rsi"]
    bull = np.zeros(len(df), dtype=int)
    bear = np.zeros(len(df), dtype=int)
    for i in range(lookback, len(df)):
        # Use positional index via .iloc to avoid label look‑up
        price_i = price.iloc[i]
        price_prev = price.iloc[i-1]
        rsi_i = rsi.iloc[i]
        rsi_prev = rsi.iloc[i-1]
        # bullish divergence: price lower low, RSI higher low
        if price_i < price_prev and rsi_i > rsi_prev:
            bull[i] = 1
        # bearish divergence: price higher high, RSI lower high
        if price_i > price_prev and rsi_i < rsi_prev:
            bear[i] = 1
    df["rsi_bull_div"] = bull
    df["rsi_bear_div"] = bear
    return df

# ------------------------------------------------------------
# 3️⃣ Feature engineering
# ------------------------------------------------------------
def build_features(df: pd.DataFrame) -> (pd.DataFrame, List[str]):
    df["rsi"] = compute_rsi(df["adj_close"])
    df["sma_20"] = df["adj_close"].rolling(20).mean()
    df["sma_50"] = df["adj_close"].rolling(50).mean()
    df["price_change_5d"] = df["adj_close"].pct_change(5)
    df["atr"] = atr(df["high"], df["low"], df["adj_close"], period=14)
    df = detect_rsi_divergence(df, lookback=5)
    df["sma_trend"] = (df["sma_20"] > df["sma_50"]).astype(int)
    # binary target: next‑day close higher than today
    df["target"] = (df["adj_close"].shift(-1) > df["adj_close"]).astype(int)
    feature_cols = ["sma_trend", "rsi", "price_change_5d", "rsi_bull_div", "rsi_bear_div"]
    df = df.dropna(subset=feature_cols + ["target"]).copy()
    return df, feature_cols

# ------------------------------------------------------------
# 4️⃣ Simple back‑test using model predictions as signals
# ------------------------------------------------------------
def backtest_with_signals(df: pd.DataFrame, signal: pd.Series, init_capital: float = 100_000, risk_perc: float = 0.02) -> pd.Series:
    """Simplified back‑test (no ATR).
    * ``signal`` values: 1 = long, -1 = short, 0 = flat.
    * Position size = risk_perc of current cash equity (dollar amount).
    * Entries and exits are executed at the day’s close price.
    * No trailing stop or ATR‑based sizing is used.
    """
    equity = init_capital
    position = None  # None or dict with direction, shares, entry_price, size_usd
    equity_curve = []

    for dt, row in df.iterrows():
        # ---- Signal‑driven exit / reversal ----
        sig = signal.get(dt, 0)
        if position and ((position["direction"] == "long" and sig == -1) or (position["direction"] == "short" and sig == 1)):
            exit_price = row["adj_close"]
            if position["direction"] == "long":
                pnl = (exit_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
            else:
                pnl = (position["entry_price"] - exit_price) / position["entry_price"] * position["size_usd"]
            equity += position["size_usd"] + pnl
            position = None

        # ---- Entry logic (only when flat) ----
        if not position and sig != 0:
            direction = "long" if sig == 1 else "short"
            risk_amount = risk_perc * equity
            # Allocate the entire risk amount (no ATR scaling)
            shares = int(risk_amount / row["adj_close"])
            if shares > 0:
                entry_price = row["adj_close"]
                size_usd = shares * entry_price
                position = {
                    "direction": direction,
                    "shares": shares,
                    "entry_price": entry_price,
                    "size_usd": size_usd,
                }
                equity -= size_usd

        # ---- Mark‑to‑market equity value ----
        market_val = 0.0
        if position:
            if position["direction"] == "long":
                market_val = position["shares"] * row["adj_close"]
            else:
                # short exposure: profit = (entry - current) * shares
                market_val = position["shares"] * (2 * position["entry_price"] - row["adj_close"])
        total = equity + market_val
        equity_curve.append(total)

    # ---- Close any open position on the final day ----
    if position:
        final_price = df["adj_close"].iloc[-1]
        if position["direction"] == "long":
            pnl = (final_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
        else:
            pnl = (position["entry_price"] - final_price) / position["entry_price"] * position["size_usd"]
        equity += position["size_usd"] + pnl
    return pd.Series(equity_curve, index=df.index)

# ------------------------------------------------------------
# 5️⃣ Performance metrics (same as in the dual‑MA script)
# ------------------------------------------------------------
def performance(equity: pd.Series) -> dict:
    # unchanged – kept for reference
    start = equity.index[0]
    end = equity.index[-1]
    years = (end - start).days / 365.25
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1
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

def generate_signal_series(proba: pd.Series, high_thresh: float = 0.65, low_thresh: float = 0.35) -> pd.Series:
    """Convert probability predictions into -1/0/1 signals.
    - ``proba`` is the probability of class 1 (price up).
    - If ``proba`` > ``high_thresh`` → long signal (1).
    - If ``proba`` < ``low_thresh`` → short signal (-1).
    - Otherwise → flat (0).
    """
    sig = pd.Series(0, index=proba.index)
    sig[proba > high_thresh] = 1
    sig[proba < low_thresh] = -1
    return sig
    start = equity.index[0]
    end = equity.index[-1]
    years = (end - start).days / 365.25
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1
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
# 6️⃣ Main execution flow
# ------------------------------------------------------------
def main() -> None:
    ticker = "BTC-USD"
    start = "2015-01-01"
    end = datetime.today().strftime("%Y-%m-%d")
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    if len(sys.argv) > 2:
        start = sys.argv[2]
    if len(sys.argv) > 3:
        end = sys.argv[3]
    print(f"Fetching {ticker} data from {start} to {end} …")
    data = download(ticker, start, end)
    df, feature_cols = build_features(data)
    # chronological train / test split (70% train, 30% test)
    split_idx = int(len(df) * 0.70)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    X_train = train_df[feature_cols]
    y_train = train_df["target"]
    X_test = test_df[feature_cols]
    y_test = test_df["target"]
    model = GradientBoostingClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=3,
        random_state=42,
    )
    model.fit(X_train, y_train)
    # predictions for test set (probability > 0.5 => 1, else 0)
    # Classification metrics (binary prediction) – keep for reference
    test_pred = model.predict(X_test)
    acc = accuracy_score(y_test, test_pred)
    print("\n=== Classification on test set ===")
    print(f"Accuracy: {acc:.3%}")
    print(classification_report(y_test, test_pred, digits=3))

    # ---- Grid search for best back‑test parameters ----
    # Use probability predictions for flexible long/short thresholds
    proba = model.predict_proba(X_test)[:, 1]
    best = None
    # modest grid – keep runtime reasonable
    for high_thr in [0.60, 0.65, 0.70, 0.75]:
        for low_thr in [0.30, 0.35, 0.40, 0.45]:
            if low_thr >= high_thr:
                continue
            # Generate raw probability‑based signal (1 = long, -1 = short, 0 = flat)
            raw_sig_series = generate_signal_series(pd.Series(proba, index=test_df.index), high_thr, low_thr)
            # Shift to avoid look‑ahead, fill NaNs with flat
            sig_series = raw_sig_series.shift(1).fillna(0).astype(int)
            # Apply SMA trend filter: only allow long when sma_trend == 1,
            # only allow short when sma_trend == 0
            sma_trend = test_df["sma_trend"]
            sig_series = sig_series.where(~((sig_series == 1) & (sma_trend == 0)), 0)
            sig_series = sig_series.where(~((sig_series == -1) & (sma_trend == 1)), 0)
            # Evaluate each risk level (no ATR/stop‑multiplier used)
            for risk in [0.02, 0.05, 0.10]:
                equity_curve = backtest_with_signals(test_df, sig_series, init_capital=100_000, risk_perc=risk)
                stats = performance(equity_curve)
                # Use total return as primary metric for "highest return"
                if best is None or stats['total_return_%'] > best['total_return_%']:
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
    else:
        print("No viable configuration found.")

if __name__ == "__main__":
    main()
