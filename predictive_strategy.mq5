//+------------------------------------------------------------------+
//|                                             PredictiveStrategy.mq5 |
//|                        Generated from predictive_strategy.py      |
//+------------------------------------------------------------------+
#property copyright "Predictive Strategy"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

// --- Inputs ---
input int      RsiPeriod        = 14;     // RSI Period
input int      MacdFast         = 12;     // MACD Fast EMA
input int      MacdSlow         = 26;     // MACD Slow EMA
input int      MacdSignal       = 9;      // MACD Signal
input int      MaPeriod         = 50;     // MA Period (SMA)
input int      VolLookback      = 20;     // Volume lookback
input double   VolMult          = 1.5;    // Volume multiplier
input int      MinScore         = 3;      // Minimum score for entry
input double   SlLongPct        = 6.0;    // Stop Loss Long %
input double   TpLongPct        = 12.0;   // Take Profit Long %
input double   SlShortPct       = 6.0;    // Stop Loss Short %
input double   TpShortPct       = 10.0;   // Take Profit Short %

// --- Handles ---
int rsiHandle, macdHandle, maHandle;

//+------------------------------------------------------------------+
//| Custom indicator initialization                                  |
//+------------------------------------------------------------------+
int OnInit()
{
   rsiHandle = iRSI(NULL, 0, RsiPeriod, PRICE_CLOSE);
   macdHandle = iMACD(NULL, 0, MacdFast, MacdSlow, MacdSignal, PRICE_CLOSE);
   maHandle = iMA(NULL, 0, MaPeriod, 0, MODE_SMA, PRICE_CLOSE);

   if (rsiHandle == INVALID_HANDLE || macdHandle == INVALID_HANDLE || maHandle == INVALID_HANDLE)
   {
      Print("Failed to create indicator handles");
      return INIT_FAILED;
   }

   IndicatorSetString(INDICATOR_SHORTNAME, "PredStrat");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Deinitialization                                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) { }

