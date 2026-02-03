@echo off
REM Navigate to project root
cd /d "%~dp0"

REM Run the main pipeline
python main.py

REM Pause to show output
pause
