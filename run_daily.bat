@echo off
REM ============================================================
REM  RUN DAILY PIPELINE
REM  Greyhound Agent — March 2026
REM ============================================================
REM
REM  What it does:
REM    - Runs main.py to generate today's form outputs
REM    - Checks for outputs/todays_form.csv, ranked.csv, picks.csv
REM
REM  Put today's PDFs in data_predictions/ first, then run this.
REM  Duration: ~2 minutes
REM ============================================================

chcp 65001 > nul
set PYTHONUTF8=1

echo.
echo ============================================================
echo  RUN DAILY PIPELINE
echo ============================================================
echo.
echo  Step 1: Make sure today's PDFs are in data_predictions\
echo  Step 2: Press any key to run
echo.
echo  Output: outputs\todays_form.csv, ranked.csv, picks.csv
echo.
echo  Press any key to start, or CTRL+C to cancel.
pause > nul

python run_daily.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  DONE — check outputs\ for today's picks
    echo ============================================================
) else (
    echo.
    echo [ERROR] run_daily.py failed  (exit code %ERRORLEVEL%)
    echo         Check that main.py exists and PDFs are in data_predictions\
)

echo.
pause
