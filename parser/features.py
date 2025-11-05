import pandas as pd
import numpy as np

def compute_features(df):
    df = df.copy()

    # Ensure DLR is numeric
    df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")

    # Placeholder values — replace with parsed metrics later
    df["BestTimeSec"] = 22.5
    df["SectionalSec"] = 8.5
    df["Last3TimesSec"] = [[22.65, 22.52, 22.77]] * len(df)
    df["Margins"] = [[5.0, 6.3, 10.3]] * len(df)
    df["BoxBiasFactor"] = 0.1
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

    # Trainer Strike Rate (fallback if missing)
    df["TrainerStrikeRate"] = df.get("TrainerStrikeRate", pd.Series([0.15] * len(df)))

    # Rest Factor (fallback if missing)
    df["RestFactor"] = df.get("RestFactor", pd.Series([0.8] * len(df)))

    # Overexposure Penalty
    df["OverexposedPenalty"] = df["CareerStarts"].apply(lambda x: -0.1 if x > 80 else 0)

    # FinalScore with dynamic weighting
    df["FinalScore"] = (
        df["EarlySpeedIndex"] * 0.25 +
        df["Speed_kmh"] * 0.20 +
        df["FormMomentum"] * 0.10 +
        df["ConsistencyIndex"] * 0.15 +
        df["PrizeMoney"] / 1000 * 0.10 +
        df["RecentFormBoost"] * 0.10 +
        df["BoxBiasFactor"] * 0.05 +
        df["TrainerStrikeRate"] * 0.05 +
        df["DistanceSuit"] * 0.05 +
        df["TrackConditionAdj"] * 0.05 +
        df["OverexposedPenalty"]
    )

    return df

def generate_trifecta_table(df):
    trifecta_rows = []

    for (track, race), group in df.groupby(["Track", "RaceNumber"]):
        top3 = group.sort_values("FinalScore", ascending=False).head(3)
        if len(top3) < 3:
            continue

        scores = top3["FinalScore"].values
        separation_score = (scores[0] - scores[1]) + (scores[1] - scores[2])

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
            "BetFlag": "BET" if scores[0] > 40 and separation_score > 2.5 else "NO BET"
        })

    trifecta_df = pd.DataFrame(trifecta_rows)
    trifecta_df = trifecta_df.sort_values("SeparationScore", ascending=False)
    return trifecta_df
