import os
import pandas as pd
from typing import Dict


# Looks for optional cache file: outputs/trainer_cache.csv with columns:
# Trainer,TrainerWinRate,TrainerCity,TrainerState


def enrich_trainer_metadata(cache_path: str = None) -> Dict[str, dict]:
if cache_path is None:
cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "trainer_cache.csv")
if not os.path.exists(cache_path):
return {}
try:
df = pd.read_csv(cache_path)
except Exception:
return {}
required = {"Trainer", "TrainerWinRate", "TrainerCity", "TrainerState"}
if not required.issubset(df.columns):
return {}
df["TrainerWinRate"] = pd.to_numeric(df["TrainerWinRate"], errors="coerce")
return {row.Trainer: {
"TrainerWinRate": row.TrainerWinRate,
"TrainerCity": row.TrainerCity,
"TrainerState": row.TrainerState,
} for _, row in df.iterrows()}
