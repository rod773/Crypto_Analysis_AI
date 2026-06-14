//+------------------------------------------------------------------+
//|                                            HeuristicStrategy.mq5 |
//|   MQL5 Indicator – synthetic technical indicators & heuristic |
//|   signal (mirrors heuristic_strategy.py and HeuristicStrategy EA). |
//+------------------------------------------------------------------+
#property copyright   "OpenCode"
#property link        "https://github.com/your-repo"
#property version     "1.00"
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   2

#property indicator_type1   DRAW_ARROW   // Buy arrows
#property indicator_color1  clrGreen
#property indicator_width1  2
#property indicator_arrow1  233   // Wingdings arrow up

#property indicator_type2   DRAW_ARROW   // Sell arrows
#property indicator_color2  clrRed
#property indicator_width2  2
#property indicator_arrow2  234   // Wingdings arrow down

//--- indicator buffers
double BuySignal[];   // Plot upward arrow on buy trigger
double SellSignal[];  // Plot downward arrow on sell trigger

//==================================================================
// Input parameters (optional – you can expose them to the UI)
//==================================================================
input int    ArrowShiftPoints = 10; // vertical offset for arrows (points)

//==================================================================
// Helper: round price like Python version (used for support/ resistance)
//==================================================================
double RoundPrice(double value)
{
   if(MathAbs(value) < 10.0)
      return NormalizeDouble(value,4);
   return NormalizeDouble(value,0);
}

//==================================================================
// Heuristic calculation – identical to the Python implementation
//==================================================================
int HeuristicSignal(double price, double change24h)
{
   // --- RSI ----------------------------------------------------
   int rsi_raw = (int)MathRound(50.0 + change24h * 1.5);
   int rsi = MathMax(15, MathMin(85, rsi_raw));

   // --- MACD ---------------------------------------------------
   string macd;
   if(rsi > 60)       macd = "bullish crossover";
   else if(rsi < 40)  macd = "bearish crossover";
   else               macd = "neutral";

   // --- Trend --------------------------------------------------
   string trend;
   if(change24h > 2.0)       trend = "bullish";
   else if(change24h < -2.0) trend = "bearish";
   else                      trend = "neutral";

   // --- Heuristic decision -------------------------------------
   if(macd == "bullish crossover" && trend == "bullish")
      return  1; // BUY
   if(macd == "bearish crossover" && trend == "bearish")
      return -1; // SELL
   return 0;    // HOLD
}

//==================================================================
// OnCalculate – main indicator loop
//==================================================================
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const int begin,
                const double &price[])
{
   //--- we need at least two closes to compute a 24‑h change
   if(rates_total < 2)
      return 0;

   //--- determine how many bars back correspond to roughly 24 hours.
   //   Use the ratio of daily seconds to the chart period seconds.
   int shift = (int)(PeriodSeconds(PERIOD_D1) / PeriodSeconds(_Period));
   if(shift < 1) shift = 1; // protect division by zero for D1 chart

   //--- set the start index (skip bars where we cannot compute change)
   int start = MathMax(shift, prev_calculated - 1);
   if(start < shift) start = shift;

   for(int i = start; i < rates_total; i++)
   {
      //--- price of the current bar
      double cur_price = price[i];
      //--- price of the bar 24 h ago (or the previous bar if not enough history)
      double past_price = (i - shift >= 0) ? price[i - shift] : price[i-1];
      if(past_price == 0) past_price = cur_price; // avoid division by zero

      double change24h = ((cur_price - past_price) / past_price) * 100.0;

      int signal = HeuristicSignal(cur_price, change24h);

      //--- clear previous values
      BuySignal[i]  = EMPTY_VALUE;
      SellSignal[i] = EMPTY_VALUE;

      if(signal == 1)
      {
         // Plot an up‑arrow a few points below the low of the bar
         double level = Low[i] - ArrowShiftPoints * _Point;
         BuySignal[i] = level;
      }
      else if(signal == -1)
      {
         // Plot a down‑arrow a few points above the high of the bar
         double level = High[i] + ArrowShiftPoints * _Point;
         SellSignal[i] = level;
      }
   }

   return rates_total;
}

//+------------------------------------------------------------------+