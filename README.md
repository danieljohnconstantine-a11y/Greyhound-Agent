# Greyhound Analytics Pipeline

Automated ML-powered prediction of greyhound racing using trained models.

## ⚠️ IMPORTANT: You need today's form guide PDF

This pipeline **cannot predict races without the correct form guide PDF** for the race date
you want to predict. It will refuse to run on the wrong date's data.

### How to get the form guide PDF

For Angle Park on **05 Mar 2026** (as an example):

1. Download the form guide PDF from GRSA:
   - **https://www.grsa.com.au/racing/form-guides** (SA Racing — Angle Park)
   - **https://www.thedogs.com.au** (National, all tracks)

2. Save the PDF to the `data/` folder. The expected filename for Angle Park is:
   ```
   data/ANGLG{DD}{MM}form.pdf
   ```
   Example: `data/ANGLG0503form.pdf` for 05 March 2026.

3. Run the pipeline:
   ```bash
   python predict_race.py --dist 530 --race 8
   ```

### Current data in this repository

The `data/` folder currently contains form guides from **October–December 2025 only**.
These are historical/testing files. They cannot be used to predict today's races.

---

## Usage

```bash
# Predict today's Race 8 at Angle Park 530m (requires today's PDF in data/)
python predict_race.py --dist 530 --race 8

# Predict all 530m races (requires today's PDF)
python predict_race.py --dist 530

# Specify a different date (requires that date's PDF)
python predict_race.py --date 2026-03-05 --dist 530 --race 8

# Run on a historical PDF for testing (bypasses date check)
python predict_race.py --pdf data/ANGLG1112form.pdf --dist 530 --race 8 --force
```

## Output Files

Saved to `outputs/` after each run:

- `predictions.csv` — full per-dog ML predictions for the race(s) run
- `picks_ml.csv` — top-pick per race

## Models

Trained models are stored in the repository root:

| File | Description |
|------|-------------|
| `Angle Park_rf.pkl` | Random Forest classifier (Angle Park) |
| `Angle Park_gb.pkl` | Gradient Boosting classifier (Angle Park) |
| `Angle Park_scaler.pkl` | Feature scaler (Angle Park) |
| `BALLARAT_rf.pkl` | Random Forest classifier (Ballarat) |
| `BALLARAT_gb.pkl` | Gradient Boosting classifier (Ballarat) |
| `BALLARAT_scaler.pkl` | Feature scaler (Ballarat) |
| `BENDIGO_rf.pkl` | Random Forest classifier (Bendigo) |
| `BENDIGO_gb.pkl` | Gradient Boosting classifier (Bendigo) |
| `BENDIGO_scaler.pkl` | Feature scaler (Bendigo) |

