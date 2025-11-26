import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def _find_distance_column(df):
    """
    Find the distance column in the DataFrame, checking for common variations.
    Returns the column name if found, None otherwise.
    
    Handles variations like: 'Distance', 'distance', 'RaceDistance', ' Distance ', etc.
    """
    # Normalize column names for comparison (strip whitespace, lowercase)
    normalized_cols = {col.strip().lower(): col for col in df.columns}
    
    # Try exact matches first (case-insensitive, whitespace-stripped)
    distance_variations = ['distance', 'racedistance', 'race_distance', 'dist']
    
    for variation in distance_variations:
        if variation in normalized_cols:
            actual_col = normalized_cols[variation]
            logger.info(f"✅ Found distance column: '{actual_col}'")
            return actual_col
    
    # If not found, log all available columns for manual review
    logger.error("❌ Could not find 'Distance' column in DataFrame!")
    logger.error(f"   Available columns: {df.columns.tolist()}")
    return None

def compute_features(df):
    """
    Compute features for greyhound race prediction.
    
    Robustly handles missing or alternative distance columns with helpful error messages.
    Normalizes numeric columns to handle various data formats.
    """
    df = df.copy()
    
    logger.info(f"🔧 Starting feature computation for {len(df)} dogs")
    
    # Find and validate Distance column
    distance_col = _find_distance_column(df)
    if distance_col is None:
        raise ValueError(
            "CRITICAL ERROR: 'Distance' column not found in DataFrame. "
            "Cannot compute features without distance information. "
            f"Available columns: {df.columns.tolist()}. "
            "Please check the PDF parsing pipeline to ensure race distance is being extracted."
        )
    
    # If the column name is not exactly 'Distance', rename it for consistency
    if distance_col != 'Distance':
        logger.info(f"🔄 Renaming '{distance_col}' to 'Distance' for consistency")
        df = df.rename(columns={distance_col: 'Distance'})

    # Ensure numeric types with robust error handling
    numeric_columns = {
        'DLR': 'Days Last Run',
        'CareerStarts': 'Career Starts',
        'Distance': 'Distance'
    }
    
    for col, description in numeric_columns.items():
        if col in df.columns:
            original_type = df[col].dtype
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Log conversion issues
            null_count = df[col].isna().sum()
            if null_count > 0:
                logger.warning(f"⚠️ {null_count} invalid values in '{col}' ({description}) converted to NaN")
            logger.debug(f"   Converted {col} from {original_type} to numeric")
        else:
            logger.warning(f"⚠️ Expected column '{col}' ({description}) not found in DataFrame")
    
    # Validate Distance values are reasonable (should be between 100m and 1000m for greyhound racing)
    if 'Distance' in df.columns:
        valid_distances = df['Distance'].notna()
        if valid_distances.sum() == 0:
            logger.error("❌ All Distance values are NaN after conversion!")
        else:
            distance_range = df.loc[valid_distances, 'Distance']
            logger.info(f"📏 Distance range: {distance_range.min():.0f}m to {distance_range.max():.0f}m")
            
            # Warn about unusual distances
            unusual_distances = (distance_range < 100) | (distance_range > 1000)
            if unusual_distances.any():
                logger.warning(f"⚠️ {unusual_distances.sum()} dogs have unusual distances (outside 100-1000m range)")
    
    # Placeholder values — replace with parsed metrics later
    # TODO: Extract these from PDF when available
    df["BestTimeSec"] = 22.5
    df["SectionalSec"] = 8.5
    df["Last3TimesSec"] = [[22.65, 22.52, 22.77]] * len(df)
    df["Margins"] = [[5.0, 6.3, 10.3]] * len(df)
    df["BoxBiasFactor"] = 0.1
    df["TrackConditionAdj"] = 1.0

    # Derived metrics - all dependent on Distance being numeric and non-null
    # These calculations are now robust to Distance column variations and format issues
    df["Speed_kmh"] = (df["Distance"] / df["BestTimeSec"]) * 3.6
    df["EarlySpeedIndex"] = df["Distance"] / df["SectionalSec"]
    df["FinishConsistency"] = df["Last3TimesSec"].apply(lambda x: np.std(x))
    df["MarginAvg"] = df["Margins"].apply(lambda x: np.mean(x))
    df["FormMomentum"] = df["Margins"].apply(lambda x: np.mean(np.diff(x)) if len(x) >= 2 else 0)

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

    # Distance Suitability - handles numeric Distance column robustly
    # Assumes Distance is in meters (e.g., 515m, 595m are common greyhound racing distances)
    df["DistanceSuit"] = df["Distance"].apply(lambda x: 1.0 if pd.notna(x) and x in [515, 595] else 0.7)

    # Fallbacks
    df["TrainerStrikeRate"] = df.get("TrainerStrikeRate", pd.Series([0.15] * len(df)))
    df["RestFactor"] = df.get("RestFactor", pd.Series([0.8] * len(df)))

    # Overexposure Penalty
    df["OverexposedPenalty"] = df["CareerStarts"].apply(lambda x: -0.1 if x > 80 else 0)

    # Race-type adaptive weighting - handles NaN distances gracefully
    def get_weights(distance):
        # Handle NaN or invalid distances by defaulting to middle-distance weights
        if pd.isna(distance) or distance <= 0:
            logger.warning(f"⚠️ Invalid distance value ({distance}), using middle-distance weights")
            distance = 450  # Default to middle distance
        
        if distance < 400:  # Sprint
            return {
                "EarlySpeedIndex": 0.30,
                "Speed_kmh": 0.20,
                "ConsistencyIndex": 0.10,
                "FinishConsistency": 0.05,
                "PrizeMoney": 0.10,
                "RecentFormBoost": 0.10,
                "BoxBiasFactor": 0.10,
                "TrainerStrikeRate": 0.05,
                "DistanceSuit": 0.05,
                "TrackConditionAdj": 0.05
            }
        elif distance <= 500:  # Middle
            return {
                "EarlySpeedIndex": 0.25,
                "Speed_kmh": 0.20,
                "ConsistencyIndex": 0.15,
                "FinishConsistency": 0.05,
                "PrizeMoney": 0.10,
                "RecentFormBoost": 0.10,
                "BoxBiasFactor": 0.05,
                "TrainerStrikeRate": 0.05,
                "DistanceSuit": 0.05,
                "TrackConditionAdj": 0.05
            }
        else:  # Long
            return {
                "EarlySpeedIndex": 0.20,
                "Speed_kmh": 0.15,
                "ConsistencyIndex": 0.20,
                "FinishConsistency": 0.10,
                "PrizeMoney": 0.10,
                "RecentFormBoost": 0.10,
                "BoxBiasFactor": 0.05,
                "TrainerStrikeRate": 0.05,
                "DistanceSuit": 0.05,
                "TrackConditionAdj": 0.05
            }

    # FinalScore calculation
    final_scores = []
    for _, row in df.iterrows():
        w = get_weights(row["Distance"])
        score = (
            row["EarlySpeedIndex"] * w["EarlySpeedIndex"] +
            row["Speed_kmh"] * w["Speed_kmh"] +
            row["ConsistencyIndex"] * w["ConsistencyIndex"] +
            row["FinishConsistency"] * w["FinishConsistency"] +
            (row["PrizeMoney"] / 1000) * w["PrizeMoney"] +
            row["RecentFormBoost"] * w["RecentFormBoost"] +
            row["BoxBiasFactor"] * w["BoxBiasFactor"] +
            row["TrainerStrikeRate"] * w["TrainerStrikeRate"] +
            row["DistanceSuit"] * w["DistanceSuit"] +
            row["TrackConditionAdj"] * w["TrackConditionAdj"] +
            row["OverexposedPenalty"]
        )
        final_scores.append(score)

    df["FinalScore"] = final_scores
    
    logger.info(f"✅ Feature computation completed successfully for {len(df)} dogs")
    logger.info(f"📊 Final score range: {df['FinalScore'].min():.2f} to {df['FinalScore'].max():.2f}")
    
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
