@echo off
REM Run Optimized ML Predictions for 50%+ Win Rate
REM 
REM This script uses optimized ML confidence thresholds based on backtest
REM analysis to achieve maximum win rate.
REM
REM Prerequisites:
REM   1. Trained ML v2.1 model (run train_ml_enhanced.bat first)
REM   2. Run backtest_analyze.py first to find optimal thresholds
REM   3. Race PDFs in data_predictions/ folder
REM
REM Usage:
REM   run_ml_optimized.bat                    (Use default settings)
REM   run_ml_optimized.bat 60 10              (Custom threshold and spread)
REM   run_ml_optimized.bat 65 15 2            (With top-N selection)

echo.
echo ================================================================================
echo OPTIMIZED ML PREDICTION SYSTEM - Targeting 50%+ Win Rate
echo ================================================================================
echo.

REM Check if arguments provided
if "%1"=="" (
    echo Using DEFAULT settings:
    echo   ML Confidence Threshold: 60%%
    echo   Minimum Confidence Spread: 10 percentage points
    echo   Selection Mode: Top 1 per race
    echo.
    python run_ml_optimized.py --threshold 60 --min-spread 10
) else if "%3"=="" (
    echo Using CUSTOM settings:
    echo   ML Confidence Threshold: %1%%
    echo   Minimum Confidence Spread: %2 percentage points
    echo   Selection Mode: Top 1 per race
    echo.
    python run_ml_optimized.py --threshold %1 --min-spread %2
) else (
    echo Using CUSTOM settings:
    echo   ML Confidence Threshold: %1%%
    echo   Minimum Confidence Spread: %2 percentage points
    echo   Selection Mode: Top %3 per race
    echo.
    python run_ml_optimized.py --threshold %1 --min-spread %2 --top-n %3
)

echo.
echo ================================================================================
echo PREDICTIONS COMPLETE
echo ================================================================================
echo.
echo Check outputs folder for:
echo   - ml_optimized_picks.xlsx          (Optimized picks)
echo   - ml_optimized_all_predictions.xlsx (All predictions)
echo   - ml_optimized_report.txt          (Detailed report)
echo.
pause
