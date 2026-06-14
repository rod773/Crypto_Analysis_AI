#!/usr/bin/env python3
"""Duplicate of the HFT predictive strategy (named dudaskopy).

Features, model, back‑test logic, and CLI are identical to
`predictive_strategy_hft.py`. This file is provided per the user request.
"""

import sys
import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import os

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report

# ------------------------------------------------------------
# Load .env variables (if the .env file exists)
# ------------------------------------------------------------
from pathlib import Path
_env_path = Path(__file__).resolve().parent.parent / "src" / ".env"
if _env_path.is_file():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#"):
                key, _, val = _line.partition("=")
                os.environ.setdefault(key, val)

# ------------------------------------------------------------
# Helper: fallback to Tickstory CSV export
# ------------------------------------------------------------
def _fallback_tickstory(ticker: str, start: str, end: str, interval: str) -> pd.DataFrame:
    export_dir = os.getenv("TICKSTORY_EXPORT_DIR")
    if not export_dir:
        return pd.DataFrame()
    file_name = f"{ticker}_{start.replace('-', '')}_{end.replace('-', '')}.csv"
    csv_path = os.path.join(export_dir, file_name)
    if not os.path.isfile(csv_path):
        print(f"Tickstory CSV not found at {csv_path}")
        return pd.DataFrame()
    try:
        return load_tickstory_csv(csv_path, interval=interval)
    except Exception as e:
        print(f"Error loading Tickstory CSV: {e}")
        return pd.DataFrame()

