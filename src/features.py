import numpy as np
import pandas as pd
from .utils import kmh




def compute_features(df: pd.DataFrame) -> pd.DataFrame:
df = df.copy()


# Compute SpeedIndex safely
if "BestTime" in df.columns and "Distance" in df.columns:
df["SpeedIndex"] = [kmh(d, t) if pd.notna(d) and pd.notna(t) else np.nan for d, t in zip(df["Distance"], df["BestTime"])]


# EarlySpeed and ClosingSpeed examples (replace with your real formulas)
if {"Sectional1", "Distance"}.issubset(df.columns):
df["EarlySpeed"] = [d / s if (pd.notna(d) and pd.notna(s) and s > 0) else np.nan for d, s in zip(df["Distance"], df["Sectional1"])]


if {"BestTime", "Sectional1"}.issubset(df.columns):
df["ClosingSpeed"] = [ (d / max((bt - s1), 1e-6)) if (pd.notna(d) and pd.notna(bt) and pd.notna(s1) and (bt - s1) > 0) else np.nan
for d, bt, s1 in zip(df["Distance"], df["BestTime"], df["Sectional1"]) ]


# ConsistencyIndex (simple example using Starts/Wins)
if {"Starts", "Wins"}.issubset(df.columns):
df["ConsistencyIndex"] = [ (w / s) if (pd.notna(w) and pd.notna(s) and s > 0) else np.nan for w, s in zip(df["Wins"], df["Starts"]) ]


# FinalScore as a weighted sum of normalized signals where present
parts = []
for col, weight in [
("SpeedIndex", 0.4), ("ConsistencyIndex", 0.2), ("EarlySpeed", 0.2), ("ClosingSpeed", 0.2)
]:
if col in df.columns:
x = df[col].astype(float)
x = (x - x.min()) / (x.max() - x.min() + 1e-9)
parts.append(x * weight)
if parts:
df["FinalScore"] = sum(parts)
else:
df["FinalScore"] = np.nan


return df
