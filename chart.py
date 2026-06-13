#!/usr/bin/env python3
"""
Generate chart for the backtest results.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def main():
    with open("backtest_result.json", "r") as f:
        data = json.load(f)

    dates = [datetime.strptime(d, "%Y-%m-%d") for d in data["dates"]]
    equity = data["equity"]
    
    # Extract candle data
    candles = data.get("candles", [])
    if candles:
        candle_dates = [datetime.strptime(c["date"], "%Y-%m-%d") for c in candles]
        closes = [c["close"] for c in candles]
    else:
        candle_dates = dates
        closes = []
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]}, sharex=True)
    
    # Plot 1: Equity curve
    ax1.plot(dates, equity, label="Strategy Equity", color="#00C49A", linewidth=1.5)
    ax1.axhline(y=10000, color="gray", linestyle="--", alpha=0.5, label="Initial Capital")
    ax1.fill_between(dates, equity, 10000, alpha=0.2, color="#00C49A")
    ax1.set_title("Crypto Analysis AI - 1 Year Backtest (ETH/USDT)", fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel("Portfolio Value ($)", fontsize=12)
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    
    # Format y-axis as currency
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Plot 2: ETH Price with trade signals
    if closes:
        ax2.plot(candle_dates, closes, label="ETH Price", color="#FF6B6B", linewidth=0.8, alpha=0.8)
        
        # Add buy/sell markers
        for trade in data.get("trades", []):
            entry_date = datetime.strptime(trade["entry_date"], "%Y-%m-%d")
            direction = trade["direction"]
            color = "#228B22" if direction == "long" else "#DC143C"
            marker = "^" if direction == "long" else "v"
            ax2.scatter([entry_date], [trade["entry_price"]], color=color, marker=marker, s=20, zorder=5, alpha=0.6)
    
    ax2.set_ylabel("ETH Price ($)", fontsize=12)
    ax2.set_xlabel("Date", fontsize=12)
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig("backtest_chart.png", dpi=150, bbox_inches="tight", facecolor="white")
    print("Chart saved to backtest_chart.png")
    
    # Show statistics text
    fig2, ax3 = plt.subplots(figsize=(10, 6))
    fig2.patch.set_facecolor('white')
    ax3.axis('off')
    
    stats_text = f"""
    BACKTEST SUMMARY
    ================================
    Period:           2024-06-13 to 2025-06-13
    Asset:            ETH/USDT
    Initial Capital:  $10,000.00
    Final Value:      ${equity[-1]:,.2f}
    Total Return:     {((equity[-1] / 10000) - 1) * 100:.2f}%
    
    Total Trades:     {len(data.get('trades', []))}
    Win Rate:         37.1%
    Avg Win:          $398.11
    Avg Loss:         $-253.28
    Sharpe Ratio:     -0.615
    
    ⚠️  STRATEGY WARNING
    The backtest shows a significant loss.
    The algorithm generated too many signals 
    and had poor risk management.
    """
    
    ax3.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center', 
             family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.savefig("backtest_stats.png", dpi=150, bbox_inches="tight", facecolor="white")
    print("Stats chart saved to backtest_stats.png")

if __name__ == "__main__":
    main()
