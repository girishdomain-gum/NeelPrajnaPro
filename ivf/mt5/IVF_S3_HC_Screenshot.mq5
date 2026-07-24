//+------------------------------------------------------------------+
//| IVF_S3_HC_Screenshot.mq5 — HC-S3 evidence capture (rev 1)        |
//| Architect-owned IVF tool. Run as a SCRIPT on the XAUUSD H1 chart.|
//|                                                                  |
//| Input InpBars: semicolon-separated entries, one per sampled bar: |
//|   "yyyy.mm.dd hh:mm|O|H|L|C;..."  (UTC open time + IVF values)   |
//| Generate it with:                                                |
//|   uv run python ivf/human/sample_s3_bars.py --clean ... --mql    |
//|                                                                  |
//| For each bar: navigate the chart there, draw a vertical line and |
//| a caption "IVF expects ... | MT5 shows ... | MATCH/MISMATCH",    |
//| save a PNG to MQL5\Files\HC_S3_<epoch>.png, and log the verdict. |
//|                                                                  |
//| TIME ZONES: chart times are SERVER time; IVF times are UTC. Set  |
//| InpUtcOffsetHours to the broker offset (try 0; if every bar is   |
//| NOT FOUND or shifted by the same amount, use 2 or 3). A wrong    |
//| offset cannot fake a MATCH — values are read from the exact bar. |
//+------------------------------------------------------------------+
#property copyright "QRF IVF"
#property version   "1.00"
#property script_show_inputs

input string InpBars           = "";    // bars: time|O|H|L|C;...
input int    InpUtcOffsetHours = 0;     // server = UTC + offset
input int    InpWidth          = 1400;  // screenshot width px
input int    InpHeight         = 800;   // screenshot height px
input double InpTol            = 0.005; // match tolerance (half a pip @2dp)

void OnStart()
  {
   if(_Period != PERIOD_H1)
     { Print("HC-S3: run this on an H1 chart. Aborting."); return; }
   if(StringLen(InpBars) == 0)
     { Print("HC-S3: InpBars is empty — paste the sampler's --mql line."); return; }

   ChartSetInteger(0, CHART_AUTOSCROLL, false);
   ChartSetInteger(0, CHART_FOREGROUND, false);

   string entries[];
   int n = StringSplit(InpBars, ';', entries);
   int matched = 0, checked = 0;

   for(int i = 0; i < n; i++)
     {
      string f[];
      if(StringSplit(entries[i], '|', f) < 5) continue;
      datetime t_utc    = StringToTime(f[0]);
      datetime t_server = t_utc + InpUtcOffsetHours * 3600;

      int shift = iBarShift(_Symbol, PERIOD_H1, t_server, true);
      if(shift < 0)
        { PrintFormat("HC-S3: bar %s (server %s) NOT FOUND — check offset.",
                      f[0], TimeToString(t_server)); continue; }

      double o = iOpen (_Symbol, PERIOD_H1, shift);
      double h = iHigh (_Symbol, PERIOD_H1, shift);
      double l = iLow  (_Symbol, PERIOD_H1, shift);
      double c = iClose(_Symbol, PERIOD_H1, shift);

      bool ok = MathAbs(o - StringToDouble(f[1])) <= InpTol
             && MathAbs(h - StringToDouble(f[2])) <= InpTol
             && MathAbs(l - StringToDouble(f[3])) <= InpTol
             && MathAbs(c - StringToDouble(f[4])) <= InpTol;
      checked++; if(ok) matched++;

      string cap = StringFormat(
         "%s UTC | IVF: O=%s H=%s L=%s C=%s | MT5: O=%.2f H=%.2f L=%.2f C=%.2f | %s",
         f[0], f[1], f[2], f[3], f[4], o, h, l, c, ok ? "MATCH" : "MISMATCH");

      string tag = StringFormat("HC_%d", (int)t_utc);
      ObjectCreate(0, tag+"_v", OBJ_VLINE, 0, t_server, 0);
      ObjectSetInteger(0, tag+"_v", OBJPROP_COLOR, clrOrange);
      ObjectSetInteger(0, tag+"_v", OBJPROP_WIDTH, 2);
      ObjectCreate(0, tag+"_t", OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, tag+"_t", OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, tag+"_t", OBJPROP_XDISTANCE, 10);
      ObjectSetInteger(0, tag+"_t", OBJPROP_YDISTANCE, 20);
      ObjectSetString (0, tag+"_t", OBJPROP_TEXT, cap);
      ObjectSetInteger(0, tag+"_t", OBJPROP_FONTSIZE, 10);
      ObjectSetInteger(0, tag+"_t", OBJPROP_COLOR, ok ? clrLime : clrRed);

      // center the bar in view, then capture
      int width_bars = (int)ChartGetInteger(0, CHART_WIDTH_IN_BARS);
      ChartNavigate(0, CHART_END, -shift + width_bars/2);
      ChartRedraw();
      Sleep(700);
      string fname = StringFormat("HC_S3_%d.png", (int)t_utc);
      if(!ChartScreenShot(0, fname, InpWidth, InpHeight, ALIGN_RIGHT))
         PrintFormat("HC-S3: screenshot FAILED for %s (err %d)", f[0], GetLastError());
      else
         PrintFormat("HC-S3: %s -> %s (%s)", f[0], fname, ok ? "MATCH" : "MISMATCH");

      ObjectDelete(0, tag+"_t");
      ObjectDelete(0, tag+"_v");
     }
   ChartRedraw();
   PrintFormat("HC-S3 done: %d/%d MATCH. PNGs in the terminal's MQL5\\Files folder "
               "(File -> Open Data Folder).", matched, checked);
  }
//+------------------------------------------------------------------+
