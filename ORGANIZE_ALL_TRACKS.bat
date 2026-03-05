@echo off
REM ============================================================
REM ORGANIZE ALL TRACKS - Greyhound Agent
REM ============================================================
REM 
REM This script organizes all 49 tracks into subdirectories
REM with training metrics and metadata.
REM 
REM Time: ~5 minutes
REM Run once after training completes
REM 
REM ============================================================

echo.
echo ============================================================
echo ORGANIZE ALL TRACKS - GREYHOUND AGENT
echo ============================================================
echo.
echo This will organize all 49 tracks into subdirectories.
echo.
echo Current: Flat files in models/ root
echo Result:  models/TRACK_NAME/ subdirectories
echo.
echo Time: Approximately 5 minutes
echo.
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [STEP 1/3] Reorganizing models by track...
echo.
python reorganize_models_by_track.py
if errorlevel 1 (
    echo [ERROR] Failed to reorganize models
    pause
    exit /b 1
)
echo [OK] Models reorganized
echo.

echo [STEP 2/3] Adding training metrics for all tracks...
echo.
python add_training_metrics.py
if errorlevel 1 (
    echo [ERROR] Failed to add training metrics
    pause
    exit /b 1
)
echo [OK] Training metrics added
echo.

echo [STEP 3/3] Validating pipeline organization...
echo.
python validate_pipeline.py
if errorlevel 1 (
    echo [WARNING] Validation found issues
    echo Check outputs/pipeline_validation_report.json for details
)
echo [OK] Validation complete
echo.

echo ============================================================
echo ORGANIZATION COMPLETE
echo ============================================================
echo.
echo All 49 tracks now have:
echo   - Organized subdirectories (models/TRACK_NAME/)
echo   - Training metrics (training_metrics.json)
echo   - Metadata files (metadata.json)
echo.
echo Check outputs/pipeline_validation_report.json for full report.
echo.
echo ============================================================
pause
