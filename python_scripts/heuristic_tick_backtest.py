#!/usr/bin/env python3
"""Backtest the heuristic strategy on tick (intraday) data.

The script fetches OHLCV data at a user‑specified interval (default 1 minute) using
the TradingView API (fallback to Tickstory CSV via ``dudaskopy``).
It then computes the synthetic technical indicators defined in
``heuristic_strategy.py`` and generates a simple ``buy``/``sell``/``hold`` signal
per bar.

Position sizing mirrors the daily back‑test: a fixed percentage of the available
cash is used for each trade. Stop‑loss and take‑profit levels are taken from the
nearest support/resistance levels produced by the synthetic indicator.

Usage example::

    python heuristic_tick_backtest.py ETHUSDT 2024-06-01 2024-06-30 1m

The result is printed to the console and saved as ``heuristic_tick_backtest_result.json``.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict

import pandas as pd

# Local imports – these modules reside in the same ``python_scripts`` package.
# ``heuristic_strategy`` provides the indicator and signal logic.
# ``tradingview_fetch`` offers a lightweight data downloader.
# If TradingView fails, ``dudaskopy`` will fall back to a Tickstory CSV export.

try:
    from heuristic_strategy import heuristic_signal, parse_technical_indicators
except Exception as e:
    print(f"Failed to import heuristic strategy module: {e}")
    sys.exit(1)

try:
    from tradingview_fetch import download_tradingview
except Exception:
    download_tradingview = None

# ``dudaskopy`` contains a robust download() helper that tries TradingView and then
# a CSV fallback. Importing the whole module pulls in heavy ML libraries, but they
# are only imported when needed. The function we need – ``download`` – is lightweight.
try:
    from dudaskopy import download as fallback_download
except Exception:
    fallback_download = None

# ---------------------------------------------------------------------------
# Configuration (mirrors daily back‑test defaults)
# ---------------------------------------------------------------------------
POSITION_SIZE_PCT = 0.95  # % of cash allocated to each trade
FEE_PCT = 0.001           # 0.1 % per trade (ignored for simplicity in equity calc)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    entry_date: str
    entry_price: float
    direction: str         # 'long' or 'short'
    size_usd: float
    exit_price: Optional[float] = None
    exit_date: Optional[str] = None
    pnl: float = 0.0
    exit_reason: str = ""

@dataclass
class BacktestState:
    cash: float
    position: Optional[Dict] = None  # None = flat, otherwise dict with trade details
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Helper: interval → minutes conversion
# ---------------------------------------------------------------------------

def interval_minutes(interval: str) -> int:
    """Convert a TradingView interval string (e.g., '1m', '5m', '1h', 'D') to minutes.

    Daily intervals are treated as 1440 minutes.
    """
    interval = interval.lower()
    if interval.endswith('m'):
        return int(interval[:-1])
    if interval.endswith('h'):
        return int(interval[:-1]) * 60
    if interval == 'd':
        return 1440
    raise ValueError(f"Unsupported interval: {interval}")

# ---------------------------------------------------------------------------
# Core back‑test logic
# ---------------------------------------------------------------------------

def run_backtest(df: pd.DataFrame) -> BacktestState:
    """Iterate over the OHLCV DataFrame and apply the heuristic strategy.

    The DataFrame must contain the columns ``open, high, low, close, volume``
    and be indexed by pandas ``Timestamp`` objects in chronological order.
    """
    # Compute 24‑hour percentage change based on the interval length.
    # For a 1 minute bar we look back 1440 rows (24 h). If the interval does not
    # divide 1440 evenly we round to the nearest integer number of periods.
    minutes = interval_minutes(df.attrs.get('interval', '1m'))
    periods = max(1, round(1440 / minutes))
    df = df.copy()
    df['change_24h'] = df['close'].pct_change(periods=periods) * 100

    state = BacktestState(cash=10_000.0)  # initial capital – mirrors daily config
    closes: List[float] = []

    for ts, row in df.iterrows():
        # Skip rows where we cannot compute a 24‑h change yet.
        if pd.isna(row['change_24h']):
            closes.append(row['close'])
            continue

        price = row['close']
        change_24h = row['change_24h']
        closes.append(price)

        # Generate heuristic signal.
        signal = heuristic_signal(price, change_24h, closes)

        # -------------------------------------------------------------------
        # Exit logic – stop‑loss / take‑profit / reversal
        # -------------------------------------------------------------------
        if state.position:
            pos = state.position
            direction = pos['direction']
            # Stop‑loss & take‑profit handling
            if direction == 'long':
                if row['low'] <= pos['stop_loss']:
                    exit_price = pos['stop_loss']
                    reason = 'stop_loss'
                elif row['high'] >= pos['take_profit']:
                    exit_price = pos['take_profit']
                    reason = 'take_profit'
                else:
                    exit_price = None
                    reason = None
            else:  # short
                if row['high'] >= pos['stop_loss']:
                    exit_price = pos['stop_loss']
                    reason = 'stop_loss'
                elif row['low'] <= pos['take_profit']:
                    exit_price = pos['take_profit']
                    reason = 'take_profit'
                else:
                    exit_price = None
                    reason = None

            # Reversal based on opposite signal
            if not exit_price and ((direction == 'long' and signal == 'sell') or (direction == 'short' and signal == 'buy')):
                exit_price = row['close']
                reason = 'signal_reversal'

            if exit_price is not None:
                # Compute P&L
                if direction == 'long':
                    pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * pos['size_usd']
                else:
                    pnl = (pos['entry_price'] - exit_price) / pos['entry_price'] * pos['size_usd']
                state.cash += pos['size_usd'] + pnl - (pos['size_usd'] * FEE_PCT)
                state.trades.append(
                    Trade(
                        entry_date=pos['entry_date'],
                        entry_price=pos['entry_price'],
                        direction=direction,
                        size_usd=pos['size_usd'],
                        exit_price=exit_price,
                        exit_date=ts.strftime('%Y-%m-%d'),
                        pnl=pnl,
                        exit_reason=reason,
                    )
                )
                state.position = None

        # -------------------------------------------------------------------
        # Entry logic – open a new position if flat.
        # -------------------------------------------------------------------
        if not state.position and signal in ('buy', 'sell'):
            size_usd = state.cash * POSITION_SIZE_PCT
            state.cash -= size_usd
            # Generate synthetic technicals for stop / TP levels.
            tech = parse_technical_indicators(price, change_24h, closes)
            if signal == 'buy':
                stop_loss = tech.support_levels[0]
                take_profit = tech.resistance_levels[0]
                direction = 'long'
            else:  # sell
                stop_loss = tech.resistance_levels[0]
                take_profit = tech.support_levels[0]
                direction = 'short'
            state.position = {
                'direction': direction,
                'entry_price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'size_usd': size_usd,
                'entry_date': ts.strftime('%Y-%m-%d'),
                'entry_idx': None,  # not needed for equity calc
            }

        # -------------------------------------------------------------------
        # Equity tracking – mark‑to‑market valuation of open position.
        # -------------------------------------------------------------------
        equity = state.cash
        if state.position:
            pos = state.position
            if pos['direction'] == 'long':
                equity += pos['size_usd'] * (price / pos['entry_price'])
            else:
                # For short we approximate profit as (entry/price) * size
                equity += pos['size_usd'] * (pos['entry_price'] / price)
        state.equity_curve.append(equity)
        state.dates.append(ts.strftime('%Y-%m-%d'))

    # -------------------------------------------------------------------
    # Close any remaining open position at the last price.
    # -------------------------------------------------------------------
    if state.position:
        pos = state.position
        final_price = df.iloc[-1]['close']
        if pos['direction'] == 'long':
            pnl = (final_price - pos['entry_price']) / pos['entry_price'] * pos['size_usd']
        else:
            pnl = (pos['entry_price'] - final_price) / pos['entry_price'] * pos['size_usd']
        state.cash += pos['size_usd'] + pnl - (pos['size_usd'] * FEE_PCT)
        state.trades.append(
            Trade(
                entry_date=pos['entry_date'],
                entry_price=pos['entry_price'],
                direction=pos['direction'],
                size_usd=pos['size_usd'],
                exit_price=final_price,
                exit_date=df.index[-1].strftime('%Y-%m-%d'),
                pnl=pnl,
                exit_reason='end_of_test',
            )
        )
        state.position = None

    return state

# ---------------------------------------------------------------------------
# Data download wrapper – tries TradingView first, then Tickstory CSV.
# ---------------------------------------------------------------------------

def fetch_data(ticker: str, start: str, end: str, interval: str = "1m") -> pd.DataFrame:
    """Fetch OHLCV data for the given ticker/period.

    The function prefers the lightweight TradingView fetch; if it fails it falls
    back to the CSV loader from ``dudaskopy`` (which itself tries TradingView
    internally). If both fail, we attempt a yfinance download (useful for forex
    symbols such as ``AUDUSD=X``). The returned DataFrame has ``open, high, low,
    close, volume`` columns and a ``Timestamp`` index.
    """
    # 1️⃣ TradingView fetch (primary)
    if download_tradingview:
        try:
            df = download_tradingview(ticker, start, end, interval)
            if not df.empty:
                df.attrs['interval'] = interval
                return df
        except Exception as exc:
            print(f"TradingView fetch failed ({exc}), falling back to CSV.")
    # 2️⃣ CSV fallback (Tickstory)
    if fallback_download:
        df = fallback_download(ticker, start, end, interval)
        if not df.empty:
            df.attrs['interval'] = interval
            return df
    # 3️⃣ yfinance fallback (especially for forex symbols)
    try:
        import yfinance as yf
        # yfinance expects interval strings like '1m', '5m', '1h', '1d'
        df = yf.Ticker(ticker).history(start=start, end=end, interval=interval, auto_adjust=False)
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.rename(columns={'Close': 'close'}, inplace=True)
            df.columns = [c.lower() for c in df.columns]
            df.index = pd.to_datetime(df.index)
            df.attrs['interval'] = interval
            return df
    except Exception as e:
        print(f"yfinance fetch failed ({e})")
    raise RuntimeError("Unable to fetch data for the requested ticker/interval.")

# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Heuristic strategy backtest on tick data.")
    parser.add_argument("ticker", help="Ticker symbol, e.g., ETHUSDT or BINANCE:BTCUSDT")
    parser.add_argument("start", help="Start date (YYYY‑MM‑DD)")
    parser.add_argument("end", nargs='?', default=datetime.now().strftime('%Y-%m-%d'), help="End date (default: today)")
    parser.add_argument("interval", nargs='?', default="1m", help="Data interval such as 1m, 5m, 1h, D (default: 1m)")
    parser.add_argument("--csv", dest="csv_path", default=None, help="Path to a Tickstory CSV file (overrides ticker download)")
    args = parser.parse_args()

    if args.csv_path:
        # Load Tickstory CSV directly
        try:
            from dudaskopy import load_tickstory_csv
        except Exception as e:
            print(f"Failed to import Tickstory CSV loader: {e}")
            sys.exit(1)
        print(f"Loading Tickstory CSV from {args.csv_path} …")
        df = load_tickstory_csv(args.csv_path, interval=args.interval)
        df.attrs['interval'] = args.interval
    else:
        print(f"Fetching {args.ticker} [{args.interval}] data from {args.start} to {args.end} …")
        df = fetch_data(args.ticker, args.start, args.end, args.interval)
    if df.empty:
        print("No data fetched – aborting.")
        return
    print(f"Fetched {len(df)} rows of OHLCV data.")

    state = run_backtest(df)

    # Simple report analogous to the daily back‑test.
    final_equity = state.equity_curve[-1] if state.equity_curve else state.cash
    total_return = (final_equity / 10_000.0 - 1) * 100
    print("\n=== Heuristic Tick Backtest Report ===")
    print(f"Initial Capital:    $10,000.00")
    print(f"Final Equity:        ${final_equity:,.2f}")
    print(f"Total Return:        {total_return:.2f}%")
    print(f"Trades executed:    {len(state.trades)}")

    # Save detailed results for further analysis.
    output = {
        "dates": state.dates,
        "equity": state.equity_curve,
        "trades": [
            {
                "entry_date": t.entry_date,
                "entry_price": t.entry_price,
                "direction": t.direction,
                "size_usd": t.size_usd,
                "exit_price": t.exit_price,
                "exit_date": t.exit_date,
                "pnl": t.pnl,
                "exit_reason": t.exit_reason,
            }
            for t in state.trades
        ],
    }
    out_path = "heuristic_tick_backtest_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nDetailed results saved to {out_path}")


if __name__ == "__main__":
    main()
