@echo off
REM ============================================================
REM  AUDIT ALL FEATURES
REM  Greyhound Agent — March 2026
REM ============================================================
REM
REM  What it does:
REM    - Verifies all 75 ML features are computed per dog correctly
REM    - Confirms each feature produces a unique value per dog
REM      (or a meaningful track/race-level signal where expected)
REM    - Writes reports/FEATURE_AUDIT_<date>.txt
REM
REM  Run this after any change to src/features.py to verify
REM  nothing is accidentally duplicated or zeroed out.
REM  Duration: ~10 seconds
REM ============================================================

chcp 65001 > nul
set PYTHONUTF8=1

echo.
echo ============================================================
echo  AUDIT ALL FEATURES  (75 ML features)
echo ============================================================
echo.
echo  Output: reports\FEATURE_AUDIT_^<date^>.txt
echo.
echo  Press any key to start, or CTRL+C to cancel.
pause > nul

python audit_all_features.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  AUDIT COMPLETE — see reports\FEATURE_AUDIT_*.txt
    echo ============================================================
) else (
    echo.
    echo [ERROR] audit_all_features.py failed  (exit code %ERRORLEVEL%)
)

echo.
pause
