@echo off
REM Greyhound Racing Prediction System - Setup
REM Install all required dependencies

echo ========================================
echo Greyhound Prediction System Setup
echo ========================================
echo.

echo Installing required Python packages...
echo This may take a few minutes...
echo.

pip install --upgrade pip
pip install scikit-learn pandas numpy PyPDF2 tabulate

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    echo Please make sure Python and pip are installed correctly
    pause
    exit /b 1
)

REM Create required folders
if not exist "data\" mkdir data
if not exist "models\" mkdir models
if not exist "output\" mkdir output

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Created folders:
echo   - data\     (place race PDFs here)
echo   - models\   (ML models saved here)
echo   - output\   (prediction results saved here)
echo.
echo Next steps:
echo 1. Add race PDFs to the data\ folder
echo 2. Run run_predictions.bat for v4.4 predictions
echo 3. Run train_ml.bat to train ML model (optional)
echo 4. Run run_ml_hybrid.bat for hybrid predictions (optional)
echo.
pause
