import re
import pandas as pd
from typing import Dict, List, Any, Optional
from .utils import clean_text


# Typical examples in daily greyhound forms:
# "Box 1: 3-1-0  Track 15: 4-3-2  Distance 10: 2-1-1"
RE_BOX_LINE = re.compile(r"Box\s*(\d+):\s*(\d+)-(\d+)-(\d+)", re.IGNORECASE)
RE_TRACK_LINE = re.compile(r"Track\s*(\d+):\s*(\d+)-(\d+)-(\d+)", re.IGNORECASE)
RE_DIST_LINE = re.compile(r"Distance\s*(\d+):\s*(\d+)-(\d+)-(\d+)", re.IGNORECASE)


def parse_box_history(text: str, box_bias_map: Optional[dict] = None) -> pd.DataFrame:
    """
    Parse the 'Box History' section for each dog in the form, extracting box/track/distance stats.

    Args:
        text: The extracted text from the PDF form (string)
        box_bias_map: Optional dict of precomputed bias factors per (track, box)

    Returns:
        pd.DataFrame with fields:
        ['BoxHistory', 'Box', 'BoxWins', 'BoxPlaces', 'BoxBiasFactor',
         'TrackStarts', 'TrackWins', 'TrackDistanceWins', 'TrackDistancePlaces',
         'DistanceStarts', 'DistanceWins', 'DistancePlaces']
    """
    lines = [clean_text(x) for x in text.splitlines()]
    rows: List[Dict[str, Any]] = []

    for line in lines:
        if not line or "Box" not in line:
            continue

        # many forms embed all 3 stats on one line
        if ("Track" in line or "Distance" in line) and ("Box" in line):
            r: Dict[str, Any] = {
                "BoxHistory": line,
                "Box": None,
                "BoxWins": None,
                "BoxPlaces": None,
                "BoxBiasFactor": None,
                "TrackStarts": None,
                "TrackWins": None,
                "TrackDistanceWins": None,
                "TrackDistancePlaces": None,
                "DistanceStarts": None,
                "DistanceWins": None,
                "DistancePlaces": None,
            }

            if (m := RE_BOX_LINE.search(line)):
                r["Box"] = int(m.group(1))
                r["BoxWins"] = int(m.group(2))
                r["BoxPlaces"] = int(m.group(3))

            if (m := RE_TRACK_LINE.search(line)):
                r["TrackStarts"] = int(m.group(1))
                r["TrackWins"] = int(m.group(2))
                r["TrackDistanceWins"] = int(m.group(3))
                r["TrackDistancePlaces"] = int(m.group(4))

            if (m := RE_DIST_LINE.search(line)):
                r["DistanceStarts"] = int(m.group(1))
                r["DistanceWins"] = int(m.group(2))
                r["DistancePlaces"] = int(m.group(3))

            # attach bias factor if available
            if box_bias_map and r.get("Box") is not None:
                # optionally include track in future
                track_bias = box_bias_map.get(str(r["Box"]), 0)
                r["BoxBiasFactor"] = track_bias

            rows.append(r)

    return pd.DataFrame(rows)
