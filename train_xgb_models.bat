@echo off
REM ============================================================
REM  TRAIN XGB MODELS ONLY
REM  Greyhound Agent — March 2026
REM ============================================================
REM
REM  What it does:
REM    - Trains XGBoost models only (NOT RF or GB)
REM    - Reads data/results_*.csv + matching PDF form guides
REM    - Reuses existing per-track scalers (must already exist)
REM    - Saves models/{TRACK}_xgb.pkl alongside existing RF+GB models
REM
REM  Use this if you want to rebuild only the XGB models without
REM  re-running the full retrain.
REM
REM  For a full retrain of ALL models use retrain_all_tracks_sigmoid.bat
REM
REM  Prerequisites: models/{TRACK}_scaler.pkl must already exist.
REM  Duration: ~10 minutes
REM ============================================================

chcp 65001 > nul
set PYTHONUTF8=1

echo.
echo ============================================================
echo  TRAIN XGB MODELS ONLY
echo ============================================================
echo.
echo  Input : data\results_*.csv + data\*.pdf (form guides)
echo  Output: models\{TRACK}_xgb.pkl per track
echo.
echo  NOTE: For a full retrain, use retrain_all_tracks_sigmoid.bat instead.
echo.
echo  Press any key to start, or CTRL+C to cancel.
pause > nul

python -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl" 2>nul
if errorlevel 1 (
    echo Installing missing packages...
    pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
    echo.
)

python train_xgb_models.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  XGB TRAINING COMPLETE — models\{TRACK}_xgb.pkl updated
    echo ============================================================
) else (
    echo.
    echo [ERROR] train_xgb_models.py failed  (exit code %ERRORLEVEL%)
    echo         Make sure models\{TRACK}_scaler.pkl files exist first.
    echo         Run retrain_all_tracks_sigmoid.bat if scalers are missing.
)

echo.
pause
