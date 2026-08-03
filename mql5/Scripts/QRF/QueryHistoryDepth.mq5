//+------------------------------------------------------------------+
//| QueryHistoryDepth.mq5                                             |
//| S07: a capability query ONLY -- reports the earliest available    |
//| M5 bar's timestamp for the pinned symbol via                      |
//| SeriesInfoInteger(SERIES_FIRSTDATE), which never copies a single   |
//| price bar. No CopyRates call exists in this script. Used to        |
//| decide whether untouched pre-2024 M5 history exists AT ALL,        |
//| before choosing a data path -- a question about the terminal,     |
//| never a look at market data.                                      |
//+------------------------------------------------------------------+
#property strict

#define PINNED_SYMBOL "XAUUSD"

void OnStart()
{
   string requested = _Symbol;
   if(requested != PINNED_SYMBOL)
   {
      Print("QRF_QUERY_REFUSED symbol=", requested, " pinned=", PINNED_SYMBOL);
      return;
   }

   datetime first = (datetime)SeriesInfoInteger(_Symbol, _Period, SERIES_FIRSTDATE);
   if(first <= 0)
   {
      Print("QRF_QUERY_REFUSED SERIES_FIRSTDATE unavailable, error=", GetLastError());
      return;
   }

   if(!FolderCreate("QRF"))
   {
      int err = GetLastError();
      if(err != 0 && err != 4200)
         Print("QRF_QUERY_WARN FolderCreate error=", err);
   }

   int h = FileOpen("QRF\\history_depth.txt", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE)
   {
      Print("QRF_QUERY_REFUSED cannot open output, error=", GetLastError());
      return;
   }
   FileWrite(h, IntegerToString((long)first));
   FileClose(h);

   Print("QRF_QUERY_OK first_m5_bar_epoch=", (long)first);
}