//+------------------------------------------------------------------+
//| Iteration                                                        |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   static int lastSignalBar = 0;
   static string signalDir = "";
   static double signalSl = 0, signalTp = 0;

   if (rates_total < 60) return 0;

   int start = prev_calculated > 0 ? prev_calculated - 1 : 60;

   // Buffers
   double rsiBuf[], macdBuf[], macdSigBuf[], macdHistBuf[], maBuf[], volAvgBuf[];
   ArraySetAsSeries(rsiBuf, true);
   ArraySetAsSeries(macdBuf, true);
   ArraySetAsSeries(macdSigBuf, true);
   ArraySetAsSeries(macdHistBuf, true);
   ArraySetAsSeries(maBuf, true);
   ArraySetAsSeries(volAvgBuf, true);

   CopyBuffer(rsiHandle, 0, 0, rates_total, rsiBuf);
   CopyBuffer(macdHandle, 0, 0, rates_total, macdBuf);
   CopyBuffer(macdHandle, 1, 0, rates_total, macdSigBuf);
   CopyBuffer(macdHandle, 2, 0, rates_total, macdHistBuf);
   CopyBuffer(maHandle, 0, 0, rates_total, maBuf);

   // Volume SMA
   double volSma[];
   ArrayResize(volSma, rates_total);
   for (int i = 0; i < rates_total; i++)
   {
      if (i < VolLookback)
      {
         double sum = 0;
         for (int j = 0; j <= i; j++) sum += (double)tick_volume[j];
         volSma[i] = sum / (i + 1);
      }
      else
      {
         double sum = 0;
         for (int j = i - (int)VolLookback + 1; j <= i; j++) sum += (double)tick_volume[j];
         volSma[i] = sum / VolLookback;
      }
   }

   // Main loop
   for (int i = start; i < rates_total; i++)
   {
      int idx = i;
      if (idx < 30) continue;

      // --- Divergence ---
      bool bullishDiv = false, bearishDiv = false;
      if (idx > 20)
      {
         int s1 = idx - 10, s2 = idx - 7, s3 = idx - 4, s4 = idx - 1;
         if (s1 >= 0 && s2 >= 0 && s3 >= 0 && s4 >= 0)
         {
            if (low[s3] > low[s4] && rsiBuf[s3] < rsiBuf[s4])
               bullishDiv = true;
            if (low[s3] < low[s4] && rsiBuf[s3] > rsiBuf[s4])
               bearishDiv = true;
         }
      }

      // --- MACD ---
      bool histGrowing = macdHistBuf[idx] > macdHistBuf[idx - 2];
      bool histDeclining = macdHistBuf[idx] < macdHistBuf[idx - 2];
      bool macdBuy = histGrowing && macdBuf[idx] < macdSigBuf[idx];
      bool macdSell = histDeclining && macdBuf[idx] > macdSigBuf[idx];

      // --- Volume ---
      bool volSpike = (double)tick_volume[idx] > volSma[idx] * VolMult;

      // --- Scoring ---
      int buyScore = 0, sellScore = 0;

      if (bullishDiv) buyScore += 3;
      if (macdBuy) buyScore += 2;
      if (close[idx] > maBuf[idx]) buyScore += 1;
      if (rsiBuf[idx] < 35) buyScore += 1;
      if (volSpike) buyScore += 1;

      if (bearishDiv) sellScore += 3;
      if (macdSell) sellScore += 2;
      if (close[idx] < maBuf[idx]) sellScore += 1;
      if (rsiBuf[idx] > 65) sellScore += 1;
      if (volSpike) sellScore += 1;

      // --- Signal ---
      string dir = "";
      double sl = 0, tp = 0;

      if (buyScore > sellScore && buyScore >= MinScore && lastSignalBar != idx)
      {
         dir = "buy";
         sl = close[idx] * (1 - SlLongPct / 100);
         tp = close[idx] * (1 + TpLongPct / 100);
         lastSignalBar = idx;
      }
      else if (sellScore > buyScore && sellScore >= MinScore && lastSignalBar != idx)
      {
         dir = "sell";
         sl = close[idx] * (1 + SlShortPct / 100);
         tp = close[idx] * (1 - TpShortPct / 100);
         lastSignalBar = idx;
      }

      // --- Draw objects ---
      if (dir == "buy" && lastSignalBar == idx)
      {
         ObjectDelete(0, "sig_" + IntegerToString(idx));
         ObjectCreate(0, "sig_" + IntegerToString(idx), OBJ_ARROW_BUY, 0, time[idx], low[idx] - 5 * Point());
         ObjectSetInteger(0, "sig_" + IntegerToString(idx), OBJPROP_COLOR, clrLime);
         ObjectSetInteger(0, "sig_" + IntegerToString(idx), OBJPROP_WIDTH, 2);

         ObjectDelete(0, "sl_" + IntegerToString(idx));
         ObjectCreate(0, "sl_" + IntegerToString(idx), OBJ_TREND, 0, time[idx], sl, time[idx] + 86400, sl);
         ObjectSetInteger(0, "sl_" + IntegerToString(idx), OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, "sl_" + IntegerToString(idx), OBJPROP_STYLE, STYLE_DASH);

         ObjectDelete(0, "tp_" + IntegerToString(idx));
         ObjectCreate(0, "tp_" + IntegerToString(idx), OBJ_TREND, 0, time[idx], tp, time[idx] + 86400, tp);
         ObjectSetInteger(0, "tp_" + IntegerToString(idx), OBJPROP_COLOR, clrLime);
         ObjectSetInteger(0, "tp_" + IntegerToString(idx), OBJPROP_STYLE, STYLE_DASH);
      }
      else if (dir == "sell" && lastSignalBar == idx)
      {
         ObjectDelete(0, "sig_" + IntegerToString(idx));
         ObjectCreate(0, "sig_" + IntegerToString(idx), OBJ_ARROW_SELL, 0, time[idx], high[idx] + 5 * Point());
         ObjectSetInteger(0, "sig_" + IntegerToString(idx), OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, "sig_" + IntegerToString(idx), OBJPROP_WIDTH, 2);

         ObjectDelete(0, "sl_" + IntegerToString(idx));
         ObjectCreate(0, "sl_" + IntegerToString(idx), OBJ_TREND, 0, time[idx], sl, time[idx] + 86400, sl);
         ObjectSetInteger(0, "sl_" + IntegerToString(idx), OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, "sl_" + IntegerToString(idx), OBJPROP_STYLE, STYLE_DASH);

         ObjectDelete(0, "tp_" + IntegerToString(idx));
         ObjectCreate(0, "tp_" + IntegerToString(idx), OBJ_TREND, 0, time[idx], tp, time[idx] + 86400, tp);
         ObjectSetInteger(0, "tp_" + IntegerToString(idx), OBJPROP_COLOR, clrLime);
         ObjectSetInteger(0, "tp_" + IntegerToString(idx), OBJPROP_STYLE, STYLE_DASH);
      }

      // Label on last bar
      if (idx == rates_total - 1)
      {
         string lbl = "Buy Score: " + IntegerToString(buyScore) + "\nSell Score: " + IntegerToString(sellScore);
         ObjectDelete(0, "score_label");
         ObjectCreate(0, "score_label", OBJ_LABEL, 0, 0, 0);
         ObjectSetInteger(0, "score_label", OBJPROP_CORNER, CORNER_RIGHT_UPPER);
         ObjectSetInteger(0, "score_label", OBJPROP_XDISTANCE, 10);
         ObjectSetInteger(0, "score_label", OBJPROP_YDISTANCE, 50);
         ObjectSetString(0, "score_label", OBJPROP_TEXT, lbl);
         ObjectSetInteger(0, "score_label", OBJPROP_COLOR, clrWhite);
         ObjectSetInteger(0, "score_label", OBJPROP_FONTSIZE, 10);
      }
   }

   return rates_total;
}
//+------------------------------------------------------------------+
