# ML Training and Prediction Showcase

This branch contains the complete ML training and prediction infrastructure for greyhound racing analysis.

## Contents

### Training Scripts
- **train_ml_track_ensemble.py** (618 lines) - Python script for training track-specific ensemble models
- **train_ml_track_ensemble.bat** - Batch file to run the training script

### Prediction Scripts
- **run_track_ensemble_predictions.py** (463 lines) - Python script for running predictions using trained models
- **run_track_ensemble_predictions.bat** - Batch file to run predictions

### Data Organization
- **ORGANIZE_ALL_TRACKS.bat** - Utility script for organizing race data by track

### Data Folders

#### data/ (719 files)
Contains historical race data:
- Race form PDFs from multiple tracks (Nov 2025 - Jan 2026)
- Results CSV files with race outcomes
- Track and weather condition data

#### data_predictions/ (12 files)
Contains prediction input PDFs for recent races across various tracks including:
- CAPAG, DRWNG, GRAFG, HEALG, MBRGG, MTGG, QPRKG, RICHG, ROCKG, SALEG, WENPG

#### models/ (15 files)
Pre-trained ensemble models for two tracks:

**SALE Track:**
- rf.pkl - Random Forest model
- gb.pkl - Gradient Boosting model
- xgb.pkl - XGBoost model
- scaler.pkl - Feature scaler
- metadata.json - Model metadata
- training_metrics.json - Performance metrics

**WENTWORTH PARK Track:**
- rf.pkl - Random Forest model
- gb.pkl - Gradient Boosting model
- xgb.pkl - XGBoost model
- scaler.pkl - Feature scaler
- metadata.json - Model metadata
- training_metrics.json - Performance metrics

**Configuration:**
- ensemble_config.json - Ensemble configuration
- config.pkl - Model configuration

## Usage

1. **Training Models**: Run `train_ml_track_ensemble.bat` to train new models for specific tracks
2. **Making Predictions**: Run `run_track_ensemble_predictions.bat` to generate predictions using trained models
3. **Data Organization**: Run `ORGANIZE_ALL_TRACKS.bat` to organize race data files

## Model Architecture

The system uses an ensemble approach combining three different algorithms:
- Random Forest (RF)
- Gradient Boosting (GB)
- XGBoost (XGB)

Each model is trained on track-specific data and uses calibrated probability predictions for optimal accuracy.
