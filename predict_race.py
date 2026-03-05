"""
Greyhound Race Prediction Pipeline
===================================
Full ML pipeline: PDF parsing → Feature engineering → Model prediction → Output

Usage:
    python predict_race.py [--track "Angle Park"] [--race 8] [--pdf data/ANGLG1112form.pdf]

IMPORTANT: This pipeline only works with the correct form guide PDF for the race date
you want to predict. The PDF must be placed in the data/ folder first.

For Angle Park on DD/MM/YYYY, the file is typically named:  data/ANGLG{DD}{MM}form.pdf
Example for 05 Mar 2026:  data/ANGLG0503form.pdf

Download current form guides from:
  https://www.grsa.com.au/racing/form-guides  (SA Racing)
  https://grv.racing/form-guides              (VIC Racing)
  https://www.thedogs.com.au                  (National)
"""

import os
import re
import sys
import pickle
import warnings
import argparse
import datetime
import numpy as np
import pandas as pd
import pdfplumber

warnings.filterwarnings("ignore")


def _scan_available_pdfs(data_dir: str = "data") -> None:
    """Print a clear inventory of what PDF data is actually available."""
    RACE_HDR_RE = re.compile(
        r"Race No\s+(\d{1,2})\s+(\w{3})\s+(\d{2})\s+(\d{1,2}:\d{2}(?:AM|PM))\s+(.+?)\s+(\d+)m",
        re.IGNORECASE,
    )
    pdfs = sorted(f for f in os.listdir(data_dir) if f.lower().endswith(".pdf"))
    if not pdfs:
        print("  ❌  data/ folder is empty — no form guides available.")
        return
    print(f"  📁  data/ folder contains {len(pdfs)} PDF file(s):")
    for fname in pdfs:
        try:
            with pdfplumber.open(os.path.join(data_dir, fname)) as pdf:
                text = (pdf.pages[0].extract_text() or "")
            m = RACE_HDR_RE.search(text)
            if m:
                day, mon, yr, time_, track, dist = m.groups()
                yr4 = int("20" + yr)
                try:
                    mon_num = datetime.datetime.strptime(mon.capitalize(), "%b").month
                    race_date = datetime.date(yr4, mon_num, int(day))
                    date_str = race_date.strftime("%d %b %Y")
                except ValueError:
                    date_str = f"{day} {mon} 20{yr}"
                print(f"       {fname}  →  {date_str}  {track}")
            else:
                print(f"       {fname}  →  (date unknown)")
        except Exception:
            print(f"       {fname}  →  (unreadable)")


def _abort_wrong_date(race_date_str: str, requested_date_str: str | None) -> None:
    """
    Raise a clear error if the PDF's race date does not match today (or requested date).
    race_date_str: 'YYYY-MM-DD' from parsed PDF
    requested_date_str: 'YYYY-MM-DD' from --date arg (or None = use today)
    """
    today = datetime.date.today()
    target = today if not requested_date_str else datetime.date.fromisoformat(requested_date_str)
    try:
        pdf_date = datetime.date.fromisoformat(race_date_str)
    except ValueError:
        return  # can't parse, let it through

    if pdf_date != target:
        sep = "!" * 80
        print(f"\n{sep}")
        print(f"  ❌  WRONG DATE — THIS IS NOT TODAY'S RACE CARD")
        print(f"  ❌  PDF race date : {pdf_date.strftime('%d %b %Y')}")
        print(f"  ❌  Target date   : {target.strftime('%d %b %Y')}")
        print(f"{sep}")
        print()
        print("  The dogs listed in this PDF are NOT competing today.")
        print("  Running predictions on the wrong date produces meaningless results.")
        print()
        print("  You need the form guide PDF for the correct date.")
        print(f"  For Angle Park on {target.strftime('%d %b %Y')}, the file name is likely:")
        print(f"      data/ANGLG{target.strftime('%d%m')}form.pdf")
        print()
        print("  Download it from one of these sources, then re-run:")
        print("      https://www.grsa.com.au/racing/form-guides   (SA Racing)")
        print("      https://www.thedogs.com.au                   (National)")
        print()
        print("  Available PDFs in data/:")
        _scan_available_pdfs()
        print()
        print(f"{sep}")
        sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# 1. PDF PARSER
# ──────────────────────────────────────────────────────────────────────────────

MONTHS = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}

# Regex for race header:  "Race No 11 Dec 25 06:37PM Angle Park 530m"
RACE_HDR_RE = re.compile(
    r"Race No\s+(\d{1,2})\s+(\w{3})\s+(\d{2})\s+(\d{1,2}:\d{2}(?:AM|PM))\s+(.+?)\s+(\d+)m",
    re.IGNORECASE,
)

