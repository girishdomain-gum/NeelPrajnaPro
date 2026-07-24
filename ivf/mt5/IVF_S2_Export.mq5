//+------------------------------------------------------------------+
//| IVF_S2_Export.mq5 — independent bar + RSI + calendar export       |
//| IVF Sprint-2 reference tool (Verification Framework §3.1).        |
//| Deliberately primitive: export what the terminal itself computes, |
//| so the reference is MT5's own arithmetic, not ours.               |
//|                                                                   |
//| Output CSV (MQL5\Files\IVF_S2_<symbol>_<tf>.csv):                 |
//|   time_open_sec, time_close_sec, open, high, low, close,          |
//|   rsi<period>, dow_utc(0=Sun..6=Sat per TimeDayOfWeek of OPEN)    |
//| NOTE: MT5 bar 'time' is the OPEN time and is SERVER time. The     |
//| close time is derived as open + PeriodSeconds(). The Python check |
//| treats these times as the same timeline the qrf-side export uses; |
//| any server-vs-UTC offset must be identical on both sides (both    |
//| exports come from the same terminal data) so EXACT comparison of  |
//| event timestamps remains valid.                                   |
//+------------------------------------------------------------------+
#property script_show_inputs
input string   InpSymbol   = "XAUUSD";
input ENUM_TIMEFRAMES InpTF = PERIOD_H1;
input datetime InpFrom     = D'2024.01.01 00:00';
input datetime InpTo       = D'2024.02.01 00:00';
input int      InpRSIPeriod = 14;

void OnStart()
  {
   MqlRates rates[];
   int n = CopyRates(InpSymbol, InpTF, InpFrom, InpTo, rates);
   if(n <= 0){ Print("IVF_S2_Export: CopyRates failed: ", GetLastError()); return; }

   int hRSI = iRSI(InpSymbol, InpTF, InpRSIPeriod, PRICE_CLOSE);
   if(hRSI == INVALID_HANDLE){ Print("IVF_S2_Export: iRSI failed"); return; }
   double rsi[];
   if(CopyBuffer(hRSI, 0, 0, 0, rsi) <= 0)
     { // fall back: copy by time range
       if(CopyBuffer(hRSI, 0, InpFrom, InpTo, rsi) <= 0)
         { Print("IVF_S2_Export: CopyBuffer failed: ", GetLastError()); return; }
     }
   ArraySetAsSeries(rates, false);
   ArraySetAsSeries(rsi, false);

   string fname = StringFormat("IVF_S2_%s_%s.csv", InpSymbol, EnumToString(InpTF));
   int fh = FileOpen(fname, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(fh == INVALID_HANDLE){ Print("IVF_S2_Export: FileOpen failed: ", GetLastError()); return; }

   FileWrite(fh, "time_open_sec","time_close_sec","open","high","low","close",
                 StringFormat("rsi%d", InpRSIPeriod), "dow");
   int per = PeriodSeconds(InpTF);
   // Align: CopyBuffer over a range may not align 1:1 with rates when the
   // range differs; export defensively by recomputing RSI index offset.
   int off = ArraySize(rsi) - n; if(off < 0) off = 0;
   for(int i = 0; i < n; i++)
     {
      double r = (i + off < ArraySize(rsi)) ? rsi[i + off] : EMPTY_VALUE;
      FileWrite(fh,
        (long)rates[i].time,
        (long)rates[i].time + per,
        DoubleToString(rates[i].open, 8),
        DoubleToString(rates[i].high, 8),
        DoubleToString(rates[i].low, 8),
        DoubleToString(rates[i].close, 8),
        (r == EMPTY_VALUE ? "" : DoubleToString(r, 6)),
        (int)TimeDayOfWeek(rates[i].time));
     }
   FileClose(fh);
   PrintFormat("IVF_S2_Export: wrote %d bars to %s", n, fname);
  }
//+------------------------------------------------------------------+
