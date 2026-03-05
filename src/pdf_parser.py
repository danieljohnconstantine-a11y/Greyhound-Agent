"""
Comprehensive PDF parser for Australian greyhound race form guides.
Parses each dog's individual race history, times, margins and career stats.
"""
import re
import pdfplumber
import pandas as pd
from typing import List, Dict, Optional, Tuple


# ─── helpers ───────────────────────────────────────────────────────────────────

def _parse_career(text: str) -> Tuple[int, int, int]:
    """Parse 'W - P - S' or 'W-P-S' career record."""
    m = re.search(r'(\d+)\s*-\s*(\d+)\s*-\s*(\d+)', text)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 0, 0, 0


def _parse_time(text: str) -> Optional[float]:
    """Parse 'M:SS.cc' or 'SS.cc' race time to total seconds."""
    m = re.match(r'(\d+):(\d+\.\d+)', text.strip())
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m2 = re.match(r'(\d+\.\d+)', text.strip())
    if m2:
        return float(m2.group(1))
    return None


def _parse_age_sex(code: str) -> Tuple[float, str]:
    """Parse '3b' → (age_months≈36, 'B')  or '2d' → (24, 'D')."""
    m = re.match(r'(\d+)([a-zA-Z]+)', code.strip())
    if m:
        age_yrs = int(m.group(1))
        sex_code = m.group(2).upper()
        sex_map = {'B': 'B', 'D': 'D', 'BE': 'B'}
        sex = sex_map.get(sex_code, sex_code[0])
        return age_yrs * 12.0, sex
    return 24.0, 'D'


# ─── race-entry header line ────────────────────────────────────────────────────

_DOG_HEADER_RE = re.compile(
    r'^(?:E)?(\d+)\.\s*'               # box (optional E prefix)
    r'([\dxX\-]{3,8})?'               # optional form code (digits, x for scratchings, dashes)
    r"([A-Za-z'' \-]+?)\s+"           # dog name
    r'(\d[a-zA-Z]+)\s+'               # age/sex
    r'([\d.]+)kg\s+'                  # weight
    r'(\d+)\s+'                       # BP
    r"([A-Za-z'' \-]+?)\s+"          # trainer
    r'(\d+)\s*-\s*(\d+)\s*-\s*(\d+)' # career W-P-S
    r'\s+\$([\d,]+)'                  # prize
    r'\s+(\d+)'                       # RTC
    r'\s+(\d+)'                       # DLR
    r'\s+(\d+)'                       # DLW
)


def _parse_dog_header(line: str) -> Optional[Dict]:
    """Parse a Tab/dog summary line from the race card header table."""
    m = _DOG_HEADER_RE.match(line.strip())
    if not m:
        return None
    (box, form_code, raw_name, age_sex, weight, bp, trainer,
     wins, places, starts, prize, rtc, dlr, dlw) = m.groups()

    dog_name = raw_name.strip()
    age_months, sex = _parse_age_sex(age_sex)

    return {
        'Box': int(box),
        'DogName': dog_name,
        'FormCode': form_code or '',
        'Trainer': trainer.strip(),
        'AgeMonths': age_months,
        'Sex': sex,
        'Weight': float(weight),
        'BP': int(bp),
        'CareerWins': int(wins),
        'CareerPlaces': int(places),
        'CareerStarts': int(starts),
        'PrizeMoney': float(prize.replace(',', '')),
        'RTC': int(rtc),
        'DLR': int(dlr),
        'DLW': int(dlw),
    }


# ─── dog detail block ──────────────────────────────────────────────────────────

# The detail block for each dog has a header line like:
# "1. 0kg (1) bdl 2 B PAUL FAGAN  Horse: 2-12-34  6%-41% ..."
_DETAIL_HEADER_RE = re.compile(
    r'^(?:E)?(\d+)\.\s+'          # box
    r'([\d.]+)kg\s+'              # weight
    r'\((\d+)\)'                  # box position number
)

# CarPM/s line:
# "$245 $245 0.2 35/16.73 22 9 144 0 2-12-34 2-12-34 2-4-20 2-5-22 - 2-12-33"
_STATS_RE = re.compile(
    r'\$(\d+)\s+\$(\d+)\s+([\d.]+)\s+'      # CarPM, 12mPM, API
    r'(\d+)/([\d.]+)\s+'                     # RTC_raw / RTC_km
    r'(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+'      # RDistTC, DLS, DLW_dup, DOD
    r'(\d+)-(\d+)-(\d+)\s+'                  # Car W-P-S
    r'(\d+)-(\d+)-(\d+)\s+'                  # 12m W-P-S
    r'(\d+)-(\d+)-(\d+)\s+'                  # Crs W-P-S
    r'(\d+)-(\d+)-(\d+)'                     # Dist W-P-S
)