# Regex for dog entry line:
#   "1. 36361Our Little Force 2d 0.0kg 1 Karen Wittholz 4 - 22 - 54 $11,325 55 10 10"
#   Box / Form / Name / Sex+Age / Weight / BoxPos / Trainer / W-P-S / Prize / RTC / DLR / DLW
DOG_LINE_RE = re.compile(
    r"^(\d{1,2})\.\s*"           # box number
    r"([0-9x]{3,8})?"            # optional form digits
    r"([A-Za-z''\-\. ]{2,40}?)" # dog name (lazy)
    r"\s+(\d+[a-zA-Z])"         # sex/age e.g. 2d, 3b
    r"\s+([\d.]+)kg"             # weight
    r"\s+(\d{1,2})"              # box position (BP / Draw)
    r"\s+([A-Za-z''\-\. ]{2,40})" # trainer name
    r"\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)"  # W - P - S
    r"\s+\$([\d,]+)"             # prize money
    r"\s+(\d+)"                  # RTC
    r"\s+(\d+)"                  # DLR
    r"\s+(\d+|Mdn)",             # DLW (or "Mdn" for maiden)
)

# Regex to extract race time from history:  "Race Time 0:31.17 Sec Time 5.37"
RACE_TIME_RE = re.compile(r"Race Time\s+\d+:(\d+\.\d+)\s+Sec Time\s+(\d+\.\d+)")

# Regex to extract margin from history:  "Margin 0.1 Lengths"
MARGIN_RE = re.compile(r"Margin\s+([\d.]+)\s+Lengths")

# Regex to extract distance from history line:  "Distance 530m"
HIST_DIST_RE = re.compile(r"\bDistance\s+(\d+)m\b")

# Regex to extract finish position:  "1st of 6" / "6th of 6"
POSITION_RE = re.compile(r"^(\d+)(?:st|nd|rd|th)\s+of\s+(\d+)")


def _clean_name(raw: str) -> str:
    return " ".join(raw.strip().split())


def parse_angle_park_pdf(pdf_path: str) -> list[dict]:
    """
    Parse an Angle Park (or compatible) race-card PDF.
    Returns a list of race dicts, each containing a 'dogs' list.
    """
    text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            text_pages.append(t or "")

    full_text = "\n".join(text_pages)
    lines = full_text.splitlines()

    races: list[dict] = []
    current_race: dict | None = None
    current_dog: dict | None = None
    race_counter = 0

    # We'll collect (position, margin, race_time_sec, sectional_sec)
    # from the dog history block that follows each dog entry.

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # ── Race header ──────────────────────────────────────────────────────
        m = RACE_HDR_RE.match(line)
        if m:
            day, mon, yr, time_, track_raw, dist = m.groups()
            year = int("20" + yr)
            month = MONTHS.get(mon.capitalize(), "01")
            race_date = f"{year}-{month}-{day.zfill(2)}"
            race_counter += 1
            current_race = {
                "RaceNumber": race_counter,
                "RaceDate": race_date,
                "RaceTime": time_.upper(),
                "Track": track_raw.strip(),
                "Distance": int(dist),
                "RaceName": "",
                "dogs": [],
            }
            races.append(current_race)
            current_dog = None
            i += 1
            # Next non-empty line is usually race name
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                next_line = lines[i].strip()
                # Race name typically starts with a digit (race num) then name
                if re.match(r"^\d+\s+", next_line):
                    current_race["RaceName"] = next_line
                    i += 1
            continue

        # ── Dog entry ────────────────────────────────────────────────────────
        if current_race is not None:
            dm = DOG_LINE_RE.match(line)
            if dm:
                (box, form, raw_name, sex_age, weight, draw,
                 trainer, wins, places, starts, prize, rtc, dlr, dlw) = dm.groups()

                dlw_val = 999 if (dlw or "").upper() == "MDN" else int(dlw or 0)
                age_match = re.match(r"(\d+)[a-zA-Z]", sex_age or "")
                age_years = int(age_match.group(1)) if age_match else 2

                current_dog = {
                    "Box":          int(box),
                    "FormDigits":   form or "",
                    "DogName":      _clean_name(raw_name),
                    "SexAge":       sex_age or "",
                    "AgeYears":     age_years,
                    "Weight":       float(weight),
                    "Draw":         int(draw),
                    "Trainer":      _clean_name(trainer),
                    "CareerWins":   int(wins),
                    "CareerPlaces": int(places),
                    "CareerStarts": int(starts),
                    "PrizeMoney":   float(prize.replace(",", "")),
                    "RTC":          int(rtc),
                    "DLR":          int(dlr),
                    "DLW":          dlw_val,
                    "Distance":     current_race["Distance"],
                    "Track":        current_race["Track"],
                    "RaceNumber":   current_race["RaceNumber"],
                    "RaceDate":     current_race["RaceDate"],
                    "RaceTime":     current_race["RaceTime"],
                    # History — filled below
                    "_race_times":  [],   # list of (time_sec, sec_time)
                    "_margins":     [],   # list of floats
                    "_positions":   [],   # list of (pos, field_size)
                }
                current_race["dogs"].append(current_dog)
                i += 1
                continue

        # ── Dog history lines (after a dog entry) ────────────────────────────
        if current_dog is not None:
            # Race result history line: starts with "1st of 6", "2nd of 5", etc.
            pm = POSITION_RE.match(line)
            if pm:
                pos, field = int(pm.group(1)), int(pm.group(2))
                current_dog["_positions"].append((pos, field))

                # Combine current line + next line (history lines are often wrapped)
                combined = line
                if i + 1 < len(lines):
                    combined = line + " " + lines[i + 1].strip()

                # Only use times from races at the same distance (±30m)
                dm_hist = HIST_DIST_RE.search(combined)
                hist_dist = int(dm_hist.group(1)) if dm_hist else current_dog["Distance"]
                same_dist = abs(hist_dist - current_dog["Distance"]) <= 30

                mm = MARGIN_RE.search(combined)
                if mm:
                    current_dog["_margins"].append(float(mm.group(1)))

                if same_dist:
                    tm = RACE_TIME_RE.search(combined)
                    if tm:
                        rt = float(tm.group(1))
                        st = float(tm.group(2))
                        # Sanity check: time must be realistic for the distance
                        min_t = current_dog["Distance"] / 20.0
                        max_t = current_dog["Distance"] / 14.0
                        if min_t <= rt <= max_t:
                            current_dog["_race_times"].append((rt, st))

        i += 1

    return races


