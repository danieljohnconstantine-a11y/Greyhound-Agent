# Track Ensemble Predictions Upload Folder

Place historical **track_ensemble_predictions Excel files** in this folder.

## Expected use
1. Manually copy all historical prediction spreadsheets into this folder.
2. Keep original file names if possible (date included is preferred).
3. Keep format as `track_ensemble_predictionsDDMMYYYY.xlsx` for automatic date matching.
4. Run your normal training command:
   - `python retrain_all_tracks_sigmoid.py`
5. The retrain flow now automatically:
   - builds per-track calibration profiles from this folder
   - compares candidate vs previous profiles with a promotion gate
   - only promotes updates when guardrails improve/hold
   - applies stronger recency/context weighting (30/60/90-day influence + distance/RTC context)
   - keeps historical edge patterns only when recent track regime still supports them
   - continues training with the active per-track profiles

## Notes
- This folder is only for prediction-history files (Excel).
- Existing daily prediction output/report formats do not need to change.
- Prediction selection now applies stricter confidence guardrails (low spread / tiny top-2 gap / model disagreement = low confidence).
- Calibration artifacts are written to `best_bets_reports/`:
  - `track_calibration_profiles_candidate.json`
  - `track_calibration_profiles.json` (active)
  - `TRACK_CALIBRATION_REPORT.md`
