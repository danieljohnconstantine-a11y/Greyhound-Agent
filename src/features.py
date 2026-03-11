import numpy as np
import pandas as pd

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
    # =========================================================================
    # DATA PROVENANCE SUMMARY
    # =========================================================================
    # FACTUAL (directly from the race PDF):
    #   Box, Draw, DogName, SexAge, Weight, Trainer, Distance, Track,
    #   RaceNumber, RaceDate, RaceTime, CareerWins, CareerPlaces, CareerStarts,
    #   PrizeMoney, RTC, DLR (Days Last Race), DLW (Days Last Win),
    #   BestTimeSec*, SectionalSec*, Last3TimesSec, Margins
    #
    #   * BestTimeSec and SectionalSec are extracted from the dog's PAST RACE
    #     history inside the PDF.  If the PDF contains no race history (new or
    #     lightly-raced dog), both fields arrive as None/NaN — the parser no
    #     longer fabricates values for them.  When NaN:
    #       - Speed_kmh = NaN, EarlySpeedIndex = NaN (excluded from scoring)
    #       - BestTimePercentile = 1/n percentile (lowest rank, via na_option="top")
    #       - timing_weight_adjustment = 1.4× (career/form factors boosted)
    #     The flag TimeEstimated=True is set on those rows.
    #
    # DERIVED FROM PDF DATA (computed, but all inputs are factual):
    #   Speed_kmh, EarlySpeedIndex, SpeedAtDistance, ConsistencyIndex,
    #   PlaceRate, WinPlaceRate, WinStreakFactor/DLWFactor (from DLW),
    #   FreshnessFactor/RestFactor (from DLR), ClassRating (PrizeMoney/field),
    #   AgeFactor/AgeMonths (from SexAge), RTCFactor (from RTC),
    #   ExperienceTier (from CareerStarts), TrainerStrikeRate (trainer career
    #   stats aggregated across the card), BestTimePercentile/EarlySpeedPercentile
    #   (rank within race), TimeVsField/SpeedVsField, FinishConsistency,
    #   MarginAvg/MarginFactor/FormMomentum, Last3AvgFinish, FieldSize,
    #   CompetitorDensity, DrawFactor, PaceBoxFactor, FieldSimilarityIndex
    #
    # HISTORICAL (real data from 7,108+ factual race results, NOT the current PDF):
    #   BoxPositionBias, BoxPlaceRate, BoxTop3Rate, BoxPenaltyFactor,
    #   TrackBox1Adjustment (v5.2: track's Box 1 win-rate adj for ALL dogs at venue),
    #   TrackBox4Adjustment (v5.2: track's Box 4 win-rate adj for ALL dogs at venue),
    #   TrackComprehensiveAdjustment (each dog's own box adj at this track),
    #   TrackUpsetFactor, RailPreference
    #
    # NEUTRAL PLACEHOLDERS (constant — ML models effectively ignore them):
    #   TrackConditionAdj (always 1.0 — no track condition in PDF)
    #   DistanceSuit      (1.0 for all standard distances 300–700 m;
    #                      kept for model compatibility, constant within any race)
    #
    # NOTE: FinalScore (end of this function) is a HEURISTIC composite of all
    # the above.  It is included in config['feature_cols'] because the ensemble
    # models were trained with it, but it is NOT directly from the PDF.
    # =========================================================================
    df = df.copy()

    # Ensure numeric types
    df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")
    df["CareerStarts"] = pd.to_numeric(df["CareerStarts"], errors="coerce")
    df["Distance"] = pd.to_numeric(df["Distance"], errors="coerce")
    
    # === ADD MISSING FEATURES FOR MODEL COMPATIBILITY ===
    # These features are expected by trained models but may not be in parsed data
    
    # CareerWins - use ONLY factual data from PDF (NO estimation)
    if "CareerWins" not in df.columns:
        # Try to use alternative column name if available
        if "Wins" in df.columns:
            df["CareerWins"] = pd.to_numeric(df["Wins"], errors="coerce").fillna(0)
        else:
            # Missing from PDF - use 0 (do NOT estimate from other fields)
            df["CareerWins"] = 0
    else:
        df["CareerWins"] = pd.to_numeric(df["CareerWins"], errors="coerce").fillna(0)
    
    # CareerPlaces - use ONLY factual data from PDF (NO estimation)
    if "CareerPlaces" not in df.columns:
        # Try to use alternative column name if available
        if "Places" in df.columns:
            df["CareerPlaces"] = pd.to_numeric(df["Places"], errors="coerce").fillna(0)
        else:
            # Missing from PDF - use 0 (do NOT estimate from other fields)
            df["CareerPlaces"] = 0
    else:
        df["CareerPlaces"] = pd.to_numeric(df["CareerPlaces"], errors="coerce").fillna(0)
    
    # PrizeMoney - use ONLY factual data from PDF (NO estimation)
    if "PrizeMoney" not in df.columns:
        # Missing from PDF - use 0 (do NOT estimate from other fields)
        df["PrizeMoney"] = 0
    else:
        df["PrizeMoney"] = pd.to_numeric(df["PrizeMoney"], errors="coerce").fillna(0)

    # Preserve parsed BestTimeSec and SectionalSec values if they exist, otherwise set to NaN
    if "BestTimeSec" not in df.columns:
        df["BestTimeSec"] = np.nan
        print("[WARNING] WARNING: BestTimeSec not found in parsed data - setting to NaN")
    else:
        df["BestTimeSec"] = pd.to_numeric(df["BestTimeSec"], errors="coerce")
        # Check for missing values
        missing_count = df["BestTimeSec"].isna().sum()
        if missing_count > 0:
            print(f"[WARNING] WARNING: {missing_count} dogs have missing BestTimeSec values")
        # Check if all values are the same (indicating parsing failure)
        # Only check if we have at least 2 non-NaN values
        if len(df) > 1:
            non_nan_count = df["BestTimeSec"].notna().sum()
            if non_nan_count > 1:
                unique_values = df["BestTimeSec"].dropna().nunique()
                if unique_values == 1:
                    print(f"[WARNING] WARNING: All {non_nan_count} dogs with BestTimeSec values have the same value ({df['BestTimeSec'].dropna().iloc[0]}). This may indicate a parsing issue.")
                    # Don't raise error - continue with data
    
    if "SectionalSec" not in df.columns:
        df["SectionalSec"] = np.nan
        print("[WARNING] WARNING: SectionalSec not found in parsed data - setting to NaN")
    else:
        df["SectionalSec"] = pd.to_numeric(df["SectionalSec"], errors="coerce")
        # Check for missing values
        missing_count = df["SectionalSec"].isna().sum()
        if missing_count > 0:
            print(f"[WARNING] WARNING: {missing_count} dogs have missing SectionalSec values")
        # Check if all values are the same (indicating parsing failure)
        # Only check if we have at least 2 non-NaN values
        if len(df) > 1:
            non_nan_count = df["SectionalSec"].notna().sum()
            if non_nan_count > 1:
                unique_values = df["SectionalSec"].dropna().nunique()
                if unique_values == 1:
                    print(f"[WARNING] WARNING: All {non_nan_count} dogs with SectionalSec values have the same value ({df['SectionalSec'].dropna().iloc[0]}). This may indicate a parsing issue.")
                    # Don't raise error - continue with data
    
    # Preserve parsed Last3TimesSec values if they exist, otherwise set to empty list
    if "Last3TimesSec" not in df.columns:
        df["Last3TimesSec"] = [[] for _ in range(len(df))]
        print("[WARNING] WARNING: Last3TimesSec not found in parsed data - setting to empty lists")
    else:
        # Check for missing values
        empty_count = df["Last3TimesSec"].apply(lambda x: len(x) == 0 if isinstance(x, list) else True).sum()
        if empty_count > 0:
            print(f"[WARNING] WARNING: {empty_count} dogs have missing/empty Last3TimesSec values")
        # Check if all values are the same (indicating parsing failure)
        if len(df) > 1:
            non_empty = df["Last3TimesSec"].apply(lambda x: tuple(x) if isinstance(x, list) and len(x) > 0 else None)
            non_empty_count = non_empty.notna().sum()
            if non_empty_count > 1:
                unique_values = non_empty.dropna().nunique()
                if unique_values == 1:
                    print(f"[WARNING] WARNING: All {non_empty_count} dogs with Last3TimesSec values have the same value. This may indicate a parsing issue.")
                    # Don't raise error - continue with data
    
    # Preserve parsed Margins values if they exist, otherwise set to empty list
    if "Margins" not in df.columns:
        df["Margins"] = [[] for _ in range(len(df))]
        print("[WARNING] WARNING: Margins not found in parsed data - setting to empty lists")
    else:
        # Check for missing values
        empty_count = df["Margins"].apply(lambda x: len(x) == 0 if isinstance(x, list) else True).sum()
        if empty_count > 0:
            print(f"[WARNING] WARNING: {empty_count} dogs have missing/empty Margins values")
        # Check if all values are the same (indicating parsing failure)
        if len(df) > 1:
            non_empty = df["Margins"].apply(lambda x: tuple(x) if isinstance(x, list) and len(x) > 0 else None)
            non_empty_count = non_empty.notna().sum()
            if non_empty_count > 1:
                unique_values = non_empty.dropna().nunique()
                if unique_values == 1:
                    print(f"[WARNING] WARNING: All {non_empty_count} dogs with Margins values have the same value. This may indicate a parsing issue.")
                    # Don't raise error - continue with data
    
    # BoxBiasFactor: Use parsed value if available, otherwise default to 0.0
    if "BoxBiasFactor" not in df.columns:
        df["BoxBiasFactor"] = 0.0
        print("[WARNING] WARNING: BoxBiasFactor not found in parsed data. Setting to 0.0 (neutral).")
    
    # TrackConditionAdj: Track condition adjustment.
    # SOURCE: NOT from PDF — greyhound form PDFs do not include track condition
    # (Good / Heavy / Wet etc.).  Set to 1.0 (neutral) for all dogs.
    # NOTE: This column is excluded from ML training (excluded in retrain_all_tracks_sigmoid.py
    # and train_ml_track_ensemble.py) because it is constant across every row in every race
    # and contributes zero information to the models.  Computed here only for any
    # legacy code that may reference it directly.
    df["TrackConditionAdj"] = 1.0
    
    # RestFactor: Calculate from DLR (Days Last Race) if not in parsed data
    if "RestFactor" not in df.columns:
        # Calculate RestFactor from DLR using factual data only
        if "DLR" in df.columns and df["DLR"].notna().sum() > 0:
            # Optimal rest is 6-10 days based on analysis
            df["RestFactor"] = df["DLR"].apply(
                lambda dlr: 1.0 if pd.notna(dlr) and 6 <= dlr <= 10 else
                           0.9 if pd.notna(dlr) and 4 <= dlr <= 14 else
                           0.7 if pd.notna(dlr) and 2 <= dlr <= 21 else
                           0.5 if pd.notna(dlr) else 0.8
            )
            print(f"[OK] Calculated RestFactor from DLR for {df['DLR'].notna().sum()} dogs")
        else:
            df["RestFactor"] = 1.0  # Neutral - no data to differentiate
            print("[INFO] INFO: RestFactor/DLR not found - set to neutral 1.0 (no differentiation).")

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
    # CRITICAL FIX: Detect maiden races (all dogs have CareerWins=0)
    # In maiden races, use CareerStarts as experience proxy instead of constant 0
    total_career_wins = df["CareerWins"].sum() if "CareerWins" in df.columns else 1
    is_maiden_race = total_career_wins == 0
    
    if is_maiden_race:
        # Maiden race: Use experience (CareerStarts) as differentiation
        # More starts = more experience = slight edge (normalize to 0-1 range)
        df["ConsistencyIndex"] = df["CareerStarts"].apply(lambda s: min(s / 20.0, 1.0))
        print(f"[WARNING] MAIDEN RACE DETECTED - Using CareerStarts for ConsistencyIndex differentiation")
    else:
        # Normal race: Use win rate
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
    # SOURCE: race Distance column from PDF (factual).
    # All dogs in a race run the same distance, so this is a race-level constant —
    # it cannot discriminate between dogs within the same race.  Its value is kept
    # purely for ML model compatibility (the model was trained with this feature).
    # Formula: standard greyhound distances (300–700 m) are all legitimate race
    # distances; no individual distance is "more suitable" than another in general.
    # We therefore give every standard distance 1.0 and only shade truly extreme
    # distances (< 300 m or > 700 m) which are rare and atypical.
    # PREVIOUS BUG: the formula was `1.0 if x in [515, 595] else 0.7` which
    # arbitrarily penalised every distance except the exact values 515 m
    # (Rockhampton) and 595 m (Darwin), effectively hard-coding a track advantage
    # for two venues rather than measuring distance suitability.
    def _distance_suit(x):
        """Return a distance-suitability score from the PDF race distance.

        All standard greyhound distances (300–700 m) are equally suitable, so
        they all receive 1.0.  Only truly atypical distances outside that range
        receive a slight reduction.  The value is the same for every dog in the
        same race (they all run the same distance), so it cannot discriminate
        between dogs within a race — it is kept solely for ML model compatibility.
        """
        if pd.isna(x):
            return 1.0
        try:
            d = float(x)
        except (ValueError, TypeError):
            return 1.0
        if d < 300:
            return 0.90   # Very short sprint — atypical
        if d <= 700:
            return 1.00   # All standard Australian greyhound distances
        return 0.90       # Very long — atypical

    df["DistanceSuit"] = df["Distance"].apply(_distance_suit)

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
        
        print(f"[OK] Calculated TrainerStrikeRate for {len(trainer_stats)} unique trainers")
        print(f"  Range: {df['TrainerStrikeRate'].min():.4f} to {df['TrainerStrikeRate'].max():.4f}")
        print(f"  Mean: {df['TrainerStrikeRate'].mean():.4f}")
    else:
        df["TrainerStrikeRate"] = 0.15
        print("[WARNING] WARNING: Cannot calculate TrainerStrikeRate - missing required columns. Setting to 0.15 (default).")
    
    # RestFactor: Check if it was already calculated above or present in parsed data
    if "RestFactor" in df.columns:
        # Log statistics
        rest_count = df["RestFactor"].notna().sum()
        print(f"[INFO] INFO: RestFactor found or calculated for {rest_count}/{len(df)} dogs.")

    # Overexposure Penalty
    df["OverexposedPenalty"] = df["CareerStarts"].apply(lambda x: -0.1 if x > 80 else 0)
    
    # === NEW VARIABLES - Added from 320-race analysis ===
    
    # PlaceRate: Career places / starts (dogs that place consistently are safer bets)
    if "CareerPlaces" in df.columns and "CareerStarts" in df.columns:
        df["PlaceRate"] = df.apply(
            lambda row: row["CareerPlaces"] / row["CareerStarts"] if row["CareerStarts"] > 0 else 0,
            axis=1
        )
        print(f"[OK] Calculated PlaceRate for {len(df)} dogs")
    else:
        df["PlaceRate"] = 0.15
        print("[WARNING] WARNING: Cannot calculate PlaceRate - missing required columns. Setting to 0.15.")
    
    # DLW Factor: Days since last win (recent winners perform better)
    # Analysis of 320 races (Sep-Nov 2025) from data/race_results_nov_2025.csv showed:
    # - Dogs that won within 14 days: ~23% higher win rate than average
    # - Dogs that won within 30 days: ~15% higher win rate
    # - Dogs with no recent wins (60+ days): significantly lower win rates
    # CRITICAL FIX: Handle maiden races (DLW="Mdn") specially
    if "DLW" in df.columns:
        # Check for maiden race indicators
        maiden_count = (df["DLW"] == "Mdn").sum() + (df["DLW"] == "MDN").sum()
        is_maiden_for_dlw = maiden_count >= len(df) * 0.5
        
        if is_maiden_for_dlw:
            # Maiden race: All dogs get neutral DLWFactor
            df["DLWFactor"] = 0.5
            print(f"[WARNING] MAIDEN RACE DETECTED (DLW='Mdn') - Setting neutral DLWFactor=0.5 for all")
        else:
            # Normal race: Convert numeric DLW values
            df["DLW"] = pd.to_numeric(df["DLW"], errors="coerce")
            df["DLWFactor"] = df["DLW"].apply(
                lambda x: 1.0 if pd.notna(x) and x <= 14 else 
                         0.7 if pd.notna(x) and x <= 30 else 
                         0.4 if pd.notna(x) and x <= 60 else 0.2
            )
            print(f"[OK] Calculated DLWFactor based on Days Last Win")
    else:
        df["DLWFactor"] = 0.5
        print("[WARNING] WARNING: DLW not found - setting DLWFactor to 0.5 (neutral).")
    
    # Weight Factor: Greyhound PDFs never include weight data → Weight=0 always.
    # WeightFactor is therefore always 1.0 (neutral) for every dog in every race.
    # NOTE: Both 'Weight' and 'WeightFactor' are excluded from ML training (removed
    # from FEATURE_COLS in retrain_all_tracks_sigmoid.py and added to exclude_cols
    # in train_ml_track_ensemble.py).  They are computed here only for any legacy
    # code that may reference them directly.
    if "Weight" in df.columns:
        df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
        valid_weights = df["Weight"][(df["Weight"].notna()) & (df["Weight"] > 0)]
        if len(valid_weights) == 0:
            df["WeightFactor"] = 1.0
        else:
            df["WeightFactor"] = df["Weight"].apply(
                lambda w: 1.0 if pd.notna(w) and 29.5 <= w <= 31.5 else 
                         0.9 if pd.notna(w) and 28 <= w <= 33 else 
                         0.7 if pd.notna(w) and 25 <= w <= 36 else 0.5
            )
    else:
        df["WeightFactor"] = 1.0
    
    # Draw Factor: Inside draws (1-4) generally perform better
    # Analysis of 320 races showed draws 1-3 have ~17% higher win rate than draws 7-10
    # FACTUAL DATA ONLY: Use Draw/Box data if available
    if "Draw" in df.columns:
        df["Draw"] = pd.to_numeric(df["Draw"], errors="coerce")
        valid_draw = df["Draw"].notna().sum()
        if valid_draw > 0:
            df["DrawFactor"] = df["Draw"].apply(
                lambda d: 1.0 if pd.notna(d) and d <= 3 else 
                         0.85 if pd.notna(d) and d <= 5 else 
                         0.7 if pd.notna(d) and d <= 8 else 0.6
            )
            print(f"[OK] Calculated DrawFactor for {valid_draw} dogs")
        else:
            df["DrawFactor"] = 0.85  # Neutral - all same
            print("[INFO] INFO: Draw column exists but all values missing - DrawFactor set to neutral 0.85")
    elif "Box" in df.columns:
        # Use Box as fallback for Draw
        df["Draw"] = pd.to_numeric(df["Box"], errors="coerce")
        valid_draw = df["Draw"].notna().sum()
        if valid_draw > 0:
            df["DrawFactor"] = df["Draw"].apply(
                lambda d: 1.0 if pd.notna(d) and d <= 3 else 
                         0.85 if pd.notna(d) and d <= 5 else 
                         0.7 if pd.notna(d) and d <= 8 else 0.6
            )
            print(f"[OK] Calculated DrawFactor from Box for {valid_draw} dogs")
        else:
            df["DrawFactor"] = 0.85  # Neutral
            print("[INFO] INFO: Box column exists but all values missing - DrawFactor set to neutral 0.85")
    else:
        df["DrawFactor"] = 0.85  # Neutral - no data
        print("[INFO] INFO: Draw/Box not found - DrawFactor set to neutral 0.85 (no differentiation).")
    
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
    # FACTUAL DATA ONLY: If RTC missing, use neutral value (no differentiation)
    if "RTC" in df.columns:
        df["RTC"] = pd.to_numeric(df["RTC"], errors="coerce")
        valid_rtc = df["RTC"].notna().sum()
        if valid_rtc > 0:
            df["RTCFactor"] = df.apply(
                lambda row: min(max((row["RTC"] - 50) / 50, 0), 1) if pd.notna(row["RTC"]) else 0.5,
                axis=1
            )
            print(f"[OK] Calculated RTCFactor from Racing Times Category for {valid_rtc} dogs")
        else:
            df["RTCFactor"] = 0.5  # Neutral - all same, no differentiation
            print("[INFO] INFO: RTC column exists but all values missing - RTCFactor set to neutral 0.5")
    else:
        df["RTCFactor"] = 0.5  # Neutral - no data, no differentiation
        print("[INFO] INFO: RTC not found - RTCFactor set to neutral 0.5 (no differentiation).")

    # ========================================================================
    # COMPREHENSIVE BOX ANALYSIS - Based on 386 race results (Sep-Nov 2025)
    # Source: data/race_results_nov_2025.csv | 90.3% timing data coverage
    # ========================================================================
    
    # === BOX WIN RATE — computed from 7,108 factual race results (Mar 2026) ===
    # All 57 results CSVs across all tracks; zero synthetic data.
    BOX_WIN_RATE = {
        1: 0.183,   # 1298/7108 = 18.3%  (+5.8 pp above random)
        2: 0.159,   # 1127/7108 = 15.9%  (+3.4 pp)
        3: 0.102,   #  728/7108 = 10.2%  (-2.3 pp)
        4: 0.122,   #  870/7108 = 12.2%  (-0.3 pp, near-random)
        5: 0.093,   #  663/7108 =  9.3%  (-3.2 pp)
        6: 0.094,   #  668/7108 =  9.4%  (-3.1 pp)
        7: 0.110,   #  781/7108 = 11.0%  (-1.5 pp)
        8: 0.130,   #  922/7108 = 13.0%  (+0.5 pp)
    }

    # === PLACE RATE (2nd place) — computed from 7,108 results ===
    BOX_PLACE_RATE = {
        1: 0.159,   # 1127/7108 = 15.9%
        2: 0.151,   # 1075/7108 = 15.1%
        3: 0.098,   #  698/7108 =  9.8%
        4: 0.121,   #  860/7108 = 12.1%
        5: 0.093,   #  663/7108 =  9.3%
        6: 0.105,   #  743/7108 = 10.5%
        7: 0.122,   #  868/7108 = 12.2%
        8: 0.142,   # 1012/7108 = 14.2%
    }

    # === TOP 3 RATE (1st+2nd+3rd) — computed from 7,108 results ===
    BOX_TOP3_RATE = {
        1: 0.493,   # 3507/7108 = 49.3%
        2: 0.434,   # 3087/7108 = 43.4%
        3: 0.303,   # 2157/7108 = 30.3%
        4: 0.375,   # 2665/7108 = 37.5%
        5: 0.291,   # 2070/7108 = 29.1%
        6: 0.301,   # 2140/7108 = 30.1%
        7: 0.357,   # 2540/7108 = 35.7%
        8: 0.414,   # 2944/7108 = 41.4%
    }
    
    # === EXACTA PATTERNS — computed from 7,108 factual race results (Mar 2026) ===
    EXACTA_BONUS = {
        (1, 2): 0.036,  # 257/7108 = 3.6% — most common
        (2, 1): 0.035,  # 246/7108 = 3.5%
        (1, 8): 0.032,  # 227/7108 = 3.2% — inside/outside combo
        (2, 8): 0.028,  # 196/7108 = 2.8%
        (4, 1): 0.026,  # 183/7108 = 2.6%
        (1, 4): 0.025,  # 178/7108 = 2.5%
        (8, 2): 0.025,  # 177/7108 = 2.5%
        (8, 1): 0.024,  # 173/7108 = 2.4%
        (1, 7): 0.024,  # 171/7108 = 2.4%
        (2, 7): 0.023,  # 163/7108 = 2.3%
    }
    
    # === TRACK-SPECIFIC BOX 1 BIAS ===
    # NOTE: All track+box adjustments are now consolidated in TRACK_COMPREHENSIVE_ADJUSTMENTS
    # below (computed from 7,108 real races). TRACK_BOX1_ADJUSTMENT is zeroed to prevent
    # double-counting — the comprehensive dict already covers Box 1 for every track.
    # The TrackBox1Adjustment column is kept for model compatibility (trained models expect it).
    TRACK_BOX1_ADJUSTMENT = {
        "DEFAULT": 0.0,
    }
    
    # === TRACK-SPECIFIC BOX 4 BOOST ===
    # NOTE: Consolidated into TRACK_COMPREHENSIVE_ADJUSTMENTS. Zeroed to prevent double-counting.
    TRACK_BOX4_ADJUSTMENT = {
        "DEFAULT": 0.0,
    }
    
    # ========================================================================
    # v4.0: COMPREHENSIVE TRACK-SPECIFIC SCORING
    # Based on deep-dive analysis of 386+ races (Nov 2025)
    # 
    # PROBLEM: Darwin (9.1%) and Rockhampton (0%) have very low accuracy
    # SOLUTION: Track-specific box adjustments for ALL boxes, not just Box 1/4
    # 
    # Key findings:
    # Updated with data-driven values computed from 7,108 real race results (Mar 2026)
    # Formula: adjustment = (win_rate_pct - 12.5) * 0.008, capped at ±0.15
    # Only adjustments with |value| >= 0.005 are included (noise threshold).
    # ========================================================================

    TRACK_COMPREHENSIVE_ADJUSTMENTS = {
        # ====================================================================
        # DATA-DRIVEN BOX ADJUSTMENTS — computed from 7,108 factual race results
        # Each value = (actual_win_pct - 12.5%) × 0.008, capped ±0.15
        # Source: data/results_*.csv — ALL factual, zero synthetic data
        # ====================================================================

        # Angle Park (254 races): Box1=24%, Box2=21%, Box3=4%, Box6=6%
        "Angle Park": {
            1:  0.089, 2:  0.067,
            3: -0.065, 6: -0.056, 5: -0.024, 8: -0.009, 7: -0.006,
        },
        # Ballarat (239 races): Box1=20%, Box3=8%, Box5=9%, Box7=10%
        "Ballarat": {
            1:  0.057, 4:  0.014,
            3: -0.036, 5: -0.026, 7: -0.020, 6: -0.010,
        },
        # Bendigo (178 races): Box2=16%, Box8=16%, Box5=8%, Box6=9%
        "Bendigo": {
            2:  0.030, 8:  0.030, 1:  0.012, 4:  0.012,
            5: -0.033, 6: -0.028, 7: -0.019,
        },
        # Bulli (101 races): Box2=23%, Box1=20%, Box4=17%, Box5=5%
        "Bulli": {
            2:  0.082, 1:  0.058, 4:  0.035,
            5: -0.060, 3: -0.045, 6: -0.037, 7: -0.029,
        },
        # Cannington (158 races): Box1=28%, Box2=18%, Box6=4%, Box7=7%
        "Cannington": {
            1:  0.123, 2:  0.047,
            6: -0.065, 7: -0.044, 8: -0.039, 3: -0.014, 4: -0.014,
        },
        # Capalaba / BetDeluxe Capalaba (158 races): Box8=17%, Box1=16%, Box7=16%, Box5=7%
        "Capalaba": {
            8:  0.037, 1:  0.032, 7:  0.032,
            5: -0.044, 3: -0.034, 4: -0.014,
        },
        # Casino (137 races): Box1=26%, Box4=15%, Box2=15%, Box6=6%
        "Casino": {
            1:  0.104, 4:  0.023, 2:  0.017,
            6: -0.053, 5: -0.036, 8: -0.036, 3: -0.030,
        },
        # Darwin (82 races): Box2=30%, Box8=22%, Box3=4%, Box6=5%
        "Darwin": {
            2:  0.144, 8:  0.076,
            3: -0.071, 6: -0.061, 5: -0.041, 4: -0.032,
        },
        # Dubbo (114 races): Box1=19%, Box4=16%, Box5=15%, Box6=4%
        "Dubbo": {
            1:  0.054, 4:  0.026, 5:  0.019,
            6: -0.065, 2: -0.030, 7: -0.023,
        },
        # Gardens / Ladbrokes Gardens (168 races): Box2=18%, Box1=17%, Box8=8%, Box5=10%
        "Gardens": {
            2:  0.043, 1:  0.038,
            8: -0.033, 5: -0.024, 3: -0.019, 7: -0.019,
        },
        # Gawler (163 races): Box1=25%, Box8=17%, Box3=7%, Box6=7%
        "Gawler": {
            1:  0.101, 8:  0.033,
            3: -0.046, 6: -0.041, 7: -0.036, 5: -0.031,
        },
        # Geelong (144 races): Box2=16%, Box4=15%, Box7=15%, Box5=6%
        "Geelong": {
            2:  0.028, 4:  0.022, 7:  0.017, 3:  0.011, 8:  0.011,
            5: -0.050, 6: -0.044,
        },
        # Gosford (104 races): near-even distribution, slight outside advantage
        "Gosford": {
            2:  0.015, 8:  0.015, 1:  0.008, 7:  0.008,
            4: -0.023, 3: -0.015, 5: -0.008, 6: -0.008,
        },
        # Goulburn (64 races): Box1=22%, Box8=16%, Box3=6%, Box6=8%
        "Goulburn": {
            1:  0.075, 8:  0.025, 4:  0.012, 5:  0.012,
            3: -0.050, 6: -0.038, 7: -0.025, 2: -0.012,
        },
        # Grafton (120 races): Box2=17%, Box8=17%, Box4=16%, Box5=7%
        "Grafton": {
            2:  0.033, 8:  0.033, 4:  0.027,
            5: -0.047, 3: -0.027, 6: -0.020,
        },
        # Gunnedah (116 races): Box2=17%, Box3=8%, Box5=10%
        "Gunnedah": {
            2:  0.038, 1:  0.010, 7:  0.010,
            3: -0.038, 5: -0.017, 4: -0.010, 8: -0.010,
        },
        # Healesville (253 races): Box8=15%, Box2=14%, Box1=13%, Box7=13%
        "Healesville": {
            8:  0.023, 2:  0.014, 1:  0.004, 7:  0.004,
            4: -0.018, 5: -0.018, 3: -0.015,
        },
        # Hobart / Tasmania (113 races): Box1=21%, Box3=15%, Box7=6%
        "Hobart": {
            1:  0.070, 3:  0.020, 4:  0.013, 8:  0.013,
            7: -0.050, 5: -0.036, 6: -0.029, 2: -0.015,
        },
        # Horsham (84 races): Box1=23%, Box2=21%, Box3=16%, Box5=5%
        "Horsham": {
            1:  0.081, 2:  0.071, 3:  0.024,
            5: -0.062, 6: -0.033, 8: -0.033, 4: -0.024, 7: -0.024,
        },
        # Launceston (120 races): Box1=33% — strongest inside bias in dataset
        "Launceston": {
            1:  0.150, 2:  0.013,
            5: -0.060, 6: -0.047, 4: -0.040, 7: -0.020, 8: -0.013,
        },
        # Maitland (88 races): Box2=18%, Box3=16%, Box5=8%, Box6=8%
        "Maitland": {
            2:  0.045, 3:  0.027, 4:  0.009,
            5: -0.036, 6: -0.036, 1: -0.009, 8: -0.009,
        },
        # Mandurah (334 races): Box1=17%, Box2=16%, Box3=15%, Box4=8%
        "Mandurah": {
            1:  0.037, 2:  0.027, 3:  0.020, 8:  0.017,
            4: -0.040, 6: -0.026, 5: -0.023, 7: -0.016,
        },
        # Meadows (146 races): Box1=23%, Box4=15%, Box5=8%, Box6=8%
        "Meadows": {
            1:  0.081, 4:  0.021, 2:  0.015,
            5: -0.040, 6: -0.034, 3: -0.023, 7: -0.012,
        },
        # Mount Gambier (155 races): Box1=27%, Box2=19%, Box3=2%, Box5=4%
        "Mount Gambier": {
            1:  0.117, 2:  0.050, 4:  0.029, 8:  0.008,
            3: -0.085, 5: -0.064, 7: -0.038, 6: -0.033,
        },
        # Murray Bridge (41 races): Box8=22%, Box2=20%, Box3=2%, Box6=5%
        "Murray Bridge": {
            8:  0.076, 2:  0.056, 1:  0.037, 5:  0.017,
            3: -0.080, 6: -0.061, 7: -0.041,
        },
        # Murray Bridge Straight (88 races): Box2=20%, Box1=18%, Box4=17%, Box8=16%
        "Murray Bridge Straight": {
            2:  0.064, 1:  0.045, 4:  0.036, 8:  0.027,
            3: -0.055, 5: -0.045, 6: -0.045, 7: -0.027,
        },
        # Nowra (168 races): Box2=20%, Box1=17%, Box5=16%, Box3=7%
        "Nowra": {
            2:  0.057, 1:  0.038, 5:  0.024, 4:  0.014,
            3: -0.043, 7: -0.043, 6: -0.029, 8: -0.019,
        },
        # Q Lakeside / Ladbrokes Q1 Lakeside (402 races): Box1=18%, Box2=15%
        "Lakeside": {
            1:  0.043, 2:  0.021, 4:  0.009,
            5: -0.032, 6: -0.026, 3: -0.012,
        },
        # Q Parklands / Ladbrokes Q2 Parklands (162 races): Box2=18%, Box1=16%, Box6=7%
        "Parklands": {
            2:  0.043, 1:  0.028, 4:  0.014, 7:  0.009,
            6: -0.041, 5: -0.026, 8: -0.026, 3: -0.011,
        },
        # Q Straight / Ladbrokes Q Straight (183 races): Box6=16%, Box3=15%, Box2=15%
        "Q Straight": {
            6:  0.027, 2:  0.022, 3:  0.022,
            4: -0.030, 5: -0.021, 7: -0.017, 8: -0.017,
        },
        # Richmond (234 races): Box1=18%, Box2=14%, Box4=9%, Box5=9%
        "Richmond": {
            1:  0.047, 2:  0.009, 8:  0.009,
            4: -0.025, 5: -0.025, 7: -0.018,
        },
        # Richmond Straight (65 races): Box8=20%, Box1=14%
        "Richmond Straight": {
            8:  0.060, 1:  0.011,
            2: -0.014, 4: -0.014, 5: -0.014, 6: -0.014, 7: -0.014,
        },
        # Rockhampton / BetDeluxe Rockhampton (141 races): Box1=21%, Box7=14%, Box8=8%
        "Rockhampton": {
            1:  0.065, 7:  0.008,
            8: -0.032, 3: -0.021, 5: -0.015, 6: -0.009,
        },
        # Sale (178 races): Box8=17%, Box6=15%, Box3=9%
        "Sale": {
            8:  0.035, 6:  0.017,
            3: -0.028, 4: -0.015, 5: -0.015,
        },
        # Sandown (148 races): Box2=25%, Box1=18%, Box4=17%, Box7=7%
        "Sandown": {
            2:  0.100, 1:  0.046, 4:  0.035,
            7: -0.046, 6: -0.041, 3: -0.035, 5: -0.035, 8: -0.030,
        },
        # Shepparton (191 races): Box1=16%, Box2=16%, Box4=8%, Box5=10%
        "Shepparton": {
            1:  0.030, 2:  0.030, 3:  0.009, 8:  0.005,
            4: -0.033, 5: -0.016, 6: -0.016, 7: -0.016,
        },
        # Taree (157 races): Box2=16%, Box1=15%, Box6=8%, Box4=10%
        "Taree": {
            2:  0.027, 1:  0.022, 8:  0.012, 5:  0.007,
            6: -0.039, 4: -0.024, 7: -0.018,
        },
        # Temora (78 races): Box1=22%, Box8=15%, Box3=8%
        "Temora": {
            1:  0.074, 8:  0.023,
            3: -0.038, 4: -0.018, 5: -0.018, 6: -0.018, 7: -0.008,
        },
        # Townsville / Bet Nation Townsville (143 races): Box8=17%, Box1=16%, Box5=9%
        "Townsville": {
            8:  0.034, 1:  0.029,
            5: -0.027, 6: -0.016, 2: -0.010, 3: -0.010,
        },
        # Wagga (80 races): Box1=22%, Box8=15%, Box6=5%
        "Wagga": {
            1:  0.080, 8:  0.020, 3:  0.010, 4:  0.010,
            6: -0.060, 5: -0.040, 2: -0.020,
        },
        # Warragul (226 races): Box2=20%, Box3=16%, Box1=15%, Box5=7%
        "Warragul": {
            2:  0.059, 3:  0.027, 1:  0.017, 8:  0.017,
            5: -0.047, 4: -0.036, 6: -0.022, 7: -0.019,
        },
        # Warrnambool (203 races): Box2=18%, Box6=18%, Box5=5%
        "Warrnambool": {
            2:  0.042, 6:  0.042, 1:  0.018, 4:  0.006,
            5: -0.057, 3: -0.025, 7: -0.021, 8: -0.013,
        },
        # Wentworth Park (135 races): Box5=16%, Box1=16%, Box2=11%, Box3=10%
        "Wentworth Park": {
            5:  0.030, 1:  0.024,
            3: -0.017, 6: -0.017, 2: -0.011, 4: -0.011,
        },

        # Broken Hill (24 races): small sample — conservative adjustments
        "Broken Hill": {
            4:  0.040, 1:  0.020,
            3: -0.030, 7: -0.020,
        },
    }

    # Keep backward-compat aliases so any PDF that uses the long sponsor name still
    # matches the same dict entry via the substring lookup at line ~1095.
    TRACK_COMPREHENSIVE_ADJUSTMENTS["BetDeluxe Capalaba"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Capalaba"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Ladbrokes Gardens"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Gardens"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Ladbrokes Q1 Lakeside"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Lakeside"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Ladbrokes Q2 Parklands"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Parklands"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Ladbrokes Q Straight"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Q Straight"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["BetDeluxe Rockhampton"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Rockhampton"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Bet Nation Townsville"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Townsville"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Tasmania"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Hobart"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Murray Bdge Straight"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Murray Bridge Straight"]
    TRACK_COMPREHENSIVE_ADJUSTMENTS["Sandown Park"] = TRACK_COMPREHENSIVE_ADJUSTMENTS["Sandown"]

    # ========================================================================
    # v4.1: TRACK-SPECIFIC FACTOR WEIGHT ADJUSTMENTS
    # Based on analysis of 484+ races identifying which factors matter most
    # at each track type. Different tracks favor different winning profiles.
    # ========================================================================
    
    TRACK_FACTOR_WEIGHTS = {
        # BOX 1 DOMINANT TRACKS - Speed/Inside Advantage
        # Prioritize: BestTimePercentile, EarlySpeedPercentile, BoxPositionBias
        "Meadows": {"BestTimePercentile": 0.08, "EarlySpeedPercentile": 0.06, "BoxPositionBias": 0.05, "WinStreakFactor": 0.04},
        "Angle Park": {"BestTimePercentile": 0.08, "EarlySpeedPercentile": 0.06, "BoxPositionBias": 0.05, "WinStreakFactor": 0.04},
        "Ladbrokes Q Straight": {"BestTimePercentile": 0.08, "EarlySpeedPercentile": 0.06, "BoxPositionBias": 0.05},
        "Mount Gambier": {"BestTimePercentile": 0.07, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.04},
        "Sale": {"BestTimePercentile": 0.07, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.04},
        # Sandown (148 races): Box2=25% dominant — form/speed dual; Box 1 secondary (18%)
        "Sandown Park": {"DLWFactor": 0.07, "BestTimePercentile": 0.06, "ConsistencyIndex": 0.05, "BoxPositionBias": 0.04},
        "Sandown": {"DLWFactor": 0.07, "BestTimePercentile": 0.06, "ConsistencyIndex": 0.05, "BoxPositionBias": 0.04},
        
        # BOX 2 DOMINANT / FORM TRACKS - Form/Consistency Advantage
        # Dubbo (114 races): Box1=19% dominant, Box4=16%, Box6=4% weak — Box 1 speed track
        # (was incorrectly marked Box 2 dominant — Box 2 only 9%)
        "Dubbo": {"BestTimePercentile": 0.07, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.05, "ConsistencyIndex": 0.04},
        # Nowra (168 races): Box2=20%, Box1=17%, Box5=16% — Box 2 slight form
        "Nowra": {"DLWFactor": 0.08, "ConsistencyIndex": 0.07, "PlaceRate": 0.05, "CloserBonus": 0.04},
        
        # v4.2: Q PARKLANDS - Box 2 dominant (40% Nov 30)
        # Reduce Box 1 bias, boost form/consistency factors
        "Ladbrokes Q2 Parklands": {"DLWFactor": 0.08, "ConsistencyIndex": 0.06, "PlaceRate": 0.05, "BestTimePercentile": 0.03},
        "Q2 Parklands": {"DLWFactor": 0.08, "ConsistencyIndex": 0.06, "PlaceRate": 0.05, "BestTimePercentile": 0.03},
        "Q Parklands": {"DLWFactor": 0.08, "ConsistencyIndex": 0.06, "PlaceRate": 0.05, "BestTimePercentile": 0.03},
        
        # Richmond (234 races): Box1=18% — mild inside advantage, near-even distribution
        # Corrected from v4.2 "Box 2 dominant" which was based on one Nov 30 session
        "Richmond": {"BestTimePercentile": 0.06, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.04, "ConsistencyIndex": 0.04},
        
        # Darwin (82 races): Box2=30%, Box8=22% — Box 2 form track, Box 8 closer
        # Corrected from v4.2 "Box 7 dominant" which was wrong; real data shows Box7=11%
        "Darwin": {"DLWFactor": 0.09, "ConsistencyIndex": 0.07, "CloserBonus": 0.06, "PlaceRate": 0.05},
        
        # BOX 8 DOMINANT TRACKS - Closer Advantage
        # Prioritize: CloserBonus, BestTimePercentile at distance
        # v5.1: Casino MOVED to BOX 1 — actual data (137 races) shows Box 1=25.5%
        "Horsham": {"CloserBonus": 0.07, "BestTimePercentile": 0.05, "ExperienceTier": 0.04},
        "Warrnambool": {"ConsistencyIndex": 0.07, "DLWFactor": 0.06, "PlaceRate": 0.05, "BestTimePercentile": 0.04},
        "Healesville": {"CloserBonus": 0.06, "BestTimePercentile": 0.06, "ExperienceTier": 0.05},

        # BOX 4 DOMINANT TRACKS - Experience Advantage
        # Prioritize: ExperienceTier, ConsistencyIndex
        "Bendigo": {"ExperienceTier": 0.06, "ConsistencyIndex": 0.05, "BestTimePercentile": 0.04, "FormMomentumNorm": 0.03},
        # v5.0: Shepparton REMOVED from BOX 4 DOMINANT — Box 4 only 8% on 10/03/2026.
        # Reclassified below as MIXED (Box 1/8 — see TRACK_COMPREHENSIVE_ADJUSTMENTS).

        # MIXED (BOX 1 + OUTER) TRACKS - Speed + Closing combo
        # Prioritize: BestTimePercentile + CloserBonus equally
        "Shepparton": {"BestTimePercentile": 0.05, "CloserBonus": 0.04, "ConsistencyIndex": 0.04, "ExperienceTier": 0.03},
        
        # BOX 2 DOMINANT TRACKS (updated) — Warragul reclassified from BOX 6 to BOX 2
        # v5.1: 226 race data confirms Box 2=19.9% dominant
        "Warragul": {"DLWFactor": 0.07, "ConsistencyIndex": 0.06, "PlaceRate": 0.05, "TrainerStrikeRate": 0.04},
        
        # BOX 7 DOMINANT TRACKS - Closer Advantage
        # Prioritize: CloserBonus, FormMomentum
        "Wentworth Park": {"CloserBonus": 0.08, "FormMomentumNorm": 0.05, "BestTimePercentile": 0.04, "AgeFactor": 0.03},
        "Mandurah": {"BestTimePercentile": 0.06, "EarlySpeedPercentile": 0.05, "ConsistencyIndex": 0.05, "WinStreakFactor": 0.04},
        
        # v4.2: PROBLEMATIC TRACKS - MAJOR OVERHAUL based on Nov 30 actual results
        # ROCKHAMPTON: Box 1 (33.3%) + Box 3 (25%) - Inside track advantage
        # We were picking Box 8/4 (0% wins there) - PENALIZE outside speed, BOOST inside form
        "Rockhampton": {
            "DLWFactor": 0.10,           # v4.2: Form matters more than speed here
            "ConsistencyIndex": 0.08,    # v4.2: Consistent dogs win
            "BoxPositionBias": 0.06,     # v4.2: Still boost Box 1
            "BestTimePercentile": 0.02,  # v4.2: REDUCED - speed alone doesn't work here
        },
        "BetDeluxe Rockhampton": {
            "DLWFactor": 0.10,
            "ConsistencyIndex": 0.08, 
            "BoxPositionBias": 0.06,
            "BestTimePercentile": 0.02,
        },
        
        "Maitland": {
            "DLWFactor": 0.06,
            "ConsistencyIndex": 0.05,
            "BestTimePercentile": 0.05,
            "PlaceRate": 0.04,
        },

        # ====================================================================
        # v5.1: NEW TRACK ENTRIES — based on actual results CSV data
        # ====================================================================

        # BOX 1 DOMINANT — speed/inside advantage
        "Cannington": {"BestTimePercentile": 0.09, "EarlySpeedPercentile": 0.07, "BoxPositionBias": 0.06, "WinStreakFactor": 0.04},
        "Casino": {"BestTimePercentile": 0.07, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.05, "ConsistencyIndex": 0.04},
        "Goulburn": {"BestTimePercentile": 0.07, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.05},
        "Hobart": {"BestTimePercentile": 0.07, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.05, "ConsistencyIndex": 0.03},
        "Launceston": {"BestTimePercentile": 0.09, "EarlySpeedPercentile": 0.07, "BoxPositionBias": 0.07, "WinStreakFactor": 0.04},
        "Wagga": {"BestTimePercentile": 0.07, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.05, "ConsistencyIndex": 0.03},

        # BOX 2 DOMINANT — form/consistency advantage
        "Bulli": {"DLWFactor": 0.08, "ConsistencyIndex": 0.07, "PlaceRate": 0.05, "TrainerStrikeRate": 0.04},

        # MIXED / EVEN — balanced approach
        "Geelong": {"ConsistencyIndex": 0.06, "DLWFactor": 0.05, "BestTimePercentile": 0.05, "PlaceRate": 0.04},
        "Gosford": {"ConsistencyIndex": 0.06, "DLWFactor": 0.05, "PlaceRate": 0.04, "WinStreakFactor": 0.04},
        "Taree": {"ConsistencyIndex": 0.06, "DLWFactor": 0.05, "BestTimePercentile": 0.04, "PlaceRate": 0.04},
        "Townsville": {"BestTimePercentile": 0.06, "EarlySpeedPercentile": 0.05, "CloserBonus": 0.05, "ConsistencyIndex": 0.04},

        # GARDENS — slight Box 1/2 inside bias
        "Ladbrokes Gardens": {"BestTimePercentile": 0.06, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.04, "ConsistencyIndex": 0.04},

        # MANDURAH — very even; balanced
        # (already in dict above, kept for canonical name)

        # MURRAY BRIDGE — Box 8/2 outer-inner split
        "Murray Bridge": {"CloserBonus": 0.07, "DLWFactor": 0.06, "ConsistencyIndex": 0.05, "PlaceRate": 0.04},
        "Murray Bridge Straight": {"BestTimePercentile": 0.06, "EarlySpeedPercentile": 0.05, "BoxPositionBias": 0.04, "CloserBonus": 0.04},

        # RICHMOND STRAIGHT — Box 8 closer advantage
        "Richmond Straight": {"CloserBonus": 0.08, "BestTimePercentile": 0.06, "ExperienceTier": 0.04},
    }
    
    def get_track_factor_adjustments(track_name):
        """Get track-specific factor weight adjustments based on winner pattern analysis."""
        if pd.isna(track_name):
            return {}
        track_str = str(track_name).strip().lower()
        
        # Three safe matching conditions (no startswith to avoid "Murray Bridge"
        # matching "Murray Bridge Straight"):
        #   1) exact match
        #   2) track ends with key  (e.g. "Ladbrokes Q Straight" → key "Q Straight")
        #   3) key ends with track  (e.g. track "Capalaba" → key "BetDeluxe Capalaba")
        # Sort longest-first as a safety net for remaining ambiguities.
        for key in sorted(TRACK_FACTOR_WEIGHTS, key=len, reverse=True):
            key_lower = key.lower()
            if (key_lower == track_str or
                track_str.endswith(" " + key_lower) or
                key_lower.endswith(" " + track_str)):
                return TRACK_FACTOR_WEIGHTS[key]
        return {}  # Return empty dict for tracks without specific adjustments
    
    def get_track_comprehensive_adjustment(track_name, box):
        """Get track-specific adjustment for ANY box based on historical patterns."""
        if pd.isna(track_name) or pd.isna(box):
            return 0.0
        track_str = str(track_name).strip().lower()
        box = int(box)
        
        # Three safe matching conditions (no startswith to avoid "Murray Bridge"
        # matching "Murray Bridge Straight"):
        #   1) exact match
        #   2) track ends with key  (e.g. "Ladbrokes Q Straight" → key "Q Straight")
        #   3) key ends with track  (e.g. track "Capalaba" → key "BetDeluxe Capalaba")
        # Sort longest-first as a safety net for remaining ambiguities.
        for key in sorted(TRACK_COMPREHENSIVE_ADJUSTMENTS, key=len, reverse=True):
            key_lower = key.lower()
            if (key_lower == track_str or
                track_str.endswith(" " + key_lower) or
                key_lower.endswith(" " + track_str)):
                adjustments = TRACK_COMPREHENSIVE_ADJUSTMENTS[key]
                return adjustments.get(box, 0.0)
        return 0.0
    
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
        
        # === TRACK-SPECIFIC BOX 1 + BOX 4 CHARACTERISTIC FEATURES (v5.2) ===
        # These features inform ALL dogs at a venue about how strongly Box 1 and
        # Box 4 are historically biased there — giving all 3 models (RF/GB/XGB)
        # a track-type signal that is independent of each dog's own box.
        #
        # Previously TRACK_BOX1_ADJUSTMENT and TRACK_BOX4_ADJUSTMENT contained
        # only {"DEFAULT": 0.0} after being consolidated into
        # TRACK_COMPREHENSIVE_ADJUSTMENTS, so every dog received 0.0 (zero-variance).
        # These two columns were wasting 2 of the 75 feature slots.
        #
        # Fix: derive the value from TRACK_COMPREHENSIVE_ADJUSTMENTS[track][1] and
        # TRACK_COMPREHENSIVE_ADJUSTMENTS[track][4] for ALL dogs in the race.
        # Example: at Launceston every dog (not just Box 1) gets
        #   TrackBox1Adjustment = 0.150 (strongest inside-bias in the dataset).
        # This lets the model learn "at an inside-speed track, outside boxes lose more".
        #
        # NOT added to BoxPositionBias — they are independent track-level features.
        # BoxPositionBias already captures each dog's own box via
        # TrackComprehensiveAdjustment (added below).
        if "Track" in df.columns:
            df["TrackBox1Adjustment"] = df["Track"].apply(
                lambda t: get_track_comprehensive_adjustment(t, 1) if pd.notna(t) else 0.0
            )
            df["TrackBox4Adjustment"] = df["Track"].apply(
                lambda t: get_track_comprehensive_adjustment(t, 4) if pd.notna(t) else 0.0
            )

            # === v4.0: COMPREHENSIVE TRACK-SPECIFIC BOX ADJUSTMENT ===
            # Applies to ALL boxes (1-8) based on track-specific winner patterns
            # This is the key fix for Darwin (9.1%) and Rockhampton (0%) accuracy
            df["TrackComprehensiveAdjustment"] = df.apply(
                lambda row: get_track_comprehensive_adjustment(row.get("Track", ""), row.get("Box"))
                            if pd.notna(row.get("Box")) 
                            else 0.0,
                axis=1
            )
            df["BoxPositionBias"] = df["BoxPositionBias"] + df["TrackComprehensiveAdjustment"]
            
            # === v4.1: TRACK-SPECIFIC FACTOR WEIGHT STORAGE ===
            # Store the dominant track pattern for reference and weight adjustment
            # Derived from TRACK_FACTOR_WEIGHTS to maintain consistency
            def get_track_pattern(track_name):
                if pd.isna(track_name):
                    return "NEUTRAL"
                track_str = str(track_name).strip().lower()
                
                # Helper function for more precise matching
                def matches_track(pattern, track):
                    pattern_lower = pattern.lower()
                    return (pattern_lower == track or 
                            track.startswith(pattern_lower + " ") or 
                            track.endswith(" " + pattern_lower) or
                            " " + pattern_lower + " " in " " + track + " " or
                            pattern_lower.startswith(track + " ") or
                            pattern_lower.endswith(" " + track))
                
                # Track categories derived from TRACK_FACTOR_WEIGHTS keys
                box1_tracks = ["meadows", "angle park", "ladbrokes q straight", "mount gambier", "sale", "sandown park"]
                box2_tracks = ["dubbo", "ladbrokes q2 parklands", "nowra", "darwin"]
                box8_tracks = ["casino", "horsham", "warrnambool", "healesville"]
                box4_tracks = ["bendigo", "shepparton"]
                box6_tracks = ["warragul"]
                box7_tracks = ["wentworth park", "mandurah"]
                problem_tracks = ["rockhampton", "betdeluxe rockhampton"]
                
                for t in problem_tracks:
                    if matches_track(t, track_str):
                        return "PROBLEM_BOX1"
                for t in box1_tracks:
                    if matches_track(t, track_str):
                        return "BOX1_SPEED"
                for t in box2_tracks:
                    if matches_track(t, track_str):
                        return "BOX2_FORM"
                for t in box8_tracks:
                    if matches_track(t, track_str):
                        return "BOX8_CLOSER"
                for t in box4_tracks:
                    if matches_track(t, track_str):
                        return "BOX4_EXPERIENCE"
                for t in box6_tracks:
                    if matches_track(t, track_str):
                        return "BOX6_FORM"
                for t in box7_tracks:
                    if matches_track(t, track_str):
                        return "BOX7_CLOSER"
                return "NEUTRAL"
            
            df["TrackPattern"] = df["Track"].apply(get_track_pattern)

            # === v5.1: DIRECT TRACK+BOX WIN RATE FEATURES ===
            # These provide the ML models with a STRONG, EXPLICIT box bias signal
            # that is 100% factual (derived from historical race results).
            #
            # TrackBoxWinRatePct: actual win% for this box at this track (0–50 scale).
            #   Example: Box 1 at Launceston → ~31.25 (cap-derived; actual 33%).
            #   Uses the inverse of the TRACK_COMPREHENSIVE_ADJUSTMENTS formula:
            #     win_rate_pct = adj / 0.008 + 12.5
            #   Tracks without data default to the global average for that box number.
            #
            # TrackBoxRank: rank of this box's win rate at this track (1=best, 8=worst).
            #   Easy for tree-based models to split: "Box rank ≤ 2 → higher probability".
            #
            # BoxWinAdvantage: 1 if this box is in the top-4 win-rate boxes for the
            #   track, 0 otherwise.  Binary feature — clear and unambiguous.
            def get_track_box_win_rate_pct(track_name, box):
                """Return estimated win% (0–50) for box at track via adjustment formula."""
                if pd.isna(track_name) or pd.isna(box):
                    # Unknown track or box: return global average (12.5 = 1/8)
                    return 12.5
                adj = get_track_comprehensive_adjustment(track_name, int(box))
                # Invert: win_rate_pct = adj/0.008 + 12.5
                win_rate_pct = adj / 0.008 + 12.5
                return float(max(0.0, min(50.0, win_rate_pct)))

            # Cache per-track win rate rankings so each track is computed once
            # rather than once per dog (avoids O(n × 8) repeated look-ups).
            _track_rank_cache = {}

            def get_track_box_rank(track_name, box):
                """Rank this box at this track (1=highest win rate, 8=lowest)."""
                if pd.isna(track_name) or pd.isna(box):
                    return 4  # neutral rank for unknown tracks
                cache_key = str(track_name)
                if cache_key not in _track_rank_cache:
                    rates = [get_track_box_win_rate_pct(track_name, b) for b in range(1, 9)]
                    # sorted_boxes[0] is the box number with the highest win rate
                    sorted_boxes = sorted(range(1, 9), key=lambda b: -rates[b - 1])
                    # Map box number → rank (1-indexed)
                    _track_rank_cache[cache_key] = {box_num: rank + 1
                                                    for rank, box_num in enumerate(sorted_boxes)}
                return _track_rank_cache[cache_key].get(int(box), 4)

            df["TrackBoxWinRatePct"] = df.apply(
                lambda row: get_track_box_win_rate_pct(row.get("Track"), row.get("Box"))
                if pd.notna(row.get("Box")) else 12.5,
                axis=1,
            )
            df["TrackBoxRank"] = df.apply(
                lambda row: get_track_box_rank(row.get("Track"), row.get("Box"))
                if pd.notna(row.get("Box")) else 4,
                axis=1,
            )
            # BoxWinAdvantage: 1 if this box is in the top half (≤4) for this track
            df["BoxWinAdvantage"] = (df["TrackBoxRank"] <= 4).astype(float)

            print(f"[OK] Applied track-specific Box 1, Box 4, and COMPREHENSIVE adjustments (v5.2)")
            print(f"  TrackBox1Adjustment and TrackBox4Adjustment now reflect actual track bias for ALL dogs")
            print(f"  Added TrackBoxWinRatePct, TrackBoxRank, BoxWinAdvantage for all 8 boxes")
            print(f"  Track patterns identified: {df['TrackPattern'].value_counts().to_dict()}")
        else:
            df["TrackBox1Adjustment"] = 0.0
            df["TrackBox4Adjustment"] = 0.0
            df["TrackComprehensiveAdjustment"] = 0.0
            df["TrackBoxWinRatePct"] = df["Box"].apply(
                lambda x: BOX_WIN_RATE.get(int(x), 0.125) * 100 if pd.notna(x) else 12.5
            )
            df["TrackBoxRank"] = 4  # neutral rank when no track info
            df["BoxWinAdvantage"] = 0.5  # neutral when no track info
        
        print(f"[OK] Applied comprehensive BoxPositionBias from 386-race analysis (v5.1)")
        print(f"  Win/Place/Top3 rates analyzed for all 8 boxes")
    else:
        df["BoxPositionBias"] = 0.0
        df["BoxPlaceRate"] = 0.0
        df["BoxTop3Rate"] = 0.0
        df["TrackBox1Adjustment"] = 0.0
        df["TrackBox4Adjustment"] = 0.0
        df["TrackComprehensiveAdjustment"] = 0.0
        df["TrackBoxWinRatePct"] = 12.5  # global average
        df["TrackBoxRank"] = 4           # neutral rank
        df["BoxWinAdvantage"] = 0.5      # neutral
    
    # === AGE FACTOR ===
    # Greyhounds typically peak at 2-3.5 years (24-42 months)
    # Parse age from SexAge field
    # Format variations:
    # - "2d" = 2 years old, dog (male)
    # - "3b" = 3 years old, bitch (female)
    # - "1b", "4d", "5b" etc.
    # - Some PDFs may use "2y", "24m" format
    if "SexAge" in df.columns:
        def parse_age_months(sex_age):
            if pd.isna(sex_age):
                return 30  # Default to prime age
            s = str(sex_age).lower().strip()
            try:
                # Format 1: "Nd" or "Nb" (e.g., "2d", "3b") - most common in our PDFs
                # N is age in years, d=dog, b=bitch
                if s[-1] in ['d', 'b'] and s[:-1].isdigit():
                    years = int(s[:-1])
                    return years * 12
                # Format 2: "Ny" (e.g., "2y", "3y") - years
                elif 'y' in s:
                    years = int(s.replace('y', '').replace('m', '').replace('f', '').replace('d', '').replace('b', ''))
                    return years * 12
                # Format 3: "NNm" (e.g., "24m", "36m") - months
                elif 'm' in s and not s.endswith('d') and not s.endswith('b'):
                    months_str = ''.join(filter(str.isdigit, s))
                    if months_str:
                        return int(months_str)
                # Format 4: Just a number (assume years)
                elif s.isdigit():
                    return int(s) * 12
            except Exception as e:
                pass
            return 30  # Default to prime age
        
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
        print(f"[OK] Calculated AgeFactor for {len(df)} dogs")
    else:
        df["AgeFactor"] = 0.85
        df["AgeMonths"] = 30
        print("[WARNING] WARNING: SexAge not found - setting AgeFactor to 0.85 (default)")
    
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
            # v3.9 UPDATE: Recalibrated based on Nov 28-30 actual results (335 races)
            # v4.3 Key changes for improved winning %:
            # - Box 1 penalty FURTHER REDUCED (still over-picking)
            # - Box 2 now gets STRONGER BONUS (proven undervalued 2 days in a row)
            # - Box 7 penalty MAINTAINED with slight increase for form-based tracks
            # - Box 8 penalty factor INCREASED (strong rail advantage at many tracks)
            BOX_PENALTY_FACTORS = {
                1: 1.05,   # v4.3: FURTHER REDUCED from 1.08 - still over-picking Box 1
                2: 1.08,   # v4.3: INCREASED from 1.03 - proven undervalued!
                3: 0.80,   # v4.3: Slight penalty - trap box
                4: 1.04,   # v4.3: INCREASED from 1.02 - middle boxes performing
                5: 0.90,   # v4.3: Slight increase from 0.88
                6: 0.95,   # v4.3: INCREASED from 0.92 - performing better
                7: 0.85,   # v4.3: INCREASED from 0.82 - closer advantage at some tracks
                8: 1.08,   # v4.3: INCREASED from 1.05 - rail advantage matters
            }
            return BOX_PENALTY_FACTORS.get(box, 1.0)
        
        df["BoxPenaltyFactor"] = df["Box"].apply(get_box_penalty_factor)
        print(f"[OK] Calculated BoxPenaltyFactor (v4.3: Box 1=1.05x, Box 2=1.08x, Box 8=1.08x)")
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
        # Convert DLW to numeric, handling "Mdn" (maiden) and other non-numeric values
        df["DLW"] = pd.to_numeric(df["DLW"], errors="coerce")
        df["WinStreakFactor"] = df["DLW"].apply(
            lambda x: 1.2 if pd.notna(x) and x <= 7 else    # Very recent win
                     1.1 if pd.notna(x) and x <= 14 else   # Recent win
                     1.0 if pd.notna(x) and x <= 28 else   # Within a month
                     0.9 if pd.notna(x) and x <= 60 else   # Going cold
                     0.8                                    # Long time since win or maiden
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
        print(f"[OK] Calculated GradeFactor for race grade adjustment (v3.6 speed-adjusted)")
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
        print(f"[OK] Calculated Last3FinishFactor (1.8x weight for winners)")
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
        print(f"[OK] Calculated DistanceChangeFactor for distance changes")
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
        print(f"[OK] Calculated PaceBoxFactor ({front_runner_count} front-runners detected)")
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
        print(f"[OK] Enhanced TrainerTier classification")
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
        print(f"[OK] Refined FreshnessFactor (optimal 6-10 days)")
    
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
        print(f"[OK] Refined AgeFactor (peak 26-36 months)")
    
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
        print(f"[OK] Calculated SurfacePreferenceFactor for track surface")
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
    # Higher EarlySpeedIndex = faster early = better.  Dogs with NaN (no sectional
    # timing in PDF) should get the LOWEST percentile (na_option="top" ensures
    # this with default ascending=True: rank 1 = lowest → pct = 1/n = lowest).
    if "EarlySpeedIndex" in df.columns:
        df["EarlySpeedPercentile"] = df.groupby(["Track", "RaceNumber"])["EarlySpeedIndex"].rank(pct=True, na_option="top")
    else:
        df["EarlySpeedPercentile"] = 0.5
    
    # === BEST TIME PERCENTILE ===
    # Rank dogs by best time within race
    # LOWER BestTimeSec = FASTER = should get HIGHER percentile rank.
    # ascending=False → lower time → highest rank number → pct = 1.0 (best) ✓
    # na_option="top"  → NaN → rank 1 (lowest rank number) → pct = 1/n (worst) ✓
    # NOTE: "bottom" was the OLD value — it put NaN at rank n → pct=1.0 (BEST),
    #       which was hidden when BestTimeSec was always non-NaN (previously
    #       fabricated as distance/15.5).  Now that NaN flows through correctly,
    #       "top" is required so untimed dogs get the lowest percentile.
    if "BestTimeSec" in df.columns:
        df["BestTimePercentile"] = df.groupby(["Track", "RaceNumber"])["BestTimeSec"].rank(pct=True, ascending=False, na_option="top")
        print(f"[OK] Calculated BestTimePercentile (lower time = higher rank)")
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
    # CRITICAL FIX: Convert race-level constants to dog-vs-field comparisons
    if "EarlySpeedIndex" in df.columns and "BestTimeSec" in df.columns:
        # Calculate race-level statistics for comparison
        df["FieldSpeedStd"] = df.groupby(["Track", "RaceNumber"])["EarlySpeedIndex"].transform("std")
        df["FieldTimeStd"] = df.groupby(["Track", "RaceNumber"])["BestTimeSec"].transform("std")
        
        # NEW: Convert to dog-vs-field comparison (VARIES by dog)
        df["TimeVsField"] = df.apply(
            lambda row: (row["BestTimeSec"] - df[(df["Track"] == row["Track"]) & 
                                                  (df["RaceNumber"] == row["RaceNumber"])]["BestTimeSec"].mean()) / 
                        (row.get("FieldTimeStd", 1.0) + 0.1) if row.get("FieldTimeStd", 0) > 0.1 else 0,
            axis=1
        )
        df["SpeedVsField"] = df.apply(
            lambda row: (row["EarlySpeedIndex"] - df[(df["Track"] == row["Track"]) & 
                                                       (df["RaceNumber"] == row["RaceNumber"])]["EarlySpeedIndex"].mean()) / 
                        (row.get("FieldSpeedStd", 1.0) + 0.1) if row.get("FieldSpeedStd", 0) > 0.1 else 0,
            axis=1
        )
        
        # Normalize: High std = more predictable (clear differences)
        df["FieldSimilarityIndex"] = df.apply(
            lambda row: 0.8 if (pd.notna(row.get("FieldSpeedStd")) and row.get("FieldSpeedStd", 0) > 3) or 
                               (pd.notna(row.get("FieldTimeStd")) and row.get("FieldTimeStd", 0) > 1.5)
                        else 1.0 if (pd.notna(row.get("FieldSpeedStd")) and row.get("FieldSpeedStd", 0) > 1.5)
                        else 1.1,  # High similarity = more unpredictable = reduce confidence
            axis=1
        )
        print(f"[OK] Calculated FieldSimilarityIndex + dog-vs-field comparisons for {len(df)} dogs")
    else:
        df["FieldSimilarityIndex"] = 1.0
        df["FieldSpeedStd"] = np.nan
        df["FieldTimeStd"] = np.nan
        df["TimeVsField"] = 0
        df["SpeedVsField"] = 0
    
    # === UPSET PROBABILITY ===
    # v3.9 UPDATE: Based on Nov 28-30 analysis (335 races)
    # Added Rockhampton (0% accuracy!) and Darwin (9.1% accuracy)
    TRACK_UPSET_PROBABILITY = {
        # Low upset tracks (more predictable) - Box 1 dominance
        "Angle Park": 0.80,      # 50% Box 1 wins (Nov 27) - Very predictable
        "Cannington": 0.82,      # 41.7% Box 1 (Nov 29) - Very predictable
        "Sandown": 0.85,         # 33.3% Box 1 (Nov 29)
        "Meadows": 0.85,         # 42% Box 1 wins (Nov 27)
        "Temora": 0.85,          # 41% Box 1 wins (Nov 28) 
        "Goulburn": 0.85,        # 41.7% Box 1 wins (Nov 28)
        "Capalaba": 0.87,        # v3.9: 30% success (Nov 30) - predictable
        "Gawler": 0.87,          # 33% Box 1 wins (Nov 28)
        "Bendigo": 0.88,         # 33% Box 1 wins (Nov 28)
        # Medium upset tracks
        "Broken Hill": 0.90,     # v3.9: 25% success (Nov 30)
        "Dubbo": 0.90,           # 27.3% Box 1 (Nov 29)
        "Wentworth Park": 0.92,
        "Lakeside": 0.92,        # 20% Box 1 (Nov 29)
        "Ladbrokes Q Straight": 0.92,
        "Parklands": 0.92,       # v3.9: 20% success (Nov 30)
        "Ladbrokes Gardens": 0.92,
        "Grafton": 0.95,         # v3.9: 16.7% success (Nov 30)
        "Warragul": 0.95,
        "Wagga": 0.95,
        "Sale": 0.95,            # v3.9: 16.7% success (Nov 30)
        "Mount Gambier": 0.95,   # v3.9: 18.2% success (Nov 30) - moved from high
        "Warrnambool": 0.95,
        # High upset tracks (more unpredictable)
        "Rockhampton": 1.15,     # v3.9: 0% accuracy (Nov 30) - VERY UNPREDICTABLE!
        "Darwin": 1.10,          # v3.9: 9.1% accuracy (Nov 30) - unpredictable
        "Taree": 1.08,           # 9.1% Box 1 (Nov 29) - Very unpredictable (0/11 wins)
        "Murray Bridge": 1.05,   # v3.9: Not processed but volatile
        "Gardens": 1.05,         # 8.3% Box 1 (Nov 29)
        "Ballarat": 1.05,        # 8.3% Box 1 (Nov 29)
        "Casino": 1.05,          # High entropy = more random
        "Hobart": 1.05,
        "Shepparton": 1.05,
        "Healesville": 1.02,     # Improved 25% on Nov 30
        "Richmond": 1.02,        # Improved 16.7% on Nov 30
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
    print(f"[OK] Applied TrackUpsetFactor (track-specific luck factor)")
    
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
        print(f"[OK] Calculated FieldSizeAdjustment based on field size")
    else:
        df["FieldSizeAdjustment"] = 0.0
    
    # ========================================================================
    # ENHANCEMENT #9: INCREASED WINNING STREAK BONUS (v4.4 UPDATE)
    # Analysis of missed winners showed 19% had 2+ consecutive wins (hot streak)
    # v4.4: MAXIMUM INCREASE bonus - hot form is THE CRITICAL predictor
    # ========================================================================
    if "DLW" in df.columns:
        df["WinStreakFactorV2"] = df["DLW"].apply(
            lambda x: 1.50 if pd.notna(x) and x <= 7 else     # v4.4: Hot streak - MAXIMUM BOOST (was 1.40)
                     1.32 if pd.notna(x) and x <= 14 else    # v4.4: Recent winner (was 1.28)
                     1.15 if pd.notna(x) and x <= 28 else    # v4.4: Within month (was 1.10)
                     0.90 if pd.notna(x) and x <= 60 else    # v4.4: Going cold (was 0.92)
                     0.75                                     # v4.4: Long time (was 0.80)
        )
        # Replace old WinStreakFactor with enhanced version
        df["WinStreakFactor"] = df["WinStreakFactorV2"]
        print(f"[OK] Enhanced WinStreakFactor v4.4 (1.50x for hot streaks, 1.32x for recent wins)")
    
    # ========================================================================
    # ENHANCEMENT #9B: RECENT PLACE STREAK (v4.4 NEW)
    # Dogs that have been placing consistently in last 3 races show good form
    # Even if not winning, consistent placing indicates competitiveness
    # ========================================================================
    if "Last3Finishes" in df.columns:
        def calc_recent_place_streak(finishes):
            if not isinstance(finishes, list) or len(finishes) == 0:
                return 1.0
            
            # Count top-3 finishes in last 3 races
            places = sum(1 for f in finishes[:3] if pd.notna(f) and f <= 3)
            
            if places >= 3:
                return 1.12  # v4.4: All 3 recent races in top 3 - strong form
            elif places == 2:
                return 1.06  # v4.4: 2 of 3 in top 3 - good form
            elif places == 1:
                return 1.03  # v4.4: 1 of 3 in top 3 - some form
            else:
                return 0.98  # v4.4: No top-3 finishes - losing form
        
        df["RecentPlaceStreak"] = df["Last3Finishes"].apply(calc_recent_place_streak)
        print(f"[OK] Added RecentPlaceStreak v4.4 (1.12x for 3/3 places, 1.06x for 2/3)")
    else:
        df["RecentPlaceStreak"] = 1.0
        print("[WARNING] WARNING: Last3Finishes not found - RecentPlaceStreak set to 1.0")
    
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
        print(f"[OK] Calculated CloserBonus ({closer_bonus_count} dogs with bonus)")
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
        print(f"[OK] Calculated TrainerMomentum (trainer hot streak factor)")
    else:
        df["TrainerMomentum"] = 1.0
    
    # ========================================================================
    # COMPREHENSIVE WEIGHT SYSTEM - 25+ Variables
    # v3.9 UPDATE: Based on 335 races (Nov 28-30, 2025)
    # ========================================================================
    
    def get_weights(distance):
        """
        Return optimal feature weights based on race distance.
        
        v3.9 - CRITICAL REBALANCE based on Nov 28-30 race results (335 races)
        
        Key changes from v3.8:
        - Box 1 weight REDUCED (was over-picking by 50%)
        - Box 2 weight INCREASED (was under-valued by 4%)
        - Box 7 penalty REDUCED (was too harsh)
        
        25+ variables grouped into categories:
        1. Box/Draw Position (30-38% of signal) - Rebalanced for Box 2
        2. Career/Experience (26-30% of signal) 
        3. Speed/Timing (18-22% of signal) - BestTimePercentile reliable
        4. Form/Momentum (10-15% of signal) - WinStreakFactor confirmed
        5. Conditioning (5-8% of signal) - Reduced (noisy factors)
        
        Key findings from Nov 28-30 analysis:
        - Box 1 wins 19.5% (vs 21% in matrix) - REDUCED weight
        - Box 2 wins 16.2% (vs 12% in matrix) - INCREASED weight
        - Box 7 wins 9.1% (vs 5.5% in matrix) - INCREASED weight
        - BoxPenaltyFactor (multiplicative) handles Box 7/3 over-picking
        
        Weights are optimized from 371+ race results analysis.
        """
        
        if distance < 400:  # SPRINT - Box position is CRITICAL
            return {
                # === BOX POSITION (40% total) - Increased for sprint ===
                "DrawFactor": 0.12,            # Draw position advantage
                "BoxPositionBias": 0.12,       # Win rate by box - INCREASED (Box 1=21%)
                "BoxPlaceRate": 0.06,          # 2nd place rate by box
                "BoxTop3Rate": 0.05,           # Top 3 rate by box  
                "RailPreference": 0.03,        # Inside/outside rail bonus
                "BoxBiasFactor": 0.02,         # Individual dog's box preference
                
                # === CAREER/EXPERIENCE (24% total) ===
                "PlaceRate": 0.05,             # Career place rate
                "ConsistencyIndex": 0.05,      # Win rate
                "WinPlaceRate": 0.04,          # Combined win+place rate
                "ExperienceTier": 0.04,        # Career starts tier
                "TrainerStrikeRate": 0.04,     # Trainer success
                "ClassRating": 0.02,           # Prize money class
                
                # === SPEED/TIMING (20% total) - BestTime fixed, weighted higher ===
                "EarlySpeedPercentile": 0.05,  # Early speed rank in race
                "BestTimePercentile": 0.06,    # Best time rank - INCREASED (now correct)
                "SectionalSec": 0.03,          # Raw sectional time
                "EarlySpeedIndex": 0.03,       # Early speed index
                "Speed_kmh": 0.02,             # Raw speed
                "SpeedClassification": 0.01,   # Sprinter vs stayer
                
                # === FORM/MOMENTUM (10% total) ===
                "DLWFactor": 0.03,             # Days since last win
                "WinStreakFactor": 0.03,       # Winning streak bonus (multiplicative)
                "FormMomentumNorm": 0.02,      # Form trend
                "MarginFactor": 0.02,          # Winning margin factor
                
                # === CONDITIONING (4% total) — Weight removed (always 0 kg in PDFs) ===
                "FreshnessFactor": 0.04,       # Days since last race (boosted from 0.02; Weight slot redistributed)
                "AgeFactor": 0.02,             # Age in optimal range
            }
            
        elif distance <= 500:  # MIDDLE - Most common distance (v4.3 UPDATE)
            return {
                # === BOX POSITION (32% total) - v4.3 REBALANCED ===
                "DrawFactor": 0.08,            # v4.3: REDUCED from 0.10
                "BoxPositionBias": 0.08,       # v4.3: REDUCED - less Box 1 bias
                "BoxPlaceRate": 0.05,          
                "BoxTop3Rate": 0.04,           
                "RailPreference": 0.04,        # v4.3: INCREASED for rail advantage
                "BoxBiasFactor": 0.03,         # v4.3: INCREASED
                
                # === CAREER/EXPERIENCE (30% total) - v4.4 MAXIMUM BOOST ===
                "PlaceRate": 0.07,             # v4.4: INCREASED - placing dogs win more
                "ConsistencyIndex": 0.08,      # v4.4: MAXIMUM BOOST - winners are VERY consistent
                "WinPlaceRate": 0.05,          
                "ExperienceTier": 0.04,        
                "TrainerStrikeRate": 0.04,     
                "ClassRating": 0.02,           # v4.4: REDUCED - less important
                
                # === SPEED/TIMING (18% total) - v4.4 FURTHER REDUCED ===
                "EarlySpeedPercentile": 0.05,  
                "BestTimePercentile": 0.04,    # v4.4: REDUCED further - form > speed
                "SectionalSec": 0.04,          
                "EarlySpeedIndex": 0.03,       
                "Speed_kmh": 0.01,             # v4.4: REDUCED
                "SpeedClassification": 0.01,   
                
                # === FORM/MOMENTUM (17% total) - v4.4 MAXIMUM INCREASE ===
                "DLWFactor": 0.05,             # v4.4: INCREASED - recent wins critical
                "WinStreakFactor": 0.06,       # v4.4: MAXIMUM - hot form is THE key
                "RecentPlaceStreak": 0.03,     # v4.4: NEW - consistent placing shows form
                "FormMomentumNorm": 0.03,      
                "MarginFactor": 0.02,          
                
                # === CONDITIONING (4% total) — Weight removed (always 0 kg in PDFs) ===
                "FreshnessFactor": 0.04,       # Days since last race (boosted; Weight slot redistributed)
                "AgeFactor": 0.02,             # Age in optimal range
            }
            
        else:  # LONG - Stamina & consistency dominate
            return {
                # === BOX POSITION (28% total) ===
                "DrawFactor": 0.08,            
                "BoxPositionBias": 0.08,       # Still important even at distance
                "BoxPlaceRate": 0.04,          
                "BoxTop3Rate": 0.04,           
                "RailPreference": 0.02,        
                "BoxBiasFactor": 0.02,         
                
                # === CAREER/EXPERIENCE (30% total) ===
                "PlaceRate": 0.06,             
                "ConsistencyIndex": 0.06,      
                "WinPlaceRate": 0.06,          
                "ExperienceTier": 0.05,        
                "TrainerStrikeRate": 0.04,     
                "ClassRating": 0.03,           
                
                # === SPEED/TIMING (22% total) ===
                "EarlySpeedPercentile": 0.04,  
                "BestTimePercentile": 0.06,    # INCREASED - now fixed and reliable
                "SectionalSec": 0.04,          
                "EarlySpeedIndex": 0.04,       
                "Speed_kmh": 0.03,             
                "SpeedClassification": 0.01,   
                
                # === FORM/MOMENTUM (14% total) ===
                "DLWFactor": 0.04,             
                "WinStreakFactor": 0.04,       # INCREASED - captures hot form
                "FormMomentumNorm": 0.04,      
                "MarginFactor": 0.02,          
                
                # === CONDITIONING (4% total) — Weight removed (always 0 kg in PDFs) ===
                "FreshnessFactor": 0.04,       # Days since last race (boosted; Weight slot redistributed)
                "AgeFactor": 0.02,             # Age in optimal range
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
        
        # 5. CONDITIONING SCORE (4% — Weight removed: always 0 kg in PDFs)
        conditioning_score = (
            row.get("FreshnessFactor", 1.0) * w.get("FreshnessFactor", 0) +
            row.get("AgeFactor", 0.85) * w.get("AgeFactor", 0)
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
        
        # Enhancement #13 (v4.4): Hot Trainer + Hot Form COMBO BONUS
        # When both trainer and dog are on hot streaks, amplify the effect
        recent_place_streak = row.get("RecentPlaceStreak", 1.0)
        dlw = row.get("DLW", 999)
        trainer_strike_rate = row.get("TrainerStrikeRate", 0)
        
        hot_combo_bonus = 1.0
        # Hot dog (DLW ≤ 7) + Hot trainer (25%+ strike rate) = MAXIMUM CONFIDENCE
        if pd.notna(dlw) and dlw <= 7 and pd.notna(trainer_strike_rate) and trainer_strike_rate >= 0.25:
            hot_combo_bonus = 1.15  # v4.4: +15% when both hot
        # Hot dog + good trainer (20%+ strike rate) = HIGH CONFIDENCE  
        elif pd.notna(dlw) and dlw <= 7 and pd.notna(trainer_strike_rate) and trainer_strike_rate >= 0.20:
            hot_combo_bonus = 1.08  # v4.4: +8% when dog hot, trainer good
        # Recent placer + hot trainer = GOOD CONFIDENCE
        elif recent_place_streak >= 1.06 and pd.notna(trainer_strike_rate) and trainer_strike_rate >= 0.25:
            hot_combo_bonus = 1.06  # v4.4: +6% when both showing form
        
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
            box_penalty *             # v3.7: Box penalty factor (Box 7=0.75x, Box 3=0.80x)
            recent_place_streak *     # v4.4: Recent placing consistency
            hot_combo_bonus           # v4.4: Hot trainer + hot form combo
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
