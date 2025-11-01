import re
import pandas as pd
from typing import List, Dict, Any
from .utils import clean_text, to_float

RE_DOG_IDENT = re.compile(r"^(\\d+)\\.\\s*([0-9]{0,6})?([A-Za-z'’\\- ]+)")
RE_LAST_DATE = re.compile(r"Last Start Date[: ]+(\\d{2}/\\d{2}/\\d{4})", re.IGNORECASE)
RE_LAST_TRACK = re.compile(r"Last Start Track[: ]+([A-Za-z ]+)", re.IGNORECASE)
RE_LAST_RESULT = re.compile(r"Last Start Result[: ]+(\\d+(?:st|nd|rd|th))", re.IGNORECASE)
RE_LAST_MARGIN = re.compile(r"Last Start Margin[: ]+([\\d\\.]+)", re.IGNORECASE)
RE_LAST_COMMENT = re.compile(r"Last Start Comment[: ]+(.*)", re.IGNORECASE)

def parse_last_start(text: str) -> pd.DataFrame:
    """
    Extract last start date, track, result, margin, and comment for each dog.
    Returns DataFrame keyed by Box & DogName.
    """
    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []
    current: Dict[str, Any] = None

    for line in lines:
        d = RE_DOG_IDENT.search(line)
        if d:
            current = {"Box": int(d.group(1)), "DogName": clean_text(d.group(3))}
            rows.append(current)
            continue
        if current is None:
            continue

        if (m := RE_LAST_DATE.search(line)):
            current["LastStartDate"] = m.group(1)
        if (m := RE_LAST_TRACK.search(line)):
            current["LastStartTrack"] = clean_text(m.group(1))
        if (m := RE_LAST_RESULT.search(line)):
            current["LastStartResult"] = m.group(1)
        if (m := RE_LAST_MARGIN.search(line)):
            current["LastStartMargin"] = to_float(m.group(1))
        if (m := RE_LAST_COMMENT.search(line)):
            current["LastStartComment"] = clean_text(m.group(1))

    return pd.DataFrame(rows)