# ──────────────────────────────────────────────────────────────────────────────
# 2. FEATURE ENGINEERING (74 features required by the model)
# ──────────────────────────────────────────────────────────────────────────────

# Angle Park 530m box historical win/place statistics
# (approximate values from publicly available SA track statistics)
AP530_BOX_WINS  = {1: 0.155, 2: 0.140, 3: 0.130, 4: 0.120,
                    5: 0.115, 6: 0.110, 7: 0.105, 8: 0.105,
                    9: 0.105, 10: 0.105}
AP530_BOX_PLACE = {1: 0.450, 2: 0.420, 3: 0.400, 4: 0.390,
                    5: 0.385, 6: 0.375, 7: 0.360, 8: 0.360,
                    9: 0.360, 10: 0.355}
AP530_BOX_TOP3  = {1: 0.480, 2: 0.460, 3: 0.440, 4: 0.430,
                    5: 0.420, 6: 0.410, 7: 0.395, 8: 0.395,
                    9: 0.390, 10: 0.385}


def _grade_factor(race_name: str) -> float:
    rn = race_name.upper()
    if "OPEN" in rn or "GR 1" in rn:
        return 1.0
    if "GR 2" in rn:
        return 0.9
    if "GR 3" in rn or "GR 4" in rn:
        return 0.8
    if "GR 5" in rn or "GR 6" in rn:
        return 0.7
    if "MDN" in rn or "MAIDEN" in rn:
        return 0.5
    return 0.65


