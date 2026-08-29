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
- HEALESVILLE: `HEALESVILLE_rf.pkl`, `HEALESVILLE_gb.pkl`, `HEALESVILLE_xgb.pkl`, `HEALESVILLE_scaler.pkl`
- Maitland: `Maitland_rf.pkl`, `Maitland_gb.pkl`, `Maitland_xgb.pkl`, `Maitland_scaler.pkl`
- SHEPPARTON: `SHEPPARTON_rf.pkl`, `SHEPPARTON_gb.pkl`, `SHEPPARTON_xgb.pkl`, `SHEPPARTON_scaler.pkl`

## Known Issues (Mar 2026 Audit)

The RF models for HEALESVILLE, Maitland, and SHEPPARTON have broken isotonic
calibration — the calibration lookup table maps all real-world RF probabilities
(range 0.10–0.36) to a single constant value, making all dogs score identically.

The same flat-mapping affects:
- GB: Maitland (near-flat, spread 0.8%) and SHEPPARTON (near-flat, spread 1.3%)
- XGB: SHEPPARTON (2 unique values out of 8)

**This does NOT break predictions** because `run_track_ensemble_predictions.py`
contains an automatic fallback guard that detects calibration collapse and falls
back to the uncalibrated base estimator predictions (which show 7–18% spread).

**To permanently fix**: retrain all 3 tracks with `method='sigmoid'` instead of
`method='isotonic'` in `CalibratedClassifierCV`. Sigmoid (Platt scaling) does
not produce flat mappings on sparse win-event datasets.

See `reports/MODEL_AUDIT_2026-03-10.txt` for the full audit report.

## Configuration Files
- `config.pkl` - Ensemble configuration (pickle format)
- `ensemble_config.json` - Ensemble configuration (JSON format, human-readable)

## Training New Models

Use the sigmoid retraining flow:

```bash
python retrain_all_tracks_sigmoid.py
```

Or on Ubuntu:

```bash
bash train_ubuntu.sh
```

Do **not** use `train_ml_track_ensemble.py` / `train_ml_track_ensemble.bat` (obsolete isotonic flow).
