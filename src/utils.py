import re
import pandas as pd
from typing import Optional, List

SPACE_RE = re.compile(r"\s+")
CURRENCY_RE = re.compile(r"\$([\d,]+(?:\.\d{2})?)")
FLOAT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)")

def clean_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.replace("\xa0", " ").replace("\u200b", " ")
    return SPACE_RE.sub(" ", s).strip()

def to_float(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    m = FLOAT_RE.search(str(s))
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None

def money_to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    m = CURRENCY_RE.search(str(s))
    if not m:
        return None
    return float(m.group(1).replace(",", ""))

def safe_concat_frames(frames: List[pd.DataFrame], on_keys: List[str], how: str = "left") -> pd.DataFrame:
    base = None
    for f in frames:
        if f is None or f.empty:
            continue
        if base is None:
            base = f.copy()
        else:
            base = pd.merge(base, f, on=on_keys, how=how, suffixes=("", "_dup"))
            dup_cols = [c for c in base.columns if c.endswith("_dup")]
            if dup_cols:
                base.drop(columns=dup_cols, inplace=True)
    return base if base is not None else pd.DataFrame()
