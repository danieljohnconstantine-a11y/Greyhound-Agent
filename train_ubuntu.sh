#!/bin/bash
# ============================================================
#  RETRAIN ALL TRACKS — SIGMOID CALIBRATION (Ubuntu / Linux)
#  Greyhound Agent — March 2026
# ============================================================
#
#  This is the Linux/Ubuntu equivalent of retrain_all_tracks_sigmoid.bat.
#  Use this script when training on Ubuntu (Windows PowerShell times out
#  for large datasets — Ubuntu handles it without timeout issues).
#
#  What it does:
#    - Reads all results CSVs + PDF form guides in data/
#    - Trains RF + GB + XGB with sigmoid calibration per track
#    - Saves models/{TRACK}_rf/gb/xgb/scaler.pkl  (each < 5 MB)
#    - Writes a report to reports/RETRAIN_REPORT_<date>.txt
#
#  Duration: ~20 minutes on a modern machine
#  Output: models/{TRACK}_rf.pkl, _gb.pkl, _xgb.pkl, _scaler.pkl
#
#  After training, copy models/*.pkl to your Windows machine and
#  run  run_track_ensemble_predictions.bat  as normal.
# ============================================================

set -e

# ── Colors ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ── Move to script directory ────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "============================================================"
echo " RETRAIN ALL TRACKS — SIGMOID CALIBRATION"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""
echo " Script  : retrain_all_tracks_sigmoid.py"
echo " Duration: ~20 minutes"
echo " Output  : models/{TRACK}_rf.pkl  _gb.pkl  _xgb.pkl  _scaler.pkl"
echo ""

# ── Activate virtual environment if present ────────────────
if [ -d "venv" ]; then
    echo -e "${BLUE}==>${NC} Activating virtual environment (venv/)..."
    source venv/bin/activate
    echo -e "${GREEN}✓${NC}  venv active: $(python --version)"
elif [ -d ".venv" ]; then
    echo -e "${BLUE}==>${NC} Activating virtual environment (.venv/)..."
    source .venv/bin/activate
    echo -e "${GREEN}✓${NC}  venv active: $(python --version)"
else
    echo -e "${YELLOW}ℹ${NC}  No venv found — using system Python"
fi

# ── Resolve python command ─────────────────────────────────
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "${RED}✗${NC}  Python not found. Install python3 and try again."
    exit 1
fi

# ── Check required packages ────────────────────────────────
echo ""
echo -e "${BLUE}==>${NC} Checking required packages..."
if ! $PYTHON -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl" 2>/dev/null; then
    echo -e "${YELLOW}ℹ${NC}  Installing missing packages..."
    $PYTHON -m pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
    echo ""
fi
echo -e "${GREEN}✓${NC}  All packages present"

# ── Check results availability across data + dataN dirs ─────
RESULT_FILES_COUNT=$($PYTHON - <<'PY'
from src.results_loader import find_result_files
print(len(find_result_files('data')))
PY
)
if [ "${RESULT_FILES_COUNT}" -eq 0 ]; then
    echo -e "${RED}✗${NC}  No supported results files found in data/data2/data3/data4."
    echo "   Add results CSV/DOCX files with Track,Date,Race,Winner,2nd,3rd,4th."
    exit 1
fi
echo -e "${GREEN}✓${NC}  Found ${RESULT_FILES_COUNT} results file(s) across data directories"

# ── Remove stale models so we start clean ──────────────────
echo ""
echo -e "${BLUE}==>${NC} Removing old models/*.pkl files..."
rm -f models/*.pkl 2>/dev/null || true
echo -e "${GREEN}✓${NC}  Old models cleared"

# ── Run training ────────────────────────────────────────────
echo ""
echo -e "${BLUE}==>${NC} Starting training..."
echo "   (First progress line appears after ~30-60 seconds of PDF parsing)"
echo ""

$PYTHON retrain_all_tracks_sigmoid.py "$@"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    MODEL_COUNT=$(ls models/*.pkl 2>/dev/null | wc -l)
    echo "============================================================"
    echo -e " ${GREEN}TRAINING COMPLETE ✓${NC}"
    echo "============================================================"
    echo ""
    echo " Models saved in models/  ($MODEL_COUNT .pkl files)"
    echo " Report saved in reports/RETRAIN_REPORT_*.txt"
    echo ""
    echo " Next steps:"
    echo "   1. Check models/ — you should see 4 .pkl files per track"
    echo "   2. Copy models/*.pkl to your Windows machine"
    echo "   3. On Windows, run run_track_ensemble_predictions.bat"
    echo ""
    echo "   OR commit models directly:"
    echo "   git add models/*.pkl"
    echo "   git commit -m 'retrain all tracks: sigmoid calibration'"
    echo "   git push"
    echo ""
    echo "============================================================"
else
    echo "============================================================"
    echo -e " ${RED}ERROR — Training failed (exit code $EXIT_CODE)${NC}"
    echo "============================================================"
    echo ""
    echo " Common fixes:"
    echo "   - '0 tracks trained': make sure results files exist in data/ and/or data2+/"
    echo "   - ModuleNotFoundError: run  pip install pdfplumber xgboost"
    echo "   - 'Can't pickle': update to latest code (nthread=1 fix applied)"
    echo ""
    echo "============================================================"
    exit $EXIT_CODE
fi
