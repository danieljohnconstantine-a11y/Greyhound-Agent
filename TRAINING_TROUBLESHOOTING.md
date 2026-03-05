# Training Troubleshooting Guide

## Your Question: "why is this not working"

**First:** You didn't show the actual error message! The terminal output was cut off after package installation.

**This guide covers:** All possible issues and how to fix them.

---

## Quick Answer

The most common reasons training might not work:

1. **No data files** - Training needs 600+ PDFs in `data/` directory
2. **Wrong directory** - Must run from repository root
3. **Virtual environment not activated** - Must have `(venv)` in prompt
4. **Missing dependencies** - Need all 6 packages installed

**Most likely:** Your training is actually RUNNING but takes 10-90 minutes! You might think it's "not working" when it's actually processing.

---

## Pre-Flight Checklist

### Before Running Training

✅ **1. Verify You're in the Right Directory**
```bash
pwd
# Should show: /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
```

✅ **2. Check Virtual Environment is Activated**
```bash
# Your prompt should show: (venv)
# If not, run:
source venv/bin/activate
```

✅ **3. Verify All Packages Installed**
```bash
python -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl; print('✅ All packages OK')"
```
**Expected:** `✅ All packages OK`
**If error:** Some package failed to install

✅ **4. Check Data Files Exist**
```bash
ls data/*.pdf | wc -l
```
**Expected:** 600-700 PDF files
**If 0:** No data files! Training can't work without data.

✅ **5. Check Script Exists**
```bash
ls train_ml_track_ensemble.py
```
**Expected:** File found
**If not found:** Wrong directory!

---

## How to Run Training

### Correct Command

```bash
python train_ml_track_ensemble.py
```

OR use the batch file:
```bash
python train_ml_track_ensemble.bat
```

### What You Should See

**Immediate output (first 10 seconds):**
```
================================================================================
🏁 GREYHOUND RACE PREDICTION - TRACK-SPECIFIC ENSEMBLE TRAINING
================================================================================
🎯 TRAINING APPROACH:
   • Track-specific models: Separate model per venue
   • 3 algorithms: RandomForest + GradientBoosting + XGBoost
   • Ensemble predictions: Average across all 3 algorithms
   • Calibrated probabilities: Isotonic regression for better estimates

📁 STEP 1: Loading historical race data...
--------------------------------------------------------------------------------
✅ Loaded 645 races
   Total dogs: 5821
   Winner entries: 645
```

**This means training is WORKING!**

### How Long It Takes

| Data Size | Time |
|-----------|------|
| 100 races | 10-15 minutes |
| 300 races | 20-30 minutes |
| 600+ races | 45-90 minutes |

**If you see the output above, BE PATIENT!** It takes time.

---

## Common Errors and Solutions

### Error 1: "No such file or directory"

**Error message:**
```
python: can't open file 'train_ml_track_ensemble.py': [Errno 2] No such file or directory
```

**Cause:** Wrong directory

**Solution:**
```bash
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
python train_ml_track_ensemble.py
```

### Error 2: "ModuleNotFoundError: No module named 'pandas'"

**Error message:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Cause:** Packages not installed OR virtual environment not activated

**Solution:**
```bash
# Activate venv
source venv/bin/activate

# Verify activation (should see (venv) in prompt)
# Then install packages
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Error 3: "No data files found" or "Loaded 0 races"

**Error message:**
```
❌ ERROR loading data: No PDFs found in data/
```

**Cause:** No data files in data/ directory

**Solution:**
The repository should have 600+ PDFs in `data/`. If missing:
1. Check if data/ directory exists: `ls data/`
2. If empty, you need to add historical race PDFs
3. Each PDF should be a race form (e.g., SALEG0101form.pdf)

### Error 4: "MemoryError" or System Freezes

**Error message:**
```
MemoryError: Unable to allocate array
```

**Cause:** Not enough RAM (needs 4-8GB)

**Solution:**
- Close other programs
- Use a machine with more RAM
- OR train on fewer races (reduce data)

### Error 5: Script Seems Stuck (No Output for Minutes)

**What you see:**
```
📁 STEP 1: Loading historical race data...
[nothing for 5+ minutes]
```

**Cause:** Processing large PDFs (THIS IS NORMAL!)

**Solution:**
- **BE PATIENT!** PDF parsing takes 5-15 minutes
- Watch CPU usage - if high, it's working
- Don't close the terminal
- Wait for "✅ Loaded X races" message

### Error 6: "Permission denied" on Windows

**Error message:**
```
PermissionError: [Errno 13] Permission denied: 'models/track_ensemble'
```

**Cause:** File/folder permission issue or antivirus blocking

**Solution:**
```bash
# Create directories manually
mkdir -p models/track_ensemble
mkdir -p logs

# Run as administrator if needed
```

---

## Expected Training Output

### Full Training Session Example

```
================================================================================
🏁 GREYHOUND RACE PREDICTION - TRACK-SPECIFIC ENSEMBLE TRAINING
================================================================================
🎯 TRAINING APPROACH:
   • Track-specific models: Separate model per venue
   • 3 algorithms: RandomForest + GradientBoosting + XGBoost
   • Ensemble predictions: Average across all 3 algorithms

📁 STEP 1: Loading historical race data...
--------------------------------------------------------------------------------
✅ Loaded 645 races
   Total dogs: 5821
   Winner entries: 645

🔧 STEP 2: Extracting features and organizing by track...
--------------------------------------------------------------------------------
   CHECKPOINT: Entered STEP 2 try block
   Processing 645 race entries with 645 winner entries...
   Note: With Top 4 training, each race appears 4 times (1st/2nd/3rd/4th)

