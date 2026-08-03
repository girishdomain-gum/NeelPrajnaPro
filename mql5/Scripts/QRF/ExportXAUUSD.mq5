//+------------------------------------------------------------------+
//| ExportXAUUSD.mq5                                                  |
//| S03 observation exporter — writes recent XAUUSD bars plus their   |
//| provenance metadata to MQL5\Files\QRF\, for a Python harvester    |
//| to pick up after the terminal self-closes (ShutdownTerminal=1).   |
//|                                                                   |
//| Design after F:\Fable's launch/harvest pattern (a script run via  |
//| /config [StartUp], never a live IPC session) — re-implemented for |
//| this project's own exact-symbol pin (A-007 Owner order O-008),    |
//| never copied. Refuses outright on any symbol but an EXACT match.  |
//+------------------------------------------------------------------+
#property strict
#property script_show_inputs

input int InpBarCount = 5000; // lookback, most-recent-N bars by default

// S07 Phase 1B: optional historical cutoff. If MQL5\Files\QRF\
// export_end_time.txt exists (one line: a unix epoch second), the export
// requests InpBarCount bars ENDING at that historical time instead of
// "most recent" -- staged the same way Fable's own hc_capture job stages
// its input file into the terminal's own MQL5\Files before launch.

#define PINNED_SYMBOL "XAUUSD"

string PeriodName(ENUM_TIMEFRAMES p)
{
   switch(p)
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
      case PERIOD_W1:  return "W1";
      case PERIOD_MN1: return "MN1";
      default:         return IntegerToString((int)p);
   }
}

void OnStart()
{
   string requested = _Symbol;
   if(requested != PINNED_SYMBOL)
   {
      Print("QRF_EXPORT_REFUSED symbol=", requested, " pinned=", PINNED_SYMBOL);
      return;
   }

   int start_shift = 0;
   bool historical = false;
   long end_time_epoch = 0;
   int bar_count = InpBarCount;
   string range_file = "QRF\\export_end_time.txt";
   if(FileIsExist(range_file))
   {
      int rf = FileOpen(range_file, FILE_READ|FILE_TXT|FILE_ANSI);
      if(rf != INVALID_HANDLE)
      {
         string line1 = FileReadString(rf);
         string line2 = "";
         if(!FileIsEnding(rf))
            line2 = FileReadString(rf);
         FileClose(rf);
         end_time_epoch = (long)StringToInteger(line1);
         int staged_count = (int)StringToInteger(line2);
         if(staged_count > 0)
            bar_count = staged_count;
         if(end_time_epoch > 0)
         {
            start_shift = iBarShift(_Symbol, _Period, (datetime)end_time_epoch, false);
            if(start_shift < 0)
            {
               Print("QRF_EXPORT_REFUSED iBarShift failed for end_time=", end_time_epoch,
                     " error=", GetLastError());
               return;
            }
            historical = true;
         }
      }
   }

   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int copied = CopyRates(_Symbol, _Period, start_shift, bar_count, rates);
   if(copied <= 0)
   {
      Print("QRF_EXPORT_REFUSED no rates copied, error=", GetLastError());
      return;
   }

   if(!FolderCreate("QRF"))
   {
      int err = GetLastError();
      if(err != 0 && err != 4200) // 4200 = ERR_DIRECTORY_ALREADY_EXISTS-ish; folder may pre-exist
         Print("QRF_EXPORT_WARN FolderCreate error=", err);
   }

   string csv_name  = "QRF\\xauusd_export.csv";
   string meta_name = "QRF\\xauusd_export.meta.json";

   int csv_handle = FileOpen(csv_name, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(csv_handle == INVALID_HANDLE)
   {
      Print("QRF_EXPORT_REFUSED cannot open csv, error=", GetLastError());
      return;
   }
   FileWrite(csv_handle, "time,open,high,low,close,tick_volume,spread,real_volume");
   for(int i = 0; i < copied; i++)
   {
      FileWrite(csv_handle,
         IntegerToString((long)rates[i].time) + "," +
         DoubleToString(rates[i].open, 8) + "," +
         DoubleToString(rates[i].high, 8) + "," +
         DoubleToString(rates[i].low, 8) + "," +
         DoubleToString(rates[i].close, 8) + "," +
         IntegerToString(rates[i].tick_volume) + "," +
         IntegerToString(rates[i].spread) + "," +
         IntegerToString((long)rates[i].real_volume));
   }
   FileClose(csv_handle);

   long   digits      = SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point       = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double tick_size   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   long   account     = AccountInfoInteger(ACCOUNT_LOGIN);
   string server      = AccountInfoString(ACCOUNT_SERVER);
   string company     = AccountInfoString(ACCOUNT_COMPANY);
   long   build       = TerminalInfoInteger(TERMINAL_BUILD);
   long   server_time = (long)TimeCurrent();
   long   local_time  = (long)TimeLocal();

   int meta_handle = FileOpen(meta_name, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(meta_handle == INVALID_HANDLE)
   {
      Print("QRF_EXPORT_REFUSED cannot open meta, error=", GetLastError());
      return;
   }
   FileWrite(meta_handle, "{");
   FileWrite(meta_handle, "\"symbol\": \"" + _Symbol + "\",");
   FileWrite(meta_handle, "\"timeframe\": \"" + PeriodName(_Period) + "\",");
   FileWrite(meta_handle, "\"broker\": \"" + company + "\",");
   FileWrite(meta_handle, "\"server\": \"" + server + "\",");
   FileWrite(meta_handle, "\"account\": " + IntegerToString(account) + ",");
   FileWrite(meta_handle, "\"terminal_build\": " + IntegerToString(build) + ",");
   FileWrite(meta_handle, "\"digits\": " + IntegerToString(digits) + ",");
   FileWrite(meta_handle, "\"point\": " + DoubleToString(point, 8) + ",");
   FileWrite(meta_handle, "\"trade_tick_size\": " + DoubleToString(tick_size, 8) + ",");
   FileWrite(meta_handle, "\"requested_bar_count\": " + IntegerToString(bar_count) + ",");
   FileWrite(meta_handle, "\"requested_end_utc_cutoff\": " +
             (historical ? IntegerToString(end_time_epoch) : "null") + ",");
   FileWrite(meta_handle, "\"row_count\": " + IntegerToString(copied) + ",");
   FileWrite(meta_handle, "\"returned_start_utc\": " + IntegerToString((long)rates[0].time) + ",");
   FileWrite(meta_handle, "\"returned_end_utc\": " + IntegerToString((long)rates[copied-1].time) + ",");
   FileWrite(meta_handle, "\"server_time_at_export\": " + IntegerToString(server_time) + ",");
   FileWrite(meta_handle, "\"local_time_at_export\": " + IntegerToString(local_time));
   FileWrite(meta_handle, "}");
   FileClose(meta_handle);

   Print("QRF_EXPORT_OK rows=", copied);
}
