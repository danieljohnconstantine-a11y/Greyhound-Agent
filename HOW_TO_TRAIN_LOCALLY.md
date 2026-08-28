# How to Train and Run Predictions Locally (Updated March 2026)

---

## 🟢 BASIC STEP-BY-STEP — copy and paste ONE line at a time

> **Wait for each command to finish before typing the next one.**  
> A command is finished when you see the `$` prompt again (or "Press any key" on Windows).

---

### Option A — Ubuntu or WSL (Windows Subsystem for Linux)

Open an **Ubuntu** terminal window, then type each line below and press **Enter**:

**Step 1 — Go to your home folder**
```bash
cd ~
```

**Step 2 — Clone the repository** *(downloads all code and data — ~200 MB, takes 2–5 min)*
```bash
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Step 3 — Go into the folder**
```bash
cd Greyhound-Agent
```

**Step 4 — Create a Python virtual environment** *(a self-contained Python install)*
```bash
python3 -m venv venv
```

**Step 5 — Activate the virtual environment** *(you must do this every new terminal session)*
```bash
source venv/bin/activate
```
> ✅ You should now see `(venv)` at the start of your prompt.

**Step 6 — Install required Python packages** *(one-time; takes 1–3 min)*
```bash
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

**Step 7 — Train all models** *(takes ~20 min; output appears after ~30–60 s)*
```bash
python retrain_all_tracks_sigmoid.py
```

**Step 8 — Check models were created** *(should list 4 files per track)*
```bash
ls -lh models/*.pkl | head -20
```

**That's it!** Models are saved in `models/`. To run predictions, see Step 11 below.

---

### Option B — Windows (PowerShell or Command Prompt)

Open **PowerShell** (search "PowerShell" in the Start menu), then type each line:

**Step 1 — Go to your Desktop**
```powershell
cd $env:USERPROFILE\Desktop
```

**Step 2 — Clone the repository** *(keep this on ONE line — no space before "https")*
```powershell
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Step 3 — Go into the folder**
```powershell
cd Greyhound-Agent
```

**Step 4 — Create a Python virtual environment**
```powershell
python -m venv venv
```

**Step 5 — Allow scripts to run** *(one-time; PowerShell only)*
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
> Press `Y` and Enter when asked.

**Step 6 — Activate the virtual environment**
```powershell
venv\Scripts\Activate.ps1
```
> ✅ You should now see `(venv)` at the start of your prompt.

**Step 7 — Install required Python packages**
```powershell
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

**Step 8 — Delete any old models** *(start clean)*
```powershell
Remove-Item models\*.pkl -Force -ErrorAction SilentlyContinue
```

**Step 9 — Train all models** *(takes ~20 min; ⚠️ PowerShell may time out on slow PCs — use Ubuntu instead)*
```powershell
python retrain_all_tracks_sigmoid.py
```

**Alternatively — double-click this file in Explorer instead of Step 9:**
```
retrain_all_tracks_sigmoid.bat
```

**Step 10 — Run daily predictions**
```
1. Put today's PDF form guides in the  data_predictions\  folder
2. Double-click  run_track_ensemble_predictions.bat
3. Open  outputs\track_ensemble_predictions.xlsx  for results
```

---

### ❌ DO NOT run this — it is the OLD wrong script:
```bash
python train_ml_track_ensemble.py   ← WRONG (isotonic calibration, wrong file layout)
```
Always use `python retrain_all_tracks_sigmoid.py` or `bash train_ubuntu.sh` instead.

---

## ⚠️ CORRECTED Ubuntu Quick-Start (replaces old instructions)

> The **old** instructions contained a critical error — `python train_ml_track_ensemble.py`  
> uses obsolete isotonic calibration and writes models in the wrong layout.  
> Use the corrected commands below.

### ❌ OLD (wrong — do not use)
```bash
cd /mnt/c/Users/danie/OneDrive/Desktop   # ← slow Windows filesystem via WSL
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again \
    https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
python3 -m venv venv && source venv/bin/activate
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
rm -f models/*.pkl
python train_ml_track_ensemble.py   # ← WRONG SCRIPT (isotonic, wrong layout)
```

### ✅ CORRECT — one-time setup on Ubuntu
```bash
# Run from any Ubuntu terminal (native Ubuntu or WSL — use the Ubuntu home directory,
# NOT /mnt/c/ which is slow and may hit permission issues)
cd ~

# Option A — if you already cloned the repo (recommended: inspect before running):
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again \
    https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
cat setup_ubuntu.sh          # inspect the script first
bash setup_ubuntu.sh         # then run it
# This creates venv/ and installs all Python packages.
```

If you already have the repo cloned, skip setup and just do:
```bash
cd ~/Greyhound-Agent              # ← native Ubuntu home dir (fast)
source venv/bin/activate
bash train_ubuntu.sh              # ← CORRECT training script (sigmoid calibration)
```

### What changed vs the old instructions

