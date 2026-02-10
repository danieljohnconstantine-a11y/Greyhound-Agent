@echo off
REM ======================================================================
REM GREYHOUND PREDICTIONS - TRACK ENSEMBLE (BEST ACCURACY)
REM ======================================================================
REM
REM This is the RECOMMENDED entry point for daily predictions!
REM Uses track-specific ensemble models for highest accuracy.
REM
REM ======================================================================

echo.
echo ======================================================================
echo GREYHOUND RACING PREDICTIONS - TRACK ENSEMBLE MODE
echo ======================================================================
echo.
echo This is the RECOMMENDED mode for best accuracy!
echo.
echo Prerequisites:
echo   1. Models trained (run TRAIN_MODELS.bat first time only)
echo   2. Race PDFs in data_predictions/ folder
echo.
echo ======================================================================
echo.

REM Check if data_predictions folder exists
if not exist "data_predictions\" (
    echo Creating data_predictions folder...
    mkdir data_predictions
)

REM Count PDFs
set PDF_COUNT=0
for %%f in (data_predictions\*.pdf) do set /a PDF_COUNT+=1

if %PDF_COUNT%==0 (
    echo ERROR: No PDF files found!
    echo.
    echo Please copy today's race form PDFs to: data_predictions/
    echo Example: WENPG0203form.pdf
    echo.
    pause
    exit /b 1
)

echo Found %PDF_COUNT% race form PDF(s)
echo.
echo Running track ensemble predictions...
echo.

python run_track_ensemble_predictions.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo PREDICTIONS COMPLETE!
    echo ======================================================================
    echo.
    echo Check: outputs/track_ensemble_predictions.xlsx
    echo.
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo ERROR - Prediction failed with error code %ERRORLEVEL%
    echo ======================================================================
    echo.
)

pause