def build_features(dogs: list[dict], race_name: str = "", distance: int = 530) -> pd.DataFrame:
    """
    Compute all 74 features for every dog in a race field.
    Returns a DataFrame ready for the scaler + ML model.
    """
    rows = []
    for d in dogs:
        w   = d["CareerWins"]
        p   = d["CareerPlaces"]
        s   = d["CareerStarts"]
        pm  = d["PrizeMoney"]
        rtc = d["RTC"]
        dlr = d["DLR"]
        dlw = d["DLW"]
        box = d["Box"]
        draw = d["Draw"]
        dist = d["Distance"]
        age_y = d.get("AgeYears", 2)

        # ── Times ──────────────────────────────────────────────────────────
        times_at_dist = [rt for rt, _ in d["_race_times"]]
        sect_times    = [st for _, st in d["_race_times"]]

        # Best time at current distance
        if times_at_dist:
            best_time = min(times_at_dist)
            avg_time  = np.mean(times_at_dist)
        else:
            # Fallback: estimate from distance (typical Angle Park 530m ~31.0s)
            best_time = 31.0 if dist == 530 else (dist / 17.1)
            avg_time  = best_time + 0.2

        if sect_times:
            sect_time = np.mean(sect_times)
        else:
            sect_time = 5.30 if dist == 530 else (dist / 100.0)

        # ── Margins ────────────────────────────────────────────────────────
        margins = d["_margins"][:6]  # take up to 6 recent margins
        if margins:
            margin_avg  = np.mean(margins)
            form_mom    = float(np.mean(np.diff(margins))) if len(margins) >= 2 else 0.0
        else:
            margin_avg  = 5.0
            form_mom    = 0.0

        # ── Position history ───────────────────────────────────────────────
        positions = d["_positions"][:6]  # recent results
        if positions:
            last3_avg = np.mean([p for p, _ in positions[:3]]) if len(positions) >= 1 else 4.0
        else:
            last3_avg = 4.0

        # Form digits (e.g. "36361") → last result is the rightmost digit
        form_str = d.get("FormDigits", "")
        form_digits = [int(c) for c in form_str if c.isdigit()][-5:]

        # Win/place streak from form digits
        win_streak = 0
        for fd in reversed(form_digits):
            if fd == 1:
                win_streak += 1
            else:
                break

        place_streak = 0
        for fd in reversed(form_digits):
            if fd <= 3:
                place_streak += 1
            else:
                break

        # Closer bonus: dog improved position recently
        closer = 1 if (len(form_digits) >= 2 and form_digits[-1] < form_digits[-2]) else 0

        # ── Derived metrics ────────────────────────────────────────────────
        consistency   = w / s if s > 0 else 0.0
        place_rate    = (w + p) / s if s > 0 else 0.0
        win_place_rate = place_rate

        speed_kmh      = (dist / best_time) * 3.6
        early_speed    = dist / sect_time if sect_time > 0 else dist / 5.3

        finish_cons = float(np.std(times_at_dist)) if len(times_at_dist) >= 2 else 0.5

        # DLW factor: higher = better recent form
        dlw_factor = max(0.0, 1.0 - dlw / 30.0) if dlw < 999 else 0.0

        # Freshness / rest
        if dlr <= 5:
            recent_form_boost = 1.0 if w > 0 else 0.5
            freshness = 1.0
        elif dlr <= 10:
            recent_form_boost = 0.5
            freshness = 0.8
        elif dlr <= 21:
            recent_form_boost = 0.2
            freshness = 0.6
        else:
            recent_form_boost = 0.0
            freshness = 0.3

        freshness_v2 = 1.0 / (1.0 + dlr / 14.0)

        # Weight factor
        weight_val  = d["Weight"] if d["Weight"] > 0 else 32.0
        weight_factor = weight_val / 34.0

        # Draw / box factors
        draw_factor = 1.0 - (draw - 1) * 0.02  # slight penalty per position
        box_pos_bias = AP530_BOX_WINS.get(box, 0.10)
        box_place_rt = AP530_BOX_PLACE.get(box, 0.38)
        box_top3_rt  = AP530_BOX_TOP3.get(box, 0.40)
        box_penalty  = max(0.0, (box - 4) * 0.02)  # penalty for wide draws

        # Track-specific box adjustments (Angle Park 530m)
        track_box1 = 1.05 if box == 1 else 1.0
        track_box4 = 1.02 if box == 4 else 1.0
        track_comp = track_box1 * track_box4

        # Rail preference (simplified: inner boxes preferred)
        rail_pref = max(0.0, 1.0 - (box - 1) * 0.05)

        # Age factors
        age_months = age_y * 12
        age_factor = 1.0 if 24 <= age_months <= 48 else (0.8 if age_months < 24 else 0.7)
        age_factor_v2 = 1.0 - abs(age_months - 36) / 60.0

        # Overexposure
        overexposed = -0.1 if s > 80 else 0.0

        # Experience tier
        if s < 10:
            exp_tier = 0
        elif s < 30:
            exp_tier = 1
        elif s < 60:
            exp_tier = 2
        else:
            exp_tier = 3

        # Distance suitability (530m is a key Angle Park distance)
        dist_suit = 1.0 if dist in [530, 515, 595] else 0.7

        # Class / grade rating
        class_rating = pm / (s * 500 + 1) if s > 0 else 0.0
        grade_factor = _grade_factor(race_name)

        # Trainer-based factors (approximate from available data)
        trainer_sr   = w / max(s, 1) * 1.5  # rough trainer proxy
        trainer_tier = 1 if trainer_sr > 0.15 else (0.5 if trainer_sr > 0.08 else 0.2)
        trainer_mom  = place_rate * freshness

        # Speed classification (0-3)
        if speed_kmh > 63:
            speed_cls = 3
        elif speed_kmh > 61:
            speed_cls = 2
        elif speed_kmh > 59:
            speed_cls = 1
        else:
            speed_cls = 0

        # Speed at distance (normalised)
        speed_at_dist = speed_kmh / 65.0

        # Surface preference (all these races are on artificial/synthetic)
        surface_pref = 1.0

        # Win streak factors
        win_streak_factor    = min(1.0, win_streak * 0.2)
        win_streak_factor_v2 = 1.0 if win_streak >= 2 else (0.5 if win_streak == 1 else 0.0)

        recent_place_streak = place_streak

        # Form momentum (normalised)
        form_mom_norm = np.tanh(form_mom / 3.0)

        # Margin factor
        margin_factor = max(0.0, 1.0 - margin_avg / 10.0)

        # RTC factor (experience at this course)
        rtc_factor = min(1.0, rtc / 50.0)

        # Distance change factor (we don't know last distance, use 1.0)
        dist_change_factor = 1.0

        # Last3FinishFactor
        last3_finish_factor = max(0.0, 1.0 - (last3_avg - 1) / 6.0)

        # Pace box factor (inner boxes pace better in greyhound racing)
        pace_box = 1.0 - (box - 1) * 0.03

        # Traditional FinalScore (used as a feature — same formula as scorer)
        w_early = 0.20; w_speed = 0.15; w_consist = 0.20
        w_fin_c = 0.10; w_prize = 0.10; w_rfb = 0.10
        w_box   = 0.05; w_trn   = 0.05; w_dist  = 0.05; w_tc = 0.05
        final_score = (
            early_speed  * w_early +
            speed_kmh    * w_speed +
            consistency  * w_consist +
            finish_cons  * w_fin_c +
            (pm / 1000)  * w_prize +
            recent_form_boost * w_rfb +
            box_pos_bias * w_box +
            trainer_sr   * w_trn +
            dist_suit    * w_dist +
            1.0          * w_tc +  # TrackConditionAdj = 1.0 (Good)
            overexposed
        )

        rows.append({
            "Box":                      box,
            "Weight":                   weight_val,
            "Draw":                     draw,
            "CareerWins":               w,
            "CareerPlaces":             p,
            "CareerStarts":             s,
            "PrizeMoney":               pm,
            "RTC":                      rtc,
            "DLR":                      dlr,
            "DLW":                      dlw if dlw < 999 else 999,
            "Distance":                 dist,
            "BestTimeSec":              best_time,
            "SectionalSec":             sect_time,
            "BoxBiasFactor":            box_pos_bias,
            "TrackConditionAdj":        1.0,
            "RestFactor":               freshness,
            "Speed_kmh":                speed_kmh,
            "EarlySpeedIndex":          early_speed,
            "FinishConsistency":        finish_cons,
            "MarginAvg":                margin_avg,
            "FormMomentum":             form_mom,
            "ConsistencyIndex":         consistency,
            "RecentFormBoost":          recent_form_boost,
            "DistanceSuit":             dist_suit,
            "TrainerStrikeRate":        trainer_sr,
            "OverexposedPenalty":       overexposed,
            "PlaceRate":                place_rate,
            "DLWFactor":                dlw_factor,
            "WeightFactor":             weight_factor,
            "DrawFactor":               draw_factor,
            "FormMomentumNorm":         form_mom_norm,
            "MarginFactor":             margin_factor,
            "RTCFactor":                rtc_factor,
            "BoxPositionBias":          box_pos_bias,
            "BoxPlaceRate":             box_place_rt,
            "BoxTop3Rate":              box_top3_rt,
            "TrackBox1Adjustment":      track_box1,
            "TrackBox4Adjustment":      track_box4,
            "TrackComprehensiveAdjustment": track_comp,
            "AgeMonths":                age_months,
            "AgeFactor":                age_factor,
            "RailPreference":           rail_pref,
            "BoxPenaltyFactor":         box_penalty,
            "SpeedAtDistance":          speed_at_dist,
            "SpeedClassification":      speed_cls,
            "ExperienceTier":           exp_tier,
            "WinStreakFactor":          win_streak_factor,
            "FreshnessFactor":          freshness,
            "ClassRating":              class_rating,
            "GradeFactor":              grade_factor,
            "Last3AvgFinish":           last3_avg,
            "Last3FinishFactor":        last3_finish_factor,
            "DistanceChangeFactor":     dist_change_factor,
            "PaceBoxFactor":            pace_box,
            "TrainerTier":              trainer_tier,
            "FreshnessFactorV2":        freshness_v2,
            "AgeFactorV2":              age_factor_v2,
            "SurfacePreferenceFactor":  surface_pref,
            "WinPlaceRate":             win_place_rate,
            # Field-level percentiles — filled after building full field df
            "EarlySpeedPercentile":     0.0,
            "BestTimePercentile":       0.0,
            "FieldSpeedStd":            0.0,
            "FieldTimeStd":             0.0,
            "FieldSimilarityIndex":     0.0,
            "TrackUpsetFactor":         0.0,
            "CompetitorDensity":        0.0,
            "CompetitorAdjustment":     0.0,
            "FieldSize":                float(len(dogs)),
            "FieldSizeAdjustment":      1.0 / len(dogs) if dogs else 0.0,
            "WinStreakFactorV2":        win_streak_factor_v2,
            "RecentPlaceStreak":        float(recent_place_streak),
            "CloserBonus":              float(closer),
            "TrainerMomentum":          trainer_mom,
            "FinalScore":               final_score,
            # Metadata (not fed to model)
            "_DogName":   d["DogName"],
            "_Trainer":   d["Trainer"],
            "_SexAge":    d.get("SexAge", ""),
            "_FormDigits": d.get("FormDigits", ""),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # ── Field-level features (need all dogs in race) ──────────────────────
    speeds  = df["Speed_kmh"].values
    times   = df["BestTimeSec"].values
    early   = df["EarlySpeedIndex"].values

    df["FieldSpeedStd"]       = float(np.std(speeds))
    df["FieldTimeStd"]        = float(np.std(times))
    df["FieldSimilarityIndex"] = 1.0 / (1.0 + np.std(speeds))

    # Percentile rank (0 = slowest, 1 = fastest)
    from scipy.stats import rankdata
    df["EarlySpeedPercentile"] = rankdata(early) / len(early)
    df["BestTimePercentile"]   = 1.0 - rankdata(times) / len(times)  # lower time = better

    # Competitor density (how many dogs are within 5% of top speed)
    top_speed = speeds.max()
    df["CompetitorDensity"]    = float(np.sum(speeds >= top_speed * 0.95))
    df["CompetitorAdjustment"] = speeds / (top_speed + 1e-9)

    # Track upset factor — higher variance = higher upset potential
    speed_cv = np.std(speeds) / (np.mean(speeds) + 1e-9)
    df["TrackUpsetFactor"] = float(speed_cv)

    return df


# ──────────────────────────────────────────────────────────────────────────────
# 3. MODEL LOADING
# ──────────────────────────────────────────────────────────────────────────────

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))


