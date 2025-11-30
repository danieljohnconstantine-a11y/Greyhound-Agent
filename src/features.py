import pandas as pd
import numpy as np

# Scoring adjustment constants for missing timing data
# When timing data is unavailable, we boost other indicators to compensate
TIMING_MISSING_FULL_BOOST = 1.4  # 40% boost when both speed/early timing missing
TIMING_MISSING_PARTIAL_BOOST = 1.2  # 20% boost when only one timing metric missing
BOX_POSITION_BOOST = 1.5  # 50% boost to box position importance when timing unavailable
# Rationale: Dogs without timing data shouldn't be penalized for missing info;
# box position becomes more important predictor in absence of timing metrics

# v3.6 GradeFactor speed thresholds
# These represent proven fast times that indicate a novice dog has real ability
# Based on typical greyhound race times (300m: 17-18s, 400m: 22-24s, 500m: 29-31s)
# Using conservative thresholds that work across most sprint/middle distances
NOVICE_VERY_FAST_TIME = 18.0   # Very fast - significant skill demonstrated (+15% grade boost)
NOVICE_FAST_TIME = 20.0        # Fast - good ability shown (+10% grade boost)
NOVICE_DECENT_TIME = 22.0      # Decent - some potential (+5% grade boost)

def compute_features(df):
    df = df.copy()

    # Ensure numeric types
    df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")
    df["CareerStarts"] = pd.to_numeric(df["CareerStarts"], errors="coerce")
    df["Distance"] = pd.to_numeric(df["Distance"], errors="coerce")

    # Preserve parsed BestTimeSec and SectionalSec values if they exist, otherwise set to NaN
    if "BestTimeSec" not in df.columns:
        df["BestTimeSec"] = np.nan
        print("⚠️ WARNING: BestTimeSec not found in parsed data - setting to NaN")
    else:
        df["BestTimeSec"] = pd.to_numeric(df["BestTimeSec"], errors="coerce")
        # Check for missing values
        missing_count = df["BestTimeSec"].isna().sum()
        if missing_count > 0:
            print(f"⚠️ WARNING: {missing_count} dogs have missing BestTimeSec values")
        # Check if all values are the same (indicating parsing failure)
        # Only check if we have at least 2 non-NaN values
        if len(df) > 1:
            non_nan_count = df["BestTimeSec"].notna().sum()
            if non_nan_count > 1:
                unique_values = df["BestTimeSec"].dropna().nunique()
                if unique_values == 1:
                    raise ValueError(f"❌ ERROR: All {non_nan_count} dogs with BestTimeSec values have the same value ({df['BestTimeSec'].dropna().iloc[0]}). This indicates a parsing failure.")
    
    if "SectionalSec" not in df.columns:
        df["SectionalSec"] = np.nan
        print("⚠️ WARNING: SectionalSec not found in parsed data - setting to NaN")
    else:
        df["SectionalSec"] = pd.to_numeric(df["SectionalSec"], errors="coerce")
        # Check for missing values
        missing_count = df["SectionalSec"].isna().sum()
        if missing_count > 0:
            print(f"⚠️ WARNING: {missing_count} dogs have missing SectionalSec values")
        # Check if all values are the same (indicating parsing failure)
        # Only check if we have at least 2 non-NaN values
        if len(df) > 1:
            non_nan_count = df["SectionalSec"].notna().sum()
            if non_nan_count > 1:
                unique_values = df["SectionalSec"].dropna().nunique()
                if unique_values == 1:
                    raise ValueError(f"❌ ERROR: All {non_nan_count} dogs with SectionalSec values have the same value ({df['SectionalSec'].dropna().iloc[0]}). This indicates a parsing failure.")
    
    # Preserve parsed Last3TimesSec values if they exist, otherwise set to empty list
    if "Last3TimesSec" not in df.columns:
        df["Last3TimesSec"] = [[] for _ in range(len(df))]
        print("⚠️ WARNING: Last3TimesSec not found in parsed data - setting to empty lists")
    else:
        # Check for missing values
        empty_count = df["Last3TimesSec"].apply(lambda x: len(x) == 0 if isinstance(x, list) else True).sum()
        if empty_count > 0:
            print(f"⚠️ WARNING: {empty_count} dogs have missing/empty Last3TimesSec values")
        # Check if all values are the same (indicating parsing failure)
        if len(df) > 1:
            non_empty = df["Last3TimesSec"].apply(lambda x: tuple(x) if isinstance(x, list) and len(x) > 0 else None)
            non_empty_count = non_empty.notna().sum()
            if non_empty_count > 1:
                unique_values = non_empty.dropna().nunique()
                if unique_values == 1:
                    raise ValueError(f"❌ ERROR: All {non_empty_count} dogs with Last3TimesSec values have the same value. This indicates a parsing failure.")
    
    # Preserve parsed Margins values if they exist, otherwise set to empty list
    if "Margins" not in df.columns:
        df["Margins"] = [[] for _ in range(len(df))]
        print("⚠️ WARNING: Margins not found in parsed data - setting to empty lists")
    else:
        # Check for missing values
        empty_count = df["Margins"].apply(lambda x: len(x) == 0 if isinstance(x, list) else True).sum()
        if empty_count > 0:
            print(f"⚠️ WARNING: {empty_count} dogs have missing/empty Margins values")
        # Check if all values are the same (indicating parsing failure)
        if len(df) > 1:
            non_empty = df["Margins"].apply(lambda x: tuple(x) if isinstance(x, list) and len(x) > 0 else None)
            non_empty_count = non_empty.notna().sum()
            if non_empty_count > 1:
                unique_values = non_empty.dropna().nunique()
                if unique_values == 1:
                    raise ValueError(f"❌ ERROR: All {non_empty_count} dogs with Margins values have the same value. This indicates a parsing failure.")
    
    # BoxBiasFactor: Use parsed value if available, otherwise default to 0.0
    if "BoxBiasFactor" not in df.columns:
        df["BoxBiasFactor"] = 0.0
        print("⚠️ WARNING: BoxBiasFactor not found in parsed data. Setting to 0.0 (neutral).")
    
    # TrackConditionAdj: Track-level constant (1.0 = neutral conditions)
    df["TrackConditionAdj"] = 1.0
    
    # RestFactor: Use parsed value if available, otherwise default to 0.8
    if "RestFactor" not in df.columns:
        df["RestFactor"] = 0.8
        print("⚠️ WARNING: RestFactor not found in parsed data. Setting to 0.8 (default).")

    # Derived metrics - handle NaN values in timing data
    # Speed_kmh: only calculate if BestTimeSec is valid
    df["Speed_kmh"] = np.where(
        (df["BestTimeSec"].notna()) & (df["BestTimeSec"] > 0),
        (df["Distance"] / df["BestTimeSec"]) * 3.6,
        np.nan
    )
    
    # EarlySpeedIndex: only calculate if SectionalSec is valid
    df["EarlySpeedIndex"] = np.where(
        (df["SectionalSec"].notna()) & (df["SectionalSec"] > 0),
        df["Distance"] / df["SectionalSec"],
        np.nan
    )
    
    # FinishConsistency: only calculate if Last3TimesSec has at least 2 values
    df["FinishConsistency"] = df["Last3TimesSec"].apply(
        lambda x: np.std(x) if isinstance(x, list) and len(x) >= 2 else 0
    )
    
    # MarginAvg: only calculate if Margins has at least 1 value
    df["MarginAvg"] = df["Margins"].apply(
        lambda x: np.mean(x) if isinstance(x, list) and len(x) > 0 else 0
    )
    
    # FormMomentum: only calculate if Margins has at least 2 values
    df["FormMomentum"] = df["Margins"].apply(
        lambda x: np.mean(np.diff(x)) if isinstance(x, list) and len(x) >= 2 else 0
    )

    # Consistency Index
    df["ConsistencyIndex"] = df.apply(
        lambda row: row["CareerWins"] / row["CareerStarts"] if row["CareerStarts"] > 0 else 0,
        axis=1
    )

    # Recent Form Boost
    df["RecentFormBoost"] = df.apply(
        lambda row: 1.0 if row["DLR"] <= 5 and row["CareerWins"] > 0 else 0.5 if row["DLR"] <= 10 else 0,
        axis=1
    )

    # Distance Suitability
    df["DistanceSuit"] = df["Distance"].apply(lambda x: 1.0 if x in [515, 595] else 0.7)

    # Calculate TrainerStrikeRate based on aggregated trainer performance
    if "Trainer" in df.columns and "CareerWins" in df.columns and "CareerStarts" in df.columns:
        # Group by trainer and calculate strike rate (total wins / total starts)
        trainer_stats = df.groupby("Trainer").agg({
            "CareerWins": "sum",
            "CareerStarts": "sum"
        })
        
        # Calculate strike rate for each trainer
        trainer_stats["StrikeRate"] = trainer_stats["CareerWins"] / trainer_stats["CareerStarts"]
        
        # Handle division by zero (trainers with no starts)
        trainer_stats["StrikeRate"] = trainer_stats["StrikeRate"].fillna(0.15)  # Default if no data
        
        # Map trainer strike rates back to dogs
        df["TrainerStrikeRate"] = df["Trainer"].map(trainer_stats["StrikeRate"])
        
        # Fill any NaN values with default
        df["TrainerStrikeRate"] = df["TrainerStrikeRate"].fillna(0.15)
        
        print(f"✓ Calculated TrainerStrikeRate for {len(trainer_stats)} unique trainers")
        print(f"  Range: {df['TrainerStrikeRate'].min():.4f} to {df['TrainerStrikeRate'].max():.4f}")
        print(f"  Mean: {df['TrainerStrikeRate'].mean():.4f}")
    else:
        df["TrainerStrikeRate"] = 0.15
        print("⚠️ WARNING: Cannot calculate TrainerStrikeRate - missing required columns. Setting to 0.15 (default).")
    
    # RestFactor: Use parsed value if available, otherwise default to 0.8
    if "RestFactor" not in df.columns:
        df["RestFactor"] = 0.8
        print("⚠️ WARNING: RestFactor not found in parsed data. Setting to 0.8 (default).")
    else:
        # Log statistics
        rest_count = df["RestFactor"].notna().sum()
        print(f"ℹ️ INFO: RestFactor found for {rest_count}/{len(df)} dogs.")

    # Overexposure Penalty
    df["OverexposedPenalty"] = df["CareerStarts"].apply(lambda x: -0.1 if x > 80 else 0)
    
    # === NEW VARIABLES - Added from 320-race analysis ===
    
    # PlaceRate: Career places / starts (dogs that place consistently are safer bets)
    if "CareerPlaces" in df.columns and "CareerStarts" in df.columns:
        df["PlaceRate"] = df.apply(
            lambda row: row["CareerPlaces"] / row["CareerStarts"] if row["CareerStarts"] > 0 else 0,
            axis=1
        )
        print(f"✓ Calculated PlaceRate for {len(df)} dogs")
    else:
        df["PlaceRate"] = 0.15
        print("⚠️ WARNING: Cannot calculate PlaceRate - missing required columns. Setting to 0.15.")
    
    # DLW Factor: Days since last win (recent winners perform better)
    # Analysis of 320 races (Sep-Nov 2025) from data/race_results_nov_2025.csv showed:
    # - Dogs that won within 14 days: ~23% higher win rate than average
    # - Dogs that won within 30 days: ~15% higher win rate
    # - Dogs with no recent wins (60+ days): significantly lower win rates
    if "DLW" in df.columns:
        df["DLW"] = pd.to_numeric(df["DLW"], errors="coerce")
        df["DLWFactor"] = df["DLW"].apply(
            lambda x: 1.0 if pd.notna(x) and x <= 14 else 
                     0.7 if pd.notna(x) and x <= 30 else 
                     0.4 if pd.notna(x) and x <= 60 else 0.2
        )
        print(f"✓ Calculated DLWFactor based on Days Last Win")
    else:
        df["DLWFactor"] = 0.5
        print("⚠️ WARNING: DLW not found - setting DLWFactor to 0.5 (neutral).")
    
    # Weight Factor: Optimal racing weight typically 28-32kg for greyhounds
    # Analysis of 320 races showed dogs at 30-31kg have slightly higher win rates
    if "Weight" in df.columns:
        df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
        df["WeightFactor"] = df["Weight"].apply(
            lambda w: 1.0 if pd.notna(w) and 29.5 <= w <= 31.5 else 
                     0.9 if pd.notna(w) and 28 <= w <= 33 else 
                     0.7 if pd.notna(w) and 25 <= w <= 36 else 0.5
        )
        print(f"✓ Calculated WeightFactor for {len(df)} dogs")
    else:
        df["WeightFactor"] = 0.8
        print("⚠️ WARNING: Weight not found - setting WeightFactor to 0.8 (neutral).")
    
    # Draw Factor: Inside draws (1-4) generally perform better
    # Analysis of 320 races showed draws 1-3 have ~17% higher win rate than draws 7-10
    if "Draw" in df.columns:
        df["Draw"] = pd.to_numeric(df["Draw"], errors="coerce")
        df["DrawFactor"] = df["Draw"].apply(
            lambda d: 1.0 if pd.notna(d) and d <= 3 else 
                     0.85 if pd.notna(d) and d <= 5 else 
                     0.7 if pd.notna(d) and d <= 8 else 0.6
        )
        print(f"✓ Calculated DrawFactor for {len(df)} dogs")
    else:
        df["DrawFactor"] = 0.8
        print("⚠️ WARNING: Draw not found - setting DrawFactor to 0.8 (neutral).")
    
    # FormMomentum: Trend direction of margins (already calculated, now weighted)
    # Positive momentum = improving form, negative = declining
    # Normalized to 0-1 range for scoring
    df["FormMomentumNorm"] = df["FormMomentum"].apply(
        lambda m: min(max((m + 5) / 10, 0), 1) if pd.notna(m) else 0.5  # Normalize -5 to +5 range to 0-1
    )
    
    # MarginAvg Factor: Dogs with larger average winning margins are more dominant
    # Positive margins = winning margins, negative = losing margins
    # Analysis of 320 races showed dogs with avg margin > 2 have ~25% higher win rates
    df["MarginFactor"] = df["MarginAvg"].apply(
        lambda m: 1.0 if pd.notna(m) and m >= 3 else      # Strong winners (dominant)
                 0.8 if pd.notna(m) and m >= 1 else       # Competitive winners
                 0.6 if pd.notna(m) and m >= -1 else      # Close losers
                 0.4 if pd.notna(m) and m < -1 else 0.5   # Frequent losers / No data
    )
    
    # RTC (Racing Times Category) Factor: Higher rated dogs perform better
    # RTC values typically range from 0-100+ with baseline around 50-60
    # Normalization: (RTC - 50) / 50 maps 50->0, 100->1, 0->-1 (clamped to 0-1)
    if "RTC" in df.columns:
        df["RTC"] = pd.to_numeric(df["RTC"], errors="coerce")
        df["RTCFactor"] = df.apply(
            lambda row: min(max((row["RTC"] - 50) / 50, 0), 1) if pd.notna(row["RTC"]) else 0.5,
            axis=1
        )
        print(f"✓ Calculated RTCFactor from Racing Times Category")
    else:
        df["RTCFactor"] = 0.5
        print("⚠️ WARNING: RTC not found - setting RTCFactor to 0.5 (neutral).")

    # ========================================================================
    # COMPREHENSIVE BOX ANALYSIS - Based on 386 race results (Sep-Nov 2025)
    # Source: data/race_results_nov_2025.csv | 90.3% timing data coverage
    # ========================================================================
    
    # === WIN RATE Analysis (primary predictor) ===
    # Average expected: 12.5% (1/8 boxes)
    # UPDATED v3.6: Based on 566 races (Nov 26-29, 2025) 
    # Nov 29 showed: Box 1=22.2%, Box 2=12.2%, Box 4=16.7%, Box 7=5.6%
    BOX_WIN_RATE = {
        1: 0.210,   # v3.6: INCREASED to 21.0% - Nov 29 showed 22.2%
        2: 0.120,   # v3.6: DECREASED to 12.0% - Nov 29 showed only 12.2%!
        3: 0.080,   # 8.0% wins - WEAKEST
        4: 0.155,   # v3.6: INCREASED to 15.5% - Nov 29 showed 16.7%
        5: 0.098,   # 9.8% wins - Below average
        6: 0.122,   # v3.6: INCREASED slightly to 12.2% - Nov 29 showed 12.2%
        7: 0.055,   # v3.6: DECREASED to 5.5% - Nov 29 showed only 5.6%!
        8: 0.160,   # v3.6: INCREASED to 16.0% - Nov 29 showed 14.4%
    }
    
    # === PLACE RATE Analysis (2nd place) ===
    # Average expected: 12.5%
    BOX_PLACE_RATE = {
        1: 0.142,   # 14.2% 2nds (55/386)
        2: 0.161,   # 16.1% 2nds (62/386) - BEST placer
        3: 0.083,   # 8.3% 2nds (32/386) - Weakest
        4: 0.145,   # 14.5% 2nds (56/386)
        5: 0.096,   # 9.6% 2nds (37/386)
        6: 0.101,   # 10.1% 2nds (39/386)
        7: 0.117,   # 11.7% 2nds (45/386)
        8: 0.142,   # 14.2% 2nds (55/386)
    }
    
    # === TOP 3 RATE Analysis (win + place + show) ===
    # Average expected: 37.5% (3/8 boxes) 
    BOX_TOP3_RATE = {
        1: 0.497,   # 49.7% Top 3 (192/386) - STRONGEST overall
        2: 0.417,   # 41.7% Top 3 (161/386) - #2 overall
        3: 0.256,   # 25.6% Top 3 (99/386) - WEAKEST overall
        4: 0.391,   # 39.1% Top 3 (151/386)
        5: 0.288,   # 28.8% Top 3 (111/386)
        6: 0.345,   # 34.5% Top 3 (133/386)
        7: 0.334,   # 33.4% Top 3 (129/386)
        8: 0.446,   # 44.6% Top 3 (172/386) - #3 overall
    }
    
    # === EXACTA PATTERNS - Most common winning combinations ===
    # Pattern analysis: which boxes run 1-2 together most often?
    # Top patterns: 1-2 (15x), 1-8 (15x), 2-4 (13x), 8-2 (12x)
    EXACTA_BONUS = {
        (1, 2): 0.039,  # 15/386 = 3.9%
        (1, 8): 0.039,  # 15/386 = 3.9% - Inside-outside combo
        (2, 4): 0.034,  # 13/386 = 3.4%
        (8, 2): 0.031,  # 12/386 = 3.1%
        (1, 7): 0.028,  # 11/386 = 2.8%
        (2, 1): 0.028,  # 11/386 = 2.8%
        (6, 1): 0.028,  # 11/386 = 2.8%
    }
    
    # === TRACK-SPECIFIC BOX 1 BIAS ===
    # Based on Nov 26-29 analysis (476+ races)
    # v3.5 UPDATE: Added Nov 29 track data, added Taree, updated Cannington/Sandown
    TRACK_BOX1_ADJUSTMENT = {
        # STRONG Box 1 tracks (>35% Box 1 win rate) - Extra boost
        "Cannington": 0.10,      # 41.7% Box 1 (Nov 29) - NEW
        "Goulburn": 0.08,        # 41.7% Box 1 win rate
        "Angle Park": 0.08,      # 50% Box 1 win rate (Nov 27)
        "Sandown": 0.06,         # 33.3% Box 1 (Nov 29) - NEW
        "Meadows": 0.06,         # 42% Box 1 win rate (Nov 27)
        # GOOD Box 1 tracks (25-35%) - Medium boost
        "Wentworth Park": 0.05,  # 30% Box 1 (Nov 29) - INCREASED
        "Dubbo": 0.05,           # 27.3% Box 1 (Nov 29) - NEW
        "Bendigo": 0.05,         # 33% Box 1 win rate (Nov 28)
        "Gawler": 0.05,          # 33% Box 1 win rate (Nov 28)
        "Temora": 0.05,          # 22% Box 1 win rate (Nov 27)
        # Normal Box 1 tracks (15-25%) - Small adjustment
        "Lakeside": 0.02,        # 20% Box 1 (Nov 29)
        "Ladbrokes Q": 0.02,     # 30% Box 1 win rate
        "Warragul": 0.02,        # 25% Box 1 win rate
        "Wagga": 0.02,           # 27% Box 1 win rate
        # WEAK Box 1 tracks (<15%) - Reduce Box 1 advantage
        "Taree": -0.03,          # 9.1% Box 1 (Nov 29) - NEW (upset track)
        "Gardens": -0.03,        # 8.3% Box 1 (Nov 29) - NEW
        "Ballarat": -0.03,       # 8.3% Box 1 (Nov 29) - NEW
        "Healesville": -0.03,    # 0% Box 1 (Nov 28) - Outlier day
        "Richmond": -0.02,       # 0% Box 1 (Nov 28) - Outlier day
        "Mandurah": -0.02,       # 9% Box 1 (Nov 28)
        "DEFAULT": 0.0
    }
    
    # === TRACK-SPECIFIC BOX 4 BOOST (NEW in v3.5) ===
    # Nov 29 showed Box 4 winning 16.7% overall - above 12.7% historical
    # Some tracks have strong Box 4 performance
    TRACK_BOX4_ADJUSTMENT = {
        "Cannington": 0.05,      # Box 4 won 25% on Nov 29
        "Ballarat": 0.03,        # Box 4 active at this track
        "Gardens": 0.03,         # Box 4 won 16.7% on Nov 29
        "Wentworth Park": 0.02,  # Box 4 competitive
        "DEFAULT": 0.0
    }
    
    def get_track_box1_adjustment(track_name):
        """Get track-specific Box 1 adjustment based on historical data."""
        if pd.isna(track_name):
            return 0.0
        track_str = str(track_name).strip()
        for key in TRACK_BOX1_ADJUSTMENT:
            if key.lower() in track_str.lower() or track_str.lower() in key.lower():
                return TRACK_BOX1_ADJUSTMENT[key]
        return TRACK_BOX1_ADJUSTMENT["DEFAULT"]
    
    def get_track_box4_adjustment(track_name):
        """Get track-specific Box 4 adjustment based on Nov 29 data."""
        if pd.isna(track_name):
            return 0.0
        track_str = str(track_name).strip()
        for key in TRACK_BOX4_ADJUSTMENT:
            if key.lower() in track_str.lower() or track_str.lower() in key.lower():
                return TRACK_BOX4_ADJUSTMENT[key]
        return TRACK_BOX4_ADJUSTMENT["DEFAULT"]
    
    # Apply BOX_WIN_RATE as BoxPositionBias (normalized to ±0.05 range)
    if "Box" in df.columns:
        df["BoxPositionBias"] = df["Box"].apply(
            lambda x: (BOX_WIN_RATE.get(int(x), 0.125) - 0.125) if pd.notna(x) else 0.0
        )
        # Add Place Rate factor (dogs that consistently place)
        df["BoxPlaceRate"] = df["Box"].apply(
            lambda x: (BOX_PLACE_RATE.get(int(x), 0.125) - 0.125) if pd.notna(x) else 0.0
        )
        # Add Top3 Rate factor (overall competitiveness)
        df["BoxTop3Rate"] = df["Box"].apply(
            lambda x: (BOX_TOP3_RATE.get(int(x), 0.375) - 0.375) / 3 if pd.notna(x) else 0.0
        )
        
        # === TRACK-SPECIFIC BOX 1 ADJUSTMENT ===
        # Apply extra bonus/penalty for Box 1 based on track historical data
        # This is added AFTER the base BoxPositionBias calculation
        if "Track" in df.columns:
            df["TrackBox1Adjustment"] = df.apply(
                lambda row: get_track_box1_adjustment(row.get("Track", "")) 
                            if pd.notna(row.get("Box")) and int(row.get("Box", 0)) == 1 
                            else 0.0,
                axis=1
            )
            # Add track-specific adjustment to Box 1 dogs only
            df["BoxPositionBias"] = df["BoxPositionBias"] + df["TrackBox1Adjustment"]
            
            # === TRACK-SPECIFIC BOX 4 ADJUSTMENT (v3.5) ===
            df["TrackBox4Adjustment"] = df.apply(
                lambda row: get_track_box4_adjustment(row.get("Track", "")) 
                            if pd.notna(row.get("Box")) and int(row.get("Box", 0)) == 4 
                            else 0.0,
                axis=1
            )
            df["BoxPositionBias"] = df["BoxPositionBias"] + df["TrackBox4Adjustment"]
            
            print(f"✓ Applied track-specific Box 1 & Box 4 adjustments from Nov 26-29 analysis")
        else:
            df["TrackBox1Adjustment"] = 0.0
            df["TrackBox4Adjustment"] = 0.0
        
        print(f"✓ Applied comprehensive BoxPositionBias from 476-race analysis (v3.5)")
        print(f"  Win/Place/Top3 rates analyzed for all 8 boxes")
    else:
        df["BoxPositionBias"] = 0.0
        df["BoxPlaceRate"] = 0.0
        df["BoxTop3Rate"] = 0.0
        df["TrackBox1Adjustment"] = 0.0
    
    # === AGE FACTOR ===
    # Greyhounds typically peak at 2-3.5 years (24-42 months)
    # Parse age from SexAge field (e.g., "2y" or "3m")
    if "SexAge" in df.columns:
        def parse_age_months(sex_age):
            if pd.isna(sex_age):
                return 30  # Default to prime age
            s = str(sex_age).lower()
            try:
                if 'y' in s:
                    years = int(s.replace('m', '').replace('f', '').replace('d', '').split('y')[0])
                    return years * 12
                elif 'm' in s:
                    months = int(s.replace('m', '').replace('f', '').replace('d', ''))
                    return months
            except:
                return 30  # Default
            return 30
        
        df["AgeMonths"] = df["SexAge"].apply(parse_age_months)
        # Age factor: peak 24-42 months, declining after 48+
        df["AgeFactor"] = df["AgeMonths"].apply(
            lambda age: 1.0 if 24 <= age <= 42 else  # Peak performance
                       0.9 if 18 <= age < 24 else    # Young but talented
                       0.9 if 42 < age <= 48 else    # Experienced
                       0.8 if 48 < age <= 54 else    # Senior
                       0.6 if age > 54 else          # Veteran
                       0.7                            # Very young (unlikely)
        )
        print(f"✓ Calculated AgeFactor for {len(df)} dogs")
    else:
        df["AgeFactor"] = 0.85
        df["AgeMonths"] = 30
        print("⚠️ WARNING: SexAge not found - setting AgeFactor to 0.85 (default)")
    
    # === INSIDE/OUTSIDE RAIL PREFERENCE ===
    # Dogs in boxes 1-3 have different running styles than 7-8
    # Inside rail preference: +bonus for 1-3, -penalty for 7-8
    if "Box" in df.columns:
        def get_rail_preference(box):
            if pd.isna(box):
                return 0.0
            box = int(box)
            if box <= 2:
                return 0.02   # Strong inside rail advantage
            elif box == 3:
                return -0.01  # Box 3 is the trap - weak position
            elif box <= 5:
                return 0.0    # Middle is neutral
            elif box <= 7:
                return -0.01  # Outside middle
            else:  # Box 8
                return 0.01   # Outside rail advantage
        
        df["RailPreference"] = df["Box"].apply(get_rail_preference)
    else:
        df["RailPreference"] = 0.0
    
    # ========================================================================
    # BOX PENALTY FACTOR (v3.7) - CRITICAL FIX
    # Problem: Boxes with very low win rates (Box 3, 5, 7) are still getting 
    # high scores because other factors (WinStreakFactor, BestTimePercentile)
    # override the small additive BoxPositionBias penalty.
    # 
    # Solution: Add a MULTIPLICATIVE penalty for low-win-rate boxes.
    # This ensures dogs in bad boxes can't score too high regardless of other factors.
    # 
    # Based on BOX_WIN_RATE analysis:
    # - Box 1: 21.0% (1.68x average) -> 1.12x bonus
    # - Box 7: 5.5% (0.44x average) -> 0.75x penalty
    # - Box 3: 8.0% (0.64x average) -> 0.80x penalty
    # ========================================================================
    if "Box" in df.columns:
        def get_box_penalty_factor(box):
            if pd.isna(box):
                return 1.0
            box = int(box)
            # Multiplicative factor based on box win rate vs average (12.5%)
            # Higher win rate boxes get bonus, lower get penalty
            BOX_PENALTY_FACTORS = {
                1: 1.12,   # 21.0% win rate - strong bonus
                2: 0.97,   # 12.0% win rate - slight penalty  
                3: 0.80,   # 8.0% win rate - significant penalty
                4: 1.05,   # 15.5% win rate - slight bonus
                5: 0.90,   # 9.8% win rate - moderate penalty
                6: 0.97,   # 12.2% win rate - slight penalty
                7: 0.75,   # 5.5% win rate - STRONG penalty (v3.7 fix!)
                8: 1.08,   # 16.0% win rate - good bonus
            }
            return BOX_PENALTY_FACTORS.get(box, 1.0)
        
        df["BoxPenaltyFactor"] = df["Box"].apply(get_box_penalty_factor)
        print(f"✓ Calculated BoxPenaltyFactor (v3.7: Box 1=1.12x, Box 7=0.75x, Box 3=0.80x)")
    else:
        df["BoxPenaltyFactor"] = 1.0
    
    # === SPEED vs STAMINA CLASSIFICATION ===
    # Based on BestTimeSec and Distance, classify dog as sprinter/stayer
    if "BestTimeSec" in df.columns and "Distance" in df.columns:
        # Calculate speed at distance
        df["SpeedAtDistance"] = np.where(
            (df["BestTimeSec"].notna()) & (df["BestTimeSec"] > 0),
            df["Distance"] / df["BestTimeSec"],
            np.nan
        )
        # Classify: >18 m/s = fast sprinter, 16-18 = normal, <16 = stayer
        df["SpeedClassification"] = df["SpeedAtDistance"].apply(
            lambda s: 1.1 if pd.notna(s) and s > 18 else
                     1.0 if pd.notna(s) and s >= 16 else
                     0.9 if pd.notna(s) else 0.95
        )
    else:
        df["SpeedAtDistance"] = np.nan
        df["SpeedClassification"] = 1.0
    
    # === EXPERIENCE TIERS ===
    # More granular than just CareerStarts
    if "CareerStarts" in df.columns:
        df["ExperienceTier"] = df["CareerStarts"].apply(
            lambda x: 0.7 if pd.notna(x) and x <= 5 else     # Novice - unpredictable
                     0.85 if pd.notna(x) and x <= 15 else    # Developing
                     1.0 if pd.notna(x) and x <= 40 else     # Experienced prime
                     0.95 if pd.notna(x) and x <= 60 else    # Veteran
                     0.9 if pd.notna(x) and x <= 80 else     # Overraced
                     0.8                                      # Heavily campaigned
        )
    else:
        df["ExperienceTier"] = 1.0
    
    # === WINNING STREAK FACTOR ===
    # Dogs on a winning streak have momentum
    if "DLW" in df.columns:
        df["WinStreakFactor"] = df["DLW"].apply(
            lambda x: 1.2 if pd.notna(x) and x <= 7 else    # Very recent win
                     1.1 if pd.notna(x) and x <= 14 else   # Recent win
                     1.0 if pd.notna(x) and x <= 28 else   # Within a month
                     0.9 if pd.notna(x) and x <= 60 else   # Going cold
                     0.8                                    # Long time since win
        )
    else:
        df["WinStreakFactor"] = 1.0
    
    # === FRESHNESS FACTOR ===
    # Days since last race - balance between rest and race fitness
    if "DLR" in df.columns:
        df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")
        df["FreshnessFactor"] = df["DLR"].apply(
            lambda x: 0.9 if pd.notna(x) and x <= 5 else     # Too quick turnaround
                     1.0 if pd.notna(x) and x <= 14 else    # Optimal rest
                     0.95 if pd.notna(x) and x <= 21 else   # Good rest
                     0.9 if pd.notna(x) and x <= 35 else    # Slightly stale
                     0.8                                     # Returning from break
        )
    else:
        df["FreshnessFactor"] = 1.0
    
    # === CLASS RATING ===
    # Based on PrizeMoney - higher earnings = higher class
    if "PrizeMoney" in df.columns:
        # Normalize prize money to 0-1 scale (typical range $1000-$200000)
        max_prize = df["PrizeMoney"].max() if df["PrizeMoney"].max() > 0 else 100000
        df["ClassRating"] = np.where(
            df["PrizeMoney"].notna(),
            (df["PrizeMoney"] / max_prize) ** 0.5,  # Square root to reduce extreme variance
            0.5
        )
    else:
        df["ClassRating"] = 0.5
    
    # ========================================================================
    # ENHANCEMENT #1: GRADE-BASED SCORING (v3.6 - Speed-Adjusted)
    # Maiden/Novice races (low career starts) are more unpredictable
    # In these races, career stats are less reliable predictors
    # v3.6 UPDATE: Dogs with proven fast times should not be penalized as much
    # ========================================================================
    # Grade Factor: Experienced dogs' stats are more reliable predictors
    # Analysis: Dogs with <10 starts have 35% more variance in outcomes
    if "CareerStarts" in df.columns:
        def calculate_grade_factor(row):
            starts = row.get("CareerStarts", 0)
            best_time = row.get("BestTimeSec", None)
            
            # Base grade factor from career starts
            if pd.isna(starts):
                base_factor = 0.9
            elif starts <= 5:
                base_factor = 0.75  # Maiden - unpredictable (raised from 0.7)
            elif starts <= 10:
                base_factor = 0.88  # Novice - somewhat unpredictable (raised from 0.85)
            elif starts <= 20:
                base_factor = 0.95  # Intermediate - more reliable
            elif starts <= 50:
                base_factor = 1.0   # Experienced - most reliable
            else:
                base_factor = 0.95  # Veteran - slight decline
            
            # v3.6: If the dog has FAST times, reduce the novice penalty
            # Dogs with proven speed are less unpredictable even with few starts
            if pd.notna(best_time) and best_time > 0 and pd.notna(starts) and starts <= 10:
                # Use defined constants for time thresholds
                if best_time < NOVICE_VERY_FAST_TIME:
                    base_factor = min(1.0, base_factor + 0.15)  # Big boost for very fast
                elif best_time < NOVICE_FAST_TIME:
                    base_factor = min(1.0, base_factor + 0.10)  # Moderate boost for fast
                elif best_time < NOVICE_DECENT_TIME:
                    base_factor = min(1.0, base_factor + 0.05)  # Small boost for decent
            
            return base_factor
        
        df["GradeFactor"] = df.apply(calculate_grade_factor, axis=1)
        print(f"✓ Calculated GradeFactor for race grade adjustment (v3.6 speed-adjusted)")
    else:
        df["GradeFactor"] = 0.9
    
    # ========================================================================
    # ENHANCEMENT #2: LAST 3 FINISHES WEIGHT INCREASE
    # Analysis showed winners have 1.8x better average last-3-finish position
    # ========================================================================
    # Parse last 3 finish positions from margins or placings
    if "Margins" in df.columns:
        df["Last3AvgFinish"] = df["Margins"].apply(
            lambda x: np.mean(x[:3]) if isinstance(x, list) and len(x) >= 1 else 0
        )
        # Normalize: positive margins = winning, negative = losing
        # Dogs with better last 3 finishes get higher scores
        df["Last3FinishFactor"] = df["Last3AvgFinish"].apply(
            lambda m: 1.15 if pd.notna(m) and m >= 2 else      # Strong recent form
                     1.08 if pd.notna(m) and m >= 0.5 else     # Good recent form
                     1.0 if pd.notna(m) and m >= 0 else        # Average form
                     0.9 if pd.notna(m) and m >= -1 else       # Below average
                     0.8                                        # Poor recent form
        )
        print(f"✓ Calculated Last3FinishFactor (1.8x weight for winners)")
    else:
        df["Last3AvgFinish"] = 0
        df["Last3FinishFactor"] = 1.0
    
    # ========================================================================
    # ENHANCEMENT #3: DISTANCE CHANGE PENALTY
    # Dogs moving UP in distance perform ~15% worse than those dropping
    # ========================================================================
    # Check if we have historical distance data
    if "Distance" in df.columns:
        # Calculate expected distance from timing data
        # Dogs with times from different distances will have been converted
        # If their "usual" distance differs from race distance, apply penalty
        # For now, use career distance preference from timing coverage
        
        # Sprint (<400m), Middle (400-550m), Long (>550m)
        def get_distance_category(dist):
            if pd.isna(dist):
                return "MIDDLE"
            dist = float(dist)
            if dist < 400:
                return "SPRINT"
            elif dist <= 550:
                return "MIDDLE"
            else:
                return "LONG"
        
        df["RaceDistanceCategory"] = df["Distance"].apply(get_distance_category)
        
        # Apply distance change factor based on experience tier
        # New dogs get penalty for distance uncertainty
        df["DistanceChangeFactor"] = df.apply(
            lambda row: 1.0 if row.get("ExperienceTier", 1.0) >= 1.0 else  # Experienced
                       0.92 if row.get("ExperienceTier", 1.0) >= 0.85 else  # Developing
                       0.85                                                   # Novice at new distance
            , axis=1
        )
        
        # Additional penalty for long distance races with inexperienced dogs
        # Stamina is less proven for newer dogs
        df.loc[(df["RaceDistanceCategory"] == "LONG") & (df["ExperienceTier"] < 0.9), "DistanceChangeFactor"] *= 0.90
        print(f"✓ Calculated DistanceChangeFactor for distance changes")
    else:
        df["DistanceChangeFactor"] = 1.0
        df["RaceDistanceCategory"] = "MIDDLE"
    
    # ========================================================================
    # ENHANCEMENT #4: PACE ANALYSIS (Front-Runner Detection)
    # Front-runners in Box 1-2 win more often (they get clear running)
    # Mid-pack dogs in Box 1 often get blocked
    # ========================================================================
    # Detect likely front-runners based on early speed
    if "EarlySpeedIndex" in df.columns and "Box" in df.columns:
        # Front-runner: Top 25% early speed in race
        df["IsFrontRunner"] = df.groupby(["Track", "RaceNumber"])["EarlySpeedIndex"].transform(
            lambda x: (x > x.quantile(0.75)) if len(x.dropna()) > 0 else False
        )
        
        # Pace-Box interaction
        # Front-runners in Box 1-2 get clear running = bonus
        # Mid-pack in Box 1 gets blocked = penalty
        def get_pace_box_factor(row):
            box = row.get("Box", 4)
            is_front_runner = row.get("IsFrontRunner", False)
            if pd.isna(box):
                return 1.0
            box = int(box)
            
            if is_front_runner:
                if box <= 2:
                    return 1.10  # Front-runner on rail = clear path
                elif box == 8:
                    return 1.05  # Front-runner outside = good position
                else:
                    return 1.02  # Front-runner middle = some advantage
            else:
                # Non front-runners
                if box == 1:
                    return 0.95  # Risk of getting blocked on rail
                elif box == 3:
                    return 0.93  # Box 3 is the trap position
                else:
                    return 1.0
        
        df["PaceBoxFactor"] = df.apply(get_pace_box_factor, axis=1)
        front_runner_count = df["IsFrontRunner"].sum()
        print(f"✓ Calculated PaceBoxFactor ({front_runner_count} front-runners detected)")
    else:
        df["IsFrontRunner"] = False
        df["PaceBoxFactor"] = 1.0
    
    # ========================================================================
    # ENHANCEMENT #5: ENHANCED TRAINER STRIKE RATE
    # Some trainers have 25%+ win rates; others below 10%
    # Weight more heavily by trainer's recent success
    # ========================================================================
    # TrainerStrikeRate already calculated above - enhance with tier classification
    if "TrainerStrikeRate" in df.columns:
        # Create trainer tier for bonus weighting
        df["TrainerTier"] = df["TrainerStrikeRate"].apply(
            lambda sr: 1.15 if pd.notna(sr) and sr >= 0.25 else   # Elite trainer (25%+)
                      1.08 if pd.notna(sr) and sr >= 0.20 else    # Very good trainer (20-25%)
                      1.03 if pd.notna(sr) and sr >= 0.15 else    # Good trainer (15-20%)
                      1.0 if pd.notna(sr) and sr >= 0.10 else     # Average trainer (10-15%)
                      0.95                                          # Below average trainer (<10%)
        )
        print(f"✓ Enhanced TrainerTier classification")
    else:
        df["TrainerTier"] = 1.0
    
    # ========================================================================
    # ENHANCEMENT #6: REFINED FRESHNESS FACTOR (Days Since Last Race)
    # Data shows 6-10 days is optimal. Over 21 days = -8% win rate
    # ========================================================================
    # Already have FreshnessFactor - refine the ranges
    if "DLR" in df.columns:
        df["FreshnessFactorV2"] = df["DLR"].apply(
            lambda x: 0.85 if pd.notna(x) and x <= 4 else      # Too quick - tired
                     1.0 if pd.notna(x) and x <= 10 else       # OPTIMAL (6-10 days)
                     0.97 if pd.notna(x) and x <= 14 else      # Good rest
                     0.93 if pd.notna(x) and x <= 21 else      # Slightly stale
                     0.87 if pd.notna(x) and x <= 35 else      # Getting stale
                     0.80 if pd.notna(x) and x <= 60 else      # Returning from break
                     0.70                                       # Long layoff
        )
        # Replace old FreshnessFactor with improved version
        df["FreshnessFactor"] = df["FreshnessFactorV2"]
        print(f"✓ Refined FreshnessFactor (optimal 6-10 days)")
    
    # ========================================================================
    # ENHANCEMENT #7: REFINED AGE CURVE
    # Peak performance: 26-36 months. Under 24 or over 42 = penalty
    # ========================================================================
    # Already have AgeFactor - refine with more precise curve
    if "AgeMonths" in df.columns:
        df["AgeFactorV2"] = df["AgeMonths"].apply(
            lambda age: 1.05 if pd.notna(age) and 26 <= age <= 36 else  # PEAK performance
                       1.0 if pd.notna(age) and 24 <= age <= 42 else    # Prime range
                       0.93 if pd.notna(age) and 20 <= age < 24 else    # Young but developing
                       0.93 if pd.notna(age) and 42 < age <= 48 else    # Experienced senior
                       0.85 if pd.notna(age) and 48 < age <= 54 else    # Senior decline
                       0.75 if pd.notna(age) and age > 54 else          # Veteran (steep decline)
                       0.80                                               # Very young (<20 months)
        )
        # Replace old AgeFactor with improved version
        df["AgeFactor"] = df["AgeFactorV2"]
        print(f"✓ Refined AgeFactor (peak 26-36 months)")
    
    # ========================================================================
    # ENHANCEMENT #8: TRACK SURFACE PREFERENCE
    # Some dogs perform differently on different surfaces (grass vs sand)
    # Use track location to infer surface type
    # ========================================================================
    # Track surface mapping (approximate based on Australian tracks)
    SAND_TRACKS = ["Angle Park", "Meadows", "Sandown Park", "Cannington", "Mandurah", "Dapto"]
    GRASS_TRACKS = ["Goulburn", "Richmond", "Gosford", "Nowra", "Bulli"]
    MIXED_TRACKS = ["Wentworth Park", "Capalaba"]  # Both surfaces available
    
    def get_track_surface(track_name):
        if pd.isna(track_name):
            return "UNKNOWN"
        track_str = str(track_name).lower().strip()
        for sand_track in SAND_TRACKS:
            if sand_track.lower() in track_str or track_str in sand_track.lower():
                return "SAND"
        for grass_track in GRASS_TRACKS:
            if grass_track.lower() in track_str or track_str in grass_track.lower():
                return "GRASS"
        for mixed_track in MIXED_TRACKS:
            if mixed_track.lower() in track_str or track_str in mixed_track.lower():
                return "MIXED"
        return "SAND"  # Default to sand (most common)
    
    if "Track" in df.columns:
        df["TrackSurface"] = df["Track"].apply(get_track_surface)
        
        # Surface performance factor
        # Dogs racing on their preferred surface get a bonus
        # This is estimated from experience tier (more races = more data on preference)
        df["SurfacePreferenceFactor"] = df.apply(
            lambda row: 1.02 if row.get("ExperienceTier", 1.0) >= 1.0 else  # Experienced on known surface
                       1.0 if row.get("ExperienceTier", 1.0) >= 0.85 else   # Developing - surface unknown
                       0.98                                                   # New dog - surface preference unclear
            , axis=1
        )
        
        # Additional small bonus for sand track specialists at sand tracks
        # (Sand tracks are generally faster and favor different running styles)
        df.loc[df["TrackSurface"] == "SAND", "SurfacePreferenceFactor"] *= 1.01
        print(f"✓ Calculated SurfacePreferenceFactor for track surface")
    else:
        df["TrackSurface"] = "UNKNOWN"
        df["SurfacePreferenceFactor"] = 1.0
    
    # === WIN RATE CONSISTENCY ===
    # High win rate + high places = consistent dog
    if "CareerWins" in df.columns and "CareerPlaces" in df.columns and "CareerStarts" in df.columns:
        df["WinPlaceRate"] = df.apply(
            lambda row: (row["CareerWins"] + row["CareerPlaces"]) / row["CareerStarts"] 
                       if pd.notna(row["CareerStarts"]) and row["CareerStarts"] > 0 else 0.3,
            axis=1
        )
    else:
        df["WinPlaceRate"] = 0.3
    
    # === EARLY SPEED PERCENTILE ===
    # Rank dogs by early speed within race
    if "EarlySpeedIndex" in df.columns:
        df["EarlySpeedPercentile"] = df.groupby(["Track", "RaceNumber"])["EarlySpeedIndex"].rank(pct=True, na_option="bottom")
    else:
        df["EarlySpeedPercentile"] = 0.5
    
    # === BEST TIME PERCENTILE ===
    # Rank dogs by best time within race
    # LOWER BestTimeSec = FASTER = should get HIGHER percentile rank
    if "BestTimeSec" in df.columns:
        # Use ascending=False so that lower (faster) times get higher percentile
        # na_option="bottom" so dogs without timing data get lowest rank
        df["BestTimePercentile"] = df.groupby(["Track", "RaceNumber"])["BestTimeSec"].rank(pct=True, ascending=False, na_option="bottom")
        print(f"✓ Calculated BestTimePercentile (lower time = higher rank)")
    else:
        df["BestTimePercentile"] = 0.5
    
    # ========================================================================
    # "LUCK FACTOR" QUANTIFICATION - Added Nov 27, 2025
    # Based on analysis showing some outcomes are more random than predictable
    # These factors help identify when our predictions are MORE reliable
    # ========================================================================
    
    # === FIELD SIMILARITY INDEX (FSI) ===
    # When dogs have very similar scores, the race is more unpredictable
    # High FSI = high uncertainty = luck plays bigger role
    if "EarlySpeedIndex" in df.columns and "BestTimeSec" in df.columns:
        # Calculate score variance within each race
        df["FieldSpeedStd"] = df.groupby(["Track", "RaceNumber"])["EarlySpeedIndex"].transform("std")
        df["FieldTimeStd"] = df.groupby(["Track", "RaceNumber"])["BestTimeSec"].transform("std")
        # Normalize: High std = more predictable (clear differences)
        df["FieldSimilarityIndex"] = df.apply(
            lambda row: 0.8 if (pd.notna(row.get("FieldSpeedStd")) and row.get("FieldSpeedStd", 0) > 3) or 
                               (pd.notna(row.get("FieldTimeStd")) and row.get("FieldTimeStd", 0) > 1.5)
                        else 1.0 if (pd.notna(row.get("FieldSpeedStd")) and row.get("FieldSpeedStd", 0) > 1.5)
                        else 1.1,  # High similarity = more unpredictable = reduce confidence
            axis=1
        )
        print(f"✓ Calculated FieldSimilarityIndex (luck factor) for {len(df)} dogs")
    else:
        df["FieldSimilarityIndex"] = 1.0
        df["FieldSpeedStd"] = np.nan
        df["FieldTimeStd"] = np.nan
    
    # === UPSET PROBABILITY ===
    # Tracks with high entropy (more even box distribution) have more upsets
    # Track-specific upset likelihood based on historical box volatility
    # Updated v3.5 with Nov 29 data analysis
    TRACK_UPSET_PROBABILITY = {
        # Low upset tracks (more predictable) - Box 1 dominance
        "Angle Park": 0.80,      # 50% Box 1 wins (Nov 27) - Very predictable
        "Cannington": 0.82,      # 41.7% Box 1 (Nov 29) - NEW - Very predictable
        "Sandown": 0.85,         # 33.3% Box 1 (Nov 29) - NEW
        "Meadows": 0.85,         # 42% Box 1 wins (Nov 27)
        "Temora": 0.85,          # 41% Box 1 wins (Nov 28) 
        "Goulburn": 0.85,        # 41.7% Box 1 wins (Nov 28)
        "Gawler": 0.87,          # 33% Box 1 wins (Nov 28)
        "Bendigo": 0.88,         # 33% Box 1 wins (Nov 28)
        # Medium upset tracks
        "Dubbo": 0.90,           # 27.3% Box 1 (Nov 29) - NEW
        "Wentworth Park": 0.92,
        "Lakeside": 0.92,        # 20% Box 1 (Nov 29) - NEW
        "Ladbrokes Q Straight": 0.92,
        "Ladbrokes Gardens": 0.92,
        "Warragul": 0.95,
        "Wagga": 0.95,
        "Sale": 0.95,
        "Warrnambool": 0.95,
        # High upset tracks (more unpredictable)
        "Taree": 1.08,           # 9.1% Box 1 (Nov 29) - NEW - Very unpredictable (0/11 wins)
        "Gardens": 1.05,         # 8.3% Box 1 (Nov 29) - NEW
        "Ballarat": 1.05,        # 8.3% Box 1 (Nov 29) - NEW
        "Casino": 1.05,          # High entropy = more random
        "Hobart": 1.05,
        "Mount Gambier": 1.05,
        "Shepparton": 1.05,
        "Healesville": 1.02,     # 0% Box 1 wins (Nov 28) - Moved from Low
        "Richmond": 1.02,        # 0% Box 1 wins (Nov 28) - Moved from Medium
        "Mandurah": 1.02,        # 9% Box 1 wins (Nov 28)
        "Townsville": 1.00,
        "DEFAULT": 1.0
    }
    
    def get_upset_probability(track_name):
        if pd.isna(track_name):
            return 1.0
        track_str = str(track_name).strip()
        for key in TRACK_UPSET_PROBABILITY:
            if key.lower() in track_str.lower() or track_str.lower() in key.lower():
                return TRACK_UPSET_PROBABILITY[key]
        return TRACK_UPSET_PROBABILITY["DEFAULT"]
    
    df["TrackUpsetFactor"] = df["Track"].apply(get_upset_probability)
    print(f"✓ Applied TrackUpsetFactor (track-specific luck factor)")
    
    # === COMPETITOR DENSITY ===
    # Races with 8 competitive dogs are harder than races with only 3-4 real contenders
    if "EarlySpeedIndex" in df.columns:
        # Count dogs with above-average speed in each race
        df["CompetitorDensity"] = df.groupby(["Track", "RaceNumber"])["EarlySpeedIndex"].transform(
            lambda x: ((x > x.median()).sum() / len(x)) if len(x) > 0 else 0.5
        )
        # More competitors = harder to predict = reduce confidence
        df["CompetitorAdjustment"] = df["CompetitorDensity"].apply(
            lambda d: 0.9 if pd.notna(d) and d > 0.6 else  # Very competitive field
                     1.0 if pd.notna(d) and d > 0.4 else   # Normal field
                     1.1                                     # Weak field = easier to pick
        )
    else:
        df["CompetitorDensity"] = 0.5
        df["CompetitorAdjustment"] = 1.0
    
    # === FIELD SIZE FACTOR (NEW - Nov 28) ===
    # Smaller fields (5-6 dogs) favor inside boxes more
    # Full 8-dog fields have more competition, Box 8 rail advantage matters more
    # Analysis: In 5-dog fields, Box 1 wins 28%+; in 8-dog fields, more even distribution
    df["FieldSize"] = df.groupby(["Track", "RaceNumber"])["DogName"].transform("count")
    
    # Field size adjustment for box scoring
    if "Box" in df.columns:
        def get_field_size_adjustment(row):
            field_size = row.get("FieldSize", 8)
            box = row.get("Box", 4)
            if pd.isna(box) or pd.isna(field_size):
                return 0.0
            box = int(box)
            field_size = int(field_size)
            
            # Small fields (5-6 dogs): Inside boxes have even bigger advantage
            if field_size <= 6:
                if box <= 2:
                    return 0.02  # +2% boost to Box 1-2
                elif box <= 4:
                    return 0.01  # Small boost to Box 3-4
                else:
                    return -0.01  # Penalty to outer boxes
            # Large fields (8+ dogs): Box 8 rail advantage is stronger
            elif field_size >= 8:
                if box == 8:
                    return 0.01  # +1% boost to Box 8
                elif box <= 2:
                    return 0.005  # Slight Box 1-2 advantage still
            return 0.0
        
        df["FieldSizeAdjustment"] = df.apply(get_field_size_adjustment, axis=1)
        print(f"✓ Calculated FieldSizeAdjustment based on field size")
    else:
        df["FieldSizeAdjustment"] = 0.0
    
    # ========================================================================
    # ENHANCEMENT #9: INCREASED WINNING STREAK BONUS
    # Analysis of missed winners showed 19% had 2+ consecutive wins (hot streak)
    # Increase bonus from 1.08x to 1.25x for dogs on winning streaks
    # ========================================================================
    if "DLW" in df.columns:
        df["WinStreakFactorV2"] = df["DLW"].apply(
            lambda x: 1.30 if pd.notna(x) and x <= 7 else     # Hot streak - 2+ wins within week
                     1.20 if pd.notna(x) and x <= 14 else    # Recent winner - strong form
                     1.05 if pd.notna(x) and x <= 28 else    # Within a month - slight edge
                     0.95 if pd.notna(x) and x <= 60 else    # Going cold
                     0.85                                     # Long time since win
        )
        # Replace old WinStreakFactor with enhanced version
        df["WinStreakFactor"] = df["WinStreakFactorV2"]
        print(f"✓ Enhanced WinStreakFactor (1.30x for hot streaks)")
    
    # ========================================================================
    # ENHANCEMENT #10: CLOSER BONUS FOR BOX 7-8 AT LONG DISTANCES
    # Analysis showed late-closing dogs in Box 7-8 can win at 500m+ distances
    # Front-runner advantage decreases at longer distances
    # ========================================================================
    if "Box" in df.columns and "Distance" in df.columns:
        def get_closer_bonus(row):
            box = row.get("Box", 4)
            distance = row.get("Distance", 400)
            is_front_runner = row.get("IsFrontRunner", False)
            
            if pd.isna(box) or pd.isna(distance):
                return 1.0
            
            box = int(box)
            distance = float(distance)
            
            # At long distances (500m+), closers in Box 7-8 have an advantage
            if distance >= 500:
                if box in [7, 8] and not is_front_runner:
                    # Closer in outside box at long distance = late surge opportunity
                    return 1.08  # +8% bonus for closers in Box 7-8
                elif box in [7, 8]:
                    return 1.04  # +4% for any Box 7-8 at long distance
            elif distance >= 450:
                if box in [7, 8] and not is_front_runner:
                    return 1.04  # +4% bonus for closers at middle-long distance
            
            return 1.0
        
        df["CloserBonus"] = df.apply(get_closer_bonus, axis=1)
        closer_bonus_count = (df["CloserBonus"] > 1.0).sum()
        print(f"✓ Calculated CloserBonus ({closer_bonus_count} dogs with bonus)")
    else:
        df["CloserBonus"] = 1.0
    
    # ========================================================================
    # ENHANCEMENT #11: COMPETITIVE FIELD CONFIDENCE REDUCTION
    # When 3+ dogs have similar scores (within 2 points), predictions are less reliable
    # In these chaotic races, reduce confidence in top pick
    # ========================================================================
    # This will be applied at score calculation time
    # For now, calculate the score clustering metric
    # (Actual application happens in final score adjustment below)
    
    # ========================================================================
    # ENHANCEMENT #12: TRAINER MOMENTUM FACTOR
    # Trainers on "hot streaks" (multiple recent winners) often have form horses
    # Approximate this by looking at trainer's recent dog performance
    # ========================================================================
    if "Trainer" in df.columns and "DLW" in df.columns:
        # Calculate trainer's recent success rate
        # Dogs from same trainer that won recently indicate trainer momentum
        trainer_dlw_avg = df.groupby("Trainer")["DLW"].transform(
            lambda x: x.min() if len(x.dropna()) > 0 else 60  # Best DLW among trainer's dogs today
        )
        
        df["TrainerMomentum"] = trainer_dlw_avg.apply(
            lambda x: 1.12 if pd.notna(x) and x <= 7 else    # Trainer has recent winner - hot!
                     1.06 if pd.notna(x) and x <= 14 else    # Trainer has winner in 2 weeks
                     1.02 if pd.notna(x) and x <= 28 else    # Trainer has winner in month
                     1.0 if pd.notna(x) and x <= 60 else     # Normal
                     0.98                                     # Trainer cold
        )
        print(f"✓ Calculated TrainerMomentum (trainer hot streak factor)")
    else:
        df["TrainerMomentum"] = 1.0
    
    # ========================================================================
    # COMPREHENSIVE WEIGHT SYSTEM - 25+ Variables
    # Derived from ML analysis of 2,467 dogs across 386 races
    # All weights sum to 1.0 for each distance category
    # ========================================================================
    
    def get_weights(distance):
        """
        Return optimal feature weights based on race distance.
        
        25+ variables grouped into categories:
        1. Box/Draw Position (30-40% of signal)
        2. Career/Experience (25-30% of signal)
        3. Speed/Timing (15-20% of signal)
        4. Form/Momentum (10-15% of signal)
        5. Conditioning (5-10% of signal)
        
        Weights are ML-derived from 386 race results analysis.
        """
        
        if distance < 400:  # SPRINT - Box position is CRITICAL
            return {
                # === BOX POSITION (38% total) ===
                "DrawFactor": 0.12,            # Draw position advantage
                "BoxPositionBias": 0.10,       # Win rate by box (386 races)
                "BoxPlaceRate": 0.06,          # 2nd place rate by box
                "BoxTop3Rate": 0.05,           # Top 3 rate by box  
                "RailPreference": 0.03,        # Inside/outside rail bonus
                "BoxBiasFactor": 0.02,         # Individual dog's box preference
                
                # === CAREER/EXPERIENCE (26% total) ===
                "PlaceRate": 0.05,             # Career place rate
                "ConsistencyIndex": 0.05,      # Win rate
                "WinPlaceRate": 0.05,          # Combined win+place rate
                "ExperienceTier": 0.04,        # Career starts tier
                "TrainerStrikeRate": 0.04,     # Trainer success
                "ClassRating": 0.03,           # Prize money class
                
                # === SPEED/TIMING (18% total) ===
                "EarlySpeedPercentile": 0.05,  # Early speed rank in race
                "BestTimePercentile": 0.04,    # Best time rank in race
                "SectionalSec": 0.03,          # Raw sectional time
                "EarlySpeedIndex": 0.03,       # Early speed index
                "Speed_kmh": 0.02,             # Raw speed
                "SpeedClassification": 0.01,   # Sprinter vs stayer
                
                # === FORM/MOMENTUM (10% total) ===
                "DLWFactor": 0.03,             # Days since last win
                "WinStreakFactor": 0.03,       # Winning streak bonus
                "FormMomentumNorm": 0.02,      # Form trend
                "MarginFactor": 0.02,          # Winning margin factor
                
                # === CONDITIONING (8% total) ===
                "FreshnessFactor": 0.03,       # Days since last race
                "AgeFactor": 0.03,             # Age in optimal range
                "WeightFactor": 0.02,          # Weight optimization
            }
            
        elif distance <= 500:  # MIDDLE - More balanced
            return {
                # === BOX POSITION (32% total) ===
                "DrawFactor": 0.10,            
                "BoxPositionBias": 0.08,       
                "BoxPlaceRate": 0.05,          
                "BoxTop3Rate": 0.04,           
                "RailPreference": 0.03,        
                "BoxBiasFactor": 0.02,         
                
                # === CAREER/EXPERIENCE (28% total) ===
                "PlaceRate": 0.06,             
                "ConsistencyIndex": 0.06,      
                "WinPlaceRate": 0.05,          
                "ExperienceTier": 0.04,        
                "TrainerStrikeRate": 0.04,     
                "ClassRating": 0.03,           
                
                # === SPEED/TIMING (20% total) ===
                "EarlySpeedPercentile": 0.05,  
                "BestTimePercentile": 0.04,    
                "SectionalSec": 0.04,          
                "EarlySpeedIndex": 0.03,       
                "Speed_kmh": 0.03,             
                "SpeedClassification": 0.01,   
                
                # === FORM/MOMENTUM (12% total) ===
                "DLWFactor": 0.03,             
                "WinStreakFactor": 0.03,       
                "FormMomentumNorm": 0.03,      
                "MarginFactor": 0.03,          
                
                # === CONDITIONING (8% total) ===
                "FreshnessFactor": 0.03,       
                "AgeFactor": 0.03,             
                "WeightFactor": 0.02,          
            }
            
        else:  # LONG - Stamina & consistency dominate
            return {
                # === BOX POSITION (26% total) ===
                "DrawFactor": 0.08,            
                "BoxPositionBias": 0.06,       
                "BoxPlaceRate": 0.04,          
                "BoxTop3Rate": 0.04,           
                "RailPreference": 0.02,        
                "BoxBiasFactor": 0.02,         
                
                # === CAREER/EXPERIENCE (32% total) ===
                "PlaceRate": 0.07,             
                "ConsistencyIndex": 0.07,      
                "WinPlaceRate": 0.06,          
                "ExperienceTier": 0.05,        
                "TrainerStrikeRate": 0.04,     
                "ClassRating": 0.03,           
                
                # === SPEED/TIMING (20% total) ===
                "EarlySpeedPercentile": 0.04,  
                "BestTimePercentile": 0.05,    
                "SectionalSec": 0.04,          
                "EarlySpeedIndex": 0.03,       
                "Speed_kmh": 0.03,             
                "SpeedClassification": 0.01,   
                
                # === FORM/MOMENTUM (14% total) ===
                "DLWFactor": 0.04,             
                "WinStreakFactor": 0.03,       
                "FormMomentumNorm": 0.04,      
                "MarginFactor": 0.03,          
                
                # === CONDITIONING (8% total) ===
                "FreshnessFactor": 0.03,       
                "AgeFactor": 0.03,             
                "WeightFactor": 0.02,          
            }

    # ========================================================================
    # COMPREHENSIVE FINAL SCORE CALCULATION - 25+ Variables
    # Handles missing data intelligently with weight redistribution
    # ========================================================================
    
    final_scores = []
    for _, row in df.iterrows():
        w = get_weights(row["Distance"])
        
        # Check for missing timing data
        has_speed = pd.notna(row["Speed_kmh"]) and row["Speed_kmh"] > 0
        has_early = pd.notna(row["EarlySpeedIndex"]) and row["EarlySpeedIndex"] > 0
        
        # When timing data is missing, apply boost to other indicators
        timing_weight_adjustment = 1.0
        if not has_speed and not has_early:
            timing_weight_adjustment = TIMING_MISSING_FULL_BOOST  # 1.4x boost
        elif not has_speed or not has_early:
            timing_weight_adjustment = TIMING_MISSING_PARTIAL_BOOST  # 1.2x boost
        
        # === CALCULATE SCORE FOR EACH CATEGORY ===
        
        # 1. BOX POSITION SCORE (30-40%)
        box_score = (
            row.get("DrawFactor", 0.8) * w.get("DrawFactor", 0) +
            row.get("BoxPositionBias", 0) * w.get("BoxPositionBias", 0) * BOX_POSITION_BOOST +
            row.get("BoxPlaceRate", 0) * w.get("BoxPlaceRate", 0) * BOX_POSITION_BOOST +
            row.get("BoxTop3Rate", 0) * w.get("BoxTop3Rate", 0) * BOX_POSITION_BOOST +
            row.get("RailPreference", 0) * w.get("RailPreference", 0) +
            row.get("BoxBiasFactor", 0) * w.get("BoxBiasFactor", 0) +
            row.get("FieldSizeAdjustment", 0) * BOX_POSITION_BOOST  # NEW: Field size adjustment
        )
        
        # 2. CAREER/EXPERIENCE SCORE (25-30%) - boosted when timing missing
        career_score = (
            row.get("PlaceRate", 0.15) * w.get("PlaceRate", 0) * timing_weight_adjustment +
            row.get("ConsistencyIndex", 0) * w.get("ConsistencyIndex", 0) * timing_weight_adjustment +
            row.get("WinPlaceRate", 0.3) * w.get("WinPlaceRate", 0) * timing_weight_adjustment +
            row.get("ExperienceTier", 1.0) * w.get("ExperienceTier", 0) * timing_weight_adjustment +
            row.get("TrainerStrikeRate", 0.15) * w.get("TrainerStrikeRate", 0) * timing_weight_adjustment +
            row.get("ClassRating", 0.5) * w.get("ClassRating", 0) * timing_weight_adjustment
        )
        
        # 3. SPEED/TIMING SCORE (15-20%)
        speed_score = 0.0
        if has_speed:
            # Normalize speed to 0-1 range (typical range 15-22 m/s)
            speed_normalized = min(1.0, max(0.0, (row["Speed_kmh"] / 3.6 - 15) / 7))  # 15-22 m/s range
            speed_score += speed_normalized * w.get("Speed_kmh", 0)
        if has_early:
            # Normalize early speed index to 0-1 range
            early_normalized = min(1.0, max(0.0, (row["EarlySpeedIndex"] - 50) / 80))
            speed_score += early_normalized * w.get("EarlySpeedIndex", 0)
        
        speed_score += (
            row.get("EarlySpeedPercentile", 0.5) * w.get("EarlySpeedPercentile", 0) +
            row.get("BestTimePercentile", 0.5) * w.get("BestTimePercentile", 0) +
            row.get("SpeedClassification", 1.0) * w.get("SpeedClassification", 0)
        )
        
        # Handle SectionalSec (lower is better, so invert)
        if pd.notna(row.get("SectionalSec")) and row["SectionalSec"] > 0:
            sec_normalized = min(1.0, max(0.0, 1 - (row["SectionalSec"] - 4) / 8))  # 4-12s range
            speed_score += sec_normalized * w.get("SectionalSec", 0)
        
        # 4. FORM/MOMENTUM SCORE (10-15%)
        form_score = (
            row.get("DLWFactor", 0.5) * w.get("DLWFactor", 0) * timing_weight_adjustment +
            row.get("WinStreakFactor", 1.0) * w.get("WinStreakFactor", 0) +
            row.get("FormMomentumNorm", 0.5) * w.get("FormMomentumNorm", 0) +
            row.get("MarginFactor", 0.5) * w.get("MarginFactor", 0)
        )
        
        # 5. CONDITIONING SCORE (5-10%)
        conditioning_score = (
            row.get("FreshnessFactor", 1.0) * w.get("FreshnessFactor", 0) +
            row.get("AgeFactor", 0.85) * w.get("AgeFactor", 0) +
            row.get("WeightFactor", 0.8) * w.get("WeightFactor", 0)
        )
        
        # COMBINE ALL SCORES
        total_score = box_score + career_score + speed_score + form_score + conditioning_score
        
        # Apply any penalties
        total_score += row.get("OverexposedPenalty", 0)
        
        # === APPLY LUCK FACTORS ===
        # These reduce/increase confidence based on predictability indicators
        field_similarity = row.get("FieldSimilarityIndex", 1.0)
        track_upset = row.get("TrackUpsetFactor", 1.0)
        competitor_adj = row.get("CompetitorAdjustment", 1.0)
        
        # Combine luck factors (multiplicative)
        luck_adjustment = field_similarity * (1 / track_upset) * competitor_adj
        
        # Apply luck adjustment (affects separation, not base score)
        # High luck_adjustment = more predictable = score stands
        # Low luck_adjustment = less predictable = scores compressed toward mean
        total_score = total_score * (0.8 + 0.2 * luck_adjustment)
        
        # ====================================================================
        # APPLY 8 NEW ENHANCEMENT FACTORS (Suggestions 1-8)
        # These are multiplicative adjustments based on analysis
        # ====================================================================
        
        # Enhancement #1: Grade-Based Scoring (reduces reliability for novices)
        grade_factor = row.get("GradeFactor", 0.9)
        
        # Enhancement #2: Last 3 Finishes Weight (recent form predictor)
        last3_factor = row.get("Last3FinishFactor", 1.0)
        
        # Enhancement #3: Distance Change Factor (penalize distance changes)
        distance_change_factor = row.get("DistanceChangeFactor", 1.0)
        
        # Enhancement #4: Pace-Box Interaction (front-runners in good boxes)
        pace_box_factor = row.get("PaceBoxFactor", 1.0)
        
        # Enhancement #5: Enhanced Trainer Tier
        trainer_tier = row.get("TrainerTier", 1.0)
        
        # Enhancement #6: Already applied in FreshnessFactor (refined)
        # Enhancement #7: Already applied in AgeFactor (refined)
        
        # Enhancement #8: Surface Preference Factor
        surface_factor = row.get("SurfacePreferenceFactor", 1.0)
        
        # ====================================================================
        # APPLY 4 ADDITIONAL ENHANCEMENT FACTORS (v3.4 - Capturing missed winners)
        # Based on analysis of 68 missed winners from Nov 28
        # ====================================================================
        
        # Enhancement #9: Enhanced Winning Streak (1.30x for hot streaks vs 1.08x before)
        # Already applied in WinStreakFactor (now WinStreakFactorV2)
        win_streak_bonus = row.get("WinStreakFactor", 1.0)
        
        # Enhancement #10: Closer Bonus for Box 7-8 at long distances
        closer_bonus = row.get("CloserBonus", 1.0)
        
        # Enhancement #11: Trainer Momentum (hot streak trainers)
        trainer_momentum = row.get("TrainerMomentum", 1.0)
        
        # Enhancement #12 (v3.7): Box Penalty Factor - CRITICAL FIX
        # Multiplicative penalty for boxes with very low win rates (Box 3, 7)
        # This prevents dogs in bad boxes from scoring too high
        box_penalty = row.get("BoxPenaltyFactor", 1.0)
        
        # Combine all enhancement factors (multiplicative)
        enhancement_multiplier = (
            grade_factor *
            last3_factor *
            distance_change_factor *
            pace_box_factor *
            trainer_tier *
            surface_factor *
            win_streak_bonus *        # Enhanced winning streak
            closer_bonus *            # Closer bonus at long distances
            trainer_momentum *        # Trainer hot streak
            box_penalty               # v3.7: Box penalty factor (Box 7=0.75x, Box 3=0.80x)
        )
        
        # Apply enhancement multiplier (centered around 1.0)
        # Range: Best case with all new factors = ~2.0x
        # Range: Worst case with all penalties = ~0.30x (including box penalty)
        total_score = total_score * enhancement_multiplier
        
        # Scale to 0-100 range for readability
        final_score = total_score * 100
        
        final_scores.append(final_score)

    df["FinalScore"] = final_scores
    return df

