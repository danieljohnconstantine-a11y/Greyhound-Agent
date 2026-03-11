@echo off
REM ============================================================
REM  RETRAIN ALL TRACKS — SIGMOID CALIBRATION
REM  Greyhound Agent — March 2026
REM ============================================================
REM
REM  This is the CORRECT training script.
REM  Do NOT use train_ml_track_ensemble.bat (isotonic calibration, wrong layout).
REM
REM  What it does:
REM    - Reads all results CSVs + PDF form guides in data/
REM    - Trains RF + GB + XGB with sigmoid calibration per track
REM    - Saves models/{TRACK}_rf/gb/xgb/scaler.pkl  (each < 5 MB)
REM    - Writes a report to reports/RETRAIN_REPORT_<date>.txt
REM
REM  Duration: ~20 minutes on a modern laptop
REM  Output: models/{TRACK}_rf.pkl, _gb.pkl, _xgb.pkl, _scaler.pkl
REM ============================================================

chcp 65001 > nul
set PYTHONUTF8=1

echo.
echo ============================================================
echo  RETRAIN ALL TRACKS — SIGMOID CALIBRATION
echo ============================================================
echo.
echo  Script  : retrain_all_tracks_sigmoid.py
echo  Duration: ~20 minutes
echo  Output  : models\{TRACK}_rf.pkl  _gb.pkl  _xgb.pkl  _scaler.pkl
echo.
echo  Press any key to start, or CTRL+C to cancel.
echo ============================================================
echo.
pause

REM ── Check Python is available ──────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found in PATH.
    echo         Please install Python 3.10+ and re-run.
    echo.
    pause
    exit /b 1
)

REM ── Check required packages ────────────────────────────────
echo Checking required packages...
python -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl" 2>nul
if errorlevel 1 (
    echo.
    echo [INFO] Installing missing packages...
    echo.
    pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
    echo.
)

REM ── Delete stale models so we start clean ──────────────────
echo Removing old models\*.pkl files...
del /Q models\*.pkl 2>nul
echo.

REM ── Run training ───────────────────────────────────────────
echo Starting training...
echo (First progress line appears after ~30-60 seconds of PDF parsing)
echo.

python retrain_all_tracks_sigmoid.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  TRAINING COMPLETE
    echo ============================================================
    echo.
    echo  Models saved in models\
    echo  Report saved in reports\RETRAIN_REPORT_*.txt
    echo.
    echo  Next steps:
    echo    1. Check models\ — you should see 4 .pkl files per track
    echo    2. git add models\*.pkl
    echo    3. git commit -m "retrain all tracks: sigmoid calibration"
    echo    4. git push origin copilot/copy-ml-training-prediction-files-again
    echo    5. Then run run_track_ensemble_predictions.bat to generate predictions
    echo.
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo  ERROR — Training failed  (exit code %ERRORLEVEL%)
    echo ============================================================
    echo.
    echo  Common fixes:
    echo    - "0 tracks trained" : make sure data\*.csv results files exist
    echo    - ModuleNotFoundError: run  pip install pdfplumber xgboost
    echo    - File too large for GitHub: each .pkl must be under 100 MB
    echo.
    echo ============================================================
)

pause
