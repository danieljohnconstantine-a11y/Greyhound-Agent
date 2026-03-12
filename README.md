# Greyhound Analytics Pipeline

Automated parsing and scoring of greyhound racing forms.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection

## 🟢 Quick Setup

> **New here?** See [`HOW_TO_TRAIN_LOCALLY.md`](HOW_TO_TRAIN_LOCALLY.md) for a **basic step-by-step guide** — every command on its own numbered line, for both Ubuntu and Windows.

### 1 — Clone the repo

**WSL / Linux / macOS:**
```bash
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
```

**Windows PowerShell:**
```powershell
git clone --depth 1 -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
```

### 2 — Create and activate a virtual environment

> **Which activate command do I use?** It depends on your terminal:
>
> | Terminal | Command |
> |---|---|
> | **Windows PowerShell** | `venv\Scripts\Activate.ps1` |
> | **Windows CMD** | `venv\Scripts\activate.bat` |
> | **WSL / Linux / macOS** | `source venv/bin/activate` |

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

> If PowerShell shows "running scripts is disabled", run once:
> `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 3 — Install dependencies
```bash
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### 4 — Train models and run predictions

**Ubuntu/WSL (recommended):**
```bash
python retrain_all_tracks_sigmoid.py
```

**Windows — double-click in Explorer:**
```
retrain_all_tracks_sigmoid.bat
```

> ❌ Do NOT run `train_ml_track_ensemble.py` — obsolete isotonic script.  
> See [`HOW_TO_TRAIN_LOCALLY.md`](HOW_TO_TRAIN_LOCALLY.md) for the complete basic step-by-step guide.

## Usage
1. Place your `.txt` form file in the `data/` folder.
2. Run `main.py`
3. Check results in `outputs/`

## Output Files
- `todays_form.csv`: Parsed race data
- `ranked.csv`: Scored dogs
- `picks.csv`: Top 5 betting picks
