@echo off
REM Run Backtest Analysis to Find Optimal Thresholds for 50%+ Win Rate
REM 
REM This script analyzes historical predictions vs actual results to find
REM the best ML confidence threshold and settings to achieve 50%+ win rate.
REM
REM Prerequisites:
REM   1. Trained ML v2.1 model (run train_ml_enhanced.bat first)
REM   2. Historical race PDFs in data/ folder
REM   3. Results CSVs in data/ folder
REM
REM Output:
REM   outputs/backtest_analysis_report.txt - Full analysis with recommendations

echo.
echo ================================================================================
echo BACKTEST ANALYSIS - Finding Optimal Thresholds for 50%+ Win Rate
echo ================================================================================
echo.
echo This will test different ML confidence thresholds against historical data
echo to find the optimal settings for achieving 50%+ win rate.
echo.
echo NOTE: This analysis may take 5-10 minutes to complete.
echo.
pause

python backtest_analyze.py

echo.
echo ================================================================================
echo ANALYSIS COMPLETE
echo ================================================================================
echo.
echo Review the report at: outputs\backtest_analysis_report.txt
echo.
echo Next step: Use run_ml_optimized.bat with the recommended settings
echo.
pause
