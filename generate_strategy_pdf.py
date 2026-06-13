#!/usr/bin/env python3
"""Generate a PDF explaining the predictive_strategy.py trading logic."""

from fpdf import FPDF


class StrategyPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Crypto Analysis AI - Predictive Strategy", align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 60, 120)
        self.cell(0, 10, title)
        self.ln(6)
        self.set_draw_color(20, 60, 120)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.set_x(self.l_margin)
        self.cell(0, 8, title)
        self.ln(6)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5, "  -  " + text)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(0, 4.5, text, fill=True)
        self.ln(2)


def build_pdf():
    pdf = StrategyPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Title ──
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 14, "Predictive Trading Strategy", align="C")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "Standalone signal engine for crypto / equities backtesting", align="C")
    pdf.ln(14)

    # ── 1. Overview ──
    pdf.section_title("1. Overview")
    pdf.body_text(
        "The Predictive Strategy is a rule-based trading signal engine that combines "
        "multiple technical indicators into a scoring system. It generates buy, sell, or "
        "hold signals with associated stop-loss and take-profit levels. The strategy is "
        "designed for backtesting on historical OHLCV (Open, High, Low, Close, Volume) "
        "candle data."
    )

    # ── 2. Data Model ──
    pdf.section_title("2. Data Model")
    pdf.body_text(
        "Each price candle is represented as a Candle dataclass with the following fields:"
    )
    for fld, desc in [("ts", "Timestamp (integer)"),
                      ("o",  "Open price"),
                      ("h",  "High price"),
                      ("l",  "Low price"),
                      ("c",  "Close price"),
                      ("v",  "Volume")]:
        pdf.bullet(f"{fld}  -  {desc}")
    pdf.ln(2)

    # ── 3. Indicators ──
    pdf.section_title("3. Technical Indicators")

    pdf.sub_title("3.1  EMA (Exponential Moving Average)")
    pdf.body_text(
        "Calculated with smoothing factor k = 2 / (period + 1). The first value is the "
        "simple mean of the first 'period' prices; subsequent values are computed as:\n"
        "    EMA = price * k + previous_EMA * (1 - k)\n"
        "Used as the building block for MACD."
    )

    pdf.sub_title("3.2  RSI (Relative Strength Index)")
    pdf.body_text(
        "Standard 14-period RSI. Computed by averaging gains and losses over the lookback "
        "window:\n"
        "    RS = avg_gain / avg_loss\n"
        "    RSI = 100 - (100 / (1 + RS))\n"
        "Thresholds: oversold at 35, overbought at 65."
    )

    pdf.sub_title("3.3  MACD (Moving Average Convergence Divergence)")
    pdf.body_text(
        "Built from three EMAs:\n"
        "    MACD Line = EMA(close, 12) - EMA(close, 26)\n"
        "    Signal    = EMA(MACD Line, 9)\n"
        "    Histogram = MACD Line - Signal\n\n"
        "Trading signals are derived from the histogram direction relative to the signal line."
    )

    pdf.sub_title("3.4  SMA (Simple Moving Average)")
    pdf.body_text(
        "50-period simple moving average used as a trend filter. Price above MA50 suggests "
        "uptrend; price below suggests downtrend."
    )

    # ── 4. Signal Generation ──
    pdf.section_title("4. Signal Generation Logic")

    pdf.sub_title("4.1  RSI / Price Divergence")
    pdf.body_text(
        "Divergence is detected by sampling three price lows and RSI values across the last "
        "10 candles (every 3rd candle):\n"
        "    Bullish divergence:  Price makes lower low, RSI makes higher low.\n"
        "    Bearish divergence:  Price makes higher low, RSI makes lower low.\n"
        "Divergence is the strongest signal and contributes 3 points to the scoring system."
    )

    pdf.sub_title("4.2  MACD Signal Prediction")
    pdf.body_text(
        "The algorithm checks the histogram slope over a 2-bar lookback:\n"
        "    MACD buy  = histogram rising AND MACD line below signal line.\n"
        "    MACD sell = histogram falling AND MACD line above signal line.\n"
        "MACD signals contribute 2 points."
    )

    pdf.sub_title("4.3  Trend & Volume Filters")
    pdf.body_text(
        "Each of the following conditions contributes 1 point to the respective score:\n"
        "    Trend:  Price vs. 50-period SMA (above = bullish, below = bearish)\n"
        "    RSI extreme:  Below 35 (oversold, bullish) / above 65 (overbought, bearish)\n"
        "    Volume spike:  Current volume > 1.5x the 20-bar average volume"
    )

    # ── 5. Scoring & Entry ──
    pdf.section_title("5. Scoring & Entry Rules")
    pdf.body_text(
        "Buy and sell scores are accumulated independently. A signal is generated when:\n"
        "    1. The dominant score exceeds 3 (e.g., buy_score >= 3).\n"
        "    2. The dominant score is strictly greater than the opposite score.\n\n"
        "If conditions are not met, the engine returns 'hold'."
    )

    pdf.sub_title("Signal Types")
    for label, desc in [
        ("Buy",  "Direction = 'buy', reason = 'div' (divergence) or 'macd'"),
        ("Sell", "Direction = 'sell', reason = 'div' or 'macd'"),
        ("Hold", "No actionable signal; skip this bar"),
    ]:
        pdf.bullet(f"{label}:  {desc}")
    pdf.ln(2)

    # ── 6. Risk Management ──
    pdf.section_title("6. Risk Management (Stop-Loss & Take-Profit)")
    pdf.body_text(
        "Every entry signal includes fixed percentage stop-loss and take-profit levels "
        "relative to the entry price:\n\n"
        "    Buy  entry:  SL = price * 0.94  (6% below entry)\n"
        "                  TP = price * 1.12  (12% above entry)\n\n"
        "    Sell entry:  SL = price * 1.06  (6% above entry)\n"
        "                  TP = price * 0.90  (10% below entry)\n\n"
        "The reward-to-risk ratio is 2:1 for buys and approximately 1.67:1 for sells."
    )

    # ── 7. Limitations ──
    pdf.section_title("7. Known Limitations")
    pdf.bullet("No dynamic position sizing or capital management.")
    pdf.bullet("Fixed SL/TP levels do not adapt to volatility (e.g., ATR-based).")
    pdf.bullet("Divergence detection uses a simple 3-point heuristic, not a peak/trough algorithm.")
    pdf.bullet("No trade filtering by broader market regime or trend strength (ADX).")
    pdf.bullet("Backtest-only logic; no live data feed or order execution integration.")
    pdf.ln(4)

    # ── 8. Usage ──
    pdf.section_title("8. Usage")
    pdf.code_block(
        "from predictive_strategy import Candle, generate_signal\n\n"
        "candles = [Candle(ts=..., o=..., h=..., l=..., c=..., v=...), ...]\n"
        "direction, reason, sl, tp = generate_signal(candles, idx=-1)"
    )

    pdf.body_text(
        "See predictive_strategy.py (132 lines) for the full implementation."
    )

    pdf.output("Predictive_Strategy_Guide.pdf")
    print("Created Predictive_Strategy_Guide.pdf")


if __name__ == "__main__":
    build_pdf()
