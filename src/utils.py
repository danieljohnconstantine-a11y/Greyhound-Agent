import re
import math
import pandas as pd
from typing import Optional


SPACE_RE = re.compile(r"\s+")
CURRENCY_RE = re.compile(r"\$([\d,]+(?:\.\d{2})?)")
FLOAT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)")




def clean_text(s: str) -> str:
if not s:
return ""
s = s.replace("\xa0", " ").replace("\u200b", " ")
return SPACE_RE.sub(" ", s).strip()




def to_float(s: Optional[str]) -> Optional[float]:
if s is None:
return None
m = FLOAT_RE.search(s)
if not m:
return None
try:
return float(m.group(1))
except:
return None




def money_to_float(s: Optional[str]) -> Optional[float]:
if not s:
return None
m = CURRENCY_RE.search(s)
if not m:
return None
return float(m.group(1).replace(",", ""))




def split_age_sex(token: str):
# Examples: "2d", "3b", "2f" (age-digit + sex-letter), fallback to None
if not token:
return None, None
token = token.strip().lower()
age = None
sex = None
if token and token[0].isdigit():
age = int(re.match(r"(\d+)", token).group(1))
if token and token[-1].isalpha():
sex = token[-1].upper()
return age, sex




def safe_concat_frames(frames, on_keys, how="left"):
import pandas as pd
base = None
for f in frames:
if f is None or f.empty:
continue
if base is None:
base = f.copy()
else:
base = pd.merge(base, f, on=on_keys, how=how, suffixes=("", "_dup"))
# Remove any _dup leftover columns
for c in list(base.columns):
return None
