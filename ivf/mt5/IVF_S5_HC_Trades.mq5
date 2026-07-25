//+------------------------------------------------------------------+
//| IVF_S5_HC_Trades.mq5 — engine trade evidence capture (rev 1)     |
//| ADR-009 tool, generation 3. All S3/S4 lessons baked in: file     |
//| input, absolute paths, verified navigation, ALIGN_LEFT capture,  |
//| provenance caption, short caption lines, offset can only fail    |
//| loudly. New: chart-side NO-LOOK-AHEAD verification — the entry   |
//| price must equal the entry bar's OPEN in MT5's OWN series.       |
//|                                                                  |
//| INPUT FILE (MQL5\Files\HC_S5_input.txt) — two lines from         |
//| ivf/human/sample_s5_trades.py:                                   |
//|   line 1: PROV|dataset=...|manifest=...|hold=...|seed=...        |
//|   line 2: "entry_time|exit_time|dir|entry|exit|gross|net;..."    |
//|            (times are the bars' CLOSE ts in UTC; open = -1h)     |
//| Run as SCRIPT on the XAUUSD H1 chart.                            |
//+------------------------------------------------------------------+
#property copyright "QRF IVF"
#property version   "1.00"
#property script_show_inputs

input string InpFile           = "HC_S5_input.txt";
input int    InpUtcOffsetHours = 0;      // server = UTC + offset (0 verified)
input double InpTol            = 0.005;  // price match tolerance

