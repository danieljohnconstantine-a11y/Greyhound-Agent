@echo off
REM ############################################################################
REM Package Installation Script for Unstable Internet Connections (Windows)
REM 
REM This script installs Python packages with extended timeouts and retry logic
REM Designed for users with slow or unstable internet connections
REM
REM Usage: install_packages.bat
REM ############################################################################

setlocal enabledelayedexpansion

REM Configuration
set TIMEOUT=300
set RETRIES=10
set MAX_ATTEMPTS=5

REM Package list
set PACKAGES=pandas numpy scikit-learn xgboost pdfplumber openpyxl

echo ================================================================
echo   Package Installation Script for Unstable Connections
echo ================================================================
echo.

REM Check if in virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo WARNING: No virtual environment detected
    echo It's recommended to use a virtual environment
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        echo Installation cancelled.
        exit /b 1
    )
)

REM Configure pip
echo Configuring pip with extended timeouts (%TIMEOUT% seconds^)...
pip config set --user global.timeout %TIMEOUT% >nul 2>&1

echo Configuring pip with increased retries (%RETRIES% retries^)...
pip config set --user global.retries %RETRIES% >nul 2>&1

echo Configuration complete!
echo.

REM Install packages
echo Installing packages one-by-one with retry logic...
echo.

set INSTALLED_COUNT=0
set FAILED_COUNT=0
set FAILED_LIST=

set PKG_NUM=0
for %%P in (%PACKAGES%) do (
    set /a PKG_NUM+=1
    echo --------------------------------------------------------
    echo Installing package !PKG_NUM!/6: %%P
    echo --------------------------------------------------------
    
    set SUCCESS=0
    for /L %%A in (1,1,%MAX_ATTEMPTS%) do (
        if !SUCCESS!==0 (
            echo Attempt %%A/%MAX_ATTEMPTS%: pip install --timeout %TIMEOUT% %%P
            
            pip install --timeout %TIMEOUT% --retries %RETRIES% %%P >nul 2>&1
            if !errorlevel!==0 (
                echo [SUCCESS] Installed %%P
                set SUCCESS=1
                set /a INSTALLED_COUNT+=1
            ) else (
                echo [FAILED] Attempt %%A failed
                if %%A LSS %MAX_ATTEMPTS% (
                    echo Waiting 5 seconds before retry...
                    timeout /t 5 /nobreak >nul
                )
            )
        )
    )
    
    if !SUCCESS!==0 (
        echo [ERROR] Failed to install %%P after %MAX_ATTEMPTS% attempts
        set /a FAILED_COUNT+=1
        if "!FAILED_LIST!"=="" (
            set FAILED_LIST=%%P
        ) else (
            set FAILED_LIST=!FAILED_LIST! %%P
        )
    )
    
    echo.
)

REM Print summary
echo ================================================================
echo   Installation Summary
echo ================================================================

for %%P in (%PACKAGES%) do (
    echo !FAILED_LIST! | find "%%P" >nul 2>&1
    if errorlevel 1 (
        echo [OK] %%P - Installed successfully
    ) else (
        echo [FAIL] %%P - Failed to install
    )
)

echo.

if %FAILED_COUNT%==0 (
    echo Success: All 6 packages installed!
    echo.
    echo Next steps:
    echo 1. Verify installation:
    echo    python -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl; print('All packages work!'^)"
    echo.
    echo 2. Run the prediction system:
    echo    python run_track_ensemble_predictions.py
    echo.
    exit /b 0
) else (
    echo Warning: %FAILED_COUNT% package(s^) failed to install
    echo Failed packages: %FAILED_LIST%
    echo.
    echo Troubleshooting:
    echo 1. Check your internet connection
    echo 2. Try again later (different time of day^)
    echo 3. Install failed packages individually:
    for %%P in (%FAILED_LIST%) do (
        echo    pip install --timeout 600 --retries 20 %%P
    )
    echo.
    echo 4. See PIP_INSTALL_TIMEOUT_SOLUTION.md for more options
    echo.
    exit /b 1
)
