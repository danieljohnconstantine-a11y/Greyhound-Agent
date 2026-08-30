# Greyhound Analytics Pipeline

---

## 📬 OUTREACH LETTER

> **Draft message to Ryan Conneely (Barking Mad Betting):**  
> 👉 **[outreach/email_ryan_conneely_barking_mad_betting.txt](outreach/email_ryan_conneely_barking_mad_betting.txt)**

---

## 📢 LATEST RESPONSE

> **Today's full betting summary and prediction audit:**  
> 👉 **[RESPONSE.md](RESPONSE.md)** — rendered (easiest to read)  
> 👉 **[LAST_RESPONSE.txt](LAST_RESPONSE.txt)** — plain text  
> *(updated each race day)*

---

Automated parsing and scoring of greyhound racing forms.

## Features
- PDF-to-text ingestion
- Race form parsing
- Trainer matching
- Feature scoring
- Top pick selection

## 🟢 Quick Setup

> **New here?** See [`HOW_TO_TRAIN_LOCALLY.md`](HOW_TO_TRAIN_LOCALLY.md) for the full guide.  
> **If Windows times out, use Ubuntu with these exact commands:**
> ```bash
> cd ~
> rm -rf Greyhound-Agent
> git clone -b copilot/copy-ml-training-prediction-files-again https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
> cd Greyhound-Agent
> python3 -m venv venv
> source venv/bin/activate
> pip install --upgrade pip
> pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
> python check_system_ready.py
> python retrain_all_tracks_sigmoid.py
> ```
>
> **If you want to train in Ubuntu and use daily in Windows:**  
> Use the `Train in Ubuntu, use daily in Windows` section in `HOW_TO_TRAIN_LOCALLY.md` (includes Python 3.11 Windows setup and model-copy step).

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
