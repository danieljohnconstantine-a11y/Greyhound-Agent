import re
import logging
from datetime import datetime

# Get logger for this module (logging is configured in main.py if needed)
logger = logging.getLogger(__name__)

# Distance tolerance constants for matching race times to current race distance
DISTANCE_EXACT_MATCH_TOLERANCE = 10  # meters
DISTANCE_SIMILAR_MATCH_TOLERANCE = 50  # meters

# Distance conversion: enable converting times from different distances
# Formula: converted_time = original_time * (target_distance / original_distance)
# This assumes consistent average speed (m/s) across distances, which is reasonable for greyhounds
ENABLE_DISTANCE_CONVERSION = True
# Maximum distance difference to convert from (beyond this, conversion is unreliable)
MAX_DISTANCE_CONVERSION_DIFF = 200  # meters (e.g., can convert 400m time to 500m, but not 300m to 600m)

def convert_time_to_distance(original_time, original_distance, target_distance):
    """
    Convert a race time from one distance to an estimated time at another distance.
    
    Uses linear scaling based on average speed:
    - Speed (m/s) = original_distance / original_time
    - Estimated time = target_distance / speed = original_time * (target_distance / original_distance)
    
    This is an approximation - actual times may vary due to:
    - Track conditions
    - Dog's stamina (sprint vs distance specialists)
    - Box position effects
    
    Args:
        original_time: Time in seconds at original distance
        original_distance: Original distance in meters
        target_distance: Target distance to convert to in meters
        
    Returns:
        Estimated time at target distance in seconds
    """
    if original_distance <= 0 or original_time <= 0:
        return None
    
    # Calculate speed and convert
    speed_mps = original_distance / original_time
    converted_time = target_distance / speed_mps
    
    return round(converted_time, 2)

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
    current_race = None  # Will be set when first race header is found
    race_number = 0
    
    # Track which dog's detailed section we're currently in
    current_dog_section_index = -1
    dog_timing_data = {}  # Index -> {race_times: [(time, distance)], sec_times: [(time, distance)], box_history: [(box_pos, won)]}
    previous_line_distance = None  # Track distance from previous line

    # CRITICAL FIX: Join "Race No" lines that are split across two lines
    # Modern PDFs often have: Line 1: "Race No"  Line 2: "1 10 Jan 26 07:27pm DUBBO 400m"
    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # If this line is "Race No" and next line starts with digits, join them
        if line == "Race No" and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and next_line[0].isdigit():
                # Join the lines
                processed_lines.append(f"Race No {next_line}")
                i += 2  # Skip both lines
                continue
        processed_lines.append(line)
        i += 1
    
    lines = processed_lines

    for i, line in enumerate(lines):
        line = line.strip()

        # Match race header - flexible format for different months and date formats
        # Format: "Race No  1 Oct 16 04:00PM Angle Park 530m" OR "Race No 110 Jan 26 07:27pm DUBBO 400m"
        # The "110" is actually race "1" + day "10" (no space between them in some PDFs)
        # Groups: (race_day_combined, month_abbr, year_2digit, time, track, distance)
        # Example: "Race No 110 Jan 26 07:27pm DUBBO 400m"
        # Captures: "110", "Jan", "26", "07:27pm", "DUBBO", "400"
        # We'll parse race_num and day from the combined string
        header_match = re.match(r"Race No\s*(\d+)\s+([A-Za-z]{3})\s+(\d{2})\s+(\d{2}:\d{2}[APap][Mm])\s+([A-Za-z ]+?)\s+(\d+)m", line)
        
        # Fallback: Try simpler race header patterns if main pattern doesn't match
        if not header_match:
            # Pattern 1: "Race 1" or "R1" followed by optional info
            simple_race_match = re.match(r"(?:Race|R)\s*(\d{1,2})\s*[:>\-]?\s*(.*)$", line, re.IGNORECASE)
            if simple_race_match and len(line) < 100:  # Avoid false matches on long lines
                try:
                    # Found a simple race header - increment race number
                    race_number += 1
                    # Use current date as fallback with proper defaults
                    current_race = {
                        "RaceNumber": race_number,
                        "RaceDate": datetime.now().strftime("%Y-%m-%d"),
                        "RaceTime": "TBD",
                        "Track": "Unknown",
                        "Distance": 500  # Default distance
                    }
                    logger.info(f"[INFO] Detected race header (simple format): Race {race_number}")
                    current_dog_section_index = -1
                    continue
                except:
                    pass
        
        if header_match:
            race_day_combined, month_abbr, year_2digit, time, track, distance = header_match.groups()
            
            # Increment race number each time we detect a new race header
            # This ensures proper race numbering even when PDFs use same number for all races
            race_number += 1
            
            # Parse day from the number in header
            # Modern PDFs: "10" = day 10, Old PDFs: "110" = might be race+day or just day
            # We parse as day only since we auto-increment race_number above
            if len(race_day_combined) >= 2:
                # Try to extract day - could be last 2 digits or entire number
                try:
                    day_of_race = race_day_combined[-2:]  # Last 2 digits as day
                    if not (1 <= int(day_of_race) <= 31):  # Validate day
                        day_of_race = race_day_combined  # Use full number if invalid
                except:
                    day_of_race = race_day_combined
            else:
                day_of_race = race_day_combined
            
            # Convert 2-digit year to 4-digit year (e.g., '25' -> 2025, '26' -> 2026)
            year = BASE_YEAR + int(year_2digit)
            
            # Normalize time to uppercase
            time = time.upper()
            
            # Convert month abbreviation to numeric format using MONTH_MAP
            month_num = MONTH_MAP.get(month_abbr, None)
            if month_num is None:
                # Month abbreviation not recognized, use default and log error
                logger.error(
                    f"[ERROR] Unrecognized month abbreviation '{month_abbr}' in race header. "
                    f"Using '01' (January) as fallback. Please update MONTH_MAP if this is a valid month."
                )
                month_num = '01'  # Default to January to maintain valid ISO date format
            
            current_race = {
                "RaceNumber": race_number,
                "RaceDate": f"{year}-{month_num}-{day_of_race.zfill(2)}",  # ISO format: YYYY-MM-DD
                "RaceTime": time,
                "Track": track.strip(),
                "Distance": int(distance)
            }
            logger.info(f"[INFO] Detected race header: Race {race_number}, {track}, {distance}m on {year}-{month_num}-{day_of_race.zfill(2)} at {time}")
            current_dog_section_index = -1  # Reset dog section when new race starts
            continue
        
        # Skip dog parsing if no race header found yet
        if current_race is None:
            continue

        # Match dog entry with glued form number
        # Form number can contain digits, 'x' and 'f' characters (e.g., "8x324", "67f67")
        # BUG FIX: Added 'f' to form number pattern - many dogs have 'f' in their form number
        # which was causing them to not be parsed (e.g., "67f67Lil Patti" was missed)
        # CRITICAL FIX #21: Make form number completely optional {0,7} to catch dogs with NO form number
        # CRITICAL FIX #22: Handle multi-line dog entries where career stats wrap to next lines
        # ENHANCED: More flexible pattern to handle edge cases and spacing variations
        dog_match = re.match(
            r"""^(\d+)\.?\s*([0-9xf]{0,7})?([A-Za-z''\- ]+?)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z''\- ]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$?([\d,]+)\s+(\S+)\s+(\S+)\s+(\S+)""",
            line
        )
        
        # NEW: Also try pattern for dogs where career stats are on NEXT line(s)
        # Pattern: Box, FormNum, Name, Sex/Age, Weight, BP, Trainer, Prize, then partial career stats
        # Example: "5. 48537Great North 4d 0.0kg 5 Brett Gilbert $33,285 173 7 96"
        # Where "173 7 96" are partial career stats on same line, and rest is on next line
        if not dog_match:
            partial_dog_match = re.match(
                r"""^(\d+)\.?\s*([0-9xf]{0,7})?([A-Za-z''\- ]+?)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z''\- ]+?)\s+\$?([\d,]+)(?:\s+(\d+)\s+(\d+)\s+(\d+))?""",
                line
            )
            if partial_dog_match and i + 2 < len(lines):
                # Found partial match
                groups = partial_dog_match.groups()
                box = groups[0]
                form_number = groups[1]
                raw_name = groups[2]
                sex_age = groups[3]
                weight = groups[4]
                draw = groups[5]
                trainer = groups[6]
                prize = groups[7]
                # Career stats might be on same line or next lines
                wins = groups[8] if groups[8] else None
                places = groups[9] if groups[9] else None
                starts = groups[10] if groups[10] else None
                
                # Check next lines for more career stats if not all on current line
                if wins and places and starts:
                    # All stats on same line, just need RTC/DLR/DLW from next line
                    next_line = lines[i + 1].strip()
                    # Look for pattern like "172" (continuation) or skip
                    # Then look for "35 - 59 -" pattern
                    next_next_line = lines[i + 2].strip() if i + 2 < len(lines) else ""
                    
                    # Try to extract RTC, DLR, DLW from next line after continuation
                    rtc_dlr_match = re.search(r'^(\d+)\s*-\s*(\d+)\s*-\s*(\S+)?', next_next_line)
                    if rtc_dlr_match:
                        rtc = rtc_dlr_match.group(1) if rtc_dlr_match.group(1) else "0"
                        dlr = rtc_dlr_match.group(2) if rtc_dlr_match.group(2) else "0"
                        dlw = rtc_dlr_match.group(3) if rtc_dlr_match.group(3) else "Mdn"
                    else:
                        rtc, dlr, dlw = "0", "0", "Mdn"
                else:
                    # Career stats spread across next lines
                    next_line = lines[i + 1].strip()
                    next_next_line = lines[i + 2].strip() if i + 2 < len(lines) else ""
                    
                    # Pattern 1: All stats on next line after prize
                    # "2. 38236Blazin' Bad Zula 4b 0.0kg 2 Nathan Goodwin $42,595 106 7 164"
                    # Next line: "105"
                    # Next next line: "35 - 59 -"
                    if not wins:
                        # Extract from current line - might have partial stats after prize
                        prize_and_stats = re.search(r'\$?([\d,]+)\s+(\d+)\s+(\d+)', line)
                        if prize_and_stats:
                            wins = int(prize_and_stats.group(2))
                            places = int(prize_and_stats.group(3))
                    
                    # Get starts from next line
                    career_match = re.search(r'^(\d+)$', next_line)
                    if career_match:
                        starts = int(career_match.group(1))
                    else:
                        starts = 0
                    
                    # Get RTC, DLR, DLW from next next line
                    stats_match = re.search(r'^(\d+)\s*-\s*(\d+)\s*-\s*(\S+)?', next_next_line)
                    if stats_match:
                        rtc = stats_match.group(1)
                        dlr = stats_match.group(2)
                        dlw = stats_match.group(3) if stats_match.group(3) else "Mdn"
                    else:
                        rtc, dlr, dlw = "0", "0", "Mdn"
                
                dog_name = raw_name.strip()
                if form_number and dog_name.startswith(form_number[-2:]):
                    dog_name = dog_name[len(form_number[-2:]):].strip()
                
                dog_index = len(dogs)
                try:
                    dogs.append({
                        "Box": int(box),
                        "DogName": dog_name,
                        "FormNumber": form_number or "",
                        "Trainer": trainer.strip(),
                        "SexAge": sex_age,
                        "Weight": float(weight),
                        "Draw": int(draw),
                        "CareerWins": int(wins) if wins else 0,
                        "CareerPlaces": int(places) if places else 0,
                        "CareerStarts": int(starts) if starts else 0,
                        "PrizeMoney": float(prize.replace(",", "")),
                        "RTC": rtc,
                        "DLR": dlr,
                        "DLW": dlw,
                        **current_race
                    })
                    
                    # Initialize timing data collection for this dog
                    dog_timing_data[dog_index] = {"race_times": [], "sec_times": [], "box_history": [], "race_dates": [], "name": dog_name}
                    logger.info(f"[OK] Parsed dog (multi-line format): Box {box} - {dog_name} (Race {current_race.get('RaceNumber', '?')})")
                    continue  # Skip to next iteration - we've handled this dog
                except Exception as e:
                    logger.warning(f"[WARNING] Failed to parse multi-line dog: {e}")

        if dog_match:
            (
                box, form_number, raw_name, sex_age, weight, draw, trainer,
                wins, places, starts, prize, rtc, dlr, dlw
            ) = dog_match.groups()

            dog_name = raw_name.strip()
            if form_number and dog_name.startswith(form_number[-2:]):
                dog_name = dog_name[len(form_number[-2:]):].strip()

            dog_index = len(dogs)
            try:
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
                logger.debug(f"[OK] Parsed dog: Box {box} - {dog_name} (Race {current_race.get('RaceNumber', '?')})")
            except Exception as e:
                logger.warning(f"[WARNING] Failed to parse dog from line: {line[:100]}... Error: {e}")
            continue
        
        # Skip dog parsing if no race header found yet
        if current_race is None:
            continue
        
        # CRITICAL FIX #2: Enhanced fallback pattern to catch more dogs
        # Pattern: Box Number, optional form, Dog Name (more flexible spacing/punctuation)
        # This catches edge cases where the main pattern fails
        # RELAXED to accept dogs with minimal form data
        if not dog_match and line and line[0].isdigit():
            simple_dog_match = re.match(
                r"""^(\d+)[\.\s]+([0-9xf]{0,7})?\s*([A-Za-z''\- ]+?)\s+(\d+[a-z])?\s*([\d.]+)?kg""",
                line
            )
            if simple_dog_match:
                logger.debug(f"Using fallback pattern for line: {line[:80]}...")
                # Try to extract remaining fields with more flexible pattern
                remaining_pattern = re.search(
                    r"""(\d+)\s+([A-Za-z''\- ]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$?([\d,]+)\s+(\S+)\s+(\S+)\s+(\S+)""",
                    line[simple_dog_match.end():]
                )
                if remaining_pattern:
                    box, form_number, raw_name, sex_age, weight = simple_dog_match.groups()
                    draw, trainer, wins, places, starts, prize, rtc, dlr, dlw = remaining_pattern.groups()
                    
                    dog_name = raw_name.strip() if raw_name else "Unknown"
                    if form_number and dog_name.startswith(form_number[-2:]):
                        dog_name = dog_name[len(form_number[-2:]):].strip()
                    
                    dog_index = len(dogs)
                    try:
                        dogs.append({
                            "Box": int(box),
                            "DogName": dog_name,
                            "FormNumber": form_number or "",
                            "Trainer": trainer.strip() if trainer else "Unknown",
                            "SexAge": sex_age if sex_age else "0d",
                            "Weight": float(weight) if weight else 30.0,
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
                        logger.info(f"[OK] Parsed dog (fallback): Box {box} - {dog_name}")
                    except Exception as e:
                        logger.warning(f"[WARNING] Fallback parse failed: {e}")
                    continue

        # Check if this is a dog name header (dog name in caps at start of line)
        # This marks the start of a dog's detailed section
        # IMPROVED: Use fuzzy/prefix matching to handle lines like "RUBY'S MATE j50s j350s t50s t350s"
        # where the dog name appears at the start but has extra lowercase text after it
        # Note: Don't require entire line to be uppercase - just check if it starts with uppercase chars
        first_word = line.split()[0] if line.split() else ""
        looks_like_header = (
            len(line) >= 3 and 
            first_word.upper() == first_word and  # First word is uppercase
            len(first_word) >= 2 and
            first_word[0].isalpha()  # Starts with a letter (not a number like race position)
        )
        
        if looks_like_header:
            # Exclude common non-dog headers
            if any(keyword in line.upper() for keyword in ['RACE', 'PRIZE', 'DISTANCE', 'TRACK', 'HORSE', 'WINNER', 'MARGIN', 'LENGTHS', 'SETTLED', 'SECOND', 'THIRD', 'FOURTH']):
                continue
            
            # Try to match this to a known dog using prefix/fuzzy matching
            line_normalized = line.replace("'", "").replace("-", " ").replace("  ", " ").strip().upper()
            
            best_match_idx = -1
            best_match_len = 0
            
            for dog_idx, dog in enumerate(dogs):
                dog_name_normalized = dog["DogName"].upper().replace("'", "").replace("-", " ").strip()
                
                # Method 1: Exact match (original behavior)
                if dog_name_normalized == line_normalized:
                    best_match_idx = dog_idx
                    best_match_len = len(dog_name_normalized)
                    break  # Exact match is best, stop searching
                
                # Method 2: Prefix match - dog name appears at the start of the line
                # E.g., "RUBYS MATE J50S J350S" starts with "RUBYS MATE"
                if line_normalized.startswith(dog_name_normalized + " ") or line_normalized.startswith(dog_name_normalized + "\t"):
                    # Only update if this is a longer/better match
                    if len(dog_name_normalized) > best_match_len:
                        best_match_idx = dog_idx
                        best_match_len = len(dog_name_normalized)
                
                # Method 3: Check if the line starts with the dog name (no space required for longer names)
                elif len(dog_name_normalized) >= 5 and line_normalized.startswith(dog_name_normalized):
                    if len(dog_name_normalized) > best_match_len:
                        best_match_idx = dog_idx
                        best_match_len = len(dog_name_normalized)
            
            if best_match_idx >= 0:
                current_dog_section_index = best_match_idx

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
                
                # DISTANCE CONVERSION: If no similar-distance times, convert from other distances
                elif ENABLE_DISTANCE_CONVERSION:
                    # Get all times with valid distances within conversion range
                    convertible_times = [
                        (time, dist) for time, dist in race_times 
                        if dist is not None and abs(dist - dog_race_distance) <= MAX_DISTANCE_CONVERSION_DIFF
                    ]
                    
                    if convertible_times:
                        # Convert each time to the target distance
                        converted_times = []
                        for orig_time, orig_dist in convertible_times:
                            converted = convert_time_to_distance(orig_time, orig_dist, dog_race_distance)
                            if converted is not None:
                                converted_times.append(converted)
                        
                        if converted_times:
                            # Use the best (fastest) converted time
                            dogs[dog_index]["BestTimeSec"] = min(converted_times)
                            # Mark as converted for transparency
                            dogs[dog_index]["TimeConverted"] = True
                            # Last3 from converted times
                            dogs[dog_index]["Last3TimesSec"] = converted_times[-3:] if len(converted_times) >= 3 else converted_times
                            logger.info(f"Converted timing for {dogs[dog_index].get('DogName', 'Unknown')}: "
                                       f"{len(convertible_times)} times from other distances -> {min(converted_times):.2f}s at {dog_race_distance}m")
        
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
                # Note: We don't convert sectional times as they're for the initial portion of the race
                # and don't scale linearly with total distance
        
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

    # Add default values for ALL missing data fields
    # This ensures Excel has values instead of blanks
    for dog in dogs:
        # If BestTimeSec is missing, use a reasonable default based on distance
        if "BestTimeSec" not in dog or dog["BestTimeSec"] is None or pd.isna(dog.get("BestTimeSec")):
            distance = dog.get("Distance", 500)
            # Rough estimate: 15-16 m/s average speed for greyhounds
            estimated_time = distance / 15.5
            dog["BestTimeSec"] = round(estimated_time, 2)
            dog["TimeEstimated"] = True  # Flag that this is an estimate
            logger.debug(f"Using estimated time for {dog.get('DogName', 'Unknown')}: {estimated_time:.2f}s at {distance}m")
        
        # If SectionalSec is missing, use a reasonable default
        if "SectionalSec" not in dog or dog["SectionalSec"] is None or pd.isna(dog.get("SectionalSec")):
            # Typical sectional (first 100-200m) is 5-8 seconds
            dog["SectionalSec"] = 6.5  # Neutral estimate
            if "TimeEstimated" not in dog:
                dog["TimeEstimated"] = True
        
        # Ensure Last3TimesSec exists
        if "Last3TimesSec" not in dog or dog["Last3TimesSec"] is None:
            dog["Last3TimesSec"] = []
        
        # Ensure TimeConverted flag exists
        if "TimeConverted" not in dog:
            dog["TimeConverted"] = False
        
        # Split SexAge field into separate Sex and Age columns
        # Format: "7d" = 7 years old, dog (male)
        # Format: "3b" = 3 years old, bitch (female)
        if 'SexAge' in dog and dog['SexAge']:
            sex_age_str = str(dog['SexAge'])
            # Extract age (numeric part) and sex (letter at the end)
            age_match = re.match(r'(\d+)([a-z])', sex_age_str.lower())
            if age_match:
                dog['Age'] = int(age_match.group(1))
                sex_letter = age_match.group(2)
                # Convert letter to readable sex: 'd' = dog (male), 'b' = bitch (female)
                dog['Sex'] = 'Dog' if sex_letter == 'd' else 'Bitch' if sex_letter == 'b' else 'Unknown'
            else:
                # Fallback if format doesn't match expected pattern
                dog['Age'] = None
                dog['Sex'] = 'Unknown'
        else:
            dog['Age'] = None
            dog['Sex'] = 'Unknown'
        
        # CRITICAL: Ensure Trainer field has value (never blank/None)
        if 'Trainer' not in dog or dog['Trainer'] is None or pd.isna(dog.get('Trainer')) or (isinstance(dog.get('Trainer'), str) and dog['Trainer'].strip() == ''):
            dog['Trainer'] = 'N/A'
        
        # Ensure numeric fields have values (never blank/None)
        numeric_fields_defaults = {
            'Weight': 0,
            'PrizeMoney': 0,
            'CareerWins': 0,
            'CareerStarts': 0
        }
        for field, default_val in numeric_fields_defaults.items():
            if field not in dog or dog[field] is None or pd.isna(dog.get(field)):
                dog[field] = default_val
    
    df = pd.DataFrame(dogs)
    
    # Normalize column names: strip whitespace and ensure consistent casing
    if len(df) > 0:
        df.columns = [str(col).strip() for col in df.columns]
    
    # CRITICAL FIX #1: Extract date from PDF filename if not in header
    # Format: TRACKDDMM (e.g., ANGLG0212 → Dec 02, 2025)
    # This enables Phase 1 features that require dates
    race_date = current_race.get('date') if current_race else None
    if not race_date and current_race and 'Track' in current_race:
        # Try to extract from typical filename pattern
        # Filenames like: ANGLG0212form.pdf → track=ANGLG, day=02, month=12
        track_code = current_race.get('Track', '').upper()
        # Look for pattern: 4-letter track code + 4 digits (DDMM)
        if len(track_code) >= 8 and track_code[:4].isalpha() and track_code[4:8].isdigit():
            day = track_code[4:6]
            month = track_code[6:8]
            # Assume year 2025 from CSV context
            race_date = f"2025-{month}-{day}"
            logger.info(f"Extracted date from filename: {race_date}")
    
    # Add RaceDate column to DataFrame for temporal features
    if race_date and len(df) > 0:
        df['RaceDate'] = race_date
        logger.info(f"Added RaceDate column: {race_date}")
    elif len(df) > 0:
        df['RaceDate'] = None  # Will be filled by CSV matching
        logger.warning("No race date extracted - will rely on CSV matching")
    
    # Log parsing results
    logger.info(f"[SUCCESS] Parsed {len(df)} dogs across {race_number} races")
    logger.info(f"[INFO] Columns in parsed DataFrame: {df.columns.tolist()}")
    
    # Check for critical columns and log warnings if missing
    critical_columns = ['Distance', 'DogName', 'Box', 'Track', 'RaceNumber']
    missing_critical = [col for col in critical_columns if col not in df.columns]
    if missing_critical:
        logger.warning(f"[WARNING] Missing critical columns: {missing_critical}")
    
    # Log sample of Distance values to verify parsing
    if 'Distance' in df.columns:
        logger.info(f"[INFO] Distance values (sample): {df['Distance'].unique()[:5].tolist()}")
    else:
        logger.error("[ERROR] 'Distance' column is MISSING from parsed DataFrame!")
    
    # Validation: Count how many dogs have timing data
    if len(df) > 0:
        best_time_count = df["BestTimeSec"].notna().sum() if "BestTimeSec" in df.columns else 0
        sec_time_count = df["SectionalSec"].notna().sum() if "SectionalSec" in df.columns else 0
        print(f"[SUCCESS] Parsed {len(df)} dogs")
        print(f"   [INFO] Timing data extracted: {best_time_count}/{len(df)} dogs have BestTimeSec, {sec_time_count}/{len(df)} have SectionalSec")
        
        if best_time_count == 0:
            print(f"   [WARNING]  WARNING: No BestTimeSec data extracted from any dog")
            logger.warning("No BestTimeSec data extracted from any dog")
        if sec_time_count == 0:
            print(f"   [WARNING]  WARNING: No SectionalSec data extracted from any dog")
            logger.warning("No SectionalSec data extracted from any dog")
        
        # CRITICAL FIX #2: Reduce "missing dogs" warnings - only warn if significantly fewer than expected
        if 'RaceNumber' in df.columns:
            for race_num in df['RaceNumber'].unique():
                race_dogs = df[df['RaceNumber'] == race_num]
                dog_count = len(race_dogs)
                # Only warn if less than 4 dogs (clearly incomplete) or more than 10 (duplicates)
                if dog_count < 4:
                    print(f"   [WARNING]  Race {race_num}: Only {dog_count} dogs parsed (expected 6-8)")
                    logger.warning(f"Race {race_num}: Only {dog_count} dogs parsed (possible missing dogs)")
                    # List the boxes that were found
                    found_boxes = sorted(race_dogs['Box'].tolist())
                    print(f"      Found boxes: {found_boxes}")
                elif dog_count > 10:
                    print(f"   [WARNING]  Race {race_num}: {dog_count} dogs parsed (expected 6-8, possible duplicates)")
                    logger.warning(f"Race {race_num}: {dog_count} dogs parsed (possible duplicates)")
    
    return df
