import pandas as pd
import re
import logging

# Get logger for this module (logging is configured in main.py if needed)
logger = logging.getLogger(__name__)

# Distance tolerance constants for matching race times to current race distance
DISTANCE_EXACT_MATCH_TOLERANCE = 10  # meters
DISTANCE_SIMILAR_MATCH_TOLERANCE = 50  # meters

# Month abbreviation to number mapping for date parsing
MONTH_MAP = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}

# Year conversion constant (for 2-digit years in format YY -> 20YY)
# Assumes all greyhound racing data is from 2000-2099 (current era)
BASE_YEAR = 2000

def parse_race_form(text):
    """
    Enhanced parser that extracts timing data from race history.
    
    Multi-level approach to extract BestTimeSec and SectionalSec:
    1. Primary: Extract from race history lines (Race Time and Sec Time patterns)
    2. Track dog sections using dog name headers
    3. Match race times to distances from preceding line
    4. Filter best time for the specific distance the dog is racing at
    5. Fallback: Legacy "Best:" and "Sectional:" format (backward compatibility)
    6. Validation: Filter out invalid values (race times: 10-200s, sectionals: 1-15s)
       - Sectionals measure first 100-200m, so >15s likely indicates incidents/errors
    7. Ensure no silent failures, log extraction results
    """
    lines = text.splitlines()
    dogs = []
    current_race = {}
    race_number = 0
    
    # Track which dog's detailed section we're currently in
    current_dog_section_index = -1
    dog_timing_data = {}  # Index -> {race_times: [(time, distance)], sec_times: [(time, distance)], box_history: [(box_pos, won)]}
    previous_line_distance = None  # Track distance from previous line

    for i, line in enumerate(lines):
        line = line.strip()

        # Match race header - flexible format for different months and date formats
        # Format: "Race No  1 Oct 16 04:00PM Angle Park 530m" or "Race No 07 Sep 25 06:04PM Q STRAIGHT 300m"
        header_match = re.match(r"Race No\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})\s+(\d{2}:\d{2}[AP]M)\s+([A-Za-z ]+?)\s+(\d+)m", line)
        if header_match:
            race_number += 1
            race_num, month, day, time, track, distance = header_match.groups()
            
            # Convert 2-digit year (day is actually year in the regex) to 4-digit year
            year = BASE_YEAR + int(day)
            
            # Convert month abbreviation to numeric format using MONTH_MAP
            month_num = MONTH_MAP.get(month, None)
            if month_num is None:
                # Month abbreviation not recognized, use default and log error
                logger.error(
                    f"❌ Unrecognized month abbreviation '{month}' in race header. "
                    f"Using '01' (January) as fallback. Please update MONTH_MAP if this is a valid month."
                )
                month_num = '01'  # Default to January to maintain valid ISO date format
            
            # Extract day from race_num (which is actually the day in current parse)
            # The regex groups are: race_num (day), month, day (year), time, track, distance
            actual_day = race_num  # First capture group is the day
            
            current_race = {
                "RaceNumber": race_number,
                "RaceDate": f"{year}-{month_num}-{actual_day.zfill(2)}",  # ISO format: YYYY-MM-DD
                "RaceTime": time,
                "Track": track.strip(),
                "Distance": int(distance)
            }
            logger.debug(f"Parsed race header: Race {race_number}, {track}, {distance}m on {year}-{month_num}-{actual_day.zfill(2)}")
            current_dog_section_index = -1  # Reset dog section when new race starts
            continue

        # Match dog entry with glued form number
        # Form number can contain digits and 'x' character (e.g., "8x324")
        dog_match = re.match(
            r"""^(\d+)\.?\s*([0-9x]{3,6})?([A-Za-z''\- ]+)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z''\- ]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$([\d,]+)\s+(\S+)\s+(\S+)\s+(\S+)""",
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
            dog_timing_data[dog_index] = {"race_times": [], "sec_times": [], "box_history": [], "race_dates": [], "name": dog_name}
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
            
            # Store distance for this line's timing data (both Race Time and Sec Time can use it)
            line_distance = previous_line_distance
            
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
                        (total_seconds, line_distance)
                    )
                    
                    # Extract Box Position (BP) from the same line if available
                    # Pattern: " BP 2 " or " BP 10 "
                    bp_match = re.search(r' BP (\d+)', line)
                    if bp_match:
                        box_pos = int(bp_match.group(1))
                        # Determine if dog won: look for "Prize Won" (indicates placed)
                        # More precise: check if this is first place
                        # API ~1.0 typically means won, API < 0.5 means lost badly
                        # For now, use Prize Won as indicator of placing/winning
                        won = "Prize Won" in line
                        dog_timing_data[current_dog_section_index]["box_history"].append(
                            (box_pos, won)
                        )
                    
                    # Extract race date from the beginning of the line
                    # Common formats: "07Oct24", "15Nov24", etc.
                    date_match = re.search(r'(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2})', line)
                    if date_match:
                        day = int(date_match.group(1))
                        month_str = date_match.group(2)
                        year_short = int(date_match.group(3))
                        
                        # Convert month string to number
                        month_map = {
                            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
                        }
                        month = month_map.get(month_str, 1)
                        
                        # Assume 20xx for year (e.g., 24 -> 2024)
                        year = 2000 + year_short
                        
                        # Store race date
                        from datetime import date as date_obj
                        try:
                            race_date = date_obj(year, month, day)
                            dog_timing_data[current_dog_section_index]["race_dates"].append(race_date)
                        except ValueError:
                            # Invalid date - skip
                            pass
            
            # Pattern: "Sec Time 5.28" (sectional time in seconds)
            # Both Race Time and Sec Time can appear on the same line with the same distance
            sec_time_match = re.search(r'Sec Time (\d+\.\d+)', line)
            if sec_time_match:
                sec_time = float(sec_time_match.group(1))
                # Validate: sectional times should be between 1 and 15 seconds
                # Sectionals measure first 100-200m, so even slow dogs should be under 12-14s
                # Values above 15s likely indicate incidents, falls, or data errors
                if 1 <= sec_time <= 15:
                    # Store sectional time with distance (same distance as race time if both on same line)
                    dog_timing_data[current_dog_section_index]["sec_times"].append(
                        (sec_time, line_distance)
                    )
            
            # Reset distance after processing this line's timing data
            if race_time_match or sec_time_match:
                previous_line_distance = None

        # Legacy: Match Best/Sectional/Last3 block (for backward compatibility)
        time_match = re.search(r'Best:\s*(\d+\.\d+)\s+Sectional:\s*(\d+\.\d+)', line)
        if time_match and dogs:
            best_time = float(time_match.group(1))
            sec_time = float(time_match.group(2))
            # Validate before assigning
            if 10 <= best_time <= 200:
                dogs[-1]["BestTimeSec"] = best_time
            if 1 <= sec_time <= 15:  # Sectionals should be under 15s (typically first 100-200m)
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
        
        # Calculate box preference/bias for this dog
        box_history = timing.get("box_history", [])
        if box_history and "Box" in dogs[dog_index]:
            current_box = dogs[dog_index]["Box"]
            
            # Group boxes into categories
            # Typically: 1-3 (inside), 4-6 (mid), 7-10 (outside)
            def get_box_group(box):
                if box <= 3:
                    return "inside"
                elif box <= 6:
                    return "mid"
                else:
                    return "outside"
            
            current_box_group = get_box_group(current_box)
            
            # Calculate win rate for each box group
            box_group_stats = {"inside": {"races": 0, "wins": 0}, 
                              "mid": {"races": 0, "wins": 0}, 
                              "outside": {"races": 0, "wins": 0}}
            
            for box_pos, won in box_history:
                group = get_box_group(box_pos)
                box_group_stats[group]["races"] += 1
                if won:
                    box_group_stats[group]["wins"] += 1
            
            # Calculate win rates
            overall_wins = sum(stats["wins"] for stats in box_group_stats.values())
            overall_races = sum(stats["races"] for stats in box_group_stats.values())
            overall_win_rate = overall_wins / overall_races if overall_races > 0 else 0
            
            # Win rate in current box group
            current_group_stats = box_group_stats[current_box_group]
            current_group_win_rate = (current_group_stats["wins"] / current_group_stats["races"] 
                                     if current_group_stats["races"] > 0 else overall_win_rate)
            
            # BoxBiasFactor: difference from overall win rate
            # Positive = performs better in this box group
            # Negative = performs worse in this box group
            box_bias = current_group_win_rate - overall_win_rate
            
            # Store in dog data
            dogs[dog_index]["BoxBiasFactor"] = box_bias
        else:
            # No box history or current box - use neutral bias
            dogs[dog_index]["BoxBiasFactor"] = 0.0

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
    
    # Validation: Count how many dogs have timing data
    if len(df) > 0:
        best_time_count = df["BestTimeSec"].notna().sum() if "BestTimeSec" in df.columns else 0
        sec_time_count = df["SectionalSec"].notna().sum() if "SectionalSec" in df.columns else 0
        print(f"✅ Parsed {len(df)} dogs")
        print(f"   📊 Timing data extracted: {best_time_count}/{len(df)} dogs have BestTimeSec, {sec_time_count}/{len(df)} have SectionalSec")
        
        if best_time_count == 0:
            print(f"   ⚠️  WARNING: No BestTimeSec data extracted from any dog")
            logger.warning("No BestTimeSec data extracted from any dog")
        if sec_time_count == 0:
            print(f"   ⚠️  WARNING: No SectionalSec data extracted from any dog")
            logger.warning("No SectionalSec data extracted from any dog")
    
    return df