| | Old (wrong) | New (correct) |
|---|---|---|
| **Training script** | `python train_ml_track_ensemble.py` | `bash train_ubuntu.sh` → runs `retrain_all_tracks_sigmoid.py` |
| **Calibration** | isotonic (collapses on small datasets) | sigmoid (always monotonic) |
| **Working directory** | `/mnt/c/…` (Windows drive via WSL — slow) | `~/Greyhound-Agent` (Ubuntu native — fast) |
| **Model filenames** | shared `rf.pkl`, `gb.pkl` | per-track `{TRACK}_rf.pkl`, `{TRACK}_gb.pkl` |
| **After training** | manually copy models | `git push` then `git pull` on Windows |

---

## 🐧 NEW: Train on Ubuntu → Run Predictions on Windows

> Windows PowerShell times out on large training jobs.  
> **Train on Ubuntu instead, then copy the models to Windows and run predictions with the normal bat file.**

### Ubuntu training + Windows predictions — quick-start

| Step | Platform | What to do |
|---|---|---|
| **1 — Setup Ubuntu** | Ubuntu | Run `bash setup_ubuntu.sh` (first time only) |
| **2 — Train all models** | Ubuntu | Run `bash train_ubuntu.sh` |
| **3 — Copy models to Windows** | Windows | Copy `models/*.pkl` from Ubuntu to your Windows `models\` folder |
| **4 — Daily predictions** | Windows | Double-click **`run_track_ensemble_predictions.bat`** |

### Step-by-step: Ubuntu training

```bash
# ── 1. Open a terminal on Ubuntu ──────────────────────────────────────────
# If this is your first time on this machine, run the one-time setup:
bash setup_ubuntu.sh
# This installs prerequisites, clones the repo, creates a venv, and
# installs all Python packages.  Skip if already set up.

# ── 2. Navigate to the repo ───────────────────────────────────────────────
cd ~/Greyhound-Agent       # or wherever you cloned the repo

# ── 3. Activate virtual environment ──────────────────────────────────────
source venv/bin/activate

# ── 4. Run training (one command) ────────────────────────────────────────
bash train_ubuntu.sh
# Duration: ~20 minutes
# Output: models/{TRACK}_rf.pkl  _gb.pkl  _xgb.pkl  _scaler.pkl

# ── 5. Verify models were created ────────────────────────────────────────
ls -lh models/*.pkl | wc -l   # should be 4× number of tracks

# ── 6. Transfer models to Windows ────────────────────────────────────────
# Option A — commit and push to GitHub, then pull on Windows:
git add models/*.pkl
git commit -m "retrain all tracks: sigmoid calibration"
git push

# Option B — copy over the network (adjust IP/path):
# scp models/*.pkl user@windows-machine:/path/to/Greyhound-Agent/models/

# Option C — USB drive or shared folder
```

### Step-by-step: Windows predictions (after models are copied)

```
1. Put today's PDF form guides into the  data_predictions\  folder
2. Double-click  run_track_ensemble_predictions.bat
3. Open  outputs\track_ensemble_predictions.xlsx  for results
```

> ✅ The bat file works exactly the same whether the models were trained on  
> Ubuntu or Windows — `.pkl` files are fully cross-platform.

---

## ⚡ Quick-start for Windows-only (training + predictions on the same machine)

> ### ⚡ Quick-start for Windows — just double-click the bat file
>
> | Step | What to do | Bat file to double-click |
> |---|---|---|
> | **1 — First-time only: train all models** | Run after adding new results CSVs or Word results docs | **`retrain_all_tracks_sigmoid.bat`** |
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
- The PDF form guides and results files are already in `data/` — CSV (`results_*.csv`) and Word (`*RESULTS.docx`) are both supported.

---

## 2 — Clone the repo

> 💡 **Ubuntu users:** Run `bash setup_ubuntu.sh` (see the Ubuntu quick-start section above) — it clones the repo and sets everything up automatically.

**Ubuntu / Linux terminal (manual):**
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

> 🐧 **Ubuntu users:** Use `bash train_ubuntu.sh` — it handles venv activation and provides coloured progress output.  
> 🪟 **Windows users:** Use the bat file below.

**Ubuntu (recommended for large datasets):**
```bash
bash train_ubuntu.sh
```

**Double-click (Windows):**
```
retrain_all_tracks_sigmoid.bat
```

**Terminal (any platform):**
```bash
python retrain_all_tracks_sigmoid.py
```

**What this does:**
- Reads all results files in `data/` (CSV and `*RESULTS.docx`) and matches them to PDF form guides
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
| **`retrain_all_tracks_sigmoid.bat`** | `retrain_all_tracks_sigmoid.py` | After adding new results CSVs or Word results docs — full retrain | ~20 min |
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
| `0 tracks trained` | Make sure you are in the repo root and results files exist in `data/` and/or `data2`/`data3`/`data4` |
| Git push rejected (file too large) | Re-check you used `retrain_all_tracks_sigmoid.py`, not `train_ml_track_ensemble.py`; each `.pkl` must be < 100 MB |
| Training takes > 40 min | Normal on older hardware — PDF parsing is CPU-bound |
| PowerShell says `running scripts is disabled` | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` once, then retry |
| `❌ ERROR training <TRACK>: Can't pickle` | Fixed in current code (`n_jobs=1` in `CalibratedClassifierCV`). Update to latest code and retry. |