string FilesPath() { return TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\"; }

void OnStart()
  {
   PrintFormat("HC-S5 rev1. Files folder (absolute): %s", FilesPath());
   if(_Period != PERIOD_H1)
     { Print("HC-S5: run this on an H1 chart. Aborting."); return; }

   int h = FileOpen(InpFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE)
     {
      int w = FileOpen(InpFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
      if(w != INVALID_HANDLE) { FileWriteString(w, ""); FileClose(w); }
      PrintFormat("HC-S5: created empty %s%s — paste the sampler's TWO lines "
                  "and run again.", FilesPath(), InpFile);
      return;
     }
   string prov = FileReadString(h);
   string line = FileReadString(h);
   FileClose(h);
   StringTrimLeft(prov); StringTrimRight(prov);
   StringTrimLeft(line); StringTrimRight(line);
   if(StringFind(prov, "PROV|") != 0 || StringLen(line) == 0)
     { Print("HC-S5: input must be PROV line then entries line."); return; }
   PrintFormat("HC-S5: provenance: %s", prov);

   ChartSetInteger(0, CHART_AUTOSCROLL, false);
   string entries[];
   int n = StringSplit(line, ';', entries);
   PrintFormat("HC-S5: %d entr%s after split.", n, n == 1 ? "y" : "ies");
   int matched = 0, checked = 0;

   for(int i = 0; i < n; i++)
     {
      string f[];
      if(StringSplit(entries[i], '|', f) < 7)
        { PrintFormat("HC-S5: entry %d UNPARSED: '%s'", i, entries[i]); continue; }
      datetime e_close = StringToTime(f[0]) + InpUtcOffsetHours * 3600;
      datetime x_close = StringToTime(f[1]) + InpUtcOffsetHours * 3600;
      datetime e_open  = e_close - PeriodSeconds(PERIOD_H1);
      datetime x_open  = x_close - PeriodSeconds(PERIOD_H1);
      int dir      = (int)StringToInteger(f[2]);
      double entry = StringToDouble(f[3]);
      double exitp = StringToDouble(f[4]);

      int e_shift = iBarShift(_Symbol, PERIOD_H1, e_open, true);
      int x_shift = iBarShift(_Symbol, PERIOD_H1, x_open, true);
      if(e_shift < 0 || x_shift < 0)
        { PrintFormat("HC-S5: bar NOT FOUND for entry %s / exit %s — adjust "
                      "offset.", f[0], f[1]); continue; }

      // NO-LOOK-AHEAD verification from MT5's own series:
      double mt5_entry_open = iOpen(_Symbol, PERIOD_H1, e_shift);
      double mt5_exit_open  = iOpen(_Symbol, PERIOD_H1, x_shift);
      bool ok = MathAbs(mt5_entry_open - entry) <= InpTol
             && MathAbs(mt5_exit_open  - exitp) <= InpTol;
      checked++; if(ok) matched++;

      string tag = StringFormat("HC5_%d", (int)e_close);
      // entry arrow (up for long, down for short) + exit arrow + connector
      ObjectCreate(0, tag+"_e", dir > 0 ? OBJ_ARROW_BUY : OBJ_ARROW_SELL,
                   0, e_open, entry);
      ObjectCreate(0, tag+"_x", OBJ_ARROW_CHECK, 0, x_open, exitp);
      ObjectSetInteger(0, tag+"_x", OBJPROP_COLOR, clrDodgerBlue);
      ObjectCreate(0, tag+"_l", OBJ_TREND, 0, e_open, entry, x_open, exitp);
      ObjectSetInteger(0, tag+"_l", OBJPROP_COLOR, clrOrange);
      ObjectSetInteger(0, tag+"_l", OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, tag+"_l", OBJPROP_RAY_RIGHT, false);

      string cap1 = StringFormat("%s %s | entry %.2f exit %.2f",
                                 dir > 0 ? "LONG" : "SHORT", f[0],
                                 entry, exitp);
      string cap2 = StringFormat("gross %s net %s | MT5 opens %.2f/%.2f | %s",
                                 f[5], f[6], mt5_entry_open, mt5_exit_open,
                                 ok ? "MATCH" : "MISMATCH");
      color vcol = ok ? clrLime : clrRed;
      string caps[2]; caps[0] = cap1; caps[1] = cap2;
      for(int c = 0; c < 2; c++)
        {
         string ct = StringFormat("%s_t%d", tag, c);
         ObjectCreate(0, ct, OBJ_LABEL, 0, 0, 0);
         ObjectSetInteger(0, ct, OBJPROP_CORNER, CORNER_LEFT_UPPER);
         ObjectSetInteger(0, ct, OBJPROP_XDISTANCE, 10);
         ObjectSetInteger(0, ct, OBJPROP_YDISTANCE, 34 + 18 * c);
         ObjectSetString (0, ct, OBJPROP_TEXT, caps[c]);
         ObjectSetInteger(0, ct, OBJPROP_FONTSIZE, 10);
         ObjectSetInteger(0, ct, OBJPROP_COLOR, c == 1 ? vcol : clrWhite);
        }
      ObjectCreate(0, tag+"_t2", OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_XDISTANCE, 10);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_YDISTANCE, 70);
      ObjectSetString (0, tag+"_t2", OBJPROP_TEXT, prov);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_COLOR, clrSilver);

      int width_bars = (int)ChartGetInteger(0, CHART_WIDTH_IN_BARS);
      bool visible = false;
      for(int attempt = 0; attempt < 3 && !visible; attempt++)
        {
         ChartNavigate(0, CHART_END, -e_shift + width_bars/2);
         ChartRedraw();
         Sleep(1000);
         int first = (int)ChartGetInteger(0, CHART_FIRST_VISIBLE_BAR);
         visible = (e_shift <= first) && (e_shift > first - width_bars);
        }
      string fname = StringFormat("HC_S5_%d%s.png", (int)e_close,
                                  visible ? "" : "_NAVFAIL");
      int px_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
      int px_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 0)
               + (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 1);
      if(px_h <= 0) px_h = 800;
      if(!ChartScreenShot(0, fname, px_w, px_h, ALIGN_LEFT))
         PrintFormat("HC-S5: screenshot FAILED for %s (err %d)", f[0], GetLastError());
      else
         PrintFormat("HC-S5: %s -> %s%s (%s%s)", f[0], FilesPath(), fname,
                     ok ? "MATCH" : "MISMATCH",
                     visible ? "" : ", NAVFAIL — evidence INVALID");

      ObjectDelete(0, tag+"_t0"); ObjectDelete(0, tag+"_t1");
      ObjectDelete(0, tag+"_t2"); ObjectDelete(0, tag+"_e");
      ObjectDelete(0, tag+"_x"); ObjectDelete(0, tag+"_l");
     }
   ChartRedraw();
   PrintFormat("HC-S5 done: %d/%d MATCH (entry+exit at next-bar opens, "
               "MT5's own series). PNGs: %s", matched, checked, FilesPath());
  }
//+------------------------------------------------------------------+