📊 TRACK: SALE (291 races, 2619 dogs)
   Training 3 models for SALE...
      Training RandomForest with weighted samples...
      📊 OOB accuracy: 45.2% (free validation)
      Calibrating RandomForest...
      Training GradientBoosting with advanced optimizations...
      ⚡ Early stopping: used 187/200 estimators
      📊 GB top feature: BestTimeSec (0.284)
      Calibrating GradientBoosting...
      Training XGBoost with histogram method...
      ⚡ XGB early stopping: used 183/200 rounds
      📊 XGB top feature: BestTimeSec (0.312)
      Calibrating XGBoost...

   ✅ SALE training complete
      RF accuracy: 38.5%
      GB accuracy: 42.1%
      XGB accuracy: 43.7%
      Ensemble accuracy: 44.9%
      Calibrated RF: 39.2%
      Calibrated GB: 43.0%
      Calibrated XGB: 44.5%
      Calibrated Ensemble: 46.1% ⭐ BEST

📊 TRACK: WENTWORTH PARK (354 races, 3202 dogs)
   [... similar output for each track ...]

✅ Training pipeline completed successfully!
   Models saved to: /path/to/models/track_ensemble/
```

**If you see this → Training is working!**

---

## Verification After Training

### Check Models Were Created

```bash
ls -lh models/track_ensemble/
```

**Expected output:**
```
SALE_rf.pkl          (14-15 MB)
SALE_gb.pkl          (800-900 KB)
SALE_xgb.pkl         (500-600 KB)
SALE_scaler.pkl      (3-4 KB)
WENTWORTH PARK_rf.pkl (14-15 MB)
WENTWORTH PARK_gb.pkl (900-1000 KB)
... (more track models)
```

**If you see these files → Training succeeded!**

### Test Loading a Model

```python
import pickle
with open('models/track_ensemble/SALE_rf.pkl', 'rb') as f:
    model = pickle.load(f)
print("✅ Model loaded successfully!")
```

---

## What to Do If You Still Have Issues

### Step 1: Get the Actual Error Message

Run training and **copy the FULL output** including error messages:

```bash
python train_ml_track_ensemble.py 2>&1 | tee training_output.txt
```

This saves all output to `training_output.txt` so you can read the error.

### Step 2: Check System Requirements

**Minimum:**
- RAM: 4GB (8GB recommended)
- Disk: 2GB free space
- CPU: Multi-core (4+ cores recommended)
- Python: 3.8+ (you have 3.12 ✅)

### Step 3: Verify Package Versions

```bash
pip list | grep -E "(pandas|numpy|scikit-learn|xgboost|pdfplumber|openpyxl)"
```

**Expected:**
```
numpy          2.4.2
pandas         3.0.1
pdfplumber     0.11.9
openpyxl       3.1.5
scikit-learn   1.8.0
xgboost        3.2.0
```

### Step 4: Check Python Version

```bash
python --version
```

**Expected:** Python 3.8 or higher
**You have:** 3.12 ✅

---

## Quick Diagnosis Commands

Run these to diagnose issues:

```bash
# Check you're in right place
pwd

# Check venv is activated
which python
# Should show: /path/to/venv/bin/python

# Check packages
python -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl; print('✅ OK')"

# Check data files
ls data/*.pdf | wc -l

# Check script exists
ls train_ml_track_ensemble.py

# Check available RAM
free -h  # Linux
# OR
wmic OS get FreePhysicalMemory  # Windows

# Check disk space
df -h .  # Linux
# OR
dir  # Windows (look at "bytes free")
```

---

## Most Likely Issues

### Issue 1: "Not Working" = Actually Running!

**Symptom:** No output for 5-10 minutes after starting

**Reality:** Training takes 45-90 minutes for 600+ races. The script:
1. Parses 600+ PDF files (5-15 minutes)
2. Extracts features (2-5 minutes)
3. Trains models (30-70 minutes)

**Solution:** **BE PATIENT!** Check CPU usage - if high, it's working.

### Issue 2: No Output at All

**Symptom:** Command runs, returns immediately, nothing happens

**Cause:** Usually wrong directory or missing script

**Solution:**
```bash
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
ls train_ml_track_ensemble.py  # Verify it exists
python train_ml_track_ensemble.py
```

### Issue 3: Package Import Errors

**Symptom:** ModuleNotFoundError for any package

**Cause:** Virtual environment not activated or packages not installed

**Solution:**
```bash
source venv/bin/activate  # Activate venv
pip install -r requirements.txt  # Install all packages
```

---

## Summary

### Question
"why is this not working"

### Most Likely Answer
**It IS working!** Training takes 45-90 minutes. You need to wait.

### Quick Checklist
- [ ] In correct directory
- [ ] Virtual environment activated `(venv)`
- [ ] All packages installed
- [ ] Data files exist (600+ PDFs)
- [ ] Running correct command: `python train_ml_track_ensemble.py`
- [ ] Waiting long enough (45-90 minutes)

### If Actually Broken
1. Get the FULL error message
2. Check the "Common Errors" section above
3. Run the "Quick Diagnosis Commands"
4. Provide complete error output for help

### Expected Behavior
- Starts immediately (shows title banner)
- Loads data (5-15 minutes)
- Trains models (30-70 minutes)
- Saves models to `models/track_ensemble/`
- Shows "✅ Training pipeline completed successfully!"

**If you see the title banner → It's working → Be patient!**

---

## Next Steps After Training

### 1. Verify Models Created
```bash
ls -lh models/track_ensemble/
```

### 2. Test Predictions
```bash
python run_track_ensemble_predictions.py
```

### 3. Check Outputs
```bash
ls outputs/*.xlsx
```

---

**Most important:** Show the ACTUAL error message if something fails!

Without seeing what error you got, we can only guess what went wrong.
