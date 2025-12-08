@echo off
REM ======================================================================
REM Daily Predictions - Predict winners for today's races
REM ======================================================================
REM 
REM This script runs predictions ONLY on PDFs in the data_predictions/ folder
REM 
REM Usage:
REM   1. Copy today's race form PDFs to data_predictions/ folder
REM   2. Double-click this file
REM   3. View predictions for each race
REM 
REM After races run:
REM   - Move PDFs from data_predictions/ to data/
REM   - Add results CSV to data/
REM   - Run train_ml.bat to update ML model
REM ======================================================================

echo ======================================================================
echo Daily Predictions - v4.4 Greyhound Racing System
echo ======================================================================
echo.
echo Analyzing races in: data_predictions\
echo.

REM Check if data_predictions folder exists
if not exist "data_predictions\" (
    echo ERROR: data_predictions\ folder not found!
    echo Please create it and add today's race form PDFs
    pause
    exit /b 1
)

REM Count PDF files
set PDF_COUNT=0
for %%f in (data_predictions\*.pdf) do set /a PDF_COUNT+=1

if %PDF_COUNT%==0 (
    echo WARNING: No PDF files found in data_predictions\
    echo.
    echo Please add today's race form PDFs to data_predictions\ folder
    echo Example: BDGOG0612form.pdf, MAITG0612form.pdf
    pause
    exit /b 1
)

echo Found %PDF_COUNT% race form PDF(s)
echo.
echo Running predictions...
echo ======================================================================
echo.

REM Run predictions on all PDFs in data_predictions folder
python main.py data_predictions\*.pdf

echo.
echo ======================================================================
echo Predictions complete!
echo ======================================================================
echo.
echo NEXT STEPS:
echo   After races run:
echo   1. Move PDFs from data_predictions\ to data\
echo   2. Add results CSV to data\
echo   3. Run train_ml.bat to update ML model
echo.
pause
