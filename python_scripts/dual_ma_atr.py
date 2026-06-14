# dual_ma_atr.py
"""
Dual moving‑average crossover strategy with ATR‑based position sizing
and a 2×ATR trailing stop. Educational example – not a guaranteed profit.

Features
- SMA short (default 50) vs SMA long (default 200)
- ATR for volatility‑adjusted position size
- Fixed risk per trade (default 2 % of equity)
- Trailing stop set to 2×ATR below entry (for longs)
- Simple back‑test loop, prints CAGR, total return and max draw‑down

Usage:
    python dual_ma_atr.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# ------------------------------------------------------------
# 1️⃣ Download data
# ------------------------------------------------------------
def download(ticker: str, start: str, end: str) -> pd.DataFrame:
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(start=start, end=end, auto_adjust=False)
    # Keep required columns and rename Close to adj_close for consistency
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.rename(columns={"Close": "adj_close"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index)
    return df

# ------------------------------------------------------------
# 2️⃣ Indicator helpers
# ------------------------------------------------------------
def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ------------------------------------------------------------

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line - signal_line

# 3️⃣ Build signals & risk parameters
# ------------------------------------------------------------
def add_signals(df: pd.DataFrame,
                short_win: int = 50,
                long_win: int = 200,
                atr_win: int = 14,
                risk_perc: float = 0.02,
                stop_mult: float = 2.0) -> pd.DataFrame:
    # Moving averages
    df['sma_short'] = df['adj_close'].rolling(short_win).mean()
    df['sma_long']  = df['adj_close'].rolling(long_win).mean()

    # ATR for volatility‑based sizing
    df['atr'] = atr(df['high'], df['low'], df['adj_close'], period=atr_win)

    # Compute technical features
    df['rsi'] = compute_rsi(df['adj_close'], period=14)
    df['macd_hist'] = compute_macd(df['adj_close'])
    df['price_change_5d'] = df['adj_close'].pct_change(5)

    # Divergence features (5‑day lookback)
    df['rsi_change_5d'] = df['rsi'].diff(5)
    df['macd_change_5d'] = df['macd_hist'].diff(5)
    df['rsi_bull_div'] = ((df['price_change_5d'] < 0) & (df['rsi_change_5d'] > 0)).astype(int)
    df['macd_bull_div'] = ((df['price_change_5d'] < 0) & (df['macd_change_5d'] > 0)).astype(int)

    # Trend indicator
    df['sma_trend'] = (df['sma_short'] > df['sma_long']).astype(int)

    # Target: next‑day up move (1) vs down/no‑move (0)
    df['future_return'] = df['adj_close'].shift(-1) / df['adj_close'] - 1
    df['target'] = (df['future_return'] > 0).astype(int)

    # Features for the machine‑learning model
    feature_cols = ['sma_trend', 'rsi', 'macd_hist', 'rsi_bull_div', 'macd_bull_div', 'price_change_5d']
    train_df = df.dropna(subset=feature_cols + ['target'])
    if not train_df.empty:
        X = train_df[feature_cols]
        y = train_df['target']
        # Use a random forest for non‑linear relationships
        model = RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42, n_jobs=-1)
        model.fit(X, y)
        # Use probability threshold to generate a higher‑confidence long signal
        prob = model.predict_proba(df[feature_cols].fillna(0))[:, 1]
        df['ml_signal'] = (prob > 0.65).astype(int)
    else:
        df['ml_signal'] = 0
    # Final trading signal (shifted to avoid look‑ahead)
    df['signal'] = df['ml_signal'].shift(1).fillna(0)

    # Placeholder columns for stop price – will be filled in the back‑test loop
    df['stop_price'] = np.nan
    return df

# ------------------------------------------------------------
# 4️⃣ Back‑test loop (vectorised where possible)
# ------------------------------------------------------------
def backtest(df: pd.DataFrame,
             initial_capital: float = 100_000,
             risk_perc: float = 0.02,
             stop_mult: float = 2.0) -> pd.DataFrame:
    df = df.dropna(subset=['sma_short', 'sma_long', 'atr']).copy()
    equity = initial_capital
    position = 0          # number of shares held
    entry_price = 0.0
    stop_price = 0.0

    equity_curve = []
    position_series = []

    for i, row in df.iterrows():
        # ---- Update trailing stop if we have an open position ----
        if position > 0:
            # trailing stop = max(previous stop, current close - stop_mult * ATR)
            new_stop = max(stop_price, row['adj_close'] - stop_mult * row['atr'])
            stop_price = new_stop
            # Stop hit?
            if row['low'] <= stop_price:
                equity -= position * stop_price
                position = 0
                entry_price = 0.0
                stop_price = 0.0

        # ---- Entry logic (only when flat) ----
        if position == 0 and row['signal'] == 1:
            # Risk per trade = risk_perc * equity
            risk_amount = risk_perc * equity
            # Dollar size = risk_amount / (stop_mult * ATR)
            dollar_size = risk_amount / (stop_mult * row['atr'])
            # Number of shares (floor to whole shares)
            shares = int(dollar_size / row['adj_close'])
            if shares > 0:
                entry_price = row['adj_close']
                stop_price = entry_price - stop_mult * row['atr']
                position = shares
                equity -= shares * entry_price  # cash outflow

        # ---- Daily mark‑to‑market for equity ----
        market_value = position * row['adj_close'] if position else 0.0
        total_equity = equity + market_value
        equity_curve.append(total_equity)
        position_series.append(position)

    df = df.assign(equity=pd.Series(equity_curve, index=df.index),
                   shares=pd.Series(position_series, index=df.index))
    return df

# ------------------------------------------------------------
# 5️⃣ Performance metrics
# ------------------------------------------------------------
def performance(df: pd.DataFrame) -> dict:
    start = df.index[0]
    end = df.index[-1]
    years = (end - start).days / 365.25
    total_ret = df['equity'].iloc[-1] / df['equity'].iloc[0] - 1
    cagr = (1 + total_ret) ** (1 / years) - 1
    # Max draw‑down
    roll_max = df['equity'].cummax()
    drawdown = (roll_max - df['equity']) / roll_max
    max_dd = drawdown.max()
    return {
        'total_return_%': round(total_ret * 100, 2),
        'cagr_%': round(cagr * 100, 2),
        'max_drawdown_%': round(max_dd * 100, 2),
        'years': round(years, 2)
    }

# ------------------------------------------------------------
# 6️⃣ Run the whole pipeline (with optional grid optimisation)
# ------------------------------------------------------------
if __name__ == '__main__':
    ticker = 'BTC-USD'                 # Bitcoin USD pair – higher volatility
    start_date = '2000-01-01'
    end_date   = datetime.today().strftime('%Y-%m-%d')

    data = download(ticker, start_date, end_date)
    # Basic run – default parameters
    data = add_signals(data,
                       short_win=50,
                       long_win=200,
                       atr_win=14,
                       risk_perc=0.05,
                       stop_mult=1.5)
    print(f"Signal count: {data['signal'].sum()}")
    data = backtest(data,
                    initial_capital=100_000,
                    risk_perc=0.02,
                    stop_mult=2.0)

    stats = performance(data)
    print('\n=== Dual-MA + ATR Strategy on {} ==='.format(ticker))
    for k, v in stats.items():
        print(f'{k}: {v}')

    # --------------------------------------------------------
    # Grid optimisation disabled for speed (removed heavy loops)
    # ---- Mini grid search for better parameters (fast) ----
    best = None
    for risk in [0.01, 0.05, 0.1]:
        for stop in [1.0, 1.5, 2.0]:
            tmp = add_signals(data.copy(), short_win=20, long_win=80,
                               atr_win=10, risk_perc=risk, stop_mult=stop)
            tmp = backtest(tmp, initial_capital=100_000, risk_perc=risk, stop_mult=stop)
            s = performance(tmp)
            if best is None or s['cagr_%'] > best['cagr_%']:
                best = {'risk_perc': risk, 'stop_mult': stop, **s}
    if best:
        print('\n=== Mini-grid best result ===')
        for k, v in best.items():
            print(f'{k}: {v}')

