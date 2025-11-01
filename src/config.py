import os


ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")
OUTPUT_DIR = os.path.join(ROOT, "outputs")
LOG_DIR = os.path.join(OUTPUT_DIR, "logs")


# Update this list to match your 61 headers exactly (order matters for Excel)
HEADER_ORDER = [
# Race basics
"Track", "RaceNumber", "Race", "RaceDate", "RaceTime", "Grade", "RaceClass", "Distance",
# Dog basics
"Box", "DogName", "Trainer", "Owner", "Sire", "Dam", "Age", "Sex", "Color", "Weight",
# Career summary
"Starts", "Wins", "Seconds", "Thirds", "CareerPrizeMoney", "CareerBest",
# Trainer stats
"TrainerWinRate", "TrainerCity", "TrainerState",
# Conditions
"TrackCondition", "Weather", "Interference", "Direction",
# Performance metrics
"Odds", "Odds_num", "BestTime", "BestTime_num", "Margin",
"Sectional1", "Sectional2", "Sectional3", "SplitAvg",
"SpeedIndex", "EarlySpeed", "ClosingSpeed", "ConsistencyIndex",
# Box/Distance stats
"TrackDistanceWins", "TrackDistancePlaces", "TrackStarts", "TrackWins",
"DistanceStarts", "DistanceWins", "DistancePlaces",
"BoxHistory", "BoxWins", "BoxPlaces", "BoxBiasFactor",
# Recency
"RTC", "DLR", "DLW",
# Narrative
"RaceComment", "LastStartDate", "LastStartTrack", "LastStartResult", "LastStartMargin", "LastStartComment",
# Derived score
"Score", "FinalScore",
# Admin
"Comments", "Notes", "SourcePDF"
]


# Regex common patterns
RE_FLOAT = r"[0-9]+(?:\.[0-9]+)?"
RE_TIME = r"\d{1,2}:\d{2}\.\d{2}"
RE_MONEY = r"\$[\d,]+(?:\.\d{2})?"


# Thresholds / feature weights (editable)
FEATURES_CFG = {
"early_weight_sprint": 0.30,
"early_weight_mid": 0.25,
"early_weight_long": 0.20,
}
