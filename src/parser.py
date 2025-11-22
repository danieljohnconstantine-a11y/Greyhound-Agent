import pandas as pd
import re

def parse_race_form(text):
    """
    Enhanced parser that extracts timing data from race history.
    
    Multi-level approach to extract BestTimeSec and SectionalSec:
    1. Primary: Extract from race history lines (Race Time and Sec Time patterns)
    2. Track dog sections using dog name headers
    3. Fallback: Legacy "Best:" and "Sectional:" format (backward compatibility)
    4. Validation: Filter out invalid values (0, negative, or unrealistic times)
    5. Ensure no silent failures, log extraction results
    """
    lines = text.splitlines()
    dogs = []
    current_race = {}
    race_number = 0
    
    # Track which dog's detailed section we're currently in
    current_dog_section_index = -1
    dog_timing_data = {}  # Index -> {race_times: [], sec_times: []}

    for i, line in enumerate(lines):
        line = line.strip()

        # Match race header
        header_match = re.match(r"Race No\s+(\d{1,2}) Oct (\d{2}) (\d{2}:\d{2}[AP]M) ([A-Za-z ]+)\s+(\d+)m", line)
        if header_match:
            race_number += 1
            day, year, time, track, distance = header_match.groups()
            current_race = {
                "RaceNumber": race_number,
                "RaceDate": f"2025-10-{day.zfill(2)}",
                "RaceTime": time,
                "Track": track.strip(),
                "Distance": int(distance)
            }
            current_dog_section_index = -1  # Reset dog section when new race starts
            continue

        # Match dog entry with glued form number
        dog_match = re.match(
            r"""^(\d+)\.?\s*([0-9]{3,6})?([A-Za-z''\- ]+)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z''\- ]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$([\d,]+)\s+(\S+)\s+(\S+)\s+(\S+)""",
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

            dog_index = len(dogs)
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
            
            # Initialize timing data collection for this dog
            dog_timing_data[dog_index] = {"race_times": [], "sec_times": [], "name": dog_name}
            continue

        # Check if this is a dog name header (all caps, short line)
        # This marks the start of a dog's detailed section
        # Improved matching: exact match or very close match, excluding generic headers
        if line.upper() == line and 3 <= len(line) <= 50 and len(line.split()) <= 5:
            # Exclude common non-dog headers
            if any(keyword in line for keyword in ['RACE', 'PRIZE', 'DISTANCE', 'TRACK', 'HORSE', 'WINNER']):
                continue
            
            # Try to match this to a known dog
            line_normalized = line.replace("'", "").replace("-", " ").replace("  ", " ").strip()
            for dog_idx, dog in enumerate(dogs):
                dog_name_normalized = dog["DogName"].upper().replace("'", "").replace("-", " ").strip()
                # More strict matching: the line should be the dog name (with minor variations)
                if dog_name_normalized == line_normalized:
                    current_dog_section_index = dog_idx
                    break

        # Extract timing data from race history lines
        # Only attribute to a dog if we know which dog's section we're in
        if current_dog_section_index >= 0 and current_dog_section_index in dog_timing_data:
            # Pattern: "Race Time 0:30.92" (mm:ss.ss format)
            race_time_match = re.search(r'Race Time (\d+):(\d+\.\d+)', line)
            if race_time_match:
                minutes = int(race_time_match.group(1))
                seconds = float(race_time_match.group(2))
                total_seconds = minutes * 60 + seconds
                # Validate: race times should be between 10 and 200 seconds for greyhounds
                if 10 <= total_seconds <= 200:
                    dog_timing_data[current_dog_section_index]["race_times"].append(total_seconds)
            
            # Pattern: "Sec Time 5.28" (sectional time in seconds)
            sec_time_match = re.search(r'Sec Time (\d+\.\d+)', line)
            if sec_time_match:
                sec_time = float(sec_time_match.group(1))
                # Validate: sectional times should be between 1 and 30 seconds
                if 1 <= sec_time <= 30:
                    dog_timing_data[current_dog_section_index]["sec_times"].append(sec_time)

        # Legacy: Match Best/Sectional/Last3 block (for backward compatibility)
        time_match = re.search(r'Best:\s*(\d+\.\d+)\s+Sectional:\s*(\d+\.\d+)', line)
        if time_match and dogs:
            best_time = float(time_match.group(1))
            sec_time = float(time_match.group(2))
            # Validate before assigning
            if 10 <= best_time <= 200:
                dogs[-1]["BestTimeSec"] = best_time
            if 1 <= sec_time <= 30:
                dogs[-1]["SectionalSec"] = sec_time
            # Also check for Last3
            last3_match = re.search(r'Last3:\s*\[([\d., ]+)\]', line)
            if last3_match:
                try:
                    last3 = [float(t.strip()) for t in last3_match.group(1).split(",")]
                    dogs[-1]["Last3TimesSec"] = last3
                except:
                    pass

        # Match Margins block
        margin_match = re.search(r'Margins:\s*\[([\d., ]+)\]', line)
        if margin_match and dogs:
            try:
                margins = [float(m.strip()) for m in margin_match.group(1).split(",")]
                dogs[-1]["Margins"] = margins
            except:
                pass

    # Apply collected timing data to each dog
    for dog_index, timing in dog_timing_data.items():
        race_times = timing["race_times"]
        sec_times = timing["sec_times"]
        
        if race_times:
            # BestTimeSec: minimum race time (best performance)
            dogs[dog_index]["BestTimeSec"] = min(race_times)
            # Last3TimesSec: most recent 3 race times (last 3 in the list, as they're in chronological order)
            dogs[dog_index]["Last3TimesSec"] = race_times[-3:] if len(race_times) >= 3 else race_times
        
        if sec_times:
            # SectionalSec: minimum sectional time (best sectional)
            dogs[dog_index]["SectionalSec"] = min(sec_times)

    df = pd.DataFrame(dogs)
    
    # Validation: Count how many dogs have timing data
    if len(df) > 0:
        best_time_count = df["BestTimeSec"].notna().sum() if "BestTimeSec" in df.columns else 0
        sec_time_count = df["SectionalSec"].notna().sum() if "SectionalSec" in df.columns else 0
        print(f"✅ Parsed {len(df)} dogs")
        print(f"   📊 Timing data extracted: {best_time_count}/{len(df)} dogs have BestTimeSec, {sec_time_count}/{len(df)} have SectionalSec")
        
        if best_time_count == 0:
            print(f"   ⚠️  WARNING: No BestTimeSec data extracted from any dog")
        if sec_time_count == 0:
            print(f"   ⚠️  WARNING: No SectionalSec data extracted from any dog")
    
    return df
