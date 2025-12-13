@echo off
echo ========================================
echo ML Hybrid Enhanced Prediction System
echo v2.1 with Weather ^& Track Conditions
echo ========================================
echo.
echo.
echo Running ML v2.1 enhanced predictions on today's races...
echo.
echo Note: This uses weather and track condition data for maximum accuracy
echo       Expected: 41-47%% win rate (vs 40-45%% v2.0, 35-40%% v1.0)
echo.
echo Folder structure:
echo   data_predictions\  - Today's races (for predictions)
echo   data\              - Historical races (for ML training)
echo   data\weather_conditions.csv - Weather data
echo   data\track_conditions.csv - Track condition ratings
echo.

REM Check if data_predictions folder exists, create if not
if not exist "data_predictions\" (
    echo Creating data_predictions folder...
    mkdir data_predictions
    echo.
)

REM Check for PDFs in data_predictions
dir /b data_predictions\*.pdf >nul 2>&1
if errorlevel 1 (
    echo ========================================
    echo WARNING: No PDFs found in data_predictions
    echo ========================================
    echo.
    echo Please copy today's race PDFs to data_predictions\
    echo Example: ANGLG1212form.pdf, SANDG1212form.pdf, etc.
    echo.
    echo The script will continue but may not generate predictions...
    echo.
)

REM Run the Python script
python run_ml_hybrid_enhanced.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR - Prediction failed with error code %errorlevel%
    echo ========================================
    echo.
    echo Check the error messages above for details.
    echo Common issues:
    echo   1. ML model not trained - run train_ml_enhanced.bat first
    echo   2. Missing PDFs in data_predictions folder
    echo   3. Missing weather or track condition data
    echo.
) else (
    echo.
    echo ========================================
    echo ML Enhanced predictions complete!
    echo ========================================
    echo.
    echo Check outputs folder for:
    echo   - ml_hybrid_enhanced_picks.xlsx (Excel with ML v2.1 hybrid picks)
    echo   - ml_enhanced_all_predictions.xlsx (All ML v2.1 predictions ranked)
    echo   - v44_picks_comparison.csv (All v4.4 picks for reference)
    echo.
)

pause