def load_models(track: str = "Angle Park") -> dict:
    """Load RF, GB (and XGB if available) models + scaler for a given track."""
    models = {}
    for model_type in ("rf", "gb", "xgb"):
        path = os.path.join(MODEL_DIR, f"{track}_{model_type}.pkl")
        if os.path.exists(path):
            with open(path, "rb") as fh:
                models[model_type] = pickle.load(fh)
            print(f"  ✅ Loaded {path}")
        else:
            print(f"  ⚠️  Model not found: {path}")

    scaler_path = os.path.join(MODEL_DIR, f"{track}_scaler.pkl")
    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as fh:
            models["scaler"] = pickle.load(fh)
        print(f"  ✅ Loaded {scaler_path}")
    else:
        print(f"  ❌ Scaler not found: {scaler_path}")
        models["scaler"] = None

    return models


# ──────────────────────────────────────────────────────────────────────────────
# 4. PREDICTION
# ──────────────────────────────────────────────────────────────────────────────

FEATURE_COLS = [
    "Box", "Weight", "Draw", "CareerWins", "CareerPlaces", "CareerStarts",
    "PrizeMoney", "RTC", "DLR", "DLW", "Distance", "BestTimeSec",
    "SectionalSec", "BoxBiasFactor", "TrackConditionAdj", "RestFactor",
    "Speed_kmh", "EarlySpeedIndex", "FinishConsistency", "MarginAvg",
    "FormMomentum", "ConsistencyIndex", "RecentFormBoost", "DistanceSuit",
    "TrainerStrikeRate", "OverexposedPenalty", "PlaceRate", "DLWFactor",
    "WeightFactor", "DrawFactor", "FormMomentumNorm", "MarginFactor",
    "RTCFactor", "BoxPositionBias", "BoxPlaceRate", "BoxTop3Rate",
    "TrackBox1Adjustment", "TrackBox4Adjustment", "TrackComprehensiveAdjustment",
    "AgeMonths", "AgeFactor", "RailPreference", "BoxPenaltyFactor",
    "SpeedAtDistance", "SpeedClassification", "ExperienceTier",
    "WinStreakFactor", "FreshnessFactor", "ClassRating", "GradeFactor",
    "Last3AvgFinish", "Last3FinishFactor", "DistanceChangeFactor",
    "PaceBoxFactor", "TrainerTier", "FreshnessFactorV2", "AgeFactorV2",
    "SurfacePreferenceFactor", "WinPlaceRate", "EarlySpeedPercentile",
    "BestTimePercentile", "FieldSpeedStd", "FieldTimeStd",
    "FieldSimilarityIndex", "TrackUpsetFactor", "CompetitorDensity",
    "CompetitorAdjustment", "FieldSize", "FieldSizeAdjustment",
    "WinStreakFactorV2", "RecentPlaceStreak", "CloserBonus",
    "TrainerMomentum", "FinalScore",
]


