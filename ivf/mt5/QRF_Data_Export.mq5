//+------------------------------------------------------------------+
//| QRF_Data_Export.mq5 — ingest-format bar export + provenance (rev 1)|
//| ARCH-009 §4 data-acquisition tool (Architect-owned, ivf/mt5/).   |
//| Purpose: export H1 bars from ANY MT5 terminal (primary 2025      |
//| extension; SECOND independent feed) in the EXACT CSV format the  |
//| QRF ingest already consumes (XAUUSD_H1_2024_FULL.csv layout):    |
//|   time_open_sec,time_close_sec,open,high,low,close,rsi14,dow     |
//| (dow 0=Sun..6=Sat of the bar OPEN time; times are SERVER epoch   |
//| seconds — see the provenance sidecar for the server-vs-GMT       |
//| offset, which MUST be declared to the ingest if nonzero).        |
//|                                                                  |
//| Alongside the CSV it writes <name>.provenance.txt: broker        |
//| company, account server, symbol description/path, digits, the    |
//| CURRENT server-vs-GMT offset, export range, bar count, first/    |
//| last bars, and a gap census — the raw material for the Owner's   |
//| independence-tier declaration (ARCH-009 §4 Decision 1) and for   |
//| the Developer's ingest params.                                   |
//|                                                                  |
//| HISTORY ROBUSTNESS: a freshly-installed terminal serves partial  |
//| history until the download completes; this script retries        |
//| CopyRates with waits and REFUSES to write a silently-truncated   |
//| export (loud INCOMPLETE verdict instead).                        |
//| Run as SCRIPT on any chart of the target terminal.               |
//+------------------------------------------------------------------+
#property copyright "QRF"
#property version   "1.00"
#property script_show_inputs

input string          InpSymbol   = "";                   // empty = current chart symbol
input ENUM_TIMEFRAMES InpTF       = PERIOD_H1;
input datetime        InpFrom     = D'2024.01.01 00:00';  // server time
input datetime        InpTo       = D'2026.01.01 00:00';  // server time (exclusive-ish)
input int             InpRSIPeriod= 14;
input string          InpTag      = "";                   // optional filename tag, e.g. "secondfeed"
input int             InpMaxTries = 12;                   // history-download retries
input int             InpWaitMs   = 3000;                 // wait between retries

