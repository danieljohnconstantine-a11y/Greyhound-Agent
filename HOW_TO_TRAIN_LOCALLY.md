# How to Train All Track Models Locally (Updated March 2026)

> **Use this guide** — the branch has been updated with sigmoid calibration, correct
> PDF year detection, and track-code fixes. Training now takes ~20 minutes on a
> modern laptop. Each model file is ≤ 2.3 MB (was 9–24 MB), so all files commit to
> GitHub directly without LFS.

---

## 1 — Prerequisites

- Windows 11 / Ubuntu 22.04 (WSL or native)
- Python 3.10+
- Git
- ~4 GB free RAM
- The PDF form guides and results CSVs are already in `data/` in the repo — you do
  not need to download them separately.

---

## 2 — Clone the correct branch

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop
rm -rf Greyhound-Agent
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
```

> ⚠️ **Branch name has changed** from the old instructions — use `copilot/copy-ml-training-prediction-files-again`.
>
> ⚠️ **Common mistake:** do NOT split the `git clone` line with a backslash `\` across two lines when typing in a terminal. If you copy-paste and a space appears before `https`, git will fail with `fatal: protocol ' https' is not supported`. Keep the whole command on one line.

---

## 3 — Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate          # Linux / WSL
# OR on Windows PowerShell:
# venv\Scripts\Activate.ps1
```

---

## 4 — Install dependencies

```bash
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

---

## 5 — Delete old models (start clean)

```bash
rm -f models/*.pkl
```

---

## 6 — Run full training (uses ALL PDFs + results CSVs in `data/`)

```bash
python retrain_all_tracks_sigmoid.py
```

**What this does:**
- Reads all results CSVs in `data/` and matches them to PDF form guides
- Trains RF + GB + XGB with **sigmoid calibration** for every track that has enough data
- Saves per-track `.pkl` files to `models/` (e.g. `models/BENDIGO_rf.pkl`, `models/BENDIGO_gb.pkl`, `models/BENDIGO_xgb.pkl`, `models/BENDIGO_scaler.pkl`)
- Writes a retrain report to `reports/RETRAIN_REPORT_<date>.txt`
- Prints accuracy and probability-spread stats per track when done

> ❌ **Do NOT run** `train_ml_track_ensemble.py` — it uses the old isotonic calibration and a flat model-file layout that the prediction script no longer expects.

**What you will see on screen:**

```
🔁 RETRAIN ALL TRACKS — SIGMOID CALIBRATION
============================================================
Found NN tracks with enough data to train
[1/NN] BENDIGO  (NNN samples) ...
   RF  accuracy=xx.x%  spread=0.xxx
   GB  accuracy=xx.x%  spread=0.xxx
   XGB accuracy=xx.x%  spread=0.xxx
[2/NN] CANNINGTON ...
   ...
============================================================
✅  NN/NN tracks retrained successfully
Report saved: reports/RETRAIN_REPORT_<date>.txt
```

**Expected output (summary line):**
```
✅  NN/NN tracks retrained successfully
```

---

## 7 — Verify models were created

```bash
ls -lh models/
```

You should see four `.pkl` files per track, named `{TRACK}_rf.pkl`, `{TRACK}_gb.pkl`, `{TRACK}_xgb.pkl`, and `{TRACK}_scaler.pkl` (e.g. `BENDIGO_rf.pkl`).
Every individual `.pkl` file should be **under 5 MB**.

---

## 8 — Push new models to GitHub

```bash
git add models/*.pkl
git commit -m "retrain all tracks: sigmoid calibration"
git push origin copilot/copy-ml-training-prediction-files-again
```

If prompted, use your GitHub username and a Personal Access Token (not your password).

---

## What changed since the previous training guide

| Area | Old behaviour | New behaviour |
|---|---|---|
| Branch name | `copy-ml-training-prediction-files` | `copy-ml-training-prediction-files-again` |
| Training script | `train_ml_track_ensemble.py` (isotonic, flat model layout) | `retrain_all_tracks_sigmoid.py` (sigmoid, per-track model layout) |
| Calibration | `isotonic` (collapsed to flat step functions on small datasets) | `sigmoid` (monotonic — no collapse possible) |
| Model filenames | `rf.pkl`, `gb.pkl` etc. (shared) | `{TRACK}_rf.pkl`, `{TRACK}_gb.pkl` etc. (per-track) |
| Collapse detection | Triggered on both true collapse AND spread < 0.5% (near-constant) | Only triggers on true collapse (n_unique < half field); low spread = evenly-matched race, not a model fault |
| RF max_depth | 15–30 → 9–24 MB files, too large for GitHub | 10 → ~2.3 MB, fits in GitHub |
| Year detection | Only January PDFs treated as 2026 | Months Jan–Jun correctly treated as 2026 |
| Track codes | Broken Hill, Mount Gambier, Q Parklands, Warrnambool silently skipped | All 4 now matched to their PDFs |
| Form-guide date | Exact date match only | Also checks PDF date = race date − 1 day (form guides published day before) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `fatal: protocol ' https' is not supported` | You have a **space before `https`** — copy the `git clone` line as one unbroken line; never split it with `\` |
| `python retrain_all_tracks_sigmoid.py` shows nothing for 2–3 min | **Normal** — the script reads all results CSVs and PDFs silently at startup. First progress line appears after ~30–60 s. |
| `ModuleNotFoundError: pdfplumber` | Run `pip install pdfplumber` |
| `ModuleNotFoundError: xgboost` | Run `pip install xgboost` |
| `0 tracks trained` | Make sure you are in the repo root and `data/*.csv` results files exist |
| Git push rejected (file too large) | All models should be < 5 MB each; if one is > 100 MB, re-check you used `retrain_all_tracks_sigmoid.py` and not `train_ml_track_ensemble.py` |
| Training takes > 40 min | Normal on older hardware — PDF parsing is CPU-bound |