def predict_race(df: pd.DataFrame, models: dict) -> pd.DataFrame:
    """Run all available models and ensemble the win probabilities."""
    scaler = models.get("scaler")
    if scaler is None:
        raise RuntimeError("Scaler not loaded — cannot normalise features.")

    X = df[FEATURE_COLS].fillna(0).values
    X_scaled = scaler.transform(X)

    proba_cols = {}
    for name in ("rf", "gb", "xgb"):
        m = models.get(name)
        if m is None:
            continue
        try:
            proba = m.predict_proba(X_scaled)
            # class 1 = win (most models trained as binary win/not-win)
            if proba.shape[1] >= 2:
                proba_cols[f"P_win_{name}"] = proba[:, 1]
            else:
                proba_cols[f"P_win_{name}"] = proba[:, 0]
        except Exception as e:
            print(f"  ⚠️  {name} prediction failed: {e}")

    if not proba_cols:
        raise RuntimeError("No model produced predictions.")

    result = df[["_DogName", "_Trainer", "_SexAge", "_FormDigits",
                 "Box", "Draw", "CareerWins", "CareerPlaces",
                 "CareerStarts", "PrizeMoney", "DLR", "DLW",
                 "BestTimeSec", "Speed_kmh", "FinalScore"]].copy()
    result.rename(columns={
        "_DogName": "DogName",
        "_Trainer": "Trainer",
        "_SexAge":  "SexAge",
        "_FormDigits": "Form",
    }, inplace=True)

    for col, vals in proba_cols.items():
        result[col] = vals

    # Ensemble (equal weight of available models)
    p_cols = [c for c in result.columns if c.startswith("P_win_")]
    result["P_win_ensemble"] = result[p_cols].mean(axis=1)

    # Normalise to sum to 1 within race
    total = result["P_win_ensemble"].sum()
    if total > 0:
        result["P_win_pct"] = (result["P_win_ensemble"] / total * 100).round(2)
    else:
        result["P_win_pct"] = (100.0 / len(result))

    result.sort_values("P_win_ensemble", ascending=False, inplace=True)
    result.reset_index(drop=True, inplace=True)
    result.index += 1  # 1-based ranking
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 5. MAIN PIPELINE
# ──────────────────────────────────────────────────────────────────────────────

