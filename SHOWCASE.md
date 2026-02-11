# ML Training and Prediction Showcase

This branch contains the complete ML training and prediction infrastructure for greyhound racing analysis, including source code, prediction outputs, and trained models.

## Contents

### Training Scripts
- **train_ml_track_ensemble.py** (618 lines) - Python script for training track-specific ensemble models
- **train_ml_track_ensemble.bat** - Batch file to run the training script

### Prediction Scripts
- **run_track_ensemble_predictions.py** (463 lines) - Python script for running predictions using trained models
- **run_track_ensemble_predictions.bat** - Batch file to run predictions

### Data Organization
- **ORGANIZE_ALL_TRACKS.bat** - Utility script for organizing race data by track

### Source Code (src/ folder - 12 files)
Complete Python codebase for ML prediction and analysis:
- **bet_worthy.py** (30KB) - Betting analysis and recommendation logic
- **excel_export.py** - Excel output functionality
- **excel_formatter.py** - Excel formatting and styling utilities
- **feature_engineering_enhanced.py** (22KB) - Advanced feature engineering
- **features.py** (104KB) - Core feature extraction and processing
- **immediate_fix_scorer.py** - Quick scoring fixes and adjustments
- **ml_optimization_phases.py** - ML model optimization logic
- **ml_predictor.py** (50KB) - Basic ML prediction engine
- **ml_predictor_advanced.py** (32KB) - Advanced ML prediction with ensemble methods
- **parser.py** (43KB) - Data parsing utilities for race forms
- **scorer.py** - Scoring algorithms
- **weather_track_data.py** (16KB) - Weather and track data handling

### Prediction Outputs (outputs/ folder - 24 files)
Generated predictions and analysis results:

**By Track Analysis:**
- BALLARAT/ - details.json, predictions.xlsx, summary.txt
- Maitland/ - details.json, predictions.xlsx, summary.txt
- NOWRA/ - details.json, predictions.xlsx, summary.txt
- Q STRAIGHT/ - details.json, predictions.xlsx, summary.txt
- SANDOWN/ - details.json, predictions.xlsx, summary.txt
- SHEPPARTON/ - details.json, predictions.xlsx, summary.txt

**Combined Analysis:**
- all_tracks_predictions.xlsx - Consolidated predictions across all tracks
- all_tracks_summary.txt - Summary statistics for all tracks

**Validation & Reports:**
- pipeline_validation_report.json - Pipeline validation metrics
- track_ensemble_predictions.xlsx - Ensemble prediction results
- track_ensemble_summary.txt - Ensemble summary statistics

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
4. **Source Code**: Use modules in `src/` folder for custom analysis and integration
5. **View Results**: Check `outputs/` folder for generated predictions and analysis reports

## Model Architecture

The system uses an ensemble approach combining three different algorithms:
- Random Forest (RF)
- Gradient Boosting (GB)
- XGBoost (XGB)

Each model is trained on track-specific data and uses calibrated probability predictions for optimal accuracy.

## Complete File Inventory

**Total Files: ~790**
- 719 data files (race PDFs and CSVs)
- 12 prediction input PDFs
- 15 model files (SALE and WENTWORTH PARK)
- 24 output files (predictions and reports)
- 12 source code files
- 4 training/prediction scripts
- 1 utility script
- 2 documentation files
