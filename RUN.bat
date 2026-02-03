@echo off
REM ======================================================================
REM DAILY PREDICTIONS - Get today's predictions
REM ======================================================================
echo.
echo ======================================================================
echo GREYHOUND RACING PREDICTIONS - TODAY
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
echo Running predictions...
echo.

REM Use existing run_predictions_today.bat which calls main.py
python main.py data_predictions\*.pdf

echo.
echo ======================================================================
echo PREDICTIONS COMPLETE!
echo ======================================================================
echo.
echo Check the outputs\ folder for results
echo Look for HIGH CONFIDENCE races to bet on!
echo.
pause
