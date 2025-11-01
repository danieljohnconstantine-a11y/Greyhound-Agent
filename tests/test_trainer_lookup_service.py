import os
import pandas as pd
from src.trainer_lookup_service import enrich_trainer_metadata




def test_trainer_cache(tmp_path):
f = tmp_path / "trainer_cache.csv"
pd.DataFrame([
{"Trainer": "John Doe", "TrainerWinRate": 0.22, "TrainerCity": "Sydney", "TrainerState": "NSW"}
]).to_csv(f, index=False)


cache = enrich_trainer_metadata(str(f))
assert "John Doe" in cache
assert abs(cache["John Doe"]["TrainerWinRate"] - 0.22) < 1e-6
assert cache["John Doe"]["TrainerCity"] == "Sydney"
assert cache["John Doe"]["TrainerState"] == "NSW"
