@echo off
REM ========================================
REM FULLY AUTOMATED SETUP AND TEST
REM ========================================
REM This script does EVERYTHING automatically:
REM 1. Checks Python installation
REM 2. Creates virtual environment
REM 3. Installs all dependencies
REM 4. Runs the 3-track test
REM 5. Analyzes results
REM No manual intervention needed!
REM ========================================

cd /d "%~dp0"
echo.
echo ============================================================
echo AUTOMATED SETUP AND TEST - GREYHOUND AGENT
echo ============================================================
echo.
echo This will:
echo   1. Check Python installation
echo   2. Create/update virtual environment
echo   3. Install all dependencies automatically
echo   4. Run 3-track test (Cannington, Dubbo, Wentworth Park)
echo   5. Display results
echo.
echo Expected time: 10-15 minutes (first run)
echo               5-10 minutes (subsequent runs)
echo.
echo ============================================================
echo.

REM Step 1: Check Python
echo [STEP 1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo [ERROR] Python not found!
    echo ========================================
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
echo   [OK] Python found
python --version
echo.

REM Step 2: Create/check virtual environment
echo [STEP 2/6] Setting up virtual environment...
if not exist "venv\" (
    echo   Creating new virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to create virtual environment!
        echo.
        pause
        exit /b 1
    )
    echo   [OK] Virtual environment created
) else (
    echo   [OK] Virtual environment already exists
)
echo.

REM Step 3: Activate virtual environment
echo [STEP 3/6] Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to activate virtual environment!
    echo.
    pause
    exit /b 1
)
echo   [OK] Virtual environment activated
echo.

REM Step 4: Install/update dependencies
echo [STEP 4/6] Installing dependencies (this may take a few minutes)...
echo   This is a one-time process - subsequent runs will be faster.
echo.
pip install --quiet --upgrade pip
pip install --quiet pandas numpy xgboost scikit-learn pdfplumber
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo.
    pause
    exit /b 1
)
echo   [OK] All dependencies installed
echo.

REM Step 5: Run the quick test
echo [STEP 5/6] Running 3-track test...
echo ============================================================
echo.
echo Selected tracks for testing:
echo   1. Cannington (CANNG2401form.pdf)
echo   2. Dubbo (DUBBG2401form.pdf)
echo   3. Wentworth Park (WENPG2401form.pdf)
echo.
echo Expected time: 5-10 minutes
echo ============================================================
echo.

REM Create test directories and outputs folder
if not exist "data_test\" mkdir data_test
if not exist "models\track_ensemble_test\" mkdir models\track_ensemble_test
if not exist "outputs\" mkdir outputs

REM Copy test files
echo Copying test PDFs...
copy /Y data_predictions\CANNG2401form.pdf data_test\ >nul 2>&1
copy /Y data_predictions\DUBBG2401form.pdf data_test\ >nul 2>&1
copy /Y data_predictions\WENPG2401form.pdf data_test\ >nul 2>&1
copy /Y data\results_2026-01-*.csv data_test\ >nul 2>&1
echo   [OK] Test files copied
echo.

echo Starting training...
echo.
echo ========================================
echo WATCH FOR THESE MESSAGES:
echo   "WARNING MAIDEN RACE - Using CareerStarts for differentiation"
echo   "WARNING MAIDEN RACE (DLW='Mdn') - neutral DLWFactor"
echo.
echo If you see these messages, the fix is working!
echo ========================================
echo.

REM Run training and save output to outputs folder
python train_quick_test_3tracks.py > outputs\test_training_output.txt 2>&1

REM Check if training succeeded
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Training failed!
    echo.
    echo Error log:
    type outputs\test_training_output.txt
    echo.
    pause
    exit /b 1
)

echo.
echo   [OK] Training completed successfully!
echo.

REM Run predictions and save output to outputs folder
echo Running predictions...
python predict_quick_test_3tracks.py > outputs\test_predictions_output.txt 2>&1

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Predictions failed!
    echo.
    echo Error log:
    type outputs\test_predictions_output.txt
    echo.
    pause
    exit /b 1
)

echo   [OK] Predictions completed
echo.

REM Step 6: Display results
echo [STEP 6/6] Analyzing results...
echo ============================================================
echo.

REM Check for maiden race messages
findstr /C:"MAIDEN RACE" outputs\test_training_output.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo [CHECK 1] Maiden race detection: PASS
    echo   Found maiden race handling messages in training log
) else (
    echo [CHECK 1] Maiden race detection: WARNING
    echo   No maiden race messages found - may not have trained maiden races
)
echo.

REM Display predictions summary if it exists
if exist "outputs\test_predictions_summary.txt" (
    echo [CHECK 2] Prediction results:
    echo.
    type outputs\test_predictions_summary.txt
    echo.
) else (
    echo [CHECK 2] Prediction summary file not found
    echo.
)

echo ============================================================
echo.
echo TEST COMPLETE!
echo.
echo Output files saved to outputs folder:
echo   - outputs\test_training_output.txt (training log)
echo   - outputs\test_predictions_output.txt (prediction log)
echo   - outputs\test_predictions_summary.txt (results summary)
echo   - Models: models\track_ensemble_test\
echo.
echo ============================================================
echo.
echo NEXT STEPS:
echo.
echo If the test shows varied scores (e.g., 10%%, 18%%, 24%%, 32%%):
echo   SUCCESS! The fix is working. You can now train all tracks:
echo   1. Delete old models: del /Q models\track_ensemble\*.*
echo   2. Run: train_ml_track_ensemble.bat
echo.
echo If the test still shows identical scores (e.g., 14.5%%, 14.5%%, 14.5%%):
echo   Contact support with the outputs\test_training_output.txt file
echo.
echo ============================================================
echo.
pause
