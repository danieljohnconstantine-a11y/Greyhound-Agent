@echo off
REM ============================================================================
REM Train Enhanced ML Model v2.1 - Weather & Track Condition Integration
REM ============================================================================
REM
REM This script trains the enhanced ML model with weather and track condition
REM data integration for maximum accuracy.
REM
REM Features:
REM   - All ML v2.0 features (track-specific, ensemble, 70+ features)
REM   - Weather data integration (temperature, humidity, rainfall, wind)
REM   - Track condition modeling (fast/slow/heavy ratings)
REM   - Expected: 41-47% win rate (vs 40-45% v2.0)
REM
REM Usage:
REM   1. Ensure data folder contains historical race PDFs and results CSVs
REM   2. Optionally add weather data to data/weather_conditions.csv
REM   3. Optionally add track conditions to data/track_conditions.csv
REM   4. Run this script
REM
REM Output:
REM   - Enhanced model saved to models/greyhound_ml_v2.1_enhanced.pkl
REM   - Training metrics and performance report
REM
REM ============================================================================

echo.
echo ================================================================================
echo ENHANCED ML TRAINING v2.1 - Weather ^& Track Condition Integration
echo ================================================================================
echo.
echo This system adds weather and track condition modeling to ML v2.0:
echo   * Weather: Temperature, humidity, rainfall, wind speed
echo   * Track conditions: Fast/slow/heavy ratings and effects
echo   * Expected improvement: +1-2%% win rate (40-45%% -^> 41-47%%)
echo.
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and run setup.bat first
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import pandas, numpy, sklearn, pickle" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Required packages not installed
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Check for data folder
if not exist "data\" (
    echo ERROR: data folder not found
    echo Please ensure you have historical race data in the data folder
    pause
    exit /b 1
)

REM Create models folder if it doesn't exist
if not exist "models\" mkdir models

REM Create sample weather/track condition files if they don't exist
echo.
echo Setting up weather and track condition data files...
python -c "from src.weather_track_data import create_sample_data_files; create_sample_data_files()"

echo.
echo ================================================================================
echo Starting Enhanced ML Training...
echo ================================================================================
echo.
echo This may take 10-20 minutes depending on your system.
echo The script will:
echo   1. Load historical race data and results
echo   2. Load weather and track condition data
echo   3. Extract 80+ enhanced features (70+ ML + 10+ weather/track)
echo   4. Train track-specific ensemble models
echo   5. Optimize hyperparameters per venue
echo   6. Validate performance and save model
echo.

REM Run the training script
python train_ml_enhanced.py

if %errorlevel% equ 0 (
    echo.
    echo ================================================================================
    echo SUCCESS - Enhanced ML Model v2.1 Training Complete!
    echo ================================================================================
    echo.
    echo Model saved to: models/greyhound_ml_v2.1_enhanced.pkl
    echo.
    echo Next steps:
    echo   1. Copy today's race PDFs to data_predictions/ folder
    echo   2. Run: run_ml_hybrid_enhanced.bat
    echo   3. Check outputs/ml_hybrid_enhanced_picks.xlsx
    echo.
    echo Expected Performance:
    echo   - Win Rate: 41-47%% (hybrid picks)
    echo   - Selectivity: ~6-8%% of races
    echo   - Improvement: +1-2%% over ML v2.0
    echo.
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo ERROR - Training failed with error code %errorlevel%
    echo ================================================================================
    echo.
    echo Check the error messages above for details.
    echo Common issues:
    echo   1. Insufficient training data (need 100+ races minimum)
    echo   2. Missing required columns in data
    echo   3. Memory error (try closing other applications)
    echo.
    pause
    exit /b 1
)

pause
