@echo off
REM Run Predictions with Track-Specific Ensemble Models
REM 
REM Uses the track-specific ensemble models to generate predictions
REM on today's races in data_predictions/ folder
REM
REM Prerequisites:
REM   1. Models trained (run train_ml_track_ensemble.bat first)
REM   2. Race PDFs in data_predictions/ folder
REM
REM Output:
REM   - outputs/track_ensemble_predictions.xlsx
REM   - outputs/track_ensemble_summary.txt

echo.
echo ================================================================================
echo  TRACK-SPECIFIC ENSEMBLE PREDICTIONS
echo ================================================================================
echo.
echo  This will generate predictions using:
echo    - Track-specific ensemble models
echo    - RandomForest + GradientBoosting + XGBoost per track
echo    - Averaged predictions for highest accuracy
echo.
echo  Input: PDFs in data_predictions/ folder
echo  Output: Excel file with predictions in outputs/ folder
echo.
echo ================================================================================
echo.
echo Checking Python packages...
echo.

REM Check if required packages are installed
python -c "import xgboost" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    echo This may take a few minutes...
    echo.
    pip install --upgrade scikit-learn==1.8.0 xgboost pandas numpy pdfplumber
    echo.
)

REM Verify scikit-learn version
python -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')"
echo.

pause

python run_track_ensemble_predictions.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo  PREDICTIONS COMPLETE!
    echo ================================================================================
    echo.
    echo  Check outputs/ folder for:
    echo    - track_ensemble_predictions.xlsx
    echo    - track_ensemble_summary.txt
    echo.
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo  ERROR - Prediction failed with error code %ERRORLEVEL%
    echo ================================================================================
    echo.
)

pause
