# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms with machine learning predictions.

## Complete Pipeline Structure

```
├── RUN.bat                 # Run predictions (Windows)
├── TRAIN.sh               # Train models (Ubuntu)
├── main.py                # Entry point for predictions
├── requirements.txt       # Python dependencies
├── src/                   # All Python modules
│   ├── config.py
│   ├── parser.py
│   ├── features.py
│   ├── exporter.py
│   ├── extract.py
│   ├── utils.py
│   └── main.py           # Training functions
├── data/                  # Historical PDFs for training
├── data_predictions/      # Today's PDFs for predictions
├── models/                # Trained model files (.pkl)
└── outputs/               # Prediction results
```

## Usage

### Step 1: Training (Ubuntu)
Train ML models on historical data:
```bash
bash TRAIN.sh
```
This will:
- Install dependencies from requirements.txt
- Process all PDFs in data/ folder
- Train models for each track
- Save models to models/ directory

### Step 2: Daily Predictions (Windows)
Run predictions on today's races:
1. Place today's race form PDFs in `data_predictions/` folder
2. Double-click `RUN.bat`

This will:
- Load trained models from models/ directory
- Process PDFs in data_predictions/ folder
- Generate predictions
- Save results to outputs/ directory

## Output Files
- `outputs/todays_form.csv`: Parsed race data
- `outputs/ranked.csv`: Scored dogs
- `outputs/picks.csv`: Top betting picks

## Requirements
- Python 3.7+
- Dependencies listed in requirements.txt
