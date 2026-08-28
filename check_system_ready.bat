@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo  SYSTEM READY CHECK
echo ============================================================
echo.
python check_system_ready.py
if errorlevel 1 (
  echo.
  echo [NO-GO] Issues found. See reports\SYSTEM_READY_CHECK_*.txt
  pause
  exit /b 1
)
echo.
echo [GO] System/data checks passed.
pause
