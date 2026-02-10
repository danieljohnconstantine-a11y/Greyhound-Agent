@echo off
REM Greyhound Prediction Pipeline - Windows
REM Run daily predictions using trained models

echo =====================================
echo  GREYHOUND PREDICTION PIPELINE
echo =====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.
    pause
    exit /b 1
)

REM Check if models directory exists
if not exist "models\" (
    echo ERROR: models\ directory not found.
    echo Please run TRAIN.sh on Ubuntu first to create models.
    pause
    exit /b 1
)

REM Check if data_predictions directory has PDFs
if not exist "data_predictions\*.pdf" (
    echo ERROR: No PDFs found in data_predictions\ folder.
    echo Please place today's race form PDFs in data_predictions\ folder.
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Running predictions...
python main.py

echo.
echo =====================================
echo  PREDICTIONS COMPLETE!
echo =====================================
echo Results saved to outputs\ directory
echo.
pause
