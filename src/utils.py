# src/utils.py

import re
import pandas as pd
from typing import Optional, List, Tuple

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


def split_age_sex(token: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    """
    Parse tokens like '2d', '3b', '2D', '3B' commonly used on greyhound forms.
    Returns (age:int|None, sex:str|None) where sex is 'M' or 'F'.
    """
    if not token:
        return None, None
    t = str(token).strip()
    if not t:
        return None, None

    # age = leading digits (if any)
    age = None
    m_age = re.match(r"(\d+)", t)
    if m_age:
        try:
            age = int(m_age.group(1))
        except Exception:
            age = None

    # sex = trailing letter (if any)
    sex = None
    m_sex = re.search(r"([A-Za-z])$", t)
    if m_sex:
        letter = m_sex.group(1).lower()
        if letter == "d":  # dog (male)
            sex = "M"
        elif letter == "b":  # bitch (female)
            sex = "F"
        else:
            # Fallback: use uppercase of the letter if not d/b
            sex = letter.upper()

    return age, sex


def kmh(distance_m: Optional[float], time_s: Optional[float]) -> Optional[float]:
    if distance_m and time_s and time_s > 0:
        return (distance_m / time_s) * 3.6
    return None


def safe_concat_frames(frames: List[pd.DataFrame], on_keys: List[str], how: str = "left") -> pd.DataFrame:
    """
    Merge a list of dataframes on specific keys, tolerating empty/None frames,
    and dropping duplicate-suffix columns created by merge.
    """
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
