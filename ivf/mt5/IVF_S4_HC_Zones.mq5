//+------------------------------------------------------------------+
//| IVF_S4_HC_Zones.mq5 — SMC zone evidence capture (rev 1)          |
//| ADR-009 tool, generation 5 of the S3 line: file input, verified  |
//| navigation, ALIGN_LEFT capture, provenance caption, and a chart- |
//| side FVG recomputation (numbers decide, even inside the PNG).    |
//|                                                                  |
//| INPUT FILE (MQL5\Files\HC_S4_input.txt) — exactly two lines from |
//| ivf/human/sample_s4_zones.py:                                    |
//|   line 1: PROV|dataset=...|manifest=...|events=...|seed=...      |
//|   line 2: "yyyy.mm.dd hh:mm|event_type|zone_hi|zone_lo|dir;..."  |
//|            (time = event CLOSE ts in UTC; open = close - 1h)     |
//|                                                                  |
//| For smc.fvg.* the script RECOMPUTES the zone from its own bars   |
//| (bull: zone_lo=high[i-1], zone_hi=low[i+1]) and stamps MATCH /   |
//| MISMATCH. For other events (order_block): VISUAL-ONLY, honestly  |
//| labeled — their knowability is operational per DEVQ-010.         |
//| Screenshots: HC_S4_<epoch>.png in MQL5\Files (absolute path      |
//| printed). Run as SCRIPT on the XAUUSD H1 chart.                  |
//+------------------------------------------------------------------+
#property copyright "QRF IVF"
#property version   "1.00"
#property script_show_inputs

input string InpFile           = "HC_S4_input.txt"; // two-line input file
input int    InpUtcOffsetHours = 0;                 // server = UTC + offset (0 verified S3)
input double InpTol            = 0.005;             // zone match tolerance

