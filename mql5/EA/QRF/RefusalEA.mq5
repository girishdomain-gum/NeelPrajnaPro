//+------------------------------------------------------------------+
//| RefusalEA.mq5                                                     |
//| S07 (A-029 §3): a fresh, from-scratch EA that reads a staged       |
//| instruction, VALIDATES it, and REFUSES the invalid ones -- and     |
//| places no orders at all. No pattern logic (AM-02): no bias, no    |
//| trigger, no gate, no market condition of any kind. Mechanics only  |
//| (terminal lifecycle, file staging/polling) are reused in SHAPE     |
//| from F:\Fable\tools\np_agent.py and this project's own S03         |
//| launcher.py, exactly like both of those already do -- re-          |
//| implemented from scratch here, never copied (S07 import plan,      |
//| A-028: F:\Fable stays a mechanics QUARRY, never a source, and       |
//| nothing was imported from it).                                     |
//|                                                                     |
//| CLOCK SOURCE (runtime/contract.py's docstring states the Python     |
//| side; this is the EA side of the same decision): expiry is checked |
//| against TimeGMT() -- the terminal's own GMT-normalized broker time |
//| -- deliberately NOT against S03's clock_drift_probe_seconds, which |
//| is latency-inflated and documented as never a timezone constant    |
//| (F-04). A refusal-only EA that places no orders does not need      |
//| sub-second precision; "well past its window" is the only           |
//| resolution that matters.                                           |
//+------------------------------------------------------------------+
#property strict

#define PINNED_SYMBOL "XAUUSD"
#define INSTRUCTION_FILE "QRF\\instruction.json"
#define FEEDBACK_FILE "QRF\\ea_feedback.txt"

//+------------------------------------------------------------------+
//| A single, very small, hand-written JSON reader -- the staged       |
//| instruction has a known, fixed, flat shape (see                    |
//| runtime/contract.py's Instruction.to_dict()), so a general JSON     |
//| library is not needed and would be one more untested dependency.   |
//| Refuses (returns false) on anything it cannot parse confidently,   |
//| rather than guessing a value.                                      |
//+------------------------------------------------------------------+
bool JsonExtractString(const string &text, const string &key, string &out)
  {
   string needle = "\"" + key + "\":\"";
   int pos = StringFind(text, needle);
   if(pos < 0) return false;
   int start = pos + StringLen(needle);
   int end = StringFind(text, "\"", start);
   if(end < 0) return false;
   out = StringSubstr(text, start, end - start);
   return true;
  }

bool JsonExtractNumber(const string &text, const string &key, double &out)
  {
   string needle = "\"" + key + "\":";
   int pos = StringFind(text, needle);
   if(pos < 0) return false;
   int start = pos + StringLen(needle);
   int end = start;
   int len = StringLen(text);
   while(end < len)
     {
      ushort c = StringGetCharacter(text, end);
      if(c == ',' || c == '}') break;
      end++;
     }
   if(end <= start) return false;
   out = StringToDouble(StringSubstr(text, start, end - start));
   return true;
  }

void LogRefusal(const string reason)
  {
   Print("QRF_REFUSED: ", reason);
   int h = FileOpen(FEEDBACK_FILE, FILE_WRITE | FILE_READ | FILE_TXT | FILE_ANSI);
   if(h == INVALID_HANDLE) return;
   FileSeek(h, 0, SEEK_END);
   FileWrite(h, "REFUSED " + TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS) + " " + reason);
   FileClose(h);
  }

//+------------------------------------------------------------------+
//| ValidateAndRefuse -- the whole point of this EA. Every branch      |
//| that fails names EXACTLY which check failed (A-029 §3.2), and NO   |
//| branch, on any path, calls anything that places or modifies an     |
//| order. No order-placement API of any kind is referenced anywhere   |
//| in this file -- 3.3 is satisfied by absence, not by a guard.       |
//+------------------------------------------------------------------+
void ValidateAndRefuse()
  {
   if(_Symbol != PINNED_SYMBOL)
     {
      LogRefusal("symbol mismatch: chart is " + _Symbol + ", pinned is " + PINNED_SYMBOL);
      return;
     }

   int h = FileOpen(INSTRUCTION_FILE, FILE_READ | FILE_TXT | FILE_ANSI);
   if(h == INVALID_HANDLE)
     {
      LogRefusal("no staged instruction file present");
      return;
     }
   string text = "";
   while(!FileIsEnding(h))
      text += FileReadString(h);
   FileClose(h);

   string instruction_id, direction, action;
   double valid_until_d, trigger_price;

   if(!JsonExtractString(text, "instruction_id", instruction_id))
     { LogRefusal("malformed: missing instruction_id"); return; }
   if(!JsonExtractString(text, "direction", direction))
     { LogRefusal("malformed: missing direction (" + instruction_id + ")"); return; }
   if(direction != "long" && direction != "short")
     { LogRefusal("malformed: direction not recognised (" + instruction_id + ")"); return; }
   if(!JsonExtractString(text, "action", action))
     { LogRefusal("malformed: missing action (" + instruction_id + ")"); return; }
   if(action != "open")
     { LogRefusal("malformed: action not recognised (" + instruction_id + ")"); return; }
   if(!JsonExtractNumber(text, "trigger_price", trigger_price))
     { LogRefusal("malformed: missing trigger_price (" + instruction_id + ")"); return; }
   if(!JsonExtractNumber(text, "valid_until", valid_until_d))
     { LogRefusal("malformed: missing valid_until (" + instruction_id + ")"); return; }

   datetime valid_until = (datetime)(long)valid_until_d;
   datetime now_gmt = TimeGMT();
   if(now_gmt > valid_until)
     {
      LogRefusal("expired: valid_until=" + TimeToString(valid_until, TIME_DATE | TIME_SECONDS) +
                 " now=" + TimeToString(now_gmt, TIME_DATE | TIME_SECONDS) +
                 " (" + instruction_id + ")");
      return;
     }

   // Every check passed. Per A-029 §3.3, THIS EA STILL PLACES NO ORDER --
   // acting on a valid instruction is explicitly OUT OF SCOPE for S07
   // (see the module header). Only a passing log entry is written.
   Print("QRF_VALID: instruction ", instruction_id, " passed every check; NO ORDER PLACED (S07 scope)");
  }

int OnInit()
  {
   ValidateAndRefuse();
   return(INIT_SUCCEEDED);
  }

void OnTick()
  {
  }
