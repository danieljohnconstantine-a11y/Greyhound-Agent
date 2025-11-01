import re
import pandas as pd
from typing import List, Dict, Any
from .utils import clean_text

RE_HEADER = re.compile(r"Race\\s*No\\s*(\\d+)\\s*(\\d{1,2}\\s+\\w+\\s+\\d{2})\\s*(\\d{1,2}:\\d{2}[AP]M)\\s*([A-Za-z '’\\-&]+)\\s*(\\d{3,4})m", re.IGNORECASE)
RE_GRADE = re.compile(r"(\\d(?:st|nd|rd|th) Grade|Maiden|Novice|Open|Mixed\\s*\\d*)", re.IGNORECASE)
RE_PRIZE = re.compile(r"Prizemoney[: ]+\\$([\\d,]+)", re.IGNORECASE)
RE_RACE_NAME = re.compile(r"^[A-Z0-9'& ]+\\s+STAKE.*", re.IGNORECASE)

def parse_classification(text: str) -> pd.DataFrame:
    """
    Extract race classification lines: Grade, CareerPrizeMoney, Race (name).
    Returns DataFrame keyed by Track & Race (number).
    """
    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []
    current_track = None
    current_race = None

    for line in lines:
        h = RE_HEADER.search(line)
        if h:
            current_race = int(h.group(1))
            current_track = h.group(4).strip()
            continue

        m_grade = RE_GRADE.search(line)
        m_prize = RE_PRIZE.search(line)
        m_race = RE_RACE_NAME.search(line)

        if current_track and current_race and (m_grade or m_prize or m_race):
            row: Dict[str, Any] = {"Track": current_track, "Race": current_race}
            if m_grade:
                row["Grade"] = m_grade.group(1).title()
            if m_prize:
                row["CareerPrizeMoney"] = float(m_prize.group(1).replace(",", ""))
            if m_race:
                row["RaceClass"] = line.strip()
            rows.append(row)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).drop_duplicates(subset=["Track", "Race"], keep="last")
    return df
