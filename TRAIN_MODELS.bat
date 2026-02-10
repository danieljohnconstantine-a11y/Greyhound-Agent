@echo off
REM ======================================================================
REM TRAIN MODELS - Track-Specific Ensemble Models
REM ======================================================================
REM
REM Run this once to train models, then use RUN_ENSEMBLE.bat daily.
REM Retraining is only needed when you have new historical data.
REM
REM ======================================================================

echo.
echo ======================================================================
echo TRAIN TRACK-SPECIFIC ENSEMBLE MODELS
echo ======================================================================
echo.
echo This will train ML models using historical race data.
echo.
echo Prerequisites:
echo   - Historical race PDFs in data/ folder
echo.
echo Training time: 5-15 minutes
echo Output: models/track_ensemble/
echo.
echo ======================================================================
echo.
pause

python train_ml_track_ensemble.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo TRAINING COMPLETE!
    echo ======================================================================
    echo.
    echo Models saved to: models/track_ensemble/
    echo.
    echo Next: Use RUN_ENSEMBLE.bat for daily predictions
    echo.
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo ERROR - Training failed with error code %ERRORLEVEL%
    echo ======================================================================
    echo.
)

pause
