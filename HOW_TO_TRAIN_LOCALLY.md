# How to Train and Run Predictions Locally (Updated March 2026)

> ### ⚡ Quick-start for Windows — just double-click the bat file
>
> | Step | What to do | Bat file to double-click |
> |---|---|---|
> | **1 — First-time only: train all models** | Run after adding new results CSVs | **`retrain_all_tracks_sigmoid.bat`** |
> | **2 — Check models are healthy** | Run after training | **`check_system_ready.bat`** |
> | **3 — Validate pipeline** | Confirms every model loads OK | **`validate_pipeline.bat`** |
> | **4 — Daily: run predictions** | Put today's PDFs in `data_predictions/` first | **`run_track_ensemble_predictions.bat`** |
>
> ❌ **Do NOT use `train_ml_track_ensemble.bat`** — obsolete isotonic script, do not run it.

---

## 1 — Prerequisites

- Windows 10/11 (native PowerShell or WSL) or Ubuntu 22.04
- Python 3.10+ — download from https://www.python.org/downloads/ (tick **"Add to PATH"**)
- Git
- ~4 GB free RAM
- The PDF form guides and results CSVs are already in `data/` — you don't need to download them separately.

---

## 2 — Clone the repo

**WSL or Linux terminal:**
```bash
cd ~
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
```

**Windows PowerShell:**
```powershell
cd $env:USERPROFILE\Desktop
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
```

> ⚠️ Keep the `git clone` command on **one line** — if a space sneaks in before `https`, git will fail with `fatal: protocol ' https' is not supported`.

---

## 3 — Create and activate a virtual environment

> ### ❓ Which activate command do I use?
>
> **It depends which terminal you are in:**
>
> | Terminal | Command to activate |
> |---|---|
> | **Windows PowerShell** (native Windows) | `venv\Scripts\Activate.ps1` |
> | **Windows CMD** (Command Prompt) | `venv\Scripts\activate.bat` |
> | **WSL / Linux / macOS bash** | `source venv/bin/activate` |
>
> The bat files in this repo handle activation automatically — you don't need to activate manually if you always use the bat files.

**WSL / Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows PowerShell:**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

---

## 4 — Install dependencies

