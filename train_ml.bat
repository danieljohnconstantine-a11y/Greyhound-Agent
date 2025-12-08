@echo off
REM Greyhound Racing Prediction System - ML Training
REM Train the machine learning model on historical data

echo ========================================
echo ML Model Training - v1.0
echo ========================================
echo.

REM Check if required files exist
if not exist "train_ml_model.py" (
    echo ERROR: train_ml_model.py not found!
    pause
    exit /b 1
)

if not exist "data\" (
    echo ERROR: data folder not found!
    echo Please create a 'data' folder with historical race PDFs
    pause
    exit /b 1
)

echo Installing required packages...
pip install scikit-learn pandas numpy --quiet

echo.
echo Training ML model on historical data...
echo This may take a few minutes...
echo.

REM Train the model
python train_ml_model.py

if errorlevel 1 (
    echo.
    echo ERROR: Training failed!
    echo Please check the error messages above
    pause
    exit /b 1
)

REM Verify the model file was actually created
if not exist "models\greyhound_ml_v1.pkl" (
    echo.
    echo ========================================
    echo WARNING: Training script completed but model file not found!
    echo ========================================
    echo.
    echo Expected location: models\greyhound_ml_v1.pkl
    echo Current directory: %CD%
    echo.
    echo Please check the training output above for errors.
    echo The script may have encountered an issue during the save step.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Training complete!
echo Model saved to: models\greyhound_ml_v1.pkl
echo ========================================
echo.
pause
