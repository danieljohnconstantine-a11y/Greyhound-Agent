import re
import pandas as pd
from .utils import clean_text


RE_HEADER = re.compile(r"Race No\s*(\d+)\s*(\d{1,2} \w+ \d{2}) (\d{1,2}:\d{2}[AP]M) ([A-Za-z ]+) (\d{3,4})m")
RE_GRADE = re.compile(r"(\d(?:st|nd|rd|th) Grade|(?:Maiden|Novice|Open|Mixed)\s*\d*)", re.IGNORECASE)
RE_PRIZE = re.compile(r"Prizemoney[: ]+\$([\d,]+)", re.IGNORECASE)
RE_RACE_NAME = re.compile(r"^[A-Z0-9'& ]+ STAKE.*", re.IGNORECASE)




def parse_classification(text: str) -> pd.DataFrame:
lines = [clean_text(x) for x in text.splitlines()]
rows = []
current_track = None
current_race = None


for line in lines:
h = RE_HEADER.search(line)
if h:
current_race = int(h.group(1))
current_track = h.group(4).strip()
continue
# Capture grade / prizemoney / race name lines
m1 = RE_GRADE.search(line)
m2 = RE_PRIZE.search(line)
m3 = RE_RACE_NAME.search(line)
if current_track and current_race and (m1 or m2 or m3):
row = {"Track": current_track, "RaceNumber": current_race}
if m1:
row["Grade"] = m1.group(1).title()
if m2:
row["CareerPrizeMoney"] = float(m2.group(1).replace(",", ""))
if m3:
row["Race"] = line.strip()
rows.append(row)


# Deduplicate by Track+RaceNumber, keep last
if not rows:
return pd.DataFrame()
df = pd.DataFrame(rows).drop_duplicates(subset=["Track", "RaceNumber"], keep="last")
return df
