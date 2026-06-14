//+------------------------------------------------------------------+
//|                                             HeuristicStrategy.mq5|
//|  Expert Advisor – synthetic technical indicators & heuristic signal|
//+------------------------------------------------------------------+
#property copyright   "OpenCode"
#property link        "https://github.com/your-repo"
#property version     "1.00"

#property strict

#include <Trade\Trade.mqh>
CTrade trade;

//==================================================================
// Input parameters
//==================================================================
input double   Lots            = 0.01;   // lot size per trade
input int      Slippage        = 5;      // max slippage (points)
input double   MaxSpread       = 5;      // max spread (points) to allow trading
input bool     UseTrailingStop = false;  // optional trailing stop (not used here)

//==================================================================
// Struct to hold the synthetic technical indicators
//==================================================================
struct TechnicalIndicators
{
   int    rsi;
   string macd;          // "bullish crossover", "bearish crossover", "neutral"
   double ma50;
   double ma200;
   double support[3];
   double resistance[3];
   string trend;         // "bullish", "bearish", "neutral"
};

//==================================================================
// Helper: round price like Python version
//==================================================================
double RoundPrice(double value)
{
   if(MathAbs(value)<10.0)
      return NormalizeDouble(value,4);
   return NormalizeDouble(value,0);
}

//==================================================================
// Helper: clamp integer
//==================================================================
int ClampInt(int value,int low,int high)
{
   if(value<low)  return low;
   if(value>high) return high;
   return value;
}

//==================================================================
// Compute 24‑hour percent change using daily candles
//==================================================================
double GetChange24h()
{
   // yesterday's close (daily timeframe)
   double close1 = iClose(_Symbol,PERIOD_D1,1);
   // today's close (most recent daily candle)
   double close0 = iClose(_Symbol,PERIOD_D1,0);
   if(close1==0) return 0.0;
   return ((close0-close1)/close1)*100.0;
}

//==================================================================
// Generate synthetic technical indicators
//==================================================================
TechnicalIndicators ParseTechnicalIndicators(double price,double change24h)
{
   TechnicalIndicators ti;

   // ----- RSI ----------------------------------------------------
   int rsi_raw = (int)MathRound(50.0 + change24h*1.5);
   ti.rsi = ClampInt(rsi_raw,15,85);

   // ----- MACD ---------------------------------------------------
   if(ti.rsi>60)      ti.macd = "bullish crossover";
   else if(ti.rsi<40) ti.macd = "bearish crossover";
   else               ti.macd = "neutral";

   // ----- Moving averages (synthetic) ----------------------------
   if(change24h>0.0)
   {
      ti.ma50  = price*0.97;
      ti.ma200 = price*0.92;
   }
   else
   {
      ti.ma50  = price*1.03;
      ti.ma200 = price*1.08;
   }

   // ----- Support / Resistance -----------------------------------
   double supp_f[3] = {0.95,0.90,0.85};
   double res_f[3]  = {1.04,1.08,1.15};

   for(int i=0;i<3;i++)
   {
      ti.support[i]    = RoundPrice(price*supp_f[i]);
      ti.resistance[i] = RoundPrice(price*res_f[i]);
   }

   // ----- Trend --------------------------------------------------
   if(change24h>2.0)      ti.trend = "bullish";
   else if(change24h<-2.0)ti.trend = "bearish";
   else                   ti.trend = "neutral";

   return ti;
}

//==================================================================
// Heuristic signal: 1 = buy, -1 = sell, 0 = hold
//==================================================================
int HeuristicSignal(const TechnicalIndicators &ti)
{
   // Use trend alone for signal: bullish => BUY, bearish => SELL, neutral => HOLD
   if(ti.trend=="bullish")
      return 1;
   if(ti.trend=="bearish")
      return -1;
   return 0;
}

//==================================================================
// Close all open positions of the current symbol
//==================================================================
void CloseAll()
{
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;

      double volume = PositionGetDouble(POSITION_VOLUME);
      trade.PositionClose(ticket);
   }
}

//==================================================================
// Main entry point – run on each new bar
//==================================================================
datetime lastBarTime=0;

void OnTick()
{
   //--- ensure spread is acceptable
   double spread = SymbolInfoDouble(_Symbol,(ENUM_SYMBOL_INFO_DOUBLE)SYMBOL_SPREAD);
   if(spread>MaxSpread*_Point) return;

   //--- work only on new bar
   datetime curBarTime = (Period()==0) ? TimeCurrent() : iTime(_Symbol,0,0);
   if(curBarTime==lastBarTime) return;
   lastBarTime = curBarTime;

   //--- current price (close of the just‑closed bar)
   double price = iClose(_Symbol,0,0);
   double change24h = GetChange24h();

   //--- generate indicators & signal
   TechnicalIndicators ti = ParseTechnicalIndicators(price,change24h);
   int sig = HeuristicSignal(ti);

   //--- keep track of existing positions
   bool haveLong  = false;
   bool haveShort = false;
   for(int i=0;i<PositionsTotal();i++)
   {
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)  haveLong  = true;
      if(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_SELL) haveShort = true;
   }

   //--- exit opposite positions first
   if(sig==1 && haveShort)  CloseAll();
   if(sig==-1 && haveLong)  CloseAll();

   //--- open new positions if signal is BUY/SELL and none exists
   if(sig==1 && !haveLong)
   {
      double sl = ti.support[0];
      double tp = ti.resistance[0];
      trade.SetExpertMagicNumber((ulong)123456);
      trade.Buy(Lots,_Symbol,0,sl,tp,Slippage);
   }
   else if(sig==-1 && !haveShort)
   {
      double sl = ti.resistance[0];
      double tp = ti.support[0];
      trade.SetExpertMagicNumber((ulong)123456);
      trade.Sell(Lots,_Symbol,0,sl,tp,Slippage);
   }

   //--- optional trailing stop placeholder
   // if(UseTrailingStop) { /* add trailing‑stop handling here */ }
}

//+------------------------------------------------------------------+
