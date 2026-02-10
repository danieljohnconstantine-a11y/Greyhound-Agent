@echo off
REM ======================================================================
REM GREYHOUND RACING PREDICTIONS - MAIN ENTRY POINT
REM ======================================================================
REM 
REM This is the main entry point for running predictions with the
REM track-specific ensemble models (BEST ACCURACY).
REM
REM Prerequisites:
REM   1. Models trained (run train_ml_track_ensemble.bat first)
REM   2. Race PDFs in data_predictions/ folder
REM
REM Output:
REM   - outputs/track_ensemble_predictions.xlsx
REM ======================================================================

echo.
echo ======================================================================
echo  GREYHOUND RACING PREDICTIONS - ENSEMBLE MODE
echo ======================================================================
echo.
echo  Running predictions with track-specific ensemble models...
echo  (BEST ACCURACY)
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
    echo Please copy today's race form PDFs to: data_predictions\
    echo Example: WENPG0203form.pdf
    echo.
    pause
    exit /b 1
)

echo Found %PDF_COUNT% race form PDF(s)
echo.

REM Call the track ensemble predictions script
call run_track_ensemble_predictions.bat

echo.
echo ======================================================================
echo  COMPLETE!
echo ======================================================================
echo.
echo  Check outputs\track_ensemble_predictions.xlsx for results
echo.

pause
