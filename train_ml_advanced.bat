@echo off
REM Train Advanced ML Model - World-Class Prediction System
REM
REM This trains track-specific models with ensemble learning
REM for maximum accuracy. Takes 5-15 minutes depending on data size.
REM
REM Features:
REM - Track-specific models (learns venue patterns)
REM - Hyperparameter optimization 
REM - Ensemble: RF + GradientBoosting + XGBoost + LightGBM
REM - 70+ advanced features
REM - Expected: 40-45%% win rate when combined with v4.4
REM
REM Usage: train_ml_advanced.bat
REM

echo ========================================
echo Advanced ML Training - World-Class System
echo ========================================
echo.
echo This will train track-specific models with:
echo   - Hyperparameter optimization
echo   - Ensemble learning (multiple algorithms)
echo   - 70+ advanced features
echo   - Track-specific patterns
echo.
echo Estimated time: 5-15 minutes
echo.
pause

echo.
echo ========================================
echo Starting training...
echo ========================================
echo.

REM Run training script
python train_ml_advanced.py

REM Check if training succeeded
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Training failed
    echo ========================================
    echo.
    echo Please check the error message above.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Training Complete!
echo ========================================
echo.
echo Advanced model saved to: models/greyhound_ml_v2_advanced.pkl
echo.
echo You can now use this model with run_ml_hybrid_today.bat
echo or run_ml_hybrid_advanced.bat for best results.
echo.
echo The advanced model should give 40-45%% win rate when
echo combined with v4.4 rule-based scoring.
echo.
pause