string FilesPath() { return TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\"; }

int DowOf(datetime t)
  {
   MqlDateTime s;
   TimeToStruct(t, s);
   return s.day_of_week; // 0=Sunday .. 6=Saturday
  }

string D8(double v) { return DoubleToString(v, 8); }

void OnStart()
  {
   string sym = (StringLen(InpSymbol) > 0) ? InpSymbol : _Symbol;
   if(!SymbolSelect(sym, true))
     { PrintFormat("QRF_Data_Export: symbol %s not found on this terminal.", sym); return; }

   // ---- history download with retries (never a silent truncation) ----
   MqlRates rates[];
   int n = 0;
   datetime slack = 7 * 86400; // first bar may legitimately start a few days late (holidays)
   for(int attempt = 1; attempt <= InpMaxTries; attempt++)
     {
      n = CopyRates(sym, InpTF, InpFrom, InpTo, rates);
      if(n > 0)
        {
         ArraySetAsSeries(rates, false);
         if(rates[0].time <= InpFrom + slack) break; // history reaches the start
        }
      PrintFormat("QRF_Data_Export: history attempt %d/%d — %s "
                  "(have %d bars%s); waiting %dms for download…",
                  attempt, InpMaxTries,
                  n <= 0 ? "no data yet" : "range incomplete",
                  MathMax(n, 0),
                  n > 0 ? StringFormat(", first %s",
                          TimeToString(rates[0].time, TIME_DATE|TIME_MINUTES)) : "",
                  InpWaitMs);
      Sleep(InpWaitMs);
     }
   if(n <= 0)
     { PrintFormat("QRF_Data_Export: FAILED — no bars for %s after %d tries "
                   "(err %d). Open a %s chart, let history load, run again.",
                   sym, InpMaxTries, GetLastError(), sym); return; }
   ArraySetAsSeries(rates, false);
   bool complete = (rates[0].time <= InpFrom + slack);

   // ---- RSI from THIS terminal's own arithmetic ----
   int hRSI = iRSI(sym, InpTF, InpRSIPeriod, PRICE_CLOSE);
   if(hRSI == INVALID_HANDLE){ Print("QRF_Data_Export: iRSI failed"); return; }
   double rsi[];
   int m = -1;
   for(int attempt = 1; attempt <= InpMaxTries && m <= 0; attempt++)
     {
      m = CopyBuffer(hRSI, 0, InpFrom, InpTo, rsi);
      if(m <= 0) Sleep(InpWaitMs);
     }
   if(m <= 0){ PrintFormat("QRF_Data_Export: CopyBuffer failed (err %d)", GetLastError()); return; }
   ArraySetAsSeries(rsi, false);

   // ---- filenames ----
   string tf = EnumToString(InpTF);           // e.g. PERIOD_H1
   string from_s = TimeToString(InpFrom, TIME_DATE);
   string to_s   = TimeToString(InpTo,   TIME_DATE);
   StringReplace(from_s, ".", ""); StringReplace(to_s, ".", "");
   string tag = (StringLen(InpTag) > 0) ? ("_" + InpTag) : "";
   string base = StringFormat("QRF_%s_%s_%s_%s%s", sym, tf, from_s, to_s, tag);
   string csv_name  = base + ".csv";
   string prov_name = base + ".provenance.txt";

   // ---- CSV (EXACT ingest layout) ----
   int fh = FileOpen(csv_name, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(fh == INVALID_HANDLE){ PrintFormat("QRF_Data_Export: FileOpen failed (err %d)", GetLastError()); return; }
   FileWrite(fh, "time_open_sec","time_close_sec","open","high","low","close",
                 StringFormat("rsi%d", InpRSIPeriod), "dow");
   int per = PeriodSeconds(InpTF);
   int off = m - n; if(off < 0) off = 0;      // defensive buffer alignment
   int gaps = 0; long max_gap = 0; datetime max_gap_at = 0;
   for(int i = 0; i < n; i++)
     {
      if(i > 0)
        {
         long dt = (long)rates[i].time - (long)rates[i-1].time;
         if(dt > per)
           {
            gaps++;
            if(dt > max_gap){ max_gap = dt; max_gap_at = rates[i-1].time; }
           }
        }
      double r = (i + off < m) ? rsi[i + off] : EMPTY_VALUE;
      FileWrite(fh,
        (long)rates[i].time,
        (long)rates[i].time + per,
        D8(rates[i].open), D8(rates[i].high), D8(rates[i].low), D8(rates[i].close),
        (r == EMPTY_VALUE ? "" : DoubleToString(r, 6)),
        DowOf(rates[i].time));
     }
   FileClose(fh);

   // ---- provenance sidecar (the independence-tier raw material) ----
   long srv_gmt_off = (long)TimeTradeServer() - (long)TimeGMT(); // CURRENT offset, seconds
   int ph = FileOpen(prov_name, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(ph != INVALID_HANDLE)
     {
      FileWriteString(ph, "QRF data export provenance (rev 1)\r\n");
      FileWriteString(ph, StringFormat("exported_utc: %s\r\n",
                      TimeToString(TimeGMT(), TIME_DATE|TIME_MINUTES|TIME_SECONDS)));
      FileWriteString(ph, StringFormat("terminal_company: %s\r\n", TerminalInfoString(TERMINAL_COMPANY)));
      FileWriteString(ph, StringFormat("terminal_name: %s\r\n", TerminalInfoString(TERMINAL_NAME)));
      FileWriteString(ph, StringFormat("account_server: %s\r\n", AccountInfoString(ACCOUNT_SERVER)));
      FileWriteString(ph, StringFormat("account_company: %s\r\n", AccountInfoString(ACCOUNT_COMPANY)));
      FileWriteString(ph, StringFormat("symbol: %s\r\n", sym));
      FileWriteString(ph, StringFormat("symbol_description: %s\r\n", SymbolInfoString(sym, SYMBOL_DESCRIPTION)));
      FileWriteString(ph, StringFormat("symbol_path: %s\r\n", SymbolInfoString(sym, SYMBOL_PATH)));
      FileWriteString(ph, StringFormat("digits: %d\r\n", (int)SymbolInfoInteger(sym, SYMBOL_DIGITS)));
      FileWriteString(ph, StringFormat("timeframe: %s (%d s)\r\n", tf, per));
      FileWriteString(ph, StringFormat("requested_range_server_time: %s .. %s\r\n",
                      TimeToString(InpFrom, TIME_DATE|TIME_MINUTES),
                      TimeToString(InpTo, TIME_DATE|TIME_MINUTES)));
      FileWriteString(ph, StringFormat("server_vs_gmt_offset_seconds_NOW: %d\r\n", (int)srv_gmt_off));
      FileWriteString(ph, "NOTE: offset is measured NOW; DST-era offsets in history may differ.\r\n");
      FileWriteString(ph, StringFormat("bars_written: %d\r\n", n));
      FileWriteString(ph, StringFormat("first_bar_open_server: %s (epoch %d)\r\n",
                      TimeToString(rates[0].time, TIME_DATE|TIME_MINUTES), (long)rates[0].time));
      FileWriteString(ph, StringFormat("last_bar_open_server: %s (epoch %d)\r\n",
                      TimeToString(rates[n-1].time, TIME_DATE|TIME_MINUTES), (long)rates[n-1].time));
      FileWriteString(ph, StringFormat("gaps_gt_1_period: %d\r\n", gaps));
      FileWriteString(ph, StringFormat("max_gap_seconds: %d (after bar %s)\r\n",
                      (int)max_gap, max_gap_at > 0 ? TimeToString(max_gap_at, TIME_DATE|TIME_MINUTES) : "n/a"));
      FileWriteString(ph, StringFormat("history_complete_vs_request: %s\r\n", complete ? "YES" : "NO — INCOMPLETE"));
      FileWriteString(ph, "owner_provenance_statement: (Owner fills: where does this feed's price come from?)\r\n");
      FileWriteString(ph, "declared_independence_tier: (Owner fills: broker | lp | venue | unknown)\r\n");
      FileClose(ph);
     }

   PrintFormat("QRF_Data_Export: %d bars -> %s%s", n, FilesPath(), csv_name);
   PrintFormat("QRF_Data_Export: provenance -> %s%s", FilesPath(), prov_name);
   PrintFormat("QRF_Data_Export: server-vs-GMT offset NOW = %d s%s", (int)srv_gmt_off,
               srv_gmt_off == 0 ? " (UTC-aligned)" :
               " — *** NOT UTC: declare this to the ingest ***");
   if(gaps > 0)
      PrintFormat("QRF_Data_Export: %d gaps > 1 period; largest %d s after %s "
                  "(weekend/holiday gaps are normal)", gaps, (int)max_gap,
                  TimeToString(max_gap_at, TIME_DATE|TIME_MINUTES));
   if(!complete)
      PrintFormat("QRF_Data_Export: *** INCOMPLETE *** first bar %s is after the "
                  "requested start — history did not fully download. Re-run after "
                  "the terminal finishes syncing; do NOT ingest this file.",
                  TimeToString(rates[0].time, TIME_DATE|TIME_MINUTES));
   else
      Print("QRF_Data_Export: COMPLETE vs requested range.");
  }
//+------------------------------------------------------------------+