# Individual race result line (wrapped but first part is parseable):
# "2nd of 6 22/11/2025 Angle Park Margin 4.3 Lengths Distance 342m SOT G RST TG1-4W Race ..."
# "... Race Time 0:19.81 Sec Time 4.53 ..."
_RACE_LINE_RE = re.compile(
    r'^(\d+)(?:st|nd|rd|th) of (\d+)\s+'         # pos of field
    r'(\d{2}/\d{2}/\d{4})\s+'                     # date
    r'(.+?)\s+Margin\s+([\d.]+)\s+Lengths?\s+'   # track, margin
    r'Distance\s+(\d+)m\s+'                       # distance
    r'SOT\s+(\w+)'                                 # surface
)
_RACE_TIME_RE = re.compile(r'Race Time\s+([\d:]+\.[\d]+)')
_SEC_TIME_RE  = re.compile(r'Sec Time\s+([\d.]+)')
_GRADE_RE     = re.compile(r'RST\s+(\w+(?:\s+\w+)?)\s+Race\s+')
_ODDS_RE      = re.compile(r'Odds\s+([\d.]+)')


def _extract_race_results(lines: List[str], start_idx: int, end_idx: int) -> List[Dict]:
    """Extract race results from a dog's detail block lines."""
    results = []
    # Join continuation lines
    block_text = ' '.join(lines[start_idx:end_idx])

    # Split on ordinal position markers
    # e.g. "2nd of 6 22/11/2025 ..."
    parts = re.split(r'(?=\d+(?:st|nd|rd|th) of \d+\s+\d{2}/\d{2}/\d{4})', block_text)

    for part in parts:
        part = part.strip()
        m_race = _RACE_LINE_RE.match(part)
        if not m_race:
            continue

        pos = int(m_race.group(1))
        field = int(m_race.group(2))
        date = m_race.group(3)
        track = m_race.group(4).strip()
        margin = float(m_race.group(5))
        dist = int(m_race.group(6))
        surface = m_race.group(7)

        race_time_sec = None
        t = _RACE_TIME_RE.search(part)
        if t:
            race_time_sec = _parse_time(t.group(1))

        sec_time = None
        s = _SEC_TIME_RE.search(part)
        if s:
            sec_time = float(s.group(1))

        grade = 'UNK'
        g = _GRADE_RE.search(part)
        if g:
            grade = g.group(1).strip()

        odds = 0.0
        o = _ODDS_RE.search(part)
        if o:
            odds = float(o.group(1))

        results.append({
            'Pos': pos,
            'Field': field,
            'Date': date,
            'Track': track,
            'Margin': margin,
            'RaceDist': dist,
            'Surface': surface,
            'Grade': grade,
            'RaceTimeSec': race_time_sec,
            'SecTime': sec_time,
            'Odds': odds,
        })

    return results[:10]  # keep up to last 10 races


# ─── main parser ──────────────────────────────────────────────────────────────

_RACE_HEADER_RE = re.compile(
    r'^Race No\s+(\d{2})\s+(\w{3})\s+(\d{2})\s+([\d:APM]+)\s+'
    r'(.+?)\s+(\d+)m\s*$'
)
_RACE_NUM_LINE_RE = re.compile(r'^(\d{1,2})\s+\S')  # "8 RACE NAME..."


