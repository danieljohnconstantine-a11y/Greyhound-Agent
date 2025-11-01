import pandas as pd
from typing import List
from .config import MERGE_KEYS
from .utils import safe_concat_frames

def merge_all(frames: List[pd.DataFrame], header_order: List[str]) -> pd.DataFrame:
    df = safe_concat_frames(frames, on_keys=MERGE_KEYS, how="outer")
    for col in header_order:
        if col not in df.columns:
            df[col] = None
    return df[header_order]
