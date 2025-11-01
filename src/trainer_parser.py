import re
import pandas as pd
from typing import Dict, List, Any
from .utils import clean_text, to_float

# Identify new dog entries (box, dog name)
RE_DOG_IDENT = re.compile(r"^(\\d+)\\.\\s*([0-9]{0,6})?([A-Za-z'’\\- ]+)")
RE_TRAINER = re.compile(r"Trainer[: ]+([A-Za-z'’\\- ]+)", re.IGNORECASE)
RE_OWNER = re.compile(r"Owner[: ]+([A-Za-z'’\\- ,]+)", re.IGNORECASE)
RE_SIRE  = re.compile(r"Sire[: ]+([A-Za-z'’\\- ]+)", re.IGNORECASE)
RE_DAM   = re.compile(r"Dam[: ]+([A-Za-z'’\\- ]+)", re.IGNORECASE)
RE_COLOR = re.compile(r"Color[: ]+([A-Za-z ]+)", re.IGNORECASE)
RE_AGE   = re.compile(r"Age[: ]+(\\d+)", re.IGNORECASE)
RE_SEX   = re.compile(r"Sex[: ]+([A-Za-z])", re.IGNORECASE)

def parse_trainer_blocks(text: str, trainer_cache: Dict[str, dict]) -> pd.DataFrame:
    """
    Parse trainer information and enrich with cached trainer metadata.
    Returns a DataFrame keyed by Box & DogName with trainer & breeding details.
    """
    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []
    current: Dict[str, Any] = None

    for line in lines:
        dog_match = RE_DOG_IDENT.search(line)
        if dog_match:
            current = {
                "Box": int(dog_match.group(1)),
                "DogName": clean_text(dog_match.group(3)),
            }
            rows.append(current)
            continue

        if current is None:
            continue

        if (m := RE_TRAINER.search(line)):
            trainer_name = clean_text(m.group(1))
            current["Trainer"] = trainer_name
            # enrich from cache
            meta = trainer_cache.get(trainer_name, {})
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