def load_tickstory_csv(csv_path: str, interval: str = "1m") -> pd.DataFrame:
    """Load a Tickstory‑exported CSV of raw trades and resample to OHLCV."""
    df_raw = pd.read_csv(csv_path, sep="[,;]", engine="python")
    ts_col = next((c for c in df_raw.columns if "time" in c.lower()), None)
    if ts_col is None:
        raise KeyError("No timestamp column found in Tickstory CSV")
    df_raw = df_raw.rename(columns={ts_col: "timestamp"})
    df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"], unit="ns", errors="coerce")
    df_raw = df_raw.dropna(subset=["timestamp"])
    price_col = next((c for c in df_raw.columns if "price" in c.lower()), None)
    size_col = next((c for c in df_raw.columns if "size" in c.lower()), None)
    if price_col is None or size_col is None:
        raise KeyError("Price or size column missing in Tickstory CSV")
    df_raw = df_raw.set_index("timestamp")[[price_col, size_col]].rename(columns={price_col: "adj_close", size_col: "volume"})
    pd_interval = interval.replace("m", "T").replace("h", "H")
    ohlc = df_raw["adj_close"].resample(pd_interval).ohlc()
    vol = df_raw["volume"].resample(pd_interval).sum()
    df = pd.concat([ohlc, vol.rename("volume")], axis=1).dropna()
    df.rename(columns={"close": "adj_close"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    return df

# ------------------------------------------------------------
# 1️⃣ Data download (intraday)
# ------------------------------------------------------------
def download(ticker: str, start: str, end: str, interval: str = "1m") -> pd.DataFrame:
    """Fetch tick data via TradingView API, fallback to Tickstory CSV export."""
    # Attempt TradingView historical data fetch
    try:
        from tradingview_fetch import download_tradingview
        df = download_tradingview(ticker, start, end, interval)
        if not df.empty:
            return df
    except Exception as e:
        print(f"TradingView fetch error: {e}")
    # Fallback to Tickstory CSV export if TradingView fails or returns empty
    df = _fallback_tickstory(ticker, start, end, interval)
    if df.empty:
        print("No Tickstory CSV data loaded.")
    return df

# ------------------------------------------------------------
# 2️⃣ Technical indicators (same as daily version)
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
# 3️⃣ Feature engineering (minute‑level)
# ------------------------------------------------------------
def build_features(df: pd.DataFrame) -> (pd.DataFrame, list):
    df["rsi"] = compute_rsi(df["adj_close"])
    df["macd_hist"] = macd_hist(df["adj_close"])
    df["price_change_5"] = df["adj_close"].pct_change(5)  # 5‑minute change
    df["sma_20"] = df["adj_close"].rolling(20).mean()
    df["sma_50"] = df["adj_close"].rolling(50).mean()
    df["sma_trend"] = (df["sma_20"] > df["sma_50"]).astype(int)
    df["vol_change_5"] = df["volume"].pct_change(5)
    df["vol_change_5"] = df["vol_change_5"].fillna(0)
    df["target"] = (df["adj_close"].shift(-1) > df["adj_close"]).astype(int)
    feature_cols = ["rsi", "macd_hist", "price_change_5", "sma_trend", "vol_change_5"]
    df = df.dropna(subset=feature_cols + ["target"]).copy()
    return df, feature_cols

# ------------------------------------------------------------
# 4️⃣ Simple HFT‑style back‑test (tight SL/TP)
# ------------------------------------------------------------
def backtest(df: pd.DataFrame, signal: pd.Series, init_capital: float = 100_000,
             risk_perc: float = 0.02, stop_loss_factor: float = 0.001,
             take_profit_factor: float = 0.002) -> pd.Series:
    equity = init_capital
    position = None
    equity_curve = []
    for dt, row in df.iterrows():
        sig = signal.get(dt, 0)
        # --- stop‑loss / take‑profit handling for an open position ---
        if position:
            if position["direction"] == "long":
                if row["low"] <= position["stop_price"]:
                    exit_price = position["stop_price"]
                    pnl = (exit_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
                elif row["high"] >= position["take_price"]:
                    exit_price = position["take_price"]
                    pnl = (exit_price - position["entry_price"]) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
            else:
                if row["high"] >= position["stop_price"]:
                    exit_price = position["stop_price"]
                    pnl = (position["entry_price"] - exit_price) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
                elif row["low"] <= position["take_price"]:
                    exit_price = position["take_price"]
                    pnl = (position["entry_price"] - exit_price) / position["entry_price"] * position["size_usd"]
                    equity += position["size_usd"] + pnl
                    position = None
        # --- reversal based on opposite signal (if still in position) ---
        if position and ((position["direction"] == "long" and sig == -1) or (position["direction"] == "short" and sig == 1)):
            exit_price = row["adj_close"]
            pnl = (exit_price - position["entry_price"]) / position["entry_price"] * position["size_usd"] if position["direction"] == "long" else \
                  (position["entry_price"] - exit_price) / position["entry_price"] * position["size_usd"]
            equity += position["size_usd"] + pnl
            position = None
        # --- entry when flat ---
        if not position and sig != 0:
            direction = "long" if sig == 1 else "short"
            risk_amount = risk_perc * equity
            shares = int(risk_amount / row["adj_close"])
            if shares > 0:
                entry_price = row["adj_close"]
                size_usd = shares * entry_price
                if direction == "long":
                    stop_price = entry_price * (1 - stop_loss_factor)
                    take_price = entry_price * (1 + take_profit_factor)
                else:
                    stop_price = entry_price * (1 + stop_loss_factor)
                    take_price = entry_price * (1 - take_profit_factor)
                position = {"direction": direction, "shares": shares, "entry_price": entry_price,
                            "size_usd": size_usd, "stop_price": stop_price, "take_price": take_price}
                equity -= size_usd
        # --- mark‑to‑market valuation ---
        market_val = 0.0
        if position:
            if position["direction"] == "long":
                market_val = position["shares"] * row["adj_close"]
            else:
                market_val = position["shares"] * (2 * position["entry_price"] - row["adj_close"])
        total = equity + market_val
        equity_curve.append(total)
    # close any open position at the end of the test set
    if position:
        final_price = df["adj_close"].iloc[-1]
        pnl = (final_price - position["entry_price"]) / position["entry_price"] * position["size_usd"] if position["direction"] == "long" else \
              (position["entry_price"] - final_price) / position["entry_price"] * position["size_usd"]
        equity += position["size_usd"] + pnl
    return pd.Series(equity_curve, index=df.index)

# ------------------------------------------------------------
# 5️⃣ Performance metrics
# ------------------------------------------------------------
def performance(equity: pd.Series) -> dict:
    start, end = equity.index[0], equity.index[-1]
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
# 6️⃣ Probability → signal conversion
# ------------------------------------------------------------
def prob_to_signal(proba: pd.Series, high_thr: float = 0.65, low_thr: float = 0.35) -> pd.Series:
    sig = pd.Series(0, index=proba.index)
    sig[proba > high_thr] = 1
    sig[proba < low_thr] = -1
    return sig

# ------------------------------------------------------------
# 7️⃣ Main driver (rolling‑train / test)
# ------------------------------------------------------------
def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AUDUSD"
    start = sys.argv[2] if len(sys.argv) > 2 else (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    end = sys.argv[3] if len(sys.argv) > 3 else datetime.datetime.now().strftime("%Y-%m-%d")
    interval = sys.argv[4] if len(sys.argv) > 4 else "1m"
    print(f"Fetching {ticker} [{interval}] data from {start} to {end} …")
    raw = download(ticker, start, end, interval)
    if raw.empty:
        print("No data fetched for the given ticker/interval; exiting.")
        return
    df, feature_cols = build_features(raw)
    if df.empty:
        print("No data fetched for the given ticker/interval; exiting.")
        return
    split_days = 5
    split_idx = df.index.searchsorted(df.index[0] + pd.Timedelta(days=split_days))
    train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]
    X_train, y_train = train_df[feature_cols], train_df["target"]
    X_test, y_test = test_df[feature_cols], test_df["target"]
    model = GradientBoostingClassifier(n_estimators=500, learning_rate=0.05, max_depth=3, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print("\n=== Classification on test set ===")
    print(f"Accuracy: {acc:.3%}")
    print(classification_report(y_test, pred, digits=3))
    proba = pd.Series(model.predict_proba(X_test)[:, 1], index=test_df.index)
    best = None
    for high_thr in [0.60, 0.65, 0.70, 0.75]:
        for low_thr in [0.30, 0.35, 0.40, 0.45]:
            if low_thr >= high_thr:
                continue
            raw_sig = prob_to_signal(proba, high_thr, low_thr)
            sig = raw_sig.where(~((raw_sig == 1) & (test_df["sma_trend"] == 0)), 0)
            sig = sig.where(~((sig == -1) & (test_df["sma_trend"] == 1)), 0)
            for risk in [0.02, 0.05, 0.10]:
                eq = backtest(test_df, sig, risk_perc=risk, stop_loss_factor=0.001, take_profit_factor=0.002)
                stats = performance(eq)
                if best is None or stats["total_return_%"] > best["total_return_%"]:
                    best = {"high_thr": high_thr, "low_thr": low_thr, "risk_perc": risk, **stats}
    if best:
        print("\n=== Best dudaskopy grid‑search result (highest total return) ===")
        for k, v in best.items():
            print(f"{k}: {v}")
    else:
        print("No viable configuration found.")

if __name__ == "__main__":
    main()
