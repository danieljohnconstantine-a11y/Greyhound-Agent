@echo off
REM Train Track-Specific Ensemble Models - Option C Implementation
REM 
REM This trains multiple models for improved accuracy:
REM - 3 algorithms (RandomForest, GradientBoosting, XGBoost) per track
REM - Separate models for each track (venue-specific patterns)
REM - Expected: 8-12% accuracy improvement over baseline
REM
REM Duration: 5-15 minutes depending on data size
REM Output: models/track_ensemble/ folder with all trained models

echo.
echo ================================================================================
echo  TRACK-SPECIFIC ENSEMBLE MODEL TRAINING - Option C
echo ================================================================================
echo.
echo  This will train improved ML models with:
echo    - Separate models per track (venue-specific patterns)
echo    - 3 algorithms per track: RandomForest + GradientBoosting + XGBoost
echo    - Ensemble averaging for best predictions
echo.
echo  Expected improvement: 8-12%% better accuracy
echo  Training time: 5-15 minutes
echo.
echo ================================================================================
echo.
pause

python train_ml_track_ensemble.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo  TRAINING COMPLETE!
    echo ================================================================================
    echo.
    echo  Models saved to: models/track_ensemble/
    echo.
    echo  Next step: Run predictions on today's races
    echo    run_track_ensemble_predictions.bat
    echo.
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo  ERROR - Training failed with error code %ERRORLEVEL%
    echo ================================================================================
    echo.
)

pause
