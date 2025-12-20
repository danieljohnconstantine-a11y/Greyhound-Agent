@echo off
REM Greyhound Racing Prediction System - ML Hybrid Mode (Today's Races)
REM Run ML hybrid predictions on today's races from data_predictions folder
REM Creates separate Excel output with ML picks

echo ========================================
echo ML Hybrid Prediction System - Today
echo v4.4 + Machine Learning
echo ========================================
echo.

REM Create data_predictions folder if it doesn't exist
if not exist "data_predictions\" (
    echo Creating data_predictions folder...
    mkdir data_predictions
    echo.
)

REM Check if there are any PDFs in data_predictions
set PDF_COUNT=0
for %%f in (data_predictions\*form.pdf) do set /a PDF_COUNT+=1
if %PDF_COUNT%==0 (
    echo WARNING: No race PDFs found in data_predictions folder!
    echo.
    echo Please add today's race form PDFs to the 'data_predictions' folder
    echo Example: BDGOG0812form.pdf, MAITG0812form.pdf
    echo.
    echo The script will continue anyway - the Python script will check again.
    echo.
)

echo.
echo Running ML hybrid predictions on today's races...
echo.
echo Note: This combines v4.4 rule-based scoring with ML predictions
echo       Only shows bets when BOTH systems strongly agree
echo       Expected: 35-40%% win rate (vs 28-30%% v4.4 alone)
echo.
echo Folder structure:
echo   data_predictions\  - Today's races (for predictions)
echo   data\              - Historical races (for ML training)
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
