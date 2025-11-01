import re
import pandas as pd
from typing import List, Dict, Any, Optional
from .utils import clean_text, to_float, money_to_float, split_age_sex


HEADER_CORE = [
"Track", "RaceNumber", "RaceDate", "RaceTime", "Distance",
"Box", "DogName", "Trainer", "SexAge", "Weight",
"Starts", "Wins", "Seconds", "Thirds", "CareerPrizeMoney", "CareerBest",
"RTC", "DLR", "DLW", "SourcePDF"
]


# Example patterns (tune to your PDFs)
RE_RACE_HEADER = re.compile(r"Race No\s*(\d+)\s*(\d{1,2} \w+ \d{2}) (\d{1,2}:\d{2}[AP]M) ([A-Za-z ]+) (\d{3,4})m")
RE_DOG_LINE = re.compile(
r"^(\d+)\.\s*([0-9]{0,6})?([A-Za-z'’\- ]+)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z'’\- ]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$([\d,]+)\s+(\S+)\s+(\S+)\s+(\S+)"
)




def parse_race_form(text: str, source_pdf: Optional[str] = None) -> pd.DataFrame:
lines = [clean_text(x) for x in text.splitlines()]
dogs: List[Dict[str, Any]] = []
current = {}


race_number = 0
for line in lines:
if not line:
continue


h = RE_RACE_HEADER.search(line)
if h:
race_number = int(h.group(1))
date = h.group(2)
rtime = h.group(3)
track = h.group(4).strip()
distance = int(h.group(5))
current = {
"RaceNumber": race_number,
"RaceDate": date,
"RaceTime": rtime,
"Track": track,
"Distance": distance,
}
continue


m = RE_DOG_LINE.search(line)
if m:
box = int(m.group(1))
form_number = (m.group(2) or "").strip()
raw_name = (m.group(3) or "").strip()
sex_age = (m.group(4) or "").strip()
weight = to_float(m.group(5))
draw = int(m.group(6)) # unused but kept
trainer = (m.group(7) or "").strip()
wins, places, starts = int(m.group(8)), int(m.group(9)), int(m.group(10))
prize = money_to_float(m.group(11))
rtc, dlr, dlw = m.group(12), m.group(13), m.group(14)


dog_name = raw_name
d: Dict[str, Any] = {
**current,
"Box": box,
"DogName": dog_name,
"Trainer": trainer,
"SexAge": sex_age,
"Weight": weight,
"Starts": starts,
"Wins": wins,
"Seconds": places,
"Thirds": 0, # not present in this line; optional further parse elsewhere
"CareerPrizeMoney": prize,
return pd.DataFrame(dogs, columns=HEADER_CORE)
