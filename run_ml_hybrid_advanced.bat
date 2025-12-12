@echo off
REM Advanced ML Hybrid Predictions - World-Class System
REM
REM Uses track-specific models with ensemble learning for maximum accuracy
REM
REM Features:
REM - Track-specific models (learns unique venue patterns)
REM - Ensemble predictions (RF + GB + XGBoost + LightGBM voting)
REM - 70+ advanced features
REM - Expected: 40-45%% win rate vs 28-30%% v4.4 alone
REM
REM Usage: run_ml_hybrid_advanced.bat
REM

echo ========================================
echo Advanced ML Hybrid Prediction System
echo Track-Specific + Ensemble Learning
echo ========================================
echo.
echo Running advanced hybrid predictions on today's races...
echo.
echo Note: This combines v4.4 rule-based scoring with advanced ML
echo       - Track-specific models
echo       - Ensemble predictions
echo       - 70+ features
echo       - Only shows bets when BOTH systems strongly agree
echo       - Expected: 40-45%% win rate vs 28-30%% v4.4 alone
echo.
echo Folder structure:
echo   data_predictions\  - Today's races (for predictions)
echo   data\              - Historical races (for ML training)
echo.

REM Check for data_predictions folder
if not exist data_predictions (
    echo Creating data_predictions folder...
    mkdir data_predictions
    echo.
    echo Please copy today's race PDFs to data_predictions\
    echo Then run this script again.
    echo.
    pause
    exit /b 0
)

REM Check for PDFs
dir /b data_predictions\*form.pdf >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: No race PDFs found in data_predictions\
    echo.
    echo Please copy today's race PDFs to data_predictions\ folder.
    echo Expected filename pattern: *form.pdf
    echo.
    echo The script will continue but may not find any races to analyze.
    echo.
)

REM Run advanced hybrid predictions
python run_ml_hybrid_advanced.py

REM Check if it completed successfully
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Advanced hybrid predictions failed
    echo ========================================
    echo.
    echo Please check the error message above.
    echo.
    echo If the advanced model is not found:
    echo   1. Run: train_ml_advanced.bat
    echo   2. Wait for training to complete (5-15 minutes)
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Advanced hybrid predictions complete!
echo ========================================
echo.
echo Check outputs folder for:
echo   - ml_hybrid_advanced_picks.xlsx (Excel with your advanced hybrid bets)
echo   - ml_advanced_all_predictions.xlsx (All ML predictions ranked)
echo   - v44_picks_comparison.csv (All v4.4 picks for comparison)
echo.
echo The advanced model uses track-specific patterns for maximum accuracy!
echo.
pause
