import re
import pandas as pd
from typing import Dict, List, Any
from .utils import clean_text, to_float

# Examples:
# "Best Time 22.45"
# "Sectional 1 5.12  Sectional 2 10.34  Sectional 3 16.45"
# "Margin 2.50"
# Optional: "Box Bias: -0.3"

RE_BEST_TIME = re.compile(r"Best\s*Time[: ]*([0-9]+\.[0-9]+)", re.IGNORECASE)
RE_SECTIONAL = re.compile(
    r"Sectional\s*1[: ]*([0-9]+\.[0-9]+).*?Sectional\s*2[: ]*([0-9]+\.[0-9]+).*?Sectional\s*3[: ]*([0-9]+\.[0-9]+)",
    re.IGNORECASE,
)
RE_MARGIN = re.compile(r"Margin[: ]*([0-9]+\.[0-9]+)", re.IGNORECASE)
RE_BOX_BIAS = re.compile(r"Box\s*Bias[: ]*([\-0-9\.]+)", re.IGNORECASE)

def parse_timing_metrics(text: str) -> pd.DataFrame:
    """
    Extract time and sectional metrics.
    Returns columns: BestTime, Sectional1, Sectional2, Sectional3, Margin, BoxBiasFactor
    """
    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}

    for line in lines:
        if not line:
            continue

        if (m := RE_BEST_TIME.search(line)):
            current["BestTime"] = to_float(m.group(1))

        if (m := RE_SECTIONAL.search(line)):
            current["Sectional1"] = to_float(m.group(1))
            current["Sectional2"] = to_float(m.group(2))
            current["Sectional3"] = to_float(m.group(3))

        if (m := RE_MARGIN.search(line)):
            current["Margin"] = to_float(m.group(1))

        if (m := RE_BOX_BIAS.search(line)):
            current["BoxBiasFactor"] = to_float(m.group(1))

        # Push a row whenever we catch something (conservative; downstream merge dedups)
        if current:
            rows.append(current)
            current = {}

    return pd.DataFrame(rows)
