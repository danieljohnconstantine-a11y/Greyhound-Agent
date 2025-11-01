import os

# ===============================
# 📁 PATHS AND FILE STRUCTURE
# ===============================
ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")
OUTPUT_DIR = os.path.join(ROOT, "outputs")
LOG_DIR = os.path.join(OUTPUT_DIR, "logs")
ARCHIVE_DIR = os.path.join(OUTPUT_DIR, "archived")

# Ensure directories exist
for path in [DATA_DIR, OUTPUT_DIR, LOG_DIR, ARCHIVE_DIR]:
    os.makedirs(path, exist_ok=True)

# ===============================
# 🧩 HEADER ORDER (From Excel)
# ===============================
HEADER_ORDER = [
    "Track", "Race", "Box", "DogName", "Trainer", "Grade", "Distance", "RaceDate",
    "Form", "WinRate", "PlaceRate", "Odds", "BestTime", "Margin",
    "Sectional1", "Sectional2", "Sectional3", "RaceComment",
    "Starts", "Wins", "Seconds", "Thirds", "CareerPrizeMoney", "CareerBest",
    "RaceClass", "TrackCondition", "Weather", "Interference",
    "TrainerWinRate", "TrainerState", "TrainerCity",
    "Owner", "Sire", "Dam", "Age", "Sex", "Color", "Weight",
    "LastStartDate", "LastStartTrack", "LastStartResult",
    "LastStartMargin", "LastStartComment",
    "SplitAvg", "SpeedIndex", "ConsistencyIndex",
    "TrackDistanceWins", "TrackDistancePlaces", "TrackStarts", "TrackWins",
    "DistanceStarts", "DistanceWins", "DistancePlaces",
    "BoxHistory", "BoxWins", "BoxPlaces",
    "EarlySpeed", "ClosingSpeed",
    "Score", "Comments", "Notes", "SourcePDF"
]

# ===============================
# 🧮 REGEX PATTERNS
# ===============================
# General numeric and timing expressions
RE_FLOAT = r"[0-9]+(?:\\.[0-9]+)?"
RE_TIME = r"\\d{1,2}:\\d{2}\\.\\d{2}"
RE_MONEY = r"\\$[\\d,]+(?:\\.\\d{2})?"
RE_PERCENT = r"\\d{1,2}(?:\\.\\d+)?%"

# ===============================
# ⚙️ FEATURE CALCULATION WEIGHTS
# ===============================
FEATURES_CFG = {
    "speed_weight": 0.4,
    "consistency_weight": 0.2,
    "early_weight": 0.2,
    "closing_weight": 0.2,
}

# ===============================
# 🎯 MERGE KEYS (used across parsers)
# ===============================
MERGE_KEYS = ["Track", "Race", "Box", "DogName"]

# ===============================
# 🧠 DIAGNOSTIC SETTINGS
# ===============================
DIAGNOSTIC_TOP_MISSING_FIELDS = 10
DIAGNOSTIC_OUTPUT_CSV = os.path.join(LOG_DIR, "audit_summary.csv")

# ===============================
# ✅ CONFIG SUMMARY
# ===============================
print(f"[CONFIG] Loaded Greyhound-Agent configuration:")
print(f"  Data Directory  : {DATA_DIR}")
print(f"  Output Directory: {OUTPUT_DIR}")
print(f"  Log Directory   : {LOG_DIR}")
print(f"  Headers Loaded  : {len(HEADER_ORDER)} fields")
