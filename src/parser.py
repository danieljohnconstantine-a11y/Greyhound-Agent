import pandas as pd
import re

def parse_race_form(text):
    lines = text.splitlines()
    dogs = []
    current_race = {}
    race_number = 0

    for line in lines:
        line = line.strip()

        # Match race header - handles any month (Oct, Nov, Dec, etc.)
        header_match = re.match(r"Race No\s+(\d{1,2}) ([A-Za-z]{3}) (\d{2}) (\d{2}:\d{2}[AP]M) ([A-Za-z ]+)\s+(\d+)m", line)
        if header_match:
            race_number += 1
            day, month, year, time, track, distance = header_match.groups()
            
            # Convert month abbreviation to number
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            month_num = month_map.get(month, None)
            
            # Skip if invalid month
            if month_num is None:
                print(f"⚠️ Warning: Unknown month '{month}' in race header, skipping")
                continue
            
            # Convert 2-digit year to 4-digit (assumes 2000s for 00-99)
            # Years 00-49 -> 2000-2049, Years 50-99 -> 1950-1999
            year_int = int(year)
            if year_int < 50:
                full_year = f"20{year}"
            else:
                full_year = f"19{year}"
            
            current_race = {
                "RaceNumber": race_number,
                "RaceDate": f"{full_year}-{month_num}-{day.zfill(2)}",
                "RaceTime": time,
                "Track": track.strip(),
                "Distance": int(distance)
            }
            continue

        # Match dog entry with glued form number
        dog_match = re.match(
            r"""^(\d+)\.?\s*([0-9]{3,6})?([A-Za-z'’\- ]+)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z'’\- ]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$([\d,]+)\s+(\S+)\s+(\S+)\s+(\S+)""",
            line
        )

        if dog_match:
            (
                box, form_number, raw_name, sex_age, weight, draw, trainer,
                wins, places, starts, prize, rtc, dlr, dlw
            ) = dog_match.groups()

            dog_name = raw_name.strip()
            if form_number and dog_name.startswith(form_number[-2:]):
                dog_name = dog_name[len(form_number[-2:]):].strip()

            dogs.append({
                "Box": int(box),
                "DogName": dog_name,
                "FormNumber": form_number or "",
                "Trainer": trainer.strip(),
                "SexAge": sex_age,
                "Weight": float(weight),
                "Draw": int(draw),
                "CareerWins": int(wins),
                "CareerPlaces": int(places),
                "CareerStarts": int(starts),
                "PrizeMoney": float(prize.replace(",", "")),
                "RTC": rtc,
                "DLR": dlr,
                "DLW": dlw,
                **current_race
            })
            continue

        # Match Best/Sectional/Last3 block
        time_match = re.match(
            r"""Best:\s*(\d+\.\d+)\s+Sectional:\s*(\d+\.\d+)\s+Last3:\s*

\[(.*?)\]

""",
            line
        )
        if time_match and dogs:
            dogs[-1]["BestTimeSec"] = float(time_match.group(1))
            dogs[-1]["SectionalSec"] = float(time_match.group(2))
            try:
                last3 = [float(t.strip()) for t in time_match.group(3).split(",")]
                dogs[-1]["Last3TimesSec"] = last3
            except:
                dogs[-1]["Last3TimesSec"] = []

        # Match Margins block
        margin_match = re.match(
            r"""Margins:\s*

\[(.*?)\]

""",
            line
        )
        if margin_match and dogs:
            try:
                margins = [float(m.strip()) for m in margin_match.group(1).split(",")]
                dogs[-1]["Margins"] = margins
            except:
                dogs[-1]["Margins"] = []

    df = pd.DataFrame(dogs)
    print(f"✅ Parsed {len(df)} dogs")
    return df
