//+------------------------------------------------------------------+
//| IVF_S3_HC_Screenshot.mq5 — HC-S3 evidence capture (rev 4)        |
//| Architect-owned IVF tool. Run as a SCRIPT on the XAUUSD H1 chart.|
//|                                                                  |
//| rev 2: (a) bars can be read from a FILE — the terminal's input   |
//| dialog truncates long strings, which produced 0/0 on rev 1;      |
//| (b) the absolute Files path is printed at start and end;         |
//| (c) verbose per-entry parse logging — nothing fails silently.    |
//|                                                                  |
//| USAGE:                                                           |
//|  1. Run the script ONCE with defaults — it prints the absolute   |
//|     Files folder path and creates HC_S3_input.txt there if       |
//|     missing.                                                     |
//|  2. Put the sampler's --mql line (one line) into that file:      |
//|       uv run python ivf/human/sample_s3_bars.py --clean ...      |
//|           --mql                                                  |
//|     Entries: "yyyy.mm.dd hh:mm|O|H|L|C;..." (UTC open times).    |
//|  3. Run the script again. PNGs appear in the printed folder.     |
//|                                                                  |
//| TIME ZONES: chart times are SERVER time; IVF times are UTC. Set  |
//| InpUtcOffsetHours (try 0, then 2, then 3 if bars are NOT FOUND). |
//| A wrong offset can only fail loudly — never a false MATCH.       |
//+------------------------------------------------------------------+
#property copyright "QRF IVF"
#property version   "4.00"
#property script_show_inputs

input string InpBars           = "";               // bars inline (optional; file preferred)
input string InpFile           = "HC_S3_input.txt";// bars file in MQL5\Files
input int    InpUtcOffsetHours = 0;                // server = UTC + offset
input double InpTol            = 0.005;            // match tolerance
// rev 3: screenshots capture the ACTUAL visible window at its true pixel
// size — no width/height inputs, no alignment guessing; and navigation is
// VERIFIED before capture (rev 2 shot the chart end while claiming Jan-2024).

