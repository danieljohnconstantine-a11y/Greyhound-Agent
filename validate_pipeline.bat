@echo off
REM ============================================================
REM  VALIDATE PIPELINE
REM  Greyhound Agent — March 2026
REM ============================================================
REM
REM  What it does:
REM    - Scans models/ directory for all .pkl files
REM    - Confirms each track has RF + GB + XGB + scaler
REM    - Test-loads every model to verify it is not corrupt
REM    - Runs a dummy prediction through each ensemble
REM    - Checks ensemble_config.json matches actual model files
REM
REM  Run this after training to confirm all models are valid.
REM  Duration: ~60 seconds
REM ============================================================

chcp 65001 > nul
set PYTHONUTF8=1

echo.
echo ============================================================
echo  VALIDATE PIPELINE — MODEL INTEGRITY CHECK
echo ============================================================
echo.
echo  Scanning models\ for RF + GB + XGB + scaler per track...
echo.
echo  Press any key to start, or CTRL+C to cancel.
pause > nul

python validate_pipeline.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  VALIDATION PASSED — all models loaded and tested OK
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo  VALIDATION FAILED  (exit code %ERRORLEVEL%)
    echo ============================================================
    echo.
    echo  Common fixes:
    echo    - Missing .pkl : re-run retrain_all_tracks_sigmoid.bat
    echo    - Corrupt model : delete models\*.pkl and retrain
)

echo.
pause
