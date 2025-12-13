@echo off
REM Greyhound Racing Prediction System - ML Hybrid Mode
REM Run hybrid predictions (v4.4 + Machine Learning)

echo ========================================
echo ML Hybrid Prediction System
echo v4.4 + Machine Learning
echo ========================================
echo.

REM Check if data folder exists
if not exist "data\" (
    echo ERROR: data folder not found!
    echo Please create a 'data' folder and add race PDFs
    pause
    exit /b 1
)

echo Running ML hybrid predictions...
echo Only bets when v4.4 AND ML both agree (35-40%% win rate expected)
echo.
echo Note: If model not found, script will show instructions to train it
echo.

REM Run hybrid predictions
python demo_ml_hybrid.py

echo.
echo ========================================
echo Hybrid predictions complete!
echo ========================================
echo.
pause