def parse_form_pdf(pdf_path: str, target_race: Optional[int] = None,
                   target_dist: Optional[int] = None) -> pd.DataFrame:
    """
    Parse a greyhound form PDF into a DataFrame.

    Each row is one dog.  All statistics come from that dog's own
    form lines; no shared/global defaults are used except where
    genuinely not present in the PDF.

    Parameters
    ----------
    pdf_path      : path to the PDF file
    target_race   : if set, only return dogs for this race number
    target_dist   : if set, only return dogs for races of this distance
    """
    text_pages: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_pages.append(t)

    full_text = '\n'.join(text_pages)
    lines = full_text.splitlines()

    # ── locate race headers ──────────────────────────────────────────────────
    race_blocks: List[Dict] = []          # {meta, lines: [str]}
    current_meta = None
    current_lines: List[str] = []

    MONTH_MAP = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5,
                 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10,
                 'Nov': 11, 'Dec': 12}

    for line_idx, line in enumerate(lines):
        m = _RACE_HEADER_RE.match(line.strip())
        if m:
            if current_meta is not None:
                current_meta['lines'] = current_lines
                race_blocks.append(current_meta)
            day, mon, yr, time_, track_name, dist_m = m.groups()
            mon_num = MONTH_MAP.get(mon, 1)
            current_meta = {
                'RaceNumber': None,        # to be filled from next line
                '_day': int(day),
                'RaceDate': f'20{yr}-{mon_num:02d}-{int(day):02d}',
                'RaceTime': time_,
                'Track': track_name.strip(),
                'Distance': int(dist_m),
                'lines': [],
                '_header_next': True,      # flag: next line has race number
            }
            current_lines = []
            continue
        if current_meta is not None:
            # First content line after the Race No header contains the race number
            if current_meta.get('_header_next'):
                nm = _RACE_NUM_LINE_RE.match(line.strip())
                if nm:
                    current_meta['RaceNumber'] = int(nm.group(1))
                current_meta['_header_next'] = False
            current_lines.append(line)

    if current_meta is not None:
        current_meta['lines'] = current_lines
        race_blocks.append(current_meta)

    # Fill in race numbers that were not captured (fallback: sequential)
    seq = 0
    for rb in race_blocks:
        seq += 1
        if rb['RaceNumber'] is None:
            rb['RaceNumber'] = seq

    # ── filter ───────────────────────────────────────────────────────────────
    if target_race is not None:
        race_blocks = [rb for rb in race_blocks if rb['RaceNumber'] == target_race]
    if target_dist is not None:
        race_blocks = [rb for rb in race_blocks if rb['Distance'] == target_dist]

    # ── parse dogs from each race block ─────────────────────────────────────
    all_dogs: List[Dict] = []

    for rb in race_blocks:
        race_meta = {k: v for k, v in rb.items() if k not in ('lines', '_header_next', '_day')}
        dogs_in_race = _parse_race_block(rb['lines'], race_meta)
        all_dogs.extend(dogs_in_race)

    df = pd.DataFrame(all_dogs)
    if df.empty:
        return df

    # Ensure numeric columns
    for col in ['Box', 'BP', 'Weight', 'CareerWins', 'CareerPlaces', 'CareerStarts',
                'PrizeMoney', 'RTC', 'DLR', 'DLW', 'Distance', 'AgeMonths']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.reset_index(drop=True)


def _parse_race_block(lines: List[str], race_meta: Dict) -> List[Dict]:
    """Parse dogs from a single race's text block."""
    dogs: List[Dict] = []

    # ── 1. collect dog header lines (the summary table rows) ────────────────
    dog_dicts: List[Dict] = []
    for line in lines:
        d = _parse_dog_header(line)
        if d:
            d.update(race_meta)
            dog_dicts.append(d)

    if not dog_dicts:
        return []

    # ── 2. find detail blocks for each dog ──────────────────────────────────
    # Detail block starts with a line like "1. 0kg (1) bdl 2 B PAUL FAGAN  Horse:"
    # We identify boundaries by matching the dog number pattern
    DETAIL_START_RE = re.compile(
        r'^(?:E)?(\d+)\.\s+([\d.]+)kg\s+\(\d+\)\s+\w+'
    )

    # Map box→start_line_idx in the lines list
    block_starts: List[Tuple[int, int]] = []  # (box_number, line_idx)
    for idx, line in enumerate(lines):
        m = DETAIL_START_RE.match(line.strip())
        if m:
            box = int(m.group(1))
            block_starts.append((box, idx))

    # ── 3. For each dog, extract their detail block ──────────────────────────
    for i, (box, start_idx) in enumerate(block_starts):
        end_idx = block_starts[i + 1][1] if i + 1 < len(block_starts) else len(lines)
        block = lines[start_idx:end_idx]

        # Find the matching dog header record
        header = next((d for d in dog_dicts if d['Box'] == box), None)
        if header is None:
            continue

        dog = dict(header)

        # Parse stats row (CarPM/s line)
        stats = _parse_stats_row(block)
        if stats:
            dog.update(stats)

        # Parse race results
        races = _extract_race_results(block, 0, len(block))
        dog['RecentRaces'] = races

        # Compute aggregates from recent races
        _enrich_from_races(dog, races)

        dogs.append(dog)

    # ── 4. Fall back for dogs without detail blocks ─────────────────────────
    # Some dogs only have header lines (e.g. emergency starters)
    dogs_with_box = {d['Box'] for d in dogs}
    for d in dog_dicts:
        if d['Box'] not in dogs_with_box:
            d['RecentRaces'] = []
            _enrich_from_races(d, [])
            dogs.append(d)

    return dogs


