import pandas as pd
import numpy as np

def compute_features(df):
    df = df.copy()

    # Ensure numeric types
    df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")
    df["CareerStarts"] = pd.to_numeric(df["CareerStarts"], errors="coerce")
    
    # Handle Distance - use default if not present or invalid
    if "Distance" not in df.columns:
        df["Distance"] = 500  # Default distance
    else:
        df["Distance"] = pd.to_numeric(df["Distance"], errors="coerce").fillna(500)

    # Use parsed metrics if available, otherwise use placeholder defaults
    # BestTimeSec - use parsed value or estimate from distance
    if "BestTimeSec" not in df.columns or df["BestTimeSec"].isna().all():
        # Estimate based on typical greyhound speed (~60 km/h = 16.67 m/s)
        df["BestTimeSec"] = df["Distance"] / (60 / 3.6)  # distance (m) / speed (m/s) = time (s)
    else:
        # Fill missing values with estimate
        df["BestTimeSec"] = df["BestTimeSec"].fillna(df["Distance"] / (60 / 3.6))
    
    # SectionalSec - use parsed value or estimate
    if "SectionalSec" not in df.columns or df["SectionalSec"].isna().all():
        # Estimate: sectional is typically ~40% of total race time
        df["SectionalSec"] = df["BestTimeSec"] * 0.4
    else:
        df["SectionalSec"] = df["SectionalSec"].fillna(df["BestTimeSec"] * 0.4)
    
    # Last3TimesSec - use parsed value or create default
    def create_default_last3(best_time):
        """Create default Last3TimesSec with small variations"""
        return [best_time * 1.01, best_time * 0.99, best_time * 1.02]
    
    if "Last3TimesSec" not in df.columns or df["Last3TimesSec"].isna().all():
        # Create default based on BestTimeSec with small variations
        df["Last3TimesSec"] = df["BestTimeSec"].apply(create_default_last3)
    else:
        # Fill missing with default
        df["Last3TimesSec"] = df.apply(
            lambda row: row["Last3TimesSec"] if isinstance(row.get("Last3TimesSec"), list) 
            else create_default_last3(row["BestTimeSec"]),
            axis=1
        )
    
    # Margins - use parsed value or create default
    DEFAULT_MARGINS = [5.0, 6.3, 10.3]
    
    if "Margins" not in df.columns or df["Margins"].isna().all():
        # Create default margins based on typical race gaps
        df["Margins"] = [DEFAULT_MARGINS] * len(df)
    else:
        # Fill missing with default
        df["Margins"] = df["Margins"].apply(
            lambda x: x if isinstance(x, list) else DEFAULT_MARGINS
        )
    
    # BoxBiasFactor - use distance-specific bias if available, otherwise default
    if "BoxBiasFactor" not in df.columns:
        df["BoxBiasFactor"] = 0.1
    
    # TrackConditionAdj - default to neutral
    if "TrackConditionAdj" not in df.columns:
        df["TrackConditionAdj"] = 1.0

    # Derived metrics
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

    # Distance Suitability
    df["DistanceSuit"] = df["Distance"].apply(lambda x: 1.0 if x in [515, 595] else 0.7)

    # Fallbacks
    df["TrainerStrikeRate"] = df.get("TrainerStrikeRate", pd.Series([0.15] * len(df)))
    df["RestFactor"] = df.get("RestFactor", pd.Series([0.8] * len(df)))

    # Overexposure Penalty
    df["OverexposedPenalty"] = df["CareerStarts"].apply(lambda x: -0.1 if x > 80 else 0)

    # Race-type adaptive weighting
    def get_weights(distance):
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
