@echo off
REM Greyhound Racing Prediction System - v4.4
REM Run predictions on race PDFs

echo ========================================
echo Greyhound Prediction System v4.4
echo ========================================
echo.

REM Check if data folder exists
if not exist "data\" (
    echo ERROR: data folder not found!
    echo Please create a 'data' folder and add race PDFs
    pause
    exit /b 1
)

REM Check if PDF files exist
dir /b data\*form.pdf >nul 2>&1
if errorlevel 1 (
    echo ERROR: No PDF files found in data folder!
    echo Please add race PDFs to the data folder
    pause
    exit /b 1
)

echo Running predictions on all PDFs in data folder...
echo.

REM Run predictions on all PDFs
python main.py data\*form.pdf

echo.
echo ========================================
echo Predictions complete!
echo Check the output above for results
echo ========================================
echo.
pause
