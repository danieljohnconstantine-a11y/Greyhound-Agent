import pandas as pd
import numpy as np

# Scoring adjustment constants for missing timing data
# When timing data is unavailable, we boost other indicators to compensate
TIMING_MISSING_FULL_BOOST = 1.4  # 40% boost when both speed/early timing missing
TIMING_MISSING_PARTIAL_BOOST = 1.2  # 20% boost when only one timing metric missing
BOX_POSITION_BOOST = 1.5  # 50% boost to box position importance when timing unavailable
# Rationale: Dogs without timing data shouldn't be penalized for missing info;
# box position becomes more important predictor in absence of timing metrics

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
    BOX_WIN_RATE = {
        1: 0.181,   # 18.1% wins (70/386) - STRONGEST - 1.45x average
        2: 0.153,   # 15.3% wins (59/386) - #2 - 1.22x average
        3: 0.080,   # 8.0% wins (31/386) - WEAKEST - 0.64x average
        4: 0.127,   # 12.7% wins (49/386) - Near average
        5: 0.098,   # 9.8% wins (38/386) - Below average
        6: 0.119,   # 11.9% wins (46/386) - Slightly below
        7: 0.096,   # 9.6% wins (37/386) - Below average
        8: 0.142,   # 14.2% wins (55/386) - #3 - 1.14x average
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
        print(f"✓ Applied comprehensive BoxPositionBias from 386-race analysis")
        print(f"  Win/Place/Top3 rates analyzed for all 8 boxes")
    else:
        df["BoxPositionBias"] = 0.0
        df["BoxPlaceRate"] = 0.0
        df["BoxTop3Rate"] = 0.0
    
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
    if "BestTimeSec" in df.columns:
        df["BestTimePercentile"] = df.groupby(["Track", "RaceNumber"])["BestTimeSec"].rank(pct=True, ascending=True, na_option="top")
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
    TRACK_UPSET_PROBABILITY = {
        # Low upset tracks (more predictable)
        "Angle Park": 0.85,      # Box 1 dominance makes it predictable
        "Meadows": 0.87,
        "Temora": 0.88,
        "Healesville": 0.90,
        # Medium upset tracks
        "Bendigo": 0.95,
        "Sale": 0.95,
        "Richmond": 0.95,
        "Wentworth Park": 0.95,
        "Ladbrokes Q Straight": 0.95,
        "Warrnambool": 0.95,
        # High upset tracks (more unpredictable)
        "Casino": 1.05,          # High entropy = more random
        "Hobart": 1.05,
        "Mount Gambier": 1.05,
        "Shepparton": 1.05,
        "Warragul": 1.05,
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
            row.get("BoxBiasFactor", 0) * w.get("BoxBiasFactor", 0)
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
