//+------------------------------------------------------------------+
//| IVF_HC_Trades.mq5 — sprint-agnostic trade evidence capture (rev 1)|
//| ADR-009 tool, generation 4. THE NAMING FIX (owed since S5's tool |
//| was reused for S7 and stamped HC_S4_* on the S7 evidence): this  |
//| tool has NO hardcoded sprint anywhere. The label comes from the  |
//| sampler's PROV line (label=HC_S<k>) and is stamped into every    |
//| caption, object tag, PNG filename and log line. If the PROV line |
//| carries no label the tool REFUSES to run — evidence can no       |
//| longer be captured under the wrong sprint's name.                |
//|                                                                  |
//| INPUT FILE (MQL5\Files\HC_input.txt) — two lines from an         |
//| ivf/human/sample_*.py sampler:                                   |
//|   line 1: PROV|label=HC_S8|verdicts=...|seed=...|sampler=...     |
//|   line 2: "entry_time|exit_time|dir|entry|exit|gross|net|note;.."|
//|            (times are the bars' CLOSE ts in UTC; open = -1h;     |
//|             note: FVG = plain capture, MON = additionally verify |
//|             the entry bar OPENS on a Monday — DEVQ-019 contract; |
//|             the exit day is CAPTIONED honestly, not asserted:    |
//|             on the real feed a 22-bar Monday hold exits in the   |
//|             early hours of Tuesday, see checklist_s8.md)         |
//|                                                                  |
//| Chart-side NO-LOOK-AHEAD verification as in generation 3: entry  |
//| and exit prices must equal their bars' OPENs in MT5's own series.|
//| Run as SCRIPT on the XAUUSD H1 chart.                            |
//+------------------------------------------------------------------+
#property copyright "QRF IVF"
#property version   "1.00"
#property script_show_inputs

input string InpFile           = "HC_input.txt";
input int    InpUtcOffsetHours = 0;      // server = UTC + offset (0 verified)
input double InpTol            = 0.005;  // price match tolerance

