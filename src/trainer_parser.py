import re
import pandas as pd
from typing import Dict
from .utils import clean_text, to_float


RE_TRAINER = re.compile(r"Trainer[: ]+([A-Za-z'’\- ]+)")
RE_TRAINER_WIN = re.compile(r"Win Rate[: ]+(\d{1,2}(?:\.\d+)?%)")
RE_CITY = re.compile(r"City[: ]+([A-Za-z'’\- ]+)")
RE_STATE = re.compile(r"State[: ]+([A-Za-z]{2,3})")
RE_OWNER = re.compile(r"Owner[: ]+([A-Za-z'’\- ,]+)")
RE_SIRE = re.compile(r"Sire[: ]+([A-Za-z'’\- ]+)")
RE_DAM = re.compile(r"Dam[: ]+([A-Za-z'’\- ]+)")
RE_COLOR = re.compile(r"Color[: ]+([A-Za-z ]+)")
RE_AGE = re.compile(r"Age[: ]+(\d+)")
RE_SEX = re.compile(r"Sex[: ]+([A-Za-z])")




def parse_trainer_blocks(text: str, trainer_cache: Dict[str, dict]) -> pd.DataFrame:
lines = [clean_text(x) for x in text.splitlines()]


RE_DOG_IDENT = re.compile(r"^(\d+)\.\s*([0-9]{0,6})?([A-Za-z'’\- ]+)")
rows = []
current = None


for line in lines:
d = RE_DOG_IDENT.search(line)
if d:
current = {"Box": int(d.group(1)), "DogName": clean_text(d.group(3))}
rows.append(current)
continue
if current is None:
continue


if (m := RE_TRAINER.search(line)):
current["Trainer"] = clean_text(m.group(1))
# Enrich from cache if available
meta = trainer_cache.get(current["Trainer"], {})
current.update({
"TrainerWinRate": meta.get("TrainerWinRate"),
"TrainerCity": meta.get("TrainerCity"),
"TrainerState": meta.get("TrainerState"),
})
if (m := RE_OWNER.search(line)):
current["Owner"] = clean_text(m.group(1))
if (m := RE_SIRE.search(line)):
current["Sire"] = clean_text(m.group(1))
if (m := RE_DAM.search(line)):
current["Dam"] = clean_text(m.group(1))
if (m := RE_COLOR.search(line)):
current["Color"] = clean_text(m.group(1))
if (m := RE_AGE.search(line)):
current["Age"] = int(m.group(1))
if (m := RE_SEX.search(line)):
current["Sex"] = clean_text(m.group(1)).upper()


return pd.DataFrame(rows)
