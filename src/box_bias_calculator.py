import os
import glob
import pandas as pd
from typing import Dict


# Reads historical outputs (CSV in outputs/archived) and computes box win/place deltas per track


def load_box_bias_lookup(archived_dir: str) -> Dict[str, Dict[int, float]]:
lookup: Dict[str, Dict[int, float]] = {}
if not archived_dir or not os.path.isdir(archived_dir):
return lookup


paths = glob.glob(os.path.join(archived_dir, "*.csv"))
if not paths:
return lookup


frames = []
for p in paths:
try:
frames.append(pd.read_csv(p))
except Exception:
pass
if not frames:
return lookup


df = pd.concat(frames, ignore_index=True)
# Expect columns: Track, RaceNumber, Box, DogName, FinalScore, Result(optional)
if "Track" not in df.columns or "Box" not in df.columns:
return lookup


# Approx: win if Result == 1 or RaceComment says "1st"
if "Result" in df.columns:
df["is_win"] = (df["Result"] == 1).astype(int)
elif "RaceComment" in df.columns:
df["is_win"] = df["RaceComment"].fillna("").str.contains(r"\b1st\b", case=False, regex=True).astype(int)
else:
df["is_win"] = 0


grouped = df.groupby([df["Track"].str.upper(), "Box"])['is_win'].mean().reset_index()
# Center per track so neutral = 0.0
for track, g in grouped.groupby("Track"):
mean = g['is_win'].mean()
lookup[track] = {int(row['Box']): float(row['is_win'] - mean) for _, row in g.iterrows()}
return lookup
