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

## 6 — Run full training (uses ALL 96 PDFs + 3 results CSVs)

```bash
python train_ml_track_ensemble.py
```

**What this does:**
- Parses all 96 PDF form guides in `data/` (~15 min — reads every page of every PDF)
- Matches each race in the 3 results CSVs to its form guide PDF
- Trains RF + GB + XGB with **sigmoid calibration** for every track that has data
- Saves flat `.pkl` files to `models/` (e.g. `models/Angle Park_rf.pkl`)
- Prints a summary table of ensemble accuracy per track when done

**What you will see on screen:**

```
📁 STEP 1: Loading historical race data...
[INFO] Loading data using HYBRID method (PDFs + CSV results)...
[INFO] Found 96 PDFs and 3 results CSV files
   [INFO] Processed 1/96 PDFs (1%)...
   [INFO] Processed 10/96 PDFs (10%)...
   [INFO] Processed 20/96 PDFs (20%)...
   ...  (one line every ~60–90 seconds)
   [INFO] Processed 90/96 PDFs (93%)...
[SUCCESS] Extracted dog data from NNN races in PDFs
🔧 STEP 2: Extracting features...
🚀 STEP 3: Training track-specific ensemble models...
   [1/N] Training models for Angle Park...
   ...
🎉 SUCCESS! Trained N track-specific ensembles
```

> ⏳ **The first progress line (`1/96 PDFs`) appears after ~60 seconds. This is normal — pdfplumber is reading every page of every PDF. If nothing appears for 2–3 minutes, the script is still running.** Do NOT press Ctrl+C.

To watch detailed progress in a second terminal:

```bash
tail -f logs/train_track_ensemble.log
```

**Expected output (final line):**
```
🎉 SUCCESS! Trained N track-specific ensembles
   Models saved to: .../models/
📊 Average ensemble accuracy: 87–89%
```

---

## 7 — Verify models were created

```bash
ls -lh models/*.pkl
```

You should see `rf.pkl`, `gb.pkl`, `xgb.pkl`, and `scaler.pkl` for each track.
Every file should be **under 5 MB**.

---

## 8 — Push new models to GitHub

```bash
git add models/*.pkl models/config.pkl models/ensemble_config.json
git commit -m "retrain all tracks: full PDF+CSV data, sigmoid calibration"
git push origin copilot/copy-ml-training-prediction-files-again
```

If prompted, use your GitHub username and a Personal Access Token (not your password).

---

## What changed since the previous training guide

| Area | Old behaviour | New behaviour |
|---|---|---|
| Branch name | `copy-ml-training-prediction-files` | `copy-ml-training-prediction-files-again` |
| Calibration | `isotonic` (collapsed to flat step functions) | `sigmoid` (no collapse) |
| RF max_depth | 15–30 → 9–24 MB files, too large for GitHub | 10 → ~2.3 MB, fits in GitHub |
| Year detection | Only January PDFs treated as 2026 | Months Jan–Jun correctly treated as 2026 |
| Track codes | Broken Hill, Mount Gambier, Q Parklands, Warrnambool silently skipped | All 4 now matched to their PDFs |
| Form-guide date | Exact date match only | Also checks PDF date = race date − 1 day (form guides published day before) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `fatal: protocol ' https' is not supported` | You have a **space before `https`** — copy the `git clone` line as one unbroken line; never split it with `\` |
| `python train_ml_track_ensemble.py` shows nothing for 2–3 min | **Normal** — pdfplumber reads 96 PDFs silently at startup. First progress line appears after ~60 s. Run `tail -f logs/train_track_ensemble.log` in a second terminal to see live detail. |
| `ModuleNotFoundError: pdfplumber` | Run `pip install pdfplumber` |
| `ModuleNotFoundError: xgboost` | Run `pip install xgboost` |
| `0 tracks trained` | Make sure you are in the repo root and `data/*.pdf` files exist |
| Git push rejected (file too large) | All models should be < 5 MB now; if one is > 100 MB, re-check you used the right branch |
| Training takes > 40 min | Normal on older hardware — the PDF parsing is CPU-bound |
