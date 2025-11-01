import re
import pandas as pd
from .utils import clean_text


RE_RACE_COMMENT = re.compile(r"Race Comment[: ]+(.*)", re.IGNORECASE)
RE_LAST_START_COMMENT = re.compile(r"Last Start Comment[: ]+(.*)", re.IGNORECASE)
RE_INTERFERENCE = re.compile(r"Interference[: ]+(.*)", re.IGNORECASE)
RE_WEATHER = re.compile(r"Weather[: ]+(.*)", re.IGNORECASE)
RE_CONDITION = re.compile(r"Track Condition[: ]+(.*)", re.IGNORECASE)


RE_DOG_IDENT = re.compile(r"^(\d+)\.\s*([0-9]{0,6})?([A-Za-z'’\- ]+)")




def parse_comments_and_conditions(text: str):
lines = [clean_text(x) for x in text.splitlines()]


rows_comment = []
rows_cond = []
current = None


for line in lines:
d = RE_DOG_IDENT.search(line)
if d:
current = {"Box": int(d.group(1)), "DogName": clean_text(d.group(3))}
rows_comment.append(dict(current))
rows_cond.append(dict(current))
continue
if current is None:
continue


if (m := RE_RACE_COMMENT.search(line)):
rows_comment[-1]["RaceComment"] = clean_text(m.group(1))
if (m := RE_LAST_START_COMMENT.search(line)):
rows_comment[-1]["LastStartComment"] = clean_text(m.group(1))
if (m := RE_INTERFERENCE.search(line)):
rows_cond[-1]["Interference"] = clean_text(m.group(1))
if (m := RE_WEATHER.search(line)):
rows_cond[-1]["Weather"] = clean_text(m.group(1))
if (m := RE_CONDITION.search(line)):
rows_cond[-1]["TrackCondition"] = clean_text(m.group(1))


return pd.DataFrame(rows_comment), pd.DataFrame(rows_cond)
