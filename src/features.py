import numpy as np
import pandas as pd
from .utils import kmh


def _minmax01(series: pd.Series) -> pd.Series:
    x = series.astype(float)
    return (x - x.min()) / (x.max() - x.min() + 1e-9)


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Compute SplitAvg from any combination of Sectional columns
    if all(c in df.columns for c in ["Sectional1", "Sectional2", "Sectional3"]):
        df["SplitAvg"] = [
            np.nanmean([s for s in [a, b, c] if pd.notna(s)])
            if any(pd.notna(v) for v in [a, b, c]) else np.nan
            for a, b, c in zip(df["Sectional1"], df["Sectional2"], df["Sectional3"])
        ]

    # SpeedIndex (km/h)
    if "Distance" in df.columns and "BestTime" in df.columns:
        df["SpeedIndex"] = [
            kmh(dist, time) if pd.notna(dist) and pd.notna(time) else np.nan
            for dist, time in zip(df["Distance"], df["BestTime"])
        ]

    # EarlySpeed (based on Sectional1)
    if "Distance" in df.columns and "Sectional1" in df.columns:
        df["EarlySpeed"] = [
            kmh(dist, sec1) if pd.notna(dist) and pd.notna(sec1) else np.nan
            for dist, sec1 in zip(df["Distance"], df["Sectional1"])
        ]

    # ClosingSpeed (remaining distance after Sectional1)
    if all(c in df.columns for c in ["BestTime", "Sectional1", "Distance"]):
        df["ClosingSpeed"] = [
            kmh(dist, bt - s1) if pd.notna(dist) and pd.notna(bt) and pd.notna(s1) and (bt > s1)
            else np.nan
            for dist, bt, s1 in zip(df["Distance"], df["BestTime"], df["Sectional1"])
        ]

    # ConsistencyIndex = Wins / Starts
    if "Wins" in df.columns and "Starts" in df.columns:
        df["ConsistencyIndex"] = [
            (w / s) if (pd.notna(w) and pd.notna(s) and s > 0) else np.nan
            for w, s in zip(df["Wins"], df["Starts"])
        ]

    # Derived final score
    parts = []
    for col, weight in [("SpeedIndex", 0.4), ("ConsistencyIndex", 0.2),
                        ("EarlySpeed", 0.2), ("ClosingSpeed", 0.2)]:
        if col in df.columns:
            parts.append(_minmax01(df[col]) * weight)

    df["Score"] = sum(parts) if parts else np.nan
    return df
