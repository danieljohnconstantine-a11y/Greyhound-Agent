import re
import pandas as pd
from typing import Dict, List, Any
from .utils import clean_text, to_float

# Examples in forms:
# "Best Time 22.45"
# "Sectional 1 5.12  Sectional 2 10.34  Sectional 3 16.45"
# "Margin 2.50L"
# "Box Bias: -0.3"

RE_BEST_TIME = re.compile(r"Best\s*Time[: ]*([0-9]+\.[0-9]+)", re.IGNORECASE)
RE_SECTIONAL = re.compile(
    r"Sectional\s*1[: ]*([0-9]+\.[0-9]+).*?Sectional\s*2[: ]*([0-9]+\.[0-9]+).*?Sectional\s*3[: ]*([0-9]+\.[0-9]+)",
    re.IGNORECASE,
)
RE_MARGIN = re.compile(r"Margin[: ]*([0-9]+\.[0-9]+)", re.IGNORECASE)
RE_BOX_BIAS = re.compile(r"Box\s*Bias[: ]*([\-0-9\.]+)", re.IGNORECASE)


def parse_timing_metrics(text: str) -> pd.DataFrame:
    """
    Extracts time and sectional metrics for each dog entry.
    Matches 'Best Time', 'Sectional 1/2/3', 'Margin', and optional 'Box Bias'.
    """

    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []
    current_row: Dict[str, Any] = {}

    for line in lines:
        if not line:
            continue

        if (m := RE_BEST_TIME.search(line)):
            current_row["BestTime"] = to_float(m.group(1))

        if (m := RE_SECTIONAL.search(line)):
            current_row["Sectional1"] = to_float(m.group(1))
            current_row["Sectional2"] = to_float(m.group(2))
            current_row["Sectional3"] = to_float(m.group(3))

        if (m := RE_MARGIN.search(line)):
            current_row["Margin"] = to_float(m.group(1))

        if (m := RE_BOX_BIAS.search(line)):
            current_row["BoxBiasFactor"] = to_float(m.group(1))

        # When we have at least one complete metric, push and reset
        if current_row:
            rows.append(current_row)
            current_row = {}

    return pd.DataFrame(rows)