def _parse_stats_row(block: List[str]) -> Optional[Dict]:
    """
    Extract the CarPM/s statistics row from a dog's detail block.

    The row looks like:
      $245 $245 0.2 35/16.73 22 9 144 0 2-12-34 2-12-34 2-4-20 2-5-22 - 2-12-33

    Columns (per PDF header):
      CarPM  12mPM  API  RTC/km  RDistTC  DLS  DLW  DOD  Car  12m  Crs  Dist  ClockW  AClockW
    """
    # Find the data line following the "CarPM/s 12mPM/s API RTC/km..." header
    stats_line = None
    for i, l in enumerate(block):
        if 'CarPM' in l and 'API' in l:
            # Next line is the data
            if i + 1 < len(block):
                stats_line = block[i + 1].strip()
            break

    if not stats_line:
        # Try to find a line starting with $
        for l in block[:20]:
            l = l.strip()
            if l.startswith('$') and re.search(r'\d+-\d+-\d+', l):
                stats_line = l
                break

    if not stats_line:
        return None

    # Flexible tokenizer: split into tokens, handling "-" dashes as null values
    # Format: $CarPM $12mPM API RTC/km RDistTC DLS DLW DOD W-P-S ...
    tokens = stats_line.split()
    if len(tokens) < 8:
        return None

    result = {}

    try:
        # CarPM = $XXX
        result['CarPM'] = int(tokens[0].lstrip('$').replace(',', '')) if tokens[0].startswith('$') else 0
        # 12mPM = $XXX
        result['M12PM'] = int(tokens[1].lstrip('$').replace(',', '')) if tokens[1].startswith('$') else 0
        # API
        result['API'] = float(tokens[2]) if re.match(r'[\d.]+', tokens[2]) else 0.0
        # RTC/km e.g. "35/16.73" or "SU/0.4" or "FU/0"
        rtc_part = tokens[3] if len(tokens) > 3 else '0/0'
        parts = rtc_part.split('/')
        rtc_num_str = parts[0] if parts[0].isdigit() else '0'
        result['RTC_km'] = float(parts[1]) if len(parts) > 1 and re.match(r'[\d.]+', parts[1]) else 0.0
        result['RTC_total'] = int(rtc_num_str)
        # RDistTC
        result['RDistTC'] = int(tokens[4]) if len(tokens) > 4 and tokens[4].isdigit() else 0
        # DLS (days last start) - token 5
        result['DLS'] = int(tokens[5]) if len(tokens) > 5 and tokens[5].lstrip('-').isdigit() else 0
        # DLW (days last win) - token 6
        result['DLW_stats'] = int(tokens[6]) if len(tokens) > 6 and tokens[6].isdigit() else 0
        # DOD - token 7 (can be negative or "FU")
        # Skip DOD, start looking for W-P-S groups from token 8+
        # Parse W-P-S groups: "2-12-34" patterns
        wps_groups = []
        for tok in tokens[7:]:
            m = re.match(r'^(\d+)-(\d+)-(\d+)$', tok)
            if m:
                wps_groups.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
            # dash = missing data, skip

        # Groups order: Car, 12m, Crs, Dist, ClockW, AClockW
        # We need at least Car and want Dist
        if len(wps_groups) >= 1:
            result['CarW'], result['CarP'], result['CarS'] = wps_groups[0]
        if len(wps_groups) >= 2:
            result['M12W'], result['M12P'], result['M12S'] = wps_groups[1]
        if len(wps_groups) >= 3:
            result['CrsW'], result['CrsP'], result['CrsS'] = wps_groups[2]
        if len(wps_groups) >= 4:
            result['DistW'], result['DistP'], result['DistS'] = wps_groups[3]
        else:
            # Dist data not available separately - use course data if available
            result.setdefault('DistW', result.get('CrsW', 0))
            result.setdefault('DistP', result.get('CrsP', 0))
            result.setdefault('DistS', result.get('CrsS', 0))

    except (ValueError, IndexError):
        pass

    return result if result else None


