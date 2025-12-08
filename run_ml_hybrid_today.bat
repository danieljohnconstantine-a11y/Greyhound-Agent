@echo off
REM Greyhound Racing Prediction System - ML Hybrid Mode (Today's Races)
REM Run ML hybrid predictions on today's races from data_predictions folder
REM Creates separate Excel output with ML picks

echo ========================================
echo ML Hybrid Prediction System - Today
echo v4.4 + Machine Learning
echo ========================================
echo.

REM Check if data_predictions folder exists
if not exist "data_predictions\" (
    echo ERROR: data_predictions folder not found!
    echo.
    echo Please create 'data_predictions' folder and add today's race PDFs
    echo.
    echo Folder structure:
    echo   data_predictions\  - Today's races (for predictions)
    echo   data\              - Historical races (for ML training)
    echo.
    pause
    exit /b 1
)

echo Running ML hybrid predictions on today's races...
echo.
echo Note: This combines v4.4 rule-based scoring with ML predictions
echo       Only shows bets when BOTH systems strongly agree
echo       Expected: 35-40%% win rate (vs 28-30%% v4.4 alone)
echo.

REM Run ML hybrid predictions
python run_ml_hybrid_today.py

echo.
echo ========================================
echo ML Hybrid predictions complete!
echo ========================================
echo.
echo Check outputs folder for:
echo   - ml_hybrid_picks.xlsx (Excel with your ML hybrid bets)
echo   - v44_picks_comparison.csv (All v4.4 picks for reference)
echo.
pause
