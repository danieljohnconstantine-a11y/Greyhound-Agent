import pandas as pd
import re
import logging

# Get logger for this module (logging is configured in main.py)
logger = logging.getLogger(__name__)

# Month abbreviation to number mapping for date parsing
MONTH_MAP = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}

# Year conversion constant (for 2-digit years in format YY -> 20YY)
# Assumes all greyhound racing data is from 2000-2099 (current era)
# This is appropriate since we're processing recent/current race forms, not historical data
BASE_YEAR = 2000

def parse_race_form(text):
    lines = text.splitlines()
    dogs = []
    current_race = {}
    race_number = 0

    for line in lines:
        line = line.strip()

        # Match race header - accepts any 3-letter month abbreviation
        # Examples: "Race No 22 Nov 25 07:21PM WENTWORTH PARK 520m"
        header_match = re.match(r"Race No\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})\s+(\d{2}:\d{2}[AP]M)\s+([A-Za-z ]+)\s+(\d+)m", line)
        if header_match:
            race_number += 1
            day, month_abbr, year_2digit, time, track, distance = header_match.groups()
            
            # Convert 2-digit year to 4-digit year (assumes 2000-2099)
            # For years 00-99, interpret as 2000-2099 (greyhound racing data context)
            year = BASE_YEAR + int(year_2digit)
            
            # Convert month abbreviation to numeric format (e.g., 'Nov' -> '11')
            month_num = MONTH_MAP.get(month_abbr, None)
            if month_num is None:
                # Month abbreviation not recognized, use default and log error
                logger.error(
                    f"❌ Unrecognized month abbreviation '{month_abbr}' in race header. "
                    f"Using '01' (January) as fallback. Please update MONTH_MAP if this is a valid month."
                )
                month_num = '01'  # Default to January to maintain valid ISO date format
            
            current_race = {
                "RaceNumber": race_number,
                "RaceDate": f"{year}-{month_num}-{day.zfill(2)}",  # ISO format: YYYY-MM-DD
                "RaceTime": time,
                "Track": track.strip(),
                "Distance": int(distance)
            }
            logger.debug(f"Parsed race header: Race {race_number}, {track}, {distance}m")
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
    
    # Normalize column names: strip whitespace and ensure consistent casing
    df.columns = df.columns.str.strip()
    
    # Log parsing results
    logger.info(f"✅ Parsed {len(df)} dogs across {race_number} races")
    logger.info(f"📊 Columns in parsed DataFrame: {df.columns.tolist()}")
    
    # Check for critical columns and log warnings if missing
    critical_columns = ['Distance', 'DogName', 'Box', 'Track', 'RaceNumber']
    missing_critical = [col for col in critical_columns if col not in df.columns]
    if missing_critical:
        logger.warning(f"⚠️ Missing critical columns: {missing_critical}")
    
    # Log sample of Distance values to verify parsing
    if 'Distance' in df.columns:
        logger.info(f"📏 Distance values (sample): {df['Distance'].unique()[:5].tolist()}")
    else:
        logger.error("❌ 'Distance' column is MISSING from parsed DataFrame!")
    
    print(f"✅ Parsed {len(df)} dogs")
    return df
