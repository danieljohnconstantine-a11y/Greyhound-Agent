@echo off
REM Quick Test Training - 3 Tracks (Cannington, Dubbo, Wentworth Park)
REM This script tests the maiden race fixes with a small subset of tracks
REM Expected time: 5-10 minutes

echo ========================================
echo QUICK TEST TRAINING - 3 TRACKS
echo ========================================
echo.
echo Selected tracks for testing:
echo   1. Cannington (CANNG2401form.pdf)
echo   2. Dubbo (DUBBG2401form.pdf)
echo   3. Wentworth Park (WENPG2401form.pdf)
echo.
echo Expected time: 5-10 minutes
echo ========================================
echo.

REM Step 1: Create test directories
echo Step 1: Creating test directories...
if not exist data_test mkdir data_test
if not exist models\track_ensemble_test mkdir models\track_ensemble_test
echo   [OK] Test directories created
echo.

REM Step 2: Copy test PDFs
echo Step 2: Copying test PDFs...
if exist data_predictions\CANNG2401form.pdf (
    copy data_predictions\CANNG2401form.pdf data_test\ >nul
    echo   [OK] Copied Cannington PDF
) else (
    echo   [WARNING] Cannington PDF not found
)

if exist data_predictions\DUBBG2401form.pdf (
    copy data_predictions\DUBBG2401form.pdf data_test\ >nul
    echo   [OK] Copied Dubbo PDF
) else (
    echo   [WARNING] Dubbo PDF not found
)

if exist data_predictions\WENPG2401form.pdf (
    copy data_predictions\WENPG2401form.pdf data_test\ >nul
    echo   [OK] Copied Wentworth Park PDF
) else (
    echo   [WARNING] Wentworth Park PDF not found
)
echo.

REM Step 3: Copy CSV results
echo Step 3: Copying CSV results for training data...
copy data\results_2026-01-*.csv data_test\ >nul 2>&1
echo   [OK] CSV files copied
echo.

REM Step 4: Activate virtual environment and run training
echo Step 4: Starting training...
echo ========================================
echo.
echo WATCH FOR THESE MESSAGES:
echo   "⚠️ MAIDEN RACE - Using CareerStarts for differentiation"
echo   "⚠️ MAIDEN RACE (DLW='Mdn') - neutral DLWFactor"
echo.
echo If you see these messages, the fix is working!
echo ========================================
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    python train_quick_test_3tracks.py 2>&1 | tee test_training.log
    
    echo.
    echo ========================================
    echo TRAINING COMPLETE
    echo ========================================
    echo.
    echo Check test_training.log for maiden race messages
    echo Models saved to: models\track_ensemble_test\
    echo.
    
    REM Step 5: Run test predictions
    echo Step 5: Running test predictions...
    python predict_quick_test_3tracks.py
    
    echo.
    echo ========================================
    echo RESULTS
    echo ========================================
    echo.
    type outputs\test_predictions_summary.txt
    echo.
    
    call venv\Scripts\deactivate.bat
) else (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run this script again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo QUICK TEST COMPLETE
echo ========================================
echo.
echo Next steps:
echo   1. Check if scores VARY within each race
echo   2. If scores still identical - check test_training.log for maiden messages
echo   3. If fix working - run full training with train_ml_track_ensemble.bat
echo.
pause
