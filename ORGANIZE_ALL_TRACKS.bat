@echo off
REM ==========================================================================
REM ORGANIZE_ALL_TRACKS.bat
REM Full pipeline organiser and validator for all track models
REM
REM What this script does:
REM   1. Validates that all model files exist and are loadable
REM   2. Trains XGB models for any track that is missing one
REM   3. Runs the full prediction pipeline validation
REM   4. Generates a pipeline health report
REM
REM Usage:
REM   ORGANIZE_ALL_TRACKS.bat
REM   ORGANIZE_ALL_TRACKS.bat --track "Angle Park"
REM ==========================================================================

setlocal enabledelayedexpansion

echo.
echo ===================================================================
echo  GREYHOUND ML PIPELINE - ORGANISE ALL TRACKS
echo  %DATE% %TIME%
echo ===================================================================
echo.

REM ── Check Python is available ────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    where python3 >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python not found. Please install Python 3.8+ and try again.
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

echo [INFO] Using: %PYTHON%
echo.

REM ── Check required script files ──────────────────────────────────────
set MISSING_SCRIPTS=0
for %%F in (validate_pipeline.py predict_race.py src\pdf_parser.py src\race_features.py) do (
    if not exist "%%F" (
        echo [ERROR] Required script not found: %%F
        set MISSING_SCRIPTS=1
    )
)

if %MISSING_SCRIPTS% neq 0 (
    echo.
    echo [ERROR] One or more required scripts are missing. 
    echo         Please ensure the full pipeline is installed.
    exit /b 1
)

echo [INFO] All required scripts found.
echo.

REM ── Step 1: Validate all track models ─────────────────────────────────
echo -------------------------------------------------------------------
echo  STEP 1: Validating track model files
echo -------------------------------------------------------------------
echo.

set TRACKS=Angle Park BALLARAT BENDIGO
for %%T in (%TRACKS%) do (
    echo Checking models for: %%T
    for %%A in (rf gb xgb scaler) do (
        if exist "%%T_%%A.pkl" (
            echo   [OK]  %%T_%%A.pkl
        ) else (
            if "%%A"=="xgb" (
                echo   [MISSING - will train] %%T_%%A.pkl
            ) else (
                echo   [MISSING] %%T_%%A.pkl
            )
        )
    )
    echo.
)

REM ── Step 2: Train missing XGB models ─────────────────────────────────
echo -------------------------------------------------------------------
echo  STEP 2: Training missing XGB models
echo -------------------------------------------------------------------
echo.

set TRAINED_ANY=0
for %%T in ("Angle Park" BALLARAT BENDIGO) do (
    if not exist "%%~T_xgb.pkl" (
        echo Training XGB for: %%~T
        %PYTHON% train_xgb_for_track.py %%~T
        if %errorlevel% equ 0 (
            set TRAINED_ANY=1
        ) else (
            echo   [WARNING] XGB training failed for %%~T
        )
    )
)

if %TRAINED_ANY%==0 (
    echo [INFO] All XGB models already present.
)
echo.

REM ── Step 3: Run pipeline validation ──────────────────────────────────
echo -------------------------------------------------------------------
echo  STEP 3: Full pipeline validation
echo -------------------------------------------------------------------
echo.

%PYTHON% validate_pipeline.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Pipeline validation reported issues. Check output above.
) else (
    echo [INFO] Pipeline validation completed.
)
echo.

REM ── Step 4: Summary ──────────────────────────────────────────────────
echo -------------------------------------------------------------------
echo  STEP 4: Pipeline Summary
echo -------------------------------------------------------------------
echo.
echo  Model files:
for %%T in ("Angle Park" BALLARAT BENDIGO) do (
    set TRACK_OK=1
    for %%A in (rf gb scaler) do (
        if not exist "%%~T_%%A.pkl" set TRACK_OK=0
    )
    if !TRACK_OK!==1 (
        echo    [READY]   %%~T
    ) else (
        echo    [MISSING] %%~T
    )
)

echo.
echo  To run predictions:
echo    %PYTHON% predict_race.py --pdf data\ANGLG0112form.pdf --race 8 --dist 530 --track "Angle Park"
echo.
echo  To validate:
echo    %PYTHON% validate_pipeline.py
echo.
echo ===================================================================
echo  ORGANIZE_ALL_TRACKS complete — %DATE% %TIME%
echo ===================================================================
echo.

endlocal
