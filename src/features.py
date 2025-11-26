import pandas as pd
import numpy as np

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

    # Box Position Bias - Optimized from 320 race results analysis (Sep-Nov 2025)
    # Based on actual win rates: Box 1 (18.1%), Box 4 (15.3%), Box 2 (14.4%), Box 8 (12.8%)
    # Box 3 weakest at 8.4% - inner boxes perform significantly better
    BOX_POSITION_BIAS = {
        1: 0.067,   # 18.1% wins - 1.45x average - STRONGEST
        2: 0.022,   # 14.4% wins - 1.15x average
        3: -0.049,  # 8.4% wins - 0.68x average - WEAKEST
        4: 0.034,   # 15.3% wins - 1.23x average - SECOND STRONGEST
        5: -0.023,  # 10.6% wins - 0.85x average
        6: -0.026,  # 10.3% wins - 0.82x average
        7: -0.037,  # 9.4% wins - 0.75x average
        8: 0.004,   # 12.8% wins - 1.02x average
    }
    
    # Apply box position bias based on actual race data
    if "Box" in df.columns:
        df["BoxPositionBias"] = df["Box"].apply(
            lambda x: BOX_POSITION_BIAS.get(int(x), 0.0) if pd.notna(x) else 0.0
        )
        print(f"✓ Applied optimized BoxPositionBias from 320-race analysis")
    else:
        df["BoxPositionBias"] = 0.0
    
    # Race-type adaptive weighting - Optimized from 320 race results analysis
    # Expanded to include ALL available variables for comprehensive scoring
    # Weights adjusted to sum to 1.0 (100%) for each distance category
    def get_weights(distance):
        if distance < 400:  # Sprint - Box position and early speed matter most
            return {
                "EarlySpeedIndex": 0.20,      # Critical for sprints
                "Speed_kmh": 0.14,             # Raw speed important
                "ConsistencyIndex": 0.08,      # Win rate
                "FinishConsistency": 0.03,     # Time consistency
                "PrizeMoney": 0.05,            # Class indicator
                "RecentFormBoost": 0.08,       # Recent racing activity
                "BoxBiasFactor": 0.06,         # Dog's box preference
                "BoxPositionBias": 0.06,       # Position win rate from 320 races
                "TrainerStrikeRate": 0.04,     # Trainer success
                "DistanceSuit": 0.03,          # Distance preference
                "TrackConditionAdj": 0.02,     # Track conditions
                # NEW VARIABLES (from 320-race analysis)
                "PlaceRate": 0.04,             # Consistency in placing
                "DLWFactor": 0.05,             # Days since last win
                "WeightFactor": 0.03,          # Optimal weight range
                "DrawFactor": 0.03,            # Draw position advantage
                "FormMomentumNorm": 0.03,      # Form trending direction
                "MarginFactor": 0.02,          # Average winning margins
                "RTCFactor": 0.01              # Rating
            }
        elif distance <= 500:  # Middle - More balanced approach
            return {
                "EarlySpeedIndex": 0.16,       # Still important
                "Speed_kmh": 0.14,             # Sustained speed
                "ConsistencyIndex": 0.12,      # Win rate more important
                "FinishConsistency": 0.04,     # Time consistency
                "PrizeMoney": 0.06,            # Class indicator
                "RecentFormBoost": 0.08,       # Recent form
                "BoxBiasFactor": 0.05,         # Box preference
                "BoxPositionBias": 0.05,       # Position win rate
                "TrainerStrikeRate": 0.04,     # Trainer success
                "DistanceSuit": 0.03,          # Distance preference
                "TrackConditionAdj": 0.02,     # Track conditions
                # NEW VARIABLES
                "PlaceRate": 0.05,             # Placing consistency
                "DLWFactor": 0.04,             # Recent winning
                "WeightFactor": 0.03,          # Weight factor
                "DrawFactor": 0.03,            # Draw advantage
                "FormMomentumNorm": 0.03,      # Form direction
                "MarginFactor": 0.02,          # Margins
                "RTCFactor": 0.01              # Rating
            }
        else:  # Long - Stamina, consistency and form matter more
            return {
                "EarlySpeedIndex": 0.12,       # Less critical for long races
                "Speed_kmh": 0.10,             # Sustainable pace
                "ConsistencyIndex": 0.14,      # Very important for stamina
                "FinishConsistency": 0.06,     # Time consistency important
                "PrizeMoney": 0.06,            # Class indicator
                "RecentFormBoost": 0.08,       # Recent form
                "BoxBiasFactor": 0.04,         # Less impact at distance
                "BoxPositionBias": 0.04,       # Less impact at distance
                "TrainerStrikeRate": 0.04,     # Trainer success
                "DistanceSuit": 0.04,          # Distance preference more important
                "TrackConditionAdj": 0.03,     # Track conditions
                # NEW VARIABLES - Higher weights for form indicators
                "PlaceRate": 0.06,             # Placing consistency key for stamina
                "DLWFactor": 0.05,             # Recent winning important
                "WeightFactor": 0.04,          # Weight affects stamina
                "DrawFactor": 0.03,            # Draw still matters
                "FormMomentumNorm": 0.04,      # Form direction important
                "MarginFactor": 0.02,          # Margins
                "RTCFactor": 0.01              # Rating
            }

    # FinalScore calculation - handle NaN values by treating them as 0
    # Includes ALL 18 weighted variables from 320-race analysis
    final_scores = []
    for _, row in df.iterrows():
        w = get_weights(row["Distance"])
        score = (
            # Original variables
            (row["EarlySpeedIndex"] if pd.notna(row["EarlySpeedIndex"]) else 0) * w["EarlySpeedIndex"] +
            (row["Speed_kmh"] if pd.notna(row["Speed_kmh"]) else 0) * w["Speed_kmh"] +
            row["ConsistencyIndex"] * w["ConsistencyIndex"] +
            row["FinishConsistency"] * w["FinishConsistency"] +
            (row["PrizeMoney"] / 1000) * w["PrizeMoney"] +
            row["RecentFormBoost"] * w["RecentFormBoost"] +
            row["BoxBiasFactor"] * w["BoxBiasFactor"] +
            row["BoxPositionBias"] * w["BoxPositionBias"] +
            row["TrainerStrikeRate"] * w["TrainerStrikeRate"] +
            row["DistanceSuit"] * w["DistanceSuit"] +
            row["TrackConditionAdj"] * w["TrackConditionAdj"] +
            # NEW variables from 320-race analysis
            row["PlaceRate"] * w["PlaceRate"] +
            row["DLWFactor"] * w["DLWFactor"] +
            row["WeightFactor"] * w["WeightFactor"] +
            row["DrawFactor"] * w["DrawFactor"] +
            row["FormMomentumNorm"] * w["FormMomentumNorm"] +
            row["MarginFactor"] * w["MarginFactor"] +
            row["RTCFactor"] * w["RTCFactor"] +
            row["OverexposedPenalty"]
        )
        final_scores.append(score)

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
