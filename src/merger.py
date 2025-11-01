import pandas as pd
from typing import List
from .utils import safe_concat_frames


KEYS = ["Box", "DogName"] # Track/RaceNumber may be missing in some partials; added where present




def merge_all(frames: List[pd.DataFrame], header_order: List[str]) -> pd.DataFrame:
# Prefer merging on richer keys when present
# Start by outer-joining on Box+DogName, then re-attach Track/RaceNumber where available
df = safe_concat_frames(frames, on_keys=KEYS, how="outer")


# Ensure all header_order columns exist
for col in header_order:
if col not in df.columns:
df[col] = None


# Reorder
df = df[header_order]
return df
