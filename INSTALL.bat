@echo off
REM ======================================================================
REM GREYHOUND PREDICTION SYSTEM - ONE-TIME INSTALLATION
REM ======================================================================
echo.
echo ======================================================================
echo GREYHOUND RACING PREDICTION SYSTEM
echo One-Time Installation
echo ======================================================================
echo.
echo This will install all required packages...
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found!
echo.
echo Installing packages (this may take 2-3 minutes)...
echo.

pip install --upgrade pip
pip install numpy pandas scikit-learn xgboost pdfplumber pillow

echo.
echo ======================================================================
echo INSTALLATION COMPLETE!
echo ======================================================================
echo.
echo MODELS STATUS:
if exist "models\WENTWORTH PARK\rf.pkl" (
    echo   [OK] Pre-trained models found
    echo   System ready to use immediately!
) else (
    echo   [!] No pre-trained models found
    echo   You'll need to run train_ml.bat first
)
echo.
echo NEXT STEPS:
echo   1. Put today's PDFs in data_predictions folder
echo   2. Run RUN.bat to get predictions
echo.
pause