```bash
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

> The bat files auto-install missing packages, so if you always use the bat files you can skip this step.

---

## 5 — Delete old models (start clean, first time only)

**WSL / Linux:**
```bash
rm -f models/*.pkl
```

**Windows:**
```cmd
del /Q models\*.pkl
```

> The `retrain_all_tracks_sigmoid.bat` does this automatically before training.

---

## 6 — Train all models

**Double-click (Windows):**
```
retrain_all_tracks_sigmoid.bat
```

**Terminal:**
```bash
python retrain_all_tracks_sigmoid.py
```

**What this does:**
- Reads all results CSVs in `data/` and matches them to PDF form guides
- Trains RF + GB + XGB with **sigmoid calibration** for every track with ≥50 races
- Saves per-track `.pkl` files: `models/BENDIGO_rf.pkl`, `_gb.pkl`, `_xgb.pkl`, `_scaler.pkl`
- Writes `reports/RETRAIN_REPORT_<date>.txt`

> ❌ **Do NOT run** `train_ml_track_ensemble.py` or `train_ml_track_ensemble.bat` — obsolete isotonic calibration, wrong file layout.

**Expected screen output:**
```
🔁 RETRAIN ALL TRACKS — SIGMOID CALIBRATION
Found NN tracks with enough data to train
[1/NN] BENDIGO  (NNN samples) ...
   RF  accuracy=xx.x%  spread=0.xxx
   ...
✅  NN/NN tracks retrained successfully
Report saved: reports/RETRAIN_REPORT_<date>.txt
```

---

## 7 — Check system readiness (GO / NO-GO)

**Double-click (Windows):**
```
check_system_ready.bat
```

**Terminal:**
```bash
python check_system_ready.py
```

Confirms every track has RF + GB + XGB + scaler, checks calibration quality, and lists any tracks that need retraining.

---

## 8 — Validate pipeline (model integrity)

**Double-click (Windows):**
```
validate_pipeline.bat
```

**Terminal:**
```bash
python validate_pipeline.py
```

Test-loads every model and runs a dummy prediction through each ensemble. All rows should show `PASS`.

---

## 9 — Verify models were created

**WSL / Linux:**
```bash
ls -lh models/
```

**Windows:**
```cmd
dir models\
```

Each track should have four `.pkl` files. Every file should be **under 5 MB**.

---

## 10 — Push new models to GitHub

```bash
git add models/*.pkl
git commit -m "retrain all tracks: sigmoid calibration"
git push origin copilot/copy-ml-training-prediction-files-again
```

If prompted for a password, use a [Personal Access Token](https://github.com/settings/tokens) — not your GitHub password.

---

## 11 — Run predictions on today's races

1. Copy today's PDF form guides into the `data_predictions/` folder.
2. **Double-click (Windows):**
   ```
   run_track_ensemble_predictions.bat
   ```
   **Or terminal:**
   ```bash
   python run_track_ensemble_predictions.py
   ```
3. Open `outputs/track_ensemble_predictions.xlsx` for the results.

---

## Complete bat file reference

| Bat file | Script it runs | When to use | Duration |
|---|---|---|---|
| **`retrain_all_tracks_sigmoid.bat`** | `retrain_all_tracks_sigmoid.py` | After adding new results CSVs — full retrain | ~20 min |
| **`check_system_ready.bat`** ✨ NEW | `check_system_ready.py` | After training, or any time you want a GO/NO-GO | ~30 sec |
| **`validate_pipeline.bat`** ✨ NEW | `validate_pipeline.py` | After training, confirm all models load correctly | ~60 sec |
| **`run_track_ensemble_predictions.bat`** | `run_track_ensemble_predictions.py` | Daily — predictions from PDFs in `data_predictions/` | ~2 min |
| **`backtest_win_rate.bat`** ✨ NEW | `backtest_win_rate.py` | Analyse historical win rates from results CSVs | ~10 sec |
| **`audit_all_features.bat`** ✨ NEW | `audit_all_features.py` | After editing `src/features.py` — verify 75 features | ~10 sec |
| **`train_xgb_models.bat`** ✨ NEW | `train_xgb_models.py` | Rebuild XGB models only (RF+GB unchanged) | ~10 min |
| **`run_daily.bat`** ✨ NEW | `run_daily.py` | Run the full daily pipeline via `main.py` | ~2 min |
| `run_parser.bat` | `src/main.py` | Parse PDFs with heuristic scorer only (no ML) | ~1 min |
| `run_main.bat` | `main.py` | Legacy entry point | — |
| `ORGANIZE_ALL_TRACKS.bat` | `reorganize_models_by_track.py` + `add_training_metrics.py` | One-off: reorganise models into subdirectories | ~30 sec |

> ❌ **`train_ml_track_ensemble.bat`** — **DO NOT USE** — obsolete isotonic script.

---

## What changed since the previous training guide

| Area | Old | New |
|---|---|---|
| Training script | `train_ml_track_ensemble.py` (isotonic) | `retrain_all_tracks_sigmoid.py` (sigmoid) |
| Calibration | `isotonic` → flat step functions on small datasets | `sigmoid` → monotonic, no collapse possible |
| Model filenames | `rf.pkl`, `gb.pkl` (shared) | `{TRACK}_rf.pkl`, `{TRACK}_gb.pkl` (per-track) |
| RF max_depth | 15–30 (9–24 MB, too large for GitHub) | 10 (~2.3 MB, fits in GitHub) |
| Year detection | Only January treated as 2026 | Jan–Jun correctly treated as 2026 |
| Form-guide date | Exact date match only | Also checks PDF date = race date − 1 day |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `fatal: protocol ' https' is not supported` | Space before `https` — keep the `git clone` on one line |
| Nothing printed for 2–3 min after starting training | **Normal** — PDF parsing is silent at startup; first line appears after ~30–60 s |
| `ModuleNotFoundError: pdfplumber` | `pip install pdfplumber` |
| `ModuleNotFoundError: xgboost` | `pip install xgboost` |
| `0 tracks trained` | Make sure you are in the repo root and `data/*.csv` results files exist |
| Git push rejected (file too large) | Re-check you used `retrain_all_tracks_sigmoid.py`, not `train_ml_track_ensemble.py`; each `.pkl` must be < 100 MB |
| Training takes > 40 min | Normal on older hardware — PDF parsing is CPU-bound |
| PowerShell says `running scripts is disabled` | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` once, then retry |
