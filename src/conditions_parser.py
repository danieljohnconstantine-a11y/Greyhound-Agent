import re
import pandas as pd
from typing import Dict, List, Any
from .utils import clean_text

RE_DOG_IDENT = re.compile(r"^(\\d+)\\.\\s*([0-9]{0,6})?([A-Za-z'’\\- ]+)")
RE_DIRECTION = re.compile(r"Track Direction[: ]+(Clockwise|Anti\\-?clockwise)", re.IGNORECASE)
RE_RACETIME = re.compile(r"Race Time[: ]+(\\d{1,2}:\\d{2}\\.\\d{2})", re.IGNORECASE)

def parse_conditions_banner(text: str) -> pd.DataFrame:
    """
    Banner-level conditions (Direction, RaceTime).
    Attaches info to the last-seen dog row in each race.
    Returns DataFrame keyed by Box & DogName.
    """
    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []
    current: Dict[str, Any] = None

    for line in lines:
        d = RE_DOG_IDENT.search(line)
        if d:
            current = {"Box": int(d.group(1)), "DogName": clean_text(d.group(3))}
            rows.append(dict(current))
            continue
        if current is None:
            continue

        if (m := RE_DIRECTION.search(line)):
            rows[-1]["Direction"] = m.group(1).title()
        if (m := RE_RACETIME.search(line)):
            rows[-1]["RaceTime"] = m.group(1)

    return pd.DataFrame(rows)
