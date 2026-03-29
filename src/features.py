import pandas as pd
import numpy as np

def compute_features(df):
    df = df.copy()

    # Ensure numeric types
    df["DLR"] = pd.to_numeric(df["DLR"], errors="coerce")
    df["CareerStarts"] = pd.to_numeric(df["CareerStarts"], errors="coerce")
    df["Distance"] = pd.to_numeric(df["Distance"], errors="coerce")

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

    # Consistency Index — vectorized (avoids slow axis=1 apply)
    df["ConsistencyIndex"] = np.where(
        df["CareerStarts"] > 0,
        df["CareerWins"] / df["CareerStarts"],
        0.0
    )

    # Recent Form Boost — vectorized (avoids slow axis=1 apply)
    df["RecentFormBoost"] = np.select(
        [
            (df["DLR"] <= 5) & (df["CareerWins"] > 0),
            df["DLR"] <= 10,
        ],
        [1.0, 0.5],
        default=0.0
    )

    # Distance Suitability — vectorized (avoids slow element-wise apply)
    df["DistanceSuit"] = np.where(df["Distance"].isin([515, 595]), 1.0, 0.7)

    # Fallbacks
    df["TrainerStrikeRate"] = df.get("TrainerStrikeRate", pd.Series([0.15] * len(df)))
    df["RestFactor"] = df.get("RestFactor", pd.Series([0.8] * len(df)))

    # Overexposure Penalty — vectorized (avoids slow element-wise apply)
    df["OverexposedPenalty"] = np.where(df["CareerStarts"] > 80, -0.1, 0.0)

    # Race-type adaptive weights — computed once per distance band, not per row.
    # Three bands: Sprint (<400m), Middle (400–500m), Long (>500m).
    # The Long band is handled by the `default` parameter in each np.select() call below.
    is_sprint = df["Distance"] < 400
    is_middle = (df["Distance"] >= 400) & (df["Distance"] <= 500)

    w_early  = np.select([is_sprint, is_middle], [0.30, 0.25], default=0.20)
    w_speed  = np.select([is_sprint, is_middle], [0.20, 0.20], default=0.15)
    w_cons   = np.select([is_sprint, is_middle], [0.10, 0.15], default=0.20)
    w_fin    = np.select([is_sprint, is_middle], [0.05, 0.05], default=0.10)
    w_prize  = 0.10  # identical across all bands
    w_recent = 0.10  # identical across all bands
    w_box    = np.select([is_sprint, is_middle], [0.10, 0.05], default=0.05)
    w_trn    = 0.05  # identical across all bands
    w_dist   = 0.05  # identical across all bands
    w_track  = 0.05  # identical across all bands

    # FinalScore — fully vectorized (replaces the previous iterrows() loop)
    df["FinalScore"] = (
        df["EarlySpeedIndex"]  * w_early  +
        df["Speed_kmh"]        * w_speed  +
        df["ConsistencyIndex"] * w_cons   +
        df["FinishConsistency"] * w_fin   +
        (df["PrizeMoney"] / 1000) * w_prize +
        df["RecentFormBoost"]  * w_recent +
        df["BoxBiasFactor"]    * w_box    +
        df["TrainerStrikeRate"] * w_trn   +
        df["DistanceSuit"]     * w_dist   +
        df["TrackConditionAdj"] * w_track +
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
