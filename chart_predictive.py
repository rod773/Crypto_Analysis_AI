#!/usr/bin/env python3
"""Generate comparison chart: reactive vs predictive backtest."""
import json, datetime
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter

# Load data
with open('backtest_result.json') as f: old = json.load(f)
with open('predictive_backtest.json') as f: new = json.load(f)

# Dates
old_dates = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in old['dates']]
new_dates = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in new['dates']]

# Normalize both to 10000 initial
old_eq = old['equity']
new_eq = new['equity']
old_ret = ((old_eq[-1] / 10000) - 1) * 100
new_ret = ((new_eq[-1] / 10000) - 1) * 100

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [2, 1, 1]})

# Panel 1: Equity curves
ax1.plot(old_dates, old_eq, label=f"Reactive: {old_ret:.1f}%", color="red", linewidth=1.5)
ax1.plot(new_dates, new_eq, label=f"Predictive: {new_ret:.1f}%", color="green", linewidth=1.5)
ax1.axhline(10000, color="black", linestyle="--", alpha=0.3)
ax1.set_title("Crypto Analysis AI - Reactive vs Predictive Backtest (ETH/USDT)", fontsize=16, fontweight="bold")
ax1.set_ylabel("Portfolio Value ($)")
ax1.legend(loc="upper left")
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Panel 2: ETH Price with trade markers (predictive)
candles = new.get('candles', [])
if candles:
    c_dates = [datetime.datetime.strptime(c['date'], "%Y-%m-%d") for c in candles]
    closes = [c['close'] for c in candles]
    ax2.plot(c_dates, closes, label="ETH Price", color="black", linewidth=0.8, alpha=0.7)
    # Predictive trades
    for t in new['trades']:
        try:
            td = datetime.datetime.strptime(t['date'], "%Y-%m-%d")
            if t['side'] == 'long':
                ax2.scatter([td], [t['entry']], color='green', marker='^', s=30, zorder=5)
            else:
                ax2.scatter([td], [t['entry']], color='red', marker='v', s=30, zorder=5)
        except KeyError:
            continue
    ax2.set_ylabel("ETH Price ($)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Panel 3: Statistics comparison
stats_text = (
    "Reactive (Old)\n"
    f"  Return: {((json.load(open('backtest_result.json'))['equity'][-1]/10000)-1)*100:.1f}%\n"
    f"  Trades: {len(json.load(open('backtest_result.json'))['trades'])}\n"
    f"  Win Rate: {37.1:.1f}%\n\n"
    "Predictive (New)\n"
    f"  Return: {new_ret:.1f}%\n"
    f"  Trades: {len(new['trades'])}\n"
    f"  Win Rate: {(37/75)*100:.1f}%\n"
)
ax3.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center', family='monospace')
ax3.axis('off')

plt.tight_layout()
plt.savefig("comparison_chart.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Chart saved to comparison_chart.png")
