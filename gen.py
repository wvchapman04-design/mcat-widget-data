#!/usr/bin/env python3
"""Build status.json (the widget feed) from a saved MCAT Mastery state.
Usage: python3 gen.py state.json > status.json
Only aggregate numbers go in the feed: streak, mastery %, next topic, weekly change."""
import json, sys, datetime, os
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(HERE, "topics.json")))
COUNTS = {"cp": 33, "cars": 7, "bb": 37, "ps": 32}
SHORT = {"cp": "C/P", "cars": "CARS", "bb": "B/B", "ps": "P/S"}
BELTS = ["White", "Blue", "Purple", "Brown", "Black"]
TZ = ZoneInfo("Pacific/Honolulu")

st = json.load(open(sys.argv[1]))
topics = st.get("topics") or {}
now = datetime.datetime.now(TZ)
today = now.strftime("%Y-%m-%d")
now_ms = now.timestamp() * 1000

def mast(t):
    return 1.0 if t.get("l", 0) >= 5 else (t.get("l", 0) + t.get("p", 0) / 100) / 5

sec = {}
for s, n in COUNTS.items():
    total = sum(mast(t) for k, t in topics.items() if k.startswith(s + "-"))
    sec[s] = round(total / n * 100, 2)
ov = round(sum(sec.values()) / 4, 2)
r = min(24, int(ov // 4))
belt = f"{BELTS[r // 5]} belt" + (f" · {r % 5} stripe{'s' if r % 5 > 1 else ''}" if r % 5 else "")

# streak still alive if played today or yesterday
last = st.get("lastDay") or ""
yday = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
streak = st.get("streak", 0) if last in (today, yday) else 0

# next up: due topic with lowest mastery, else the first unplayed topic of the lowest section
due = [(mast(t), k) for k, t in topics.items() if not k.startswith("cars-") and t.get("n") and t.get("l", 0) < 5 and t.get("due", 0) <= now_ms]
nxt = None
if due:
    k = sorted(due)[0][1]
    nxt = {"name": NAMES.get(k, k), "sec": SHORT[k.split("-")[0]]}
else:
    for s in sorted(["cp", "bb", "ps", "cars"], key=lambda x: sec[x]):
        if s == "cars":
            nxt = {"name": "CARS passage", "sec": "CARS"}; break
        fresh = [k for k in NAMES if k.startswith(s + "-") and not (topics.get(k) or {}).get("n")]
        if fresh:
            k = sorted(fresh, key=lambda x: int(x.split("-")[1]))[0]
            nxt = {"name": NAMES[k], "sec": SHORT[s]}; break

# weekly change: now minus the last history snapshot on or before 7 days ago
hist = st.get("hist") or {}
cut = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
old = [d for d in hist if d <= cut]
base = hist[max(old)]["pct"] if old else {}
week_delta = {s: round(sec[s] - (base.get(s) or 0), 2) for s in COUNTS}
week_keys = [(now - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
week_secs = sum((hist.get(d) or {}).get("secs", 0) for d in week_keys)

out = {
    "updated": now.isoformat(timespec="minutes"),
    "streak": streak, "lastDay": last, "playedToday": last == today, "tokens": st.get("tokens", 0),
    "roundsToday": (st.get("day") or {}).get("rounds", 0) if (st.get("day") or {}).get("d") == today else 0,
    "ov": ov, "belt": belt, "sec": sec, "weekDelta": week_delta, "weekSecs": week_secs,
    "dueCount": len(due), "next": nxt,
}
print(json.dumps(out, ensure_ascii=False, indent=1))
