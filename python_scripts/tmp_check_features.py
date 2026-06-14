import yfinance as yf, pandas as pd, datetime

def download(ticker, start, end):
    df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.rename(columns={"Close": "adj_close"}, inplace=True)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index)
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))

def macd_hist(series):
    ema_fast = series.ewm(span=12, adjust=False).mean()
    ema_slow = series.ewm(span=26, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    sig_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line - sig_line

def build_features(df):
    df["rsi"] = compute_rsi(df["adj_close"])
    df["macd_hist"] = macd_hist(df["adj_close"])
    df["price_change_5d"] = df["adj_close"].pct_change(5)
    df["sma_20"] = df["adj_close"].rolling(20).mean()
    df["sma_50"] = df["adj_close"].rolling(50).mean()
    df["sma_trend"] = (df["sma_20"] > df["sma_50"]).astype(int)
    df["vol_change_5d"] = df["volume"].pct_change(5)
    df["target"] = (df["adj_close"].shift(-1) > df["adj_close"]).astype(int)
    cols = ["rsi", "macd_hist", "price_change_5d", "sma_trend", "vol_change_5d"]
    df = df.dropna(subset=cols + ["target"]).copy()
    return df

ticker = "AUDUSD=X"
start = "2015-01-01"
end = datetime.datetime.today().strftime("%Y-%m-%d")
raw = download(ticker, start, end)
print('raw rows', len(raw))
feat = build_features(raw)
print('feature rows', len(feat))
print(feat.head())
print(feat.tail())
print('Columns present:', raw.columns)
