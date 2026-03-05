# Models Directory

This directory contains pre-trained track-specific ensemble models for greyhound race prediction.

## Model Files

Flat-file layout: `{Track Name}_{algorithm}.pkl`

### Algorithms
- `rf` - Random Forest
- `gb` - Gradient Boosting
- `xgb` - XGBoost
- `scaler` - StandardScaler for feature normalisation

### Available Tracks
- Angle Park: `Angle Park_rf.pkl`, `Angle Park_gb.pkl`, `Angle Park_scaler.pkl`
- BALLARAT: `BALLARAT_rf.pkl`, `BALLARAT_gb.pkl`, `BALLARAT_scaler.pkl`
- BENDIGO: `BENDIGO_rf.pkl`, `BENDIGO_gb.pkl`, `BENDIGO_scaler.pkl`

## Configuration Files
- `config.pkl` - Ensemble configuration (pickle format)
- `ensemble_config.json` - Ensemble configuration (JSON format, human-readable)

## Training New Models

Run `train_ml_track_ensemble.py` to retrain models on new historical data:

```
python train_ml_track_ensemble.py
```

Or use the batch file on Windows:
```
train_ml_track_ensemble.bat
```