def _enrich_from_races(dog: Dict, races: List[Dict]) -> None:
    """Derive per-dog statistics from individual race history."""
    if not races:
        # Absolute minimums from header data (still individual per dog)
        dog.setdefault('BestTimeSec', None)
        dog.setdefault('SectionalSec', None)
        dog.setdefault('Last3Positions', [])
        dog.setdefault('Last3Times', [])
        dog.setdefault('MarginLast3', [])
        dog.setdefault('AvgMargin', None)
        dog.setdefault('FormMomentumVal', 0.0)
        dog.setdefault('AvgOdds', None)
        dog.setdefault('WinFromOdds', 0)
        return

    # Sort races by date descending (most recent first)
    def date_key(r):
        try:
            parts = r['Date'].split('/')
            return (int(parts[2]), int(parts[1]), int(parts[0]))
        except Exception:
            return (0, 0, 0)

    races_sorted = sorted(races, key=date_key, reverse=True)

    # Target distance (from the current race being predicted)
    target_dist = dog.get('Distance', 530)

    # Build time-to-target-distance equivalents for all timed races
    # Scale each race time to the target distance for fair comparison.
    # Races within ±30m get exact time; others get scaled estimate.
    def _equiv_time(r):
        """Scale race time to target distance equivalent."""
        rt = r.get('RaceTimeSec')
        rd = r.get('RaceDist')
        if rt is None or not rd or rd <= 0:
            return None
        if abs(rd - target_dist) <= 30:
            return rt  # close enough — use as-is
        # Simple linear scaling; slightly conservative for longer distances
        # (dogs are proportionally slightly slower at longer distances)
        scale = (target_dist / rd)
        # Apply a small non-linear correction: longer distances are relatively slower
        if rd < target_dist:
            scale *= (1 + (target_dist - rd) / 3000.0)  # small fatigue penalty
        return round(rt * scale, 2)

    timed_races = [(r, _equiv_time(r)) for r in races_sorted]
    timed_valid = [(r, t) for r, t in timed_races if t is not None]

    # Best equivalent time (at target distance)
    if timed_valid:
        best_r, best_t = min(timed_valid, key=lambda x: x[1])
        dog['BestTimeSec'] = best_t
        dog['_BestTimeSource'] = f"{best_r.get('RaceDist')}m@{best_r.get('Track','?')} scaled→{target_dist}m"
    else:
        dog['BestTimeSec'] = None
        dog['_BestTimeSource'] = 'N/A'

    # Sectional time — only from races at similar distance (±50m)
    # Sectional times are not meaningful across very different distances
    sec_same = [r['SecTime'] for r in races_sorted
                if r.get('SecTime') and abs(r.get('RaceDist', 0) - target_dist) <= 50]
    sec_all   = [r['SecTime'] for r in races_sorted if r.get('SecTime') is not None]
    if sec_same:
        dog['SectionalSec'] = min(sec_same)
    elif sec_all:
        dog['SectionalSec'] = min(sec_all)
    else:
        dog['SectionalSec'] = None

    last3 = races_sorted[:3]
    dog['Last3Positions'] = [r['Pos'] for r in last3]
    dog['Last3Times'] = [r['RaceTimeSec'] for r in last3 if r['RaceTimeSec'] is not None]
    dog['MarginLast3'] = [r['Margin'] for r in last3]

    margins = [r['Margin'] for r in races_sorted if r.get('Margin') is not None]
    dog['AvgMargin'] = sum(margins) / len(margins) if margins else None

    # Form momentum: change in margin last 3 races (negative = improving)
    if len(dog['MarginLast3']) >= 2:
        diffs = [dog['MarginLast3'][i] - dog['MarginLast3'][i + 1]
                 for i in range(len(dog['MarginLast3']) - 1)]
        dog['FormMomentumVal'] = sum(diffs) / len(diffs)
    else:
        dog['FormMomentumVal'] = 0.0

    # Average odds (market perception)
    odds_vals = [r['Odds'] for r in races_sorted if r.get('Odds', 0) > 0]
    dog['AvgOdds'] = sum(odds_vals) / len(odds_vals) if odds_vals else None

    # Count wins at short odds (favourite)
    dog['WinFromOdds'] = sum(1 for r in races_sorted if r.get('Odds', 99) <= 3 and r['Pos'] == 1)
