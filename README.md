# Greyhound Racing Predictions

## Quick Start

### Run Predictions (Best Accuracy)
1. Put today's race PDFs in `data_predictions/` folder
2. Double-click `RUN_ENSEMBLE.bat`
3. Check results in `outputs/track_ensemble_predictions.xlsx`

### Retrain Models (Optional)
1. Put historical PDFs in `data/` folder
2. Double-click `train_ml_track_ensemble.bat`
3. Wait 30-60 minutes

## Requirements
- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`

## Folder Structure
```
├── RUN_ENSEMBLE.bat              Main entry point
├── run_track_ensemble_predictions.py
├── train_ml_track_ensemble.py
├── main.py
├── src/                          Source code
├── models/                       Trained models
├── data/                         Historical data
├── data_predictions/             Today's races
└── outputs/                      Results
```

## Support
See PROJECT_GOAL.md for technical details.
