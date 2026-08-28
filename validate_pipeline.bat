@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo  PIPELINE VALIDATION
echo ============================================================
echo.
python validate_pipeline.py
if errorlevel 1 (
  echo.
  echo [FAIL] Validation found issues. See outputs\pipeline_validation_report.json
  pause
  exit /b 1
)
echo.
echo [PASS] Pipeline validation succeeded.
pause