string FilesPath() { return TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\"; }

void OnStart()
  {
   PrintFormat("HC-S4 rev1. Files folder (absolute): %s", FilesPath());
   if(_Period != PERIOD_H1)
     { Print("HC-S4: run this on an H1 chart. Aborting."); return; }

   int h = FileOpen(InpFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE)
     {
      int w = FileOpen(InpFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
      if(w != INVALID_HANDLE) { FileWriteString(w, ""); FileClose(w); }
      PrintFormat("HC-S4: created empty %s%s — paste the sampler's TWO "
                  "lines into it and run again.", FilesPath(), InpFile);
      return;
     }
   string prov = FileReadString(h);
   string bars = FileReadString(h);
   FileClose(h);
   StringTrimLeft(prov); StringTrimRight(prov);
   StringTrimLeft(bars); StringTrimRight(bars);
   if(StringFind(prov, "PROV|") != 0 || StringLen(bars) == 0)
     { Print("HC-S4: input file must have PROV line then entries line."); return; }
   PrintFormat("HC-S4: provenance: %s", prov);

   ChartSetInteger(0, CHART_AUTOSCROLL, false);
   string entries[];
   int n = StringSplit(bars, ';', entries);
   PrintFormat("HC-S4: %d entr%s after split.", n, n == 1 ? "y" : "ies");
   int matched = 0, checked = 0, visual = 0;

   for(int i = 0; i < n; i++)
     {
      string f[];
      if(StringSplit(entries[i], '|', f) < 5)
        { PrintFormat("HC-S4: entry %d UNPARSED: '%s'", i, entries[i]); continue; }
      datetime close_utc  = StringToTime(f[0]);
      datetime close_srv  = close_utc + InpUtcOffsetHours * 3600;
      datetime open_srv   = close_srv - PeriodSeconds(PERIOD_H1);
      string   etype      = f[1];
      double   zhi        = StringToDouble(f[2]);
      double   zlo        = StringToDouble(f[3]);

      int shift = iBarShift(_Symbol, PERIOD_H1, open_srv, true);
      if(shift < 0)
        { PrintFormat("HC-S4: bar NOT FOUND (server open %s) — adjust "
                      "InpUtcOffsetHours.", TimeToString(open_srv)); continue; }

      // chart-side recomputation for FVG only
      string verdict = "VISUAL-ONLY";
      color  vcol    = clrGoldenrod;
      bool   isFvg   = (StringFind(etype, "smc.fvg.") == 0);
      if(isFvg)
        {
         // event bar = i+1 of the 3-bar pattern; its shift is `shift`,
         // pattern bars: prev2 = shift+2 (i-1), this = shift (i+1)
         double myHi, myLo;
         if(StringFind(etype, ".bull") > 0)
           { myLo = iHigh(_Symbol, PERIOD_H1, shift + 2);
             myHi = iLow (_Symbol, PERIOD_H1, shift); }
         else
           { myHi = iLow (_Symbol, PERIOD_H1, shift + 2);
             myLo = iHigh(_Symbol, PERIOD_H1, shift); }
         bool ok = MathAbs(myHi - zhi) <= InpTol && MathAbs(myLo - zlo) <= InpTol;
         checked++; if(ok) matched++;
         verdict = ok ? "MATCH" : StringFormat("MISMATCH (chart [%.2f,%.2f])",
                                               myLo, myHi);
         vcol = ok ? clrLime : clrRed;
        }
      else visual++;

      string tag = StringFormat("HC4_%d", (int)close_utc);
      datetime rect_from = open_srv - 4 * PeriodSeconds(PERIOD_H1);
      datetime rect_to   = open_srv + 8 * PeriodSeconds(PERIOD_H1);
      ObjectCreate(0, tag+"_z", OBJ_RECTANGLE, 0, rect_from, zlo, rect_to, zhi);
      ObjectSetInteger(0, tag+"_z", OBJPROP_COLOR, clrOrange);
      ObjectSetInteger(0, tag+"_z", OBJPROP_FILL, false);
      ObjectSetInteger(0, tag+"_z", OBJPROP_WIDTH, 2);
      string cap1 = StringFormat("%s UTC(close) | %s | IVF zone [%.2f, %.2f] | %s",
                                 f[0], etype, zlo, zhi, verdict);
      ObjectCreate(0, tag+"_t1", OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_XDISTANCE, 10);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_YDISTANCE, 34);
      ObjectSetString (0, tag+"_t1", OBJPROP_TEXT, cap1);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_FONTSIZE, 10);
      ObjectSetInteger(0, tag+"_t1", OBJPROP_COLOR, vcol);
      ObjectCreate(0, tag+"_t2", OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_XDISTANCE, 10);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_YDISTANCE, 52);
      ObjectSetString (0, tag+"_t2", OBJPROP_TEXT, prov);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, tag+"_t2", OBJPROP_COLOR, clrSilver);

      int width_bars = (int)ChartGetInteger(0, CHART_WIDTH_IN_BARS);
      bool visible = false;
      for(int attempt = 0; attempt < 3 && !visible; attempt++)
        {
         ChartNavigate(0, CHART_END, -shift + width_bars/2);
         ChartRedraw();
         Sleep(1000);
         int first = (int)ChartGetInteger(0, CHART_FIRST_VISIBLE_BAR);
         visible = (shift <= first) && (shift > first - width_bars);
        }
      string fname = StringFormat("HC_S4_%d%s.png", (int)close_utc,
                                  visible ? "" : "_NAVFAIL");
      int px_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
      int px_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 0)
               + (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 1);
      if(px_h <= 0) px_h = 800;
      if(!ChartScreenShot(0, fname, px_w, px_h, ALIGN_LEFT))
         PrintFormat("HC-S4: screenshot FAILED for %s (err %d)", f[0], GetLastError());
      else
         PrintFormat("HC-S4: %s -> %s%s (%s%s)", f[0], FilesPath(), fname,
                     verdict, visible ? "" : ", NAVFAIL — evidence INVALID");
      ObjectDelete(0, tag+"_t1");
      ObjectDelete(0, tag+"_t2");
      ObjectDelete(0, tag+"_z");
     }
   ChartRedraw();
   PrintFormat("HC-S4 done: FVG %d/%d MATCH, %d visual-only. PNGs: %s",
               matched, checked, visual, FilesPath());
  }
//+------------------------------------------------------------------+