def print_race_card(race: dict, result: pd.DataFrame):
    dist = race["Distance"]
    sep  = "═" * 80
    print(f"\n{sep}")
    print(f"  🏟  RACE {race['RaceNumber']}  │  {race['RaceDate']} {race['RaceTime']}")
    print(f"  📍 {race['Track']}  │  {dist}m")
    if race.get("RaceName"):
        print(f"  📋 {race['RaceName']}")
    print(sep)

    hdr = (f"{'Rank':<5} {'Box':<5} {'Dog Name':<26} {'Form':<8} "
           f"{'W-P-S':<12} {'Prize $':>8} {'BestT':>7} "
           f"{'RF%':>7} {'GB%':>7} {'ENS%':>7} {'Win%':>7}")
    print(hdr)
    print("─" * 80)

    for rank, row in result.iterrows():
        w = int(row.CareerWins); p = int(row.CareerPlaces); ss = int(row.CareerStarts)
        wps = f"{w}-{p}-{ss}"
        rf_pct  = f"{row.get('P_win_rf',  0)*100:.1f}" if "P_win_rf"  in result.columns else "  -"
        gb_pct  = f"{row.get('P_win_gb',  0)*100:.1f}" if "P_win_gb"  in result.columns else "  -"
        xgb_pct = f"{row.get('P_win_xgb', 0)*100:.1f}" if "P_win_xgb" in result.columns else None
        ens_pct = f"{row['P_win_ensemble']*100:.1f}"
        win_pct = f"{row['P_win_pct']:.1f}"

        line = (f"{rank:<5} {int(row.Box):<5} {row.DogName:<26} {row.Form or '─':<8} "
                f"{wps:<12} {int(row.PrizeMoney):>8,} {row.BestTimeSec:>7.2f} "
                f"{rf_pct:>7} {gb_pct:>7} {ens_pct:>7} {win_pct:>6}%")
        if rank == 1:
            line = "🥇 " + line
        elif rank == 2:
            line = "🥈 " + line
        elif rank == 3:
            line = "🥉 " + line
        else:
            line = "   " + line
        print(line)

    print("─" * 80)
    top = result.iloc[0]
    print(f"\n  ✅ TOP PICK  →  Box {int(top.Box)} {top.DogName}"
          f"  (win prob {top['P_win_pct']:.1f}%)")

    if len(result) >= 3:
        q1 = result.iloc[0]
        q2 = result.iloc[1]
        q3 = result.iloc[2]
        print(f"  📌 QUINELLA  →  {int(q1.Box)} {q1.DogName} / {int(q2.Box)} {q2.DogName}")
        print(f"  📌 TRIFECTA  →  {int(q1.Box)}-{int(q2.Box)}-{int(q3.Box)}"
              f"  ({q1.DogName} / {q2.DogName} / {q3.DogName})")

    print()


