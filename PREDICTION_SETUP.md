# Prediction Setup Guide

## Issue: "ModuleNotFoundError: No module named 'xgboost'"

If you see this error when running predictions in Windows, it means the required Python packages are not installed in your Windows Python environment.

## Solution

### Option 1: Use the Updated Batch File (Easiest)

The `run_track_ensemble_predictions.bat` file has been updated to automatically install missing packages.

Simply run:
```
run_track_ensemble_predictions.bat
```

The script will:
1. Check if xgboost is installed
2. Install required packages if missing (scikit-learn 1.8.0, xgboost, pandas, numpy, pdfplumber)
3. Run predictions

### Option 2: Manual Installation

If you prefer to install packages manually:

```cmd
pip install --upgrade scikit-learn==1.8.0 xgboost pandas numpy pdfplumber
```

Then run predictions:
```
run_track_ensemble_predictions.bat
```

## Important Notes

### Package Version Compatibility

- **Training was done with scikit-learn 1.8.0** in Ubuntu
- **Windows must use the same version** to load models correctly
- The batch file automatically installs scikit-learn 1.8.0

### Why This Happens

When you trained models in Ubuntu (WSL), you installed packages in a **Linux virtual environment**.

Windows Python has its **own separate environment** that doesn't share packages with Ubuntu.

### Verification

After installation, verify packages are installed:

```cmd
python -c "import xgboost; import sklearn; print(f'xgboost: OK, sklearn: {sklearn.__version__}')"
```

Expected output:
```
xgboost: OK, sklearn: 1.8.0
```

## Running Predictions

### From Windows:
```
run_track_ensemble_predictions.bat
```

### From Ubuntu (WSL):
```bash
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
source venv/bin/activate
python run_track_ensemble_predictions.py
```

Both will work and use the same models from `models/track_ensemble/`.