def generate_trifecta_table(df):
    trifecta_rows = []

    for (track, race), group in df.groupby(["Track", "RaceNumber"]):
        top3 = group.sort_values("FinalScore", ascending=False).head(3)
        if len(top3) < 3:
            continue

        scores = top3["FinalScore"].values
        separation_score = (scores[0] - scores[1]) + (scores[1] - scores[2])

        # Confidence tiering
        if scores[0] > 42 and separation_score > 3:
            tier = "Tier 1"
        elif scores[0] > 40 and separation_score > 2:
            tier = "Tier 2"
        elif scores[0] > 38 and separation_score > 1.5:
            tier = "Tier 3"
        else:
            tier = "Tier 4"

        trifecta_rows.append({
            "Track": track,
            "RaceNumber": race,
            "Dog1": top3.iloc[0]["DogName"],
            "Dog2": top3.iloc[1]["DogName"],
            "Dog3": top3.iloc[2]["DogName"],
            "Score1": scores[0],
            "Score2": scores[1],
            "Score3": scores[2],
            "SeparationScore": round(separation_score, 3),
            "ConfidenceTier": tier,
            "BetFlag": "BET" if tier in ["Tier 1", "Tier 2"] else "NO BET"
        })

    trifecta_df = pd.DataFrame(trifecta_rows)
    trifecta_df = trifecta_df.sort_values("SeparationScore", ascending=False)
    return trifecta_df
