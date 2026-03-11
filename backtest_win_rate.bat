@echo off
REM ============================================================
REM  BACKTEST WIN RATE
REM  Greyhound Agent — March 2026
REM ============================================================
REM
REM  What it does:
REM    - Reads all data/results_*.csv files (factual race outcomes)
REM    - Computes historical win rate by box and by track
REM    - Shows what winning % the model can realistically target
REM    - Writes reports/BACKTEST_WIN_RATE_<date>.txt
REM
REM  Does NOT need models or PDFs — results CSVs only.
REM  Duration: ~10 seconds
REM ============================================================

chcp 65001 > nul
set PYTHONUTF8=1

echo.
echo ============================================================
echo  BACKTEST WIN RATE ANALYSIS
echo ============================================================
echo.
echo  Input : data/results_*.csv  (no PDFs or models needed)
echo  Output: reports/BACKTEST_WIN_RATE_^<date^>.txt
echo.
echo  Press any key to start, or CTRL+C to cancel.
pause > nul

python backtest_win_rate.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  DONE — report saved to reports\BACKTEST_WIN_RATE_*.txt
    echo ============================================================
) else (
    echo.
    echo [ERROR] Script failed  (exit code %ERRORLEVEL%)
    echo         Make sure data\results_*.csv files exist.
)

echo.
pause