def main():
    parser = argparse.ArgumentParser(description="Greyhound Race Prediction Pipeline")
    parser.add_argument("--track",  default="Angle Park", help="Track name matching model file prefix")
    parser.add_argument("--pdf",    default=None,         help="Path to race-card PDF")
    parser.add_argument("--race",   type=int, default=None, help="Race number to show (default: all)")
    parser.add_argument("--dist",   type=int, default=None, help="Filter by distance (e.g. 530)")
    parser.add_argument("--date",   default=None,         help="Expected race date YYYY-MM-DD (default: today). Used to verify correct PDF.")
    parser.add_argument("--force",  action="store_true",  help="Skip date validation (use for historical/testing purposes ONLY)")
    parser.add_argument("--output", default="outputs",    help="Output directory")
    args = parser.parse_args()

    print("\n" + "═" * 80)
    print("  🐾  GREYHOUND ANALYTICS — FULL ML PREDICTION PIPELINE")
    print("═" * 80)

    # ── Show what data is actually available ──────────────────────────────────
    print("\n── AVAILABLE FORM GUIDES IN data/ ─────────────────────────────────────────")
    _scan_available_pdfs()

    today = datetime.date.today()
    target_date = today if not args.date else datetime.date.fromisoformat(args.date)
    print(f"\n  📅  Target race date: {target_date.strftime('%d %b %Y')}")

    # ── Find PDF ──────────────────────────────────────────────────────────────
    pdf_path = args.pdf
    if not pdf_path:
        # Auto-detect: look for a PDF matching the target date by filename convention
        # Angle Park naming: ANGLG{DD}{MM}form.pdf
        data_dir = "data"
        expected_name = f"ANGLG{target_date.strftime('%d%m')}form.pdf"
        expected_path = os.path.join(data_dir, expected_name)
        if os.path.exists(expected_path):
            pdf_path = expected_path
            print(f"  ✅  Found matching PDF: {pdf_path}")
        else:
            sep = "!" * 80
            print(f"\n{sep}")
            print(f"  ❌  NO FORM GUIDE FOUND FOR {target_date.strftime('%d %b %Y')}")
            print(f"  ❌  Expected file: {expected_path}")
            print(f"{sep}")
            print()
            print("  Cannot predict races without the correct form guide.")
            print("  Download the form guide PDF and save it as:")
            print(f"      {expected_path}")
            print()
            print("  Download sources:")
            print("      https://www.grsa.com.au/racing/form-guides   (SA Racing — Angle Park)")
            print("      https://www.thedogs.com.au                   (National)")
            print()
            sys.exit(1)

    print(f"\n📄  PDF: {pdf_path}")
    print(f"🏟  Track: {args.track}")

    # ── Parse PDF ─────────────────────────────────────────────────────────────
    print("\n── STEP 1: Parsing race card ──────────────────────────────────────────────")
    races = parse_angle_park_pdf(pdf_path)
    print(f"  ✅ Parsed {len(races)} races from PDF")

    if not races:
        print("❌  Could not parse any races from this PDF.")
        sys.exit(1)

    # ── DATE VALIDATION — check PDF actually matches target date ──────────────
    if not args.force:
        first_race_date = races[0].get("RaceDate", "")
        _abort_wrong_date(first_race_date, target_date.isoformat())

    # Filter by distance if requested
    all_races_before_filter = races[:]
    if args.dist:
        races = [r for r in races if r["Distance"] == args.dist]
        print(f"  🔍 Filtered to {len(races)} races at {args.dist}m")

    # Filter by race number if requested
    if args.race:
        search_pool = races if args.dist else all_races_before_filter
        races_filtered = [r for r in search_pool if r["RaceNumber"] == args.race]
        if not races_filtered:
            available = [r["RaceNumber"] for r in all_races_before_filter]
            print(f"  ⚠️  Race {args.race} not found in this PDF.")
            print(f"  ⚠️  Available race numbers: {available}")
            sys.exit(1)
        races = races_filtered

    if not races:
        print("❌  No races matched your filters.")
        sys.exit(1)

    # ── Load models ───────────────────────────────────────────────────────────
    print("\n── STEP 2: Loading ML models ──────────────────────────────────────────────")
    models = load_models(args.track)
    if "scaler" not in models or models["scaler"] is None:
        print("❌  Could not load scaler. Aborting.")
        sys.exit(1)
    print(f"  ✅ Models loaded: {[k for k in models if k != 'scaler']}")

    # ── Process each race ─────────────────────────────────────────────────────
    print("\n── STEP 3: Feature engineering & prediction ───────────────────────────────")
    os.makedirs(args.output, exist_ok=True)
    all_results = []

    for race in races:
        dogs = race.get("dogs", [])
        if not dogs:
            print(f"  ⚠️  Race {race['RaceNumber']} has no dogs — skipping.")
            continue

        print(f"\n  🏁 Race {race['RaceNumber']} — {race['RaceDate']} {race['RaceTime']} "
              f"— {race['Track']} {race['Distance']}m  ({len(dogs)} dogs)")

        df = build_features(dogs, race_name=race.get("RaceName", ""), distance=race["Distance"])
        if df.empty:
            print("     ⚠️  No feature rows built — skipping.")
            continue

        result = predict_race(df, models)

        print_race_card(race, result)

        result["RaceNumber"] = race["RaceNumber"]
        result["RaceDate"]   = race["RaceDate"]
        result["RaceTime"]   = race["RaceTime"]
        result["Track"]      = race["Track"]
        result["Distance"]   = race["Distance"]
        all_results.append(result)

    # ── Save outputs ──────────────────────────────────────────────────────────
    if all_results:
        print("── STEP 4: Saving outputs ─────────────────────────────────────────────────")
        combined = pd.concat(all_results, ignore_index=True)

        pred_csv = os.path.join(args.output, "predictions.csv")
        combined.to_csv(pred_csv, index=False)
        print(f"  💾 Saved {pred_csv}")

        # Top pick per race
        p_col  = [c for c in combined.columns if c.startswith("P_win_ensemble")]
        if p_col:
            picks = combined.loc[combined.groupby(["RaceDate", "RaceNumber"])[p_col[0]].idxmax()]
            picks_csv = os.path.join(args.output, "picks_ml.csv")
            picks.to_csv(picks_csv, index=False)
            print(f"  💾 Saved {picks_csv}")

        print("\n" + "═" * 80)
        print("  ✅  PIPELINE COMPLETE")
        print("═" * 80 + "\n")


if __name__ == "__main__":
    main()
