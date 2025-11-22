import pandas as pd
import re
import logging

# Configure logging for diagnostics
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_race_form(text):
    lines = text.splitlines()
    dogs = []
    current_race = {}
    race_number = 0

    for line in lines:
        line = line.strip()

        # Match race header - updated to handle different date formats
        # Format: "Race No 22 Nov 25 07:21PM WENTWORTH PARK 520m"
        # Where 22 is race number, Nov is month, 25 is year (2025)
        header_match = re.match(r"Race No\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})\s+(\d{2}:\d{2}[AP]M)\s+([A-Z\s]+?)\s+(\d+)m", line, re.IGNORECASE)
        if header_match:
            race_num_str, month, year_suffix, time, track, distance = header_match.groups()
            race_number += 1
            
            # Convert month abbreviation to number
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            month_num = month_map.get(month.lower()[:3], '01')
            
            # Construct full year from 2-digit suffix (e.g., '25' -> '2025')
            year = f"20{year_suffix}"
            
            # Use the race number from the PDF or our counter
            # The date is year-month-day format, but we don't have the day from this format
            # So we'll use day 01 as a placeholder
            current_race = {
                "RaceNumber": race_number,
                "RaceDate": f"{year}-{month_num}-01",  # Using day 01 as placeholder
                "RaceTime": time,
                "Track": track.strip(),
                "Distance": int(distance)
            }
            logging.debug(f"✅ Parsed race header: {current_race}")
            continue

        # Match dog entry with glued form number
        dog_match = re.match(
            r"""^(\d+)\.?\s*(\d{3,6})?([A-Za-z'' -]+?)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z'' -]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$([0-9,]+)\s+(\S+)\s+(\S+)\s+(\S+)""",
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

            # Initialize dog data with defaults for time metrics
            dog_data = {
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
                **current_race,
                # Initialize time metrics as None - will be filled if found
                "BestTimeSec": None,
                "SectionalSec": None,
                "Last3TimesSec": None,
                "Margins": None
            }
            
            dogs.append(dog_data)
            continue

        # Match Best/Sectional/Last3 block
        time_match = re.match(
            r"""Best:\s*(\d+\.\d+)\s+Sectional:\s*(\d+\.\d+)\s+Last3:\s*\[(.*?)\]""",
            line
        )
        if time_match and dogs:
            try:
                dogs[-1]["BestTimeSec"] = float(time_match.group(1))
                dogs[-1]["SectionalSec"] = float(time_match.group(2))
                last3 = [float(t.strip()) for t in time_match.group(3).split(",")]
                dogs[-1]["Last3TimesSec"] = last3
                logging.debug(f"✅ Parsed time data for {dogs[-1]['DogName']}: Best={dogs[-1]['BestTimeSec']}, Sectional={dogs[-1]['SectionalSec']}")
            except ValueError as e:
                logging.warning(f"⚠️ Error parsing time data for {dogs[-1].get('DogName', 'Unknown')}: {e}")
                dogs[-1]["Last3TimesSec"] = []

        # Match Margins block
        margin_match = re.match(
            r"""Margins:\s*\[(.*?)\]""",
            line
        )
        if margin_match and dogs:
            try:
                margins = [float(m.strip()) for m in margin_match.group(1).split(",")]
                dogs[-1]["Margins"] = margins
                logging.debug(f"✅ Parsed margins for {dogs[-1]['DogName']}: {margins}")
            except ValueError as e:
                logging.warning(f"⚠️ Error parsing margins for {dogs[-1].get('DogName', 'Unknown')}: {e}")
                dogs[-1]["Margins"] = []

    df = pd.DataFrame(dogs)
    
    # Log diagnostic information about missing data
    if len(df) > 0:
        missing_best_time = df["BestTimeSec"].isna().sum()
        missing_sectional = df["SectionalSec"].isna().sum()
        missing_last3 = df["Last3TimesSec"].isna().sum()
        missing_margins = df["Margins"].isna().sum()
        
        if missing_best_time > 0:
            logging.warning(f"⚠️ {missing_best_time}/{len(df)} dogs missing BestTimeSec data")
        if missing_sectional > 0:
            logging.warning(f"⚠️ {missing_sectional}/{len(df)} dogs missing SectionalSec data")
        if missing_last3 > 0:
            logging.warning(f"⚠️ {missing_last3}/{len(df)} dogs missing Last3TimesSec data")
        if missing_margins > 0:
            logging.warning(f"⚠️ {missing_margins}/{len(df)} dogs missing Margins data")
        
        logging.info(f"✅ Parsed {len(df)} dogs from race form")
    else:
        logging.error("❌ No dogs were parsed from the race form - check PDF format and regex patterns")
    
    print(f"✅ Parsed {len(df)} dogs")
    return df
