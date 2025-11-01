import re
import pandas as pd
from typing import Dict
from .utils import clean_text


RE_BOX_HISTORY = re.compile(r"Box History[: ]*(.*)")
RE_BOX_WINS = re.compile(r"Box Wins[: ]*(\d+)")
RE_BOX_PLACES = re.compile(r"Box Places[: ]*(\d+)")




def parse_box_history(text: str, box_bias_map: Dict[str, Dict[int, float]]) -> pd.DataFrame:
lines = [clean_text(x) for x in text.splitlines()]
RE_DOG_IDENT = re.compile(r"^(\d+)\.\s*([0-9]{0,6})?([A-Za-z'’\- ]+)")


rows = []
current = None
current_track = None
current_race = None


# Track/race inference (optional lightweight; classification_parser can do better)
RE_RACE_HEADER = re.compile(r"Race No\s*(\d+)\s*(\d{1,2} \w+ \d{2}) (\d{1,2}:\d{2}[AP]M) ([A-Za-z ]+) (\d{3,4})m")


for line in lines:
h = RE_RACE_HEADER.search(line)
if h:
current_race = int(h.group(1))
current_track = h.group(4).strip()
continue


d = RE_DOG_IDENT.search(line)
if d:
current = {"Track": current_track, "RaceNumber": current_race, "Box": int(d.group(1)), "DogName": clean_text(d.group(3))}
rows.append(current)
continue
if current is None:
continue


if (m := RE_BOX_HISTORY.search(line)):
current["BoxHistory"] = clean_text(m.group(1))
if (m := RE_BOX_WINS.search(line)):
current["BoxWins"] = int(m.group(1))
if (m := RE_BOX_PLACES.search(line)):
current["BoxPlaces"] = int(m.group(1))


df = pd.DataFrame(rows)
# Inject BoxBiasFactor from map if available
if not df.empty and box_bias_map:
def bias_lookup(row):
t = (row.get("Track") or "").upper()
b = int(row.get("Box") or 0)
return box_bias_map.get(t, {}).get(b)
df["BoxBiasFactor"] = df.apply(bias_lookup, axis=1)
return df
