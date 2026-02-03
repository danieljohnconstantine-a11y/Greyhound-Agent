@echo off
echo ================================================================================
echo COMPLETE ANALYSIS PIPELINE - ONE-CLICK SOLUTION
echo ================================================================================
echo.
echo This will:
echo   1. Analyze all PDFs in data_predictions/ folder
echo   2. Generate ML v2.1 predictions with weather/track conditions
echo   3. Create all reports including detailed feature analysis
echo   4. Sort feature analysis by Track -^> Race -^> Box
echo.
echo Output files:
echo   - ml_enhanced_all_predictions.xlsx (ALL dogs with ML scores)
echo   - ml_hybrid_enhanced_picks.xlsx (High-confidence picks)
echo   - v44_picks_comparison.csv (v4.4 picks comparison)
echo   - ml_feature_analysis_detailed.xlsx (Detailed features, sorted)
echo   - complete_analysis_summary.txt (Quick summary)
echo.
echo ================================================================================
echo.
pause

python run_complete_analysis.py

echo.
echo ================================================================================
echo COMPLETE! Check outputs/ folder for all reports
echo ================================================================================
pause
