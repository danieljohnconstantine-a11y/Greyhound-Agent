# Best Bets Reports Workspace

This folder stores artifacts used to tune training from historical `best_bets_report*.txt` files.

## Files
- `model_tuning_overrides.json` — RF/GB/XGB parameter overrides generated from report-vs-results performance.
- `tuning_summary.md` — human-readable summary of matched sample size and win rates.
- `best_bets_report_index.csv` — parsed race-level rows extracted from best-bets reports.

## Generate / Refresh tuning inputs

From repository root:

```bash
python generate_best_bets_tuning.py \
  --reports-dir best_bets_reports \
  --results-root . \
  --output-dir best_bets_reports
```

Then run training as normal:

```bash
python retrain_all_tracks_sigmoid.py
```

`train_ml_track_ensemble.py` will auto-load `best_bets_reports/model_tuning_overrides.json` when present.
