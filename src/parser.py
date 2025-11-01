import re
import pandas as pd
from typing import List, Dict, Any, Optional
from .utils import clean_text, to_float, money_to_float, split_age_sex

# Example header: "Race No 3 16 Oct 25 12:34PM ANGLE PARK 530m"
RE_RACE_HEADER = re.compile(
    r"Race\s*No\s*(\d+)\s+(\d{1,2}\s+\w+\s+\d{2})\s+(\d{1,2}:\d{2}[AP]M)\s+([A-Za-z '’&\-]+)\s+(\d{3,4})m",
    re.IGNORECASE
)

# Example dog: "1. 22313 Life's A Journey 2d 29.0kg ..."
RE_DOG_START = re.compile(r"^(\d+)\.\s*(?:\d{0,6})?\s*([A-Za-z'’\- ]+)\s+(\d+[a-zA-Z])\s+([\d.]+)kg", re.IGNORECASE)

RE_TRAINER = re.compile(r"Trainer[: ]+([A-Za-z'’\- ]+)", re.IGNORECASE)
RE_RUNS = re.compile(r"Runs?[: ]+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", re.IGNORECASE)
RE_PRIZE = re.compile(r"(?:Prize|Career(?:\s+)?Prize(?:\s+)?Money)[: ]+(\$[\d,]+(?:\.\d{2})?)", re.IGNORECASE)
RE_WINRATE = re.compile(r"Win\s*Rate[: ]+(\d{1,2}(?:\.\d+)?%)", re.IGNORECASE)
RE_PLCRATE = re.compile(r"Place\s*Rate[: ]+(\d{1,2}(?:\.\d+)?%)", re.IGNORECASE)
RE_ODDS = re.compile(r"Odds[: ]*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
RE_FORM = re.compile(r"Form[: ]*([0-9A-Za-z]+)", re.IGNORECASE)
RE_CAREER_BEST = re.compile(r"(?:Career\s*Best|Best\s*Time)[: ]*([0-9]+\.[0-9]+)", re.IGNORECASE)
RE_RTC = re.compile(r"RTC[: ]*(\S+)", re.IGNORECASE)
RE_DLR = re.compile(r"DLR[: ]*(\S+)", re.IGNORECASE)
RE_DLW = re.compile(r"DLW[: ]*(\S+)", re.IGNORECASE)

RE_OWNER = re.compile(r"Owner[: ]+([A-Za-z'’\- ,]+)", re.IGNORECASE)
RE_SIRE  = re.compile(r"Sire[: ]+([A-Za-z'’\- ]+)", re.IGNORECASE)
RE_DAM   = re.compile(r"Dam[: ]+([A-Za-z'’\- ]+)", re.IGNORECASE)
RE_COLOR = re.compile(r"Color[: ]+([A-Za-z ]+)", re.IGNORECASE)


def parse_race_form(text: str) -> pd.DataFrame:
    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []

    current_track = None
    current_race_no = None
    current_date = None
    current_time = None
    current_distance = None
    current_row = None

    for line in lines:
        if not line:
            continue

        # Race header
        rh = RE_RACE_HEADER.search(line)
        if rh:
            current_race_no = int(rh.group(1))
            current_date = rh.group(2)
            current_time = rh.group(3)
            current_track = rh.group(4).strip()
            current_distance = int(rh.group(5))
            continue

        # New dog entry
        m = RE_DOG_START.search(line)
        if m:
            if current_row:
                rows.append(current_row)

            box = int(m.group(1))
            dog_name = clean_text(m.group(2))
            sex_age_token = m.group(3)
            weight = to_float(m.group(4))
            age, sex = split_age_sex(sex_age_token)

            current_row = {
                "Track": current_track,
                "Race": current_race_no,
                "RaceDate": current_date,
                "RaceTime": current_time,
                "Distance": current_distance,
                "Box": box,
                "DogName": dog_name,
                "Sex": sex,
                "Age": age,
                "Weight": weight,
                "Trainer": None,
                "Form": None,
                "WinRate": None,
                "PlaceRate": None,
                "Odds": None,
                "CareerPrizeMoney": None,
                "CareerBest": None,
                "Starts": None, "Wins": None, "Seconds": None, "Thirds": None,
                "RTC": None, "DLR": None, "DLW": None,
                "Owner": None, "Sire": None, "Dam": None, "Color": None,
            }
            continue

        if current_row is None:
            continue

        if (t := RE_TRAINER.search(line)): current_row["Trainer"] = t.group(1).strip()
        if (r := RE_RUNS.search(line)):
            current_row["Starts"] = int(r.group(1))
            current_row["Wins"] = int(r.group(2))
            current_row["Seconds"] = int(r.group(3))
            current_row["Thirds"] = int(r.group(4))
        if (p := RE_PRIZE.search(line)): current_row["CareerPrizeMoney"] = money_to_float(p.group(1))
        if (w := RE_WINRATE.search(line)): current_row["WinRate"] = w.group(1)
        if (pl := RE_PLCRATE.search(line)): current_row["PlaceRate"] = pl.group(1)
        if (o := RE_ODDS.search(line)): current_row["Odds"] = o.group(1)
        if (f := RE_FORM.search(line)): current_row["Form"] = f.group(1)
        if (cb := RE_CAREER_BEST.search(line)): current_row["CareerBest"] = cb.group(1)
        if (x := RE_RTC.search(line)): current_row["RTC"] = x.group(1)
        if (x := RE_DLR.search(line)): current_row["DLR"] = x.group(1)
        if (x := RE_DLW.search(line)): current_row["DLW"] = x.group(1)

        if (m := RE_OWNER.search(line)): current_row["Owner"] = m.group(1).strip()
        if (m := RE_SIRE.search(line)):  current_row["Sire"] = m.group(1).strip()
        if (m := RE_DAM.search(line)):   current_row["Dam"] = m.group(1).strip()
        if (m := RE_COLOR.search(line)): current_row["Color"] = m.group(1).strip()

    if current_row:
        rows.append(current_row)

    return pd.DataFrame(rows)