string FilesPath() { return TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\"; }

// day-of-week of a datetime: 0=Sunday .. 6=Saturday (MQL5 struct convention)
int DayOfWeekOf(datetime t)
  {
   MqlDateTime s;
   TimeToStruct(t, s);
   return s.day_of_week;
  }

// extract "label=..." from the PROV line; empty string if absent
string LabelOf(string prov)
  {
   int p = StringFind(prov, "label=");
   if(p < 0) return "";
   int from = p + 6;
   int to = StringFind(prov, "|", from);
   if(to < 0) to = StringLen(prov);
   return StringSubstr(prov, from, to - from);
  }

void OnStart()
  {
   PrintFormat("HC rev1 (generation 4, label-driven). Files folder: %s",
               FilesPath());
   if(_Period != PERIOD_H1)
     { Print("HC: run this on an H1 chart. Aborting."); return; }

   int h = FileOpen(InpFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE)
     {
      int w = FileOpen(InpFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
      if(w != INVALID_HANDLE) { FileWriteString(w, ""); FileClose(w); }
      PrintFormat("HC: created empty %s%s — paste the sampler's TWO lines "
                  "and run again.", FilesPath(), InpFile);
      return;
     }
   string prov = FileReadString(h);
   string line = FileReadString(h);
   FileClose(h);
   StringTrimLeft(prov); StringTrimRight(prov);
   StringTrimLeft(line); StringTrimRight(line);
   if(StringFind(prov, "PROV|") != 0 || StringLen(line) == 0)
     { Print("HC: input must be PROV line then entries line. Aborting."); return; }

   string label = LabelOf(prov);
   if(StringFind(label, "HC_S") != 0)
     {
      PrintFormat("HC REFUSED: PROV line carries no valid label "
                  "(label=HC_S<k> required; got '%s'). The label names the "
                  "sprint the evidence belongs to — no label, no capture.",
                  label);
      return;
     }
   PrintFormat("HC[%s]: provenance: %s", label, prov);

   ChartSetInteger(0, CHART_AUTOSCROLL, false);
   string entries[];
   int n = StringSplit(line, ';', entries);
   PrintFormat("HC[%s]: %d entr%s after split.", label, n, n == 1 ? "y" : "ies");
   int matched = 0, checked = 0;

   for(int i = 0; i < n; i++)
     {
      string f[];
      int nf = StringSplit(entries[i], '|', f);
      if(nf < 7)
        { PrintFormat("HC[%s]: entry %d UNPARSED: '%s'", label, i, entries[i]);
          continue; }
      datetime e_close = StringToTime(f[0]) + InpUtcOffsetHours * 3600;
      datetime x_close = StringToTime(f[1]) + InpUtcOffsetHours * 3600;
      datetime e_open  = e_close - PeriodSeconds(PERIOD_H1);
      datetime x_open  = x_close - PeriodSeconds(PERIOD_H1);
      int    dir   = (int)StringToInteger(f[2]);
      double entry = StringToDouble(f[3]);
      double exitp = StringToDouble(f[4]);
      string note  = (nf >= 8) ? f[7] : "";

      int e_shift = iBarShift(_Symbol, PERIOD_H1, e_open, true);
      int x_shift = iBarShift(_Symbol, PERIOD_H1, x_open, true);
      if(e_shift < 0 || x_shift < 0)
        { PrintFormat("HC[%s]: bar NOT FOUND for entry %s / exit %s — adjust "
                      "offset.", label, f[0], f[1]); continue; }

      // NO-LOOK-AHEAD verification from MT5's own series:
      double mt5_entry_open = iOpen(_Symbol, PERIOD_H1, e_shift);
      double mt5_exit_open  = iOpen(_Symbol, PERIOD_H1, x_shift);
      bool price_ok = MathAbs(mt5_entry_open - entry) <= InpTol
                   && MathAbs(mt5_exit_open  - exitp) <= InpTol;

      // MON contract check (DEVQ-019): the entry bar must OPEN on a Monday.
      // The exit day is reported, never asserted (real-feed 22-bar holds
      // exit early Tuesday — checklist_s8.md explains).
      bool dow_ok = true;
      string dowtxt = "";
      if(note == "MON")
        {
         int edow = DayOfWeekOf(e_open - InpUtcOffsetHours * 3600); // UTC
         int xdow = DayOfWeekOf(x_open - InpUtcOffsetHours * 3600);
         dow_ok = (edow == 1);
         dowtxt = StringFormat(" | entry dow=%d %s, exit dow=%d",
                               edow, dow_ok ? "MON-OK" : "MON-BAD", xdow);
        }
      bool ok = price_ok && dow_ok;
      checked++; if(ok) matched++;

      string tag = StringFormat("%s_%d", label, (int)e_close);
      ObjectCreate(0, tag+"_e", dir > 0 ? OBJ_ARROW_BUY : OBJ_ARROW_SELL,
                   0, e_open, entry);
      ObjectCreate(0, tag+"_x", OBJ_ARROW_CHECK, 0, x_open, exitp);
      ObjectSetInteger(0, tag+"_x", OBJPROP_COLOR, clrDodgerBlue);
      ObjectCreate(0, tag+"_l", OBJ_TREND, 0, e_open, entry, x_open, exitp);
      ObjectSetInteger(0, tag+"_l", OBJPROP_COLOR, clrOrange);
      ObjectSetInteger(0, tag+"_l", OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, tag+"_l", OBJPROP_RAY_RIGHT, false);

      string cap1 = StringFormat("%s | %s %s | entry %.2f exit %.2f%s",
                                 label, dir > 0 ? "LONG" : "SHORT", f[0],
                                 entry, exitp,
                                 note == "" ? "" : " | " + note);
      string cap2 = StringFormat("gross %s net %s | MT5 opens %.2f/%.2f | %s%s",
                                 f[5], f[6], mt5_entry_open, mt5_exit_open,
                                 ok ? "MATCH" : "MISMATCH", dowtxt);
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
      string fname = StringFormat("%s_%d%s.png", label, (int)e_close,
                                  visible ? "" : "_NAVFAIL");
      int px_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
      int px_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 0)
               + (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, 1);
      if(px_h <= 0) px_h = 800;
      if(!ChartScreenShot(0, fname, px_w, px_h, ALIGN_LEFT))
         PrintFormat("HC[%s]: screenshot FAILED for %s (err %d)", label, f[0],
                     GetLastError());
      else
         PrintFormat("HC[%s]: %s -> %s%s (%s%s)", label, f[0], FilesPath(),
                     fname, ok ? "MATCH" : "MISMATCH",
                     visible ? "" : ", NAVFAIL — evidence INVALID");

      ObjectDelete(0, tag+"_t0"); ObjectDelete(0, tag+"_t1");
      ObjectDelete(0, tag+"_t2"); ObjectDelete(0, tag+"_e");
      ObjectDelete(0, tag+"_x"); ObjectDelete(0, tag+"_l");
     }
   ChartRedraw();
   PrintFormat("HC[%s] done: %d/%d MATCH (entry+exit at next-bar opens, "
               "MT5's own series; MON rows also require a Monday entry). "
               "PNGs: %s", label, matched, checked, FilesPath());
  }
//+------------------------------------------------------------------+
