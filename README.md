# Greyhound Racing Predictions

## Quick Start (For Daily Use)

### 1. Get Today's Predictions (Recommended - Best Accuracy)
1. Put race PDFs in `data_predictions/` folder
2. Double-click `RUN_ENSEMBLE.bat`
3. Check results in `outputs/track_ensemble_predictions.xlsx`

### 2. Quick Testing Mode
1. Put race PDFs in `data_predictions/` folder  
2. Double-click `RUN_SIMPLE.bat`
3. Check results in `outputs/`

### 3. Retrain Models (Optional)
1. Put historical PDFs in `data/` folder
2. Double-click `TRAIN_MODELS.bat`
3. Wait 30-60 minutes

## What You Need
- Python 3.8+
- Race form PDFs from TAB

## Folder Structure
```
├── RUN_ENSEMBLE.bat         ⭐ Main entry point - Use this!
├── RUN_SIMPLE.bat           Quick testing mode
├── TRAIN_MODELS.bat         Retrain models
├── data/                    Historical PDFs for training
├── data_predictions/        Today's PDFs go here
├── outputs/                 Results appear here
├── models/                  Trained ML models
│   └── track_ensemble/      Track-specific models
└── src/                     Source code
```

## Need Help?
See PROJECT_GOAL.md for technical details.