string FilesPath() { return TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\"; }

string LoadBars()
  {
   if(StringLen(InpBars) > 0)
     { PrintFormat("HC-S3: using inline InpBars (%d chars).", StringLen(InpBars));
       return InpBars; }
   int h = FileOpen(InpFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE)
     {
      int w = FileOpen(InpFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
      if(w != INVALID_HANDLE) { FileWriteString(w, ""); FileClose(w); }
      PrintFormat("HC-S3: created empty %s%s — paste the sampler's --mql line "
                  "into it (one line) and run again.", FilesPath(), InpFile);
      return "";
     }
   string s = "";
   while(!FileIsEnding(h)) s += FileReadString(h);
   FileClose(h);
   StringTrimLeft(s); StringTrimRight(s);
   PrintFormat("HC-S3: read %d chars from %s%s", StringLen(s), FilesPath(), InpFile);
   return s;
  }

void OnStart()
  {
   PrintFormat("HC-S3 rev2. Files folder (absolute): %s", FilesPath());
   if(_Period != PERIOD_H1)
     { Print("HC-S3: run this on an H1 chart. Aborting."); return; }

   string bars = LoadBars();
   if(StringLen(bars) == 0)
     { Print("HC-S3: no bar entries — nothing to do."); return; }

   ChartSetInteger(0, CHART_AUTOSCROLL, false);

   string entries[];
   int n = StringSplit(bars, ';', entries);
   PrintFormat("HC-S3: %d entr%s after split.", n, n == 1 ? "y" : "ies");
   int matched = 0, checked = 0;

   for(int i = 0; i < n; i++)
     {
      string raw = entries[i];
      StringTrimLeft(raw); StringTrimRight(raw);
      if(StringLen(raw) == 0) continue;
      string f[];
      int nf = StringSplit(raw, '|', f);
      if(nf < 5)
        { PrintFormat("HC-S3: entry %d UNPARSED (%d fields): '%s'", i, nf, raw);
          continue; }
      datetime t_utc    = StringToTime(f[0]);
      datetime t_server = t_utc + InpUtcOffsetHours * 3600;
      PrintFormat("HC-S3: entry %d: %s UTC -> server %s",
                  i, f[0], TimeToString(t_server));

      int shift = iBarShift(_Symbol, PERIOD_H1, t_server, true);
      if(shift < 0)
        { PrintFormat("HC-S3: bar NOT FOUND at server %s — adjust "
                      "InpUtcOffsetHours (try 2 or 3).",
                      TimeToString(t_server)); continue; }

      double o = iOpen (_Symbol, PERIOD_H1, shift);
      double h = iHigh (_Symbol, PERIOD_H1, shift);
      double l = iLow  (_Symbol, PERIOD_H1, shift);
      double c = iClose(_Symbol, PERIOD_H1, shift);

      bool ok = MathAbs(o - StringToDouble(f[1])) <= InpTol
             && MathAbs(h - StringToDouble(f[2])) <= InpTol
             && MathAbs(l - StringToDouble(f[3])) <= InpTol
             && MathAbs(c - StringToDouble(f[4])) <= InpTol;
      checked++; if(ok) matched++;

      string cap1 = StringFormat("%s UTC | IVF: O=%s H=%s L=%s C=%s",
                                 f[0], f[1], f[2], f[3], f[4]);
      string cap2 = StringFormat("MT5: O=%.2f H=%.2f L=%.2f C=%.2f | %s",
                                 o, h, l, c, ok ? "MATCH" : "MISMATCH");

      string tag = StringFormat("HC_%d", (int)t_utc);
      ObjectCreate(0, tag+"_v", OBJ_VLINE, 0, t_server, 0);
      ObjectSetInteger(0, tag+"_v", OBJPROP_COLOR, clrOrange);
      ObjectSetInteger(0, tag+"_v", OBJPROP_WIDTH, 2);
      ObjectCreate(0, tag+"_t1", OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_XDISTANCE, 10);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_YDISTANCE, 30);
      ObjectSetString (0, tag+"_t1", OBJPROP_TEXT, cap1);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_FONTSIZE, 10);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_COLOR, clrWhite);
      ObjectCreate(0, tag+"_t2", OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_XDISTANCE, 10);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_YDISTANCE, 50);
      ObjectSetString (0, tag+"_t2", OBJPROP_TEXT, cap2);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_FONTSIZE, 10);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_COLOR, ok ? clrLime : clrRed);

      // navigate so the bar is centered — then VERIFY it is on screen
      int width_bars = (int)ChartGetInteger(0, CHART_WIDTH_IN_BARS);
      bool visible = false;
      for(int attempt = 0; attempt < 3 && !visible; attempt++)
        {
         ChartNavigate(0, CHART_END, -shift + width_bars/2);
         ChartRedraw();
         Sleep(1000);
         int first = (int)ChartGetInteger(0, CHART_FIRST_VISIBLE_BAR);
         visible = (shift <= first) && (shift > first - width_bars);
         PrintFormat("HC-S3: nav attempt %d: first_visible=%d target_shift=%d "
                     "width=%d -> %s", attempt+1, first, shift, width_bars,
                     visible ? "ON SCREEN" : "off screen");
        }

      string fname = StringFormat("HC_S3_%d%s.png", (int)t_utc,
                                  visible ? "" : "_NAVFAIL");
      int px_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
      int px_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 0)
               + (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 1);
      if(px_h <= 0) px_h = 800;
      // rev 4: ALIGN_LEFT — anchors the capture at the FIRST VISIBLE bar
      // (the navigated view). ALIGN_RIGHT re-renders from the newest data
      // and produced July-2026 PNGs while the screen showed Jan-2024.
      if(!ChartScreenShot(0, fname, px_w, px_h, ALIGN_LEFT))
         PrintFormat("HC-S3: screenshot FAILED for %s (err %d)", f[0], GetLastError());
      else
         PrintFormat("HC-S3: %s -> %s%s (%s%s)",
                     f[0], FilesPath(), fname, ok ? "MATCH" : "MISMATCH",
                     visible ? "" : ", NAVFAIL — evidence INVALID, rerun");

      ObjectDelete(0, tag+"_t1");
      ObjectDelete(0, tag+"_t2");
      ObjectDelete(0, tag+"_v");
     }
   ChartRedraw();
   PrintFormat("HC-S3 done: %d/%d MATCH. PNGs (absolute): %s", matched, checked,
               FilesPath());
  }
//+------------------------------------------------------------------+
