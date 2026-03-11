@echo off
REM ============================================================
REM  SYSTEM READINESS CHECK
REM  Greyhound Agent — March 2026
REM ============================================================
REM
REM  What it does:
REM    - GO/NO-GO checklist for the full prediction pipeline
REM    - Checks every deployed track has RF + GB + XGB + scaler .pkl
REM    - Checks model calibration (spread > 0.5%, not collapsed)
REM    - Lists tracks that have results data but no model yet
REM    - Writes reports/SYSTEM_READY_CHECK_<date>.txt
REM
REM  Run this BEFORE running predictions to confirm the system is healthy.
REM  Duration: ~30 seconds
REM ============================================================

chcp 65001 > nul
set PYTHONUTF8=1

echo.
echo ============================================================
echo  SYSTEM READINESS CHECK  (GO / NO-GO)
echo ============================================================
echo.
echo  Checking all track models and calibration...
echo  Output: reports\SYSTEM_READY_CHECK_^<date^>.txt
echo.
echo  Press any key to start, or CTRL+C to cancel.
pause > nul

python check_system_ready.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  CHECK COMPLETE — see report above or in reports\ folder
    echo ============================================================
) else (
    echo.
    echo [ERROR] Script failed  (exit code %ERRORLEVEL%)
)

echo.
pause
