import re
import pandas as pd
from typing import Optional
from .utils import clean_text, to_float


RE_BEST = re.compile(r"Best[: ]+(\d+\.\d+)")
RE_SECTIONAL = re.compile(r"Sectional[: ]+(\d+\.\d+)")
RE_LAST3_BLOCK = re.compile(r"Last3[: ]*\[(.*?)\]")
RE_MARGINS_BLOCK = re.compile(r"Margins[: ]*\[(.*?)\]")


# A looser matcher by dog context can be added if needed per PDF style.




def parse_timing_metrics(text: str) -> pd.DataFrame:
lines = [clean_text(x) for x in text.splitlines()]
# We attach metrics to the *latest seen dog line* heuristically
rows = []
current = {"Track": None, "RaceNumber": None, "Box": None, "DogName": None}


# Dog-ident line (e.g., "1. 22313 Life's A Journey 2d 0.0kg 1 Trainer ...")
RE_DOG_IDENT = re.compile(r"^(\d+)\.\s*([0-9]{0,6})?([A-Za-z'’\- ]+)")


for line in lines:
m = RE_DOG_IDENT.search(line)
if m:
current = {"Track": None, "RaceNumber": None, "Box": int(m.group(1)), "DogName": clean_text(m.group(3))}
rows.append({**current})
continue


if rows:
if (b := RE_BEST.search(line)):
rows[-1]["BestTime"] = to_float(b.group(1))
if (s := RE_SECTIONAL.search(line)):
rows[-1]["Sectional1"] = to_float(s.group(1))
if (l3 := RE_LAST3_BLOCK.search(line)):
try:
rows[-1]["Sectional2"], rows[-1]["Sectional3"] = [to_float(x) for x in l3.group(1).split(",")[:2]]
except Exception:
pass
if (mg := RE_MARGINS_BLOCK.search(line)):
rows[-1]["Margin"] = to_float(mg.group(1).split(",")[0])


df = pd.DataFrame(rows)
# Speeds derived only if inputs present; leave NaN otherwise
return df[[c for c in ["Box", "DogName", "BestTime", "Sectional1", "Sectional2", "Sectional3", "Margin"] if c in df.columns]]
