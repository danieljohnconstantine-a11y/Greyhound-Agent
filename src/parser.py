import pandas as pd
import re

# Distance tolerance constants for matching race times to current race distance
DISTANCE_EXACT_MATCH_TOLERANCE = 10  # meters
DISTANCE_SIMILAR_MATCH_TOLERANCE = 50  # meters

def parse_race_form(text):
    """
    Enhanced parser that extracts timing data from race history.
    
    Multi-level approach to extract BestTimeSec and SectionalSec:
    1. Primary: Extract from race history lines (Race Time and Sec Time patterns)
    2. Track dog sections using dog name headers
    3. Match race times to distances from preceding line
    4. Filter best time for the specific distance the dog is racing at
    5. Fallback: Legacy "Best:" and "Sectional:" format (backward compatibility)
    6. Validation: Filter out invalid values (0, negative, or unrealistic times)
    7. Ensure no silent failures, log extraction results
    """
    lines = text.splitlines()
    dogs = []
    current_race = {}
    race_number = 0
    
    # Track which dog's detailed section we're currently in
    current_dog_section_index = -1
    dog_timing_data = {}  # Index -> {race_times: [(time, distance)], sec_times: [(time, distance)]}
    previous_line_distance = None  # Track distance from previous line

    for i, line in enumerate(lines):
        line = line.strip()

        # Match race header - flexible format for different months and date formats
        # Format: "Race No  1 Oct 16 04:00PM Angle Park 530m" or "Race No 07 Sep 25 06:04PM Q STRAIGHT 300m"
        header_match = re.match(r"Race No\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})\s+(\d{2}:\d{2}[AP]M)\s+([A-Za-z ]+?)\s+(\d+)m", line)
        if header_match:
            race_number += 1
            race_num, month, day, time, track, distance = header_match.groups()
            # Map month abbreviations to numbers
            month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
            month_num = month_map.get(month, '01')
            current_race = {
                "RaceNumber": race_number,
                "RaceDate": f"2025-{month_num}-{day.zfill(2)}",
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
            # Check if current line has distance info (appears before race time)
            distance_match = re.search(r'Distance (\d+)m', line)
            if distance_match:
                previous_line_distance = int(distance_match.group(1))
            
            race_time_processed = False  # Flag to track if we processed race time on this line
            
            # Pattern: "Race Time 0:30.92" (mm:ss.ss format)
            race_time_match = re.search(r'Race Time (\d+):(\d+\.\d+)', line)
            if race_time_match:
                minutes = int(race_time_match.group(1))
                seconds = float(race_time_match.group(2))
                total_seconds = minutes * 60 + seconds
                # Validate: race times should be between 10 and 200 seconds for greyhounds
                if 10 <= total_seconds <= 200:
                    # Store race time with distance (if we just saw a distance in a recent line)
                    # Note: distance might be None if not found recently
                    dog_timing_data[current_dog_section_index]["race_times"].append(
                        (total_seconds, previous_line_distance)
                    )
                    race_time_processed = True
                # Reset distance after processing race time
                previous_line_distance = None
            
            # Pattern: "Sec Time 5.28" (sectional time in seconds)
            # Only process if we didn't already process race time (they appear on same line)
            sec_time_match = re.search(r'Sec Time (\d+\.\d+)', line)
            if sec_time_match and not race_time_processed:
                sec_time = float(sec_time_match.group(1))
                # Validate: sectional times should be between 1 and 30 seconds
                if 1 <= sec_time <= 30:
                    # Store sectional time with distance
                    dog_timing_data[current_dog_section_index]["sec_times"].append(
                        (sec_time, previous_line_distance)
                    )
                    previous_line_distance = None

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
        race_times = timing["race_times"]  # List of (time, distance) tuples
        sec_times = timing["sec_times"]    # List of (time, distance) tuples
        dog_race_distance = dogs[dog_index]["Distance"]  # The distance this dog is racing today
        
        if race_times:
            # Filter race times for the same distance (within exact match tolerance)
            same_distance_times = [
                time for time, dist in race_times 
                if dist is not None and abs(dist - dog_race_distance) <= DISTANCE_EXACT_MATCH_TOLERANCE
            ]
            
            # If we have times at the same distance, use those
            if same_distance_times:
                # BestTimeSec: minimum race time at this distance (best performance)
                dogs[dog_index]["BestTimeSec"] = min(same_distance_times)
                # Last3TimesSec: most recent 3 race times at this distance
                dogs[dog_index]["Last3TimesSec"] = same_distance_times[-3:] if len(same_distance_times) >= 3 else same_distance_times
            else:
                # Try wider tolerance for similar distances
                similar_distance_times = [
                    time for time, dist in race_times 
                    if dist is not None and abs(dist - dog_race_distance) <= DISTANCE_SIMILAR_MATCH_TOLERANCE
                ]
                if similar_distance_times:
                    dogs[dog_index]["BestTimeSec"] = min(similar_distance_times)
                    dogs[dog_index]["Last3TimesSec"] = similar_distance_times[-3:] if len(similar_distance_times) >= 3 else similar_distance_times
                # Otherwise: skip this dog's BestTimeSec (leave it as NaN)
                # Don't use times from vastly different distances as it's misleading
        
        if sec_times:
            # Filter sectional times for the same distance (exact match tolerance)
            same_distance_sectionals = [
                time for time, dist in sec_times 
                if dist is not None and abs(dist - dog_race_distance) <= DISTANCE_EXACT_MATCH_TOLERANCE
            ]
            
            # If we have sectionals at the same distance, use those
            if same_distance_sectionals:
                # SectionalSec: minimum sectional time at this distance
                dogs[dog_index]["SectionalSec"] = min(same_distance_sectionals)
            else:
                # Try wider tolerance for similar distances
                similar_distance_sectionals = [
                    time for time, dist in sec_times 
                    if dist is not None and abs(dist - dog_race_distance) <= DISTANCE_SIMILAR_MATCH_TOLERANCE
                ]
                if similar_distance_sectionals:
                    dogs[dog_index]["SectionalSec"] = min(similar_distance_sectionals)
                # Otherwise: skip (leave as NaN)

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
