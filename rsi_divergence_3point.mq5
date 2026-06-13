//+------------------------------------------------------------------+
//|                                      RSI_Divergence_3Point.mq5   |
//|               RSI Divergence (3-Point Heuristic) for MT5          |
//+------------------------------------------------------------------+
#property copyright "RSI Divergence 3-Point"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

input int      RsiPeriod      = 14;      // RSI Period
input int      LookbackStep   = 3;       // Step between samples
input int      SampleRange    = 10;      // Total range to sample (bars)
input bool     DrawLines      = true;    // Draw divergence lines
input color    BullColor      = clrLimeGreen;  // Bullish line color
input color    BearColor      = clrRed;        // Bearish line color
input int      LineWidth      = 2;       // Line width

int rsiHandle;
double rsiBuf[];

//+------------------------------------------------------------------+
//| Custom indicator initialization                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   rsiHandle = iRSI(NULL, 0, RsiPeriod, PRICE_CLOSE);
   if (rsiHandle == INVALID_HANDLE)
   {
      Print("Failed to create RSI handle");
      return INIT_FAILED;
   }

   ArraySetAsSeries(rsiBuf, true);
   IndicatorSetString(INDICATOR_SHORTNAME, "RSI_Div_3Pt");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Deinitialization                                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "RSIDiv_");
}

//+------------------------------------------------------------------+
//| Iteration                                                         |
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
   if (rates_total < RsiPeriod + SampleRange + 1)
      return rates_total;

   ArraySetAsSeries(time, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);

   int start = prev_calculated > 0 ? prev_calculated - 1 : 1;
   if (start < SampleRange)
      start = SampleRange;

   int copied = CopyBuffer(rsiHandle, 0, 0, rates_total, rsiBuf);
   if (copied != rates_total)
      return rates_total;

   for (int i = start; i < rates_total; i++)
   {
      int idx2 = i - 4;
      int idx3 = i - 1;

      if (idx2 < 0 || idx3 < 0)
         continue;

      double p2 = low[idx2];
      double p3 = low[idx3];
      double r2 = rsiBuf[idx2];
      double r3 = rsiBuf[idx3];

      string prefix = "RSIDiv_" + IntegerToString(i) + "_";

      if (p2 > p3 && r2 < r3)
      {
         if (DrawLines)
         {
            DrawDivLine(prefix + "Price", time[idx2], p2, time[idx3], p3, BullColor);
            DrawDivLine(prefix + "RSI",   time[idx2], r2, time[idx3], r3, BullColor);
            DrawLabel(prefix + "Label", time[idx3], p3, "Bull Div", BullColor);
         }
      }
      else if (p2 < p3 && r2 > r3)
      {
         if (DrawLines)
         {
            DrawDivLine(prefix + "Price", time[idx2], p2, time[idx3], p3, BearColor);
            DrawDivLine(prefix + "RSI",   time[idx2], r2, time[idx3], r3, BearColor);
            DrawLabel(prefix + "Label", time[idx3], p3, "Bear Div", BearColor);
         }
      }
   }

   return rates_total;
}

//+------------------------------------------------------------------+
void DrawDivLine(const string name, datetime t1, double p1, datetime t2, double p2, color clr)
{
   ObjectCreate(0, name, OBJ_TREND, 0, t1, p1, t2, p2);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, LineWidth);
   ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, name, OBJPROP_BACK, true);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT, false);
}

//+------------------------------------------------------------------+
void DrawLabel(const string name, datetime t, double price, string text, color clr)
{
   ObjectCreate(0, name, OBJ_LABEL, 0, t, price);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 10);
   ObjectSetString(0, name, OBJPROP_FONT, "Arial");
   ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_BOTTOM);
}
//+------------------------------------------------------------------+
